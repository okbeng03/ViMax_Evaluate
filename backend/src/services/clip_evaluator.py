"""CLIP evaluator using open_clip_torch for semantic similarity."""

from typing import Optional, Tuple
from io import BytesIO
import asyncio
import httpx

from PIL import Image
import torch
import open_clip

from src.config import settings
from src.utils.logger import logger


class CLIPEvaluator:
    """CLIP-based semantic similarity evaluator."""

    def __init__(self):
        self._model = None
        self._preprocess = None
        self._device = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize CLIP model."""
        if self._initialized:
            return

        try:
            self._device = settings.clip_device if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading CLIP model: {settings.clip_model_name} on {self._device}")
            
            model, _, preprocess = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: open_clip.create_model_and_transforms(
                    settings.clip_model_name,
                    device=self._device,
                    pretrained="openai"
                )
            )
            
            model.eval()  # 默认为 train 模式，需设为 eval
            self._model = model
            self._preprocess = preprocess
            self._initialized = True
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise

    async def evaluate(
        self,
        image_source: str,
        prompt: str,
    ) -> Tuple[float, str]:
        """Evaluate semantic similarity between image and prompt.
        
        Returns:
            Tuple of (score, interpretation)
            - score: 0.0 to 1.0 semantic similarity
            - interpretation: "consistent", "ambiguous", or "inconsistent"
        """
        if not self._initialized:
            await self.initialize()

        try:
            image = await self._load_image(image_source)
            
            def _compute_score():
                image_tensor = self._preprocess(image).unsqueeze(0).to(self._device)
                with torch.no_grad():
                    image_features = self._model.encode_image(image_tensor)
                    text_features = self._model.encode_text(
                        open_clip.get_tokenizer(settings.clip_model_name)([prompt]).to(self._device)
                    )
                    
                    image_features /= image_features.norm(dim=-1, keepdim=True)
                    text_features /= text_features.norm(dim=-1, keepdim=True)
                    
                    similarity = (image_features @ text_features.T).item()
                
                return similarity

            score = await asyncio.get_event_loop().run_in_executor(None, _compute_score)
            score = float(score)

            interpretation = self._interpret_score(score)
            logger.info(f"CLIP evaluation: score={score:.4f}, interpretation={interpretation}")

            return score, interpretation

        except Exception as e:
            logger.error(f"CLIP evaluation failed: {e}")
            raise

    async def _load_image(self, image_source: str) -> Image.Image:
        """Load image from URL or base64."""
        if image_source.startswith("http://") or image_source.startswith("https://"):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_source)
                response.raise_for_status()
                return Image.open(BytesIO(response.content)).convert("RGB")
        else:
            import base64
            image_data = base64.b64decode(image_source)
            return Image.open(BytesIO(image_data)).convert("RGB")

    def _interpret_score(self, score: float) -> str:
        """Interpret CLIP score."""
        if score >= 0.7:
            return "consistent"
        elif score <= 0.5:
            return "inconsistent"
        else:
            return "ambiguous"


clip_evaluator = CLIPEvaluator()

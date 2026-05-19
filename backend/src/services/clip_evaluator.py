"""CLIP evaluator using open_clip_torch for semantic similarity."""

from typing import Optional, Tuple
import asyncio

from PIL import Image
import torch
import open_clip

from src.config import settings
from src.utils.logger import logger
from src.services.image_loader import image_loader


class CLIPEvaluator:
    """CLIP-based semantic similarity evaluator."""

    def __init__(self):
        self._model = None
        self._preprocess = None
        self._device = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize CLIP model (lazy loading - only loads when first used)."""
        if self._initialized:
            return
        
        # 模型为懒加载模式，只在第一次 evaluate() 时加载
        self._initialized = True
        logger.info("CLIP evaluator ready (lazy loading enabled)")

    async def _ensure_loaded(self) -> None:
        """Ensure model is loaded (called on first use)."""
        if self._model is None:
            await self._load_model()

    async def _load_model(self) -> None:
        """Load CLIP model."""
        try:
            self._device = settings.clip_device if torch.cuda.is_available() else "cpu"
            
            model_name = "ViT-L-14"
            pretrained = settings.clip_model_path if settings.clip_model_path else "openai"
            logger.info(f"Loading CLIP model: {model_name} on {self._device}, pretrained: {pretrained}")
            
            model, _, preprocess = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: open_clip.create_model_and_transforms(
                    model_name,
                    device=self._device,
                    pretrained=pretrained
                )
            )
            
            model.eval()
            self._model = model
            self._preprocess = preprocess
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise

    def _release_model(self) -> None:
        """Release model from memory and GPU."""
        if self._model is not None:
            del self._model
            self._model = None
            self._preprocess = None
            if self._device and "cuda" in self._device:
                torch.cuda.synchronize()  # 等待当前进程所有 CUDA 操作完成
                torch.cuda.empty_cache()   # 清空当前进程缓存
            logger.info("CLIP model released from memory")

    async def evaluate(
        self,
        image_source: str,
        prompt: str,
    ) -> Tuple[float, str]:
        """Evaluate semantic similarity between image and prompt.
        
        Model is loaded on demand and released after evaluation.
        
        Returns:
            Tuple of (score, interpretation)
            - score: 0.0 to 1.0 semantic similarity
            - interpretation: "consistent", "ambiguous", or "inconsistent"
        """
        if not self._initialized:
            await self.initialize()

        try:
            await self._ensure_loaded()
            image = await image_loader.load(image_source)
            
            def _compute_score():
                image_tensor = self._preprocess(image).unsqueeze(0).to(self._device)
                with torch.no_grad():
                    image_features = self._model.encode_image(image_tensor)
                    text_features = self._model.encode_text(
                        open_clip.get_tokenizer("ViT-L-14")([prompt]).to(self._device)
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
        finally:
            # 评估完成后立即释放模型
            self._release_model()

    def _interpret_score(self, score: float) -> str:
        """Interpret CLIP score."""
        if score >= 0.7:
            return "consistent"
        elif score <= 0.5:
            return "inconsistent"
        else:
            return "ambiguous"


clip_evaluator = CLIPEvaluator()

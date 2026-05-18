"""ComfyUI client for Qwen VL workflow integration."""

import asyncio
import json
from typing import Optional, Dict, Any
from io import BytesIO
import base64

import httpx

from src.config import settings
from src.utils.logger import logger


class ComfyUIClient:
    """Client for ComfyUI Qwen VL workflow."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.comfyui_url,
                timeout=settings.comfyui_timeout,
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate_description(
        self,
        image_source: str,
    ) -> str:
        """Generate structured description using Qwen VL via ComfyUI workflow.
        
        Returns:
            Structured description of the image content.
        """
        if not self._client:
            await self.initialize()

        try:
            prompt_id = await self._submit_workflow(image_source)
            result = await self._wait_for_result(prompt_id)
            
            description = self._extract_description(result)
            logger.info(f"Generated description: {description[:100]}...")
            
            return description

        except Exception as e:
            logger.error(f"ComfyUI description generation failed: {e}")
            raise

    async def _submit_workflow(self, image_source: str) -> str:
        """Submit image description workflow to ComfyUI."""
        image_data = await self._prepare_image(image_source)
        
        workflow = {
            "3": {
                "class_type": "UploadImage",
                "inputs": {
                    "image": image_data,
                    "upload_method": "base64",
                }
            },
            "4": {
                "class_type": "QwenVLProcessor",
                "inputs": {
                    "image_node": "3",
                    "prompt": "请详细描述这张图片的内容，包括主体、场景、风格、颜色等要素。",
                }
            },
            "5": {
                "class_type": "PrimitiveNode",
                "inputs": {
                    "value": "",
                }
            }
        }

        response = await self._client.post("/prompt", json={"prompt": workflow})
        response.raise_for_status()
        data = response.json()
        
        return data.get("prompt_id", "")

    async def _wait_for_result(self, prompt_id: str) -> Dict[str, Any]:
        """Wait for workflow completion and return result."""
        history_url = f"/history/{prompt_id}"
        
        for _ in range(settings.comfyui_timeout // 2):
            await asyncio.sleep(2)
            
            response = await self._client.get(history_url)
            if response.status_code == 200:
                data = response.json()
                if prompt_id in data:
                    return data[prompt_id]
        
        raise TimeoutError(f"ComfyUI workflow timed out: {prompt_id}")

    async def _prepare_image(self, image_source: str) -> str:
        """Prepare image data for ComfyUI."""
        if image_source.startswith("http://") or image_source.startswith("https://"):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_source)
                response.raise_for_status()
                image_bytes = response.content
        else:
            image_bytes = base64.b64decode(image_source)
        
        return base64.b64encode(image_bytes).decode("utf-8")

    def _extract_description(self, result: Dict[str, Any]) -> str:
        """Extract description from workflow result."""
        outputs = result.get("outputs", {})
        for node_id, output in outputs.items():
            if "text" in output:
                return output["text"]
            if "ui" in output:
                ui_content = output["ui"]
                if isinstance(ui_content, list) and len(ui_content) > 0:
                    if isinstance(ui_content[0], dict) and "text" in ui_content[0]:
                        return ui_content[0]["text"]
        
        return "无法生成描述"


comfyui_client = ComfyUIClient()

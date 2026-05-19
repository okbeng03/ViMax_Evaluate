"""ComfyUI client for Qwen VL workflow integration."""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import base64
import random

import httpx

from src.config import settings
from src.utils.logger import logger
from src.services.image_loader import image_loader

max_noise = 2**50 - 1

class ComfyUIClient:
    """Client for ComfyUI Qwen VL workflow."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._workflows: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize HTTP client and load workflows."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.comfyui_url,
                timeout=settings.comfyui_timeout,
            )
        await self._load_workflows()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _load_workflows(self) -> None:
        """Load all workflow JSON files from the workflows directory."""
        workflow_dir = Path(settings.comfyui_workflow_dir)
        
        if not workflow_dir.exists():
            logger.warning(f"Workflow directory not found: {workflow_dir}")
            return
        
        for workflow_file in workflow_dir.glob("*.json"):
            try:
                with open(workflow_file, "r", encoding="utf-8") as f:
                    workflow_data = json.load(f)
                    workflow_name = workflow_file.stem
                    self._workflows[workflow_name] = workflow_data
                    logger.info(f"Loaded workflow: {workflow_name}")
            except Exception as e:
                logger.error(f"Failed to load workflow {workflow_file}: {e}")

    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a loaded workflow by name."""
        return self._workflows.get(name)

    def list_workflows(self) -> List[str]:
        """List all available workflow names."""
        return list(self._workflows.keys())

    async def generate_description(
        self,
        image_source: str,
        workflow_name: str = "qwen_vl",
        custom_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured description using Qwen VL via ComfyUI workflow.
        
        Args:
            image_source: Image source (URL, base64, or hash_id).
            workflow_name: Name of the workflow to use (without .json extension).
            custom_prompt: Optional custom prompt to override workflow default.
        
        Returns:
            Structured description of the image content.
        """
        if not self._client:
            await self.initialize()

        try:
            prompt_id = await self._submit_workflow(
                image_source,
                workflow_name,
                custom_prompt,
            )
            result = await self._wait_for_result(prompt_id)
            
            description = self._extract_description(result)
            logger.info(f"Generated description: {description[:100]}...")
            
            return description

        except Exception as e:
            logger.error(f"ComfyUI description generation failed: {e}")
            raise

    async def _submit_workflow(
        self,
        image_source: str,
        workflow_name: str,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Submit workflow to ComfyUI with replaced values."""
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found. Available: {self.list_workflows()}")
        
        # 上传图片到 ComfyUI 获取 image_name
        image_name = await self._upload_image(image_source)
        logger.info(f"Image uploaded to ComfyUI: {image_name}")
        
        # 替换工作流中的变量
        workflow = self._replace_workflow_vars(workflow, image_name)

        response = await self._client.post("/prompt", json={"prompt": workflow})
        response.raise_for_status()
        data = response.json()
        
        return data.get("prompt_id", "")

    def _replace_workflow_vars(
        self,
        workflow: Dict[str, Any],
        image_name: str,
    ) -> Dict[str, Any]:
        """Replace variables in workflow with actual values.
        
        qwen_vl.json workflow structure:
            Node "1" (LoadImage): sets image path/filename
            Node "2" (AILab_QwenVL): takes image from node 1, sets model params
            Node "5" (PreviewAny): preview output
        """
        import copy
        workflow = copy.deepcopy(workflow)
        
        workflow["1"]["inputs"]["image"] = image_name

        # TODO:: random seed
        # random.randint(1, max_noise)
        
        return workflow

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

    async def _upload_image(self, image_source: str) -> str:
        """Upload image to ComfyUI and return the image name.
        
        Args:
            image_source: Image source (URL, base64, or hash_id).
        
        Returns:
            Image name as stored in ComfyUI.
        """
        image = await image_loader.load(image_source)
        buffer = __import__("io").BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        
        files = {"image": (f"{uuid.uuid4()}.png", image_bytes, "image/png")}
        
        response = await self._client.post("/upload/image", files=files)
        response.raise_for_status()
        data = response.json()
        
        # ComfyUI 返回格式: {"name": "xxx.png", "type": "input"}
        image_name = data.get("name", "")
        if not image_name:
            raise ValueError(f"Failed to upload image: {data}")
        
        return image_name

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

"""ComfyUI client for Qwen VL workflow integration."""

import os
import json
import shutil
import asyncio
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import base64
import random
import uuid
import re

import httpx
import websockets

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
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Generate structured description using Qwen VL via ComfyUI workflow.
        
        Args:
            image_source: Image source (URL, base64, or hash_id).
            workflow_name: Name of the workflow to use (without .json extension).
            custom_prompt: Optional custom prompt to override workflow default.
            progress_callback: Optional callback for progress updates.
        
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
            result = await self._wait_for_result(prompt_id, progress_callback)
            
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
        
        # 根据 image_source 类型处理
        if self._is_hash_id(image_source):
            # hash_id 是 filename_prefix，需要找到 output 目录中的实际文件并复制到 input
            image_name = await self._prepare_hash_id_image(image_source)
        else:
            # 其他类型 (URL, base64) 通过上传接口处理
            image_name = await self._upload_image(image_source)
        
        logger.info(f"Image prepared for workflow: {image_name}")
        
        # 替换工作流中的变量
        workflow = self._replace_workflow_vars(workflow, image_name)

        response = await self._client.post("/prompt", json={"prompt": workflow})
        response.raise_for_status()
        data = response.json()
        
        return data.get("prompt_id", "")

    def _is_hash_id(self, value: str) -> bool:
        """Check if value is a hash_id (UUID format without extension)."""
        if not value:
            return False
        # hash_id 是 UUID 格式，没有扩展名
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(_\d+)?$'
        return bool(re.match(uuid_pattern, value, re.IGNORECASE))

    async def _prepare_hash_id_image(self, hash_id: str) -> str:
        """Find output image by hash_id prefix and copy to input directory.
        
        Args:
            hash_id: Image hash_id (filename_prefix), e.g., "ede480c0-ba42-4ab6-b970-929a65671505"
        
        Returns:
            Filename to use in workflow (copied to input folder).
        """
        # 1. 在 output 目录中查找匹配的文件
        output_path = Path(settings.comfyui_output_dir)
        if not output_path.exists():
            raise FileNotFoundError(f"ComfyUI output directory not found: {output_path}")
        
        # 查找以 hash_id 开头的文件
        pattern = f"{hash_id}_*.png"
        matching_files = list(output_path.glob(pattern))
        
        if not matching_files:
            # 也尝试不带下划线的模式
            pattern = f"{hash_id}*"
            matching_files = [f for f in output_path.glob(pattern) if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.gif']]
        
        if not matching_files:
            raise FileNotFoundError(
                f"Image with hash_id prefix '{hash_id}' not found in {output_path}. "
                f"Expected pattern: {hash_id}_*.png"
            )
        
        # 使用最新的文件（如果有多个）
        source_file = max(matching_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Found output image: {source_file.name}")
        
        # 2. 复制到 input 目录
        input_path = Path(settings.comfyui_input_dir)
        input_path.mkdir(parents=True, exist_ok=True)
        
        # 使用源文件名（ComfyUI 会从这个名称加载）
        dest_file = input_path / source_file.name
        
        # 如果目标文件已存在且相同，跳过复制
        if not dest_file.exists() or dest_file.stat().st_size != source_file.stat().st_size:
            shutil.copy2(source_file, dest_file)
            logger.info(f"Copied image to input: {dest_file}")
        
        return source_file.name

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
        workflow["14"]["inputs"]["seed"] = random.randint(1, max_noise)
        
        return workflow

    async def _wait_for_result(
        self,
        prompt_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Wait for workflow completion using WebSocket and return result.
        
        Args:
            prompt_id: The prompt ID returned from workflow submission.
            progress_callback: Optional callback to receive progress updates.
        
        Returns:
            Workflow execution result.
        """
        ws_url = settings.comfyui_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws"
        
        try:
            async with websockets.connect(ws_url, ping_timeout=None) as ws:
                # 订阅指定的 prompt_id
                subscribe_msg = {
                    "type": "subscribe",
                    "data": {"prompt_id": prompt_id}
                }
                await ws.send(json.dumps(subscribe_msg))
                logger.info(f"WebSocket subscribed to prompt_id: {prompt_id}")
                
                executed_nodes = set()
                final_result = None
                last_progress = {"percent": 0}
                
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=settings.comfyui_timeout)
                        data = json.loads(message)
                        
                        msg_type = data.get("type", "")
                        
                        # 处理执行中状态
                        if msg_type == "executing":
                            node_data = data.get("data", {})
                            node_id = node_data.get("node")
                            if node_id:
                                executed_nodes.add(node_id)
                                progress_info = {
                                    "type": "executing",
                                    "node": node_id,
                                    "executed_nodes": len(executed_nodes),
                                }
                                logger.debug(f"Executing node: {node_id}")
                                if progress_callback:
                                    progress_callback(progress_info)
                        
                        # 处理进度信息
                        elif msg_type == "progress":
                            progress_data = data.get("data", {})
                            value = progress_data.get("value", 0)
                            max_value = progress_data.get("max", 100)
                            percent = int(value / max_value * 100) if max_value > 0 else 0
                            last_progress = {
                                "type": "progress",
                                "value": value,
                                "max": max_value,
                                "percent": percent,
                            }
                            logger.info(f"Progress: {percent}%")
                            if progress_callback:
                                progress_callback(last_progress)
                        
                        # 处理节点执行完成
                        elif msg_type == "executed":
                            node_data = data.get("data", {})
                            node_id = node_data.get("node")
                            output = node_data.get("output", {})
                            progress_info = {
                                "type": "executed",
                                "node": node_id,
                                "executed_nodes": len(executed_nodes),
                            }
                            logger.info(f"Node executed: {node_id}")
                            if progress_callback:
                                progress_callback(progress_info)
                        
                        # 处理工作流完成
                        elif msg_type == "executed":
                            result_data = data.get("data", {})
                            if "output" in result_data:
                                final_result = result_data["output"]
                                break
                        
                        # 处理完成状态
                        elif msg_type == "status":
                            status_data = data.get("data", {})
                            status_obj = status_data.get("status", {})
                            if status_obj.get("completed", False):
                                break
                    
                    except asyncio.TimeoutError:
                        raise TimeoutError(f"ComfyUI workflow timed out: {prompt_id}")
        
        except websockets.exceptions.WebSocketException as e:
            logger.warning(f"WebSocket error, falling back to HTTP polling: {e}")
            return await self._poll_for_result(prompt_id)
        
        # 通过 HTTP 获取最终结果
        if final_result is None:
            history_url = f"/history/{prompt_id}"
            response = await self._client.get(history_url)
            if response.status_code == 200:
                data = response.json()
                if prompt_id in data:
                    final_result = data[prompt_id]
        
        if final_result is None:
            raise TimeoutError(f"ComfyUI workflow timed out: {prompt_id}")
        
        return final_result

    async def _poll_for_result(self, prompt_id: str) -> Dict[str, Any]:
        """Fallback polling method when WebSocket is unavailable."""
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

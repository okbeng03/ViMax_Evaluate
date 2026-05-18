"""Image loader service supporting multiple image sources."""

import os
import re
from pathlib import Path
from typing import Optional
from io import BytesIO

import httpx
from PIL import Image

from src.config import settings
from src.utils.logger import logger


class ImageLoader:
    """Load images from various sources: URL, base64, or ComfyUI output by hash_id."""

    # 支持的图片扩展名
    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp"]

    async def load(self, image_source: str) -> Image.Image:
        """Load image from any supported source.
        
        Args:
            image_source: Can be:
                - URL (http:// or https://)
                - Base64 encoded image data
                - Hash ID (looks for file in ComfyUI output directory)
        
        Returns:
            PIL Image in RGB format.
        
        Raises:
            ValueError: If image source format is invalid or not found.
        """
        if image_source.startswith("http://") or image_source.startswith("https://"):
            return await self._load_from_url(image_source)
        elif self._is_base64(image_source):
            return self._load_from_base64(image_source)
        else:
            # 尝试作为 hash_id 处理
            return await self._load_from_hash_id(image_source)

    async def _load_from_url(self, url: str) -> Image.Image:
        """Load image from URL."""
        logger.info(f"Loading image from URL: {url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")

    def _load_from_base64(self, data: str) -> Image.Image:
        """Load image from base64 data."""
        logger.info("Loading image from base64 data")
        image_data = data.encode("utf-8") if isinstance(data, str) else data
        return Image.open(BytesIO(image_data)).convert("RGB")

    def _is_base64(self, data: str) -> bool:
        """Check if string looks like base64 image data."""
        if len(data) < 100:
            return False
        # 检查是否包含 base64 特征字符
        base64_pattern = re.compile(r'^[A-Za-z0-9+/=]+$')
        return bool(base64_pattern.match(data[:100]))

    async def _load_from_hash_id(self, hash_id: str) -> Image.Image:
        """Load image from ComfyUI output directory by hash_id.
        
        The hash_id is matched against filenames in the output directory,
        supporting filenames like: {hash_id}.png, {hash_id}_0001.png, etc.
        """
        output_dir = Path(settings.comfyui_output_dir)
        
        if not output_dir.exists():
            raise ValueError(f"ComfyUI output directory not found: {output_dir}")
        
        logger.info(f"Searching for image with hash_id '{hash_id}' in {output_dir}")
        
        # 查找匹配的文件
        for ext in self.SUPPORTED_EXTENSIONS:
            # 精确匹配
            exact_path = output_dir / f"{hash_id}{ext}"
            if exact_path.exists():
                logger.info(f"Found exact match: {exact_path}")
                return Image.open(exact_path).convert("RGB")
            
            # 前缀匹配 (用于 _0001, _0002 等编号文件)
            prefix_path = output_dir / f"{hash_id}_{ext}"
            if prefix_path.exists():
                logger.info(f"Found prefix match: {prefix_path}")
                return Image.open(prefix_path).convert("RGB")
        
        # 模糊匹配 - 查找以 hash_id 开头的文件
        matching_files = list(output_dir.glob(f"{hash_id}*"))
        if matching_files:
            # 取最新修改的文件
            latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
            if latest_file.is_file():
                logger.info(f"Found fuzzy match: {latest_file}")
                return Image.open(latest_file).convert("RGB")
        
        raise ValueError(
            f"Image not found for hash_id '{hash_id}' in {output_dir}. "
            f"Supported extensions: {', '.join(self.SUPPORTED_EXTENSIONS)}"
        )


image_loader = ImageLoader()

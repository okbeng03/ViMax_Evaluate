"""Llama server lifecycle manager for controlling llama.cpp server process."""

import asyncio
import subprocess
import signal
import time
from typing import Optional
from pathlib import Path

from src.config import settings
from src.utils.logger import logger


class LlamaServer:
    """Manages the llama.cpp server lifecycle - start on demand, stop after evaluation."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._start_time: Optional[float] = None
        self._is_running: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        """Check if server is currently running."""
        return self._is_running and self._process is not None and self._process.poll() is None

    @property
    def base_url(self) -> str:
        """Get the server base URL."""
        return settings.llm_base_url.rstrip("/v1").rstrip("/")

    async def start(self, timeout: int = 60) -> bool:
        """Start the llama.cpp server.
        
        Args:
            timeout: Maximum seconds to wait for server to be ready.
            
        Returns:
            True if server started successfully, False otherwise.
        """
        async with self._lock:
            if self.is_running:
                logger.info("Llama server already running")
                return True

            if self._process is not None and self._process.poll() is not None:
                # Process exists but died, clean up
                self._process = None
                self._is_running = False

            try:
                logger.info("Starting llama.cpp server...")
                
                # Build command
                cmd = [
                    settings.llama_server_path,
                    "-m", settings.llama_model_path,
                    "-c", str(settings.llama_context_size),
                    "--port", str(settings.llama_port),
                    "-ngl", str(settings.llama_n_gpu_layers),
                ]
                
                # Add optional flags
                if settings.llama_n_threads:
                    cmd.extend(["-t", str(settings.llama_n_threads)])
                if settings.llama_n_parallel:
                    cmd.extend(["-np", str(settings.llama_n_parallel)])
                if settings.llama_flash_attention:
                    cmd.append("--flash-attention")

                logger.info(f"Running: {' '.join(cmd)}")

                # Start process
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                
                self._start_time = time.time()
                self._is_running = True

                # Wait for server to be ready
                if await self._wait_for_server(timeout):
                    uptime = time.time() - self._start_time
                    logger.info(f"Llama server started successfully in {uptime:.1f}s")
                    return True
                else:
                    logger.error("Llama server failed to start within timeout")
                    await self.stop()
                    return False

            except Exception as e:
                logger.error(f"Failed to start llama server: {e}")
                await self.stop()
                return False

    async def stop(self) -> None:
        """Stop the llama.cpp server."""
        async with self._lock:
            if self._process is None:
                self._is_running = False
                return

            try:
                logger.info("Stopping llama.cpp server...")
                
                if self._process.poll() is None:
                    # Try graceful shutdown first
                    self._process.send_signal(signal.SIGTERM)
                    
                    try:
                        await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None, self._process.wait, 5
                            ),
                            timeout=5
                        )
                    except asyncio.TimeoutError:
                        # Force kill if graceful shutdown fails
                        logger.warning("Graceful shutdown timed out, forcing kill")
                        self._process.kill()
                        self._process.wait()

                # Read remaining output
                try:
                    remaining_output = self._process.stdout.read()
                    if remaining_output:
                        logger.debug(f"Server output: {remaining_output[:500]}")
                except:
                    pass

                self._process = None
                self._is_running = False
                
                if self._start_time:
                    uptime = time.time() - self._start_time
                    logger.info(f"Llama server stopped (uptime: {uptime:.1f}s)")
                    self._start_time = None

            except Exception as e:
                logger.error(f"Error stopping llama server: {e}")
                self._process = None
                self._is_running = False

    async def restart(self) -> bool:
        """Restart the server."""
        await self.stop()
        await asyncio.sleep(1)  # Brief pause before restart
        return await self.start()

    async def _wait_for_server(self, timeout: int) -> bool:
        """Wait for server to respond to health check."""
        import httpx

        health_url = f"{self.base_url}/health"
        start = time.time()

        while time.time() - start < timeout:
            if self._process and self._process.poll() is not None:
                # Process died
                return False

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(health_url)
                    if response.status_code == 200:
                        return True
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

            await asyncio.sleep(1)

        return False

    async def get_server_info(self) -> dict:
        """Get server information."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/info")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to get server info: {e}")
        
        return {}


# Global instance
llama_server = LlamaServer()

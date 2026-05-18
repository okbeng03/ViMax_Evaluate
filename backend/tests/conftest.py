"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def anyio_backend():
    """Configure anyio backend for pytest-asyncio."""
    return "asyncio"

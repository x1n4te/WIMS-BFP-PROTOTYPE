import pytest_asyncio
import redis.asyncio as aioredis
import os

@pytest_asyncio.fixture(autouse=True)
async def flush_rate_limits():
    """Ensure each test starts with a clean bucket."""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    r = aioredis.from_url(redis_url)
    # The tests use MOCK_IP = "192.168.1.1"
    await r.delete("rate_limit:192.168.1.1")
    await r.aclose()

import os
import pytest

from dotenv import load_dotenv

load_dotenv()  # Load .env for local test runs against Docker containers

# =============================================================================
# Pytest markers
# =============================================================================
# Register custom markers so pytest -m <marker> works reliably.
# CI uses these to select fast test subsets vs. integration-heavy suites.

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests that do not require Docker services")
    config.addinivalue_line("markers", "integration: Integration tests requiring Docker services (postgres, redis)")
    config.addinivalue_line("markers", "requires_keycloak: Tests that require Keycloak to be running")
    config.addinivalue_line("markers", "requires_docker: Tests that require Docker containers to be running")
    config.addinivalue_line("markers", "slow: Tests that take >5s to run")

# =============================================================================
# Rate-limit flushing
# =============================================================================

try:
    import pytest_asyncio
    import redis.asyncio as aioredis

    @pytest_asyncio.fixture(autouse=True)
    async def flush_rate_limits():
        """Ensure each test starts with a clean Redis bucket."""
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            client = await aioredis.from_url(redis_url, decode_responses=True)
            await client.flushdb()
            await client.aclose()
        except Exception:
            pass  # CI environments without Redis skip silently

except ImportError:
    @pytest.fixture(autouse=True)
    def flush_rate_limits():
        """No-op when pytest_asyncio/redis not installed."""
        return None
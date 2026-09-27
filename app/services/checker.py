import time

import httpx

from app.services.url_security import UnsafeURL, validate_public_url


async def check_url(url: str) -> dict:
    start_time = time.perf_counter()

    try:
        await validate_public_url(url)

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, trust_env=False) as client:
            response = await client.get(url)

        response_time_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "is_up": 200 <= response.status_code < 400,
        }

    except (UnsafeURL, httpx.RequestError):
        response_time_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "status_code": None,
            "response_time_ms": response_time_ms,
            "is_up": False,
        }

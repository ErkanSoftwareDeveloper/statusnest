import time

import httpx


async def check_url(url: str) -> dict:
    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

        elapsed = time.perf_counter() - start_time

        return {
            "status_code": response.status_code,
            "response_time_ms": int(elapsed * 1000),
            "is_up": 200 <= response.status_code < 500,
        }

    except httpx.RequestError:
        elapsed = time.perf_counter() - start_time

        return {
            "status_code": None,
            "response_time_ms": int(elapsed * 1000),
            "is_up": False,
        }

import pytest

from app.services.url_security import UnsafeURL, validate_public_url


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://localhost",
        "http://10.0.0.1",
        "http://192.168.1.1",
        "http://169.254.169.254",
        "http://[::1]",
    ],
)
async def test_blocks_private_and_local_addresses(url):
    with pytest.raises(UnsafeURL):
        await validate_public_url(url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "file:///etc/passwd",
        "http://user:password@example.com",
    ],
)
async def test_blocks_unsafe_url_formats(url):
    with pytest.raises(UnsafeURL):
        await validate_public_url(url)


@pytest.mark.asyncio
async def test_allows_public_url():
    await validate_public_url("https://example.com")

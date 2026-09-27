import asyncio
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURL(ValueError):
    pass


async def validate_public_url(url: str) -> None:
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise UnsafeURL("Invalid URL") from exc

    if parsed.scheme not in {"http", "https"}:
        raise UnsafeURL("Only HTTP and HTTPS URLs are allowed")

    if not parsed.hostname:
        raise UnsafeURL("URL must contain a hostname")

    if parsed.username is not None or parsed.password is not None:
        raise UnsafeURL("URLs with credentials are not allowed")

    hostname = parsed.hostname.rstrip(".").lower()

    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafeURL("Localhost is not allowed")

    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeURL("Invalid port") from exc

    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    try:
        direct_ip = ipaddress.ip_address(hostname)
        addresses = {direct_ip}

    except ValueError:
        try:
            address_info = await asyncio.to_thread(
                socket.getaddrinfo,
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise UnsafeURL("Hostname could not be resolved") from exc

        addresses = {
            ipaddress.ip_address(info[4][0].split("%")[0])
            for info in address_info
        }

    if not addresses:
        raise UnsafeURL("Hostname resolved to no addresses")

    for address in addresses:
        if not address.is_global or address.is_multicast:
            raise UnsafeURL(
                f"Non-public address is not allowed: {address}"
            )

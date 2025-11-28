import asyncio
import logging

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.common_types import Link
from core.config import NETWORK_ERRORS

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(NETWORK_ERRORS),
)
async def get_file_size(
    url: Link, session: ClientSession, timeout: ClientTimeout | None = None
) -> int:
    """Get info about file size in bytes from header."""
    try:
        return await _try_get_file_size(url, session, timeout)

    except asyncio.TimeoutError:
        logger.exception(
            "Too much time to get content size. Retry or check your connection."
        )
        raise


async def _try_get_file_size(
    url: Link, session: ClientSession, timeout: ClientTimeout | None = None
) -> int:
    async with session.head(url, timeout=timeout) as resp:
        return _extract_file_size_from_response(resp)


def _extract_file_size_from_response(response: ClientResponse) -> int:
    try:
        return int(response.headers["Content-Length"])

    except KeyError:
        logger.exception(
            "Unable to get file size. 'Content-Length' header does not exist"
        )
        raise

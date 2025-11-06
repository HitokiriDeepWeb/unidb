from asyncio import Semaphore
from typing import ClassVar

from aiohttp import ClientTimeout


class DownloadConfig:
    """
    Central configuration class for download.

    CHUNK_SIZE - size of the chunk for streaming downloads (bytes).

    HEAD_REQUEST_TIMEOUT - timeout for HEAD request.

    LARGE_FILE_TIMEOUT - timeout to download huge files.

    SMALL_FILE_TIMEOUT - timeout to download regular files.

    NCBI_CONNECTIONS - simultaneous connection limit for NCBI FTP site.

    UNIPROT_SMALL_FILES_CONNECTIONS - connections for UniProt small files download.

    UNIPROT_LARGE_FILES_CONNECTIONS - simultaneous connection limit for UniProt.
    large file download from FTP site.

    MAX_CONNECTIONS - global connection pool size.
    Must be >= (NCBI_CONNECTIONS + UNIPROT_CONNECTIONS).

    GRACEFUL_SHUTDOWN_DELAY - delay to close SSL connections.
    """

    CHUNK_SIZE: ClassVar[int] = 2**20
    HEAD_REQUEST_TIMEOUT: ClassVar[ClientTimeout] = ClientTimeout(total=60)
    LARGE_FILE_TIMEOUT: ClassVar[ClientTimeout] = ClientTimeout(total=3600 * 2)
    SMALL_FILE_TIMEOUT: ClassVar[ClientTimeout] = ClientTimeout(total=300)
    UNIPROT_LARGE_FILES_CONNECTIONS: ClassVar[int] = 18
    UNIPROT_SMALL_FILES_CONNECTIONS: ClassVar[int] = 2
    NCBI_CONNECTIONS: ClassVar[int] = 1
    MAX_CONNECTIONS: ClassVar[int] = (
        UNIPROT_LARGE_FILES_CONNECTIONS
        + UNIPROT_SMALL_FILES_CONNECTIONS
        + NCBI_CONNECTIONS
    )
    SEMAPHORE: ClassVar[Semaphore] = Semaphore(MAX_CONNECTIONS)
    GRACEFUL_SHUTDOWN_DELAY: ClassVar[float] = 0.250

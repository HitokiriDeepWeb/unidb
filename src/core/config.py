import asyncio
from asyncio import Semaphore
from enum import StrEnum
from pathlib import Path

import aiohttp
from aiohttp import ClientTimeout

from core.common_types import Link
from domain.entities import BASE_DIR

# Donwload config

# Size of the chunk for streaming downloads (bytes).
CHUNK_SIZE: int = 2**20

HEAD_REQUEST_TIMEOUT: ClientTimeout = ClientTimeout(total=60)

LARGE_FILE_TIMEOUT: ClientTimeout = ClientTimeout(total=3600 * 2)

SMALL_FILE_TIMEOUT: ClientTimeout = ClientTimeout(total=300)

# Simultaneous connection limit for UniProt large file download from FTP site.
UNIPROT_LARGE_FILES_CONNECTIONS: int = 18

# Connection limit for UniProt small files download.
UNIPROT_SMALL_FILES_CONNECTIONS: int = 2

# Simultaneous connection limit for NCBI FTP site.
NCBI_CONNECTIONS: int = 1

# Global connection pool size. Must be >= (NCBI_CONNECTIONS + UNIPROT_CONNECTIONS).
MAX_CONNECTIONS: int = (
    UNIPROT_LARGE_FILES_CONNECTIONS + UNIPROT_SMALL_FILES_CONNECTIONS + NCBI_CONNECTIONS
)

# Limit of connections to not disturb FTP servers work.
SEMAPHORE: Semaphore = Semaphore(MAX_CONNECTIONS)

# Delay to close SSL connections.
GRACEFUL_SHUTDOWN_DELAY: float = 0.250

UNIPROT_SP_LINK: Link = Link(
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "current_release/knowledgebase/complete/"
    "uniprot_sprot.fasta.gz"
)
UNIPROT_TR_LINK: Link = Link(
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "current_release/knowledgebase/complete/"
    "uniprot_trembl.fasta.gz"
)
UNIPROT_SP_ISOFORMS_LINK: Link = Link(
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "current_release/knowledgebase/complete/"
    "uniprot_sprot_varsplic.fasta.gz"
)
NCBI_LINK: Link = Link(
    "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz"
)

LAST_MODIFIED_DATE: Path = BASE_DIR / "last_modified.txt"

NETWORK_ERRORS = (
    aiohttp.ClientError,
    asyncio.TimeoutError,
    ConnectionAbortedError,
    aiohttp.ClientConnectionError,
)


# File names that must be extracted / prepared.
class NCBIFiles(StrEnum):
    RANKS = "nodes.dmp"
    NAMES = "names.dmp"
    LINEAGE = "taxidlineage.dmp"
    MERGED = "merged.dmp"
    DELNODES = "delnodes.dmp"


class UniprotFiles(StrEnum):
    SWISS_PROT = "uniprot_sprot.fasta"
    SP_ISOFORMS = "uniprot_sprot_varsplic.fasta"
    TREMBL = "uniprot_trembl.fasta"

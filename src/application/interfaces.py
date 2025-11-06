from abc import abstractmethod
from collections.abc import Iterator
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from core.interfaces import StringKeyMapping
from domain.models import ChunkRange


class DatabaseConnectorProtocol(Protocol):
    """Connector which creates pool of connections to database."""

    @abstractmethod
    def open_pool(self, config: StringKeyMapping) -> AbstractAsyncContextManager[Any]:
        pass


class UniprotLifecycleProtocol(Protocol):
    """Set of UniProt database operations which together constitute its lifecycle."""

    @abstractmethod
    async def execute_database_operations_before_copy(self, pool: Any) -> None:
        """Execute queries that will prepare database environment for data copy."""
        pass

    @abstractmethod
    async def execute_database_operations_after_copy(self, pool: Any) -> None:
        """
        Execute queries that will create required constraints and indexes
        after all data was copied.
        """

    @abstractmethod
    async def reset_database(self, pool: Any) -> None:
        """
        Execute queries that will clean uniprot database tables if it was set up before.
        """
        pass

    @abstractmethod
    async def remove_database(self, pool: Any) -> None:
        """Remove database after unsuccessful setup attempt."""
        pass


class ChunkRangeIteratorProtocol(Protocol):
    """
    Iterate over file and create a set of chunk ranges that will split it appropriately.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[ChunkRange]:
        pass


class DownloaderProtocol(Protocol):
    @abstractmethod
    async def download_files(self) -> None:
        """Download all the required files."""
        pass


class UpdateCheckerProtocol(Protocol):
    """Find and save information about update."""

    @abstractmethod
    async def need_update(self) -> bool:
        """Checks if database is up to date."""
        pass

    @abstractmethod
    def save_database_update_time(self) -> None:
        """Saves update time locally."""
        pass


class FilePreparerProtocol(Protocol):
    """Prepare all required files to start operate on them."""

    @abstractmethod
    async def prepare_required_files(self, *args: Any, **kwargs: Any) -> None:
        """Execute all the required operations on files to work with them."""
        pass


class SystemPreparerProtocol(Protocol):
    """
    Execute all necessary operations on system to prepare it for UniProt setup.
    And clean it afterwards.
    """

    @abstractmethod
    async def prepare_environment(self) -> None:
        """Prepare system for UniProt setup."""
        pass

    @abstractmethod
    async def delete_unnecessary_files(self) -> None:
        """Clean system after database was set up."""
        pass

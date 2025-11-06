from abc import abstractmethod
from collections.abc import Iterable, Iterator
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from core.interfaces import StringKeyMapping
from domain.entities import (
    LineagePair,
    MergedPair,
    SequenceRecord,
    Tables,
    Taxonomy,
)


class DatabaseCopyAdapterProtocol(Protocol):
    @abstractmethod
    def open_pool(self, config: StringKeyMapping) -> AbstractAsyncContextManager[Any]:
        pass

    @abstractmethod
    async def copy(
        self,
        pool: Any,
        table_name: Tables,
        records: Iterable[Any],
        timeout: float | None = None,
    ) -> None:
        pass

    @abstractmethod
    def prepare_record_for_copy(self, record: object) -> Any:
        """
        Turn records to appropriate form for copy in a particular
        database management system driver.
        """
        pass


class SequenceIteratorProtocol(Protocol):
    @abstractmethod
    def __iter__(self) -> Iterator[SequenceRecord]:
        pass


class NCBIIteratorProtocol(Protocol):
    @abstractmethod
    def __iter__(self) -> Iterator[Taxonomy | LineagePair | MergedPair]:
        pass

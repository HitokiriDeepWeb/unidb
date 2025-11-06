from asyncio import AbstractEventLoop
from asyncio.futures import Future
from collections.abc import Callable, Iterable
from concurrent.futures.process import ProcessPoolExecutor
from functools import partial
from itertools import chain
from threading import Event

from application.interfaces import ChunkRangeIteratorProtocol
from application.models import IteratorToTable
from core.interfaces import StringKeyMapping
from core.utils import process_futures
from domain.entities import Tables
from domain.exceptions import CopyToUniprotDBError
from domain.interfaces import (
    DatabaseCopyAdapterProtocol,
    SequenceIteratorProtocol,
)
from domain.services.batch_copier import BatchCopier
from domain.services.queue_manager import QueueConfig


class DatabaseFileCopier:
    """
    Manage database data copy using BatchCopier.
    Prepares TrEMBL iterators right before copy.
    """

    def __init__(
        self,
        db_adapter: DatabaseCopyAdapterProtocol,
        connection_pool_config: StringKeyMapping,
        queue_config: QueueConfig,
        iterators_to_tables: Iterable[IteratorToTable],
        trembl_iterator: partial[SequenceIteratorProtocol],
        chunk_range_iterator: ChunkRangeIteratorProtocol,
        batch_size: int = 10_000,
    ):
        self._db_adapter = db_adapter
        self._connection_pool_config = connection_pool_config
        self._queue_config = queue_config
        self._iterators_to_tables = iterators_to_tables
        self._trembl_iterator = trembl_iterator
        self._chunk_range_iterator = chunk_range_iterator
        self._batch_size = batch_size

    async def copy(
        self,
        loop: AbstractEventLoop,
        process_pool: ProcessPoolExecutor,
        event: Event,
    ) -> None:
        tasks: list[Future] = []
        callables = self._prepare_copy_file_callables()

        for callable in callables:
            tasks.append(loop.run_in_executor(process_pool, callable))

        await process_futures(tasks, event, CopyToUniprotDBError())

    def _prepare_copy_file_callables(self) -> list[Callable]:
        trembl_iterators_to_tables = self._get_trembl_sequence_iterators_to_table()
        all_iterators_to_tables = list(
            chain(self._iterators_to_tables, trembl_iterators_to_tables)
        )

        copy_callables = []

        for iterator_to_table in all_iterators_to_tables:
            db_copier = BatchCopier(
                db_adapter=self._db_adapter,
                batch_size=self._batch_size,
                connection_pool_config=self._connection_pool_config,
                record_gen=iterator_to_table.iterator,
                queue_config=self._queue_config,
                table_name=iterator_to_table.table,
            )
            copy_callables.append(db_copier.copy_file_in_new_loop)

        return copy_callables

    def _get_trembl_sequence_iterators_to_table(self) -> list[IteratorToTable]:
        """
        Get appropriate iterators that will go through partial TrEMBL data
        and UniProt table that will be populated with this data.

        Impossible to prepare it outside the class because no files are available yet,
        and TrEMBL 'SequenceIterator' uses 'ChunkRange(s)'
        from existing files to be initialized.
        """
        trembl_iterators_to_table = []

        for chunk_range in self._chunk_range_iterator:
            trembl_iterators_to_table.append(
                IteratorToTable(
                    self._trembl_iterator(chunk_range=chunk_range),
                    Tables.UNIPROT,
                )
            )

        return trembl_iterators_to_table

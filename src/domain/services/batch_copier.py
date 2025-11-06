import asyncio
import logging
import os
from typing import Any

from core.exceptions import NeighbouringProcessError
from core.interfaces import StringKeyMapping
from core.utils import is_shutdown_event_set, set_shutdown_event
from domain.entities import Tables
from domain.exceptions import CopyToUniprotDBError
from domain.interfaces import (
    DatabaseCopyAdapterProtocol,
    NCBIIteratorProtocol,
    SequenceIteratorProtocol,
)
from domain.services.queue_manager import AsyncQueueManager, QueueConfig

logger = logging.getLogger(__name__)


class BatchCopier:
    """
    Manages copy of record batches to database tables in multiple processes.
    Uses global shutdown event to coordinate with other processes.
    """

    def __init__(
        self,
        db_adapter: DatabaseCopyAdapterProtocol,
        batch_size: int,
        connection_pool_config: StringKeyMapping,
        record_gen: SequenceIteratorProtocol | NCBIIteratorProtocol,
        queue_config: QueueConfig,
        table_name: Tables,
        timeout: float = 30.0,
    ):
        self._db_adapter = db_adapter
        self._batch_size = batch_size
        self._connection_pool_config = connection_pool_config
        self._record_gen = record_gen
        self._queue_manager = AsyncQueueManager(queue_config)
        self._table_name = table_name
        self._timeout = timeout

    def copy_file_in_new_loop(self) -> None:
        """Copy file chunk records to the database in separate loop."""
        logger.debug("[%s] Starting copy process", os.getpid())

        async def copy_file():
            try:
                await self._enqueue_record_batches()

            except Exception as e:
                set_shutdown_event()
                raise CopyToUniprotDBError from e

        asyncio.run(copy_file())

    async def _enqueue_record_batches(self) -> None:
        records: list[object] = []

        async with (
            self._db_adapter.open_pool(self._connection_pool_config) as db_pool,
            self._queue_manager,
        ):
            for record in self._record_gen:
                records.append(self._db_adapter.prepare_record_for_copy(record))

                if self._appropriate_records_count_reached(records):
                    await self._safe_append_copy_task_to_queue(db_pool, records)
                    records.clear()

            await self._safe_append_copy_task_to_queue(db_pool, records)
            records.clear()

    async def _safe_append_copy_task_to_queue(
        self,
        db_pool: Any,
        records: list[object],
    ) -> None:
        """
        Append copy task to queue if neighboring process did not set shutdown event.
        """
        logger.debug("records: %s", (len(records)))

        if is_shutdown_event_set():
            raise NeighbouringProcessError()

        try:
            await self._try_safe_append_copy_task_to_queue(db_pool, records)

        except Exception as e:
            sample = records[0] if records else "N/A"
            set_shutdown_event()

            raise CopyToUniprotDBError(
                f"Unable to copy records to database. Records sample: {sample}"
            ) from e

    async def _try_safe_append_copy_task_to_queue(
        self,
        db_pool: Any,
        records: list[object],
    ) -> None:
        if records:
            await asyncio.wait_for(
                self._queue_manager.enqueue_task(
                    self._copy_records(db_pool, records.copy())
                ),
                timeout=self._timeout,
            )

    async def _copy_records(self, db_pool: Any, records: list[object]) -> None:
        try:
            await self._db_adapter.copy(
                db_pool, self._table_name, records, self._timeout
            )

        except Exception as e:
            sample = records[0] if records else "N/A"
            logger.exception(
                "Failed to copy %s to table %s. Record sample: %s",
                len(records),
                self._table_name,
                sample,
            )
            set_shutdown_event()
            raise CopyToUniprotDBError(
                f"Failed to copy len(records) to table {self._table_name}.\n"
                f"Record sample: {sample}"
            ) from e

    def _appropriate_records_count_reached(self, records: list[object]) -> bool:
        return len(records) >= self._batch_size

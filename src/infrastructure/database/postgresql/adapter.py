import asyncio
import logging
from collections.abc import AsyncGenerator, Coroutine, Iterable, Iterator
from contextlib import asynccontextmanager
from dataclasses import astuple
from typing import Any

import asyncpg
from asyncpg import Connection, Pool

from core.interfaces import StringKeyMapping
from core.utils import create_tasks, process_tasks
from domain.entities import Tables
from infrastructure.database.common_types import QueryNested
from infrastructure.database.exceptions import (
    ConnectionDatabaseError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)


class PostgreSQLAdapter:
    """Adapter to perform operations in PostgreSQL."""

    @asynccontextmanager
    async def open_pool(self, config: StringKeyMapping) -> AsyncGenerator[Pool]:
        try:
            async with asyncpg.create_pool(**config) as pool:
                yield pool

        except Exception as e:
            logger.exception("Failed to initialize pool")
            raise ConnectionDatabaseError from e

    async def execute_queries_async(self, pool: Pool, queries: QueryNested) -> None:
        """Execute queries concurrently. Order has no importance."""
        coros: list[Coroutine] = [
            self._execute_query(pool, query) for query in self._query_gen(queries)
        ]

        tasks = create_tasks(coros)
        await process_tasks(tasks)

    async def execute_queries_sync(self, pool: Pool, queries: QueryNested) -> None:
        """Execute queries sequentially to preserve order."""
        [await self._execute_query(pool, query) for query in self._query_gen(queries)]

    async def copy(
        self,
        pool: Pool,
        table_name: Tables,
        records: Iterable[tuple],
        timeout: float | None = None,
    ) -> None:
        """Copy records in separate connection from connection pool."""
        async with pool.acquire(timeout=timeout) as conn:
            try:
                await conn.copy_records_to_table(table_name, records=records)

            except Exception:
                logger.exception("Failed to copy to table %s.", table_name)
                raise

    def prepare_record_for_copy(self, record: Any) -> tuple:
        """Turn record to the form appropriate for database copy."""
        return astuple(record)

    async def _execute_single_query_async(
        self, conn: Connection, query: str, timeout: float | None = None
    ) -> None:
        try:
            await asyncio.wait_for(conn.execute(query), timeout=timeout)

        except Exception as e:
            logger.exception("Failed to execute query: \n%s", query)
            raise QueryExecutionError from e

    def _query_gen(self, queries: QueryNested) -> Iterator[str]:
        """Iterate over nested query iterable and yield separate query."""

        if isinstance(queries, str):
            yield queries

        else:
            for query in queries:
                yield from self._query_gen(query)

    async def _execute_query(self, pool: Pool, query: QueryNested) -> None:
        """Execute query in separate connection from connection pool."""
        async with pool.acquire() as conn:
            logger.debug("Executing %s", query)
            return await conn.execute(query)

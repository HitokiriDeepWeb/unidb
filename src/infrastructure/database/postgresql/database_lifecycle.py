import logging
from collections.abc import Callable, Coroutine

from asyncpg import Pool

import infrastructure.database.postgresql.queries as q
from core.utils import create_tasks, process_tasks
from infrastructure.database.postgresql.adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)


class PostgreSQLUniprotLifecycle:
    """
    Set of UniProt database operations appropriate for PostgreSQL
    which together constitute its lifecycle.
    """

    def __init__(self, trgm_required: bool):
        self._trgm_required = trgm_required
        self._db_adapter = PostgreSQLAdapter()

    async def execute_database_operations_before_copy(self, pool: Pool) -> None:
        """Execute queries that will prepare database environment for data copy."""
        operations: list[Callable] = [
            self.remove_database,
            self._prepare_database,
            self._create_tables,
            self._add_comments,
        ]

        [await operation(pool) for operation in operations]

    async def execute_database_operations_after_copy(self, pool: Pool) -> None:
        """Create required constraints and indexes after all data was copied."""
        operations: list[Callable] = [
            self._create_constraints_and_indexes_for_taxonomy_and_lineage,
            self._validate_uniprot_kb_ncbi_ids,
        ]
        if self._trgm_required:
            operations.append(self._create_trgm_index_for_sequence_column)

        [await operation(pool) for operation in operations]

    async def reset_database(self, pool: Pool) -> None:
        """Clean uniprot database if it was set up before"""
        try:
            # Truncate tables if database is being updated.
            await self._execute_reset_operation(pool)
            logger.info("Clear existing tables")

        except Exception:
            logger.error("Failed to clear tables %s", q.RESET_DATABASE_QUERIES)
            pass

    async def remove_database(self, pool: Pool) -> None:
        await self._db_adapter.execute_queries_async(pool, q.REMOVE_DATABASE_QUERIES)

    async def _prepare_database(self, pool: Pool) -> None:
        """
        Make neccessary preparations (create required extensions and types)
        before creating tables.
        """
        await self._db_adapter.execute_queries_async(pool, q.PREPARATION_QUERIES)

    async def _create_tables(self, pool: Pool) -> None:
        """Create required tables."""
        await self._db_adapter.execute_queries_async(pool, q.TABLE_CREATION_QUERIES)

    async def _add_comments(self, pool: Pool) -> None:
        """Add comments to tables and columns."""
        await self._db_adapter.execute_queries_async(pool, q.COMMENT_QUERIES)

    async def _create_constraints_and_indexes_for_taxonomy_and_lineage(
        self, pool: Pool
    ) -> None:
        """Create constraints and indexes for taxonomy and lineage tables."""
        queries = q.CREATE_CONSTRAINTS_AND_IDXS_FOR_TAXONOMY_AND_LINEAGE_QUERIES
        coros: list[Coroutine] = [self._db_adapter.execute_queries_sync(pool, queries)]

        tasks = create_tasks(coros)
        await process_tasks(tasks)

    async def _validate_uniprot_kb_ncbi_ids(self, pool: Pool) -> None:
        """Validate that 'uniprot_kb' and 'taxonomy' tables have the same NCBI ID's."""
        coros: list[Coroutine] = [
            self._db_adapter.execute_queries_sync(
                pool, q.UNIPROT_KB_AND_TAXONOMY_VALIDATION_QUERIES
            )
        ]

        tasks = create_tasks(coros)
        await process_tasks(tasks)

    async def _create_trgm_index_for_sequence_column(self, pool: Pool) -> None:
        await self._db_adapter.execute_queries_sync(
            pool, q.CREATE_TRGM_IDX_ON_UNIPROT_KB
        )

    async def _execute_reset_operation(self, pool) -> None:
        await self._db_adapter.execute_queries_sync(pool, q.RESET_DATABASE_QUERIES)

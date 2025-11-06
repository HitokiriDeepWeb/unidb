from application.interfaces import (
    DatabaseConnectorProtocol,
    UniprotLifecycleProtocol,
)
from core.interfaces import StringKeyMapping


class UniprotOperator:
    """Operate UniProt database lifecycle."""

    def __init__(
        self,
        db_connector: DatabaseConnectorProtocol,
        uniprot_lifecycle: UniprotLifecycleProtocol,
    ):
        self._db_connector = db_connector
        self._uniprot_lifecycle = uniprot_lifecycle

    async def remove_database(self, pool_config: StringKeyMapping) -> None:
        """Remove database after unsuccessful setup attempt."""
        async with self._db_connector.open_pool(pool_config) as pool:
            await self._uniprot_lifecycle.remove_database(pool)

    async def prepare_database_environment(self, pool_config: StringKeyMapping) -> None:
        """Prepare database for data copy."""
        async with self._db_connector.open_pool(pool_config) as pool:
            await self._uniprot_lifecycle.execute_database_operations_before_copy(pool)

    async def reset_database(self, pool_config: StringKeyMapping) -> None:
        """Clean up database tables."""
        async with self._db_connector.open_pool(pool_config) as conn:
            await self._uniprot_lifecycle.reset_database(conn)

    async def finalize_database_setup(self, pool_config: StringKeyMapping) -> None:
        """Execute final queries after all data was copied."""
        async with self._db_connector.open_pool(pool_config) as pool:
            await self._uniprot_lifecycle.execute_database_operations_after_copy(pool)

import asyncpg

from core.interfaces import StringKeyMapping


async def get_available_connections_amount(config: StringKeyMapping) -> int:
    """
    Get available amount of connections in PostgreSQL if user has required rights.
    Otherwise returns default amount of 95 connections.
    """
    conn = await asyncpg.connect(**config)

    get_max_connections_query = "SHOW max_connections"
    get_active_connections_query = "SELECT COUNT(*) FROM pg_stat_activity"
    current_connection = 1

    try:
        max_connections: str = await conn.fetchval(get_max_connections_query)
        active_connections: str = await conn.fetchval(get_active_connections_query)

        # Our current connection will no longer be used so we add it at the end.
        available_connections = (
            int(max_connections) - int(active_connections)
        ) + current_connection

        assert available_connections >= 0
        return available_connections

    except asyncpg.InsufficientPrivilegeError:
        postgresql_default_available_connections = 95
        return postgresql_default_available_connections

    finally:
        await conn.close()

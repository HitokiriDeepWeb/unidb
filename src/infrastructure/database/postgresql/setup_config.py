import os

import asyncpg

from core.interfaces import StringKeyMapping
from domain.services.queue_manager import QueueConfig
from infrastructure.database.postgresql.config import ConnectionPoolConfig


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

    except asyncpg.InsufficientPrivilegeError:
        postgresql_default_available_connections = 95
        return postgresql_default_available_connections

    else:
        return available_connections

    finally:
        await conn.close()


def adjust_workers_by_db_connection_limit(
    desired_workers_number: int, available_connections: int
) -> int:
    """Restrict workers num quantity due to database connection amount limit."""
    cpu_count = _set_system_cpu_number(available_connections)

    if _is_workers_number_valid(
        desired_workers_number, cpu_count, available_connections
    ):
        return desired_workers_number

    elif _can_use_cpu_count(cpu_count, available_connections):
        return cpu_count

    else:
        return available_connections


def setup_connection_pool_config(
    database: str,
    user: str,
    port: int,
    host: str,
    password: str,
    workers_number: int,
    available_connections: int,
) -> ConnectionPoolConfig:
    """Setup database config depending on number of workers provided."""
    min_pool_size, max_pool_size = _adjust_pool_number_by_number_of_workers(
        workers_number, available_connections
    )
    return ConnectionPoolConfig(
        database=database,
        user=user,
        port=port,
        host=host,
        password=password,
        min_size=min_pool_size,
        max_size=max_pool_size,
    )


def setup_queue_config(workers_number: int, available_connections: int) -> QueueConfig:
    """Setup queue config depending on number of workers provided."""
    reserved_workers = 2
    _, queue_max_size = _adjust_pool_number_by_number_of_workers(
        workers_number, available_connections
    )
    queue_workers_number = queue_max_size + reserved_workers
    return QueueConfig(
        queue_max_size=queue_max_size, queue_workers_number=queue_workers_number
    )


def _set_system_cpu_number(available_connections: int) -> int:
    cpu_count = os.cpu_count()
    return cpu_count if cpu_count else available_connections


def _is_workers_number_valid(
    workers_number: int, cpu_count: int, available_connections: int
) -> bool:
    return workers_number <= available_connections and workers_number <= cpu_count


def _can_use_cpu_count(system_cpu_number: int, available_connections: int) -> bool:
    return system_cpu_number <= available_connections


def _adjust_pool_number_by_number_of_workers(
    workers_number: int, available_connections: int
) -> tuple[int, int]:
    max_size = available_connections // workers_number
    min_size = max_size // 2 if max_size > 1 else 1
    return min_size, max_size

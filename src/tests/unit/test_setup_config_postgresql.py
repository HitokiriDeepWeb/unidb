from typing import Any

import pytest

from domain.services.queue_manager import QueueConfig
from infrastructure.database.postgresql import (
    ConnectionPoolConfig,
    setup_connection_pool_config,
    setup_queue_config,
)


@pytest.mark.parametrize(
    "workers_number, expected_result",
    [
        (1, QueueConfig(queue_max_size=95, queue_workers_number=97)),
        (15, QueueConfig(queue_max_size=6, queue_workers_number=8)),
        (30, QueueConfig(queue_max_size=3, queue_workers_number=5)),
    ],
)
def test_setup_queue_config(workers_number: int, expected_result: QueueConfig):
    available_connections = 95

    result = setup_queue_config(workers_number, available_connections)

    assert result == expected_result


@pytest.mark.parametrize(
    "workers_number, expected_result",
    [
        (
            1,
            ConnectionPoolConfig(
                database="test",
                user="test",
                port=5432,
                host="test",
                password="test",
                min_size=47,
                max_size=95,
            ),
        ),
        (
            15,
            ConnectionPoolConfig(
                database="test",
                user="test",
                port=5432,
                host="test",
                password="test",
                min_size=3,
                max_size=6,
            ),
        ),
        (
            30,
            ConnectionPoolConfig(
                database="test",
                user="test",
                port=5432,
                host="test",
                password="test",
                min_size=1,
                max_size=3,
            ),
        ),
    ],
)
def test_setup_database_config(
    workers_number: int, expected_result: ConnectionPoolConfig
):
    default_arguments: dict[str, Any] = dict(
        database="test",
        user="test",
        port=5432,
        host="test",
        password="test",
        available_connections=95,
    )

    result = setup_connection_pool_config(
        **default_arguments, workers_number=workers_number
    )

    assert result == expected_result

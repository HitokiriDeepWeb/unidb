import asyncio

import pytest

from core.exceptions import NeighbouringProcessError
from domain.exceptions import CopyToUniprotDBError
from domain.services.queue_manager import AsyncQueueManager, QueueConfig

TEST_QUEUE_VALUE: int = 5


@pytest.fixture
def test_config() -> QueueConfig:
    return QueueConfig(
        queue_max_size=TEST_QUEUE_VALUE, queue_workers_number=TEST_QUEUE_VALUE
    )


@pytest.fixture
def timeout_config() -> QueueConfig:
    return QueueConfig(
        queue_max_size=TEST_QUEUE_VALUE,
        queue_workers_number=TEST_QUEUE_VALUE,
        task_timeout=0.01,
    )


@pytest.mark.asyncio
async def test_initialization(mocker, test_config: QueueConfig):
    _mock_is_shutdown_event_set_func(mocker, False)

    async with AsyncQueueManager(test_config) as queue_manager:
        assert len(queue_manager._workers) == TEST_QUEUE_VALUE


@pytest.mark.asyncio
async def test_task_processing(mocker, test_config: QueueConfig):
    # Arrange.
    test_values: list[int] = []
    result: list[int] = []
    _mock_is_shutdown_event_set_func(mocker, False)

    async def populate_test_values(number: int) -> None:
        test_values.append(number)

    # Act.
    async with AsyncQueueManager(test_config) as sut:
        for number in range(TEST_QUEUE_VALUE):
            result.append(number)
            await sut.enqueue_task(populate_test_values(number))

    # Assert.
    assert sorted(test_values) == result


@pytest.mark.asyncio
async def test_shutdown_event_true(mocker, test_config: QueueConfig):
    _mock_is_shutdown_event_set_func(mocker, True)
    _mock_shutdown_event_set_func(mocker)

    with pytest.raises(NeighbouringProcessError):
        async with AsyncQueueManager(test_config) as queue_manager:
            for _ in range(TEST_QUEUE_VALUE):
                await queue_manager.enqueue_task(asyncio.sleep(0.1))


@pytest.mark.asyncio
async def test_timeout(mocker, timeout_config: QueueConfig):
    excess_time = 1
    _mock_is_shutdown_event_set_func(mocker, False)

    with pytest.raises(CopyToUniprotDBError):
        async with AsyncQueueManager(timeout_config) as queue_manager:
            await queue_manager.enqueue_task(asyncio.sleep(excess_time))


@pytest.mark.asyncio
async def test_error_propagation(mocker, test_config: QueueConfig):
    # Arrange.
    error_message = "Testing error message propagation"
    _mock_is_shutdown_event_set_func(mocker, False)

    async def test_error_task() -> None:
        raise ValueError(error_message)

    # Act + assert.
    with pytest.raises(CopyToUniprotDBError) as exc_info:
        async with AsyncQueueManager(test_config) as queue_manager:
            await queue_manager.enqueue_task(test_error_task())

    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == error_message


def _mock_shutdown_event_set_func(mocker):
    return mocker.patch(
        "domain.services.queue_manager.queue_manager.set_shutdown_event",
        return_value=None,
    )


def _mock_is_shutdown_event_set_func(mocker, flag: bool):
    return mocker.patch(
        "domain.services.queue_manager.queue_manager.is_shutdown_event_set",
        return_value=flag,
    )

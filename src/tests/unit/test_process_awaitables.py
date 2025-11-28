import asyncio
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from multiprocessing.managers import ListProxy

import pytest

from core.utils import init_shutdown_event, process_futures, process_tasks


class TaskProcessor:
    def append_to_list(self, task_result: ListProxy[int], value: int) -> None:
        task_result.append(value)

    def raise_value_error(self) -> None:
        raise ValueError()

    def empty_function(self) -> None:
        pass


@pytest.mark.asyncio
async def test_process_tasks():
    # Arrange.
    task_result: list[int] = []

    async def append_to_list(value: int) -> None:
        await asyncio.sleep(0.2)
        task_result.append(value)

    expected_result = list(range(10))

    # Act.
    tasks = [asyncio.create_task(append_to_list(value)) for value in range(10)]
    await process_tasks(tasks)

    # Assert.
    assert sorted(task_result) == expected_result


@pytest.mark.asyncio
async def test_process_futures():
    # Arrange.

    with Manager() as manager:
        event = manager.Event()
        task_result = manager.list()
        processor = TaskProcessor()
        workers_number = 1

        with ProcessPoolExecutor(
            max_workers=workers_number,
            initializer=init_shutdown_event,
            initargs=(event,),
        ) as process_pool:
            loop = asyncio.get_running_loop()

            futures = [
                loop.run_in_executor(
                    process_pool, processor.append_to_list, task_result, value
                )
                for value in range(10)
            ]
        expected_result = list(range(10))

        # Act.
        await process_futures(futures, event, ValueError())

        # Assert.
        assert sorted(list(task_result)) == expected_result


@pytest.mark.asyncio
async def test_process_futures_raises_original_error():
    # Arrange.

    with Manager() as manager:
        event = manager.Event()
        processor = TaskProcessor()
        workers_number = 1

        with ProcessPoolExecutor(
            max_workers=workers_number,
            initializer=init_shutdown_event,
            initargs=(event,),
        ) as process_pool:
            loop = asyncio.get_running_loop()

            futures = [loop.run_in_executor(process_pool, processor.raise_value_error)]

        # Act.
        with pytest.raises(ValueError):
            await process_futures(futures, event, KeyError())


@pytest.mark.asyncio
async def test_process_futures_raises_default_error():
    # Arrange.

    with Manager() as manager:
        event = manager.Event()
        event.set()
        processor = TaskProcessor()
        workers_number = 1

        with ProcessPoolExecutor(
            max_workers=workers_number,
            initializer=init_shutdown_event,
            initargs=(event,),
        ) as process_pool:
            loop = asyncio.get_running_loop()

            futures = [loop.run_in_executor(process_pool, processor.empty_function)]

        # Act.
        with pytest.raises(ValueError):
            await process_futures(futures, event, ValueError())

import asyncio

import pytest

from core.utils import process_tasks


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

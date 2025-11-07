import asyncio
import logging
import os
from asyncio import Task
from collections.abc import Coroutine
from typing import Self

from core.exceptions import NeighbouringProcessError
from core.utils import create_tasks, is_shutdown_event_set, set_shutdown_event
from domain.exceptions import CopyToUniprotDBError
from domain.services.queue_manager.config import QueueConfig

logger = logging.getLogger(__name__)


class AsyncQueueManager:
    """
    Asynchronous context manager for task queue processing.
    Uses global shutdown event to coordinate with other processes.
    Manages a queue and worker tasks that execute enqueued operations.
    Handles graceful shutdown and error propagation during task execution.
    """

    def __init__(self, config: QueueConfig):
        self._config = config
        self._record_queue = asyncio.Queue(maxsize=config.queue_max_size)
        self._workers: list[Task] = []
        self._first_exception: Exception | None = None

    async def enqueue_task(self, coro: Coroutine) -> None:
        if self._workers:
            task = asyncio.create_task(coro)

            await asyncio.wait_for(
                self._record_queue.put(task),
                timeout=self._config.task_timeout,
            )

    async def __aenter__(self) -> Self:
        self._workers = self._create_worker_tasks()
        return self

    async def __aexit__(self, *_) -> None:
        logger.debug("[%s] Queue manager exiting", os.getpid())

        if is_shutdown_event_set() or self._first_exception:
            self._shutdown_on_event()

        else:
            await self._graceful_shutdown()

    def _create_worker_tasks(self) -> list[Task]:
        coroutines = [
            self._worker(self._record_queue)
            for _ in range(self._config.queue_workers_number)
        ]

        tasks = create_tasks(coroutines)
        return tasks

    async def _worker(self, queue: asyncio.Queue) -> None:
        worker_id = id(self)

        while True:
            if is_shutdown_event_set():
                raise NeighbouringProcessError

            try:
                task = await queue.get()
                await self._process_queue_task(task, queue)

            except asyncio.CancelledError:
                logger.debug("Worker %s cancelled", worker_id)
                break

            except Exception as e:
                logger.exception("Worker %s failed with exception.", worker_id)

                self._register_error(e)
                set_shutdown_event()
                raise CopyToUniprotDBError from e

        logger.debug("Worker %s exiting", worker_id)

    async def _process_queue_task(self, task: Task, queue: asyncio.Queue):
        try:
            await asyncio.wait_for(task, timeout=self._config.task_timeout)

        except asyncio.TimeoutError as e:
            logger.exception("Task %s was not done due to timeout error", task)
            raise CopyToUniprotDBError from e

        finally:
            queue.task_done()

    def _register_error(self, exception: Exception):
        if self._first_exception is None:
            self._first_exception = exception

    def _shutdown_on_event(self) -> None:
        while not self._record_queue.empty():
            self._record_queue.get_nowait()
            self._record_queue.task_done()

        self._cancel_all_workers()

        if self._first_exception:
            raise NeighbouringProcessError from self._first_exception

        raise NeighbouringProcessError

    async def _graceful_shutdown(self) -> None:
        try:
            await asyncio.wait_for(
                self._record_queue.join(), timeout=self._config.join_timeout
            )

        finally:
            self._cancel_all_workers()

            if self._first_exception:
                raise CopyToUniprotDBError from self._first_exception

    def _cancel_all_workers(self) -> None:
        [worker.cancel() for worker in self._workers]

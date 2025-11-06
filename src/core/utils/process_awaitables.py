from asyncio import FIRST_EXCEPTION, AbstractEventLoop, Task, create_task, wait
from asyncio.futures import Future
from collections.abc import Coroutine, Iterable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from threading import Event

from core.models import FunctionCall


def create_tasks(coros: Iterable[Coroutine]) -> list[Task]:
    return [create_task(coro) for coro in coros]


async def process_futures(
    tasks: list[Future], event: Event, default_exception: Exception
) -> None:
    """
    Handle futures in multiprocessing environment.
    The 'event' is used to terminate futures when neighbouring process failed.
    """
    done, pending = await wait(tasks, return_when=FIRST_EXCEPTION)
    _terminate_on_failure(done, pending, event, default_exception)


async def process_tasks(tasks: list[Task]) -> None:
    done, pending = await wait(tasks, return_when=FIRST_EXCEPTION)
    cancel_on_error(done, pending)


def cancel_on_error(done: set[Task], pending: set[Task]) -> None:
    """Cancel pending task in case of error and raise exception."""
    try:
        for done_task in done:
            if exception := done_task.exception():
                raise exception

    finally:
        for task in pending:
            task.cancel()


def run_futures(
    loop: AbstractEventLoop,
    process_pool: ProcessPoolExecutor,
    callables: Iterable[FunctionCall],
) -> list[Future]:
    partials = _build_partials(callables)
    return [loop.run_in_executor(process_pool, partial) for partial in partials]


def _terminate_on_failure(
    done: set[Future],
    pending: set[Future],
    event: Event,
    default_exception: Exception,
) -> None:
    """Terminate pending futures that did not start working yet and raise exception."""
    exception = _get_flagged_exception(done, event)
    _cancel_pending_tasks(pending)
    _propagate_error_on_condition(exception, event, default_exception)


def _get_flagged_exception(done: set[Future], event: Event) -> BaseException | None:
    exception: BaseException | None = None

    for task in done:
        if exception := task.exception():
            event.set()
            return exception


def _cancel_pending_tasks(pending: set[Future]) -> None:
    [task.cancel() for task in pending]


def _propagate_error_on_condition(
    exception: BaseException | None, event: Event, default_exception: Exception
) -> None:
    if event.is_set():
        if exception:
            raise exception

        raise default_exception


def _build_partials(
    callables: Iterable[FunctionCall],
) -> list[partial]:
    return [
        partial(callable.func, *callable.args, **callable.kwargs)
        for callable in callables
    ]

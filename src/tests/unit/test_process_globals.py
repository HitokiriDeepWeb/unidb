from multiprocessing import Manager

from src.core.utils.process_globals import (
    init_shutdown_event,
    is_shutdown_event_set,
    set_shutdown_event,
)


def test_shutdown_event_is_not_set():
    with Manager() as manager:
        event = manager.Event()
        init_shutdown_event(event)

        assert not is_shutdown_event_set()


def test_shutdown_event_is_set():
    with Manager() as manager:
        event = manager.Event()
        event.set()
        init_shutdown_event(event)

        assert is_shutdown_event_set()


def test_set_shutdown_event():
    with Manager() as manager:
        event = manager.Event()
        init_shutdown_event(event)

        set_shutdown_event()

        assert event.is_set()


def test_global_processing_functions_work_together():
    with Manager() as manager:
        event = manager.Event()
        init_shutdown_event(event)

        set_shutdown_event()

        assert is_shutdown_event_set()

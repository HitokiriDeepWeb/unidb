from threading import Event


def init_shutdown_event(event: Event) -> None:
    """
    Initialize shutdown event that will be sent to every process
    to stop work in case of error.
    """
    global shutdown_event
    shutdown_event = event


def is_shutdown_event_set() -> bool:
    return shutdown_event.is_set()


def set_shutdown_event() -> None:
    shutdown_event.set()

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueConfig:
    queue_max_size: int
    queue_workers_number: int
    task_timeout: float = 1800.0
    join_timeout: float = 1900.0

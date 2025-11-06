from dataclasses import dataclass


@dataclass
class QueueConfig:
    queue_max_size: int
    queue_workers_number: int
    task_timeout: float = 40.0
    join_timeout: float = 50.0

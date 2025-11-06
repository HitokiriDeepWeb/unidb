from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChunkRange:
    start: int
    end: int

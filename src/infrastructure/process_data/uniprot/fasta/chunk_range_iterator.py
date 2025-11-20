from collections.abc import Iterator
from pathlib import Path
from typing import IO

from domain.models import ChunkRange


class ChunkRangeIterator:
    def __init__(self, path_to_file: Path, workers_number: int):
        self._path_to_file = path_to_file
        self._workers_number = workers_number

    def __iter__(self) -> Iterator[ChunkRange]:
        """
        Generate chunk ranges that split FASTA file on parts
        depending on number of workers.
        """
        chunk_boundaries = self._split_file_on_chunks()
        yield from self._ranges_from_boundaries_gen(chunk_boundaries)

    @staticmethod
    def _ranges_from_boundaries_gen(
        chunk_boundaries: list[int],
    ) -> Iterator[ChunkRange]:
        """Generate chunks from boundaries."""
        chunk_boundaries_num = len(chunk_boundaries)

        for index in range(chunk_boundaries_num - 1):
            yield ChunkRange(chunk_boundaries[index], chunk_boundaries[index + 1] - 1)

    def _split_file_on_chunks(self) -> list[int]:
        """Split FASTA file on chunks depending on number of workers."""
        file_size = self._get_file_size()
        chunk_size = self._get_chunk_size(file_size)
        chunk_boundaries = self._get_chunk_boundaries(chunk_size, file_size)

        return chunk_boundaries

    def _get_file_size(self) -> int:
        return self._path_to_file.stat().st_size

    def _get_chunk_size(self, file_size: int) -> int:
        return file_size // self._workers_number

    def _get_chunk_boundaries(self, chunk_size: int, file_size: int) -> list[int]:
        """Return all chunk boundaries gathered together."""
        with self._path_to_file.open("rb") as file:
            chunk_boundaries = self._collect_chunk_offsets(file, file_size, chunk_size)

        # Add end of last chunk.
        chunk_boundaries.append(file_size)
        return chunk_boundaries

    def _collect_chunk_offsets(
        self, file: IO, file_size: int, chunk_size: int
    ) -> list[int]:
        """Append chunks to chunk boundaries and return them."""
        # The first chunk start position is 0.
        chunk_boundaries = [0]
        current_position = chunk_size

        while current_position < file_size:
            self._move_file_position(file, current_position)

            if record_position_boundary := self._get_nearest_record_position(file):
                chunk_boundaries.append(record_position_boundary)
                current_position = record_position_boundary + chunk_size

            else:
                break

        return chunk_boundaries

    @staticmethod
    def _get_nearest_record_position(file: IO) -> int | None:
        """Get nearest record delimiter position from the current line."""
        for line in file:
            if line.startswith(b">"):
                record_position = file.tell() - len(line)
                return record_position

        return None

    @staticmethod
    def _move_file_position(file: IO, position: int) -> None:
        """Moves file position to the nearest line after jump on chunk size (bytes)."""
        file.seek(position)
        # Get to the next line in case we jumped to the middle of the previous line.
        next(file)

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

from domain.entities import SequenceRecord
from domain.models import ChunkRange
from infrastructure.process_data.exceptions import (
    InvalidRecordError,
    IteratorError,
)
from infrastructure.process_data.uniprot.fasta.parser import FastaParser


class FastaIterator:
    """Iterate over sequence records and yield parsed data."""

    def __init__(self, path_to_file: Path, chunk_range: ChunkRange | None = None):
        self._path_to_file = path_to_file
        self._fasta_parser = FastaParser()
        self._chunk_range = chunk_range
        self._logger = logging.getLogger(self.__class__.__name__)

    def __iter__(self) -> Iterator[SequenceRecord]:
        """Generate sequence data structs from fasta file."""
        resolved_chunk_range = self._resolve_chunk_range()

        with self._open_file(resolved_chunk_range) as file:
            yield from self._record_gen(file, resolved_chunk_range)

    def _resolve_chunk_range(self) -> ChunkRange:
        if not self._chunk_range:
            try:
                file_size = self._path_to_file.stat().st_size

            except Exception as e:
                self._logger.exception("Failed to open file %s", self._path_to_file)
                raise IteratorError from e

            if file_size == 0:
                raise IteratorError("Empty file provided")

            # The last byte of the file is '' so we substract it.
            extra_byte: int = 1
            chunk_end = file_size - extra_byte
            chunk_start = 0
            return ChunkRange(chunk_start, chunk_end)

        return self._chunk_range

    @contextmanager
    def _open_file(self, resolved_chunk_range: ChunkRange) -> Iterator[IO]:
        try:
            with self._path_to_file.open("r", encoding="utf-8") as file:
                self._move_file_cursor_position(file, resolved_chunk_range)
                yield file

        except Exception as e:
            self._logger.exception("Failed to open file %s", self._path_to_file)
            raise IteratorError from e

    @staticmethod
    def _move_file_cursor_position(file: IO, resolved_chunk_range: ChunkRange) -> None:
        """Jump to the position provided with chunk start value."""
        file.seek(resolved_chunk_range.start)

    def _record_gen(
        self,
        file: IO,
        resolved_chunk_range: ChunkRange,
    ) -> Iterator[SequenceRecord]:
        """Generate sequence data structs depending on chunk values."""
        current_position: int = resolved_chunk_range.start
        end_position: int = resolved_chunk_range.end

        assert current_position >= 0
        assert end_position > 0

        while not self._is_position_beyond_limit(current_position, end_position):
            raw_sequence_info: str = ""
            sequence_parts: list[str] = []

            for line in file:
                current_position = self._update_current_position(current_position, line)
                line = line.strip()

                if self._is_record_start(line):
                    yield from self._yield_parsed_record(
                        raw_sequence_info, sequence_parts
                    )
                    sequence_parts.clear()
                    raw_sequence_info = line

                else:
                    sequence_parts.append(line)

                # When chunk end is crossed - stop iteration through file.
                if self._is_position_beyond_limit(current_position, end_position):
                    break

            yield from self._yield_final_parsed_record(
                raw_sequence_info, sequence_parts
            )

    @staticmethod
    def _is_position_beyond_limit(current_position: int, end_position: int) -> bool:
        return current_position > end_position

    @staticmethod
    def _update_current_position(current_position: int, line: str) -> int:
        return current_position + len(line)

    def _is_record_start(self, line: str) -> bool:
        """Check if current string is a record start"""
        record_delimiter: str = ">"
        return line.startswith(record_delimiter)

    def _yield_parsed_record(
        self, raw_sequence_info: str, sequence_parts: list[str]
    ) -> Iterator[SequenceRecord]:
        """Generate parsed record if parts of the sequence were gathered."""
        if sequence_parts:
            result = self._fasta_parser.parse(raw_sequence_info, sequence_parts)
            yield result

    def _yield_final_parsed_record(
        self, raw_sequence_info: str, sequence_parts: list[str]
    ) -> Iterator[SequenceRecord]:
        """Try generate the last sequence data struct."""
        try:
            yield from self._try_yield_final_parsed_record(
                raw_sequence_info, sequence_parts
            )

        except InvalidRecordError as e:
            self._logger.exception("Invalid file provided --> %s", self._path_to_file)
            raise IteratorError(
                f"Invalid file provided --> {self._path_to_file}"
            ) from e

    def _try_yield_final_parsed_record(
        self, raw_sequence_info: str, sequence_parts: list[str]
    ) -> Iterator[SequenceRecord]:
        """Generate the final parsed sequence data struct."""
        yield self._fasta_parser.parse(raw_sequence_info, sequence_parts)

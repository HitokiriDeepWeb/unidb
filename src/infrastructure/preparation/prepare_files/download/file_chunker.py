from domain.models import ChunkRange


class FileChunkCalculator:
    """Calculate file chunk ranges for partial download."""

    def __init__(self, file_size: int, total_chunk_quantity: int):
        self._file_size = file_size
        self._total_chunk_quantity = total_chunk_quantity
        self._chunk_size = file_size // total_chunk_quantity

    def get_chunk_range(self, chunk_number: int) -> ChunkRange:
        chunk_start = self._calculate_chunk_start(chunk_number)
        chunk_end = self._calculate_chunk_end(chunk_number, chunk_start)
        return ChunkRange(chunk_start, chunk_end)

    def _calculate_chunk_start(self, chunk_number: int) -> int:
        """Calculate the start of the chunk."""
        return self._chunk_size * chunk_number

    def _calculate_chunk_end(self, chunk_number: int, chunk_start: int) -> int:
        """Calculate the end of the chunk."""
        redundant_byte_offset: int = 1
        redundant_index_offset: int = 1

        if chunk_number < self._total_chunk_quantity - redundant_index_offset:
            return chunk_start + self._chunk_size - redundant_byte_offset

        return self._file_size - redundant_byte_offset

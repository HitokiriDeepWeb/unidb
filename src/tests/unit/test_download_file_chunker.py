import pytest

from domain.models import ChunkRange
from infrastructure.preparation.prepare_files.download import FileChunkCalculator


@pytest.mark.parametrize(
    "chunk_number, expected_result",
    [
        (0, ChunkRange(start=0, end=24)),
        (1, ChunkRange(start=25, end=49)),
        (2, ChunkRange(start=50, end=74)),
        (3, ChunkRange(start=75, end=99)),
    ],
)
def test_chunk_calculator_with_even_file_size_value(
    chunk_number: int,
    expected_result: ChunkRange,
):
    chunk_quantity = 4
    even_file_size_value = 100
    sut = FileChunkCalculator(
        total_chunk_quantity=chunk_quantity, file_size=even_file_size_value
    )

    result = sut.get_chunk_range(chunk_number)

    assert result == expected_result


@pytest.mark.parametrize(
    "chunk_number, expected_result",
    [
        (0, ChunkRange(start=0, end=24)),
        (1, ChunkRange(start=25, end=49)),
        (2, ChunkRange(start=50, end=74)),
        (3, ChunkRange(start=75, end=100)),
    ],
)
def test_chunk_calculator_with_uneven_file_size_value(
    chunk_number: int, expected_result: ChunkRange
):
    chunk_quantity = 4
    uneven_file_size_value = 101
    sut = FileChunkCalculator(
        total_chunk_quantity=chunk_quantity, file_size=uneven_file_size_value
    )

    result = sut.get_chunk_range(chunk_number)

    assert result == expected_result

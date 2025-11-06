from pathlib import Path

from domain.models import ChunkRange
from infrastructure.process_data.uniprot.fasta import ChunkRangeIterator


def test_chunk_range_gen(test_fasta: Path):
    workers_number = 10
    sut = ChunkRangeIterator(test_fasta, workers_number)
    expected_result = [
        ChunkRange(start=0, end=173),
        ChunkRange(start=174, end=400),
        ChunkRange(start=401, end=607),
        ChunkRange(start=608, end=844),
        ChunkRange(start=845, end=1067),
        ChunkRange(start=1068, end=1291),
    ]

    result = list(sut)

    assert result == expected_result

from pathlib import Path

import pytest

from domain.entities import (
    SequenceRecord,
    SequenceSource,
)
from infrastructure.process_data.exceptions import IteratorError
from infrastructure.process_data.uniprot.fasta import (
    ChunkRangeIterator,
    FastaIterator,
)


@pytest.fixture
def damaged_fasta(tmp_path: Path) -> Path:
    content = "damaged content"
    path_to_file = tmp_path / "uniprot.fasta"
    path_to_file.open("w").write(content)
    return path_to_file


@pytest.fixture
def empty_fasta(tmp_path: Path) -> Path:
    path_to_file = tmp_path / "uniprot_empty.fasta"
    path_to_file.open("w").close()
    return path_to_file


expected_result = [
    SequenceRecord(
        is_reviewed=False,
        accession="A0A023T699",
        source=SequenceSource.TREMBL,
        entry_name="A0A023T699_EMCV",
        peptide_name="Genome polyprotein",
        organism_name="Encephalomyocarditis virus",
        ncbi_id=12104,
        sequence="MATTMEQETCAHPLTFEECPKCSALQYRNGFYLLKYDEEW"
        "YPEELLIDGEDDVFDPELDMESVEYRWRSLFW",
    ),
    SequenceRecord(
        is_reviewed=True,
        accession="A0A076FVY1",
        source=SequenceSource.SWISS_PROT,
        entry_name="A0A076FVY1_BATSU",
        peptide_name="Tyrosine-protein kinase receptor (Fragment)",
        organism_name="Bathyergus suillus",
        ncbi_id=10172,
        sequence="ASELENFMGLIEVVTGYVKIRHSHALVSLSFLKNLRQILG"
        "EEQLEGNYSFYVLDNQNLQQPGVLVLRASFDERQPYAHMNGGRTNERAL"
        "PLPQSSTC",
    ),
    SequenceRecord(
        is_reviewed=False,
        accession="A0A076G1H5",
        source=SequenceSource.TREMBL,
        entry_name="A0A076G1H5_FUKDA",
        peptide_name="Tyrosine-protein kinase receptor (Fragment)",
        organism_name="Fukomys damarensis",
        ncbi_id=885580,
        sequence="ICGPGIDIRNDYQQLKRLENCTVIEGYLHILLISKAEDYRS"
        "YRFPKLTVITEYLLLFRVAGGRTNERALPLPQSSTC",
    ),
    SequenceRecord(
        is_reviewed=True,
        accession="A0A091CJV8-1",
        source=SequenceSource.SP_ISOFORMS,
        entry_name="A0A091CJV8_FUKDA",
        peptide_name="non-specific serine/threonine protein kinase",
        organism_name="Fukomys damarensis",
        ncbi_id=885580,
        sequence="MAQKENAYPWPYGRQTSQSGLNTLPQRVLRKEPATPSTLVL"
        "MSRSNGQATAVPGQKVVENDLISKLLKHNPSERLPLAQVSAHPWVQAHSKRVLPPSAP",
    ),
    SequenceRecord(
        is_reviewed=False,
        accession="A0A091CK25",
        source=SequenceSource.TREMBL,
        entry_name="A0A091CK25_FUKDA",
        peptide_name="non-specific serine/threonine protein kinase",
        organism_name="Fukomys damarensis",
        ncbi_id=885580,
        sequence="MSAEVRLRRLQQLALDPSFLGLEPLLDLLLGVHQELGASDL"
        "AQDKYVADFLQWAEPIVARALGCFGLVAHAGYLAPGWRRPGTAFTP",
    ),
    SequenceRecord(
        is_reviewed=False,
        accession="A0A091CKG8",
        source=SequenceSource.TREMBL,
        entry_name="A0A091CKG8_FUKDA",
        peptide_name="Succinate dehydrogenase [ubiquinone] "
        "iron-sulfur subunit, mitochondrial",
        organism_name="Fukomys damarensis",
        ncbi_id=885580,
        sequence="MAAVAGFSLRRRFPATVLGGSCLQACRGAQTAADRAPRIKKFAIYRWDPDKTGDKPRMQTAVR",
    ),
]


def test_fasta_iterator(test_fasta: Path):
    workers_number = 1
    chunk_range = list(ChunkRangeIterator(test_fasta, workers_number))
    sut = FastaIterator(test_fasta, *chunk_range)

    records = list(sut)

    assert records == expected_result


def test_fasta_iterator_with_damaged_file(damaged_fasta: Path):
    sut = FastaIterator(damaged_fasta)

    with pytest.raises(IteratorError):
        list(sut)


def test_fasta_iterator_with_empty_file(empty_fasta: Path):
    sut = FastaIterator(empty_fasta)

    with pytest.raises(IteratorError):
        list(sut)


def test_fasta_iterator_fail_to_open_file(tmp_path: Path):
    path_to_file = tmp_path / "no_file.fasta"
    sut = FastaIterator(path_to_file)

    with pytest.raises(IteratorError):
        list(sut)

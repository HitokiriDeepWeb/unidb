import pytest

from domain.entities import SequenceRecord, SequenceSource
from infrastructure.process_data.exceptions import InvalidRecordError
from infrastructure.process_data.uniprot.fasta import FastaParser


@pytest.mark.parametrize(
    "raw_sequence_info, sequence_parts, expected_result",
    [
        (
            ">tr|A0A023T699|A0A023T699_EMCV Genome polyprotein "
            "OS=Encephalomyocarditis virus OX=12104 PE=3 SV=1",
            [
                "MATTMEQETCAHPLTFEECPKCSALQYRNGF",
                "YLLKYDEEWYPEELLIDGEDDVFDPELDMES",
                "VEYRWRSLFW",
            ],
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
        ),
        (
            ">sp|A0A076FVY1|A0A076FVY1_BATSU Tyrosine-protein kinase receptor "
            "(Fragment) OS=Bathyergus suillus OX=10172 GN=IGF1R PE=2 SV=1",
            [
                "ASELENFMGLIEVVTGYVKIRHSHALVSLSF",
                "LKNLRQILGEEQLEGNYSFYVLDNQNLQQPG",
                "VLVLRASFDERQPYAHMNGGRTNERA",
                "LPLPQSSTC",
            ],
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
        ),
        (
            ">tr|A0A076G1H5|A0A076G1H5_FUKDA Tyrosine-protein kinase receptor "
            "(Fragment) OS=Fukomys damarensis OX=885580 GN=IGF1R PE=2 SV=1",
            [
                "ICGPGIDIRNDYQQLKRLENCTVIEGYLHILL",
                "ISKAEDYRSYRFPKLTVITEYLLLFRVAGGRT",
                "NERALPLPQSSTC",
            ],
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
        ),
        (
            ">sp|A0A091CJV8-1|A0A091CJV8_FUKDA non-specific "
            "serine/threonine protein kinase "
            "OS=Fukomys damarensis OX=885580 GN=H920_19768 PE=3 SV=1",
            [
                "MAQKENAYPWPYGRQTSQSGLNTLPQRVLRKE",
                "PATPSTLVLMSRSNGQATAVPGQKVVENDLIS",
                "KLLKHNPSERLPLAQVSAHPWVQAHSKRVLPPSAP",
            ],
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
        ),
        (
            ">tr|A0A091CK25|A0A091CK25_FUKDA non-specific serine/threonine "
            "protein kinase OS=Fukomys damarensis OX=885580 GN=H920_19633 PE=3 SV=1",
            [
                "MSAEVRLRRLQQLALDPSFLGLEPLLDLLLGV",
                "HQELGASDLAQDKYVADFLQWAEPIVARALGC",
                "FGLVAHAGYLAPGWRRPGTAFTP",
            ],
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
        ),
        (
            ">tr|A0A091CKG8|A0A091CKG8_FUKDA "
            "Succinate dehydrogenase [ubiquinone] iron-sulfur subunit, mitochondrial "
            "OS=Fukomys damarensis OX=885580 GN=H920_19443 PE=3 SV=1",
            [
                "MAAVAGFSLRRRFPATVLGGSCLQACRGAQTA",
                "ADRAPRIKKFAIYRWDPDKTGDKPRMQTAVR",
            ],
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
        ),
    ],
)
def test_fasta_parser_with_valid_content(
    raw_sequence_info: str, sequence_parts: list[str], expected_result: SequenceRecord
):
    sut = FastaParser()

    result = sut.parse(raw_sequence_info, sequence_parts)

    assert result == expected_result


@pytest.mark.parametrize(
    "raw_sequence_info, sequence_parts", [("damaged_data", ["damaged_sequence"])]
)
def test_fasta_parser_with_invalid_content(
    raw_sequence_info: str, sequence_parts: list[str]
):
    sut = FastaParser()

    with pytest.raises(InvalidRecordError):
        sut.parse(raw_sequence_info, sequence_parts)

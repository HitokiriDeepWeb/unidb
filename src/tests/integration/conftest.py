from collections.abc import Iterator
from pathlib import Path

import pytest

content = (
    ">tr|A0A023T699|A0A023T699_EMCV Genome polyprotein "
    "OS=Encephalomyocarditis virus OX=12104 PE=3 SV=1\n"
    "MATTMEQETCAHPLTFEECPKCSALQYRNGF\n"
    "YLLKYDEEWYPEELLIDGEDDVFDPELDMES\n"
    "VEYRWRSLFW\n"
    ">sp|A0A076FVY1|A0A076FVY1_BATSU Tyrosine-protein kinase receptor (Fragment) "
    "OS=Bathyergus suillus OX=10172 GN=IGF1R PE=2 SV=1\n"
    "ASELENFMGLIEVVTGYVKIRHSHALVSLSF\n"
    "LKNLRQILGEEQLEGNYSFYVLDNQNLQQPG\n"
    "VLVLRASFDERQPYAHMNGGRTNERA\n"
    "LPLPQSSTC\n"
    ">tr|A0A076G1H5|A0A076G1H5_FUKDA Tyrosine-protein kinase receptor (Fragment) "
    "OS=Fukomys damarensis OX=885580 GN=IGF1R PE=2 SV=1\n"
    "ICGPGIDIRNDYQQLKRLENCTVIEGYLHILL\n"
    "ISKAEDYRSYRFPKLTVITEYLLLFRVAGGRT\n"
    "NERALPLPQSSTC\n"
    ">sp|A0A091CJV8-1|A0A091CJV8_FUKDA non-specific "
    "serine/threonine protein kinase "
    "OS=Fukomys damarensis OX=885580 GN=H920_19768 PE=3 SV=1\n"
    "MAQKENAYPWPYGRQTSQSGLNTLPQRVLRKE\n"
    "PATPSTLVLMSRSNGQATAVPGQKVVENDLIS\n"
    "KLLKHNPSERLPLAQVSAHPWVQAHSKRVLPPSAP\n"
    ">tr|A0A091CK25|A0A091CK25_FUKDA non-specific serine/threonine protein kinase "
    "OS=Fukomys damarensis OX=885580 GN=H920_19633 PE=3 SV=1\n"
    "MSAEVRLRRLQQLALDPSFLGLEPLLDLLLGV\n"
    "HQELGASDLAQDKYVADFLQWAEPIVARALGC\n"
    "FGLVAHAGYLAPGWRRPGTAFTP\n"
    ">tr|A0A091CKG8|A0A091CKG8_FUKDA "
    "Succinate dehydrogenase [ubiquinone] iron-sulfur subunit, mitochondrial "
    "OS=Fukomys damarensis OX=885580 GN=H920_19443 PE=3 SV=1\n"
    "MAAVAGFSLRRRFPATVLGGSCLQACRGAQTA\n"
    "ADRAPRIKKFAIYRWDPDKTGDKPRMQTAVR"
)


@pytest.fixture
def test_fasta(tmp_path: Path) -> Iterator[Path]:
    path_to_file = tmp_path / "uniprot.fasta"

    with path_to_file.open("w") as file:
        file.write(content)

    yield path_to_file

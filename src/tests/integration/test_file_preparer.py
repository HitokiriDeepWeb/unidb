import asyncio
import gzip
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from pathlib import Path

import pytest

from core.utils import init_shutdown_event
from infrastructure.preparation.prepare_files.preparer import FilePreparer
from src.core.config import UniprotFiles

CONTENT = (
    ">tr|I7CLV3|I7CLV3_BOVIN Insulin (Fragment) "
    "OS=Bos taurus OX=9913 PE=2 SV=1\n"
    "FVNQHLCGSHLVEALYLVCGERGFFYTPKARREVEGPQVGALELAGGPGAGGLEGPPQKR\n"
    ">tr|A5PJB2|A5PJB2_BOVIN Insulin OS=Bos taurus OX=9913 GN=INS PE=2 SV=1\n"
    "MALWTRLAPLLALLALWAPAPARAFVNQHLCGSHLVEALYLVCGERGFFYTPKARREVEG\n"
    ">tr|Q17QJ6|Q17QJ6_BOVIN B-cell lymphoma/leukemia 10 "
    "OS=Bos taurus OX=9913 GN=BCL10 PE=2 SV=1\n"
    "MEPTAPSLTEEDLTEVKKDALENLRVYLCEKIIAERHFDHLRAKKILSREDTEEISCRTS\n"
    ">tr|A4GX95|A4GX95_BOVIN Somatotropin OS=Bos taurus OX=9913 PE=2 SV=1\n"
    "MMAAGPRTSLLLAFTLLCLPWTQVVGAFPAMSLSGLFANAVLRAQHLHQLAADTFKEFER\n"
    ">tr|B5B3R8|B5B3R8_BOVIN Alpha-S1-casein OS=Bos taurus OX=9913 "
    "GN=CSN1S1 PE=2 SV=1\n"
    "MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNELSKDIG\n"
    ">tr|F1MZV2|F1MZV2_BOVIN Charged multivesicular body protein 5 "
    "OS=Bos taurus OX=9913 GN=CHMP5 PE=3 SV=1\n"
    "MNRFFGKAKPKAPPPSLTDCIGTVDSRAESIDKKISRLDAELVKYKDQIKKMREGPAKNM\n"
    ">tr|A0A3Q1LW04|A0A3Q1LW04_BOVIN "
    "Phosphoinositide-3-kinase regulatory subunit 1 "
    "OS=Bos taurus OX=9913 GN=PIK3R1 PE=3 SV=2\n"
    "MYNTVWNMEDLDLEYAKTDINCGTDLMFYIEMDPPALPPKPPKPTTVANNGMNNNMSLQD\n"
    ">tr|A0A3Q1MXQ5|A0A3Q1MXQ5_BOVIN Phosphatidylinositol 3,4,5-trisphosphate "
    "3-phosphatase and dual-specificity protein phosphatase PTEN "
    "OS=Bos taurus OX=9913 GN=PTEN PE=3 SV=2\n"
    "MTAIIKEIVSRNKRRYQEDGFDLDLTYIYPNIIAMGFPAERLEGVYRNNIDDVVRCAERH\n"
    "YDTAKFNCRVAQYPFEDHNPPQLELIKPFCEDLDQWLSEDDNHVAAIHCKAGKGRTGVMI\n"
    ">tr|E1B9U0|E1B9U0_BOVIN Scleraxis bHLH transcription factor "
    "OS=Bos taurus OX=9913 GN=SCX PE=4 SV=4\n"
    "MSFAMLRSAPPGRYLYPEVSPLSEDEDRGSESSGSDEKPCRVHAARCGLQGARRRAGGRR\n"
    ">tr|A0AAA9SDZ8|A0AAA9SDZ8_BOVIN Sterol carrier protein 2 "
    "OS=Bos taurus OX=9913 GN=SCP2 PE=4 SV=1\n"
    "MSLVASQSPLRNRVFVVGVGMTKFTKPGVENRDYPDLAKEAGQKALADAQIPYSAVEQAC"
).encode("utf-8")


@pytest.fixture
def test_gz(tmp_path: Path) -> Path:
    gz_path = tmp_path / "uniprot_trembl.fasta.gz"

    with gzip.open(gz_path, "wb") as file:
        file.write(CONTENT)

    return gz_path


@pytest.fixture(autouse=True)
def trembl_gz_file_parts(test_gz: Path):
    gz_parts = 18

    gz_content = Path(f"{test_gz}").open("rb").read()
    gz_size = test_gz.stat().st_size
    chunk_size = gz_size // gz_parts

    for part in range(gz_parts):
        start = part * chunk_size
        end = (part + 1) * chunk_size if part < gz_parts - 1 else len(gz_content)
        part_content = gz_content[start:end]

        Path(f"{test_gz}.{part}").open("wb").write(part_content)

    test_gz.unlink()


@pytest.mark.asyncio
async def test_file_preparer_after_all_files_were_downloaded(tmp_path: Path):
    sut = FilePreparer(source_folder=tmp_path, preparation_is_required=True)

    with Manager() as manager:
        event = manager.Event()
        workers_number = 4

        with ProcessPoolExecutor(
            max_workers=workers_number,
            initializer=init_shutdown_event,
            initargs=(event,),
        ) as process_pool:
            loop = asyncio.get_running_loop()
            await sut.prepare_required_files(
                loop=loop, process_pool=process_pool, event=event
            )

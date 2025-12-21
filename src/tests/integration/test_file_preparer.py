import asyncio
import gzip
from concurrent.futures import ProcessPoolExecutor
from itertools import chain
from multiprocessing import Manager
from pathlib import Path

import pytest

from core.utils import init_shutdown_event
from infrastructure.preparation.prepare_files.preparer import FilePreparer
from src.core.config import NCBIFiles, UniprotFiles


@pytest.fixture
def test_gz(tmp_path: Path, test_fasta: Path) -> Path:
    gz_path = tmp_path / "uniprot_trembl.fasta.gz"

    with gzip.open(gz_path, "wb") as file, test_fasta.open("rb") as fasta_file:
        file.write(fasta_file.read())

    test_fasta.unlink()

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
async def test_file_preparer_when_files_need_preparation(tmp_path: Path):
    sut = FilePreparer(source_folder=tmp_path, preparation_is_required=True)
    expected_result = set(chain(UniprotFiles, NCBIFiles))

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

    result = {file.name for file in tmp_path.iterdir() if file.is_file()}

    assert result == expected_result


@pytest.mark.asyncio
async def test_file_preparer_when_files_do_not_need_preparation(tmp_path: Path):
    sut = FilePreparer(source_folder=tmp_path, preparation_is_required=True)
    expected_result = set(chain(UniprotFiles, NCBIFiles))

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

    result = {file.name for file in tmp_path.iterdir() if file.is_file()}

    assert result == expected_result

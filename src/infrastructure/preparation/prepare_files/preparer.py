import logging
from asyncio import AbstractEventLoop
from concurrent.futures import ProcessPoolExecutor
from itertools import chain
from pathlib import Path
from threading import Event

from core.models import FunctionCall
from core.utils import process_futures, run_futures
from domain.entities import DEFAULT_SOURCE_FILES_FOLDER
from infrastructure.models import NCBIFiles, UniprotFiles
from infrastructure.preparation.prepare_files.exceptions import FilePreparationError
from infrastructure.preparation.prepare_files.file_operations import (
    concatenate_files,
    decompress_gz,
    extract_from_tar,
)

logger = logging.getLogger(__name__)


def process_trembl_file(path_to_trembl: Path) -> None:
    try:
        concatenate_files(path_to_trembl)
        decompress_gz(path_to_trembl)

    except Exception as e:
        raise FilePreparationError(f"Unable to prepare file {path_to_trembl}") from e


class FilePreparer:
    def __init__(
        self,
        source_folder: Path = DEFAULT_SOURCE_FILES_FOLDER,
        preparation_is_required: bool = True,
    ):
        self._source_folder = source_folder
        self._preparation_is_required = preparation_is_required
        self._path_to_tr_gz = source_folder / "uniprot_trembl.fasta.gz"
        self._path_to_new_taxdump = source_folder / "new_taxdump.tar.gz"
        self._path_to_sp_gz = source_folder / "uniprot_sprot.fasta.gz"
        self._path_to_sp_iso_gz = source_folder / "uniprot_sprot_varsplic.fasta.gz"

    async def prepare_required_files(
        self, loop: AbstractEventLoop, process_pool: ProcessPoolExecutor, event: Event
    ) -> None:
        if not self._preparation_is_required:
            self._check_prepared_files_existence()
            return

        self._check_files_that_will_be_prepared_existence()

        preparation_calls = [
            FunctionCall(
                func=extract_from_tar, args=(self._path_to_new_taxdump, NCBIFiles)
            ),
            FunctionCall(func=decompress_gz, args=(self._path_to_sp_gz,)),
            FunctionCall(func=decompress_gz, args=(self._path_to_sp_iso_gz,)),
            FunctionCall(func=process_trembl_file, args=(self._path_to_tr_gz,)),
        ]

        tasks = run_futures(loop, process_pool, preparation_calls)
        await process_futures(tasks, event, FilePreparationError())

    def _check_files_that_will_be_prepared_existence(self) -> None:
        required_files: list[Path] = [
            self._path_to_sp_iso_gz,
            self._path_to_sp_gz,
            self._path_to_new_taxdump,
        ]

        trembl_gz_files: str = "uniprot_trembl.fasta.gz*"
        matching_files: list[Path] = list(
            self._source_folder.glob("uniprot_trembl.fasta.gz.*")
        )

        if not matching_files:
            raise FileNotFoundError(f"Missing TrEMBL file(s): {trembl_gz_files}")

        [self._check_file_existence(file) for file in required_files]

    def _check_prepared_files_existence(self) -> None:
        ncbi_files = [self._source_folder / file for file in NCBIFiles]
        uniprot_files = [self._source_folder / file for file in UniprotFiles]

        required_files: list[Path] = list(chain(ncbi_files, uniprot_files))
        [self._check_file_existence(file) for file in required_files]

    def _check_file_existence(self, file: Path) -> None:
        if not file.exists():
            logger.error("Missing required file %s", file)
            raise FileNotFoundError(f"Missing {file=}")

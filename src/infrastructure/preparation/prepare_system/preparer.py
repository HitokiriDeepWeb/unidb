import asyncio
import logging
import shutil
from asyncio import Task
from collections.abc import Coroutine
from pathlib import Path

from aiofiles import os as async_os
from aiohttp import ClientSession, ClientTimeout

from core.utils import (
    cancel_on_error,
    create_tasks,
    process_tasks,
)
from domain.entities import DEFAULT_SOURCE_FILES_FOLDER
from infrastructure.preparation.constants import (
    LAST_MODIFIED_DATE,
    NCBI_LINK,
    UNIPROT_SP_ISOFORMS_LINK,
    UNIPROT_SP_LINK,
    UNIPROT_TR_LINK,
)
from infrastructure.preparation.prepare_files.download.get_file_size import (
    get_file_size,
)
from infrastructure.preparation.prepare_system.config import SystemPreparerConfig
from infrastructure.preparation.prepare_system.exceptions import NotEnoughSpaceError
from infrastructure.preparation.prepare_system.models import UserAnswer

logger = logging.getLogger(__name__)


class SystemPreparer:
    """
    Execute all necessary operations on system to prepare it for UniProt setup.
    And clean it afterwards.
    """

    _DECOMPRESSION_COEFF = 1.96

    def __init__(self, config: SystemPreparerConfig):
        self._config = config

    async def prepare_environment(self) -> None:
        file_size_in_bytes = await self._get_file_size_in_bytes()
        file_size_in_gb = self._get_file_size_in_gb(file_size_in_bytes)

        self._check_disk_space_required_size(file_size_in_gb)
        self._create_required_folders_before_download()

    async def _get_file_size_in_bytes(self) -> float:
        file_size_in_bytes: float = 0

        if self._config.download_is_required:
            file_size_in_bytes = await self._estimate_required_space_for_files()
            self._verify_disk_space_availability_for_download(file_size_in_bytes)

        return file_size_in_bytes

    def _check_disk_space_required_size(self, file_size_in_gb: float) -> None:
        """Count database size and prompt user for confirmation."""
        if not self._config.accept_setup_automatically:
            database_size_in_gb = self._estimate_required_space_for_database(
                file_size_in_gb
            )
            self._prompt_user_for_disk_space_confirmation(
                file_size_in_gb, database_size_in_gb
            )

    @staticmethod
    def _get_file_size_in_gb(file_size_in_bytes: float) -> float:
        bytes_in_one_gb = 1_073_741_824
        return file_size_in_bytes / bytes_in_one_gb

    def _create_required_folders_before_download(self) -> None:
        if self._config.download_is_required:
            self._create_neccessary_folders()

    def _prompt_user_for_disk_space_confirmation(
        self, file_size: float, database_size: float
    ) -> None:
        max_setup_size = file_size + (file_size / self._DECOMPRESSION_COEFF)
        while True:
            prompt: str = (
                "The files to download approximate size will estimate "
                f"{file_size:.2f} GB.\n"
                "The approximate size required for setup process will estimate "
                f"{max_setup_size:.2f} GB.\n"
                f"The result database approximate size will estimate "
                f"{database_size:.2f} GB."
                " Proceed (y/n)?"
            )

            answer: str = input(prompt).lower().strip()

            if answer in (UserAnswer.YES, UserAnswer.DEFAULT):
                break

            elif answer == UserAnswer.NO:
                raise SystemExit("Setup cancelled by user")

            else:
                print("Input must be 'y' or 'n'")

    async def delete_unnecessary_files(self) -> None:
        async def _async_delete_file(path_to_file: Path) -> None:
            logger.info("...removing %s file", path_to_file.name)

            if await async_os.path.exists(str(path_to_file)):
                await async_os.unlink(str(path_to_file))

            logger.info("Done")

        coros: list[Coroutine] = [
            _async_delete_file(file) for file in DEFAULT_SOURCE_FILES_FOLDER.iterdir()
        ]

        tasks: list[Task] = create_tasks(coros)
        await process_tasks(tasks)

    async def _estimate_required_space_for_files(self) -> float:
        general_file_size_in_bytes = await self._count_general_file_size()

        result_file_size_in_bytes = self._calculate_result_file_size(
            general_file_size_in_bytes
        )
        return result_file_size_in_bytes

    @staticmethod
    async def _count_general_file_size() -> int:
        head_request_timeout = ClientTimeout(total=60)
        general_file_size = 0

        async with ClientSession(
            raise_for_status=True, timeout=head_request_timeout
        ) as session:
            coros = [
                get_file_size(UNIPROT_TR_LINK, session),
                get_file_size(UNIPROT_SP_LINK, session),
                get_file_size(NCBI_LINK, session),
                get_file_size(UNIPROT_SP_ISOFORMS_LINK, session),
            ]

            tasks = create_tasks(coros)
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_EXCEPTION
            )

            cancel_on_error(done, pending)

            for task in done:
                general_file_size += task.result()

        return general_file_size

    def _calculate_result_file_size(self, general_file_size: int) -> float:
        assert general_file_size > 0

        space_for_proper_system_work: int = 10**10

        result_file_size = (
            general_file_size * self._DECOMPRESSION_COEFF
        ) + space_for_proper_system_work
        return result_file_size

    def _estimate_required_space_for_database(self, file_size: float) -> float:
        trgm_coeff: float = 2.25
        db_coeff: float = 1.12 if not self._config.trgm_required else trgm_coeff

        approximate_file_size_in_gb = file_size

        if self._exact_file_size_is_not_available(file_size):
            approximate_file_size_in_gb = 96

        database_size_in_gb = db_coeff * approximate_file_size_in_gb
        return database_size_in_gb

    @staticmethod
    def _exact_file_size_is_not_available(file_size: float):
        return file_size == 0

    def _verify_disk_space_availability_for_download(
        self, required_size: float
    ) -> None:
        *_, free_space = shutil.disk_usage(Path("."))

        if free_space - required_size >= 0:
            return

        raise NotEnoughSpaceError

    def _create_neccessary_folders(self) -> None:
        """
        Create neccessary folders and file 'last_modified.txt' which
        will store information about last update of official UniProt database.
        Delete all the files from folders if any exist.
        """
        logger.info("...creating folders if do not exist")
        DEFAULT_SOURCE_FILES_FOLDER.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Folder %s has been created successfully", DEFAULT_SOURCE_FILES_FOLDER
        )

        logger.info("...creating file last_modified.txt if does not exist")
        LAST_MODIFIED_DATE.touch(exist_ok=True)

        logger.info("Done")

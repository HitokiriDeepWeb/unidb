import functools
import glob
import gzip
import inspect
import logging
import shutil
import subprocess
import tarfile
from collections.abc import Callable, Iterable
from gzip import GzipFile
from io import BufferedWriter
from pathlib import Path
from tarfile import TarFile, TarInfo
from typing import Any

from core.exceptions import NeighbouringProcessError
from core.utils import is_shutdown_event_set, set_shutdown_event
from infrastructure.preparation.prepare_files.exceptions import FilePreparationError

logger = logging.getLogger(__name__)


def file_preparation_handler(func: Callable) -> Any:
    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        path_to_file = bound_args.arguments["path_to_file"]

        try:
            if is_shutdown_event_set():
                raise NeighbouringProcessError

            result = func(*args, **kwargs)
            logger.info("File %s was prepared successfully", path_to_file.name)
            return result

        except NeighbouringProcessError:
            raise

        except Exception as e:
            set_shutdown_event()
            logger.exception(
                "Unable to prepare file %s for processing", path_to_file.name
            )
            raise FilePreparationError from e

        finally:
            _delete_file(path_to_file)

    return wrapper


@file_preparation_handler
def extract_from_tar(path_to_file: Path, files_to_extract: Iterable[str]) -> None:
    _try_extract_from_tar(path_to_file, files_to_extract)


def _try_extract_from_tar(path_to_file: Path, files_to_extract: Iterable[str]) -> None:
    directory_path = _get_directory_path(path_to_file)

    with tarfile.open(path_to_file) as archive:
        logger.info("...extracting files from %s", path_to_file.name)
        _extract_appropriate_files(files_to_extract, directory_path, archive)


def _get_directory_path(path_to_file: Path) -> str:
    return str(path_to_file.parent)


def _extract_appropriate_files(
    files_to_extract: Iterable[str], directory_path: str, archive: TarFile
) -> None:
    members_to_extract: Iterable[TarInfo] = []

    for member in archive.getmembers():
        if _member_in_files(member, files_to_extract):
            members_to_extract.append(member)

    if members_to_extract:
        archive.extractall(
            path=directory_path, members=members_to_extract, filter="data"
        )


def _member_in_files(member: TarInfo, files_to_extract: Iterable[str]) -> bool:
    return member.name in files_to_extract


@file_preparation_handler
def decompress_gz(path_to_file: Path) -> None:
    """Decompress file with .gz format."""
    _try_decompress_gz(path_to_file)


def _try_decompress_gz(path_to_file: Path) -> None:
    with gzip.open(path_to_file, "rb") as compressed_file:
        output_file_name = _get_output_file_name(path_to_file)
        logger.info(f"...decompressing file {output_file_name}")

        with open(path_to_file.parent / output_file_name, "wb") as output_file:
            _copy_compressed_data(compressed_file, output_file)


def _get_output_file_name(path_to_file: Path) -> str:
    return path_to_file.stem


def _copy_compressed_data(
    compressed_file: GzipFile, output_file: BufferedWriter
) -> None:
    shutil.copyfileobj(compressed_file, output_file)


def concatenate_files(path_to_file: Path) -> None:
    """Concatenate parts of the file to a single whole."""
    files = sorted(
        glob.glob(f"{path_to_file}.*"), key=lambda x: int(x.split(".").pop())
    )

    if is_shutdown_event_set():
        raise NeighbouringProcessError

    try:
        _try_concatenate_files(path_to_file, files)

    except subprocess.CalledProcessError as e:
        logger.exception("File concatenation failed with code %s: %s", e.returncode)

        set_shutdown_event()
        raise FilePreparationError(
            f"File concatenation failed with code {e.returncode}: {e.stderr}"
        ) from e

    except Exception as e:
        logger.exception("File concatenation failed due to unexpected error")

        set_shutdown_event()
        raise FilePreparationError("File concatenation failed") from e

    finally:
        _delete_file_parts(files)


def _try_concatenate_files(path_to_file: Path, file_parts: list[str]) -> None:
    with open(path_to_file, "wb") as file:
        subprocess.run(
            ["cat"] + file_parts,
            stdout=file,
            stderr=subprocess.PIPE,
            check=True,
        )


def _delete_file_parts(files: list[str]) -> None:
    try:
        for file in files:
            _delete_file(Path(file))

    except Exception:
        logger.exception("Unable to delete file parts %s", files)


def _delete_file(path_to_file: Path) -> None:
    logger.info("...removing %s file", path_to_file.name)
    path_to_file.unlink(missing_ok=True)
    logger.info("Done")

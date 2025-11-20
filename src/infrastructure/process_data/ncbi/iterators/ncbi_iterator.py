import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from domain.entities import LineagePair, MergedPair, Taxonomy
from infrastructure.process_data.exceptions import IteratorError
from infrastructure.process_data.ncbi.models import PresenterType
from infrastructure.process_data.ncbi.presenters import NCBI_PRESENTERS

logger = logging.getLogger(__name__)


class NCBIIterator:
    def __init__(self, path_to_file: Path, presenter: PresenterType):
        self._path_to_file = path_to_file
        self._presenter = presenter

    @contextmanager
    def _open_file(self, path_to_file: Path):
        try:
            with path_to_file.open("r", encoding="utf-8") as file:
                yield file

        except Exception as e:
            logger.exception("Failed to open file %s", path_to_file)
            raise IteratorError(f"Failed to open file {path_to_file}") from e

    def __iter__(self) -> Iterator[MergedPair | LineagePair | Taxonomy]:
        with self._open_file(self._path_to_file) as file:
            yield from NCBI_PRESENTERS[self._presenter].present(file)

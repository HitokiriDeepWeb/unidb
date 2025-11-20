import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

from domain.entities import Taxonomy
from infrastructure.process_data.exceptions import IteratorError
from infrastructure.process_data.ncbi.models import NameData
from infrastructure.process_data.ncbi.parsers import NamesParser, RanksParser

logger = logging.getLogger(__name__)


class TaxonomyIterator:
    """Taxonomy iterator, yields dataclass_name(rank, name, tax_name)."""

    def __init__(
        self,
        path_to_names: Path,
        path_to_ranks: Path,
    ):
        self._path_to_names = path_to_names
        self._path_to_ranks = path_to_ranks
        self._names_parser = NamesParser()
        self._ranks_parser = RanksParser()

    @contextmanager
    def _open_file(self, path_to_file: Path):
        try:
            with path_to_file.open("r", encoding="utf-8") as file:
                yield file

        except Exception as e:
            logger.exception("Failed to open file %s", path_to_file)
            raise IteratorError(f"Failed to open file {path_to_file}") from e

    def __iter__(self) -> Iterator[Taxonomy]:
        """Take 'ranks' from file 'nodes.dmp' and add them to file 'names.dmp'."""
        with (
            self._open_file(self._path_to_ranks) as ranks,
            self._open_file(self._path_to_names) as names,
        ):
            for name_record in names:
                name = self._names_parser.parse(name_record)
                yield from self._taxonomy_gen_if_name_not_none(name, ranks)

    def _taxonomy_gen_if_name_not_none(
        self, name: NameData, ranks: IO
    ) -> Iterator[Taxonomy]:
        if name:
            rank = self._extract_rank(ranks)

            try:
                yield from self._taxonomy_gen(name, rank)

            except Exception as e:
                logger.exception("Failed to build dataclass from %s, %s", name, rank)
                raise IteratorError(
                    f"Failed to build dataclass from {name, rank}"
                ) from e

    def _extract_rank(self, ranks: IO):
        return self._ranks_parser.parse(next(ranks))

    @staticmethod
    def _taxonomy_gen(name: NameData, rank: str) -> Iterator[Taxonomy]:
        if name.specification:
            yield Taxonomy(rank, name.ncbi_id, f"{name.specification}[{name.ncbi_id}]")

        else:
            yield Taxonomy(rank, name.ncbi_id, f"{name.tax_name}[{name.ncbi_id}]")

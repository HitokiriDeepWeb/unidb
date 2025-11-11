from functools import partial
from pathlib import Path

from application.models import IteratorToTable
from core.config import NCBIFiles, UniprotFiles
from domain.entities import Tables
from infrastructure.process_data.ncbi import (
    NCBIIterator,
    PresenterType,
    TaxonomyIterator,
)
from infrastructure.process_data.uniprot.fasta import FastaIterator


def stick_iterators_to_tables(source_folder: Path) -> list[IteratorToTable]:
    lineage_iterator = NCBIIterator(
        path_to_file=source_folder / NCBIFiles.LINEAGE, presenter=PresenterType.LINEAGE
    )
    merged_iterator = NCBIIterator(
        path_to_file=source_folder / NCBIFiles.MERGED, presenter=PresenterType.MERGED
    )
    delnodes_iterator = NCBIIterator(
        path_to_file=source_folder / NCBIFiles.DELNODES,
        presenter=PresenterType.DELNODES,
    )
    taxonomy_iterator = TaxonomyIterator(
        path_to_names=source_folder / NCBIFiles.NAMES,
        path_to_ranks=source_folder / NCBIFiles.RANKS,
    )

    swiss_prot_iterator = FastaIterator(
        path_to_file=source_folder / UniprotFiles.SWISS_PROT
    )
    swiss_prot_isoforms = FastaIterator(
        path_to_file=source_folder / UniprotFiles.SP_ISOFORMS
    )
    iterators_to_tables = [
        IteratorToTable(iterator=lineage_iterator, table=Tables.LINEAGE),
        IteratorToTable(iterator=merged_iterator, table=Tables.MERGED),
        IteratorToTable(iterator=delnodes_iterator, table=Tables.TAXONOMY),
        IteratorToTable(iterator=taxonomy_iterator, table=Tables.TAXONOMY),
        IteratorToTable(iterator=swiss_prot_iterator, table=Tables.UNIPROT),
        IteratorToTable(iterator=swiss_prot_isoforms, table=Tables.UNIPROT),
    ]
    return iterators_to_tables


def create_trembl_iterator_partial(source_folder: Path) -> partial[FastaIterator]:
    sequence_iterator_partial = partial(
        FastaIterator, source_folder / UniprotFiles.TREMBL
    )
    return sequence_iterator_partial


def calculate_workers_to_split_trembl_file(workers_number: int) -> int:
    workers_number_for_small_files = 1
    trembl_workers = workers_number - workers_number_for_small_files
    return trembl_workers if trembl_workers > 0 else 1

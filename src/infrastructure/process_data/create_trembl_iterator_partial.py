from functools import partial
from pathlib import Path

from infrastructure.models import UniprotFiles
from infrastructure.process_data.uniprot.fasta.iterator import FastaIterator


def create_trembl_iterator_partial(source_folder: Path) -> partial[FastaIterator]:
    sequence_iterator_partial = partial(
        FastaIterator, source_folder / UniprotFiles.TREMBL
    )
    return sequence_iterator_partial

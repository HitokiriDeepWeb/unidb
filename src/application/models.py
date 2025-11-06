from dataclasses import dataclass

from domain.entities import Tables
from domain.interfaces import NCBIIteratorProtocol, SequenceIteratorProtocol


@dataclass(frozen=True, slots=True)
class IteratorToTable:
    """
    Iterators that go through the data
    and tables that will be populated with this data.
    """

    iterator: SequenceIteratorProtocol | NCBIIteratorProtocol
    table: Tables

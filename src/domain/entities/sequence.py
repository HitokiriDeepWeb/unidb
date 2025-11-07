import reprlib
from dataclasses import dataclass, fields
from enum import StrEnum


class SequenceSource(StrEnum):
    """
    Source of the sequences. Depends on what kind of sequences file contains.
    TrEMBL contains unreviewed (tr), 'Swiss-Prot' contains reviewed sequences (sp).
    Also file may contain (reviewed) isoforms (sp_iso).
    """

    SWISS_PROT = "sp"
    TREMBL = "tr"
    SP_ISOFORMS = "sp_iso"


@dataclass(frozen=True, slots=True)
class SequenceMetaInfo:
    """
    First part of information block of FASTA record.
    Example of FASTA file: '>sp|P01308'.
    """

    is_reviewed: bool
    accession: str
    source: SequenceSource


@dataclass(frozen=True, slots=True)
class SequenceBioInfo:
    """
    Second part of the information block of the record.
    Example of FASTA file: "INS_HUMAN Insulin OS=Homo sapiens OX=9606 GN=INS PE=1 SV=1"
    """

    entry_name: str
    peptide_name: str
    organism_name: str
    ncbi_id: int


@dataclass(frozen=True, slots=True)
class SequenceRecord:
    """
    Contain main info about sequence provided with the record.
    Example FASTA record:
    >sp|P01308|INS_HUMAN Insulin OS=Homo sapiens OX=9606 GN=INS PE=1 SV=1
    MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAED
    LQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN
    """

    source: SequenceSource
    is_reviewed: bool
    accession: str
    entry_name: str
    peptide_name: str
    ncbi_id: int
    organism_name: str
    sequence: str

    def __repr__(self) -> str:
        cls = self.__class__
        cls_name = cls.__name__
        field_repr: list[str] = []
        indent: str = " " * len(cls_name)

        for field in fields(self):
            value: str = getattr(self, field.name)

            if field.name == "sequence":
                value = reprlib.repr(value)

            field_repr.append(f"{indent + field.name}={value!r}")

        return f"{cls_name}(\n{',\n'.join(field_repr)}\n)"

from domain.entities import (
    SequenceBioInfo,
    SequenceMetaInfo,
    SequenceRecord,
    SequenceSource,
)
from infrastructure.process_data.exceptions import InvalidRecordError


class FastaParser:
    """Parse separate FASTA record and return grouped data."""

    _ORGANISM_NAME_TAG: str = " OS="
    _NCBI_ID_TAG: str = " OX="

    def parse(
        self, raw_sequence_info: str, sequence_parts: list[str]
    ) -> SequenceRecord:
        """Parse FASTA record."""
        try:
            meta_info, biological_info = self._extract_sequence_info(raw_sequence_info)
            sequence = self._get_sequence(sequence_parts)

        except Exception as e:
            raise InvalidRecordError(
                "Invalid record provided. Check file structure, record: "
                f"{raw_sequence_info} sequence parts: {sequence_parts}"
            ) from e

        else:
            return SequenceRecord(
                accession=meta_info.accession,
                is_reviewed=meta_info.is_reviewed,
                source=meta_info.source,
                entry_name=biological_info.entry_name,
                peptide_name=biological_info.peptide_name,
                organism_name=biological_info.organism_name,
                ncbi_id=biological_info.ncbi_id,
                sequence=sequence,
            )

    @staticmethod
    def _get_sequence(sequence_parts: list[str]) -> str:
        if not sequence_parts:
            raise InvalidRecordError("Empty sequence provided. Check file structure")

        return "".join(sequence_parts)

    def _extract_sequence_info(
        self, raw_sequence_info: str
    ) -> tuple[SequenceMetaInfo, SequenceBioInfo]:
        """Extract all required sequence data from FASTA file."""
        if not raw_sequence_info:
            raise InvalidRecordError("Empty sequence provided. Check file structure")

        meta_info, raw_biological_info = self._parse_sequence_info(raw_sequence_info)
        biological_info = self._parse_biological_info(raw_biological_info)
        return (
            SequenceMetaInfo(
                meta_info.is_reviewed,
                meta_info.accession,
                meta_info.source,
            ),
            SequenceBioInfo(
                biological_info.entry_name,
                biological_info.peptide_name,
                biological_info.organism_name,
                biological_info.ncbi_id,
            ),
        )

    def _parse_sequence_info(
        self, raw_sequence_info: str
    ) -> tuple[SequenceMetaInfo, str]:
        """
        Parse first part of the sequence info (review status, accession and source).
        Also return the rest of unprocessed data.
        """

        sequence_info_parts = self._split_sequence_info(raw_sequence_info)
        is_reviewed = self._determine_review_status(sequence_info_parts)
        accession = self._extract_accession(sequence_info_parts)
        source = self._extract_sequence_source(is_reviewed, accession)
        raw_biological_info = self._extract_biological_info(sequence_info_parts)

        return SequenceMetaInfo(is_reviewed, accession, source), raw_biological_info

    @staticmethod
    def _split_sequence_info(raw_sequence_info: str) -> list[str]:
        return raw_sequence_info.split("|", 2)

    def _parse_biological_info(self, raw_biological_info: str) -> SequenceBioInfo:
        """
        Process the second part of sequence data
        (entry name, peptide name, organism name, ncbi id).
        """
        entry_name = self._extract_entry_name(raw_biological_info)
        modified_raw_biological_info = self._remove_entry_name(
            raw_biological_info, entry_name
        )
        peptide_name_end_index, organism_name_end_index = self._get_names_indexes(
            modified_raw_biological_info
        )
        peptide_name = self._extract_peptide_name(
            modified_raw_biological_info, peptide_name_end_index
        )
        organism_name = self._extract_organism_name(
            modified_raw_biological_info,
            peptide_name_end_index,
            organism_name_end_index,
        )
        ncbi_id = self._extract_ncbi_organism_id(
            modified_raw_biological_info, organism_name_end_index
        )
        return SequenceBioInfo(entry_name, peptide_name, organism_name, ncbi_id)

    @staticmethod
    def _remove_entry_name(raw_biological_info: str, entry_name: str) -> str:
        return raw_biological_info.replace(entry_name + " ", "")

    @staticmethod
    def _determine_review_status(sequence_info_parts: list[str]) -> bool:
        # sp = Swiss-Prot - sequences that were reviewed manually.
        status = sequence_info_parts[0] == ">sp"
        return status

    @staticmethod
    def _extract_accession(sequence_info_parts: list[str]) -> str:
        accession = sequence_info_parts[1]
        return accession

    def _extract_sequence_source(
        self, review_status: bool, accession: str
    ) -> SequenceSource:
        iso_suffix = "-"

        if not review_status:
            return SequenceSource.TREMBL

        elif iso_suffix not in accession:
            return SequenceSource.SWISS_PROT

        else:
            return SequenceSource.SP_ISOFORMS

    @staticmethod
    def _extract_biological_info(sequence_info_parts: list[str]) -> str:
        raw_biological_info = sequence_info_parts[2]
        return raw_biological_info

    @staticmethod
    def _extract_entry_name(raw_biological_info: str) -> str:
        entry_name = raw_biological_info.split()[0]
        return entry_name

    def _get_names_indexes(self, raw_biological_info: str) -> tuple[int, int]:
        peptide_name_end_index = raw_biological_info.index(self._ORGANISM_NAME_TAG)
        organism_name_end_index = raw_biological_info.index(self._NCBI_ID_TAG)
        return peptide_name_end_index, organism_name_end_index

    @staticmethod
    def _extract_peptide_name(raw_biological_info: str, end_index: int) -> str:
        peptide_name = raw_biological_info[:end_index]
        return peptide_name

    def _extract_organism_name(
        self, raw_biological_info: str, start_index: int, end_index: int
    ) -> str:
        organism_name = raw_biological_info[start_index:end_index].replace(
            self._ORGANISM_NAME_TAG, ""
        )
        return organism_name

    def _extract_ncbi_organism_id(
        self, raw_biological_info: str, start_index: int
    ) -> int:
        ncbi_organism_id = int(
            raw_biological_info[start_index:]
            .replace(self._NCBI_ID_TAG, "")
            .split(" ")[0]
        )
        return ncbi_organism_id

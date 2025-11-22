from domain.entities import MergedPair
from infrastructure.process_data.exceptions import InvalidRecordError
from infrastructure.process_data.ncbi.models import LineageTaxonomyIDs, NameData
from infrastructure.process_data.ncbi.utils import ncbi_logger


class LineageParser:
    """Parse raw lineage dmp file with lineage taxonomy tables."""

    _LOG_MESSAGE: str = (
        "Invalid record provided. File taxidlineage.dmp might be damaged. "
        "It must have such form: 12345\t|\t1|2|3|4\t|\nCurrent form."
    )

    @ncbi_logger(_LOG_MESSAGE)
    def parse(self, record: str) -> LineageTaxonomyIDs:
        """Parse raw lineage record."""
        record_parts = self._get_record_parts(record)
        main_taxid = self._extract_main_taxid(record, record_parts)
        parent_taxids = self._extract_parent_taxids(record, record_parts)
        return LineageTaxonomyIDs(main_taxid=main_taxid, parent_taxids=parent_taxids)

    @staticmethod
    def _get_record_parts(record: str) -> list[str]:
        delimiter = "\t|\t"

        try:
            return record.strip().split(delimiter)

        except Exception as e:
            raise InvalidRecordError(f"Invalid record provided: {record}") from e

    def _extract_parent_taxids(self, record: str, record_parts: list[str]) -> list[int]:
        """Extract parent taxon ID's of a specific taxon."""
        delimiter = "|"

        try:
            parent_taxids_str = record_parts[1].replace(delimiter, "").split()

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e

        else:
            return [int(parent_taxid) for parent_taxid in parent_taxids_str]

    def _extract_main_taxid(self, record: str, record_parts: list[str]) -> int:
        """Extract main taxon ID."""
        try:
            return int(record_parts[0])

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e


class MergedParser:
    """
    Parse raw merged dmp record from merged.dmp file with merged IDs.
    with deprecated - current ID's.

    Example input line: '12\t|\t74109\t|' (merged.dmp)

    Output line: dataclass_name(12 74109) (deprecated_id - current_id)
    """

    _LOG_MESSAGE = (
        "Invalid record provided. File merged.dmp might be damaged. "
        "It must have such form: 12\t|\t74109\t|\nCurrent form."
    )

    @ncbi_logger(_LOG_MESSAGE)
    def parse(self, record: str) -> MergedPair:
        """Parse raw merged record."""
        record_parts = self._get_record_parts(record)
        deprecated_id = self._extract_deprecated_id(record, record_parts)
        current_id = self._extract_current_id(record, record_parts)
        return MergedPair(deprecated_id=deprecated_id, current_id=current_id)

    @staticmethod
    def _get_record_parts(record: str) -> list[str]:
        delimiter = "\t|\t"

        try:
            return record.strip().split(delimiter)

        except Exception as e:
            raise InvalidRecordError(f"Invalid record provided: {record}") from e

    def _extract_deprecated_id(self, record: str, record_parts: list[str]) -> int:
        try:
            return int(record_parts[0])

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e

    def _extract_current_id(self, record: str, record_parts: list[str]) -> int:
        delimiter = "\t|"

        try:
            return int(record_parts[1].replace(delimiter, ""))

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e


class DelnodesParser:
    """
    Parse raw record in the format: 'no rank|deleted_id|deleted[deleted_id]'.

    Example input line: '3418941\t|' (delnodes.dmp)

    Output: 3418941
    """

    _LOG_MESSAGE = (
        "Invalid record provided. File delnode.dmp might be damaged. "
        "It must have such form: 3418941\t|\nCurrent form:"
    )

    @ncbi_logger(_LOG_MESSAGE)
    def parse(self, record: str) -> int:
        """Parse raw delnode record."""
        return self._extract_deleted_id(record)

    def _extract_deleted_id(self, record: str) -> int:
        delimiter = "\t|"

        try:
            return int(record.strip().replace(delimiter, ""))

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e


class RanksParser:
    """
    Parse raw nodes.dmp record.

    "Example input line: "
    "'39\t|\t80811\t|\tfamily\t|\t\t|\t0\t|\t1\t|\t11\t|\t1\t|\t0\t|\t1\t|->
    ->\t0\t|\t0\t|\tcode compliant\t|\t\t|\t\t|\t0\t|\t0\t|\t1\t|'"

    "Output: 'family'."
    """

    _LOG_MESSAGE = (
        "Invalid record provided. File nodes.dmp might be damaged. "
        "It must have such form: "
        "39\t|\t80811\t|\tfamily\t|\t\t|\t0\t|\t1\t|\t11\t|\t1\t|"
        "\t0\t|\t1\t|\t0\t|\t0\t|\tcode compliant\t|\t\t|\t\t|\t0\t|\t0\t|\t1\t|\n"
        "Current form: "
    )

    @ncbi_logger(_LOG_MESSAGE)
    def parse(self, record: str) -> str:
        """Parse raw nodes record."""
        record_parts = self._get_record_parts(record)
        return self._extract_rank(record, record_parts)

    @staticmethod
    def _get_record_parts(record: str) -> list[str]:
        delimiter = "\t|\t"

        try:
            return record.strip().split(delimiter)

        except Exception as e:
            raise InvalidRecordError(f"Invalid record provided: {record}") from e

    def _extract_rank(self, record: str, record_parts: list[str]):
        try:
            return record_parts[2]

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e


class NamesParser:
    """
    Parse raw names.dmp record.
    Example input line: 2\t|\tBacteria\t|\tBacteria <bacteria>\t|\tscientific name\t|
    Unwanted lines will become None values
    Required lines will be returned in form:
    dataclass_name(2, "Bacteria", "Bacteria<bacteria>").
    """

    _LOG_MESSAGE = (
        "Invalid record provided. File names.dmp might be damaged. "
        "It must have such form: "
        "2\t|\t'tax name'\t|\t'specific name'\t|\tscientific name\t|\nCurrent form:"
    )
    _MISPRINTED_LINE = "'Beach rock 4+5\"'"

    @ncbi_logger(_LOG_MESSAGE)
    def parse(self, record: str) -> NameData | None:
        """Parse raw names record."""
        new_record: str | None = self._prepare_necessary_records(record)
        return self._extract_name_data(new_record)

    def _extract_name_data(self, new_record: str | None) -> NameData | None:
        if not new_record:
            return None

        try:
            ncbi_id, tax_name, specification, *_ = self._split_record(new_record)

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {new_record}") from e

        else:
            return NameData(
                ncbi_id=int(ncbi_id), tax_name=tax_name, specification=specification
            )

    def _split_record(self, new_record: str) -> list[str]:
        delimiter = "\t|\t"

        try:
            return new_record.strip().split(delimiter)

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {new_record}") from e

    def _prepare_necessary_records(self, record: str) -> str | None:
        """Prepare and return line if it has scientific tag otherwise return None."""
        try:
            if self._is_scientific_name(record):
                return self._remove_misprint(record)

            return None

        except Exception as e:
            raise InvalidRecordError(f"{self._LOG_MESSAGE}: {record}") from e

    def _is_scientific_name(self, record: str) -> bool:
        scientific_tag = "|\tscientific name\t|"
        return scientific_tag in record

    def _remove_misprint(self, record: str) -> str:
        if self._is_record_with_misprint(record):
            fixed_line = "'Beach rock 4+5'"
            return record.replace(self._MISPRINTED_LINE, fixed_line)

        return record

    def _is_record_with_misprint(self, record: str) -> bool:
        return self._MISPRINTED_LINE in record

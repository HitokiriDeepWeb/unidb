import argparse
from pathlib import Path

from core.models import LogConfig, LogType
from domain.entities import BASE_DIR


def positive_int(value: int | str) -> int:
    try:
        number = int(value)

    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Inappropriate value provided {value}") from e

    if number <= 0:
        raise argparse.ArgumentTypeError("Value must be a positive non-zero number")

    return number


parser = argparse.ArgumentParser(description=("UniProt database setup"))
parser.add_argument("--dbname", "-d", required=True, type=str)
parser.add_argument("--dbuser", "-U", required=True, type=str)
parser.add_argument("--password", "-p", type=str)
parser.add_argument("--port", "-P", default=5432, type=positive_int)
parser.add_argument("--host", "-u", default="localhost", type=str)
parser.add_argument(
    "--processes",
    "-j",
    default=1,
    type=positive_int,
    help="How many processes will the work be distributed to",
)
parser.add_argument(
    "--path-to-source-files",
    "-k",
    type=Path,
    help="If you prepared all the source files manually and "
    "do not want script to download and unpack them",
)
parser.add_argument(
    "--path-to-source-archives",
    "-z",
    type=Path,
    help="If you downloaded all the source archives (tar, gz files) manually and "
    "do not want script to download them",
)
parser.add_argument(
    "-y",
    action="store_true",
    help="If you want to automatically say 'yes' "
    "to all the conditions and accept setup",
)
parser.add_argument(
    "--trgm",
    "-i",
    action="store_true",
    help="Build trigram index on sequence column in uniprot_kb table",
)
parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    help="How detailed will logging be",
)
parser.add_argument(
    "--no-clean-up-on-failure",
    "-g",
    action="store_true",
    help="Prevent source files and database clean up on failure",
)
parser.add_argument(
    "--logtype",
    "-t",
    default=LogType.CONSOLE,
    type=LogType,
    help="Where to log info. Either 'console' or 'file'",
)
parser.add_argument("--loglevel", "-l", default="info", type=str)
parser.add_argument(
    "--logpath",
    "-L",
    default=BASE_DIR / "logs",
    type=Path,
    help="Directory path to log files",
)

app_args = parser.parse_args()

log_config = LogConfig(
    log_type=app_args.logtype,
    log_path=app_args.logpath,
    log_level=app_args.loglevel,
    verbose=app_args.verbose,
)

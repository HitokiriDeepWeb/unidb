import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

import asyncpg
import docker
import pytest
from docker import DockerClient
from docker.models.containers import Container

from application.services import (
    DatabaseFileCopier,
    SetupUniprotDatabase,
    UniprotOperator,
)
from infrastructure.database.postgresql import (
    ConnectionConfig,
    ConnectionPoolConfig,
    PostgreSQLAdapter,
    PostgreSQLUniprotLifecycle,
    get_available_connections_amount,
    setup_connection_pool_config,
    setup_queue_config,
)
from infrastructure.models import NCBIFiles, UniprotFiles
from infrastructure.preparation.prepare_files import (
    FilePreparer,
    UpdateChecker,
)
from infrastructure.preparation.prepare_files.download import Downloader
from infrastructure.preparation.prepare_system import (
    SystemPreparer,
    SystemPreparerConfig,
)
from infrastructure.process_data import (
    calculate_workers_to_split_trembl_file,
    create_trembl_iterator_partial,
    stick_iterators_to_tables,
)
from infrastructure.process_data.uniprot.fasta import ChunkRangeIterator

DB_NAME: str = "testdb"
DB_USER: str = "postgres"
DB_HOST: str = "localhost"
DB_PORT: str = "5468"
DB_PASSWORD: str = "password"


class HealthcheckStatus(StrEnum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class UnhealthyContainerError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class DBTestConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    internal_container_port: str


DATABASE_ENV = DBTestConfig(
    host=DB_HOST,
    port=int(DB_PORT),
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    internal_container_port="5432",
)


nodes_content: str = (
    "9606\t|\t9605\t|\tspecies\t|\tHS\t|\t5\t|\t1\t|"
    "\t1\t|\t1\t|\t2\t|\t1\t|\t1\t|\t0\t|\tcode compliant; specified\t|\t"
    "\t|\t\t|\t1\t|\t0\t|\t1\t|\n"
    "9913\t|\t9903\t|\tspecies\t|\tBT\t|\t2\t|\t1\t|"
    "\t1\t|\t1\t|\t2\t|\t1\t|\t1\t|\t0\t|\tcode compliant; specified\t|\t"
    "\t|\t\t|\t1\t|\t0\t|\t1\t|\n"
    "131567\t|\t1\t|\tno rank\t|\t\t|\t8\t|\t1\t|\t1\t|\t1\t|\t0\t|\t1\t|"
    "\t1\t|\t0\t|\t\t|\t\t|\t\t|\t0\t|\t0\t|\t1\t|\n"
    "2759\t|\t131567\t|\tsuperkingdom\t|\t\t|\t1\t|\t0\t|\t1\t|\t0\t|"
    "\t1\t|\t0\t|\t0\t|\t0\t|\t\t|\t11\t|\t0\t|\t0\t|\t0\t|\t1\t|\n"
    "33154\t|\t2759\t|\tclade\t|\t\t|\t4\t|\t0\t|\t1\t|\t1\t|\t1\t|\t1\t|"
    "\t1\t|\t0\t|\t\t|\t\t|\t0\t|\t0\t|\t0\t|\t1\t|"
)

names_content: str = (
    "9606\t|\tHomo sapiens\t|\t\t|\tscientific name\t|\n"
    "9913\t|\tBos taurus\t|\t\t|\tscientific name\t|\n"
    "131567\t|\tcellular organisms\t|\t\t|\tscientific name\t|\n"
    "2759\t|\tEukaryota\t|\t\t|\tscientific name\t|\n"
    "33154\t|\tOpisthokonta\t|\t\t|\tscientific name\t|"
)

merged_content: str = "272461\t|\t9913\t|\n272470\t|\t192252\t|"

lineage_content: str = "9606\t|\t131567 2759 33154 \t|\n9913\t|\t131567 2759 33154 \t|"

delnodes_content: str = (
    "3122894\t|\n"
    "3122893\t|\n"
    "3122892\t|\n"
    "3122891\t|\n"
    "3122890\t|\n"
    "3122889\t|\n"
    "3122888\t|\n"
    "3122887\t|\n"
    "3122886\t|\n"
    "3122885\t|"
)

uniprot_sprot_content: str = (
    ">sp|A0JNW5|BLT3B_HUMAN Bridge-like lipid transfer protein family member 3B "
    "OS=Homo sapiens OX=9606 GN=BLTP3B PE=1 SV=2\n"
    "MAGIIKKQILKHLSRFTKNLSPDKINLSTLKGEGELKNLELDEEVLQNMLDLPTWLAINK\n"
    ">sp|A0JP26|POTB3_HUMAN POTE ankyrin domain family member B3 "
    "OS=Homo sapiens OX=9606 GN=POTEB3 PE=1 SV=2\n"
    "MGKCCHHCFPCCRGSGTSNVGTSGDHDNSFMKTLRSKMGKWCCHCFPCCRGSGKSNVGTW\n"
    ">sp|A0PK11|CLRN2_HUMAN Clarin-2 OS=Homo sapiens OX=9606 GN=CLRN2 PE=1 SV=1\n"
    "MPGWFKKAWYGLASLLSFSSFILIIVALVVPHWLSGKILCQTGVDLVNATDRELVKFIGD\n"
    ">sp|A1L3X0|ELOV7_HUMAN Very long chain fatty acid elongase 7 "
    "OS=Homo sapiens OX=9606 GN=ELOVL7 PE=1 SV=1\n"
    "PFELKKAMITYNFFIVLFSVYMCYEFVMSGWGIGYSFRCDIVDYSRSPTALRMARTCWLY\n"
    ">sp|A2A2Y4|FRMD3_HUMAN FERM domain-containing protein 3 "
    "OS=Homo sapiens OX=9606 GN=FRMD3 PE=1 SV=1\n"
    "MFASCHCVPRGRRTMKMIHFRSSSVKSLSQEMRCTIRLLDDSEISCHIQRETKGQFLIDH\n"
    ">sp|A2RU14|TM218_HUMAN Transmembrane protein 218 "
    "OS=Homo sapiens OX=9606 GN=TMEM218 PE=1 SV=1\n"
    "MAGTVLGVGAGVFILALLWVAVLLLCVLLSRASGAARFSVIFLFFGAVIITSVLLLFPRA\n"
    ">sp|A4D1B5|GSAP_HUMAN Gamma-secretase-activating protein "
    "OS=Homo sapiens OX=9606 GN=GSAP PE=1 SV=2\n"
    "MALRLVADFDLGKDVLPWLRAQRAVSEASGAGSGGADVLENDYESLHVLNVERNGNIIYT\n"
    ">sp|A1A519|F170A_HUMAN Protein FAM170A "
    "OS=Homo sapiens OX=9606 GN=FAM170A PE=1 SV=1\n"
    "MKRRQKRKHLENEESQETAEKGGGMSKSQEDALQPGSTRVAKGWSQGVGEVTSTSEYCSC\n"
    ">sp|A2RUB6|CCD66_HUMAN Coiled-coil domain-containing protein 66 "
    "OS=Homo sapiens OX=9606 GN=CCDC66 PE=1 SV=4\n"
    "CIGSEKLLQKKPVGSETSQAKGEKNGMTFSSTKDLCKQCIDKDCLHIQKEISPATPNMQK\n"
    ">sp|A2RUC4|TYW5_HUMAN tRNA wybutosine-synthesizing protein 5 "
    "OS=Homo sapiens OX=9606 GN=TYW5 PE=1 SV=1\n"
    "MAGQHLPVPRLEGVSREQFMQHLYPQRKPLVLEGIDLGPCTSKWTVDYLSQVGGKKEVKI\n"
    "HVAAVAQMDFISKNFVYRTLPFDQLVQRAAEEKHKEFFVSEDEKYYLRSLGEDPRKDVAD"
)

uniprot_varsplic_content: str = (
    ">sp|P31946-2|1433B_HUMAN Isoform Short of 14-3-3 protein beta/alpha "
    "OS=Homo sapiens OX=9606 GN=YWHAB\n"
    "VISSIEQKTERNEKKQQMGKEYREKIEAELQDICNDVLELLDKYLIPNATQPESKVFYLK\n"
    ">sp|P62258-2|1433E_HUMAN Isoform SV of 14-3-3 protein epsilon "
    "OS=Homo sapiens OX=9606 GN=YWHAE\n"
    "MVESMKKVAGMDVELTVEERNLLSVAYKNVIGARRASWRIISSIEQKEENKGGEDKLKMI\n"
    ">sp|P31947-2|1433S_HUMAN Isoform 2 of 14-3-3 protein sigma "
    "OS=Homo sapiens OX=9606 GN=SFN\n"
    "MERASLIQKAKLAEQAERYEDMAAFMKGAVEKGEELSCEERNLLSVAYKNVVGGQRAAWR\n"
    ">sp|P63104-2|1433Z_HUMAN Isoform 2 of 14-3-3 protein zeta/delta "
    "OS=Homo sapiens OX=9606 GN=YWHAZ\n"
    "MSQPCRKLWRHNYETSSCIEFLKSLLEKFLIPNASQAESKVFYLKMKGDYYRYLAEVAAG\n"
    ">sp|Q96QU6-2|1A1L1_HUMAN Isoform 2 of 1-aminocyclopropane-1-carboxylate "
    "synthase-like protein 1 OS=Homo sapiens OX=9606 GN=ACCS\n"
    "MFTLPQKDFRAPTTCLGPTCMQDLGSSHGEDLEGECSRKLDQKLPELRGVGDPAMISSDT\n"
    ">sp|Q2LL38-2|AAKG3_BOVIN Isoform 2 of 5'-AMP-activated protein kinase subunit "
    "gamma-3 OS=Bos taurus OX=9913 GN=PRKAG3\n"
    "MEPAELEHALCGTPSWSSFGGPEHQEMSFLEQGDSTSWPSPAMTTSAEISLGEQRTKVSR\n"
    "WKSQEDVEERELPGLEGGPQSRAAAESTGLEATFPKATPLAQATPLSAVGTPTTERDSLP\n"
    ">sp|Q2LL38-3|AAKG3_BOVIN Isoform 3 of 5'-AMP-activated protein kinase subunit "
    "gamma-3 OS=Bos taurus OX=9913 GN=PRKAG3\n"
    "MEPAELEHALCGSLFSTQTPSWSSFGGPEHQEMSFLEQGDSTSWPSPAMTTSAEISLGEQ\n"
    "RTKVSRWKSQEDVEERELPGLEGGPQSRAAAESTGLEATFPKATPLAQATPLSAVGTPTT\n"
    ">sp|Q2LL38-4|AAKG3_BOVIN Isoform 4 of 5'-AMP-activated protein kinase subunit "
    "gamma-3 OS=Bos taurus OX=9913 GN=PRKAG3\n"
    "MEPAELEHALCGTPSWSSFGGPEHQEMSFLEQGDSTSWPSPAMTTSAEISLGEQRTKVSR\n"
    "ADCTASASSSSTDDLDQGIEFSAPAAWGDELGLVEERPAQCPSPQVPVLRLGWDDELRKP\n"
    ">sp|A6QNS3-2|ABR_BOVIN Isoform 2 of Active breakpoint cluster region-related "
    "protein OS=Bos taurus OX=9913 GN=ABR\n"
    "MEILLIIRFCCNCTYALLYKPIDRVTRSTLVLHDLLKHTPVDHPDYPLLQDALRISQNFL\n"
    ">sp|P23795-2|ACES_BOVIN Isoform H of Acetylcholinesterase "
    "OS=Bos taurus OX=9913 GN=ACHE\n"
    "MRPPWCPLHTPSLTPPLLLLLFLIGGGAEAEGPEDPELLVMVRGGRLRGLRLMAPRGPVS"
)

uniprot_trembl_content: str = (
    ">tr|I7CLV3|I7CLV3_BOVIN Insulin (Fragment) OS=Bos taurus OX=9913 PE=2 SV=1\n"
    "FVNQHLCGSHLVEALYLVCGERGFFYTPKARREVEGPQVGALELAGGPGAGGLEGPPQKR\n"
    ">tr|A5PJB2|A5PJB2_BOVIN Insulin OS=Bos taurus OX=9913 GN=INS PE=2 SV=1\n"
    "MALWTRLAPLLALLALWAPAPARAFVNQHLCGSHLVEALYLVCGERGFFYTPKARREVEG\n"
    ">tr|Q17QJ6|Q17QJ6_BOVIN B-cell lymphoma/leukemia 10 "
    "OS=Bos taurus OX=9913 GN=BCL10 PE=2 SV=1\n"
    "MEPTAPSLTEEDLTEVKKDALENLRVYLCEKIIAERHFDHLRAKKILSREDTEEISCRTS\n"
    ">tr|A4GX95|A4GX95_BOVIN Somatotropin OS=Bos taurus OX=9913 PE=2 SV=1\n"
    "MMAAGPRTSLLLAFTLLCLPWTQVVGAFPAMSLSGLFANAVLRAQHLHQLAADTFKEFER\n"
    ">tr|B5B3R8|B5B3R8_BOVIN Alpha-S1-casein OS=Bos taurus OX=9913 "
    "GN=CSN1S1 PE=2 SV=1\n"
    "MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNELSKDIG\n"
    ">tr|F1MZV2|F1MZV2_BOVIN Charged multivesicular body protein 5 "
    "OS=Bos taurus OX=9913 GN=CHMP5 PE=3 SV=1\n"
    "MNRFFGKAKPKAPPPSLTDCIGTVDSRAESIDKKISRLDAELVKYKDQIKKMREGPAKNM\n"
    ">tr|A0A3Q1LW04|A0A3Q1LW04_BOVIN Phosphoinositide-3-kinase regulatory subunit 1 "
    "OS=Bos taurus OX=9913 GN=PIK3R1 PE=3 SV=2\n"
    "MYNTVWNMEDLDLEYAKTDINCGTDLMFYIEMDPPALPPKPPKPTTVANNGMNNNMSLQD\n"
    ">tr|A0A3Q1MXQ5|A0A3Q1MXQ5_BOVIN Phosphatidylinositol 3,4,5-trisphosphate "
    "3-phosphatase and dual-specificity protein phosphatase PTEN "
    "OS=Bos taurus OX=9913 GN=PTEN PE=3 SV=2\n"
    "MTAIIKEIVSRNKRRYQEDGFDLDLTYIYPNIIAMGFPAERLEGVYRNNIDDVVRCAERH\n"
    "YDTAKFNCRVAQYPFEDHNPPQLELIKPFCEDLDQWLSEDDNHVAAIHCKAGKGRTGVMI\n"
    ">tr|E1B9U0|E1B9U0_BOVIN Scleraxis bHLH transcription factor "
    "OS=Bos taurus OX=9913 GN=SCX PE=4 SV=4\n"
    "MSFAMLRSAPPGRYLYPEVSPLSEDEDRGSESSGSDEKPCRVHAARCGLQGARRRAGGRR\n"
    ">tr|A0AAA9SDZ8|A0AAA9SDZ8_BOVIN Sterol carrier protein 2 "
    "OS=Bos taurus OX=9913 GN=SCP2 PE=4 SV=1\n"
    "MSLVASQSPLRNRVFVVGVGMTKFTKPGVENRDYPDLAKEAGQKALADAQIPYSAVEQAC"
)


@pytest.fixture(autouse=True)
def nodes_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / NCBIFiles.RANKS
    path_to_file.open("w").write(nodes_content)


@pytest.fixture(autouse=True)
def names_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / NCBIFiles.NAMES
    path_to_file.open("w").write(names_content)


@pytest.fixture(autouse=True)
def merged_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / NCBIFiles.MERGED
    path_to_file.open("w").write(merged_content)


@pytest.fixture(autouse=True)
def lineage_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / NCBIFiles.LINEAGE
    path_to_file.open("w").write(lineage_content)


@pytest.fixture(autouse=True)
def delnodes_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / NCBIFiles.DELNODES
    path_to_file.open("w").write(delnodes_content)


@pytest.fixture(autouse=True)
def uniprot_sprot_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / UniprotFiles.SWISS_PROT
    path_to_file.open("w").write(uniprot_sprot_content)


@pytest.fixture(autouse=True)
def uniprot_sprot_varsplic_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / UniprotFiles.SP_ISOFORMS
    path_to_file.open("w").write(uniprot_varsplic_content)


@pytest.fixture(autouse=True)
def uniprot_trembl_file(tmp_path: Path) -> None:
    path_to_file = tmp_path / UniprotFiles.TREMBL
    path_to_file.open("w").write(uniprot_trembl_content)


@pytest.fixture(scope="session", autouse=True)
def test_environment_lifecycle(request) -> None:
    client = _create_docker_client()

    postgres_container = _setup_postgres_container(client)

    _wait_for_container_healthcheck(postgres_container)

    def remove_container():
        postgres_container.stop()
        postgres_container.remove()

    request.addfinalizer(remove_container)


def _create_docker_client() -> DockerClient:
    return docker.from_env()


def _setup_postgres_container(client: DockerClient) -> Container:
    container = client.containers.run(
        image="postgres:17-alpine",
        environment={
            "POSTGRES_DB": DATABASE_ENV.dbname,
            "POSTGRES_PASSWORD": DATABASE_ENV.password,
            "POSTGRES_USER": DATABASE_ENV.user,
        },
        healthcheck={
            "test": [
                "CMD-SHELL",
                f"pg_isready -U {DATABASE_ENV.user} -d {DATABASE_ENV.dbname}",
            ],
            "interval": 5 * 10**9,
            "retries": 5,
            "timeout": 5 * 10**9,
            "start_period": 10**10,
        },
        ports={f"{DATABASE_ENV.internal_container_port}/tcp": DATABASE_ENV.port},
        detach=True,
    )
    return container


def _wait_for_container_healthcheck(container: Container) -> None:
    container.reload()
    while (
        status := container.attrs["State"]["Health"]["Status"]
    ) != HealthcheckStatus.HEALTHY:
        if status == HealthcheckStatus.UNHEALTHY:
            raise UnhealthyContainerError("Container healthcheck failed")
        time.sleep(1)
        container.reload()


async def _compose_dependencies(
    path_to_files: Path,
) -> tuple[SetupUniprotDatabase, int, ConnectionConfig]:
    trgm_required = True
    uniprot_lifecycle = PostgreSQLUniprotLifecycle(trgm_required=trgm_required)
    postgresql_copy_adapter = PostgreSQLAdapter()
    file_preparer = FilePreparer(
        source_folder=path_to_files, preparation_is_required=False
    )

    single_connection_config = _get_connection_config()
    available_connections = await get_available_connections_amount(
        asdict(single_connection_config)
    )
    workers_number = 8
    connection_pool_config: ConnectionPoolConfig = setup_connection_pool_config(
        **asdict(single_connection_config),
        workers_number=workers_number,
        available_connections=available_connections,
    )
    db_copier = _get_database_file_copier(
        path_to_files=path_to_files,
        workers_number=workers_number,
        available_connections=available_connections,
        postgresql_copy_adapter=postgresql_copy_adapter,
        connection_pool_config=connection_pool_config,
    )
    uniprot_operator = UniprotOperator(
        uniprot_lifecycle=uniprot_lifecycle, db_connector=postgresql_copy_adapter
    )
    update_checker = UpdateChecker()
    downloader = Downloader()
    system_preparer_config = SystemPreparerConfig(
        download_is_required=False, trgm_required=True, accept_setup_automatically=True
    )
    system_preparer = SystemPreparer(system_preparer_config)
    uniprot_setup = SetupUniprotDatabase(
        uniprot_operator=uniprot_operator,
        file_preparer=file_preparer,
        db_copier=db_copier,
        system_preparer=system_preparer,
        db_pool_config=asdict(connection_pool_config),
        downloader=downloader,
        update_checker=update_checker,
    )
    return uniprot_setup, workers_number, single_connection_config


def _get_connection_config() -> ConnectionConfig:
    return ConnectionConfig(
        host=DATABASE_ENV.host,
        database=DATABASE_ENV.dbname,
        password=DATABASE_ENV.password,
        port=DATABASE_ENV.port,
        user=DATABASE_ENV.user,
    )


def _get_database_file_copier(
    path_to_files: Path,
    workers_number: int,
    available_connections: int,
    postgresql_copy_adapter: PostgreSQLAdapter,
    connection_pool_config: ConnectionPoolConfig,
) -> DatabaseFileCopier:
    iterators_to_tables = stick_iterators_to_tables(path_to_files)
    queue_config = setup_queue_config(workers_number, available_connections)

    trembl_workers_number = calculate_workers_to_split_trembl_file(workers_number)
    trembl_path = path_to_files / UniprotFiles.TREMBL
    chunk_range_iterator = ChunkRangeIterator(
        path_to_file=trembl_path,
        workers_number=trembl_workers_number,
    )
    trembl_iterator = create_trembl_iterator_partial(path_to_files)
    return DatabaseFileCopier(
        db_adapter=postgresql_copy_adapter,
        queue_config=queue_config,
        connection_pool_config=asdict(connection_pool_config),
        trembl_iterator=trembl_iterator,  # type: ignore
        chunk_range_iterator=chunk_range_iterator,
        iterators_to_tables=iterators_to_tables,
    )


@pytest.mark.asyncio
async def test_postgresql_uniprot_setup(tmp_path: Path):
    # Arrange.
    (
        uniprot_setup,
        workers_number,
        single_connection_config,
    ) = await _compose_dependencies(tmp_path)

    query = """
            SELECT u.accession
            FROM uniprot_kb u
            JOIN taxonomy t ON u.ncbi_organism_id = t.ncbi_taxon_id
            WHERE ncbi_taxon_id = 9606
            AND u.source = 'sp'
            AND u.sequence like '%KHL%'
            """
    expected_result = [dict(accession="A0JNW5"), dict(accession="A1A519")]

    # Act.
    await uniprot_setup.setup(workers_number=workers_number, download_is_required=False)

    conn = await asyncpg.connect(**asdict(single_connection_config))
    rows = await conn.fetch(query)
    result: list[dict[str, str]] = [dict(row) for row in rows]

    await conn.close()

    # Assert.
    assert result == expected_result

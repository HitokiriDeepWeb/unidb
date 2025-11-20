import time
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import docker
import pytest
from docker import DockerClient
from docker.models.containers import Container

from src.core.config import NCBIFiles, UniprotFiles

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
content = (
    ">tr|A0A023T699|A0A023T699_EMCV Genome polyprotein "
    "OS=Encephalomyocarditis virus OX=12104 PE=3 SV=1\n"
    "MATTMEQETCAHPLTFEECPKCSALQYRNGF\n"
    "YLLKYDEEWYPEELLIDGEDDVFDPELDMES\n"
    "VEYRWRSLFW\n"
    ">sp|A0A076FVY1|A0A076FVY1_BATSU Tyrosine-protein kinase receptor (Fragment) "
    "OS=Bathyergus suillus OX=10172 GN=IGF1R PE=2 SV=1\n"
    "ASELENFMGLIEVVTGYVKIRHSHALVSLSF\n"
    "LKNLRQILGEEQLEGNYSFYVLDNQNLQQPG\n"
    "VLVLRASFDERQPYAHMNGGRTNERA\n"
    "LPLPQSSTC\n"
    ">tr|A0A076G1H5|A0A076G1H5_FUKDA Tyrosine-protein kinase receptor (Fragment) "
    "OS=Fukomys damarensis OX=885580 GN=IGF1R PE=2 SV=1\n"
    "ICGPGIDIRNDYQQLKRLENCTVIEGYLHILL\n"
    "ISKAEDYRSYRFPKLTVITEYLLLFRVAGGRT\n"
    "NERALPLPQSSTC\n"
    ">sp|A0A091CJV8-1|A0A091CJV8_FUKDA non-specific "
    "serine/threonine protein kinase "
    "OS=Fukomys damarensis OX=885580 GN=H920_19768 PE=3 SV=1\n"
    "MAQKENAYPWPYGRQTSQSGLNTLPQRVLRKE\n"
    "PATPSTLVLMSRSNGQATAVPGQKVVENDLIS\n"
    "KLLKHNPSERLPLAQVSAHPWVQAHSKRVLPPSAP\n"
    ">tr|A0A091CK25|A0A091CK25_FUKDA non-specific serine/threonine protein kinase "
    "OS=Fukomys damarensis OX=885580 GN=H920_19633 PE=3 SV=1\n"
    "MSAEVRLRRLQQLALDPSFLGLEPLLDLLLGV\n"
    "HQELGASDLAQDKYVADFLQWAEPIVARALGC\n"
    "FGLVAHAGYLAPGWRRPGTAFTP\n"
    ">tr|A0A091CKG8|A0A091CKG8_FUKDA "
    "Succinate dehydrogenase [ubiquinone] iron-sulfur subunit, mitochondrial "
    "OS=Fukomys damarensis OX=885580 GN=H920_19443 PE=3 SV=1\n"
    "MAAVAGFSLRRRFPATVLGGSCLQACRGAQTA\n"
    "ADRAPRIKKFAIYRWDPDKTGDKPRMQTAVR"
)


@pytest.fixture
def test_fasta(tmp_path: Path) -> Iterator[Path]:
    path_to_file = tmp_path / "uniprot.fasta"

    with path_to_file.open("w") as file:
        file.write(content)

    yield path_to_file


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
def uniprot_sprot_file(tmp_path: Path) -> Path:
    path_to_file = tmp_path / UniprotFiles.SWISS_PROT
    path_to_file.open("w").write(uniprot_sprot_content)
    return path_to_file


@pytest.fixture(autouse=True)
def uniprot_sprot_varsplic_file(tmp_path: Path) -> Path:
    path_to_file = tmp_path / UniprotFiles.SP_ISOFORMS
    path_to_file.open("w").write(uniprot_varsplic_content)
    return path_to_file


@pytest.fixture(autouse=True)
def uniprot_trembl_file(tmp_path: Path) -> Path:
    path_to_file = tmp_path / UniprotFiles.TREMBL
    path_to_file.open("w").write(uniprot_trembl_content)
    return path_to_file


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

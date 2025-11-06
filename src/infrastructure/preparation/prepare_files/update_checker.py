import asyncio
import logging
from pathlib import Path

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from application.services.exceptions import NoUpdateRequired
from infrastructure.preparation.common_types import Link
from infrastructure.preparation.constants import LAST_MODIFIED_DATE, UNIPROT_SP_LINK

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Find and save information about update."""

    def __init__(
        self,
        url: Link = UNIPROT_SP_LINK,
        path_to_modification_date: Path = LAST_MODIFIED_DATE,
    ):
        self._current_modification_date: str | None = None
        self._request_timeout = ClientTimeout(total=60)
        self._url = url
        self._path_to_modification_date = path_to_modification_date

    async def need_update(self) -> bool:
        """Check if database that was set up earlier needs update."""
        logger.info("...checking updates")

        async with ClientSession(raise_for_status=True) as session:
            self._current_modification_date = await self._get_modification_date(session)

            # Check if previous database setup is still up to date.
            previous_modification_date = self._get_previous_modification_date()
            need_update = self._database_is_not_up_to_date(previous_modification_date)
            return self._manage_information_about_update(need_update)

    def _manage_information_about_update(self, need_update: bool) -> bool:
        if need_update:
            logger.info(
                "New version from %s is available", self._current_modification_date
            )
            return need_update

        else:
            logger.info("UniProt database is up to date")
            raise NoUpdateRequired

    def save_database_update_time(self) -> None:
        """
        To know wnen to update database -
        save UniProt files modification time to local file.
        """
        if self._current_modification_date:
            self._path_to_modification_date.open("w").write(
                self._current_modification_date
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _get_modification_date(self, session: ClientSession) -> str:
        try:
            return await self._try_get_modification_date(session)

        except aiohttp.ClientConnectionError:
            logger.exception("Make sure your network connection is fine")
            raise

        except Exception:
            logger.exception(
                "Unable to reveal last time official uniprot database was updated"
            )
            raise

    async def _try_get_modification_date(self, session: ClientSession) -> str:
        timeout = self._request_timeout

        async with session.head(url=self._url, timeout=timeout) as resp:
            current_modification_date: str = resp.headers["last-modified"]
            logger.debug("modification date: %s", current_modification_date)
            return current_modification_date

    def _database_is_not_up_to_date(
        self, previous_modification_date: str | None
    ) -> bool:
        if previous_modification_date:
            return previous_modification_date != self._current_modification_date

        return True

    def _get_previous_modification_date(self) -> str | None:
        try:
            return self._path_to_modification_date.open("r").readline()

        except FileNotFoundError:
            pass

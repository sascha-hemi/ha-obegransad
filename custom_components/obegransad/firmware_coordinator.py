import logging
from dataclasses import dataclass
from typing import Self

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .connector import ObegransadConnector
from .connector.exceptions import ObegransadException
from .connector.model import ObegransadFirmwareData, ObegransadReleaseData
from .const import DOMAIN, FIRMWARE_ASSET_NAME, FIRMWARE_GITHUB_REPO, FIRMWARE_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class ObegransadFirmwareStatus:
    installed: ObegransadFirmwareData
    latest: ObegransadReleaseData


class ObegransadFirmwareUpdateCoordinator(DataUpdateCoordinator[ObegransadFirmwareStatus]):
    """Polls the device's own version and the latest GitHub release.

    Runs on a much longer interval than the main device-state coordinator:
    the device version rarely changes and GitHub's unauthenticated API is
    rate-limited to 60 requests/hour per IP.
    """

    obegransad_connector: ObegransadConnector

    def __init__(self: Self, hass: HomeAssistant, connector: ObegransadConnector) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_firmware",
            update_interval=FIRMWARE_UPDATE_INTERVAL,
            update_method=self.update_data,
        )
        self.obegransad_connector = connector

    async def update_data(self: Self) -> ObegransadFirmwareStatus:
        try:
            installed = await self.obegransad_connector.get_firmware_version()
            latest = await self.obegransad_connector.get_latest_release(
                FIRMWARE_GITHUB_REPO, FIRMWARE_ASSET_NAME
            )
            return ObegransadFirmwareStatus(installed=installed, latest=latest)
        except ObegransadException as err:
            raise UpdateFailed(err) from err

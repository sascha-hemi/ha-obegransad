import logging
from typing import Self

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .connector import ObegransadConnector, ObegransadDeviceData
from .connector.exceptions import ObegransadException
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ObegransadDataUpdateCoordinator(DataUpdateCoordinator[ObegransadDeviceData]):

    obegransad_connector: ObegransadConnector

    def __init__(self: Self, hass: HomeAssistant, host: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            update_method=self.update_data,
        )
        self.obegransad_connector = ObegransadConnector(
            async_get_clientsession(hass), host
        )
        # Set by update.py around a firmware install. The device is a
        # single-core ESP32 running a blocking flash write during OTA; on
        # real hardware, this coordinator's normal 10s /api/info poll
        # firing concurrently with an in-progress OTA upload was observed
        # to hang the device mid-write. Skip polling while an install runs.
        self.ota_in_progress = False

    async def update_data(self: Self) -> ObegransadDeviceData:
        if self.ota_in_progress:
            return self.data
        try:
            return await self.obegransad_connector.get_data()
        except ObegransadException as err:
            raise UpdateFailed(err) from err

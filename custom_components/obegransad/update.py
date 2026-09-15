from __future__ import annotations

import logging
from typing import Any, Self

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_OTA_PASSWORD,
    CONF_OTA_USERNAME,
    DEFAULT_OTA_PASSWORD,
    DEFAULT_OTA_USERNAME,
)
from .entity import ObegransadEntity
from .firmware_coordinator import ObegransadFirmwareUpdateCoordinator
from .typing_helpers import ObegransadConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ObegransadConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime_data = entry.runtime_data
    async_add_entities(
        [
            ObegransadFirmwareUpdateEntity(
                runtime_data.firmware_coordinator, entry
            )
        ]
    )


class ObegransadFirmwareUpdateEntity(ObegransadEntity, UpdateEntity):
    """Firmware update entity backed by the device's /api/version endpoint
    and the latest GitHub release of ph1p/ikea-led-obegraensad."""

    _attr_translation_key = "firmware"
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    )

    coordinator: ObegransadFirmwareUpdateCoordinator

    def __init__(
        self: Self,
        coordinator: ObegransadFirmwareUpdateCoordinator,
        config_entry: ObegransadConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.data[CONF_HOST]}_firmware_update"

    @property
    def installed_version(self: Self) -> str | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.installed.version

    @property
    def latest_version(self: Self) -> str | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.latest.version

    @property
    def release_url(self: Self) -> str | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.latest.release_url

    async def async_release_notes(self: Self) -> str | None:
        if self.coordinator.data is None:
            return None
        return (
            f"See the full changelog on GitHub: "
            f"{self.coordinator.data.latest.release_url}"
        )

    async def async_install(
        self: Self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        if self.coordinator.data is None or self.coordinator.data.latest.download_url is None:
            _LOGGER.error("No firmware download URL available, cannot install update")
            return

        ota_username = self._config_entry.data.get(
            CONF_OTA_USERNAME, DEFAULT_OTA_USERNAME
        )
        ota_password = self._config_entry.data.get(
            CONF_OTA_PASSWORD, DEFAULT_OTA_PASSWORD
        )

        await self.coordinator.obegransad_connector.install_firmware(
            self.coordinator.data.latest.download_url,
            ota_username,
            ota_password,
        )

        # The device reboots itself once the flash write finishes; give it a
        # moment before the next poll instead of hammering an offline host.
        await self.coordinator.async_request_refresh()

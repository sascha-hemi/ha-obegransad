from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, Platform, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

from .const import PLATFORMS, DOMAIN, ATTR_CONFIG_ENTRY_ID
from .coordinator import ObegransadDataUpdateCoordinator
from .firmware_coordinator import ObegransadFirmwareUpdateCoordinator
from .services import async_setup_services
from .typing_helpers import ObegransadConfigEntry, ObegransadRuntimeData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ObegransadConfigEntry) -> bool:
    host: str = entry.data[CONF_HOST]

    obegransad_update_coordinator = ObegransadDataUpdateCoordinator(hass, host)
    await obegransad_update_coordinator.async_config_entry_first_refresh()

    firmware_update_coordinator = ObegransadFirmwareUpdateCoordinator(
        hass, obegransad_update_coordinator.obegransad_connector
    )
    # Don't block setup if GitHub is unreachable or the device is still
    # running firmware without the /api/version endpoint - the update
    # entity will simply come up unavailable and retry on its own interval.
    await firmware_update_coordinator.async_refresh()

    entry.runtime_data = ObegransadRuntimeData(
        obegransad_update_coordinator, firmware_update_coordinator
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {
                CONF_NAME: entry.title,
                ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            },
            hass.config,
        )
    )
    async_setup_services(hass, obegransad_update_coordinator)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ObegransadConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .coordinator import ObegransadDataUpdateCoordinator
from .firmware_coordinator import ObegransadFirmwareUpdateCoordinator


@dataclass
class ObegransadRuntimeData:
    coordinator: ObegransadDataUpdateCoordinator
    firmware_coordinator: ObegransadFirmwareUpdateCoordinator


type ObegransadConfigEntry = ConfigEntry[ObegransadRuntimeData]

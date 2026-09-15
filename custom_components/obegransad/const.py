from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

NAME: Final = "Obegränsad"

DOMAIN: Final = "obegransad"

ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"

ATTR_TEXT: Final = "text"
ATTR_GRAPH: Final = "graph"
ATTR_MIN_Y: Final = "min_y"
ATTR_MAX_Y: Final = "max_y"
ATTR_REPEAT: Final = "repeat"
ATTR_MESSAGE_ID: Final = "message_id"
ATTR_DELAY: Final = "delay"
ATTR_SCHEDULE: Final = "schedule"
ATTR_PLUGIN_ID: Final = "plugin_id"
ATTR_DURATION: Final = "duration"

DATA_HASS_CONFIG: Final = "hass_config"

SERVICE_SET_SCHEDULE: Final = "set_schedule"
SERVICE_REMOVE_MESSAGE: Final = "remove_message"
SERVICE_CLEAR_STORAGE: Final = "clear_storage"

UPDATE_INTERVAL: Final = timedelta(seconds=10)
FIRMWARE_UPDATE_INTERVAL: Final = timedelta(hours=3)

CONF_OTA_USERNAME: Final = "ota_username"
CONF_OTA_PASSWORD: Final = "ota_password"

# Defaults baked into the ph1p/ikea-led-obegraensad firmware's CI build
# (see build-and-release.yaml) - used as config-flow defaults so most users
# never have to type them.
DEFAULT_OTA_USERNAME: Final = "admin"
DEFAULT_OTA_PASSWORD: Final = "ikea-led-wall"

# Repository whose GitHub Releases are polled for firmware updates, and the
# asset name built for the ESP32-S3 target (see build-and-release.yaml).
#
# NOTE: this is a standalone firmware repo (not upstream
# ph1p/ikea-led-obegraensad), because the /api/version endpoint this
# integration relies on only exists there for now.
FIRMWARE_GITHUB_REPO: Final = "sascha-hemi/obegransad-firmware"
FIRMWARE_ASSET_NAME: Final = "esp32s3_firmware.bin"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.UPDATE,
]

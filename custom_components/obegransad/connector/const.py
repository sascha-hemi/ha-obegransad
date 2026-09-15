from typing import Final

from aiohttp import ClientTimeout

API_BASE_URL: Final = "http://{host}/api"
API_URL_INFO: Final = API_BASE_URL + "/info"
API_URL_VERSION: Final = API_BASE_URL + "/version"
API_URL_PLUGIN: Final = API_BASE_URL + "/plugin"
API_URL_BRIGHTNESS: Final = API_BASE_URL + "/brightness"
API_URL_DATA: Final = API_BASE_URL + "/data"
API_URL_SCHEDULE: Final = API_BASE_URL + "/schedule"
API_URL_SCHEDULE_START: Final = API_URL_SCHEDULE + "/start"
API_URL_SCHEDULE_STOP: Final = API_URL_SCHEDULE + "/stop"
API_URL_MESSAGE: Final = API_BASE_URL + "/message"
API_URL_REMOVE_MESSAGE: Final = API_BASE_URL + "/removemessage"
API_URL_CLEAR_STORAGE: Final = API_BASE_URL + "/clearstorage"

# ElegantOTA v3 endpoints exposed by the firmware itself (src/ota.cpp),
# protected with HTTP basic/digest auth using the OTA username/password
# configured on the device. See ElegantOTA.cpp: GET /ota/start allocates the
# flash region, POST /ota/upload streams the multipart firmware body.
OTA_START_URL: Final = "http://{host}/ota/start"
OTA_UPLOAD_URL: Final = "http://{host}/ota/upload"

GITHUB_API_BASE_URL: Final = "https://api.github.com"
GITHUB_LATEST_RELEASE_URL: Final = GITHUB_API_BASE_URL + "/repos/{repo}/releases/latest"
GITHUB_USER_AGENT: Final = "home-assistant-obegransad-integration"

TIMEOUT = ClientTimeout(total=10)
DOWNLOAD_TIMEOUT = ClientTimeout(total=120)

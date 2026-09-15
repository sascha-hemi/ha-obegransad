import hashlib
import json
import logging
from typing import Any, Self

from aiohttp import BasicAuth, ClientSession, FormData

from .const import (
    API_URL_INFO,
    API_URL_VERSION,
    API_URL_BRIGHTNESS,
    API_URL_PLUGIN,
    TIMEOUT,
    DOWNLOAD_TIMEOUT,
    API_URL_MESSAGE,
    API_URL_SCHEDULE,
    API_URL_SCHEDULE_START,
    API_URL_SCHEDULE_STOP,
    API_URL_REMOVE_MESSAGE,
    API_URL_CLEAR_STORAGE,
    OTA_START_URL,
    OTA_UPLOAD_URL,
    GITHUB_LATEST_RELEASE_URL,
    GITHUB_USER_AGENT,
)
from .exceptions import (
    ObegransadApiException,
)
from .model import ObegransadDeviceData, ObegransadFirmwareData, ObegransadReleaseData

_LOGGER = logging.getLogger(__name__)


class ObegransadConnector:
    _session: ClientSession
    _host: str
    _last_brightness: int | None

    def __init__(self: Self, session: ClientSession, host: str) -> None:
        self._session = session
        self._host = host
        self._last_brightness = None

    async def _get_data(self: Self, url: str) -> Any:
        response = await self._session.get(url, timeout=TIMEOUT)

        response_text = await response.text()

        if response.status != 200:
            raise ObegransadApiException(response.status, response_text)

        return json.loads(response_text)

    async def get_data(self: Self) -> ObegransadDeviceData:
        url = API_URL_INFO.format(host=self._host)
        data = await self._get_data(url)
        obegransad_device_data = ObegransadDeviceData.from_dict(data)
        if obegransad_device_data.brightness != 0:
            self._last_brightness = obegransad_device_data.brightness
        return obegransad_device_data

    async def set_brightness(self: Self, brightness: int | None) -> None:
        if brightness is None:
            brightness_value = self._last_brightness or 255
        else:
            brightness_value = brightness
        url = API_URL_BRIGHTNESS.format(host=self._host)
        await self._session.patch(
            url, data={"value": brightness_value}, timeout=TIMEOUT
        )

    async def set_plugin(self: Self, plugin_id: int) -> None:
        url = API_URL_PLUGIN.format(host=self._host)
        await self._session.patch(url, data={"id": plugin_id}, timeout=TIMEOUT)

    async def display_message(
        self: Self,
        text: str | None,
        graph: list[int] | None,
        min_y: int | None,
        max_y: None,
        repeat: int | None,
        message_id: str | None,
        delay: int | None,
    ) -> None:
        url = API_URL_MESSAGE.format(host=self._host)
        data = {}
        if text is not None and text != "":
            data["text"] = text
        if graph is not None:
            data["graph"] = ",".join(list(map(lambda g: str(g), graph)))
        if min_y is not None:
            data["miny"] = min_y
        if max_y is not None:
            data["maxy"] = max_y
        if repeat is not None:
            data["repeat"] = repeat
        if message_id is not None:
            data["id"] = message_id
        if delay is not None:
            data["delay"] = delay
        await self._session.get(url, data=data, timeout=TIMEOUT)

    async def remove_message(self: Self, message_id: str) -> None:
        url = API_URL_REMOVE_MESSAGE.format(host=self._host)
        data = {"id": message_id}
        await self._session.get(url, data=data, timeout=TIMEOUT)

    async def start_schedule(self: Self) -> None:
        url = API_URL_SCHEDULE_START.format(host=self._host)
        await self._session.get(url, timeout=TIMEOUT)

    async def stop_schedule(self: Self) -> None:
        url = API_URL_SCHEDULE_STOP.format(host=self._host)
        await self._session.get(url, timeout=TIMEOUT)

    async def set_schedule(self: Self, schedule_data: list[dict[str, int]]) -> None:
        url = API_URL_SCHEDULE.format(host=self._host)
        response = await self._session.post(
            url,
            data={
                "schedule": json.dumps(schedule_data).replace("plugin_id", "pluginId")
            },
            timeout=TIMEOUT,
        )
        text = await response.text()
        print(text)

    async def clear_storage(self: Self) -> None:
        url = API_URL_CLEAR_STORAGE.format(host=self._host)
        await self._session.get(url, timeout=TIMEOUT)

    async def get_firmware_version(self: Self) -> ObegransadFirmwareData:
        """Read the version currently running on the device (/api/version)."""
        url = API_URL_VERSION.format(host=self._host)
        data = await self._get_data(url)
        return ObegransadFirmwareData.from_dict(data)

    async def get_latest_release(
        self: Self, repo: str, asset_name: str
    ) -> ObegransadReleaseData:
        """Look up the latest firmware release published on GitHub."""
        url = GITHUB_LATEST_RELEASE_URL.format(repo=repo)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": GITHUB_USER_AGENT,
        }
        response = await self._session.get(url, headers=headers, timeout=TIMEOUT)
        response_text = await response.text()

        if response.status != 200:
            raise ObegransadApiException(response.status, response_text)

        return ObegransadReleaseData.from_dict(json.loads(response_text), asset_name)

    async def install_firmware(
        self: Self,
        download_url: str,
        ota_username: str,
        ota_password: str,
    ) -> None:
        """Download a firmware binary and flash it via the device's ElegantOTA (v3) endpoints.

        Mirrors the two-step protocol implemented by the firmware's own
        scripts/upload.py PlatformIO uploader:
          1. GET  /ota/start?mode=fr&hash=<md5>  - allocates flash space
          2. POST /ota/upload (multipart: MD5 + firmware) - streams the binary
        """
        auth = BasicAuth(ota_username, ota_password)

        firmware_response = await self._session.get(
            download_url, timeout=DOWNLOAD_TIMEOUT
        )
        if firmware_response.status != 200:
            raise ObegransadApiException(
                firmware_response.status, "Failed to download firmware asset"
            )
        firmware_bytes = await firmware_response.read()
        md5_hash = hashlib.md5(firmware_bytes).hexdigest()

        start_url = OTA_START_URL.format(host=self._host)
        start_response = await self._session.get(
            start_url,
            params={"mode": "fr", "hash": md5_hash},
            auth=auth,
            timeout=DOWNLOAD_TIMEOUT,
        )
        start_text = await start_response.text()
        if start_response.status != 200:
            raise ObegransadApiException(start_response.status, start_text)

        # NOTE: ElegantOTA v3's /ota/upload handler (see ElegantOTA.cpp) only ever
        # reads the uploaded *file* part - it does not look at a separate "MD5"
        # form field (the hash is already committed via /ota/start above). An
        # extra plain-text field ahead of the file part was found, on real
        # hardware, to confuse ESPAsyncWebServer's multipart parser: the device
        # wrote only 32 bytes (exactly len(md5_hash)) before aborting with
        # "Flash Read Failed". Sending only the file part avoids that.
        form = FormData()
        form.add_field(
            "firmware",
            firmware_bytes,
            filename="firmware",
            content_type="application/octet-stream",
        )

        upload_url = OTA_UPLOAD_URL.format(host=self._host)
        upload_response = await self._session.post(
            upload_url,
            data=form,
            auth=auth,
            timeout=DOWNLOAD_TIMEOUT,
        )
        upload_text = await upload_response.text()
        if upload_response.status != 200:
            raise ObegransadApiException(upload_response.status, upload_text)

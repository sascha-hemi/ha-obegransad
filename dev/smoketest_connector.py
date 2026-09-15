"""Standalone smoke test for the connector logic - no real device/GitHub needed.

Run from the integration repo root (where custom_components/ lives):
    python3 dev/smoketest_connector.py
"""
import asyncio
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import custom_components.obegransad.connector as connector_module
from custom_components.obegransad.connector import ObegransadConnector
from custom_components.obegransad.connector.model import (
    ObegransadFirmwareData,
    ObegransadReleaseData,
)


class FakeResponse:
    def __init__(self, status, text_body=None, json_body=None, read_body=None):
        self.status = status
        self._text_body = text_body if text_body is not None else json.dumps(json_body or {})
        self._read_body = read_body or b""

    async def text(self):
        return self._text_body

    async def read(self):
        return self._read_body


class FakeSession:
    def __init__(self, timeout=None):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("/api/version"):
            return FakeResponse(200, json_body={"version": "1.0.0", "board": "esp32s3"})
        if "releases/latest" in url:
            return FakeResponse(
                200,
                json_body={
                    "tag_name": "v1.0.1",
                    "html_url": "https://github.com/ph1p/ikea-led-obegraensad/releases/tag/v1.0.1",
                    "assets": [
                        {
                            "name": "esp32s3_firmware.bin",
                            "browser_download_url": "https://example.invalid/esp32s3_firmware.bin",
                        },
                        {
                            "name": "esp32dev_firmware.bin",
                            "browser_download_url": "https://example.invalid/esp32dev_firmware.bin",
                        },
                    ],
                },
            )
        if url.startswith("https://example.invalid/"):
            return FakeResponse(200, read_body=b"FAKE_FIRMWARE_BYTES")
        if "/ota/start" in url:
            assert kwargs["params"]["mode"] == "fr"
            expected_md5 = hashlib.md5(b"FAKE_FIRMWARE_BYTES").hexdigest()
            assert kwargs["params"]["hash"] == expected_md5, "MD5 mismatch in /ota/start"
            assert kwargs["auth"].login == "admin"
            return FakeResponse(200, text_body="OK")
        raise AssertionError(f"Unexpected GET {url}")

    async def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if "/ota/upload" in url:
            form = kwargs["data"]
            # aiohttp.FormData stores fields internally; just sanity check auth+url
            assert kwargs["auth"].login == "admin"
            return FakeResponse(200, text_body="OK")
        raise AssertionError(f"Unexpected POST {url}")


async def main():
    session = FakeSession()
    # install_firmware() opens its own dedicated ClientSession rather than
    # reusing self._session (see the comment in connector/__init__.py for
    # why) - patch the module-level import so it hands back the same fake,
    # keeping every call visible in session.calls.
    connector_module.ClientSession = lambda **kwargs: session

    connector = ObegransadConnector(session, "192.168.1.50")

    firmware = await connector.get_firmware_version()
    assert isinstance(firmware, ObegransadFirmwareData)
    assert firmware.version == "1.0.0"
    assert firmware.board == "esp32s3"
    print("get_firmware_version() OK ->", firmware)

    release = await connector.get_latest_release(
        "ph1p/ikea-led-obegraensad", "esp32s3_firmware.bin"
    )
    assert isinstance(release, ObegransadReleaseData)
    assert release.version == "1.0.1"
    assert release.download_url == "https://example.invalid/esp32s3_firmware.bin"
    print("get_latest_release() OK ->", release)

    await connector.install_firmware(release.download_url, "admin", "ikea-led-wall")
    print("install_firmware() OK, calls made:")
    for method, url, kwargs in session.calls:
        print(" ", method, url, {k: v for k, v in kwargs.items() if k != "data"})

    print("\nALL SMOKE TESTS PASSED")


asyncio.run(main())

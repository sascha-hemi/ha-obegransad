"""Real production-path test: checks the actual GitHub release for
sascha-hemi/obegransad-firmware and installs it on the physical device via
the real ObegransadConnector code (same path update.py uses) - no mocks,
no local file server, no manual asset handling.

Usage: edit HOST below, then from the integration repo root:
    python3 dev/e2e_ota_test_real_release.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiohttp import ClientSession
from custom_components.obegransad.connector import ObegransadConnector
from custom_components.obegransad.const import FIRMWARE_ASSET_NAME, FIRMWARE_GITHUB_REPO

HOST = "10.42.0.104"
OTA_USERNAME = "admin"
OTA_PASSWORD = "ikea-led-wall"


async def main():
    async with ClientSession() as session:
        connector = ObegransadConnector(session, HOST)

        installed = await connector.get_firmware_version()
        print("Installed version:", installed)

        latest = await connector.get_latest_release(FIRMWARE_GITHUB_REPO, FIRMWARE_ASSET_NAME)
        print("Latest GitHub release:", latest)

        if latest.download_url is None:
            print("No matching asset found - aborting")
            return

        if latest.version == installed.version:
            print("Already up to date, nothing to install (this is fine)")
            return

        print(f"Installing {latest.version} from {latest.download_url} ...")
        await connector.install_firmware(latest.download_url, OTA_USERNAME, OTA_PASSWORD)
        print("install_firmware() completed without error")

        print("Waiting for device to reboot...")
        await asyncio.sleep(8)
        for attempt in range(10):
            try:
                after = await connector.get_firmware_version()
                print("Version after OTA:", after)
                break
            except Exception as e:
                print(f"  (device not back yet, attempt {attempt + 1}/10: {e})")
                await asyncio.sleep(2)


asyncio.run(main())

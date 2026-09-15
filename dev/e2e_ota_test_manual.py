"""Real end-to-end OTA test against physical hardware using the actual
ObegransadConnector.install_firmware() code path (same code the update.py
entity calls) - not a mock. Re-flashes the currently running esp32s3 build.

Requires: pip install aiohttp homeassistant (the latter only because
custom_components/obegransad/__init__.py imports homeassistant.*, which
gets pulled in transitively via the package's __init__).

Usage: edit HOST / MY_IP / OTA credentials below, then:
    python3 dev/e2e_ota_test_manual.py
"""
import asyncio
import http.server
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiohttp import ClientSession
from custom_components.obegransad.connector import ObegransadConnector

HOST = "10.42.0.104"  # IP of the device under test
MY_IP = "10.42.0.228"  # this machine's IP, reachable by the device
OTA_USERNAME = "admin"
OTA_PASSWORD = "ikea-led-wall"
FIRMWARE_PATH = "../../firmware/.pio/build/esp32s3/firmware.bin"


async def main():
    async with ClientSession() as session:
        connector = ObegransadConnector(session, HOST)

        before = await connector.get_firmware_version()
        print("Version before OTA:", before)

        # install_firmware() downloads from a URL (mirroring the real
        # GitHub-release flow); serve the local .bin over HTTP so the exact
        # same connector code path can be exercised unmodified.
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

        firmware_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), FIRMWARE_PATH)
        firmware_dir = os.path.dirname(firmware_dir)
        os.chdir(firmware_dir)
        server = http.server.HTTPServer(("0.0.0.0", 8934), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        download_url = f"http://{MY_IP}:8934/firmware.bin"
        print("Serving firmware for device to fetch at:", download_url)

        try:
            await connector.install_firmware(download_url, OTA_USERNAME, OTA_PASSWORD)
            print("install_firmware() completed without error")
        except Exception as e:
            print("install_firmware() FAILED:", repr(e))
            print("response body:", getattr(e, "response", None))
        finally:
            server.shutdown()

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

# Obegränsad – Home Assistant Integration

Home Assistant integration for the IKEA OBEGRÄNSAD LED wall lamp, hacked with
[ph1p/ikea-led-obegraensad](https://github.com/ph1p/ikea-led-obegraensad) (see
[sascha-hemi/ikea-led-obegraensad](https://github.com/sascha-hemi/ikea-led-obegraensad),
`esp32s3-ota-integration` branch, for the ESP32-S3-targeted fork this integration was
built and tested against).

Built on top of
[PiotrMachowski/Home-Assistant-custom-components-Obegransad](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Obegransad)'s
connector/coordinator architecture, extended with a **firmware update entity**.

## Entities

- **Light**: on/off, brightness
- **Sensors**: rows, columns, status, active plugin, rotation, brightness, schedule,
  RSSI, uptime, free memory, IP/MAC address
- **Binary sensor**: schedule active
- **Switch**: schedule on/off
- **Update**: `Firmware` — compares the version reported by the device's
  `/api/version` endpoint against the latest release of
  [ph1p/ikea-led-obegraensad](https://github.com/ph1p/ikea-led-obegraensad) on GitHub,
  and installs it via the firmware's ElegantOTA endpoints when you click "Install".
- **Services**: `set_schedule`, `remove_message`, `clear_storage` (see `services.yaml`)
- **Notify**: send text/graph messages to the display

## Requirements

- The lamp must be running a firmware build that exposes `GET /api/version`
  (present on the `esp32s3-ota-integration` branch linked above; not on stock
  ph1p `main` yet).
- Home Assistant 2024.1 or newer.

## Installation

### HACS
Add this repository as a custom repository (category: Integration), then install
"Obegränsad".

### Manual
Copy `custom_components/obegransad/` into `config/custom_components/obegransad/` and
restart Home Assistant.

## Setup

Settings → Devices & Services → Add Integration → search "Obegränsad" → enter the
device's host/IP. The OTA username/password fields default to the firmware's built-in
defaults (`admin` / `ikea-led-wall`) — only change them if you changed
`include/secrets.h` on the device.

## Development

- `dev/smoketest_connector.py` — connector logic smoke test against a mocked
  `aiohttp` session (model parsing, GitHub release parsing, OTA request sequence).
- `dev/e2e_ota_test_manual.py` — real end-to-end OTA test against physical hardware,
  using the exact code path the `update` entity uses. Edit the `HOST`/`MY_IP`
  constants at the top before running.
- CI (`.github/workflows/validate.yaml`) runs hassfest, HACS validation, and imports
  every module against a real `homeassistant` install plus the connector smoke test.

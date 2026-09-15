from dataclasses import dataclass
from typing import Self, Any

type ObegransadDevicesDataMap = dict[str, ObegransadDeviceData]


@dataclass
class ObegransadScheduleData:
    plugin_id: int
    duration: int

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        return cls(
            plugin_id=data["pluginId"],
            duration=data["duration"],
        )


@dataclass
class ObegransadPluginData:
    id: int
    name: str

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            name=data["name"],
        )


@dataclass
class ObegransadFirmwareData:
    """Version reported by the device's own /api/version endpoint."""

    version: str
    board: str

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        return cls(
            version=data.get("version", "unknown"),
            board=data.get("board", "unknown"),
        )


@dataclass
class ObegransadReleaseData:
    """Latest firmware release as published on GitHub."""

    version: str
    release_url: str
    download_url: str | None

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any], asset_name: str) -> Self:
        download_url = None
        for asset in data.get("assets", []):
            if asset.get("name") == asset_name:
                download_url = asset.get("browser_download_url")
                break

        return cls(
            version=str(data["tag_name"]).lstrip("v"),
            release_url=data.get("html_url", ""),
            download_url=download_url,
        )


@dataclass
class ObegransadDeviceData:
    rows: int
    columns: int
    status: int
    plugin: int
    rotation: int
    brightness: int
    schedule_active: bool
    schedule: list[ObegransadScheduleData]
    plugins: list[ObegransadPluginData]

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, Any]) -> Self:
        return cls(
            rows=data["rows"],
            columns=data["cols"],
            status=data["status"],
            plugin=data["plugin"],
            rotation=data["rotation"],
            brightness=data["brightness"],
            schedule_active=data["scheduleActive"],
            schedule=list(
                map(lambda s: ObegransadScheduleData.from_dict(s), data["schedule"])
            ),
            plugins=list(
                map(lambda s: ObegransadPluginData.from_dict(s), data["plugins"])
            ),
        )

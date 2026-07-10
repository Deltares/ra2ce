from __future__ import annotations

import re
from enum import Enum
from typing import Any


class SupportedAssetTypeEnum(Enum):
    BRIDGE = "bridge"
    VIADUCT = "viaduct"
    AQUEDUCT = "aqueduct"
    BOARDWALK = "boardwalk"
    MOVABLE_BRIDGE = "movable_bridge"
    LOW_WATER_CROSSING = "low_water_crossing"
    TUNNEL = "tunnel"
    CULVERT = "culvert"
    FLOODED = "flooded"


BRIDGE_ASSET_MAP: dict[str, str] = {
    "bridge": SupportedAssetTypeEnum.BRIDGE.value,
    "viaduct": SupportedAssetTypeEnum.VIADUCT.value,
    "aqueduct": SupportedAssetTypeEnum.AQUEDUCT.value,
    "boardwalk": SupportedAssetTypeEnum.BOARDWALK.value,
    "movable_bridge": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "low_water_crossing": SupportedAssetTypeEnum.LOW_WATER_CROSSING.value,
}

TUNNEL_ASSET_MAP: dict[str, str] = {
    "tunnel": SupportedAssetTypeEnum.TUNNEL.value,
    "culvert": SupportedAssetTypeEnum.CULVERT.value,
    "flooded": SupportedAssetTypeEnum.FLOODED.value,
}

ASSET_ALIASES: dict[str, str] = {
    "low_water_crossing": SupportedAssetTypeEnum.LOW_WATER_CROSSING.value,
    "low-water-crossing": SupportedAssetTypeEnum.LOW_WATER_CROSSING.value,
    "low water crossing": SupportedAssetTypeEnum.LOW_WATER_CROSSING.value,
    "movable_bridge": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "movable-bridge": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "movable bridge": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "movable": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "moveable": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "movables": SupportedAssetTypeEnum.MOVABLE_BRIDGE.value,
    "bridges": SupportedAssetTypeEnum.BRIDGE.value,
    "tunnels": SupportedAssetTypeEnum.TUNNEL.value,
    "culverts": SupportedAssetTypeEnum.CULVERT.value,
    "viaducts": SupportedAssetTypeEnum.VIADUCT.value,
    "aqueducts": SupportedAssetTypeEnum.AQUEDUCT.value,
    "boardwalks": SupportedAssetTypeEnum.BOARDWALK.value,
    }


def get_supported_asset_types() -> set[str]:
    return {asset.value for asset in SupportedAssetTypeEnum}


CANONICAL_ASSET_TYPES: set[str] = get_supported_asset_types()


def normalize_asset_token(key: Any) -> str:
    if key is None:
        return ""
    return re.sub(r"[\s\-]+", "_", str(key).strip()).casefold().strip("_")


def canonicalize_asset_name(key: Any) -> str:
    token = normalize_asset_token(key)
    if not token:
        return ""

    if token in ASSET_ALIASES:
        return ASSET_ALIASES[token]

    if token.endswith("ies") and len(token) > 3:
        token = token[:-3] + "y"
    elif token.endswith(("sses", "shes", "ches", "xes", "zes")) and len(token) > 4:
        token = token[:-2]
    elif token.endswith("s") and len(token) > 1:
        token = token[:-1]

    return ASSET_ALIASES.get(token, token)

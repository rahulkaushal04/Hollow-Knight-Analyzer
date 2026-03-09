"""
Static game data loaders.

This module provides centralized access to all static Hollow Knight
game data stored as JSON files.

All files are loaded from the project's assets/data directory and
cached using Streamlit's cache_resource decorator. Each dataset is
therefore loaded only once per server session and reused across
all user interactions.

All data access within the application should go through this module.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

# Root directory that contains static game data JSON files
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "data"


def _load_json(filename: str, default: Any) -> Any:
    """
    Load a JSON file from the static data directory.

    Parameters
    ----------
    filename
        Name of the JSON file inside the data directory.

    default
        Value returned if the file is missing or cannot be parsed.

    Returns
    -------
    Any
        Parsed JSON content or the provided default value.
    """

    filepath = _DATA_DIR / filename

    if not filepath.exists():
        logger.warning(f"Game data file not found: {filepath}")
        return default

    try:
        with filepath.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return default

    except OSError as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return default


def _load_list(filename: str) -> list[dict]:
    """
    Convenience wrapper for loading JSON files that contain lists.
    """
    data = _load_json(filename, [])

    if not isinstance(data, list):
        logger.error(f"Expected list in {filename}, received {type(data).__name__}")
        return []

    return data


def _load_dict(filename: str) -> dict:
    """
    Convenience wrapper for loading JSON files that contain dictionaries.
    """
    data = _load_json(filename, {})

    if not isinstance(data, dict):
        logger.error(f"Expected dict in {filename}, received {type(data).__name__}")
        return {}

    return data


@st.cache_resource
def get_charms() -> list[dict]:
    """
    Load charm metadata.

    Returns information for all charms defined in charms.json.
    """
    return _load_list("charms.json")


@st.cache_resource
def get_bosses() -> list[dict]:
    """
    Load boss metadata.
    """
    return _load_list("bosses.json")


@st.cache_resource
def get_grubs() -> list[dict]:
    """
    Load grub locations and metadata.
    """
    return _load_list("grubs.json")


@st.cache_resource
def get_abilities() -> list[dict]:
    """
    Load player ability metadata.
    """
    return _load_list("abilities.json")


@st.cache_resource
def get_enemies() -> list[dict]:
    """
    Load enemy metadata.
    """
    return _load_list("enemies.json")


@st.cache_resource
def get_areas() -> list[dict]:
    """
    Load area metadata used by the world map.
    """
    return _load_list("areas.json")


@st.cache_resource
def get_relics() -> list[dict]:
    """
    Load relic metadata.
    """
    return _load_list("relics.json")


@st.cache_resource
def get_npcs() -> list[dict]:
    """
    Load NPC metadata.
    """
    return _load_list("npcs.json")


@st.cache_resource
def get_collectibles() -> list[dict]:
    """
    Load collectible metadata.
    """
    return _load_list("collectibles.json")


@st.cache_resource
def get_map_coordinates() -> dict:
    """
    Load world map coordinate data.

    This file maps areas or objects to map positions used by the UI.
    """
    return _load_dict("map_coordinates.json")

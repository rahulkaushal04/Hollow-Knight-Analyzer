"""
Session state key constants and initialization.

All st.session_state keys used across the app are defined here as string
constants, which eliminates typo-prone bare string literals scattered across
modules and provides a single reference for every key in use.

The init_session() function should be called at the top of every page entry
point. It is safe to call multiple times because it only writes keys that are
not already present, leaving any live state untouched.

Typical usage
-------------
    from src.core.session import init_session, SAVE_DATA, SAVE_LOADED

    init_session()

    if st.session_state[SAVE_LOADED]:
        data = st.session_state[SAVE_DATA]
"""

from __future__ import annotations

import streamlit as st


# =============================================================================
# Key constants
# =============================================================================

# Parsed SaveData object produced by the file handler pipeline.
SAVE_DATA = "save_data"

# Raw dictionary decoded from the decrypted save JSON before model conversion.
RAW_SAVE_DICT = "raw_save_dict"

# True once a save file has been successfully uploaded and parsed.
SAVE_LOADED = "save_loaded"

# True when spoiler content (e.g. boss names, area completions) is visible.
SPOILERS_ON = "spoilers_on"

# Identifier of the currently visible page, used for programmatic navigation.
ACTIVE_PAGE = "active_page"

# Human-readable error message from the most recent failed upload attempt.
UPLOAD_ERROR = "upload_error"

# Active filter value on the charms page ("all", "owned", "unowned").
CHARM_FILTER = "charm_filter"

# Index of the selected tab on the bosses page.
BOSS_TAB = "boss_tab"


# =============================================================================
# Defaults
# =============================================================================

# Maps every key to its starting value. None signals "not yet populated".
_DEFAULTS: dict = {
    SAVE_DATA: None,
    RAW_SAVE_DICT: None,
    SAVE_LOADED: False,
    SPOILERS_ON: False,
    ACTIVE_PAGE: "upload",
    UPLOAD_ERROR: None,
    CHARM_FILTER: "all",
    BOSS_TAB: 0,
}


# =============================================================================
# Initialization
# =============================================================================


def init_session() -> None:
    """Initialize all session state keys with their default values.

    Only keys that are absent from the current session are written.
    Existing values are never overwritten, so calling this function
    multiple times across a session is safe.

    This should be invoked at the start of every page entry point before
    any widget or session state access occurs.
    """
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default

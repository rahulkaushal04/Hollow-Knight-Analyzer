"""
Header bar component.

Renders a persistent top bar on every page once a save file has been loaded.
The bar is split into three horizontal sections:

    Left   -- App title ("Hallownest Codex") and current area with nail tier.
    Centre -- Quick-glance stats: geo, health, soul, and play time.
    Right  -- Spoiler visibility toggle.

The component reads all state from st.session_state using the key constants
defined in src.core.session and never mutates state directly (except through
the registered on_change callback for the spoiler toggle).

CSS classes used (.header-bar, .header-title, .header-stats, .header-stat-item)
are defined in assets/styles/theme.css and must remain in sync with the markup
produced here.
"""

from __future__ import annotations

import streamlit as st

from src.data.save_model import SaveData
from src.core.session import SAVE_DATA, SAVE_LOADED, SPOILERS_ON

# =============================================================================
# Constants
# =============================================================================

# Maps nail upgrade index (0..4) to its in-game display name.
# Index 0 is the starting weapon; index 4 is the fully upgraded Pure Nail.
_NAIL_NAMES: dict[int, str] = {
    0: "Old Nail",
    1: "Sharpened Nail",
    2: "Channelled Nail",
    3: "Coiled Nail",
    4: "Pure Nail",
}

# Fallback label shown when the nail tier value is outside the expected range.
_NAIL_FALLBACK = "Unknown Nail"

# Displayed when the save file does not record a current area.
_AREA_FALLBACK = "Unknown Area"


# =============================================================================
# Helpers
# =============================================================================


def _format_play_time(seconds: float) -> str:
    """Convert a raw play-time value in seconds to a compact HH:MM:SS string.

    Parameters
    ----------
    seconds:
        Total elapsed play time in seconds as stored in the save file.

    Returns
    -------
    str
        Formatted string such as "12:34:56". Hours are not zero-padded
        so the string stays compact for short runs (e.g. "1:05:03").
    """
    total = max(0, int(seconds))
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _nail_label(nail_tier: int) -> str:
    """Return the display name for the given nail upgrade tier.

    Parameters
    ----------
    nail_tier:
        Integer upgrade level from PlayerStats.nail_tier (0 to 4).

    Returns
    -------
    str
        Human-readable nail name, or a generic fallback for out-of-range values.
    """
    return _NAIL_NAMES.get(nail_tier, _NAIL_FALLBACK)


# =============================================================================
# Component
# =============================================================================


def render_header() -> None:
    """Render the top header bar with save summary, key stats, and spoiler toggle.

    Exits immediately without rendering anything when no save is loaded, so
    every page can call this unconditionally.

    Layout
    ------
    The bar uses the .header-bar CSS class and is divided into two flex children:
    - Left block: app title + area / nail tier subtitle.
    - Right block: geo, health, soul, play time, then the spoiler toggle column.

    Side effects
    ------------
    Writes an st.markdown block and a single-column st.toggle widget into
    the active Streamlit container.
    """
    if not st.session_state.get(SAVE_LOADED, False):
        return

    save: SaveData = st.session_state[SAVE_DATA]
    stats = save.player_stats

    area = stats.current_area or _AREA_FALLBACK
    nail = _nail_label(stats.nail_tier)
    play_time = _format_play_time(stats.play_time)

    st.markdown(
        f"""
        <div class="header-bar">
            <div>
                <span class="header-title">Hallownest Codex</span>
                <span style="color:var(--text-secondary);font-size:0.85rem;margin-left:12px;">
                    {area} &bull; {nail}
                </span>
            </div>
            <div class="header-stats">
                <span class="header-stat-item" title="Geo">
                    &#x1F4B0; {stats.geo:,}
                </span>
                <span class="header-stat-item" title="Health">
                    &#x2764;&#xFE0F; {stats.health}/{stats.max_health}
                </span>
                <span class="header-stat-item" title="Soul">
                    &#x1F52E; {stats.soul}/{stats.max_soul}
                </span>
                <span class="header-stat-item" title="Play time">
                    &#x23F1;&#xFE0F; {play_time}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Spoiler toggle is a native Streamlit widget so it remains interactive.
    # It sits in a narrow right-aligned column to avoid pushing layout content.
    cols = st.columns([0.85, 0.15])
    with cols[1]:
        current = st.session_state.get(SPOILERS_ON, False)
        label = "&#x1F441;&#xFE0F; Spoilers ON" if current else "&#x1F648; Spoilers OFF"
        st.toggle(
            label,
            value=current,
            key="_spoiler_toggle",
            on_change=_toggle_spoilers,
        )


# =============================================================================
# Callbacks
# =============================================================================


def _toggle_spoilers() -> None:
    """Sync the spoiler session flag from the native toggle widget state.

    Streamlit calls this after the _spoiler_toggle widget value changes.
    It writes the new value into SPOILERS_ON so all other components read
    a consistent flag regardless of which key they consult.
    """
    st.session_state[SPOILERS_ON] = st.session_state.get("_spoiler_toggle", False)

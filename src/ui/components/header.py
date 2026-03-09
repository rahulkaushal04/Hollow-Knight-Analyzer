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

import base64
import streamlit as st
from pathlib import Path
from functools import lru_cache

from src.data.save_model import SaveData
from src.core.session import SAVE_DATA, SAVE_LOADED, SPOILERS_ON

# Root of the project (two levels above this file: src/ui/components → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ICONS_DIR = _PROJECT_ROOT / "assets" / "icons"


@lru_cache(maxsize=None)
def _icon_src(name: str) -> str:
    """Return a base64 data-URI for the PNG icon *name* (without extension).

    Falls back to an empty string if the file is missing so the img tag
    simply renders nothing rather than raising an exception.
    """
    path = _ICONS_DIR / f"{name}.png"
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


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
    The bar uses the .header-bar CSS class and is divided into three flex children:
    - Left block: app title + play time.
    - Centre block: Geo, Masks (current), Soul (current).
    - Right block: current location + nail tier name.

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

    geo_src = _icon_src("geo")
    health_src = _icon_src("health")
    soul_src = _icon_src("soul")
    _img = lambda src, alt: (
        f'<img src="{src}" alt="{alt}" '
        'style="width:18px;height:18px;vertical-align:middle;margin-right:4px;">'
        if src
        else f"{alt} "
    )

    st.markdown(
        f"""
        <div class="header-bar">
            <div style="display:flex;flex-direction:column;justify-content:center;gap:2px;">
                <span class="header-title">Hallownest Codex</span>
                <span style="color:var(--text-secondary);font-size:0.8rem;">
                    &#x23F1;&#xFE0F; {play_time}
                </span>
            </div>
            <div class="header-stats">
                <span class="header-stat-item" title="Geo">
                    {_img(geo_src, 'Geo')}<strong>{stats.geo:,}</strong>&nbsp;Geo
                </span>
                <span class="header-stat-item" title="Masks">
                    {_img(health_src, 'Masks')}<strong>{stats.health}</strong>&nbsp;Masks
                </span>
                <span class="header-stat-item" title="Soul">
                    {_img(soul_src, 'Soul')}<strong>{stats.soul}</strong>&nbsp;Soul
                </span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;justify-content:center;gap:2px;">
                <span style="color:var(--text-primary);font-size:0.9rem;font-weight:600;">
                    {area}
                </span>
                <span style="color:var(--text-secondary);font-size:0.8rem;">
                    {nail}
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

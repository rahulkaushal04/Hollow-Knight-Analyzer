"""Header bar component — persistent top bar showing save summary and spoiler toggle."""

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
    """Return a base64 data-URI for the named PNG icon; cached indefinitely."""
    path = _ICONS_DIR / f"{name}.png"
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


@lru_cache(maxsize=None)
def _icon_html(name: str, alt: str) -> str:
    """Return an img tag for the named icon, or a plain alt prefix if missing."""
    src = _icon_src(name)
    if src:
        return (
            f'<img src="{src}" alt="{alt}" '
            'style="width:18px;height:18px;vertical-align:middle;margin-right:4px;">'
        )
    return f"{alt} "


_NAIL_NAMES: dict[int, str] = {
    0: "Old Nail",
    1: "Sharpened Nail",
    2: "Channelled Nail",
    3: "Coiled Nail",
    4: "Pure Nail",
}

_NAIL_FALLBACK = "Unknown Nail"
_AREA_FALLBACK = "Unknown Area"


def _format_play_time(seconds: float) -> str:
    """Convert play-time seconds to a HH:MM:SS string."""
    total = max(0, int(seconds))
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _nail_label(nail_tier: int) -> str:
    """Return the display name for a nail upgrade tier (0–4)."""
    return _NAIL_NAMES.get(nail_tier, _NAIL_FALLBACK)


def render_header() -> None:
    """Render the top header bar with save summary, key stats, and spoiler toggle."""
    if not st.session_state.get(SAVE_LOADED, False):
        return

    save: SaveData = st.session_state[SAVE_DATA]
    stats = save.player_stats

    area = stats.current_area or _AREA_FALLBACK
    nail = _nail_label(stats.nail_tier)
    play_time = _format_play_time(stats.play_time)

    geo_html = _icon_html("geo", "Geo")
    health_html = _icon_html("health", "Masks")
    soul_html = _icon_html("soul", "Soul")

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
                    {geo_html}<strong>{stats.geo:,}</strong>&nbsp;Geo
                </span>
                <span class="header-stat-item" title="Masks">
                    {health_html}<strong>{stats.health}</strong>&nbsp;Masks
                </span>
                <span class="header-stat-item" title="Soul">
                    {soul_html}<strong>{stats.soul}</strong>&nbsp;Soul
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

    cols = st.columns([0.85, 0.15])
    with cols[1]:
        current = st.session_state.get(SPOILERS_ON, False)
        label = "Spoilers ON" if current else "Spoilers OFF"
        st.toggle(
            label,
            value=current,
            key="_spoiler_toggle",
            on_change=_toggle_spoilers,
        )


def _toggle_spoilers() -> None:
    """Sync the SPOILERS_ON session flag from the _spoiler_toggle widget."""
    st.session_state[SPOILERS_ON] = st.session_state.get("_spoiler_toggle", False)

"""Stat card component — glassmorphism stat display.

Renders a single metric card with label, value, subtitle, and colour accent.
"""

from __future__ import annotations

import streamlit as st

from src.ui.theme import COLOURS

_COLOUR_MAP = {
    "blue": COLOURS["accent-blue"],
    "gold": COLOURS["accent-gold"],
    "purple": COLOURS["accent-purple"],
    "green": COLOURS["green"],
    "red": COLOURS["red"],
    "orange": COLOURS["orange"],
}


def stat_card(
    label: str,
    value: str | int,
    subtitle: str = "",
    colour: str = "blue",
    icon: str = "",
) -> None:
    """Render a single glassmorphism stat card."""
    accent = _COLOUR_MAP.get(colour, COLOURS["accent-blue"])
    icon_html = (
        f'<span style="font-size:1.6rem;margin-right:6px;">{icon}</span>'
        if icon
        else ""
    )
    subtitle_html = (
        f'<div style="color:var(--text-secondary);font-size:0.75rem;'
        f'margin-top:2px;">{subtitle}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div class="stat-card" style="border-top:3px solid {accent};">
            <div style="color:var(--text-secondary);font-size:0.8rem;
                 margin-bottom:4px;">{icon_html}{label}</div>
            <div style="font-family:'Fira Code',monospace;font-size:1.8rem;
                 color:{accent};font-weight:700;">{value}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

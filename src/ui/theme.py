"""Theme injector and design token registry for the Hallownest UI."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

_CSS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "assets" / "styles" / "theme.css"
)

COLOURS: dict[str, str] = {
    # Surfaces and structural backgrounds
    "bg": "#0A0A0F",
    "surface": "#12121A",
    "surface-high": "#1E1E2E",
    "border": "#2A2A3E",
    # Accent and interactive colours
    "accent-blue": "#A3C5D8",
    "accent-gold": "#C9A84C",
    "accent-purple": "#7B68EE",
    # Semantic state colours
    "green": "#4A9B6F",  # success, defeated, claimed
    "red": "#C44B4B",  # missing, failure, overcharmed
    "orange": "#D4824A",  # warning, partial progress
    "grey": "#5A5A72",  # disabled, muted, placeholder
    # Typography
    "text-primary": "#E0E0E8",
    "text-secondary": "#9898B0",
}

# Font stack values mirroring the CSS --font-* variables.
FONTS: dict[str, str] = {
    "heading": "'Cinzel', serif",  # display text, titles
    "body": "'Inter', sans-serif",  # UI copy, labels, body
    "mono": "'Fira Code', monospace",  # numbers, stats, data
}


@st.cache_resource
def _load_css() -> str:
    """Read theme.css from disk; cached for the app lifetime."""
    if not _CSS_PATH.exists():
        logger.warning(
            "Theme CSS not found at %s; app will render unstyled.", _CSS_PATH
        )
        return ""
    return _CSS_PATH.read_text(encoding="utf-8")


def apply_theme() -> None:
    """Inject theme.css into the Streamlit app. Call once at app startup."""
    css = _load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def colour(name: str) -> str:
    """Return the hex value for a design token name; falls back to #FFFFFF."""
    value = COLOURS.get(name)
    if value is None:
        logger.warning(
            "Unknown colour token %r requested; falling back to #FFFFFF.", name
        )
        return "#FFFFFF"
    return value

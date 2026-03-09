"""
Theme injector and design token registry.

This module is the single point of contact between Python code and the
Hallownest visual theme. It owns two responsibilities:

    1. Injecting the CSS into Streamlit via apply_theme().
    2. Exposing design token values as importable constants so Python
       components can reference the same colours used in theme.css without
       repeating raw hex literals.

Usage
-----
Call apply_theme() once at the top of app.py before any page renders:

    from src.ui.theme import apply_theme
    apply_theme()

To reference a colour value in Python (e.g. for a Plotly figure):

    from src.ui.theme import colour, COLOURS
    bar_colour = colour("accent-gold")   # returns "#C9A84C"

Relationship with config.toml
------------------------------
The .streamlit/config.toml file sets Streamlit's native widget theme
(primaryColor, backgroundColor, etc.). Those values control built-in
widgets such as buttons and sliders and cannot be overridden by CSS.
The values here only affect components rendered via st.markdown HTML.
The two colour systems must stay manually in sync for a coherent look.
"""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

_CSS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "assets" / "styles" / "theme.css"
)

# =============================================================================
# Design Tokens
# =============================================================================
# Every value here mirrors a CSS custom property defined in theme.css.
# The key name strips the leading "--" from the CSS variable name so that
# colour("accent-gold") corresponds to var(--accent-gold).

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


# =============================================================================
# Public API
# =============================================================================


def apply_theme() -> None:
    """Load theme.css and inject it into the Streamlit app.

    Reads the stylesheet from disk and wraps it in a <style> block injected
    via st.markdown. This must be called once at the top of app.py, before
    any page content is rendered. Subsequent calls on the same run are
    harmless because Streamlit deduplicates identical markdown blocks.

    Logs a warning and returns without raising if the CSS file is missing,
    so the app remains functional (unstyled) in environments where the
    assets directory is absent.
    """
    if not _CSS_PATH.exists():
        logger.warning(
            "Theme CSS not found at %s; app will render unstyled.", _CSS_PATH
        )
        return

    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def colour(name: str) -> str:
    """Return the hex colour value for a design token name.

    Parameters
    ----------
    name:
        Token name as it appears in COLOURS, e.g. "accent-gold" for
        the CSS variable var(--accent-gold).

    Returns
    -------
    str
        Hex colour string. Falls back to "#FFFFFF" if the name is not
        found and logs a warning so unknown tokens are easy to spot.
    """
    value = COLOURS.get(name)
    if value is None:
        logger.warning(
            "Unknown colour token %r requested; falling back to #FFFFFF.", name
        )
        return "#FFFFFF"
    return value

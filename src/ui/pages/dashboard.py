"""Dashboard page — main overview after save is loaded.

Displays key stats, progress ring, completion breakdown,
equipped charms strip, nail+soul widget, and closest-to-complete categories.
"""

from __future__ import annotations

import streamlit as st

from src.data.save_model import SaveData
from src.ui.components.stat_card import stat_card
from src.ui.components.header import render_header
from src.core.session import SAVE_DATA, SPOILERS_ON


def show_dashboard() -> None:
    """Render the main dashboard page."""
    save: SaveData = st.session_state[SAVE_DATA]

    # Row 1 — Header
    render_header()

    spoilers_on: bool = st.session_state[SPOILERS_ON]

    # Row 2 — Four stat cards
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    total_bosses = len(save.bosses)
    defeated_bosses = sum(1 for b in save.bosses if b.defeated)
    charms_owned = sum(1 for c in save.charms if c.owned)
    grubs_collected = (
        save.collectibles.grubs.grubs_collected if save.collectibles.grubs else 0
    )

    with c1:
        stat_card(
            "Bosses Defeated",
            (
                f"{defeated_bosses} / {total_bosses}"
                if spoilers_on
                else f"{defeated_bosses} / ??"
            ),
            colour="red",
        )
    with c2:
        stat_card(
            "Charms Owned",
            f"{charms_owned} / 40" if spoilers_on else f"{charms_owned} / ??",
            colour="purple",
        )
    with c3:
        stat_card(
            "Grubs Rescued",
            f"{grubs_collected} / 46" if spoilers_on else f"{grubs_collected} / ??",
            colour="blue",
        )
    with c4:
        stat_card(
            "Completion",
            (
                f"{save.completion_percent}% / 112%"
                if spoilers_on
                else f"{save.completion_percent}% / ??"
            ),
            colour="gold",
        )

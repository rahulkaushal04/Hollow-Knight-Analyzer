"""Dashboard page — main overview after save is loaded.

Displays key stats, progress ring, completion breakdown,
equipped charms strip, nail+soul widget, and closest-to-complete categories.
"""

from __future__ import annotations

import streamlit as st

from src.core.session import SAVE_DATA, SPOILERS_ON
from src.data.save_model import SaveData
from src.data.completion import calculate_completion, CompletionBreakdown
from src.ui.components.header import render_header
from src.ui.components.stat_card import stat_card


def show_dashboard() -> None:
    """Render the main dashboard page."""
    save: SaveData = st.session_state[SAVE_DATA]
    stats = save.player_stats
    breakdown = calculate_completion(save)

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
                else str(defeated_bosses)
            ),
            colour="red",
        )
    with c2:
        stat_card(
            "Charms Owned",
            f"{charms_owned} / 40" if spoilers_on else str(charms_owned),
            colour="purple",
        )
    with c3:
        stat_card(
            "Grubs Rescued",
            f"{grubs_collected} / 46" if spoilers_on else str(grubs_collected),
            colour="blue",
        )
    with c4:
        stat_card("Completion", f"{save.completion_percent}%", colour="gold")

    # Row 3 — Progress ring + Quick Stats
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        st.markdown(
            "<h3 style=\"font-family:'Cinzel',serif;color:var(--accent-gold);\">"
            "Completion Progress</h3>",
            unsafe_allow_html=True,
        )
        ring_col, table_col = st.columns([1, 2])
        with table_col:
            _render_breakdown_table(breakdown)

    with right:
        st.markdown(
            "<h3 style=\"font-family:'Cinzel',serif;color:var(--accent-gold);\">"
            "Quick Stats</h3>",
            unsafe_allow_html=True,
        )
        _quick_stat("Dream Orbs", f"{save.collectibles.dream_orbs:,}")
        if stats.play_time > 0:
            hours = int(stats.play_time) // 3600
            minutes = (int(stats.play_time) % 3600) // 60
            _quick_stat("Play Time", f"{hours}h {minutes}m")

    st.markdown("<br>", unsafe_allow_html=True)
    _render_closest_to_complete(breakdown)


def _quick_stat(label: str, value: str) -> None:
    """Render an inline quick stat row."""
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;'
        f'border-bottom:1px solid var(--border);">'
        f'<span style="color:var(--text-secondary);font-size:0.85rem;">{label}</span>'
        f"<span style=\"font-family:'Fira Code',monospace;font-size:0.85rem;"
        f'color:var(--text-primary);">{value}</span></div>',
        unsafe_allow_html=True,
    )


def _render_breakdown_table(breakdown: CompletionBreakdown) -> None:
    """Render completion breakdown as a styled table."""
    rows = []
    for cat in breakdown.categories:
        if cat.total == 0:
            continue
        pct = cat.percent
        if pct >= 100:
            bar_colour = "#4A9B6F"
        elif pct >= 50:
            bar_colour = "#C9A84C"
        else:
            bar_colour = "#C44B4B"

        rows.append(
            f"""
        <tr>
            <td style="padding:3px 6px;color:var(--text-primary);font-size:0.8rem;">
                {cat.name}</td>
            <td style="padding:3px 6px;font-family:'Fira Code',monospace;font-size:0.78rem;
                color:var(--text-secondary);text-align:right;">{cat.current}/{cat.total}</td>
            <td style="padding:3px 6px;width:100px;">
                <div style="background:var(--border);border-radius:3px;height:8px;overflow:hidden;">
                    <div class="progress-bar-fill" style="width:{min(pct, 100):.0f}%;height:100%;
                         background:{bar_colour};border-radius:3px;"></div>
                </div>
            </td>
        </tr>
        """
        )
    rows_html = "".join(rows)

    st.markdown(
        f"""
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid var(--border);">
                    <th style="text-align:left;padding:4px 6px;color:var(--text-secondary);
                        font-size:0.75rem;">Category</th>
                    <th style="text-align:right;padding:4px 6px;color:var(--text-secondary);
                        font-size:0.75rem;">Progress</th>
                    <th style="padding:4px 6px;color:var(--text-secondary);
                        font-size:0.75rem;">Bar</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def _render_closest_to_complete(breakdown: CompletionBreakdown) -> None:
    """Show categories closest to 100% completion."""
    candidates = [
        cat for cat in breakdown.categories if cat.total > 0 and 60 <= cat.percent < 100
    ]
    candidates.sort(key=lambda c: c.percent, reverse=True)
    top = candidates[:3]

    if not top:
        return

    st.markdown(
        "<h3 style=\"font-family:'Cinzel',serif;color:var(--accent-gold);\">"
        "Closest to Complete</h3>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(top))
    for i, cat in enumerate(top):
        remaining = cat.total - cat.current
        with cols[i]:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div style="color:var(--text-secondary);font-size:0.8rem;
                         margin-bottom:4px;">{cat.name}</div>
                    <div style="font-family:'Fira Code',monospace;font-size:1.2rem;
                         color:var(--accent-gold);">{cat.percent:.0f}%</div>
                    <div style="background:var(--border);border-radius:3px;height:8px;
                         margin:6px 0;overflow:hidden;">
                        <div class="progress-bar-fill" style="width:{cat.percent:.0f}%;
                             height:100%;background:var(--accent-gold);border-radius:3px;">
                        </div>
                    </div>
                    <div style="color:var(--text-secondary);font-size:0.75rem;">
                        {remaining} remaining</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

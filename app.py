"""Hallownest Codex — Hollow Knight Save Analyzer.

Streamlit entry point. Configures the page, applies the theme,
initializes session state, renders navigation, and routes to pages.
"""

from __future__ import annotations

import streamlit as st

# 1. Page config — must be the very first Streamlit call
st.set_page_config(
    page_title="Hallownest Codex",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.ui.theme import apply_theme
from src.ui.pages.upload import show_upload_page
from src.ui.pages.dashboard import show_dashboard
from src.core.session import init_session, SAVE_LOADED, ACTIVE_PAGE

# 2. Apply theme
apply_theme()

# 3. Init session state
init_session()


# 5. Route to correct page
if not st.session_state[SAVE_LOADED]:
    show_upload_page()
else:
    page = st.session_state[ACTIVE_PAGE]
    if page == "dashboard":
        show_dashboard()
    else:
        show_dashboard()

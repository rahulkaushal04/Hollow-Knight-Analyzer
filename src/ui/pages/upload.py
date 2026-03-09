"""Upload page -- landing page for save file upload.

Full-width page shown when no save is loaded. Provides a file uploader,
step-by-step instructions, and OS-specific save file location help.
"""

from __future__ import annotations

import streamlit as st

from src.core.session import (
    ACTIVE_PAGE,
    RAW_SAVE_DICT,
    SAVE_DATA,
    SAVE_LOADED,
    UPLOAD_ERROR,
)
from src.core.file_handler import FileHandlerError, handle_upload


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEP_CARDS: list[tuple[str, str, str]] = [
    ("🗂️", "Step 1", "Locate your save file on your computer"),
    ("📤", "Step 2", "Upload your <code>.dat</code> file above"),
    ("📊", "Step 3", "Explore charms, bosses, completion and more"),
]

_SAVE_LOCATIONS = {
    "Windows": r"%AppData%\LocalLow\Team Cherry\Hollow Knight\\",
    "macOS": "~/Library/Application Support/unity.Team Cherry.Hollow Knight/",
    "Linux": "~/.config/unity3d/Team Cherry/Hollow Knight/",
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_header() -> None:
    """Render the page title and subtitle."""
    st.markdown(
        '<h1 class="page-title" style="text-align:center; margin-top:2rem;">'
        "Hallownest Codex"
        "</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="'
        "text-align:center;"
        "color:var(--text-secondary);"
        "font-size:1.1rem;"
        'margin-bottom:2rem;">'
        "Upload your Hollow Knight save file to begin exploring your journey"
        " through Hallownest."
        "</p>",
        unsafe_allow_html=True,
    )


def _render_uploader() -> None:
    """Render the centred file upload zone and handle the uploaded file."""
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drop your .dat save file here",
            type=["dat"],
            key="save_uploader",
            label_visibility="visible",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        _handle_upload_error()

        if uploaded_file is not None:
            _process_upload(uploaded_file)


def _handle_upload_error() -> None:
    """Display any pending upload error, then clear it from session state."""
    error = st.session_state.get(UPLOAD_ERROR)
    if error:
        st.error(error)
        st.session_state[UPLOAD_ERROR] = None


def _process_upload(uploaded_file: object) -> None:
    """Decrypt, parse, and store the uploaded save file.

    On success, transitions the app to the dashboard page.
    On failure, stores a user-friendly error message and reruns.
    """
    with st.spinner("Decrypting and parsing your save file..."):
        try:
            save_data, raw_dict = handle_upload(uploaded_file)
        except FileHandlerError as exc:
            st.session_state[UPLOAD_ERROR] = exc.user_message
            st.rerun()
            return

    st.session_state[SAVE_DATA] = save_data
    st.session_state[RAW_SAVE_DICT] = raw_dict
    st.session_state[SAVE_LOADED] = True
    st.session_state[ACTIVE_PAGE] = "dashboard"
    st.session_state[UPLOAD_ERROR] = None
    st.rerun()


def _render_steps() -> None:
    """Render the three-step instruction cards below the upload zone."""
    st.markdown("<br>", unsafe_allow_html=True)

    for col, (icon, label, description) in zip(st.columns(3), _STEP_CARDS):
        with col:
            st.markdown(
                f"""
                <div class="stat-card" style="text-align:center;">
                    <div style="font-size:2rem; margin-bottom:8px;">{icon}</div>
                    <div style="
                        font-family:'Cinzel', serif;
                        color:var(--accent-gold);
                        font-size:1rem;
                        margin-bottom:4px;
                    ">{label}</div>
                    <div style="color:var(--text-secondary); font-size:0.85rem;">
                        {description}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_save_location_help() -> None:
    """Render a collapsible expander with OS-specific save file paths.

    Save files are named user1.dat through user4.dat, matching slots 1 to 4.
    """
    with st.expander("📁 Where is my save file?"):
        for os_name, path in _SAVE_LOCATIONS.items():
            st.markdown(f"**{os_name}:**")
            st.code(path, language=None)

        st.markdown(
            "Your save files are named `user1.dat`, `user2.dat`, `user3.dat`,"
            " or `user4.dat`, corresponding to save slots 1 to 4."
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def show_upload_page() -> None:
    """Render the full upload landing page.

    Composed of four sections rendered in order:
        1. Page header and subtitle
        2. Centred file upload zone with error handling
        3. Three-step instruction cards
        4. Collapsible save file location help
    """
    _render_header()
    _render_uploader()
    _render_steps()
    _render_save_location_help()

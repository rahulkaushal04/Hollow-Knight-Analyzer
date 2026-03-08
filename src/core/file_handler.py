"""
Streamlit save file upload handler.

This module processes Hollow Knight save files uploaded through
the Streamlit interface. The workflow is:

1. Validate the uploaded file
2. Read the binary contents
3. Decrypt the save file
4. Parse the JSON payload
5. Convert the JSON structure into a typed SaveData model

On success the handler returns both the structured SaveData object
and the raw dictionary representation of the save file.
"""

from __future__ import annotations

import re
import json
import logging
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.core.decryptor.main import HollowKnightDecryptor
from src.core.decryptor.exceptions import DecryptionError
from src.core.save_parser import parse_save
from src.data.save_model import SaveData


logger = logging.getLogger(__name__)


class FileHandlerError(Exception):
    """
    Exception raised when save file handling fails.

    The exception contains two messages:

    user_message
        A message suitable for display in the UI.

    technical_detail
        Additional debugging information useful for logs.
    """

    def __init__(self, user_message: str, technical_detail: str = "") -> None:
        self.user_message = user_message
        self.technical_detail = technical_detail
        super().__init__(user_message)


def _detect_save_slot(filename: str) -> int:
    """
    Determine the Hollow Knight save slot from a filename.

    Hollow Knight uses filenames such as:

        user1.dat
        user2.dat
        user3.dat
        user4.dat

    If the slot cannot be determined, slot 1 is returned as a fallback.
    """
    name = filename.lower()

    match = re.search(r"user(\d)", name)
    if match:
        return int(match.group(1))

    if "user" in name:
        return 1

    return 1


def handle_upload(uploaded_file: "UploadedFile") -> tuple[SaveData, dict]:
    """
    Process an uploaded Hollow Knight save file.

    Steps performed:

        1. Validate the uploaded file
        2. Read the raw binary data
        3. Decrypt the save file
        4. Parse the JSON payload
        5. Convert JSON into a SaveData model

    Parameters
    ----------
    uploaded_file
        Streamlit UploadedFile object.

    Returns
    -------
    tuple[SaveData, dict]

        SaveData
            Parsed and typed representation of the save file.

        dict
            Raw dictionary representation of the decrypted JSON.

    Raises
    ------
    FileHandlerError
        Raised when validation, decryption, or parsing fails.
        The error includes a user facing message.
    """

    if uploaded_file is None:
        raise FileHandlerError(
            "No file was uploaded. Please select a Hollow Knight .dat save file."
        )

    filename = uploaded_file.name or "unknown.dat"

    if not filename.lower().endswith(".dat"):
        raise FileHandlerError(
            "Invalid file type. Please upload a Hollow Knight .dat save file.",
            f"Filename received: {filename}",
        )

    # ------------------------------------------------------------------
    # Read uploaded file
    # ------------------------------------------------------------------

    try:
        raw_bytes = uploaded_file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise FileHandlerError(
            "Failed to read the uploaded file. Please try again.",
            str(e),
        )

    if not raw_bytes:
        raise FileHandlerError(
            "The uploaded file is empty. Please select a valid save file."
        )

    if len(raw_bytes) < 50:
        raise FileHandlerError(
            "The file is too small to be a valid Hollow Knight save file.",
            f"File size: {len(raw_bytes)} bytes",
        )

    # ------------------------------------------------------------------
    # Decrypt save file
    # ------------------------------------------------------------------

    try:
        decryptor = HollowKnightDecryptor()
        json_string = decryptor.decrypt_bytes(raw_bytes)

    except DecryptionError as e:
        logger.error(f"Save file decryption failed: {e}")

        raise FileHandlerError(
            "Failed to decrypt the save file. Ensure this is a valid "
            "Hollow Knight save file from your save directory.",
            str(e),
        )

    except Exception as e:
        logger.exception("Unexpected error during save file decryption")

        raise FileHandlerError(
            "An unexpected error occurred during decryption. "
            "The save file may be corrupted.",
            str(e),
        )

    # ------------------------------------------------------------------
    # Parse JSON payload
    # ------------------------------------------------------------------

    try:
        raw_dict = json.loads(json_string)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse decrypted JSON: {e}")

        raise FileHandlerError(
            "The decrypted data is not valid JSON. "
            "The save file may be corrupted.",
            str(e),
        )

    if not isinstance(raw_dict, dict):
        raise FileHandlerError(
            "Unexpected save file format. Expected a JSON object.",
            f"Received type: {type(raw_dict).__name__}",
        )

    # ------------------------------------------------------------------
    # Convert dictionary into SaveData model
    # ------------------------------------------------------------------

    try:
        save_data = parse_save(raw_dict)

    except Exception as e:
        logger.error(f"Save data parsing failed: {e}")

        raise FileHandlerError(
            "The save file was decrypted but could not be parsed. "
            "It may come from an unsupported game version.",
            str(e),
        )

    slot = _detect_save_slot(filename)

    logger.info(
        f"Successfully processed Hollow Knight save file "
        f"(slot {slot}, filename={filename})"
    )

    return save_data, raw_dict

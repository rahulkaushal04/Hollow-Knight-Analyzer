"""
Hollow Knight save file decryption engine.

This module implements the complete decryption pipeline used by
Hollow Knight save files.

Encryption pipeline used by the game:

    JSON -> PKCS7 padding -> AES-256 ECB encryption
         -> BASE64 encoding -> C# BinaryFormatter serialization

The save file therefore contains a serialized .NET BinaryFormatter object
that stores a BASE64 string representing AES encrypted data.

Decryption reverses the process:

    Binary file
        -> Remove BinaryFormatter header
        -> Extract BASE64 payload
        -> BASE64 decode
        -> AES-256 ECB decrypt
        -> Remove PKCS7 padding
        -> UTF-8 decode to JSON
"""

from __future__ import annotations

import json
import base64
import logging
from pathlib import Path
from typing import Any, Tuple, Union

from Crypto.Cipher import AES

from src.core.decryptor.exceptions import (
    AESDecryptionError,
    Base64DecodeError,
    DecryptionError,
    InvalidFooterError,
    InvalidHeaderError,
)

logger = logging.getLogger(__name__)

# AES-256 encryption key used by Hollow Knight
ENCRYPTION_KEY: bytes = b"UKu52ePUBwetZ9wNX88o54dnfKRu0T1l"

# Fixed BinaryFormatter header that precedes the BASE64 payload
CSHARP_HEADER: bytes = bytes.fromhex("0001000000FFFFFFFF01000000000000000601000000")

# BinaryFormatter serialized strings terminate with this byte
END_BYTE: bytes = b"\x0b"

# AES block size in bytes
BLOCK_SIZE: int = 16


class HollowKnightDecryptor:
    """
    Decrypt Hollow Knight save files.

    The class implements the full decryption pipeline used by the game.
    It can operate on files from disk or raw byte sequences already
    loaded in memory.
    """

    def __init__(self, key: bytes = ENCRYPTION_KEY) -> None:
        """
        Initialize the decryptor.

        Parameters
        ----------
        key:
            32 byte AES-256 key used by the game.
        """
        if len(key) != 32:
            raise ValueError(
                f"AES-256 requires a 32 byte key, received {len(key)} bytes"
            )

        self.key: bytes = key
        logger.debug("HollowKnightDecryptor initialized")

    def load_encrypted_file(self, filepath: Union[str, Path]) -> bytes:
        """
        Read a save file from disk.

        Returns the raw binary contents of the file.
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Save file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Expected a file but received directory: {path}")

        try:
            data = path.read_bytes()
            logger.info(f"Loaded {len(data)} bytes from {path}")
            return data

        except PermissionError as e:
            raise PermissionError(f"Permission denied reading {path}") from e

        except OSError as e:
            raise IOError(f"Failed to read {path}") from e

    def _parse_7bit_encoded_int(self, data: bytes, offset: int) -> Tuple[int, int]:
        """
        Parse a .NET BinaryReader 7 bit encoded integer.

        BinaryFormatter uses this encoding to store string lengths.

        Returns
        -------
        (value, new_offset)
        """
        result = 0
        shift = 0

        while True:
            if offset >= len(data):
                raise DecryptionError("Truncated 7 bit encoded integer")

            byte = data[offset]
            offset += 1

            result |= (byte & 0x7F) << shift

            if (byte & 0x80) == 0:
                break

            shift += 7

        return result, offset

    def strip_header(self, raw_data: bytes) -> bytes:
        """
        Remove the BinaryFormatter wrapper and extract the BASE64 payload.

        The file layout is:

            [BinaryFormatter header]
            [7 bit encoded string length]
            [BASE64 string bytes]
            [terminating byte]
        """

        if not raw_data.startswith(CSHARP_HEADER):
            raise InvalidHeaderError(
                message="Invalid BinaryFormatter header",
                expected=CSHARP_HEADER.hex(),
                actual=raw_data[: len(CSHARP_HEADER)].hex(),
            )

        if not raw_data.endswith(END_BYTE):
            raise InvalidFooterError(
                message="Missing BinaryFormatter end byte",
                expected=END_BYTE.hex(),
                actual=raw_data[-1:].hex(),
            )

        try:
            header_end = len(CSHARP_HEADER)

            length, data_start = self._parse_7bit_encoded_int(raw_data, header_end)

            base64_data = raw_data[data_start:-1]

            if len(base64_data) != length:
                logger.warning(
                    "Length mismatch in BinaryFormatter payload. "
                    f"Encoded length={length}, actual={len(base64_data)}"
                )

            logger.debug(
                f"Header stripped: {len(raw_data)} -> {len(base64_data)} bytes"
            )

            return base64_data

        except DecryptionError:
            raise

        except Exception as e:
            raise DecryptionError("Failed to parse BinaryFormatter structure") from e

    def decode_base64(self, encrypted_data: Union[bytes, str]) -> bytes:
        """
        Decode the BASE64 encoded encrypted payload.
        """
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode("utf-8")

            decoded = base64.b64decode(encrypted_data, validate=True)

            logger.debug(
                f"BASE64 decoded: {len(encrypted_data)} -> {len(decoded)} bytes"
            )

            return decoded

        except Exception as e:
            raise Base64DecodeError(f"BASE64 decoding failed: {e}") from e

    def decrypt_aes(self, encoded_data: bytes) -> bytes:
        """
        Decrypt AES-256 ECB data and remove PKCS7 padding.
        """

        if len(encoded_data) % BLOCK_SIZE != 0:
            raise AESDecryptionError(
                message=(
                    f"Encrypted data length ({len(encoded_data)}) "
                    f"is not a multiple of AES block size ({BLOCK_SIZE})"
                ),
                data_length=len(encoded_data),
            )

        try:
            cipher = AES.new(self.key, AES.MODE_ECB)
            decrypted_padded = cipher.decrypt(encoded_data)

            padding_length = decrypted_padded[-1]

            if not (1 <= padding_length <= BLOCK_SIZE):
                raise AESDecryptionError(
                    message=f"Invalid PKCS7 padding length: {padding_length}",
                    data_length=len(encoded_data),
                )

            padding = decrypted_padded[-padding_length:]

            if padding != bytes([padding_length]) * padding_length:
                raise AESDecryptionError(
                    message="Invalid PKCS7 padding bytes",
                    data_length=len(encoded_data),
                )

            decrypted_data = decrypted_padded[:-padding_length]

            logger.debug(
                f"AES decrypted and unpadded: "
                f"{len(decrypted_padded)} -> {len(decrypted_data)} bytes"
            )

            return decrypted_data

        except AESDecryptionError:
            raise

        except Exception as e:
            raise AESDecryptionError(
                message=f"AES decryption failed: {e}",
                data_length=len(encoded_data),
            ) from e

    def decrypt(self, input_filepath: Union[str, Path]) -> str:
        """
        Decrypt a Hollow Knight save file from disk.

        Returns
        -------
        JSON string representing the save state.
        """

        logger.info(f"Beginning decryption of {input_filepath}")

        try:
            raw_data = self.load_encrypted_file(input_filepath)
            base64_data = self.strip_header(raw_data)
            decoded_data = self.decode_base64(base64_data)
            decrypted_bytes = self.decrypt_aes(decoded_data)

            json_string = decrypted_bytes.decode("utf-8")

            logger.info(f"Decryption successful: {len(json_string)} characters")

            return json_string

        except (FileNotFoundError, DecryptionError):
            raise

        except UnicodeDecodeError as e:
            raise DecryptionError(
                "UTF-8 decoding failed. Decrypted data is not valid text."
            ) from e

        except Exception as e:
            raise DecryptionError(f"Unexpected decryption error: {e}") from e

    def decrypt_bytes(self, raw_data: bytes) -> str:
        """
        Decrypt raw save file bytes already loaded in memory.
        """

        logger.info(f"Decrypting {len(raw_data)} bytes")

        try:
            base64_data = self.strip_header(raw_data)
            decoded_data = self.decode_base64(base64_data)
            decrypted_bytes = self.decrypt_aes(decoded_data)

            json_string = decrypted_bytes.decode("utf-8")

            logger.info(f"Decryption successful: {len(json_string)} characters")

            return json_string

        except DecryptionError:
            raise

        except UnicodeDecodeError as e:
            raise DecryptionError(
                "UTF-8 decoding failed. Decrypted data is not valid text."
            ) from e

        except Exception as e:
            raise DecryptionError(f"Unexpected decryption error: {e}") from e

    def decrypt_to_file(
        self,
        input_filepath: Union[str, Path],
        output_filepath: Union[str, Path],
        pretty: bool = True,
    ) -> Path:
        """
        Decrypt a save file and write the resulting JSON to disk.
        """

        json_string = self.decrypt(input_filepath)
        output_path = Path(output_filepath)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if pretty:
                data: Any = json.loads(json_string)
                formatted = json.dumps(data, indent=2, ensure_ascii=False)
                output_path.write_text(formatted, encoding="utf-8")
            else:
                output_path.write_text(json_string, encoding="utf-8")

            logger.info(f"Decrypted JSON written to {output_path}")

            return output_path

        except json.JSONDecodeError:
            logger.warning("Decrypted content is not valid JSON. Writing raw output.")
            output_path.write_text(json_string, encoding="utf-8")
            return output_path

        except OSError as e:
            raise IOError(f"Failed to write output file {output_path}") from e

"""
Custom exception types used by the Hollow Knight save file decryptor.

These exceptions provide structured error information so that callers
can distinguish between different failure points in the decryption
pipeline.
"""

from __future__ import annotations


class DecryptionError(Exception):
    """
    Base exception for all Hollow Knight save decryption failures.

    All specific decryptor exceptions inherit from this class so callers
    can catch a single error type if desired.
    """

    def __init__(self, message: str = "Decryption failed") -> None:
        super().__init__(message)


class InvalidHeaderError(DecryptionError):
    """
    Raised when the BinaryFormatter header signature is invalid.
    """

    def __init__(
        self,
        message: str = "Invalid BinaryFormatter header",
        expected: str = "",
        actual: str = "",
    ) -> None:
        self.expected = expected
        self.actual = actual

        if expected and actual:
            message = f"{message}. Expected {expected}, received {actual}"

        super().__init__(message)


class InvalidFooterError(DecryptionError):
    """
    Raised when the terminating byte of the serialized payload is missing.
    """

    def __init__(
        self,
        message: str = "Invalid BinaryFormatter footer",
        expected: str = "",
        actual: str = "",
    ) -> None:
        self.expected = expected
        self.actual = actual

        if expected and actual:
            message = f"{message}. Expected {expected}, received {actual}"

        super().__init__(message)


class Base64DecodeError(DecryptionError):
    """
    Raised when the BASE64 payload cannot be decoded.
    """

    def __init__(self, message: str = "BASE64 decoding failed") -> None:
        super().__init__(message)


class AESDecryptionError(DecryptionError):
    """
    Raised when AES decryption or padding validation fails.
    """

    def __init__(
        self,
        message: str = "AES decryption failed",
        data_length: int = 0,
    ) -> None:
        self.data_length = data_length

        if data_length:
            message = f"{message}. Encrypted data length: {data_length} bytes"

        super().__init__(message)

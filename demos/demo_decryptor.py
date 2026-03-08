"""
Demo script to test the Decryptor module.

Save file locations by operating system:

    Windows:
        %APPDATA%\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat
        e.g. C:\\Users\\Alice\\AppData\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat

    macOS:
        $HOME/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat
        e.g. /Users/alice/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat

    Linux:
        $HOME/.config/unity3d/Team Cherry/Hollow Knight/user1.dat
        e.g. /home/alice/.config/unity3d/Team Cherry/Hollow Knight/user1.dat

    Note: Save slots are named user1.dat through user4.dat.
    Note: Use $HOME instead of ~ for path expansion to work correctly inside quotes.

Usage examples (Windows):
    python demo_decryptor.py decrypt --file "%APPDATA%\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat"
    python demo_decryptor.py decrypt --file "%APPDATA%\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat" --output "save.json"
    python demo_decryptor.py decrypt --file "%APPDATA%\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat" --pretty
    python demo_decryptor.py decrypt --file "%APPDATA%\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat" --key "playerData"
    python demo_decryptor.py pipeline --file "%APPDATA%\\LocalLow\\Team Cherry\\Hollow Knight\\user1.dat"

Usage examples (macOS):
    python demo_decryptor.py decrypt --file "$HOME/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat"
    python demo_decryptor.py decrypt --file "$HOME/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat" --output "save.json"
    python demo_decryptor.py decrypt --file "$HOME/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat" --pretty
    python demo_decryptor.py decrypt --file "$HOME/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat" --key "playerData"
    python demo_decryptor.py pipeline --file "$HOME/Library/Application Support/unity.Team Cherry.Hollow Knight/user1.dat"

Usage examples (Linux):
    python demo_decryptor.py decrypt --file "$HOME/.config/unity3d/Team Cherry/Hollow Knight/user1.dat"
    python demo_decryptor.py decrypt --file "$HOME/.config/unity3d/Team Cherry/Hollow Knight/user1.dat" --output "save.json"
    python demo_decryptor.py decrypt --file "$HOME/.config/unity3d/Team Cherry/Hollow Knight/user1.dat" --pretty
    python demo_decryptor.py decrypt --file "$HOME/.config/unity3d/Team Cherry/Hollow Knight/user1.dat" --key "playerData"
    python demo_decryptor.py pipeline --file "$HOME/.config/unity3d/Team Cherry/Hollow Knight/user1.dat"

General usage (any OS):
    # Show module info (key length, header hex, etc.)
    python demo_decryptor.py info
"""

import sys
import json
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.decryptor.main import (
    HollowKnightDecryptor,
    ENCRYPTION_KEY,
    CSHARP_HEADER,
    END_BYTE,
    BLOCK_SIZE,
)
from src.core.decryptor.exceptions import (
    DecryptionError,
    InvalidHeaderError,
    InvalidFooterError,
    Base64DecodeError,
    AESDecryptionError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(name)s: %(message)s",
    )


def _load_decryptor() -> HollowKnightDecryptor:
    return HollowKnightDecryptor(key=ENCRYPTION_KEY)


# ---------------------------------------------------------------------------
# Sub-command: decrypt
# ---------------------------------------------------------------------------


def cmd_decrypt(args: argparse.Namespace) -> int:
    decryptor = _load_decryptor()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        json_string = decryptor.decrypt(file_path)
    except InvalidHeaderError as e:
        print(f"[ERROR] Header validation failed: {e}", file=sys.stderr)
        return 2
    except InvalidFooterError as e:
        print(f"[ERROR] Footer validation failed: {e}", file=sys.stderr)
        return 2
    except Base64DecodeError as e:
        print(f"[ERROR] BASE64 decoding failed: {e}", file=sys.stderr)
        return 2
    except AESDecryptionError as e:
        print(f"[ERROR] AES decryption failed: {e}", file=sys.stderr)
        return 2
    except DecryptionError as e:
        print(f"[ERROR] Decryption failed: {e}", file=sys.stderr)
        return 2

    # Optionally parse and filter the JSON
    if args.pretty or args.key:
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Decrypted output is not valid JSON: {e}", file=sys.stderr)
            return 3

        if args.key:
            if args.key not in data:
                available = ", ".join(data.keys()) if isinstance(data, dict) else "N/A"
                print(
                    f"[ERROR] Key '{args.key}' not found. "
                    f"Top-level keys: {available}",
                    file=sys.stderr,
                )
                return 3
            data = data[args.key]

        json_string = json.dumps(data, indent=2 if args.pretty else None)

    # Write output
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json_string, encoding="utf-8")
        print(f"[OK] Decrypted save written to: {out_path}")
    else:
        print(json_string)

    return 0


# ---------------------------------------------------------------------------
# Sub-command: pipeline
# ---------------------------------------------------------------------------


def cmd_pipeline(args: argparse.Namespace) -> int:
    """
    Walk through each decryption stage separately and report success/failure
    for each step. Useful for diagnosing which stage fails.
    """
    decryptor = _load_decryptor()
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}", file=sys.stderr)
        return 1

    print(f"File        : {file_path}")
    print(f"File size   : {file_path.stat().st_size} bytes")
    print()

    # Step 1 – Load raw bytes
    try:
        raw = decryptor.load_encrypted_file(file_path)
        print(f"[PASS] Step 1 – Load file          : {len(raw)} bytes read")
    except Exception as e:
        print(f"[FAIL] Step 1 – Load file          : {e}", file=sys.stderr)
        return 2

    # Step 2 – Strip BinaryFormatter header
    try:
        b64_data = decryptor.strip_header(raw)
        print(f"[PASS] Step 2 – Strip header        : {len(b64_data)} bytes extracted")
    except InvalidHeaderError as e:
        print(f"[FAIL] Step 2 – Strip header        : {e}", file=sys.stderr)
        return 2
    except InvalidFooterError as e:
        print(f"[FAIL] Step 2 – Strip footer        : {e}", file=sys.stderr)
        return 2

    # Step 3 – BASE64 decode
    try:
        aes_data = decryptor.decode_base64(b64_data)
        print(f"[PASS] Step 3 – BASE64 decode       : {len(aes_data)} bytes decoded")
    except Base64DecodeError as e:
        print(f"[FAIL] Step 3 – BASE64 decode       : {e}", file=sys.stderr)
        return 2

    # Step 4 – AES-256 ECB decrypt + PKCS7 unpad
    try:
        plain_bytes = decryptor.decrypt_aes(aes_data)
        print(
            f"[PASS] Step 4 – AES decrypt         : {len(plain_bytes)} bytes decrypted"
        )
    except AESDecryptionError as e:
        print(f"[FAIL] Step 4 – AES decrypt         : {e}", file=sys.stderr)
        return 2

    # Step 5 – UTF-8 decode
    try:
        json_string = plain_bytes.decode("utf-8")
        print(f"[PASS] Step 5 – UTF-8 decode        : {len(json_string)} characters")
    except UnicodeDecodeError as e:
        print(f"[FAIL] Step 5 – UTF-8 decode        : {e}", file=sys.stderr)
        return 2

    # Step 6 – JSON parse check
    try:
        data = json.loads(json_string)
        top_keys = list(data.keys()) if isinstance(data, dict) else []
        print(f"[PASS] Step 6 – JSON parse          : {len(top_keys)} top-level keys")
        if top_keys:
            print(
                f"       Top-level keys: {', '.join(top_keys[:10])}"
                + (" ..." if len(top_keys) > 10 else "")
            )
    except json.JSONDecodeError as e:
        print(f"[FAIL] Step 6 – JSON parse          : {e}", file=sys.stderr)
        return 3

    print()
    print("[OK] All pipeline stages passed successfully.")
    return 0


# ---------------------------------------------------------------------------
# Sub-command: info
# ---------------------------------------------------------------------------


def cmd_info(_args: argparse.Namespace) -> int:
    print("HollowKnightDecryptor – module info")
    print("=" * 42)
    print(f"  AES key length  : {len(ENCRYPTION_KEY)} bytes (AES-256)")
    print(f"  AES key (text)  : {ENCRYPTION_KEY.decode()}")
    print(f"  AES mode        : ECB")
    print(f"  AES block size  : {BLOCK_SIZE} bytes")
    print(f"  Padding scheme  : PKCS7")
    print(f"  C# header (hex) : {CSHARP_HEADER.hex()}")
    print(f"  End byte (hex)  : {END_BYTE.hex()}")
    print(
        f"  Pipeline        : Binary -> Strip header -> BASE64 -> AES -> UTF-8 -> JSON"
    )
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo_decryptor",
        description="Demo tool for testing the HollowKnightDecryptor module.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging from the decryptor internals.",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # decrypt sub-command
    p_decrypt = sub.add_parser(
        "decrypt",
        help="Decrypt a Hollow Knight save file.",
    )
    p_decrypt.add_argument(
        "--file",
        "-f",
        required=True,
        metavar="PATH",
        help="Path to the encrypted save file (e.g. user1.dat).",
    )
    p_decrypt.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="Write decrypted JSON to this file instead of stdout.",
    )
    p_decrypt.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Pretty-print the output JSON with indentation.",
    )
    p_decrypt.add_argument(
        "--key",
        "-k",
        metavar="KEY",
        help="Print only this top-level JSON key from the decrypted save.",
    )
    p_decrypt.set_defaults(func=cmd_decrypt)

    # pipeline sub-command
    p_pipeline = sub.add_parser(
        "pipeline",
        help="Run each decryption stage separately and report pass/fail.",
    )
    p_pipeline.add_argument(
        "--file",
        "-f",
        required=True,
        metavar="PATH",
        help="Path to the encrypted save file.",
    )
    p_pipeline.set_defaults(func=cmd_pipeline)

    # info sub-command
    p_info = sub.add_parser(
        "info",
        help="Show decryptor module constants (key, header, etc.).",
    )
    p_info.set_defaults(func=cmd_info)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)
    sys.exit(args.func(args))

#!/usr/bin/env python3
"""
Smoke test for the LM Studio vision integration.

Validates the full local verification path:
  1. LM Studio server is reachable
  2. A vision-capable model is loaded
  3. LMStudioVisionClient can send before/after images and parse structured output

Usage:
  cd apps/api
  python scripts/smoke_test_lmstudio.py [--model MODEL] [--base-url URL]
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from app.integrations.lmstudio_client import LMStudioVisionClient


RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {CYAN}ℹ{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {msg}")


def section(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")


def create_test_image(path: Path, color: tuple[int, int, int], label: str) -> None:
    """Create a minimal valid PNG image with a solid color.

    Uses a raw uncompressed PNG with a single IDAT chunk.
    This is enough for vision models to see a distinct color.
    """
    import struct
    import zlib

    width, height = 64, 64
    r, g, b = color

    # Build raw image data: filter byte 0 + RGB pixels per row
    raw_data = b""
    for _ in range(height):
        raw_data += b"\x00"  # filter: none
        raw_data += bytes([r, g, b]) * width

    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + chunk + crc

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat_data = zlib.compress(raw_data)

    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr_data)
    png += png_chunk(b"IDAT", idat_data)
    png += png_chunk(b"IEND", b"")

    path.write_bytes(png)


def check_server(base_url: str) -> dict | None:
    """Check if LM Studio is reachable and return model list."""
    section("1. Server Connectivity")
    try:
        resp = requests.get(f"{base_url}/models", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        ok(f"LM Studio reachable at {base_url}")
        return data
    except requests.ConnectionError:
        fail(f"Cannot connect to LM Studio at {base_url}")
        info("Make sure LM Studio is running and the server is enabled.")
        info("In LM Studio: Menu → Local Server → Start Server")
        return None
    except Exception as exc:
        fail(f"Unexpected error checking server: {exc}")
        return None


def check_models(models_response: dict, requested_model: str | None) -> str | None:
    """Verify a suitable model is loaded and return the model ID to use."""
    section("2. Loaded Models")
    models = models_response.get("data", [])
    if not models:
        fail("No models loaded in LM Studio.")
        info("Load a vision-capable model (for example a Qwen VL model) in LM Studio first.")
        return None

    for m in models:
        model_id = m.get("id", "unknown")
        ok(f"Found model: {model_id}")

    if requested_model:
        ids = [m.get("id") for m in models]
        if requested_model in ids:
            ok(f"Requested model '{requested_model}' is loaded.")
            return requested_model
        else:
            warn(f"Requested model '{requested_model}' not found in loaded models.")
            info(f"Available: {ids}")
            fallback = ids[0]
            info(f"Falling back to: {fallback}")
            return fallback
    else:
        chosen = models[0].get("id")
        info(f"No model specified, using first loaded: {chosen}")
        return chosen


def run_verification(base_url: str, model: str) -> dict | None:
    """Send a real before/after verification request and return the result."""
    section("3. Vision Verification Request")

    with tempfile.TemporaryDirectory(prefix="bloom_smoke_") as tmp:
        tmp_path = Path(tmp)

        before_path = tmp_path / "before.png"
        after_path = tmp_path / "after.png"

        # Before: messy red, After: clean green
        create_test_image(before_path, (200, 60, 60), "messy")
        create_test_image(after_path, (60, 180, 60), "clean")
        info(f"Created test images: {before_path.name} (red), {after_path.name} (green)")

        gig = {
            "id": "gig_smoke_001",
            "title": "Clean bedroom",
            "description": "Tidy up your room: make the bed, clear the floor, put away toys.",
            "verification_checklist": ["bed made", "floor clear", "toys put away"],
        }

        before_photo = {
            "id": "photo_before_smoke",
            "gig_id": gig["id"],
            "kind": "before",
            "content_type": "image/png",
            "storage_ref": str(before_path),
        }

        after_photo = {
            "id": "photo_after_smoke",
            "gig_id": gig["id"],
            "kind": "after",
            "content_type": "image/png",
            "storage_ref": str(after_path),
        }

        client = LMStudioVisionClient(base_url=base_url, model=model)
        info(f"Sending verification to {model}...")
        info("(This may take 10-45s depending on model size)")

        start = time.time()
        try:
            result = client.verify(gig=gig, before_photo=before_photo, after_photo=after_photo)
        except RuntimeError as exc:
            elapsed = time.time() - start
            fail(f"Verification failed after {elapsed:.1f}s: {exc}")
            cause = getattr(exc, "__cause__", None)
            if cause:
                info(f"Cause: {cause}")
            return None
        elapsed = time.time() - start

        ok(f"Verification completed in {elapsed:.1f}s")
        return result


def print_result(result: dict) -> None:
    section("4. Verification Result")

    approved = result.get("approved")
    confidence = result.get("confidence")
    tags = result.get("tags", [])
    message = result.get("message_for_kid", "")
    reasoning = result.get("reasoning_summary", "")
    provider = result.get("raw_provider", "")
    model = result.get("raw_model", "")

    status = f"{GREEN}APPROVED{RESET}" if approved else f"{RED}REJECTED{RESET}"
    print(f"\n  Status:      {status}")
    print(f"  Confidence:  {confidence}")
    print(f"  Tags:        {', '.join(tags) if tags else '(none)'}")
    print(f"  Message:     {message}")
    print(f"  Reasoning:   {reasoning}")
    print(f"  Provider:    {provider}")
    print(f"  Model:       {model}")

    section("5. Structured Output Validation")
    errors = []
    if not isinstance(approved, bool):
        errors.append("'approved' is not a bool")
    if not isinstance(confidence, (int, float)):
        errors.append("'confidence' is not a number")
    elif not (0 <= confidence <= 1):
        errors.append(f"'confidence' out of range: {confidence}")
    if not isinstance(tags, list):
        errors.append("'tags' is not a list")
    if not message:
        errors.append("'message_for_kid' is empty")
    if not reasoning:
        errors.append("'reasoning_summary' is empty")
    if provider != "lmstudio":
        errors.append(f"'raw_provider' expected 'lmstudio', got '{provider}'")

    required_keys = {"id", "gig_id", "approved", "confidence", "tags",
                     "message_for_kid", "reasoning_summary", "raw_provider", "raw_model"}
    missing = required_keys - set(result.keys())
    if missing:
        errors.append(f"Missing keys: {missing}")

    if errors:
        for e in errors:
            fail(e)
    else:
        ok("All fields present and valid")
        ok("Schema matches VerificationResultModel")

    section("6. Raw JSON")
    print(f"  {DIM}{json.dumps(result, indent=2)}{RESET}")

    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Smoke test LM Studio vision integration")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1",
                        help="LM Studio base URL (default: http://127.0.0.1:1234/v1)")
    parser.add_argument("--model", default=None,
                        help="Model ID to use (default: first loaded model)")
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*60}")
    print("  bunq Bloom — LM Studio Vision Smoke Test")
    print(f"{'='*60}{RESET}")

    # Step 1: Check server
    models_response = check_server(args.base_url)
    if models_response is None:
        print(f"\n{RED}{BOLD}SMOKE TEST FAILED{RESET}: LM Studio not reachable.\n")
        sys.exit(1)

    # Step 2: Check models
    model = check_models(models_response, args.model)
    if model is None:
        print(f"\n{RED}{BOLD}SMOKE TEST FAILED{RESET}: No suitable model loaded.\n")
        sys.exit(1)

    # Step 3: Run verification
    result = run_verification(args.base_url, model)
    if result is None:
        print(f"\n{RED}{BOLD}SMOKE TEST FAILED{RESET}: Verification request failed.\n")
        sys.exit(1)

    # Step 4-6: Print and validate result
    valid = print_result(result)

    if valid:
        print(f"\n{GREEN}{BOLD}SMOKE TEST PASSED{RESET} ✓\n")
        sys.exit(0)
    else:
        print(f"\n{YELLOW}{BOLD}SMOKE TEST PASSED WITH WARNINGS{RESET} — output had validation issues.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.
This module integrates trusted timestamping using an external TSA (RFC 3161).
It uses the OpenSSL CLI to generate timestamp queries, and Python stdlib to POST
the query to the TSA URL. Replies (.tsr) are saved to disk, and a reference can
be embedded into audit entries.

Env Variables:
- IOA_TSA_URL: TSA endpoint URL (e.g., https://freetsa.org/tsr)
- IOA_TSA_NONCE: 1 to include nonce in request (default: 1)
- IOA_TSA_OUT_DIR: Directory for .tsr files (default: artifacts/timestamps)
- IOA_TSA_VERIFY: 1 to attempt verification (requires openssl and possibly CA)
- IOA_TSA_CA_FILE: Path to TSA CA bundle for verification (optional)
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen


@dataclass
class TimestampEvidence:
    tsr_path: str
    tsa_url: str
    digest_alg: str
    digest_hex: str
    nonce_included: bool
    tsr_sha256: str
    created_at: str


def _require_openssl() -> None:
    try:
        subprocess.run(["openssl", "version"], capture_output=True, check=True)
    except Exception as e:
        raise RuntimeError("OpenSSL CLI is required for RFC 3161 timestamping") from e


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def request_timestamp(digest_hex: str, digest_alg: str = "sha256") -> TimestampEvidence:
    tsa_url = os.getenv("IOA_TSA_URL")
    if not tsa_url:
        raise RuntimeError("IOA_TSA_URL not set; timestamping is disabled")

    _require_openssl()

    out_dir = Path(os.getenv("IOA_TSA_OUT_DIR", "artifacts/timestamps"))
    out_dir.mkdir(parents=True, exist_ok=True)

    include_nonce = os.getenv("IOA_TSA_NONCE", "1") in ("1", "true", "TRUE")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        tsq_path = tmpdir / "req.tsq"
        tsr_path = out_dir / f"ts-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}.tsr"

        # Build openssl ts -query command
        cmd = [
            "openssl", "ts", "-query",
            f"-{digest_alg}",
            "-digest", digest_hex,
            "-cert",
            "-out", str(tsq_path),
        ]
        if include_nonce:
            cmd.append("-nonce")

        subprocess.run(cmd, capture_output=True, check=True)

        # POST tsq to TSA via HTTP
        with tsq_path.open("rb") as f:
            tsq_bytes = f.read()

        req = Request(tsa_url, data=tsq_bytes, headers={"Content-Type": "application/timestamp-query"})
        with urlopen(req) as resp:
            tsr_bytes = resp.read()

        with tsr_path.open("wb") as f:
            f.write(tsr_bytes)

        tsr_sha256 = _sha256_file(tsr_path)

        evidence = TimestampEvidence(
            tsr_path=str(tsr_path),
            tsa_url=tsa_url,
            digest_alg=digest_alg,
            digest_hex=digest_hex,
            nonce_included=include_nonce,
            tsr_sha256=tsr_sha256,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Optional verification (best-effort)
        if os.getenv("IOA_TSA_VERIFY", "0") in ("1", "true", "TRUE"):
            try:
                verify_timestamp(tsr_path, digest_hex, digest_alg)
            except Exception:
                # Non-fatal
                pass

        return evidence


def verify_timestamp(tsr_path: str | Path, digest_hex: str, digest_alg: str = "sha256") -> None:
    """Best-effort verification of a .tsr against the digest.

    If IOA_TSA_CA_FILE is provided, attempts full verification; otherwise checks reply structure.
    """
    _require_openssl()
    tsr_path = Path(tsr_path)

    # Basic parse
    subprocess.run(["openssl", "ts", "-reply", "-in", str(tsr_path), "-text"], capture_output=True, check=True)

    # If CA provided, attempt full verify (requires data digest file)
    ca = os.getenv("IOA_TSA_CA_FILE")
    if ca:
        # openssl ts -verify can accept -digest and -sha256 without data file in newer versions
        cmd = ["openssl", "ts", "-verify", "-in", str(tsr_path), "-digest", digest_hex]
        if digest_alg.lower() == "sha256":
            cmd.append("-sha256")
        cmd += ["-CAfile", ca]
        subprocess.run(cmd, capture_output=True, check=True)



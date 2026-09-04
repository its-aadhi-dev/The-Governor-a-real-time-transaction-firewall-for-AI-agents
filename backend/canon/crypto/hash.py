from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def hash_block(
    *,
    sequence_number: int,
    event_type: str,
    payload_json: str,
    previous_hash: str,
) -> str:
    canonical = (
        f"{sequence_number}|{event_type}|{payload_json}|{previous_hash}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
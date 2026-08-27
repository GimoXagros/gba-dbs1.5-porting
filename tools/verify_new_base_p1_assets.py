#!/usr/bin/env python3
"""Verify generated GBA P1 command containers against their WSC sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_new_base_p1_assets import (
    GBA_BASE,
    GBA_PAYLOAD_BYTES,
    WSC_PAYLOAD_BYTES,
    convert_source,
    parse_source,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("blob", type=pathlib.Path)
    parser.add_argument("manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc15.read_bytes()
    blob = args.blob.read_bytes()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    base = int(manifest["target_base"])
    errors: list[str] = []
    payload_item_count = 0
    pointer_count = 0

    if len(blob) != int(manifest["blob_bytes"]):
        errors.append("blob length does not match manifest")
    if hashlib.sha256(blob).hexdigest().upper() != manifest["blob_sha256"]:
        errors.append("blob SHA-256 does not match manifest")

    for entry in manifest["entries"]:
        runtime_id = int(entry["runtime_id"])
        target = int(entry["target"])
        size = int(entry["bytes"])
        local = target - base
        chunk = blob[local:local + size]
        if len(chunk) != size:
            errors.append(f"ID {runtime_id} is outside blob")
            continue
        if hashlib.sha256(chunk).hexdigest().upper() != entry["sha256"]:
            errors.append(f"ID {runtime_id} SHA-256 mismatch")

        parsed = parse_source(wsc, int(entry["source"]))
        expected, _ = convert_source(parsed, target)
        if expected != chunk:
            errors.append(f"ID {runtime_id} does not reproduce source conversion")

        command_count = int(entry["logical_command_count"])
        table_pointer, reserved = struct.unpack_from("<2I", chunk, 0)
        if table_pointer != GBA_BASE + target + 8 or reserved != 0:
            errors.append(f"ID {runtime_id} header mismatch")
        for index in range(command_count):
            count, payload_pointer, a_pointer, b_pointer = struct.unpack_from(
                "<4I", chunk, 8 + index * 16
            )
            source_items = parsed["payloads"][index]
            if count != len(source_items):
                errors.append(f"ID {runtime_id} command {index} count mismatch")
                continue
            for pointer, label in ((payload_pointer, "payload"), (a_pointer, "A"),
                                   (b_pointer, "B")):
                pointer_count += 1
                raw = pointer - GBA_BASE
                if not target <= raw < target + size:
                    errors.append(
                        f"ID {runtime_id} command {index} {label} pointer is external"
                    )
            payload_local = payload_pointer - GBA_BASE - target
            for item_index, source_item in enumerate(source_items):
                start = payload_local + item_index * GBA_PAYLOAD_BYTES
                generated = chunk[start:start + GBA_PAYLOAD_BYTES]
                payload_item_count += 1
                if generated[:WSC_PAYLOAD_BYTES] != source_item:
                    errors.append(
                        f"ID {runtime_id} command {index} item {item_index} changed"
                    )
                if generated[WSC_PAYLOAD_BYTES:] != bytes(4):
                    errors.append(
                        f"ID {runtime_id} command {index} item {item_index} tail is nonzero"
                    )

    result = {
        "valid": not errors,
        "container_count": len(manifest["entries"]),
        "payload_item_count": payload_item_count,
        "validated_pointer_count": pointer_count,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

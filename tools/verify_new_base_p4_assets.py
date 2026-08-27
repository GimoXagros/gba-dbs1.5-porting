#!/usr/bin/env python3
"""Verify generated relocatable GBA P4 behavior containers."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
GBA_ITEM_BYTES = 0x34


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blob", type=pathlib.Path)
    parser.add_argument("manifest", type=pathlib.Path)
    args = parser.parse_args()

    blob = args.blob.read_bytes()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    base = int(manifest["target_base"])
    end = int(manifest["target_end"])
    errors: list[str] = []

    if end - base != len(blob):
        errors.append("manifest target range does not match blob length")
    digest = hashlib.sha256(blob).hexdigest().upper()
    if digest != manifest["blob_sha256"]:
        errors.append("blob SHA-256 does not match manifest")

    covered: list[tuple[int, int]] = []
    pointer_count = 0
    null_pointer_count = 0
    for entry in manifest["entries"]:
        target = int(entry["target"])
        count = int(entry["count"])
        size = int(entry["bytes"])
        local = target - base
        if local < 0 or local + size > len(blob):
            errors.append(f"ID {entry['runtime_id']} lies outside blob")
            continue
        chunk = blob[local:local + size]
        if hashlib.sha256(chunk).hexdigest().upper() != entry["sha256"]:
            errors.append(f"ID {entry['runtime_id']} SHA-256 mismatch")
        expected_size = 8 + count * 4 + count * GBA_ITEM_BYTES
        if size != expected_size:
            errors.append(f"ID {entry['runtime_id']} size is not canonical")
        table_pointer, header_count = struct.unpack_from("<2I", chunk, 0)
        if table_pointer != GBA_BASE + target + 8:
            errors.append(f"ID {entry['runtime_id']} table pointer mismatch")
        if header_count != count:
            errors.append(f"ID {entry['runtime_id']} count mismatch")
        item_start = target + 8 + count * 4
        item_end = item_start + count * GBA_ITEM_BYTES
        expected_items = [GBA_BASE + item_start + index * GBA_ITEM_BYTES
                          for index in range(count)]
        actual_items = list(struct.unpack_from(f"<{count}I", chunk, 8))
        if actual_items != expected_items:
            errors.append(f"ID {entry['runtime_id']} item table is not contiguous")
        valid_targets = set(expected_items)
        for index in range(count):
            item_offset = 8 + count * 4 + index * GBA_ITEM_BYTES
            values = struct.unpack_from("<13I", chunk, item_offset)
            for pointer in values[6:13]:
                pointer_count += 1
                if pointer == 0:
                    null_pointer_count += 1
                elif pointer not in valid_targets:
                    errors.append(
                        f"ID {entry['runtime_id']} item {index} has external P4 pointer "
                        f"0x{pointer:08X}"
                    )
        covered.append((target, item_end))

    for (_, previous_end), (current_start, _) in zip(sorted(covered), sorted(covered)[1:]):
        if current_start < previous_end:
            errors.append("P4 containers overlap")

    result = {
        "valid": not errors,
        "blob_sha256": digest,
        "container_count": len(manifest["entries"]),
        "pointer_count": pointer_count,
        "null_pointer_count": null_pointer_count,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

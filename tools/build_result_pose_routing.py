#!/usr/bin/env python3
"""Install two complete source-backed result-pose byte-pair views.

Only64 bytes of table data and twelve literal words are written. The native
result callbacks, P0/P1 resources and complete zero row remain unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_result_pose_routing import (
    BASE, CURRENT, GBA, OLD, NEW, FIRST, LIMIT, TABLES, LITERALS,
    analyze, negative_checks, need, sha, u,
)


def build(before, gba, old, source):
    inputs = (before, gba, old, source)
    need(tuple(map(sha, inputs)) == (CURRENT, GBA, OLD, NEW), "pinned A3E predecessor and source ROM identities")
    proof = analyze(*inputs)
    negatives = negative_checks(inputs)
    after, writes, routes = bytearray(before), [], []
    for index, (name, original, _old, raw) in enumerate(TABLES):
        target = FIRST + index * 32
        payload = source[raw:raw + 32]
        need(payload.hex().upper() == proof["tables"][index]["source_bytes"], "complete proven source table")
        need(len(payload) == 32 and payload[-2:] == b"\0\0", "sixteen exact byte-pairs including final zero pair")
        after[target:target + 32] = payload
        redirects = []
        for site in LITERALS[index]:
            offset = u(before, site) - (BASE + original)
            need(offset in (0, 1), "actual low/high byte alias")
            replacement = BASE + target + offset
            after[site:site + 4] = struct.pack("<I", replacement)
            writes.append((site, 4))
            redirects.append({"raw": f"{site:06X}", "before": f"{u(before, site):08X}", "after": f"{replacement:08X}"})
        routes.append({"family": name, "old_native": f"{BASE + original:08X}",
                       "source": f"{raw:06X}", "new_native": f"{BASE + target:08X}",
                       "bytes": 32, "payload_hex": payload.hex().upper(), "redirects": redirects})
    writes.append((FIRST, LIMIT - FIRST))
    writes.sort()
    need(len(writes) == 13 and sum(n for _, n in writes) == 112, "exact twelve literal words and64 data bytes")
    inverse, declared = bytearray(after), []
    for at, n in writes:
        inverse[at:at + n] = before[at:at + n]
        declared.append({"raw": f"{at:06X}", "bytes": n,
                         "before_sha256": sha(before[at:at + n]), "after_sha256": sha(after[at:at + n])})
    need(inverse == before and len(after) == len(before), "full inverse of exact unchanged-size output")
    need(after[0x89774:0x897AC] == before[0x89774:0x897AC], "both original tables retained")
    need(after[0x629000:FIRST] == before[0x629000:FIRST], "prior action/recovery/hit allocations retained")
    need(after[0x8A7C0:0x8AC34] == before[0x8A7C0:0x8AC34], "all native result-pose callbacks retained")
    manifest = {"schema": 1, "kind": "result-pose-routing", "input_sha256": CURRENT,
                "output_sha256": sha(after), "source_sha256": {"gba": GBA, "wsc10": OLD, "wsc15": NEW},
                "expected_writes": declared, "declared_write_bytes": 112,
                "changed_bytes": sum(a != b for a, b in zip(before, after)), "full_inverse": True,
                "ownership": proof["proposal"]["allocation"], "routes": routes,
                "source_storage_pairs": 32, "playable_pairs": 30, "retail_pairs_retained": 24,
                "corrected_playable_pairs": 6, "selected_events": proof["selected_events"],
                "selected_frames": proof["selected_frames"], "negative_checks": negatives,
                "new_RAM_bytes": 0, "new_instructions": 0, "P0_P1_palette_changes": False,
                "result_label_changes": False, "runtime_claim": False, "provided_save_accessed": False}
    return bytes(after), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("before", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(key, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.before, args.gba, args.wsc10, args.wsc15]
    need(all(p.suffix.lower() in (".gba", ".wsc") for p in inputs), "explicit ROM inputs only")
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json", "explicit artifact formats")
    need(args.output.resolve() not in {p.resolve() for p in inputs}, "output cannot overwrite an input")
    result, manifest = build(*(p.read_bytes() for p in inputs))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[result-pose-routing] {sha(result)};112 declared bytes;{manifest['negative_checks']['count']} negatives")


if __name__ == "__main__":
    main()

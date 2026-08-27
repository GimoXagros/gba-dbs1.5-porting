#!/usr/bin/env python3
"""Aggregate an exact-copy interval map by older/newer ROM bank pairs."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("map", type=pathlib.Path)
    parser.add_argument("--bank-size", type=parse_int, default=0x10000)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    source = json.loads(args.map.read_text(encoding="utf-8"))
    coverage: collections.Counter[tuple[int, int]] = collections.Counter()
    newer_total: collections.Counter[int] = collections.Counter()
    for match in source["matches"]:
        old = int(match["older_start"])
        new = int(match["newer_start"])
        remaining = int(match["length"])
        while remaining:
            old_bank = old // args.bank_size
            new_bank = new // args.bank_size
            span = min(
                remaining,
                args.bank_size - old % args.bank_size,
                args.bank_size - new % args.bank_size,
            )
            coverage[(new_bank, old_bank)] += span
            newer_total[new_bank] += span
            old += span
            new += span
            remaining -= span
    banks = []
    newer_size = int(source["newer"]["size"])
    for newer_bank in range((newer_size + args.bank_size - 1) // args.bank_size):
        pairs = [
            {"older_bank": older_bank, "covered_bytes": count}
            for (candidate_newer, older_bank), count in coverage.items()
            if candidate_newer == newer_bank
        ]
        pairs.sort(key=lambda item: (-item["covered_bytes"], item["older_bank"]))
        banks.append({
            "newer_bank": newer_bank,
            "covered_bytes": newer_total[newer_bank],
            "coverage_ratio": round(newer_total[newer_bank] / args.bank_size, 6),
            "older_bank_pairs": pairs,
        })
    result = {"bank_size": args.bank_size, "banks": banks}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

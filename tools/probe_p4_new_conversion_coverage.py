#!/usr/bin/env python3
"""Measure whether official base P4 scalar conversions cover new 1.5 fighters."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
from collections import defaultdict


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC_TABLE = 0x740000
RECORD_BYTES = 0x20


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def gba_scalar_words(gba_u32: list[int]) -> list[int]:
    result = []
    for index in range(5):
        result.extend((gba_u32[index] & 0xFFFF, gba_u32[index] >> 16))
    result.append(gba_u32[5] & 0xFFFF)
    return result


def parse_wsc_items(data: bytes, offset: int) -> list[list[int]]:
    table_relative, count = struct.unpack_from("<2H", data, offset)
    relatives = struct.unpack_from(f"<{count}H", data, offset + table_relative)
    return [list(struct.unpack_from("<18H", data, offset + relative)) for relative in relatives]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    wsc15 = args.wsc15.read_bytes()
    if hashlib.sha256(wsc15).hexdigest().upper() != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")

    learned: dict[tuple[int, int, int], set[int]] = defaultdict(set)
    for pair in corpus["pairs"]:
        for item in pair["items"]:
            source = [int(value) for value in item["wsc_u16"]]
            target = gba_scalar_words([int(value) for value in item["gba_u32"]])
            command = source[0]
            for word_index in range(11):
                learned[(command, word_index, source[word_index])].add(target[word_index])

    results = []
    statuses = defaultdict(int)
    for runtime_id in (13, 14):
        record_offset = WSC_TABLE + runtime_id * RECORD_BYTES
        target = wsc_pointer(wsc15, record_offset + 4 * 6)
        items = parse_wsc_items(wsc15, target)
        item_results = []
        for item_index, item in enumerate(items):
            command = item[0]
            word_results = []
            for word_index in range(11):
                candidates = sorted(learned.get((command, word_index, item[word_index]), set()))
                if len(candidates) == 1:
                    status = "unique"
                elif candidates:
                    status = "ambiguous"
                else:
                    status = "missing"
                statuses[status] += 1
                word_results.append({
                    "word_index": word_index,
                    "source": item[word_index],
                    "status": status,
                    "candidates": candidates,
                })
            item_results.append({
                "item": item_index,
                "command": command,
                "words": word_results,
            })
        results.append({
            "runtime_id": runtime_id,
            "wsc_target": target,
            "item_count": len(items),
            "items": item_results,
        })

    result = {
        "schema": 1,
        "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest().upper(),
        "wsc15_sha256": WSC15_SHA256,
        "status_counts": dict(statuses),
        "fighters": results,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

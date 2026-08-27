#!/usr/bin/env python3
"""Build candidate GBA P4 behavior containers for the Ver. 1.5 base additions."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
from collections import defaultdict
from fractions import Fraction


GBA_BASE = 0x08000000
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC_TABLE = 0x740000
RECORD_BYTES = 0x20
WSC_ITEM_BYTES = 0x24
GBA_ITEM_BYTES = 0x34


def parse_int(value: str) -> int:
    return int(value, 0)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def scaled(value: int, numerator: int, denominator: int, mode: str) -> int:
    fraction = Fraction(signed16(value) * numerator, denominator)
    if mode == "trunc":
        result = abs(fraction.numerator) // fraction.denominator
        result *= 1 if fraction.numerator >= 0 else -1
    elif mode == "nearest_even":
        result = round(fraction)
    elif mode == "nearest_away":
        sign = 1 if fraction.numerator >= 0 else -1
        quotient, remainder = divmod(abs(fraction.numerator), fraction.denominator)
        result = sign * (quotient + int(remainder * 2 >= fraction.denominator))
    else:
        raise ValueError(mode)
    if not -0x8000 <= result <= 0x7FFF:
        raise ValueError(f"scaled value {result} is outside signed 16-bit range")
    return result & 0xFFFF


def fallback(word_index: int, value: int) -> tuple[int, str]:
    if word_index == 3:
        return scaled(value, 4, 5, "nearest_away"), "duration-4/5"
    if word_index in (4, 7, 8):
        return scaled(value, 5, 4, "trunc"), "velocity-5/4"
    if word_index == 9:
        return scaled(value, 25, 16, "nearest_even"), "acceleration-25/16-even"
    if word_index == 10:
        return scaled(value, 25, 16, "nearest_away"), "acceleration-25/16-away"
    return value, "identity"


def gba_scalar_words(gba_u32: list[int]) -> list[int]:
    result = []
    for index in range(5):
        result.extend((gba_u32[index] & 0xFFFF, gba_u32[index] >> 16))
    result.append(gba_u32[5] & 0xFFFF)
    return result


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def learn(corpus: dict[str, object]) -> dict[tuple[int, int, int], set[int]]:
    learned: dict[tuple[int, int, int], set[int]] = defaultdict(set)
    for pair in corpus["pairs"]:
        for item in pair["items"]:
            source = [int(value) for value in item["wsc_u16"]]
            target = gba_scalar_words([int(value) for value in item["gba_u32"]])
            for word_index in range(11):
                learned[(source[0], word_index, source[word_index])].add(target[word_index])
    return learned


def choose_scalar(learned: dict[tuple[int, int, int], set[int]], command: int,
                  word_index: int, value: int) -> tuple[int, str, list[int]]:
    candidates = sorted(learned.get((command, word_index, value), set()))
    if len(candidates) == 1:
        return candidates[0], "learned-unique", candidates
    predicted, rule = fallback(word_index, value)
    if candidates:
        if value in candidates:
            return value, "ambiguous-identity", candidates
        if predicted in candidates:
            return predicted, f"ambiguous-{rule}", candidates
        raise ValueError(
            f"ambiguous official values {candidates} exclude fallback 0x{predicted:04X}"
        )
    return predicted, f"missing-{rule}", candidates


def parse_container(data: bytes, offset: int) -> tuple[list[int], list[list[int]]]:
    table_relative, count = struct.unpack_from("<2H", data, offset)
    if table_relative != 4:
        raise ValueError(f"unexpected P4 table relative 0x{table_relative:X}")
    relatives = list(struct.unpack_from(f"<{count}H", data, offset + table_relative))
    items = [list(struct.unpack_from("<18H", data, offset + relative))
             for relative in relatives]
    return relatives, items


def convert_container(data: bytes, source: int, target: int,
                      learned: dict[tuple[int, int, int], set[int]]) -> tuple[bytes, dict[str, object]]:
    relatives, items = parse_container(data, source)
    count = len(items)
    table_start = target + 8
    item_start = table_start + count * 4
    target_items = [item_start + index * GBA_ITEM_BYTES for index in range(count)]
    relative_to_index = {relative: index for index, relative in enumerate(relatives)}
    output = bytearray(8 + count * 4 + count * GBA_ITEM_BYTES)
    struct.pack_into("<2I", output, 0, GBA_BASE + table_start, count)
    struct.pack_into(f"<{count}I", output, 8, *(GBA_BASE + value for value in target_items))
    decisions = defaultdict(int)
    detailed = []
    for item_index, source_words in enumerate(items):
        command = source_words[0]
        target_words = []
        item_decisions = []
        for word_index in range(11):
            value, decision, candidates = choose_scalar(
                learned, command, word_index, source_words[word_index]
            )
            target_words.append(value)
            decisions[decision] += 1
            if not decision.startswith("learned-unique"):
                item_decisions.append({
                    "word_index": word_index,
                    "source": source_words[word_index],
                    "target": value,
                    "decision": decision,
                    "official_candidates": candidates,
                })
        scalar_u32 = [target_words[index] | (target_words[index + 1] << 16)
                      for index in range(0, 10, 2)]
        scalar_u32.append(target_words[10])
        pointers = []
        for relative in source_words[11:18]:
            if relative == 0:
                pointers.append(0)
                continue
            if relative not in relative_to_index:
                raise ValueError(
                    f"P4 item {item_index} points to non-item relative 0x{relative:X}"
                )
            pointers.append(GBA_BASE + target_items[relative_to_index[relative]])
        values = scalar_u32 + pointers
        if len(values) != 13:
            raise AssertionError("P4 item field-count invariant failed")
        struct.pack_into("<13I", output, target_items[item_index] - target, *values)
        if item_decisions:
            detailed.append({"item": item_index, "command": command, "decisions": item_decisions})
    return bytes(output), {
        "source": source,
        "target": target,
        "count": count,
        "bytes": len(output),
        "decision_counts": dict(decisions),
        "non_unique_decisions": detailed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--target-base", type=parse_int, default=0x47A000)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    learned = learn(corpus)
    wsc15 = args.wsc15.read_bytes()
    digest = hashlib.sha256(wsc15).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")

    cursor = args.target_base
    blob = bytearray()
    entries = []
    for runtime_id in (12, 13, 14):
        cursor = align(cursor, 4)
        while args.target_base + len(blob) < cursor:
            blob.append(0)
        record = WSC_TABLE + runtime_id * RECORD_BYTES
        source = wsc_pointer(wsc15, record + 4 * 6)
        converted, entry = convert_container(wsc15, source, cursor, learned)
        blob.extend(converted)
        cursor += len(converted)
        entry.update({
            "runtime_id": runtime_id,
            "sha256": hashlib.sha256(converted).hexdigest().upper(),
        })
        entries.append(entry)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    manifest = {
        "schema": 1,
        "kind": "candidate-relocatable-gba-base-p4",
        "claim_scope": "structural conversion plus official-corpus scalar rules; runtime gameplay not yet proven",
        "source_wsc_sha256": digest,
        "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest().upper(),
        "target_base": args.target_base,
        "target_end": args.target_base + len(blob),
        "blob_bytes": len(blob),
        "blob_sha256": hashlib.sha256(blob).hexdigest().upper(),
        "entries": entries,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

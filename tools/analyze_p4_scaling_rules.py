#!/usr/bin/env python3
"""Score candidate fixed-point scaling rules against the official P4 corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import defaultdict
from fractions import Fraction


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def unsigned16(value: int) -> int | None:
    return value & 0xFFFF if -0x8000 <= value <= 0x7FFF else None


def round_fraction(value: Fraction, mode: str) -> int:
    numerator, denominator = value.numerator, value.denominator
    if mode == "trunc":
        return abs(numerator) // denominator * (1 if numerator >= 0 else -1)
    if mode == "floor":
        return numerator // denominator
    if mode == "nearest_even":
        return round(value)
    if mode == "nearest_away":
        sign = 1 if numerator >= 0 else -1
        absolute = abs(numerator)
        quotient, remainder = divmod(absolute, denominator)
        if remainder * 2 >= denominator:
            quotient += 1
        return sign * quotient
    raise ValueError(mode)


def transform(value: int, numerator: int, denominator: int, mode: str) -> int | None:
    return unsigned16(round_fraction(Fraction(signed16(value) * numerator, denominator), mode))


def gba_scalar_words(gba_u32: list[int]) -> list[int]:
    result = []
    for index in range(5):
        result.extend((gba_u32[index] & 0xFFFF, gba_u32[index] >> 16))
    result.append(gba_u32[5] & 0xFFFF)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    samples = []
    for pair in corpus["pairs"]:
        for item in pair["items"]:
            source = [int(value) for value in item["wsc_u16"]]
            target = gba_scalar_words([int(value) for value in item["gba_u32"]])
            samples.append((source[0], source[:11], target))

    rules = [("identity", 1, 1)]
    for name, numerator, denominator in (
        ("duration_4_5", 4, 5),
        ("velocity_5_4", 5, 4),
        ("acceleration_25_16", 25, 16),
    ):
        rules.extend((f"{name}_{mode}", numerator, denominator)
                     for mode in ("trunc", "floor", "nearest_even", "nearest_away"))

    word_scores = []
    for word_index in range(11):
        scores = []
        for name, numerator, denominator in rules:
            mode = "trunc" if name == "identity" else name.rsplit("_", 1)[-1]
            if name.endswith("nearest_even"):
                mode = "nearest_even"
            elif name.endswith("nearest_away"):
                mode = "nearest_away"
            predicted = [transform(source[word_index], numerator, denominator, mode)
                         for _, source, _ in samples]
            mismatches = sum(value != target[word_index]
                             for value, (_, _, target) in zip(predicted, samples))
            scores.append({"rule": name, "mismatches": mismatches})
        word_scores.append({
            "word_index": word_index,
            "sample_count": len(samples),
            "scores": sorted(scores, key=lambda item: (item["mismatches"], item["rule"])),
        })

    command_best = []
    grouped: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for command, source, target in samples:
        for word_index in range(11):
            grouped[(command, word_index)].append((source[word_index], target[word_index]))
    for (command, word_index), pairs in sorted(grouped.items()):
        scores = []
        for name, numerator, denominator in rules:
            mode = "trunc" if name == "identity" else name.rsplit("_", 1)[-1]
            if name.endswith("nearest_even"):
                mode = "nearest_even"
            elif name.endswith("nearest_away"):
                mode = "nearest_away"
            mismatches = sum(transform(source, numerator, denominator, mode) != target
                             for source, target in pairs)
            scores.append((mismatches, name))
        best_mismatches = min(value for value, _ in scores)
        command_best.append({
            "command": command,
            "word_index": word_index,
            "sample_count": len(pairs),
            "best_mismatches": best_mismatches,
            "best_rules": sorted(name for value, name in scores if value == best_mismatches),
        })

    result = {
        "schema": 1,
        "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest().upper(),
        "sample_count": len(samples),
        "word_scores": word_scores,
        "command_best": command_best,
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

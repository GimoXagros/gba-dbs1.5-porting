#!/usr/bin/env python3
"""Read-only structural survey for GBA and WonderSwan ROM images."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import statistics
import zlib
from collections import Counter


KNOWN_INPUTS = {
    "996de33330ac729d10d761d1901e7a335191c9503b0470569e8f294acf6618ed": {
        "id": "gba-usa-retail",
        "title": "Digimon - Battle Spirit (USA)",
        "platform": "gba",
        "expected_size": 4 * 1024 * 1024,
    },
    "c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7": {
        "id": "wsc-jpn-15-retail",
        "title": "Digimon Tamers - Battle Spirit Ver. 1.5",
        "platform": "wsc",
        "expected_size": 8 * 1024 * 1024,
    },
    "58220b9c050c3bf29b4953885c9576be103ea8e00a7bcb96cca18607e19e9735": {
        "id": "wsc-jpn-kor-10-retail",
        "title": "Digimon Tamers - Battle Spirit",
        "platform": "wsc",
        "expected_size": 4 * 1024 * 1024,
    },
}


def hashes(data: bytes) -> dict[str, str]:
    return {
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08X}",
        "md5": hashlib.md5(data).hexdigest().upper(),
        "sha1": hashlib.sha1(data).hexdigest().upper(),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
    }


def entropy(block: bytes) -> float:
    if not block:
        return 0.0
    counts = Counter(block)
    total = len(block)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def fill_runs(data: bytes, minimum: int = 256) -> list[dict[str, int | str]]:
    runs: list[dict[str, int | str]] = []
    start = 0
    while start < len(data):
        value = data[start]
        end = start + 1
        while end < len(data) and data[end] == value:
            end += 1
        if end - start >= minimum and value in (0x00, 0xFF):
            runs.append({"offset": start, "length": end - start, "value": f"{value:02X}"})
        start = end
    return sorted(runs, key=lambda item: int(item["length"]), reverse=True)


def ascii_strings(data: bytes, minimum: int = 5) -> list[dict[str, int | str]]:
    found: list[dict[str, int | str]] = []
    start = None
    for index, value in enumerate(data + b"\x00"):
        printable = 0x20 <= value <= 0x7E or value in (0x09, 0x0A, 0x0D)
        if printable and start is None:
            start = index
        elif not printable and start is not None:
            if index - start >= minimum:
                text = data[start:index].decode("ascii", errors="replace")
                found.append({"offset": start, "length": index - start, "text": text})
            start = None
    return found


def parse_gba_header(data: bytes) -> dict[str, object]:
    if len(data) < 0xC0:
        return {"valid": False, "error": "file is smaller than the GBA header"}
    complement = (-(0x19 + sum(data[0xA0:0xBD]))) & 0xFF
    return {
        "entry_arm_word_le": f"0x{int.from_bytes(data[0:4], 'little'):08X}",
        "title": data[0xA0:0xAC].rstrip(b"\0").decode("ascii", errors="replace"),
        "game_code": data[0xAC:0xB0].decode("ascii", errors="replace"),
        "maker_code": data[0xB0:0xB2].decode("ascii", errors="replace"),
        "fixed_value": f"0x{data[0xB2]:02X}",
        "software_version": data[0xBC],
        "stored_complement": f"0x{data[0xBD]:02X}",
        "computed_complement": f"0x{complement:02X}",
        "complement_valid": complement == data[0xBD],
    }


def parse_wsc_footer(data: bytes) -> dict[str, object]:
    if len(data) < 10:
        return {"valid": False, "error": "file is smaller than the WSC footer"}
    footer = data[-10:]
    stored = int.from_bytes(footer[8:10], "little")
    computed = sum(data[:-2]) & 0xFFFF
    save_types = {
        0x00: "none",
        0x01: "SRAM 8 KiB",
        0x02: "SRAM 32 KiB",
        0x03: "SRAM 128 KiB",
        0x04: "SRAM 256 KiB",
        0x05: "SRAM 512 KiB",
        0x10: "EEPROM 128 B",
        0x20: "EEPROM 2 KiB",
        0x50: "EEPROM 1 KiB",
    }
    return {
        "raw": footer.hex(" ").upper(),
        "developer_id": f"0x{footer[0]:02X}",
        "minimum_system": f"0x{footer[1]:02X}",
        "cartridge_id": f"0x{footer[2]:02X}",
        "revision": footer[3],
        "rom_size_code": f"0x{footer[4]:02X}",
        "save_type_code": f"0x{footer[5]:02X}",
        "save_type": save_types.get(footer[5], "unknown"),
        "flags": f"0x{footer[6]:02X}",
        "rtc_or_extra": f"0x{footer[7]:02X}",
        "stored_checksum": f"0x{stored:04X}",
        "computed_checksum": f"0x{computed:04X}",
        "checksum_valid": stored == computed,
    }


def parse_lz77_0x10(data: bytes, offset: int, output_limit: int = 32 * 1024 * 1024) -> dict[str, int] | None:
    if offset + 4 > len(data) or data[offset] != 0x10:
        return None
    output_size = int.from_bytes(data[offset + 1:offset + 4], "little")
    if output_size < 32 or output_size > output_limit:
        return None
    source = offset + 4
    produced = 0
    while produced < output_size:
        if source >= len(data):
            return None
        flags = data[source]
        source += 1
        for bit in range(8):
            if produced >= output_size:
                break
            if flags & (0x80 >> bit):
                if source + 2 > len(data):
                    return None
                token = (data[source] << 8) | data[source + 1]
                source += 2
                length = (token >> 12) + 3
                displacement = (token & 0x0FFF) + 1
                if displacement > produced:
                    return None
                produced += min(length, output_size - produced)
            else:
                if source >= len(data):
                    return None
                source += 1
                produced += 1
    return {"offset": offset, "compressed_size": source - offset, "output_size": output_size}


def lz77_candidates(data: bytes) -> list[dict[str, int]]:
    results: list[dict[str, int]] = []
    start = 0
    while True:
        offset = data.find(b"\x10", start)
        if offset < 0:
            break
        candidate = parse_lz77_0x10(data, offset)
        if candidate is not None:
            results.append(candidate)
        start = offset + 1
    return results


def survey(path: pathlib.Path, block_size: int) -> dict[str, object]:
    data = path.read_bytes()
    digest = hashes(data)
    known = KNOWN_INPUTS.get(digest["sha256"].lower())
    blocks = [data[pos:pos + block_size] for pos in range(0, len(data), block_size)]
    entropies = [round(entropy(block), 4) for block in blocks]
    strings = ascii_strings(data)
    report: dict[str, object] = {
        "path": str(path),
        "size": len(data),
        "hashes": digest,
        "known_input": known,
        "known_size_matches": bool(known and known["expected_size"] == len(data)),
        "byte_counts": {"00": data.count(0), "FF": data.count(0xFF)},
        "entropy": {
            "block_size": block_size,
            "mean": round(statistics.mean(entropies), 4),
            "minimum": min(entropies),
            "maximum": max(entropies),
            "blocks": entropies,
        },
        "largest_fill_runs": fill_runs(data)[:32],
        "ascii_string_count": len(strings),
        "ascii_string_samples": strings[:100],
        "gba_bios_swi_patterns": {
            "arm_lz77_wram_11": data.count(b"\x11\x00\x00\xEF"),
            "arm_lz77_vram_12": data.count(b"\x12\x00\x00\xEF"),
            "thumb_lz77_wram_11": data.count(b"\x11\xDF"),
            "thumb_lz77_vram_12": data.count(b"\x12\xDF"),
        },
    }
    platform = known["platform"] if known else path.suffix.lower().lstrip(".")
    if platform == "gba":
        report["gba_header"] = parse_gba_header(data)
        candidates = lz77_candidates(data)
        report["gba_lz77_0x10_candidates"] = {
            "count": len(candidates),
            "items": candidates,
        }
    if platform in ("wsc", "ws"):
        report["wsc_footer"] = parse_wsc_footer(data)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="+", type=pathlib.Path)
    parser.add_argument("--block-size", type=lambda value: int(value, 0), default=0x10000)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    reports = [survey(path, args.block_size) for path in args.rom]
    rendered = json.dumps({"schema": 1, "reports": reports}, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

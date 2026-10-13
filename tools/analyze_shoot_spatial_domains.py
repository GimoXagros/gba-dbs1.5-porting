#!/usr/bin/env python3
"""Freeze remaining spatial gates without a ROM mutation or reachability claim."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_X86, CS_MODE_16, Cs

IDENTITIES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "new": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
GUARDS = (
    ("new", 0x740FC1, 0x740FE9, "A0C517EF253C8B6C5F4F4D94920A299CF3E5963495EFF4D9F90B652D6BCF2CA3"),
    ("new", 0x771FA3, 0x771FCA, "B802036E069FEAF5B09B69D90D7057D13269AE50F5C4D18CC4E94694325602AB"),
    ("new", 0x7410D6, 0x7410FA, "594272C18D0AAC7CD5B1093AB7EDE097952EF19CF0C90049927ADC71202808B7"),
    ("new", 0x750B43, 0x750B71, "E2046519E6E62BAFC05D2C95A3D93245CBB71B9E276120C45BD4F806CA21EAE9"),
    ("new", 0x75375D, 0x753772, "6832261DAAD02425BBDF39C79BE350C4A7DACCA99E3265F135645AE11632526F"),
    ("new", 0x7738C6, 0x7738D8, "4F891D7D0CDB902AA028248CB2B3F69ACA88504423705191881B1978FF54370D"),
    ("new", 0x743FC0, 0x7440C7, "A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6"),
    ("new", 0x740E28, 0x740E48, "CD98887D4E0EFA8D3D9266BEA0BB726CB7952CE99AEE8D9503AA3568992C9A1B"),
    ("gba", 0xD1A70, 0xD1A98, "CCFE6763E02844210DAF2227FDA83787F084500C1B3A6CEABF897BC1C7D5413B"),
    ("new", 0x74148B, 0x7414C1, "3FF6715B2F002F027D088BFAB120482EFF994718A42EBD92E74B430505367946"),
    ("new", 0x742199, 0x74222E, "A871239207E352C4702E87BB81A9C29A834F746E1725906B1CF237C648CB0E9D"),
    ("new", 0x742FCE, 0x743000, "8B681D3FB6B610FDDC968872993C87C3EFCED92DB94EC6862A11BED77AC17C9B"),
    ("new", 0x743C54, 0x743CB4, "07B1B3802C6F2F86567D9F6395D4B0890004D6774E57F9DCABD2ABEA4C34190B"),
    ("new", 0x7495DD, 0x74979B, "696FD0479997FFF8A4A20AF0801598C6A3A0ADAB505133A23A75593C22525D28"),
    ("new", 0x743B5C, 0x743B90, "3FA1E776EC213DE75F82FB4E4B24FA36B4BABE11C3F144C30216500C824831E2"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def instructions(source: bytes, start: int, end: int):
    result = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[start:end], start))
    require(sum(i.size for i in result) == end - start, "complete bounded source decoding")
    return result


def analyze(gba: bytes, new: bytes) -> dict:
    data = {"gba": gba, "new": new}
    require(all(sha(data[k]) == v for k, v in IDENTITIES.items()), "exact source identities")
    for key, start, end, expected in GUARDS:
        require(sha(data[key][start:end]) == expected, f"source/consumer guard {start:X}")
    start_for = lambda y: (0x800 + ((y << 6) & 0xFFFF)) & 0xFFFF
    starts = {start_for(y) for y in range(65536)}
    require(starts == set(range(0, 65536, 64)), "all1024 source clear starts")
    words = {(start + i * 2) & 0xFFFF for start in starts for i in range(64)}
    require(words == set(range(0, 65536, 2)), "all source halfword addresses covered")
    witnesses = {}
    for y in (0, 32, 63, 64, 224, 480, 736, 984, 991, 992):
        start = start_for(y)
        witnesses[str(y)] = {"start": start, "last_halfword": (start + 126) & 65535,
                             "wraps": start + 128 > 65536}
    terminal = instructions(new, 0x773650, 0x773D23)
    writes = [(i.address, i.mnemonic, i.op_str) for i in terminal
              if "es:[0x3d8]," in i.op_str and i.mnemonic in ("mov", "or", "and", "xor")]
    require(writes and all(op == "or" or op == "and" and int(operand.rsplit(", ", 1)[1], 0) & 0x800
                           for _, op, operand in writes), "terminal source never clears Shoot0800")
    manager = instructions(new, 0x743FC0, 0x7440C7)
    require(not any("0x3a18" in i.op_str or "0x3a1a" in i.op_str or "0x38]" in i.op_str or "0x3a]" in i.op_str
                    for i in manager), "36C0 contains no direct dimension/cache access")
    far_calls = [i.op_str for i in manager if i.mnemonic == "lcall"]
    require(far_calls == ["0x4fff, 0x226e", "0x4fff, 0x2389"], "36C0 only graphics-resource calls")
    return {
        "source_guards": GUARDS,
        "row_clear": {"formula": "start=(0800+((BX<<6)&FFFF))&FFFF;64halfword stores with16-bit DI wrap",
                      "all16_bit_values": 65536, "distinct_starts": len(starts), "covered_halfwords": len(words),
                      "witnesses_are_not_reachability_claims": True, "witnesses": witnesses,
                      "closed_native_domain": "0<=cameraY<=62 only; upper bound/lifetime remains unproved",
                      "reason_no_all16_bit_VRAM_projection": "source736 clearsC000..C07F including current-task metadata;source984 clearsFE00palette;source991 wraps through0000"},
        "camera_producer": {"source": "4FFF:376D..377F", "expression": "BG+12=16-bit(pageY*144+inPageY)",
                            "unit": "pixels, not a masked tile row", "initial_zero_is_not_an_invariant": True},
        "scene_live_in": {"input_priority": 0xF00, "scene_priority": 0xFF0,
                          "root_case5_installs": "4090:07D6", "input_last_BX": "ES1000:01E0, BG0+12",
                          "scheduler": "4FFF:B53..B81 preserves BX across dispatch bookkeeping",
                          "remaining": "complete intervening-task/IRQ ownership and terminal reachable range"},
        "terminal_0800_write_population": writes,
        "freeze_counterevidence": {"battle_B8B": "tests03CD low7, thenFC7 and camera; not03D4bit10",
                                   "object_wrapper1899": "gates callback/integration on03CD low7",
                                   "03D4bit10": "identified tests suppress +/-4 conveyor displacement; no general freeze established"},
        "world_limit_cache": {"source_producer": "740E28..740E47", "source_owner": "0C00:3A18/3A1A",
                              "native_producer": "080D1A70..080D1A94", "native_owner": "03004520/03004522",
                              "36C0_refreshes": False, "sole_direct_stores_in_scanned_overlay": [0x740E41, 0x740E44],
                              "scanned_literal_reference_range": [0x740900, 0x79FFFF],
                              "Y_death_consumer": "743B6D/7B compare cachedheight and release; not a source1B00 clamp"},
        "lower8EF3": {"capturedY": "8DA9 captures target+28 into lower+8C",
                      "currentX": "8CDD copies targetX;8D84/8E27 follow with sourcevelocity+/-0180, then8E27 clearsXvelocity",
                      "guarded_native_domain": "signedcurrentX<1E00 and signedcapturedtargetY<=1B00",
                      "remaining": "actual P1 collision/position consumers must establish bounds and all other displacement writers;dimensions/initializer alone do not"},
        "conclusion": "No reachable bad state proved; neither spatial route gate is closed. No frozen code or ROM was changed.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("gba", type=pathlib.Path)
    p.add_argument("wsc15", type=pathlib.Path)
    p.add_argument("--output", required=True, type=pathlib.Path)
    a = p.parse_args()
    require(a.gba.suffix.lower() != ".sav" and a.wsc15.suffix.lower() != ".sav", "save files forbidden")
    report = {"schema": 1, "kind": "shoot-spatial-route-gates", **analyze(a.gba.read_bytes(), a.wsc15.read_bytes())}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-spatial-gates] source evidence and complete16-bit clear-domain proof PASS; route gates remain open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

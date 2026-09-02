#!/usr/bin/env python3
"""Independently verify the resident Digimon Shoot upper-state graph."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs  # type: ignore


INPUT_SHA256 = "C8C3AF5DABBE7CCE9F0D124DDEEF3CD6348FCDB085416DBA5E78C65DD5BFB3B4"
OUTPUT_SHA256 = "034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
OWNERSHIP_START = 0x5BC800
OWNERSHIP_END = 0x5C1000

PLACEMENTS = (
    ("upper_7792", 0x5BC800, 144, "C1622DF06BE1389392E61182386CB33EA286618B76E46D8505F6A9077F07D32F"),
    ("upper_7803", 0x5BCA00, 100, "99F8B6067C9C067504A90019D78E7FB29DB26699AFA8FFD2D052B0277FD27712"),
    ("upper_7836", 0x5BCC00, 140, "0FB0BC2C39DE033918D288DCE7186B205691405ABE3A2209809192AE81AB3962"),
    ("upper_7893", 0x5BCE00, 140, "B0854D5880C7DFA347DA590BBEE70BD07555193E40729B5E108B11820B2D9D87"),
    ("upper_78F0", 0x5BD000, 140, "19D32C0192593FEC11B74873EFDAC3E19366B7B00312EC7B2C3943DB372E1A9F"),
    ("upper_794D", 0x5BD200, 104, "11C0B0C3CA0D370A04F35930A72FC2332294F330D798908A7CBAEABAE1177080"),
    ("upper_7996", 0x5BD400, 184, "30F02D0107CCEE9587A5AD71F28FD30AED9BC783FEECD832A3B53F77D7B5EF68"),
    ("upper_7A19", 0x5BD700, 92, "EEE830A8A5C75D3321EA6E76AAF8B7AB17A0E44EB4C3D0C34B1508AD449182AA"),
    ("upper_7A41", 0x5BD900, 96, "A4281C8B2BCE94EC045C084A9AF58F170024B01ACFC5D33C9E76F0F872F7D3E7"),
    ("upper_7A79", 0x5BDB00, 88, "5917415C6855ED5EF858417EDE0126276687F70FF45154B825AC4A95E633AE01"),
    ("upper_7AB1", 0x5BDD00, 164, "8A37DE317A192E4495D9806DA8C4CA65BB815430727A9BEBF8D5C5084F1B1C87"),
    ("upper_7B1B", 0x5BE000, 72, "F9269E0967CFB4204B685D545142DDFEE66DE517D190B5A2899E6C856BCE3922"),
    ("upper_7B3A", 0x5BE200, 312, "299C4D94D5CF4D43A751AAB62436CC4EB3B82981F9385964BF8F06DF112890FE"),
    ("upper_7BFF", 0x5BE600, 176, "6DCC641FCF4653F71952E48FF5DB110ACDFB89010ECFD47ED76FEA1C39912969"),
    ("upper_7C64", 0x5BEA00, 200, "F052AF98AA98C129CC5A6D0C0B6C97C601382AB50E41965640C677B8D46A0283"),
    ("upper_7CE5", 0x5BEE00, 316, "DF0F7BE26832F78E789C3BA2C93E0864B72EE6D42D1BBBA117EB14B22B647253"),
    ("upper_7D7C_idle", 0x5BF200, 4, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
    ("upper_7D8D", 0x5BF204, 44, "3A76973A12C401FA38F1128D7D2FB54B8EB719EB2BC7B8F3242B4828B003FEEE"),
    ("upper_7DA9", 0x5BF400, 48, "2CA41960811DFFD2C571720284E9E29CE16337625FBD762219F0A524734F3C15"),
    ("upper_7DD8_idle", 0x5BF600, 4, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
    ("upper_7DD9", 0x5BF800, 256, "B8A938294717EBFAA66169BA314C1A21B3FE1629C4C2250E49472AB58C8D3CB7"),
    ("upper_7E8D", 0x5BFC00, 96, "7F332A65B7EEBF3D1B2253B2A1F548982CACB84DEDE90412DA2C68BC981EE368"),
    ("upper_7EBB", 0x5C0000, 660, "8E10BE91ED1329ED0A0755936675ED1986951060D79850CFB0E3F4F7805FFF7E"),
    ("upper_8069", 0x5C0600, 104, "BB9F0C4CFAA7BBC1728DD07C571A3198257AFBC6F6B11E8167464EA2E6ABCF94"),
    ("upper_809C", 0x5C0800, 164, "1B0D837929456D09D826F85E240E41975118DC1611962EB57B3C55578798B6DE"),
    ("controller_9908_boundary", 0x5C0A00, 4, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
    ("upper_p2_variant_3", 0x5C0B00, 40, "829EB7173630790AA6266A53A0C4AB43BF98D9ED1B5964E8037E6311F693D793"),
    ("upper_intro_bg_palette", 0x5C0C00, 224, "7176D11049581343B4A2BB1A3A451592851D9E7F903207041268B1E8EFA1C1D2"),
    ("upper_target_table", 0x5C0D00, 64, "C7CF22F2C66285C53CE7B00F78284C82D8E6D29C5238002D5D71522C6A9836ED"),
)

EXPECTED_CALLS = {
    "upper_7792": (0x08012348, 0x08012874, 0x080D15C0),
    "upper_7803": (0x08012A84, 0x08012874),
    "upper_7836": (0x08012A84, 0x080132EC, 0x080D15C0),
    "upper_7893": (0x08012A84, 0x080132EC, 0x080D15C0),
    "upper_78F0": (0x08012A84, 0x080132EC, 0x080D15C0),
    "upper_794D": (0x08012A84, 0x080D15C0),
    "upper_7996": (0x08012A84, 0x08012348, 0x0801233C, 0x080D15C0),
    "upper_7A19": (0x08012A84,),
    "upper_7A41": (0x08012A84,),
    "upper_7A79": (0x08012600,),
    "upper_7AB1": (0x08012874,),
    "upper_7B1B": (0x08012A84,),
    "upper_7B3A": (),
    "upper_7BFF": (0x08012A84,),
    "upper_7C64": (0x08012A84, 0x080D15C0),
    "upper_7CE5": (0x08012A84, 0x080132EC),
    "upper_7D7C_idle": (),
    "upper_7D8D": (),
    "upper_7DA9": (),
    "upper_7DD8_idle": (),
    "upper_7DD9": (0x08012874, 0x08012600, 0x085BFC00, 0x08012874, 0x085C0000),
    "upper_7E8D": (0x08012A84, 0x08012874),
    "upper_7EBB": (0x08012874, 0x08012A84, 0x085C0A00, 0x08012600),
    "upper_8069": (0x08012A84, 0x08012600),
    "upper_809C": (0x085C0A00, 0x08012600),
    "controller_9908_boundary": (),
}

EXPECTED_POINTER_REFS = (
    (0x5BC88C, 0x085BCA00), (0x5BCA60, 0x085BCC00),
    (0x5BCC88, 0x085BCE00), (0x5BCE88, 0x085BD000),
    (0x5BD088, 0x085BD200), (0x5BD264, 0x085BD400),
    (0x5BD4B4, 0x085BD700), (0x5BD758, 0x085BD900),
    (0x5BD95C, 0x085BDB00), (0x5BDB54, 0x085BF800),
    (0x5BDD98, 0x085C0C00), (0x5BDDA0, 0x085BE000),
    (0x5BE044, 0x085BE200), (0x5BE334, 0x085BE600),
    (0x5BE6AC, 0x085BEA00), (0x5BEAC4, 0x085BEE00),
    (0x5BEF30, 0x085C0B00), (0x5BEF38, 0x085BF200),
    (0x5BF22C, 0x085BF400), (0x5BF42C, 0x085BF600),
    (0x5BF8F4, 0x085C0D00), (0x5BF8F8, 0x085BFC00),
    (0x5BF8FC, 0x085C0000), (0x5BFC5C, 0x085C0000),
    (0x5C0290, 0x085C0600), (0x5C0664, 0x085C0800),
    (0x5C08A0, 0x085BF800),
)

WSC_RANGES = (
    ("upper_main", 0x748092, 0x74867D, "46FF062CBF19229B16A48C1FAEA64B09042C2CE79889CC851496B65EE991A098"),
    ("upper_second", 0x74868D, 0x7486BE, "25A0BE0C607054F3C7051444B5418EE66B85413B8828AFD29F568F1E95BD2491"),
    ("upper_shared", 0x7486D8, 0x7489CB, "71CAF3C450D363D6F0D05A9B65A3C8E5FA5232739F75E2EED668C621CD6820FF"),
    ("auxiliary_idle_88F6", 0x7491F6, 0x7491F7, "383E5D7D58CAA41CE723CF16AF471B38F6EE9065C032D07FA6BEF1678CB72F1D"),
    ("intro_palette", 0x7491F8, 0x7492D8, "8E6C0695DEE2B90AF2A74DF35FD1FCCB9EF05E4C5E3954D519308E3640BC8390"),
    ("target_table", 0x7489CC, 0x748A0C, "C7CF22F2C66285C53CE7B00F78284C82D8E6D29C5238002D5D71522C6A9836ED"),
    ("p2_variant_3", 0x3D4B92, 0x3D4BB8, "CDB85BE76FA8020711EE525F1EBC4EDCA0372E484F0E10D1A66E8EEB7AE84CD4"),
)

SOURCE_CALLBACKS = (
    0x7792, 0x7803, 0x7836, 0x7893, 0x78F0, 0x794D, 0x7996,
    0x7A19, 0x7A41, 0x7A79, 0x7AB1, 0x7B1B, 0x7B3A, 0x7BFF,
    0x7C64, 0x7CE5, 0x7D7C, 0x7D8D, 0x7DA9, 0x7DD8, 0x7DD9,
    0x7E8D, 0x7EBB, 0x8069, 0x809C, 0x88F6,
)

TARGET_ROWS = (
    (0x0E00, 0x0D80, 0x0E00, 0x1880),
    (0x0880, 0x11C0, 0x0F40, 0x1880),
    (0x0600, 0x1700, 0x1600, 0x1700),
    (0x0CC0, 0x1880, 0x1380, 0x11C0),
    (0x0E00, 0x1880, 0x0E00, 0x0D80),
    (0x0F40, 0x1880, 0x0880, 0x11C0),
    (0x1600, 0x1700, 0x0600, 0x1700),
    (0x1380, 0x11C0, 0x0CC0, 0x1880),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def arm_branch_target(address: int, word: int) -> int:
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def expand_channel(value: int) -> int:
    return (value << 1) | int(value != 0)


def convert_color(value: int) -> int:
    if value & 0xF000:
        raise SystemExit(f"source color is outside BGR444: 0x{value:04X}")
    blue = expand_channel(value & 0xF)
    green = expand_channel((value >> 4) & 0xF)
    red = expand_channel((value >> 8) & 0xF)
    return red | (green << 5) | (blue << 10)


def convert_p2(source: bytes) -> bytes:
    if len(source) != 38:
        raise SystemExit("source P2 record size changed")
    header = source[:6]
    colors = struct.unpack_from("<16H", source, 6)
    result = bytearray(header)
    result.extend(struct.pack("<16H", *(convert_color(value) for value in colors)))
    result.extend(source[:2])
    return bytes(result)


def convert_palette_table(source: bytes) -> bytes:
    words = struct.unpack("<112H", source)
    return struct.pack(
        "<112H",
        *(0 if index % 16 == 0 else convert_color(value)
          for index, value in enumerate(words)),
    )


def aligned_window_refs(data: bytes) -> tuple[tuple[int, int], ...]:
    result = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + OWNERSHIP_START <= value < GBA_BASE + OWNERSHIP_END:
            result.append((offset, value))
    return tuple(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    gba = args.gba.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(before, INPUT_SHA256, "v45 input")
    require_hash(after, OUTPUT_SHA256, "v46 output")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    if before[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (OWNERSHIP_END - OWNERSHIP_START):
        raise SystemExit("v45 upper-state ownership window was not blank")
    if aligned_window_refs(before):
        raise SystemExit("v45 unexpectedly contained pointers into the ownership window")

    declared_changed = set()
    placement_report = []
    placement_by_label = {}
    for label, offset, size, digest in PLACEMENTS:
        blob = after[offset:offset + size]
        require_hash(blob, digest, label)
        if before[offset:offset + size] != bytes([0xFF]) * size:
            raise SystemExit(f"{label} input placement was not blank")
        declared_changed.update(
            offset + index
            for index, (old, new) in enumerate(zip(before[offset:offset + size], blob))
            if old != new
        )
        placement_by_label[label] = (offset, blob)
        placement_report.append({"label": label, "offset": offset, "bytes": size, "sha256": digest})
    actual_changed = {index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]}
    if actual_changed != declared_changed or len(actual_changed) != 4144:
        raise SystemExit(f"v46 changed-byte containment/count failed: {len(actual_changed)}")

    for label, start, end, digest in WSC_RANGES:
        require_hash(wsc15[start:end], digest, f"WSC {label}")
    p2_source = wsc15[0x3D4B92:0x3D4BB8]
    p2_native = convert_p2(p2_source)
    require_hash(p2_native, PLACEMENTS[-3][3], "independently converted P2 variant")
    if after[0x5C0B00:0x5C0B28] != p2_native:
        raise SystemExit("installed P2 variant differs from independent conversion")
    palette_native = convert_palette_table(wsc15[0x7491F8:0x7492D8])
    require_hash(palette_native, PLACEMENTS[-2][3], "independently converted intro palette")
    if after[0x5C0C00:0x5C0CE0] != palette_native:
        raise SystemExit("installed intro palette differs from independent conversion")
    target_bytes = struct.pack("<32H", *(value for row in TARGET_ROWS for value in row))
    if after[0x5C0D00:0x5C0D40] != target_bytes or target_bytes != wsc15[0x7489CC:0x748A0C]:
        raise SystemExit("upper-state target table changed")

    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    call_report = {}
    for label, expected in EXPECTED_CALLS.items():
        offset, blob = placement_by_label[label]
        calls = []
        for instruction in engine.disasm(blob, GBA_BASE + offset):
            if instruction.mnemonic == "bl":
                word = struct.unpack_from("<I", instruction.bytes)[0]
                calls.append(arm_branch_target(instruction.address, word))
        if tuple(calls) != expected:
            raise SystemExit(f"{label} native call population changed: {calls}")
        call_report[label] = calls

    if after[0x5BF200:0x5BF204] != bytes.fromhex("1E FF 2F E1"):
        raise SystemExit("translated 7D7C idle callback is not BX LR")
    if after[0x5BF600:0x5BF604] != bytes.fromhex("1E FF 2F E1"):
        raise SystemExit("translated 7DD8 idle callback is not BX LR")
    if after[0x5C0A00:0x5C0A04] != bytes.fromhex("1E FF 2F E1"):
        raise SystemExit("controller boundary is not BX LR")

    refs = aligned_window_refs(after)
    if refs != EXPECTED_POINTER_REFS:
        raise SystemExit(f"upper-state aligned pointer population changed: {refs}")
    if any(offset < OWNERSHIP_START or offset >= OWNERSHIP_END for offset, _value in refs):
        raise SystemExit("upper-state graph unexpectedly gained an external caller")
    if any(value in (0x085BC800, 0x085BDD00, 0x085BF204) for _offset, value in refs):
        raise SystemExit("one of the three external entry candidates gained a caller")

    # Guard the source's central dead-band paths and the table's address (not
    # its first palette value). These checks are independent of builder labels.
    for offset, expected_word in (
        (0x5BE288, 0xEA000001),  # X dead-band jumps over the positive-velocity write
        (0x5BE2D4, 0xEA000001),  # Y dead-band jumps over the positive-velocity write
        (0x5BE2F0, 0xE1C4BAB4),  # source +8E completion count retained at native +A4
        (0x5BEEC0, 0xE28F905C),  # ADR r9 -> native pointer table at 085BEF24
        (0x5BEEC4, 0xE7998100),  # table index selects a pointer, not palette bytes
    ):
        if struct.unpack_from("<I", after, offset)[0] != expected_word:
            raise SystemExit(f"upper-state semantic safeguard changed at 0x{offset:X}")
    if struct.unpack_from("<4I", after, 0x5BEF24) != (
        0x08587100, 0x08587128, 0x08587150, 0x085C0B00
    ):
        raise SystemExit("four-entry palette pointer table changed")

    sound_words = {
        0xE3A0804A: (0x5BC868,),
        0xE3A0805B: (0x5BCC5C, 0x5BCE5C, 0x5BD05C),
        0xE3A0805C: (0x5BD244, 0x5BD494, 0x5BEAA4),
    }
    for word, expected_offsets in sound_words.items():
        actual_offsets = tuple(
            offset for offset in range(OWNERSHIP_START, OWNERSHIP_END, 4)
            if struct.unpack_from("<I", after, offset)[0] == word
        )
        if actual_offsets != expected_offsets:
            raise SystemExit(f"native sound-ID signature changed for 0x{word:08X}")

    for offset, size, digest, label in (
        (0x5BC200, 436, "49D24F0D03A38A935E6FC9FA1AA0D43AFEB4EEAA9BFE7CC50FAD5A076422DC9E", "auxiliary constructor"),
        (0x587100, 40, "3EE04969CAF106CBDB949A6386BAF4E076F8AAF9A7EFC1242E0A0BDA6A37A937", "P2 variant 0"),
        (0x587128, 40, "23C9E48F2C3AA34B035BF4C6E4C27D5B0920B0AC746073D92F211D15A856AA92", "P2 variant 1"),
        (0x587150, 40, "499027430A0E296FD330B43752C9A108E8C9B42D4B9A840F9D43DB802C8B1533", "P2 variant 2"),
    ):
        require_hash(after[offset:offset + size], digest, label)
        if before[offset:offset + size] != after[offset:offset + size]:
            raise SystemExit(f"v46 changed the preinstalled {label}")

    report = {
        "schema": 1,
        "kind": "shoot-upper-state-independent-verification",
        "input_sha256": INPUT_SHA256,
        "output_sha256": OUTPUT_SHA256,
        "source_graph": {
            "callback_count": len(SOURCE_CALLBACKS),
            "source_callbacks": SOURCE_CALLBACKS,
            "reachable_code_bytes": 2320,
            "controller_9908_source_calls": [0x8057, 0x80AF],
        },
        "placements": placement_report,
        "native_calls": call_report,
        "aligned_pointer_references": refs,
        "diff": {"changed_bytes": len(actual_changed), "contained_in_declared_placements": True},
        "sound_requests": {
            "WSC15_A7_to_GBA_4A": 1,
            "WSC15_CE_to_GBA_5B": 3,
            "WSC15_D2_to_GBA_5C": 3,
        },
        "proved": [
            "26-entry WSC upper-state callback population and 2320 source bytes",
            "independently converted fourth P2 record and seven-row BG palette table",
            "exact eight-row movement target table",
            "platform-native presentation, trigonometry, RNG, P2-loader, and sound calls",
            "central X/Y dead-band branches preserve velocity and store the source completion count",
            "palette selection addresses the four-pointer table before indexing",
            "two internal calls terminate at an unimplemented resident 9908 boundary",
            "no pointer outside the ownership window reaches the resident graph",
            "all writes remain inside the 29 declared placements",
        ],
        "claim_scope": (
            "resident unconnected upper-state graph only; initializer/menu reachability, "
            "controller rules, runtime, audible behavior, emulator, and supplied-save QA excluded"
        ),
        "runtime_or_save_used": False,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

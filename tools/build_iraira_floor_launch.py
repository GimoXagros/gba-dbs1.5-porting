#!/usr/bin/env python3
"""Bind the source Iraira floor trigger to proved native motion and eight scores.

The two source-only character-13 aerial branches remain outside this layer.
No RAM is allocated: the existing fighter, timer and sound request owners are
used through their actual native consumers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

INPUT = "96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
TRIGGER, INIT, WAIT = 0x627A00, 0x627B00, 0x627C00
EFFECT8, EFFECT0 = 0x627D00, 0x627D80
RESERVATIONS = ((TRIGGER, 0x628000), (0x686800, 0x687000))
TABLE, OLD_TABLE, VOICES = 0x686800, 0x683200, 0x683520
LITERALS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
SOURCE_NOTES = (0x29, 0x2B, 0x30, 0x32, 0x34, 0x35, 0x37, 0x39)
SOURCE_HASHES = (
    "B80A6E7ED3A907765ADEAC6842EE74B26453ECC6CA04EED53644060EE234601C",
    "A6215041F58B2BCAE51F0C43FB1783DE00D2D8DC89BFB9334988B6EEE7803B9A",
    "6E9732C232D031ACFBBE6A81EAC0406DE011F6181B9394752FE33DED3571A6FC",
    "7F7CFDC43AEC507A2ED962B6F86A7DADC3112A6E76D83F34FF91BA15F0E531C9",
    "CA9A7BE27ABA5C5C7BB3049DCEACD59C9F6307D5618DBA11170A2F56073A0CAE",
    "1CAC9B4F330C12977876D38824EE7A3ED129A8DE08A17A99DE060F9A2ECA18C4",
    "A6DAB1A367D9F87DD26CA77F18FD83D1ED9B970E1B353229DC93517023E836F3",
    "6270FC5262B050A4F4AE922090E6EDFA8BC65E2E126B2338F377C2B7CC0DDB7A",
)
NATIVE_WINDOWS = (
    (0x354910, 0x35491C), (0x3549E0, 0x354A3C), (0x354C98, 0x354D7C),
    (0x354DD4, 0x354DDC), (0x357670, 0x357978), (0xD15C0, 0xD15F0),
    (0x352E1C, 0x352E48), (0xD17F8, 0xD1898), (0x373D34, 0x373D4C),
    (0x12874, 0x129A0), (0x12BBC, 0x12C00), (0x12A84, 0x12B10),
    (0x35972C, 0x3597D0), (0x3597D4, 0x359800),
    (0x35955C, 0x359568), (0x35956C, 0x35958C),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, target, link=False):
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM branch range")
    return (0xEB000000 if link else 0xEA000000) | ((delta // 4) & 0xFFFFFF)


def incoming(data):
    hits = []
    for at in range(len(data) - 3):
        value = word(data, at)
        for lo, hi in RESERVATIONS:
            if BASE + lo <= value < BASE + hi:
                hits.append((at, value, "unaligned encoded pointer"))
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        targets = []
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            targets.append((at + 8 + delta * 4, "ARM B/BL encoding"))
        if value & 0x0E1F0000 == 0x041F0000:
            delta = value & 0xFFF
            if not value & 0x00800000:
                delta = -delta
            targets.append((at + 8 + delta, "ARM PC-relative load/store encoding"))
        for target, kind in targets:
            if any(lo <= target < hi for lo, hi in RESERVATIONS):
                hits.append((at, target, kind))
    return hits


def assemble(source, at, literal_bytes):
    blob = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + at)[0])
    size = len(blob) - literal_bytes
    instructions = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(blob[:size], BASE + at))
    need(size % 4 == 0 and len(instructions) * 4 == size, "bounded ARM decode")
    # Every emitted mnemonic is an ARM7TDMI form; the independent verifier
    # additionally binds the complete instruction operands and literal values.
    allowed = {"ldrh", "ldr", "ldrb", "tst", "bne", "beq", "blo", "bls", "b", "bl", "blne",
               "orr", "strh", "strb", "str", "and", "add", "mov", "bic",
               "push", "pop", "stmdb", "ldm", "bx", "cmp"}
    need(all(i.mnemonic in allowed for i in instructions), "ARMv4T instruction allowlist")
    return blob, dict(raw=at, bytes=len(blob), code_bytes=size, instructions=len(instructions),
                      sha256=sha(blob), listing=[f"{i.address:08X}: {i.mnemonic} {i.op_str}"
                                                for i in instructions])


def trigger():
    return assemble(f"""
        ldrh r8, [r4, #6]
        tst r8, #1
        bne 0x08354DD4
        ldrh r8, [r4, #8]
        tst r8, #0x40
        bne 0x08354CB8
        orr r8, r8, #0x8000
        strh r8, [r4, #8]
        ldr r1, timer
        ldrh r1, [r1]
        and r1, r1, #7
        add r8, r1, #0x64
        ldrh r1, [r4, #6]
        tst r1, #0x1000
        beq release_test
        mov r9, #1
        mov r10, #1
        bl 0x080D15C0
    release_test:
        ldrh r8, [r4, #8]
        tst r8, #0x400
        beq set_callback
        stmdb sp!, {{r5}}
        stmdb sp!, {{r11}}
        bl 0x08012BBC
        add sp, sp, #8
        ldrh r8, [r4, #8]
        bic r8, r8, #0x400
        strh r8, [r4, #8]
    set_callback:
        ldr r8, callback
        b 0x08354D20
    timer: .word 0x03004500
    callback: .word 0x{BASE + INIT:08X}
    """, TRIGGER, 8)


def initializer():
    return assemble(f"""
        stmdb sp!, {{lr}}
        mov r9, #3
        strb r9, [r4, #0x6E]
        mov r9, #0
        strh r9, [r4, #0xA6]
        strh r9, [r4, #0x42]
        strh r9, [r4, #0x44]
        strh r9, [r4, #0x46]
        strh r9, [r4, #0x48]
        ldrh r8, [r4, #6]
        orr r8, r8, #1
        strh r8, [r4, #6]
        stmdb sp!, {{r4}}
        stmdb sp!, {{r11}}
        ldrh r8, [r4, #0x34]
        stmdb sp!, {{r8}}
        ldrh r8, [r4, #0x36]
        stmdb sp!, {{r8}}
        ldr r8, effect
        stmdb sp!, {{r8}}
        bl 0x0835972C
        add sp, sp, #20
        ldr r8, wait_callback
        str r8, [r4]
        bl 0x{BASE + WAIT:08X}
        ldmia sp!, {{lr}}
        bx lr
    effect: .word 0x00008005
    wait_callback: .word 0x{BASE + WAIT:08X}
    """, INIT, 8)


def waiter():
    return assemble("""
        stmdb sp!, {lr}
        ldrh r8, [r5, #0xA]
        tst r8, #0x2000
        beq 0x0835778C
        ldrh r8, [r4, #4]
        tst r8, #1
        bne 0x0835774C
        ldrb r8, [r4, #0x70]
        cmp r8, #24
        blo 0x0835774C
        ldr r9, velocity
        strh r9, [r4, #0xA0]
        mov r9, #20
        strh r9, [r4, #0xA2]
        mov r9, #15
        strh r9, [r4, #0xA4]
        b 0x0835774C
    velocity: .word 0xFFFFFDD4
    """, WAIT, 4)


def effect_flag(target, at):
    need(target in ("r0", "r8"), "two proven effect value registers")
    saved = "r0, r1, lr" if target == "r8" else "r1, r8, lr"
    return assemble(f"""
        push {{{saved}}}
        mov r1, {target}
        ldr r0, stage
        ldrb r0, [r0, #0xE]
        cmp r0, #11
        blne 0x080D1C78
        cmp r0, #9
        blo add_flag
        cmp r0, #10
        bls done
    add_flag:
        orr r1, r1, #0x2000
    done:
        mov {target}, r1
        pop {{{saved}}}
        bx lr
    stage: .word 0x03002310
    """, at, 4)


def score(payload):
    need(payload[:4] == bytes((0, 0, 15, 0)), "source initial score state")
    wave, volume, ticks = None, 15, 0
    track = bytearray((0xBC, 0, 0xBB, 75, 0xBF, 127))
    notes = []
    for cursor in range(4, len(payload), 2):
        op, arg = payload[cursor:cursor + 2]
        if (op, arg) == (255, 255):
            need(set(payload[cursor:]) == {255}, "terminal source padding")
            break
        if op == 0xA2:
            need(arg == 4, "source waveform 4")
            wave = 2
        elif op == 0xC1:
            need(arg == 0, "zero source envelope period")
        elif op == 0xA0:
            need(arg in (6, 2), "source decreasing volumes")
            volume = arg
        else:
            need(op < 0xA0 and arg in (1, 9), "bounded source notes and rests")
            if op & 15 < 12:
                need(wave == 2 and arg == 9, "native note contract")
                key = 36 + 12 * (op >> 4) + (op & 15)
                amplitude = (volume * 127 + 7) // 15
                track.extend((0xBD, wave, 0xBE, amplitude, 0xD8, key, 127))
                notes.append(dict(tick=ticks, duration=9, key=key, volume=amplitude))
            else:
                need((op, arg) == (0x1F, 1), "exact source one-tick rest")
            track.extend([0x81] * arg)
            ticks += arg
    else:
        raise ValueError("source score termination")
    need(ticks == 29 and len(notes) == 3, "complete finite phrase")
    track.append(0xB1)
    return bytes(track), notes


def proof(before, gba, old, source):
    guards = ((0x742EBF, 0x742FC9, "E0274770ABE0046C029789753EA0EE8E938CF0FA97CDA4E3F4FFD96AF80B0EC4"),
              (0x76895B, 0x768B4D, "3C28DB2780AA08B3FBEF1BC6B1AFBD802CD36FE22B8F0BB13AC86AA45C9ECC6D"),
              (0x768731, 0x76895B, "E6C22F200C9D339C0B6F577CC90F57B9C14AC2920AF20FD416F3E4B247167313"))
    for lo, hi, digest in guards:
        need(sha(source[lo:hi]) == digest, "source trigger / callback identity")
    for lo, hi in NATIVE_WINDOWS:
        need(before[lo:hi] == gba[lo:hi], f"native consumer preserved {lo:X}")
    # The existing flag helpers read progression directly, whereas the current
    # stage setup uses the proven temporary logical selector. Guard the old
    # helpers before replacing their two caller BLs with exact ABI adapters.
    need(word(before, 0x3597D0) == 0xEB08AC5A, "existing effect vertical adapter")
    need(before[0x584940:0x58496C] == bytes.fromhex(
        "04002de51c009fe50e00d0e5090050e30100003a0a0050e30000009a028a88e3"
        "04009de41eff2fe110230003"), "existing effect adapter ABI")
    need(word(before, 0x359568) == 0xEB08ACE4, "existing r0 effect adapter")
    need(before[0x584900:0x58492C] == bytes.fromhex(
        "04202de51c209fe50e20d2e5090052e30100003a0a0052e30000009a020a80e3"
        "04209de41eff2fe110230003"), "existing r0 effect adapter ABI")
    for lo, hi, digest in (
            (0x781BEF, 0x781C0F, "BBE9945778B6792D6BCF1FDB14AA09945C2DE04D6C46297D83E6CE1628E3DECD"),
            (0x786C5C, 0x786C7C, "EB539F996D0887ACEBFDCA19FE0C8E8B0451FDA66AE3941D6433FA1B04826F6A")):
        need(sha(source[lo:hi]) == digest, "source stage9/10 effect exception")
    policy = (0xE59F802C, 0xE5D8000A, 0xE350000B, 0x03A0000A,
              0x012FFF1E, 0xE350000D, 0x03A00008, 0x012FFF1E,
              0xE350000E, 0x03A00009, 0x012FFF1E, 0xE5D8000E,
              0xE12FFF1E, 0x03002310)
    need(word(before, 0xD1C78) == branch(0xD1C78, 0x582C40) and
         before[0x582C40:0x582C78] == struct.pack("<14I", *policy),
         "existing logical-stage getter exact r0/r8-only ABI")
    for a, b, count in ((0x768731, 0x3ADBF7, 0x23), (0x742DCA, 0x392AE2, 0x18),
                        (0x74348F, 0x393064, 0x1D), (0x76877C, 0x3ADC42, 0x1D)):
        need(source[a:a + count] == old[b:b + count], "commercial jump lineage")
    need(source[0x76895B:0x76897E] == source[0x768731:0x768754], "Iraira jump initial state lineage")
    rows = [struct.unpack_from("<4H", source, 0x742F89 + n * 8) for n in range(8)]
    need(rows == [(0xBE + n, 1, 0, 0) for n in range(8)], "all eight source request rows")
    need(source[0x742EFD:0x742F05] == bytes.fromhex("2e8b57022e8b5f02"),
         "source second and third request arguments both read row+2")
    # Only these five actual table references are replaced; all old 100 entries
    # and the three current analogue voices remain byte-for-byte intact.
    pointer = struct.pack("<I", BASE + OLD_TABLE)
    hits = tuple(at for at in range(len(before) - 3) if before[at:at + 4] == pointer)
    need(hits == LITERALS, "complete song table pointer population")
    for n, raw in enumerate((0x37EA54, 0x37E9D0, 0x37EB08)):
        need(before[VOICES + n * 12:VOICES + (n + 1) * 12] ==
             gba[raw:raw + 8] + bytes((0, 0, 15, 0)), "existing native analogue voice")
    return dict(source_windows=[dict(raw=a, end=b, sha256=c) for a, b, c in guards],
                native_windows=[dict(raw=a, end=b, sha256=sha(gba[a:b])) for a, b in NATIVE_WINDOWS],
                request_rows=rows, source_arguments=[1, 1])


def build(before, gba, old, source):
    need(len(before) == 0x800000 and sha(before) == INPUT, "fixed Train predecessor")
    need(tuple(map(sha, (gba, old, source))) == ORIGINALS, "three original ROM identities")
    evidence = proof(before, gba, old, source)
    for lo, hi in RESERVATIONS:
        need(before[lo:hi] == b"\xFF" * (hi - lo), "reserved footprint blank")
    need(not incoming(before), "possible prior reference into reservation")
    payloads, code = [], []
    for at, make in ((TRIGGER, trigger), (INIT, initializer), (WAIT, waiter),
                     (EFFECT8, lambda: effect_flag("r8", EFFECT8)),
                     (EFFECT0, lambda: effect_flag("r0", EFFECT0))):
        blob, item = make()
        need(len(blob) < 0x100, "separate bounded code slots")
        payloads.append((at, blob, f"code_{at:X}"))
        code.append(item)
    table = bytearray(before[OLD_TABLE:OLD_TABLE + 800] + bytes(64))
    cursor = TABLE + len(table)
    songs = []
    for n, packed_note in enumerate(SOURCE_NOTES):
        raw, source_id, native_id = 0x3F8746 + n * 26, 0xBE + n, 0x64 + n
        payload = source[raw:raw + 26]
        need(sha(payload) == SOURCE_HASHES[n], "exact source score")
        need(0x3F0000 + struct.unpack_from("<H", source, 0x3F0000 + source_id * 6 + 4)[0] == raw,
             "source sound table pointer")
        need(payload[8] == packed_note, "independent note population")
        track, schedule = score(payload)
        blob = bytes((1, 0, 40, 128)) + struct.pack("<II", BASE + VOICES, BASE + cursor + 12) + track
        struct.pack_into("<IHH", table, native_id * 8, BASE + cursor, 4, 4)
        payloads.append((cursor, blob, f"song_{native_id:02X}"))
        songs.append(dict(source_id=source_id, native_id=native_id, source_raw=raw,
                          source_sha256=sha(payload), raw=cursor, bytes=len(blob),
                          sha256=sha(blob), ticks=29, notes=schedule))
        cursor = (cursor + len(blob) + 3) & ~3
    need(cursor <= 0x687000, "audio reservation extent")
    payloads.append((TABLE, bytes(table), "song_table_00_6B"))
    patches = [(at, b"\xFF" * len(blob), blob, label) for at, blob, label in payloads]
    patches.append((0x354A34, struct.pack("<I", 0x08354DD4), struct.pack("<I", BASE + TRIGGER), "fighter floor class14"))
    patches.extend((at, struct.pack("<I", branch(at, oldtarget, True)),
                    struct.pack("<I", branch(at, newtarget, True)), "logical-stage effect flag")
                   for at, oldtarget, newtarget in ((0x3597D0, 0x584940, EFFECT8),
                                                   (0x359568, 0x584900, EFFECT0)))
    patches.extend((at, struct.pack("<I", BASE + OLD_TABLE), struct.pack("<I", BASE + TABLE), "native song table")
                   for at in LITERALS)
    after = bytearray(before)
    occupied = set()
    for at, expected, replacement, label in patches:
        need(before[at:at + len(expected)] == expected, "Expected Write " + label)
        indices = set(range(at, at + len(expected)))
        need(not occupied & indices, "disjoint patch spans")
        occupied.update(indices)
        after[at:at + len(expected)] = replacement
    inverse = bytearray(after)
    for at, expected, replacement, label in patches:
        inverse[at:at + len(expected)] = expected
    need(inverse == before, "full-ROM inverse")
    return bytes(after), dict(schema=1, kind="iraira-floor-launch", input_sha256=INPUT,
        output_sha256=sha(after), changed_bytes=sum(a != b for a, b in zip(before, after, strict=True)),
        expected_writes=[dict(raw=at, bytes=len(oldbytes), before_sha256=sha(oldbytes),
                             after_sha256=sha(newbytes), label=label)
                         for at, oldbytes, newbytes, label in patches],
        reservations=RESERVATIONS, allocation_inbounds=[], code=code, songs=songs,
        preserved_song_entries=100, reused_voices=BASE + VOICES, evidence=evidence,
        ABI=dict(trigger="r4 fighter, r5 presentation; parent 354910 stack {r1,r3,r5,lr}; return via354D20/354DD4/354CB8",
                 initializer="native callback r4/r5; own saved LR; same native effect and first wait invocation",
                 waiter="own saved LR; rejoin35774C or35778C, both return through357974",
                 effects="r8/r0 respectively receives the stage flag; all other registers and SP/LR restored; caller overwrites CPSR flags before use"),
        new_RAM_owner=False, provided_save_accessed=False,
        limitations=["Common native jump/fall motion; source character13 aerial branches 8522:0577/02BD are not implemented here",
                     "Effect stage uses existing temporary character route with actual Shoot11 priority; campaign progression is not modified",
                     "Eight-phase selector uses the proved native 60Hz timer owner; no separate 75Hz source timer is synthesized",
                     "Native score notes, durations, volume and right pan retained with commercial waveform analogue",
                     "WonderSwan timbre and native noise-frequency parity are not established",
                     "Runtime and audible verification are separate root-owned work"])


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    paths = [getattr(args, key) for key in ("input", "gba", "wsc10", "wsc15", "output", "manifest")]
    need(all(p.suffix.lower() != ".sav" for p in paths), "save paths forbidden")
    output, report = build(*(p.read_bytes() for p in paths[:4]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[iraira-floor-launch] " + report["output_sha256"])


if __name__ == "__main__":
    main()

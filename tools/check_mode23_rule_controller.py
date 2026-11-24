"""Author checks of linked ARM turn bodies against source-derived state effects.

Imported services use explicit fixtures. This is not a complete scene, native
adapter verification, independent review, or an emulator/gameplay result.
"""
import argparse
import hashlib
import itertools
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_rule_controller import assembly, ENTRIES, DEPENDENCIES

BASE = 0x08000000
CTX = 0x02001018
ACTORS = tuple(0x02002018 + i * 0x118 for i in range(6))
PARAM = 0x02003000


def signed16(v):
    return (v & 32767) - (v & 32768)


def link(source):
    names = [f"m23_src_{x:04X}" for x in ENTRIES] + list(DEPENDENCIES)
    names += [f"m23_cb_{x:04X}" for x in sorted(set(ENTRIES) | {0xB71C, 0xB740, 0xB7D9})]
    prefix = "\n".join(".word " + n for n in names) + "\n"
    suffix = "\n".join(n + ": bx lr" for n in names if n in DEPENDENCIES or "_cb_" in n)
    data = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(prefix + assembly(source) + suffix, BASE)[0])
    symbols = dict(zip(names, struct.unpack_from("<" + "I" * len(names), data)))
    # Literal words are stopping positions only, never accepted as instructions.
    positions = set(range(BASE + len(names) * 4, BASE + len(data), 4))
    return data, symbols, positions


class CheckedMachine(Machine):
    def run_body(self, start, positions):
        terminal = self.r[14]
        pc = start
        for _ in range(2000):
            if pc == terminal:
                return
            assert pc in positions, f"unlinked execution {pc:08X}"
            word = self.get(pc)
            if word & 0x0FC000F0 == 0x00000090:
                assert word >> 28 == 14 and not word & 0x00300000, "plain unconditional MUL only"
                rd, rm, rs = (word >> 16) & 15, word & 15, (word >> 8) & 15
                assert rd != rm and 15 not in (rd, rm, rs), "ARM7 multiply register constraint"
                self.r[rd] = self.r[rm] * self.r[rs] & 0xFFFFFFFF
                pc += 4
            else:
                pc = super().run(pc, (positions - {pc}) | {terminal}, 2)
        raise AssertionError("bounded rule body failed to return")


def case(data, symbols, positions, entry, *, timer=1, count=3, turn=0,
         mask=0, flags=0, cpu=0, angle=0, strength=1, held=0, pressed=0,
         power=256, trig=(256, -256), moving=-1, eliminated=-1):
    m = CheckedMachine(data, seed=9, flags=0xA000001F)
    for start, size in [(CTX - 0x18, 0x118), (PARAM, 4)] + [(p - 0x18, 0x118) for p in ACTORS]:
        for i in range(size):
            m.put(start + i, 0, 1)
    m.r[4] = m.r[5] = CTX
    for i, ptr in enumerate(ACTORS):
        m.put(CTX + 12 + 4 * i, ptr - 0x18)
        m.put(ptr + 0x20, PARAM)
    actor = ACTORS[turn]
    m.put(CTX + 0x30, timer, 2)
    m.put(CTX + 0x2B, count, 1)
    m.put(CTX + 0x2E, turn, 1)
    m.put(CTX + 0x26, mask, 2)
    m.put(CTX + 0x28, 65535, 2)
    m.put(CTX + 0x2F, strength, 1)
    m.put(actor, flags, 2)
    m.put(actor + 2, cpu, 1)
    m.put(actor + 0x10, angle, 2)
    m.put(PARAM + 2, power, 2)
    if moving >= 0:
        m.put(ACTORS[moving] + 0x0C, 1, 2)
    if eliminated >= 0:
        m.put(ACTORS[eliminated], 1, 2)
    original = dict(m.mem)
    events = []
    expected = dict(m.mem)
    expected_events = []

    def write(at, value, size=2):
        for i in range(size):
            expected[at + i] = value >> (8 * i) & 255

    def callback(ptr, target):
        write(ptr - 0x18, symbols[f"m23_cb_{target:04X}"], 4)
        expected_events.append(("callback", ptr, target))

    def event(ptr, value):
        expected_events.append(("event", ptr, value))

    def sound(value, priority=1):
        expected_events.append(("sound", value, priority))

    reverse_cb = {v: int(k[-4:], 16) for k, v in symbols.items() if "_cb_" in k}

    def service(name):
        def execute(vm):
            a, b = vm.r[:2]
            if name == "m23_actor":
                assert 0 <= a < count
                vm.r[0] = ACTORS[a]
            elif name == "m23_callback":
                assert b in reverse_cb
                vm.put(a - 0x18, b)
                events.append(("callback", a, reverse_cb[b]))
            elif name == "m23_event":
                events.append(("event", a, b))
            elif name == "m23_sound":
                events.append(("sound", a, b))
            elif name == "m23_held":
                vm.r[0] = held
            elif name == "m23_pressed":
                vm.r[0] = pressed
            elif name in ("m23_cos", "m23_sin"):
                events.append((name[4:], a))
                vm.r[0] = trig[name == "m23_sin"] & 0xFFFFFFFF
            elif name in ("m23_window_top", "m23_bg2_enable"):
                events.append((name[4:], a))
            elif name == "m23_src_BC9C":
                events.append(("ai",))
                vm.put(actor + 0x10, 31, 2)
                vm.put(CTX + 0x2F, 79, 1)
            elif name in ("m23_src_BA57", "m23_src_BF42"):
                events.append((name[-4:],))
            else:
                raise AssertionError(name)
        return execute

    m.services = {symbols[n]: service(n) for n in DEPENDENCIES}
    t = (timer - 1) & 65535
    timed = entry in (0xB212, 0xB276, 0xB3BF, 0xB533, 0xB6EA)
    if timed:
        write(CTX + 0x30, t)
    if entry == 0xB1E5:
        write(CTX + 0x30, 75); callback(CTX, 0xB212)
    elif entry == 0xB212 and t == 0:
        selected = turn
        wraps = 0
        while True:
            selected += 1
            if selected >= count:
                selected = 0; wraps += 1; expected_events.append(("BA57",))
            if not mask & (1 << selected):
                break
        write(CTX + 0x28, 65535 + wraps)
        write(CTX + 0x2E, selected, 1); write(CTX + 0x30, 33)
        callback(CTX, 0xB276)
    elif entry == 0xB276:
        write(actor, flags | 2)
        if t == 0:
            write(actor, flags & ~2)
            if cpu:
                write(CTX + 0x30, 30); sound(0x84)
                if not flags & 0x8000: event(actor, 1)
                callback(CTX, 0xB6EA)
            else:
                write(actor + 0x10, 0); write(actor + 0x12, 24)
                callback(actor, 0xB740); callback(CTX, 0xB355)
    elif entry == 0xB355:
        write(actor + 0x10, (angle - bool(held & 6) + bool(held & 9)) & 255)
        if pressed & 0x40:
            write(CTX + 0x30, 17); callback(CTX, 0xB3BF)
    elif entry == 0xB3BF and t == 0:
        callback(actor, 0xB71C); write(CTX + 0x2F, 1, 1)
        expected_events.append(("window_top", 128)); sound(0xD6)
        if not flags & 0x8000: event(actor, 1)
        callback(CTX, 0xB46D)
    elif entry == 0xB46D:
        expected_events.append(("bg2_enable", 1))
        value = (strength + 2) & 255
        if value > 80:
            value = 1; sound(0xD6)
        write(CTX + 0x2F, value, 1)
        expected_events.append(("window_top", 1 if value > 78 else 112 - value))
        if pressed & 0x40:
            write(CTX + 0x30, 17); sound(0x84); callback(CTX, 0xB533)
    elif entry in (0xB533, 0xB6EA) and t == 0:
        if entry == 0xB6EA:
            expected_events.append(("ai",)); angle = 31; strength = 79
            write(actor + 0x10, angle); write(CTX + 0x2F, strength, 1)
        scale = power * strength >> 8
        scale = signed16(scale + (scale >> 1) + 20)
        angle &= 248
        write(actor + 0x10, angle)
        expected_events.extend((("cos", angle), ("sin", angle)))
        for offset, value in zip((12, 14), trig):
            write(actor + offset, signed16(value) * scale >> 4)
        callback(actor, 0xB7D9); expected_events.append(("bg2_enable", 0))
        sound(0xD7, 2); event(actor, 0); callback(CTX, 0xB657)
    elif entry == 0xB657:
        expected_events.append(("BF42",))
        if moving < 0 or moving == eliminated:
            callback(CTX, 0xB6C4)
    elif entry == 0xB6C4:
        callback(CTX, 0xB1E5)
    saved = m.r[:]
    m.run_body(symbols[f"m23_src_{entry:04X}"], positions)
    assert m.r[4:15] == saved[4:15], (hex(entry), "callee registers/SP/LR")
    assert events == expected_events, (hex(entry), events, expected_events)
    assert all(m.mem[a] == v for a, v in expected.items()), (hex(entry), "live fixture state")
    assert set(m.mem) - set(original) <= set(range(saved[13] - 64, saved[13])), "only bounded dead stack"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    assert not args.report.exists(), "fresh report"
    source = args.source.read_bytes()
    data, symbols, positions = link(source)
    total = 0
    def run(entry, **options):
        nonlocal total
        case(data, symbols, positions, entry, **options); total += 1
    for entry in ENTRIES:
        run(entry)
    for count in range(3, 7):
        for turn in range(count):
            for mask in range((1 << count) - 1):
                run(0xB212, count=count, turn=turn, mask=mask)
    for timer, flags, cpu in itertools.product((0, 1, 2, 65535), (0, 2, 0x8000, 65535), (0, 1)):
        for entry in (0xB276, 0xB3BF): run(entry, timer=timer, flags=flags, cpu=cpu)
    for held, pressed, angle in itertools.product(range(16), (0, 64), (0, 1, 127, 255, 65535)):
        run(0xB355, held=held, pressed=pressed, angle=angle)
    for strength, pressed in itertools.product(range(256), (0, 64)):
        run(0xB46D, strength=strength, pressed=pressed)
    for entry, timer, angle, strength, power, trig in itertools.product(
            (0xB533, 0xB6EA), (0, 1, 2), (0, 7, 31, 128, 255), (0, 1, 79, 255),
            (0, 1, 256, 65535), ((0, 0), (256, -256), (32767, -32768))):
        run(entry, timer=timer, angle=angle, strength=strength, power=power, trig=trig)
    for moving, eliminated in itertools.product(range(-1, 3), repeat=2):
        run(0xB657, moving=moving, eliminated=eliminated)
    bad = bytearray(source); bad[0x74BAEF] ^= 1
    try:
        assembly(bytes(bad))
    except ValueError:
        pass
    else:
        raise AssertionError("changed source must reject")
    report = dict(status="PASS", role="author ARM/fixture checks", cases=total,
                  linked_fixture_bytes=len(data), source_sha256=hashlib.sha256(source).hexdigest().upper(),
                  assembly_sha256=hashlib.sha256(assembly(source).encode()).hexdigest().upper(),
                  helpers="explicit service fixtures; no adapter/scene/runtime claim",
                  body_callbacks=[f"{x:04X}" for x in ENTRIES], source_mismatch_rejected=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

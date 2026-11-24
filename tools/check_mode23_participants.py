"""Author ARM checks with explicitly declared native-service fixtures.

These checks do not stand in for native consumer review or game execution.
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
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from check_mode23_rule_controller import CheckedMachine
import mode23_participant_controller as participant
import mode23_participant_setup as setup
import mode23_item_ai as item

BASE = 0x08000000
CTX = 0x02001018
ACTORS = tuple(0x02002018 + i * 0x118 for i in range(6))
AUX = 0x02003018
PARAM = 0x02004000


def signed(v):
    return (v & 32767) - (v & 32768)


def link(source):
    bodies = [participant.assembly(source), setup.assembly(source), item.assembly(source)]
    exported = {f"m23_src_{x:04X}" for x in participant.ENTRIES} | set(participant.HELPERS)
    exported |= {"m23_participants_create", "m23_intro_actors", "m23_src_BA57",
                 "m23_src_BC9C", "m23_collision_pickup"}
    external = (set(participant.DEPENDENCIES) | set(setup.DEPENDENCIES) | set(item.DEPENDENCIES)) - exported
    external |= {f"m23_cb_{x:04X}" for x in (0xB71C, 0xB950, 0xB999, 0xB99A, 0xBC1C, 0xAC67)}
    names = sorted(exported | external)
    directory = "\n".join(".word " + n for n in names) + "\n"
    suffix = "\n".join(n + ":bx lr" for n in sorted(external))
    data = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(directory + "\n".join(bodies) + suffix, BASE)[0])
    symbols = dict(zip(names, struct.unpack_from("<" + "I" * len(names), data)))
    return data, symbols, set(range(BASE + len(names) * 4, BASE + len(data), 4)), external


def machine(data, symbols, external, *, frame=0, rng=()):
    m = CheckedMachine(data, seed=11, flags=0xA000001F)
    for p in (CTX, *ACTORS, AUX):
        for j in range(-0x18, 0x100):
            m.put(p + j, 0, 1)
    for j in range(256):
        m.put(PARAM + j, 0, 1)
    m.r[4] = CTX
    m.r[5] = ACTORS[1]
    m.put(CTX, CTX - 0x18)
    m.put(CTX + 8, AUX - 0x18)
    m.put(CTX + 0x2B, 3, 1)
    m.put(CTX + 0x2C, 3, 1)
    m.put(CTX + 0x2E, 1, 1)
    for i, p in enumerate(ACTORS):
        m.put(CTX + 12 + i * 4, p - 0x18)
        m.put(p + 2, i, 1)
        m.put(p + 3, i, 1)
        m.put(p + 0x20, PARAM)
    events, random = [], iter(rng)
    allocation = [0]

    def service(name):
        def run(vm):
            a, b, c = vm.r[:3]
            if name == "m23_actor":
                assert 0 <= a < vm.get(CTX + 0x2B, 1)
                vm.r[0] = ACTORS[a]
            elif name == "m23_callback":
                vm.put(a - 0x18, b)
                events.append((name, a, b))
            elif name == "m23_spawn":
                i = allocation[0]
                assert i < 6
                allocation[0] += 1
                p = ACTORS[i]
                for j in range(256):
                    vm.put(p + j, 0, 1)
                vm.put(p - 0x18, b)
                vm.put(p - 0x14, a)
                vm.put(p + 0xFC, c)
                vm.r[0] = p - 0x18
                events.append((name, a, b, c))
            elif name == "m23_base_param":
                vm.r[0] = PARAM + a * 8
            elif name == "m23_evolved_param":
                vm.r[0] = PARAM + 120 + a * 8
            elif name == "m23_framecounter":
                vm.r[0] = frame
            elif name == "m23_rng":
                vm.r[0] = next(random)
                events.append((name,))
            elif name == "m23_atan":
                events.append((name, signed(a), signed(b)))
                vm.r[0] = 0x35
            elif name.startswith("m23_cb_"):
                raise AssertionError("callback executed synchronously")
            else:
                events.append((name, a, b))
        return run
    m.services = {symbols[n]: service(n) for n in external}
    return m, events


def checks(source):
    data, sym, positions, imports = link(source)
    counts = {"allocation": 0, "intro": 0, "friction": 0, "motion": 0, "timers": 0, "ai": 0, "pickup": 0}
    def run(m, label):
        before = m.r[4:12].copy()
        sp = m.r[13]
        m.run_body(sym[label], positions)
        assert m.r[4:12] == before and m.r[13] == sp, label + " callee state"
    for row, selected in itertools.product(setup.tables(source), range(15)):
        m, ev = machine(data, sym, imports)
        m.put(CTX + 0x2A, row["round"], 1)
        m.put(CTX + 0x2D, selected, 1)
        run(m, "m23_participants_create")
        assert m.get(CTX + 0x2B, 1) == m.get(CTX + 0x2C, 1) == row["count"]
        assert m.get(CTX + 0x2E, 1) == 255
        for i in range(row["count"]):
            p = ACTORS[i]
            ident = selected if i == 0 else row["opponents"][(i - 1) * 2]
            if i and ident == selected:
                ident = row["opponents"][(i - 1) * 2 + 1]
            evolved = bool(row["mask"] & (1 << i))
            assert m.get(p, 2) == (0x8000 if evolved else 0)
            assert (m.get(p + 2, 1), m.get(p + 3, 1)) == (i, ident)
            assert m.get(p + 0x20) == PARAM + 8 * ident + (120 if evolved else 0)
            assert m.get(p + 0xFC) == CTX
            assert m.get(p - 0x14) == 0x2000 + (row["positions"][i * 2] & 255) - row["count"] + i
            assert [signed(m.get(p + f, 2)) for f in (4, 6, 8, 10)] == row["positions"][i * 2:i * 2 + 2] * 2
        counts["allocation"] += 1
        run(m, "m23_intro_actors")
        for i in range(row["count"]):
            p = ACTORS[i]
            expected_x = row["intro"][i * 2] + (0x5000 if i else 0xB000)
            expected_y = row["intro"][i * 2 + 1] - (0x1800 if row["mask"] & (1 << i) else 0)
            assert m.get(p + 4, 2) == expected_x & 65535
            assert m.get(p + 6, 2) == expected_y & 65535
            assert signed(m.get(p + 0xC, 2)) == (-0x600 if i else 0x600)
        counts["intro"] += 1
    for x, y, vx, vy, p0, p4 in itertools.product((-0x4801, -0x4800, 0x4800, 0x4801),
                                                  (-0x3001, 0x3000, 0x3001),
                                                  (-1, 0, 1), (-1, 1), (1, 256, 65535), (0, 7680, 65535)):
        m, ev = machine(data, sym, imports)
        a = ACTORS[1]
        for field, v in ((4, x), (6, y), (12, vx), (14, vy)):
            m.put(a + field, v, 2)
        m.put(PARAM, p0, 2); m.put(PARAM + 4, p4, 2)
        edge = x < -0x4800 and vx < 0 or y < -0x3000 and vy < 0 or x > 0x4800 and vx > 0 or y > 0x3000 and vy > 0
        reduction = min(p4 >> 5, 239) if edge else 0
        m.r[0] = a
        run(m, "m23_src_C775")
        assert m.r[0] == ((240 - reduction) * p0 >> 8) & 65535
        counts["friction"] += 1
    for velocity in (-1000, -18, -17, -16, -1, 0, 1, 16, 17, 18, 1000):
        m, ev = machine(data, sym, imports)
        a = ACTORS[1]
        m.put(PARAM, 256, 2)
        m.put(a + 12, velocity, 2); m.put(a + 14, -velocity, 2)
        run(m, "m23_src_B7D9")
        assert signed(m.get(a + 4, 2)) == velocity and signed(m.get(a + 6, 2)) == -velocity
        for field, v in ((12, velocity), (14, -velocity)):
            expected = signed(v * 240 >> 8)
            if -16 < expected < 16:
                expected = 0
            assert signed(m.get(a + field, 2)) == expected
        counts["motion"] += 1
    for timer, frame in itertools.product((0, 1, 2, 65535), (0, 4)):
        m, ev = machine(data, sym, imports, frame=frame)
        m.put(ACTORS[1] + 0x1E, timer, 2)
        run(m, "m23_src_B950")
        assert m.get(ACTORS[1] + 0x1E, 2) == (timer - 1) & 65535
        assert bool([e for e in ev if e[0] == "m23_callback"]) == (timer == 1)
        counts["timers"] += 1
    for mode in ("player", "random", "aux", "center"):
        random = {"player": (0, 17, 123), "random": (6, 2, 17, 123),
                  "aux": (17, 123), "center": (7, 123)}[mode]
        m, ev = machine(data, sym, imports, rng=random)
        for i, p in enumerate(ACTORS):
            m.put(p + 4, (i - 1) * 0x1000, 2)
            m.put(p + 6, i * 0x800, 2)
        if mode == "aux":
            m.put(CTX + 0x24, 4, 2); m.put(AUX + 4, 0x2000, 2)
        if mode == "center":
            m.put(ACTORS[1] + 4, 0x5000, 2)
        run(m, "m23_src_BC9C")
        assert m.get(ACTORS[1] + 0x10, 2) == 0x35
        assert m.get(CTX + 0x2F, 1) == (39 if mode == "center" else 33)
        assert len([e for e in ev if e[0] == "m23_rng"]) == len(random)
        target = {"player": (ACTORS[0]), "random": ACTORS[2], "aux": AUX}.get(mode)
        a = ACTORS[1]
        args = (signed(-m.get(a + 6, 2)), signed(-m.get(a + 4, 2))) if mode == "center" else tuple(
            (signed(m.get(target + f, 2)) >> 8) - (signed(m.get(a + f, 2)) >> 8) for f in (6, 4))
        assert ("m23_atan", *args) in ev
        counts["ai"] += 1
    for ident in range(15):
        m, ev = machine(data, sym, imports)
        a = ACTORS[1]
        m.put(a + 3, ident, 1); m.put(a + 4, 0x1234, 2); m.put(a + 6, 0xF000, 2)
        m.r[0], m.r[1] = a, AUX
        run(m, "m23_collision_pickup")
        assert m.get(a, 2) & 0x8000
        assert m.get(a + 0x20) == PARAM + 120 + ident * 8
        assert (m.get(AUX + 4, 2), m.get(AUX + 6, 2), m.get(AUX + 0x1E, 2)) == (0x1234, 0xE200, 40)
        assert ev[-1] == ("m23_sound", 0x98, 1)
        counts["pickup"] += 1
    return {"status": "PASS", "scope": "author linked ARM with declared imported-service fixtures",
            "counts": counts, "total": sum(counts.values()), "assembly_bytes": len(data),
            "assembly_sha256": hashlib.sha256(data).hexdigest().upper(),
            "runtime": False, "native_adapter_verified": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--wsc", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    report = checks(a.wsc.read_bytes())
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

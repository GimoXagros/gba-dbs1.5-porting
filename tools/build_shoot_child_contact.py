"""Connect the missing source stage11 child-contact successor, preserving retail stages."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner
from shoot_child_contact_callbacks import assembly, SOURCE

BASE, FIRST, LIMIT, HOOK = 0x08000000, 0xD8C800, 0xD8CE00, 0x36F77C
INPUT = "574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"
EFFECT = 0x0835972C
LABELS = ("child_contact_route", "child_contact_966a", "child_contact_96e6", "child_contact_973e")


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def assemble(text, address):
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, address)[0])


def payload(source):
    data = assemble(assembly(source, EFFECT) + "\n" + "\n".join(".word " + label for label in LABELS), BASE + FIRST)
    assert len(data) <= LIMIT - FIRST
    entries = dict(zip(LABELS, struct.unpack("<4I", data[-16:])))
    assert entries[LABELS[0]] == BASE + FIRST
    assert all(BASE + FIRST <= value < BASE + FIRST + len(data) - 16 for value in entries.values())
    return data, entries


def writes(source):
    data, entries = payload(source)
    return [(FIRST, data, "source stage11 child-contact route and callbacks"),
            (HOOK, assemble(f"b 0x{BASE+FIRST:08X}", BASE + HOOK), "typed stage11 collision successor")], entries


def parity(before, after):
    count = 0
    for stage in range(256):
        if stage == 11:
            continue
        for flags in range(16):
            outcomes = []
            for rom in (before, after):
                m = Machine(rom, seed=7, flags=(flags << 28) | 0x1F)
                m.r[4] = 0x02011018
                m.put(m.r[4] + 4, 0xD10B, 2)
                m.put(m.r[4] + 0x14, 0x02012018, 4)
                m.put(0x0300231E, stage, 1)
                m.run(BASE + HOOK, {0x0836E484})
                outcomes.append((m.r[:15], m.cpsr, m.get(0x02011018, 4),
                                 m.get(0x0201101C, 2), m.get(0x0201208E, 2)))
            assert outcomes[0] == outcomes[1], (stage, flags)
            count += 1
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "source", "output", "manifest"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    before, source = a.before.read_bytes(), a.source.read_bytes()
    assert sha(before) == INPUT and sha(source) == SOURCE
    assert not a.output.exists() and not a.manifest.exists()
    assert before[HOOK:HOOK+4] == assemble("ldr r8,[pc,#0x108]", BASE+HOOK)
    assert struct.unpack_from("<I", before, 0x36F88C)[0] == 0x083723E0
    assert before[FIRST:LIMIT] == b"\xff" * (LIMIT-FIRST)
    scan = types.FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((FIRST, LIMIT),)), argdefs=scanner.inbound.__defaults__)
    hits = scan(before)
    assert not hits, hits
    changes, entries = writes(source)
    after = bytearray(before)
    ledger = []
    for at, data, label in changes:
        ledger.append(dict(offset=at, size=len(data), before_hex=before[at:at+len(data)].hex(), after_hex=data.hex(), label=label))
        after[at:at+len(data)] = data
    inverse = bytearray(after)
    for row in ledger:
        inverse[row["offset"]:row["offset"]+row["size"]] = bytes.fromhex(row["before_hex"])
    assert bytes(inverse) == before
    cases = parity(before, bytes(after))
    report = dict(status="PASS", input_sha256=INPUT, source_sha256=SOURCE, output_sha256=sha(after),
                  entries=entries, reservations=[[FIRST, LIMIT]], writes=ledger,
                  declared_bytes=sum(row["size"] for row in ledger), changed_bytes=sum(x != y for x, y in zip(before, after)),
                  new_RAM_bytes=0, inbound_hits=hits, whole_image_inverse=True,
                  non11_native_route_parity_cases=cases,
                  source_route=[0x760E4B, 0x760E95], source_callbacks=[0x749F6A, 0x74A098],
                  effect_constructor=EFFECT, source_events=[1, 2],
                  actual_runtime_verified=False, final_port_complete=False,
                  limits=["Callback/service semantics and ownership need independent verification before main integration.",
                          "No renderer clamp, replacement animation, mode write suppression or game-state cheat."])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(after)
    a.manifest.write_text(json.dumps(report, indent=2)+"\n", encoding="utf8", newline="\n")
    print(json.dumps({key: report[key] for key in ("status", "output_sha256", "declared_bytes", "changed_bytes", "non11_native_route_parity_cases")}))


if __name__ == "__main__":
    main()

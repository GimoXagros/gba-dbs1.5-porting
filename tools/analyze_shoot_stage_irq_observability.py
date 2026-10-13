#!/usr/bin/env python3
"""Bounded source evidence for the unresolved Shoot0DEC IRQ read.

No builder import, machine execution, emulator, RAM snapshot or save access.
The map-row calculation is a conditional algebraic proof, not a claim that
its blank-tile and no-refill lifetime prerequisites have been established.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

SOURCE_SHA = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GUARDS = (
    ("main_loop", 0x7506F6, 0x750770, "EC8CCE5AF7409533D559935A99FBD79AD921458D246D9AAC9D8E897DA4E2A0C2"),
    ("scheduler", 0x750B1F, 0x750B94, "1BB8F677FA508697A9374ABECA9BB3E6321CA4DBFC73CFA854BA6D64C444C876"),
    ("frame_wait", 0x750EBD, 0x750ED9, "A0DAACB8F1902725909B378ABB3BEAEB62A81AAB1BF88BA432BC74E0343BDE7E"),
    ("task_allocator", 0x750970, 0x75099A, "9E5150552BF3890E35CF3C561D1D459279CCD98552EA126E92C4A6843A065C81"),
    ("transfer_flush", 0x7520C1, 0x7520F3, "E674B9419460D9363D1628B5DDE353F301A6AAC19B7F63F567FF1DD1724BB03B"),
    ("terminal_battle", 0x74148B, 0x74160B, "D5E1FF21AD453C5EF2EB61034B84A7B99A368D86B8438F49ADFC58CCFA319E33"),
    ("stage_bounds_consumer", 0x77E0C5, 0x77E1A4, "D27C5D44BA4721DC3688F7ACCEC47C34AA16D511A2B7E1E653728B52FA751C28"),
    ("display_transition", 0x75FB91, 0x75FBE2, "3751AF90D7BFEF65710235112085A0B5CCC7D98A35DE08100CA3FCF0D07AB290"),
    ("transition_IRQs", 0x75FC27, 0x75FCA3, "A8B2F3CC1B7C5FC7E1FB0E074332E6960AA5B0F69A380CCF0BAF7256E0BD280A"),
    ("transition_update", 0x75FCAB, 0x75FE03, "31405427B84E0B8A7732461307D3D5E8087BB654AA15DAD7FE439C61F8E04301"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def exact(source: bytes, raw: int, expected: list[str]) -> None:
    rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[raw:raw + 96], raw))[:len(expected)]
    need([f"{i.mnemonic} {i.op_str}".rstrip() for i in rows] == expected, f"source instruction contract {raw:X}")


def analyze(source: bytes) -> dict:
    need(sha(source) == SOURCE_SHA, "original source hash")
    for label, first, last, expected in GUARDS:
        need(sha(source[first:last]) == expected, "source range " + label)
    exact(source, 0x75097D, ["mov bx, 0x14", "mov cx, word ptr [bx + 0xa]", "and cx, 2", "je 0x750990", "add bx, 0x110"])
    exact(source, 0x750B5D, ["pop cx", "pop di", "pop es", "mov si, word ptr es:[0x10]", "mov ax, word ptr es:[si + 4]", "cmp word ptr es:[di + 4], ax", "mov di, word ptr es:[di + 8]"])
    exact(source, 0x750B7F, ["lcall 0x4fff, 0xecd"])
    exact(source, 0x750EBD, ["push ax", "push ds", "in al, 0xb2", "or al, 0x40", "out 0xb2, al", "mov ax, 0xc00", "mov ds, ax", "cmp byte ptr [0x3754], 0", "je 0x750eca", "mov byte ptr [0x3754], 0", "pop ds", "pop ax", "retf"])
    exact(source, 0x7520DE, ["mov di, word ptr [bx]", "mov cx, word ptr [bx + 6]", "mov si, word ptr [bx + 4]", "mov ds, word ptr [bx + 2]", "rep movsw word ptr es:[di], word ptr [si]"])
    exact(source, 0x75FC90, ["mov bx, 0x300", "mov es, bx", "mov bx, 0xea", "mov ax, word ptr es:[di + 0xa]", "out 0x10, al"])
    exact(source, 0x7414B3, ["test byte ptr es:[0x3cd], 7", "je 0x7414be", "jmp 0x74160a"])
    exact(source, 0x7415B7, ["lcall 0x4fff, 0x3367"])
    exact(source, 0x7415D7, ["lcall 0x7ccf, 0x11bc"])
    exact(source, 0x77E0E8, ["mov ax, word ptr es:[si + 0x1e]", "mov word ptr es:[di + 0x1e], ax"])
    offsets = list(source[0x75FCA3:0x75FCAB])
    need(offsets == [0, 2, 4, 7, 10, 13, 17, 21], "immutable scanline offsets")

    # Every 16-bit result of the allocator's arithmetic is congruent to4
    # modulo16. This does not assume all such addresses are valid task slots.
    values = {(0x14 + 0x110 * n) & 65535 for n in range(4096)}
    need(len(values) == 4096 and all(x % 16 == 4 for x in values) and 0xEA not in values, "task-offset congruence")

    cases, visible_states = 0, []
    for k in range(1, 144):
        # Source state4 starts at old state2=k and advances once per match.
        matches = [k + index + offset for index, offset in enumerate(offsets)]
        need(matches[-1] + 1 == k + 29, "first0DEC compare")
        if k + 29 <= 143:
            visible_states.append(k)
        for base in range(256):
            # Only previous values m>k are admitted; the current frame's
            # update/IRQ ordering cannot be used to supply a missing row.
            prior_clears = {((base + m) & 255) // 8 for m in range(136, k, -8)}
            for line in range(k + 29, 144):
                sampled_row = ((base - offsets[-1] + line) & 255) // 8
                need(sampled_row in prior_clears, "conditional visible map row coverage")
                cases += 1
    need(cases == 1678080 and visible_states == list(range(1, 115)), "complete finite coverage domain")
    return {
        "status": "EVIDENCE_CHECKS_PASS", "route_gate": "UNRESOLVED",
        "source_sha256": SOURCE_SHA,
        "source_ranges": [{"label": label, "first": first, "end_exclusive": last, "sha256": digest}
                          for label, first, last, digest in GUARDS],
        "interrupted_DI": {
            "frame_wait_preserves_DI": True,
            "scheduler_DI": "task-list offset, restored around each callback and advanced via task+8",
            "allocator_congruence": "0014+0110*n modulo65536 is4 modulo16, never00EA",
            "arithmetic_cases": 4096,
            "other_DI_writer": "main-loop transfer flush7520DE loads a destination and REP MOVSW advances DI without restoring it",
            "conclusion": "No global DI=EA invariant; this is not a timed runtime counterexample or proof that source execution is always erroneous",
        },
        "conditional_visibility": {
            "old_state2_values": [1, 143], "base_byte_values": [0, 255],
            "state6_values": [0, 8], "offsets": offsets,
            "first_final_IRQ_compare": "old_state2+29",
            "final_scroll_Y": "(base-21)&255",
            "potential_visible_final_IRQ_old_state2": [1, 114],
            "covered_visible_line_cases": cases,
            "clear_history": "only multiples8 from136 down to strictly greater than currentoldstate2",
            "current_frame_clear_required": False,
            "conditional_conclusion": "Every sampled visible row after0DEC lies in a previously cleared row, if those rows have not been repopulated",
            "open_assumptions": [
                "common bank0 tile0 is horizontally uniform and its initialization/lifetime is reachable and preserved",
                "no later BG1 refill repopulates any previously cleared sampled row",
                "source callback schedule is followed; no runtime timing or interrupt latency was measured",
            ],
        },
        "refill_gate": {
            "terminal_battle": "4090:0B8B at74148B..74160A",
            "pause_test": "only source03CD low7 at7414B3; common03D4bit10 does not bypass this camera block",
            "calls": ["7415B7 ->4FFF:3367", "7415D7 ->7CCF:11BC", "77E196 ->4FFF:3367"],
            "effect": "stage bounds copy BG0 vertical velocity into BG1 and invoke its existing map/scroll consumer",
            "actor_stationary_or_refill_footprint_proved": False,
        },
        "unvalidated_blank_tile_lead": "source74FEA0 routine clears4000..401F, but no reachable direct caller/lifetime has been validated; excluded from proof",
        "ROM_modified": False, "runtime_or_save_test": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    need(args.wsc15.suffix.lower() != ".sav", "save input forbidden")
    report = analyze(args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-stage-irq-observability] evidence checked; route remains UNRESOLVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

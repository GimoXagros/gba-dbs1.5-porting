#!/usr/bin/env python3
"""Exact storage-consumer pairs and exhaustive 8EF3 table-exhaustion semantics.

No ROM mutation or emulation. Finite input coverage does not assert gameplay
reachability. The source observer separately measures a normal-input path.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_ARCH_ARM, CS_MODE_ARM

SOURCE_SHA = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_SHA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
BASE = 0x740900


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def exact(data, at, expected, arm=False):
    engine = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    rows = list(engine.disasm(data[at:at + 256], at + (0x08000000 if arm else 0)))[:len(expected)]
    need([f"{r.mnemonic} {r.op_str}".strip() for r in rows] == expected, f"instruction contract {at:X}")


def s16(value):
    return value - 65536 if value >= 32768 else value


def spatial(source):
    exact(source, 0x7497F3, ["mov cx, 5", "mov bx, 0x8fef", "mov ax, word ptr [si + 0x8c]",
        "cmp ax, word ptr cs:[bx]", "jle 0x749807", "add bx, 8", "loop 0x7497fd",
        "mov cx, word ptr cs:[bx + 2]", "mov bx, word ptr cs:[bx + 4]",
        "mov ax, word ptr [si + 0x26]", "cmp ax, word ptr cs:[bx]", "jl 0x74981c",
        "add bx, 4", "loop 0x749812", "mov bx, word ptr cs:[bx + 2]", "mov ax, bx",
        "add bx, bx", "jmp word ptr cs:[bx - 0x7025]"])
    word = lambda offset: struct.unpack_from("<H", source, BASE + (offset & 65535))[0]
    ys = Counter()
    for y in range(65536):
        bx = 0x8FEF
        for _ in range(5):
            if s16(y) <= s16(word(bx)):
                break
            bx += 8
        ys[bx] += 1
    need(len(ys) == 6 and sum(ys.values()) == 65536, "all signed Y partitions")
    rows, entire = [], Counter()
    for row, y_count in sorted(ys.items()):
        count, pointer = word(row + 2), word(row + 4)
        need(0 < count <= 9, "actual exhausted-row count bounded")
        results = Counter()
        for x in range(65536):
            bx = pointer
            for _ in range(count):
                if s16(x) < s16(word(bx)):
                    break
                bx = (bx + 4) & 65535
            selector = word(bx + 2)
            target = word(0x8FDB + ((selector * 2) & 65535))
            results[(selector, target)] += 1
            entire[(selector, target)] += y_count
        rows.append(dict(row_offset=f"{row:04X}", y_values=y_count, count=count,
            x_pointer=f"{pointer:04X}", outcomes=[dict(selector=f"{s:04X}", target=f"{t:04X}", x_values=n)
                for (s, t), n in sorted(results.items())]))
    need(sum(entire.values()) == 2 ** 32, "complete 16-bit X/Y cross product")
    need({t for s, t in entire if s > 9} == {0x0A80, 0xEB4C, 0xE59A}, "exact out-of-table jump targets")
    need(rows[-1]["x_pointer"] == "0800", "exhausted Y loop reads code pointer")
    return dict(input_pairs=2 ** 32, evaluated_x_partitions=6 * 65536, rows=rows,
        defined_pattern_pairs=sum(n for (s, t), n in entire.items() if s <= 9 and t in (0x8F29,0x8F65)),
        unrelated_target_pairs=sum(n for (s, t), n in entire.items() if s > 9),
        conclusion="Unrestricted 16-bit arithmetic does not produce only spatial patterns; out-of-table cases jump into unrelated source addresses. Gameplay reachability is not inferred.")


def consumers(source, gba, candidate):
    expected = {
        "d83c": [0x743307,0x7435BF,0x7435C6,0x7435D0,0x747CE5,0x76055D,0x760C84,0x7672EE,0x7672F7,0x7672FE,0x76730B],
        "da3c": [0x74330E,0x747CEC],
    }
    for pattern, positions in expected.items():
        hits = [m.start() + 0x700000 for m in re.finditer(re.escape(bytes.fromhex(pattern)),source[0x700000:])]
        need(hits == positions, "complete fixed-ROM direct operand inventory " + pattern)
    pairs = []
    for source_at, register, native_at, obj, literal in (
        (0x760554,"di",0x36EB18,"r5",0x36EC04),
        (0x760C7B,"di",0x36F470,"r5",0x36F864),
        (0x7672E5,"si",0x35A080,"r4",0x35A0E8),
    ):
        exact(source,source_at,["xor bx, bx",f"mov bl, byte ptr [{register} + 0x10]","shl bx, 1","mov word ptr [bx + 0x3cd8], 0x96"])
        displacement = literal - (native_at + 8 + 8)
        exact(gba,native_at,[f"ldrb r1, [{obj}, #0x10]","lsl r1, r1, #1",f"ldr r8, [pc, #0x{displacement:x}]","mov sb, #0x96","strh sb, [r1, r8]"],True)
        need(struct.unpack_from("<I",gba,literal)[0] == 0x030048AC, "actual native timer literal")
        need(candidate[native_at:native_at+20] == gba[native_at:native_at+20] and candidate[literal:literal+4] == gba[literal:literal+4], "v65 retains real timer consumers")
        pairs.append(dict(source=f"{source_at:06X}",native=f"{0x08000000+native_at:08X}",value=150,
            native_storage="030048AC + 2*player_index",source_storage="DS:3CD8 + 2*player_index",
            ownership="normal object-task DS=0C00 inherited ABI; not source1000:3CD8"))
    exact(source,0x7672F2,["add bx, 4","cmp word ptr [bx + 0x3cd8], 0","je 0x767303","dec word ptr [bx + 0x3cd8]","jmp 0x767312","cmp word ptr [si + 0x56], 0","je 0x767312","mov word ptr [bx + 0x3cd8], 4","dec word ptr [si + 0x56]"])
    return dict(direct_operand_candidates=13,paired_delay_producers=pairs,
        decay_timer_identity="the last four indexed accesses use BX+=4, thus FCDC/FCDE and native030048B0/B2 under normal task ABI",
        distinct_SRAM_positive_reader_identified=False,
        limit="Finite direct operand population only; descriptor/indirect and restored-state accesses are not excluded.")


def observer_contract(source, script):
    sites = {0x747A68:"push bp",0x747CE2:"mov word ptr es:[0x3cd8], 0",0x772DEA:"mov ax, 0xc00",
        0x773650:"mov ax, 0xc00",0x7738CA:"mov di, bx",0x75FC90:"mov bx, 0x300",0x750EBD:"push ax"}
    for at, first in sites.items():
        exact(source,at,[first])
        need(f"0x{at:06X}" in script, "observer source anchor")
    need(not re.search(r"\b(?:memory|mainmemory)\.write|\bemu\.setregister|\bsavestate\.",script), "observer must not mutate guest or load state")
    need("assert(calibrated > 0" in script and "memory_calibration.read > 0 and memory_calibration.write > 0" in script, "positive callback calibrations required")
    return dict(sites=[dict(raw=f"{a:06X}",bus=f"{a-0x700000:05X}") for a in sites],
        callback_scope="System Bus",SRAM_aliases=["13CD8..13CDB","1BCD8..1BCDB"],
        calibration="known frame-wait execution and stage read/write must all be delivered before bounded no-hit interpretation")


def blank_tile_initializer(source):
    # The calibrated original run identifies this real writer, unlike the old unused lead.
    need(struct.unpack_from("<HH",source,0x74FACC+2*12)==(0,0x558C),"mode2 selects actual blank-tile initializer")
    exact(source,0x74FCC9,["mov ax, word ptr [di]","mov bx, ax","add bx, ax","add bx, ax","shl bx, 2"])
    exact(source,0x74FCDD,["lcall cs:[bx + 0x9c]"])
    exact(source,0x755900,["mov ax, 0x300","mov es, ax","xor di, di","mov cx, 0x4ab","xor ax, ax",
        "rep stosw word ptr es:[di], ax","mov es, ax","mov di, 0x4000","mov cx, 0x10","rep stosw word ptr es:[di], ax"])
    return dict(source_entry="558C:0000",mode=2,raw_writer="755916",destination="0000:4000..401F",
        fill=0,words=16,rendering="common bank tile zero is all-zero immediately after this reached writer",
        runtime_corroboration="root fresh run e frame518 captured all32 bytewrites atPS:PC558C:0058",
        remaining="Subsequent tile lifetime and camera refill exclusion during Shoot remain separate requirements.")


def actual_shoot_caller(source):
    direct_calls={0x7417DB:4,0x7417F3:5,0x74180F:0,0x7418AC:2,0x76C241:3,0x7864F9:1}
    hits=[m.start()+0x700000 for m in re.finditer(re.escape(bytes.fromhex("9a0000f071")),source[0x700000:])]
    need(hits==list(direct_calls),"complete fixed-ROM direct root caller inventory")
    for at,arg in direct_calls.items():
        exact(source,at-2,[f"push {arg}","lcall 0x71f0, 0"])
    exact(source,0x740C97,["mov ax, word ptr [0x50]","cmp byte ptr [0x5c], 7","jne 0x740cb0",
        "mov word ptr [0x3ce], 0x4650","mov word ptr [0x3d2], 0x4628","add ax, 2",
        "mov word ptr [0x3d0], ax"])
    exact(source,0x7417B5,["mov bx, 0xc00","mov ax, 0x1000","mov ds, bx","mov es, ax",
        "cmp word ptr es:[0x3d0], 2","jne 0x7417fe","mov bx, word ptr es:[0x65c]",
        "cmp word ptr [bx + 0x50], 0","jne 0x7417e6","cmp word ptr [bx + 0xa4], 0x3e",
        "jne 0x7417e6","push 4","lcall 0x71f0, 0","add sp, 2","jmp 0x7418c6",
        "mov bx, word ptr es:[0x65e]","cmp word ptr [bx + 0x50], 0","jg 0x7417fe",
        "push 5","lcall 0x71f0, 0","add sp, 2","jmp 0x7418c6",
        "cmp word ptr es:[0x3ce], 0","jns 0x74181a","mov word ptr es:[0x3ce], 0",
        "push 0","lcall 0x71f0, 0"])
    exact(source,0x771F69,["cmp word ptr [bp + 6], 5","je 0x771f72","jmp 0x771ff7",
        "push ax","push ds","push di","mov di, 0x1000","mov ds, di","mov di, 0x4e",
        "xor ax, ax","mov al, byte ptr [di + 0xe]","pop di","pop ds","cmp ax, 0xb",
        "pop ax","je 0x771fa3","cmp byte ptr es:[0x5d], 3","je 0x771fcd",
        "cmp byte ptr es:[0x5d], 0","je 0x771fa3","test word ptr es:[0x68], 0x400",
        "je 0x771fcd"])
    exact(source,0x771FE3,["push 0xff0","push 0x71f0","push 0xeea",
        "lcall 0x4fff, 0x980","add sp, 6","jmp 0x772048"])
    # All mode-word values in both producer branches; no assumed unsigned
    # saturation, and no claim that other mode values are normal gameplay.
    producer_modes={}
    for boss in (False,True):
        producer_modes[str(boss)]=[mode for mode in range(65536)
            if ((mode+(2 if boss else 0)) & 65535)==2]
    need(producer_modes=={"False":[2],"True":[0]},"complete 16-bit producer preimages")
    ordinary_stages=[stage for stage in range(256) if (2 if stage==7 else 0)==2]
    need(ordinary_stages==[7],"single-player root5 requires boss stage7")
    hp_truth=[s16(hp)<=0 for hp in range(65536)]
    need(sum(hp_truth)==32769 and hp_truth[0] and not hp_truth[1],"signed opponent HP branch")
    return dict(producer="740C97..740CB0: SRAM03D0=(SRAM0050+(stage005C==7?2:0))&FFFF",
        fixed_rom_direct_callers={f"{at:06X}":arg for at,arg in direct_calls.items()},
        caller_inventory_limit="Complete literal far-call encoding population in700000..7FFFFF, not exclusion of indirect/constructed calls.",
        producer_mode_preimages=producer_modes,singleplayer_mode=0,singleplayer_required_stage=7,
        source_root5_call="7417F3",other_actor_handle="SRAM065E",other_actor_field="DS0C00:handle+0050",
        other_actor_condition="signed16 HP <= 0",signed_hp_values_taking_branch=sum(hp_truth),
        priority="If first actor HP==0 and +A4==003E, earlier root4 call wins instead of root5.",
        source_timer_call="74180F: expired signed timer03CE calls root0, not root5",
        root5_scene_predicate="stage!=11 && (difficulty==3 || (difficulty!=0 && (progress&0400)==0))",
        shoot_task_allocation="771FE3..771FF4 allocates 71F0:0EEA / stack0FF0 through 4FFF:0980",
        ordinary_first_bout="Stage8 timer win or loss is insufficient. The normal-input route must reach stage7 and deplete the opponent HP before evaluating the root5 predicate.",
        reachability_limit="Static exact caller/producer proof; no campaign win or Shoot execution is inferred.")


def hard_options_route(source):
    title=0x77FFB0
    need(struct.unpack_from("<H",source,title+0x9A7)[0]==0x9C1,"root menu table")
    need(struct.unpack_from("<4H",source,title+0x9C1+3*8)==(0xFFFF,2,0,0),"root row2 terminal transition2")
    need(source[title+0x94E:title+0x953]==bytes([1,2,3,4,0]),"root down navigation")
    need(source[0x74FA30+3*6+2]==14,"title transition2 selects mode14")
    need(struct.unpack_from("<HH",source,0x74FACC+14*12)==(0,0x7564),"Options initializer")
    exact(source,0x775B5A,["push 0x1300","push 0x7564","push 0x13fe","lcall 0x4fff, 0x980",
        "add sp, 6","add ax, 0x10","mov ds, dx","mov si, ax","mov word ptr [si], 1"])
    exact(source,0x776AC7,["mov di, 0x1000","mov es, di","mov di, 0x4e","xor bx, bx",
        "mov bl, byte ptr es:[di + 0xf]","test cx, 8","jne 0x776ae4","test cx, 2",
        "jne 0x776aec","jmp 0x776b48","or bx, bx","je 0x776b05","dec bx",
        "jmp 0x776af2","cmp bx, 3","je 0x776b05","inc bx"])
    exact(source,0x776B05,["mov byte ptr es:[di + 0xf], bl"])
    exact(source,0x7764DA,["mov di, 0x300","mov es, di","mov di, 0x112",
        "and word ptr es:[di], 0xfffc","mov word ptr es:[di + 2], ax",
        "mov cx, word ptr es:[di + 6]","test ax, 0x80","jne 0x776541"])
    return dict(title_ready_callback="7FFB:067B",root_menu_options_row=2,options_mode=14,
        options_cursor="0300:0118 = RAM3118",difficulty_row=1,difficulty="1000:005D",
        right_input=2,right_handler="776AEC..776B05 increments up to3",exit_input=128,
        observation_acceptance="Options mode14 seen, difficulty3 seen, then ordinary battle mode7 still difficulty3",
        mutation="joypad only; no emulator guest-memory/register writes")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("wsc15",type=pathlib.Path);parser.add_argument("gba",type=pathlib.Path)
    parser.add_argument("candidate",type=pathlib.Path);parser.add_argument("--output",required=True,type=pathlib.Path)
    args=parser.parse_args()
    need(all(p.suffix.lower() != ".sav" for p in (args.wsc15,args.gba,args.candidate)),"save inputs forbidden")
    source,gba,candidate=[p.read_bytes() for p in (args.wsc15,args.gba,args.candidate)]
    need(sha(source)==SOURCE_SHA and sha(gba)==GBA_SHA,"immutable originals")
    need(sha(candidate)=="5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46","exact v65 baseline")
    script=(ROOT/"tools/bizhawk_probe_wsc_shoot_lifetime.lua").read_text(encoding="utf-8")
    report=dict(source_sha256=sha(source),gba_sha256=sha(gba),candidate_sha256=sha(candidate),
        consumers=consumers(source,gba,candidate),spatial=spatial(source),observer=observer_contract(source,script),
        blank_tile_initializer=blank_tile_initializer(source),
        actual_shoot_caller=actual_shoot_caller(source),
        hard_options_route=hard_options_route(source),
        ROM_modified=False,source_runtime_or_full_route_claim=False)
    # Break the actual LOOP step and a mapped timer owner; both must be rejected.
    bad=bytearray(source);bad[0x749803]^=1
    try: spatial(bytes(bad))
    except ValueError: pass
    else: raise ValueError("negative spatial control accepted")
    bad=bytearray(candidate);bad[0x36EC04]^=1
    try: consumers(source,gba,bytes(bad))
    except ValueError: pass
    else: raise ValueError("negative timer-owner control accepted")
    bad=bytearray(source);bad[0x740C9E]^=1
    try: actual_shoot_caller(bytes(bad))
    except ValueError: pass
    else: raise ValueError("negative actual-caller stage control accepted")
    bad=bytearray(source);bad[0x776AEE]^=1
    try: hard_options_route(bytes(bad))
    except ValueError: pass
    else: raise ValueError("negative hard-difficulty cap control accepted")
    report["negative_controls_rejected"]=4
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PASS: 13 direct operands, 3 actual native timer pairs, 2^32 source spatial inputs; no route closure claim")


if __name__=="__main__":
    main()

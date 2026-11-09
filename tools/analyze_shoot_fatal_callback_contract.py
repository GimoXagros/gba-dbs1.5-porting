#!/usr/bin/env python3
"""Bound the existing fatal adapter and its real retail return consumers."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16

BASE = 0x08000000
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOK, ADAPTER, TAIL = 0x36E5EC, 0x5CD960, 0x36E604
PINS = (
    (0x36E348, 0x36E69C, 'B6F0836A05992DD2AF528468F4A301AE6E8DC6566C5FCFD972429E705FBCC9F6'),
    (0x36F558, 0x36F7A4, '32612D8C26FC8EF02A4124B2B3713AA2553EAB4B31FC05CFDBA3A25AAF2A888B'),
    (0x36A69C, 0x36A6AC, '1B529220D342C8736CFBB06BEB80DFD2F3D819A6D79DB94CF0BA7EBA9EB4A68B'),
    (0x353FEC, 0x353FFC, '3440BA9A0A8FEBBA2E6A3E520C99C781F880EC1900A1A4CC65D7D63864759AC3'),
    (ADAPTER, ADAPTER+64, '49143F7C3B0DE43EE6E190BEDDD57921964C1054736DD5167523F9820545E246'),
    (0x5BDD00, 0x5BDDA4, '16C9E05B22A9A595836168FD5298D7FE7247BFFE742383468C47EAE919F23ADB'),
    (0x5BF204, 0x5BF230, 'CF607E167C38BCC3ABDCB10EC3CDBBDDA6E176E62888A172D698E0B1ED111BD6'),
)
FATAL_SOURCE = bytes.fromhex(
    '26803E5C000B744D26803E5D0003742B26803E5D0000740926F70668000004741A'
    '8BC7C7059A64C7450290408B7D1CC7050E56C745029040E93100'
    '8BC7C7059A64C7450290408B7D1CC7053657C745029040E91700'
    '8BC7C705B17AC7450290408B7D1CC7058D7DC74502904007')
ATTACKER_TARGETS = (0x0836F558,)*3 + (
    0x0836F648, 0x0836F64C, 0x0836F6C4, 0x0836F6C8,
    0x0836F72C, 0x0836F730, 0x0836F734, 0x0836F738,
    0x0836F74C, 0x0836F7A0, 0x0836E484)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u(data, at):
    return struct.unpack_from('<I', data, at)[0]


def branch_target(at, word):
    delta = word & 0xFFFFFF
    if delta & 0x800000:
        delta -= 0x1000000
    return at + 8 + delta*4


def callers(data):
    """Only the two exact entries/interior joins affected by this one-word hook."""
    result = []
    for at in range(0, len(data)-3, 4):
        word = u(data, at)
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            target = branch_target(at, word)
            if target in (0x36E348, ADAPTER) or HOOK <= target < TAIL:
                result.append([at, target])
    pointers = {}
    for target in (BASE+0x36E348, BASE+ADAPTER):
        positions, cursor = [], 0
        signature = struct.pack('<I', target)
        while True:
            cursor = data.find(signature, cursor)
            if cursor < 0:
                break
            positions.append(cursor)
            cursor += 1
        pointers[f'{target:08X}'] = positions
    need(result == [[0x353FEC, 0x36E348], [0x5CD990, 0x36E5F0]],
         'only retained collision caller and resident legacy continuation before hookup')
    need(not any(pointers.values()), 'no pointer caller to collision entry or unused adapter')
    return dict(aligned_direct_transfers=result, exact_all_byte_pointers=pointers,
                scope='Exact affected entry/join census; existing resident ownership proof reused')


def flags_dead(data):
    """Track only incoming NZCV through this bounded common-tail return join.

    TST/ORRS do NOT kill incoming V, or C with an unshifted operand. The walk
    stops once all incoming bits are dead; it does not audit the whole graph.
    """
    N, Z, C, V = 1, 2, 4, 8
    conditions = (Z,Z,C,C,N,N,V,V,C|Z,C|Z,N|V,N|V,N|Z|V,N|Z|V,0,0)
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    pending, seen, kills, calls = [(BASE+TAIL, 15)], set(), set(), set()
    while pending:
        address, live = pending.pop()
        if not live or (address, live) in seen:
            continue
        need(len(seen) < 150, 'bounded fatal-join flag lifetime')
        seen.add((address, live))
        at = address-BASE
        word = u(data, at)
        ins = next(decoder.disasm(data[at:at+4], address), None)
        need(ins is not None and ins.size == 4, 'actual join instruction')
        condition = word >> 28
        need(not conditions[condition] & live, f'incoming flags used at {address:08X}')
        # No hidden arithmetic carry input or CPSR-to-register capture is allowed.
        is_bx = word & 0x0FFFFFF0 == 0x012FFF10
        if word & 0x0C000000 == 0 and word & 0x0E000090 != 0x00000090 and not is_bx:
            operation = (word >> 21) & 15
            need(operation not in (5,6,7) or not live & C, 'incoming carry arithmetic')
            register_operand = not word & 0x02000000
            if register_operand:
                need(not (word & 0x10), 'no register-controlled shift in bounded join')
                rrx = ((word >> 5) & 3) == 3 and ((word >> 7) & 31) == 0
                need(not rrx or not live & C, 'incoming carry in RRX')
            if word & 0x00100000 or operation in (8,9,10,11):
                if operation in (2,3,4,5,6,7,10,11):
                    live = 0
                else:
                    live &= ~(N|Z)
                    rotate = (word >> 8) & 15
                    shift = (word >> 7) & 31
                    kind = (word >> 5) & 3
                    if (not register_operand and rotate) or (register_operand and (shift or kind)):
                        live &= ~C
        need(word & 0x0FFF0FFF != 0x010F0000, 'no incoming CPSR capture')
        if not live:
            kills.add(address)
            continue
        if address == 0x0836E448:
            need(word == 0xE12FFF19, 'retained attacker dispatch BX r9')
            pending.extend((target, live) for target in ATTACKER_TARGETS)
        elif word & 0x0FFFFFFF == 0x012FFF1E:
            need(address == 0x0836E488, 'only shared return before flag death')
            pending.append((0x08353FF0, live))
        elif word & 0x0E000000 == 0x0A000000:
            target = BASE+branch_target(at, word)
            if word & 0x01000000:
                need(address == 0x0836F6FC and target == 0x0836A69C,
                     'only typed freeze import before full NZCV death')
                calls.add((address,target))
            pending.append((target,live))
            if condition != 14:
                pending.append((address+4,live))
        else:
            pending.append((address+4,live))
    need({0x08353FF4,0x0836A6A8} <= kills, 'return caller and freeze-entry arithmetic kill')
    return dict(incoming_bits='NZCV', states=len(seen),
                complete_kill_sites=sorted(kills), imported_prefixes=sorted(calls),
                attacker_entries=len(ATTACKER_TARGETS),
                source_of_return='only collision caller08353FEC, flags killed by08353FF4 SUBS',
                first_logical_test_not_treated_as_full_kill=True)


def proof(before, gba, source):
    need(sha(gba)==GBA and sha(source)==SOURCE, 'exact immutable originals')
    need(source[0x760197:0x760204]==FATAL_SOURCE, 'complete source fatal selection')
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    rows = list(decoder.disasm(FATAL_SOURCE,0x760197))
    need(sum(i.size for i in rows)==len(FATAL_SOURCE), 'complete source branch decode')
    need([(i.address,i.op_str) for i in rows if i.mnemonic=='je']==[
        (0x76019D,'0x7601ec'),(0x7601A5,'0x7601d2'),
        (0x7601AD,'0x7601b8'),(0x7601B6,'0x7601d2')], 'source branch destinations and priority')
    for a,z,digest in PINS:
        need(sha(before[a:z])==digest, f'frozen existing consumer {a:X}')
        if a < 0x400000:
            need(before[a:z]==gba[a:z], 'retail consumer unchanged')
    need(u(before,HOOK)==0xE1A00005, 'unhooked displaced MOV r0,r5')
    need(u(gba,0xB9F28)+14==0x0300231E, 'retail stage-field literal owner')
    need(struct.unpack_from('<14I',before,0x36E44C)==ATTACKER_TARGETS,
         'complete retained attacker dispatch')
    need(struct.unpack_from('<3I',before,ADAPTER+52)==(0x03002310,0x085BDD00,0x085BF204),
         'existing adapter stage and repaired fatal targets')
    need(struct.unpack_from('<2I',before,0x36E68C)==(0x08371E74,0x08370BF0),
         'unchanged retail non11 callback pair')
    inventory=callers(before)
    lifetime=flags_dead(before)
    return dict(source_stage11_pair=['4090:7AB1','4090:7D8D'],
                native_stage11_pair=[0x085BDD00,0x085BF204],
                non11_source_selection='649A+5736 for difficulty3 or nonzero difficulty/progress0400 clear; otherwise649A+560E',
                non11_scope='Exact retained retail pair only; broader source non11 table not newly implemented',
                source_stage11_precedes_difficulty_and_progress=True,
                pre_hook_callers=inventory, incoming_flags_dead=lifetime,
                resident_adapter_sha256=PINS[4][2],
                no_new_function_or_reservation=True, external_entry_opened=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('gba',type=Path)
    parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    need(not args.output.exists(),'fresh contract output')
    result=proof(args.input.read_bytes(),args.gba.read_bytes(),args.source.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
    print('PASS existing fatal adapter and bounded incoming-flags lifetime')


if __name__=='__main__':main()

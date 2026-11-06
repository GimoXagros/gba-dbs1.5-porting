#!/usr/bin/env python3
"""Independently decode the controller adapter, without a builder import."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

BASE = 0x085C6500
PINS = (
    (0x5C6000, 180, "50B090CE223B5B5321F88FD96456B0EFAD263B114E4ED12F7AB77CBFDD4830CF"),
    (0x5C6200, 76, "75240FDF5E47873B21990DDC7568541B14FC458AE9B7D4040099FDDE9A962848"),
    (0x5C6400, 64, "DDFDCEFE5A45221AF27E17F729FD8FCC167418FADBF362F52D5CF4995BD18F94"),
    (0x5CB000, 6432, "50F925198CD5BF6AA23DDC8A94778B24A085BCB292B1B7EC856268E4ACA982C3"),
)
REGS = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
PRODUCTION_INPUT = "9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738"
RESIDENT_VERIFIER = "7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D"
# Pin the reviewed OPEN_DOMAIN obligations, not a completed player-domain claim.
# Production here connects only the internal chain while external entry is closed.
DOMAIN_PROOFS = (("shoot-controller-domain.json",
    "5DBB2620877D5ADEE92338B87B285610914CA07F2C484077846A602EDA707B46"),)
BOUNDARY = 0x5C0A00
CALLERS = (0x5C0274, 0x5C0870)
CALLER_PINS = (
    (0x5C0000, 660, "8E10BE91ED1329ED0A0755936675ED1986951060D79850CFB0E3F4F7805FFF7E"),
    (0x5C0800, 164, "1B0D837929456D09D826F85E240E41975118DC1611962EB57B3C55578798B6DE"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def demand(value: bool, name: str) -> None:
    if not value:
        raise ValueError(name)


def code(blob: bytes) -> None:
    demand(len(blob) == 44, "adapter size")
    ins = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(blob[:32], BASE))
    actual = [i.mnemonic + " " + i.op_str for i in ins]
    demand(actual == ["push " + REGS, "bl #0x85c6000", "ldr r1, [pc, #0x10]",
                      "ldr r2, [pc, #0x10]", "ldr r3, [pc, #0x10]", "bl #0x85c6200",
                      "pop " + REGS, "bx lr"], "complete adapter instructions and call order")
    demand(struct.unpack_from("<3I", blob, 32) == (0x085CB000, 0x085CB970, 0x085CBD80), "real callback bindings")


def verify(before: bytes, blob: bytes) -> dict:
    code(blob)
    for start, size, expected in PINS:
        demand(sha(before[start:start + size]) == expected, "resident dependency")
    demand(before[0x5C0A00:0x5C0A04] == bytes.fromhex("1EFF2FE1"), "predecessor boundary")
    demand(before[0x5C6500:0x5C652C] == b"\xff" * 44, "adapter blank bytes")
    pointer_count = branch_count = 0
    for offset in range(len(before) - 3):
        value = struct.unpack_from("<I", before, offset)[0]
        if BASE <= value < BASE + 44:
            pointer_count += 1
    for offset in range(0, len(before) - 3, 4):
        value = struct.unpack_from("<I", before, offset)[0]
        if value >> 28 == 15 or value & 0x0E000000 != 0x0A000000:
            continue
        displacement = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
        target = 0x08000000 + offset + 8 + displacement * 4
        if BASE <= target < BASE + 44:
            branch_count += 1
    demand(pointer_count == branch_count == 0, "independent inbound scan")
    rejected = []
    for label, offset, value in (("apply before select", 4, 0xEBFFFF3D), ("wrong 810D callback", 32, 0x085CB080),
                                 ("swap linked callback families", 36, 0x085CBD80), ("lost preserved r4", 24, 0xE8BD5FEF)):
        bad = bytearray(blob)
        struct.pack_into("<I", bad, offset, value)
        try:
            code(bad)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("accepted " + label)
    return {"instructions": 8, "code_bytes": 32, "literal_bytes": 12, "adapter_sha256": sha(blob),
            "RNG_contract": "SELECT zero calls on forced +76 path, exactly one otherwise; APPLY makes no RNG call",
            "same_update": "only three literal loads occur between SELECT and APPLY; no game update call",
            "argument_order": {"r1": "810D", "r2": "8AB8", "r3": "8CDD", "r4": "same current object"},
            "registers_and_SP": "all r0-r12 restored; balanced56-byte local frame", "negative_cases": rejected,
            "incoming_pointers": pointer_count, "incoming_branches": branch_count}


def production_structure(before: bytes, after: bytes) -> None:
    demand(len(before) == len(after) == 0x800000, "complete production image size")
    demand(before[BOUNDARY:BOUNDARY + 4] == bytes.fromhex("1EFF2FE1"), "actual closed boundary")
    # Independently derive the ARM unconditional B encoding, without Keystone
    # or a builder's expected-byte manifest.
    expected = 0xEA000000 | ((BASE - (0x08000000 + BOUNDARY + 8)) // 4 & 0xFFFFFF)
    demand(struct.unpack_from('<I', after, BOUNDARY)[0] == expected,
           "one unconditional tail B to actual resident adapter; no BL")
    restored = bytearray(after)
    restored[BOUNDARY:BOUNDARY + 4] = before[BOUNDARY:BOUNDARY + 4]
    demand(restored == before, "whole ROM inverse outside sole boundary word")
    code(after[0x5C6500:0x5C652C])
    for at, size, digest in PINS + CALLER_PINS:
        demand(sha(after[at:at + size]) == digest, "actual retained dependency or caller")
    for at in CALLERS:
        ins = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(after[at:at + 8], 0x08000000 + at))
        demand([f'{i.mnemonic} {i.op_str}' for i in ins] ==
               ['bl #0x85c0a00', 'bl #0x8012600'], "actual BL caller and following RNG continuation")


def bridge_execution(before: bytes, after: bytes, resident, table: bytes) -> int:
    cases = 0
    for caller in CALLERS:
        for seed in range(4):
            for forced, x, y, flag in ((1,0xE00,0x1900,0), (0,0x4FF,0,0),
                                      (0,0x500,0xBFF,0), (0,0x900,0xBFF,0x40),
                                      (0,0x901,0xC00,0)):
                # Reuse the frozen semantic oracle for these partitions.
                resident.controller_case(after,table,forced,x,y,seed,seed,flag)
                direct, linked = resident.Arm(before,seed,rng=seed), resident.Arm(after,seed,rng=seed)
                ret = 0x08000000 + caller + 4
                for arm in (direct, linked):
                    arm.r[4] = 0x02011000
                    for address,value,size in ((0x02011018,0x02012000,4),
                        (0x02011028,0x02013000,4),(0x02011064,0xFEDC,2),
                        (0x02011076,forced,2),(0x02012034,x,2),(0x02012036,y,2),
                        (0x0300231F,seed,1),(0x0300450A,flag,2)):
                        arm.put(address,value,size)
                direct.r[14] = ret
                direct.run(BASE,{ret})
                end = linked.run(0x08000000+caller,{ret})
                demand(end == ret and linked.r[:15] == direct.r[:15],
                       "actual caller BL -> tail bridge -> adapter returns to BL+4 with registers/SP intact")
                demand(linked.mem == direct.mem and linked.writes == direct.writes,
                       "bridge introduces no extra state or stack effects")
                demand(linked.rng_calls == direct.rng_calls and linked.calls[1:] == direct.calls,
                       "bridge preserves RNG population and exact SELECT/APPLY calls")
                demand(linked.calls[0][1] == 0x085C0A00, "actual caller enters declared boundary")
                cases += 1
    return cases


def closed_route_bytes(after: bytes, gba: bytes) -> None:
    for start, end in ((0x33FCCC,0x33FDC0),(0x0B9E48,0x0B9E78),(0x34059C,0x3407F4)):
        demand(after[start:end] == gba[start:end], "retail case5/progress/callback route remains unchanged")
    demand(after[0x5C9900:0x5C9B00] == b'\xff'*0x200,
           "external scene selector and progress producer remain uninstalled")


def closed_route_references(before: bytes, after: bytes, resident) -> dict:
    def external(data):
        return [row for row in resident.inbound(data)
                if not any(a <= row[1] < z for a,z in resident.SPANS)]
    previous, current = external(before), external(after)
    demand(previous == [], "frozen resident graph has no incoming caller references")
    demand(current == [('ARM branch',BOUNDARY,BASE)],
           "only new incoming resident reference is the declared internal tail bridge")
    return dict(before_external_references=previous,after_external_references=current,
        reference_scope='Frozen resident router/adapter spans, all alignments and ROM mirrors; existing internal self-references retained')


def verify_production_core(before: bytes, after: bytes, gba: bytes, source: bytes) -> dict:
    demand(sha(before) == PRODUCTION_INPUT, "exact v68 production predecessor")
    demand(sha((ROOT/'tools/verify_shoot_caller_resident.py').read_bytes()) == RESIDENT_VERIFIER,
           "frozen resident semantic verifier")
    import verify_shoot_caller_resident as resident
    demand((sha(gba),sha(source)) == resident.IDENTITIES[1:], "immutable original identities")
    production_structure(before,after)
    closed_route_bytes(after,gba)
    route_references=closed_route_references(before,after,resident)
    table = resident.source_contract(gba,source,after)
    resident.code_contract(after)
    executed = bridge_execution(before,after,resident,table)
    rejected=[]
    for label,at,value in (("wrong target",BOUNDARY,0xEA0016BF),
        ("BL instead of tail B",BOUNDARY,0xEB0016BE),
        ("outside boundary mutation",BOUNDARY+4,0),
        ("resident dependency mutation",0x5C6000,0),
        ("actual caller mutation",CALLERS[0],0)):
        bad=bytearray(after)
        struct.pack_into('<I',bad,at,value)
        try: production_structure(before,bad)
        except ValueError: rejected.append(label)
        else: raise ValueError('accepted '+label)
    semantic_rejected=[]
    for label,value in (("BL loses caller return",0xEB0016BE),
                        ("interior target skips saved-register frame",0xEA0016BF)):
        bad=bytearray(after)
        struct.pack_into('<I',bad,BOUNDARY,value)
        # Bypass hashes, the inverse, and exact instruction checking so the
        # actual composed return/register execution must reject these defects.
        try: bridge_execution(before,bad,resident,table)
        except ValueError: semantic_rejected.append(label)
        else: raise ValueError('semantic bridge accepted '+label)
    route_rejected=[]
    for label,at in (("external case5 hook changed",0x33FD04),
                     ("external progress hook changed",0x0B9E68),
                     ("external selector installed",0x5C9900)):
        bad=bytearray(after); bad[at]^=1
        try: closed_route_bytes(bad,gba)
        except ValueError: route_rejected.append(label)
        else: raise ValueError('closed route accepted '+label)
    return dict(schema=1,kind='independent-shoot-controller-bridge',status='PASS',
        input_sha256=sha(before),output_sha256=sha(after),source_sha256=sha(source),gba_sha256=sha(gba),
        declared_bytes=4,changed_bytes=sum(x!=y for x,y in zip(before,after,strict=True)),
        boundary=BOUNDARY,target=BASE,boundary_before=before[BOUNDARY:BOUNDARY+4].hex().upper(),
        boundary_after=after[BOUNDARY:BOUNDARY+4].hex().upper(),whole_ROM_inverse=True,
        actual_callers=list(CALLERS),actual_caller_return_cases=executed,
        frozen_resident_semantics_sha256=RESIDENT_VERIFIER,negative_controls=rejected,
        semantic_negative_controls=semantic_rejected,
        closed_route=route_references,closed_route_negative_controls=route_rejected,
        producer_domain_closed=False,external_scene_route_closed=True,
        external_route_changed=False,runtime_executed=False)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("before", type=pathlib.Path)
    p.add_argument("draft", type=pathlib.Path)
    p.add_argument("--output", type=pathlib.Path)
    p.add_argument("--production", action="store_true", help="second positional is the connected ROM")
    p.add_argument("--gba", type=pathlib.Path)
    p.add_argument("--wsc15", type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path)
    p.add_argument("--domain-proof", type=pathlib.Path, action="append", default=[])
    args = p.parse_args()
    if args.production:
        demand(DOMAIN_PROOFS is not None, "reviewed open-domain obligations report remains pending")
        demand(all((args.gba,args.wsc15,args.manifest,args.output)), "production originals/manifest/output required")
        inputs=[args.before,args.draft,args.gba,args.wsc15,args.manifest,*args.domain_proof]
        demand(all(p.suffix.lower() != '.sav' for p in inputs), "save inputs forbidden before reads")
        demand(args.before.suffix.lower()==args.draft.suffix.lower()==args.gba.suffix.lower()=='.gba'
               and args.wsc15.suffix.lower()=='.wsc', "production ROM extensions")
        demand(args.output.suffix.lower()=='.json' and args.output.resolve() not in {p.resolve() for p in inputs},
               "distinct JSON verification output")
        actual_domains=tuple((p.name,sha(p.read_bytes())) for p in args.domain_proof)
        demand(actual_domains==DOMAIN_PROOFS, "exact reviewed open-domain obligations dependencies")
        for path in args.domain_proof:
            obligations=json.loads(path.read_text(encoding='utf8'))
            demand(obligations.get('status') == 'OPEN_DOMAIN'
                   and obligations.get('complete_controller_input_domain') is False
                   and obligations.get('external_scene_entry_authorized') is False
                   and obligations.get('candidate_sha256') == PRODUCTION_INPUT
                   and obligations.get('source_sha256') == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7',
                   "internal-only integration must retain explicit unresolved producer domain")
        before,after,gba,source=(p.read_bytes() for p in inputs[:4])
        result=verify_production_core(before,after,gba,source)
        manifest=json.loads(args.manifest.read_text(encoding='utf8'))
        demand(manifest['kind'] in ('shoot-controller-adapter','shoot-controller-bridge'), "production manifest kind")
        for field in ('input_sha256','output_sha256','changed_bytes'):
            demand(manifest[field]==result[field], 'independently derived manifest '+field)
        demand(manifest['boundary_changed'] is True, "production boundary declaration")
        result.update(producer_domain_dependencies=actual_domains,
            manifest_sha256=sha(args.manifest.read_bytes()),
            scope='Internal controller boundary connected; external scene route remains CLOSED; player XY and terminal lifetime obligations remain OPEN; no actual Shoot gameplay claim')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
        print('[verify-shoot-controller-adapter] production bridge PASS; external route unchanged')
        return 0
    before = args.before.read_bytes()
    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    demand(draft["kind"] == "shoot-controller-adapter-draft" and draft["boundary_changed"] is False, "draft-only state")
    demand(sha(before) == draft["input_sha256"] == "223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E", "draft predecessor identity")
    result = {"schema": 1, "kind": "independent-controller-adapter-draft", "proof": verify(before, bytes.fromhex(draft["adapter_hex"])),
              "boundary_changed": False, "ROM_emitted": False,
              "gate": "full initializer/object lifetime and final predecessor pin precede boundary installation"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-shoot-controller-adapter] draft PASS; boundary unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

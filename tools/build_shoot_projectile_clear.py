#!/usr/bin/env python3
"""Isolated resident93E7 clear extension; external Shoot entry remains closed.

Only the retained normal callback domain has the no-side1-reload proof. No P2
companion projection, new RAM, shared-pixel emulation or blanket lifetime claim.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
import verify_shoot_caller_resident as resident
from verify_shoot_static_companion_clear import Machine
import analyze_shoot_p2_reload_eligibility as reload_proof
import analyze_shoot_6d_alias_lifetime as alias_proof

BASE = 0x08000000
INPUT = '35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
PROOF = '2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990'
FIRST, LIMIT = 0x6FF240, 0x6FF28C
OWNER, RENDER, ORIGINAL = 0x086FE800, 0x086FEA00, 0x086FEA50
P0 = 0x085DB300
DEPENDENCIES = {
    'verify_shoot_caller_resident.py': '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D',
    'verify_shoot_static_companion_clear.py': 'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
    'verify_shoot_attack_dispatch.py': '695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698',
    'analyze_shoot_p2_reload_eligibility.py': 'CCCAC31E2DC6A431D6747681CB3A212C84801081FC17640D6D00BE0392BD6CC4',
    'analyze_shoot_6d_alias_lifetime.py': 'DA8E07CA76C1F2A29C8DDB735126BF83409758315B56300B9FFE759A294DAC6E',
}
# Existing code/capture/preload hooks are immutable; only their renderer table
# pointer is intentionally replaced. These are the six remaining v71 writes.
RETAINED = (
    ('owner', 0x6FE800, 136, '821A51F9E0EC7B73CE4815B19963DA3A2443556F3AE38D8672E7932CECF1E843'),
    ('capture', 0x6FE900, 64, '181A42BD58329B87DF6D93B89D815AF10819E450AFAAB13B865EBD56D6A7297D'),
    ('renderer', 0x6FEA00, 648, 'A9C9CF70960F9693CA77531F0CC5DA6A9A974A5A5764D47DEC06CEE9BC032B81'),
    ('expiration', 0x6FEE00, 124, '23E691927EFDAE7CE3253E798E2050E7313F3F1CE37B01F94EB030D169B83D12'),
    ('capture_hook', 0x5CD314, 4, 'FB12DE0519E32CF13DE0FADFD794F7D2921CB64DD351589261183B90AE732C03'),
    ('preload_hook', 0x35346C, 4, '811BA60A4BD1683780F76DBA0C4B4F3908E62983F6ACEC624E9F2B9C78B6E9C6'),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def asm(text, raw):
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, BASE + raw)[0])


def selector():
    return asm(f'''
      ldrh r0, [r5, #0x14]
      cmp r0, #0x6D
      bne {RENDER:#x}
      ldrh r0, [r5, #8]
      tst r0, #2
      bne {RENDER:#x}
      ldr r0, [r5, #0x48]
      ldr r1, p0
      cmp r0, r1
      bne {RENDER:#x}
      push {{r9}}
      mov r9, #0
      bl {OWNER:#x}
      cmp r0, #0
      ldrhne r9, [r0, #0x52]
      cmp r9, #0
      subne r9, r9, #36
      b {ORIGINAL:#x}
    p0: .word {P0:#x}
    ''', FIRST)


def retained_contract(data):
    for name, at, size, digest in RETAINED:
        need(sha(data[at:at+size]) == digest, 'frozen v71 ' + name)
    need(resident.decoded(data, 0x6FEA50, 8) ==
         ['ldr ip, [pc, #0x190]', 'ldr r0, [pc, #0x190]'],
         'exact original renderer entry after mask recognition')
    need(resident.decoded(data, 0x6FEBDC, 12) ==
         ['pop {sb}', 'pop {r0, r1, r2, r3, r4, r5, lr}', 'bx lr'],
         'exact single R9 plus dispatcher-frame epilogue')


def writes():
    blob = selector()
    need(len(blob) == LIMIT-FIRST, 'exact76-byte selector')
    return [('projectile_selector', FIRST, blob),
            ('renderer_pointer', 0x12C50, struct.pack('<I', BASE+FIRST))]


def validate(before, after):
    need(len(before) == len(after), 'unchanged ROM length')
    inverse = bytearray(after)
    for name, at, blob in writes():
        need(after[at:at+len(blob)] == blob, 'exact ' + name)
        inverse[at:at+len(blob)] = before[at:at+len(blob)]
    need(bytes(inverse) == before and sha(inverse) == INPUT,
         'whole-ROM inverse to exact v71; no undeclared write')
    retained_contract(after)


def selector_semantics(data):
    """Execute actual selector bytes with the frozen owner's ABI modeled.

    Independent QA must execute the real owner and complete renderer as well.
    These checks deliberately do not compare selector bytes with the builder.
    """
    present, scene = 0x0201F000, 0x02010018
    count = 0
    masks = [0] + [first | (bits << 8) for first in range(74, 129, 2)
                  for bits in range(16)]
    cases = [(0x6D, 0, P0, True, mask) for mask in masks]
    cases += list(itertools.product((0x49, 0x6C, 0x6D, 0x6E, 0x137),
                 (0, 1, 2, 3, 0x2000), (P0, P0+4, 0x085DB400),
                 (False, True), (0, 0xF6E)))
    for tile_base, flags, p0, has_owner, mask in cases:
        m = Machine(data, count, ((count % 16) << 28) | 0x10)
        m.r[5] = present
        m.put(present+0x14, tile_base, 2)
        m.put(present+8, flags, 2)
        m.put(present+0x48, p0)
        if has_owner:
            m.put(scene+0x52, mask, 2)
        m.services[OWNER] = lambda cpu: cpu.r.__setitem__(0, scene if has_owner else 0)
        original = m.r[:]
        end = m.run(BASE+FIRST, {ORIGINAL, RENDER}, max_steps=32)
        match = tile_base == 0x6D and not flags & 2 and p0 == P0
        need(end == (ORIGINAL if match else RENDER), 'executed recognition/tail destination')
        need(all(m.r[r] == original[r] for r in (2, 3, 4, 5, 6, 7, 8, 10, 11, 12)),
             'selector preserves required registers')
        need(len(m.calls) == int(match), 'owner called only for exact93E7')
        need(m.r[13] == original[13] - (4 if match else 0), 'exactly one matched R9 push')
        expected = mask-36 if has_owner and mask else 0
        need(m.r[9] == (expected if match else original[9]), 'executed mask translation/zero guard')
        need(m.writes == ([(original[13]-4, original[9], 4)] if match else []),
             'stack-only selector write set')
        if not match:
            need(m.r[14] == original[14], 'unmatched LR unchanged')
        count += 1
    algebra = 0
    for first, bits, tile in itertools.product(range(74, 129, 2), range(16), range(24)):
        logical = 109 + tile
        mask = (first | bits << 8) - 36
        delta = 73 + tile - (mask & 255)
        actual = 0 <= delta <= 3 and bool(mask & (0x100 << delta))
        expected = 0 <= logical-first <= 3 and bool(bits & (1 << (logical-first)))
        need(actual == expected, 'all captured masks/93E7 tiles match logical clear')
        algebra += 1
    return dict(actual_selector_cases=count, logical_tile_cases=algebra,
                owner_service_modeled=True, full_renderer_executed=False)


def build(before, source, proof_bytes, lower_graph):
    need(sha(before) == INPUT and sha(source) == SOURCE, 'exact v71/original source inputs')
    for name, digest in DEPENDENCIES.items():
        need(sha((ROOT/'tools'/name).read_bytes()) == digest, 'frozen dependency ' + name)
    need(sha(proof_bytes) == PROOF, 'exact reviewed bounded reload composition report')
    proof = json.loads(proof_bytes)
    need(proof['status'] == 'BOUNDED_P2_NO_RELOAD_COMPOSITION_PASS' and
         proof['composition']['bounded_post197A_no_side1_companion_reload'] and
         proof['composition']['resident_93E7_extension_supported'] and
         not proof['full_post_clear_reload_exclusion_approved'], 'bounded proof scope retained')
    # Re-run the source contracts, not just the report booleans.
    live_proof = reload_proof.proof(source, lower_graph)
    need(all(live_proof[key] == value for key, value in proof.items()
             if key != 'negative_controls_rejected'), 'source recomputes reviewed composition')
    aliases = alias_proof.proof(source, before)
    need(not aliases['event_or_child_creation_restores_pixels'], 'static events cannot restore tiles')
    retained_contract(before)
    need(struct.unpack_from('<I', before, 0x12C50)[0] == RENDER, 'exact displaced renderer pointer')
    need(before[FIRST:LIMIT] == b'\xFF'*(LIMIT-FIRST), 'entire76-byte reservation erased')
    scanner = types.FunctionType(resident.inbound.__code__,
        dict(resident.__dict__, SPANS=((FIRST, LIMIT),)), argdefs=resident.inbound.__defaults__)
    incoming = scanner(before)
    need(not incoming, 'strict whole-ROM inbound census; no exemptions')
    after = bytearray(before)
    for _, at, blob in writes():
        after[at:at+len(blob)] = blob
    validate(before, after)
    semantics = selector_semantics(after)
    rejected = []
    # Use fresh local fixtures; never mutate or replace the supplied build graph.
    with tempfile.TemporaryDirectory(prefix='shoot-projectile-graph-') as directory:
        missing = Path(directory)/'missing.json'
        wrong = Path(directory)/'wrong.json'
        wrong.write_bytes(b'{}\n')
        for name, path in [('missing lower graph', missing), ('wrong lower graph', wrong)]:
            try:
                reload_proof.composition(source, path)
            except (OSError, ValueError, AssertionError):
                rejected.append(name)
            else:
                raise ValueError('accepted invalid graph ' + name)
    for name, offset, instruction in (
        ('wrong base', 4, 'cmp r0, #0x6C'),
        ('indexed gate', 16, 'tst r0, #4'),
        ('unmatched double push', 8, f'bne {ORIGINAL:#x}'),
        ('wrong saved register', 40, 'push {r8}'),
        ('nonzero initial mask', 44, 'mov r9, #1'),
        ('zero mask subtraction', 64, 'sub r9, r9, #36'),
        ('wrong translation', 64, 'subne r9, r9, #35'),
        ('double push entry', 68, f'b {RENDER:#x}'),
    ):
        bad = bytearray(after)
        bad[FIRST+offset:FIRST+offset+4] = asm(instruction, FIRST+offset)
        try:
            selector_semantics(bad)
        except (ValueError, AssertionError):
            rejected.append(name)
        else:
            raise ValueError('accepted selector semantics mutation ' + name)
    bad = bytearray(after)
    struct.pack_into('<I', bad, FIRST+72, P0+4)
    try:
        selector_semantics(bad)
    except (ValueError, AssertionError):
        rejected.append('wrong exact P0')
    else:
        raise ValueError('accepted wrong P0')
    for name, at in [('selector output', FIRST), ('pointer output', 0x12C50),
                     ('undeclared output', LIMIT), ('frozen clone', 0x6FEA50)]:
        bad = bytearray(after); bad[at] ^= 1
        try:
            validate(before, bad)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError('accepted output mutation ' + name)
    return bytes(after), dict(schema=1, status='RESIDENT_93E7_CLEAR_COMPONENT_PASS',
        input_sha256=INPUT, source_sha256=SOURCE, output_sha256=sha(after),
        reload_composition_report_sha256=PROOF, dependencies=DEPENDENCIES,
        lower_graph_sha256=sha(Path(lower_graph).read_bytes()),
        scope='Exact93E7 P0/base6D/static only; retained normal callback domain',
        reservation=[FIRST, LIMIT], incoming_references=incoming,
        original_renderer_entry=ORIGINAL, retained_v71_code_and_hooks_unchanged=True,
        prior_renderer_pointer_replaced=True, whole_ROM_inverse=True,
        new_RAM_or_task=False, rom_emitted=True, external_entry_authorized=False,
        complete_terminal_clear=False, P2_companion_projection=False,
        full_post_clear_reload_exclusion_approved=False, bounded_no_side1_reload=True,
        selector_semantics=semantics, negative_controls_rejected=rejected,
        changed_bytes=sum(a != b for a, b in zip(before, after)),
        writes=[dict(name=n, raw=at, bytes=len(blob), sha256=sha(blob)) for n, at, blob in writes()],
        remaining=['Independent real owner/full-renderer ARM QA required.',
            'Existing8F24 nonpattern/external-entry, primary pixels/queues, other owners and IRQ gates remain.',
            'No actual Shoot runtime or arbitrary foreign scheduler/callback state was tested.'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'source', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--reload-proof', required=True, type=Path)
    p.add_argument('--lower-graph', required=True, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    a = p.parse_args()
    paths = [x.resolve() for x in (a.candidate, a.source, a.output, a.reload_proof,
                                  a.lower_graph, a.manifest)]
    need(len(set(paths)) == 6, 'distinct input/output paths')
    need(a.source.suffix.lower() == '.wsc' and a.output.suffix.lower() == '.gba', 'explicit ROM types')
    need(not a.output.exists() and not a.manifest.exists(), 'fresh outputs required')
    result, report = build(a.candidate.read_bytes(), a.source.read_bytes(),
                           a.reload_proof.read_bytes(), a.lower_graph)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(result)
    a.manifest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({key: report[key] for key in ('status', 'output_sha256', 'changed_bytes')}))


if __name__ == '__main__':
    main()

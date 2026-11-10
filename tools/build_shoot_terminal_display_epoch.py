#!/usr/bin/env python3
"""Project the owned display mapping and recheck cheap fields at consumption."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
import verify_shoot_caller_resident as scanner

INPUT = '46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OUTPUT = '280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
HOOK, TAIL, END = 0x6FF6E8, 0x6FF720, 0x6FF768
ARM_OVERLAPS = (
    (0x6FF3B4,0xE1D010B0,0x086FF75A),
    (0x6FFBE8,0xE59F11D4,0x086FF72C),
    (0x6FFBF4,0xE5950028,0x086FF724),
    (0x6FFC00,0xE5960028,0x086FF732),
    (0x6FFC0C,0xE59F01B4,0x086FF750),
    (0x6FFC1C,0xE59F01A8,0x086FF760),
    (0x6FFC20,0xE5900000,0x086FF746),
)
PINS = (
    (0xFEC,0x103C,'7C790D050EB38E63CDDD3E7BAE8E07B16E6844E1733F09B59128457F09D93B3B'),
    (0x5E7400,0x5E7548,'019D8C1BCE934C7D91CDC31E8243C7F48A4D26AEC0BAF4BB1E558E3D12C08CDD'),
    (0x6FF600,0x6FF800,'4CC5B0AF66A1BC64E8DA74C163A4AAF5D75BA30AC4CD763D0B791EF7C45633B0'),
    (0x6FF9C0,0x6FFE04,'BB300E1C82EACE5F4A1998E11B55DD18C5A84B7B379432CDEDE3B1DB06A3158B'),
    (0x6FFE10,0x6FFED0,'39B5D48FAC09792EAED50E903ECDE85C0CC17ED3DAF52FAF17C36D3A8BF8767D'),
)
SOURCE_PINS = (
    (0x75FADA,0x75FBFC,'942169D587B8E437FD23EA635B6233B2144BF7A2470C544E791C5664D34893B9'),
    (0x75FD89,0x75FE03,'BDB9758BC73925B469647B3104A1DAB257518346B1B97E1B53D477CC263D65D6'),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(blob): return hashlib.sha256(blob).hexdigest().upper()
def word(blob, at): return struct.unpack_from('<I', blob, at)[0]
def asm(text, at): return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, 0x08000000 + at)[0])


def writes():
    # r0/r1/LR already belong to the retained tiny wrapper's saved frame.
    stub = asm('''
        mov r0, #0x04000000
        ldrh r1, [r0]
        tst r1, #7
        bne 0x086FF6F4
        ldrh r1, [r0, #10]
        tst r1, #0xCC
        bne 0x086FF6F4
        ldr r0, velocities
        ldr r1, [r0]
        cmp r1, #0
        bne 0x086FF6F4
        ldr r1, [r0, #0x50]
        cmp r1, #0
        bne 0x086FF6F4
        ldr r0, irq
        b 0x085E7400
    velocities: .word 0x03002354
    irq: .word 0x086FFE10
    ''', TAIL)
    need(len(stub) == END - TAIL, 'sixteen instructions and two literals')
    return ((HOOK, asm('bl 0x086FF720', HOOK)), (TAIL, stub),
            (0x6FFDE8, struct.pack('<I', 0xCC)), (0x6FFDEC, bytes(4)))


def inverse(before, after, replacements):
    need(len(before) == len(after) == 0x800000, 'exact eight MiB extent')
    restored = bytearray(after)
    for at, blob in replacements:
        need(after[at:at + len(blob)] == blob, 'exact expected word/body ' + hex(at))
        restored[at:at + len(blob)] = before[at:at + len(blob)]
    need(bytes(restored) == before, 'whole-ROM inverse')


def build(before, source):
    need((sha(before), sha(source)) == (INPUT, SOURCE), 'exact46B3 and WSC1.5')
    for data, pins in ((before, PINS), (source, SOURCE_PINS)):
        for a, z, digest in pins:
            need(sha(data[a:z]) == digest, 'native/source contract ' + hex(a))
    need(before[HOOK:HOOK + 4] == asm('bl 0x085E7400', HOOK), 'old display call')
    need(before[0x33FD04:0x33FD08] == asm('b 0x086FF380', 0x33FD04) and
         sha(before[0x6FF380:0x6FF3E8]) == 'B337C3187857E37930ACF81B8047C8B757E34E865DB934DC3864520541742AFF',
         'ARM scene entry and complete ARM owner of overlapping high halfword')
    need(before[0x6FF694:0x6FF698] == asm('bl 0x086FF9C0', 0x6FF694), 'ARM guard entry owns six other load overlaps')
    need((word(before, 0x6FFDE8), word(before, 0x6FFDEC)) == (0xDFCC, 0x1E00), 'old current hardware mask')
    need(before[TAIL:0x6FF800] == b'\xff' * (0x6FF800 - TAIL), 'entire retained adapter reservation tail erased')
    scan = types.FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((TAIL, END),)),
                              argdefs=scanner.inbound.__defaults__)
    incoming = scan(before)
    # These are high halves of pinned ARM loads, not executable Thumb entries.
    need(incoming == [('Thumb B', a+2, destination) for a, _, destination in ARM_OVERLAPS],
         'complete conservative inbound census contains only enumerated ARM overlaps')
    need(all(word(before,a) == value for a,value,_ in ARM_OVERLAPS), 'exact containing ARM load words')
    replacements = writes()
    after = bytearray(before)
    for at, blob in replacements:
        after[at:at + len(blob)] = blob
    after = bytes(after)
    inverse(before, after, replacements)
    need(sha(after) == OUTPUT, 'frozen output')
    return after, dict(input_sha256=INPUT, output_sha256=sha(after), source_sha256=SOURCE,
        expected_writes=[dict(offset=a, before=before[a:a+len(b)].hex(), after=b.hex()) for a, b in replacements],
        declared_bytes=sum(len(b) for _, b in replacements), changed_bytes=sum(a != b for a, b in zip(before, after)),
        whole_ROM_inverse=True, existing_owner_reservation=[0x6FF600,0x6FF800], prior_adapter_body_end=TAIL,
        new_tail_extent=[TAIL,END], conservative_incoming_references=incoming, containing_ARM_loads=ARM_OVERLAPS,
        executable_incoming_references=[], new_RAM_bytes=0, additional_stack_bytes=0,
        prospective_mapping='FEC#21: (current BG1CNT & FF) | 1E00; projected & DFCC == 1E00 iff current & CC == 0',
        consumption_recheck=['DISPCNT mode0','BG1 charbase0/4bpp/no mosaic','all four descriptor velocities zero'],
        entries=dict(consumption=0x086FF720,success=0x086FF75C,stale=0x086FF6F4),
        native_pins=PINS,source_pins=SOURCE_PINS,
        retained_contract='Heavy typed actor/queue/tile/F000-row predicates and bounded stationary ownership remain unchanged; no universal DMA claim.',
        timing='16-instruction stub, no loop or extra frame. Actual IRQ scanline deadline remains a runtime gate.',
        source_DI_emulated=False,actual_runtime_acceptance=False,final_port_complete=False)


def checks(before, after):
    import verify_shoot_guarded_transition_irq as prior

    def fixture(data, flags=0x10, counter=40, vertical=184):
        result = prior.prepared_fixture(data, flags, counter, vertical)
        m, first, upper, aux, _ = result
        m.put(aux + 0x18, first); m.put(aux + 0x28, upper)
        m.put(0x0400000A, 0x1F03, 2)
        m.writes.clear()
        return result

    for data, expected in ((before, 0), (after, 1)):
        m, *_ = fixture(data)
        m.run(0x086FF9C0, {prior.RETURN}, max_steps=70000)
        need(m.r[0] == expected, 'old mapping refusal and prospective acceptance')
    # Exact algebra for every hardware control word; unsupported low bits still fail.
    for control in range(65536):
        need((((control & 255) | 0x1E00) & 0xDFCC == 0x1E00) == (control & 0xCC == 0), 'prospective mapping algebra')
    chain = types.FunctionType(prior.queue_chain.__code__, dict(prior.__dict__, prepared_fixture=fixture),
                               argdefs=prior.queue_chain.__defaults__)
    trajectories = [chain(after, counter=k) for k in (1,143)]
    # Changes after a successful heavy guard must be rejected by the live consumer.
    mutations = [(f'velocity-{a:X}',a,1,2) for a in (0x03002354,0x03002356,0x030023A4,0x030023A6)]
    mutations += [('bitmap',0x04000000,3,2),('charbase',0x0400000A,0x1F07,2),
                  ('mosaic',0x0400000A,0x1F43,2),('8bpp',0x0400000A,0x1F83,2),
                  ('mode8',0x03002310,8,2),('stage7',0x0300231E,7,1),('phaseclear',0x0300450A,0,2)]
    cases = 0
    for flags in (0x10,0xF0000010):
        for label, address, value, size in mutations:
            a, *_ = fixture(after, flags); b, *_ = fixture(after, flags)
            registers = a.r[:]
            a.run(0x086FF9C0,{prior.RETURN},max_steps=70000)
            need(a.r[0] == 1, 'valid queue-time guard before mutation')
            a.r[:] = registers
            for m in (a,b):
                m.put(address,value,size); m.writes.clear()
            sp = a.r[13]
            a.run(prior.DISPLAY,{prior.RETURN},max_steps=70000)
            b.run(0x08587200,{prior.RETURN},max_steps=70000)
            need(a.r[:15] == b.r[:15] and prior.nonstack_writes(a,sp) == prior.nonstack_writes(b,sp),
                 'live stale fallback preserves complete route '+label)
            cases += 1
    m, *_ = fixture(after)
    initial = m.r[:15]; sp = m.r[13]
    m.run(prior.DISPLAY,{0x086FF75C},max_steps=100)
    need(m.r[0] == prior.IRQ and m.r[14] == 0x086FF6EC and m.r[13] == sp - 12 and m.r[2:13] == initial[2:13], 'success reload and retained wrapper frame')
    need(not prior.nonstack_writes(m,sp), 'cheap recheck has no nonstack writes')
    m.run(0x086FF75C,{prior.RETURN},max_steps=70000)
    need(m.r[:15] == initial and m.get(0x0400000A,2) == 0x1E03 and m.get(prior.SLOT) == prior.IRQ,
         'real FEC installs planned mapping before real IRQ owner; all registers restored')
    rejected = []
    for at in (HOOK,TAIL,END-1,END,0x6FFDE8,0x6FFDEC,0x7FFFFF):
        bad = bytearray(after); bad[at] ^= 1
        try: inverse(before,bytes(bad),writes())
        except ValueError: rejected.append(hex(at))
        else: raise ValueError('inverse mutation accepted')
    return dict(status='DISPLAY_EPOCH_AUTHOR_ARM_PASS',prospective_control_words=65536,
        queue_to_final_trajectories=trajectories,live_mutation_fallback_cases=cases,
        actual_FEC_and_dispatch_executed=True,service_models=[],success_registers_and_stack=True,
        inverse_mutations_rejected=rejected,actual_runtime_acceptance=False,
        timing='Actual scanline timing unmeasured; k1/k143 instruction trajectories are not a cycle benchmark.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path); parser.add_argument('source',type=Path); parser.add_argument('output',type=Path)
    parser.add_argument('--manifest',type=Path,required=True); parser.add_argument('--author-report',type=Path)
    args = parser.parse_args()
    outputs = [args.output,args.manifest] + ([args.author_report] if args.author_report else [])
    need(len({p.resolve() for p in [args.input,args.source]+outputs}) == 2+len(outputs), 'distinct paths')
    need(all(not p.exists() for p in outputs),'fresh outputs')
    before = args.input.read_bytes(); after,manifest = build(before,args.source.read_bytes())
    report = checks(before,after) if args.author_report else None
    for path in outputs: path.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(after); args.manifest.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    if args.author_report: args.author_report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(sha(after))


if __name__ == '__main__': main()

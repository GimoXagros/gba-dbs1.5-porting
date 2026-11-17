"""Restore the source ID13 aerial graph at all three retained fall consumers."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16
from verify_shoot_attack_dispatch import Machine
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
INPUT = 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
FIRST, LIMIT = 0xD3F100, 0xD3FA00
HOOKS = ((0x357054, FIRST), (0x35732C, FIRST+0x50), (0x3578D4, FIRST+0xA0))
INIT, READY, BOOST, SPENT = 0xD3F200, 0xD3F280, 0xD3F500, 0xD3F700
HORIZONTAL, LAND, ATTACK, OTHER = 0x0835604C, 0x08355B54, 0x08355998, 0x08355B04
SET_EVENT, ADVANCE, SPECIAL = 0x08012874, 0x08012A84, 0x08357DD4
SCANNER = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from('<I', data, at)[0]


def asm(text, at):
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, BASE+at)[0])


def branch(at, target):
    delta = target-at-8
    need(delta % 4 == 0 and -(1 << 25) <= delta < 1 << 25, 'ARM branch reach')
    return struct.pack('<I', 0xEA000000 | ((delta//4) & 0xFFFFFF))


def route(hook, at):
    return asm(f'''
      push {{r0}}
      mrs r0, cpsr
      ldrb r8, [r4, #0x11]
      cmp r8, #13
      bne legacy
      msr cpsr_f, r0
      pop {{r0}}
      ldr r8, target
      str r8, [r4]
      pop {{lr}}
      bx lr
    legacy:
      msr cpsr_f, r0
      pop {{r0}}
      ldrh r8, [r4, #0x2c]
      b 0x{BASE+hook+4:08X}
    target: .word 0x{BASE+INIT:08X}
    ''', at)


def event(value):
    load = f'mov r8, #{value}' if isinstance(value, int) else f'mov r8, {value}'
    return f'push {{r5}}\npush {{r11}}\n{load}\npush {{r8}}\nbl 0x{SET_EVENT:X}\nadd sp, sp, #12\n'


def frame_end():
    return f'''advance:
      push {{r5}}
      push {{r11}}
      mov r8, #1
      push {{r8}}
      bl 0x{ADVANCE:X}
      add sp, sp, #12
    done:
      pop {{lr}}
      bx lr
    '''


def gravity():
    # Source special-air literals stay in their existing per-update fixed-point units.
    return '''ldrsh r8, [r4, #0xaa]
      cmp r8, #0
      bne gravity_done
      mov r8, #1
      strh r8, [r4, #0xaa]
      mov r8, #0x16
      strh r8, [r4, #0x48]
      ldrh r8, [r4, #0xa2]
      cmp r8, #1
      mov r3, #10
      beq gravity_event
      mov r8, #0x1e
      strh r8, [r4, #0x48]
      mov r3, #7
    gravity_event:
    '''+event('r3')+'gravity_done:\n'


def callbacks():
    initial = asm(f'''push {{lr}}
      mov r8, #0x100
      strh r8, [r4, #0xa8]
      mov r8, #0xf0
      strh r8, [r4, #0xa0]
      ldr r8, target
      str r8, [r4]
      b 0x{BASE+READY+4:X}
    target: .word 0x{BASE+READY:X}
    ''', INIT)
    ready = asm(f'''push {{lr}}
      bl 0x{HORIZONTAL:X}
      ldrh r8, [r4, #0x2c]
      tst r8, #0x40
      beq release
      ldrh r8, [r4, #8]
      tst r8, #0x4000
      beq normal
      ldrh r8, [r4, #0xa6]
      orr r8, r8, #1
      strh r8, [r4, #0xa6]
      ldr r8, special
      str r8, [r4]
      b done
    normal:
      ldrh r8, [r4, #0xa8]
      tst r8, #0x100
      bne falling
      orr r8, r8, #0x100
      strh r8, [r4, #0xa8]
      mov r8, #0
      strh r8, [r4, #0xaa]
      mov r8, #0x10
      strb r8, [r4, #0x6e]
      mov r8, #0x18
      strh r8, [r4, #0x48]
      ldr r8, launch_speed
      strh r8, [r4, #0x44]
      ldrh r0, [r4, #0xa8]
      add r8, r0, #1
      and r8, r8, #0xff
      bic r0, r0, #0xff
      orr r8, r8, r0
      strh r8, [r4, #0xa8]
    '''+event(0x72)+f'''
      ldr r8, boosted
      str r8, [r4]
      b done
    release:
      ldrh r8, [r4, #0xa8]
      and r8, r8, #0xff
      strh r8, [r4, #0xa8]
    falling:
      ldrsh r8, [r4, #0x44]
      cmp r8, #0
      ble interrupted
    '''+gravity()+f'''
      bl 0x{LAND:X}
      cmp r0, #0
      bne done
    interrupted:
      bl 0x{ATTACK:X}
      cmp r0, #0
      bne done
      bl 0x{OTHER:X}
      cmp r0, #0
      bne done
      b advance
    '''+frame_end()+f'''
    special: .word 0x{SPECIAL:X}
    boosted: .word 0x{BASE+BOOST:X}
    launch_speed: .word 0xFFFFFD80
    ''', READY)
    boost = asm('''push {lr}
      ldrsh r8, [r4, #0x44]
      cmp r8, #0
      ble advance
    '''+gravity()+f'''
      bl 0x{LAND:X}
      cmp r0, #0
      bne done
      ldrh r8, [r4, #0xa2]
      cmp r8, #1
      moveq r3, #10
      movne r3, #7
    '''+event('r3')+'''
      mov r8, #3
      strb r8, [r4, #0x6e]
      ldrb r8, [r4, #0xa8]
      cmp r8, #3
      ldrlo r8, ready
      ldrhs r8, spent
      str r8, [r4]
      b advance
    '''+frame_end()+f'''
    ready: .word 0x{BASE+READY:X}
    spent: .word 0x{BASE+SPENT:X}
    ''', BOOST)
    spent = asm(f'''push {{lr}}
      bl 0x{HORIZONTAL:X}
      ldrsh r8, [r4, #0x44]
      cmp r8, #0
      ble interrupted
    '''+gravity()+f'''
      bl 0x{LAND:X}
      cmp r0, #0
      bne done
    interrupted:
      bl 0x{ATTACK:X}
      cmp r0, #0
      bne done
      bl 0x{OTHER:X}
      cmp r0, #0
      bne done
      b advance
    '''+frame_end(), SPENT)
    return ((INIT, READY, initial), (READY, BOOST, ready), (BOOST, SPENT, boost), (SPENT, LIMIT, spent))


def source_contracts(source, native, gba):
    windows = ((0x785797, 0x785993, '95AF262178FE267C49AB7DE8DC687C93BDEE5D87430F5DB08567BE75C66E3F77'),
               (0x7854DD, 0x7855BF, '7E9A032DFE9EFBFAE8CBA03EA3D2703E1D99052B40091E69602EAEDF91DA6DC1'),
               (0x766FC5, 0x766FF3, '95AA6EC89DB9ECB453BEBC4390DD7C717AB19DDEFBF4FA370436C3BDF0115CA2'))
    for lo, hi, digest in windows:
        need(sha(source[lo:hi]) == digest, 'exact source aerial graph/helper')
    for at in (0x7682DC, 0x7684B5, 0x7688C1, 0x768AB3):
        need(sha(source[at:at+40]) == '8EE323146B7793890D42DC85BEA3D2EF972560A668F23B178382CFD25F42C9C0', 'all four identical source entry gates')
    pattern = bytes.fromhex('c7047705c744022285')
    hits = [i for i in range(len(source)) if source.startswith(pattern, i)]
    need(hits == [0x7682FA, 0x7684D3, 0x7688DF, 0x768AD1], 'all direct source initializer stores')
    for lo, hi in ((0x35604C, 0x3560A0), (0x356FDC, 0x357988), (0x357988, 0x357F58)):
        need(native[lo:hi] == gba[lo:hi], 'actual retained shared motion and aerial services')
    need(word(native, 0x357984) == SPECIAL, 'existing source02BD native target')
    need(source[0x78528F:0x78529F].hex() == 'c744380200837c34407e05c744344000', 'source special gravity2/velocity64')
    need(word(native, 0x357A44) == 0xE3A09002 and word(native, 0x357A58) == 0xE3A09040, 'native special literals unchanged')
    need(word(native, 0x357DF4) == 0xE3A0907E and word(native, 0x357F00) == 0xE3A00080,
         'native02BD duration126/horizontal128 unchanged, no global time multiplier')
    # Installed Iraira initializer/wait assigns the retained common jump graph.
    arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    wait = list(arm.disasm(native[0x627C00:0x627C48], 0x08627C00))
    need(any(i.mnemonic == 'b' and i.op_str == '#0x835774c' for i in wait), 'Iraira reaches shared jump continuation')
    need(word(native, 0x357EE0) == 0xE1C49ABA, 'source+94 maps to native+AA through existing02BD writer')
    return dict(source_windows=[dict(start=a, end=b, sha256=c) for a, b, c in windows],
                source_entry_stores=hits, native_hooks=[BASE+x[0] for x in HOOKS],
                field_map={'32':'42','34':'44','36':'46','38':'48','5A':'6E','8A':'A0','8C':'A2','90':'A6','92':'A8','94':'AA'},
                units='Same fixed-point per-update special-aerial units; no invented clock multiplier.',
                lifetime='A8 packed held/relaunch count and AA descending flag belong to the active actor callback; INIT resets A8, each relaunch resets AA, existing shared fall/02BD use AA as the same descending flag.')


def ownership(native, audio_bytes, table_bytes):
    need(sha(audio_bytes) == 'AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91', 'audio reservation owner')
    need(sha(table_bytes) == '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6', 'preceding suballocation owner')
    audio, tables = json.loads(audio_bytes), json.loads(table_bytes)
    need([0xD33000, 0xD40000] in audio['reservations'], 'declared enclosing reservation')
    for w in audio['writes']:
        if 0xD33000 <= w['offset'] < 0xD40000:
            need(sha(native[w['offset']:w['offset']+w['size']]) == w['after_sha256'], 'earlier audio contents preserved')
    for w in tables['writes']:
        need(native[w['offset']:w['offset']+w['size']] == bytes.fromhex(w['after_hex']), 'all earlier evolution table changes preserved')
    need(tables['allocation']['remaining_tail'] == [0xD3F05A, 0xD40000], 'previous remaining ownership')
    need(native[0xD3F05A:0xD40000] == b'\xff'*(0xD40000-0xD3F05A), 'owner unused tail blank')
    need(sha(Path(scanner.__file__).read_bytes()) == SCANNER, 'pinned conservative scanner')
    scan = types.FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((FIRST, LIMIT),)), argdefs=scanner.inbound.__defaults__)
    hits = scan(native); need(not hits, 'no prior encoded pointer/control/literal reference into new code')
    return dict(enclosing_reservation=[0xD33000, 0xD40000], preceding_end=0xD3F05A,
                suballocation=[FIRST, LIMIT], inbound_hits=hits, scanner_sha256=SCANNER)


def checks(before, after):
    actor, presentation, stop = 0x02011710, 0x020117BC, 0x08000100
    cases = 0
    for (hook, _), ident, flags in itertools.product(HOOKS, range(15), range(16)):
        m = Machine(after, seed=17, flags=(flags << 28)|0x1F)
        m.r[4], m.r[5], m.r[13], m.r[14] = actor, presentation, 0x03007E00, stop
        for offset in range(0, 0x118, 4):
            m.put(actor+offset, 0)
        m.put(actor+0x11, ident, 1); m.put(actor+0x2C, 0xC04A, 2)
        m.put(m.r[13], stop)
        original, oldsp, oldflags = m.r[:15], m.r[13], m.cpsr
        end = m.run(BASE+hook, {BASE+hook+4, stop})
        need(m.cpsr == oldflags, 'route preserves all condition flags')
        if ident == 13:
            need(end == stop and m.r[13] == oldsp+4 and m.get(actor) == BASE+INIT,
                 'source automatic assignment returns through original saved LR')
        else:
            expected = original[:]; expected[8] = 0xC04A
            need(end == BASE+hook+4 and m.r[:15] == expected, 'all other identities preserve displaced load state')
            need(m.get(actor) == 0, 'other identities retain callback')
        cases += 1

    def machine():
        m = Machine(after, seed=5, flags=0x1F)
        m.r[4], m.r[5], m.r[13], m.r[14] = actor, presentation, 0x03007E00, stop
        for offset in range(0, 0x118, 4):
            m.put(actor+offset, 0)
        m.events, m.ticks = [], 0
        for target in (LAND, ATTACK, OTHER):
            m.services[target] = lambda cpu: cpu.r.__setitem__(0, 0)
        def event_service(cpu):
            need(cpu.get(cpu.r[13]+8) == presentation, 'event service presentation stack ABI')
            value = cpu.get(cpu.r[13]); cpu.events.append(value); cpu.put(presentation+0xE, value, 2, True)
        def tick_service(cpu):
            need(cpu.get(cpu.r[13]) == 1 and cpu.get(cpu.r[13]+8) == presentation, 'advance stack ABI')
            cpu.ticks += 1
        m.services[SET_EVENT], m.services[ADVANCE] = event_service, tick_service
        return m

    m = machine(); m.put(actor+0x44, 1, 2); m.put(actor+0xAA, 1, 2)
    for entry in (INIT, READY):
        m.r[14] = stop; m.run(BASE+entry, {stop})
    need(m.get(actor+0xA0, 2) == 0xF0 and m.get(actor+0xA8, 2) == 0, 'init and release establish source latch')
    for count in (1, 2, 3):
        m.put(actor+0x2C, 0x40, 2); m.r[14] = stop
        ticks = m.ticks; m.run(BASE+READY, {stop})
        need(m.get(actor) == BASE+BOOST and m.get(actor+0xA8, 2) == 0x100+count,
             'each fresh held edge consumes exactly one relaunch')
        need(m.get(actor+0x44, 2) == 0xFD80 and m.get(actor+0x48, 2) == 0x18 and
             m.get(actor+0xAA, 2) == 0 and m.events[-1] == 0x72 and m.ticks == ticks,
             'initial relaunch installs source velocity/event without advancing it')
        m.put(actor+0x44, 1, 2); m.put(actor+0x2C, 0, 2); m.r[14] = stop
        m.run(BASE+BOOST, {stop})
        need(m.get(actor) == BASE+(READY if count < 3 else SPENT), 'three relaunch exhaustion')
        need(m.get(actor+0x6E, 1) == 3 and m.get(actor+0xAA, 2) == 1, 'descent restores ordinary air phase')
        m.r[14] = stop; m.run(m.get(actor), {stop})
    m.put(actor+0x2C, 0x40, 2); m.r[14] = stop
    m.run(BASE+SPENT, {stop})
    need(m.get(actor) == BASE+SPENT and m.get(actor+0xA8, 1) == 3, 'fourth press cannot relaunch')
    need(m.r[13] == 0x03007E00, 'all callback stacks balance')

    for packed in (0x00FF, 0xAAFF, 0xFE00, 0xFF02):
        m = machine(); m.put(actor+0xA8, packed, 2); m.put(actor+0x2C, 0x40, 2)
        m.put(actor+0xAA, 1, 2); m.run(BASE+READY, {stop})
        if not packed & 0x100:
            need(m.get(actor+0xA8, 2) == ((packed | 0x100)&0xFF00)|((packed+1)&0xFF), 'INC AL preserves full high byte')
        m.put(actor+0x2C, 0, 2); m.r[14] = stop; m.run(BASE+READY, {stop})
        need(m.get(actor+0xA8, 2) < 256, 'release clears every high bit as source AND00FF')
    m = machine(); m.put(actor+8, 0x4000, 2); m.put(actor+0x2C, 0x40, 2)
    m.run(BASE+READY, {stop})
    need(m.get(actor) == SPECIAL and m.get(actor+0xA6, 2) & 1 and not m.events and not m.ticks,
         'enhanced route assigns retained02BD and returns without same-update execution')
    p1 = word(before, 0x4A80F8+13*32+4)-BASE
    events = word(before, p1)-BASE
    resources = []
    for event_id in (7, 10, 0x26, 0x27, 0x72):
        row = events+event_id*16; n, ptr = struct.unpack_from('<II', before, row)
        need(0 < n <= 255 and BASE <= ptr <= BASE+len(before)-n*16, 'ID13 actual presentation event exists')
        resources.append(dict(event=event_id, commands=n, pointer=ptr))
    return dict(selector_cases=cases, relaunches=3, fourth_press_rejected=True, packed_count_cases=4,
                enhanced_special_route=True, balanced_stacks=True, actual_resource_events=resources)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'source', 'gba', 'audio-manifest', 'table-manifest', 'output', 'manifest'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    need(not a.output.exists() and not a.manifest.exists(), 'fresh outputs required')
    paths = [getattr(a, n) for n in ('before','source','gba','audio_manifest','table_manifest','output','manifest')]
    need(len({x.resolve() for x in paths}) == len(paths), 'nonalias paths')
    before, source, gba = a.before.read_bytes(), a.source.read_bytes(), a.gba.read_bytes()
    need((sha(before), sha(source), sha(gba)) == (INPUT, SOURCE, GBA), 'exact immutable inputs')
    proof = source_contracts(source, before, gba)
    owned = ownership(before, a.audio_manifest.read_bytes(), a.table_manifest.read_bytes())
    after, writes, code = bytearray(before), [], []
    def put(at, blob, label):
        need(not any(max(at, w['offset']) < min(at+len(blob), w['offset']+w['size']) for w in writes), 'disjoint writes')
        writes.append(dict(offset=at, size=len(blob), label=label, before_hex=before[at:at+len(blob)].hex(), after_hex=blob.hex()))
        after[at:at+len(blob)] = blob
    for hook, at in HOOKS:
        need(word(before, hook) == 0xE1D482BC, 'original input-load hook')
        blob = route(hook, at); need(len(blob) <= 0x50, 'route slot')
        put(at, blob, 'ID13 shared-fall selector'); put(hook, branch(hook, at), 'shared fall hook')
    for at, end, blob in callbacks():
        need(at+len(blob) <= end, 'bounded callback slot')
        put(at, blob, f'source callback {at:X}')
        code.append(dict(raw=at, size=len(blob), sha256=sha(blob)))
    inverse = bytearray(after)
    for w in writes:
        inverse[w['offset']:w['offset']+w['size']] = bytes.fromhex(w['before_hex'])
    need(inverse == before, 'whole-image inverse')
    executed = checks(before, bytes(after))
    report = dict(status='ID13_AIR_RELAUNCH_AUTHORED', input_sha256=INPUT, output_sha256=sha(after),
                  source=proof, allocation=owned, writes=writes, callbacks=code,
                  states={'0577':BASE+INIT,'0593':BASE+READY,'066E':BASE+BOOST,'0701':BASE+SPENT},
                  helpers={'horizontal':HORIZONTAL,'landing':LAND,'attack':ATTACK,'other':OTHER,'set_event':SET_EVENT,'advance':ADVANCE,'special02BD':SPECIAL},
                  whole_inverse=True, ARM=executed, changed_bytes=sum(x!=y for x,y in zip(before,after)),
                  runtime_verified=False, wall_time_parity_claimed=False, builder_sha256=sha(Path(__file__).read_bytes()))
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True, exist_ok=True); a.manifest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(report['status'], report['output_sha256'])


if __name__ == '__main__':
    main()

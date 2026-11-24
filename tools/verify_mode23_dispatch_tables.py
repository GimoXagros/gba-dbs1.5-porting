"""Independent finite table-consumer census and native mode23 lifecycle dispatch.

Uses a typed constructor fixture; actual native task-callback setter and all
dispatcher instructions execute. No scene resources, ROM allocation or menu
producer are represented by this bounded check.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_dispatch_tables import patches, selector_assembly

BASE, TABLE, CONSTRUCTOR, SELECTOR = 0x08000000, 0x08E00000, 0x08E10000, 0x08E20000
CONFIG, TASK, MARKER = 0x03002310, 0x02010000, 0x02020000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def need(ok, why):
    if not ok: raise ValueError(why)
def u(b, a): return struct.unpack_from('<I', b, a)[0]
def asm(text, address): return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, address)[0])
def memory(m, at, size): return bytes(m.get(at + i, 1) for i in range(size))

def seed(rom, mode, flags):
    m = Machine(rom, seed=12, flags=(flags << 28) | 31)
    for i in range(0x30): m.put(CONFIG + i, (i * 7 + 9) & 255, 1)
    m.put(CONFIG, mode, 2)
    m.put(0x0300133C, TASK)
    m.put(TASK, 0x080159B4)
    m.put(0x04000006, 160, 2)
    m.put(MARKER, 0xFEEDF00D)
    return m

def census(native):
    found = {}
    for at in range(0, len(native) - 3, 4):
        word = u(native, at)
        op = (word >> 21) & 15
        if word & 0x0E0F0000 != 0x020F0000 or op not in (2, 4): continue
        value, rotate = word & 255, ((word >> 8) & 15) * 2
        imm = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF if rotate else value
        target = BASE + at + 8 + (imm if op == 4 else -imm)
        if BASE + 0x15B70 <= target < BASE + 0x15D31: found[at] = target
    expected = {0x159E0: BASE + 0x15B70, 0x159FC: BASE + 0x15B74,
                0x15A20: BASE + 0x15B74, 0x15AD4: BASE + 0x15B78,
                0x15AF0: BASE + 0x15CC8, 0x15AF8: BASE + 0x15C6C}
    need(found == expected, 'complete aligned ARM PC-address census')
    # Byte-aligned encoded literal addresses, including unaligned occurrences.
    pointer_hits = []
    for at in range(len(native) - 3):
        if native[at + 3] == 8:
            value = u(native, at)
            if BASE + 0x15B70 <= value < BASE + 0x15D31: pointer_hits.append(at)
    need(not pointer_hits, 'no additional encoded direct table addresses')
    return {f'{a:06X}': f'{b:08X}' for a, b in found.items()}

def transition(rom, mode, choice, submode, option, flags):
    m = seed(rom, mode, flags)
    for off, value in ((2, submode), (4, 1), (6, choice), (8, 0xF00D), (0x1A, option)):
        m.put(CONFIG + off, value, 2)
    m.r[5] = CONFIG
    # Entry after common callback owns the dispatcher's saved LR.
    sp, end = m.r[13], m.r[14]
    m.r[13] -= 4; m.put(m.r[13], end)
    m.run(0x08015AE4, {end}, max_steps=200)
    need(m.r[13] == sp, 'transition stack retirement')
    return memory(m, CONFIG, 0x30), m.get(TASK), m.cpsr

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('source', 'native', 'report'): p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args(); need(not a.report.exists(), 'fresh report')
    source, native = a.source.read_bytes(), a.native.read_bytes()
    need(sha(source) == SOURCE and sha(native) == NATIVE, 'immutable predecessors')
    readers = census(native)
    blob, changes = patches(source, native, TABLE, CONSTRUCTOR, SELECTOR)
    selector = asm(selector_assembly(), SELECTOR)
    need(len(blob) == 528 and len(selector) == 16 and len(changes) == 14, 'bounded table/helper/patch sizes')
    need(set(changes) == {0x159E0, 0x159FC, 0x15A20, 0x15AD4, 0x15AF0, 0x15AF8,
                         0x15AE8, 0x15AEC, 0x15B70, 0x15B74, 0x15B78, 0x15C6C, 0x15CC8, 0x81C80}, 'exact edit ownership')
    need(blob[:252] == native[0x15B70:0x15C6C], '21 old callback triples retained')
    need(blob[252:276] == bytes(24), '21/22 callback holes')
    need(struct.unpack_from('<3I', blob, 276) == (0x080159B0, CONSTRUCTOR, 0x080159B0), 'new source no-op callbacks')
    need(blob[288:372] == native[0x15C6C:0x15CC0] and blob[372:380] == bytes(8), 'old dispatches and holes')
    need(u(blob, 380) == 0x08015B40, 'source normal exit dispatcher')
    for mode in range(21):
        need(blob[384 + mode * 6:389 + mode * 6] == native[0x15CC8 + mode * 5:0x15CCD + mode * 5], 'old five choices retained')
    need(blob[384 + 21 * 6:384 + 23 * 6] == bytes(12), 'holes have no transitions')
    rom = bytearray(native)
    for at, data in changes.items(): rom[at:at + len(data)] = data
    for address, data in ((TABLE, blob), (SELECTOR, selector),
                          (CONSTRUCTOR, asm('ldr r8,slot; str r2,[r8]; bx lr; slot: .word 0x02020000', CONSTRUCTOR))):
        rom[address - BASE:address - BASE + len(data)] = data
    inverse = bytearray(rom)
    for at, data in changes.items(): inverse[at:at + len(data)] = native[at:at + len(data)]
    for address, size in ((TABLE, len(blob)), (SELECTOR, len(selector)), (CONSTRUCTOR, 16)):
        inverse[address - BASE:address - BASE + size] = native[address - BASE:address - BASE + size]
    need(inverse == native, 'whole in-memory image inverse')
    counts = dict(old_transitions=0, selectors=0, constructor_scheduler=0, common_exit=0)
    for mode in range(21):
        for choice in range(5):
            for submode, option in ((0, 0), (1, 0), (1, 0x1000)):
                for flags in (0, 15):
                    need(transition(rom, mode, choice, submode, option, flags) == transition(native, mode, choice, submode, option, flags), 'retained native transition parity')
                    counts['old_transitions'] += 1
    for bits in range(256):
        for state in (0, 0x10):
            m = seed(rom, 4, bits % 16); m.r[5] = TASK + 0x18
            m.put(m.r[5], state, 2); m.put(CONFIG + 0x1A, bits, 2)
            m.run(0x08081C64, {0x08081CB4}, max_steps=50)
            want = 4 if state else 3 if bits & 2 else 5 if bits & 8 else 1
            need(m.r[1] == want, 'selective flag priority')
            counts['selectors'] += 1
    for flags in range(16):
        for active in (0, 1, 3, 9, 52):
            m = seed(rom, 23, flags); m.r[2] = active
            sp, end = m.r[13], m.r[14]
            m.run(0x080159B4, {end}, max_steps=100)
            need(m.r[13] == sp and m.r[2] == active, 'no-op initializer retains scheduler R2/SP')
            if active:
                need(m.get(MARKER) == active and m.get(TASK) == 0x08015AB4, 'immediate constructor and actual callback store')
            else:
                need(m.get(MARKER) == 0xFEEDF00D and m.get(0x03002308) == CONSTRUCTOR and m.get(TASK) == 0x08015A48, 'deferred constructor ownership')
                m.r[14] = end; m.run(0x08015A48, {end}, max_steps=50)
                need(m.get(TASK) == 0x08015A48, 'wait does not construct before ready')
                m.r[14] = end; m.run(0x08015A78, {end}, max_steps=20)
                m.r[14] = end; m.run(0x08015A48, {end}, max_steps=50)
                need(m.get(TASK) == 0x08015A8C and m.get(CONFIG + 4, 2) == 0, 'readiness switches callback')
                m.r[14] = end; m.run(0x08015A8C, {end}, max_steps=60)
                need(m.get(MARKER) == 1 and m.get(TASK) == 0x08015AB4, 'deferred constructor actual call/store')
            counts['constructor_scheduler'] += 1
        m = seed(rom, 23, flags); m.put(CONFIG + 4, 0, 2)
        end, sp = m.r[14], m.r[13]
        m.run(0x08015AB4, {end}, max_steps=80)
        need(m.get(CONFIG, 2) == 23 and m.r[13] == sp, 'common idle keeps mode23')
        m.put(CONFIG + 4, 1, 2); m.put(CONFIG + 6, 0, 2); m.r[14] = end
        m.run(0x08015AB4, {end}, max_steps=100)
        need(m.get(CONFIG, 2) == 20 and memory(m, CONFIG + 4, 6) == bytes(6) and m.get(TASK) == 0x080159B4 and m.r[13] == sp, 'full common no-op exits through normal mode20')
        counts['common_exit'] += 1
    result = dict(status='MODE23_DISPATCH_BOUNDED_INDEPENDENT_PASS', source_sha256=SOURCE, native_sha256=NATIVE,
                  tool_sha256=sha(Path(__file__).read_bytes()), module_sha256=sha((ROOT / 'tools/mode23_dispatch_tables.py').read_bytes()),
                  table_sha256=sha(blob), selector_sha256=sha(selector), reader_census=readers, cases=counts,
                  limits=['Constructor body is a typed R2 capture fixture; no scene construction or cleanup proof.',
                          'No ROM reservation, linked image, menu entry producer or runtime execution.',
                          'Encoded census excludes arbitrary computed aliases and Thumb code discovery.',
                          'Mode18 was already unregistered; retained21 rows do not mean21 implemented modes.',
                          'Modes21/22 stay zero; integration must keep every producer from selecting them.'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))

if __name__ == '__main__': main()

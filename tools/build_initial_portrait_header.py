"""Localize the initial fixed Guilmon portrait as well as selection reloads."""
import argparse
import json
import struct
from pathlib import Path
from build_character_select_name_scene import Allocator, BASE, exclude, sha
from character_select_name_overlay import GETTER, Ks, KS_ARCH_ARM, KS_MODE_ARM
from build_progression_integration import arm_branch

BEFORE = '9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5'
OWNER = '8D4FC0A9973981D40FCA86CC639CF35D49AF580C13CC10B9810CAAB4D7636B43'
HOOK = 0x817B4


def build(before, owner):
    assert sha(before) == BEFORE and sha(owner) == OWNER
    meta = json.loads(owner)
    assert meta['output_sha256'] == BEFORE
    table = BASE + meta['table_span'][0]
    assert struct.unpack_from('<60I', before, table-BASE) == tuple(meta['header_pointers'])
    # The constructor copies ID 0 directly. Later cursor changes use the separate ID loader.
    assert struct.unpack_from('<5I', before, 0x817A4) == (
        0xE59F50F4, 0xE59F40F4, 0xE3A02C06, 0xEBFDFCF3, 0xE59F50EC)
    assert struct.unpack_from('<4I', before, 0x818A0) == (
        0x06005780, 0x080A28A0, 0x05000020, 0x080A2880)
    assembly = f"""
        push {{r0-r12,lr}}
        mrs r12,cpsr
        push {{r12}}
        ldr r12, ={GETTER}
        mov lr,pc
        bx r12
        rsb r0,r0,r0,lsl #4
        ldr r8, ={table}
        ldr r4,[r8,r0,lsl #2]
        ldr r5, =0x06005780
        mov r2,#0xc0
        ldr r12, =0x08000b84
        mov lr,pc
        bx r12
        pop {{r12}}
        msr cpsr_f,r12
        pop {{r0-r12,lr}}
        ldr r5, =0x05000020
        ldr pc, =0x080817b8
        .ltorg
    """
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(assembly)[0])
    allocator = Allocator(before)
    prior = meta['prior_excluded_extents'] + [[a['start'], a['end']] for a in meta['allocations']]
    exclude(allocator, prior)
    start = allocator.allocate(len(code), 'initial Guilmon localized portrait header', 4)
    after = bytearray(before)
    after[start:start+len(code)] = code
    struct.pack_into('<I', after, HOOK, arm_branch(HOOK, start))
    writes = [(HOOK, 4), (start, len(code))]
    inverse = bytearray(after)
    for at, size in writes:
        inverse[at:at+size] = before[at:at+size]
    assert bytes(inverse) == before
    return bytes(after), dict(input_sha256=BEFORE, output_sha256=sha(after), header_owner_sha256=OWNER,
        builder_sha256=sha(Path(__file__).read_bytes()), writes=writes, allocations=allocator.allocations,
        prior_excluded_extents=prior, table=table, initial_id=0, whole_image_inverse=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('input','owner','output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    data, meta = build(a.input.read_bytes(), a.owner.read_bytes())
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'component.gba').write_bytes(data)
    manifest = a.output/'manifest.json'
    manifest.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(meta['output_sha256'],sha(manifest.read_bytes()))


if __name__ == '__main__':
    main()

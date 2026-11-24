"""Use the original particle update only for the single-player earned Master name scene."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_mode24_link_cards import branch
from mode23_linker import compose

PARENT = '2922F5865C962A4AFA148DC80736ADBA96FDFE5786DAFB7F008845C7B529CFE7'
OWNER = '74AF7A5614AE9923EF81CC16B2657EE097046C81209766F2331DC2A755BB3F39'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ENTRY, RESUME = 0x08EA4BC0, 0x08EA4BD4
PARTICLES = 0x03003048
EXPORTS = ('m11p_start', 'm11p_tick')


def assembly(sym):
    # The retail name renderer owns 30*20 bytes of particle state at 03003048.
    # Its callback has been dormant since the score began. Restore/release that
    # sibling through the ordinary native exit, after its final custom callback.
    return f"""
m11p_start:
    push {{r0-r12,lr}}
    ldr r9,={PARTICLES-120:#x}
    ldr r10,={PARTICLES+128:#x}
    bl {sym['m24s_party_init']:#x}
    mov r0,#0
    str r0,[r10,#212]
    @ 73D3:0AB4 primes 6D7F:1A1F without submitting objects: all thirty
    @ start stationary and inside bounds, and every initial threshold is zero.
    bl 0x08012600
    bl 0x08012600
    bl 0x08012600
    and r6,r0,#15
    mov r6,r6,lsl #3
    bl 0x08012600
    mov r4,#0
    ldr r5,={PARTICLES:#x}
m11p_prime:
    bl 0x08012600
    and r0,r0,#15
    strb r0,[r5,#8]
    and r1,r4,#3
    mov r1,r1,lsl #7
    add r1,r1,#8
    add r1,r1,r6
    strh r1,[r5,#6]
    mov r0,#1
    strb r0,[r5,#9]
    add r4,r4,#1
    add r5,r5,#10
    cmp r4,#15
    addeq r5,r5,#2
    cmp r4,#30
    blo m11p_prime
    ldr r0,=0x03003cf8
    ldr r0,[r0]
    ldr r1,=m11p_tick
    str r1,[r0]
    pop {{r0-r12,lr}}
    b {RESUME:#x}

m11p_tick:
    push {{r0-r12,lr}}
    ldr r9,={PARTICLES-120:#x}
    ldr r10,={PARTICLES+128:#x}
    ldr r0,[r10,#212]
    add r0,r0,#1
    cmp r0,#30
    moveq r0,#0
    str r0,[r10,#212]
    bl {sym['m24s_particles']:#x}
    pop {{r0-r12,pc}}
.ltorg
"""


def build(image, source, raw_owner):
    assert (sha(image), sha(source), sha(raw_owner)) == (PARENT, SOURCE, OWNER)
    owner = json.loads(raw_owner)
    assert owner['output_sha256'] == PARENT
    assert struct.unpack_from('<I', image, 0xbfa10)[0] == PARTICLES
    assert struct.unpack_from('<I', image, 0xc0850)[0] == PARTICLES
    assert image[ENTRY-BASE:ENTRY-BASE+4] == bytes.fromhex('e70200eb')
    assert source[0x7747ee:0x7747ee+5] == bytes.fromhex('9a1f1a7f6d')
    prior = owner['prior_excluded_extents'] + [[a['start'], a['end']] for a in owner['allocations']]
    allocator = Allocator(image)
    exclude(allocator, prior)
    body = assembly(owner['symbols'])
    trial, _, _ = compose((body,), BASE, EXPORTS)
    start = allocator.allocate(len(trial), 'campaign Master original particle update', 4)
    code, symbols, linkage = compose((body,), BASE+start, EXPORTS)
    assert len(code) == len(trial)
    updates = ((ENTRY-BASE, branch(ENTRY, symbols['m11p_start'])), (start, code))
    result = bytearray(image)
    for raw, payload in updates:
        result[raw:raw+len(payload)] = payload
    return result, dict(input_sha256=PARENT, output_sha256=sha(result), source_sha256=SOURCE,
                        prior_owner_sha256=OWNER, symbols=symbols, linkage=linkage,
                        reused_symbols={k:owner['symbols'][k] for k in ('m24s_party_init','m24s_particles')},
                        storage_exports=owner['storage_exports'], prior_excluded_extents=prior,
                        allocations=allocator.allocations, module_sha256=sha(Path(__file__).read_bytes()),
                        writes=[dict(offset=i,size=len(p),before_sha256=sha(image[i:i+len(p)]),
                                     after_sha256=sha(p)) for i,p in updates])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'input', 'owner', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    rom, owner = build(a.input.read_bytes(), a.source.read_bytes(), a.owner.read_bytes())
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'component.gba').write_bytes(rom)
    manifest = a.output/'manifest.json'
    manifest.write_text(json.dumps(owner,indent=2)+'\n', encoding='utf-8', newline='\n')
    print(owner['output_sha256'],sha(manifest.read_bytes()))


if __name__ == '__main__':
    main()


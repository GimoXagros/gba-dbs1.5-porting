"""Restore Ver. 1.5 tag-count eligibility and the two-character ending award queue."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude
from mode23_linker import compose


SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
PARENT = "A88751B6509BF51D6B83C01F6BAA02D522D0C5E30B276B25B783CF2199204A84"
OWNER = "744860E09F7B8F4B586BF230B80633ECFCE5FFD35A17B641C9E6028C04680653"
EXPORTS = ("roster_clear_tags", "roster_filter", "roster_second", "roster_save_candidate")


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def assemble(address, read_snapshot):
    text = f"""
roster_clear_tags:
    push {{r0-r12,lr}}
    ldr r5,roster_config
    ldrh r2,[r5,#0x1a]
    tst r2,#1
    bne roster_done
    sub sp,sp,#44
    mov r0,sp
    bl {read_snapshot:#x}
    cmp r0,#0
    bne roster_release
    add r3,sp,#0x1a
    mov r4,#4
    mov r7,#0
roster_scan:
    ldrh r2,[r3],#2
    cmp r2,#0
    beq roster_next
    orr r7,r7,#0x10
    cmp r4,#8
    orrhs r7,r7,#0x20
roster_next:
    add r4,r4,#1
    cmp r4,#11
    bne roster_scan
    tst r7,#0x10
    movne r0,#0x10
    blne roster_save_candidate
    tst r7,#0x20
    movne r0,#0x20
    blne roster_save_candidate
roster_release:
    add sp,sp,#44
roster_done:
    pop {{r0-r12,pc}}
roster_save_candidate:
    push {{r0-r12,lr}}
    ldrb r1,[r5,#0x19]
    bic r0,r0,r1
    ldrb r2,[r5,#0x18]
    orr r2,r2,r0
    strb r2,[r5,#0x18]
    bl 0x0801fa98
    bl 0x080c12ec
    ldr r1,roster_config
    ldrb r0,[r1,#0x19]
    ldr r1,roster_record
    strh r0,[r1,#0x12]
    bl 0x0801fc5c
    pop {{r0-r12,pc}}
roster_filter:
    ldrb r0,[r1,#0x18]
    and r0,r0,#0x30
    strb r0,[r1,#0x18]
    ldrb r8,[r1,#0x19]
    bics r0,r0,r8
    beq 0x080bf91c
    ldr r3,roster_list
    b 0x080bf58c
roster_second:
    tst r0,#0x20
    beq 0x080bf684
    ldr r8,roster_count
    ldrh r9,[r8]
    cmp r9,#2
    bhs 0x080bf684
    add r5,r3,r9,lsl #1
    mov r2,#12
    strh r2,[r5]
    add r9,r9,#1
    strh r9,[r8]
    orr r0,r0,#0x2000
    b 0x080bf684
roster_config: .word 0x03002310
roster_record: .word 0x03001120
roster_list: .word 0x03003cf0
roster_count: .word 0x03003cf4
"""
    return compose((text,), address, EXPORTS)


def branch(at, target, link=False):
    delta = target - BASE - at - 8
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("roster ARM branch")
    return struct.pack("<I", (0xEB000000 if link else 0xEA000000) | ((delta >> 2) & 0xFFFFFF))


def build(source, before, owner):
    if (sha(source), sha(before), sha(owner)) != (SOURCE, PARENT, OWNER):
        raise ValueError("unrecognized Ver. 1.5 source, native image or ownership manifest")
    parent = json.loads(owner)
    assert parent["output_sha256"] == PARENT
    service = parent["storage_exports"]["m22_read_snapshot"]
    assert service == 0x08FB6130
    extents = parent["prior_excluded_extents"] + [[block["start"], block["end"]] for block in parent["allocations"]]
    allocator = Allocator(before)
    exclude(allocator, extents)
    size = len(assemble(0x08F00000, service)[0])
    offset = allocator.allocate(size, "Ver.1.5 tag-count eligibility and ending roster awards", 4)
    assert all(offset + size <= a or b <= offset for a, b in extents)
    code, symbols, linkage = assemble(BASE + offset, service)
    assert len(code) == size and before[offset:offset+size] == b"\xff" * size
    sites = {
        0x08B364: (branch(0x08B364, 0x085B1000, True), branch(0x08B364, symbols["roster_clear_tags"], True)),
        0x0BF4C0: (struct.pack("<I", 0xE5D10018), branch(0x0BF4C0, symbols["roster_filter"])),
        0x0BF5D0: (struct.pack("<I", 0xE3100001), branch(0x0BF5D0, symbols["roster_second"])),
        # The earlier hook promoted bit 20 even when the queue had no space.
        0x5B1104: (struct.pack("<I", 0xE3100020), branch(0x5B1104, 0x085B110C)),
        offset: (before[offset:offset+size], code),
    }
    image = bytearray(before)
    writes = []
    for at, (expected, replacement) in sorted(sites.items()):
        assert before[at:at+len(expected)] == expected and len(replacement) == len(expected)
        image[at:at+len(replacement)] = replacement
        writes.append(dict(offset=at, size=len(replacement), before_sha256=sha(expected), after_sha256=sha(replacement)))
    return bytes(image), dict(input_sha256=PARENT, output_sha256=sha(image), source_sha256=SOURCE, prior_owner_sha256=OWNER,
        symbols=symbols, storage_exports=parent["storage_exports"], prior_excluded_extents=extents,
        allocations=allocator.allocations, linkage=linkage, writes=writes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "input", "owner", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    image, manifest = build(args.source.read_bytes(), args.input.read_bytes(), args.owner.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "component.gba").write_bytes(image)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(manifest["output_sha256"], sha((args.output / "manifest.json").read_bytes()))

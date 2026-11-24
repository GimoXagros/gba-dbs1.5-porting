"""Source-bound relocatable mode23 presentation resources.

Caller supplies a proven ROM placement. No file or image is changed here.
Unknown bank windows, layouts, palette populations or P1 references fail.
"""
import hashlib
import struct

from build_full_asset_poc import convert_tile, parse_wsc_far_descriptor
from build_shoot_initializer import parse_p1, convert_p1
from convert_wsc_palette_block import convert_block

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000


def far(words):
    off, seg, bank = words
    linear = seg * 16 + off
    if not 0x80 <= bank <= 0xff or not 0x20000 <= linear < 0x30000:
        raise ValueError("mode23 resource outside proven C2 bank window")
    return (bank & 127) * 65536 + linear - 0x20000


def participant_rows(source):
    rows = []
    for evolved, raw in ((False, 0x74A580), (True, 0x74A760)):
        for ident in range(15):
            words = struct.unpack_from("<16H", source, raw + ident * 32)
            rows.append({"identity": ident, "evolved": evolved,
                         "source_row": raw + ident * 32,
                         "p0": far(words[0:3]), "p1": far(words[3:6]),
                         "p2": far(words[6:9])})
    return rows


def p0(source, raw, target, descriptor_count):
    table, seg, bank, c0, c1 = struct.unpack_from("<IHHII", source, raw)
    if table != 16:
        raise ValueError("unsupported mode23 P0 table offset")
    first = struct.unpack_from("<H", source, raw + 18)[0]
    if first < 20 or (first - 16) % 4 or first > 0x4000:
        raise ValueError("unsupported mode23 P0 population")
    count = (first - 16) // 4
    layouts, cursor = [], first
    for index in range(count):
        n, offset = struct.unpack_from("<2H", source, raw + 16 + index * 4)
        if not n or n > 128 or offset != cursor:
            raise ValueError("mode23 P0 layout extent is not contiguous")
        layouts.append(source[raw + offset:raw + offset + n * 4])
        cursor += n * 4
    descriptors = far((0, seg, bank))
    tiles = []
    if not 0 < descriptor_count <= 1024:
        raise ValueError("mode23 P0 lacks typed P1 descriptor population")
    for index in range(descriptor_count):
        at = descriptors + index * 8
        length, physical = parse_wsc_far_descriptor(source, at)
        tiles.append((physical, b"".join(convert_tile(source[p:p + 32])
                                       for p in range(physical, physical + length, 32))))
    if not tiles:
        raise ValueError("mode23 P0 unexpectedly has no tile data")
    out = bytearray(16 + count * 8)
    for index, data in enumerate(layouts):
        struct.pack_into("<2I", out, 16 + index * 8, len(data) // 4,
                         BASE + target + len(out))
        out.extend(data)
    while len(out) % 4:
        out.append(0)
    descriptor_target = len(out)
    out.extend(bytes(len(tiles) * 8))
    while (target + len(out)) % 32:
        out.append(0)
    for index, (_, data) in enumerate(tiles):
        struct.pack_into("<2I", out, descriptor_target + index * 8,
                         len(data), BASE + target + len(out))
        out.extend(data)
    struct.pack_into("<4I", out, 0, BASE + target + 16,
                     BASE + target + descriptor_target, c0, c1)
    return bytes(out), {"source": raw, "layouts": count,
                        "layout_bytes": sum(map(len, layouts)),
                        "descriptors": len(tiles),
                        "tile_bytes": sum(len(x[1]) for x in tiles)}


def parsed_p1(source, raw):
    head, reserved, count, first = struct.unpack_from("<4H", source, raw)
    if head != 4 or reserved or not count or first < 12 or (first - 4) % 8:
        raise ValueError("unsupported mode23 P1 header")
    end = first
    for index in range((first - 4) // 8):
        n, payload, a, b = struct.unpack_from("<4H", source, raw + 4 + index * 8)
        if not 0 < n < 1024 or payload < first or not a:
            raise ValueError("unsupported mode23 P1 command")
        end = max(end, payload + n * 12, a + 8, b + 10 if b else 0)
        for j in range(n):
            tail = struct.unpack_from("<H", source, raw + payload + j * 12 + 10)[0]
            if tail:
                end = max(end, tail + 10)
    if end > 0xffff or (raw & 0xffff) + end > 0x10000:
        raise ValueError("mode23 P1 crosses its source bank")
    return parse_p1(source, raw, end)


def p1(source, raw, target):
    parsed = parsed_p1(source, raw)
    if any(item[0] >> 8 not in (0, 255) for payload in parsed["payloads"] for item in payload):
        raise ValueError("mode23 P1 requires an unbound embedded sound command")
    return convert_p1(parsed, target), {"source": raw, "source_bytes": len(parsed["data"]),
                                      "events": len(parsed["commands"]),
                                      "items": sum(len(p) for p in parsed["payloads"])}


def p2(source, raw, target):
    # All selected mini/scene views currently have one source palette block.
    # The leading record/population words are validated, not assumed.
    header = struct.unpack_from("<3H", source, raw)
    if header[0:2] != (1, 1) or not 8 <= header[2] <= 15:
        raise ValueError(f"unsupported mode23 palette header at {raw:X}: {header}")
    return convert_block(source[raw:raw + 38]), {"source": raw, "source_bytes": 38}


def build(source, target):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE or target % 32:
        raise ValueError("mode23 source hash or placement alignment")
    rows = participant_rows(source)
    fixed = {
        "intro": (0x3D58F0, 0x3D87B0, 0x3D7E20),
        "aim": (0x3D6D20, 0x3D0500, 0x3D86F0),
        "item": (0x3D8690, 0x3D8D10, 0x3D86C0),
        "pickup": (0x3BDCC0, 0x3C8CF0, 0x3D7D60),
        "round_message": (0x3CB870, 0x3D29E0, 0x3D7EB0),
        "round_start": (0x14FE60, 0x3D6E10, 0x04FFC0),
        "failure": (0x11FE80, 0x37FE00, 0x3D7BB0),
    }
    all_views = rows + [{"name": name, "p0": v[0], "p1": v[1], "p2": v[2]}
                       for name, v in fixed.items()]
    descriptor_counts = {}
    for view in all_views:
        parsed = parsed_p1(source, view["p1"])
        ids = {item[2] for payload in parsed["payloads"] for item in payload}
        if not ids or min(ids) != 0 or max(ids) >= 1024:
            raise ValueError("unsupported P1 descriptor domain")
        # Native12C94..CA0 tests presentation flag2 before adding item.word2*8.
        # Static resources always use descriptor0, regardless of layout frame.
        flags = struct.unpack_from("<H", source, view["p0"] + 14)[0]
        population = max(ids) + 1 if flags & 2 else 1
        layout_count = (struct.unpack_from("<H", source, view["p0"] + 18)[0] - 16) // 4
        layout_ids = {item[1] for payload in parsed["payloads"] for item in payload}
        if min(layout_ids) < 0 or max(layout_ids) >= layout_count:
            raise ValueError("P1 layout selection escapes typed P0")
        descriptor_counts[view["p0"]] = max(descriptor_counts.get(view["p0"], 0), population)
    out, mapping, details = bytearray(), {}, []
    for view in all_views:
        for kind, converter in (("p0", p0), ("p1", p1), ("p2", p2)):
            key = kind, view[kind]
            if key in mapping:
                continue
            while (target + len(out)) % 32:
                out.append(0)
            at = target + len(out)
            if kind == "p0":
                data, detail = converter(source, view[kind], at, descriptor_counts[view[kind]])
            else:
                data, detail = converter(source, view[kind], at)
            mapping[key] = BASE + at
            out.extend(data)
            details.append({"kind": kind, "target": at, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest().upper(), **detail})
    native_views = [{**view, "native": [mapping[(kind, view[kind])]
                                        for kind in ("p1", "p0", "p2")]}
                    for view in all_views]
    while len(out) % 4:
        out.append(0)
    tables = {}
    for name, raw, size in (("base_params", 0x74A490, 120),
                            ("evolved_params", 0x74A508, 120)):
        tables[name] = BASE + target + len(out)
        out.extend(source[raw:raw + size])
    tables["participant_views"] = BASE + target + len(out)
    for view in native_views[:30]:
        out.extend(struct.pack("<3I", *view["native"]))
    for view in native_views[30:]:
        tables[view["name"]] = BASE + target + len(out)
        out.extend(struct.pack("<3I", *view["native"]))
    return bytes(out), {"source_sha256": SOURCE, "target": target,
                        "bytes": len(out), "resources": details,
                        "views": native_views, "tables": tables}


def assembly(tables):
    text = """
m23_actor_resources:
push {r4-r11,lr}
mov r6,r0
ldrb r0,[r6,#3]
add r0,r0,r0,lsl #1
ldr r1,m23_asset_participants
add r1,r1,r0,lsl #2
ldrh r0,[r6]
tst r0,#0x8000
addne r1,r1,#180
ldrb r3,[r6,#2]
add r2,r3,r3,lsl #2
mov r2,r2,lsl #2
add r2,r2,#0x100
add r0,r6,#0x24
mov r12,#0
bl m23_view_install
pop {r4-r11,lr}
bx lr
m23_evolved_param:
ldr r1,m23_asset_evolved_params
add r0,r1,r0,lsl #3
bx lr
m23_base_param:
ldr r1,m23_asset_base_params
add r0,r1,r0,lsl #3
bx lr

m23_item_resources:
add r0,r0,#0x24
ldr r1,m23_asset_item
mov r2,#0x1e0
add r2,r2,#10
mov r3,#6
mov r12,#0
b m23_view_install
m23_pickup_resources:
add r0,r0,#0x24
ldr r1,m23_asset_pickup
mov r2,#0x170
add r2,r2,#12
mvn r3,#0
mov r12,#6
b m23_view_install
m23_intro_resources:
ldr r1,m23_asset_intro
mov r2,#1
mov r3,#7
mov r12,#0
b m23_view_install
m23_aim_resources:
ldr r1,m23_asset_aim
mov r2,#0x1c0
add r2,r2,#12
mov r3,#0
mov r12,#0
b m23_view_install
m23_round_message_resources:
mov r12,r1
ldr r1,m23_asset_round_message
mov r2,#1
mov r3,#4
b m23_view_install
m23_round_start_resources:
ldr r1,m23_asset_round_start
mov r2,#1
mov r3,#4
mov r12,#0
b m23_view_install
m23_failure_resources:
ldr r1,m23_asset_failure
mov r2,#1
mov r3,#0
mov r12,#3
b m23_view_install

m23_view_install:
push {r4-r11,lr}
mov r6,r0
mov r7,r1
mov r8,r3
mov r9,r12
bl m23_present_construct
mov r0,r6
mov r1,r9
bl m23_present_event
ldrh r0,[r6,#8]
orr r0,r0,#0x2000
strh r0,[r6,#8]
ldr r0,[r7,#8]
mov r1,r8
bl m23_palette
pop {r4-r11,lr}
bx lr
"""
    keys = {"participants": "participant_views", "evolved_params": "evolved_params",
            "base_params": "base_params", "item": "item", "pickup": "pickup",
            "intro": "intro", "aim": "aim", "round_message": "round_message",
            "round_start": "round_start", "failure": "failure"}
    return text + "\n".join(f"m23_asset_{name}: .word {tables[key]}" for name, key in keys.items()) + "\n"

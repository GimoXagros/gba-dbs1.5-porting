#!/usr/bin/env python3
"""Independent bytes, native-resource, ABI and ownership checks for the selector.

This neither imports the builder nor starts a game. Fault cases are a bounded
native-order model; persistence and display require separate exact-ROM runs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_options_korean_poc import need, sha, u32, u16, layouts, expected_text, GBA_SHA, FONT_SHA
from encode_digicode_reading import CATALOG, encode

BASE = 0x08000000
ROUTINES = {"get_language": 0x633400, "palette_choice": 0x633440,
    "constructor_choice": 0x633480, "route_object": 0x6334C0, "find_task": 0x633540,
    "confirm": 0x633600, "input_guard": 0x633800, "create_task": 0x633A00,
    "init_object": 0x633C00, "set_frame": 0x633D00,
    "draw_object": 0x633D80, "tick": 0x633E00}


def decode_layouts(data, p0, count):
    table, desc = u32(data, p0) - BASE, u32(data, p0 + 4) - BASE
    size, atlas = u32(data, desc), u32(data, desc + 4) - BASE
    need(size % 32 == 0 and 0 < size <= 8192 and atlas + size <= len(data), "bounded source atlas")
    result = []
    for index in range(count):
        total, pointer = u32(data, table + index*8), u32(data, table + index*8 + 4) - BASE
        need(0 < total <= 20 and 0 <= pointer <= len(data) - total*4, "complete bounded layout")
        parts = [struct.unpack_from("<Hbb", data, pointer + n*4) for n in range(total)]
        pixels = {}
        for tile, top, left in parts:
            need((tile & 0x3FFF) < size//32, "all native tile indices are within source pool")
            for y in range(8):
                for x in range(8):
                    xx, yy = (7 - x if tile & 0x4000 else x), (7 - y if tile & 0x8000 else y)
                    value = data[atlas + (tile & 255)*32 + yy*4 + xx//2] >> (4*(xx % 2)) & 15
                    if value:
                        need((left + x, top + y) not in pixels or p0 in (0x9F980, 0xA05E0),
                             "new authored layouts do not overlap; original layout layering is retained")
                        pixels[left + x, top + y] = value
        result.append((parts, pixels))
    need(struct.unpack_from("<4H", data, p0 + 8) == (5, size//32 - 1, size - 32, 8), "exact P0 header")
    return result, atlas + size


def event_layouts(data, p1, count):
    table = u32(data, p1) - BASE
    result, end = [], table + count*16
    for event in range(count):
        total, pointer = u32(data, table + event*16), u32(data, table + event*16 + 4) - BASE
        need(0 < total <= 32 and 0 <= pointer <= len(data) - total*16, "bounded complete P1 frames")
        result.append([u16(data, pointer + n*16 + 2) for n in range(total)])
        end = max(end, pointer + total*16)
    return result, end


def branch_target(data, at, link=True):
    value = u32(data, at)
    need(value >> 24 == (0xEB if link else 0xEA), "actual ARM branch opcode")
    delta = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
    return at + 8 + delta*4


def expected_digicode(reading,catalog,glyphs):
    ink,position=set(),1
    for key in encode(reading,catalog):
        rows=glyphs[key]
        need(len(rows)==16 and any(rows),"complete required Digicode bitmap")
        points={(x,y-15) for y,row in enumerate(rows) for x in range(8) if row & (128 >> x)}
        left,right=min(x for x,y in points),max(x for x,y in points)
        ink.update((position+x-left,y) for x,y in points)
        position += right-left+2
    pixels={(x+dx,y+dy):2 for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}
    pixels.update({point:1 for point in ink})
    return pixels,max(x for x,y in pixels)+1


def failure_model():
    """Native 25-block first-failure semantics, including a torn header."""
    old = bytearray((i*17 + 3) & 255 for i in range(200))
    old[:16] = b"DIMPS Ver0.72   "
    old[15] = 0xA0
    old[192:196] = sum(old[:192]).to_bytes(4, "little")
    original = bytes(old)

    def write(ram, physical, failure):
        ram[192:196] = sum(ram[:192]).to_bytes(4, "little")
        for block in range(25):
            if block == failure:
                return False
            physical[block*8:block*8 + 8] = ram[block*8:block*8 + 8]
        return True

    cases, torn = 0, 0
    for failure in range(25):
        ram, physical = bytearray(original), bytearray(original)
        ram[15] = 0xA1
        need(not write(ram, physical, failure), "modeled first write failure")
        ram[15], ram[192:196] = original[15], original[192:196]
        need(bytes(ram) == original, "exact old tag and checksum restored in RAM")
        if 2 <= failure <= 24:
            need(physical[15] == 0xA1 and physical[192:196] == original[192:196], "torn physical header counterexample")
            torn += 1
        # B may exit only after all old blocks have actually been written.
        for repair_failure in range(25):
            copy = bytearray(physical)
            need(not write(ram, copy, repair_failure), "failed B repair must retain dirty state")
            need(bytes(ram) == original, "repair preserves exact valid old RAM record")
            cases += 1
        need(write(ram, physical, None) and bytes(physical) == original, "successful B repairs every block")
        # A may retry the new record; it commits only after all blocks succeed.
        ram[15] = 0xA1
        need(write(ram, physical, None) and physical == ram and physical[15] == 0xA1,
             "successful A retry commits coherent new record")
    return dict(first_failures=25, failed_repairs=cases, torn_header_cases=torn,
        power_failure_atomic=False, kind="finite native-order model, not device fault injection")


def verify(before, after, gba, font, draft, config, manifest):
    need(sha(gba) == GBA_SHA and sha(font) == FONT_SHA, "exact commercial source and licensed font")
    need(len(before) == len(after) == 0x800000 and manifest["input_sha256"] == sha(before) and
         manifest["output_sha256"] == sha(after), "exact full-image identities")
    need(sha(before) in {"AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF",
                        "F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E"},
         "supported immutable predecessor")
    need(before[0x9F980:0xA1060] == after[0x9F980:0xA1060] == gba[0x9F980:0xA1060],
         "both original atlases, layouts, events and palettes remain intact")
    original, _, _ = layouts(gba, 0x9F980)
    korean, korean_end = decode_layouts(after, 0x632000, 32)
    jp_events, _ = event_layouts(gba, 0xA02E8, 12)
    replaced = set()
    for row in draft["entries"]:
        event, frame = row["event"], row.get("frame", 0)
        index = jp_events[event][frame]
        expected, width = expected_text(font.decode("utf-8"), row["ko_draft"])
        left = 8 if event in (0, 2, 4, 6, 7) else ((24 if event == 11 else 40) - width)//2
        expected = {(x + left, y): color for (x, y), color in expected.items()}
        if event in (0, 2, 4, 6, 7):
            expected.update({point: color for point, color in original[index][1].items() if point[0] < 8})
        need(korean[index][1] == expected and index not in replaced, "all exact Korean text pixels")
        replaced.add(index)
    need(replaced == {0, 4, 5, 6, 7, 8, 19, 20, 30, 31}, "exact ten Korean frames")
    for index in set(range(32)) - replaced:
        need(korean[index][1] == original[index][1], "every untranslated Korean decoration/number retained")
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
    need(manifest["digicode_catalog_sha256"]==sha(json.dumps(catalog,ensure_ascii=False,sort_keys=True).encode("utf-8")),
         "authoritative Japanese-reading catalog identity")
    glyphs={key:bytes.fromhex(value) for key,value in manifest["digicode_glyph_rows"].items()}
    need(sha(b"".join(glyphs[g["id"]] for g in catalog["glyphs"]+catalog["latin_glyphs"])) ==
         "E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195",
         "independently reviewed exact98 Digicode row-byte identities")
    digicode,digicode_end=decode_layouts(after,0x639000,32)
    for row in draft["entries"]:
        event,frame=row["event"],row.get("frame",0)
        index=jp_events[event][frame]
        expected,width=expected_digicode(row["ja_reading"],catalog,glyphs)
        label=event in (0,2,4,6,7)
        left=8 if label else ((24 if event==11 else 40)-width)//2
        expected={(x+left,y):color for (x,y),color in expected.items()}
        if label:
            expected.update({point:color for point,color in original[index][1].items() if point[0]<8})
        need(digicode[index][1]==expected,"every native-decoded Digicode pixel follows the Japanese reading")
    for index in set(range(32))-replaced:
        need(digicode[index][1]==original[index][1],"all original Digicode numbers/decorations retained")
    selector, p1 = decode_layouts(after, 0x637000, 16)
    selector_events, selector_end = event_layouts(after, p1, 4)
    need(selector_events == [list(range(4*e, 4*e + 4)) for e in range(4)], "all selector frame identities")
    for event, key in enumerate(("labels", "names", "save_errors")):
        for frame, text in enumerate(config[key]):
            expected, width = (expected_digicode(text,catalog,glyphs) if frame==3 else expected_text(font.decode("utf-8"), text))
            left = 8 if event == 0 else (56 - width)//2
            expected = {(x + left, y): color for (x, y), color in expected.items()}
            need(selector[event*4 + frame][1] == expected, "every new label/name/error pixel matches exact font; no new decorative square")
    for i, index in enumerate([jp_events[8][j] for j in (0,1,1,2)]):
        expected = [((tile, y, x + 24 if x == 48 else x)) for tile, y, x in original[index][0]]
        need(selector[12 + i][0] == expected, "preserved native arrows and extended value-column spacing")

    hooks = {0xC15F4:"palette_choice", 0xC1824:"constructor_choice", 0xC184C:"create_task",
             0xC328C:"input_guard", 0xC32FC:"confirm"}
    creations, events = [], []
    for at in range(0xC2564, 0xC315C, 4):
        if u32(gba, at) >> 24 != 0xEB:
            continue
        target = branch_target(gba, at)
        if target == 0x127E4:
            creations.append(at)
            hooks[at] = "route_object"
        if target in (0x12874, 0x129C8):
            instruction = u32(gba, at - (8 if target == 0x12874 else 12))
            need(instruction & 0xFFFFFF00 == 0xE3A08000, "native event immediate")
            events.append(instruction & 255)
    need(len(creations) == 15 and events == [0,2,4,6,7,1,8,3,8,8,5,5,8,11,9], "complete native presentations")
    for at, name in hooks.items():
        need(branch_target(after, at) == ROUTINES[name], "actual native hook reaches owned routine")
    words = {0xC32B8:0xE3A02005, 0xC32C4:0xE3520005, 0xC33F4:0x3FB,
        0xC1BE4:0xE3A08005, 0xC28B4:0xE3A08005}
    for at,y in ((0xC1A08,54),(0xC1AC0,72),(0xC1BAC,90),(0xC1C64,126),
                 (0xC1EF8,54),(0xC2090,72),(0xC22C8,90)):
        for offset in (0,0xCD0):
            words[at + offset]=0xE3A00000 | y
    for at,reg,y in ((0xC34E0,9,90),(0xC34EC,9,90),(0xC36E0,9,54),(0xC36EC,9,72),
                    (0xC36F8,9,90),(0xC3704,9,126),(0xC39C8,2,54),(0xC3BA8,2,72)):
        words[at]=0xE3A00000 | reg << 12 | y
    need(all(u32(after, at) == value for at, value in words.items()), "cursor, both constructors, relayout and complete retirement")
    blocks = manifest["machine_code"]
    need({row["name"]: row["raw"] for row in blocks} == ROUTINES, "complete fixed installed routine population")
    boundaries = {BASE + row["raw"] + offset for row in blocks for offset in range(0, row["code_bytes"], 4)}
    native_calls = {BASE + x for x in (0x127E4,0x11F90,0x1FC5C,0x11AC4,0x129C8,0x12C28,0x1201C,0x12030)}
    code = {}
    for block in blocks:
        at, size = block["raw"], block["code_bytes"]
        insns = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(after[at:at + size], BASE + at))
        need(sum(i.size for i in insns) == size, "no undecoded installed machine bytes")
        need([dict(address=i.address, mnemonic=i.mnemonic, operands=i.op_str) for i in insns] == block["instructions"],
             "manifest describes final placed instructions")
        for i in insns:
            need(bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(i.mnemonic + " " + i.op_str, i.address)[0]) == i.bytes,
                 "independent instruction decode/assemble identity")
            value = int.from_bytes(i.bytes, "little")
            if value & 0x0E000000 == 0x0A000000:
                delta = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
                need(i.address + 8 + delta*4 in boundaries | native_calls, "every branch reaches a known code boundary")
            if value & 0x0F7F0000 == 0x051F0000:
                target = i.address + 8 + (value & 4095)*(1 if value & 0x800000 else -1)
                need(BASE + at + size <= target < BASE + at + size + block["literal_bytes"], "literal belongs to this routine tail")
        code[block["name"]] = [(i.mnemonic, i.op_str) for i in insns]
    need("r8" in code["find_task"][0][1] and code["find_task"][-2][0] == "pop" and
         "r8" in code["find_task"][-2][1], "priority lookup protects the caller's row register")
    need(("str", "r7, [r5, #0xc0]") in code["input_guard"] and
         ("strb", "r6, [r5, #0xf]") in code["confirm"] and
         ("str", "r7, [r5, #0xc0]") in code["confirm"], "failed commit and repair preserve exact old tag/checksum")
    need(("and", "r6, r6, #0xc0") in code["input_guard"] and
         ("strh", "r6, [r1, #2]") in code["input_guard"], "dirty-state buttons filtered for all native tasks")
    need(("mov", "r2, #0x3e") in code["create_task"] and
         ("add", "r5, r5, #0x50") in code["create_task"] and
         ("orr", "r0, r0, #0x200") in code["tick"], "248-byte clear, three 80-byte objects and retirement bit")
    need(("cmp","r0, #3") in code["get_language"] and ("cmp","r1, #3") in code["confirm"] and
         ("cmp","r2, #3") in code["tick"],"all four tagged choices are reachable and bounded")
    tick=code["tick"]
    first_draw=tick.index(("bl",f"#0x{BASE+ROUTINES['draw_object']:x}"))
    need(tick[first_draw-4]==("cmp","r7, #0") and tick[first_draw-3][0]=="bne",
         "save error bypasses only the new label before rendering full error value")
    need(after[0x11A84:0x12058] == gba[0x11A84:0x12058] and
         u32(gba,0x11BC0) == 0x02010000 and u32(gba,0x11AC0)*4 == 52*0x118 and
         u32(gba,0x11AD4) == 0x12855F46 and u32(gba,0x12024) == 0xE2800018,
         "actual native allocator pool, stride, payload start and lifetime functions unchanged")
    need(after[0x1F894:0x1FD30] == gba[0x1F894:0x1FD30] and
         after[0x127E4:0x12DD8] == gba[0x127E4:0x12DD8] and
         after[0x11708:0x11854] == gba[0x11708:0x11854], "record, renderer and transfer dependencies unchanged")
    budgets = []
    for language_index, (name, p0, native_p1) in enumerate((("en",0xA05E0,0xA0D68),
            ("ja",0x9F980,0xA02E8),("ko",0x632000,0xA02E8),("digicode",0x639000,0xA02E8))):
        decoded, _ = decode_layouts(after, p0, 32)
        frame_ids, _ = event_layouts(after, native_p1, 12)
        old = sum(max(len(decoded[index][0]) for index in frame_ids[event]) for event in events)
        extra = max(len(selector[language_index][0]) +
            max(len(selector[4 + i][0]) + len(selector[12 + i][0]) for i in range(4)),
            len(selector[8 + language_index][0]))
        need(old + extra <= 127 and (old + extra)*32 <= 4096, "all concurrent OAM and VRAM-staging consumers fit")
        budgets.append(dict(language=name, existing=old, selector=extra, maximum_oam=old + extra,
                            maximum_tile_bytes=(old + extra)*32))
    need(budgets == manifest["budgets"], "independently recovered whole-screen budgets")
    allowed = {(0x632000, korean_end - 0x632000), (0x637000, selector_end - 0x637000),
               (0x639000,digicode_end-0x639000)}
    allowed |= {(row["raw"], row["code_bytes"] + row["literal_bytes"]) for row in blocks}
    allowed |= {(at,4) for at in hooks.keys() | words.keys()}
    writes = manifest["expected_writes"]
    need(len(writes) == len(allowed) and {(w["raw"],w["bytes"]) for w in writes} == allowed, "exact Expected Write population")
    inverse, last = bytearray(after), 0
    for w in sorted(writes, key=lambda x:x["raw"]):
        at, end = w["raw"], w["raw"] + w["bytes"]
        need(at >= last and w["before_sha256"] == sha(before[at:end]) and w["after_sha256"] == sha(after[at:end]),
             "disjoint immutable before/after Expected Writes")
        if at >= 0x632000:
            need(before[at:end] == b"\xff"*(end - at), "exact new allocation source bytes")
        inverse[at:end], last = before[at:end], end
    need(inverse == before, "every final ROM difference explained, all other data intact")
    return dict(schema=1,status="PASS",kind="independent-options-selector-artifact-verification",
        rom_sha256=sha(after), supported_languages=["en","ja","ko","digicode"], budgets=budgets,
        new_task_payload_bytes=248, native_task_payload_capacity=256, native_task_slots=52,
        decoded_instructions=sum(len(x) for x in code.values()), native_presentations=15,
        modeled_save_failures=failure_model(), runtime_claim=False, supplied_save_accessed=False,
        four_language_feature_complete=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before","after","gba","font","manifest","output"):
        parser.add_argument(name,type=Path)
    root=Path(__file__).resolve().parents[1]
    parser.add_argument("--draft",type=Path,default=root/"localization/options-draft.json")
    parser.add_argument("--selector",type=Path,default=root/"localization/options-selector.json")
    parser.add_argument("--capture-directory",type=Path)
    args=parser.parse_args()
    need(all(p is None or p.suffix.lower() != ".sav" for p in vars(args).values()), "save paths forbidden")
    result=verify(*(getattr(args,k).read_bytes() for k in ("before","after","gba","font")),
        *(json.loads(getattr(args,k).read_text(encoding="utf-8")) for k in ("draft","selector","manifest")))
    if args.capture_directory:
        result["runtime_observation"]=verify_capture(args.capture_directory,args.after.read_bytes(),
            args.gba.read_bytes(),json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("[Independent Options selector verification] PASS")


def verify_capture(directory, after, gba, manifest):
    from verify_native_capture_invariants import inspect
    invariants=inspect(directory,gba)
    capture=json.loads((directory/"capture.json").read_text(encoding="utf-8"))
    need(capture["rom"]["sha256"] == sha(after) == manifest["output_sha256"], "snapshot belongs to this exact selector ROM")
    iwram,ewram,vram,oam=((directory/name).read_bytes() for name in ("iwram.bin","ewram.bin","vram.bin","oam.bin"))
    need(u16(iwram,0x2310) == 14, "stable natural Options mode")
    tasks={}
    for slot in range(52):
        at=0x10000+slot*0x118
        if u16(ewram,at+0x10)&2:
            priority=u32(ewram,at+4)
            need(priority not in tasks, "unique live task priorities")
            tasks[priority]=at+0x18
    need(0x1500 in tasks and u16(iwram,0x1338) == len(tasks) == 11, "one new task within the actual native52-slot pool")
    task=tasks[0x1500]
    pending,entry,error=struct.unpack_from("<3H",ewram,task)
    count=len(manifest["language_tags"])
    need(pending < count and entry < count and error in (0,1), "bounded live selection/entry/error state")
    need(u32(ewram,task-0x18) == BASE+ROUTINES["tick"], "actual scheduler callback reaches selector")
    options_p0=(0xA05E0,0x9F980,0x632000,0x639000)[entry]
    options_p1=0xA0D68 if entry == 0 else 0xA02E8
    options_p2=0xA1038 if entry == 0 else 0xA05B8
    native_layouts,_=decode_layouts(after,options_p0,32)
    original_objects=[]
    for priority,offsets in {0x1000:(8,0x5C,0xB0),0x1100:(8,0x5C),0x1200:(4,0x58),
            0x1300:(4,0x58),0x1400:(8,0x5C,0xB0),0x500:(8,0x5C),0x1600:(4,)}.items():
        need(priority in tasks,"every original presentation task remains live")
        for offset in offsets:
            at=tasks[priority]+offset
            need(tuple(u32(ewram,at+d) for d in (0x44,0x48,0x4C)) ==
                 (BASE+options_p1,BASE+options_p0,BASE+options_p2),"actual selected native resource tuple")
            layout=u16(ewram,at+0x18)
            need(layout < 32,"valid native presentation layout")
            original_objects.append(dict(address=0x02000000+at,x=u16(ewram,at),y=u16(ewram,at+2),
                event=u16(ewram,at+0xE),layout=layout,parts=len(native_layouts[layout][0])))
    need(len(original_objects)==15,"all fifteen original presentations retained")
    selector_info=manifest["selector_resource"]
    for offset in (8,0x58,0xA8):
        at=task+offset
        need(tuple(u32(ewram,at+d) for d in (0x44,0x48,0x4C)) == tuple(BASE+selector_info[k] for k in
             ("p1_raw","p0_raw","p2_raw")),"all three new presentations bind the installed selector")
        need(u16(ewram,at+2)==manifest.get("row_baselines",[36,56,76,96,116,136])[4],"selector row baseline")
    return_object=original_objects[4]
    pixels=native_layouts[return_object["layout"]][1]
    bounds=(return_object["x"]+min(x for x,y in pixels),return_object["y"]+min(y for x,y in pixels),
            return_object["x"]+max(x for x,y in pixels),return_object["y"]+max(y for x,y in pixels))
    window=tuple(iwram[0x12C0:0x12C4])
    need(window==(24,200,16,128) and window[0]<=bounds[0]<=bounds[2]<window[1] and
         window[2]<=bounds[1]<=bounds[3]<window[3],"complete Return pixels fit actual native clipping window")
    active=invariants["enabled_objects_at_capture"]
    need(invariants["affine_objects_at_capture"]==0 and 0<active<=manifest["budgets"][entry]["maximum_oam"] and
         u16(iwram,0x12D6)==active,"actual native/physical OAM population within whole-screen bound")
    need([u16(oam,n*8+4)&1023 for n in range(active)]==list(range(active)),"native tile-per-OAM hardware sequence")
    need(vram[0x10000:0x10000+active*32]==ewram[:active*32],"entire active staging queue reached physical OBJ VRAM")
    tag=iwram[0x112F]
    return dict(status="PASS",rom_sha256=sha(after),capture_manifest_sha256=sha((directory/"capture.json").read_bytes()),
        mode=14,row=u16(iwram,0x473E),record_tag=tag,pending_language=pending,entry_language=entry,error=error,
        record_checksum_valid=u32(iwram,0x11E0)==sum(iwram[0x1120:0x11E0]),
        task_address=0x02000000+task,task_count=len(tasks),original_presentations=original_objects,
        return_pixel_bounds=bounds,logical_window=window,enabled_oam=active,active_tile_bytes=active*32,
        native_staging_matches_hardware=True,scope="one exact stable Options snapshot; physical save contents and complete interaction coverage excluded")


if __name__ == "__main__":
    main()

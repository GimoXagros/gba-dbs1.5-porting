#!/usr/bin/env python3
"""Build the bounded five-event title language component on one exact base.

Original English bytes and all title behavior remain native. Japanese layouts
come directly from the fixed Japanese WSC 1.5 producer; Korean is a draft;
Digicode follows those Japanese readings with one explicit small-YO alias.
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
from analyze_language_consumers import INPUT_HASHES, ASSETS, decode_asset, need, sha, u32
from build_full_asset_poc import parse_wsc_far_descriptor, convert_tile
from render_wsc_asset_frames import layout_frames
from convert_wsc_palette_block import convert_block
from build_options_korean_poc import FONT_SHA, LICENSE_SHA, font_glyphs, text_pixels, pack_tile
from digicode_glyphs import font_glyphs as dg_glyphs, text_pixels as dg_pixels
from encode_digicode_reading import CATALOG, encode

BASE = 0x08000000
PREDECESSOR = "A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71"
P0, P1, P2 = 0x8FD08, 0x8FC58, 0x90878
JA_RAW, KO_RAW, DG_RAW, CODE_RAW = 0x63A800, 0x63D000, 0x63E000, 0x63FB00
DG_WIDTHS = (80, 88, 64, 64)
SOURCE_TEXT = ("スタートボタンをおしてね！", "ひとりでバトル", "ともだちとバトル", "オプション", "D-ARK")
READINGS = ("スタートボタンをおしてね", "ひとりでバトル", "ともだちとバトル", "おぷしよん")
DG_ROWS_SHA = "E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195"


def native_pixels(parts, tiles):
    pixels = {}
    for flags, y, x in parts:
        index = flags & 0x3FFF
        need(index < len(tiles) <= 256, "complete eight-bit native tile lookup")
        for yy in range(8):
            for xx in range(8):
                tx, ty = (7-xx if flags & 0x4000 else xx), (7-yy if flags & 0x8000 else yy)
                value = tiles[index][ty*4+tx//2] >> (4*(tx % 2)) & 15
                if value:
                    pixels[x+xx, y+yy] = value
    return pixels


def original_resource(gba):
    asset = decode_asset(gba, ASSETS[2])
    at = asset["atlas_pixels_raw"]
    tiles = [gba[p:p+32] for p in range(at, at+asset["atlas_bytes"], 32)]
    parts = [[(p["tile_flags"], p["y"], p["x"]) for p in row["entries"]] for row in asset["layouts"]]
    return parts, tiles


def japanese_source(w10, w15, gba):
    # Actual branch producers, not a match based only on event numbers.
    old = bytes.fromhex("33c0e4cd24013d0000757a")
    need(w10[0x3C2916:0x3C2916+len(old)] == old, "WSC 1.0 title language branch")
    new = bytes.fromhex("33c033c03d00007551")
    need(w15[0x780148:0x780148+len(new)] == new, "WSC 1.5 explicitly fixes Japanese title")
    need(w15[0x780179:0x780182] == bytes.fromhex("68bc0068fe23680000") and
         w15[0x780182:0x78018B] == bytes.fromhex("68bd0068a823680000"), "actual Japanese P0/P1 stack arguments")
    need(w15[0x780170:0x780179] == bytes.fromhex("68bd0068ee27680000"), "actual Japanese P2 stack argument")
    for data, at in ((w10,0x2B5FC0),(w10,0x2B5FF0),(w15,0x3D7EE0),(w15,0x3D7F10)):
        need(convert_block(data[at:at+38]) == gba[P2:P2+40], "all four source palettes equal native title palette")
    header = 0x3C3FE0
    source_parts = [[(tile,y,x) for tile,x,y in frame] for frame in layout_frames(w15,header)]
    need(len(source_parts) == 11 and [len(p) for p in source_parts[:5]] == [17,22,22,22,22], "bounded source title population")
    segment,bank = struct.unpack_from("<2H",w15,header+4)
    desc = ((bank & 127)<<16)+(segment-0x2000)*16
    length, raw = parse_wsc_far_descriptor(w15,desc)
    need((desc,length,raw) == (0x3D8E90,0x11C0,0x396300) and w15[desc+8:desc+16] == b"\xff"*8,
         "one exact complete static source atlas")
    tiles = [convert_tile(w15[p:p+32]) for p in range(raw,raw+length,32)]
    # First five source P1 events are exactly the same native event contracts.
    from shoot_resource_conversion import parse_shoot_p1
    from build_new_base_p1_assets import convert_payload_item
    p1 = parse_shoot_p1(w15,0x3D3A80)
    table = u32(gba,P1)-BASE
    need(p1["counts"] == [1]*11, "source title single-frame event population")
    for event in range(5):
        payload = u32(gba,table+event*16+4)-BASE
        a = u32(gba,table+event*16+8)-BASE
        need(gba[payload:payload+16] == convert_payload_item(p1["payloads"][event][0]) and
             gba[a:a+8] == w15[0x3D3A80+p1["a_relatives"][event]:0x3D3A80+p1["a_relatives"][event]+8],
             "source Japanese event and timing contract equals native title")
    return source_parts[:5], tiles, dict(p0_raw=header,p1_raw=0x3D3A80,p2_raw=0x3D7EE0,
        source_layouts=11,installed_layouts=5,descriptor_raw=desc,atlas_raw=raw,atlas_bytes=length,
        atlas_sha256=sha(w15[raw:raw+length]),same_palette_all_four_sources=True)


def bounds(pixels):
    return [min(x for x,y in pixels),min(y for x,y in pixels),max(x for x,y in pixels),max(y for x,y in pixels)]


def pack_resource(parts, tiles, raw):
    need(len(parts) == 5 and len(tiles) <= 256 and all(0 < len(p) <= 127 for p in parts), "bounded five-layout P0")
    out = bytearray(56)
    for index,layout in enumerate(parts):
        struct.pack_into("<2I",out,16+index*8,len(layout),BASE+raw+len(out))
        for tile,y,x in layout:
            out.extend(struct.pack("<Hbb",tile,y,x))
    desc = len(out)
    out.extend(struct.pack("<2I",len(tiles)*32,BASE+raw+desc+8))
    out.extend(b"".join(tiles))
    struct.pack_into("<2I4H",out,0,BASE+raw+16,BASE+raw+desc,5,len(tiles)-1,(len(tiles)-1)*32,8)
    return bytes(out)


def tile_layouts(frames):
    tiles,lookup,layouts = [],{},[]
    for pixels in frames:
        left,top,right,bottom = bounds(pixels)
        parts = []
        for y in range(top,bottom+1,8):
            for x in range(left,right+1,8):
                tile = pack_tile(pixels,x,y)
                if not any(tile):
                    continue
                if tile not in lookup:
                    lookup[tile] = len(tiles)
                    tiles.append(tile)
                parts.append((lookup[tile],y,x))
        need(native_pixels(parts,tiles) == pixels, "every authored pixel survives native pack/unpack")
        layouts.append(parts)
    return layouts,tiles


def remap_text(pixels, width, shift_y):
    return {(x,y+shift_y):(13 if v == 1 else 15) for (x,y),v in pixels.items()},width


def attach(first, width, punctuation, gap=2):
    result = dict(first)
    x0,_,x1,_ = bounds(punctuation)
    result.update({(width+gap+x-x0,y):v for (x,y),v in punctuation.items()})
    return result,width+gap+x1-x0+1


def localized_frames(gba, ja_parts, ja_tiles, font, config, catalog):
    entries = config["entries"]
    need(config["schema"] == 1 and config["status"] == "development-source-backed-title-component" and
         [e["event"] for e in entries] == list(range(5)) and
         tuple(e["source_ja"] for e in entries) == SOURCE_TEXT and
         tuple(e["digicode_reading"] for e in entries[:4]) == READINGS and
         entries[4]["digicode_parts"] == ["D","native-hyphen","ARK"], "protected Japanese title wording and explicit normalization")
    glyphs = font_glyphs(font,set("".join(e["korean_draft"] for e in entries[:4])))
    dg = dg_glyphs(catalog)
    need(sha(b"".join(dg[g["id"]] for g in catalog["glyphs"]+catalog["latin_glyphs"])) == DG_ROWS_SHA,
         "unchanged reviewed Digicode glyph rows")
    original_parts,original_tiles = original_resource(gba)
    original = [native_pixels(p,original_tiles) for p in original_parts]
    japanese = [native_pixels(p,ja_tiles) for p in ja_parts]
    exclamation = {(x,y):v for (x,y),v in japanese[0].items() if 48 <= x <= 50}
    hyphen = {(x,y):v for (x,y),v in japanese[4].items() if -7 <= x <= -2 and y == -1}
    need(bounds(exclamation) == [48,-4,50,3] and len(exclamation) == 22 and len(hyphen) == 6 and
         [hyphen[x,-1] for x in range(-7,-1)] == [14,13,13,13,13,14], "exact native punctuation slices")
    template = dict(original[1])
    for y in range(-7,7):
        for x in range(-28,43):
            template[x,y] = 15
    marker = {(x,y):v for (x,y),v in original[1].items() if -43 <= x <= -30 and -7 <= y <= 6}
    need(len(marker) == 196 and all(-43 <= x <= -30 and -7 <= y <= 6 for (x,y),v in original[1].items() if 1 <= v <= 6),
         "complete original fourteen-pixel title marker")
    korean,digicode = [],[]
    for event in range(5):
        if event == 4:
            korean.append(japanese[4])
            d,dw = remap_text(*dg_pixels("D",catalog,dg),5)
            d,dw = attach(d,dw,hyphen)
            rest,rw = remap_text(*dg_pixels("ARK",catalog,dg),5)
            d.update({(x+dw+2,y):v for (x,y),v in rest.items()});dw += 2+rw
        else:
            k,kw = remap_text(*text_pixels(entries[event]["korean_draft"],glyphs),5)
            d,dw = remap_text(*dg_pixels(entries[event]["digicode_reading"],catalog,dg),7)
            encode(entries[event]["digicode_reading"],catalog)  # no implicit aliases/fallbacks
            if event == 0:
                k,kw = attach(k,kw,exclamation)
                d,dw = attach(d,dw,exclamation)
                korean.append({(x-kw//2,y):v for (x,y),v in k.items()})
            else:
                need(kw <= 67 and -7 <= min(y for x,y in k) <= max(y for x,y in k) <= 6, "Korean text fits unchanged native button")
                frame = dict(template)
                frame.update({(x+8-kw//2,y):v for (x,y),v in k.items()})
                korean.append(frame)
        if event == 0:
            digicode.append({(x-dw//2,y):v for (x,y),v in d.items()})
        else:
            width = DG_WIDTHS[event-1]
            left,right = -width//2,width//2-1
            frame = {(x,y):(13 if x in (left,right) or y in (-9,8) else 15)
                     for y in range(-9,9) for x in range(left,right+1)}
            frame.update({(x+left+44,y):v for (x,y),v in marker.items()})
            start = left+16+(width-17-dw)//2
            need(start >= left+16 and start+dw-1 < right and all(-8 <= y <= 7 for x,y in d), "complete Digicode fits bordered title button")
            frame.update({(x+start,y):v for (x,y),v in d.items()})
            need(all(frame[x+left+44,y] == v for (x,y),v in marker.items()), "every original marker pixel retained")
            digicode.append(frame)
    return korean,digicode,dict(exclamation_source_bounds=bounds(exclamation),hyphen_source_bounds=bounds(hyphen),
        exclamation_pixels=len(exclamation),hyphen_pixels=len(hyphen),marker_pixels=len(marker),
        digicode_button_widths=list(DG_WIDTHS),digicode_button_height=18,
        reading_ids=[encode(r,catalog) for r in READINGS]+[encode("DARK",catalog)],
        glyph_rows_sha256=DG_ROWS_SHA,small_kana_alias="only source オプション -> explicit reading おぷしよん")


def branch(at,target):
    delta = target-at-8
    need(delta % 4 == 0 and -(1<<25) <= delta < (1<<25), "aligned reachable ARM B")
    return struct.pack("<I",0xEA000000 | ((delta//4)&0xFFFFFF))


def code():
    source = f"""
        push {{r0,r1}}
        mrs r1,cpsr
        ldr r0,tag
        ldrb r0,[r0]
        sub r0,r0,#0xA0
        cmp r0,#3
        movhi r0,#0
        adr r8,table
        ldr r8,[r8,r0,lsl #2]
        msr cpsr_f,r1
        pop {{r0,r1}}
        b 0x08090A1C
    tag: .word 0x0300112F
    table: .word 0x{BASE+P0:08X},0x{BASE+JA_RAW:08X},0x{BASE+KO_RAW:08X},0x{BASE+DG_RAW:08X}
    """
    payload = bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(source,BASE+CODE_RAW)[0])
    insns = list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(payload[:-20],BASE+CODE_RAW))
    need(len(payload) == 68 and len(insns) == 12 and sum(i.size for i in insns) == 48, "bounded ARM32 getter with literal-only tail")
    for i in insns:
        need(bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(i.mnemonic+" "+i.op_str,i.address)[0]) == i.bytes, "exact final placed instruction roundtrip")
    need(payload[-20:] == struct.pack("<5I",0x0300112F,BASE+P0,BASE+JA_RAW,BASE+KO_RAW,BASE+DG_RAW), "complete four-way P0 table")
    return payload,[dict(address=i.address,mnemonic=i.mnemonic,operands=i.op_str) for i in insns]


def ownership(before,spans):
    for lo,hi in spans:
        need(before[lo:hi] == b"\xff"*(hi-lo), "complete new title allocation is FF")
    def vacant(target):
        return not any(lo <= target < hi for lo,hi in spans)
    for at in range(len(before)-3):
        if before[at+3] == 8:
            need(vacant(u32(before,at)-BASE), f"no encoded inbound title pointer at {at:X}")
    for at in range(0,len(before)-3,4):
        word = u32(before,at)
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000: delta -= 1<<24
            need(vacant(at+8+delta*4), f"no ARM branch inbound at {at:X}")
        if word & 0x0E1F0000 == 0x041F0000:
            need(vacant(at+8+(word&4095)*(1 if word&0x800000 else -1)), f"no PC-relative read inbound at {at:X}")
        if word & 0x0E0F0000 == 0x020F0000 and (word>>21)&15 in (2,4):
            rotation = ((word>>8)&15)*2;immediate = word&255
            if rotation: immediate = ((immediate>>rotation)|(immediate<<(32-rotation)))&0xFFFFFFFF
            need(vacant(at+8+immediate*(1 if (word>>21)&15 == 4 else -1)), f"no PC-relative address inbound at {at:X}")
    for at in range(0,len(before)-1,2):
        half = struct.unpack_from("<H",before,at)[0]
        if half & 0xF800 in (0x4800,0xA000):
            need(vacant(((at+4)&~3)+(half&255)*4), f"no Thumb literal/ADR inbound at {at:X}")


def native_population(gba):
    """Pin the complete native title callback population, including transitions.

    The mode-controller task is priority0, the one title task priority1000,
    and the palette-only fade task priority-F000. Replacing the title task's
    callback cannot run its replacement until the next scheduler visit. The
    prompt transition branches to its epilogue, never to the menu draw loop.
    """
    c = Cs(CS_ARCH_ARM,CS_MODE_ARM)
    definitions = [
        ("prompt",0x90C7C,0x90E00,[0x90DD0],"event0 or blink-hidden"),
        ("menu_slide",0x90E58,0x90F5C,[0x90F30],"events1..4, four iterations"),
        ("menu",0x90FA0,0x9126C,[0x91240],"events1..4, four iterations"),
        ("menu_exit",0x91310,0x914A8,[0x91414],"events1..4, selected event may blink"),
        ("title_timeout",0x91598,0x91668,[],"no presentations; retires title tasks"),
        ("palette_fade",0x914E4,0x91578,[],"palette RAM only; no presentation"),
        ("mode_controller",0x15AB4,0x15B70,[],"priority0; title common callback is BX LR"),
    ]
    reports = []
    for name,lo,hi,draws,scope in definitions:
        instructions = list(c.disasm(gba[lo:hi],BASE+lo))
        need(len(instructions)*4 == hi-lo,"complete native title callback decode")
        actual = [i.address-BASE for i in instructions if i.mnemonic == "bl" and i.op_str == "#0x8012c28"]
        need(actual == draws,"exact complete native title draw-call sites")
        reports.append(dict(name=name,code_raw=[lo,hi],draw_sites_raw=draws,scope=scope,sha256=sha(gba[lo:hi])))
    guards = {
        0x90C70:0x08090C7C,0x90C74:0x080914E4, # only two title-created tasks
        0x90D54:0xE5890000,0x90DB0:0xEA000010, # callback write then prompt epilogue
        0x90E34:0x08090E58,0x90F68:0x08090FA0,0x90F88:0x08090FA0,
        0x91274:0x08091598,0x91294:0x08091598,0x912C8:0x08091310,
        0x90A70:0xE3A08004,0x90A74:0xE1C480B0, # menu population03002A64=4
        0x90F70:0x03002A64,0x90F74:0x03002AC8,
        0x911FC:0xE3A02004,0x913CC:0xE3A02004,
        0x159B0:0xE12FFF1E, # mode3 common callback has no drawing
        0x11DCC:0xE5958000,0x11DD4:0xE12FFF18,0x11DF0:0xE595500C, # visit next task after callback
        0x117C8:0xE3A07000,0x117CC:0xE5C87000, # frame queue count reset
        0x91588:0x05000020,0x9158C:0x0201E800,0x91590:0x0201E400,
    }
    for at,word in guards.items():
        need(u32(gba,at) == word,f"native title population guard {at:X}")
    ctor = list(c.disasm(gba[0x90BF4:0x90C70],BASE+0x90BF4))
    need([i.address-BASE for i in ctor if i.mnemonic == "bl"] == [0x90C18,0x90C54] and
         all(i.op_str == "#0x8011ac4" for i in ctor if i.mnemonic == "bl"),"exact two native title task allocations")
    palette = list(c.disasm(gba[0x1207C:0x12138],BASE+0x1207C))
    need([i.op_str for i in palette if i.mnemonic == "bl"] == ["#0x837db3c"]*3,
         "fade leaf invokes arithmetic division only")
    coords = [list(struct.unpack_from("<2h",gba,0x90B54+n*4)) for n in range(5)]
    need(coords == [[112,104],[-48,36],[-48,72],[-48,108],[-48,200]],"native title coordinates including offscreen D-ARK")
    return dict(callbacks=reports,coordinates=coords,menu_objects=4,prompt_objects=1,
        title_created_tasks=2,mode_controller_tasks=1,other_oam_presentations=0,
        prompt_menu_overlap=False,counts_offscreen_d_ark=True,
        queue_reset_raw=0x117C8,task_next_visit_raw=0x11DF0,
        transition="main-task callback replaced in place; old phase returns; new phase runs on next scheduler visit",
        guards=[dict(raw=at,word=f"{word:08X}") for at,word in sorted(guards.items())])


def build(before,gba,w10,w15,font,license_data,config):
    need(sha(before) == PREDECESSOR and len(before) == 0x800000, "exact reviewed Options/action/recovery predecessor")
    for label,data in (("gba",gba),("wsc10",w10),("wsc15",w15)):
        need(sha(data) == INPUT_HASHES[label], "exact commercial "+label)
    need(sha(font) == FONT_SHA and sha(license_data) == LICENSE_SHA, "exact licensed font input")
    for lo,hi in ((0x8FC58,0x916A4),(0x124CC,0x12DD8),(0x11708,0x11854),
                  (0x11A84,0x12138),(0x15970,0x15D31)):
        need(before[lo:hi] == gba[lo:hi], "unchanged native title/renderer dependency")
    need(u32(gba,0x90A18) == 0xE59F81A0 and struct.unpack_from("<3I",gba,0x15B94) == (0x080908A0,0x08090BF4,0x080159B0), "actual native producer and mode3 row")
    population = native_population(gba)
    ja_parts,ja_tiles,source_report = japanese_source(w10,w15,gba)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    korean,digicode,authored = localized_frames(gba,ja_parts,ja_tiles,font,config,catalog)
    ko_parts,ko_tiles = tile_layouts(korean);dg_parts,dg_tiles = tile_layouts(digicode)
    original_parts,original_tiles = original_resource(gba)
    resources = [("ja",JA_RAW,ja_parts,ja_tiles),("ko",KO_RAW,ko_parts,ko_tiles),("digicode",DG_RAW,dg_parts,dg_tiles)]
    writes = [(raw,pack_resource(parts,tiles,raw),language+" title resource") for language,raw,parts,tiles in resources]
    machine,decoded = code();writes.append((CODE_RAW,machine,"register/flags-preserving P0 route"))
    spans = [(raw,raw+len(value)) for raw,value,purpose in writes]
    ownership(before,spans)
    writes.append((0x90A18,branch(0x90A18,CODE_RAW),"native P0 load hook"))
    reports = []
    for language,raw,parts,tiles in [("en",P0,original_parts,original_tiles)]+resources:
        counts = [len(p) for p in parts]
        # The native callback slot draws either event0 or all four menu objects.
        # Count Y200 as emitted: native clipping permits coordinates below232.
        peak = max(counts[0],sum(counts[1:]))
        need(peak <= 127 and peak*32 <= 4096, "complete title callback-state OAM/staging bound")
        reports.append(dict(language=language,p0_raw=raw,parts=counts,atlas_tiles=len(tiles),
            frame_bounds=[bounds(native_pixels(p,tiles)) for p in parts],prompt_oam=counts[0],
            menu_oam=sum(counts[1:]),maximum_oam=peak,maximum_tile_bytes=peak*32))
    after = bytearray(before);expected=[];end=0
    for at,value,purpose in sorted(writes):
        need(end <= at and at+len(value) <= len(before), "disjoint bounded title Expected Writes")
        end = at+len(value)
        expected.append(dict(raw=at,bytes=len(value),purpose=purpose,before_sha256=sha(before[at:end]),after_sha256=sha(value)))
        after[at:end] = value
    inverse = bytearray(after)
    for w in expected: inverse[w["raw"]:w["raw"]+w["bytes"]] = before[w["raw"]:w["raw"]+w["bytes"]]
    need(inverse == before, "complete final diff returns exactly to predecessor")
    return bytes(after),dict(schema=1,kind="development-five-event-title-language",input_sha256=sha(before),output_sha256=sha(after),
        source_hashes={"gba":sha(gba),"wsc10":sha(w10),"wsc15":sha(w15),"font":sha(font),"font_license":sha(license_data)},
        source_japanese=source_report,authored=authored,resources=reports,allocation_spans=spans,expected_writes=expected,
        hook=dict(raw=0x90A18,old_word="E59F81A0",helper_raw=CODE_RAW,continuation=0x08090A1C,
                  preserves="all registers except original LDR destination r8; CPSR flags and LR preserved; fixed B continuation"),
        machine_code=decoded,new_ram_bytes=0,new_tasks=0,original_assets_preserved=True,
        native_p1_p2_unchanged=True,other_title_behavior_unchanged=True,
        native_population=population,
        bound_scope="one native callback draws prompt OR four menu labels; offscreen D-ARK included; no clamp",
        runtime_claim=False,provided_save_accessed=False,whole_game_four_languages_complete=False)


def preview(data,manifest,directory):
    from PIL import Image,ImageDraw
    colors=[tuple(((v>>shift)&31)*255//31 for shift in (0,5,10)) for v in struct.unpack_from("<16H",data,P2+6)]
    out=Image.new("RGB",(560,4*5*30),(40,40,52));draw=ImageDraw.Draw(out)
    for row,info in enumerate(manifest["resources"]):
        p0=info["p0_raw"];table=u32(data,p0)-BASE;desc=u32(data,p0+4)-BASE;raw=u32(data,desc+4)-BASE
        tiles=[data[p:p+32] for p in range(raw,raw+u32(data,desc),32)]
        for event in range(5):
            count,ptr=struct.unpack_from("<2I",data,table+event*8)
            parts=[struct.unpack_from("<Hbb",data,ptr-BASE+j*4) for j in range(count)]
            y0=(row*5+event)*30
            draw.text((4,y0+10),f"{info['language']} {event}",fill=(255,220,80))
            for (x,y),v in native_pixels(parts,tiles).items():out.putpixel((160+x,y0+14+y),colors[v])
            # Also show exact native highlight colors without palette changes.
            highlight=[tuple(((v>>shift)&31)*255//31 for shift in (0,5,10)) for v in struct.unpack_from("<16H",data,0x8B748)]
            for (x,y),v in native_pixels(parts,tiles).items():out.putpixel((400+x,y0+14+y),highlight[v])
    directory.mkdir(parents=True,exist_ok=True);path=directory/"title-all-languages.png"
    out.resize((1120,1200),Image.Resampling.NEAREST).save(path)
    return dict(name=path.name,sha256=sha(path.read_bytes()),kind="static native-palette resource preview; not runtime")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("before","gba","wsc10","wsc15","font","license","output"):parser.add_argument(name,type=Path)
    parser.add_argument("--labels",type=Path,default=Path(__file__).resolve().parents[1]/"localization/title-labels.json")
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--render-directory",type=Path)
    args=parser.parse_args()
    need(all(p is None or p.suffix.lower() != ".sav" for p in vars(args).values()),"save paths forbidden")
    need(args.output.resolve() not in {getattr(args,k).resolve() for k in ("before","gba","wsc10","wsc15","font","license")},"never overwrite inputs")
    result,report=build(*(getattr(args,k).read_bytes() for k in ("before","gba","wsc10","wsc15","font","license")),json.loads(args.labels.read_text(encoding="utf-8")))
    if args.render_directory:report["preview"]=preview(result,report,args.render_directory)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True,exist_ok=True);args.manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("[Title language] "+report["output_sha256"])


if __name__=="__main__":main()

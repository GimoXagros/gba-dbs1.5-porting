#!/usr/bin/env python3
"""Build the bounded four-language mode8 result-label component.

Only six existing initializer calls and four proven private intervals change.
English, all twelve digit frames, native P1/palette, fighter/name resources,
the mode12 alias and the strict Digicode encoder remain unchanged.
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
import analyze_result_language_budget as budget
from analyze_waterfall_third_pattern import no_inbound

BASE = 0x08000000
PREDECESSOR = "494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6"
ART = "875700A7C5C0281E46651AF09E31E30BB846D1C44675172391D323D3450B03B3"
P0, P1, P2 = 0xB8210, 0xB9004, 0xB9144
JA, KO, DG, CODE = 0x651AE0, 0x6DA640, 0x7DFC20, 0x652FA0
HOOKS = ((0x89988,0xEBFE2395), (0x899EC,0xEBFE237C), (0x89BFC,0xEBFE22F8),
         (0x89C60,0xEBFE22DF), (0x89D9C,0xEBFE2290), (0x89F34,0xEBFE222A))
GETTER = 0x633400
GETTER_SHA = "5F72868A07F73A7FC2892A38BB9902BB8986B2FFB9460F454F8A41E4AC7FCFD7"
TEXT_LAYOUTS = (0,1,14)
EXPECTED_COUNTS = ((35,20,28),(30,20,28),(30,20,26),(30,20,27))
need, sha, cut, u, h, ptr = budget.need, budget.sha, budget.cut, budget.u, budget.h, budget.pointer


def branch(at, target, link=False):
    delta = target-(BASE+at+8)
    need(delta%4 == 0 and -(1<<25) <= delta < (1<<25), "placed ARM branch range")
    return (0xEB000000 if link else 0xEA000000) | ((delta//4)&0xFFFFFF)


def helper():
    words = [0xE92D4007, 0xE10F1000, branch(CODE+8,BASE+GETTER,True),
             0xE28F2010, 0xE7920100, 0xE58D0034, 0xE128F001,
             0xE8BD4007, branch(CODE+32,BASE+0x127E4),
             BASE+P0, BASE+JA, BASE+KO, BASE+DG]
    return struct.pack("<13I",*words)


def abi(before):
    need(sha(cut(before,GETTER,28)) == GETTER_SHA, "exact shared read-only tag getter")
    need(u(before,0x127E4) == 0xE92D0039 and u(before,0x127F4) == 0xE59D0034,
         "native sixteen-byte push and P0 argument read")
    need(u(before,0x12854) == 0xE8BD0039 and u(before,0x12858) == 0xE12FFF1E,
         "native matching pop and original LR return")
    for at,expected in HOOKS:
        need(u(before,at) == expected == branch(at,BASE+0x127E4,True), "all six original init BL words")
        need(u(before,at+4) == 0xE28DD03C, "caller discards exactly fifteen argument words after return")
    insns = list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(helper()[:36],BASE+CODE))
    expected = [("push","{r0, r1, r2, lr}"),("mrs","r1, apsr"),("bl",f"#0x{BASE+GETTER:x}"),
                ("add","r2, pc, #0x10"),("ldr","r0, [r2, r0, lsl #2]"),("str","r0, [sp, #0x34]"),
                ("msr","apsr_nzcvq, r1"),("pop","{r0, r1, r2, lr}"),("b","#0x80127e4")]
    need([(i.mnemonic,i.op_str) for i in insns] == expected, "complete placed helper instruction contract")
    assembler = Ks(KS_ARCH_ARM,KS_MODE_ARM)
    for i in insns:
        need(bytes(assembler.asm(i.mnemonic+" "+i.op_str,i.address)[0]) == i.bytes, "placed instruction roundtrip")
    cases = 0
    table = (BASE+P0,BASE+JA,BASE+KO,BASE+DG)
    for tag in range(256):
        raw = (tag-0xA0)&0xFFFFFFFF
        index = raw if raw <= 3 else 0
        need(index == (tag-0xA0 if 0xA0 <= tag <= 0xA3 else 0), "all invalid tags fall back to English")
        for pattern in range(32):
            cpsr = (pattern<<27)|0x10
            original = [("entry-register",i) for i in range(15)]
            registers = original.copy()
            arguments = [("entry-argument",i) for i in range(15)]
            saved = [registers[i] for i in (0,1,2,14)]
            sp = -16
            registers[1] = cpsr
            registers[0] = index
            difference = (raw-3)&0xFFFFFFFF
            overflow = bool((raw^3)&(raw^difference)&0x80000000)
            compared = ((cpsr&0x0FFFFFFF)|((difference>>31)<<31)|
                        (int(difference==0)<<30)|(int(raw>=3)<<29)|(int(overflow)<<28))
            registers[2] = BASE+CODE+36
            registers[0] = table[index]
            need(sp+0x34 == 0x24, "wrapper STR reaches exactly entrySP+24h")
            arguments[(sp+0x34)//4] = registers[0]
            restored = (compared&0x00FFFFFF)|(registers[1]&0xFF000000)
            for i,value in zip((0,1,2,14),saved):registers[i]=value
            sp += 16
            need(registers == original and sp == 0 and restored == cpsr and
                 arguments[9] == table[index] and
                 all(arguments[i] == ("entry-argument",i) for i in range(15) if i != 9),
                 "arbitrary registers/LR/SP/CPSR and fourteen other arguments preserved")
            cases += 1
    return dict(helper_raw=CODE,bytes=52,stack_bytes=16,static_transfer_cases=cases,
                argument_offset_at_entry=0x24,argument_offset_in_wrapper=0x34,
                preserved="All registers including original BL return LR, SP and CPSR before tail-entering native initializer; only consumed P0 stack argument changes.",
                stack_proof="Wrapper uses the exact16 descending bytes subsequently used by original080127E4 push. Getter has no push; wrapper pops before tail B, so minimumSP is unchanged.",
                instructions=[dict(address=i.address,mnemonic=i.mnemonic,operands=i.op_str) for i in insns],
                table=list(table),getter_sha256=GETTER_SHA,new_persistent_RAM=0)


def original(data):
    need(h(data,P0+14) == 8, "original static-atlas result resource")
    descriptor=ptr(data,P0+4)
    start,size=ptr(data,descriptor+4),u(data,descriptor)
    need(size == 91*32, "complete91-tile native atlas")
    tiles=[cut(data,at,32) for at in range(start,start+size,32)]
    layouts=[budget.native_parts(data,P0,i) for i in range(15)]
    return layouts,tiles


def source_arrays(source,layout):
    count,relative=struct.unpack("<2H",cut(source,0x3CB870+16+layout*4,4))
    parts=[];tiles=[]
    for index in range(count):
        flags,y,x=struct.unpack("<Hbb",cut(source,0x3CB870+relative+index*4,4))
        planar=cut(source,0x3A0000+(flags&255)*32,32)
        values=[sum(((planar[yy*4+b]>>(7-xx))&1)<<b for b in range(4)) for yy in range(8) for xx in range(8)]
        tiles.append(bytes(values[k]|values[k+1]<<4 for k in range(0,64,2)))
        parts.append(((flags&0xFF00)|index,y,x))
    return parts,tiles


def check_config(config):
    need(config["schema"] == 2 and config["status"] == "approved-native-result-component", "approved native art catalog")
    need(config["shared_headings"] == "Exact Japanese-source WIN/DRAW for Japanese, Korean and Digicode; English retains native WINS/DRAW.", "user shared heading policy")
    need(config["approved_art_sha256"] == ART and config["last_chance_part_counts"] == [28,26,27], "approved art and population pins")


def pack_resource(data,layouts,tiles,raw):
    need(len(layouts)==15 and 0<len(tiles)<=256, "native result layout/atlas population")
    out=bytearray(16+15*8)
    for index,parts in enumerate(layouts):
        struct.pack_into("<2I",out,16+index*8,len(parts),BASE+raw+len(out))
        for flags,y,x in parts:out.extend(struct.pack("<Hbb",flags,y,x))
    descriptor=len(out)
    out.extend(struct.pack("<2I",len(tiles)*32,BASE+raw+descriptor+8))
    out.extend(b"".join(tiles))
    struct.pack_into("<2I4H",out,0,BASE+raw+16,BASE+raw+descriptor,h(data,P0+8),len(tiles)-1,(len(tiles)-1)*32,h(data,P0+14))
    return bytes(out)


def resources(data,source,art,config):
    check_config(config)
    original_parts,original_tiles=original(data)
    source_pixels,punctuation,source_report=budget.source_labels(source,data)
    budget.approved_labels(art,source_pixels,punctuation)
    writes=[];reports=[]
    for language,raw,expected_count in zip(("ja","ko","digicode"),(JA,KO,DG),EXPECTED_COUNTS[1:]):
        tiles=list(original_tiles);lookup={blob:i for i,blob in enumerate(tiles)}
        layouts=[list(parts) for parts in original_parts]
        pixel_reports=[]
        for index,layout in enumerate(TEXT_LAYOUTS):
            if index < 2:
                frame=art["japanese_common"][index]
                parts=[tuple(p) for p in frame["parts"]]
                new_tiles=[bytes.fromhex(t) for t in frame["tiles_4bpp_hex"]]
                wanted=source_pixels[layout]
            elif language == "ja":
                wanted=source_pixels[layout]
                parts,new_tiles=source_arrays(source,layout)
            else:
                frame=art["korean" if language == "ko" else "digicode"]
                parts=[tuple(p) for p in frame["parts"]]
                new_tiles=[bytes.fromhex(t) for t in frame["tiles_4bpp_hex"]]
                wanted={(x,y):v for x,y,v in frame["pixels"]}
            need(budget.compose(parts,new_tiles)==wanted,"source/approved indexed frame inverse")
            remapped=[]
            for flags,y,x in parts:
                tile=new_tiles[flags&255]
                if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
                need(lookup[tile]<=255,"complete atlas eight-bit tile index")
                remapped.append(((flags&0xFF00)|lookup[tile],y,x))
            layouts[layout]=remapped
            need(budget.compose(remapped,tiles)==wanted,"installed native text indexed pixel inverse")
            pixel_reports.append(dict(layout=layout,parts=len(remapped),pixels=len(wanted),bounds=budget.bounds(wanted),pixel_sha256=budget.pixel_sha(wanted)))
        need(tuple(len(layouts[i]) for i in TEXT_LAYOUTS)==expected_count,"approved exact part counts")
        need(all(len(a)<=len(b) for a,b in zip(layouts,original_parts)),"pointwise no layout increases")
        need(layouts[2:14]==original_parts[2:14] and tiles[:91]==original_tiles,"exact twelve digit arrays and91-tile prefix")
        blob=pack_resource(data,layouts,tiles,raw)
        writes.append((raw,blob,language+" approved P0/atlas"))
        reports.append(dict(language=language,p0_raw=raw,bytes=len(blob),tiles=len(tiles),layout_parts=list(map(len,layouts)),
                            text=pixel_reports,native_digit_arrays_unchanged=True,native_atlas_prefix_unchanged=True,
                            every_layout_no_larger_than_English=True,sha256=sha(blob)))
    return writes,reports,source_report


def dependency_proof(before,gba,source,art):
    # Exact predecessor identity plus each positively guarded consumer/resource
    # replaces the obsolete whole-ROM seven-span DBB restoration shortcut.
    actual=budget.analyze(before,gba,source,art=art)
    need(cut(before,P0,0xF5C)==cut(gba,P0,0xF5C),"complete original native result resource family")
    return actual,dict(exact_predecessor_sha256=PREDECESSOR,
        native_code_profiles=actual["population"]["callback_dependencies"],
        source_pose_routes_checked=True,complete_correlated_budget_recomputed=True,
        original_result_family_sha256=sha(cut(before,P0,0xF5C)))


def validate(before,after,writes):
    need(len(before)==len(after)==0x800000,"fixed ROM size")
    inverse=bytearray(after)
    for at,blob,_ in writes:
        need(cut(after,at,len(blob))==blob,"every exact Expected Write")
        inverse[at:at+len(blob)]=before[at:at+len(blob)]
    need(bytes(inverse)==before,"complete ROM inverse: no undeclared write")
    need(cut(after,P0,0xF5C)==cut(before,P0,0xF5C),"original result resource family retained")
    need(cut(after,0xBB0B4,0xA0)==cut(before,0xBB0B4,0xA0) and
         u(after,0xBBA64)==BASE+P0,"separate mode12 P0 alias and initializer unchanged")
    original_parts,original_tiles=original(before)
    for raw in (JA,KO,DG):
        desc=ptr(after,raw+4);start=ptr(after,desc+4);size=u(after,desc)
        tiles=[cut(after,a,32) for a in range(start,start+size,32)]
        layouts=[budget.native_parts(after,raw,i) for i in range(15)]
        need(layouts[2:14]==original_parts[2:14] and tiles[:91]==original_tiles,"installed native digits and atlasprefix exact")
        need(all(len(a)<=len(b) for a,b in zip(layouts,original_parts)),"installed per-layout OAM never increases")
    return dict(full_inverse=True,declared_bytes=sum(len(blob) for _,blob,_ in writes),
                changed_bytes=sum(a!=b for a,b in zip(before,after)),spans=len(writes))


def negative_checks(before,after,writes):
    rejected=[]
    for at,blob,label in writes:
        broken=bytearray(after);broken[at+len(blob)//2]^=1
        try:validate(before,broken,writes)
        except ValueError:rejected.append(label+" exact-write mutation")
        else:raise ValueError("accepted corrupted Expected Write")
    for at,label in ((0xBBA64,"mode12 alias"),(P1,"native P1"),(P2,"native palette"),
                     (0x640000,"rejected allocation"),(GETTER,"shared tag getter"),(0x652F80,"allocation gap")):
        broken=bytearray(after);broken[at]^=1
        try:validate(before,broken,writes)
        except ValueError:rejected.append(label)
        else:raise ValueError("accepted undeclared mutation")
    return dict(count=len(rejected),all_rejected=True,cases=rejected)


def build(before,gba,source,art_bytes,config):
    need(sha(before)==PREDECESSOR,"exact independently reviewed title predecessor")
    need(sha(gba)==budget.PINNED["gba"] and sha(source)==budget.PINNED["wsc15"],"pinned originals")
    # Native frame pixel hashes below bind equivalent fresh-generated art, not ignored review metadata.
    art=json.loads(art_bytes)
    full_budget,dependencies=dependency_proof(before,gba,source,art)
    abi_report=abi(before)
    writes,resource_reports,source_report=resources(before,source,art,config)
    allocations=tuple((at,at+len(blob)) for at,blob,_ in writes)+((CODE,CODE+52),)
    for lo,hi in allocations:need(cut(before,lo,hi-lo)==b"\xff"*(hi-lo),"complete recomputed resource allocation FF")
    allocation=no_inbound(before,allocations)
    need(allocation["inbound_matches"]==[] and allocation["classified_instruction_interiors"]==[],"no allocation waivers")
    writes.append((CODE,helper(),"P0 selector wrapper"))
    for at,_ in HOOKS:writes.append((at,struct.pack("<I",branch(at,BASE+CODE,True)),f"mode8 init BL {at:06X}"))
    writes.sort(key=lambda item:item[0])
    need(all(a+len(blob)<=b for (a,blob,_),(b,_,_) in zip(writes,writes[1:])),"nonoverlapping writes")
    after=bytearray(before)
    for at,blob,_ in writes:after[at:at+len(blob)]=blob
    result=validate(before,after,writes)
    need(result["spans"]==10,"complete existing hook/resource census")
    report=dict(schema=2,kind="bounded-four-language-result-labels",status="APPROVED_ART_DEVELOPMENT_COMPONENT",
        input_sha256=sha(before),output_sha256=sha(after),output_bytes=len(after),**result,
        sources=dict(gba=sha(gba),wsc15=sha(source),approved_art=sha(art_bytes)),
        hooks=[dict(raw=at,before_word=f"{old:08X}",after_word=f"{branch(at,BASE+CODE,True):08X}") for at,old in HOOKS],
        resources=[dict(language="en",p0_raw=P0,original_resource_unchanged=True,layout_parts=[len(p) for p in original(before)[0]])]+resource_reports,
        source=source_report,abi=abi_report,allocation=allocation,budget_dependencies=dependencies,
        aggregate_budget=full_budget["budgets"],correlated_pose_budget=full_budget["poses"],pointwise_layout_nonincrease=True,
        writes=[dict(raw=at,bytes=len(blob),purpose=label,sha256=sha(blob)) for at,blob,label in writes],
        negative_checks=negative_checks(before,after,writes),
        limits=["Existing mode8 events only; mode12, source-only LOSE and whole-game localization remain separate.",
                "No renderer/task/state changes, new persistent RAM, save access or emulator execution.",
                "Isolated component requires independent artifact verification and normal result-screen runtime."])
    return bytes(after),report


def preview(data,report,path):
    from PIL import Image,ImageDraw
    colors=[tuple(((v>>shift)&31)*255//31 for shift in (0,5,10)) for v in struct.unpack("<16H",cut(data,P2+6,32))]
    image=Image.new("RGB",(4*144,3*48+20),(34,36,47));draw=ImageDraw.Draw(image)
    for column,resource in enumerate(report["resources"]):
        raw=resource["p0_raw"];desc=ptr(data,raw+4);start=ptr(data,desc+4)
        tiles=[cut(data,at,32) for at in range(start,start+u(data,desc),32)]
        draw.text((column*144+8,4),resource["language"],fill=(244,215,120))
        for row,layout in enumerate(TEXT_LAYOUTS):
            pixels=budget.compose(budget.native_parts(data,raw,layout),tiles)
            for (x,y),value in pixels.items():image.putpixel((column*144+72+x,20+row*48+24+y),colors[value])
    path.parent.mkdir(parents=True,exist_ok=True)
    image.resize((image.width*3,image.height*3),Image.Resampling.NEAREST).save(path)
    return dict(name=path.name,sha256=sha(path.read_bytes()),kind="static native-palette resource preview, not runtime")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("before","gba","wsc15","art","output"):p.add_argument(name,type=Path)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--config",type=Path,default=Path(__file__).resolve().parents[1]/"localization/result-labels.json")
    p.add_argument("--preview",type=Path)
    args=p.parse_args()
    names=("before","gba","wsc15","art","config")
    paths={name:getattr(args,name) for name in names}
    outputs=[args.output,args.manifest]+([args.preview] if args.preview else [])
    need(all(path.suffix.lower()!=".sav" for path in [*paths.values(),*outputs]),"save paths forbidden")
    need(args.output.suffix.lower()==".gba" and args.manifest.suffix.lower()==".json" and
         (args.preview is None or args.preview.suffix.lower()==".png"),"explicit output types")
    need(len({p.resolve() for p in outputs})==len(outputs) and not {p.resolve() for p in outputs}&{p.resolve() for p in paths.values()},"outputs distinct from inputs")
    data={name:path.read_bytes() for name,path in paths.items()}
    after,report=build(data["before"],data["gba"],data["wsc15"],data["art"],json.loads(data["config"]))
    report["input_files"]={name:sha(value) for name,value in data.items()}
    if args.preview:report["preview"]=preview(after,report,args.preview)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_bytes((json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    print(json.dumps(dict(status="PASS",rom_sha256=sha(after),manifest_sha256=sha(args.manifest.read_bytes()),
                         declared_bytes=report["declared_bytes"],negatives=report["negative_checks"]["count"])))


if __name__=="__main__":
    main()

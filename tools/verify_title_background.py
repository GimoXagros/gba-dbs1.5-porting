#!/usr/bin/env python3
"""Independent final-byte/source checks for the 1.5 title background layer.

No generator, conversion helper or generator manifest is imported.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

BASE=0x08000000
PARENT="428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281"
GBA="996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
TILE_A,TILE_B,MAP,PAL,CODE=0x712680,0x717F40,0x6FBDA8,0x6FC198,0x6FC298
SPANS=((TILE_A,TILE_A+8192),(TILE_B,TILE_B+4864),(MAP,MAP+1008),(PAL,PAL+256),(CODE,CODE+48))
HOOKS=(0x90924,0x90B7C,0x90B90)

def sha(data):return hashlib.sha256(data).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)
def u32(data,at):return struct.unpack_from("<I",data,at)[0]
def seq(data,at,expected):
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(data[at:at+len(expected)*4],BASE+at))
    need([i.mnemonic+" "+i.op_str for i in code]==expected,f"native instructions {at:X}")
def literal(data,at):
    word=u32(data,at);need(word&0x0FFF0000==0x059F0000,"positive native PC literal")
    return u32(data,at+8+(word&4095))
def color(word):
    return sum((0 if ((word>>s)&15)==0 else 2*((word>>s)&15)+1)<<(5*i) for i,s in enumerate((8,4,0)))
def source_pixel(data,tile,x,y):
    return sum(((data[tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
def native_pixel(data,tile,x,y):return (data[tile*32+y*4+x//2]>>(4*(x%2)))&15

def assets(after,gba,wsc):
    planar=wsc[0x4A84B0:0x4AB7B0]
    native=after[TILE_A:TILE_A+8192]+after[TILE_B:TILE_B+4864]
    need(len(planar)==len(native)==13056,"complete408 tile population")
    for tile in range(408):
        for y in range(8):
            for x in range(8):need(source_pixel(planar,tile,x,y)==native_pixel(native,tile,x,y),"source planar/native nibble inverse")
    source_palette=struct.unpack_from("<96H",wsc,0x4AB6B0)
    converted=tuple(map(color,source_palette))
    need(struct.unpack_from("<96H",after,PAL)==converted,"six source palette rows")
    need(after[PAL+192:PAL+256]==gba[0x8FC18:0x8FC58],"retained two native palette rows")
    need(struct.pack("<16H",*map(color,struct.unpack_from("<16H",wsc,0x4AB790)))==gba[0x8B748:0x8B768],"secondary palette commercial identity")
    original_map=struct.unpack_from("<504H",wsc,0x4A80C0)
    native_map=struct.unpack_from("<504H",after,MAP)
    banks=set();tiles=set();palettes=set();pixels=bytearray();zeros=0
    for index,(old,new) in enumerate(zip(original_map,native_map,strict=True)):
        bank=(old>>13)&1;tile=(old&511)+bank*512;pal=(old>>9)&15
        need(400<=tile<808 and 1<=pal<=6,"source map owned tile/palette extent")
        need((new&1023,new>>12,bool(new&1024),bool(new&2048))==
             (tile,pal,bool(old&0x4000),bool(old&0x8000)),"map bank/flip/palette inverse")
        banks.add(bank);tiles.add(tile);palettes.add(pal)
        for y in range(8):
            for x in range(8):
                sx=7-x if old&0x4000 else x;sy=7-y if old&0x8000 else y
                source_address=(0x8000 if bank else 0x4000)+(old&511)*32
                source_tile=(source_address-0x7200)//32
                need(source_tile==tile-400,"WSC bank physical-address inverse")
                a=source_pixel(planar,source_tile,sx,sy)
                b=native_pixel(native,(new&1023)-400,7-x if new&1024 else x,7-y if new&2048 else y)
                need(a==b,"displayed pixel inverse including flips")
                zeros+=a==0;pixels.extend(struct.pack("<H",converted[(pal-1)*16+a]))
    need(banks=={0,1} and len(tiles)==400 and min(tiles)==400 and max(tiles)==799,"full source bank/tile population")
    need(zeros==0,"GBA index-zero transparency discrepancy")
    return dict(loaded_tiles=408,tile_pixels=26112,map_cells=504,displayed_pixels=32256,
                used_tiles=400,used_tile_range=[400,799],banks=sorted(banks),palettes=sorted(palettes),
                mapped_color_zero_pixels=zeros,display_cell_order_rgb555_sha256=sha(pixels))

def source_consumers(wsc):
    need(sha(wsc[0x780003:0x78010E])=="C2C39F287950417BA6B3F3DF71AF5A57B0A605D0A8510952056B37D28C2B9106","complete source initializer producer")
    instructions={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(wsc[0x780003:0x78010E],3)}
    anchors={0x39:("mov","ax, 0x380c"),0x3C:("mov","ds, ax"),0x3E:("mov","ax, 0xca"),0x41:("out","0xc3, al"),
             0x43:("mov","di, 0xfe20"),0x4F:("mov","si, 0x35f0"),0x59:("mov","cx, 0x60"),
             0x5E:("mov","ax, 0x300"),0x61:("mov","es, ax"),0x63:("mov","di, 0x2d8"),0x67:("mov","cx, 0x60"),
             0x70:("mov","di, 0x7200"),0x7C:("mov","si, 0x3f0"),0x85:("mov","cx, 0x1980"),
             0x8A:("mov","di, 0x800"),0x96:("mov","si, 0"),0x9F:("mov","cx, 0x12"),0xA3:("mov","cx, 0x1c"),0xA8:("add","di, 8")}
    need(all(instructions.get(a)==v for a,v in anchors.items()),"positive source bank/palette/tiles/map consumers")
    for a in (0x48,0x75,0x8F):need(instructions[a]==("xor","ax, ax"),"fixed Japanese source branch")
    return {"code_sha256":sha(wsc[0x780003:0x78010E]),"anchors":len(anchors)+3,"banked_base":0x4A80C0}

def consumers(after,before,gba):
    # Prove the existing mode-3 dispatch selects this initializer; hash is retail-derived.
    need(sha(gba[0x15AB4:0x15BD4])=="4F7182E201691A208435A2358DCDFB163C5DA5791F15CC232510153D7DFFD77D","retail mode dispatch identity")
    need(after[0x15AB4:0x15BD4]==gba[0x15AB4:0x15BD4],"retained actual mode dispatcher")
    seq(after,0x15AC8,["ldrh r0, [r5]","add r1, r0, r0, lsl #1","lsl r1, r1, #2","add r8, pc, #0x9c","ldr sb, [r8, r1]","mov lr, pc","bx sb"])
    need(u32(after,0x15B70+3*12)==BASE+0x908A0,"mode3 title initializer entry")
    need(after[0x908A0:0x90924]==gba[0x908A0:0x90924],"retail initializer reaches palette and hook")
    seq(after,0x90900,["ldr r5, [pc, #0x270]","ldr r4, [pc, #0x270]","stmdb sp!, {r4}","mov r2, #0x40","bl #0x8000b84","ldr r5, [pc, #0x264]","ldm sp!, {r4}","mov r2, #0x40","bl #0x8000b84"])
    need((literal(after,0x90900),literal(after,0x90904),literal(after,0x90914))==(0x05000020,BASE+PAL,0x0201E400),"same physical/staging palette source")
    seq(after,0x90924,["b #0x86fc298"])
    seq(after,CODE,["ldr r5, [pc, #0x18]","ldr r4, [pc, #0x18]","mov r2, #0x800","bl #0x8000b84","ldr r4, [pc, #0x10]","mov r2, #0x4c0","ldr lr, [pc, #0xc]","b #0x8000b84"])
    need(tuple(literal(after,CODE+n) for n in (0,4,16,24))==(0x06003200,BASE+TILE_A,BASE+TILE_B,0x08090938),"helper destination/sources/return ABI")
    decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM);decoder.detail=True
    need(all(not i.update_flags for i in decoder.disasm(after[CODE:CODE+32],BASE+CODE)),"all helper flags preserved")
    need(sha(after[0xB84:0xBA8])=="7F3A5BB5C97441ACE990D2F73353C30FB43540ED3E5528A303FF7CC81A4D64C8","actual DMA32 count and advancing source/destination")
    need(after[0x90928:0x909D0]==gba[0x90928:0x909D0],"all original map/shared transfer instructions retained")
    seq(after,0x90938,["ldr r5, [pc, #0x24c]","ldr r4, [pc, #0x24c]","mov fp, #0x12","mov r2, #0xe","bl #0x8000b84","add r5, r5, #8","subs fp, fp, #1","bgt #0x8090944"])
    need((literal(after,0x90938),literal(after,0x9093C))==(0x0600F000,BASE+MAP),"map source/destination")
    for at,value in ((0x90970,0x0600F800),(0x90980,0x08080D40),(0x90998,0x06007080),(0x9099C,0x08080140),(0x909A8,0x0600F840),(0x909AC,0x08080DC0),(0x909B8,0x0808B748),(0x909BC,0x03002C38)):
        need(literal(after,at)==value,"shared transfer owners retained")
    need(sha(after[0x914E4:0x91598])=="6FDAC1A527B5091A2A19A343A425658ABB59454A9BBFA1D523766D084A38A6FF","complete native fade staging consumer")
    need(tuple(literal(after,a) for a in (0x9152C,0x91538,0x91544))==(0x05000020,0x0201E800,0x0201E400),"fade physical/source staging pointers")
    seq(after,0x91550,["mov r8, #0x80"])
    seq(after,0x91568,["bl #0x801207c"])
    need(after[0x1207C:0x12138]==gba[0x1207C:0x12138],"native 128-halfword fade processor unchanged")
    need(after[0x8B748:0x90924]==before[0x8B748:0x90924] and after[0x90A18:0x90A1C]==before[0x90A18:0x90A1C],"old shared artwork and current language hook preserved")
    # Inverse already excludes extra writes. These are independently calculated extents.
    need(0x06003200+0x800*4==0x06005200 and 0x06005200+0x4C0*4==0x06006500,"two DMA tile extents")
    return {"entry":0x080908A0,"mode":3,"tile_dma_ranges":[[0x06003200,0x06005200],[0x06005200,0x06006500]],
            "map_rows":18,"map_row_bytes":56,"map_stride":64,"map_end_exclusive":0x0600F478,
            "physical_palette":[0x05000020,0x05000120],"staging_palette":[0x0201E400,0x0201E500],"fade_halfwords":128,
            "continuation":0x08090938,"flags_and_stack_preserved":True}

def inbound(data,spans,origin=0):
    """Independent conservative decoder, no generator ownership declarations."""
    found=[]
    def check(kind,offset,target):
        if 0x08000000<=target<0x0E000000:
            raw=target&0x1FFFFFF
            if any(lo<=raw<hi for lo,hi in spans):found.append([kind,origin+offset,target])
    for off in range(len(data)-3):check("pointer",off,u32(data,off))
    def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value
    for off in range(0,len(data)-3,4):
        w=u32(data,off);pc=BASE+origin+off+8
        if w&0x0E000000==0x0A000000:check("ARM branch",off,pc+signed(w&0xFFFFFF,24)*4)
        if w&0x0F7F0000 in (0x051F0000,0x055F0000):check("ARM literal",off,pc+(w&4095)*(1 if w&0x800000 else -1))
        if w&0x0FFF0000 in (0x028F0000,0x024F0000):
            v=w&255;r=((w>>8)&15)*2;v=((v>>r)|(v<<(32-r)))&0xFFFFFFFF
            check("ARM ADR",off,pc+(v if w&0x01E00000==0x00800000 else -v))
    half=struct.unpack("<"+str(len(data)//2)+"H",data[:len(data)//2*2])
    for index,w in enumerate(half):
        off=index*2;pc=BASE+origin+off+4
        if w&0xF800 in (0x4800,0xA000):check("Thumb literal/ADR",off,(pc&~3)+4*(w&255))
        if w&0xF800==0xE000:check("Thumb B",off,pc+2*signed(w&2047,11))
        if w&0xF000==0xD000 and w&0x0F00<0x0E00:check("Thumb conditional",off,pc+2*signed(w&255,8))
        if w&0xF800==0xF000 and index+1<len(half):
            tail=half[index+1]
            if tail&0xF800 in (0xF800,0xE800):
                target=pc+(signed(w&2047,11)<<12)+((tail&2047)<<1)
                check("Thumb BL/BLX",off,target&~3 if tail&0xF800==0xE800 else target)
    return found

def inverse(after,before):
    need(len(after)==len(before)==0x800000,"whole native ROM extent")
    restored=bytearray(after)
    for lo,hi in SPANS+tuple((a,a+4) for a in HOOKS):restored[lo:hi]=before[lo:hi]
    need(restored==before,"full-ROM inverse outside eight independently owned spans")
    return sha(restored)

def literal_owners(before,gba):
    references=inbound(before,((0x90B7C,0x90B80),(0x90B90,0x90B94)))
    need(references==[["ARM literal",0x90904,0x08090B7C],["ARM literal",0x9093C,0x08090B90],
                      ["ARM branch",0xA8BA0,0x08090B90],["Thumb B",0x9103A,0x08090B7C]],"complete modified literal reference population")
    # Prove the apparent ARM branch belongs to a native tile DMA source, rather than guessing from its appearance.
    need(before[0x832A0:0x83318]==gba[0x832A0:0x83318],"retained retail indexed palette/tile DMA body/table")
    seq(before,0x832B8,["ldr r5, [pc, #0x28]","add r8, pc, #0x30","ldr r4, [r8, r1, lsl #3]","mov r2, #0x600","bl #0x8000b84"])
    need(literal(before,0x832B8)==0x06005780 and u32(before,0x832F4+4*8)==0x080A8940,"positive row4 tile source and VRAM destination")
    need(0xA8940<=0xA8BA0<0xA8940+0x600*4 and before[0xA8940:0xAA140]==gba[0xA8940:0xAA140],"complete retained tile payload containing raw branch match")
    need(u32(before,0xA8BA0)==0xAAFF9FFA,"exact raw branch-shaped tile word")
    # Thumb E59F is the upper halfword of this positively dispatched ARM routine's LDR.
    need(u32(before,0x15B98)==BASE+0x90BF4,"mode3 ARM frame callback owner")
    need(before[0x90BF4:0x91050]==gba[0x90BF4:0x91050],"retail ARM callback containing apparent Thumb reference")
    seq(before,0x91030,["ldr r8, [pc, #0x258]","ldr sb, [r8]","ldr r0, [pc, #0x254]","str r0, [sb]","ldr r8, [pc, #0x250]","ldrh sb, [r8]","orr sb, sb, #2","strh sb, [r8]"])
    return {"actual_pc_literal_consumers":[0x08090904,0x0809093C],
            "classified_raw_matches":[{"address":0x080A8BA0,"word":"AAFF9FFA","reason":"inside native tile DMA row4 source080A8940..080AA140, consumer080832B8..080832C8"},
                                      {"address":0x0809103A,"word":"E59F0254","reason":"upper halfword of native ARM LDR at08091038 inside mode3 frame callback"}]}

def core(after,before,gba,wsc):
    inverse(after,before)
    consumer=consumers(after,before,gba)
    return {"consumers":consumer,"assets":assets(after,gba,wsc)}

def negative_controls(after,before,gba,wsc):
    cases=[]
    for lo,hi in SPANS:
        cases.extend([(f"first owned byte {lo:X}",lo,1),(f"last owned byte {hi-1:X}",hi-1,1)])
    cases.extend((name,at,mask) for name,at,mask in (
        ("tile bank bit",MAP+1,2),("horizontal flip",MAP+1,4),("vertical flip",MAP+1,8),("palette row",MAP+1,16),
        ("first DMA count",CODE+8,1),("second DMA count",CODE+20,1),("continuation",CODE+44,4),
        ("destination",CODE+32,4),("palette literal",0x90B7C,4),("map literal",0x90B90,4),
        ("branch condition",0x90927,16),("undeclared outside byte",0x200,1)))
    rejected=[]
    for name,at,mask in cases:
        changed=bytearray(after);changed[at]^=mask
        try:core(changed,before,gba,wsc)
        except (ValueError,IndexError):rejected.append(name)
        else:raise ValueError("undetected negative control: "+name)
    # Test the reference detector independently with positive incoming references.
    controls=[("unaligned mirrored pointer",bytes(1)+struct.pack("<I",0x0C6FC298)+bytes(3),0),
              ("ARM branch",struct.pack("<I",0xEA000000|(((CODE-8)//4)&0xFFFFFF)),0),
              ("ARM literal",struct.pack("<I",0xE59F0000),CODE-8),
              ("ARM ADR",struct.pack("<I",0xE28F0000),CODE-8),
              ("Thumb literal",struct.pack("<2H",0x4800,0),CODE-4),
              ("Thumb ADR",struct.pack("<2H",0xA000,0),CODE-4),
              ("Thumb B",struct.pack("<2H",0xE000,0),CODE-4),
              ("Thumb conditional",struct.pack("<2H",0xD000,0),CODE-4),
              ("Thumb BL",struct.pack("<2H",0xF000,0xF800),CODE-4)]
    for name,data,origin in controls:need(bool(inbound(data,SPANS,origin)),"ownership detector "+name)
    need(not inbound(bytes(32),SPANS),"ownership empty negative control")
    return {"mutated_artifacts_rejected":rejected,"incoming_reference_controls":[name for name,_,_ in controls],"empty_control":True}

def main():
    parser=argparse.ArgumentParser()
    for name in ("before","after","gba","wsc15","output"):parser.add_argument(name,type=Path)
    a=parser.parse_args();need(not a.output.exists(),"do not overwrite a prior independent report")
    before,after,gba,wsc=(p.read_bytes() for p in (a.before,a.after,a.gba,a.wsc15))
    need((sha(before),sha(gba),sha(wsc))==(PARENT,GBA,WSC),"pinned independent original inputs")
    for lo,hi in SPANS:need(before[lo:hi]==b'\xff'*(hi-lo),"unowned clean allocation")
    owners=inbound(before,SPANS);need(not owners,f"existing incoming allocation owner {owners[:8]}")
    report={"status":"PASS_STATIC_COMPONENT","before_sha256":sha(before),"after_sha256":sha(after),"gba_sha256":sha(gba),"wsc15_sha256":sha(wsc),
            "source_consumers":source_consumers(wsc),**core(after,before,gba,wsc),
            "ownership":{"spans":SPANS,"existing_inbound":owners,"mirrors_and_all_pointer_alignments":True,"arm_thumb_literal_branch_adr":True},
            "changed_literal_owners":literal_owners(before,gba),
            "full_rom_inverse_sha256":inverse(after,before),"changed_bytes":sum(x!=y for x,y in zip(before,after,strict=True)),
            "negative_controls":negative_controls(after,before,gba,wsc),
            "limitations":["Static isolated title-background component only; runtime validation remains separate.","The native five-label title selector is retained. The source extra-menu controller/events are not implemented by this component."]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({"status":report['status'],"report_sha256":sha(a.output.read_bytes()),"output_sha256":sha(after)}))

if __name__=="__main__":main()


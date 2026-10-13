#!/usr/bin/env python3
"""Bound the inherited case-5 release list to its actual native object pools."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'vendor'))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

HASH = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
RANGES = (
 (0x341034,0x34136C,'9B16BDE5A4397680DD768E19C3634DBBF37A30BB3A05F9D80DEEDC0FD4AEDB37'),
 (0x378C14,0x378DAC,'BAA8C9B98384103FE76CDA489DDB14A66838094B7B4009563D23EDB454832025'),
 (0x352374,0x3524C4,'D95AE0375837FDAAC54A7619B2C3C383DB3CA42B239DD3DAEFBD8F25A3BF8121'),
 (0x352B78,0x352C0C,'1F842C3C31E5F69B51612C58452E37010CDA8509E26EDB702EDCF1D0F587749D'),
 (0x34059C,0x34064C,'BDE4BA9E7854C7F2BDF44F9FAE1A4EB85ADD2579F4BE8FA530E2081AD75DC104'),
)
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def need(c,m):
 if not c: raise ValueError(m)
def listing(b,start,end):
 return [f'{i.mnemonic} {i.op_str}' for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(b[start:end],0x08000000+start)]
def literal(b,pos):
 op,=struct.unpack_from('<I',b,pos)
 need(op&0x0FFF0000==0x059F0000,'positive PC literal load')
 return struct.unpack_from('<I',b,pos+8+(op&0xFFF))[0]
def inspect(g):
 # Two independent actual append paths: ordinary dropped collectible and
 # scripted collectible presentation. Both ask the same native pool0 owner.
 need(literal(g,0x341054)==0x03004760,'ordinary list receiver')
 need(listing(g,0x34119C,0x3411AC)==['mov r8, #0','stmdb sp!, {r8}','bl #0x8352374','add sp, sp, #0x1c'],'ordinary pool0 allocation')
 need(listing(g,0x341304,0x341310)==['str r1, [r5], #4','subs r2, r2, #1','bgt #0x8341174'],'ordinary append loop')
 need(literal(g,0x378C24)==0x03004760,'script list receiver')
 need(listing(g,0x378C28,0x378C2C)==['str sb, [r1, #4]'],'script retained list')
 need(listing(g,0x378CC0,0x378CC8)==['ldr r0, [r1, #4]','stmdb sp!, {r0}'],'script allocator destination')
 need(listing(g,0x378CE8,0x378CF8)==['mov r8, #0','stmdb sp!, {r8}','bl #0x8352374','add sp, sp, #0x1c'],'script pool0 allocation')
 need(listing(g,0x352378,0x352388)==['ldr r1, [sp, #0x14]','add r8, pc, #4','ldr sb, [r8, r1, lsl #2]','bx sb'],'allocator pool selector')
 need(struct.unpack_from('<6I',g,0x352388)==(0x083523A0,0x083523AC,0x083523B4,0x083523C0,0x083523C8,0x083523D0),'six pool dispatches')
 need(literal(g,0x3523A0)==0x03004810 and listing(g,0x3523A4,0x3523A8)==['mov r2, #0xf'],'pool0 fifteen slots')
 need(literal(g,0x3523C0)==0x03004824 and literal(g,0x3523C8)==0x03004825,'fighter pool slots')
 need(literal(g,0x3523D0)==0x03004826 and listing(g,0x3523D4,0x3523D8)==['mov r2, #2'],'aux pool two slots')
 need(listing(g,0x352BA4,0x352BB4)==['mov r8, #3','stmdb sp!, {r8}','bl #0x8352374','add sp, sp, #0x1c'],'first fighter pool3')
 need(listing(g,0x352BE0,0x352BF0)==['mov r8, #4','stmdb sp!, {r8}','bl #0x8352374','add sp, sp, #0x1c'],'second fighter pool4')
 need(literal(g,0x352B80)==0x0300489C and literal(g,0x352BBC)==0x030048A0,'actual fighter destinations')
 need(literal(g,0x3405C8)==0x03004760 and literal(g,0x3405CC)==0x0300475E,'inherited case5 list and count')
 need(listing(g,0x3405DC,0x3405F8)==['ldr r8, [r5], #4','stmdb sp!, {r8}','stmdb sp!, {fp}','bl #0x83524c4','add sp, sp, #8','subs r2, r2, #1','bgt #0x83405dc'],'inherited release order')
 # This is a finite producer/pool ownership proof. It is deliberately not a
 # promise of safety after memory corruption or arbitrary foreign task entry.
 return dict(released_pool=0,released_flag_slots=[0x03004810,0x0300481F],
             fighter_pools=[3,4],fighter_flag_slots=[0x03004824,0x03004825],
             auxiliary_pool=5,auxiliary_flag_slots=[0x03004826,0x03004828],
             normal_case5_inherits_same_list_release=True,
             arbitrary_foreign_writers_excluded=False,
             precondition='normal initialized retail battle; uncorrupted engine-owned lists and pool pointers',
             runtime_executed=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('gba',type=pathlib.Path);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args()
 g=a.gba.read_bytes();need(sha(g)==HASH,'original hash')
 for start,end,h in RANGES:need(sha(g[start:end])==h,'original evidence range')
 r=inspect(g);negative=[]
 for pos,word,label in ((0x34119C,0xE3A08005,'collectible uses auxiliary pool'),(0x352BA4,0xE3A08000,'fighter uses collectible pool'),(0x340634,0x0300489C,'case5 releases fighter slot')):
  m=bytearray(g);struct.pack_into('<I',m,pos,word)
  try:inspect(m)
  except ValueError:negative.append(label)
  else:raise ValueError('ineffective negative '+label)
 r.update(input_sha256=HASH,evidence_ranges=RANGES,negative_controls=negative)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(sha(a.output.read_bytes()))
 return 0
if __name__=='__main__':raise SystemExit(main())

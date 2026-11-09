#!/usr/bin/env python3
"""Pinned source/native fields for the guarded transition component.

This proves the listed local consumers, not a global low-Y settling theorem.
The independent committed layout ledger binds declared added-ROM ownership.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from analyze_shoot_lifetime_consumers import exact,blank_tile_initializer
from analyze_shoot_player_transitions import contracts as neutral_contracts

INPUT='025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
LAYOUT_SHA='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
LAYOUT=ROOT/'records/shoot-guarded-transition-layout-20261109.json'
PINS=(
 (0xD0BC0,0xD0C70,'B153D59A562815BC73EA19E06EAD026A01E0709199D588DAD66262DA31FFFD36'),
 (0x17758,0x177B0,'77EE72EC762AB9DC9294E8611F89D952686BD903828C6C240182BCD205794DFE'),
 (0x11D78,0x11E50,'88AE7E86FA93BB8D92C4FB90E0FB2E1399DDB72F3E8079FF4C3DB9C702E1CD7E'),
 (0xD19F8,0xD1A1C,'25F640BD7A9CF34295E80B252BE4D72CAC93ED1F693E761DE9414EEB1642C68F'),
 (0x352268,0x35227C,'9C86419369623ED7CFA21FF44195BC3CE6154EBE879D27BDC2E8183806416A5C'),
 (0x5E7400,0x5E7548,'019D8C1BCE934C7D91CDC31E8243C7F48A4D26AEC0BAF4BB1E558E3D12C08CDD'),
 (0x374FAC,0x374FF4,'96CD173356EF7B40AE401D3B5226650C3FF682CB2E980866D24374875FE8CB77'),
 (0x37354C,0x3735BC,'90E6A5849630FC562BB7568E17DC027D6FA1E52D1A7F1F7B62E0B40360BCACAE'),
 (0x3561D8,0x3562B4,'86A8801B27D0213FAFDFF4404138276F5450C0FE73A0D02A0978289167BFE2AF'),
 (0x373928,0x373B34,'4DD9FC2290562670439CF4BD47D7732CB5CCCD9946452EC50478483F62AC8484'),
 (0x12C58,0x12DBC,'DAE06B2172BEC643D5A7C698F1036D082C04D4450F18FF4B567AC8D996B48E22'),
)


def sha(b):return hashlib.sha256(b).hexdigest().upper()


def need(ok,label):
    if not ok:raise ValueError(label)


def arm(b,at,expected):
    rows=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(b[at:at+4*len(expected)],0x08000000+at))
    need([i.mnemonic+' '+i.op_str for i in rows]==expected,f'native instruction consumer{at:X}')


def word(b,at):return struct.unpack_from('<I',b,at)[0]


def layout_proof(before,first,last,path=LAYOUT):
    raw=Path(path).read_bytes();need(sha(raw)==LAYOUT_SHA,'independent committed layout ledger identity')
    d=json.loads(raw)
    need(d['predecessor_sha256']==sha(before)==INPUT and d['retail_bytes']==0x400000,
         'expanded storage predecessor ownership')
    need(d['normalized_interval_count']==1394 and d['layer_count']==70,'complete predecessor layout population')
    need(all(last<=a or first>=z for a,z in d['merged_union']), 'no declared object extent overlaps reservation, including FF tails')
    return dict(ledger_sha256=LAYOUT_SHA,declared_intervals=1394,union_intervals=len(d['merged_union']),
                retail_bytes=0x400000,reservation=[first,last],overlap_count=0)


def proof(before,gba,source,first=0x6FF9C0,last=0x6FFF60):
    need((sha(before),sha(gba),sha(source))==(INPUT,GBA,SOURCE),'exact predecessor/retail/source')
    need(len(gba)==0x400000 and len(before)==0x800000,'retail and expanded ROM extents')
    for a,z,h in PINS:need(sha(before[a:z])==h,f'frozen native consumer{a:X}')
    neutral_contracts(source)
    blank=blank_tile_initializer(source)
    need(sha(source[0x75FC27:0x75FCAB])=='5191A1AAC4A834923F06224604730B0271C093D93D2AF495705C72E672687FB1','source exact IRQ/table')
    need(sha(source[0x75FB20:0x75FB58])=='AA5428F95C0705E9B2FD5AF7BC360DAAF149DCABC2D739B82655087D55707ADA','source next-display horizontal overwrite')
    exact(source,0x75FC90,['mov bx, 0x300','mov es, bx','mov bx, 0xea',
                         'mov ax, word ptr es:[di + 0xa]','out 0x10, al'])
    arm(before,0x5E74B4,['mov r0, #0','strh r0, [r5, #6]','ldrh r0, [r5, #2]',
                        'strh r0, [r5, #4]','sub r1, r0, #1','and r1, r1, #0xff',
                        'bic r0, r0, #0xff','orr r0, r0, r1','strh r0, [r5, #2]'])
    arm(before,0x5E7434,['ldrb r0, [r5, #2]','bl #0x8000f2c','ldrb r0, [r5, #3]','bl #0x8000f44'])
    need(word(before,0x5E7524)==0x0300456C,'next-display independent prepared scroll tuple')
    arm(gba,0xF44,['ldr r8, [pc, #0x60]','strb r0, [r8]','mov sb, #0x4000000',
                   'sub sl, r0, #8','strh sl, [sb, #0x16]','bx lr'])
    arm(gba,0xC4C,['mov r8, #0x4000000','ldrh r0, [r8, #4]','bx lr'])
    arm(gba,0xC10,['mov r8, #0x4000000','ldrh sb, [r8, #4]','and sb, sb, #0xff',
                   'add sb, sb, r0, lsl #8','orr sb, sb, #0x20','strh sb, [r8, #4]','bx lr'])
    for at in (0xC9904,0xC991C,0xC9928):need(word(gba,at)==0x030012E0,'all fallback arms replace IRQslot')
    for at in (0xC9838,0xC9880,0xC98A8):arm(gba,at,['str sb, [r8]'])
    for at in (0x5BF200,0x5BF600):arm(before,at,['bx lr'])
    need(struct.unpack_from('<2I',before,0x4A80F8)==(0x080D7A58,0x080D45B8),'baseID0 P0/P1 resource roles')
    need([word(before,a) for a in (0x582B58,0x582B5C,0x582B74,0x582B78)]==
         [0x0600F800,0x030012BA,0x0600F000,0x030012B8],'Shoot-specific descriptor/map/scroll mapping')
    # Native copy initialization: cumulative destination DB0, 1C words from
    # C9008, immediate32-bit DMA. This is retained startup, not an invented stub.
    need(word(gba,0x3B4)==0x080C9008 and word(gba,0xC9064)==0x03000DB0,'real queue helper copy lineage')
    arm(gba,0x244,['add r7, r7, #0x1c0','str r7, [r6, #0xd8]',
                  'ldr r4, [pc, #0x160]','str r4, [r6, #0xd4]',
                  'mov r4, #0x1c','strh r4, [r6, #0xdc]','strh r8, [r6, #0xde]'])
    arm(gba,0xC9008,['ldr r5, [pc, #0x58]','ldr r0, [r5]','orrs r0, r0, r0','bxeq lr'])
    need(word(gba,0xC9068)==0x03004574,'actual scanline queue count')
    arm(before,0xD0BE8,['bl #0x8017758'])
    arm(before,0x352270,['bl #0x80d0bc0'])
    need(word(before,0xD1AE4)==0x08352268 and word(before,0xD1AE8)==0x03004518,
         'late F000 task constructor and owned header')
    arm(before,0xD1A04,['mov r8, #0xf000'])
    arm(before,0x11AE4,['ldr r0, [sp, #0x14]','lsl r0, r0, #0x10',
                       'asr r0, r0, #0x10','str r0, [r5, #4]'])
    need([word(before,a) for a in (0x177A0,0x177A4,0x177A8,0x177AC)]==
         [0x03002474,0x03004574,0x03002478,0x03004578],'real prepared queue copy')
    arm(before,0xD0C10,['ldr r5, [pc, #0x4c]','mov r0, #0',
                       'strh r0, [r5, #0x1c]','strh r0, [r5, #0x1e]'])
    need(word(before,0xD0C60)==0x12B and word(before,0xD0C64)==0x03002338,
         'line1 IRQ and only remaining descriptor velocity stores')
    need(word(before,0x11E48)==0x03001344,'scheduler last-header owner')
    need(word(gba,0x340CBC)==0x03002310,'retained native mode-state owner, not battle flags')
    arm(gba,0x340C90,['mov r8, #1','strh r8, [sb, #4]','mov r8, #0',
                      'strh r8, [sb, #6]','mov r8, #0','strh r8, [sb, #8]'])
    return dict(schema=1,status='LOCAL_TRANSITION_FIELDS_AND_IRQ_CONTRACT_PASS',
                predecessor_sha256=INPUT,source_sha256=SOURCE,layout=layout_proof(before,first,last),
                source_blank_initializer=blank,
                guard_current_rows='native y=k+37..159, row((state8-29+y)&255)>>3, all32cells zero',
                counter='pre-display oldstate2 becomes state4, state2 lowbyte decremented; state8 unchanged',
                native_blank='current BG1CNT text/charbase0/4bpp/no-mosaic/screenbase30 plus06000000..1F zero',
                next_horizontal_kill='prepared0300456E→F2C before next display routing',
                exact_source_operand_not_emulated=True,low_Y_moving_entry_closed=False,
                callsite_timing='D0BE8 after real17758; constructor-signextended FFFFF000 current4518==last1344 after111B0 wait; sole4578 callback substituted; C9000 pops1 to0 before VCOUNT1',
                lifetime='Neutral base0/control0/motion0/noop upper+aux preserve stationary family; current rows avoid historical refill assumption; next iteration may execute and is not claimed quiescent',
                stale_callback='tiny wrapper rechecks mode7/stage11/0400 and otherwise tails unchanged8587200; source mode8 exit can retain stage11/0400')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('gba',type=Path);p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=proof(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
    print(d['status'])


if __name__=='__main__':main()

"""Relocatable header-only overlay at the existing portrait DMA completion.

The caller supplies a 60-entry table of pointers to 768-byte headers ordered
language-major then physical ID. No allocator, ROM writer or state owner here.
"""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
HOOK=0x084A5C6C
OLD_WORD=0xE59F401C
GETTER=0x08633400
GETTER_SHA='5F72868A07F73A7FC2892A38BB9902BB8986B2FFB9460F454F8A41E4AC7FCFD7'
def assembly(table_address):
 assert 0x08000000<=table_address<0x0A000000 and table_address%4==0
 return f'''
 stmdb sp!, {{r0-r12,lr}}
 mrs r12,cpsr
 stmdb sp!, {{r12}}
 ldr r12, ={GETTER}
 mov lr,pc
 bx r12
 rsb r0,r0,r0,lsl #4
 add r0,r0,r1
 ldr r8, ={table_address}
 ldr r4,[r8,r0,lsl #2]
 ldr r5, =0x06005780
 mov r2,#0xc0
 ldr r12, =0x08000b84
 mov lr,pc
 bx r12
 ldmia sp!, {{r12}}
 msr cpsr_f,r12
 ldmia sp!, {{r0-r12,lr}}
 ldr r4, =0x03004710
 ldr pc, =0x084a5c70
 .ltorg
 '''
def assemble(address,table_address):
 assert address%4==0
 return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(assembly(table_address),addr=address)[0])
def hook(address):
 delta=address-HOOK-8
 assert delta%4==0 and -(1<<25)<=delta<(1<<25)
 return struct.pack('<I',0xEA000000|((delta>>2)&0xffffff))

"""Bind the retail's matching confetti initializer and selected-character motion events."""
import struct
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

START, END = 0xbf2e0, 0xbf4a8
EVENTS = (0, 2, 3, 4, 5, 6, 7, 17, 86)


def assembly(native, source):
    # 73D3:0A28 populates the thirty source particles. Native BF334..F4A0
    # consumes the identical positions, palettes and P0/P1 through real services.
    assert native[0xbbb88:0xbbb88+120] == source[0x774ca8:0x774ca8+120]
    dis = Cs(CS_ARCH_ARM,CS_MODE_ARM)
    lines = ['m11_start_confetti:', 'push {r0-r12,lr}']
    section = list(dis.disasm(native[START:END],0x08000000+START))
    assert len(section)*4 == END-START
    for inst in section:
        name, arg = inst.mnemonic,inst.op_str
        lines.append(f'm11_party_{inst.address:x}:')
        if name=='ldr' and '[pc, #' in arg:
            dst, imm = arg.split(', [pc, #')
            offset = inst.address-0x08000000+8+int(imm[:-1],0)
            value = struct.unpack_from('<I',native,offset)[0]
            arg = f'{dst}, ={value:#x}'
        elif name in ('bgt','blo','bl'):
            dest=int(arg.lstrip('#'),0)
            if 0x08000000+START<=dest<0x08000000+END:
                arg=f'm11_party_{dest:x}'
            else:
                assert name=='bl' and 0x08000000<=dest<0x09000000
                arg=f'{dest:#x}'
        lines.append(f'{name} {arg}')
    lines.extend(['pop {r0-r12,pc}', '.ltorg'])
    def word(bus):
        return struct.unpack_from('<I',native,bus-0x08000000)[0]
    ticks=[]
    for actor in range(15):
        p0,p1=struct.unpack_from('<II',native,0x4a80f8+actor*32)
        layouts,descs=word(p0),word(p0+4)
        cmds=word(p1)
        assert (word(cmds+4)-cmds)//16 > max(EVENTS)
        durations={}
        for event in EVENTS:
            count,frames=word(cmds+16*event),word(cmds+16*event+4)
            elapsed=0
            for k in range(count):
                at=frames-0x08000000+16*k
                t,_,layout,art=struct.unpack_from('<BBHH',native,at)
                assert 0<t<=255
                elapsed+=t
                n=word(layouts+8*layout)
                parts=word(layouts+8*layout+4)-0x08000000
                size=word(descs+8*art)
                assert 0<n<=127 and 0<size<=0x10000
                assert all((struct.unpack_from('<H',native,parts+4*j)[0]&511)*32<size for j in range(n))
            durations[event]=elapsed
        ticks.extend((durations[4],durations[17]))
    lines.append('m11_jump_ticks: .byte '+','.join(map(str,ticks)))
    lines.append('.align 2')
    return '\n'.join(lines)


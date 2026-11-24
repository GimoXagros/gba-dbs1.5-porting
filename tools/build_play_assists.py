"""Apply the Options settings to the solo battle actors before the HUD and result consumers."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_mode24_link_cards import branch
from mode23_linker import compose

INIT = 0x080D1C04
TICK = 0x08373638
NATIVE = 0x08373928
EXPORTS = ('assist_battle_init', 'assist_battle_tick', 'assist_score_store', 'assist_boss_store')


def battle_code(reader):
    return f"""
assist_battle_init:
    str r0,[r8]
    push {{r0-r3,r12,lr}}
    mrs r2,cpsr
    push {{r0,r2}}
    bl 0x{reader:x}
    pop {{r1,r2}}
    str r0,[r1,#0x114]
    msr cpsr_f,r2
    pop {{r0-r3,r12,lr}}
    b 0x{INIT+4:x}

assist_battle_tick:
    push {{r0-r7,lr}}
    mrs r7,cpsr
    ldr r0,=0x03004514
    ldr r1,[r0]
    ldr r2,[r1,#0x114]
    movs r0,r2,lsl #21
    beq assist_continue
    ldr r3,=0x03002310
    ldrh r0,[r3]
    cmp r0,#7
    bne assist_continue
    ldrb r0,[r3,#0x1a]
    tst r0,#1
    bne assist_continue
    ldr r0,=0x0300489c
    ldr r4,[r0]
    ldr r5,[r0,#4]
    cmp r4,#0
    cmpne r5,#0
    beq assist_continue
    ldr r0,[r4,#0x14]
    cmp r0,r4
    ldreq r0,[r5,#0x14]
    cmpeq r0,r5
    ldreq r0,[r4,#0x18]
    cmpeq r0,r5
    ldreq r0,[r5,#0x18]
    cmpeq r0,r4
    bne assist_continue
    ldrb r0,[r4,#0x10]
    cmp r0,#0
    ldrbeq r0,[r5,#0x10]
    cmpeq r0,#1
    bne assist_continue
    ldrsh r0,[r4,#0x64]
    cmp r0,#0
    ldrshgt r0,[r5,#0x64]
    cmpgt r0,#0
    ble assist_continue
    ldrb r3,[r3,#0xe]
    ldr r6,=0x03004502
    ldrh r6,[r6]
    cmp r3,#7
    cmpne r3,#11
    beq assist_boss
    cmp r3,#10
    bhi assist_continue
    cmp r6,#0
    bne assist_continue
    ldrb r0,[r5,#4]
    and r0,r0,#15
    cmp r0,#1
    bne assist_continue
    mov r0,r2,lsl #22
    movs r0,r0,lsr #22
    beq assist_continue
    ldr r6,=1000
    cmp r0,r6
    bhi assist_continue
    sub r0,r0,#1
    ldrh r6,[r4,#0x66]
    cmp r0,r6
    beq assist_continue
assist_score_store:
    strh r0,[r4,#0x66]
    b assist_continue
assist_boss:
    tst r2,#0x400
    beq assist_continue
    cmp r6,#2
    bne assist_continue
    ldrb r0,[r5,#4]
    and r0,r0,#15
    cmp r0,#3
    ldrbeq r0,[r5,#0x11]
    cmpeq r0,#15
    bne assist_continue
    ldr r0,=0x03004d3c
    ldr r0,[r0]
    cmp r0,#0
    beq assist_continue
    ldr r6,[r5,#0x28]
    cmp r6,r0
    ldreq r6,[r0,#0x28]
    cmpeq r6,r5
    bne assist_continue
    ldrb r6,[r0,#4]
    and r6,r6,#15
    cmp r3,#7
    moveq r0,#3
    movne r0,#6
    cmp r6,r0
    bne assist_continue
    ldrb r0,[r1,#0x116]
    cmp r3,r0
    beq assist_continue
    strb r3,[r1,#0x116]
    mov r0,#1
assist_boss_store:
    strh r0,[r5,#0x64]
assist_continue:
    msr cpsr_f,r7
    pop {{r0-r7,lr}}
    b 0x{NATIVE:x}
    .ltorg
"""


def build(image, raw):
    owner=json.loads(raw)
    assert len(image)==0x1000000 and sha(image)==owner['output_sha256']
    reader=owner['symbols']['assist_read']
    assert any(a['start']<=reader-BASE<a['end'] for a in owner['allocations'])
    # The renderer owns a 0x118-byte task. Registration resets the private final
    # word on every allocation, including reuse after a retry or a new game.
    for lo,n,want in ((0xd1bbc,104,'280535597F24892010062FAE3EE6870598F46C3F1F78964B1AFC950576685D2F'),
                      (0x3735bc,136,'C1BA10DC7DD69AC346DD652E2487DD4E910B112BAABD9B19C59B7F216597F458'),
                      (0x377b54,124,'AEBAFF83F2A7BF398279A5A0ED4771D1FFED86DF301B2E2996C0701369EED767')):
        assert sha(image[lo:lo+n])==want
    assert struct.unpack_from('<I',image,INIT-BASE)[0]==0xe5880000
    assert image[TICK-BASE:TICK-BASE+4]==branch(TICK,NATIVE,True)
    prior=owner['prior_excluded_extents']+[[a['start'],a['end']] for a in owner['allocations']]
    alloc=Allocator(image)
    exclude(alloc,prior)
    asm=battle_code(reader)
    trial=compose((asm,),BASE,EXPORTS)[0]
    offset=alloc.allocate(len(trial),'solo battle options',4)
    code,symbols,linkage=compose((asm,),BASE+offset,EXPORTS)
    assert len(code)==len(trial)
    writes=[(offset,code),(INIT-BASE,branch(INIT,symbols[EXPORTS[0]])),
            (TICK-BASE,branch(TICK,symbols[EXPORTS[1]],True))]
    result=bytearray(image)
    rows=[]
    for at,data in sorted(writes):
        rows.append(dict(offset=at,size=len(data),before_sha256=sha(image[at:at+len(data)]),after_sha256=sha(data)))
        result[at:at+len(data)]=data
    return result,dict(input_sha256=sha(image),prior_owner_sha256=sha(raw),output_sha256=sha(result),
                        source_sha256=owner['source_sha256'],symbols=symbols,assist_read=reader,linkage=linkage,
                        storage_exports=owner['storage_exports'],prior_excluded_extents=prior,allocations=alloc.allocations,
                        builder_sha256=sha(Path(__file__).read_bytes()),writes=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for opt in ('input','owner','output'):p.add_argument('--'+opt,type=Path,required=True)
    a=p.parse_args()
    image,meta=build(a.input.read_bytes(),a.owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    (a.output/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8',newline='\n')
    print(meta['output_sha256'])

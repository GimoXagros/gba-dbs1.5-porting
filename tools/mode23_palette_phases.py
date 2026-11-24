"""Mode23 source palette snapshot, alternating fade-out and full fade-in.

The caller must own the shared native palette mirror for the entire phase.
Context+D4 is a private16-bit phase counter, disjoint from both presentations.
"""
import hashlib

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def assembly(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("mode23 palette source mismatch")
    # Source01AB alternates eight palette rows and completes after32 calls;
    # AA70 restores all16 rows per call and decrements its16-call counter.
    assert source[0x7720ED:0x7720F3] == bytes.fromhex("26833ee80320")
    out = ["""
m23_palette_snapshot:
push {r4-r11,lr}
bl 0x085c1900
mov r0,#0
strh r0,[r4,#0xd4]
pop {r4-r11,lr}
bx lr
m23_palette_prepare_fade_in:
push {r4-r11,lr}
bl m23_palette_snapshot
mov r0,#16
strh r0,[r4,#0xd4]
mov r1,#0x05000000
mov r2,#128
mov r0,#0
m23_palette_black_bg:
strh r0,[r1],#2
subs r2,r2,#1
bne m23_palette_black_bg
add r1,r1,#0x100
mov r2,#128
m23_palette_black_obj:
strh r0,[r1],#2
subs r2,r2,#1
bne m23_palette_black_obj
bl m23_palette_zero_aliases
pop {r4-r11,lr}
bx lr

m23_palette_fade_out:
push {r4-r11,lr}
ldrh r6,[r4,#0xd4]
and r7,r6,#1
mov r1,#0x05000000
add r1,r1,r7,lsl #9
mov r2,#128
m23_palette_down_color:
ldrh r3,[r1]
cmp r7,#0
beq m23_palette_down_loaded
tst r1,#31
subeq r0,r1,#0x100
ldrheq r3,[r0]
m23_palette_down_loaded:
mov r8,#0
"""]
    for shift in (0, 5, 10):
        out.append(f"mov r0,r3,lsr #{shift}\nand r0,r0,#31\ncmp r0,#3\nmovls r0,#0\nsubhi r0,r0,#2\norr r8,r8,r0,lsl #{shift}\n")
    out.append("""
strh r8,[r1],#2
subs r2,r2,#1
bne m23_palette_down_color
cmp r7,#0
beq m23_palette_down_no_alias
bl m23_palette_zero_aliases
m23_palette_down_no_alias:
add r6,r6,#1
strh r6,[r4,#0xd4]
mov r6,r6,lsl #16
mov r6,r6,lsr #16
cmp r6,#32
moveq r0,#1
movne r0,#0
pop {r4-r11,lr}
bx lr

m23_palette_fade_in:
push {r4-r11,lr}
mov r7,#0
m23_palette_up_half:
mov r1,#0x05000000
ldr r9,m23_palette_mirror
add r1,r1,r7,lsl #9
add r9,r9,r7,lsl #9
mov r2,#128
m23_palette_up_color:
ldrh r3,[r1]
ldrh r6,[r9],#2
mov r8,#0
""")
    for shift in (0, 5, 10):
        out.append(f"""
mov r0,r3,lsr #{shift}
and r0,r0,#31
mov r10,r6,lsr #{shift}
and r10,r10,#31
cmp r0,r10
beq m23_palette_channel_{shift}
cmp r0,#0
moveq r0,#3
addne r0,r0,#2
cmp r0,r10
movhi r0,r10
m23_palette_channel_{shift}:
orr r8,r8,r0,lsl #{shift}
""")
    out.append("""
strh r8,[r1],#2
subs r2,r2,#1
bne m23_palette_up_color
add r7,r7,#1
cmp r7,#2
bne m23_palette_up_half
bl m23_palette_zero_aliases
ldrh r0,[r4,#0xd4]
sub r0,r0,#1
strh r0,[r4,#0xd4]
mov r0,r0,lsl #16
cmp r0,#0
moveq r0,#1
movne r0,#0
pop {r4-r11,lr}
bx lr
m23_palette_zero_aliases:
push {r0-r3,lr}
mov r1,#0x05000000
add r2,r1,#0x100
add r1,r1,#0x200
mov r3,#8
m23_palette_zero_loop:
ldrh r0,[r1],#0x20
strh r0,[r2],#0x20
subs r3,r3,#1
bne m23_palette_zero_loop
pop {r0-r3,lr}
bx lr
m23_palette_mirror: .word 0x0203e000
""")
    return "\n".join(out)

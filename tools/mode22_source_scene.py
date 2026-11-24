"""Source mode22 pure state primitives, to be linked with a real viewer/storage layer.

No registered entry or fake storage adapter is exported. Snapshot bytes are
logical source BE..E7 (42 bytes), independent of native checksum/live RAM.
"""
import hashlib,struct
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SNAPSHOT_BYTES=42
NAME_OFFSET=0x0E
COUNTER_OFFSET=0x12
CALLBACKS=(0x401,0x4BF,0x5B9,0x647,0x677)
EXPORTS=('m22_snapshot_classify','m22_source_highest','m22_source_carry','m22_source_score_rank','m22_source_score_award')

def assembly(source):
 assert hashlib.sha256(source).hexdigest().upper()==SOURCE
 assert source[0x7850EA:0x78510E]==bytes.fromhex('515306bb000c8ec3bbfc3983c314b90b00268b070bc0750583eb02e2f48bc148075b59cb')
 thresholds=struct.unpack_from('<44H',source,0x785092)
 assert thresholds[:11]==(249,299,349,449,549,599,649,699,799,998,65535)
 return '''
@ R0=42-byte snapshot, R1=storage status. Return branch flag:
@ 1 empty, 2 ordinary, 4 special, 8 device error, 16 invalid integrity/version.
@ Status2 is the only path that materializes legacy zero defaults.
m22_snapshot_classify:
push {r1-r12,lr}
cmp r1,#1
moveq r0,#8
beq m22_classify_return
cmp r1,#3
movhs r0,#16
bhs m22_classify_return
cmp r1,#2
bne m22_classify_read
mov r2,#0
mov r3,#21
mov r4,r0
m22_classify_zero:
strh r2,[r4]
add r4,r4,#2
subs r3,r3,#1
bne m22_classify_zero
m22_classify_read:
bl m22_source_highest
cmp r0,#10
moveq r0,#4
beq m22_classify_return
cmn r0,#1
moveq r0,#1
movne r0,#2
m22_classify_return:
pop {r1-r12,pc}

@ Source848F:07FA. R0=snapshot; return -1,0..10; all other regs retained.
m22_source_highest:
push {r1-r12,lr}
add r2,r0,#0x26
mov r0,#10
m22_highest_loop:
ldrh r1,[r2]
cmp r1,#0
bne m22_highest_done
sub r2,r2,#2
subs r0,r0,#1
bpl m22_highest_loop
m22_highest_done:
pop {r1-r12,pc}

@ Source848F:08C0. R0=snapshot, R1=rank0..10. Return1 changed/0 refused.
@ 16-bit increment wrap and source compare/store ordering are retained.
m22_source_carry:
push {r1-r12,lr}
ldrh r2,[r0,#0x26]
cmp r2,#0
bne m22_carry_refuse
add r3,r0,#0x12
add r3,r3,r1,lsl #1
mov r4,r3
mov r5,r1
m22_carry_scan:
ldrh r2,[r3]
cmp r2,#9
blo m22_carry_begin
add r3,r3,#2
add r5,r5,#1
cmp r5,#11
blo m22_carry_scan
m22_carry_refuse:
mov r0,#0
pop {r1-r12,pc}
m22_carry_begin:
mov r3,r4
mov r5,r1
m22_carry_increment:
ldrh r2,[r3]
add r2,r2,#1
mov r2,r2,lsl #16
mov r2,r2,lsr #16
strh r2,[r3]
cmp r2,#10
blo m22_carry_success
mov r2,#9
strh r2,[r3]
add r5,r5,#1
cmp r5,#11
bhs m22_carry_success
mov r2,#0
strh r2,[r3]
add r3,r3,#2
b m22_carry_increment
m22_carry_success:
mov r0,#1
pop {r1-r12,pc}

@ Source848F:0728 threshold loop. R0=difficulty0..3, R1=unsigned16 score.
m22_source_score_rank:
push {r1-r12,lr}
add r2,r0,r0,lsl #1
add r2,r2,r0,lsl #3
adr r3,m22_rank_thresholds
add r3,r3,r2,lsl #1
mov r0,#0
m22_rank_loop:
ldrh r2,[r3]
cmp r1,r2
bls m22_rank_done
add r3,r3,#2
add r0,r0,#1
b m22_rank_loop
m22_rank_done:
pop {r1-r12,pc}

@ Pure source0728 result: R0=snapshot,R1=difficulty,R2=score.
@ Return source config+23 result (8000|rank or FFFF). No save/device call.
m22_source_score_award:
push {r1-r12,lr}
mov r4,r0
mov r0,r1
mov r1,r2
bl m22_source_score_rank
mov r5,r0
mov r1,r0
mov r0,r4
bl m22_source_carry
cmp r0,#0
mvneq r0,#0
moveq r0,r0,lsr #16
orrne r0,r5,#0x8000
pop {r1-r12,pc}
.align 2
m22_rank_thresholds:
.hword '''+','.join(map(str,thresholds))+'\n'

"""Typed title tree helpers from source780CBE/780DB8 and final780AFC.

These helpers are not a visible menu/controller by themselves. Source unlock
and the temporary missing-mode22 implementation guard remain distinct.
Native task payload: 0/2 native timers;4 tree,5 row,6 count,8 transition,
A back selector;10/14 navigation pointers,18 coordinates,1C cached unlock.
The five existing title presentations remain at03002A78, stride50.
"""
import hashlib,struct
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SBASE=0x77FFB0

def contract(source):
 assert hashlib.sha256(source).hexdigest().upper()==SOURCE
 rows=[]
 for tree,count in enumerate((6,3,3,1,2)):
  off=struct.unpack_from('<H',source,SBASE+0x9A7+2*tree)[0]
  rows.append([struct.unpack_from('<4H',source,SBASE+off+8*i)for i in range(count)])
 assert rows==[[(65535,0,0,0),(65535,0,0,0),(1,6,2,0xA51),(65535,2,0,0),(65535,0,0,0),(2,8,2,0xA61)],[(0,1,5,0xA29),(65535,0,0,0),(65535,0,0,0)],[(0,1,5,0xA29),(65535,1,0,0),(65535,0,0,0)],[(2,8,2,0xA61)],[(65535,0,0,0),(0,1,5,0xA29)]]
 nav=[]
 for tree,count in enumerate((5,2,2)):
  up,down=struct.unpack_from('<2H',source,SBASE+0x929+tree*8)
  nav.append((source[SBASE+up:SBASE+up+count],source[SBASE+down:SBASE+down+count]))
 coords={off:source[SBASE+off:SBASE+off+4*count]for off,count in ((0xA29,5),(0xA51,2),(0xA61,2))}
 flags=[]
 for tree,count in enumerate((5,2,2)):
  columns=[]
  for table in (0x96B,0x97F,0x993):
   ptr=struct.unpack_from('<H',source,SBASE+table+tree*2)[0]
   columns.append(source[SBASE+ptr:SBASE+ptr+count])
  flags.append(list(zip(*columns)))
 assert flags[2][1][0]==8 and flags[2][0][0]==0
 return rows,nav,coords,flags

def assembly(source):
 rows,nav,coords,flags=contract(source)
 out=['''
m23_title_tree_init:
push {r4-r11,lr}
mov r4,r0
mov r1,#0
mov r2,#8
m23_title_init_clear:
str r1,[r0],#4
subs r2,r2,#1
bne m23_title_init_clear
mov r0,#4
strb r0,[r4,#4]
mov r0,#1
strb r0,[r4,#6]
bl m23_eligibility_read
str r0,[r4,#0x1c]
pop {r4-r11,lr}
bx lr

m23_title_handler22_available:
ldr r1,m23_title_ctor_slot
ldr r1,[r1]
ldr r0,[r1,#264]
cmp r0,#0
movne r0,#1
bx lr
m23_title_ctor_slot: .word 0x08015b74

m23_title_tree_action:
push {r4-r11,lr}
mov r4,r0
mov r5,r1
mov r0,#0
strb r0,[r4,#0xa]
tst r5,#0x40
beq m23_title_action_back
ldrb r6,[r4,#5]
ldr r7,m23_title_presentations
add r7,r7,r6,lsl #6
add r7,r7,r6,lsl #4
ldrh r7,[r7,#0xe]
cmp r7,#10
beq m23_title_action_reject
mov r0,#0x79
bl m23_title_sound
add r6,r6,#1
bl m23_title_selected_row
ldrh r1,[r7]
ldr r2,=0xffff
cmp r1,r2
mov r0,#1
bne m23_title_action_return
ldrh r1,[r7,#2]
strh r1,[r4,#8]
mov r0,#2
b m23_title_action_return
m23_title_action_back:
tst r5,#0x80
moveq r0,#0
beq m23_title_action_return
mov r0,#0x7a
bl m23_title_sound
mov r0,#1
strb r0,[r4,#0xa]
mov r6,#0
bl m23_title_selected_row
ldrh r1,[r7]
ldr r2,=0xffff
cmp r1,r2
mov r0,#1
moveq r0,#3
b m23_title_action_return
m23_title_action_reject:
mov r0,#0x7a
bl m23_title_sound
mov r0,#0
m23_title_action_return:
pop {r4-r11,lr}
bx lr
m23_title_selected_row:
ldrb r7,[r4,#4]
adr r8,m23_title_tree_pointers
ldr r7,[r8,r7,lsl #2]
add r7,r7,r6,lsl #3
bx lr

m23_title_tree_apply:
push {r4-r11,lr}
mov r4,r0
ldrb r6,[r4,#5]
add r6,r6,#1
ldrb r0,[r4,#0xa]
cmp r0,#0
movne r6,#0
bl m23_title_selected_row
ldrh r6,[r7]
strb r6,[r4,#4]
mov r0,#0
strb r0,[r4,#5]
adr r1,m23_title_navigation
add r1,r1,r6,lsl #3
ldr r0,[r1]
str r0,[r4,#0x10]
ldr r0,[r1,#4]
str r0,[r4,#0x14]
ldrh r8,[r7,#2]
ldrh r9,[r7,#4]
strb r9,[r4,#6]
ldrh r10,[r7,#6]
adr r1,m23_title_coordinates
ldr r0,=0xa29
cmp r10,r0
moveq r10,r1
addne r10,r1,#20
ldr r0,=0xa61
ldrh r2,[r7,#6]
cmp r2,r0
addeq r10,r1,#28
str r10,[r4,#0x18]
ldr r7,m23_title_presentations
m23_title_apply_loop:
mov r0,r7
mov r1,r8
bl m23_title_event
ldrh r0,[r10],#2
strh r0,[r7]
ldrh r0,[r10],#2
strh r0,[r7,#2]
add r7,r7,#0x50
add r8,r8,#1
subs r9,r9,#1
bne m23_title_apply_loop
cmp r6,#2
bne m23_title_apply_return
bl m23_title_handler22_available
cmp r0,#0
bne m23_title_source_unlock
ldr r0,m23_title_presentations
mov r1,#10
bl m23_title_event
m23_title_source_unlock:
ldr r0,[r4,#0x1c]
cmp r0,#0
bne m23_title_apply_return
ldr r0,m23_title_presentations
add r0,r0,#0x50
mov r1,#10
bl m23_title_event
m23_title_apply_return:
pop {r4-r11,lr}
bx lr

m23_title_tree_move:
push {r4-r11,lr}
mov r4,r0
tst r1,#1
ldrne r2,[r4,#0x10]
bne m23_title_move_go
tst r1,#4
ldrbeq r0,[r4,#5]
beq m23_title_move_return
ldr r2,[r4,#0x14]
m23_title_move_go:
ldrb r0,[r4,#5]
ldrb r0,[r2,r0]
strb r0,[r4,#5]
mov r0,#0x78
bl m23_title_sound
ldrb r0,[r4,#5]
m23_title_move_return:
pop {r4-r11,lr}
bx lr

m23_title_exit_config:
push {r4-r11,lr}
mov r4,r0
ldrb r1,[r4,#4]
adr r2,m23_title_flags_pointers
ldr r2,[r2,r1,lsl #2]
ldrb r1,[r4,#5]
add r1,r1,r1,lsl #1
add r2,r2,r1
ldr r3,m23_title_config
ldrh r0,[r3,#0x1a]
ldrb r1,[r2]
orr r0,r0,r1
strh r0,[r3,#0x1a]
ldrb r0,[r2,#1]
strb r0,[r3,#0x25]
ldrb r0,[r2,#2]
strh r0,[r3,#2]
mov r0,#1
strh r0,[r3,#4]
ldrh r0,[r4,#8]
strh r0,[r3,#6]
mov r0,#0
strh r0,[r3,#8]
pop {r4-r11,lr}
bx lr
m23_title_config: .word 0x03002310
m23_title_presentations: .word 0x03002a78
.ltorg
m23_title_tree_pointers:
.word m23_title_tree_0,m23_title_tree_1,m23_title_tree_2,m23_title_tree_3,m23_title_tree_4
''']
 for tree,values in enumerate(rows):
  out.append(f'm23_title_tree_{tree}:\n.hword '+','.join(str(x)for row in values for x in row)+'\n')
 out.append('.align 2\nm23_title_navigation:\n'+''.join(f'.word m23_title_up_{i},m23_title_down_{i}\n'for i in range(3)))
 for tree,(up,down)in enumerate(nav):
  out.append(f'm23_title_up_{tree}:\n.byte '+','.join(map(str,up))+'\n'+f'm23_title_down_{tree}:\n.byte '+','.join(map(str,down))+'\n')
 out.append('.align 2\nm23_title_coordinates:\n.byte '+','.join(map(str,b''.join(coords.values())))+'\n.align 2\nm23_title_flags_pointers:\n.word m23_title_flags_0,m23_title_flags_1,m23_title_flags_2\n')
 for tree,values in enumerate(flags):out.append(f'm23_title_flags_{tree}:\n.byte '+','.join(str(x)for row in values for x in row)+'\n')
 out.append('.align 2\n')
 return '\n'.join(out)

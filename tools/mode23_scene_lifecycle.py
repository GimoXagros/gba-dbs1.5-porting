"""Mode23 scene phase bodies; graphics/fade/save services must be real imports.

No mode table or visible menu is modified. This source module deliberately
cannot produce a ROM by itself: linking requires every listed dependency.
"""
import hashlib

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ENTRIES = (0xA56B, 0xA59F, 0xA7CF, 0xA895, 0xA8EA, 0xA945, 0xA973,
           0xA99C, 0xAA70, 0xAAF9, 0xAB4F, 0xABBF, 0xAC43, 0xAC67,
           0xAD53, 0xADCF, 0xADF7, 0xAE71, 0xAFCE, 0xB045, 0xB059,
           0xB188, 0xC999, 0xC9B3, 0xC9B9)
DEPENDENCIES = (
    "m23_callback", "m23_actor", "m23_spawn", "m23_release", "m23_selected",
    "m23_sound", "m23_audio_reset", "m23_audio_service",
    "m23_display_low", "m23_display_zero", "m23_display_enable", "m23_retire_vcount", "m23_window_left", "m23_window_top",
    "m23_window_right", "m23_window_bottom", "m23_scroll2_step", "m23_scroll2_zero",
    "m23_obj_color0", "m23_framecounter", "m23_pressed", "m23_sin",
    "m23_present_event", "m23_present_update", "m23_present_draw",
    "m23_present_update_draw", "m23_intro_prepare", "m23_intro_actors",
    "m23_round_prepare", "m23_round_message_resources", "m23_participants_create",
    "m23_palette_snapshot", "m23_palette_fade_out", "m23_palette_fade_in",
    "m23_failure_prepare", "m23_completion_prepare", "m23_completion_save",
    "m23_request_exit", "m23_cb_B1E5", "m23_cb_BC1C",
)


def assembly(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("mode23 lifecycle source mismatch")
    def cb(addr, pointer="r5"):
        return f"mov r0,{pointer}\nldr r1,m23_life_ptr_{addr:04X}\nbl m23_callback\n"
    def timer(value):
        return f"ldr r0,={value}\nstrh r0,[r4,#0x30]\n"
    def dec(label):
        return "ldrh r0,[r4,#0x30]\nsub r0,r0,#1\nstrh r0,[r4,#0x30]\nmov r0,r0,lsl #16\ncmp r0,#0\n" + f"bne {label}\n"
    def entry(addr, body):
        return f"m23_src_{addr:04X}:\npush {{r6-r11,lr}}\n{body}\nm23_life_done_{addr:04X}:\npop {{r6-r11,lr}}\nbx lr\n"
    out = ["""
m23_scene_create:
push {r4-r11,lr}
bl m23_display_zero
bl m23_retire_vcount
bl m23_audio_reset
mov r0,#4
mov r1,#4
bl m23_sound
bl m23_audio_service
ldr r0,=0xf100
ldr r1,m23_life_ptr_C999
mov r2,#0
bl m23_spawn
mov r6,r0
mov r0,#0x1000
ldr r1,m23_life_ptr_A56B
mov r2,#0
bl m23_spawn
mov r7,r0
add r4,r7,#0x18
str r7,[r4]
str r6,[r4,#4]
str r4,[r4,#0xfc]
str r4,[r6,#0x114]
mov r0,#0x1800
ldr r1,m23_life_ptr_BC1C
mov r2,r4
bl m23_spawn
str r0,[r4,#8]
bl m23_selected
strb r0,[r4,#0x2d]
mov r0,#0
bl m23_obj_color0
bl m23_display_enable
mov r0,r7
pop {r4-r11,lr}
bx lr

m23_src_A50D:
push {r4-r11,lr}
ldrh r0,[r4,#0x24]
bic r0,r0,#4
strh r0,[r4,#0x24]
ldr r0,[r4,#8]
add r0,r0,#0x18
ldr r1,m23_life_ptr_BC1C
bl m23_callback
mov r6,#0
ldrb r7,[r4,#0x2b]
cmp r7,#0
beq m23_life_retire_return
m23_life_retire_participants:
add r0,r4,r6,lsl #2
ldr r0,[r0,#0xc]
bl m23_release
add r6,r6,#1
cmp r6,r7
bne m23_life_retire_participants
m23_life_retire_return:
pop {r4-r11,lr}
bx lr

m23_src_A0FD:
push {r4-r11,lr}
bl m23_audio_reset
mov r0,#4
mov r1,#4
bl m23_sound
bl m23_audio_service
ldr r6,[r4]
ldr r7,[r4,#4]
ldr r8,[r4,#8]
mov r0,r6
bl m23_release
mov r0,r7
bl m23_release
mov r0,r8
bl m23_release
bl m23_request_exit
pop {r4-r11,lr}
bx lr
"""]
    out.append(entry(0xA56B, cb(0xA59F)))
    out.append(entry(0xA59F, """
bl m23_intro_prepare
bl m23_participants_create
bl m23_intro_actors
mov r0,#0x7c
mov r1,#1
bl m23_sound
mov r0,#0x24
bl m23_display_low
""" + timer(100) + cb(0xA7CF)))
    out.append(entry(0xA7CF, """
mov r6,#0
m23_life_intro_movement:
mov r0,r6
bl m23_actor
ldrh r1,[r0,#4]
ldrsh r2,[r0,#0xc]
add r1,r1,r2
strh r1,[r0,#4]
mov r3,#0xe8
mul r1,r2,r3
mov r1,r1,asr #8
strh r1,[r0,#0xc]
add r6,r6,#1
ldrb r0,[r4,#0x2b]
cmp r6,r0
bne m23_life_intro_movement
""" + dec("m23_life_done_A7CF") + timer(8) + """
mov r0,#0
bl m23_display_low
mvn r0,#0
bl m23_obj_color0
mov r0,#0x7d
mov r1,#1
bl m23_sound
""" + cb(0xA895)))
    out.append(entry(0xA895, dec("m23_life_done_A895") + timer(150) + """
mov r0,#0
bl m23_obj_color0
mov r0,#0x26
bl m23_display_low
mov r0,#0
bl m23_window_left
mov r0,#0xe0
bl m23_window_right
mov r0,#0x2a
bl m23_window_top
mov r0,#0x66
bl m23_window_bottom
""" + cb(0xA8EA)))
    out.append(entry(0xA8EA, """
add r0,r4,#0x34
bl m23_present_update_draw
bl m23_framecounter
tst r0,#1
beq m23_life_scroll_unchanged
bl m23_scroll2_step
m23_life_scroll_unchanged:
""" + dec("m23_life_done_A8EA") + "bl m23_palette_snapshot\n" + cb(0xA945)))
    out.append(entry(0xA945, "bl m23_palette_fade_out\ncmp r0,#0\nbeq m23_life_done_A945\n" + cb(0xA973)))
    out.append(entry(0xA973, "bl m23_scroll2_zero\nbl m23_src_A50D\nmov r0,#0x20\nbl m23_display_low\n" + cb(0xA99C)))
    out.append(entry(0xA99C, "bl m23_round_prepare\n" + cb(0xAA70)))
    out.append(entry(0xAA70, """
bl m23_palette_fade_in
cmp r0,#0
beq m23_life_done_AA70
mov r0,#0x6c
mov r1,#4
bl m23_sound
""" + cb(0xAAF9)))
    out.append(entry(0xAAF9, """
add r0,r4,#0x34
bl m23_present_update_draw
ldrh r0,[r4,#0x3e]
tst r0,#0x2000
beq m23_life_done_AAF9
add r0,r4,#0x34
mov r1,#1
bl m23_present_event
""" + cb(0xAB4F)))
    out.append(entry(0xAB4F, """
add r0,r4,#0x34
bl m23_present_update_draw
ldrh r0,[r4,#0x3e]
tst r0,#0x2000
beq m23_life_done_AB4F
""" + timer(30) + """
mov r0,#0
strh r0,[r4,#0x26]
strh r0,[r4,#0x28]
strb r0,[r4,#0x2f]
mov r0,#255
strb r0,[r4,#0x2e]
bl m23_participants_create
""" + cb(0xABBF)))
    out.append(entry(0xABBF, dec("m23_life_done_ABBF") + """
mov r0,#0xf0
mov r1,#4
bl m23_sound
ldrb r0,[r4,#0x2a]
cmp r0,#6
bne m23_life_music_ready
mov r0,#0xf4
mov r1,#4
bl m23_sound
m23_life_music_ready:
""" + cb(0xAC43)))
    out.append(entry(0xAC43, cb(0xB1E5)))
    out.append(entry(0xAC67, timer(0x20d) + """
ldrh r0,[r4,#0x24]
bic r0,r0,#4
strh r0,[r4,#0x24]
ldr r0,[r4,#8]
add r0,r0,#0x18
ldr r1,m23_life_ptr_BC1C
bl m23_callback
mov r0,#0
bl m23_actor
ldrh r0,[r0]
tst r0,#1
mov r6,#0
beq m23_life_message_setup
mov r6,#4
ldrh r0,[r4,#0x24]
orr r0,r0,#2
strh r0,[r4,#0x24]
""" + timer(300) + """
m23_life_message_setup:
add r0,r4,#0x34
mov r1,r6
bl m23_round_message_resources
mov r0,#112
strh r0,[r4,#0x34]
mov r0,#72
strh r0,[r4,#0x36]
""" + cb(0xAD53) + "bl m23_src_AD53\n"))
    out.append(entry(0xAD53, """
add r0,r4,#0x34
bl m23_present_update_draw
bl m23_pressed
tst r0,#0x60
bne m23_life_message_finished
""" + dec("m23_life_done_AD53") + """
m23_life_message_finished:
mov r0,#4
mov r1,#4
bl m23_sound
bl m23_palette_snapshot
""" + cb(0xADCF)))
    out.append(entry(0xADCF, "bl m23_palette_fade_out\ncmp r0,#0\nbeq m23_life_done_ADCF\n" + cb(0xADF7)))
    out.append(entry(0xADF7, """
bl m23_src_A50D
ldrh r0,[r4,#0x24]
tst r0,#2
beq m23_life_next_round
""" + cb(0xAE71) + """
b m23_life_done_ADF7
m23_life_next_round:
ldrb r0,[r4,#0x2a]
add r0,r0,#1
strb r0,[r4,#0x2a]
mov r0,r0,lsl #24
mov r0,r0,asr #24
cmp r0,#7
blt m23_life_round_repeat
""" + cb(0xB059) + """
b m23_life_done_ADF7
m23_life_round_repeat:
""" + cb(0xA56B)))
    out.append(entry(0xAE71, "bl m23_failure_prepare\n" + timer(450) + cb(0xAFCE)))
    out.append(entry(0xAFCE, """
ldrh r0,[r4,#0x34]
add r0,r0,#1
mov r0,r0,lsl #16
mov r0,r0,asr #16
cmp r0,#0xf0
movgt r0,#0xf0
cmp r0,#-0xf0
movlt r0,#0xf0
rsblt r0,r0,#0
strh r0,[r4,#0x34]
cmp r0,#0
ble m23_life_failure_window_unchanged
bl m23_window_right
m23_life_failure_window_unchanged:
bl m23_framecounter
tst r0,#1
beq m23_life_failure_draw
add r0,r4,#0x34
bl m23_present_update
m23_life_failure_draw:
add r0,r4,#0x34
bl m23_present_draw
""" + dec("m23_life_done_AFCE") + cb(0xB045)))
    out.append(entry(0xB045, "mov r0,#0xe0\nbl m23_window_right\nbl m23_src_A0FD"))
    out.append(entry(0xB059, """
bl m23_completion_save
mov r0,#0x30
mov r1,#4
bl m23_sound
bl m23_completion_prepare
""" + timer(405) + cb(0xB188)))
    out.append(entry(0xB188, """
ldrh r0,[r4,#0x30]
bl m23_sin
mov r0,r0,asr #4
add r0,r0,#100
strh r0,[r4,#0x36]
mov r0,#112
strh r0,[r4,#0x34]
ldrh r0,[r4,#0x3c]
orr r0,r0,#0x2000
strh r0,[r4,#0x3c]
add r0,r4,#0x34
bl m23_present_update_draw
""" + dec("m23_life_done_B188") + "bl m23_src_A0FD"))
    out.append(entry(0xC999, cb(0xC9B3)))
    out.append(entry(0xC9B3, "bl m23_src_C9B9"))
    # Source private flag bit1 is initialized clear and no legal source/native
    # writer sets it (only BIC4/OR2/OR4). The source4F84 fade branch is
    # unreachable on this owned scene domain; no noop fade import is installed.
    out.append(entry(0xC9B9, """
bl m23_audio_service
"""))
    for addr in sorted(set(ENTRIES) | {0xB1E5, 0xBC1C}):
        out.append(f"m23_life_ptr_{addr:04X}: .word m23_cb_{addr:04X}\n")
    # The module is comfortably below one ARM LDR literal reach. Other modules
    # must be linked after this local pool, not between its users and literals.
    out.append(".ltorg\n")
    return "\n".join(out)

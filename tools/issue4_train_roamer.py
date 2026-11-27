"""Restore the Train's item Digimon dispatcher and its source-specific flight."""
import hashlib
import struct

from build_mode24_link_cards import branch
from mode23_linker import compose

BASE = 0x08000000
START = 0xDE8A00
END = 0xDE987C
ENTRY = 0x35C21C


def apply(rom: bytearray, source: bytes) -> None:
    # The Train shares the native stage-2 monster graphics, but owns its own scheduler,
    # directions and motion. All eight original GBA stages keep the native dispatcher.
    assert source[0x740880:0x7408A0] == source[0x7407C0:0x7407E0]
    for data, start, length, digest in (
        (source, 0x763AF6, 0x6E, "256a2458011d04df5d57ab581798129a19b465d32c014284ca9cc8eb25ea659c"),
        (source, 0x76424C, 0xEA, "37deac476ca6b54bd68b7c45204641cca34bfdf5bfea2489c55be690d2e548d0"),
        (source, 0x7654A0, 0x198, "840d752a19ad140183273523a6e92b22aeb6d4bba48708413470958eb1f921c4"),
        (rom, ENTRY, 0x128, "439daf0d5e10b3300538fb9380557fe6538017df3648bdb2fca17570c3480e3c"),
        (rom, 0x35D820, 0x1C4, "0283661597f1d7be26d2cc7e7062e913376d5d92b0ae0e5aa10dedadd0fe3b4f"),
        (rom, 0x3686AC, 24, "780eefcdf33c842a9cd54bf0f2d6a65b0cc99ba19f2867070960c7c474af0592"),
    ):
        assert hashlib.sha256(data[start:start + length]).hexdigest() == digest
    assert source[0x7519C9:0x751BC9] == rom[0x12360:0x12560]
    assert struct.unpack_from("<4H", source, 0x765634) == (0x1D00, 0x400, 0x980, 0x980)
    directions = struct.unpack_from("<16H", source, 0x764336)[::2]
    assert set(directions) == {0, 1}
    assert struct.unpack_from("<16H", source, 0x764BC6)[::2] == (75,) * 8
    direction_bytes = ",".join(map(str, directions))

    # Only the real Train selects the new handler. The native stage-2 constructor
    # allocates the correct neutral actor and initializes its palette, hit points and drops.
    # Train then supplies the two entrance positions and the sine-driven flight between them.
    assert struct.unpack_from("<I", rom, 0x3524B0)[0] == 0x03004826
    code, entries, _ = compose([f"""
entry:
    push {{r0,r1,lr}}
    ldr r8,stage
    ldrh r8,[r8]
    cmp r8,#8
    bne 0x0835c220
    ldr r8,game_stage
    ldrb r8,[r8]
    cmp r8,#8
    bne 0x0835c220
    ldrb r8,[sp,#12]
    tst r8,#0xf7
    bne 0x0835c220
    mov r0,#2
    push {{r0}}
    bl native_field
    add sp,sp,#4
    ldr r0,field_callbacks
    adr r1,create
    str r1,[r0]
    adr r1,tick
    str r1,[r0,#4]
    pop {{r0,r1,lr}}
    bx lr
native_field:
    push {{r0,r1,lr}}
    b 0x0835c220
tick:
    push {{r1,lr}}
    ldr r1,active
    ldrh r0,[r1]
    cmp r0,#0
    bne inactive
    ldr r8,pool_flags
    ldrb r0,[r8]
    cmp r0,#255
    ldrbne r0,[r8,#1]
    cmpne r0,#255
    bne inactive
    ldr r8,countdown
    ldrsh r0,[r8]
    cmp r0,#0
    bgt count
    ldr r8,rng
    ldrh r0,[r8,#0x12]
    and r0,r0,#127
    add r0,r0,#75
    lsl r0,r0,#2
    add r0,r0,#2
    mov r1,#5
    bl 0x0837db3c
count:
    sub r0,r0,#1
    ldr r8,countdown
    strh r0,[r8]
    cmp r0,#0
    bgt inactive
    ldr r8,active
    mov r0,#1
    strh r0,[r8]
    pop {{r1,lr}}
    bx lr
inactive:
    mov r0,#0
    pop {{r1,lr}}
    bx lr
create:
    push {{r1,r2,lr}}
    ldr r8,pattern_index
    ldr r2,[r8]
    push {{r2}}
    bl 0x0835d820
    pop {{r2}}
    add r0,r2,#1
    and r0,r0,#3
    ldr r8,pattern_index
    str r0,[r8]
    ldr r8,seed
    ldrh r0,[r8]
    and r0,r0,#1
    add r2,r2,r0,lsl #2
    adr r0,directions
    ldrb r0,[r0,r2]
    strh r0,[r4,#0xa0]
    adr r0,init
    str r0,[r4]
    pop {{r1,r2,lr}}
    bx lr
init:
    push {{lr}}
    mov r0,#0
    strh r0,[r4,#0x42]
    strh r0,[r4,#0x44]
    strh r0,[r4,#0x46]
    strh r0,[r4,#0x48]
    ldrh r0,[r4,#0xa0]
    cmp r0,#0
    bne left_effect
    bl animation_zero
    ldrh r0,[r5,#8]
    bic r0,r0,#0x4000
    strh r0,[r5,#8]
    ldrh r0,[r4,#4]
    bic r0,r0,#0x4000
    strh r0,[r4,#4]
    mov r0,#0x1d00
    mov r1,#0x980
    bl position
    mov r0,#0
    strh r0,[r4,#0x94]
    mvn r0,#249
    strh r0,[r4,#0x42]
    b install_flight
left_effect:
    mov r0,#0x400
    mov r1,#0x960
    bl effect
    bl animation_zero
    ldrh r0,[r5,#8]
    orr r0,r0,#0x4000
    strh r0,[r5,#8]
    mov r0,#64
    strh r0,[r4,#0x94]
    adr r0,wait_left
    str r0,[r4]
    pop {{lr}}
    bx lr
wait_left:
    ldrh r0,[r4,#0x94]
    subs r0,r0,#1
    strh r0,[r4,#0x94]
    bxne lr
    push {{lr}}
    mov r0,#0x400
    mov r1,#0x980
    bl position
    mov r0,#768
    strh r0,[r4,#0x94]
    mov r0,#250
    strh r0,[r4,#0x42]
    mov r8,#0x48
    mov r9,#1
    mov r10,#0
    bl 0x080d15c0
install_flight:
    adr r0,flight
    str r0,[r4]
    pop {{lr}}
    bx lr
flight:
    push {{lr}}
    push {{r5}}
    push {{r11}}
    mov r8,#1
    push {{r8}}
    bl 0x08012a84
    add sp,sp,#12
    ldrh r0,[r4,#0x94]
    lsr r1,r0,#2
    add r0,r0,#5
    bic r0,r0,#0x400
    strh r0,[r4,#0x94]
    ldr r8,sine
    add r8,r8,r1,lsl #1
    ldrsh r0,[r8]
    asr r0,r0,#1
    add r0,r0,r0,asr #2
    strh r0,[r4,#0x44]
    ldrsh r0,[r4,#0x34]
    ldrh r1,[r4,#0xa0]
    cmp r1,#0
    bne going_right
    cmp r0,#0x1b80
    ldrhle r1,[r4,#4]
    orrle r1,r1,#0x4000
    strhle r1,[r4,#4]
    cmp r0,#0x400
    bgt alive
    ldrsh r1,[r4,#0x36]
    bl effect
    mov r0,#0x200
    rsb r0,r0,#0
    mov r1,r0
    bl position
    b release
going_right:
    cmp r0,#0x1b80
    ldrhge r1,[r4,#4]
    bicge r1,r1,#0x4000
    strhge r1,[r4,#4]
    cmp r0,#0x1d00
    blt alive
release:
    bl 0x083687d4
alive:
    pop {{lr}}
    bx lr
position:
    strh r0,[r4,#0x34]
    strh r0,[r4,#0x38]
    strh r1,[r4,#0x36]
    strh r1,[r4,#0x3a]
    bx lr
animation_zero:
    push {{lr}}
    push {{r5}}
    push {{r11}}
    mov r8,#0
    push {{r8}}
    bl 0x08012874
    add sp,sp,#12
    pop {{lr}}
    bx lr
effect:
    push {{lr}}
    push {{r4}}
    push {{r11}}
    push {{r0}}
    push {{r1}}
    ldr r8,effect_id
    push {{r8}}
    bl 0x0835972c
    add sp,sp,#20
    pop {{lr}}
    bx lr
stage: .word 0x03002656
game_stage: .word 0x0300231e
pool_flags: .word 0x03004826
field_callbacks: .word 0x03004cc8
active: .word 0x03004cc4
countdown: .word 0x03004ce0
pattern_index: .word 0x03004cd8
seed: .word 0x03004ce2
rng: .word 0x03002310
sine: .word 0x08012360
effect_id: .word 0x8007
directions: .byte {direction_bytes}
"""], BASE + START, ["entry"])
    assert START + len(code) <= END and rom[START:END] == b"\xff" * (END - START)
    rom[START:START + len(code)] = code
    rom[ENTRY:ENTRY + 4] = branch(BASE + ENTRY, entries["entry"])

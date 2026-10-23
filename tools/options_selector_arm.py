"""ARM7TDMI source for the bounded, development Options language component.

Each routine has a fixed allocation and a separate literal tail. No global RAM
is added: the native scheduler owns the 0x100-byte payload, of which 0xF8 is used.
"""
from __future__ import annotations

BASE = 0x08000000
SLOTS = {
    "get_language": (0x633400, 0x40), "palette_choice": (0x633440, 0x40),
    "constructor_choice": (0x633480, 0x40), "route_object": (0x6334C0, 0x80),
    "find_task": (0x633540, 0xC0), "confirm": (0x633600, 0x200),
    "input_guard": (0x633800, 0x200), "create_task": (0x633A00, 0x200),
    "init_object": (0x633C00, 0x100), "set_frame": (0x633D00, 0x80),
    "draw_object": (0x633D80, 0x80), "tick": (0x633E00, 0x400),
}


def source(p0, p1, p2, digicode_p0):
    a = {name: BASE + span[0] for name, span in SLOTS.items()}
    return {
        "get_language": (f"""
            ldr r0, record_tag
            ldrb r0, [r0]
            sub r0, r0, #0xA0
            cmp r0, #3
            movhi r0, #0
            bx lr
        record_tag: .word 0x0300112F
        """, 4),
        "palette_choice": (f"""
            push {{lr}}
            bl 0x{a['get_language']:08X}
            cmp r0, #0
            moveq r0, #1
            movne r0, #0
            pop {{lr}}
            bx lr
        """, 0),
        "constructor_choice": (f"""
            push {{lr}}
            bl 0x{a['get_language']:08X}
            cmp r0, #1
            moveq r0, #0
            movne r0, #1
            pop {{lr}}
            bx lr
        """, 0),
        # Entry stack belongs to native127E4. Preserve all incoming registers
        # and flags before replacing only its three resource arguments.
        "route_object": ("""
            push {r0, r1, r2}
            mrs r2, cpsr
            ldr r0, tag
            ldrb r0, [r0]
            cmp r0, #0xA2
            ldreq r1, korean_p0
            beq replace
            cmp r0, #0xA3
            bne unchanged
            ldr r1, digicode_p0
        replace:
            str r1, [sp, #0x30]
            ldr r1, korean_p1
            str r1, [sp, #0x3C]
            ldr r1, korean_p2
            str r1, [sp, #0x24]
        unchanged:
            msr cpsr_f, r2
            pop {r0, r1, r2}
            b 0x080127E4
        tag: .word 0x0300112F
        korean_p0: .word 0x08632000
        korean_p1: .word 0x080A02E8
        korean_p2: .word 0x080A05B8
        digicode_p0: .word DIGICODE_P0
        """.replace("DIGICODE_P0", f"0x{digicode_p0:08X}"), 20),
        # Native priority lookup returns a predecessor, so equality is checked.
        "find_task": ("""
            push {r1-r5, r8-r12, lr}
            ldr r1, priority
            push {r1}
            bl 0x08011F90
            add sp, sp, #4
            mov r0, #0
            cmp r3, #0
            beq finished
            cmn r3, #1
            beq finished
            ldr r1, priority
            ldr r2, [r3, #4]
            cmp r1, r2
            addeq r0, r3, #0x18
        finished:
            pop {r1-r5, r8-r12, lr}
            bx lr
        priority: .word 0x1500
        """, 4),
        # Replaces CMP r8,#4. The final flags are deliberately CMP r8,#5,
        # letting the existing input task own its native retirement callback.
        "confirm": (f"""
            cmp r8, #4
            bne compare_return
            push {{r0-r7, r9-r12, lr}}
            bl 0x{a['find_task']:08X}
            cmp r0, #0
            beq done
            mov r4, r0
            ldrh r1, [r4]
            cmp r1, #3
            bhi done
            ldr r5, record
            ldrb r6, [r5, #0xF]
            ldr r7, [r5, #0xC0]
            add r1, r1, #0xA0
            strb r1, [r5, #0xF]
            push {{r4-r7}}
            bl 0x0801FC5C
            pop {{r4-r7}}
            cmp r0, #0
            bne failure
            mov r1, #0
            strh r1, [r4, #4]
            mov r8, #5
            b done
        failure:
            strb r6, [r5, #0xF]
            str r7, [r5, #0xC0]
            mov r1, #1
            strh r1, [r4, #4]
            mov r8, #4
        done:
            pop {{r0-r7, r9-r12, lr}}
        compare_return:
            cmp r8, #5
            bx lr
        record: .word 0x03001120
        """, 4),
        # Runs in priority100 input task before every presentation consumer.
        # On failed native I/O, lock row4 to A retry / B old-record repair.
        # Removing B from both r0 and the shared button halfword is essential.
        "input_guard": (f"""
            push {{r1-r12, lr}}
            mov r6, r0
            bl 0x{a['find_task']:08X}
            cmp r0, #0
            beq done
            mov r4, r0
            ldrh r1, [r4, #4]
            cmp r1, #0
            beq done
            and r6, r6, #0xC0
            tst r6, #0x80
            beq filtered
            ldr r5, record
            ldr r7, [r5, #0xC0]
            push {{r4-r7}}
            bl 0x0801FC5C
            pop {{r4-r7}}
            cmp r0, #0
            bne repair_failed
            mov r1, #0
            strh r1, [r4, #4]
            b filtered
        repair_failed:
            str r7, [r5, #0xC0]
            mov r6, #0
        filtered:
            ldr r1, options
            strh r6, [r1, #2]
        done:
            mov r0, r6
            pop {{r1-r12, lr}}
            tst r0, #0x80
            bx lr
        options: .word 0x03004738
        record: .word 0x03001120
        """, 8),
        # New priority1500 task: pending+0, entry-language+2, I/O-error+4,
        # padding+6, label+8, value+58, arrows+A8. EndF8 <= native100.
        "create_task": (f"""
            push {{r0-r7, r9-r12, lr}}
            ldr r0, callback
            push {{r0}}
            mov r0, #0
            push {{r0}}
            ldr r0, priority
            push {{r0}}
            bl 0x08011AC4
            add sp, sp, #12
            add r4, r0, #0x18
            mov r0, #0
            mov r1, r4
            mov r2, #0x3E
        clear_payload:
            str r0, [r1], #4
            subs r2, r2, #1
            bne clear_payload
            bl 0x{a['get_language']:08X}
            strh r0, [r4]
            strh r0, [r4, #2]
            mov r0, #0
            str r0, [r4, #4]
            add r5, r4, #8
            mov r6, #0
        next_object:
            mov r0, r5
            bl 0x{a['init_object']:08X}
            mov r1, #108
            strh r1, [r5, #2]
            cmp r6, #0
            moveq r1, #32
            cmp r6, #1
            moveq r1, #136
            cmp r6, #2
            moveq r1, #120
            strh r1, [r5]
            mov r0, r5
            mov r1, r6
            cmp r6, #2
            moveq r1, #3
            ldrh r2, [r4]
            bl 0x{a['set_frame']:08X}
            add r5, r5, #0x50
            add r6, r6, #1
            cmp r6, #3
            blo next_object
            pop {{r0-r7, r9-r12, lr}}
            ldr r8, fade
            bx lr
        callback: .word 0x{a['tick']:08X}
        priority: .word 0x1500
        fade: .word 0x080C3ED8
        """, 12),
        # r0=owned presentation. Preserve loop variables across native ABI.
        "init_object": (f"""
            push {{r0-r12, lr}}
            sub sp, sp, #0x3C
            mov r1, #0
            mov r2, #0
        clear_args:
            str r1, [sp, r2]
            add r2, r2, #4
            cmp r2, #0x3C
            blo clear_args
            str r0, [sp, #0x38]
            ldr r1, p1
            str r1, [sp, #0x30]
            ldr r1, p0
            str r1, [sp, #0x24]
            ldr r1, p2
            str r1, [sp, #0x18]
            mov r1, #0x4000
            str r1, [sp, #0xC]
            mov r1, #0x1800
            str r1, [sp, #8]
            mov r1, #1
            str r1, [sp, #4]
            bl 0x080127E4
            add sp, sp, #0x3C
            ldrh r1, [r0, #8]
            orr r1, r1, #0x2000
            strh r1, [r0, #8]
            pop {{r0-r12, lr}}
            bx lr
        p0: .word 0x{p0:08X}
        p1: .word 0x{p1:08X}
        p2: .word 0x{p2:08X}
        """, 12),
        "set_frame": ("""
            push {r0-r12, lr}
            push {r0}
            mov r3, #0
            push {r3}
            push {r1}
            push {r2}
            bl 0x080129C8
            add sp, sp, #16
            pop {r0-r12, lr}
            bx lr
        """, 0),
        "draw_object": ("""
            push {r0-r12, lr}
            push {r0}
            mov r1, #0
            push {r1}
            bl 0x08012C28
            add sp, sp, #8
            pop {r0-r12, lr}
            bx lr
        """, 0),
        "tick": (f"""
            push {{r0-r12, lr}}
            bl 0x0801201C
            mov r4, r0
            ldr r5, options
            ldrh r0, [r5]
            tst r0, #0x8000
            bne retire
            ldrh r0, [r5, #2]
            tst r0, #0x80
            bne retire
            ldrh r1, [r5, #6]
            cmp r1, #4
            mov r6, #0
            moveq r6, #1
            ldrh r7, [r4, #4]
            cmp r7, #0
            bne refresh
            cmp r6, #0
            beq refresh
            ldrh r2, [r4]
            tst r0, #8
            beq right
            cmp r2, #0
            subne r2, r2, #1
            b selected
        right:
            tst r0, #2
            beq refresh
            cmp r2, #3
            addlo r2, r2, #1
        selected:
            strh r2, [r4]
        refresh:
            cmp r7, #0
            bne value
            add r0, r4, #8
            strh r6, [r0, #0x10]
            bl 0x{a['draw_object']:08X}
        value:
            add r0, r4, #0x58
            mov r1, #1
            ldrh r2, [r4]
            cmp r7, #0
            movne r1, #2
            ldrhne r2, [r4, #2]
            bl 0x{a['set_frame']:08X}
            strh r6, [r0, #0x10]
            bl 0x{a['draw_object']:08X}
            cmp r7, #0
            bne finished
            add r0, r4, #0xA8
            mov r1, #3
            ldrh r2, [r4]
            bl 0x{a['set_frame']:08X}
            strh r6, [r0, #0x10]
            bl 0x{a['draw_object']:08X}
            b finished
        retire:
            ldrh r0, [r5, #4]
            orr r0, r0, #0x200
            strh r0, [r5, #4]
            bl 0x08012030
        finished:
            pop {{r0-r12, lr}}
            bx lr
        options: .word 0x03004738
        """, 4),
    }

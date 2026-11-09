#!/usr/bin/env python3
"""Positive append/preload/draw ordering for the static companion projection."""
import struct

from analyze_shoot_lifetime_consumers import exact, need
from analyze_shoot_scene_ownership import arm_at


def arm_literal(data, at):
    word=struct.unpack_from('<I',data,at)[0]
    need(word & 0xFFFF0000 == 0xE59F0000, 'positive ARM literal load')
    return struct.unpack_from('<I',data,at+8+(word & 0xFFF))[0]


def contracts(source, native):
    # The actor task appends a presentation; it does not call the renderer.
    exact(source, 0x74241A, ['mov bx, word ptr [0x3a20]', 'shl bx, 1',
        'mov word ptr [bx + 0x3a22], di', 'inc word ptr [0x3a20]'])
    arm_at(native, 0x35298C, ['ldr r8, [pc, #0x40]', 'ldrh r1, [r8]',
        'ldr sb, [pc, #0x3c]', 'str r5, [sb, r1, lsl #2]',
        'add sb, r1, #1', 'strh sb, [r8]'])
    need([arm_literal(native, a) for a in (0x35298C, 0x352994)] ==
         [0x0300482A, 0x03004830], 'actual native presentation list')
    exact(source, 0x741495, ['mov cx, word ptr [0x3a20]', 'or cx, cx',
        'je 0x7414b3', 'mov bx, 0x3a22', 'mov ax, word ptr [bx]',
        'push 0xc00', 'push ax', 'lcall 0x4fff, 0x2a4b',
        'add sp, 4', 'add bx, 2', 'loop 0x7414a0'])
    arm_at(native, 0x373550, ['ldr r8, [pc, #0x58]', 'ldrh r2, [r8]',
        'movs r2, r2', 'ble #0x8373580', 'ldr r1, [pc, #0x4c]',
        'ldr r0, [r1], #4', 'stmdb sp!, {r0}', 'stmdb sp!, {fp}',
        'bl #0x8012c28', 'add sp, sp, #8', 'subs r2, r2, #1',
        'bgt #0x8373564'])
    need([arm_literal(native, a) for a in (0x373550, 0x373560)] ==
         [0x0300482A, 0x03004830], 'actual native draw consumes same list')
    arm_at(native, 0xD1BF0, ['mov r8, #0x6000', 'stmdb sp!, {r8}',
        'bl #0x8011ac4', 'add sp, sp, #0xc', 'ldr r8, [pc, #0x18]',
        'str r0, [r8]'])
    need(arm_literal(native, 0xD1C00) == 0x03004514, 'battle priority owner')
    arm_at(native, 0x11E7C, ['ldr r8, [sp, #0xc]', 'ldr sb, [sp, #4]',
        'str sb, [r8]', 'bx lr'])
    arm_at(native, 0x3522D0, ['add r8, pc, #0x24', 'ldrsh r8, [r1, r8]',
        'stmdb sp!, {r8}', 'bl #0x8011ac4'])
    priorities = struct.unpack_from('<26h', native, 0x3522FC)
    need(priorities[16:20] == (0x2C00,)*4 and priorities[20:22] == (0x3000,0x3800),
         'companion pool2 and fighter pool3/4 priorities')
    need(all(0 <= x < 0x6000 for x in priorities), 'all existing actor tasks precede draw')
    arm_at(native, 0x352BA4, ['mov r8, #3', 'stmdb sp!, {r8}',
        'bl #0x8352374', 'add sp, sp, #0x1c'])
    arm_at(native, 0x352BE0, ['mov r8, #4', 'stmdb sp!, {r8}',
        'bl #0x8352374', 'add sp, sp, #0x1c'])
    arm_at(native, 0x35345C, ['ldr sb, [sp, #0x20]', 'cmp sb, #0',
        'moveq r3, #0x49', 'movne r3, #0x6d', 'ldr r0, [sp, #0x20]'])
    arm_at(native, 0x353348, ['ldr r0, [sp, #0x1c]', 'lsl r0, r0, #5',
        'mov r5, r0', 'mov r1, r5'])
    arm_at(native, 0x353370, ['ldr r0, [pc, #0x140]', 'ldr r8, [pc, #0x140]',
        'sub r0, r0, r8', 'add r1, r1, r0', 'add r5, r5, r0'])
    arm_at(native, 0x35349C, ['ldr r8, [pc, #0x30]', 'add r5, r5, r8',
        'str r5, [r1, #0x80]'])
    need([arm_literal(native, a) for a in (0x353370, 0x353374, 0x35349C)] ==
         [0x0860B000, 0x084A80F8, 0x084A82D8],
         'preload R5 is resource offset until companion table addition')
    sites=[]; cursor=0
    while (cursor := source.find(bytes.fromhex('9A742E9040'), cursor)) >= 0:
        sites.append(cursor); cursor+=1
    need(sites == [0x74374D,0x747D0C,0x767503,0x7676D1,0x76BC62],
         'source direct character reconstruction call population')
    # The first two initialize actors before the terminal owner exists. The
    # form-completion calls execute inside the existing fighter actor tasks.
    exact(source, 0x7674F5, ['xor ax, ax', 'xor dx, dx',
        'mov al, byte ptr [si + 0x10]', 'mov dl, byte ptr [si + 0x11]',
        'push 1', 'push dx', 'push ax', 'lcall 0x4090, 0x2e74'])
    exact(source, 0x7676C3, ['xor ax, ax', 'xor dx, dx',
        'mov al, byte ptr [si + 0x10]', 'mov dl, byte ptr [si + 0x11]',
        'push 0', 'push dx', 'push ax', 'lcall 0x4090, 0x2e74'])
    exact(source, 0x76BC32, ['mov bx, word ptr es:[0x65c]',
        'mov si, word ptr es:[0x65e]', 'mov byte ptr [si + 0x5d], 0'])
    need(struct.unpack_from('<I', native, 0x12C50)[0] == 0x03000204,
         'existing dynamic dispatcher points after relocated PUSH')
    return dict(status='APPEND_PRELOAD_DRAW_ORDER_PASS',
        ordering=['scene0FF0 capture', 'companion2C00 list append',
                  'FIRST3000 form completion/preload', 'battle6000 actual dynamic render'],
        source_reconstruction_calls=[f'{a:06X}' for a in sites],
        companion_priorities=list(priorities[16:20]), fighter_priorities=list(priorities[20:22]),
        all_actor_priorities=list(priorities), source_render='741495..7414B1',
        native_render='08373550..0837357C', native_list='0300482A/03004830',
        preload_resource='084A82D8 + R5 byte offset; form delta 00162F08',
        no_late_reload_assumption=False,
        scope='normal retained actor/task and exclusive terminal-owner lifecycle; not an arbitrary scheduler state')

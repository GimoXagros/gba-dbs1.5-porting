"""Generate graphics initialization from the mode 22 source lists and placements."""


def assembly(meta, pointers):
    objects = {row["label"]: row for row in meta["objects"]}
    def transfer(name, target=None):
        row = objects[name]
        if target is None:
            dst = row["source_destination"]
            target = (0x06000000 + dst - 0x4000 if row["kind"] == "tiles"
                      else 0x05000000 + dst - 0xFE00)
        return f".word {pointers[name]}, {target}, {row['size']//2}, 1"
    def rect(name, x, y, width, height):
        assert objects[name]["size"] == width*height*2
        return f".word {pointers[name]}, {0x0600F800+64*y+2*x}, {width}, {height}"
    def group(name, entries):
        return name + ":\n" + "\n".join(entries) + "\n.word 0\n"
    edges = [transfer("common-edge", addr) for addr in (0x0600F000, 0x0600F440)]
    out = ["""
m22_prepare:
push {r4-r11,lr}
mov r4,r0
mov r0,#0x04000000
ldr r1,=0x1f02
strh r1,[r0,#8]
ldr r1,=0x1e03
strh r1,[r0,#10]
ldr r0,=0x0600f000
mov r1,#0
mov r2,#1024
m22_clear_maps:
str r1,[r0],#4
subs r2,r2,#1
bne m22_clear_maps
ldr r0,=0x030012b8
str r1,[r0]
ldr r0,=m22_common_list
bl m22_copy_list
ldrb r5,[r4,#26]
cmp r5,#2
beq m22_prepare_ordinary
cmp r5,#4
beq m22_prepare_special
ldr r0,=m22_empty_list
bl m22_copy_list
cmp r5,#8
ldreq r0,=m22_device_error
cmp r5,#16
ldreq r0,=m22_invalid_data
cmp r5,#1
ldreq r0,=m22_empty_message
ldr r0,[r0]
ldr r1,=0x0600fa0c
ldr r2,=0x8001
m22_empty_text:
ldrb r3,[r0],#1
cmp r3,#0
beq m22_empty_done
sub r3,r3,#32
add r3,r3,r2
strh r3,[r1],#2
b m22_empty_text
m22_empty_done:
ldr r0,=0x030012bb
mov r1,#252
strb r1,[r0]
b m22_graphics_done
m22_prepare_special:
ldr r0,=m22_special_list
bl m22_copy_list
b m22_graphics_done
m22_prepare_ordinary:
ldr r0,=m22_ordinary_base_list
bl m22_copy_list
ldrb r5,[r4,#27]
ldr r0,=m22_rank_lists
ldr r0,[r0,r5,lsl #2]
bl m22_copy_list
ldr r0,=m22_tag_tiles
bl m22_copy_list
mov r5,#9
m22_ordinary_maps:
add r0,r4,r5,lsl #1
ldrh r0,[r0,#4]
cmp r0,#0
beq m22_next_ordinary_map
ldr r0,=m22_tag_maps
ldr r0,[r0,r5,lsl #2]
bl m22_copy_list
m22_next_ordinary_map:
subs r5,r5,#1
bpl m22_ordinary_maps
ldr r0,=m22_common_edges
bl m22_copy_list
m22_graphics_done:
ldr r0,=0x030012b6
mov r1,#7
strb r1,[r0]
ldr r0,=0x030012ca
mov r1,#0
strb r1,[r0]
pop {r4-r11,pc}
.ltorg

@ Entries give source, destination, halfwords per row, and row count.
m22_copy_list:
push {r4-r8,lr}
mov r4,r0
m22_list_next:
ldr r0,[r4],#4
cmp r0,#0
beq m22_list_done
ldr r1,[r4],#4
ldr r2,[r4],#4
ldr r3,[r4],#4
m22_rect_row:
mov r5,r2
mov r6,r1
m22_rect_copy:
ldrh r7,[r0],#2
strh r7,[r6],#2
subs r5,r5,#1
bne m22_rect_copy
add r1,r1,#64
subs r3,r3,#1
bne m22_rect_row
b m22_list_next
m22_list_done:
pop {r4-r8,pc}
"""]
    out.append(group("m22_common_list",[transfer("shared-bg-tiles"),transfer("shared-bg-palette"),transfer("scroll-map",0x0600F000)]))
    out.append(group("m22_common_edges",edges))
    out.append(group("m22_empty_list",[transfer("ascii-font-tiles"),transfer("ascii-font-palette"),*edges]))
    out.append(group("m22_special_list",[transfer("special-tiles"),transfer("special-palette"),
        rect("special-map",9,4,10,6),transfer("ascii-font-tiles"),transfer("ascii-font-palette"),transfer("name-palette"),
        transfer("name-palette",0x05000300),transfer("special-top",0x0600F000),transfer("special-bottom",0x0600F440),
        rect("special-banner-map",0,12,28,2),transfer("special-portrait-tiles"),transfer("special-portrait-palette")]))
    out.append(group("m22_ordinary_base_list",[transfer("ordinary-base-tiles"),transfer("ordinary-base-palette"),rect("ordinary-base-map",10,6,8,6)]))
    out.append(group("m22_tag_tiles",[transfer("digits-tiles"),transfer("digits-palette"),transfer("digits-palette",0x050003E0),
        *(transfer(f"tag-{i}-tiles") for i in range(10)),transfer("ordinary-palettes")]))
    icons=meta["ordinary_icons"]
    for i, row in enumerate(icons):
        out.append(group(f"m22_rank_{i}",[transfer(f"rank-tiles-{i}"),transfer(f"rank-palette-{i}"),rect(f"rank-map-{i}",10,8,8,2)]))
        out.append(group(f"m22_tag_{i}",[rect(f"tag-{i}-map",row["map_x"],row["map_y"],row["map_width"],4)]))
    out.append("m22_rank_lists:\n.word "+",".join(f"m22_rank_{i}" for i in range(10)))
    out.append("m22_tag_maps:\n.word "+",".join(f"m22_tag_{i}" for i in range(10)))
    out.append("m22_digit_positions:\n.hword "+",".join(str(r["digit_x"]*256+r["digit_y"]) for r in icons))
    out.append(f"m22_empty_message: .word {pointers['empty-text']}\nm22_device_error: .word m22_device_label\nm22_invalid_data: .word m22_invalid_label")
    out.append('m22_device_label: .ascii "TAG READ ERROR"\n.byte 0\nm22_invalid_label: .ascii "INVALID TAG DATA"\n.byte 0\n.align 2')
    return "\n".join(out)

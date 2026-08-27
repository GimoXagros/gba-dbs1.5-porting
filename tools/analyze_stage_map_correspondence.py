#!/usr/bin/env python3
"""Compare rendered WSC and GBA Battle Spirit stage-map frames.

Both releases keep the fighting viewport as a 28x18 tile surface.  This tool
renders maps to canonical BGR555 pixels, so it can prove map correspondence
even when the GBA converter reordered the underlying tile set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from PIL import Image


WIDTH = 28
HEIGHT = 18
MAP_BYTES = WIDTH * HEIGHT * 2
RESOURCE_SIZE = 0x18


def parse_int(value: str) -> int:
    return int(value, 0)


def expand4(value: int) -> int:
    return (value << 1) | (value >> 3)


def wsc_color_to_bgr555(value: int) -> int:
    blue = expand4(value & 0xF)
    green = expand4((value >> 4) & 0xF)
    red = expand4((value >> 8) & 0xF)
    return red | (green << 5) | (blue << 10)


def wsc_tile(tile: bytes) -> list[int]:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return pixels


def gba_tile(tile: bytes) -> list[int]:
    pixels: list[int] = []
    for value in tile:
        pixels.extend((value & 0xF, value >> 4))
    return pixels


def decode_wsc_entry(entry: int) -> tuple[int, int, bool, bool]:
    tile = (entry & 0x1FF) | ((entry & 0x2000) >> 4)
    palette = (entry >> 9) & 0xF
    return tile, palette, bool(entry & 0x4000), bool(entry & 0x8000)


def decode_gba_entry(entry: int) -> tuple[int, int, bool, bool]:
    return entry & 0x3FF, (entry >> 12) & 0xF, bool(entry & 0x400), bool(entry & 0x800)


def render(map_data: bytes, tiles: list[list[int]], palettes: list[list[int]], decoder) -> bytes:
    if len(map_data) != MAP_BYTES:
        raise ValueError("map is not 28x18 entries")
    canvas = [0] * (WIDTH * 8 * HEIGHT * 8)
    pitch = WIDTH * 8
    for map_index, (entry,) in enumerate(struct.iter_unpack("<H", map_data)):
        tile_index, palette_index, hflip, vflip = decoder(entry)
        if tile_index >= len(tiles) or palette_index >= len(palettes):
            return b""
        tile = tiles[tile_index]
        tx = (map_index % WIDTH) * 8
        ty = (map_index // WIDTH) * 8
        for y in range(8):
            sy = 7 - y if vflip else y
            for x in range(8):
                sx = 7 - x if hflip else x
                color = tile[sy * 8 + sx]
                canvas[(ty + y) * pitch + tx + x] = palettes[palette_index][color]
    return struct.pack(f"<{len(canvas)}H", *canvas)


def save_image(pixels: bytes, path: pathlib.Path) -> None:
    words = struct.unpack(f"<{len(pixels) // 2}H", pixels)
    rgb = bytearray()
    for value in words:
        red = value & 0x1F
        green = (value >> 5) & 0x1F
        blue = (value >> 10) & 0x1F
        rgb.extend((red * 255 // 31, green * 255 // 31, blue * 255 // 31))
    image = Image.frombytes("RGB", (WIDTH * 8, HEIGHT * 8), bytes(rgb))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--gba-palette", type=parse_int, required=True)
    parser.add_argument("--gba-tiles", type=parse_int, required=True)
    parser.add_argument("--resource-start", type=parse_int, default=0x7F8E0)
    parser.add_argument("--resource-first", type=int, required=True)
    parser.add_argument("--resource-count", type=int, required=True)
    parser.add_argument("--wsc-palette", type=parse_int, required=True)
    parser.add_argument("--wsc-tiles", type=parse_int, required=True)
    parser.add_argument("--wsc-maps", type=parse_int, required=True)
    parser.add_argument("--wsc-map-count", type=int, default=32)
    parser.add_argument("--palette-dest-index", type=int, default=1)
    parser.add_argument("--palette-color-count", type=int, default=0x6F)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--image-dir", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    gba_palette_ram = [0] * 256
    wsc_palette_ram = [0] * 256
    gba_source = struct.unpack_from(f"<{args.palette_color_count}H", gba, args.gba_palette)
    wsc_source = struct.unpack_from(f"<{args.palette_color_count}H", wsc, args.wsc_palette)
    for index, value in enumerate(gba_source, args.palette_dest_index):
        gba_palette_ram[index] = value
    for index, value in enumerate(wsc_source, args.palette_dest_index):
        wsc_palette_ram[index] = wsc_color_to_bgr555(value)
    gba_palettes = [gba_palette_ram[index:index + 16] for index in range(0, 256, 16)]
    wsc_palettes = [wsc_palette_ram[index:index + 16] for index in range(0, 256, 16)]

    # Stage-specific graphics are loaded into tile bank 1 / character index
    # 0x200 on both machines.  Bank 0 contains shared runtime graphics.
    blank_tile = [0] * 64
    gba_tiles = [blank_tile] * 512 + [
        gba_tile(gba[args.gba_tiles + index * 32:args.gba_tiles + (index + 1) * 32])
        for index in range(512)
    ]
    wsc_tiles = [blank_tile] * 512 + [
        wsc_tile(wsc[args.wsc_tiles + index * 32:args.wsc_tiles + (index + 1) * 32])
        for index in range(512)
    ]

    wsc_rendered: list[tuple[int, bytes, str]] = []
    for index in range(args.wsc_map_count):
        offset = args.wsc_maps + index * MAP_BYTES
        pixels = render(wsc[offset:offset + MAP_BYTES], wsc_tiles, wsc_palettes, decode_wsc_entry)
        if pixels:
            wsc_rendered.append((offset, pixels, hashlib.sha256(pixels).hexdigest().upper()))
            if args.image_dir:
                save_image(pixels, args.image_dir / f"wsc-{offset:06X}.png")

    gba_maps = []
    matches = []
    nearest = []
    for resource_index in range(args.resource_first, args.resource_first + args.resource_count):
        resource = args.resource_start + resource_index * RESOURCE_SIZE
        width, height = struct.unpack_from("<HH", gba, resource)
        descriptor_pointer = struct.unpack_from("<I", gba, resource + 8)[0]
        descriptor = descriptor_pointer - 0x08000000
        for frame in range(width * height):
            count, map_pointer = struct.unpack_from("<II", gba, descriptor + frame * 8)
            map_offset = map_pointer - 0x08000000
            pixels = render(gba[map_offset:map_offset + MAP_BYTES], gba_tiles, gba_palettes, decode_gba_entry)
            digest = hashlib.sha256(pixels).hexdigest().upper() if pixels else None
            row = {
                "resource_index": resource_index,
                "frame": frame,
                "descriptor": descriptor + frame * 8,
                "count": count,
                "map_offset": map_offset,
                "render_sha256": digest,
            }
            gba_maps.append(row)
            if pixels and args.image_dir:
                save_image(pixels, args.image_dir / f"gba-r{resource_index:02d}-f{frame:02d}-{map_offset:06X}.png")
            for wsc_offset, wsc_pixels, wsc_digest in wsc_rendered:
                if pixels == wsc_pixels:
                    matches.append({
                        "resource_index": resource_index,
                        "frame": frame,
                        "gba_map_offset": map_offset,
                        "wsc_map_offset": wsc_offset,
                        "render_sha256": wsc_digest,
                    })
            if pixels and wsc_rendered:
                scored = []
                pixel_count = len(pixels) // 2
                for wsc_offset, wsc_pixels, _ in wsc_rendered:
                    equal = sum(
                        pixels[pos:pos + 2] == wsc_pixels[pos:pos + 2]
                        for pos in range(0, len(pixels), 2)
                    )
                    scored.append((equal / pixel_count, wsc_offset))
                for ratio, wsc_offset in sorted(scored, reverse=True)[:3]:
                    nearest.append({
                        "resource_index": resource_index,
                        "frame": frame,
                        "gba_map_offset": map_offset,
                        "wsc_map_offset": wsc_offset,
                        "equal_pixel_ratio": round(ratio, 6),
                    })

    result = {
        "schema": 1,
        "viewport_tiles": [WIDTH, HEIGHT],
        "gba_maps": gba_maps,
        "wsc_candidate_maps": [
            {"offset": offset, "render_sha256": digest}
            for offset, _, digest in wsc_rendered
        ],
        "exact_render_matches": matches,
        "nearest_render_matches": nearest,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

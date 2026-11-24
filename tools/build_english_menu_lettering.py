"""Refine the two English title buttons using glyphs already in their native atlas."""
import argparse
import json
from pathlib import Path

from build_mode23_title_assets_r4 import BASE, pack, tile_layouts
from verify_source_english_submenus import P0, decode, sha

PARENT = "A1CA6459F3E798B3AEA279C1EF5D166B4A37A0EFA86FEB62F8EB330B65455DA3"
OWNER = "5809C36EEEEFA27F04A547D9DB0D5190A219B6B5A2152CDF3F2EDE3C34536C7C"
SPAN = 6064
ORIGINAL = "49B357B0795DC925DB7CEA8F72F2D219C6612F64113A4CFE39FD1B4F7E4F6F7F"

# (event, first raster column, width), measured on the 88x16 native button.
GLYPHS = {"V": (6, 22, 6), "S": (6, 29, 6), "E": (1, 75, 5),
          "R": (6, 54, 6), "B": (1, 41, 6), "•": (7, 45, 3)}


def draw_glyph(frames, target, char, left):
    event, src, width = GLYPHS[char]
    for y in range(-3, 4):
        for x in range(width):
            value = frames[event][src + x - 44, y]
            assert value in (13, 14, 15)
            target[left + x - 44, y] = value


def build(before, owner_bytes, pinned_parent=PARENT, pinned_owner=OWNER):
    parent = json.loads(owner_bytes)
    assert sha(before) == parent["output_sha256"] == pinned_parent and sha(owner_bytes) == pinned_owner
    assert sha(before[P0:P0 + SPAN]) == ORIGINAL
    frames = decode(before, P0, 11)
    edited = [frame.copy() for frame in frames]
    # The USA OPTIONS tile contains a four-column remnant; center a full S
    # after the N, with two blank columns, as between the preceding O and N.
    for y in range(-3, 4):
        for x in range(64, 73):
            edited[3][x - 44, y] = 15
    draw_glyph(frames, edited[3], "S", 66)
    # The user-facing series abbreviation uses the original middle-dot mark.
    # Its narrower width leaves equal margins on the caption side of the icon.
    for y in range(-3, 4):
        for x in range(18, 85):
            edited[7][x - 44, y] = 15
    for char, x in zip("VSVERB•S", (22, 29, 39, 46, 52, 62, 69, 73)):
        draw_glyph(frames, edited[7], char, x)
    layouts, tiles = tile_layouts(edited)
    assert list(map(len, layouts)) == [8] + [22] * 10
    data = pack(layouts, tiles, BASE + P0)
    assert len(data) <= SPAN
    after = before[:P0] + data + before[P0 + len(data):]
    assert decode(after, P0, 11) == edited and {i for i in range(11) if edited[i] != frames[i]} == {3, 7}
    used = parent["prior_excluded_extents"] + [[e["start"], e["end"]] for e in parent["allocations"]]
    meta = dict(input_sha256=pinned_parent, prior_owner_sha256=pinned_owner, output_sha256=sha(after),
                prior_excluded_extents=used, allocations=[], storage_exports=parent["storage_exports"],
                writes=[dict(offset=P0, size=len(data), purpose="English title buttons 3 and 7",
                             before_sha256=sha(before[P0:P0 + len(data)]), after_sha256=sha(data))],
                title_p0=BASE + P0, owned_extent=[P0, SPAN], changed_events=[3, 7],
                labels=["OPTIONS", "VS VER B•S"], whole_image_inverse=True,
                builder_sha256=sha(Path(__file__).read_bytes()))
    return after, meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("input", "owner", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--pinned-parent", "--input-sha256", dest="parent_pin")
    parser.add_argument("--pinned-owner", "--owner-sha256", dest="owner_pin")
    a = parser.parse_args()
    if bool(a.parent_pin) != bool(a.owner_pin):
        parser.error("the parent ROM and owner digest must be supplied together")
    rom, manifest = build(a.input.read_bytes(), a.owner.read_bytes(), a.parent_pin or PARENT, a.owner_pin or OWNER)
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / "component.gba").write_bytes(rom)
    output = a.output / "manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(sha(rom), sha(output.read_bytes()))

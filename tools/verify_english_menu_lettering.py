"""Verify native glyph shapes against game memory and the final composited PNG."""
import argparse
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw
from verify_source_english_submenus import P0, decode, sha
from verify_source_english_submenu_capture import check

CANDIDATE = "58C7352A1F3F69C73A29DDF863F428F0610E7E064DB5DE7EDA476203DC2F422A"
PRIOR = "A1CA6459F3E798B3AEA279C1EF5D166B4A37A0EFA86FEB62F8EB330B65455DA3"


def box(fr, lo, width):
    return tuple(tuple(fr[x-44, y] for x in range(lo, lo+width)) for y in range(-3, 4))


def screenshot_row(path, name, row):
    data = (path / (name + "-iwram.bin")).read_bytes()
    x, y = struct.unpack_from("<hh", data, 0x2A78+80*row)
    img = Image.open(path / (name + ".png")).convert("RGB")
    return img.crop((x-36, y, x-36+88, y+16))


def main(a):
    before = a.parent.read_bytes()
    current = (a.live/"loaded-rom.bin").read_bytes()
    assert sha(before) == PRIOR and sha(current) == CANDIDATE
    launch = json.loads((a.live/"launch.json").read_bytes())
    assert launch["outcome"] == "ordinary-language-title-portrait-complete" and launch["loaded_rom_exact"]
    assert not launch["guest_writes"] and not launch["visible"] and not launch["supplied_save_used"]
    for name, checksum in launch["files"].items():
        assert sha((a.live/name).read_bytes()) == checksum
    old = decode(before, P0, 11)
    new = decode(current, P0, 11)
    assert {i for i in range(11) if old[i] != new[i]} == {3,7}
    assert before[:P0] == current[:P0] and before[P0+6064:] == current[P0+6064:]
    native = decode(before, 0x8FD08, 5)
    assert native[3] == old[3]
    assert {x for x in range(65,77) if any(old[3][x-44,y] != 15 for y in range(-3,4))} == {68,69,70,71}
    assert box(new[3], 66, 6) == box(old[6], 29, 6) == box(new[7], 29, 6) == box(new[7], 73, 6)
    for start, src_event, src_x, width in [(22,6,22,6),(39,6,41,6),(46,1,75,5),(52,6,54,6),(62,1,41,6),(69,7,45,3)]:
        assert box(new[7], start, width) == box(old[src_event], src_x, width)
    for i, left, right in ((3,66,71),(7,18,84)):
        assert all(old[i][(x,y)] == col for (x,y),col in new[i].items()
                   if not (-3 <= y <= 3 and left <= x+44 <= right))
    result = {name:check(a.live, name, events, new) for name,events in
              (("root",[1,2,3,4,5]),("versus-visible",[6,7]))}
    baseline = (a.baseline/"loaded-rom.bin").read_bytes()
    assert decode(baseline, P0, 11) == old
    old_live = {name:check(a.baseline,name,events,old) for name,events in
                (("root",[1,2,3,4,5]),("versus-visible",[6,7]))}
    a.out.mkdir(parents=True,exist_ok=True)
    sheet = Image.new("RGB",(88*2+8,16*2+4),(36,38,42))
    for row,(menu,index) in enumerate((("root",2),("versus-visible",1))):
        for col,path in enumerate((a.baseline,a.live)):
            sheet.paste(screenshot_row(path,menu,index),(col*96,row*20))
    sheet.save(a.out/"buttons-before-after-1x.png")
    result_img = Image.new("RGB",(sheet.width*4,sheet.height*4+20),(36,38,42))
    result_img.paste(sheet.resize((sheet.width*4,sheet.height*4), Image.Resampling.NEAREST),(0,20))
    label = ImageDraw.Draw(result_img)
    label.text((1,2),"Before", fill="white");label.text((385,2),"After", fill="white")
    result_img.save(a.out/"buttons-before-after-4x.png")
    report = dict(status="PASS",old=PRIOR,new=CANDIDATE,current_physical=result,prior_physical=old_live,
                  panels=["OPTIONS","VS VER B•S"],old_options_ink_columns=[68,69,70,71],
                  new_options_ink_columns=list(range(66,72)),capture_launch=sha((a.live/"launch.json").read_bytes()),
                  gallery_sha256=sha((a.out/"buttons-before-after-1x.png").read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()))
    path=a.out/"report.json"
    path.write_text(json.dumps(report,indent=2)+"\n", encoding="utf-8", newline="\n")
    print("PASS", sha(path.read_bytes()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("parent","baseline","live","out"):
        parser.add_argument(arg,type=Path)
    main(parser.parse_args())

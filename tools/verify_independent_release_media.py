"""Check the release ROM against physical localization captures and native sound evidence."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from PIL import Image


BASE = 0x08000000
FINAL = "AA6BB1EB93027464F842D6EB0CC69A68959F26B38460FAF1B0C63BDD5FFA4BB1"
RETAIL = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
MEDIA_PROOFS = {
    "title-portrait-live-qa-20261124/report.json": "27C7DB153DD9AA190F365F4D61AAF7BF1854261396E01AA314E546EAA502F18D",
    "v94-release/opening-playback.json": "1CA26DABAD5006C6416A12019405F1348A3E8D122D88900909538C8F5DE9E9E3",
    "fighter-sfx-clean-native-v94-20261124/verified.json": "3E35AFCEDC01E46AB5B91AA39C2B2D6FCC64E7046E629EF297E60BABD876D617",
    "fighter-sfx-retail-mix-v94-20261124/report.json": "557E41333926E80CCFF64571395F99139F2FA75E84C8F387B328D4FB5CEFC4B9",
    "evolution-music-three-capture-qa-20261116/audit-6c-b.json": "76742352091B9941CB17C9CF21C64E784CBCFFB029F1FD9FFB8358C32D72394C",
    "evolution-music-three-capture-qa-20261116/audit-6d-a.json": "286E9188BCEE94389A29D80E9F02BC7DCAA95F0B43F6E05B20258A26E1D5830F",
    "evolution-music-pause-capture-qa-20261116/audit.json": "68A8960E0BF02746DF28122E8A8137C05AF0DE9911310B11DF034F14732C87E9",
    "evolution-music-three-capture-qa-20261116/audit-6f-c.json": "F72A105BDFA4989CCAB96AAEF0222CDB5C4E5FE0DECED4A239560FDBA3C05BB3",
}


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def read(path):
    return json.loads(path.read_bytes())


def compare_picture(path, tiles, palette, mgba):
    im = Image.open(path).convert("RGB")
    assert im.size == (240, 160)
    indices = Image.new("P", (96, 128))
    colors = []
    for word in struct.unpack("<16H", palette):
        for shift in (0, 5, 10):
            v = (word >> shift) & 31
            colors.append((v << 3 | v >> 2) if mgba else round(v * 255 / 31))
    indices.putpalette(colors)
    pixels = bytearray()
    for y in range(128):
        for x in range(96):
            pos = ((y // 8) * 12 + x // 8) * 32 + (y % 8) * 4 + x % 8 // 2
            pixels.append((tiles[pos] >> (4 * (x % 2))) & 15)
    indices.frombytes(bytes(pixels))
    assert indices.convert("RGB").tobytes() == im.crop((124, 16, 220, 144)).tobytes(), path
    return pixels


def check(build, image):
    rom = image.read_bytes()
    assert digest(rom) == FINAL
    for name, expected in MEDIA_PROOFS.items():
        assert digest((build / name).read_bytes()) == expected, name
    menu_root = build / "menu-review-four-languages-20261124"
    menus = read(menu_root / "v93-d432dbe9-menus.json")
    screens = menus["source_screenshots"]
    assert len(screens) == 52 and digest((menu_root / "v93-d432dbe9-menus.png").read_bytes()) == menus["sheet_sha256"]
    assert len({(r["language"], r["menu"], r["earned_tag"]) for r in screens}) == len(screens)
    for r in screens:
        p = build.parent / r["file"].replace("\\", "/")
        assert Image.open(p).size == (240, 160) and digest(p.read_bytes()) == r["sha256"]
    credit = read(build / "v94-original-a/intermediate/tag-release/credit/manifest.json")
    for w in credit["writes"]:
        off, size = w["offset"], w["size"]
        assert digest(rom[off:off + size]) == w["after_sha256"], w
    portraits = read(build / "v94-original-a/intermediate/portrait-names/manifest.json")["entries"]
    selector = read(build / "v94-original-a/portrait-selector.json")
    tl, th = selector["table_span"]
    pointers = struct.unpack("<60I", rom[tl:th])
    assert list(pointers) == selector["header_pointers"] and len(portraits) == 60
    mixed = []
    for language in range(4):
        old = build / f"bizhawk-title-headers-roster60-lang{language}"
        boundary = build / ("mixed-v1-aa6b-boundary-b1" if language == 0 else f"independent-release-20261125/mixed-lang{language}")
        locale = build / f"mixed-v1-aa6b-locale-{language}"
        for capture in (boundary, locale):
            launch = read(capture / "launch.json")
            assert not launch["visible"] and not launch["guest_writes"]
            a, b = launch["cartridges"]
            assert (a["core"], b["core"]) == (1, 2) and a["save"] != b["save"]
            assert a["loaded_sha256"] == RETAIL and b["loaded_sha256"] == FINAL
            assert a["status"] == b["status"] == "PASS"
        log = (locale / "trace-2.txt").read_text()
        assert re.search(f"version locale=A{language} row=1 returned=1", log)
        battle = (boundary / "trace-2.txt").read_text()
        assert "common fighters 6/10" in battle and "offer op=0F" in battle
        if language:
            assert "0F81/000A" in battle
        oldlog = read(old / "launch.json")
        assert not oldlog["guest_writes"] and not oldlog["visible"] and oldlog["loaded_rom_exact"]
        for ident in range(15):
            i = language * 15 + ident
            r = portraits[i]
            assert r["id"] == ident and r["language"] == ("en", "ja", "ko", "dg")[language]
            pal, tile = struct.unpack_from("<II", rom, 0x4A5BC0 + 8 * ident)
            palette = rom[pal - BASE:pal - BASE + 32]
            header = rom[pointers[i] - BASE:pointers[i] - BASE + 768]
            body = rom[tile - BASE + 768:tile - BASE + 6144]
            assert digest(header) == r["sha256"] and digest(body) == r["native_body_sha256"]
            stem = f"fighter-{ident:02d}"
            assert (old / (stem + "-tiles.bin")).read_bytes() == header + body
            assert (old / (stem + "-palette.bin")).read_bytes() == palette
            filename = stem + ".png"
            assert digest((old / filename).read_bytes()) == oldlog["files"][filename]
            pixels = compare_picture(old / filename, header + body, palette, False)
            if language == 2:
                for left, right in zip(r["syllables"], r["syllables"][1:]):
                    gap = range(left["right"] + 1, right["left"])
                    assert len(gap) == 2
                    assert all(pixels[y * 96 + x] == r["colors"]["background"] for y in range(1, 16) for x in gap)
            if ident in (0, 10):
                shot = locale / "p2-actual-select.png" if ident == 0 else boundary / "p2-boundary.png"
                compare_picture(shot, header + body, palette, True)
        mixed.append({"locale": language, "selection": [0, 10], "boundary_battle_pair": [6, 10]})
    title_heights = []
    for language in range(4):
        row = next(r for r in screens if r["language"] == language and r["menu"] == "title" and not r["earned_tag"])
        im = Image.open(build.parent / row["file"].replace("\\", "/")).convert("RGB")
        ys = [y for y in range(128, 140) if any(min(im.getpixel((x, y))) > 230 for x in range(61, 201))]
        title_heights.append(max(ys) - min(ys) + 1)
    assert title_heights == [7, 8, 7, 12]
    sounds = {}
    for fighter in (11, 14):
        directory = build / f"flow-release-fighter-{fighter}-c"
        report = read(directory / "report.json")
        data = (directory / "events.txt").read_bytes()
        assert digest(data) == report["events"] and report["rom"] == FINAL and report["result"] == "PASS"
        assert not report["guest_writes"] and not report["visible"]
        for frame, sound, own, own_event, opp, opp_event in re.findall(
            r"(?m)^(\d+) accepted sound ([0-9A-F]{2}) caller=08012918 player=(\d+) event=(\d+) enemy=(\d+) event=(\d+)", data.decode()
        ):
            sounds.setdefault(sound, dict(frame=int(frame), player=int(own), player_event=int(own_event),
                                          enemy=int(opp), enemy_event=int(opp_event)))
    assert set(sounds) == {"5F", "60", "61", "62", "63"}
    return dict(result="PASS", rom=FINAL, menu_screens=len(screens), roster_headers=60,
                roster_pixels=60*96*128, verified_mixed_portrait_pixels=8*96*128, mixed=mixed,
                korean_syllable_clear_columns=2, credit_height_en_ja_ko_dg=title_heights,
                media_evidence=MEDIA_PROOFS, actual_sound_requests=sounds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("build", "image", "report"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args()
    results = check(args.build.resolve(), args.image)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("PASS", digest(args.report.read_bytes()))


if __name__ == "__main__":
    main()


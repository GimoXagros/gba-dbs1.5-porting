"""Install the four v94 stages after the verified v93 ending and link build."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from build_ending_awards_main_tail import sha, verify_writes
from build_tag_audio_link_tail import check_files

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "records/assist-opening-audio-build.json"
RELATIVE = Path("intermediate/assist-opening-audio")
BASE = Path("intermediate/tag-audio-link/link-editor-clock")
PARENT = "D432DBE9B221A0EFC15B644B8E76A0D39D374DFF1087165A917EF977A3E8BD99"
PARENT_OWNER = "55390CB7C04E02AFC82BF38F9574BBAB234AC4E3B9316876F6E90D61DF6C553D"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def pins():
    rows = json.loads(PINS.read_bytes())
    names = [row["stage"] for row in rows]
    if names != ["options","native-battle","opening","fighter-audio"]:
        raise ValueError("Incomplete or misordered v94 layer record")
    return rows


def expected_layers():
    rows = pins()
    result = {(RELATIVE / row["stage"] / "component.gba").as_posix():row["sha256"] for row in rows}
    result["current-candidate.gba"] = rows[-1]["sha256"]
    return result


def produce(stage, before, owner, source, font, renders, dest, run):
    inputs = ["--input",before,"--owner",owner,"--output",dest]
    image, manifest, report = (dest / n for n in ("component.gba","manifest.json","cpu.json"))
    parent = ["--input-sha256",sha(before.read_bytes()),"--owner-sha256",sha(owner.read_bytes())]
    check = ["--image",image,"--owner",manifest,"--report",report]
    if stage == "options":
        run("build_battle_assist_options.py",*inputs,"--font",font)
        run("verify_battle_assist_options.py",*check,"--prior",before)
    elif stage == "native-battle":
        run("build_play_assists.py",*inputs)
        run("verify_play_assists.py",*check,"--prior",before)
    elif stage == "opening":
        run("build_opening_choice_skip_fix.py",*inputs,*parent,"--source",source)
        run("verify_opening_choice_skip_fix.py",*check,"--prior",before,"--source",source)
    elif stage == "fighter-audio":
        if renders is None:
            # Source audio is an authenticated build input and is not part of the distributed ROM inventory.
            with TemporaryDirectory(dir=dest.parent) as tmp:
                generated = Path(tmp) / "wsc"
                run("render_fighter_sfx.py","--platform","wsc","--rom",source,"--rom-sha256",SOURCE,"--output",generated)
                produce(stage,before,owner,source,font,generated,dest,run)
            return
        run("build_fighter_sfx_timbre.py",*inputs,*parent,"--source",source,"--renders",renders)
        run("verify_fighter_sfx_timbre.py",*check,"--parent",before,"--source",source,"--renders",renders)
    else:
        raise ValueError(f"Unknown stage {stage}")


def install(output, source, font, renders, run):
    source, font = source.resolve(), font.resolve()
    if renders is not None:
        renders = renders.resolve()
    base = output / BASE
    before, owner = base/"component.gba",base/"manifest.json"
    if sha(before.read_bytes()) != PARENT or sha(owner.read_bytes()) != PARENT_OWNER:
        raise ValueError("Unknown link-editor image or ownership record")
    rows = pins()
    dest = output / RELATIVE
    dest.mkdir(parents=True,exist_ok=True)
    for row in rows:
        stage = dest / row["stage"]
        if not stage.exists():
            with TemporaryDirectory(dir=dest) as tmp:
                pending = Path(tmp) / "complete"
                produce(row["stage"],before,owner,source,font,renders,pending,run)
                check_files(pending,row)
                verify_writes(before,pending/"component.gba",pending/"manifest.json")
                pending.rename(stage)
        else:
            check_files(stage,row)
            verify_writes(before,stage/"component.gba",stage/"manifest.json")
        next_owner = stage/"manifest.json"
        if json.loads(next_owner.read_bytes())["prior_owner_sha256"] != sha(owner.read_bytes()):
            raise ValueError(f"Prior ownership does not match at {stage.name}")
        before,owner = stage/"component.gba",next_owner
    for name, path in (("current-candidate.gba",before),("current-candidate.json",owner)):
        pending = output / (name+".pending")
        pending.write_bytes(path.read_bytes())
        pending.replace(output/name)
    return rows

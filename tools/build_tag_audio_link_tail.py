"""Build and verify the native score audio and link reward screens on the complete v92 base."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from build_ending_awards_main_tail import sha, verify_writes


PINS = Path(__file__).resolve().parents[1] / "records/tag-audio-link-build.json"
RELATIVE = Path("intermediate/tag-audio-link")
PARENT = "D71E08960BC8E6FC0F264EE5B69105F2A27041CC2871B0F9861D4CBD68F61AE5"
PARENT_OWNER = "D0FCAAAF7CEFEEDA0F47C239CF5B0A91AA0727065AC11EF3F28364FD4711BBE7"
PRESENTATION = "876C1468C10DCDD66520D65E673D4D0C1ABDC3F3DF27B6E9C0BFFF7F7F5A91A9"
PRESENTATION_CPU = "309C525BD8AAD2DBBB1B8D83673BA85D4BFFEE2CAB25AF3BC5548D752EC6C3E9"
LINK = "853B99FDEB7292478696928FD010A0BB24A3EBC22126CD5407D27509A7ECF1F9"


def pins():
    return json.loads(PINS.read_bytes())


def expected_layers():
    rows = pins()
    return {
        **{(RELATIVE / row["stage"] / "component.gba").as_posix():row["sha256"] for row in rows},
        "current-candidate.gba":rows[-1]["sha256"],
    }


def check_files(directory, row):
    for name, column in (("component.gba","sha256"),("manifest.json","owner_sha256"),("cpu.json","cpu_sha256")):
        if sha((directory / name).read_bytes()) != row[column]:
            raise ValueError(f"{row['stage']} {name} does not match the verified build record")


def produce(stage, before, owner, source, presentation, link, dest, run):
    args = ["--source",source, "--input",before, "--owner",owner, "--output",dest]
    image = dest / "component.gba"
    manifest = dest / "manifest.json"
    check = ["--image",image, "--report",dest / "cpu.json"]
    if stage == "result-audio":
        run("build_tag_result_audio.py",*args,"--input-sha256",PARENT,"--owner-sha256",PARENT_OWNER,
            "--presentation-owner",presentation)
        run("verify_tag_result_audio.py",*check,"--source",source,"--parent",before,"--manifest",manifest)
    elif stage == "score-audio":
        run("build_mode11_score_audio.py",*args)
        run("verify_mode11_score_audio.py",*check,"--prior",before,"--owner",manifest)
    elif stage == "link-cards":
        run("build_mode24_link_cards.py",*args,"--input-sha256",sha(before.read_bytes()),
            "--owner-sha256",sha(owner.read_bytes()),"--link-owner",link,"--link-owner-sha256",LINK,
            "--presentation-owner",presentation,"--presentation-owner-sha256",PRESENTATION)
        run("verify_mode24_link_scene.py",*check,"--before",before,"--owner",manifest)
    elif stage == "master-feedback":
        run("build_mode24_special_feedback.py",*args,"--presentation-owner",presentation)
        run("verify_mode24_master_feedback.py",*check,"--owner",manifest)
    elif stage == "master-celebration":
        run("build_mode24_special_celebration.py",*args)
        run("verify_mode24_special_particles.py",*check,"--source",source,"--prior",before,"--owner",manifest)
    elif stage == "campaign-celebration":
        run("build_mode11_source_particles.py",*args)
        run("verify_mode11_source_particles.py",*check,"--source",source,"--prior",before,"--owner",manifest)
    elif stage == "link-editor-clock":
        celebration = owner.parent.parent / "master-celebration/manifest.json"
        run("build_link_editor_tick_bound.py","--input",before,"--owner",owner,
            "--celebration-owner",celebration,"--output",dest)
        run("verify_link_editor_tick_bound.py",*check,"--prior",before,"--owner",manifest)
    else:
        raise ValueError(f"Unknown tag release stage {stage}")


def install(output,source,run):
    base = output / "intermediate/tag-release"
    before = base / "id12/component.gba"
    owner = base / "id12/manifest.json"
    presentation = base / "presentation/manifest.json"
    link = base / "link/manifest.json"
    if [sha(p.read_bytes()) for p in (before,owner,presentation,link)] != [PARENT,PARENT_OWNER,PRESENTATION,LINK]:
        raise ValueError("Unknown v92 image or tag/link ownership record")
    rows = pins()
    dest = output / RELATIVE
    dest.mkdir(exist_ok=True)
    score_report = dest / "presentation.json"
    if not score_report.exists():
        with TemporaryDirectory(dir=dest) as tmp:
            report = Path(tmp) / score_report.name
            run("verify_mode11_tag_presentation.py","--source",source,"--prior",output/"ending-awards.gba",
                "--image",presentation.with_name("component.gba"),"--owner",presentation,"--report",report)
            if sha(report.read_bytes()) != PRESENTATION_CPU:
                raise ValueError("Earned tag presentation differs from the independent score check")
            report.rename(score_report)
    elif sha(score_report.read_bytes()) != PRESENTATION_CPU:
        raise ValueError("Invalid existing earned tag presentation report")
    for row in rows:
        stage = dest / row["stage"]
        if not stage.exists():
            with TemporaryDirectory(dir=dest) as tmp:
                ready = Path(tmp) / "complete"
                produce(row["stage"],before,owner,source,presentation,link,ready,run)
                check_files(ready,row)
                verify_writes(before,ready/"component.gba",ready/"manifest.json")
                ready.rename(stage)
        else:
            check_files(stage,row)
            verify_writes(before,stage/"component.gba",stage/"manifest.json")
        manifest = json.loads((stage/"manifest.json").read_bytes())
        if manifest["prior_owner_sha256"] != sha(owner.read_bytes()):
            raise ValueError(f"Unknown owner for {row['stage']}")
        before,owner = stage/"component.gba",stage/"manifest.json"
    for filename,data in (("current-candidate.gba",before),("current-candidate.json",owner)):
        pending = output / (filename+".pending")
        pending.write_bytes(data.read_bytes())
        pending.replace(output/filename)
    return rows

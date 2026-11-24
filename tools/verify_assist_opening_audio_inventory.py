"""Compare both original v93 builds, extend them separately and verify the entire v94 inventories."""
import argparse
import json
from pathlib import Path

from build_assist_opening_audio_tail import install, pins, RELATIVE, PINS
from build_ending_awards_main_tail import sha
from verify_id13_main_inventory import inventory
from concurrent.futures import ThreadPoolExecutor


ARCHIVE = "B6A90263554B0C0E0D6B79F5A856DE61D9929A3C1CF307C73ACFAB6B286221AE"
TOP = {"current-candidate.gba","current-candidate.json","build-manifest.json"}


def both(function, directories):
    with ThreadPoolExecutor(2) as workers:
        return list(workers.map(function,directories))


def save(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf8",newline="\n") as out:
        out.write(json.dumps(data,indent=2)+"\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("first","second","parent-audit","before","report"):
        p.add_argument("--"+flag,type=Path,required=True)
    for flag in ("source","font","fighter-sfx-renders","second-fighter-sfx-renders"):
        p.add_argument("--"+flag,type=Path)
    p.add_argument("--prepare-only",action="store_true")
    a = p.parse_args()
    raw = a.parent_audit.read_bytes()
    assert sha(raw) == ARCHIVE
    baseline = json.loads(raw)["sha256_by_relative_path"]
    assert len(baseline) == 579
    dirs = [a.first.resolve(),a.second.resolve()]
    assert dirs[0] != dirs[1] and all(d.is_dir() for d in dirs)
    assert all(not f.resolve().is_relative_to(d) for f in (a.parent_audit,a.before,a.report) for d in dirs)
    states = both(inventory,dirs)
    if not a.before.exists():
        assert states[0] == states[1] == baseline, "Original builds are incomplete or differ from v93"
        save(a.before,dict(status="IDENTICAL_COMPLETE_V93",parent_audit=ARCHIVE,files_each=len(baseline),
                           directories=[str(d) for d in dirs],sha256_by_relative_path=states[0]))
    else:
        proof = json.loads(a.before.read_bytes())
        assert proof["status"]=="IDENTICAL_COMPLETE_V93" and proof["parent_audit"]==ARCHIVE
        assert proof["directories"]==[str(d) for d in dirs] and proof["sha256_by_relative_path"]==baseline
        for state in states:
            assert all(state.get(n)==v for n,v in baseline.items() if n not in TOP)
            assert all(n in baseline or n.startswith(RELATIVE.as_posix()+"/") for n in state)
    if a.prepare_only:
        print("PASS",len(baseline),"identical original-build files",sha(a.before.read_bytes()))
        return
    if not a.source or not a.font:
        p.error("v94 installation requires --source and --font")
    assert not a.report.exists()
    import build_current_candidate as production
    from verify_tag_release_inventory import update_manifest

    def extend(d):
        renders = a.second_fighter_sfx_renders if d == dirs[1] and a.second_fighter_sfx_renders else a.fighter_sfx_renders
        rows = install(d,a.source.resolve(),a.font.resolve(),renders,production.run)
        update_manifest(d,production.EXPECTED_LAYERS,"assist_opening_audio_build",rows)
        return inventory(d)

    first,second = both(extend,dirs)
    assert first == second
    added = {(RELATIVE / row["stage"] / file).as_posix() for row in pins()
             for file in ("component.gba","manifest.json","cpu.json")}
    assert set(first) == set(baseline) | added
    assert {n for n,v in baseline.items() if first[n]!=v} == TOP
    assert all(first[n]==value for n,value in production.EXPECTED_LAYERS.items())
    result = dict(status="PASS",parent_audit=ARCHIVE,pristine_pair_sha256=sha(a.before.read_bytes()),
                  previous_files=len(baseline),files_each=len(first),final_sha256=first["current-candidate.gba"],
                  pipeline_sha256=sha(Path(production.__file__).read_bytes()),stages_sha256=sha(PINS.read_bytes()),
                  sha256_by_relative_path=first)
    save(a.report,result)
    print("PASS",len(first),"files per build",first["current-candidate.gba"],sha(a.report.read_bytes()))


if __name__=="__main__":
    main()

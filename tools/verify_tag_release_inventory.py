"""Check and compare two complete independently built cartridge output directories."""
import argparse
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import build_current_candidate as production
import build_tag_release_tail as v92
import build_tag_audio_link_tail as current
from build_ending_awards_main_tail import sha
from verify_id13_main_inventory import inventory


V91_AUDIT = "772EF5207CC97F1678AB3F31A7008E9DF74CD1108A28570CEE9A9D713D5D334B"
V92_AUDIT = "9BCA05F9661AC1DE3D2EB9914C4097DFCE427F8635ABB2BA683FC25CD2A3E191"
V92_RAW_MANIFEST = "A02DD46B1EF9F9C1F1D174D1891CF3C7969BE160F90E366F1EE89D23578A59E8"
TOP = {"current-candidate.gba","current-candidate.json","build-manifest.json"}


def save(path, record):
    path.parent.mkdir(parents=True,exist_ok=True)
    pending = path.with_name(path.name+".pending")
    pending.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
    pending.replace(path)


def update_manifest(output,layers,field,rows):
    path = output/"build-manifest.json"
    data = json.loads(path.read_bytes())
    data["layers"] = layers
    data["collection_and_language"][field] = rows
    pending = output/"build-manifest.pending"
    # The original main recipe uses the host text newline for this existing document.
    pending.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    pending.replace(path)


def both(fn, arguments):
    with ThreadPoolExecutor(2) as pool:
        jobs = [pool.submit(fn,*args) for args in arguments]
        return [job.result() for job in jobs]


def archived_layer_order(layers):
    # The old incremental recipe appended tag stages after all v91 layers.
    late = ("initial-portrait.gba", "portrait-selector.gba", "stage11-results.gba")
    result = {}
    for name, value in layers.items():
        if name == "ending-awards.gba":
            result.update((key, layers[key]) for key in late)
        if name not in late:
            result[name] = value
    return result


def v93_layers():
    from build_assist_opening_audio_tail import RELATIVE as later
    layers = {k:v for k,v in production.EXPECTED_LAYERS.items() if not k.startswith(later.as_posix()+"/")}
    layers["current-candidate.gba"] = current.pins()[-1]["sha256"]
    return layers


def v92_layers():
    parent = {n:val for n,val in v93_layers().items()
              if not n.startswith(current.RELATIVE.as_posix()+"/")}
    parent["current-candidate.gba"] = current.PARENT
    return archived_layer_order(parent)


def historical(parent,output,previous,source,font,credit):
    assert inventory(parent)==previous and not output.exists()
    shutil.copytree(parent,output)
    rows = v92.install(output,source,font,credit,production.run)
    update_manifest(output,v92_layers(),"ending_and_title_build",rows)
    return inventory(output)


def extend(output,source):
    rows=current.install(output,source,production.run)
    update_manifest(output,v93_layers(),"tag_audio_and_link_build",rows)
    return inventory(output)


def fresh(a,archive):
    original=archive["sha256_by_relative_path"].copy()
    archived_manifest=original["build-manifest.json"]
    original["build-manifest.json"]=V92_RAW_MANIFEST
    dirs=(a.first.resolve(),a.second.resolve())
    proof=a.pre_report or a.report.with_name("v92-before.json")
    assert dirs[0]!=dirs[1] and all(p.is_dir() for p in dirs)
    assert all(not q.resolve().is_relative_to(d) for d in dirs for q in (proof,a.report,a.parent_audit))
    states=both(inventory,[(directory,) for directory in dirs])
    if not proof.exists():
        # No write inside either source build precedes this complete comparison.
        assert states[0]==states[1], "the two raw v92 builds differ or are still running"
        assert states[0]==original, "raw v92 differs from the recorded 557-file release"
        for directory in dirs:
            manifest=json.loads((directory/"build-manifest.json").read_bytes())
            manifest["layers"]=archived_layer_order(manifest["layers"])
            previous_bytes=(json.dumps(manifest,indent=2)+"\n").replace("\n","\r\n").encode()
            assert sha(previous_bytes)==archived_manifest, "historical v92 manifest differs beyond layer order"
        save(proof,dict(status="IDENTICAL_COMPLETE_V92",prior_audit=V92_AUDIT,files_each=len(original),
                        archived_manifest_sha256=archived_manifest,raw_manifest_sha256=V92_RAW_MANIFEST,
                        directories=[str(p) for p in dirs],sha256_by_relative_path=states[0]))
    else:
        prior=json.loads(proof.read_bytes())
        assert prior["status"]=="IDENTICAL_COMPLETE_V92" and prior["prior_audit"]==V92_AUDIT
        assert prior["directories"]==[str(p) for p in dirs] and prior["sha256_by_relative_path"]==original
        # A previously verified prefix can be resumed after a later stage is frozen.
        allowed={current.PARENT,*[r["sha256"] for r in current.pins()]}
        for state in states:
            assert state["current-candidate.gba"] in allowed
            assert all(state.get(path)==value for path,value in original.items() if path not in TOP)
            assert all(n in original or n.startswith(current.RELATIVE.as_posix()+"/") for n in state)
    if a.prepare_only:
        print("PASS original complete pair",len(original),sha(proof.read_bytes()))
        return
    assert a.source and not a.report.exists()
    one,two=both(extend,[(d,a.source.resolve()) for d in dirs])
    assert one==two
    added={(current.RELATIVE/r["stage"]/name).as_posix() for r in current.pins()
           for name in ("component.gba","manifest.json","cpu.json")}
    added.add((current.RELATIVE/"presentation.json").as_posix())
    assert set(one)-set(original)==added and not (set(original)-set(one))
    assert {n for n,v in original.items() if one[n]!=v}==TOP
    assert all(one[key]==value for key,value in v93_layers().items())
    result=dict(status="PASS",prior_audit=V92_AUDIT,pristine_pair_sha256=sha(proof.read_bytes()),
                previous_files=len(original),files_each=len(one),final_sha256=one["current-candidate.gba"],
                pipeline_sha256=sha(Path(production.__file__).read_bytes()),stages_sha256=sha(current.PINS.read_bytes()),
                installer_sha256=sha(Path(current.__file__).read_bytes()),sha256_by_relative_path=one)
    save(a.report,result)
    print("PASS",len(one),"files per build",result["final_sha256"],sha(a.report.read_bytes()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ("first","second","parent-audit","report"):
        parser.add_argument("--"+arg,type=Path,required=True)
    for arg in ("first-parent","second-parent","font","credit-font","source","pre-report"):
        parser.add_argument("--"+arg,type=Path)
    parser.add_argument("--extend-in-place",action="store_true")
    parser.add_argument("--prepare-only",action="store_true")
    a=parser.parse_args()
    raw=a.parent_audit.read_bytes()
    if a.extend_in_place:
        assert sha(raw)==V92_AUDIT
        fresh(a,json.loads(raw))
        return
    if a.prepare_only or not all((a.first_parent,a.second_parent,a.source,a.font,a.credit_font)):
        parser.error("old v91-to-v92 verification needs both parent directories, source and fonts")
    assert len({p.resolve() for p in (a.first_parent,a.second_parent,a.first,a.second)})==4
    assert all(not p.exists() for p in (a.first,a.second,a.report)) and sha(raw)==V91_AUDIT
    previous=json.loads(raw)["sha256_by_relative_path"]
    first,second=both(historical,[(old,new,previous,a.source,a.font,a.credit_font) for old,new in
                                  ((a.first_parent,a.first),(a.second_parent,a.second))])
    assert first==second and len(previous)==540
    assert {k for k,v in previous.items() if first.get(k)!=v}==TOP
    assert first["ending-awards.gba"]==previous["current-candidate.gba"]
    assert first["ending-awards.json"]==previous["current-candidate.json"]
    assert all(first[key]==value for key,value in v92_layers().items())
    result=dict(status="PASS",parent_audit=V91_AUDIT,previous_files=len(previous),files_each=len(first),
                final_sha256=first["current-candidate.gba"],pipeline_sha256=sha(Path(production.__file__).read_bytes()),
                stages_sha256=sha(v92.PINS.read_bytes()),sha256_by_relative_path=first)
    save(a.report,result)
    print("PASS",len(first),"files per build",result["final_sha256"],sha(a.report.read_bytes()))


if __name__=="__main__":
    main()

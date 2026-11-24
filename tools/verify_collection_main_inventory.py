"""Run the production collection suffix on both audited v90 parents and compare every artifact."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil

import build_current_candidate as main
import build_collection_native_tail as tail
from verify_id13_main_inventory import inventory

PRIOR_AUDIT = "C75B330AE420A76DC42EC07A82AB040B55DDB830D4AC9F6E4DEC905BAE1C1EEC"


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def create(parent, output, source, originals):
    if inventory(parent) != originals:
        raise ValueError(f"modified v90 input at {parent}")
    shutil.copytree(parent, output)
    (output/"current-candidate.gba").rename(output/"source-english.gba")
    (output/"current-candidate.json").rename(output/"source-english.json")
    tail.build(source, output, main.run, main.require_hash)
    path=output/"build-manifest.json"
    manifest=json.loads(path.read_bytes())
    manifest["layers"]=main.EXPECTED_LAYERS
    tail.update_manifest(manifest)
    path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return inventory(output)


def main_cli():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("first-parent","second-parent","first","second","source","v90-audit","report"):
        parser.add_argument("--"+name,type=Path,required=True)
    a=parser.parse_args()
    paths=[a.first_parent,a.second_parent,a.first,a.second]
    assert len(set(p.resolve() for p in paths))==4 and not any(p.exists() for p in [a.first,a.second,a.report])
    prior=a.v90_audit.read_bytes()
    assert sha(prior)==PRIOR_AUDIT
    old=json.loads(prior)["sha256_by_relative_path"]
    assert old["current-candidate.gba"]==tail.STAGES["source-english.gba"]
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(create,p,out,a.source,old) for p,out in ((a.first_parent,a.first),(a.second_parent,a.second))]
        first,second=[job.result() for job in futures]
    assert first==second
    assert {key for key in old if first.get(key)!=old[key]}=={"current-candidate.gba","current-candidate.json","build-manifest.json"}
    assert first["source-english.json"]==old["current-candidate.json"]
    for key,expected in main.EXPECTED_LAYERS.items():
        assert first[key]==expected
    assert first["current-candidate.json"]==tail.OWNER
    for name,expected in tail.REVIEWS.items():
        assert first["intermediate/collection-native/"+name]==expected
    report=dict(status="COLLECTION_NATIVE_MAIN_TWO_VERIFIED_PARENT_BUILDS",v90_audit_sha256=PRIOR_AUDIT,
                main_sha256=sha(Path(main.__file__).read_bytes()),suffix_sha256=sha(Path(tail.__file__).read_bytes()),
                verifier_sha256=sha(Path(__file__).read_bytes()),files_each=len(first),inherited_unchanged=len(old)-3,
                manifest_layers=len(main.EXPECTED_LAYERS),final_sha256=first["current-candidate.gba"],sha256_by_relative_path=first)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(report["status"],len(first),sha(a.report.read_bytes()))


if __name__=="__main__":
    main_cli()


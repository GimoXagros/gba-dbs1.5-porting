"""Run the two ending reward producers independently on the audited collection cores."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

import build_current_candidate as production
import build_ending_awards_main_tail as awards
from verify_id13_main_inventory import inventory

CORE_AUDIT = "93100E2379EC3609DDB0821E31A8CFAE677BAE7AB5C76D024BE82E4D60D37C8D"


def build(parent, output, source, approved_inventory):
    assert inventory(parent) == approved_inventory, "parent files match the original-backed A887 core"
    shutil.copytree(parent,output)
    awards.build(source,output,production.run,production.require_hash)
    path=output/"build-manifest.json"
    data=json.loads(path.read_bytes())
    data["layers"]=production.EXPECTED_LAYERS
    awards.update_manifest(data)
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    return inventory(output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("first-parent","second-parent","first","second","source","core-audit","report"):
        parser.add_argument("--"+name,type=Path,required=True)
    a=parser.parse_args()
    assert len({p.resolve() for p in [a.first_parent,a.second_parent,a.first,a.second]})==4
    assert not any(p.exists() for p in (a.first,a.second,a.report))
    source_audit=a.core_audit.read_bytes()
    assert awards.sha(source_audit)==CORE_AUDIT
    previous=json.loads(source_audit)["sha256_by_relative_path"]
    with ThreadPoolExecutor(2) as pool:
        jobs=[pool.submit(build,parent,out,a.source,previous) for parent,out in
              ((a.first_parent,a.first),(a.second_parent,a.second))]
        first,second=[job.result() for job in jobs]
    assert first==second
    assert {key for key in previous if first.get(key)!=previous[key]}=={"build-manifest.json","current-candidate.gba","current-candidate.json"}
    assert first["collection-core.gba"]==previous["current-candidate.gba"]
    assert first["collection-core.json"]==previous["current-candidate.json"]
    assert first["current-candidate.json"]==awards.OWNER
    for name,digest in production.EXPECTED_LAYERS.items():
        assert first[name]==digest
    report=dict(status="ENDING_AWARDS_MAIN_TWO_VERIFIED_CORE_BUILDS",core_audit_sha256=CORE_AUDIT,
                primary_sha256=awards.sha(Path(production.__file__).read_bytes()),
                suffix_sha256=awards.sha(Path(awards.__file__).read_bytes()),
                verifier_sha256=awards.sha(Path(__file__).read_bytes()),files_each=len(first),
                inherited_unchanged=len(previous)-3,manifest_layers=len(production.EXPECTED_LAYERS),
                final_sha256=first["current-candidate.gba"],sha256_by_relative_path=first)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(report["status"],len(first),awards.sha(a.report.read_bytes()))


if __name__=="__main__":
    main()


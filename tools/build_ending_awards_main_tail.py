"""Build the source ending reward queue and verify all declared whole-image writes."""
import hashlib
import json

CORE = "A88751B6509BF51D6B83C01F6BAA02D522D0C5E30B276B25B783CF2199204A84"
CORE_OWNER = "744860E09F7B8F4B586BF230B80633ECFCE5FFD35A17B641C9E6028C04680653"
ROSTER = "476E753BC09D8EB3B39F2CB0F6734241233EE7080B4E901AB57C20B603327D08"
ROSTER_OWNER = "27AF52D2CBBD96AF21A2B98D71E28C6762B5FB807D121AB005BEC0E1643333C7"


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def verify_writes(before_path, image_path, owner_path):
    before, image = before_path.read_bytes(), image_path.read_bytes()
    owner=json.loads(owner_path.read_bytes())
    assert owner["input_sha256"]==sha(before) and owner["output_sha256"]==sha(image) and len(image)==len(before)
    spans=sorted((r["offset"],r["offset"]+r["size"],r) for r in owner["writes"])
    assert all(left[1]<=right[0] for left,right in zip(spans,spans[1:]))
    inverse=bytearray(image)
    for start,end,row in spans:
        assert 0<=start<end<=len(image)
        assert sha(before[start:end])==row["before_sha256"] and sha(image[start:end])==row["after_sha256"]
        inverse[start:end]=before[start:end]
    assert inverse==before


def prepare_roster(source, output, run, require_hash):
    core=output/"collection-core.gba"
    core_owner=output/"collection-core.json"
    (output/"current-candidate.gba").replace(core)
    (output/"current-candidate.json").replace(core_owner)
    require_hash(core,CORE,"verified collection core")
    require_hash(core_owner,CORE_OWNER,"collection ownership")
    roster=output/"intermediate"/"ending-roster"
    run("build_mode11_roster_awards.py","--source",source,"--input",core,"--owner",core_owner,"--output",roster)
    require_hash(roster/"component.gba",ROSTER,"two source character reward slots")
    require_hash(roster/"manifest.json",ROSTER_OWNER,"ending roster ownership")
    verify_writes(core,roster/"component.gba",roster/"manifest.json")
    return roster



RANK = "78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924"
OWNER = "0D06FCB9A11A53629FB75B11495043D4A22499E4100153E2FC7EE6B6CDDC4278"
STAGES = {
    "collection-core.gba": CORE,
    "intermediate/ending-roster/component.gba": ROSTER,
    "current-candidate.gba": RANK,
}
ROSTER_QA = "5F22D9EE7302D8ECDC3D44A50842131E8F687A5107A4D1DAE8E7B50E21493929"


def build(source, output, run, require_hash):
    roster=prepare_roster(source,output,run,require_hash)
    work=output/"intermediate"
    check=work/"ending-roster-verification.json"
    run("verify_mode11_roster_awards.py","--source",source,"--native",output/"collection-core.gba",
        "--installed",roster/"component.gba","--owner",roster/"manifest.json","--report",check)
    require_hash(check,ROSTER_QA,"source award queue capacity, portraits and earned data")
    rank=work/"ending-rank"
    run("build_mode11_rank_award.py","--source",source,"--input",roster/"component.gba",
        "--owner",roster/"manifest.json","--output",rank)
    require_hash(rank/"component.gba",RANK,"earned Tamer Tag storage")
    require_hash(rank/"manifest.json",OWNER,"earned Tamer Tag ownership")
    verify_writes(roster/"component.gba",rank/"component.gba",rank/"manifest.json")
    checks=work/"ending-rank-verification.json"
    run("verify_mode11_rank_award.py","--source",source,"--prior",roster/"component.gba",
        "--image",rank/"component.gba","--report",checks)
    require_hash(checks,"DEA4B98D968B795A5E8A93FDD3454F0B7DEA636F8275A8177AD6C3E06ED0ED54",
                 "score, carried tag, refusal and verified CRC device writes")
    (rank/"component.gba").replace(output/"current-candidate.gba")
    (rank/"manifest.json").replace(output/"current-candidate.json")


def update_manifest(manifest):
    details=manifest["collection_and_language"]
    details.update(ending_character_award_slots=2,ending_score_tag_award=True)

"""Build the registered Tamer Tag, VS RECORD and Shoot terminal layers from the English title."""
from pathlib import Path

STAGES = {
    "source-english.gba": "8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869",
    "intermediate/collection-native/ending.gba": "2A7E8296DDD1DB3898CF3484E5849E623066A6249D3F70B090374956213CD083",
    "intermediate/collection-native/storage/component.gba": "D390CA3B9620A2A9F3DAC214F2EC9DD3C8D0D8A91787BA78735AB8AC2E11749F",
    "intermediate/collection-native/viewer/component.gba": "63D7B68138CF7C1EBD96CEE168E1AFCD414A7591EDD9FBD8329A7E64C96F6248",
    "intermediate/collection-native/stats/component.gba": "3CB82DEC80C68FF85199A5BD264D78F3C794A6C522539731550B1A797A06A74C",
    "intermediate/collection-native/vs/component.gba": "F824434CBEE46F3BBFE59DF95038B618C2F534274CC44A59B0FB0B9C477E599B",
    "current-candidate.gba": "A88751B6509BF51D6B83C01F6BAA02D522D0C5E30B276B25B783CF2199204A84",
}
OWNER = "744860E09F7B8F4B586BF230B80633ECFCE5FFD35A17B641C9E6028C04680653"
REVIEWS = {
    "source-primitives.json": "0C5AD911EB9D66881591A4B1A304C96E513FA95235D3E8A069BBE20FDC25E2A3",
    "fc-score.json": "0741125B47A0A89225F139C13FF630A1C00906103FE7901DBC7CC6793C8E01D8",
    "viewer.json": "9A70C41DCCFBD60950A7E1166632C19B2198B8B61F83148FE9E837206E56D51C",
    "stats.json": "E62AFD1810FB6653D259F41F472217264229E9A1E37B934AEB4ECB724575A023",
    "vs.json": "E98B44740DF3FA74ECAD0BF4EAC79CF602D2B80567BFC1F5AA06D786F32F13A6",
    "aux.json": "D5EA9FDD5F8A058ED72998A0C172751B105F84F882D65350512F0A3FE1635924",
}


def build(source: Path, output: Path, run, require_hash):
    base = output / "source-english.gba"
    require_hash(base, STAGES["source-english.gba"], "previous English main")
    work = output / "intermediate" / "collection-native"
    work.mkdir()
    ending = work / "ending.gba"
    storage, viewer, stats, vs, aux = [work / name for name in ("storage","viewer","stats","vs","aux")]
    resources, music = work / "resources", work / "music"
    native = output / "shoot-child-contact.gba"
    run("build_mode11_source_card_selector.py", "--before", base, "--source", source, "--output", ending)
    run("build_mode22_snapshot_storage.py", "--before", ending, "--owner", output / "initial-portrait.json", "--output", storage)
    run("check_mode22_snapshot_storage.py")
    run("build_mode22_resources.py", "--source", source, "--output-dir", resources)
    run("build_mode22_audio_assets.py", "--source", source, "--native", native, "--output-dir", music)
    run("check_mode22_audio_assets.py", "--source", source, "--native", native, "--assets", music, "--report", work / "fc-score.json")
    run("check_mode22_source_primitives.py", "--source", source, "--report", work / "source-primitives.json")
    run("build_mode22_viewer_scene.py", "--source", source, "--input", storage / "component.gba",
        "--owner", storage / "manifest.json", "--resources", resources, "--audio", music, "--output", viewer)
    run("verify_mode22_viewer_scene.py", "--before", storage / "component.gba", "--after", viewer / "component.gba",
        "--owner", viewer / "manifest.json", "--source", source, "--report", work / "viewer.json")
    run("build_mode22_stats_bridge.py", "--input", viewer / "component.gba", "--owner", viewer / "manifest.json", "--output", stats)
    run("verify_mode22_stats_bridge.py", "--baseline", base, "--prior", viewer / "component.gba",
        "--image", stats / "component.gba", "--report", work / "stats.json")
    run("build_vs_record_pages.py", "--source", source, "--input", stats / "component.gba", "--owner", stats / "manifest.json", "--output", vs)
    run("verify_vs_record_pages.py", "--source", source, "--image", vs / "component.gba", "--report", work / "vs.json")
    run("build_shoot_terminal_aux_owner.py", "--source", source, "--input", vs / "component.gba", "--owner", vs / "manifest.json", "--output", aux)
    final = output / "current-candidate.gba"
    (aux / "component.gba").replace(final)
    (aux / "manifest.json").replace(output / "current-candidate.json")
    run("verify_shoot_terminal_aux_visibility.py", vs / "component.gba", final, source, work / "aux.json")
    require_hash(output / "current-candidate.json", OWNER, "combined ownership and full inverse")
    for name, pin in REVIEWS.items():
        require_hash(work / name, pin, name)
    for name, pin in STAGES.items():
        require_hash(output / name, pin, name)


def update_manifest(manifest):
    details = manifest["collection_and_language"]
    details.update(tamer_tag_guarded=False, tamer_tag_mode=22, tamer_tag_snapshot_blocks=list(range(27,34)),
                   vs_record_pages=[[0,1,2],[3,4,5],[6,7,8],[9,10,13],[14,11,12]],
                   mode11_source_selector=255, shoot_terminal_hidden_flag=32)


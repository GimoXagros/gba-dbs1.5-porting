#!/usr/bin/env python3
"""Rebuild the exact current Ver. 1.5 integration candidate from originals."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
CORPUS_SHA256 = "6E648C301837662DCC26613B1D237E55CF356277C3BE13AFA530A45927D7B8E2"
OPENING_P1_CORPUS_SHA256 = (
    "B9F671AB5FE6E66DA7351AFFFAFD7C6E4D07370E84D231E501A6D8C51B52B887"
)
OPENING_LINEAR_VERIFICATION_SHA256 = (
    "15BA39813EE3B54BFA3181251432310E558420D2491A8FF4AAE8825D5DC6FB80"
)
SHOOT_RESOURCE_VERIFICATION_SHA256 = (
    "1047C6163FCC7C40D0F4CED65305108BFE16CD5ED2C9E3DF84ADA757AC504E3F"
)
SHOOT_AUDIO_LINEAGE_SHA256 = (
    "0CD28C17EB6DC3F1FE88F0FB755910434EC0B05DD06AD2F164A078BBEE60997E"
)
SHOOT_INITIALIZER_RESOURCE_SHA256 = (
    "4367C6588F904C282DD857E37CC6F67AC9B8E5DAB8FA8D222239655D7522C1C5"
)
DIRECT_P1_COMMERCIAL_ORACLE_SHA256 = (
    "21B9DF5B7248E069FF4AC750C34305D42B6974FE5141C667B31A231B2E19D82B"
)
SHOOT_INITIALIZER_P1_VERIFICATION_SHA256 = (
    "A435A75BA9D68D4D937125F3B0523BE54980A21D58EBE86E137A665B1DA3CBAD"
)
SHOOT_INITIALIZER_RESOURCE_INTEGRATION_VERIFICATION_SHA256 = (
    "7114A9C7B8CA51F8C52254EB03C3771F90B0CBB63B2D19D3D9B50ABA34A3576B"
)
SHOOT_CHILD_VERIFICATION_SHA256 = (
    "ACA1CE4BABEC56324AA5F06D216F462DB50FD7F3128FF7BD9C233321D8058F05"
)
SHOOT_CE_SOUND_VERIFICATION_SHA256 = (
    "98EB32D4CA01A8AF1F824D1FAB6E88E2F735CB620DE012D819182498D72EC748"
)
SHOOT_PARENT_VERIFICATION_SHA256 = (
    "3989E33CD893742F9DD116D7050D9F33071763A04D9A174321EEC0A723755D13"
)

EXPECTED_ASSETS = {
    "id12-base.bin": "129991FB37E43FFE10DADE20E8552706BB2C594AA20D8253F35D542B01A8E0CB",
    "id13-base.bin": "740D81D7F0AA793AB838ACD65C955CA67901A7CBCA2ABDBCF4343B41D1DA4F34",
    "id14-base.bin": "65D9FBE7206A511C95C9984FFF6A44CE9EDBF1E458B78EDF78FCAC5E28A8ACC3",
    "character-palettes.bin": "7A3FA731080DFA913D4552AF3B9AD9E094CFB1F583DF47222AB135FF3557161A",
    "new-base-p4.bin": "0EF3E00BCC746928DCA58D7B8DBF771377C1CC48EB77CF62F6A89C8289B0C365",
    "new-base-p1.bin": "1945BEB38A3C0DF32315151B2E932A3F92DF48EF3AC59522D7459ADE47465E59",
    "selection-portraits.bin": "6E56A118274A4C07D9B5E9923DA7227B2B8823A1720FC0C6C056312F108B9067",
    "vs-presentation.bin": "2D212622DB36E3D86281768F8C3438D394451FA275D519AA32B97FEE697D2856",
    "character-physics.bin": "1F632B750D33E68C2D3265A2AB35676CD22145F716800784D13775A23B214600",
    "vs-character-events.bin": "2226A35FFA64F6BE0DF610D6600754C4C31B74D29A4D1274DA1C81640EE630A5",
    "evolution-p0.bin": "7DAED3DFC07460C5CE2CA6D377BCEA9DA8892E846BF8ED6AC4E36E8500516DBD",
    "evolution-p1.bin": "58E01C289E3454F95312A35AF657F8606EB994FF3077534C2845F3CDDFC3FECD",
    "evolution-p4.bin": "518337CCB2520572D3F98E962119B90D889147E50E9EA9EAFB40653963D94E2B",
    "zeed-boss.bin": "57E7393D51163A537E705D0F05EE203357CFF9922B23C47FBDC95B32785EE8BC",
}
EXPECTED_STAGE_ASSETS = {
    "stage-impmon-maps.bin": "61E0039B4D05EE306CDD44081F5723709DA12165FF67CB6E88BEAC8A80940C73",
    "stage-impmon-palette.bin": "7ABBFF3442FFD4705CBC96AC7C80042792AF015AE414379C5B9C50B55866EA6C",
    "stage-impmon-tiles.bin": "9EA691F13854BD0FCCF63D02CCE42AD9228B36655A18F2DBF5032BF301352916",
    "stage-shoot-maps.bin": "4898B4B0B2CB2F32F01CB3D86F4B2F51BD87564A0DDA7B3F2AB79EAB43206225",
    "stage-shoot-palette.bin": "1BDFEB85B8B7C3B7428653AE9B767E8A50EFAA72225EF4A48DE75793375F8198",
    "stage-shoot-tiles.bin": "EC647CB7926256F09F53C91ECBEAFA5FEE314EE24687321D9D1DE233A3AC68F9",
    "stage-train-maps.bin": "4C0E00946A60E3F9A11A104D92454396B74E8024AAA96F358D7886F6073F67AC",
    "stage-train-palette.bin": "5C11E1F6613C02B6C1860006212B3DE6484EBB48F1FE40D5EEBAD1032C4D2349",
    "stage-train-tiles.bin": "E10CE7D866C9CB6555788C1AFC490F83222AF6025B7D912FA0281FD0D4F77A26",
    "stage-waterfall-maps.bin": "8BD70A2DF6835024044F4182A804AB282BDB06B172B9340BCB64BDE335E28D7E",
    "stage-waterfall-palette.bin": "0D1BD11C34F9740A5DB031B24E7050354C91CE4E458372EBA692E6A8C4A104F1",
    "stage-waterfall-tiles.bin": "413FDA31AA6494F3AE6B4104AA03C48E351CBB377D239D10800FA10604027330",
}
EXPECTED_OPENING_ASSETS = {
    "opening-p0.bin": "2F085D49410AFAEA4A5AC9EEF7ECC806CFF6E8095FFAA8305EC801A551829151",
    "opening-presentation.json": "32F3ED03234C65C88ED33A99562A9C5F0E62246D31A0FBA74BA7E5DFEF167278",
}
EXPECTED_SHOOT_ASSETS = {
    "shoot-spawn-p1.bin": "6E854C5F2138D74B9860843DF8DBC3144AEB71CB04BF5F1875B0E73F26DB4E78",
    "shoot-spawn-p0.bin": "023A9E47227DC88431A6EE129F40D79944A3173E365DF0B10F615C6D7738D6B8",
    "shoot-spawn-p2.bin": "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C",
    "shoot-rule-resources.json": "8843C960221876323FF16E72587AC49B37B69FEF22A2128E81AA5035357E8246",
    "shoot-initializer-p1.bin": "778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2",
    "shoot-initializer-p1.json": "D5577CA88BA017249E41CBEF8E8D2CE89FAEFAE29F6594C2F11B1A8514515503",
    "shoot-init-active-p0.bin": "04F248F48F22DC66BEB965ADBCB72DDA271534A5BE9A8EB0B5F04CB373BD97BB",
    "shoot-init-rules-p0.bin": "C739645446A1802F937551F845327D2F87B861B6ABE8DDA02EA7D91B8A24CB91",
    "shoot-init-extra-6d-p0.bin": "D17DAC9D4464BF0E8D1577F4C98463B15CAC5F53D043F40DE61BC70851BC159B",
    "shoot-init-extra-137-p0.bin": "716C3A7042A4DD9A7D6B9C12F172D08693DB264AE99D7AEBDFD886BC92CE0B62",
    "shoot-init-extra-91-p0.bin": "7EFAC4D8ADF7A00450DBE2603187C4A3EF556FBC252BAE210D911934AC979214",
    "shoot-init-rules-p2.bin": "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD",
    "shoot-init-extra-slot5-p2.bin": "B5652748382A44ADDEB2BB191FFA880D46D6721CEA54CACF15D7B0C51729A4A1",
    "shoot-initializer-resources.json": "F2051289A9F0A1A3043C495EFF15DBC896F73286BC01E5C4850808FE03197CD0",
}
EXPECTED_LAYERS = {
    "base.gba": "5FE62385736851014C62E8F68B5D8F1583230DE2A30648CE893E3A45440B4ECA",
    "stage.gba": "FA0A48EC933AB9A2BD8960A61D0BE6F07CD15E2FC0B2037917595BDE154DACED",
    "progression.gba": "6D18B67E80C85429B20468449EB4024D4A29C50FC73A133163D028B02408D623",
    "boss.gba": "1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291",
    "opening-choice.gba": "33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1",
    "opening-linear.gba": "9E3D495A3E07F2A9A6ECCF3C07E446036AD027B2A32666DD5A5984879BA6AA5F",
    "shoot-resources.gba": "4028AB75706FDE162E7F247B2AD52CAB20E9B30E487C306B70EE1E1F38E2F45C",
    "shoot-child.gba": "35B2F717A96573B0823E43433A547B5398CC13129DAEECED6646153FC69F5492",
    "shoot-ce.gba": "9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B",
    "shoot-parent.gba": "B192AC03F75FB1B55B3BCB3BA6363836EDDFCBBAC8379DAF6D9DAB08B9AD2E06",
    "current-candidate.gba": "AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require_hash(path: pathlib.Path, expected: str, label: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def run(tool: str, *arguments: object) -> None:
    command = [sys.executable, str(ROOT / "tools" / tool), *(str(value) for value in arguments)]
    print(f"[build] {tool}")
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path, help="USA GBA original")
    parser.add_argument("wsc10", type=pathlib.Path, help="WonderSwan Color retail 1.0 original")
    parser.add_argument("wsc15", type=pathlib.Path, help="WonderSwan Color Ver. 1.5 original")
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()

    require_hash(args.gba, GBA_SHA256, "USA GBA original")
    require_hash(args.wsc10, WSC10_SHA256, "WSC 1.0 original")
    require_hash(args.wsc15, WSC15_SHA256, "WSC Ver. 1.5 original")

    output = args.output_dir.resolve()
    assets = output / "converted-assets"
    stages = output / "stage-assets"
    opening_assets = output / "opening-assets"
    shoot_assets = output / "shoot-assets"
    intermediate = output / "intermediate"
    for directory in (output, assets, stages, opening_assets, shoot_assets, intermediate):
        directory.mkdir(parents=True, exist_ok=True)

    corpus = intermediate / "p4-base-conversion-corpus.json"
    run("analyze_p4_conversion.py", args.gba, args.wsc10, "--output", corpus)
    require_hash(corpus, CORPUS_SHA256, "P4 conversion corpus")
    opening_p1_corpus = intermediate / "opening-p1-conversion-corpus.json"
    run(
        "analyze_p1_conversion.py", args.gba, args.wsc10,
        "--wsc-table", "0x390300", "--gba-table", "0x0D42A0",
        "--records", 11, "--output", opening_p1_corpus,
    )
    require_hash(
        opening_p1_corpus,
        OPENING_P1_CORPUS_SHA256,
        "opening P1 conversion corpus",
    )
    shoot_audio_lineage = intermediate / "shoot-audio-lineage.json"
    run(
        "analyze_shoot_audio_lineage.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_audio_lineage,
    )
    require_hash(
        shoot_audio_lineage,
        SHOOT_AUDIO_LINEAGE_SHA256,
        "Shoot audio request lineage",
    )
    shoot_initializer_resources = intermediate / "shoot-initializer-resources.json"
    run(
        "analyze_shoot_initializer_resources.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_initializer_resources,
    )
    require_hash(
        shoot_initializer_resources,
        SHOOT_INITIALIZER_RESOURCE_SHA256,
        "Shoot initializer resource boundary",
    )
    direct_p1_oracle = intermediate / "direct-p1-commercial-oracle.json"
    run(
        "analyze_direct_p1_commercial_oracle.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        direct_p1_oracle,
    )
    require_hash(
        direct_p1_oracle,
        DIRECT_P1_COMMERCIAL_ORACLE_SHA256,
        "direct P1 commercial oracle",
    )

    animation_specs = (
        ("id12-base", "0x29B8A0", "0x448000"),
        ("id13-base", "0x352AB0", "0x400000"),
        ("id14-base", "0x32A5E0", "0x420AC0"),
    )
    for name, header, target in animation_specs:
        run(
            "convert_wsc_animation_asset.py", args.wsc15, assets / f"{name}.bin",
            "--header", header, "--target-header", target,
            "--manifest", assets / f"{name}.json",
        )

    run("build_character_palette_assets.py", args.wsc15, assets / "character-palettes.bin",
        "--manifest", assets / "character-palettes.json")
    run("build_new_base_p4_assets.py", corpus, args.wsc15, assets / "new-base-p4.bin",
        "--manifest", assets / "new-base-p4.json")
    run("build_new_base_p1_assets.py", args.wsc15, assets / "new-base-p1.bin",
        "--gba", args.gba, "--manifest", assets / "new-base-p1.json")
    run("build_selection_portrait_assets.py", args.wsc15, assets / "selection-portraits.bin",
        "--manifest", assets / "selection-portraits.json")
    run("build_vs_presentation_assets.py", args.gba, args.wsc15, assets / "vs-presentation.bin",
        "--manifest", assets / "vs-presentation.json")
    run("build_character_physics_assets.py", args.gba, args.wsc15,
        assets / "character-physics.bin", "--manifest", assets / "character-physics.json")
    run("build_vs_character_event_assets.py", args.gba, assets / "vs-character-events.bin",
        "--manifest", assets / "vs-character-events.json")
    run("build_evolution_p0_assets.py", args.wsc15, assets / "evolution-p0.bin",
        "--manifest", assets / "evolution-p0.json")
    run("build_evolution_p1_assets.py", args.wsc15, assets / "evolution-p1.bin",
        "--gba", args.gba, "--manifest", assets / "evolution-p1.json")
    run("build_evolution_p4_assets.py", corpus, args.wsc15, assets / "evolution-p4.bin",
        "--manifest", assets / "evolution-p4.json")
    run("build_zeed_boss_assets.py", args.gba, args.wsc15, assets / "zeed-boss.bin",
        "--manifest", assets / "zeed-boss.json")
    run(
        "build_opening_presentation_assets.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        opening_p1_corpus,
        opening_assets,
    )
    run(
        "build_shoot_rule_resources.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        shoot_assets,
    )
    run(
        "build_shoot_initializer_p1_assets.py",
        args.wsc15,
        shoot_assets / "shoot-initializer-p1.bin",
        "--manifest",
        shoot_assets / "shoot-initializer-p1.json",
    )
    run(
        "build_shoot_initializer_resource_assets.py",
        args.gba,
        args.wsc15,
        shoot_assets,
    )

    for name, expected in EXPECTED_ASSETS.items():
        require_hash(assets / name, expected, name)
    for name, expected in EXPECTED_OPENING_ASSETS.items():
        require_hash(opening_assets / name, expected, name)
    for name, expected in EXPECTED_SHOOT_ASSETS.items():
        require_hash(shoot_assets / name, expected, name)

    run("build_stage_assets.py", args.wsc15, stages)
    for name, expected in EXPECTED_STAGE_ASSETS.items():
        require_hash(stages / name, expected, name)

    base = output / "base.gba"
    stage = output / "stage.gba"
    progression = output / "progression.gba"
    boss = output / "boss.gba"
    opening_choice = output / "opening-choice.gba"
    opening_linear = output / "opening-linear.gba"
    shoot_resources = output / "shoot-resources.gba"
    shoot_child = output / "shoot-child.gba"
    shoot_ce = output / "shoot-ce.gba"
    shoot_parent = output / "shoot-parent.gba"
    candidate = output / "current-candidate.gba"
    run("build_base_roster_probe.py", args.gba, assets, base,
        "--manifest", output / "base.json")
    run("build_stage_integration.py", base, stages, stage, "--wsc15", args.wsc15,
        "--manifest", output / "stage.json")
    run("build_progression_integration.py", stage, progression,
        "--manifest", output / "progression.json")
    run("build_boss_integration.py", progression, assets, boss,
        "--manifest", output / "boss.json")
    run("build_opening_integration.py", boss, args.wsc15, opening_choice,
        "--asset-dir", opening_assets,
        "--manifest", output / "opening-choice.json")
    run(
        "build_opening_linear_integration.py",
        opening_choice,
        args.wsc15,
        opening_linear,
        "--manifest",
        output / "opening-linear.json",
    )
    run(
        "build_shoot_resource_integration.py",
        opening_linear,
        shoot_assets,
        shoot_resources,
        "--manifest",
        output / "shoot-resources.json",
    )
    run(
        "build_shoot_child_integration.py",
        shoot_resources,
        args.gba,
        args.wsc15,
        shoot_child,
        "--manifest",
        output / "shoot-child.json",
    )
    run(
        "build_shoot_ce_sound_integration.py",
        shoot_child,
        args.gba,
        args.wsc15,
        shoot_ce,
        "--manifest",
        output / "shoot-ce.json",
    )
    run(
        "build_shoot_parent_integration.py",
        shoot_ce,
        args.gba,
        args.wsc15,
        shoot_parent,
        "--manifest",
        output / "shoot-parent.json",
    )
    run(
        "build_shoot_initializer_resource_integration.py",
        shoot_parent,
        shoot_assets,
        candidate,
        "--manifest",
        output / "current-candidate.json",
    )
    for name, expected in EXPECTED_LAYERS.items():
        require_hash(output / name, expected, name)
    opening_linear_verification = intermediate / "opening-linear-verification.json"
    run(
        "analyze_opening_linear_integration.py",
        opening_choice,
        opening_linear,
        args.wsc15,
        "--output",
        opening_linear_verification,
    )
    require_hash(
        opening_linear_verification,
        OPENING_LINEAR_VERIFICATION_SHA256,
        "opening linear integration verification",
    )
    shoot_resource_verification = intermediate / "shoot-resource-verification.json"
    run(
        "verify_shoot_resource_integration.py",
        opening_linear,
        shoot_resources,
        args.wsc15,
        "--output",
        shoot_resource_verification,
    )
    require_hash(
        shoot_resource_verification,
        SHOOT_RESOURCE_VERIFICATION_SHA256,
        "Shoot resource integration verification",
    )
    shoot_child_verification = intermediate / "shoot-child-verification.json"
    run(
        "verify_shoot_child_integration.py",
        shoot_resources,
        shoot_child,
        args.gba,
        args.wsc15,
        "--output",
        shoot_child_verification,
    )
    require_hash(
        shoot_child_verification,
        SHOOT_CHILD_VERIFICATION_SHA256,
        "Shoot child integration verification",
    )
    shoot_ce_sound_verification = intermediate / "shoot-ce-sound-verification.json"
    run(
        "verify_shoot_ce_sound_integration.py",
        shoot_child,
        shoot_ce,
        args.gba,
        args.wsc15,
        "--output",
        shoot_ce_sound_verification,
    )
    require_hash(
        shoot_ce_sound_verification,
        SHOOT_CE_SOUND_VERIFICATION_SHA256,
        "Shoot CE sound integration verification",
    )
    shoot_parent_verification = intermediate / "shoot-parent-verification.json"
    run(
        "verify_shoot_parent_integration.py",
        shoot_ce,
        shoot_parent,
        args.gba,
        args.wsc15,
        "--output",
        shoot_parent_verification,
    )
    require_hash(
        shoot_parent_verification,
        SHOOT_PARENT_VERIFICATION_SHA256,
        "Shoot parent integration verification",
    )
    shoot_initializer_resource_integration_verification = (
        intermediate / "shoot-initializer-resource-integration-verification.json"
    )
    run(
        "verify_shoot_initializer_resource_integration.py",
        shoot_parent,
        candidate,
        shoot_assets,
        "--output",
        shoot_initializer_resource_integration_verification,
    )
    require_hash(
        shoot_initializer_resource_integration_verification,
        SHOOT_INITIALIZER_RESOURCE_INTEGRATION_VERIFICATION_SHA256,
        "Shoot initializer resource integration independent verification",
    )
    shoot_initializer_p1_verification = intermediate / "shoot-initializer-p1-verification.json"
    run(
        "verify_shoot_initializer_p1_assets.py",
        args.wsc15,
        shoot_assets / "shoot-initializer-p1.bin",
        "--output",
        shoot_initializer_p1_verification,
    )
    require_hash(
        shoot_initializer_p1_verification,
        SHOOT_INITIALIZER_P1_VERIFICATION_SHA256,
        "Shoot initializer P1 independent verification",
    )

    manifest = {
        "schema": 1,
        "kind": "reproducible-current-candidate-build",
        "claim_scope": (
            "exact current integration candidate including the five-state "
            "opening choice path, selector records 11..14, the four added "
            "linear opening callbacks, the Shoot child resource layer, and the "
            "resident 9229->94C1->9570->9617 child generator/callback family with "
            "the exact-payload-derived A7-to-0x4A sound request, plus the bounded "
            "Ver. 1.5-only CE-to-GBA-0x5B pitch/timing/volume-decay reconstruction "
            "and internally connected 9083->90F3->912A->91AB->91EF parent chain, "
            "plus the independently verified resource-only placement of all converted "
            "7168 initializer P1/P0/P2 assets; "
            "external controller 9908/9A1B entry, audible timbre parity, "
            "playback and runtime validation, "
            "remaining Ver. 1.5 content completion, and final QA excluded"
        ),
        "sources": {
            "gba_usa_sha256": GBA_SHA256,
            "wsc_10_sha256": WSC10_SHA256,
            "wsc_15_sha256": WSC15_SHA256,
        },
        "intermediate": {
            "p4_base_conversion_corpus_sha256": CORPUS_SHA256,
            "opening_p1_conversion_corpus_sha256": OPENING_P1_CORPUS_SHA256,
            "opening_linear_verification_sha256": OPENING_LINEAR_VERIFICATION_SHA256,
            "shoot_resource_verification_sha256": SHOOT_RESOURCE_VERIFICATION_SHA256,
            "shoot_audio_lineage_sha256": SHOOT_AUDIO_LINEAGE_SHA256,
            "shoot_initializer_resource_sha256": SHOOT_INITIALIZER_RESOURCE_SHA256,
            "direct_p1_commercial_oracle_sha256": DIRECT_P1_COMMERCIAL_ORACLE_SHA256,
            "shoot_initializer_p1_verification_sha256": SHOOT_INITIALIZER_P1_VERIFICATION_SHA256,
            "shoot_initializer_resource_integration_verification_sha256": (
                SHOOT_INITIALIZER_RESOURCE_INTEGRATION_VERIFICATION_SHA256
            ),
            "shoot_child_verification_sha256": SHOOT_CHILD_VERIFICATION_SHA256,
            "shoot_ce_sound_verification_sha256": SHOOT_CE_SOUND_VERIFICATION_SHA256,
            "shoot_parent_verification_sha256": SHOOT_PARENT_VERIFICATION_SHA256,
        },
        "assets": EXPECTED_ASSETS,
        "stage_assets": EXPECTED_STAGE_ASSETS,
        "opening_assets": EXPECTED_OPENING_ASSETS,
        "shoot_assets": EXPECTED_SHOOT_ASSETS,
        "layers": EXPECTED_LAYERS,
        "output": "current-candidate.gba",
    }
    (output / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[build] PASS {candidate} {EXPECTED_LAYERS['current-candidate.gba']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

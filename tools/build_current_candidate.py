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
SHOOT_D2_ANALYSIS_SHA256 = (
    "ECB4780B4EC38D44B6F5FC0B11D7E45A7BF0D30214474D5A45778F91CC231E0B"
)
SHOOT_D2_VERIFICATION_SHA256 = (
    "A636C763D0AF93DA8E47D9BC67DDBD8F1895D1A4BF95C1AE0029CF2A3C79B473"
)
SHOOT_CE_STEREO_VERIFICATION_SHA256 = (
    "A087DCD31E27A17615AEB897BD037F090F69C699D1EB2C6384674D4B2F0A0ABA"
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
SHOOT_AUX_OBJECT_LIFETIME_SHA256 = (
    "8F7E38A3C835503B5F1598CD9CD2468A7E229A1B483307F8A918D5ED10097F50"
)
SHOOT_AUX_OBJECT_VERIFICATION_SHA256 = (
    "BC3B8E04C681C6DB7EF3A3A9A1BDF02B320E7478590877E0C5513C3327610228"
)
SHOOT_UPPER_STATE_GRAPH_SHA256 = (
    "55B6AD9E1FA162C67AE6B14A125F6D02E257506F80FB16786D54B678B49C75A0"
)
SHOOT_UPPER_STATE_VERIFICATION_SHA256 = (
    "504A375A5A4F98A6F92975D06044FC46791481915E3A7FF528FA21ECF38353EE"
)
SHOOT_PLAYER_BINDING_VERIFICATION_SHA256 = (
    "8427FBAD3FDD00EB15CCDF69D55BD39E0341E21629B86CD2B143AFFCC07F9930"
)
SHOOT_FAR_TILE_VERIFICATION_SHA256 = (
    "25C5C3F6F96B8335ADA627D199630264D361CECD3C70342D0646E384E802105C"
)
SHOOT_OTHER_PLAYER_VERIFICATION_SHA256 = (
    "6F0B0191F2CC84961908C512F1CEA016FA72EBD9CE5E6A4876940630915B3F20"
)
SHOOT_TAIL_RESOURCE_VERIFICATION_SHA256 = (
    "56A41B0B88EA9BD49402F986A0CAEA63CF24C1156D019B4B99BCEB739CAFB87C"
)
SHOOT_RULES_VERIFICATION_SHA256 = "7F4DFF7CB239B0C90A80A2168FC1D9BF5F9F05605E7953084A8203C2C8FC7678"
SHOOT_PALETTE_VERIFICATION_SHA256 = "7A6A9632EEDA2A98498405A2EAD2F78A27AB4BC6CEF142CEC9CBDF1FD9B96AAB"
SHOOT_PALETTE_OWNERSHIP_SHA256 = "2F5FA817B464F13A7606388F9650549A41C801A8FEB439A4FE51A2430A3048ED"
SHOOT_INITIALIZER_COMPONENT_VERIFICATION_SHA256 = "F2BC89B285C7051DCE8C4A1680344A426CA5201B36F15764302DEB069D184C3E"

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
    "character-physics-current.bin": "93C735C0A3EE3A9DF09243246BE38129B97AF6A88F5C4546C0229FB7339753C3",
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
    "shoot-initializer-resources.gba": "AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E",
    "shoot-d2.gba": "7BB890FEC50BBAB796B5F94FE7761EAE9C4A284BB8E3CC9FA75A12FD20FB2264",
    "shoot-ce-stereo.gba": "000683972B02F1E58369517F6AC32B270854ED2BBA4FC292BCA54E9E9700FBEB",
    "shoot-aux-object.gba": "C8C3AF5DABBE7CCE9F0D124DDEEF3CD6348FCDB085416DBA5E78C65DD5BFB3B4",
    "shoot-upper-state.gba": "034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC",
    "shoot-player-binding.gba": "ECE3D7E6428A81C93767FC72F79BC8EA5BD7E243E814FBEDCC6FFB079CEFDFC0",
    "shoot-far-tiles.gba": "11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E",
    "shoot-other-player.gba": "93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E",
    "shoot-tail-resources.gba": "C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1",
    "shoot-rules.gba": "FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C",
    "shoot-palette.gba": "2008EC0520554F09C84351220B8A30931E1E636A7CEEE9BF3CBBB12C28C1B5AE",
    "current-candidate.gba": "726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284",
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
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SystemExit("output directory must be new or empty; existing builds are preserved")
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
    shoot_d2_analysis = intermediate / "shoot-d2-analysis.json"
    run(
        "analyze_shoot_d2_sound.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_d2_analysis,
    )
    require_hash(
        shoot_d2_analysis,
        SHOOT_D2_ANALYSIS_SHA256,
        "Shoot D2 sound boundary",
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
    shoot_aux_object_lifetime = intermediate / "shoot-aux-object-lifetime.json"
    run(
        "analyze_shoot_aux_object_lifetime.py",
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_aux_object_lifetime,
    )
    require_hash(
        shoot_aux_object_lifetime,
        SHOOT_AUX_OBJECT_LIFETIME_SHA256,
        "Shoot auxiliary-object lifetime and native lineage",
    )
    shoot_upper_state_graph = intermediate / "shoot-upper-state-graph.json"
    run(
        "analyze_shoot_upper_state_graph.py",
        args.wsc15,
        args.gba,
        "--output",
        shoot_upper_state_graph,
    )
    require_hash(
        shoot_upper_state_graph,
        SHOOT_UPPER_STATE_GRAPH_SHA256,
        "Shoot upper-state callback graph",
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
    shoot_palette_ownership = intermediate / "shoot-palette-ownership.json"
    run(
        "analyze_shoot_palette_ownership.py", args.gba, args.wsc10, args.wsc15,
        "--output", shoot_palette_ownership,
    )
    require_hash(shoot_palette_ownership, SHOOT_PALETTE_OWNERSHIP_SHA256,
                 "Shoot palette representation and unresolved ownership boundary")

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
        assets / "character-physics.bin", "--manifest", assets / "character-physics.json",
        "--legacy-v48-layout")
    run("build_character_physics_assets.py", args.gba, args.wsc15,
        assets / "character-physics-current.bin", "--manifest", assets / "character-physics-current.json")
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
    shoot_initializer_resources_layer = output / "shoot-initializer-resources.gba"
    shoot_d2 = output / "shoot-d2.gba"
    shoot_ce_stereo = output / "shoot-ce-stereo.gba"
    shoot_aux_object = output / "shoot-aux-object.gba"
    shoot_upper_state = output / "shoot-upper-state.gba"
    shoot_player_binding = output / "shoot-player-binding.gba"
    shoot_far_tiles = output / "shoot-far-tiles.gba"
    shoot_other_player = output / "shoot-other-player.gba"
    shoot_tail_resources = output / "shoot-tail-resources.gba"
    shoot_rules = output / "shoot-rules.gba"
    shoot_palette = output / "shoot-palette.gba"
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
        shoot_initializer_resources_layer,
        "--manifest",
        output / "shoot-initializer-resources.json",
    )
    run(
        "build_shoot_d2_sound_integration.py",
        shoot_initializer_resources_layer,
        args.gba,
        args.wsc10,
        args.wsc15,
        shoot_d2,
        "--manifest",
        output / "shoot-d2.json",
    )
    run(
        "build_shoot_ce_stereo_correction.py",
        shoot_d2,
        args.wsc15,
        shoot_ce_stereo,
        "--manifest",
        output / "shoot-ce-stereo.json",
    )
    run(
        "build_shoot_aux_object_integration.py",
        shoot_ce_stereo,
        args.gba,
        args.wsc10,
        args.wsc15,
        shoot_aux_object,
        "--manifest",
        output / "shoot-aux-object.json",
    )
    run(
        "build_shoot_upper_state_integration.py",
        shoot_aux_object,
        args.gba,
        args.wsc15,
        shoot_upper_state,
        "--manifest",
        output / "shoot-upper-state.json",
    )
    run(
        "build_shoot_player_binding.py",
        shoot_upper_state,
        args.gba,
        args.wsc10,
        args.wsc15,
        shoot_player_binding,
        "--manifest",
        output / "shoot-player-binding.json",
    )
    run(
        "build_shoot_far_tile_repair.py",
        shoot_player_binding,
        args.gba,
        args.wsc10,
        args.wsc15,
        shoot_far_tiles,
        "--manifest",
        output / "shoot-far-tiles.json",
    )
    run(
        "build_shoot_other_player_binding.py",
        shoot_far_tiles,
        args.gba,
        args.wsc15,
        shoot_other_player,
        "--manifest",
        output / "shoot-other-player.json",
    )
    run(
        "build_shoot_tail_resources.py",
        shoot_other_player,
        args.gba,
        args.wsc15,
        shoot_tail_resources,
        "--manifest",
        output / "shoot-tail-resources.json",
    )
    run(
        "build_shoot_rules.py", shoot_tail_resources, args.gba, args.wsc10, args.wsc15,
        shoot_rules, "--manifest", output / "shoot-rules.json",
    )
    run(
        "build_shoot_palette_transition.py", shoot_rules, args.gba, args.wsc15,
        shoot_palette, "--manifest", output / "shoot-palette.json",
    )
    run(
        "build_shoot_initializer.py", shoot_palette, args.gba, args.wsc10, args.wsc15,
        candidate,
        "--manifest",
        output / "current-candidate.json",
    )
    for name, expected in EXPECTED_LAYERS.items():
        require_hash(output / name, expected, name)
    current_physics = (assets / "character-physics-current.bin").read_bytes()
    if candidate.read_bytes()[0x485000:0x485000 + len(current_physics)] != current_physics:
        raise SystemExit("final physics pointers/payloads differ from the corrected asset builder")
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
        shoot_initializer_resources_layer,
        shoot_assets,
        "--output",
        shoot_initializer_resource_integration_verification,
    )
    require_hash(
        shoot_initializer_resource_integration_verification,
        SHOOT_INITIALIZER_RESOURCE_INTEGRATION_VERIFICATION_SHA256,
        "Shoot initializer resource integration independent verification",
    )
    shoot_d2_verification = intermediate / "shoot-d2-verification.json"
    run(
        "verify_shoot_d2_sound_integration.py",
        shoot_initializer_resources_layer,
        shoot_d2,
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_d2_verification,
    )
    require_hash(
        shoot_d2_verification,
        SHOOT_D2_VERIFICATION_SHA256,
        "Shoot D2 sound integration independent verification",
    )
    shoot_ce_stereo_verification = intermediate / "shoot-ce-stereo-verification.json"
    run(
        "verify_shoot_ce_stereo_correction.py",
        shoot_d2,
        shoot_ce_stereo,
        args.wsc15,
        "--output",
        shoot_ce_stereo_verification,
    )
    require_hash(
        shoot_ce_stereo_verification,
        SHOOT_CE_STEREO_VERIFICATION_SHA256,
        "Shoot CE stereo correction independent verification",
    )
    shoot_aux_object_verification = intermediate / "shoot-aux-object-verification.json"
    run(
        "verify_shoot_aux_object_integration.py",
        shoot_ce_stereo,
        shoot_aux_object,
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_aux_object_verification,
    )
    require_hash(
        shoot_aux_object_verification,
        SHOOT_AUX_OBJECT_VERIFICATION_SHA256,
        "Shoot auxiliary-object integration independent verification",
    )
    shoot_upper_state_verification = intermediate / "shoot-upper-state-verification.json"
    run(
        "verify_shoot_upper_state_integration.py",
        shoot_aux_object,
        shoot_upper_state,
        args.gba,
        args.wsc15,
        "--output",
        shoot_upper_state_verification,
    )
    require_hash(
        shoot_upper_state_verification,
        SHOOT_UPPER_STATE_VERIFICATION_SHA256,
        "Shoot upper-state integration independent verification",
    )
    shoot_player_binding_verification = intermediate / "shoot-player-binding-verification.json"
    run(
        "verify_shoot_player_binding.py",
        shoot_upper_state,
        shoot_player_binding,
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_player_binding_verification,
    )
    require_hash(
        shoot_player_binding_verification,
        SHOOT_PLAYER_BINDING_VERIFICATION_SHA256,
        "Shoot constructor-consumer and player-binding verification",
    )
    shoot_far_tile_verification = intermediate / "shoot-far-tile-verification.json"
    run(
        "verify_shoot_far_tile_repair.py",
        shoot_player_binding,
        shoot_far_tiles,
        args.gba,
        args.wsc10,
        args.wsc15,
        "--output",
        shoot_far_tile_verification,
    )
    require_hash(
        shoot_far_tile_verification,
        SHOOT_FAR_TILE_VERIFICATION_SHA256,
        "Shoot source-segment/descriptor/pixel repair verification",
    )
    shoot_other_player_verification = intermediate / "shoot-other-player-verification.json"
    run(
        "verify_shoot_other_player_binding.py",
        shoot_far_tiles,
        shoot_other_player,
        args.gba,
        args.wsc15,
        "--output",
        shoot_other_player_verification,
    )
    require_hash(
        shoot_other_player_verification,
        SHOOT_OTHER_PLAYER_VERIFICATION_SHA256,
        "Shoot other-player/native-physics consumer verification",
    )
    shoot_tail_resource_verification = intermediate / "shoot-tail-resource-verification.json"
    run(
        "verify_shoot_tail_resources.py",
        shoot_other_player,
        shoot_tail_resources,
        args.gba,
        args.wsc15,
        "--output",
        shoot_tail_resource_verification,
    )
    require_hash(
        shoot_tail_resource_verification,
        SHOOT_TAIL_RESOURCE_VERIFICATION_SHA256,
        "Shoot tail resource/actual HUD and OBJ palette consumer verification",
    )
    shoot_rules_verification = intermediate / "shoot-rules-verification.json"
    run(
        "verify_shoot_rules.py", shoot_tail_resources, shoot_rules, args.gba, args.wsc10,
        args.wsc15, "--output", shoot_rules_verification,
    )
    require_hash(shoot_rules_verification, SHOOT_RULES_VERIFICATION_SHA256, "Shoot controller components")
    shoot_palette_verification = intermediate / "shoot-palette-verification.json"
    run(
        "verify_shoot_palette_transition.py", shoot_rules, shoot_palette, args.gba, args.wsc15,
        "--output", shoot_palette_verification,
    )
    require_hash(shoot_palette_verification, SHOOT_PALETTE_VERIFICATION_SHA256, "Shoot palette operations")
    shoot_initializer_component_verification = intermediate / "shoot-initializer-component-verification.json"
    run(
        "verify_shoot_initializer.py", shoot_palette, candidate, args.gba, args.wsc10,
        args.wsc15, "--output", shoot_initializer_component_verification,
    )
    require_hash(shoot_initializer_component_verification, SHOOT_INITIALIZER_COMPONENT_VERIFICATION_SHA256,
                 "Shoot initializer final instructions and resource consumers")
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
            "7168 initializer P1/P0/P2 assets, and the bounded Ver. 1.5-only "
            "D2-to-GBA-0x5C pitch/timing/stereo/modulation reconstruction; "
            "the final one-byte CE layer also corrects its source-proved right-only pan; "
            "the resident but intentionally uncalled auxiliary-object constructor binds "
            "WSC Ver. 1.5 ES:071E through the commercial 1.0 ID-0x343/pool-5 lineage "
            "to native GBA slot 0x03004D3C and installed Shoot rule resources; the "
            "resident 26-entry upper-state population translates 2320 source code bytes, "
            "its fourth P2 record, intro palette table, target table, native RNG role, "
            "and internal state transitions, while deliberately terminating both 9908 "
            "calls at an unimplemented boundary; a final dependent layer corrects inverted "
            "P1/P2 constructor arguments in the child and auxiliary components and inverted "
            "auxiliary player links, then installs source 71D1..7394 player binding with "
            "a fifteen-entry HP table and allocation-free reuse of the existing auxiliary body; "
            "the phase assigns upper entry 7792 internally but has no external caller; "
            "a subsequent dependent repair corrects five P0 descriptor pointers and installs "
            "all 46 source far descriptors and 393 missing tiles, preserving code and layouts; "
            "the legacy zero-descriptor artifacts remain historical intermediates only; "
            "the final dependent layer fixes three additional-character physics pointers "
            "and installs resident source 73F0..74A2 other-player restoration using native "
            "character resources, the existing OBJ palette mirror and 32-bit physics pointers; "
            "this second player phase also remains uncalled until complete initialization; "
            "two further resident resource segments implement source 7394..73A9 OBJ slot-5 "
            "palette loading and 74A2..74DA native HUD tile-3FC/palette-6 loading plus scroll reset; "
            "they reuse exact commercial HUD pixels and have no external caller; "
            "new resident controller selection/application components preserve the 64-way source "
            "decision table and RNG cardinality without connecting absent callbacks; palette "
            "operations preserve selective backup, split BG/OBJ row consumers and source-channel "
            "cadence, with exclusive scene ownership still an unfulfilled caller precondition; "
            "initializer components add native graphics resets, stage manager preparation, "
            "the source timer in commercial native units, the proven 0660 clear and two "
            "constructor adapters with independently relocated per-item P1 records; "
            "outer initializer preparation/tail/menu entry, external controller 9908/9A1B rules, audible timbre parity, "
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
            "shoot_d2_analysis_sha256": SHOOT_D2_ANALYSIS_SHA256,
            "shoot_d2_verification_sha256": SHOOT_D2_VERIFICATION_SHA256,
            "shoot_ce_stereo_verification_sha256": SHOOT_CE_STEREO_VERIFICATION_SHA256,
            "shoot_child_verification_sha256": SHOOT_CHILD_VERIFICATION_SHA256,
            "shoot_ce_sound_verification_sha256": SHOOT_CE_SOUND_VERIFICATION_SHA256,
            "shoot_parent_verification_sha256": SHOOT_PARENT_VERIFICATION_SHA256,
            "shoot_aux_object_lifetime_sha256": SHOOT_AUX_OBJECT_LIFETIME_SHA256,
            "shoot_aux_object_verification_sha256": SHOOT_AUX_OBJECT_VERIFICATION_SHA256,
            "shoot_upper_state_graph_sha256": SHOOT_UPPER_STATE_GRAPH_SHA256,
            "shoot_upper_state_verification_sha256": SHOOT_UPPER_STATE_VERIFICATION_SHA256,
            "shoot_player_binding_verification_sha256": SHOOT_PLAYER_BINDING_VERIFICATION_SHA256,
            "shoot_far_tile_verification_sha256": SHOOT_FAR_TILE_VERIFICATION_SHA256,
            "shoot_other_player_verification_sha256": SHOOT_OTHER_PLAYER_VERIFICATION_SHA256,
            "shoot_tail_resource_verification_sha256": SHOOT_TAIL_RESOURCE_VERIFICATION_SHA256,
            "shoot_rules_verification_sha256": SHOOT_RULES_VERIFICATION_SHA256,
            "shoot_palette_verification_sha256": SHOOT_PALETTE_VERIFICATION_SHA256,
            "shoot_palette_ownership_sha256": SHOOT_PALETTE_OWNERSHIP_SHA256,
            "shoot_initializer_component_verification_sha256": SHOOT_INITIALIZER_COMPONENT_VERIFICATION_SHA256,
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

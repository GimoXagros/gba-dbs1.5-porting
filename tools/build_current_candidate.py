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
FONT_SHA256 = "4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED"
FONT_LICENSE_SHA256 = "76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C"
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

SHOOT_LOWER_AUDIO_VERIFICATION_SHA256 = "D177C343BCA6776520048CDA97D584EE539A005577E8CA5B7773E494B2A61AFE"
SHOOT_LOWER_RULES_VERIFICATION_SHA256 = "313105EF1A8D5C26A42F690DB93A7BE0B25F89771168D0036FC3071E9CE26030"
SHOOT_GRAPHICS_VERIFICATION_SHA256 = "8D5AB7EE5F2EC2CA7CF30BA374CF87A167A60981C6AB59713DBEE041A9CF0DB5"
SHOOT_TRANSITION_AUDIO_SHA256 = "48424A2F144A1C41035111E75363E624D5E2A84F9FF9A2E7D9AD4A71B57B6D1B"
SHOOT_SCENE_OBJECTS_SHA256 = "A4E1DE4CB5000EC31B56471D99490936E2B82C84277976B3FA0F5AA36665F8B5"
SHOOT_STAGE_ASSET_VERIFICATION_SHA256 = "213203E94233DA124057CC5BE7D9481BBA98F838D475F40C03EEC28EDAEE1E25"
SHOOT_STAGE_HANDSHAKE_VERIFICATION_SHA256 = "E9B32C9DBF53FA543D5CC2800C467764D4CE44C6659528EBFB353F8DFC9B5FF5"
SHOOT_TERMINAL_VERIFICATION_SHA256 = "4D6FE917B45ADF7E26E9F0E4FAE4EF938AF1AC84D91D06B63BC0798D06C466BF"
SHOOT_NORMAL_DISPLAY_VERIFICATION_SHA256 = "7BD2283D660C034FFCC5A7C458E22126C06E55C208CFCB45E5A6B7A863A8752F"
SHOOT_SPATIAL_REPAIR_VERIFICATION_SHA256 = "3BB0886B55FB760CD423BBFF58582049FDCD5F8CA52CE90D90A2F307D22548E4"
CHARACTER_PHYSICS_ROUTING_VERIFICATION_SHA256 = "C6823829AF3EC159BF2FAA85C00CE2D5C1E97603CD40BFA35987221D9B42E88A"
OPENING_PRESENTATION_ROUTING_VERIFICATION_SHA256 = "E7E453C645762232D0B4668FEA6FA760A5C76F7DE1B50094144218841FB9C42A"
SHOOT_SRAM_BOUNDARY_SHA256 = "29304FA84432898B857AC8874C1525E57FDE0EABBAFFC5008DBFA80962E27295"

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
    "character-physics-current.bin": "B1DC4C8BC816DE6EF5952403C75A1BF4140A8F6A01A2051A33A3F65809EC29DF",
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
    "shoot-initializer-components.gba": "726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284",
    "shoot-lower-audio.gba": "0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103",
    "shoot-lower-rules.gba": "223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E",
    "shoot-graphics.gba": "6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29",
    "shoot-stage-assets.gba": "00C4A8F4710BC0E2F4A31810CDD6FE2610D9670D9A989273162ADF33167211E7",
    "shoot-stage-handshake.gba": "F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF",
    "shoot-terminal.gba": "39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D",
    "shoot-normal-display.gba": "455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48",
    "shoot-spatial-repair.gba": "CAB43EA68A6620D150CA853FC51D4690AAF0889A6D7351D90F99128FE5DD2C69",
    "character-physics-routing.gba": "8B91E5DA0147E16CC949785F73F6447878529B404949CB27EEA81B47275A77C2",
    "opening-presentation-routing.gba": "E2B700D26818148C0C196DC1C594AB5CE5FD6CBDD348384F7617D168CC62AE4D",
    "character-p0-completion.gba": "973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D",
    "character-audio.gba": "10372B5606647673F829EC676853C1987F17E64BA19EA51EB751F92FA22B3354",
    "character-p1-completion.gba": "3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA",
    "character-resource-routing.gba": "3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065",
    "opening-callback6-parity.gba": "A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949",
    "selection-palette-routing.gba": "C5152150749B1E16C7B39BCF7E67C69810FE31C970CCA78988828921DA9AC017",
    "player-spawn-literal.gba": "1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995",
    "added-stage-collision.gba": "7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD",
    "logical-stage-spawn.gba": "83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD",
    "train-graphics-repair.gba": "96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530",
    "iraira-floor-launch.gba": "7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470",
    "roster-list-routing.gba": "7DBFA0B464AB9A0E2DA55049855A0BC08AABAAACDA1AF3E21CC780F2864854E9",
    "vs-name-layout-repair.gba": "99EFB070C3DC604040B4F67B70DB9D2099186C8401A3F8E9CDE981567AC3EFD1",
    "selection-palette-index-repair.gba": "AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF",
    "waterfall-display-repair.gba": "C50ADCF54D29B327CCF5BFAE21F51784AC2A7A9544DF6093680BDB6387F93DFF",
    "character-followup-routing.gba": "F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E",
    "options-language-selector.gba": "3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C",
    "character-input-action.gba": "F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0",
    "character-recovery-routing.gba": "A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71",
    "title-language.gba": "143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80",
    "character-hit-routing.gba": "A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61",
    "result-pose-routing.gba": "DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C",
    "waterfall-third-pattern.gba": "B31A46AEC0DD74736CB300339D1475DF23363E8A97E3D79846E3CE64073C3AF8",
    "stage-priority-routing.gba": "389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1",
    "shoot-initializer-prefix.gba": "4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC",
    "shoot-initializer-player-chain.gba": "2C9C96129EBECF30FCB915E077899CE91FBA979F4AC44C027EE39F4C9A8C4BC7",
    "shoot-initializer-front.gba": "CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7",
    "shoot-initializer-storage.gba": "66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF",
    "shoot-initializer-tail-chain.gba": "5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46",
    "shoot-scene.gba": "428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281",
    "title-background.gba": "494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6",
    "result-language.gba": "A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F",
    "shoot-caller.gba": "9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738",
    "controller-bridge.gba": "72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC",
    "shoot-attack.gba": "B64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B",
    "shoot-spatial-subset.gba": "8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717",
    "shoot-static-companion-clear.gba": "35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A",
    "shoot-projectile-clear.gba": "025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA",
    "shoot-guarded-transition.gba": "18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1",
    "shoot-fatal-callback.gba": "6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7",
    "shoot-native-scene.gba": "6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331",
    "shoot-child-rectangle.gba": "1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC",
    "shoot-palette-calls.gba": "FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8",
    "shoot-owner-link.gba": "46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B",
    "shoot-display-epoch.gba": "280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7",
    "evolution-music.gba": "DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049",
    "evolution-music-display.gba": "C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346",
    "evolution-music-pause.gba": "C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278",
    "impmon-evolution.gba": "8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8",
    "evolution-transition.gba": "C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1",
    "id13-air-relaunch.gba": "FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD",
    "campaign-stage-progression.gba": "ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9",
    "campaign-progress-consumers.gba": "933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775",
    "character-type8-tables.gba": "75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F",
    "character-ai-tables.gba": "DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98",
    "character-ai-parameter-alignment.gba": "E6B2C30E3E7D880BFFEE82A3201D0F69AE3DE0EBBEE5B523D24DD6D03FA08CF4",
    "iraira-render.gba": "3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F",
    "mode20-title-assets.gba": "3CB7A7137762AA77C7C8D9147CF32AB356CDB269E6CE819115B911DEF444E49E",
    "current-candidate.gba": "574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76",
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
    parser.add_argument("--font", required=True, type=pathlib.Path, help="pinned Galmuri11-Condensed BDF")
    parser.add_argument("--font-license", required=True, type=pathlib.Path, help="original SIL Open Font License text")
    args = parser.parse_args()

    try:
        from PIL import Image, ImageFilter
    except ImportError as error:
        raise SystemExit("Full build requires Pillow for independent Digicode verification; use a Python runtime with Pillow installed.") from error

    require_hash(args.gba, GBA_SHA256, "USA GBA original")
    require_hash(args.wsc10, WSC10_SHA256, "WSC 1.0 original")
    require_hash(args.wsc15, WSC15_SHA256, "WSC Ver. 1.5 original")
    require_hash(args.font, FONT_SHA256, "Options font source")
    require_hash(args.font_license, FONT_LICENSE_SHA256, "Options font license")

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
    shoot_initializer_components = output / "shoot-initializer-components.gba"
    shoot_lower_audio = output / "shoot-lower-audio.gba"
    shoot_lower_rules = output / "shoot-lower-rules.gba"
    shoot_graphics = output / "shoot-graphics.gba"
    shoot_stage_assets = output / "shoot-stage-assets.gba"
    shoot_stage_handshake = output / "shoot-stage-handshake.gba"
    shoot_terminal = output / "shoot-terminal.gba"
    shoot_normal_display = output / "shoot-normal-display.gba"
    shoot_spatial_repair = output / "shoot-spatial-repair.gba"
    physics_routing = output / "character-physics-routing.gba"
    opening_routing = output / "opening-presentation-routing.gba"
    character_p0 = output / "character-p0-completion.gba"
    character_audio = output / "character-audio.gba"
    character_p1 = output / "character-p1-completion.gba"
    character_routing = output / "character-resource-routing.gba"
    callback6_parity = output / "opening-callback6-parity.gba"
    selection_palette = output / "selection-palette-routing.gba"
    player_spawn = output / "player-spawn-literal.gba"
    added_collision = output / "added-stage-collision.gba"
    logical_spawn = output / "logical-stage-spawn.gba"
    train_graphics = output / "train-graphics-repair.gba"
    iraira_floor = output / "iraira-floor-launch.gba"
    roster_list = output / "roster-list-routing.gba"
    vs_names = output / "vs-name-layout-repair.gba"
    selection_index = output / "selection-palette-index-repair.gba"
    waterfall_display = output / "waterfall-display-repair.gba"
    character_followup = output / "character-followup-routing.gba"
    language_options = output / "options-language-selector.gba"
    character_action = output / "character-input-action.gba"
    character_recovery = output / "character-recovery-routing.gba"
    title_language = output / "title-language.gba"
    character_hit = output / "character-hit-routing.gba"
    result_pose = output / "result-pose-routing.gba"
    waterfall_third = output / "waterfall-third-pattern.gba"
    stage_priority = output / "stage-priority-routing.gba"
    initializer_prefix = output / "shoot-initializer-prefix.gba"
    initializer_player_chain = output / "shoot-initializer-player-chain.gba"
    initializer_front = output / "shoot-initializer-front.gba"
    initializer_storage = output / "shoot-initializer-storage.gba"
    initializer_tail = output / "shoot-initializer-tail-chain.gba"
    scene_dependencies = intermediate / "shoot-scene-dependencies.json"
    shoot_scene = output / "shoot-scene.gba"
    title_background = output / "title-background.gba"
    result_art = intermediate / "result-approved-art.json"
    result_language = output / "result-language.gba"
    shoot_caller = output / "shoot-caller.gba"
    controller_domain = intermediate / "shoot-controller-domain.json"
    controller_bridge = output / "controller-bridge.gba"
    shoot_attack = output / "shoot-attack.gba"
    shoot_spatial_subset = output / "shoot-spatial-subset.gba"
    shoot_companion_clear = output / "shoot-static-companion-clear.gba"
    shoot_projectile_clear = output / "shoot-projectile-clear.gba"
    shoot_guarded_transition = output / "shoot-guarded-transition.gba"
    shoot_fatal = output / "shoot-fatal-callback.gba"
    shoot_native_scene = output / "shoot-native-scene.gba"
    shoot_rectangle = output / "shoot-child-rectangle.gba"
    shoot_palette_calls = output / "shoot-palette-calls.gba"
    shoot_owner_link = output / "shoot-owner-link.gba"
    shoot_display_epoch = output / "shoot-display-epoch.gba"
    evolution_music = output / "evolution-music.gba"
    evolution_music_display = output / "evolution-music-display.gba"
    evolution_music_pause = output / "evolution-music-pause.gba"
    impmon_evolution = output / "impmon-evolution.gba"
    evolution_transition = output / "evolution-transition.gba"
    id13_air = output / "id13-air-relaunch.gba"
    campaign_stage = output / "campaign-stage-progression.gba"
    campaign_consumers = output / "campaign-progress-consumers.gba"
    character_type8 = output / "character-type8-tables.gba"
    character_ai = output / "character-ai-tables.gba"
    ai_aligned = output / "character-ai-parameter-alignment.gba"
    iraira_render = output / "iraira-render.gba"
    mode20_title = output / "mode20-title-assets.gba"
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
        shoot_initializer_components, "--manifest", output / "shoot-initializer-components.json",
    )
    run("build_shoot_lower_audio.py", shoot_initializer_components, args.gba, args.wsc10,
        args.wsc15, shoot_lower_audio, "--manifest", output / "shoot-lower-audio.json")
    run("build_shoot_lower_rules.py", shoot_lower_audio, args.gba, args.wsc15,
        shoot_lower_rules, "--manifest", output / "shoot-lower-rules.json")
    run("build_shoot_graphics_initializer.py", shoot_lower_rules, args.gba, args.wsc10,
        args.wsc15, shoot_graphics, "--manifest", output / "shoot-graphics.json")
    run("build_shoot_stage_assets.py", shoot_graphics, args.wsc15, shoot_stage_assets,
        "--manifest", output / "shoot-stage-assets.json")
    run("build_shoot_stage_handshake.py", shoot_stage_assets, args.gba, args.wsc10, args.wsc15, shoot_stage_handshake,
        "--manifest", output / "shoot-stage-handshake.json")
    run("build_shoot_terminal.py", shoot_stage_handshake, args.gba, args.wsc10, args.wsc15, shoot_terminal,
        "--manifest", output / "shoot-terminal.json")
    run("build_shoot_normal_display_route.py", shoot_terminal, args.gba, shoot_normal_display,
        "--manifest", output / "shoot-normal-display.json")
    run("build_shoot_spatial_repair.py", shoot_normal_display, args.gba, args.wsc15, shoot_spatial_repair,
        "--manifest", output / "shoot-spatial-repair.json")
    run("build_character_physics_routing.py", shoot_spatial_repair, args.gba, args.wsc15, physics_routing,
        "--manifest", output / "character-physics-routing.json")
    run("build_opening_presentation_routing_repair.py", physics_routing, args.gba, args.wsc15, opening_routing,
        "--manifest", output / "opening-presentation-routing.json")
    run("build_character_p0_completion.py", opening_routing, args.gba, args.wsc15, character_p0,
        "--manifest", output / "character-p0-completion.json")
    run("build_character_audio.py", character_p0, args.gba, args.wsc15, character_audio,
        "--manifest", output / "character-audio.json")
    run("build_character_p1_completion.py", character_audio, args.gba, args.wsc10, args.wsc15, character_p1,
        "--manifest", output / "character-p1-completion.json")
    run("build_character_resource_routing.py", character_p1, args.gba, args.wsc10, args.wsc15, character_routing,
        "--manifest", output / "character-resource-routing.json")
    run("build_opening_callback6_parity.py", character_routing, args.gba, args.wsc10, args.wsc15, callback6_parity,
        "--manifest", output / "opening-callback6-parity.json")
    run("build_selection_palette_routing_repair.py", callback6_parity, args.gba, selection_palette,
        "--manifest", output / "selection-palette-routing.json")
    run("build_player_spawn_literal_repair.py", selection_palette, args.gba, args.wsc15, player_spawn,
        "--manifest", output / "player-spawn-literal.json")
    run("build_added_stage_collision.py", player_spawn, args.gba, args.wsc10, args.wsc15, added_collision,
        "--manifest", output / "added-stage-collision.json")
    run("build_logical_stage_spawn.py", added_collision, args.wsc15, logical_spawn,
        "--manifest", output / "logical-stage-spawn.json")
    run("build_train_graphics_repair.py", logical_spawn, args.gba, args.wsc10, args.wsc15, train_graphics,
        "--manifest", output / "train-graphics-repair.json")
    run("build_iraira_floor_launch.py", train_graphics, args.gba, args.wsc10, args.wsc15, iraira_floor,
        "--manifest", output / "iraira-floor-launch.json")
    run("build_roster_list_routing.py", iraira_floor, args.gba, args.wsc15, roster_list,
        "--manifest", output / "roster-list-routing.json")
    run("build_vs_name_layout_repair.py", roster_list, args.gba, args.wsc10, args.wsc15, vs_names,
        "--manifest", output / "vs-name-layout-repair.json")
    run("build_selection_palette_index_repair.py", vs_names, args.gba, selection_index,
        "--manifest", output / "selection-palette-index-repair.json")
    run("build_waterfall_display_repair.py", selection_index, args.gba, args.wsc10, args.wsc15, waterfall_display,
        "--manifest", output / "waterfall-display-repair.json")
    run("build_character_followup_routing.py", waterfall_display, args.gba, args.wsc10, args.wsc15, character_followup,
        "--manifest", output / "character-followup-routing.json")
    run("build_options_selector.py", character_followup, args.gba, args.font, args.font_license, language_options,
        "--manifest", output / "options-language-selector.json")
    run("build_character_action_routing.py", language_options, args.gba, args.wsc10, args.wsc15, character_action,
        "--manifest", output / "character-input-action.json")
    run("build_character_damage_routing.py", character_action, args.gba, args.wsc10, args.wsc15, character_recovery,
        "--manifest", output / "character-recovery-routing.json")
    run("build_title_language.py", character_recovery, args.gba, args.wsc10, args.wsc15, args.font, args.font_license, title_language,
        "--manifest", output / "title-language.json")
    run("build_character_hit_routing.py", title_language, args.gba, args.wsc10, args.wsc15, character_hit,
        "--manifest", output / "character-hit-routing.json")
    run("build_result_pose_routing.py", character_hit, args.gba, args.wsc10, args.wsc15, result_pose,
        "--manifest", output / "result-pose-routing.json")
    run("build_waterfall_third_pattern.py", result_pose, args.gba, args.wsc10, args.wsc15, waterfall_third,
        "--manifest", output / "waterfall-third-pattern.json")
    run("build_stage_priority_routing.py", waterfall_third, args.gba, args.wsc10, args.wsc15, stage_priority,
        "--manifest", output / "stage-priority-routing.json")
    run("build_shoot_initializer_prefix.py", stage_priority, args.gba, args.wsc10, args.wsc15, initializer_prefix,
        "--manifest", output / "shoot-initializer-prefix.json")
    run("build_shoot_initializer_player_chain.py", initializer_prefix, args.gba, args.wsc10, args.wsc15, initializer_player_chain,
        "--manifest", output / "shoot-initializer-player-chain.json")
    run("build_shoot_initializer_front.py", initializer_player_chain, args.gba, args.wsc10, args.wsc15, initializer_front,
        "--manifest", output / "shoot-initializer-front.json")
    run("build_shoot_initializer_storage.py", initializer_front, args.gba, args.wsc10, args.wsc15, initializer_storage,
        "--manifest", output / "shoot-initializer-storage.json")
    run("build_shoot_initializer_tail_chain.py", initializer_storage, args.gba, args.wsc10, args.wsc15, initializer_tail,
        "--manifest", output / "shoot-initializer-tail-chain.json")
    scene_dependencies.write_text(json.dumps({
        "input_sha256": EXPECTED_LAYERS["shoot-initializer-tail-chain.gba"],
        "initializer": {"entry": 0x08629800, "bytes": 140,
                        "sha256": "8FEDEC3D4115A92339E37D1F78CAC2A1DE4A435A074CF641339FF22EC90B5F13"},
    }, indent=2) + "\n", encoding="utf-8")
    run("build_shoot_scene_transition.py", initializer_tail, args.gba, args.wsc10, args.wsc15,
        scene_dependencies, shoot_scene, "--manifest", output / "shoot-scene.json")
    run("build_title_background.py", shoot_scene, args.wsc15, title_background,
        "--manifest", output / "title-background.json")
    run("build_result_pixel_art.py", "--generate-data", args.gba, args.wsc15,
        ROOT / "localization/digicode-reference.json", result_art)
    require_hash(result_art, "8BFC3960335EDD29ECEBFA2DB7A673FDE586C6B5B79B0FDB47622BC601083074",
                 "approved native result pixels regenerated from original inputs")
    run("build_result_language.py", title_background, args.gba, args.wsc15, result_art, result_language,
        "--manifest", output / "result-language.json")
    run("build_shoot_caller_resident.py", result_language, args.gba, args.wsc15, shoot_caller,
        "--manifest", output / "shoot-caller.json")
    run("analyze_shoot_controller_domain.py", args.wsc15, shoot_caller, "--output", controller_domain)
    require_hash(controller_domain, "5DBB2620877D5ADEE92338B87B285610914CA07F2C484077846A602EDA707B46",
                 "source controller obligations; coupled coordinate domain remains open")
    run("build_shoot_controller_adapter.py", shoot_caller, controller_bridge,
        "--manifest", output / "controller-bridge.json")
    run("build_shoot_attack_dispatch.py", controller_bridge, args.gba, args.wsc10, args.wsc15, shoot_attack,
        "--manifest", output / "shoot-attack.json")
    run("build_shoot_spatial_subset.py", shoot_attack, args.wsc15, shoot_spatial_subset,
        "--manifest", output / "shoot-spatial-subset.json")
    run("build_shoot_static_companion_clear.py", shoot_spatial_subset, args.wsc15, shoot_companion_clear,
        "--manifest", output / "shoot-static-companion-clear.json")
    lower_graph = intermediate / "shoot-rule-graph.json"
    reload_proof = intermediate / "shoot-p2-reload-eligibility.json"
    run("analyze_shoot_rule_callback_graph.py", args.wsc15, "--output", lower_graph)
    require_hash(lower_graph, "37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281",
                 "source lower callback graph regenerated for this build")
    run("analyze_shoot_p2_reload_eligibility.py", args.wsc15, reload_proof, "--lower-graph", lower_graph)
    require_hash(reload_proof, "2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990",
                 "bounded source side1 reload ownership; external domain remains open")
    run("build_shoot_projectile_clear.py", shoot_companion_clear, args.wsc15, shoot_projectile_clear,
        "--reload-proof", reload_proof, "--lower-graph", lower_graph,
        "--manifest", output / "shoot-projectile-clear.json")
    run("build_shoot_guarded_transition_irq.py", shoot_projectile_clear, args.gba, args.wsc15,
        shoot_guarded_transition, "--manifest", output / "shoot-guarded-transition.json")
    run("build_shoot_fatal_callback_route.py", shoot_guarded_transition, args.gba, args.wsc15, shoot_fatal,
        "--manifest", output / "shoot-fatal-callback.json")
    run("build_shoot_native_scene_connection.py", shoot_fatal, args.gba, args.wsc15, shoot_native_scene,
        "--manifest", output / "shoot-native-scene.json")
    run("build_shoot_child_attack_rectangle.py", shoot_native_scene, args.gba, args.wsc15, shoot_rectangle,
        "--manifest", output / "shoot-child-rectangle.json")
    run("build_shoot_palette_dim_calls.py", shoot_rectangle, args.wsc15, shoot_palette_calls,
        "--manifest", output / "shoot-palette-calls.json")
    run("build_shoot_terminal_owner_link.py", shoot_palette_calls, args.wsc15, shoot_owner_link,
        "--manifest", output / "shoot-owner-link.json")
    run("build_shoot_terminal_display_epoch.py", shoot_owner_link, args.wsc15, shoot_display_epoch,
        "--manifest", output / "shoot-display-epoch.json")
    run("build_wsc_evolution_music.py", "--input", shoot_owner_link, "--wsc", args.wsc15, "--gba", args.gba,
        "--output", evolution_music, "--manifest", output / "evolution-music.json")
    run("build_evolution_music_integration.py", "--display", shoot_display_epoch, "--audio", evolution_music,
        "--output", evolution_music_display, "--manifest", output / "evolution-music-display.json")
    run("build_evolution_music_pause_cache.py", "--before", evolution_music_display,
        "--output", evolution_music_pause, "--manifest", output / "evolution-music-pause.json")
    run("build_impmon_evolution_gate.py", "--before", evolution_music_pause, "--gba", args.gba,
        "--wsc10", args.wsc10, "--wsc15", args.wsc15, "--output", impmon_evolution,
        "--manifest", output / "impmon-evolution.json")
    run("build_evolution_transition_tables.py", "--before", impmon_evolution, "--wsc15", args.wsc15,
        "--allocation-manifest", output / "evolution-music.json", "--output", evolution_transition,
        "--manifest", output / "evolution-transition.json")
    run("build_id13_air_relaunch.py", "--before", evolution_transition, "--source", args.wsc15,
        "--gba", args.gba, "--audio-manifest", output / "evolution-music.json",
        "--table-manifest", output / "evolution-transition.json", "--output", id13_air,
        "--manifest", output / "id13-air-relaunch.json")
    run("build_campaign_stage_progression.py", "--before", id13_air, "--source", args.wsc15,
        "--audio-manifest", output / "evolution-music.json", "--table-manifest", output / "evolution-transition.json",
        "--id13-manifest", output / "id13-air-relaunch.json", "--output", campaign_stage,
        "--manifest", output / "campaign-stage-progression.json")
    run("build_campaign_progression_consumers.py", "--before", campaign_stage, "--source", args.wsc15,
        "--audio-manifest", output / "evolution-music.json", "--table-manifest", output / "evolution-transition.json",
        "--id13-manifest", output / "id13-air-relaunch.json", "--campaign-manifest", output / "campaign-stage-progression.json",
        "--output", campaign_consumers, "--manifest", output / "campaign-progress-consumers.json")
    run("build_character_type8_tables.py", "--before", campaign_consumers, "--gba", args.gba,
        "--old", args.wsc10, "--source", args.wsc15,
        "--owners", output / "evolution-music.json", output / "evolution-transition.json",
        output / "id13-air-relaunch.json", output / "campaign-stage-progression.json",
        output / "campaign-progress-consumers.json", "--output", character_type8,
        "--manifest", output / "character-type8-tables.json")
    run("build_character_ai_tables.py", "--before", character_type8, "--gba", args.gba,
        "--old", args.wsc10, "--source", args.wsc15,
        "--owners", output / "evolution-music.json", output / "evolution-transition.json",
        output / "id13-air-relaunch.json", output / "campaign-stage-progression.json",
        output / "campaign-progress-consumers.json", output / "character-type8-tables.json",
        "--output", character_ai, "--manifest", output / "character-ai-tables.json")
    run("build_character_ai_parameter_alignment.py", "--before", character_ai,
        "--source", args.wsc15, "--owner", output / "character-ai-tables.json",
        "--output", ai_aligned, "--manifest", output / "character-ai-parameter-alignment.json")
    run("build_iraira_render_repair.py", "--before", ai_aligned, "--source", args.wsc15,
        "--alignment-owner", output / "character-ai-parameter-alignment.json",
        "--output", iraira_render, "--manifest", output / "iraira-render.json")
    run("build_mode20_title_assets.py", "--before", iraira_render, "--source", args.wsc15,
        "--owner", output / "iraira-render.json", "--output", mode20_title,
        "--manifest", output / "mode20-title-assets.json")
    run("build_iraira_outer_palette_route.py", "--before", mode20_title, "--source", args.wsc15,
        "--owners", output / "mode20-title-assets.json", output / "iraira-render.json",
        output / "character-ai-parameter-alignment.json", "--output", candidate,
        "--manifest", output / "current-candidate.json")
    (output / "font-license.txt").write_bytes(args.font_license.read_bytes())
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
        "--legacy-v49-source-routing",
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
        "verify_shoot_initializer.py", shoot_palette, shoot_initializer_components, args.gba, args.wsc10,
        args.wsc15, "--output", shoot_initializer_component_verification,
    )
    require_hash(shoot_initializer_component_verification, SHOOT_INITIALIZER_COMPONENT_VERIFICATION_SHA256,
                 "Shoot initializer final instructions and resource consumers")
    for tool, before, after, pin, report_name, flag in (
        ("verify_shoot_lower_audio.py", shoot_initializer_components, shoot_lower_audio,
         SHOOT_LOWER_AUDIO_VERIFICATION_SHA256, "shoot-lower-audio-verification.json", "--output"),
        ("verify_shoot_lower_rules.py", shoot_lower_audio, shoot_lower_rules,
         SHOOT_LOWER_RULES_VERIFICATION_SHA256, "shoot-lower-rules-verification.json", "--output"),
        ("verify_shoot_graphics_initializer.py", shoot_lower_rules, shoot_graphics,
         SHOOT_GRAPHICS_VERIFICATION_SHA256, "shoot-graphics-verification.json", "--report"),
    ):
        report_path = intermediate / report_name
        run(tool, before, after, args.gba, args.wsc10, args.wsc15, flag, report_path)
        require_hash(report_path, pin, report_name)
    transition_audio = intermediate / "shoot-transition-audio.json"
    run("analyze_shoot_transition_audio.py", args.gba, args.wsc10, args.wsc15,
        "--output", transition_audio)
    require_hash(transition_audio, SHOOT_TRANSITION_AUDIO_SHA256, "Shoot transition audio services")
    scene_objects = intermediate / "shoot-scene-objects.json"
    run("analyze_shoot_scene_objects.py", args.gba, "--output", scene_objects)
    require_hash(scene_objects, SHOOT_SCENE_OBJECTS_SHA256, "Shoot scene object ownership")
    stage_assets_verification = intermediate / "shoot-stage-asset-verification.json"
    run("verify_shoot_stage_assets.py", shoot_stage_assets, shoot_graphics, args.wsc15, args.gba,
        "--output", stage_assets_verification)
    require_hash(stage_assets_verification, SHOOT_STAGE_ASSET_VERIFICATION_SHA256,
                 "Shoot actual source addresses and native map consumers")
    stage_handshake_verification = intermediate / "shoot-stage-handshake-verification.json"
    run("verify_shoot_stage_handshake.py", shoot_stage_assets, shoot_stage_handshake, args.gba, args.wsc10,
        args.wsc15, "--output", stage_handshake_verification)
    require_hash(stage_handshake_verification, SHOOT_STAGE_HANDSHAKE_VERIFICATION_SHA256,
                 "Shoot main update, display and scanline contracts")
    terminal_verification = intermediate / "shoot-terminal-verification.json"
    run("verify_shoot_terminal.py", shoot_stage_handshake, shoot_terminal, args.gba, args.wsc10,
        args.wsc15, "--output", terminal_verification)
    require_hash(terminal_verification, SHOOT_TERMINAL_VERIFICATION_SHA256,
                 "Shoot terminal resident phases and same-update repairs")
    normal_display_verification = intermediate / "shoot-normal-display-verification.json"
    run("verify_shoot_normal_display_route.py", shoot_terminal, shoot_normal_display, args.gba,
        "--output", normal_display_verification)
    require_hash(normal_display_verification, SHOOT_NORMAL_DISPLAY_VERIFICATION_SHA256,
                 "Shoot connected normal display with preserved terminal fallback")
    sram_boundary = intermediate / "shoot-sram-boundary.json"
    spatial_verification = intermediate / "shoot-spatial-repair-verification.json"
    run("verify_shoot_spatial_repair.py", shoot_normal_display, shoot_spatial_repair, args.gba,
        args.wsc10, args.wsc15, "--output", spatial_verification)
    require_hash(spatial_verification, SHOOT_SPATIAL_REPAIR_VERIFICATION_SHA256,
                 "Shoot collision grid and same-invocation terminal transition")
    physics_verification = intermediate / "character-physics-routing-verification.json"
    run("verify_character_physics_routing.py", shoot_spatial_repair, physics_routing,
        args.gba, args.wsc15, "--output", physics_verification)
    require_hash(physics_verification, CHARACTER_PHYSICS_ROUTING_VERIFICATION_SHA256,
                 "actual source pointer routing and complete native physics groups")
    opening_routing_verification = intermediate / "opening-presentation-routing-verification.json"
    run("verify_opening_presentation_routing_repair.py", physics_routing, opening_routing,
        args.gba, args.wsc15, opening_routing_verification)
    require_hash(opening_routing_verification, OPENING_PRESENTATION_ROUTING_VERIFICATION_SHA256,
                 "opening selector view and native renderer resource bounds")
    for tool, before, after, sources, expected in (
        ("verify_character_p0_completion.py", opening_routing, character_p0, [args.gba, args.wsc15],
         "9330DCE05012EC852202F59A5994F9362B193035DB6A1D68E43D78C325E6ECEB"),
        ("verify_character_audio.py", character_p0, character_audio, [args.gba, args.wsc15],
         "191A6B7E03D8C0A994834CBD84F4A12CB038B41EAFFCD1DA8F1DA92E9E8E1217"),
        ("verify_character_p1_completion.py", character_audio, character_p1, [args.gba, args.wsc10, args.wsc15],
         "FAC5E6F50B55BF4789E4FB06EB6454DF1AFB8DCE5172E08A7F35275AD08E87E7"),
        ("verify_character_resource_routing.py", character_p1, character_routing, [args.gba, args.wsc10, args.wsc15],
         "476488DE9B0413D53BACA1125B41241FC6322ACB54D2AA139E20E187CCFE6C2A"),
        ("verify_opening_callback6_parity.py", character_routing, callback6_parity, [args.gba, args.wsc10, args.wsc15],
         "1F7673D861FFA2342ABDA367CA4EF661E63CFABFD4D8EDCD6586DAF7BF65EB00"),
        ("verify_selection_palette_routing_repair.py", callback6_parity, selection_palette, [args.gba],
         "BB7C2B169796F71EAF2FFD39E1A8AB6CE7300E979EF8D108B967B4B49423E2AD"),
        ("verify_player_spawn_literal_repair.py", selection_palette, player_spawn, [args.gba, args.wsc10, args.wsc15],
         "5AA3B9172D5E9462B310E6A60478A9B6C89307D0416A933F1CB1BF4E466DBD0E"),
        ("verify_added_stage_collision.py", player_spawn, added_collision, [args.gba, args.wsc10, args.wsc15],
         "B7B695D12609FFACF06F84C10E26E7A797D2CCD5C90F508AE1AE2221B99A5AD0"),
        ("verify_logical_stage_spawn.py", added_collision, logical_spawn, [args.wsc15],
         "D8C5A070EDA84A4CAD2ACB8A0D3910BEE7B1E5272990918F60F49F0D64BE5094"),
        ("verify_train_graphics_repair.py", logical_spawn, train_graphics, [args.gba, args.wsc10, args.wsc15],
         "C4DCF5669AB21BB92978EE0ECE6B5EC027BC0CDF42CDE72D1FBDB9AEDFF084EC"),
        ("verify_iraira_floor_launch.py", train_graphics, iraira_floor, [args.gba, args.wsc10, args.wsc15],
         "3E9CC0CD8498605C34DD8904663211875107F36D8FD5DE29F8140372DF7699B0"),
        ("verify_roster_list_routing.py", iraira_floor, roster_list, [args.gba, args.wsc15],
         "1CA72D8AE54AA88E6F7786BAE85B1876169FA8225022DE441BB275C6410FCD96"),
        ("verify_vs_name_layout_repair.py", roster_list, vs_names,
         [args.gba, args.wsc10, args.wsc15, ROOT / "records/fixtures/id14-vs-name-overflow-20261021.json"],
         "D5080E7D2813E274BCB19E4B688A357734ABFF1F7B722EEC3739D7ED63AA09F8"),
        ("verify_selection_palette_index_repair.py", vs_names, selection_index, [args.gba],
         "D699F79E826696454DD9E614A9C8B67193EFCE52692399DC5D61E1A899D4D2C1"),
        ("verify_waterfall_display_repair.py", selection_index, waterfall_display, [args.gba, args.wsc10, args.wsc15],
         "2FE4896E11B5CD9C63AD30010594C7A613F9C0AE2DA21459DCCBE73D0F29A6D1"),
        ("verify_character_followup_routing.py", waterfall_display, character_followup, [args.gba, args.wsc10, args.wsc15],
         "A96E3DB159C9F33B867D0B96C4290423640DC24C695803F9485058E8C25FC3A9"),
        ("verify_options_selector.py", character_followup, language_options,
         [args.gba, args.font, output / "options-language-selector.json"],
         "85F723E9B043A161788B1821F6D2BF895D3906254EFF6CBF255CB8D1B9094175"),
        ("verify_character_action_routing.py", language_options, character_action, [args.gba, args.wsc10, args.wsc15],
         "D9B1BBC12B8DF71CB3E9522F780063EC699AD12E8D246FBD10A0F2C08A5EFDF8"),
        ("verify_character_damage_routing.py", character_action, character_recovery, [args.gba, args.wsc10, args.wsc15],
         "9D2E87557FC06DEB0816EA2917F1AC0897FBC47110BA14079C7CE3DF2202E9C0"),
        ("verify_character_hit_routing.py", title_language, character_hit, [args.gba, args.wsc10, args.wsc15],
         "775EA0F411E73DA7940BFAA74DD9127CC88D896DD7D5C15C3802576BA3857DCE"),
        ("verify_result_pose_routing.py", character_hit, result_pose, [args.gba, args.wsc10, args.wsc15],
         "C399601AA969E290F9C61A345CDE035374235BFE0D40B1A6E68E01E7293FFB08"),
        ("verify_waterfall_third_pattern.py", result_pose, waterfall_third, [args.gba, args.wsc10, args.wsc15],
         "0F30817BB70154F582B6E2FED3A286C440CBF84F97F7E2C1952962CAB9F1B4A1"),
        ("verify_stage_priority_routing.py", waterfall_third, stage_priority, [args.gba, args.wsc10, args.wsc15],
         "0D922956162CB291190290EE0B1FA5083FA2826D49619A1AD061880BBD6465B3"),
        ("verify_shoot_initializer_prefix.py", stage_priority, initializer_prefix, [args.gba, args.wsc10, args.wsc15],
         "58B559ADDB89ED4279A000447E276FDAAE68F0C90EBB4A6D5345E3B6C7F05BEB"),
        ("verify_shoot_initializer_player_chain.py", initializer_prefix, initializer_player_chain, [args.gba, args.wsc10, args.wsc15],
         "3AF4894852EFFEC04F66F4D65F1D85BC14C2034E869FA26AE85D57827AA118F7"),
        ("verify_shoot_initializer_front.py", initializer_player_chain, initializer_front, [args.gba, args.wsc10, args.wsc15],
         "471C31326FEE5FDCD2BD7841FB227082EE38D8CAB782AD6EA967C27C7C9C881F"),
        ("verify_shoot_initializer_storage.py", initializer_front, initializer_storage, [args.gba, args.wsc10, args.wsc15],
         "BC75F6EACF9E9320463CC8436A731E7405F4DE15959882CA59B71DC32C90333E"),
        ("verify_shoot_initializer_tail_chain.py", initializer_storage, initializer_tail, [args.gba, args.wsc10, args.wsc15],
         "9C530F9BB055BAEB5CE52B279110721E063C07973297EBBE0FDB0A182937BC50"),
    ):
        report = intermediate / (tool.removeprefix("verify_").removesuffix(".py").replace("_", "-") + "-verification.json")
        run(tool, before, after, *sources, report)
        require_hash(report, expected, tool)
    scene_review = intermediate / "shoot-scene-verification.json"
    run("verify_shoot_scene_transition.py", initializer_tail, shoot_scene, args.gba, args.wsc10, args.wsc15,
        scene_dependencies, "--output", scene_review)
    require_hash(scene_review, "AC1D7CCFBC2753D1439B2AFCA364240F7AFC0D26C1E030860898B82ED99DD15D",
                 "independent resident Shoot scene verification")
    title_background_review = intermediate / "title-background-verification.json"
    run("verify_title_background.py", shoot_scene, title_background, args.gba, args.wsc15, title_background_review)
    require_hash(title_background_review, "1D2AF8B349E42701DD85BA59B1111E1ED3C88E5AF7C7AB3B3F0DEC289800C665",
                 "independent source 1.5 title background verification")
    result_review = intermediate / "result-language-verification.json"
    run("verify_result_language.py", title_background, result_language, args.gba, args.wsc10, args.wsc15,
        result_art, output / "result-language.json", result_review)
    require_hash(result_review, "50351DA73917A2884CAAC4AFDAC40FFB6E1F42E8EE5B30D34B5B9EF064C5775F",
                 "independent four-language result resource and population verification")
    caller_review = intermediate / "shoot-caller-resident-verification.json"
    run("verify_shoot_caller_resident.py", result_language, shoot_caller, args.gba, args.wsc15,
        output / "shoot-caller.json", "--output", caller_review)
    require_hash(caller_review, "B079E66FA7DE910679E6D83539F8EAABF2BD1642A4B65D98F7140D10B67062F5",
                 "independent synchronous Shoot caller and terminal-router verification")
    controller_review = intermediate / "shoot-controller-bridge-verification.json"
    run("verify_shoot_controller_adapter.py", shoot_caller, controller_bridge, "--production",
        "--gba", args.gba, "--wsc15", args.wsc15, "--manifest", output / "controller-bridge.json",
        "--domain-proof", controller_domain, "--output", controller_review)
    require_hash(controller_review, "ACCAA6312E68606199B35F5588BEE28C860F0AF6CD9C051636A02A61C4053525",
                 "independent internal controller bridge and unchanged external route")
    attack_review = intermediate / "shoot-attack-dispatch-verification.json"
    run("verify_shoot_attack_dispatch.py", controller_bridge, shoot_attack, args.gba, args.wsc10, args.wsc15,
        output / "shoot-attack.json", "--output", attack_review)
    require_hash(attack_review, "02E7819CC861561CC8E747683420294B7CB0F9A691AE2BEF4A355261F29368FD",
                 "independent Shoot type1A/1B consumers and preserved legacy dispatch")
    spatial_review = intermediate / "shoot-spatial-subset-verification.json"
    run("verify_shoot_spatial_subset.py", shoot_attack, shoot_spatial_subset, args.wsc15,
        "--manifest", output / "shoot-spatial-subset.json", "--output", spatial_review)
    require_hash(spatial_review, "4F5A9EDA33FF91BE70A94DB5240814ADA94EAEBD2CE2F7E6B1FCF00E729543B9",
                 "independent complete source-normal pattern subset and actual ARM semantics")
    companion_review = intermediate / "shoot-static-companion-clear-verification.json"
    run("verify_shoot_static_companion_clear.py", shoot_spatial_subset, shoot_companion_clear, args.gba, args.wsc15, companion_review)
    require_hash(companion_review, "DF06DEBA3B9BF1B405F6BFE81DE3188DC6002F935723491DEB45A0AB999422CC",
                 "independent actual static-companion clear, native renderer and preload lifetime")
    projectile_review = intermediate / "shoot-projectile-clear-verification.json"
    run("verify_shoot_projectile_clear.py", shoot_companion_clear, shoot_projectile_clear, args.wsc15, projectile_review,
        "--source-proof", reload_proof, "--lower-graph", lower_graph)
    require_hash(projectile_review, "95458CCEBEBDBCD5BE5D2CE703D32490F106629BE58DDEAAC280203DA0830C38",
                 "independent bounded93E7 clear and complete native renderer execution")
    guarded_review = intermediate / "shoot-guarded-transition-verification.json"
    run("verify_shoot_guarded_transition_irq.py", shoot_guarded_transition, shoot_projectile_clear,
        args.gba, args.wsc15, "--manifest", output / "shoot-guarded-transition.json",
        "--layout", ROOT / "records/shoot-guarded-transition-layout-20261109.json", "--output", guarded_review)
    require_hash(guarded_review, "555554FDADF48C80F74DE2A9700B7ECD6FC798F859C151B6A4AC440A9C6925FB",
                 "independent stationary-family native queue and transition IRQ")
    fatal_review = intermediate / "shoot-fatal-callback-verification.json"
    run("verify_shoot_fatal_callback_route.py", shoot_fatal, shoot_guarded_transition, args.gba, args.wsc15,
        "--manifest", output / "shoot-fatal-callback.json", "--output", fatal_review)
    require_hash(fatal_review, "61656691CD4126193003FB2E43B851F3CAA57A8C6C78A147ED602B181F2F2FD4",
                 "independent stage11 fatal callback selection and retained native HP handling")
    scene_review = intermediate / "shoot-native-scene-verification.json"
    run("verify_shoot_native_scene_connection.py", "--before", shoot_fatal, "--after", shoot_native_scene,
        "--gba", args.gba, "--source", args.wsc15, "--manifest", output / "shoot-native-scene.json", "--report", scene_review)
    require_hash(scene_review, "37812C30D6A1EA005F48CB1E3298D38FBCD795008A614CEEA9339679B16B75B8",
                 "source-only native entry, receiver lifetime, HUD and nonfatal composition")
    rectangle_review = intermediate / "shoot-child-rectangle-verification.json"
    run("verify_shoot_child_attack_rectangle_production.py", "--before", shoot_native_scene, "--after", shoot_rectangle,
        "--gba", args.gba, "--source", args.wsc15, "--manifest", output / "shoot-child-rectangle.json", "--report", rectangle_review)
    require_hash(rectangle_review, "BAD282D7F5AEAC391022D3A3C350C4257A6BC15A901406EC29F875CEDFB4DACA",
                 "source-relative child command rectangles and complete163-payload ownership")
    palette_calls_review = intermediate / "shoot-palette-calls-verification.json"
    run("verify_shoot_palette_dim_calls_production.py", "--before", shoot_rectangle, "--after", shoot_palette_calls,
        "--source", args.wsc15, "--manifest", output / "shoot-palette-calls.json", "--report", palette_calls_review)
    require_hash(palette_calls_review, "94F9FD0FC4B95F64CA7BFB4F424DF333EF29170B8CDA32A1CA2FB4BEF0BDC840",
                 "source-bound conditional dim calls with complete four-word inverse")
    owner_link_review = intermediate / "shoot-owner-link-verification.json"
    run("verify_shoot_terminal_owner_link_production.py", "--before", shoot_palette_calls, "--after", shoot_owner_link,
        "--source", args.wsc15, "--manifest", output / "shoot-owner-link.json", "--report", owner_link_review)
    require_hash(owner_link_review, "8CE38E626C7629F4A1F2ABB041B55B85B94AD71809CC1B8EA8C1F8F338AF27A3",
                 "source-bound reciprocal auxiliary owner and retained terminal guard")
    display_epoch_review = intermediate / "shoot-display-epoch-verification.json"
    run("verify_shoot_terminal_display_epoch_production.py", "--before", shoot_owner_link, "--after", shoot_display_epoch,
        "--source", args.wsc15, "--manifest", output / "shoot-display-epoch.json", "--report", display_epoch_review)
    require_hash(display_epoch_review, "AFC67C96B20744286BEC58BA05313808A7CE22D3788E05E6B2385874A8ADCE65",
                 "planned display mapping and live consumption recheck with exact whole inverse")
    music_author_review = intermediate / "evolution-music-author-verification.json"
    run("verify_wsc_evolution_music_author.py", "--rom", evolution_music,
        "--manifest", output / "evolution-music.json", "--report", music_author_review)
    require_hash(music_author_review, "D7B0A1E03B1AA25F7B627FF0CA316DF09364FEF12F6664FC7B17AEA3FF20B0FD",
                 "complete source music stream decoding and native selector ABI")
    music_integration_review = intermediate / "evolution-music-integration-verification.json"
    run("verify_evolution_music_display_composition.py", "--before", shoot_display_epoch, "--audio", evolution_music,
        "--after", evolution_music_display, "--music-manifest", output / "evolution-music.json",
        "--display-manifest", output / "shoot-display-epoch.json", "--report", music_integration_review)
    require_hash(music_integration_review, "FAFF1A4105F0F9A555FAB4FA18B3599EBA27915B6796E51C19AF27F4A1A38FD0",
                 "disjoint music and display layers with both whole-image inverses")
    music_pause_review = intermediate / "evolution-music-pause-verification.json"
    run("verify_evolution_music_pause_cache.py", "--before", evolution_music_display, "--after", evolution_music_pause,
        "--manifest", output / "evolution-music-pause.json", "--report", music_pause_review)
    require_hash(music_pause_review, "1E30456EC7394CF98D74B94D4AB3EBA49D7F1D084A4094E71EFE4BEF987EE022",
                 "four-song cache admission and actual native pause/resume header consumers")
    impmon_evolution_review = intermediate / "impmon-evolution-verification.json"
    run("verify_impmon_evolution_gate.py", "--before", evolution_music_pause, "--after", impmon_evolution,
        "--gba", args.gba, "--wsc10", args.wsc10, "--wsc15", args.wsc15, "--report", impmon_evolution_review)
    require_hash(impmon_evolution_review, "D727C5DC1D35E2C743F8C3B8E6D24BC096AFFACBE45172FE078DD5196A250661",
                 "source default-mode Impmon contact route with exact full-image inverse")
    evolution_tables_review = intermediate / "evolution-transition-verification.json"
    run("verify_evolution_event_tables.py", "--before", impmon_evolution, "--after", evolution_transition,
        "--wsc15", args.wsc15, "--music-manifest", output / "evolution-music.json", "--report", evolution_tables_review)
    require_hash(evolution_tables_review, "A787F41CD3A78BD0B509F2A7EC96C10133BDB825292BC11EDB169D162AA2469B",
                 "source fifteen-identity evolution selectors, bounded allocation and full-image inverse")
    id13_air_review = intermediate / "id13-air-relaunch-verification.json"
    run("verify_id13_air_relaunch.py", "--before", evolution_transition, "--after", id13_air,
        "--manifest", output / "id13-air-relaunch.json", "--source", args.wsc15, "--gba", args.gba,
        "--audio-manifest", output / "evolution-music.json", "--table-manifest", output / "evolution-transition.json",
        "--report", id13_air_review)
    require_hash(id13_air_review, "AF427CBB5E7FCD208D20E624CD907DDF4F3A3573408A67AD8272FB198DFFD6C0",
                 "ID13 source aerial graph, all three fall callers, owned aliases and full-image inverse")
    campaign_review = intermediate / "campaign-stage-progression-verification.json"
    run("verify_campaign_stage_progression.py", "--before", id13_air, "--after", campaign_stage,
        "--manifest", output / "campaign-stage-progression.json", "--source", args.wsc15, "--gba", args.gba,
        "--audio-manifest", output / "evolution-music.json", "--table-manifest", output / "evolution-transition.json",
        "--id13-manifest", output / "id13-air-relaunch.json", "--report", campaign_review)
    require_hash(campaign_review, "1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0",
                 "source clean-mode campaign producer, both stage getters and whole-image inverse")
    campaign_consumers_review = intermediate / "campaign-stage-consumers-verification.json"
    run("verify_campaign_stage_consumers_r2.py", "--before", campaign_stage, "--after", campaign_consumers,
        "--manifest", output / "campaign-progress-consumers.json", "--source", args.wsc15,
        "--audio-manifest", output / "evolution-music.json", "--table-manifest", output / "evolution-transition.json",
        "--id13-manifest", output / "id13-air-relaunch.json", "--producer-manifest", output / "campaign-stage-progression.json",
        "--producer-review", campaign_review, "--report", campaign_consumers_review)
    require_hash(campaign_consumers_review, "3E22A59DD56C2A5EF6F61FABDCACEEA62174636EDACE6BAEB1D7BACCB3FE9A84",
                 "source progress-indexed AI tables, decimal round label and complete layered inverse")
    type8_review = intermediate / "type8-tables-verification.json"
    run("verify_character_type8_tables.py", "--before", campaign_consumers, "--after", character_type8,
        "--source", args.wsc15, "--old", args.wsc10, "--gba", args.gba,
        "--owners", output / "evolution-music.json", output / "evolution-transition.json",
        output / "id13-air-relaunch.json", output / "campaign-stage-progression.json",
        output / "campaign-progress-consumers.json", "--report", type8_review)
    require_hash(type8_review, "0A5EB8355D74AF38C61A90C74ECAD636BDCF6250066C786119DC4EC2513C8896",
                 "source fifteen-identity type8 selectors, actual event consumers and exact inverse")
    character_ai_review = intermediate / "character-ai-tables-verification.json"
    run("verify_character_ai_tables.py", "--before", character_type8, "--after", character_ai,
        "--source", args.wsc15, "--old", args.wsc10, "--gba", args.gba,
        "--owners", output / "evolution-music.json", output / "evolution-transition.json",
        output / "id13-air-relaunch.json", output / "campaign-stage-progression.json",
        output / "campaign-progress-consumers.json", output / "character-type8-tables.json",
        "--report", character_ai_review)
    require_hash(character_ai_review, "B1B21A1C119028B2EBD70602BCCB82F6580CF02A38932E69EB58187A7B885FC7",
                 "source AI identity mapping, complete parameter/behavior/action consumers and exact inverse")
    alignment_review = intermediate / "ai-parameter-alignment-verification.json"
    run("verify_character_ai_parameter_alignment.py", "--before", character_ai, "--after", ai_aligned,
        "--source", args.wsc15, "--owner", output / "character-ai-tables.json", "--report", alignment_review)
    require_hash(alignment_review, "34CB670213FC84344BB76C6052E812DEAB079DC78F85AC46211D8DC389677664",
                 "ARM7-aware source halfword loads and aligned parameter consumers")
    iraira_review = intermediate / "iraira-render-verification.json"
    run("verify_iraira_render_consumers.py", "--before", ai_aligned, "--after", iraira_render,
        "--source", args.wsc15, "--manifest", output / "iraira-render.json",
        "--alignment-owner", output / "character-ai-parameter-alignment.json", "--report", iraira_review)
    require_hash(iraira_review, "0112FDCC4B6EB2A64DB67A22CB57583847840FEC6A96DA11ACB91614702DABCC",
                 "source Iraira graphics, palette and display ownership")
    mode20_review = intermediate / "mode20-title-assets-verification.json"
    run("verify_mode20_title_assets.py", "--before", iraira_render, "--after", mode20_title,
        "--source", args.wsc15, "--owner", output / "iraira-render.json", "--report", mode20_review)
    require_hash(mode20_review, "94DCC785AD5CF8305F4B0B95143E82AC82C9DE46D123FDF659FCC1F63BAB10F2",
                 "source title assets in native return-to-title continuation")
    outer_review = intermediate / "iraira-outer-palette-verification.json"
    run("verify_iraira_outer_palette_route_portable.py", "--before", mode20_title, "--after", candidate,
        "--source", args.wsc15, "--report", outer_review)
    require_hash(outer_review, "C095EBCB4238A058BA763C2C322E70EF59B0D0C348B19F6282AD3034A10C1C8B",
                 "source Iraira outer display dispatch and complete palette consumer")
    glyphs = intermediate / "digicode-font.json"
    language_inventory = intermediate / "language-native-inventory.json"
    digicode_review = intermediate / "digicode-resource-verification.json"
    run("digicode_glyphs.py", glyphs)
    require_hash(glyphs, "ABDFB29C40C3C8F38BB64214B1F3695FED4774C32362A6ACC1F4EE5D90029EEA", "Digicode pixel identities")
    title_review = intermediate / "title-language-verification.json"
    run("verify_title_language.py", character_recovery, title_language, args.gba, args.wsc10, args.wsc15,
        args.font, args.font_license, output / "title-language.json", title_review, "--digicode-font", glyphs)
    require_hash(title_review, "9974145ADB151ABE505E0CB09467C38342DE899CBEC848740999BC4534FCC724", "independent title review")
    run("analyze_language_consumers.py", args.gba, args.wsc10, args.wsc15, selection_index, language_inventory)
    require_hash(language_inventory, "9B0E4A7C563C5F9497F02FAAFAADB5314D6CEDF5A00C6314AA62A11C24E9AD21", "native language inventory")
    run("verify_digicode_resource.py", language_options, output / "options-language-selector.json", glyphs, language_inventory, digicode_review)
    require_hash(digicode_review, "947522802723845EF01DD7090F5F39D3BF6D06BA1209FE6BDB42EE11633DA05F", "independent Digicode resource review")
    run("analyze_shoot_sram_boundary.py", args.wsc15, "--output", sram_boundary)
    require_hash(sram_boundary, SHOOT_SRAM_BOUNDARY_SHA256, "Shoot unresolved SRAM observer evidence")
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
            "exact current integration candidate with four source evolution scores and original waveforms; "
            "existing production music stop/return behavior retained, audible parity not claimed; "
            "including the five-state "
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
            "the source-bound auxiliary-object constructor binds "
            "WSC Ver. 1.5 ES:071E through the commercial 1.0 ID-0x343/pool-5 lineage "
            "to native GBA slot 0x03004D3C and installed Shoot rule resources; the "
            "resident 26-entry upper-state population translates 2320 source code bytes, "
            "its fourth P2 record, intro palette table, target table, native RNG role, "
            "and internal state transitions; the final resident boundary layer connects both 9908 "
            "calls to same-update SELECT/APPLY; a later source-conditioned route connects the scene, and a dependent layer corrects inverted "
            "P1/P2 constructor arguments in the child and auxiliary components and inverted "
            "auxiliary player links, then installs source 71D1..7394 player binding with "
            "a fifteen-entry HP table and allocation-free reuse of the existing auxiliary body; "
            "at that historical layer the phase assigns upper entry 7792 internally without an external caller; "
            "a subsequent dependent repair corrects five P0 descriptor pointers and installs "
            "all 46 source far descriptors and 393 missing tiles, preserving code and layouts; "
            "the legacy zero-descriptor artifacts remain historical intermediates only; "
            "the final dependent layer fixes three additional-character physics pointers "
            "and installs resident source 73F0..74A2 other-player restoration using native "
            "character resources, the existing OBJ palette mirror and 32-bit physics pointers; "
            "at that historical layer this second player phase awaited complete initialization; "
            "two further resident resource segments implement source 7394..73A9 OBJ slot-5 "
            "palette loading and 74A2..74DA native HUD tile-3FC/palette-6 loading plus scroll reset; "
            "they reuse exact commercial HUD pixels and had no external caller at that historical layer; "
            "new resident controller selection/application components preserve the 64-way source "
            "decision table and RNG cardinality without connecting absent callbacks; palette "
            "operations preserve selective backup, split BG/OBJ row consumers and source-channel "
            "cadence, with exclusive scene ownership still an unfulfilled caller precondition; "
            "initializer components add native graphics resets, stage manager preparation, "
            "the source timer in commercial native units, the proven 0660 clear and two "
            "constructor adapters with independently relocated per-item P1 records; "
            "the next layers append CF/D1 native scores with explicit timbre/stereo/modulation limits, "
            "33 lower rule routines with a bounded spatial-domain guard, and dedicated graphics/HUD/IRQ "
            "initialization; compact palette state repairs writes beyond the original 32-byte owner "
            "and preserves the adjacent live AI state; actual-stage bounds and palette consumers are "
            "hooked with legacy paths preserved; the actual C9:383F stage-loader source fixes "
            "the Shoot palette/tile bank offset and installs all twelve maps with original "
            "two-by-three geometry in the existing native background consumers; "
            "the source 0E0B main stage update is connected with its original state owner, "
            "source-corrected normal display/IRQ preserve the flag-0400-clear path; a late prepared-queue "
            "guard connects the stationary base0 terminal family to the source transition IRQ, "
            "retaining prior queued callbacks on rejection; seventeen terminal phases, native result "
            "consumers and four upper-state same-update repairs are resident; the stage11 fatal "
            "callback selector, nonfatal palette path and source-conditioned external scene entry are connected; "
            "the presentation target survives native angle calls, stage11 omits the ordinary score HUD, "
            "and all eight child command rectangles resolve against their own source P1 resource; "
            "SRAM observer analysis remains explicitly UNRESOLVED_OBSERVER; general terminal "
            "interrupted-DI and moving-player camera domains remain unfulfilled; "
            "the final repair binds both Shoot backgrounds to the complete source collision grid "
            "and executes terminal 197A in the successful 193B invocation; "
            "the next repair follows the actual noncontiguous source physics pointer table "
            "for IDs 12..14 while retaining corrected native pointers; callback 6 selector 13 "
            "now uses the expanded presentation view to prevent out-of-table resource reads; "
            "complete P0 descriptor tails and companion graphics are installed; five bounded native scores "
            "and all fourteen added-character P1 containers are installed, with 544 source events "
            "and 2742 commands; four canonical resource groups now bind 46 preserved retail "
            "and 14 added records, complete palettes and companion P4, with native evolution views; "
            "callback6 preserves source position, two flag writes, event0 and palette13; "
            "selection portrait palette DMA now resolves the actual table and hardware destination; "
            "the relocated ordinary fighter spawner resolves native stage state before source-backed coordinates; "
            "three complete added-stage collision grids bind five native descriptors, with a bounded twelve-row "
            "floor classification table; spawn selects the existing logical-stage service; "
            "clean Ver.1.5 mode now uses the source eleven-encounter campaign, RNG row and CPU table, "
            "with authoritative stage getters, extended progress-indexed AI and decimal round labels; "
            "Train binds all36 source maps and100 descriptors to two native backgrounds, restores "
            "the twelve-row camera table, and uses the proven palette and display-snapshot owners; "
            "source Train shake update reachability and native private state remain unproved; "
            "Iraira class14 now invokes the source-backed launch trigger, quiet initial/wait phases "
            "and eight bounded scores, with two effect consumers using the same logical stage; "
            "ID13 automatic aerial entry and four source callbacks connect through all three shared fall consumers; "
            "shared field aliases and native special-air units are preserved; audio timbre parity remains unimplemented; "
            "three roster consumers use immutable expanded lists without overwriting the native "
            "selection presentation handle; source alternate-mode roster policy remains unchanged; "
            "VS names append two source layouts to the retained native font, and the palette-only "
            "selection path resolves the fighter ID from the same immutable roster views; "
            "Waterfall restores source layer ownership, display phase and bounded palette state; "
            "the indexed damage follow-up view covers all fifteen source fighters; "
            "Options supports English, Japanese, Korean and Japanese-reading Digicode with "
            "a native owned selector task and checked save failure paths; other text consumers "
            "and whole-game localization remain incomplete; "
            "fourteen input action tables cover fifteen source fighters and the four "
            "source-changed ID11 evolution actions while preserving existing native descriptors; "
            "the separate thirteen-row recovery table now covers all fifteen source fighters; "
            "the five existing title labels select English, source Japanese, Korean or Japanese-reading Digicode; "
            "four indexed hit/follow-up views cover fifteen fighters, including source variant8 across the original record blocks; "
            "two result-pose byte-pair views preserve the source win/lose events for all fifteen fighters; "
            "the third Waterfall pattern binds its source mode3 constructor and shared continuations, with corrected successor-row clearing; "
            "two manager lookups retain dedicated logical stage11 priority; "
            "a disconnected initializer chain covers preparation, stage manager, player phase, slot5 palette and the owned0660 clear in source phase order; "
            "two ordered source SRAM halfword clears use native EEPROM block25 with separate read-modify-write operations, "
            "preserving the other six API-buffer bytes per write under the initialized functional-backend contract; "
            "existing other-player, HUD/scroll and selective palette phases then run in source order through7534; "
            "the earlier snapshot and exclusive palette ownership remain caller preconditions, and source observers remain unresolved; "
            "all source-defined normal8EF3pattern selections are represented, including exhaustedXtable paths, "
            "while unrelated source control transfers remain unresolved; "
            "source Shoot attack types1A/1B now have native typed consumers, no-freeze reaction constructors "
            "and the retained HP/orb helper without changing old dispatch destinations; "
            "general menu and scene families beyond the verified base0 route, "
            "unverified controller cases, unresolved player spatial lifetimes, audible timbre parity, "
            "playback and runtime validation, "
            "remaining Ver. 1.5 content completion, and final QA excluded"
        ),
        "title_and_result": {
            "result_verification_sha256": "50351DA73917A2884CAAC4AFDAC40FFB6E1F42E8EE5B30D34B5B9EF064C5775F",
            "title_background_verification_sha256": "1D2AF8B349E42701DD85BA59B1111E1ED3C88E5AF7C7AB3B3F0DEC289800C665",
            "result_art_sha256": "8BFC3960335EDD29ECEBFA2DB7A673FDE586C6B5B79B0FDB47622BC601083074",
            "scope": "Source 1.5 title BG and existing mode8 four-language result labels; additional menu tree and whole-game localization remain open",
        },
        "resident_callers": {
            "verification_sha256": "B079E66FA7DE910679E6D83539F8EAABF2BD1642A4B65D98F7140D10B67062F5",
            "controller_entry": "085C6500", "exit_router_entry": "086FC300",
            "declared_bytes": 96, "changed_bytes": 90,
            "external_hooks_changed": False,
            "scope": "Synchronous SELECT/APPLY and exact stage11 terminal routing; source-conditioned base0 entry is connected, with broader lifetime contracts still open",
        },
        "resident_controller_bridge": {
            "boundary": "085C0A00", "target": "085C6500", "declared_bytes": 4,
            "verification_sha256": "ACCAA6312E68606199B35F5588BEE28C860F0AF6CD9C051636A02A61C4053525",
            "producer_domain_sha256": "5DBB2620877D5ADEE92338B87B285610914CA07F2C484077846A602EDA707B46",
            "producer_domain_closed": False, "external_scene_route_installed_by_this_layer": False,
            "scope": "Internal call chain only; actual Shoot entry and coupled player X/Y lifetime remain unproved",
        },
        "shoot_attack_dispatch": {
            "types": ["1A", "1B"], "entry": "086FD000", "hook": "0836EB9C",
            "verification_sha256": "02E7819CC861561CC8E747683420294B7CB0F9A691AE2BEF4A355261F29368FD",
            "declared_bytes": 1828, "changed_bytes": 1375, "new_RAM_bytes": 0,
            "legacy_dispatch_preserved": True, "native_HP_orb_helper": "08341034",
            "external_scene_route_installed_by_this_layer": False, "historical_E5_cause_resolved": False,
            "scope": "Source new attack reactions use existing native services and converted records; actual Shoot reachability remains open",
        },
        "shoot_spatial_subset": {
            "verification_sha256": "4F5A9EDA33FF91BE70A94DB5240814ADA94EAEBD2CE2F7E6B1FCF00E729543B9",
            "declared_bytes": 28, "changed_bytes": 27,
            "source_normal_pattern_pairs": 2568421376, "newly_accepted_pairs": 963404288,
            "nonpattern_pairs_unresolved": 1726545920,
            "complete_controller_input_domain": False, "external_scene_route_installed_by_this_layer": False,
            "scope": "All source-defined normal patterns now represented; source unrelated control transfers and producer reachability remain open",
        },
        "shoot_static_companion_clear": {
            "verification_sha256": "DF06DEBA3B9BF1B405F6BFE81DE3188DC6002F935723491DEB45A0AB999422CC",
            "declared_bytes": 984, "changed_bytes": 964, "new_RAM_bytes": 0,
            "camera_subset": [261, 288], "static_companion_resources": 30,
            "storage": "existing terminal payload+52",
            "complete_terminal_clear": False, "external_scene_route_installed_by_this_layer": False,
            "scope": "Fixed-base49 static companion tiles and source preload expiration; primary parity, other owners, IRQ and entry remain open",
        },
        "shoot_projectile_clear": {
            "verification_sha256": "95458CCEBEBDBCD5BE5D2CE703D32490F106629BE58DDEAAC280203DA0830C38",
            "reload_proof_sha256": "2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990",
            "declared_bytes": 80, "changed_bytes": 73, "new_RAM_bytes": 0,
            "source_resource": "93E7", "native_P0": "085DB300", "fixed_tile_base": 109,
            "complete_terminal_clear": False, "external_scene_route_installed_by_this_layer": False,
            "full_post_clear_reload_exclusion_approved": False,
            "scope": "Static93E7 tiles under the retained normal callback graph; side1 companions, other owners, IRQ and entry remain open",
        },
        "shoot_guarded_transition": {
            "verification_sha256": "555554FDADF48C80F74DE2A9700B7ECD6FC798F859C151B6A4AC440A9C6925FB",
            "layout_ledger_sha256": "89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33",
            "declared_bytes": 1576, "changed_bytes": 1550, "new_RAM_bytes": 0,
            "queue_copy_hook": "080D0BE8", "transition_IRQ": "086FFE10",
            "source_DI_value_emulated": False, "low_Y_moving_family_closed": False,
            "external_scene_route_installed_by_this_layer": False,
            "scope": "Late copied-queue selection for the stationary base0 terminal family, current blank rows across all160 native lines and a mode7 callback guard; other families retain their prior queue",
        },
        "shoot_fatal_callback_route": {
            "verification_sha256": "61656691CD4126193003FB2E43B851F3CAA57A8C6C78A147ED602B181F2F2FD4",
            "hook": "0836E5EC", "existing_adapter": "085CD960",
            "declared_bytes": 4, "changed_bytes": 4, "new_code_bytes": 0, "new_RAM_bytes": 0,
            "non11_retail_behavior_retained": True, "nonfatal_hook_installed_by_this_layer": False,
            "external_scene_route_installed_by_this_layer": False, "historical_E5_cause_resolved": False,
            "scope": "Stage11 lethal kind3 damage selects the resident upper and linked-auxiliary callbacks; native HP arithmetic and common continuation are preserved",
        },
        "shoot_native_scene_connection": {
            "verification_sha256": "37812C30D6A1EA005F48CB1E3298D38FBCD795008A614CEEA9339679B16B75B8",
            "declared_bytes": 152, "changed_bytes": 136, "new_RAM_bytes": 0,
            "external_scene_route_installed": True, "nonfatal_hook_installed": True,
            "entry_hook": "0833FD04", "nonfatal_hook": "0836E634",
            "source_conditioned_entry": True, "presentation_receiver_preserved": True,
            "stage11_score_HUD_omitted": True, "final_port_complete": False,
        },
        "shoot_child_command_rectangles": {
            "verification_sha256": "BAD282D7F5AEAC391022D3A3C350C4257A6BC15A901406EC29F875CEDFB4DACA",
            "declared_bytes": 42, "changed_bytes": 34, "source_payloads_checked": 163,
            "relocated_command_pointers": 8, "null_command_pointers_unchanged": 155,
            "source_rectangle": "3D1F3C", "native_rectangle": "085B9180",
            "legacy_dispatch_unchanged": True, "historical_E5_cause_resolved": False,
        },
        "shoot_palette_dim_calls": {
            "verification_sha256": "94F9FD0FC4B95F64CA7BFB4F424DF333EF29170B8CDA32A1CA2FB4BEF0BDC840",
            "declared_bytes": 16, "changed_bytes": 12, "new_RAM_bytes": 0,
            "conditional_calls": 4, "existing_helper": "085C6FD4",
            "self_targeting_calls_removed": True,
        },
        "shoot_terminal_owner_link": {
            "verification_sha256": "8CE38E626C7629F4A1F2ABB041B55B85B94AD71809CC1B8EA8C1F8F338AF27A3",
            "declared_bytes": 4, "changed_bytes": 1, "new_RAM_bytes": 0,
            "guard_site": "086FFC00", "auxiliary_owner_offset": 40,
            "other_guard_predicates_unchanged": True, "final_port_complete": False,
        },
        "shoot_terminal_display_epoch": {
            "verification_sha256": "AFC67C96B20744286BEC58BA05313808A7CE22D3788E05E6B2385874A8ADCE65",
            "declared_bytes": 84, "changed_bytes": 69, "new_RAM_bytes": 0,
            "additional_stack_bytes": 0, "consumption_entry": "086FF720",
            "planned_mapping_checked": True, "live_display_fields_rechecked": True,
            "earliest_compare_runtime_verified": False, "final_port_complete": False,
        },
        "impmon_evolution_contact": {
            "mode_scope": "source flag-clear default Ver.1.5 mode; alternate mode not implemented",
            "declared_bytes": 4, "changed_bytes": 1, "boss_identity_15_excluded": True,
            "actual_runtime_evolution_verified": False, "final_port_complete": False,
        },
        "evolution_transition_tables": {
            "playable_identities": 15, "tables": 3, "declared_bytes": 114, "changed_bytes": 109,
            "old_identities_0_to_10_preserved": True, "source_events_and_native_bounds_verified": True,
            "actual_runtime_verified": False, "historical_e5_cause_proven": False, "final_port_complete": False,
        },
        "id13_air_relaunch": {
            "verification_sha256": "AF427CBB5E7FCD208D20E624CD907DDF4F3A3573408A67AD8272FB198DFFD6C0",
            "source_entry_sites": 4, "native_entry_sites": 3, "callbacks": 4,
            "declared_bytes": 988, "changed_bytes": 968, "new_RAM_bytes": 0,
            "actual_runtime_verified": False, "wall_clock_parity_verified": False,
            "final_port_complete": False,
        },
        "campaign_progression": {
            "producer_verification_sha256": "1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0",
            "consumer_verification_sha256": "3E22A59DD56C2A5EF6F61FABDCACEEA62174636EDACE6BAEB1D7BACCB3FE9A84",
            "mode_scope": "source config+25 mask0001 clear; alternate-mode owner remains unimplemented",
            "encounters": 11, "RNG_rows": 8, "ordinary_CPU_entries": 11,
            "initial_AI_entries": 13, "AI_entries_per_difficulty": 12, "difficulty_rows": 3,
            "declared_bytes": 453, "changed_bytes": 423, "new_RAM_bytes": 0,
            "temporary_character_stage_override_removed": True, "dedicated_stage11_preserved": True,
            "actual_runtime_verified": False, "whole_campaign_runtime_verified": False,
            "final_port_complete": False,
        },
        "type8_reaction_tables": {
            "verification_sha256": "0A5EB8355D74AF38C61A90C74ECAD636BDCF6250066C786119DC4EC2513C8896",
            "source_identities": 15, "tables": 4, "native_pointer_readers": 5,
            "declared_bytes": 260, "changed_bytes": 255, "new_RAM_bytes": 0,
            "native_action_records_and_code_preserved": True,
            "actual_runtime_verified": False, "whole_campaign_runtime_verified": False,
            "final_port_complete": False,
        },
        "character_ai_tables": {
            "verification_sha256": "B1B21A1C119028B2EBD70602BCCB82F6580CF02A38932E69EB58187A7B885FC7",
            "parameter_rows": 10, "parameter_bytes_per_row": 17,
            "behavior_rows": 10, "behavior_bytes_per_row": 384,
            "action_records": 264, "action_bytes_per_record": 18,
            "declared_bytes": 8890, "changed_bytes": 8128, "new_RAM_bytes": 0,
            "dedicated_stage7_boss_skips_ordinary_initializer": True,
            "retained_native_source_exception": "action42 +0C input mask007E instead of sourceFF7E",
            "actual_runtime_verified": False, "whole_campaign_runtime_verified": False,
            "final_port_complete": False,
        },
        "ai_parameter_alignment": {
            "verification_sha256": "34CB670213FC84344BB76C6052E812DEAB079DC78F85AC46211D8DC389677664",
            "source_bytes_per_row": 17, "native_bytes_per_row": 18, "rows": 10,
            "declared_bytes": 244, "changed_bytes": 196, "new_RAM_bytes": 0,
            "restores_source_halfwords_on_odd_rows": True,
            "supersedes_flat_read_model_for_parameter_loads": True,
            "actual_runtime_verified": False, "final_port_complete": False,
        },
        "iraira_render": {
            "verification_sha256": "0112FDCC4B6EB2A64DB67A22CB57583847840FEC6A96DA11ACB91614702DABCC",
            "source_tiles": 512, "source_maps": 8, "initial_palette_colors": 111,
            "animated_palette_colors": 38, "palette_counters": 5,
            "declared_bytes": 25382, "changed_bytes": 23155, "new_RAM_bytes": 0,
            "actual_runtime_verified": False, "final_port_complete": False,
        },
        "mode20_title_assets": {
            "verification_sha256": "94DCC785AD5CF8305F4B0B95143E82AC82C9DE46D123FDF659FCC1F63BAB10F2",
            "declared_bytes": 60, "changed_bytes": 58, "new_RAM_bytes": 0,
            "mode23_implemented": False,
            "native_timing_and_task_handshake_retained": True,
            "actual_runtime_verified": False, "final_port_complete": False,
        },
        "iraira_outer_palette": {
            "verification_sha256": "C095EBCB4238A058BA763C2C322E70EF59B0D0C348B19F6282AD3034A10C1C8B",
            "declared_bytes": 64, "changed_bytes": 63, "new_RAM_bytes": 0,
            "replaces_stage10_legacy_stage3_display_dispatch": True,
            "retains_source_common_font_overlay": True,
            "actual_runtime_verified": False, "final_port_complete": False,
        },
        "original_evolution_music": {
            "source_groups": [56, 60, 64, 248], "native_songs": [108, 109, 110, 111],
            "source_channels": 16, "notes": 1917, "prior_song_entries_preserved": 108,
            "input_size": 8388608, "output_size": 16777216,
            "music_changed_bytes": 104216, "test_stop_suppression": False,
            "pause_cache_declared_bytes": 24, "pause_cache_changed_bytes": 23,
            "pause_cache_additional_ids": [108, 109, 110, 111],
            "pause_resume_gameplay_runtime_verified": False,
            "representation_limits": "tempo, pitch/pan quantization, waveform restart and vibrato phase",
            "full_audible_parity_verified": False, "final_port_complete": False,
        },
        "resident_scene": {
            "verification_sha256": "AC1D7CCFBC2753D1439B2AFCA364240F7AFC0D26C1E030860898B82ED99DD15D",
            "initializer_entry": "08629800", "phase_12C6_entry": "085C9B00",
            "external_route_installed": True, "controller_boundary_connected": True,
            "scope": "22 source-ordered resident scene placements with the source-conditioned external route and observed healthy controller activation; general camera/IRQ and terminal domains remain gates",
        },
        "sources": {
            "gba_usa_sha256": GBA_SHA256,
            "wsc_10_sha256": WSC10_SHA256,
            "wsc_15_sha256": WSC15_SHA256,
            "options_font_sha256": FONT_SHA256,
            "options_font_license_sha256": FONT_LICENSE_SHA256,
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
            "shoot_lower_audio_verification_sha256": SHOOT_LOWER_AUDIO_VERIFICATION_SHA256,
            "shoot_lower_rules_verification_sha256": SHOOT_LOWER_RULES_VERIFICATION_SHA256,
            "shoot_graphics_verification_sha256": SHOOT_GRAPHICS_VERIFICATION_SHA256,
            "shoot_transition_audio_sha256": SHOOT_TRANSITION_AUDIO_SHA256,
            "shoot_scene_objects_sha256": SHOOT_SCENE_OBJECTS_SHA256,
            "shoot_stage_asset_verification_sha256": SHOOT_STAGE_ASSET_VERIFICATION_SHA256,
            "shoot_stage_handshake_verification_sha256": SHOOT_STAGE_HANDSHAKE_VERIFICATION_SHA256,
            "shoot_terminal_verification_sha256": SHOOT_TERMINAL_VERIFICATION_SHA256,
            "shoot_normal_display_verification_sha256": SHOOT_NORMAL_DISPLAY_VERIFICATION_SHA256,
            "shoot_spatial_repair_verification_sha256": SHOOT_SPATIAL_REPAIR_VERIFICATION_SHA256,
            "character_physics_routing_verification_sha256": CHARACTER_PHYSICS_ROUTING_VERIFICATION_SHA256,
            "opening_presentation_routing_verification_sha256": OPENING_PRESENTATION_ROUTING_VERIFICATION_SHA256,
            "shoot_sram_boundary_unresolved_sha256": SHOOT_SRAM_BOUNDARY_SHA256,
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

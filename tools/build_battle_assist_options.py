"""Install the seven-row Options list, four localized assist screens and persistent settings."""

import argparse
import json
import struct
from pathlib import Path

import battle_assist_art as art
import battle_assist_menu as menu
import battle_assist_storage as storage
from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_options_korean_poc import FONT_SHA
from build_options_selector import branch
from mode23_linker import compose

PARENT = "D432DBE9B221A0EFC15B644B8E76A0D39D374DFF1087165A917EF977A3E8BD99"
OWNER = "55390CB7C04E02AFC82BF38F9574BBAB234AC4E3B9316876F6E90D61DF6C553D"
NATIVE_DRAW = (0xc343c,0xc3508,0xc3738,0xc3844,0xc39f0,0xc3bd8,0x633d90)


def build(image, prior_owner, font):
    assert (sha(image),sha(prior_owner),sha(font)) == (PARENT,OWNER,FONT_SHA)
    parent=json.loads(prior_owner)
    prior=parent["prior_excluded_extents"] + [[a["start"],a["end"]] for a in parent["allocations"]]
    allocator=Allocator(image)
    exclude(allocator,prior)
    changes=[]

    def install(name, assemble):
        example, *_=assemble(BASE)
        at=allocator.allocate(len(example),name,4)
        data,*info=assemble(BASE+at)
        assert len(example)==len(data)
        changes.append((at,data))
        return info

    api,storage_link=install("single-block battle assist settings",storage.assemble)
    assert api["assist_read"]==0x08dcc204
    assets=[]
    for lang in range(4):
        info,=install("assist page "+str(lang),lambda addr:art.resource(font,lang,addr-BASE))
        assets.append(info)
    body=menu.assembly(assets,api)
    symbols,menu_link=install("native options and assist controls",lambda addr:compose((body,),addr,menu.EXPORTS))

    def replace(at,old,new):
        assert image[at:at+len(old)]==old and len(new)==len(old), hex(at)
        changes.append((at,new))

    def word(value):
        return struct.pack("<I",value)

    for at in NATIVE_DRAW:
        replace(at,branch(at,0x12c28),branch(at,symbols["assist_draw_guard"]-BASE))
    replace(0xc328c,branch(0xc328c,0x633800),branch(0xc328c,symbols["assist_input"]-BASE))
    replace(0x633abc,word(0x08633e00),word(symbols["assist_tick"]))
    replace(0x633a30,word(0xe3a0203e),word(0xe3a02040))
    result=bytearray(image)
    end=0
    for at,data in sorted(changes):
        assert at>=end
        end=at+len(data)
        result[at:end]=data
    inverse=result[:]
    for at,data in changes:
        inverse[at:at+len(data)]=image[at:at+len(data)]
    assert inverse==image
    return result,dict(input_sha256=PARENT,output_sha256=sha(result),prior_owner_sha256=OWNER,source_sha256=parent["source_sha256"],
        storage_exports=parent["storage_exports"],symbols={**api,**symbols},font_sha256=FONT_SHA,
        prior_excluded_extents=prior,allocations=allocator.allocations,
        link_checks=[storage_link,menu_link],assets=assets,
        assist_storage=dict(eeprom_block=34,magic="BAS1",value="0=off, 1..1000=0..999; bit 10 = boss HP 1",
                            options_payload_private_bytes=[248,256],global_ram_bytes=0),
        modules={p.name:sha(p.read_bytes()) for p in (Path(__file__),Path(art.__file__),
                    Path(menu.__file__),Path(storage.__file__))},whole_image_inverse=True,
        writes=[dict(offset=at,size=len(data),before_sha256=sha(image[at:at+len(data)]),
                 after_sha256=sha(data)) for at,data in sorted(changes)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("input","owner","font","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    a=parser.parse_args()
    result,record=build(a.input.read_bytes(),a.owner.read_bytes(),a.font.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"component.gba").write_bytes(result)
    path=a.output/"manifest.json"
    path.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(record["output_sha256"],sha(path.read_bytes()))


if __name__=="__main__":
    main()

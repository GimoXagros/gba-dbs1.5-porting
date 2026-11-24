"""Extend the ending animation pointer table with the missing Ver. 1.5 Extra Guilmon sequence."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def build(before, source, owner, pinned_parent, pinned_owner):
    parent = json.loads(owner)
    assert sha(before) == parent["output_sha256"] == pinned_parent and sha(owner) == pinned_owner
    assert sha(source) == SOURCE
    offsets = struct.unpack_from("<6H", source, 0x77ADEF)
    assert offsets == (0xEAB, 0xEB3, 0xEB7, 0xEBF, 0xEC7, 0xECF)
    assert 0x779F50 + offsets[5] == 0x77AE1F
    sequence = source[0x77AE1F:0x77AE23]
    assert sequence == struct.pack("<2H", 0x6C, 0xFFFF)
    pointers = struct.unpack_from("<5I", before, 0xC08DC)
    assert pointers == (0x080C08F0, 0x080C08F4, 0x080C08F8, 0x080C0900, 0x080C0904)
    assert struct.unpack_from("<I", before, 0xC08F0)[0] == 0xFFFF005C
    literal = 0xC0C60
    assert struct.unpack_from("<I", before, literal)[0] == BASE + 0xC08DC
    assert before[0xC0A24:0xC0A3C] == bytes.fromhex("bc51d1e1075055e20551b0e128929fe5095095e0005095e5")
    inherited = parent["prior_excluded_extents"] + [[e["start"],e["end"]] for e in parent["allocations"]]
    space = Allocator(before)
    exclude(space,inherited)
    at = space.allocate(28, "ending animation selectors for fighter IDs 7 through 12", 4)
    assert all(at+28 <= a or b <= at for a,b in inherited)
    table = struct.pack("<6I", *pointers, BASE+at+24) + sequence
    data = bytearray(before)
    writes = []
    for offset, replacement in ((at,table), (literal,struct.pack("<I",BASE+at))):
        original = before[offset:offset+len(replacement)]
        data[offset:offset+len(replacement)] = replacement
        writes.append(dict(offset=offset,size=len(replacement),before_sha256=sha(original),after_sha256=sha(replacement)))
    result = bytes(data)
    return result,dict(input_sha256=pinned_parent,output_sha256=sha(result),source_sha256=SOURCE,prior_owner_sha256=pinned_owner,
                       prior_excluded_extents=inherited,allocations=space.allocations,storage_exports=parent["storage_exports"],
                       writes=writes, source_table=0x77ADEF,source_sequence=0x77AE1F,
                       native_literal=literal,table=at,builder_sha256=sha(Path(__file__).read_bytes()))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ("input","source","owner","output"):
        parser.add_argument("--"+arg,type=Path,required=True)
    for arg in ("input-sha256","owner-sha256"):
        parser.add_argument("--"+arg,required=True)
    a=parser.parse_args()
    rom,manifest=build(a.input.read_bytes(),a.source.read_bytes(),a.owner.read_bytes(),a.input_sha256,a.owner_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"component.gba").write_bytes(rom)
    path=a.output/"manifest.json"
    path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(sha(rom),sha(path.read_bytes()))

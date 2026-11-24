"""Use the original fourth opening pair and bind the added scenes' skip to the live fade timer."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SOURCE_RANGES = (
    (0x7593ce, 0x75940c, '28AF0E38FCACA54C37282E08D829341354042FDCAFC2393EEE3FFC51B3EC460C'),
    (0x75a58c, 0x75a59a, 'F25B6943E39012C66562CC551206671807FFFDC8D71DE9DB08C1ED519264D382'),
    (0x740560, 0x7405a0, '2A26B92770B63E8AD89A9A379F49BEED567CB8D54D79E8C6AF53758DE16B8245'),
    (0x757623, 0x75762e, 'C2DFD9645965220ED250EF3C851257653480DD327C5B345DA00B6007A4733864'),
    (0x75a227, 0x75a233, '8896DD761A14623B55582FA439E61C97A503DAE78DA138FC04F1E3B48C631692'),
)
NATIVE_RANGES = (
    (0x5b4100, 0x5b4258, '19B1CF5950AECE32A8F641786CFC1EA61CF5FA6D07E3387904F8EA65B8882AED'),
    (0x5b8400, 0x5b84a4, '971103B5BA9AD7CB75AA4ABD9979CBC52EC74655F9A088B03BD8BFE238022F3B'),
    (0x087e74, 0x087e8c, 'D78B7298CE53A3677021551EFD6ECDDDD82EF33D68E2B50929E7B29B52686DA9'),
    (0x60b1a0, 0x60b1e0, 'F4B784537CF9403F0D9A57C89530FCA302FE226CBCBDDA518063713A5340FA32'),
)
FIXES = (
    (0x5b4254, 0x085b5400, 0x0860b000, 'source record 30 plus selector 13 or 14'),
    (0x5b8488, 0x03002338, 0x0300267c, 'live terminal fade duration and elapsed time'),
)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def build(source, image, owner_bytes, input_sha, owner_sha):
    owner = json.loads(owner_bytes)
    assert sha(source) == SOURCE and sha(owner_bytes) == owner_sha
    assert len(image) == 0x1000000 and sha(image) == owner['output_sha256'] == input_sha
    for data, ranges in ((source, SOURCE_RANGES), (image, NATIVE_RANGES)):
        for lo, hi, expected in ranges:
            assert sha(data[lo:hi]) == expected
    after = bytearray(image)
    writes = []
    for offset, old, new, label in FIXES:
        assert struct.unpack_from('<I', image, offset)[0] == old
        struct.pack_into('<I', after, offset, new)
        writes.append(dict(offset=offset, size=4, purpose=label, before_sha256=sha(image[offset:offset+4]),
                           after_sha256=sha(after[offset:offset+4])))
    inverse = after[:]
    for offset, old, _, _ in FIXES:
        struct.pack_into('<I', inverse, offset, old)
    assert inverse == image
    occupied = owner['prior_excluded_extents'] + [[r['start'],r['end']] for r in owner['allocations']]
    return after, dict(input_sha256=input_sha, prior_owner_sha256=owner_sha, source_sha256=SOURCE,
                       output_sha256=sha(after), builder_sha256=sha(Path(__file__).read_bytes()),
                       storage_exports=owner['storage_exports'], prior_excluded_extents=occupied,
                       allocations=[], writes=writes, whole_image_inverse=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','input','owner','output'):
        p.add_argument('--'+key,type=Path,required=True)
    for key in ('input-sha256','owner-sha256'):
        p.add_argument('--'+key,required=True)
    a=p.parse_args()
    rom,report=build(a.source.read_bytes(),a.input.read_bytes(),a.owner.read_bytes(),a.input_sha256,a.owner_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(rom)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(report['output_sha256'],sha(manifest.read_bytes()))


if __name__=='__main__':
    main()

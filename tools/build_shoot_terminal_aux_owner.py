"""Apply the terminal Shoot visibility field on the registered five-page record build."""
import argparse
import json
from pathlib import Path
from apply_shoot_terminal_aux_visibility import apply, digest

PARENT = 'F824434CBEE46F3BBFE59DF95038B618C2F534274CC44A59B0FB0B9C477E599B'
OWNER = '4270D744333694EBF8F363975A221D54D95006D6FBAACDB8566440B2353C9AB3'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','input','owner','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    before=a.input.read_bytes()
    owner=a.owner.read_bytes()
    assert digest(before)==PARENT and digest(owner)==OWNER
    parent=json.loads(owner)
    assert parent['output_sha256']==PARENT
    after,proof=apply(before,a.source.read_bytes())
    assert len(proof['writes'])==1
    change=proof['writes'][0]
    at=change['offset']
    assert len(bytes.fromhex(change['before']))==len(bytes.fromhex(change['after']))==12
    assert after[:at]+bytes.fromhex(change['before'])+after[at+12:]==before
    # The fixed-site guard needs no allocation. All live placements still belong
    # to their original scenes, including their reserved but erased padding.
    proof.update(prior_owner_sha256=OWNER,storage_exports=parent['storage_exports'],
        prior_excluded_extents=parent['prior_excluded_extents']+[[r['start'],r['end']] for r in parent['allocations']],
        allocations=[],whole_image_inverse=True)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(after)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(proof['output_sha256'],digest(manifest.read_bytes()))


if __name__=='__main__':
    main()


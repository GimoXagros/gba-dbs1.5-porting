"""Replay the actual earned Master and a separate cold boot after the campaign particle patch."""
import argparse
import json
from pathlib import Path

from run_mode11_tag_presentation import OWNER as PRESENTATION_OWNER, ROOT, run
from build_mode11_source_particles import ENTRY, PARENT, PARTICLES
from verify_mode23_completion_save import sha

OWNER = '07A7EA616C71FE39DB3EE8B7235D32C577253DE88EDD9FEF5C94EB54D8A608B4'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','owner','presentation-owner','output'):
        p.add_argument('--'+name, type=Path, required=True)
    a=p.parse_args()
    raw=a.owner.read_bytes()
    meta=json.loads(raw)
    assert sha(raw)==OWNER and meta['input_sha256']==PARENT
    image=a.rom.read_bytes()
    assert sha(image)==meta['output_sha256']
    original=a.presentation_owner.read_bytes()
    assert sha(original)==PRESENTATION_OWNER
    controller=json.loads(original)['symbols']['m11_controller']
    out=a.output.resolve()
    out.mkdir()
    state=ROOT/'build/bizhawk-collection-hidden-aux-v91-20261124-b/permanent-award.State'
    save=run('award',out/'award',a.rom,state,controller)
    run('cold',out/'cold',a.rom,save,controller)
    for phase in ('celebration','name-confirmation'):
        iwram=(out/'award'/(phase+'-IWRAM.bin')).read_bytes()
        ewram=(out/'award'/(phase+'-EWRAM.bin')).read_bytes()
        sibling=int.from_bytes(iwram[0x3cf8:0x3cfc],'little')-0x02000000
        assert int.from_bytes(ewram[sibling:sibling+4],'little')==meta['symbols']['m11p_tick']
        assert int.from_bytes(iwram[PARTICLES-0x03000000+340:PARTICLES-0x03000000+344],'little')<30
    print('SOURCE_PARTICLE_CALLBACK_ACTIVE_DURING_EARNED_MASTER_AND_NAME; RETURN_AND_COLD_PASS')


if __name__=='__main__':
    main()


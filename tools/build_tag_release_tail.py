"""Build the earned-tag cutscene, link exchange and localized selection screens on v91."""
import json
from pathlib import Path
from build_ending_awards_main_tail import RANK,OWNER,sha,verify_writes
from mode11_special_name import EXPORTS

PINS=Path(__file__).resolve().parents[1]/'records'/'tag-release-build-v92.json'

def produce(before,owner,output,source,font,credit_font,run):
    assert sha(before.read_bytes())==RANK and sha(owner.read_bytes())==OWNER
    stages=[]
    for name,builder,options,pin_inputs in (
        ('presentation','build_mode11_tag_presentation.py',('--source',source),False),
        ('link','build_link_tag_result.py',('--source',source),True),
        ('badge','build_title_tag_badge.py',('--source',source),False),
        ('empty','build_tag_empty_locales.py',('--font',font),False),
        ('english','build_english_menu_lettering.py',(),True),
        ('credit','build_title_credit_locales.py',('--source',source,'--font',credit_font),False),
        ('id12','build_mode11_extra_award_sequence.py',('--source',source),True)):
        directory=output/name
        args=['--input',before,'--owner',owner,'--output',directory,*options]
        if pin_inputs:
            args+=['--input-sha256',sha(before.read_bytes()),'--owner-sha256',sha(owner.read_bytes())]
        run(builder,*args)
        candidate,manifest=directory/'component.gba',directory/'manifest.json'
        verify_writes(before,candidate,manifest)
        meta=json.loads(manifest.read_bytes())
        assert meta['prior_owner_sha256']==sha(owner.read_bytes())
        if name=='presentation':
            entries=[hex(meta['symbols'][label]) for label in EXPORTS]
            run('check_mode11_special_name.py',candidate,source,'--entries',*entries)
        elif name=='link':
            run('verify_link_tag_result.py','--source',source,'--prior',before,'--image',candidate,
                '--owner',manifest,'--report',directory/'cpu.json')
        elif name=='badge': run('verify_title_tag_badge_state.py',candidate,manifest)
        elif name=='empty': run('check_tag_empty_locales.py',candidate,manifest)
        elif name=='credit': run('check_title_credit_locales.py',candidate,manifest)
        elif name=='id12':
            import struct
            data=candidate.read_bytes()
            table=meta['table']
            assert struct.unpack_from('<I',data,0xC0C60)[0]==0x08000000+table
            assert data[table:table+20]==data[0xC08DC:0xC08DC+20]
            assert struct.unpack_from('<IHH',data,table+20)==(0x08000000+table+24,0x6c,0xffff)
        stages.append(dict(stage=name,sha256=meta['output_sha256'],owner_sha256=sha(manifest.read_bytes())))
        before,owner=candidate,manifest
    return stages

def expected_layers():
    rows=json.loads(PINS.read_bytes())
    paths={'ending-awards.gba':RANK,'current-candidate.gba':rows[-1]['sha256']}
    paths.update({f'intermediate/tag-release/{row["stage"]}/component.gba':row['sha256'] for row in rows})
    return paths

def install(output,source,font,credit_font,run):
    before=output/'ending-awards.gba'
    owner=output/'ending-awards.json'
    (output/'current-candidate.gba').replace(before)
    (output/'current-candidate.json').replace(owner)
    root=output/'intermediate'/'tag-release'
    rows=produce(before,owner,root,source,font,credit_font,run)
    assert rows==json.loads(PINS.read_bytes()),'Integrated layer or owner differs from verified v92'
    last=root/rows[-1]['stage']
    for src,dst in [('component.gba','current-candidate.gba'),('manifest.json','current-candidate.json')]:
        (output/dst).write_bytes((last/src).read_bytes())
    return rows

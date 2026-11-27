"""Drive D-ARK twice from the real title in a private emulator desktop, without guest writes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import time

from run_flow_release import BIZHAWK, DONOR
from run_native_play_assists import PrivateDesktopProcess, ROOT, digest

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def play(rom, expected, out, lang, fighter, donor=None):
    ws = rom.suffix.lower() == '.wsc'
    assert digest(rom) == expected and (not ws or expected == SOURCE)
    assert donor is None or digest(donor) == DONOR
    assert Path('W:/').samefile(ROOT) and out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True,exist_ok=False)
    alias = 'W:/'+out.relative_to(ROOT).as_posix()
    exe = ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert digest(exe) == BIZHAWK
    cfg = json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i,entry in enumerate(cfg['PathEntries']['Paths']):
        entry['Path'] = alias+'/data/'+str(i)
        Path(entry['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,
               SoundEnabled=False,SoundOutputMethod=3)
    (out/'config.json').write_text(json.dumps(cfg),encoding='utf8')
    saved = out/'data/104/probe.SaveRAM'
    if donor: shutil.copyfile(donor,saved)
    name='probe'+rom.suffix
    shutil.copyfile(rom,out/name)
    shutil.copyfile(Path(__file__).with_name('bizhawk_dark_wait.lua'),out/'controller.lua')
    lua=(out/'controller.lua').read_text()
    assert all(x not in lua for x in ('memory.write','savestate.','setregister','dofile','loadfile'))
    args=['--gdi','--config='+alias+'/config.json','--lua='+alias+'/controller.lua',
          f'--userdata=out:{alias};lang:{lang};fighter:{fighter}',alias+'/'+name]
    with PrivateDesktopProcess(exe,args,exe.parent) as process:
        end = time.monotonic()+300
        while not (out/'done').exists() and time.monotonic()<end: time.sleep(.25)
        if (out/'done').exists():
            assert process._wait_process(process.process.hProcess,20000)==0
    result=(out/'done').read_text() if (out/'done').exists() else 'timeout'
    report=dict(rom=digest(rom),loaded=(out/'loaded.bin').exists() and digest(out/'loaded.bin')==expected,
                result=result,language=lang,fighter=fighter,source_save=digest(donor) if donor else None,
                final_save=digest(saved) if saved.exists() else None,trace=digest(out/'events.txt'),
                capture=digest(out/'wait-2.png') if (out/'wait-2.png').exists() else None,
                visible=False,guest_writes=[])
    if result == 'PASS' and report['loaded']:
        report['visual_checks'] = check_images(out,ws)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(out.name,result,flush=True)
    assert result=='PASS' and report['loaded'],report
    return report



def check_images(out, ws):
    """Compare measured pixels independently of the observed scene/selection variables."""
    import hashlib
    from PIL import Image
    def read(name):
        with Image.open(out/(name+'.png')) as im:
            return im.convert('RGB')
    shift = 0 if ws else 8
    expected_wait = '8044ffa0bface252379330151beae2a38ac4d13cfafedec1b9b1cba0d12364c8'
    def region(image, box):
        return image.crop(tuple(value+shift for value in box))
    def rim(image):
        return b''.join(image.crop(box).tobytes() for box in
                        [(0,0,240,8),(0,152,240,160),(0,8,8,152),(232,8,240,152)])
    checks = []
    for visit in (1,2):
        scene = read(f'wait-{visit}')
        mask = bytes(all(v>170 for v in rgb)
                     for rgb in region(scene,(31,36,83,69)).get_flattened_data())
        assert hashlib.sha256(mask).hexdigest()==expected_wait and sum(mask)==233
        motion = [scene,*[read(f'motion-{visit}-{n}') for n in range(1,7)]]
        poses = len({region(im,(27,76,87,136)).tobytes() for im in motion})
        rails = len({region(im,(0,0,224,8)).tobytes() for im in motion})
        assert poses>=2 and rails>=2
        row = dict(visit=visit,visible_poses=poses,rail_positions=rails,source_wait_pixels=sum(mask))
        if not ws:
            selection = read(f'selected-{visit}')
            returned = read(f'return-{visit}')
            reference = read('title-ref-2')
            assert rim(scene)==rim(selection)==rim(returned)==rim(reference)
            # The animation clock can make PRESS START blink. The whole logo and its
            # surrounding playfield above the prompt must match, including its colors.
            upper = (8,8,232,104)
            assert reference.crop(upper).tobytes()==returned.crop(upper).tobytes()
            body = (124,16,220,144)
            selected_pixels = selection.crop(body).get_flattened_data()
            waiting_pixels = scene.crop(body).get_flattened_data()
            for selected, waiting in zip(selected_pixels,waiting_pixels):
                expected = tuple(round((round(v*31/255)//2)*255/31) for v in selected)
                assert waiting==expected,(out.name,visit,'portrait color or pixel mismatch')
            row.update(rim_pixels=6144,title_logo_pixels=224*96,portrait_pixels=96*128)
        checks.append(row)
    return checks


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('gba','wsc','earned','output'): parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--expected',required=True)
    args=parser.parse_args()
    root=args.output.resolve()
    root.mkdir(parents=True,exist_ok=False)
    jobs=[(args.wsc,SOURCE,root/'wsc',-1,1,None)]
    jobs.extend((args.gba,args.expected,root/f'{kind}-{lang}',lang,fighter,save)
                for kind,ids,save in [('fresh',(0,1,2,3),None),('earned',(9,13,14,11),args.earned)]
                for lang,fighter in enumerate(ids))
    with ThreadPoolExecutor(3) as pool:
        reports=[job.result() for job in [pool.submit(play,*entry) for entry in jobs]]
    (root/'matrix.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf8')

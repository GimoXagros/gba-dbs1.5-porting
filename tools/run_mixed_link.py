"""Launch an independently identified retail and port cartridge on mGBA's local link bus."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time

from mgba_headless_gdb_capture import PrivateDesktopProcess
from run_link_tag_capture import EXE,sha

ROOT=Path(__file__).resolve().parents[1]
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'


def run(a):
    out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and Path('W:/').samefile(ROOT)
    out.mkdir(parents=True,exist_ok=False)
    alias=(Path('W:/')/out.relative_to(ROOT)).as_posix()
    emu=next((ROOT/'local/mgba-dev-complete').glob('*/mGBA.exe'))
    assert sha(emu)==EXE
    gui=out/'mGBA.exe'
    shutil.copyfile(emu,gui)
    (out/'portable.ini').write_bytes(b'')
    (out/'qt.ini').write_text('[General]\nfirstRun=false\n',encoding='ascii')
    (out/'config.ini').write_text('[ports.qt]\naudioSync=0\nvideoSync=0\naudioBuffers=2048\nmute=1\nlogLevel=0\nvolume=0\n',encoding='ascii')
    slots=[]
    for core in (1,2):
        retail=core==a.retail_core
        image=(a.retail if retail else a.port).resolve()
        size=image.stat().st_size
        expected=RETAIL if retail else a.port_sha256
        assert sha(image)==expected and size==(0x400000 if retail else 0x1000000)
        game=out/f'player{core}.gba'
        os.link(image,game)
        save=out/f'player{core}.sav'
        donor=a.retail_save if retail else a.port_save
        if donor:
            assert donor.stat().st_size==512
            shutil.copyfile(donor,save)
        slots.append(dict(core=core,profile='retail' if retail else 'port',source=str(image),sha256=expected,
                          bytes=size,save=save.name,initial_save=sha(save) if donor else 'erased (no file)'))
    source=Path(__file__).with_name('mgba_mixed_link.lua')
    script=source.read_text(encoding='utf8')
    profiles=[int.from_bytes((a.retail if row['profile']=='retail' else a.port).read_bytes()[0x37c2a4:0x37c2a8],'little') for row in slots]
    assert profiles[0]!=profiles[1]
    for key,value in {'OUTPUT':alias,'FIRST_SIG':profiles[0],'SECOND_SIG':profiles[1],'RETAIL_CORE':a.retail_core,
                      'FIRST_ATTACKER':a.first_attacker,'LIMIT':a.limit,'SCENARIO':a.scenario}.items():
        script=script.replace('@@'+key+'@@',str(value))
    assert not any(k in script for k in ('emu:write','setRegister','loadState'))
    launch=out/'probe.lua'
    launch.write_text(script,encoding='utf8',newline='\n')
    args=['--script',f'{alias}/probe.lua',f'{alias}/player1.gba',f'{alias}/player2.gba']
    report=dict(exe_sha256=sha(gui),core_version='mGBA dev 9127-fa977ccbc8',script_sha256=sha(launch),
                input_source_sha256=sha(source),arguments=args,cartridges=slots,scenario=a.scenario,
                first_attacker=a.first_attacker,guest_writes=[],visible=False)
    with PrivateDesktopProcess(gui,args,out):
        deadline=time.monotonic()+a.timeout
        while time.monotonic()<deadline and not all((out/f'done-{n}').exists() for n in (1,2)):
            time.sleep(.2)
    for c in slots:
        n=c['core']
        loaded=out/f'loaded-{n}.bin'
        c['loaded_sha256']=sha(loaded) if loaded.is_file() else None
        c['status']=(out/f'done-{n}').read_text() if (out/f'done-{n}').exists() else 'host-timeout'
        c['save_out']=sha(out/c['save']) if (out/c['save']).is_file() else None
        assert c['sha256']==sha(out/f'player{n}.gba')
    (out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print([(c['profile'],c['status'],c['loaded_sha256']) for c in slots])
    assert all(c['loaded_sha256']==c['sha256'] and c['status']=='PASS' for c in slots)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('retail','port','output'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('retail-save','port-save'):p.add_argument('--'+k,type=Path)
    p.add_argument('--port-sha256',required=True)
    p.add_argument('--retail-core',required=True,type=int,choices=(1,2))
    p.add_argument('--first-attacker',type=int,choices=(1,2),default=1)
    p.add_argument('--scenario',choices=('match','cold','wrong','boundary','contact','locale'),default='match')
    p.add_argument('--limit',type=int,default=42000)
    p.add_argument('--timeout',type=int,default=480)
    run(p.parse_args())

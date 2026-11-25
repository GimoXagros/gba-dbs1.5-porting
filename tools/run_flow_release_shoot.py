"""Replay the game-earned Collection entry against an explicitly hashed later cartridge."""
import argparse
import json
import shutil
import time
from pathlib import Path

from run_flow_release import ROOT, BIZHAWK, PrivateDesktopProcess, digest

ARCHIVE=ROOT/'build/bizhawk-collection-v89-20261124-final-a'
PLAN='CEA147C623FE12C1127A4D6E3E43BC4B835B05A785463F5AE68A2582274DA3B0'
STATE='FBAE44F5E6AC349940ACA6FC328F5F53298317F5ED507548C0DD41586C2F9534'
SAVE='6B10ABBD459E034B6D16FC035AB89EA8A6A1280FC7A90C9FE1D1B7F0BA0B5148'


def observe(rom,expected,out,win,donor):
    assert digest(rom)==expected and Path('W:/').samefile(ROOT)
    script=ROOT/'tools/bizhawk_probe_collection_seven_round_v90.lua'
    assert digest(script)==PLAN
    archive=json.loads((ARCHIVE/'launch.json').read_bytes())
    assert archive['files']['ordinary-clear-title.State']==STATE
    state=ARCHIVE/'ordinary-clear-title.State'
    assert digest(state)==STATE
    out=out.resolve()
    assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True,exist_ok=False)
    alias='W:/'+out.relative_to(ROOT).as_posix()
    text=script.read_text().replace('local rom="8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869"','local rom="'+expected+'"')
    prep='''assert(savestate.load(out.."/earned.State"))
 assert(mode()==3)
 ''' if win else '''assert(emu.framecount()<4)
 for _=1,4200 do
  if mode()==3 then break end
  joypad.set({});emu.frameadvance()
 end
 assert(mode()==3)
 '''
    start=text.index(' local original=file')
    end=text.index(' local previous,started',start)
    text=text[:start]+ ' '+prep+'''local f=assert(io.open(out.."/loaded.bin","wb"))
 f:write(memory.read_bytes_as_binary_string(0,0x1000000,"ROM"));f:close()
 client.speedmode(800)
'''+text[end:]
    if not win:
        start=text.index('   local h=payload()',text.index('  elseif m==23 then'))
        end=text.index('  elseif m==20 and entry then',start)
        text=text[:start]+'''   if observed["scene-playing"] and frame%40==0 then button="A";nextInput=frame end
'''+text[end:]
        text=text.replace('observed["completion-save"] and observed["success-exit"] and englishCaptured and currentRound==6','observed["failure-exit"] and not observed["completion-save"] and englishCaptured')
    assert 'memory.write' not in text and 'dofile(' not in text
    frozen=out/'controller.lua'
    frozen.write_text(text,encoding='utf8',newline='\n')
    cfg=json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i,row in enumerate(cfg['PathEntries']['Paths']):
        row['Path']=alias+'/data/'+str(i);Path(row['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,SoundOutputMethod=3)
    (out/'config.json').write_text(json.dumps(cfg),encoding='utf8')
    shutil.copyfile(rom,out/'probe.gba')
    saved=out/'data/104/probe.SaveRAM'
    if win: shutil.copyfile(state,out/'earned.State')
    else:
        assert digest(donor)==SAVE
        shutil.copyfile(donor,saved)
    exe=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert digest(exe)==BIZHAWK
    args=['--gdi','--config='+alias+'/config.json','--lua='+alias+'/controller.lua','--userdata=output:'+alias+';probe_sha256:'+expected,alias+'/probe.gba']
    with PrivateDesktopProcess(exe,args,exe.parent) as process:
        deadline=time.monotonic()+480
        while not (out/'collection-done.txt').exists() and time.monotonic()<deadline:time.sleep(.25)
        result=(out/'collection-done.txt').read_text() if (out/'collection-done.txt').exists() else 'timeout'
        if result!='timeout':
            assert process._wait_process(process.process.hProcess,20000)==0,'emulator shutdown deadline'
    trace=(out/'collection-trace.txt').read_text()
    assert result=='collection-seven-round-win-returned' and digest(out/'loaded.bin')==expected,(result,trace[-350:])
    assert ('completion-save mode=23' in trace)==win and ('failure-exit mode=23' in trace)!=win
    assert 'mode=20' in trace and trace.strip().endswith('mode=3')
    assert saved.exists()
    report=dict(rom=expected,previous_script=PLAN,script=digest(frozen),state=STATE if win else None,
                save_in=None if win else SAVE,save_out=digest(saved),exact_rom=True,guest_writes=[],inputs='ordinary buttons',visible=False,
                seven_round_win=win,actual_defeat=not win,trace=digest(out/'collection-trace.txt'))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(report)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--expected',required=True)
    p.add_argument('--win',action='store_true')
    p.add_argument('--save',type=Path)
    a=p.parse_args()
    observe(a.rom,a.expected,a.out,a.win,a.save)

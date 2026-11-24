"""Run two independent GBA cores on a private desktop through one real link result."""
import argparse
import hashlib
import json
import shutil
import struct
import time
import zlib
from pathlib import Path

from mgba_headless_gdb_capture import PrivateDesktopProcess

EXE='0D9A2779ADD78D41A093C3AF8CEC7D72CC07A5451C8A1E1B167B48CD54950288'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('emulator','rom','first-native-prefix','second-native-prefix','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--rom-sha256',required=True)
    parser.add_argument('--attacker',required=True,type=int,choices=(1,2))
    parser.add_argument('--version',required=True,choices=('1.5','legacy'))
    parser.add_argument('--card-screens',action='store_true')
    parser.add_argument('--carry-to-special',action='store_true')
    parser.add_argument('--name-idle-frames',type=int,default=0)
    a=parser.parse_args()
    assert 0<=a.name_idle_frames<=12000 and (not a.name_idle_frames or (a.card_screens and a.carry_to_special))
    assert a.rom.stat().st_size==0x1000000 and sha(a.rom)==a.rom_sha256 and sha(a.emulator)==EXE
    out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    if '"' in str(out) or '\n' in str(out):
        raise ValueError('output path cannot be used in a quoted Lua path')
    gui=out/'mGBA.exe'
    shutil.copyfile(a.emulator,gui)
    (out/'portable.ini').write_bytes(b'')
    (out/'config.ini').write_text('[ports.qt]\naudioSync=0\nvideoSync=0\naudioBuffers=2048\nmute=1\nlogLevel=0\nvolume=0\n',encoding='ascii')
    (out/'qt.ini').write_text('[General]\nfirstRun=false\n',encoding='ascii')
    for p,prefix,rank,amount,streak,name in ((1,a.first_native_prefix,2,1,7,b'AGU\0'),(2,a.second_native_prefix,4,2,11,b'PAT\0')):
        native=prefix.read_bytes()
        assert len(native)==512
        data=bytearray(44)
        data[14:18]=name
        if a.carry_to_special:rank,amount=9,9
        struct.pack_into('<H',data,18+rank*2,amount)
        struct.pack_into('<H',data,40,streak)
        record=b'BS15TAG\x01'+data+struct.pack('<I',zlib.crc32(data))
        physical=b''.join(record[i:i+8][::-1] for i in range(0,56,8))
        starting=native[:216]+physical+native[272:]
        (out/f'initial-{p}.bin').write_bytes(starting)
        (out/f'player{p}.sav').write_bytes(starting)
        shutil.copyfile(a.rom,out/f'player{p}.gba')
    source=Path(__file__).with_name('mgba_probe_link_tag_result.lua')
    # mGBA's Windows scripting runtime reads ASCII paths. Use the existing
    # checked subst alias when the repository's absolute path includes Hangul.
    alias=out
    if not alias.as_posix().isascii():
        root=Path(__file__).resolve().parents[1]
        if not Path('W:/').samefile(root):
            raise ValueError('ASCII private output path required by the Windows Lua runtime')
        alias=Path('W:/')/out.relative_to(root)
    script=source.read_text(encoding='utf8').replace('@@OUTPUT@@',alias.as_posix())
    script=script.replace('@@ATTACKER@@',str(a.attacker)).replace('@@VERSION_ROW@@','0' if a.version=='1.5' else '1')
    if a.card_screens:
        snippet=Path(__file__).with_name('mgba_link_card_capture.lua').read_text(encoding='utf8')
        if a.carry_to_special:
            master=Path(__file__).with_name('mgba_link_master_capture.lua').read_text(encoding='utf8')
            meta_path=a.rom.with_name('manifest.json')
            meta=json.loads(meta_path.read_bytes()) if meta_path.exists() else {}
            party_init=meta.get('symbols',{}).get('m24s_party_init') or meta.get('reused_symbols',{}).get('m24s_party_init')
            if party_init:
                assert meta['output_sha256']==a.rom_sha256
                master=master.replace('@@PARTY_INIT@@',str(party_init)).replace('@@NAME_IDLE@@',str(a.name_idle_frames))
            else:
                master='local function inspect_master(f) end'
            snippet=snippet.replace('local function inspect_card(f,mode)',master+'\nlocal function inspect_card(f,mode)')
            snippet=snippet.replace('local elapsed=f-card_entered','local elapsed=f-card_entered\n inspect_master(f)')
        script=script.replace('local function frame()',snippet+'\nlocal function frame()').replace('f-exit_frame>220','f-exit_frame>30').replace('f>=21000','f>=48000')
        script=script.replace('if md==4 and entered_result and not exit_frame then exit_frame=f end','if md==4 and entered_result and not exit_frame then if card_had_result then exit_frame=f else entered_result=nil end end')
        script=script.replace('emu:clearKeys(1023);','if md==7 then allowed=arena_keys(f,'+str(a.attacker)+') end\n emu:clearKeys(1023);')
        if a.name_idle_frames:
            assert party_init
            script=script.replace('emu:clearKeys(1023);','if blocking_master_input(f) then allowed=0 end\n emu:clearKeys(1023);')
        script=script.replace('local serial=read(0x04000128,2)','inspect_card(f,md)\n local serial=read(0x04000128,2)')
    script_path=out/'probe.lua' 
    script_path.write_text(script,encoding='utf8',newline='\n')
    args=['--script',str(alias/'probe.lua'),str(alias/'player1.gba'),str(alias/'player2.gba')]
    report=dict(host_sha256=sha(gui),rom_sha256=sha(a.rom),visible=False,physical_input=False,guest_writes=[],
                attacker=a.attacker,version=a.version,name_idle_frames=a.name_idle_frames,card_screens=a.card_screens,carry_to_special=a.carry_to_special,source_rev='fa977ccbc815efc93aefad9acddc9af0577d7827',
                script_sha256=sha(source),arguments=args)
    ends=[out/f'finished-{p}.txt' for p in (1,2)]
    with PrivateDesktopProcess(gui,args,out):
        deadline=time.monotonic()+(360 if a.card_screens else 160)
        while time.monotonic()<deadline and not all(f.exists() for f in ends):
            time.sleep(.35)
    report['finished']=[f.exists() and f.read_text()=='exchange-complete' for f in ends]
    (out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    assert all(report['finished']),report
    print(report['version'],report['attacker'],report['finished'])


if __name__=='__main__':
    main()

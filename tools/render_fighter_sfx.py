"""Isolate each finite added-fighter cue at the normal boot request and dump native PCM."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import struct
import wave

from mgba_headless_gdb_capture import PrivateDesktopProcess

ROOT=Path(__file__).resolve().parents[1]
IDS=(0xBC,0xC6,0xC8,0xCB,0xCC)
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
EXE='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'


def sha(blob):
    return hashlib.sha256(blob).hexdigest().upper()


@contextmanager
def ascii_output_drive(directory):
    # Lua 5.1 on Windows cannot address every Unicode filename. Map only
    # this fresh capture directory and remove only this exact DOS target.
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=(ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR)
    kernel.CreateMutexW.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=(wintypes.HANDLE,wintypes.DWORD)
    kernel.ReleaseMutex.argtypes=(wintypes.HANDLE,)
    kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
    kernel.DefineDosDeviceW.argtypes=(wintypes.DWORD,wintypes.LPCWSTR,wintypes.LPCWSTR)
    mutex=kernel.CreateMutexW(None,False,'Local\\DBS15FighterAudioCaptureDrives')
    if not mutex:raise ctypes.WinError(ctypes.get_last_error())
    device=None
    target='\\??\\'+str(directory.resolve())
    try:
        if kernel.WaitForSingleObject(mutex,30000) not in (0,128):
            raise RuntimeError('timed out acquiring a capture drive letter')
        try:
            used=kernel.GetLogicalDrives()
            for n in range(25,5,-1):
                if not used & (1<<n):
                    candidate=chr(65+n)+':'
                    if kernel.DefineDosDeviceW(1|8,candidate,target):
                        device=candidate
                        break
        finally:
            kernel.ReleaseMutex(mutex)
        if device is None:raise RuntimeError('no unused drive letter available for isolated Lua output')
        assert Path(device+'/').samefile(directory)
        yield device+'/'
    finally:
        if device and not kernel.DefineDosDeviceW(1|2|4|8,device,target):
            raise ctypes.WinError(ctypes.get_last_error())
        kernel.CloseHandle(mutex)


def isolated_config(alias):
    global_types=('Base','ROM','Firmware','Movies','Movie backups','A/V Dumps','Tools','Lua','Watch (.wch)',
                  'Debug Logs','Macros','Multi-Disk Bundles','External Tools','Temp Files')
    game_types=('Base','ROM','Savestates','Save RAM','Screenshots','Cheats')
    entries=[]
    for system,types in (('Global_NULL',global_types),('WSWAN',game_types),('GBA',game_types)):
        for kind in types:
            path=alias+'/data/'+str(len(entries))
            Path(path).mkdir(parents=True)
            entries.append(dict(System=system,Type=kind,Path=path))
    return dict(LastWrittenFrom='2.11.1',PathEntries=dict(Paths=entries,UseRecentForRoms=False),
                AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,
                SoundEnabled=False,SoundEnabledNormal=False,SoundVolume=0,SoundVolumeRWFF=0,
                SpeedPercent=1000,DispMethod=1,SoundOutputMethod=1,SkipSuperuserPrivsCheck=True)


def capture(rom,kind,sid,out,drive,exe):
    out.mkdir()
    alias=drive+out.name
    fixture=bytearray(rom)
    if kind=='wsc':
        # 755D51 names ordinary boot music DC and four descriptors. Request
        # exactly one existing SFX through the same unmodified sound driver.
        assert rom[0x755d51:0x755d5b]==bytes.fromhex('c74402dc00c7440e0400')
        fixture[0x755d54:0x755d56]=struct.pack('<H',sid)
        fixture[0x755d59]=1
        struct.pack_into('<H',fixture,len(fixture)-2,sum(fixture[:-2])&0xffff)
        slot,channel=struct.unpack_from('<HH',rom,0x3f0000+sid*6)
        assert channel==2
        suffix='wsc'
    else:
        table=struct.unpack_from('<I',rom,0x37c2a4)[0]-0x08000000
        native=0x5f+IDS.index(sid)
        original=rom[table+8*native:table+8*native+8]
        _,player,mirror=struct.unpack('<IHH',original)
        assert player==mirror==4
        fixture[table+8:table+16]=original
        slot=struct.unpack_from('<I',rom,0x37fbb4+12*player)[0]-0x03000000
        suffix='gba'
    name='fixture.'+suffix
    (out/name).write_bytes(fixture)
    cfg=isolated_config(alias)
    (out/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    args=['--gdi','--config='+alias+'/config.json','--lua='+drive+'observer.lua',
          '--userdata=output:'+alias+';platform:'+kind+';slot:'+str(slot),
          '--dump-type=wave','--dump-name='+alias+'/render.wav','--dump-length=650','--dump-close',alias+'/'+name]
    with PrivateDesktopProcess(exe,args,exe.parent)as proc:
        assert proc._wait_process(proc.process.hProcess,120000)==0
    with wave.open(str(out/'render.wav'))as wav:
        assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())==(2,2,44100)
    return dict(source=sid,fixture_sha256=sha(fixture),trace_sha256=sha((out/'trace.txt').read_bytes()),
                wav_sha256=sha((out/'render.wav').read_bytes()),guest_writes=False,headless=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--platform',choices=('wsc','gba'),required=True)
    for n in ('rom','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--rom-sha256',required=True)
    p.add_argument('--emulator',type=Path,default=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe')
    a=p.parse_args()
    exe=a.emulator.resolve()
    assert sha(exe.read_bytes())==EXE
    rom=a.rom.read_bytes()
    assert sha(rom)==a.rom_sha256 and (a.platform!='wsc' or a.rom_sha256==SOURCE)
    out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(ROOT/'tools/bizhawk_fighter_sfx.lua',out/'observer.lua')
    with ascii_output_drive(out) as drive, ThreadPoolExecutor(max_workers=2)as pool:
        rows=list(pool.map(lambda s:capture(rom,a.platform,s,out/f'{s:02x}',drive,exe),IDS))
    report=dict(rom_sha256=sha(rom),platform=a.platform,rows=rows,exe_sha256=EXE,
                observer_sha256=sha((ROOT/'tools/bizhawk_fighter_sfx.lua').read_bytes()),
                host_sha256=sha(Path(__file__).read_bytes()))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(sha((out/'report.json').read_bytes()))


if __name__=='__main__':
    main()


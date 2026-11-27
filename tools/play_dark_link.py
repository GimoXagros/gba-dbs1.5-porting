"""Play the GBA D-ARK cartridge and WonderSwan D-Project on a direct emulated cable."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from time import perf_counter

from PIL import Image
from gba_dark_link import Cable, GameBoyAdvance, WonderSwan
from dark_link_audio import Sound

GBA_INPUT = {'w':'Up','a':'Left','s':'Down','d':'Right','j':'A','k':'B',
             'Return':'Start','BackSpace':'Select','u':'L','i':'R'}
WS_INPUT = {'Up':'Up','Left':'Left','Down':'Down','Right':'Right','z':'A','x':'B',
            'space':'Start','1':'Y1','2':'Y2','3':'Y3','4':'Y4'}


def cart_save(folder, role, rom):
    return folder / (role + '-' + sha256(rom.read_bytes()).hexdigest() + '.sav')


def persist(path, contents):
    if not contents or (path.exists() and path.read_bytes() == contents):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temp.write(contents)
        temp.flush()
        os.fsync(temp.fileno())
    try:
        os.replace(temp.name, path)
    finally:
        Path(temp.name).unlink(missing_ok=True)


def play(a):
    import tkinter as tk
    from tkinter import filedialog
    from PIL import ImageTk

    root = tk.Tk()
    root.withdraw()
    root.title('D-ARK · GBA ↔ WonderSwan')
    for key, title, ext in [('gba','배틀 스피릿 GBA 롬을 선택하세요','gba'),
                             ('dproject','D-Project 원본 또는 한국어판을 선택하세요','wsc')]:
        if getattr(a, key) is None:
            chosen = filedialog.askopenfilename(parent=root, title=title, filetypes=[(ext.upper(), '*.'+ext)])
            if not chosen:
                root.destroy()
                return
            setattr(a, key, Path(chosen))
    gba_save = cart_save(a.saves, 'gba', a.gba)
    ws_save = cart_save(a.saves, 'dproject', a.dproject)
    if not ws_save.exists() and not a.dproject_save:
        player_folder = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).resolve().parent
        sample = player_folder/'test-saves'/ws_save.name
        if sample.is_file():
            from tkinter import messagebox
            if messagebox.askyesno('D-Project', '통신용 PC를 열고 디지몬을 등록한 검사용 세이브로 시작할까요?', parent=root):
                a.dproject_save = sample
    peer_audio = bytearray()
    if a.dproject_save and ws_save.exists():
        raise ValueError('이 D-Project 롬에는 저장 데이터가 있습니다. 새 저장 폴더를 선택하세요.')
    sound = Sound(a.cores/'SDL2.dll')
    g = GameBoyAdvance(a.cores/'mgba_libretro.dll', a.gba, gba_save if gba_save.exists() else None)
    try:
        w = WonderSwan(a.cores/'ws_uart.dll', a.dproject, ws_save if ws_save.exists() else a.dproject_save, peer_audio.extend)
        try:
            cable = Cable(g,w)
            keys = set()
            panels = []
            for column, title, help_text in (
                    (0, 'GBA · Battle Spirit', 'WASD 이동   J / K 결정·취소   Enter 시작'),
                    (1, 'WonderSwan · D-Project', '방향키 이동   Z / X 결정·취소   Space 시작   1–4 Y 버튼')):
                tk.Label(root,text=title).grid(row=0,column=column)
                panel = tk.Label(root)
                panel.grid(row=1,column=column)
                panels.append(panel)
                tk.Label(root,text=help_text).grid(row=2,column=column,padx=12,pady=4)
            message = tk.StringVar(root)
            tk.Label(root,textvariable=message).grid(row=3,columnspan=2)
            root.bind('<KeyPress>', lambda e: keys.add(e.keysym))
            root.bind('<KeyRelease>', lambda e: keys.discard(e.keysym))
            root.bind('<FocusOut>', lambda e: keys.clear())
            root.protocol('WM_DELETE_WINDOW',root.quit)
            next_frame = perf_counter()
            errors = []
            def tick():
                nonlocal next_frame
                try:
                    cable.frame([GBA_INPUT[k] for k in keys if k in GBA_INPUT],
                                [WS_INPUT[k] for k in keys if k in WS_INPUT])
                    sound.push(g.audio(), peer_audio)
                    peer_audio.clear()
                    if w.frame_id % 2 == 0:
                        for panel, screen in zip(panels,(g.screen(),w.screen())):
                            size = tuple(x * 2 for x in screen.size)
                            photo = ImageTk.PhotoImage(screen.resize(size, Image.Resampling.NEAREST))
                            panel.configure(image=photo)
                            panel.image = photo
                    if w.frame_id % 30 == 0:
                        message.set(f'전송한 바이트   GBA {cable.tx_count}   ·   WonderSwan {cable.rx_count}')
                    if w.frame_id % 375 == 0:
                        persist(gba_save,g.save())
                        persist(ws_save,w.save())
                    next_frame = max(next_frame + 159 / 12000, perf_counter() - .03)
                    root.after(max(1,round((next_frame-perf_counter()) * 1000)),tick)
                except Exception as exc:
                    errors.append(exc)
                    root.quit()
            root.deiconify()
            root.after(1,tick)
            root.mainloop()
            if errors:
                raise errors[0]
            persist(gba_save,g.save())
            persist(ws_save,w.save())
        finally:
            w.close()
    finally:
        g.close()
        sound.close()
        root.destroy()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('gba','dproject','dproject-save','headless-report'):
        p.add_argument('--'+key,type=Path)
    p.add_argument('--cores',type=Path,default=Path(getattr(sys,'_MEIPASS',Path(__file__).parent)))
    p.add_argument('--saves',type=Path,default=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'DBS15-DarkLink'/'saves')
    a=p.parse_args()
    if a.headless_report:
        if not (a.gba and a.dproject):
            p.error('The headless check needs both cartridges')
        import json
        import tkinter
        from verify_dark_cross_cable import enter, task, run
        if a.dproject_save:
            run(argparse.Namespace(gba_core=a.cores/'mgba_libretro.dll', ws_core=a.cores/'ws_uart.dll',
                gba=a.gba, dproject=a.dproject, state=None, peer_save=a.dproject_save, buttons=None, frames=12000,
                fighter=1, settle=120, wait_frames=0, disconnected=False, output=a.headless_report.parent))
            a.headless_report.write_bytes((a.headless_report.parent/'trace.json').read_bytes())
            return
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        g = GameBoyAdvance(a.cores/'mgba_libretro.dll', a.gba)
        peer_audio = bytearray()
        w = WonderSwan(a.cores/'ws_uart.dll',a.dproject,a.dproject_save,peer_audio.extend)
        sound = Sound(a.cores/'SDL2.dll')
        try:
            enter(g)
            cable = Cable(g,w)
            sizes = [0,0]
            for _ in range(180):
                cable.frame()
                pcm = g.audio()
                sizes[0] += len(pcm)
                sizes[1] += len(peer_audio)
                sound.push(pcm,peer_audio)
                peer_audio.clear()
            assert g.read16(0x03002310) == 18 and g.read16(task(g)+0x40) & 255 == 0
            assert sound.device and min(sizes) > 0 and not (cable.rx_count or cable.tx_count)
            a.headless_report.write_text(json.dumps(dict(audio_bytes=sizes,port_bytes=[0,0],
                gba_screen=g.screen().size,ws_screen=w.screen().size,tcl=tkinter.Tcl().eval('info patchlevel'))))
        finally:
            w.close()
            g.close()
            sound.close()
        return
    try:
        play(a)
    except Exception as e:
        from tkinter.messagebox import showerror
        showerror('D-ARK',str(e))
        raise


if __name__=='__main__':
    try:
        main()
    except Exception:
        if '--headless-report' not in sys.argv:
            raise
        import traceback
        report = Path(sys.argv[sys.argv.index('--headless-report') + 1])
        report.with_suffix('.error.txt').write_text(traceback.format_exc(),encoding='utf8')
        raise SystemExit(1)

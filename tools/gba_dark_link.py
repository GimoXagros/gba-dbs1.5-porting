"""Clock an mGBA cartridge and a WonderSwan cartridge on one virtual serial cable."""
import ctypes as C
from pathlib import Path

from PIL import Image

from wsc_dark_link import Core as WonderSwan

GBA_CLOCK = 16_777_216
WSC_CLOCK = 3_072_000
GBA_KEYS = {'A': 0, 'B': 1, 'Select': 2, 'Start': 3, 'Right': 4,
            'Left': 5, 'Up': 6, 'Down': 7, 'R': 8, 'L': 9}


class GameBoyAdvance:
    def __init__(self, dll, rom, save=None):
        self.lib = C.CDLL(str(Path(dll).resolve()))
        signatures = {
            'open': (C.c_int, C.c_void_p, C.c_size_t, C.c_void_p, C.c_size_t),
            'close': (None,), 'until': (None, C.c_uint64), 'clock': (C.c_uint64,),
            'frame': (C.c_uint,), 'keys': (None, C.c_uint), 'pixels': (C.c_void_p,),
            'audio': (C.c_int, C.c_void_p, C.c_int), 'send': (C.c_int,), 'receive': (C.c_int, C.c_uint),
            'read16': (C.c_int, C.c_uint32), 'save': (C.c_size_t, C.c_void_p, C.c_size_t),
        }
        for name, (ret, *args) in signatures.items():
            fn = getattr(self.lib, 'cable_gba_' + name)
            fn.restype, fn.argtypes = ret, args
        data = Path(rom).read_bytes()
        contents = Path(save).read_bytes() if isinstance(save, (str, Path)) else (save or b'')
        if not self.lib.cable_gba_open(data, len(data), contents, len(contents)):
            raise ValueError('Could not start the GBA cartridge with this save')

    def set_keys(self, keys):
        if isinstance(keys, str):
            keys = (keys,)
        self.lib.cable_gba_keys(keys if isinstance(keys, int) else sum(1 << GBA_KEYS[k] for k in set(keys)))

    def screen(self):
        raw = C.string_at(self.lib.cable_gba_pixels(), 240 * 160 * 2)
        return Image.frombytes('RGB', (240, 160), raw, 'raw', 'BGR;16')

    def audio(self):
        out = C.create_string_buffer(2048 * 4)
        frames = self.lib.cable_gba_audio(out, 2048)
        return out.raw[:4 * frames]

    def read16(self, address):
        return self.lib.cable_gba_read16(address)

    def save(self):
        buffer = C.create_string_buffer(0x20000)
        size = self.lib.cable_gba_save(buffer, len(buffer))
        if size > len(buffer):
            raise ValueError('Unexpected GBA save size')
        return buffer.raw[:size]

    def close(self):
        self.lib.cable_gba_close()


class Cable:
    def __init__(self, gba, ws):
        self.gba, self.ws = gba, ws
        self.start = gba.lib.cable_gba_clock()
        self.lines = 0
        self.tx_count = self.rx_count = self.overruns = 0

    def frame(self, gba_keys=0, ws_keys=0, trace=None):
        self.gba.set_keys(gba_keys)
        self.ws.begin(ws_keys)
        for _ in range(260):
            done = self.ws.line()
            self.lines += 1
            target = self.start + self.lines * 256 * GBA_CLOCK // WSC_CLOCK
            self.gba.lib.cable_gba_until(target)
            byte = self.ws.take()
            while byte >= 0:
                accepted = self.gba.lib.cable_gba_receive(byte)
                self.rx_count += 1
                self.overruns += accepted < 0
                if trace is not None:
                    trace.append((self.lines, 'WSC', byte, accepted))
                byte = self.ws.take()
            byte = self.gba.lib.cable_gba_send()
            while byte >= 0:
                self.ws.give(byte)
                self.tx_count += 1
                if trace is not None:
                    trace.append((self.lines, 'GBA', byte))
                byte = self.gba.lib.cable_gba_send()
            if done:
                self.ws.end()
                return
        raise RuntimeError('No WonderSwan frame boundary within 260 scanlines')

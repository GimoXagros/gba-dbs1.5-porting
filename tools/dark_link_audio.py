"""Mix native 44.1 kHz stereo from both consoles and queue it to SDL2."""
import ctypes as C
from array import array


class Spec(C.Structure):
    _fields_ = [('rate', C.c_int), ('format', C.c_uint16), ('channels', C.c_uint8),
                ('silence', C.c_uint8), ('samples', C.c_uint16), ('padding', C.c_uint16),
                ('size', C.c_uint32), ('callback', C.c_void_p), ('userdata', C.c_void_p)]


class Sound:
    def __init__(self, path):
        self.lib = C.CDLL(str(path.resolve()))
        self.device = 0
        self.gba, self.ws = bytearray(), bytearray()
        self.lib.SDL_OpenAudioDevice.argtypes = [C.c_char_p, C.c_int, C.POINTER(Spec), C.POINTER(Spec), C.c_int]
        self.lib.SDL_OpenAudioDevice.restype = C.c_uint32
        self.lib.SDL_QueueAudio.argtypes = [C.c_uint32, C.c_void_p, C.c_uint32]
        if self.lib.SDL_InitSubSystem(0x10) == 0:
            self.device = self.lib.SDL_OpenAudioDevice(None, 0, C.byref(Spec(44100, 0x8010, 2, 0, 1024)), None, 0)
            if self.device:
                self.lib.SDL_PauseAudioDevice(self.device, 0)

    def push(self, gba, ws):
        if not self.device:
            return
        self.gba.extend(gba)
        self.ws.extend(ws)
        size = min(len(self.gba), len(self.ws))
        if size:
            left = array('h', self.gba[:size])
            right = array('h', self.ws[:size])
            mixed = array('h', ((a+b)//2 for a,b in zip(left,right))).tobytes()
            if self.lib.SDL_GetQueuedAudioSize(self.device) < 44100:
                self.lib.SDL_QueueAudio(self.device, mixed, len(mixed))
            del self.gba[:size]
            del self.ws[:size]
        # Drop a stale backlog if a host audio callback paused independently.
        for pending in (self.gba, self.ws):
            if len(pending) > 44100:
                pending.clear()

    def close(self):
        if self.device:
            self.lib.SDL_CloseAudioDevice(self.device)
        self.lib.SDL_QuitSubSystem(0x10)

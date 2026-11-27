"""Headless native WonderSwan cores and a bidirectional, per-scanline serial cable."""
import ctypes as C
from pathlib import Path
import shutil
import tempfile

from PIL import Image

BTN = {'B':0,'Start':3,'Up':4,'Down':5,'Left':6,'Right':7,'A':8,'Y4':10,'Y2':11,'Y3':12,'Y1':13}
ENV = C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
POLL = C.CFUNCTYPE(None)
INPUT = C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)
VIDEO = C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
AUDIO = C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)


class Game(C.Structure):
    _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]


class Core:
    """Each instance loads an isolated native core, separate cart save and RAM."""
    def __init__(self, dll, rom, save=None, audio_sink=None):
        self.folder=tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.file=Path(self.folder.name)/Path(dll).name
        shutil.copyfile(dll,self.file)
        self.lib=C.CDLL(str(self.file))
        self.keys=0
        self.frame_id=0
        self.picture=None
        self.pixel=0
        self.callbacks=[]
        self.rom=Path(rom).read_bytes()
        data=C.create_string_buffer(self.rom)
        self._data=data
        self.game=Game(str(rom).encode(),C.cast(data,C.c_void_p),len(self.rom),None)
        self._bind('retro_load_game',C.c_bool,C.POINTER(Game))
        self._bind('retro_get_memory_data',C.c_void_p,C.c_uint)
        self._bind('retro_get_memory_size',C.c_size_t,C.c_uint)
        self._bind('retro_serialize_size',C.c_size_t)
        self._bind('retro_serialize',C.c_bool,C.c_void_p,C.c_size_t)
        self._bind('retro_unserialize',C.c_bool,C.c_void_p,C.c_size_t)
        def audio(data, size):
            if audio_sink is not None:
                audio_sink(C.string_at(data, size * 4))
            return size

        for api,proto,call in [
            ('environment',ENV,self._env),('input_poll',POLL,lambda:None),
            ('input_state',INPUT,self._input),('video_refresh',VIDEO,self._video),
            ('audio_sample_batch',AUDIO,audio)]:
            callback=proto(call)
            self.callbacks.append(callback)
            getattr(self.lib,'retro_set_'+api)(callback)
        self.lib.retro_init()
        if not self.lib.retro_load_game(C.byref(self.game)):
            raise ValueError(f'Could not load {rom}')
        self._ram=(C.c_ubyte*self.lib.retro_get_memory_size(2)).from_address(self.lib.retro_get_memory_data(2))
        self.ram=memoryview(self._ram).cast('B').toreadonly()
        self.sram=memoryview((C.c_ubyte*self.lib.retro_get_memory_size(0)).from_address(self.lib.retro_get_memory_data(0))).cast('B').toreadonly()
        if save is not None:
            contents=Path(save).read_bytes() if isinstance(save,(str,Path)) else save
            if len(contents)!=self.lib.retro_get_memory_size(0):
                raise ValueError('Incorrect cart SaveRAM size')
            C.memmove(self.lib.retro_get_memory_data(0),contents,len(contents))

    def _bind(self,name,result,*args):
        fn=getattr(self.lib,name);fn.restype=result;fn.argtypes=list(args)

    def _env(self,cmd,arg):
        if cmd==10: # RETRO_ENVIRONMENT_SET_PIXEL_FORMAT
            self.pixel=C.c_int.from_address(arg).value
            return self.pixel in (0,1,2)
        return False

    def _input(self,port,device,index,button):
        return int(bool(self.keys & (1<<button))) if port==0 and device==1 else 0

    def _video(self,data,width,height,pitch):
        if data: self.picture=(data,width,height,pitch)

    def screen(self):
        if not self.picture: raise ValueError('No frame has been drawn')
        data,w,h,pitch=self.picture
        layout=('BGR;15','BGRX','BGR;16')[self.pixel]
        return Image.frombytes('RGB',(w,h),C.string_at(data,pitch*h),'raw',layout,pitch,1)

    def set_keys(self,keys):
        if isinstance(keys,str):keys=(keys,)
        self.keys=keys if isinstance(keys,int) else sum(1<<BTN[k] for k in set(keys))

    def frame(self,keys=0):
        self.set_keys(keys)
        self.lib.retro_run()
        self.frame_id+=1

    def begin(self,keys=0):
        self.set_keys(keys);self.lib.hb_ws_run_pre();self.lib.hb_ws_emu_begin(0,1)

    def line(self):
        return bool(self.lib.hb_ws_emu_line())

    def end(self):
        self.lib.hb_ws_emu_end(0,1);self.lib.hb_ws_run_post();self.frame_id+=1

    def take(self):
        return self.lib.hb_ws_link_take()

    def give(self,byte):
        if not 0<=byte<256: raise ValueError('UART requires one unsigned byte')
        self.lib.hb_ws_link_give(byte)

    def uart_stats(self):
        values=(C.c_uint32*10)()
        self.lib.hb_ws_link_stats(values,10)
        return dict(zip(('sent','received','overrun','lost','tx_ignored','control','sending','unread','overrun_flag','last_received'),values))

    def state(self):
        n=self.lib.retro_serialize_size();data=C.create_string_buffer(n)
        if not self.lib.retro_serialize(data,n):raise RuntimeError('Cannot capture core state')
        return data.raw

    def restore(self,raw):
        data=C.create_string_buffer(raw)
        if not self.lib.retro_unserialize(data,len(raw)):raise RuntimeError('Cannot restore core state')

    def save(self):
        return C.string_at(self.lib.retro_get_memory_data(0),self.lib.retro_get_memory_size(0))

    def close(self):
        self.lib.retro_unload_game();self.lib.retro_deinit()
        import _ctypes,os
        release=_ctypes.FreeLibrary if os.name=='nt' else _ctypes.dlclose
        release(self.lib._handle)
        self.folder.cleanup()


def linked_frame(left,right,left_keys=0,right_keys=0,trace=None):
    """Forward completed native UART bytes; the receiver core owns readiness and IRQs."""
    left.begin(left_keys);right.begin(right_keys)
    a=b=False
    for scanline in range(260):
        if not a:a=left.line()
        if not b:b=right.line()
        for tx,rx,side in ((left,right,0),(right,left,1)):
            val=tx.take()
            while val>=0:
                rx.give(val)
                if trace is not None: trace.append((left.frame_id,scanline,side,val))
                val=tx.take()
        if a and b:break
    else:raise RuntimeError('WonderSwan frame exceeded 260 scanlines')
    left.end();right.end()

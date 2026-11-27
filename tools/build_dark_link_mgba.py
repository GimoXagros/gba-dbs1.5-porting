"""Build the headless GBA UART core from mGBA 0.10.5, without modifying an installed emulator."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

REV = '26b7884bc25a5933960f3cdcd98bac1ae14d42e2'
UPSTREAM = 'https://github.com/mgba-emu/mgba.git'


def build(source, output, cmake, gcc, ninja):
    if not source.exists():
        subprocess.run(['git', 'clone', '--depth', '1', '--branch', '0.10.5', UPSTREAM, source], check=True)
    if subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('Unexpected mGBA checkout')
    path = source / 'src/gba/io.c'
    original = subprocess.check_output(['git', '-C', source, 'show', 'HEAD:src/gba/io.c']).decode()
    changes = {
        'mLOG_DEFINE_CATEGORY(GBA_IO,': '#include "dark_link_mgba.c"\n\nmLOG_DEFINE_CATEGORY(GBA_IO,',
        'uint16_t GBAIORead(struct GBA* gba, uint32_t address) {':
            'uint16_t GBAIORead(struct GBA* gba, uint32_t address) {\n\tuint16_t uart;\n\tif (uartRead(gba, address, &uart)) return uart;',
        'void GBAIOWrite(struct GBA* gba, uint32_t address, uint16_t value) {':
            'void GBAIOWrite(struct GBA* gba, uint32_t address, uint16_t value) {\n\tif (uartWrite(gba, address, value)) return;',
    }
    edited = original
    for old, new in changes.items():
        if edited.count(old) != 1:
            raise ValueError('Unrecognized mGBA I/O layout')
        edited = edited.replace(old, new)
    previous = path.read_text(encoding='utf8')
    if previous not in (original, edited):
        raise ValueError('Use a dedicated mGBA checkout without other I/O edits')
    if previous != edited:
        path.write_text(edited, encoding='utf8', newline='\n')
    shutil.copyfile(Path(__file__).with_name('dark_link_mgba.c'), path.with_name('dark_link_mgba.c'))
    output.mkdir(parents=True, exist_ok=True)
    gcc = gcc.absolute()
    env = {**os.environ, 'PATH': str(gcc.parent) + os.pathsep + os.environ['PATH']}
    disabled = ('USE_GDB_STUB USE_FFMPEG USE_ZLIB USE_MINIZIP USE_PNG '
                'USE_LIBZIP USE_SQLITE3 USE_ELF USE_LUA USE_LZMA USE_DISCORD_RPC '
                'M_CORE_GB BUILD_GL BUILD_GLES2 BUILD_GLES3 BUILD_QT BUILD_SDL BUILD_TEST '
                'BUILD_STATIC BUILD_LTO BUILD_PYTHON BUILD_EXAMPLE BUILD_PERF').split()
    subprocess.run([cmake, '-S', source, '-B', output, '-G', 'Ninja',
                    '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_MAKE_PROGRAM=' + ninja.as_posix(),
                    '-DCMAKE_C_COMPILER=' + gcc.as_posix(), '-DCMAKE_CXX_COMPILER=' + gcc.with_name('g++.exe').as_posix(),
                    '-DCMAKE_RC_COMPILER=' + gcc.with_name('windres.exe').as_posix(),
                    '-DSKIP_LIBRARY=ON', '-DBUILD_LIBRETRO=ON', '-DUSE_EPOXY=OFF', '-DUSE_DEBUGGERS=OFF', '-DDISABLE_FRONTENDS=ON', '-DM_CORE_GBA=ON',
                    *['-D' + option + '=OFF' for option in disabled]], env=env, check=True)
    subprocess.run([cmake, '--build', output, '--target', 'mgba_libretro', '--parallel', '8'], env=env, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'output', 'cmake', 'gcc', 'ninja'):
        parser.add_argument('--' + key, type=Path, required=True)
    build(**vars(parser.parse_args()))

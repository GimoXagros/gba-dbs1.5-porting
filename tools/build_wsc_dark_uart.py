"""Build a headless, scanline-steppable Beetle WonderSwan UART core with MSVC."""
import argparse
import os
import re
import subprocess
from pathlib import Path

BEETLE = '4b01295838ea89e3f1355bbe4cb5cf98aa6108cd'
PATCHES = 'db00c5fd2c863563da4ae84c4fe2d78364f7e3dc'


def build(source, patches, out):
    for path, commit in ((source, BEETLE), (patches, PATCHES)):
        if subprocess.check_output(['git', '-C', path, 'rev-parse', 'HEAD'], text=True).strip() != commit:
            raise ValueError(f'Unexpected revision in {path}')
    patch_files = sorted((patches / 'cores/wswan-mednafen-dual/patches').glob('000[12]-*.patch'))
    if len(patch_files) != 2:
        raise ValueError('Expected the core UART and scanline driver patches')
    for patch in patch_files:
        cmd = ['git', '-C', str(source), 'apply']
        if subprocess.run(cmd+['--reverse', '--check', str(patch)], capture_output=True).returncode:
            subprocess.run(cmd+['--whitespace=nowarn', str(patch)], check=True)
    out.mkdir(parents=True, exist_ok=True)
    cfiles = [*sorted((source/'mednafen/wswan').glob('*.c')),
              *(source/'mednafen'/n for n in ['mempatcher.c','settings.c','state.c','sound/Blip_Buffer.c']),
              *(source/'libretro-common/compat'/n for n in ['compat_strl.c','compat_snprintf.c']),
              source/'libretro.c']
    incl = ['.','mednafen','mednafen/include','mednafen/hw_sound','mednafen/hw_cpu','mednafen/hw_misc','libretro-common/include']
    defines = ['NO_COMPUTED_GOTO','WANT_16BPP','FRONTEND_SUPPORTS_RGB565','WANT_STEREO_SOUND','LSB_FIRST','SIZEOF_DOUBLE=8','MEDNAFEN_VERSION_NUMERIC=931','MPC_FIXED_POINT','STDC_HEADERS','__STDC_LIMIT_MACROS','__LIBRETRO__','_LOW_ACCURACY_','INLINE=_inline','_CRT_SECURE_NO_WARNINGS']
    source_text = (source/'libretro.c').read_text(encoding='utf8')
    # libretro exports its own ABI. Expose the UART extensions defined in libretro.c.
    exports = sorted(set(re.findall(
        r'^\w[\w \t*]*\b(hb_ws_\w+)\([^;\n]*\)[ \t]*\n\{',
        source_text, flags=re.MULTILINE)))
    if not {"hb_ws_subframes", "hb_ws_link_take", "hb_ws_link_give"} <= set(exports):
        raise ValueError("WonderSwan UART patch entry points are missing")
    (out/'core.def').write_text('EXPORTS\n'+'\n'.join(exports)+'\n',encoding='ascii')
    vswhere = Path(os.environ['ProgramFiles(x86)'])/'Microsoft Visual Studio/Installer/vswhere.exe'
    vs = subprocess.check_output([vswhere,'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'], text=True).strip()
    setup = Path(vs)/'VC/Auxiliary/Build/vcvars64.bat'
    flags=['/nologo','/utf-8','/std:c11','/O2','/MT','/LD','/w',*('/D'+d for d in defines), *('/I'+str(source/i) for i in incl), *map(str,cfiles),'/link','/DEF:core.def','/OUT:ws_uart.dll']
    (out/'build.rsp').write_text(subprocess.list2cmdline(flags), encoding='utf-16')
    (out/'compile.cmd').write_text('@echo off\ncall "'+str(setup)+'" >nul\nif errorlevel 1 exit /b 1\ncl @build.rsp\n',encoding='ascii')
    subprocess.run(['cmd','/d','/c','compile.cmd'], cwd=out, check=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','patches','out'): p.add_argument(name,type=lambda x:Path(x).resolve())
    a=p.parse_args()
    build(a.source,a.patches,a.out)

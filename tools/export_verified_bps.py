"""Create a local patch, reapply it to a clean USA input, and compare every output byte."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

USA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'


def digest(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def export(flips, base, image, expected, output):
    if digest(base.read_bytes()) != USA:
        raise ValueError('Original USA image hash mismatch')
    built = image.read_bytes()
    if len(built) != 0x1000000 or digest(built) != expected.upper():
        raise ValueError('Candidate hash or length mismatch')
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        patch = Path(tmp)/'port.bps'
        applied = Path(tmp)/'applied.gba'
        def run(*args):
            subprocess.run([str(flips),*map(str,args)],check=True,
                           creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        run('--create','--bps',base,image,patch)
        run('--apply',patch,base,applied)
        if applied.read_bytes()!=built or not patch.read_bytes().startswith(b'BPS1'):
            raise ValueError('BPS roundtrip mismatch')
        report=dict(source_sha256=USA,output_sha256=digest(built),bps_sha256=digest(patch.read_bytes()),
                    bps_bytes=patch.stat().st_size,rom_bytes=len(built),whole_image_roundtrip=True)
        patch.rename(output)
        return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for a in ('flips','base','image','output'):p.add_argument('--'+a,type=Path,required=True)
    p.add_argument('--expected',required=True)
    a=p.parse_args()
    checks=export(a.flips.resolve(),a.base.resolve(),a.image.resolve(),a.expected,a.output.resolve())
    print(json.dumps(checks,indent=2))

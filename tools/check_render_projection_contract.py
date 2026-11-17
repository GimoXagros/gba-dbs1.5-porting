"""Pin world/presentation units and inspect existing two terminal snapshots."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def contracts(source, native):
    expected = [
        'ldrsh r0, [r4, #0x34]', 'ldrsh r1, [r4, #0x36]',
        'asr r0, r0, #4', 'asr r1, r1, #4',
        'ldr r8, [pc, #0xd0]', 'ldrsh sb, [r8]', 'sub r0, r0, sb',
        'ldr r8, [pc, #0xc8]', 'ldrsh sb, [r8]', 'sub r1, r1, sb']
    rows = Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(native[0x3528DC:0x352904], 0x083528DC)
    assert [i.mnemonic+' '+i.op_str for i in rows] == expected, 'native signed projection'
    expected = ['mov ax, word ptr [si + 0x26]', 'mov bx, word ptr [si + 0x28]',
                'sar ax, 4', 'sar bx, 4', 'sub ax, word ptr [0x3a14]',
                'sub bx, word ptr [0x3a16]']
    rows = Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[0x74239D:0x7423B1], 0x74239D)
    assert [i.mnemonic+' '+i.op_str for i in rows] == expected, 'source signed projection'
    assert struct.unpack_from('<II', native, 0x3529C4) == (0x0300451C, 0x0300451E)
    assert native[0x352940:0x352950] == bytes.fromhex('B000C5E1B210C5E13E00C4E54010C4E5'), 'presentation stores'


def inspect(name):
    p = ROOT / 'build' / name
    iw = (p/'pause-end-iwram.bin').read_bytes()
    ew = (p/'pause-end-ewram.bin').read_bytes()
    camera = struct.unpack_from('<hh', iw, 0x451C)
    assert camera == struct.unpack_from('<hh', iw, 0x2348), 'snapshot equals BG camera at boundary'
    assert struct.unpack_from('<H', iw, 0x4502)[0] != 2, 'shake mode is inactive in these snapshots'
    rows = []
    for owner in (0x489C, 0x48A0):
        a = struct.unpack_from('<I', iw, owner)[0] - 0x02000000
        assert 0 <= a <= len(ew)-0x118
        world = struct.unpack_from('<hh', ew, a+0x34)
        previous = struct.unpack_from('<hh', ew, a+0x38)
        pixels = tuple(v >> 4 for v in world)
        projected = tuple(v-c for v, c in zip(pixels, camera))
        presentation = struct.unpack_from('<hh', ew, a+0xAC)
        assert projected == presentation, 'actual projection agrees with current body and camera'
        flags = struct.unpack_from('<H', ew, a+0xB4)[0]
        rows.append(dict(actor=f'{a+0x02000000:08X}', world=world, previous=previous,
                         pixels=pixels, presentation=presentation, hidden_bit0800=bool(flags & 0x800)))
    assert rows[0]['presentation'] == (22, 68) and not rows[0]['hidden_bit0800']
    assert rows[1]['presentation'][1] > 160 and rows[1]['hidden_bit0800']
    return dict(capture=name, camera=camera, actors=rows,
                queue_count=struct.unpack_from('<H', iw, 0x482A)[0], obj_count=iw[0x12CA],
                iwram_sha256=sha(iw), ewram_sha256=sha(ew))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists(), 'fresh output'
    source = a.source.read_bytes()
    native = (ROOT/'build/bizhawk-id14-air-20261117-b/loaded-rom.bin').read_bytes()
    assert sha(source) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert sha(native) == 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
    contracts(source, native)
    negatives = []
    for at in (0x3528E4, 0x3528FC, 0x3529C4, 0x352940):
        bad = bytearray(native); bad[at] ^= 1
        try:
            contracts(source, bad)
        except AssertionError:
            negatives.append(hex(at))
        else:
            raise AssertionError('undetected projection mutation')
    result = dict(status='RENDER_PROJECTION_CONTRACT_PASS', source_sha256=sha(source),
                  native_sha256=sha(native), rejected_mutations=negatives,
                  snapshots=[inspect(n) for n in ('bizhawk-id14-air-20261117-b',
                                                  'bizhawk-id14-evolution-20261116-c')],
                  conclusion='P1 in-view projection is correct; P2 is offscreen. No camera patch justified.',
                  limit='Snapshots do not establish later draw/queue lifetime; bounded tail observer is separate.',
                  emulator_launched=False, ROM_modified=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'])


if __name__ == '__main__':
    main()

"""Bind the newly observed tail to native and source devolution blinking."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def contracts(source, native):
    def exact(data, start, end, expected, arm=False):
        decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
        rows = decoder.disasm(data[start:end], start+(0x08000000 if arm else 0))
        assert [i.mnemonic+' '+i.op_str for i in rows] == expected
    exact(source, 0x743508, 0x74352F, [
        'test word ptr [si + 8], 0x1000', 'je 0x74352f', 'dec byte ptr [si + 0x5e]',
        'jne 0x743521', 'and word ptr [si + 8], 0xefff', 'and word ptr [si + 4], 0xffdf',
        'jmp 0x74352f', 'mov al, byte ptr [si + 0x5e]', 'and al, 3', 'cmp al, 3',
        'jne 0x74352f', 'xor word ptr [si + 4], 0x20'])
    exact(native, 0x352ED0, 0x352F24, [
        'ldrh r8, [r4, #8]', 'tst r8, #0x1000', 'beq #0x8352f24',
        'ldrb r8, [r4, #0x72]', 'subs r8, r8, #1', 'strb r8, [r4, #0x72]',
        'bne #0x8352f08', 'ldrsh r8, [r4, #8]', 'bics r8, r8, #0x1000',
        'strh r8, [r4, #8]', 'ldrsh r8, [r4, #4]', 'bics r8, r8, #0x20',
        'strh r8, [r4, #4]', 'b #0x8352f24', 'ldrb r0, [r4, #0x72]',
        'and r0, r0, #3', 'cmp r0, #3', 'bne #0x8352f24',
        'ldrh r8, [r4, #4]', 'eor r8, r8, #0x20', 'strh r8, [r4, #4]'], True)
    exact(source, 0x7676B2, 0x7676C3, ['or word ptr [si + 8], 0x1001',
        'mov byte ptr [si + 0x5b], 0x4b', 'mov byte ptr [si + 0x5e], 0x4b',
        'mov byte ptr [si + 0x5f], 0x4b'])
    exact(native, 0x35A720, 0x35A730, ['mov sb, #0x3c', 'strb sb, [r4, #0x6f]',
        'strb sb, [r4, #0x72]', 'strb sb, [r4, #0x73]'], True)
    assert struct.unpack_from('<I', native, 0x35A7C4)[0] == 0x1001
    exact(native, 0x373604, 0x373620, ['ldrsh r8, [r0, #-0xa8]', 'tst r8, #0x20',
        'bne #0x8373620', 'stmdb sp!, {r0}', 'stmdb sp!, {fp}',
        'bl #0x8012c28', 'add sp, sp, #8'], True)
    assert struct.unpack_from('<I', native, 0x12C50)[0] == 0x086FF240
    exact(native, 0x6FF240, 0x6FF24C, ['ldrh r0, [r5, #0x14]', 'cmp r0, #0x6d',
        'bne #0x86fea00'], True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists()
    capture = ROOT/'build/bizhawk-id14-render-tail-20261117-a'
    source = a.source.read_bytes(); native = (capture/'loaded-rom.bin').read_bytes()
    assert sha(source) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert sha(native) == 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
    contracts(source, native)
    negatives = []
    for at in (0x352EE0, 0x352EFC, 0x352F1C, 0x35A720, 0x373608, 0x12C50):
        bad = bytearray(native); bad[at] ^= 1
        try:
            contracts(source, bad)
        except AssertionError:
            negatives.append(hex(at))
        else:
            raise AssertionError('unrejected semantic mutation')
    trace = (capture/'render-tail.txt').read_text()
    snapshots = [line for line in trace.splitlines() if line.startswith('snapshot=age-')]
    assert len(snapshots) == 121
    count, hidden = 58, True
    states = []
    for age, line in enumerate(snapshots):
        assert line.startswith(f'snapshot=age-{age} core={9708+age} ')
        actor = line.split('P1{')[1].split('}')[0]
        f4 = int(re.search(r'f4=([0-9A-F]+)', actor)[1], 16)
        f8 = int(re.search(r'f8=([0-9A-F]+)', actor)[1], 16)
        assert bool(f4 & 0x20) == hidden and bool(f8 & 0x1000) == bool(count)
        assert 'world=0163,0D00' in actor and 'present=0016,0044' in actor
        dispatch = [s for s in trace.splitlines() if s.startswith(f'event=dispatch core={9708+age} ')]
        if age < 120:
            # Dispatch happens during this boundary's next frame, after the decrement.
            remaining = max(count-1, 0)
            next_hidden = False if remaining == 0 else not hidden if remaining % 4 == 3 else hidden
            assert len(dispatch) == int(not next_hidden)
        states.append(dict(age=age, remaining=count, hidden=hidden))
        if count:
            count -= 1
            hidden = False if count == 0 else not hidden if count % 4 == 3 else hidden
    assert all(not row['hidden'] for row in states[58:])
    capture_hashes = {}
    for age in (0, 1, 2, 4, 8, 16, 32, 64, 120):
        ew = (capture/f'render-tail-{age}-ewram.bin').read_bytes()
        assert ew[0x11782] == ew[0x1177F] == max(58-age, 0)
        assert struct.unpack_from('<H', ew, 0x117D0)[0] == 1, 'ordinary P1 tile base routes to 086FEA00'
        capture_hashes[str(age)] = sha(ew)
    assert 'count event=dispatch observed=91 suppressed=0' in trace
    assert 'count event=render observed=0 suppressed=0' in trace
    result = dict(status='RENDER_BLINK_SOURCE_AND_TAIL_PASS', snapshot_frames=121,
                  initial_remaining=58, stable_visible_from_age=58, dispatches=91,
                  source_duration=75, native_duration=60, source_algorithm_preserved=True,
                  native_renderer='08012C50 -> 086FF240 -> 086FEA00',
                  unused_IWRAM_hook_hits=0, rejected_mutations=negatives,
                  capture_ewram_sha256=capture_hashes, trace_sha256=sha(trace.encode()),
                  limits=['The 121-boundary tail is one grounded ID14 route, not every camera/game path.',
                          'IWRAM renderer hooks were not on the active replacement-renderer route.',
                          '75 versus 60 is a retained duration difference; no new source/native wall-time parity run.'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()

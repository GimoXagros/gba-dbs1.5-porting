"""Bounded source/native ownership and fixed-point anchors for the new ID13 graph."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(value):
    return hashlib.sha256(value).hexdigest().upper()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    need(not a.output.exists(), 'fresh output')
    s, n = a.source.read_bytes(), a.native.read_bytes()
    need(sha(s) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7', 'source pin')
    need(sha(n) == 'FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD', 'component pin')
    anchors = []

    def exact(data, at, expected, arm=False):
        base = 0x08000000 if arm else 0
        c = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
        ins = list(c.disasm(data[at:at + 192], at + base, len(expected)))
        got = [(i.mnemonic + ' ' + i.op_str).strip() for i in ins]
        need(got == expected, f'exact instruction anchor {at:06X}: {got!r}')
        size = sum(i.size for i in ins)
        anchors.append(dict(raw=at, native=arm, size=size, sha256=sha(data[at:at+size]), instructions=got))

    exact(s, 0x742309, ['mov ax, word ptr [bp - 4]', 'mov bx, word ptr [si + 0x38]',
        'add word ptr [si + 0x32], ax', 'add word ptr [si + 0x34], bx'])
    exact(s, 0x742318, ['mov bx, word ptr [si + 0x34]', 'cmp ax, 0', 'jge 0x742322',
        'neg ax', 'sar ax, 4', 'sar bx, 4'])
    exact(s, 0x742357, ['add word ptr [si + 0x3a], ax', 'add word ptr [si + 0x3c], bx'])
    exact(n, 0x3527A4, ['ldrsh r1, [r4, #0x48]', 'ldrsh r8, [r4, #0x42]',
        'add r8, r8, r0', 'strh r8, [r4, #0x42]', 'ldrsh r8, [r4, #0x44]',
        'add r8, r8, r1', 'strh r8, [r4, #0x44]'], True)
    exact(n, 0x3527C8, ['ldrsh r1, [r4, #0x44]', 'movs r0, r0', 'rsbmi r0, r0, #0',
        'asr r0, r0, #4', 'asr r1, r1, #4'], True)
    exact(n, 0x352824, ['ldrsh r8, [r4, #0x4c]', 'add r8, r8, r1', 'strh r8, [r4, #0x4c]'], True)
    exact(s, 0x76698D, ['mov ax, word ptr es:[bx + 0x1c]', 'mov dx, word ptr es:[bx + 0x1e]',
        'mov word ptr [si + 0x92], ax', 'mov word ptr [si + 0x94], dx'])
    exact(n, 0x355674, ['ldrsh r0, [r1, #0x1a]', 'ldrsh r3, [r1, #0x1c]',
        'strh r0, [r4, #0xa8]', 'strh r3, [r4, #0xaa]'], True)
    exact(n, 0x3525B8, ['stmdb sp!, {r4}', 'ldr r8, [r4]', 'mov lr, pc', 'bx r8', 'ldm sp!, {r4}'], True)
    exact(n, 0x36AE14, ['ldrsh r0, [r4, #0xaa]', 'lsl r0, r0, #5', 'add r1, r1, r0'], True)
    result = dict(status='PASS', source_sha256=sha(s), native_sha256=sha(n), anchors=anchors,
        units='Velocity and acceleration integrate as signed halfwords; velocity ASR4 feeds 1/16-pixel movement. Velocity has 1/256-pixel per-update units. No wall-clock equivalence claimed.',
        lifetime='A8/AA alias action parameters and follow-up state. Action entry overwrites both; ID13 INIT overwrites A8 and each relaunch clears AA. Actor dispatch invokes one current callback.',
        scope='Exact bounded anchors, not an exhaustive global writer census or runtime landing assertion.')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], anchors=len(anchors), sha256=sha(a.output.read_bytes()))))


if __name__ == '__main__':
    main()

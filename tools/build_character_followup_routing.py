#!/usr/bin/env python3
"""Expand the source-identical damage follow-up view for all fifteen fighters."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PRE = 'C50ADCF54D29B327CCF5BFAE21F51784AC2A7A9544DF6093680BDB6387F93DFF'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
WSC10 = '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
WSC15 = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BASE, SITE, TABLE, END = 0x08000000, 0x36A668, 0x628900, 0x62893C


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from('<I', data, at)[0]


def ownership(before):
    need(before[TABLE:END] == b'\xff' * (END - TABLE), 'exact table reservation is FF')
    for at in range(len(before) - 3):
        need(not BASE + TABLE <= word(before, at) < BASE + END,
             'no encoded pointer into new table')
    for at in range(0, len(before) - 3, 4):
        value = word(before, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            delta -= 0x1000000 if delta & 0x800000 else 0
            need(not TABLE <= at + 8 + delta * 4 < END, 'no ARM branch into new table')
        if value & 0x0E1F0000 == 0x041F0000:
            delta = (value & 4095) * (1 if value & 0x800000 else -1)
            need(not TABLE <= at + 8 + delta < END, 'no PC-relative access into new table')


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PRE, GBA, WSC10, WSC15),
         'fixed predecessor and three original identities')
    need(len(before) == 0x800000, 'native candidate extent')
    for lo, hi, digest in (
        (0x36A5FC, 0x36A6BC, 'B4CA36AC057052EBB59315B1CE838599CFBD835A596F968602575FB2D44B072B'),
        (0x36AE08, 0x36AE30, 'D7AC6209461BC39F2D9359DE99BA9E178F20B88212BFF3341C340042998FC5BE'),
        (0x3555D0, 0x35568C, 'D97F696E87FDF8660E2D1E0BE9C5667514683823BFFABD4A3C831C21C65088B1'),
    ):
        need(before[lo:hi] == gba[lo:hi] and sha(before[lo:hi]) == digest,
             'native table, metadata and actual follow-up consumers')
    need(sha(source[0x762762:0x7627DE]) == '72D12D42ED044BDC5FAF0CDC06FBD7318F84893023B28AEBF9497D7B86403437'
         and sha(old[0x3A6582:0x3A65F2]) == '695D8744FF05D9CC937CD4ED9020DCC0EC41943AF7550B34FD394994CB1B3A52',
         'source and commercial ancestor table/record contracts')
    need(struct.unpack_from('<15H', source, 0x762780) == (0x27EE,) * 15
         and struct.unpack_from('<12H', old, 0x3A659A) == (0x2022,) * 12,
         'fifteen source rows share the same commercial follow-up behavior')
    current, ancestor = source[0x75FFD0 + 0x27EE:0x75FFD0 + 0x27EE + 32], old[0x3A45B0 + 0x2022:0x3A45B0 + 0x2022 + 32]
    need(current[:4] + current[8:] == ancestor[:4] + ancestor[8:],
         'identical source action payload outside relocated callback')
    need(source[0x76135B:0x7613BC] == old[0x3A579F:0x3A5800],
         'relocated follow-up callback retains its commercial constructor instructions')
    need(struct.unpack_from('<12I', before, 0x36A62C) == (0x0836A67C,) * 12
         and word(before, SITE) == 0x0836A62C, 'exact native table and metadata pointer')
    ownership(before)
    after = bytearray(before)
    after[TABLE:END] = struct.pack('<15I', *((0x0836A67C,) * 15))
    struct.pack_into('<I', after, SITE, BASE + TABLE)
    spans = ((SITE, 4), (TABLE, END - TABLE))
    inverse = bytearray(after)
    writes = []
    for at, size in spans:
        inverse[at:at + size] = before[at:at + size]
        writes.append(dict(raw=at, bytes=size, before_sha256=sha(before[at:at + size]),
                           after_sha256=sha(after[at:at + size])))
    need(inverse == before, 'complete inverse of two exact Expected Writes')
    need(all(word(after, TABLE + ident * 4) == 0x0836A67C for ident in range(15)),
         'all fighter IDs resolve the proven native follow-up record')
    return bytes(after), dict(schema=1, kind='character-followup-routing', input_sha256=PRE,
        output_sha256=sha(after), expected_writes=writes, fighter_rows=15,
        changed_bytes=sum(a != b for a, b in zip(before, after, strict=True)),
        scope='damage follow-up metadata view only; initial/input action tables remain separate',
        new_ram_bytes=0, new_instructions=0, provided_save_accessed=False, runtime_claim=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'gba', 'wsc10', 'wsc15', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    a = p.parse_args()
    need(all(path.suffix.lower() != '.sav' for path in vars(a).values()), 'save paths forbidden')
    result, manifest = build(*(getattr(a, name).read_bytes() for name in ('before', 'gba', 'wsc10', 'wsc15')))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(result)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('[character-followup-routing] ' + manifest['output_sha256'])


if __name__ == '__main__':
    main()

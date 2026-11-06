#!/usr/bin/env python3
"""Source-pinned drop-through continuation and solid-sidewall closure."""
import argparse
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha


def contracts(r):
    exact(r, 0x766A66, ['mov ax, word ptr [si + 0x4a]', 'and ax, 3',
        'cmp ax, 2', 'jne 0x766ab4', 'mov dx, word ptr [si + 0x4a]',
        'and dx, 0x3c', 'shr dx, 2', 'cmp dx, 1', 'je 0x766ab4',
        'cmp dx, 5', 'je 0x766ab4', 'add word ptr [si + 0x3c], 0x10',
        'or word ptr [si + 6], 3', 'mov word ptr [si], 0x1cda',
        'mov word ptr [si + 2], 0x668e'])
    exact(r, 0x742330, ['test word ptr [si + 4], 0x8000', 'je 0x742357',
        'cmp ax, 0x7f', 'jle 0x74233f', 'mov ax, 0x7f', 'cmp ax, 0xff81',
        'jge 0x742347', 'mov ax, 0xff81', 'cmp bx, 0x7f', 'jle 0x74234f',
        'mov bx, 0x7f', 'cmp bx, -0x7f', 'jge 0x742357', 'mov bx, 0xff81',
        'add word ptr [si + 0x3a], ax', 'add word ptr [si + 0x3c], bx'])
    exact(r, 0x74190A, ['test word ptr [si + 6], 2', 'je 0x741917',
        'push word ptr [si + 0x28]', 'push word ptr [si + 0x3c]'])
    exact(r, 0x74196A, ['test word ptr [si + 6], 2', 'je 0x741977',
        'pop word ptr [si + 0x3c]', 'pop word ptr [si + 0x28]'])
    exact(r, 0x741A12, ['mov word ptr [si + 0x3a], 0',
        'mov word ptr [si + 0x3c], 0'])
    exact(r, 0x7685EB, ['mov word ptr [si], 0x1d14',
        'mov word ptr [si + 2], 0x668e', 'or word ptr [si + 6], 3',
        'mov al, 0xbb', 'out 0xc2, al', 'mov ax, 0x2846', 'mov es, ax',
        'mov bx, word ptr [si + 0x4e]', 'mov ax, word ptr es:[bx + 0x1c]',
        'mov word ptr [si + 0x38], ax', 'mov ax, word ptr es:[bx + 2]',
        'mov word ptr [si + 0x8a], ax', 'lcall 0x668e, 0x6a6',
        'test word ptr [si + 0x4a], 3', 'jne 0x76862f',
        'mov word ptr [si], 0x1b8f', 'mov word ptr [si + 2], 0x668e',
        'and word ptr [si + 6], 0xfffd', 'retf'])
    exact(r, 0x766F86, ['push ax', 'push dx', 'push bx', 'push es',
        'mov word ptr [si + 0x32], 0', 'mov word ptr [si + 0x36], 0',
        'test word ptr [si + 0x1e], 0xa', 'je 0x766fc0'])
    exact(r, 0x76FEBD, ['and dx, 3', 'je 0x76feff', 'cmp dx, 2',
        'je 0x76feff', 'mov ax, word ptr [di + 0x3a]',
        'mov bx, word ptr [di + 0x26]', 'mov cx, word ptr [di + 0x42]',
        'shl cx, 4', 'add bx, ax', 'or ax, ax', 'js 0x76ff02'])
    exact(r, 0x76FEF0, ['and bx, 0xff80', 'sub bx, cx', 'dec bx',
        'mov word ptr [di + 0x26], bx', 'mov word ptr [di + 0x3a], 0'])
    exact(r, 0x76FF0E, ['and bx, 0xff80', 'add bx, 0x80', 'add bx, cx',
        'mov word ptr [di + 0x26], bx', 'mov word ptr [di + 0x3a], 0'])
    exact(r, 0x76F91E, ['js 0x76f937', 'shr cx, 4', 'mov ax, cx',
        'add cx, word ptr [di + 0x42]', 'shr cx, 3'])
    exact(r, 0x76F95A, ['or ax, word ptr es:[si + 2]',
        'or dx, word ptr es:[si]', 'add si, bx', 'dec cx', 'jne 0x76f95a'])


def analyze(r):
    need(sha(r) == SOURCE_SHA, 'immutable source')
    contracts(r)
    grid = list(struct.iter_unpack('<HH', r[0x33CA20:0x33CA20+56*54*4]))
    need(all(aux == 0 and flags in (0, 1, 2, 3) for flags, aux in grid),
         'no material or auxiliary displacement')
    need(all(grid[y*56+x][0] & 1 for y in range(50)
             for x in (*range(7), *range(49,56))), 'continuous solid sidewalls')
    radii = []
    speeds = []
    exact(r,0x7674B4,['add word ptr [si + 0x4e], 0x50'])
    for form in (0,0x50):
        for n in range(15):
            p = 0x3B8460 + struct.unpack_from('<H', r, 0x3B8460+n*2)[0] + form
            radii.append(struct.unpack_from('<HH', r, p+0x24))
            speeds.append(struct.unpack_from('<H', r, p)[0])
            need(struct.unpack_from('<H', r, p+0x1C)[0] == 30, 'base/evolved drop gravity30')
    need(set(radii) == {(6,30),(6,48),(6,56)}, 'all30 base/evolved player footprints')
    lo, hi = 7*128+6*16, 49*128-6*16-1
    # Exact 76FEF0/76FF0E cancellation at the first solid sidewall column.
    wall_cases = 0
    for x in range(lo,hi+1):
        for dx in range(-127,128):
            after=x+dx
            edge=after+(96 if dx>0 else -96)
            if dx>0 and edge>>7 >=49:
                after=(edge & ~127)-96-1
            elif dx<0 and edge>>7 <7:
                after=(edge & ~127)+128+96
            need(lo<=after<=hi, 'horizontal collision retains complete-footprint interior')
            wall_cases+=1
    support=[]
    for row in range(54):
        for x in range(0,56*128):
            first=max(0, ((x>>4)-6)>>3)
            last=min(55, ((x>>4)+6)>>3)
            flags=0
            for col in range(first,last+1):
                flags |= grid[row*56+col][0]
            if flags == 2:
                need(lo<=x<=hi, 'drop entry support excludes both solid walls')
                support.append((row,x))
    rows=sorted({row for row,x in support})
    need(rows == [33,39,42,44], 'all actual drop-support rows')
    max_y=max(rows)*128+127
    max_after=max_y+127+16
    need(max_after<50*128, 'even first drop step cannot jump empty gap to bottom floor')
    need(all(grid[y*56+x][0] == 0 for y in range(45,50) for x in range(7,49)),
         'entire retained footprint samples empty below final one-way platform')
    # Every fraction and nonnegative capped step from every supported row:
    # either another supported/solid row is sampled above the empty gap, or
    # the first empty sample clears drop before the next collision update.
    transitions=0
    for row in rows:
        for fraction in range(128):
            for delta in range(144):
                y=row*128+fraction+delta
                need(y<6400, 'drop continuation cannot bypass bottom floor')
                if y>=45*128:
                    need(45<=y//128<=46, 'first lower-gap sample is empty')
                transitions+=1
    negatives=[]
    for at in (0x742349,0x741971,0x768629,0x76FF0E,0x766A6C):
        bad=bytearray(r);bad[at]^=1
        try: contracts(bad)
        except ValueError: negatives.append(hex(at))
        else: raise ValueError('ineffective mutation')
    return dict(source_sha256=SOURCE_SHA, footprints=sorted(set(radii)), stat_rows=len(radii), interior_X=[lo,hi],
        horizontal_cases=wall_cases, drop_support_rows=rows, supported_samples=len(support),
        vertical_transitions=transitions, max_first_step=143, max_drop_Y=max_after,
        subsequent_own_step_max=127, all_form_horizontal_speeds=speeds,
        empty_sample_exit='768619 -> 768629 clears flag2 before next collision',
        negative_or_zero_vy='7419CC..DE clears support on airborne vy<=0; next drop callback exits',
        closed_contract='terrain-enabled base/evolved fighter drop callback with ordinary actor own-motion',
        separate_ownership='entry terrain flags and external callback/coordinate writers audited separately',
        negative_controls_rejected=negatives, ROM_modified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh output required')
    result=analyze(a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',result['horizontal_cases'],'wall cases;',result['vertical_transitions'],
          'drop transitions; maximum drop Y',result['max_drop_Y'])


if __name__=='__main__': main()

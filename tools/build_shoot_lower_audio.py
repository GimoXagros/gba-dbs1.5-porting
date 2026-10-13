#!/usr/bin/env python3
"""Append CF/D1 native M4A reconstructions; never execute or inspect saves."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, struct

INPUT_SHA256 = '726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284'
GBA_SHA256 = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
WSC10_SHA256 = '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
WSC15_SHA256 = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BASE = 0x08000000
TABLE = 0x5BA400
CF, D1, VOICES = 0x5CA000, 0x5CA100, 0x5CA300
CF_BYTES = bytes.fromhex('00000f00a202c100a177a7071f0313071f0316071f0319071f0320071f0323071f0326071f032907ffff')
D1_BYTES = bytes.fromhex('00000f01c240a31aa20016083010a204cb10a334a00f62061f02a00562081f04a0026206ffff')

def sha(data): return hashlib.sha256(data).hexdigest().upper()
def need(ok, message):
    if not ok: raise ValueError(message)

def source_events(payload):
    """Finite score parser, not an APU/CPU interpreter."""
    wave, volume, mode, period, modulation, cursor, time = payload[1], payload[2], 0, 0, 0, 4, 0
    out = []
    while payload[cursor:cursor+2] != b'\xff\xff':
        op, arg = payload[cursor:cursor+2]; cursor += 2
        if op == 0xA0: volume = arg
        elif op == 0xA2: wave = arg
        elif op == 0xA3: modulation = arg
        elif 0xC0 <= op <= 0xCF: mode, period = op & 15, arg
        elif op == 0xA1: pass  # conditional hardware sweep; explicit QA boundary
        elif op == 0xA7:
            out.append(dict(time=time, ticks=arg, note=None)); time += arg
        elif op < 0xA0:
            out.append(dict(time=time, ticks=arg, note=op if (op & 15) < 12 else None,
                            wave=wave, volume=volume, mode=mode, period=period, modulation=modulation))
            time += arg
        else: raise ValueError(f'unsupported score command {op:02X}')
    need(cursor + 2 == len(payload), 'whole source score consumed')
    return out, time

def envelope(source, event):
    result = []
    for age in range(event['ticks']):
        volume = event['volume'] & 15
        if event['mode'] and event['period']:
            # Original four-step shift/subtract quotient for the bounded
            # ages here equals floor(age*16/period); no 8-bit wrap is reached.
            slot = age * 16 // event['period']
            need(slot < 16, 'bounded envelope index')
            shape = source[0x754DA0 + event['mode'] * 16 + slot] & 0xF0
            volume = source[0x754867 + (shape | volume)] >> 4
        result.append((volume * 127 + 7) // 15)
    return result

def track(payload, wsc):
    events, total = source_events(payload)
    out = bytearray((0xBC, 0, 0xBB, 0x4B, 0xBF, 0x7F))
    details = []
    for event in events:
        if event['note'] is None:
            need(0 < event['ticks'] <= 24, 'short rest')
            out.append(0x80 + event['ticks'])
            continue
        voice = {2: 0, 0: 1, 4: 2}[event['wave']]
        mod = event['modulation']
        out.extend((0xBD, voice, 0xC2, 0x10, 0xC4, mod, 0xC5, 0))
        values = envelope(wsc, event)
        note = 36 + 12 * (event['note'] >> 4) + (event['note'] & 15)
        need(0 <= note < 128 and 0 < event['ticks'] <= 24, 'native pitch/duration')
        out.extend((0xBE, values[0], 0xCF + event['ticks'], note, 0x7F))
        previous = values[0]
        for age, value in enumerate(values):
            if value != previous:
                out.extend((0xBE, value)); previous = value
            out.append(0x81)
        details.append(dict(**event, midi_note=note, native_voice=voice, volumes=values))
    out.extend((0xC4, 0, 0xB1))
    return bytes(out), dict(total_ticks=total, notes=details, source_events=events)

def incoming(data, intervals):
    refs = []
    for pos in range(0, len(data)-3, 4):
        word, = struct.unpack_from('<I', data, pos)
        values = [('pointer', word)]
        if word & 0x0E000000 == 0x0A000000:
            d = word & 0xFFFFFF
            if d & 0x800000: d -= 0x1000000
            values.append(('branch', (BASE+pos+8+d*4) & 0xFFFFFFFF))
        for kind, value in values:
            if any(BASE+begin <= value < BASE+end for begin,end in intervals):
                refs.append(dict(site=pos, kind=kind, target=value))
    return refs

def main():
    p=argparse.ArgumentParser()
    for name in ('input','gba','wsc10','wsc15','output'): p.add_argument(name,type=pathlib.Path)
    p.add_argument('--manifest',required=True,type=pathlib.Path)
    a=p.parse_args()
    before,gba,old,wsc=[getattr(a,n).read_bytes() for n in ('input','gba','wsc10','wsc15')]
    for b,h in zip((before,gba,old,wsc),(INPUT_SHA256,GBA_SHA256,WSC10_SHA256,WSC15_SHA256),strict=True):
        need(sha(b)==h,'input hash')
    need(wsc[0x3F891A:0x3F8944]==CF_BYTES and wsc[0x3F895E:0x3F8984]==D1_BYTES,'source payloads')
    need(sha(before[TABLE:TABLE+0x5D*8])=='E2EDA063E005E0F5552CA70631A40B34B75F24CF8B4455EEEB3F5D98EDE8830B','existing table')
    voices = bytearray()
    for address in (0x37E8E0+0x14*12, 0x37E8E0+0x17*12, 0x37EAA8+8*12):
        record=bytearray(gba[address:address+12])
        record[8:12]=bytes((0,0,15,0))  # source finite envelopes own amplitude
        voices.extend(record)
    placements=[(VOICES,bytes(voices),'voices')]; schedules={}
    for sid,offset,payload in ((0x5D,CF,CF_BYTES),(0x5E,D1,D1_BYTES)):
        stream,schedule=track(payload,wsc); schedules[f'{sid:02X}']=schedule
        song=bytes((1,0,0x28,0x80))+struct.pack('<II',BASE+VOICES,BASE+offset+12)+stream
        need(len(song)<0x100 if sid==0x5D else len(song)<0x200,'song capacity')
        placements.extend(((offset,song,f'song_{sid:02X}'),
                           (TABLE+sid*8,struct.pack('<IHH',BASE+offset,4,4),f'entry_{sid:02X}')))
    intervals=[(offset,offset+len(blob)) for offset,blob,_ in placements]
    need(not incoming(before,intervals),'pre-existing incoming references')
    after=bytearray(before); writes=[]; allowed=set()
    for offset,blob,label in placements:
        need(before[offset:offset+len(blob)]==b'\xff'*len(blob),'Expected Write '+label)
        after[offset:offset+len(blob)]=blob;allowed.update(range(offset,offset+len(blob)))
        writes.append(dict(label=label,offset=offset,bytes=len(blob),sha256=sha(blob)))
    changed={i for i,(x,y) in enumerate(zip(before,after,strict=True)) if x!=y}
    need(changed and changed<=allowed,'whole ROM diff containment')
    report=dict(input_sha256=INPUT_SHA256,output_sha256=sha(after),writes=writes,
                schedules=schedules,changed_bytes=len(changed),runtime_executed=False,
                fidelity_limits=['commercial timbre analogues','right pan follows earlier bounded reconstructions; hardware mix parity unverified',
                    'A3 represented with native MOD analogue','CF A1 hardware sweep remains unverified'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['output_sha256'])
    return 0
if __name__=='__main__': raise SystemExit(main())

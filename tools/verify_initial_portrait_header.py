"""Check the actual initial portrait path against its retail transfers and localized headers."""
import argparse
import json
import struct
from pathlib import Path
from verify_character_select_name_scene import BASE, DMA, mem, need, sha

BEFORE = '9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5'
AFTER = 'F61053394798E4529F45A75E8363791EC8777774681F0B7354A69966EF780E3B'


def verify(before, after, manifest, headers):
    need((sha(before),sha(after)) == (BEFORE,AFTER), 'exact initial-entry composite')
    need(sha(headers) == '8D4FC0A9973981D40FCA86CC639CF35D49AF580C13CC10B9810CAAB4D7636B43','header owner')
    table = json.loads(headers)['table_span'][0]
    inverse = bytearray(after)
    for at,size in manifest['writes']:
        inverse[at:at+size] = before[at:at+size]
    need(inverse==before,'whole image inverse')
    for tag in range(256):
        state = dict(seed=tag,flags=(tag%16)<<28|0x1F)
        reference,live = DMA(before,**state),DMA(after,**state)
        for cpu in (reference,live):
            cpu.put(0x0300112F,tag,1)
            cpu.run(0x080817A4,{0x080817C4})
        language = tag-0xA0 if 0xA0<=tag<=0xA3 else 0
        pointer = struct.unpack_from('<I',before,table+60*language)[0]
        old_transfers=[(0x080A28A0,0x06005780,1536),(0x080A2880,0x05000020,8)]
        need(reference.transfers==old_transfers,'actual retail initial portrait/palette transfer')
        need(live.transfers==[old_transfers[0],(pointer,0x06005780,192),old_transfers[1]],'one selected initial header transfer')
        need(mem(live,0x06005780,768)==before[pointer-BASE:pointer-BASE+768],'exact installed language header')
        need(reference.r[:15]==live.r[:15] and reference.cpsr==live.cpsr,'register and flag parity')
        sp=reference.r[13]
        for at in live.mem.keys()|reference.mem.keys():
            if sp-64<=at<sp or 0x06005780<=at<0x06005A80:continue
            need(live.mem.get(at)==reference.mem.get(at),'all other live bytes equal')
    return dict(status='PASS',image=AFTER,previous=BEFORE,tags=256,hardware_DMA_modeled=True,
        physical_header=[0x06005780,0x06005A80],body_preserved=5376,whole_image_inverse=True,
        checker_sha256=sha(Path(__file__).read_bytes()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','manifest','owner','report'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    result=verify(a.before.read_bytes(),a.after.read_bytes(),json.loads(a.manifest.read_bytes()),a.owner.read_bytes())
    a.report.parent.mkdir(exist_ok=True,parents=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()

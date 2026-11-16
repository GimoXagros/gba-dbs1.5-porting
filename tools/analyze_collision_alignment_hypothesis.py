"""Bound the historical collision metadata hypothesis, without replay or ROM edits."""
import argparse, hashlib, json, struct
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser();p.add_argument('--historical',type=Path,required=True);p.add_argument('--probe',type=Path,required=True);p.add_argument('--emulator-source',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 b=a.historical.read_bytes();j=a.probe.read_bytes();m=a.emulator_source.read_bytes()
 assert sha(b)=='389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1'
 assert sha(j)=='22A2F2D822688D1E2E7239C987F303AA2F6AA8FEE6AD0A5EBADA4437D16C9937'
 assert sha(m)=='501DBBCA7D5D7CBAA86240DE2D6A4E2E1186B50F74DDE11BCF2F323C4AF8C437'
 regs=struct.unpack('<17I',bytes.fromhex(json.loads(j)['timeout_registers_hex']))
 assert regs[0]==0 and regs[2]==0 and regs[3]==0x04000020
 assert struct.unpack_from('<3I',b,0x36E374)==(0xE5941010,0xE1D100B0,0xE1D130B2)
 assert b'int rotate = (address & 1) << 3;'in m and b'return ROR(value, rotate);'in m
 def rotate(v,n):return ((v>>n)|(v<<(32-n)))&0xFFFFFFFF if n else v
 assert rotate(0x2004,8)==regs[3] and rotate(0x2004,0)!=regs[3] and rotate(0,8)==0
 candidates=[i for i in range(0,len(b)-3,2)if b[i:i+4]==bytes.fromhex('00000420')]
 assert candidates==[0xD2920]
 assert rotate(struct.unpack_from('<H',b,candidates[0]+4)[0],8)==regs[2]
 pointer=0x08000000+candidates[0]+1
 pointer_refs=[i for i in range(len(b)-3)if b[i:i+4]==struct.pack('<I',pointer)]
 assert not pointer_refs
 assert regs[11]==0x080D26F0 and struct.unpack_from('<2I',b,0xD26E8)==(0x7E0,regs[11])
 assert regs[8]+regs[1]*2==0x0836EF1C and struct.unpack_from('<I',b,0x36EF1C)[0]==regs[9]==regs[15]
 report=dict(status='HYPOTHESIS_BOUNDED_NOT_ROOT_CAUSE',input_sha256=dict(rom=sha(b),probe=sha(j),emulator_source=sha(m)),registers=[f'{x:08X}'for x in regs],conditional_odd_pointer=f'{pointer:08X}',raw_signature_offsets=[f'{x:06X}'for x in candidates],literal_pointer_occurrences=pointer_refs,source_url='https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/memory.c#L612-L614',limitations=['Timeout packet is not an immediate pre-dispatch capture.','Requires ordinary E37C path with unchanged r3 afterward.','Unique candidate applies only to this ROM region; failure-time RAM/IO/mirrors unobserved.','The executable binary-to-source identity is not independently proved.','No writer provenance or corrective ROM change established.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()

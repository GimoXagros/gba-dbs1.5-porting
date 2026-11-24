"""Actual ARM author fixtures for source mode22 state primitives, no device stub."""
import argparse,hashlib,json,struct
from pathlib import Path
from verify_shoot_static_companion_clear import Machine
from mode23_linker import compose
import mode22_source_scene as scene
BASE=0x08000000;START=0x08010000;BUFFER=0x02018000
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def oracle(values,rank):
 out=list(values)
 if out[10]!=0 or not any(x<9 for x in out[rank:]):return out,0
 for i in range(rank,11):
  out[i]=(out[i]+1)&65535
  if out[i]<10:break
  out[i]=9
  if i==10:break
  out[i]=0
 return out,1
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--source',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 source=a.source.read_bytes();code,symbols,link=compose([scene.assembly(source)],START,scene.EXPORTS);rom=bytes(START-BASE)+code
 def run(name,args,snapshot=None,flags=0):
  m=Machine(rom,seed=1,flags=flags<<28|0x1F)
  for i,v in enumerate(args):m.r[i]=v
  if snapshot is not None:
   assert len(snapshot)==42
   for i,v in enumerate(snapshot):m.put(BUFFER+i,v,1)
  original=m.r[:];m.run(symbols[name],{m.r[14]})
  assert m.r[1:14]==original[1:14]
  assert all(original[13]-160<=at<original[13] or BUFFER<=at<BUFFER+42 for at,v,n in m.writes)
  return m
 def snapshot(values):return bytes(range(18))+struct.pack('<11H',*values)+b'\xA6\xB7'
 def values(m):return list(struct.unpack('<11H',bytes(m.mem[BUFFER+18+i]for i in range(22))))
 carries=awards=ranks=classifies=0
 patterns=[[0]*11,[8]*10+[0],[9]*10+[0],[65535]*10+[0],[65534]*10+[0],[0]*10+[1]]
 patterns += [[9]*i+[0]+[9]*(9-i)+[0]for i in range(10)]
 for rank in range(11):
  for v in patterns:
   expected,changed=oracle(v,rank)
   for flags in range(16):
    m=run('m22_source_carry',[BUFFER,rank],snapshot(v),flags)
    assert m.r[0]==changed and values(m)==expected
    assert bytes(m.mem[BUFFER+i]for i in range(18))==bytes(range(18))and bytes(m.mem[BUFFER+40+i]for i in range(2))==b'\xA6\xB7'
    carries+=1
 tables=[struct.unpack_from('<11H',source,0x785092+d*22)for d in range(4)]
 for difficulty,table in enumerate(tables):
  for score in sorted({0,65535}|{max(0,min(65535,t+delta))for t in table for delta in(-1,0,1)}):
   rank=next(i for i,t in enumerate(table)if score<=t)
   for flags in range(16):
    m=run('m22_source_score_rank',[difficulty,score],flags=flags);assert m.r[0]==rank;ranks+=1
   for v in patterns[:6]:
    expected,changed=oracle(v,rank);m=run('m22_source_score_award',[BUFFER,difficulty,score],snapshot(v))
    assert m.r[0]==(0x8000|rank if changed else 0xffff)and values(m)==expected;awards+=1
 for status in (0,1,2,3,255):
  for high in(-1,0,9,10):
   v=[0]*11
   if high>=0:v[high]=1
   for flags in range(16):
    # Error statuses deliberately have no readable snapshot memory.
    raw=None if status in(1,3,255)else snapshot(v)
    m=run('m22_snapshot_classify',[BUFFER,status],raw,flags)
    expected=8 if status==1 else 16 if status>=3 else 1 if status==2 or high==-1 else 4 if high==10 else 2
    assert m.r[0]==expected
    if status==2:assert bytes(m.mem[BUFFER+i]for i in range(42))==bytes(42)
    elif status==0:assert bytes(m.mem[BUFFER+i]for i in range(42))==raw
    else:assert not any(BUFFER<=at<BUFFER+42 for at,v,n in m.writes)and not any(BUFFER<=at<BUFFER+42 for at,n in m.reads)
    classifies+=1
 result=dict(status='PURE_STATE_PRIMITIVES_PASS',source_sha256=sha(source),module_sha256=sha(Path(scene.__file__).read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),code_sha256=sha(code),code_bytes=len(code),symbols=symbols,link=link,carry_actual_ARM_cases=carries,score_rank_boundary_cases=ranks,score_award_cases=awards,storage_status_classifier_cases=classifies,error_status_snapshot_reads=0,error_status_snapshot_writes=0,limits=['Not a registered viewer, native storage integration, mode11 hook or actual award/save proof.','Real42-byte fixture inputs only; no fake device-success import.','Source 16-bit carry/overflow behavior preserved, including nondecimal input words; no silent clamping.','Error status1/3 and unknownstatus select distinct target error categories without reading returned payload.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()

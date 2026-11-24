"""Independent ARM condition/LR and fail-closed syntax checks of scene linking."""
import argparse,hashlib,json,struct
from pathlib import Path
from mode23_linker import compose
import mode23_linker
from verify_shoot_child_contact_component import Machine
BASE=0x08000000
CODE=0x08E00000
NATIVE=0x080159B0
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def condition(c,f):
 n,z,carry,v=[bool(f&x) for x in (8,4,2,1)]
 return [z,not z,carry,not carry,n,not n,v,not v,carry and not z,not carry or z,n==v,n!=v,not z and n==v,z or n!=v,True][c]
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 conditions={'eq':0,'ne':1,'hs':2,'cs':2,'lo':3,'cc':3,'mi':4,'pl':5,'vs':6,'vc':7,'hi':8,'ls':9,'ge':10,'lt':11,'gt':12,'le':13,'':14,'al':14}
 cases=0;images=0
 for op in ('b','bl'):
  for suffix,c in conditions.items():
   for numeric in (False,True):
    for form in ('line','inline','indented'):
     branch=op+suffix+' '+('0x080159B0' if numeric else 'target')
     body={'line':'entry:\n'+branch,'inline':'entry: '+branch,'indented':'entry:\n    '+branch}[form]
     body+='\nfall: bx lr\ntarget: bx lr\n'
     code,sym,meta=compose([body],CODE,['entry','fall','target'])
     assert meta['direct_branches_checked']==(2 if op=='bl' and c!=14 else 1)
     assert len(meta['native_veneers'])==int(numeric)
     rom=bytearray(0x1000000);rom[CODE-BASE:CODE-BASE+len(code)]=code
     dest=NATIVE if numeric else sym['target'];images+=1
     for flags in range(16):
      m=Machine(rom,seed=6,flags=(flags<<28)|31);prior=m.r.copy();expected=condition(c,flags)
      stop=m.run(sym['entry'],{sym['fall'],dest},max_steps=8)
      assert stop==(dest if expected else sym['fall'])
      assert m.r[:14]==prior[:14] and m.cpsr==(flags<<28)|31
      assert m.r[14]==(sym['fall'] if expected and op=='bl' else prior[14])
      cases+=1
 negative=['entry: bl 0X080159B0','entry: bl 134306224','entry: bl 0x080159B0 @ comment',
           'entry: BL 0x080159B0','entry: b missing','entry: bl 0x080159B1','entry: bl 0x02000000',
           'entry: bx lr\nentry: bx lr','entry: alias: bl 0X080159B0',
           'entry: alias: bl 134306224','entry: alias: bl 0x080159B0 @ comment']
 rejected=0
 for body in negative:
  try:compose([body],CODE,['entry'])
  except (AssertionError,ValueError):rejected+=1
  else:raise AssertionError(('unsupported branch accepted',body))
 result=dict(status='MODE23_LINKER_INDEPENDENT_PASS',tool_sha256=sha(Path(__file__).read_bytes()),module_sha256=sha(Path(mode23_linker.__file__).read_bytes()),actual_arm_cases=cases,linked_images=images,negative_rejections=rejected,coverage='All16 NZCV; B/BL all condition aliases, symbolic/native, inline/indented/standalone; exact target, LR, SP, non-PC registers and flags.',limits=['Finite branch syntax and generated ARM verification, not all scene semantics or runtime.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()

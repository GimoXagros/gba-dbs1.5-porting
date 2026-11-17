"""Compose mode23 ARM with checked symbolic branches and absolute native veneers.

Keystone numeric relative branches are not trusted across composed sections.
All such branches become symbolic calls to literal PC veneers. Every direct
branch (including source callback branches) has its actual encoding checked.
"""
import re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
CONDITIONS={'eq':0,'ne':1,'hs':2,'cs':2,'lo':3,'cc':3,'mi':4,'pl':5,'vs':6,'vc':7,'hi':8,'ls':9,'ge':10,'lt':11,'gt':12,'le':13,'':14,'al':14}
BRANCH=re.compile(r'^(b|bl)(eq|ne|hs|cs|lo|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al)?\s+(0x[0-9a-fA-F]+|[A-Za-z_]\w*)\s*$',re.M)
def compose(bodies,address,exports=()):
 text='\n'.join(line.strip() for body in bodies for line in body.splitlines())
 while True:
  normalized=re.sub(r'(?m)^(\w+):[ \t]*(?=\S)',r'\1:\n',text)
  if normalized==text:break
  text=normalized
 mnemonics={op+condition for op in ('b','bl') for condition in CONDITIONS}
 for line in text.splitlines():
  token=line.split(None,1)[0].lower() if line.strip() else ''
  if token in mnemonics and not BRANCH.fullmatch(line):raise ValueError('unsupported direct branch syntax: '+line)
 natives={};checks=[]
 def replace(m):
  op,cond,target=m.group(1),m.group(2) or '',m.group(3)
  if target.startswith('0x'):
   value=int(target,16);assert value%4==0 and 0x08000000<=value<0x0A000000,'typed ARM ROM external'
   target='m23_link_native_'+format(value,'08X');natives[target]=value
  site='m23_link_branch_'+str(len(checks));checks.append((site,target,op=='bl',CONDITIONS[cond]))
  # Conditional BL forward labels also have a Keystone defect. Express the
  # exact condition as an opposite conditional skip plus unconditional BL.
  if op=='bl' and cond and CONDITIONS[cond]!=14:
   opposite={0:'ne',1:'eq',2:'lo',3:'hs',4:'pl',5:'mi',6:'vc',7:'vs',8:'ls',9:'hi',10:'lt',11:'ge',12:'le',13:'gt'}[CONDITIONS[cond]]
   end=site+'_skip';skip=site+'_condition'
   checks[-1]=(skip,end,False,CONDITIONS[cond]^1)
   checks.append((site,target,True,14))
   return skip+':\nb'+opposite+' '+end+'\n'+site+':\nbl '+target+'\n'+end+':'
  return site+':\n'+op+cond+' '+target
 text=BRANCH.sub(replace,text)
 for name,target in sorted(natives.items()):text+='\n'+name+': .word 0xE51FF004, '+str(target)+'\n'
 labels=re.findall(r'^(\w+):',text,re.M);assert len(labels)==len(set(labels)),'duplicate symbol'
 required=set(exports)|{t for _,t,_,_ in checks};assert required<=set(labels),('unresolved',sorted(required-set(labels)))
 directory=list(dict.fromkeys(list(exports)+[x for pair in checks for x in pair[:2]]+list(natives)))
 marker='m23_link_directory';text+='\n.align 2\n'+marker+':\n'+'\n'.join('.word '+n for n in directory)+'\n'
 raw=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(text,address)[0]);size=len(directory)*4
 values=struct.unpack_from('<'+'I'*len(directory),raw,len(raw)-size);symbols=dict(zip(directory,values));code=raw[:-size] if size else raw
 for site,target,link,condition in checks:
  at=symbols[site]-address;w=struct.unpack_from('<I',code,at)[0]
  assert w&0x0E000000==0x0A000000 and bool(w&0x1000000)==link and w>>28==condition,(site,'opcode')
  disp=w&0xFFFFFF
  if disp&0x800000:disp-=1<<24
  assert address+at+8+disp*4==symbols[target],(site,target,'actual direct target')
 for name,target in natives.items():assert struct.unpack_from('<2I',code,symbols[name]-address)==(0xE51FF004,target)
 return code,{n:symbols[n] for n in exports},dict(direct_branches_checked=len(checks),native_veneers={name:dict(address=symbols[name],target=value) for name,value in sorted(natives.items())},directory_removed_bytes=size)

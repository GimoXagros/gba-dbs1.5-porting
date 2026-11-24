"""Installed title selector, real constructor, prompt wait and Start handoff."""
import argparse,json
from pathlib import Path
from check_mode23_title_installed_r2 import FastResourceMachine
from build_mode23_title_scene_r2 import sha,BASE

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('component','manifest','assets_manifest','report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();rom=a.component.read_bytes();meta=json.loads(a.manifest.read_text(encoding='utf-8'));assets=json.loads(a.assets_manifest.read_text(encoding='utf-8'))
 assert sha(rom)==meta['output_sha256']=='9F0DA0316B76CA6D2634DF7F89CCE1FFD1F1B0AC2CB37B2EDCDC0753466B228A'
 symbols=meta['symbols'];code=set(range(BASE+meta['code_span'][0],BASE+meta['code_span'][1],4))
 selector_cases=0
 for tag in range(256):
  for nzcv in range(16):
   m=FastResourceMachine(rom,seed=tag+1,flags=(nzcv<<28)|0x1F)
   m.put(0x0300112F,tag,1);old=m.r.copy();flags=m.cpsr;m.r[14]=0x08090A1C
   m.run_checked(0x08090A18,code|{0x08090A18})
   language=('english','japanese','korean','digicode')[tag-0xA0 if 0xA0<=tag<=0xA3 else 0]
   assert m.r[8]==meta['asset_pointers'][language+'_p0'] and m.cpsr==flags
   assert all(m.r[i]==old[i]for i in range(14)if i!=8)
   selector_cases+=1
 positions=code|set(range(0x08090BF4,0x08090E00,4))|set(range(0x08011AC4,0x08012020,4))|set(range(0x08012710,0x08012DD8,4))|set(range(0x086FEA00,0x086FF28C,4))|set(range(0x08D8D200,0x08D8D2E8,4))|set(range(0x080D15C0,0x080D15EC,4))
 cases=[]
 for language in assets['languages']:
  for eligible in (0,1):
   m=FastResourceMachine(rom,seed=19,flags=0x6000001F);m.eligible=eligible;m.eeprom_reads=0
   for start,size in ((0x02010000,52*0x118),(0x03002A60,0x200),(0x03001428,0x1000),(0x02000000,0x1000),(0x030022F0,0x60)):
    for at in range(start,start+size):m.put(at,0,1)
   for at in (0x03001338,0x0300133C,0x03001340,0x03001344,0x030012D0):m.put(at,0)
   for at in (0x030012CA,0x030012B6,0x030012CC,0x030012CE,0x0300130A):m.put(at,0,2)
   def invoke(address):
    m.r[14]=0x12345678;m.run_checked(address,positions)
   def stack_call(address,args):
    sp=m.r[13];m.r[13]-=4*len(args);saved=m.r[4:12].copy()
    for i,value in enumerate(args):m.put(m.r[13]+4*i,value)
    m.r[11]=0;invoke(address);m.r[13]=sp;m.r[4:12]=saved
   # Existing native five-presentation construction ABI; no private service substitute.
   for i in range(5):
    args=[0]*15;args[0]=i;args[1]=1;args[2]=0x1800;args[3]=0x4000;args[6]=0x08090878;args[9]=meta['asset_pointers'][language+'_p0'];args[12]=meta['asset_pointers']['p1'];args[14]=0x03002A78+i*0x50
    stack_call(0x080127E4,args)
    m.put(0x03002A78+i*0x50,112,2);m.put(0x03002A7A+i*0x50,72,2)
    m.r[0]=0x03002A78+i*0x50;m.r[1]=i;invoke(symbols['m23_title_event'])
   m.r[11]=0;invoke(0x08090BF4)
   assert m.get(0x03001338)==2
   headers=[0x02010000+i*0x118 for i in range(52)if m.get(0x02010000+i*0x118)==symbols['m23_title_init_callback']]
   assert len(headers)==1;header=headers[0];m.put(0x0300133C,header)
   for ticks in range(60):
    m.r[11]=0;m.put(0x030012CA,0,2);invoke(m.get(header))
    assert m.get(header)==0x08090C7C and m.eeprom_reads==1
   assert m.get(0x03002A62,1)==1 and m.get(header+0x18+0x1C)==eligible
   m.put(0x0300130A,0x20,2);m.r[11]=0;invoke(m.get(header))
   assert m.get(header)==symbols['m23_title_enter_root'] and m.get(0x030022F2,2)==0x1F
   m.put(0x0300130A,0,2)
   for slide in range(160):
    m.put(0x030012CA,0,2);invoke(m.get(header))
    if m.get(header)==symbols['m23_title_idle']:break
   else:raise AssertionError('root entry did not reach idle')
   assert m.get(header+0x1C,1)==0 and m.get(header+0x1E,1)==5
   assert m.get(0x030012CA,2)==assets['languages'][language]['root_parts']
   cases.append(dict(language=language,eligible=eligible,native_wait_ticks=60,root_slide_callbacks=slide+1,root_parts=m.get(0x030012CA,2),actual_eeprom_reads=m.eeprom_reads))
 report=dict(status='INSTALLED_TITLE_CONSTRUCTOR_PROMPT_START_PASS',component_sha256=sha(rom),manifest_sha256=sha(a.manifest.read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),selector_cases=selector_cases,cases=cases,limits=['Native complete mode initializer and display/audio playback hardware not executed','Five presentation initialization uses its actual native constructor with explicit source-equivalent arguments','Only low-level EEPROM device read is a fixture; installed eligibility comparison, constructor, prompt timer, Start queue and root callbacks execute'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()

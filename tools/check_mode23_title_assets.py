"""Author eleven-event title checks through the actual native sprite consumer."""
import argparse,json,struct
from pathlib import Path
from check_mode23_scene_resources import ResourceMachine
from mode23_linker import compose
import mode23_native_services as services
from build_mode23_title_assets import sha,NATIVE,SOURCE

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','assets_dir','report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.report.exists()
 source=a.source.read_bytes();native=a.native.read_bytes();assert (sha(source),sha(native))==(SOURCE,NATIVE)
 meta=json.loads((a.assets_dir/'manifest.json').read_text(encoding='utf-8'));data=(a.assets_dir/'assets.bin').read_bytes();assert sha(data)==meta['sha256']
 body=services.assembly(native)
 code,sym,proof=compose([body,'m23_bf42_atan:bx lr\nm23_view_install:bx lr'],0x08E10000,['m23_present_construct','m23_present_event','m23_present_update_draw'])
 rom=bytearray(native);rom[0xE00000:0xE00000+len(data)]=data;rom[0xE10000:0xE10000+len(code)]=code
 positions=set(range(0x08E10000,0x08E10000+len(code),4))|set(range(0x080127E4,0x08012DD8,4))|set(range(0x080110AC,0x08011130,4))|set(range(0x086FEA00,0x086FF28C,4))
 p1=0x08E00000+next(o['offset']for o in meta['objects']if o['label']=='p1');p2=0x08E00000+next(o['offset']for o in meta['objects']if o['label']=='p2')
 results=[]
 for language,values in meta['languages'].items():
  for events in ([0],[1,2,3,4,5],[6,7],[8,9],[10,9],[8,10]):
   m=ResourceMachine(rom,seed=13,flags=0xA000001F)
   for at in range(0x03002A78,0x03002C08):m.put(at,0,1)
   row=0x02001000
   for i,value in enumerate((p1,values['address'],p2)):m.put(row+4*i,value)
   for at in (0x030012CA,0x030012B6,0x030012CC,0x030012CE):m.put(at,0,2)
   for n,event in enumerate(events):
    pres=0x03002A78+n*0x50
    m.r[0]=pres;m.r[1]=row;m.r[2]=0;m.r[3]=0;m.r[14]=0x12345678
    m.run_checked(sym['m23_present_construct'],positions)
    m.put(pres,112,2);m.put(pres+2,32+n*18,2)
    m.r[0]=pres;m.r[1]=event;m.r[14]=0x12345678;m.run_checked(sym['m23_present_event'],positions)
    m.r[0]=pres;m.r[14]=0x12345678;m.run_checked(sym['m23_present_update_draw'],positions)
   count=sum(values['parts'][e]for e in events)
   assert m.get(0x030012CA,2)==count and count<=128,(language,events,m.get(0x030012CA,2),count)
   results.append(dict(language=language,events=events,actual_parts=count,actual_staged_tile_bytes=count*32))
 result=dict(status='TITLE_ELEVEN_EVENTS_NATIVE_RENDERER_AUTHOR_PASS',checker_sha256=sha(Path(__file__).read_bytes()),native_sha256=NATIVE,source_sha256=SOURCE,assets_sha256=sha(data),manifest_sha256=sha((a.assets_dir/'manifest.json').read_bytes()),service_sha256=sha(Path(services.__file__).read_bytes()),linker=proof,cases=results,limits=['Task/controller transitions and physical OAM upload not executed','Atan and unused full-view entry are unreachable explicit fixture symbols','No installed ROM or game execution'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()

"""Reconstruct the frozen Iraira outer display route from saved physical owners."""
import argparse,hashlib,json,struct
from pathlib import Path
from verify_shoot_static_companion_clear import Machine
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
class GradientMachine(Machine):
 def run(self,start,stops,max_steps=16000):
  for _ in range(8):
   try:return super().run(start,stops,max_steps)
   except ValueError as e:
    if str(e)!='immediate halfword transfer':raise
    pc=self.r[15]-8;assert pc==0x080C9314 and self.get(pc)==0xE19810B1
    address=self.r[8]+self.r[1];assert address%2==0
    self.r[1]=self.get(address,2);start=pc+4
  raise ValueError('bounded gradient continuation')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('capture','source','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();meta=json.loads((a.capture/'launch.json').read_bytes());assert meta['completed'] and meta['loaded_rom_exact']
 names=('loaded-rom.bin','13-campaign-active-04-iwram.bin','13-campaign-active-04-palette.bin','13-campaign-active-04-vram.bin')
 data=[(a.capture/n).read_bytes() for n in names];assert all(sha(b)==meta['files'][n] for n,b in zip(names,data))
 b,iw,pal,vr=data;assert sha(b)=='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
 s=a.source.read_bytes();assert sha(s)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
 assert (iw[0x231E],iw[0x232E],iw[0x231C])==(10,4,11)
 assert u(b,0xD0BD0)==0xEB12CF8A and u(b,0xD0C38+3*4)==0x080D0ED0
 m=GradientMachine(b,seed=1,flags=0xA000001F)
 for k,v in enumerate(iw):m.put(0x03000000+k,v,1)
 m.put(0x05000000,0,2)
 m.run(0x080D0BC0,{0x080D0ED0})
 assert m.r[1]==3 and m.r[8]==0x080D0C38 and m.r[9]==0x080D0ED0 and m.r[14]==0x080D0BE8
 m.run(0x080D0ED0,{0x080D0BE8})
 assert m.get(0x05000000,2)==0x033D==h(pal,0)
 assert m.get(0x0300466A,2)==0 and h(iw,0x2578)==0
 # The common post-stage upload, independently of this incorrect display handler.
 assert [u(b,x) for x in (0x3EEE0,0x3EEE4,0x3EEE8,0x3EEEC)]==[0xE59F52A4,0xE59F42A4,0xE3A02088,0xEBFF4881]
 assert u(b,0x3F18C)==0x06007DE0 and u(b,0x3F190)==0x0801FD50
 assert vr[0x7DE0:0x8000]==b[0x1FD50:0x1FF70]
 ins={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(s[0x77CF86:0x77CFC2],0x77CF86)}
 assert ins[0x77CF94]==('call','word ptr cs:[bx + 0x3c]')
 for at,op in ((0x77CF99,'al, 0xc2'),(0x77CF9D,'ax, 0x3fd6'),(0x77CFA0,'ds, ax'),(0x77CFB4,'ax, 0xbde'),(0x77CFB7,'es, ax'),(0x77CFB9,'si, 0x20'),(0x77CFBC,'cx, 0x110')):assert ins[at]==('mov',op)
 assert ins[0x77CFC0][0]=='rep movsw' and 0x420000+0x3FD60+0x20-0x30000==0x42FD80
 font=bytearray()
 for tile in range(17):
  for y in range(8):
   pixels=[sum(((s[0x42FD80+tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4)) for x in range(8)]
   font.extend(pixels[x]|pixels[x+1]<<4 for x in range(0,8,2))
 assert font==b[0x1FD50:0x1FF70]==vr[0x7DE0:0x8000]
 source_maps=struct.unpack_from('<4032H',s,0x4CA1C0)
 collisions=[dict(cell=i,tile=v&511) for i,v in enumerate(source_maps) if (v&511)>=495]
 initial=[]
 for off,step,n,dst,ph in ((0,32,11,0x42,4),(128,16,6,0x62,4),(192,16,7,0x82,7),(304,16,7,0xA2,6),(400,16,7,0xC2,7)):
  matches=[i for i in range(ph) if pal[dst:dst+n*2]==b[0x584200+off+step*i:0x584200+off+step*i+n*2]]
  initial.append(dict(destination=dst,matching_animator_phases=matches))
 result=dict(status='IRAIRA_OUTER_ROUTE_RECONSTRUCTION_PASS',checker_sha256=sha(Path(__file__).read_bytes()),rom_sha256=sha(b),capture_palette0=h(pal,0),captured_backdrop_RAM=h(iw,0x2654),
  reconstructed_index=3,reconstructed_target='080D0ED0',reconstructed_palette0=m.get(0x05000000,2),palette_phase_matches=initial,
  common_font_source='0801FD50',common_font_destination='06007DE0',font_bytes=544,original_WSC_font='42FD80',source_font_pixel_parity=True,source_map_tail_references=collisions,
  limitations=['Execution is reconstructed from captured memory, not a direct PC trace; new readonly witness independently measures actual routing.',
   '17 common font slots are original source pixels, distinct from the first495 stage-atlas slots; exact scrolling/raster ordering remains outside this report.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()

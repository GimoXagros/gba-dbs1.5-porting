"""Installed header component author check using the actual merged native caller."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_character_select_name_overlay import fixture,memory
import character_select_name_overlay as overlay
BASE=0x08000000
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('before','after','owner','assets','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists()
 before=a.before.read_bytes();after=a.after.read_bytes();raw=a.owner.read_bytes();owner=json.loads(raw);meta=json.loads((a.assets/'manifest.json').read_bytes())
 assert sha(before)==owner['input_sha256']=='9F0DA0316B76CA6D2634DF7F89CCE1FFD1F1B0AC2CB37B2EDCDC0753466B228A'and sha(after)==owner['output_sha256']
 assert sha((a.assets/'manifest.json').read_bytes())==owner['assets_manifest_sha256']=='9F479B7C13FA4BCECDBD24E3170628377369C31CC5FD4563D311B9B49A1C3C11'
 headers=[(a.assets/r['file']).read_bytes()for r in meta['entries']]
 inverse=bytearray(after)
 for r in owner['writes']:
  lo=r['offset'];hi=lo+r['size'];assert sha(before[lo:hi])==r['before_sha256']and sha(after[lo:hi])==r['after_sha256']
  inverse[lo:hi]=before[lo:hi]
 assert inverse==before and len(owner['writes'])==63
 code,end=owner['code_span'];table,tail=owner['table_span'];assert after[code:end]==overlay.assemble(BASE+code,BASE+table)
 assert after[overlay.HOOK-BASE:overlay.HOOK-BASE+4]==overlay.hook(BASE+code)
 pointers=struct.unpack_from('<60I',after,table);assert list(pointers)==owner['header_pointers']
 for i,ptr in enumerate(pointers):assert after[ptr-BASE:ptr-BASE+768]==headers[i]
 count=0
 for identity in range(15):
  pal,atlas=struct.unpack_from('<II',before,0x4A5BC0+identity*8)
  for flags in range(16):
   old=fixture(before,identity,0xA0,flags);ret=old.r[14];sp=old.r[13];old.run(0x084A5C40,{ret})
   for lang in range(4):
    m=fixture(after,identity,0xA0+lang,flags);m.run(0x084A5C40,{ret})
    assert m.r[:15]==old.r[:15]and m.cpsr==old.cpsr
    assert m.get(0x0300472E,2)==identity+1
    assert memory(m,0x06005780,6144)==headers[lang*15+identity]+before[atlas-BASE+768:atlas-BASE+6144]
    assert memory(m,0x05000020,32)==before[pal-BASE:pal-BASE+32]
    assert m.dma==old.dma+[(pointers[lang*15+identity],0x06005780,192)]
    assert all(sp-64<=at<sp or at==0x0300472E or 0x040000D4<=at<0x040000E0 for at,v,size in m.writes)
    count+=1
 result=dict(status='PASS',before_sha256=sha(before),after_sha256=sha(after),owner_sha256=sha(raw),asset_manifest_sha256=sha((a.assets/'manifest.json').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),actual_installed_loader_cases=count,all60_pointer_contents_verified=True,whole_image_inverse=True,returned_R0_R14_NZCV_parity=True,body_palette_cache_tail_exact=True,new_OAM=0,new_global_RAM_bytes=0,limits=['Author installed-code fixture only; independent reviewer gate and live observation separate.','Real ARM loader/getter/helper/DMA setup/continuation execute; MMIO DMA transfers modeled.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS',sha(a.report.read_bytes()))
if __name__=='__main__':main()

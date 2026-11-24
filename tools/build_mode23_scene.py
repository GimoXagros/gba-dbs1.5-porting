"""Build and register the complete owned mode23 scene; normal menu remains separate.

Requires the reviewed split-audio bundle. All fresh code/data writes occupy
strict-reference-free FF intervals in the same16MiB predecessor. No emulator,
main builder, user save or Git operation is performed.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
import mode23_participant_controller as participant
import mode23_participant_setup as setup
import mode23_item_ai as item
import mode23_scene_lifecycle as life
import mode23_native_services as native_services
import mode23_scene_resources as resources
import mode23_rule_controller as rule
import mode23_collision_rules as collision
import mode23_scene_graphics as graphics
import mode23_palette_phases as palette
import mode23_sound_adapter as sound
import mode23_completion_save as completion
import mode23_dispatch_tables as dispatch
from mode23_asset_scatter import Allocator,place_resources,place_graphics,place_bundle,BASE,CODE_RESERVE
from mode23_linker import compose
ROOT=Path(__file__).resolve().parents[1]
INPUT='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
CODE=0xDB0420;CODE_LIMIT=0xDB4400
MODULES=('mode23_participant_controller','mode23_participant_setup','mode23_item_ai','mode23_scene_lifecycle','mode23_native_services','mode23_scene_resources','mode23_rule_controller','mode23_collision_rules','mode23_scene_graphics','mode23_palette_phases','mode23_sound_adapter','mode23_completion_save','mode23_asset_scatter','mode23_linker','mode23_dispatch_tables')
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def bodies(source,native,resource_meta,graphics_meta,source_audio_report,audio_contract):
 entries=sorted(set(life.ENTRIES)|set(participant.ENTRIES)|set(rule.ENTRIES))
 values=[rule.assembly(source),collision.assembly(source),participant.assembly(source),item.assembly(source),setup.assembly(source),life.assembly(source),native_services.assembly(native),native_services.wrappers(entries),resources.assembly(resource_meta['tables']),graphics.assembly(graphics_meta['tables']),palette.assembly(source),sound.assembly(source_audio_report,audio_contract),completion.assembly(source,native)]
 return values,entries

def build(native,source,audio,audio_meta,source_audio_report,audio_contract):
 assert sha(native)==INPUT and sha(source)==SOURCE
 assert len(native)==0x1000000
 assert sha(audio_contract)==sound.AUDIO and sha(source_audio_report)==sound.REPORT
 contract=json.loads(audio_contract)
 # The split format must retain its source bundle identity and native players.
 assert audio_meta['base_bundle_sha256']==contract['bundle_sha256']
 assert sha(audio)=='D8F83AA300234C64A6B3963AF2ED4BA0CE32BB52D88CC2F62EC2AABF53FE6CA7'
 assert audio_meta['bundle_sha256']==sha(audio)
 assert audio_meta['table_entries']==122 and audio_meta['existing_entries']==112
 assert audio[:112*8]==native[0xD33000:0xD33000+112*8],'original112 MP2K entries unchanged'
 allocator=Allocator(native)
 assert native[CODE_RESERVE[0]:CODE_RESERVE[1]]==b'\xff'*(CODE_RESERVE[1]-CODE_RESERVE[0])
 assert not any(CODE_RESERVE[0]<=x<CODE_RESERVE[1] for x in allocator.targets),'whole code/root reservation strictzero'
 resource_writes,rm=place_resources(source,allocator)
 graphics_writes,gm=place_graphics(source,allocator)
 audio_objects=[dict(label='song-table',offset=audio_meta['table_offset'],size=audio_meta['table_entries']*8)]+audio_meta['asset_objects']
 audio_writes,audio_resolve,audio_places=place_bundle(audio,audio_objects,audio_meta['local_u32_fixups'],allocator,'audio-')
 values,entries=bodies(source,native,rm,gm,source_audio_report,audio_contract)
 text='\n'.join(values);labels=set(re.findall(r'^(\w+):',text,re.M));refs=set(re.findall(r'\bm23_\w+',text))
 assert refs<=labels,('unresolved scene import',refs-labels)
 exports=['m23_scene_create','m23_src_A0FD','m23_completion_save']+[f'm23_cb_{x:04X}' for x in entries]
 code,symbols,link=compose(values,BASE+CODE,exports)
 assert CODE+len(code)<=CODE_LIMIT,'scene code must leave rootentry table reservation'
 writes=[(CODE,code,'complete mode23 scene library')]+resource_writes+graphics_writes+audio_writes
 table_blob,dispatch_changes=dispatch.patches(source,native,BASE+0xDB4400,symbols['m23_scene_create'],BASE+0xDB4610)
 selector,selector_symbols,selector_link=compose([dispatch.selector_assembly()],BASE+0xDB4610,['m23_select_transition'])
 assert len(table_blob)==528 and len(selector)==16
 writes.extend([(0xDB4400,table_blob,'registered mode23 callback and transition tables'),(0xDB4610,selector,'source charselect configbit8 selector')])
 writes.extend((at,data,'native mode/transition/charselect reader') for at,data in sorted(dispatch_changes.items()))
 patches=completion.sanitizer_patches(native)
 writes.extend((at,data,'shared source completion sanitizer') for at,data in sorted(patches.items()))
 table=BASE+audio_resolve(audio_meta['table_offset'])
 for address in contract['unchanged_loader_literals']:
  at=address-BASE;assert u(native,at)==0x08D33000
  writes.append((at,struct.pack('<I',table),'native MP2K table reference'))
 ordered=sorted((at,at+len(data),label) for at,data,label in writes)
 assert all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])),'no overlap between scene assets/code/hooks'
 after=bytearray(native);declared=[]
 for at,data,label in writes:
  before=native[at:at+len(data)]
  blank=at>=0xD90000
  if blank:
   assert before==b'\xff'*len(data)
   assert not any(at<=x<at+len(data) for x in allocator.targets),'no conservative inbound exceptions'
  after[at:at+len(data)]=data
  declared.append(dict(offset=at,size=len(data),label=label,before_sha256=sha(before),after_sha256=sha(data),before_fill=255 if blank else None,before_hex=None if blank else before.hex(),strict_inbound_count=0 if blank else None))
 inverse=bytearray(after)
 for row in declared:
  at,n=row['offset'],row['size'];inverse[at:at+n]=bytes([255])*n if row['before_fill']==255 else bytes.fromhex(row['before_hex'])
 assert inverse==native,'complete whole-image inverse'
 for name,row in audio_places.items():assert row>=0xD90000
 result=dict(status='MODE23_SCENE_REGISTERED_NORMAL_MENU_NOT_EXPOSED',input_sha256=INPUT,source_sha256=SOURCE,output_sha256=sha(after),builder_sha256=sha(Path(__file__).read_bytes()),module_sha256={name:sha((ROOT/'tools'/(name+'.py')).read_bytes()) for name in MODULES},code=dict(start=CODE,end=CODE+len(code),bytes=len(code),reserved_end=CODE_LIMIT,strict_inbound_count=0),root_entry_reservation=[CODE_LIMIT,CODE_RESERVE[1]],dispatch=dict(table_address=BASE+0xDB4400,selector=selector_symbols,patch_count=len(dispatch_changes),independent_contract='EDB41729',menu_producer_missing=True),entries=symbols,initializer=0x080159B0,callback_offsets=entries,callback_count=len(entries),link=link,resources=rm,graphics=gm,audio=dict(input_bundle_sha256=sha(audio),source_contract_sha256=sha(audio_contract),table=table,placements=audio_places,objects=audio_objects,fixups=audio_meta['local_u32_fixups']),allocations=allocator.allocations,writes=declared,declared_bytes=sum(x['size'] for x in declared),changed_bytes=sum(x!=y for x,y in zip(native,after)),new_global_RAM_bytes=0,task_payload_private_bytes=0x100,max_owned_tasks=9,whole_image_inverse=True,actual_runtime_verified=False,scene_registered=True,menu_exposed=False,limits=['Mode23 registered with complete scene; source normal menu and persisted eligibility still require separate integration','No emulator or gameplay validation','Shared source palette mirror requires exclusive retired predecessor/task lifetime','Completion uses reviewed nativeC0 serializer; source extended stat tail remains a separate compatibility scope','Unused rootentry reservation remains FF; all conservative inbound hits outside actual writes remain untouched'])
 return bytes(after),result,allocator.hits

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('input','source','audio_bundle','audio_manifest','source_audio_report','audio_contract','output_dir'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 assert sha(a.audio_manifest.read_bytes())=='C1F83D6EE13179A856539FEBF2FAB15A9B252EE9FCE106AD8947819FDD32EBD1'
 after,manifest,hits=build(a.input.read_bytes(),a.source.read_bytes(),a.audio_bundle.read_bytes(),json.loads(a.audio_manifest.read_bytes()),a.source_audio_report.read_bytes(),a.audio_contract.read_bytes())
 a.output_dir.mkdir(parents=True)
 (a.output_dir/'component.gba').write_bytes(after)
 census=json.dumps(dict(input_sha256=INPUT,range=[0xD90000,0x1000000],conservative_hits=hits,actual_allocation_hits=0),indent=2)+'\n'
 (a.output_dir/'allocation-census.json').write_text(census,encoding='utf-8',newline='\n');manifest['allocation_census_sha256']=sha(census.encode())
 path=a.output_dir/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(manifest['status'],manifest['output_sha256'],sha(path.read_bytes()))
if __name__=='__main__':main()

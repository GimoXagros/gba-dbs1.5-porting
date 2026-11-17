"""Check the actual corrected event16 predecessor; campaign QA is a separate gate."""
import argparse
import json
import struct
from pathlib import Path
from verify_gba_shoot_entry_capture import fields,sha

ROOT=Path(__file__).resolve().parents[1]
ROM='75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
DELTA='F34ADBF62A1EDEEB1D3E7D0DB421A6BA6F9099463BB182A327CAFB47AFC0A6F5'
BASELINE='1B3C05A0A1AA43C0242DD1F5772D21305267579EB57C52DDADAB263DB07AE7AC'
PC={'type8-air-selector':0x0836EC90,'damage-table-entry':0x0836F3B8,'damage-record-selected':0x0836F3CC,
    'metadata-entry':0x083555D0,'setter-entry':0x08012874,'event-store':0x08012884}

def need(ok,label):
 if not ok:raise ValueError(label)
def word(b,a):return struct.unpack_from('<I',b,a)[0]

def chain_check(rows,rom):
 need(6<=len(rows)<=32,'bounded first causal chain exists')
 need([int(r['seq'])for r in rows]==list(range(int(rows[0]['seq']),int(rows[0]['seq'])+len(rows))),'contiguous captured causal chain')
 frames=[int(r['core'])for r in rows]
 need(frames==sorted(frames) and frames[-1]<=frames[0]+1,'same or next core causal boundary')
 need(rows[0]['kind']=='type8-air-selector' and rows[-1]['kind']=='event-store','selector through store endpoints')
 chosen=[];at=0
 for kind in PC:
  indexes=[i for i in range(at,len(rows))if rows[i]['kind']==kind]
  need(len(indexes)==1,'one ordered '+kind);at=indexes[0]+1;chosen.append(rows[at-1])
 selector,table,record,metadata,setter,store=chosen
 need(all(r['actor']=='02011828' and r['P1']=='0861CF0C' and int(r['pc'],16)==PC[r['kind']]+4 for r in chosen),'actual owner/resource/instruction sites')
 need(selector['conditional_NE']=='true' and int(selector['cpsr'],16)&0x40000000==0,'conditional selector really executes')
 need(int(selector['flags6'],16)&1 and int(selector['flags8'],16)&0x4000,'air and evolved owner flags')
 scratch=[int(v,16)for v in selector['scratch'].split(',')]
 need(scratch[0]&0xFFFF==8,'actual type8 collision predecessor')
 subtype=int(table['subtype']);need(0<=subtype<4 and (scratch[1]>>16)&255==subtype,'actual scratch subtype')
 need(selector['literal']==table['table']=='08D3FE90' and table['id']=='13','correct relocated table/identity')
 need(word(rom,0x36F7B8)==0x08D3FE90 and word(rom,0xD3FE90+13*4)==0x0836C2AC,'actual ROM indexed row')
 pointer=0x0836C2AC+subtype*32
 need(table['indexed']=='0836C2AC' and int(record['r1'],16)==int(metadata['r1'],16)==pointer,'source-prescribed subtype record')
 expected=','.join(f'{word(rom,pointer-0x08000000+i*4):08X}'for i in range(8))
 need(record['record']==metadata['record']==expected,'actual metadata bytes equal source-backed ROM')
 need(metadata['r4']=='02011828' and metadata['r5']=='020118D4' and metadata['lr']=='0836F3E0','metadata caller and actor swap')
 need(setter['selected']=='00000016' and setter['lr']=='08355620' and setter['cb']=='0836AAC0','correct event16 caller/callback')
 need(setter['stack'].split(',')[0]=='00000016' and setter['stack'].split(',')[2]=='020118D4','event setter arguments')
 need(store['r3']=='00000016' and store['selected']=='00000016' and store['saved_lr']=='08355620' and store['r5']=='020118D4','actual event store operand and owner')
 p1table=word(rom,0x61CF0C);need(store['table']==f'{p1table:08X}','actual P1 table')
 data=struct.unpack_from('<4I',rom,p1table-0x08000000+0x16*16)
 need(store['row']==','.join(f'{v:08X}'for v in data),'actual selected P1 row')
 need(0<data[0]<256 and 0x08000000<=data[1]<=0x09000000-data[0]*16,'bounded first command read')
 need(data[1]!=0x1000C and data[0]!=0xFF05,'old BIOS/openbus row absent')
 return dict(core=frames[0],last_core=frames[-1],subtype=subtype,record=f'{pointer:08X}',event='16',command_count=data[0],command_base=f'{data[1]:08X}',rows=chosen)

def audit(run):
 launch_bytes=(run/'launch.json').read_bytes();launch=json.loads(launch_bytes)
 need(launch.get('completed') is True and 'files'in launch,'root-finalized completed capture required')
 need(launch['launcher_sha256']=='18DDDFCFE48DD615B6F64A2B46755D270831428FE951B72A2859CCB747366864','reviewed host')
 need(launch['reviewed_pins_sha256']=='0126D44047D3AD655DA84C34E3DF75CBC33360CAD5B3450CE335B57AAD0DCD2B','reviewed pins')
 need(launch['rom_sha256']==ROM and launch['loaded_rom_exact'] and launch['scripts_unchanged'],'actual corrected ROM and scripts')
 need(not any(launch[k]for k in ('visible','physical_background_input','supplied_save_used','host_stop_requested','host_deadline_reached')),'original hidden fresh bounded controls')
 paths=['type8-event-provenance.txt','loaded-rom.bin','shoot-entry-trace.txt','campaign-complete-trace.txt','campaign-complete-done.txt']
 blobs={p:(run/p).read_bytes()for p in paths}
 need(all(sha(b)==launch['files'][p]for p,b in blobs.items()),'relevant actual artifacts match finalized inventory')
 need(sha(blobs['loaded-rom.bin'])==ROM,'actual loaded ROM hash')
 lines=blobs['type8-event-provenance.txt'].decode().splitlines()
 summary=fields(lines[0]);need(summary['guest_writes']=='none' and summary['input']=='frozen-parent','observer declaration')
 rows=[fields(x[6:])for x in lines if x.startswith('chain seq=')]
 chain_header=[fields(x)for x in lines if x.startswith('first-chain ')]
 need(len(chain_header)==1 and int(chain_header[0]['count'])==len(rows),'chain header agrees')
 witness=chain_check(rows,blobs['loaded-rom.bin'])if rows else None
 first=[fields(x[6:])for x in lines if x.startswith('first seq=')]
 tail=[fields(x)for x in lines if x.startswith('seq=')]
 need(len(first)<=256 and all(8667<=int(x['core'])<=8673 for x in first),'bounded fixed comparison window')
 total=int(summary['serial'])
 need([int(x['seq'])for x in tail]==list(range(max(1,total-255),total+1)),'final ring extent')
 counters={x.split('=',1)[0][6:]:int(x.split('=',1)[1])for x in lines if x.startswith('count ')}
 need(sum(counters.values())==total,'journal counter total')
 finalcore=int(summary['core'])
 if witness:need(finalcore>witness['last_core'],'continued beyond corrected witness')
 trace=blobs['shoot-entry-trace.txt'].decode();campaign=blobs['campaign-complete-trace.txt'].decode()
 result=blobs['campaign-complete-done.txt'].decode().strip()
 need(result==launch['outcome'],'actual reported outcome')
 invalid_guard='failure:first-invalid-producer'in trace+campaign or 'first-invalid-producer'in ' '.join(launch['files'])
 producer_rows=[fields(x)for x in trace.splitlines()if x.startswith('seq=')and ' kind=producer 'in x]
 invalid_rows=[x for x in producer_rows if not 0<=int(x['type'],16)<=0x1B]
 old=(ROOT/'build/bizhawk-type8-provenance-v80-20261117-a/type8-event-provenance.txt').read_bytes()
 need(sha(old)==BASELINE,'frozen old observed cause')
 need(sha((ROOT/'build/type8-corrected-delta-independent-final-20261117/report.json').read_bytes())==DELTA,'frozen delta-only preflight')
 # Test the witness validator against each causal fact, without rerunning a game.
 rejected=0
 mutations=[('type8-air-selector','conditional_NE','false'),('damage-table-entry','table','0836BED4'),
                      ('damage-record-selected','r1','0836C32C'),('metadata-entry','lr','0836F3E4'),
                      ('setter-entry','selected','00000036'),('event-store','row','000AFF05,0001000C,00000000,00000000')]
 for kind,key,bad in mutations if witness else []:
  mutant=[dict(x)for x in rows];next(x for x in mutant if x['kind']==kind)[key]=bad
  try:chain_check(mutant,blobs['loaded-rom.bin'])
  except ValueError:rejected+=1
 need(rejected==(6 if witness else 0),'corrupted causal facts rejected when witness exists')
 campaign_summary=next(fields(x)for x in campaign.splitlines()if x.startswith('summary '))
 return dict(status='TYPE8_CORRECTED_CAUSAL_CAPTURE_PASS'if witness else 'TYPE8_CORRECTED_WITNESS_NOT_OBSERVED',run=run.relative_to(ROOT).as_posix(),launch_sha256=sha(launch_bytes),
             artifact_sha256={p:sha(b)for p,b in blobs.items()},witness=witness,old_event='36',old_event_core=8671,
             old_invalid_producer_core=8672,corrected_event='16'if witness else None,witnessed_source_path_corrected=bool(witness),
             observer_counts=counters,expected_corrected_event='16',
             bad_producer_guard_absent=not invalid_guard,retained_invalid_producer_rows=invalid_rows,
             retained_valid_producer_rows=len(producer_rows)-len(invalid_rows),final_core=finalcore,
             last_retained_collision_producer=producer_rows[-1]if producer_rows else None,
             last_retained_type8_owner_core=max(int(x['core'])for x in tail),
             passed_old_absolute_failure_core=finalcore>8672,causal_mutations_rejected=rejected,
             fixed_window_rows=len(first),reported_campaign_outcome=result,reported_highest_progress=int(campaign_summary['highest']),
             whole_campaign_independently_verified_by_this_checker=False,
             limits=['A missing causal chain is not a runtime repair pass; any later failure remains separately reported.',
                     'The whole campaign, write ledger, captures and visuals have a separate QA owner.',
                     'Different core timing is expected because earlier valid-but-wrong reaction rows are also repaired.'])

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);p.add_argument('--root-completed',action='store_true');p.add_argument('--report',type=Path,required=True)
 a=p.parse_args();need(a.root_completed and not a.report.exists(),'explicit root completion and fresh report')
 result=audit(a.run.resolve());result['checker_sha256']=sha(Path(__file__).read_bytes())
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(result['status'],sha(a.report.read_bytes()))

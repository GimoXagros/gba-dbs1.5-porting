"""Scoped repaired initializer/action-copy proof, separate from campaign outcome."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROM='DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,why):
 if not ok:raise ValueError(why)
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('capture','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 launch=json.loads((a.capture/'launch.json').read_bytes())
 need(launch['completed'] and launch['loaded_rom_exact'] and launch['scripts_unchanged'],'finalized exact capture')
 need(not launch['host_stop_requested'] and not launch['host_deadline_reached'],'naturally finalized bounded run')
 need(launch['rom_sha256']==ROM and launch['launcher_sha256']=='F1397304FFEF2CEAAACC4DECEE774CE442A5317FAF101BA0A56F0B70C110706D','reviewed corrected host')
 need(launch['pins']['tools/bizhawk_probe_ai_corrected_campaign.lua']=='45490F604352C49539A73E54A9F7AE9FF1A2DDDDA8508A1C4BA28372B45085A4','reviewed corrected observer')
 names=('loaded-rom.bin','ai-producer-provenance.txt','campaign-complete-done.txt','campaign-complete-trace.txt','type8-event-provenance.txt')
 blobs={n:(a.capture/n).read_bytes() for n in names}
 for n,b in blobs.items():need(sha(b)==launch['files'][n],'final file pin '+n)
 rom=blobs['loaded-rom.bin'];need(sha(rom)==ROM,'actual loaded DEEE')
 outcome=blobs['campaign-complete-done.txt'].decode().strip();need(outcome==launch['outcome'],'honest terminal outcome')
 journal=blobs['ai-producer-provenance.txt'].decode()
 first=[dict(re.findall(r'(\w+)=([^\s]+)',line)) for line in journal.splitlines() if line.startswith('first seq=')]
 kinds={x['kind']:x for x in first};need(len(kinds)==len(first),'one retained first fact per kind')
 need(all((x['stage'],x['cpu'],x['progress'])==('9','14','2') for x in first),'typed Waterfall CPU14 scope')
 required=('raw-id','row-index','first-read','first-copy','parameter-copies-complete','action-first-copy','selector-load','target')
 missing=[k for k in required if k not in kinds];witness=not missing;details={};parameter_mismatches=[]
 if witness:
  rows=[kinds[k] for k in required]
  need(rows[0]['raw_id']=='14' and rows[1]['effective_id']=='9' and rows[1]['stride']=='17','source normalized identity')
  need(all(rows[i]['core']==rows[0]['core'] for i in range(5)),'same actual initializer call')
  need([int(x['seq']) for x in rows[:5]]==sorted(int(x['seq']) for x in rows[:5]),'actual initializer order')
  src=0xD88800+9*17;params=rom[src:src+17]
  need(rows[2]['row_base']=='08D88800' and int(rows[2]['offset'])==9*17 and int(rows[2]['src'],16)==0x08000000+src,'actual parameter reader source row9')
  need(bytes.fromhex(rows[2]['row17'])==params,'observed complete source parameter row')
  need(rows[3]['dst']=='03004D8A','actual first parameter destination')
  copied=bytes.fromhex(rows[4]['params_03004D88'])
  projection=((0,2,2),(2,4,2),(4,6,1),(5,7,1),(6,28,1),(7,29,1),(8,30,1),(9,31,1),(10,32,1),(11,33,1),(12,34,1),(13,8,1),(14,9,1),(15,36,1),(16,37,1))
  for x,y,n in projection:
   if copied[y:y+n]!=params[x:x+n]:parameter_mismatches.append(dict(source_offset=x,owner_offset=y,source_value=int.from_bytes(params[x:x+n],'little'),actual_value=int.from_bytes(copied[y:y+n],'little')))
  need(copied[35]==0 and h(copied,2)==int(rows[3]['value'],16),'actual first store agrees with complete buffer')
  if parameter_mismatches:
   aligned=h(rom,src&~1);rotated=((aligned>>8)|(aligned<<24))&0xFFFFFFFF
   need(parameter_mismatches==[dict(source_offset=0,owner_offset=2,source_value=0x2E4,actual_value=0xE4)] and int(rows[3]['r0'],16)==rotated==0x0F0000E4,'observed odd-address ARM halfword rotation')
  action=rows[5];ordinal=int(action['ordinal'],16);address=int(action['src'],16)
  need(0<=ordinal<264 and address==0x08D89800+ordinal*18,'actual bounded relocated action copy')
  expected=rom[address-0x08000000:address-0x08000000+18]
  need(bytes.fromhex(action['action18'])==expected and int(action['word'],16)==h(expected,0),'actual action copy source and first word')
  need(action['lr']=='080C69B8' and action['r5']=='03003D50' and int(action['r4'],16)==address+2,'native copier ABI and postincrement')
  need(int(action['bank'],16)==9*384,'normalized saved identity reaches actual behavior bank')
  need(int(action['seq'])>int(rows[4]['seq']),'action follows normalized initialization')
  load,target=rows[6:];index=int(target['index'],16)
  need(0<=index<12 and target['table']=='080C65F4' and int(target['slot'],16)==0x080C65F4+4*index,'valid native dispatch slot')
  need(int(target['target'],16)==u(rom,0xC65F4+4*index)==int(target['word'],16),'actual target equals retained native callback')
  need(load['index']==target['index'] and load['slot']==target['slot'] and load['core']==target['core'] and int(load['seq'])<int(target['seq']),'observed load precedes valid target')
  need(int(action['seq'])<int(load['seq']),'valid target follows first source action copy')
  details=dict(initializer_core=int(rows[0]['core']),action_core=int(action['core']),action_ordinal=ordinal,action_address=f'{address:08X}',
    behavior_bank=9*384,target_core=int(target['core']),target_index=index,target=target['target'],matching_parameter_fields=15-len(parameter_mismatches))
 # A later independent failure does not erase a witnessed repaired prefix.
 trace=blobs['campaign-complete-trace.txt'].decode()
 active=[dict(re.findall(r'(\w+)=([^\s]+)',line)) for line in trace.splitlines() if line.startswith('event=active-owner')]
 highest=max((int(x['progress']) for x in active),default=-1)
 type8=blobs['type8-event-provenance.txt'].decode();m=re.search(r'^first-chain count=(\d+)$',type8,re.M)
 status=('AI_CORRECTED_ACTION_PREFIX_PASS_WITH_PARAMETER_MISMATCH' if parameter_mismatches else 'AI_CORRECTED_NATIVE_PREFIX_PASS') if witness else 'AI_CORRECTED_NATIVE_WITNESS_NOT_OBSERVED'
 result=dict(status=status,
  checker_sha256=sha(Path(__file__).read_bytes()),loaded_rom_sha256=sha(rom),journal_sha256=sha(blobs['ai-producer-provenance.txt']),
  witness_observed=witness,complete_source_parameter_parity=witness and not parameter_mismatches,parameter_mismatches=parameter_mismatches,missing_first_facts=missing,details=details,campaign_outcome=outcome,highest_active_progress=highest,
  progressed_beyond_waterfall=highest>2,type8_chain_rows=int(m.group(1)) if m else None,
  limitations=['Actual normalized identity, relocated action copy and valid target observed; source parameter parity failed at odd-address first halfword.' if parameter_mismatches else 'This pass covers only the retained corrected AI prefix.' if witness else 'No complete corrected AI prefix was observed; no causal pass is claimed.',
   'Behavior bank is directly logged; individual behavior lookup address is not hooked.',
   'Campaign completion and visuals are separately audited; later failures are preserved in campaign_outcome.',
   'Type8 event16 remains a separate witness requirement; its count alone is not validation.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()

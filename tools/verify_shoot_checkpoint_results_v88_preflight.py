"""Read-only preflight of the stage 11 Results replay and its pinned launcher."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType
import zlib

from check_campaign_complete_probe import host, quote
from verify_gba_shoot_entry_capture_v2 import checkpoint_core, parse_checkpoint, prior
from verify_shoot_static_companion_clear import Machine, ROOT, need, sha


OLD = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
NEW = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
RESULT = 'bizhawk_probe_gba_shoot_checkpoint_results_v88.lua'
LEAD = 'bizhawk_probe_gba_shoot_checkpoint_lead_v87.lua'
AIM = 'bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua'
TAIL = 'bizhawk_probe_campaign_wholeplay_v86.lua'
OBSERVER = 'bizhawk_gba_shoot_entry_observer.lua'
FILES = {
    'build/run_shoot_checkpoint_lead_v87_20261117.py': '3F78FF140378F26E5CF6A715728E8EED17BB32143294554293FDBE1B7C7BA8EF',
    'build/run_shoot_checkpoint_results_v88_20261117.py': 'AB4E566847E278F48DD6557A611E39815D22E6D8BC816DCD2872B6ABF06A6274',
    'build/shoot-checkpoint-results-v88-pins-20261117.json': 'C6A560880475524EBC77F559901E5DA08D64280DECAFF6AE15F7371E56CD448F',
    'build/shoot-checkpoint-results-v88-qa-20261117/report.json': '1848B207FBE0A9BB9157093D0D4A148FA124D5F4573E6C2DFA8EADD136C7492B',
    'tools/' + RESULT: '2695C1A8EDDD6796E593A5E3DEE5273F195E58AB25218E8942C16DADA5196B7F',
    'tools/' + LEAD: '15B146DB9241A82B84E9FC118FC9BAD4077F42F9CBB50157504B2356A2786D55',
}
BASELINE = '4F4CD759EF4E0642EDD56158BD900A166C03B70A41A6EF7FCBD539D2D7648CCB'
SOURCE_CORE = 'BCA24A090D8AA084D25A4B6F7F31820DD8636054FD84898D201081D3C01793F8'
LEAD_CORE = 'E62AE99E1FD1A10B64D826ED433A89D855CEEB2104A0FAFF180B4A583FDB2EA4'
RESAVE_OFFSETS = [310, 325, 326, 327, 330, 342, 343, 384, 385, 392, 393, 394, 396, 397, 1336]
OWNER_HOOKS = {0x080BBC24: 0xE92D403F, 0x080BD8E8: 0xE8BD0020,
               0x080CA24C: 0xE92D403F, 0x080CBCC0: 0xE8BD0020}


def replace_once(raw, old, new):
    need(raw.count(old) == 1, 'one strict independent replacement ' + repr(old))
    return raw.replace(old, new, 1)


def host_check(files):
    old, new, pinned = tuple(files.values())[:3]
    substitutions = (
        (b'bizhawk-shoot-checkpoint-results-v88-20261117-[a-z]', b'bizhawk-shoot-checkpoint-lead-v87-20261117-[a-z]'),
        (b'shoot-checkpoint-results-v88-pins-20261117.json', b'shoot-checkpoint-lead-v87-pins-20261117.json'),
        ((RESULT).encode(), LEAD.encode()),
        (b'build/shoot-stage11-results-route-20261117-r2/component.gba',
         b'build/shoot-child-contact-20261117/component.gba'),
        (f"rom_sha = '{NEW}'".encode(), f"rom_sha = '{OLD}'".encode()),
        (f"assert sha(source_rom) == '{OLD}'".encode(), b'assert source_rom == rom_data'),
        (b'current-checkpoint-source-results-and-autonomous-interstitials', b'current-checkpoint-measured-lead-and-native-terminal'),
    )
    for index, (after, before) in enumerate(substitutions):
        if index == 2:
            need(new.count(after) == 2, 'same newly pinned and launched script')
            new = new.replace(after, before)
        else:
            new = replace_once(new, after, before)
    need(new == old, 'exact full launcher inverse')
    launch = files['build/run_shoot_checkpoint_results_v88_20261117.py']
    for value in (b'with PrivateDesktopProcess(exe, args, exe.parent) as process:',
                  b'time.monotonic() + 360', b'AcceptBackgroundInput=False',
                  b'AutoLoadLastSaveSlot=False', b'AutosaveSaveRAM=False', b'supplied_save_used=False',
                  b"struct.pack_into('<I', expected_core, 12, zlib.crc32(rom_data))"):
        need(launch.count(value) == 1, 'private/qualified launcher property ' + repr(value))
    pins = json.loads(pinned)
    lead_pins = json.loads((ROOT / 'build/shoot-checkpoint-lead-v87-pins-20261117.json').read_bytes())
    need(set(pins) - set(lead_pins) == {'tools/' + RESULT}
         and set(lead_pins) - set(pins) == {'tools/' + LEAD} and len(pins) == 6, 'six-scope pin ownership')
    for path, digest in pins.items():
        need(sha((ROOT / path).read_bytes()) == digest and lead_pins.get(path, digest) == digest, f'certified script {path}')
    return dict(exact_inverse_groups=len(substitutions), scope_pins=pins, runtime_bound_seconds=360,
                private_desktop=True, original_inputs_and_authorization_unchanged=True)


def lua_check(files, rom):
    aim = (ROOT / 'tools' / AIM).read_bytes().replace(b'\r\n', b'\n')
    tail = (ROOT / 'tools' / TAIL).read_bytes()
    observer = (ROOT / 'tools' / OBSERVER).read_bytes()
    lead, result = files['tools/' + LEAD], files['tools/' + RESULT]
    blocks = re.findall(rb'\[=\[(.*?)\]=\]', lead, re.S)
    need(len(blocks) == 2 and result.count(b'[=[' + blocks[1] + b']=]') == 1, 'exact measured-lead body from previous run')
    old_effective = replace_once(aim, *blocks)
    new_allow = b'mode~=7 and mode~=8 and mode~=12 and mode~=13 and mode~=11 and mode~=20 and mode~=3'
    effective = replace_once(old_effective, OLD.encode(), NEW.encode())
    effective = replace_once(effective, b'mode~=7 and mode~=8 and mode~=11 and mode~=20 and mode~=3', new_allow)
    insertion = re.search(rb'\[==\[\r?\n(.*?)\]==\]', result, re.S).group(1)
    slot = b' local start=assert(s:find("local function finish(outcome)",1,true))'
    need(insertion.endswith(slot) and insertion.count(b's=replaced(s,') == 2, 'two scoped nested-observer additions')
    effective = replace_once(effective, slot, insertion)
    author_report = json.loads(files['build/shoot-checkpoint-results-v88-qa-20261117/report.json'])
    need(sha(effective) == author_report['effective_source_sha256'], 'same reported full effective source')
    words = {int(a, 16): int(b, 16) for a, b in re.findall(
        rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})', tail)}
    words |= {0x085CD340: 0xE92D5FFF, 0x085CD740: 0xE92D5FFF}
    inserted_words = {int(a, 16): int(b, 16) for a, b in re.findall(
        rb'^ hook\(0x([0-9A-F]{8}),0x([0-9A-F]{8}),"mode1[23]-', insertion, re.M)}
    need(len(words) == 25 and inserted_words == OWNER_HOOKS, '25 existing and four exact new hook words')
    words |= inserted_words
    need(all(struct.unpack_from('<I', rom, pc - 0x08000000)[0] == word for pc, word in words.items()),
         'actual 29 hook opcodes on E212')
    need(b'if require_fact(mode()==12' in insertion and b'w(0x0201D29C)==0' in insertion
         and b'and seen["mode12-request"]' in insertion
         and b'and seen["mode13-request"]' in insertion, 'ordered scoped interstitial owner/request gates')
    need(b'joypad' not in insertion and b'memory.write' not in insertion
         and effective.count(b'memory.write') == aim.count(b'memory.write') == 1
         and tail.count(b'memory.write_u16_le') == observer.count(b'memory.write_u16_le') == 1
         and b's=without(s,"local function write_word(","local function producer(")' in effective,
         'wrapper preserves readonly observer and sole existing guarded stage 11 write')
    need(b"elseif (which==8 or which==11)" in tail and b' release()\n  local mode=' in effective,
         'outside of guarded modes every controller frame starts neutral')
    setup = (f'local lead={quote(lead)}\nlocal wrapped={quote(result)}\nlocal ref={quote(aim)}\n'
             f'local before={quote(old_effective)}\nlocal after={quote(effective)}\n')
    setup += r'''
local opened,compiled=0,0
local env=setmetatable({}, {__index=_G})
env.io={open=function(path,mode)
 assert(path=="W:/tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua" and mode=="rb")
 opened=opened+1
 return {read=function(_,arg)assert(arg=="*a");return ref end,close=function()return true end}
end}
local expected=before
env.load=function(code,name,mode,scope)
 assert(code==expected and mode=="t" and scope==env)
 assert(load(code,name,mode,scope))
 compiled=compiled+1
 return function()end
end
assert(load(lead,"@independent-lead","t",env))()
expected=after
assert(load(wrapped,"@independent-results","t",env))()
assert(opened==2 and compiled==2)
'''
    runner = host.lua_check
    FunctionType(runner.__code__, dict(runner.__globals__, CHECK=setup))('', '', '')
    return dict(runtime_Lua_expanded_exact=True, effective_sha256=sha(effective), checked_native_opcodes=len(words),
                input_lead_identical_to_15B146DB=True, scope_additions=list(inserted_words),
                readonly_observer_and_original_HP_guard=True)


def boundary_check(rom):
    cfg, timer = 0x03002310, 0x0201D29C
    need(struct.unpack_from('<I', rom, 0xBD908)[0] == timer - 12, 'actual mode 12 countdown owner')
    need(struct.unpack_from('<I', rom, 0xBD90C)[0] == cfg
         and struct.unpack_from('<I', rom, 0xCBCD4)[0] == cfg, 'both return request ownership')
    def create():
        m = Machine(rom)
        for address in (cfg + 4, cfg + 6, cfg + 8):
            m.put(address, 0x55, 2)
        return m
    m = create()
    m.put(timer, 2, 2)
    stops = {0x080BD8E8, 0x080BD900}
    need(m.run(0x080BD8A4, stops) == 0x080BD900 and m.get(timer, 2) == 1, 'mode 12 wait leaves request alone')
    need(tuple(m.get(cfg + i, 2) for i in (4, 6, 8)) == (0x55,) * 3, 'no premature request')
    m = create()
    m.put(timer, 1, 2)
    need(m.run(0x080BD8A4, stops) == 0x080BD8E8 and m.get(timer, 2) == 0,
         'mode 12 actual countdown reaches reviewed post-store site')
    need(tuple(m.get(cfg + i, 2) for i in (4, 6, 8)) == (1, 0, 0), 'mode 12 already stored exact request')
    m = create()
    m.run(0x080CBCA0, {0x080CBCC0})
    need(tuple(m.get(cfg + i, 2) for i in (4, 6, 8)) == (1, 0, 0), 'mode 13 native request already stored')
    paths = [12, 13, 11, 20, 3]
    for mode, selector, next_mode in zip([8] + paths[:-1], [3, 0, 0, 0, 0], paths, strict=True):
        need(rom[0x15CC8 + 5 * mode + selector] == next_mode, 'exact native transition table selection')
    return dict(checked_post_store_handlers=[0x080BD8E8, 0x080CBCC0], mode_chain=[8] + paths)


def checkpoint_check(old_rom, new_rom):
    baseline = ROOT / 'build/bizhawk-wholeplay-v87-20261117-a'
    launch = (baseline / 'launch.json').read_bytes()
    need(sha(launch) == BASELINE and (baseline / 'probe.gba').read_bytes() == old_rom, 'exact wholeplay source owner')
    data = json.loads(launch)
    tags = ('iwram', 'ewram', 'vram', 'palette', 'oam')
    names = ('healthy-activation.State', 'healthy-activation.txt') + tuple(f'41-healthy-activation-{n}.bin' for n in tags)
    staged = {name: (baseline / name).read_bytes() for name in names}
    need(all(sha(value) == data['files'][name] for name, value in staged.items()), 'all seven actual source artifact pins')
    info = prior.fields(staged[names[1]].decode().strip())
    enclosures = {tag: staged[name] for tag, name in zip(tags, names[2:], strict=True)}
    parsed = parse_checkpoint(staged[names[0]], info, enclosures, old_rom)
    need(parsed['frame'] == 89405 and info['stage7_consumed'] == 'true', 'same healthy frame')
    source_core, _ = checkpoint_core(staged[names[0]])
    old_resave, _ = checkpoint_core((ROOT / 'build/bizhawk-shoot-checkpoint-lead-v87-20261117-a/restored.State').read_bytes())
    need((sha(source_core), sha(old_resave)) == (SOURCE_CORE, LEAD_CORE), 'exact original and prior same-ROM restored cores')
    diffs = [i for i, (a, b) in enumerate(zip(source_core, old_resave, strict=True)) if a != b]
    need(diffs == RESAVE_OFFSETS, 'record all known same-ROM resave differences')
    qualified = bytearray(source_core)
    struct.pack_into('<I', qualified, 12, zlib.crc32(new_rom))
    prior_qualified = bytearray(old_resave)
    struct.pack_into('<I', prior_qualified, 12, zlib.crc32(new_rom))
    need([i for i, (a, b) in enumerate(zip(qualified, prior_qualified, strict=True)) if a != b] == diffs,
         'cross-ROM comparison alone changes only requested CRC, prior differences remain visible')
    return dict(source_core_sha256=sha(source_core), captured_regions=parsed['compared_regions'],
                known_original_to_same_rom_resave_differences=diffs,
                expected_source_with_candidate_crc_sha256=sha(qualified),
                prior_restored_with_candidate_crc_sha256=sha(prior_qualified),
                actual_candidate_restored_core_not_observed_in_preflight=True)


def main():
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('report', type=Path)
    args = arg_parser.parse_args()
    need(not args.report.exists(), 'new preflight report')
    files = {p: (ROOT / p).read_bytes() for p in FILES}
    need({p: sha(b) for p, b in files.items()} == FILES, 'exact reviewed inputs')
    old = (ROOT / 'build/shoot-child-contact-20261117/component.gba').read_bytes()
    new = (ROOT / 'build/shoot-stage11-results-route-20261117-r2/component.gba').read_bytes()
    need((sha(old), sha(new)) == (OLD, NEW) and len(old) == len(new) == 0x1000000,
         'exact old/current 16 MiB candidate pair')
    result = dict(status='SHOOT_RESULTS_V88_PREFLIGHT_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  active_rom_sha256=NEW, host=host_check(files), probe=lua_check(files, new),
                  observed_handler_contract=boundary_check(new), checkpoint=checkpoint_check(old, new),
                  emulator_launched=False, guest_writes_executed=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()


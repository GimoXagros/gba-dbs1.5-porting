"""Verify the corrected title's installed asset pointers and normal scene route."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import pack, unpack_from
from types import FunctionType

import verify_shoot_caller_resident as scanner
import verify_mode23_scene_component as scene
from verify_mode23_title_pixel_assets import LANGUAGES, SOURCE, exact, need, sha


ROOT = Path(__file__).resolve().parents[1]
BUS = 0x08000000
TITLE = '9F0DA0316B76CA6D2634DF7F89CCE1FFD1F1B0AC2CB37B2EDCDC0753466B228A'
MANIFEST = 'A54778FA9FCA9A689E6B632C477DBF457B50B5BAFD5CEB4A324B1AA463A87324'
ELIGIBLE = '36A126206237A5C6A0670105C8023B5237FFA055733EF7795AE2A3A42A5E3B8A'
PREVIEW_CHECK = 'A1829C48C3275569FD1116E9F2EB98B06912A33A07CF24FE3799EF22E4AEAFF4'
SCENE_CHECK = '30B5BE9E19253E3DFB8B5CF514006A9D1808DA99374AE5D60FBB6CD4210ADC4D'
PRES, CONFIG, CUR, POOL = (0x03002A78, 0x03002310, 0x0300133C, 0x02010000)


def u32(rom, off):
    return unpack_from('<I', rom, off)[0]


def absolute(rom, bus):
    return u32(rom, bus - BUS)


def branch(rom, at, condition=0xEA):
    word = absolute(rom, at)
    need(word >> 24 == condition, f'Exact typed branch at {at:08X}')
    field = word & 0xFFFFFF
    return at + 8 + 4 * (field - 2 * (field & 0x800000))


def composition(before, after, m, assets, asset_manifest, source):
    for module, digest in m['module_sha256'].items():
        exact(ROOT / 'tools' / (module + '.py'), digest)
    exact(ROOT / 'tools/build_mode23_title_scene_r2.py', m['builder_sha256'])
    need(len(before) == len(after) == 0x1000000 and m['new_global_RAM_bytes'] == 0
         and m['private_title_payload_bytes'] == 0x24 and not m['actual_runtime_verified'], 'Development scope and image extents')
    spans = sorted((r['offset'], r['offset'] + r['size'], r) for r in m['writes'])
    need(len(spans) == 10 and all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'Ten exact disjoint spans')
    code_lo, code_hi = m['code_span']
    moves = {int(old): installed for old, installed in m['object_placements'].items()}
    objects = {row['offset']: row for row in asset_manifest['objects'] if row['label'] != 'p2'}
    placements = {(moves[lo], moves[lo] + row['size']) for lo, row in objects.items()}
    need(len(moves) == 5 and set(moves) == set(objects)
         and placements | {(code_lo, code_hi)} == {(x['start'], x['end']) for x in m['allocations']}, 'Exact typed object allocation inventory')
    source_spans = ((0xD90000, 0x1000000),)
    sn = FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=source_spans), argdefs=scanner.inbound.__defaults__)
    targets = {value & 0x1FFFFFF for _, _, value in sn(before)}
    restored = bytearray(after)
    for lo, hi, row in spans:
        need(sha(before[lo:hi]) == row['before_sha256'] and sha(after[lo:hi]) == row['after_sha256'], 'Whole installed span bytes')
        if (lo, hi) in placements | {(code_lo, code_hi)}:
            need(lo >= 0xD90000 and before[lo:hi] == b'\xff' * (hi - lo)
                 and all(not lo <= t < hi for t in targets), 'Strict erased allocation with zero inbound addresses')
        restored[lo:hi] = before[lo:hi]
    need(bytes(restored) == before, 'No undeclared changes to the reviewed eligible scene')
    locations = {}
    for lo, row in objects.items():
        at = moves[lo]
        data = after[at:at + row['size']]
        locations[row['label']] = BUS + at
        refs = {}
        if row['label'].endswith('_p0'):
            table, desc = [u32(assets, lo + i) - asset_manifest['base_address'] for i in (0, 4)]
            refs = {x: u32(assets, x) - asset_manifest['base_address'] for x in
                    (lo, lo + 4, desc + 4, *(table + 8 * i + 4 for i in range(11)))}
        else:
            table = u32(assets, lo) - asset_manifest['base_address']
            refs = {x: u32(assets, x) - asset_manifest['base_address'] for x in
                    (lo, *(table + 16 * i + k for i in range(11) for k in (4, 8)))}
        original = bytearray(data)
        for origin, target in refs.items():
            need(lo <= target < lo + row['size'] and absolute(after, BUS + at + origin - lo) == BUS + at + target - lo,
                 'Every installed object-internal pointer lands in its own physical asset span')
            original[origin - lo:origin - lo + 4] = pack('<I', asset_manifest['base_address'] + target)
        need(bytes(original) == assets[lo:lo + row['size']], 'Complete relocated object inverse ' + row['label'])
    need(locations == m['asset_pointers'], 'All five physical asset base pointers')
    p2 = next(row['offset'] for row in asset_manifest['objects'] if row['label'] == 'p2')
    need(after[0x90878:0x908A0] == before[0x90878:0x908A0] == assets[p2:p2 + 40], 'Retained installed native palette')
    sym = m['symbols']
    hooks = [span[0] for span in spans if span[0] < 0xD90000]
    need(hooks == [0x90A18, 0x90BBC, 0x90C70, 0x90E34]
         and branch(after, 0x08090A18) == sym['m23_title_select_p0']
         and u32(after, 0x90BBC) == locations['p1'] and u32(after, 0x90C70) == sym['m23_title_init_callback']
         and u32(after, 0x90E34) == sym['m23_title_enter_root'], 'Exact four cold init and Start route hooks')
    need(all(unpack_from('<II', after, x['address'] - BUS) == (0xE51FF004, x['target'])
             for x in m['link']['native_veneers'].values()), 'Every linked absolute native call veneer')
    need(m['link']['native_veneers']['m23_link_native_08D8D200']['target'] == 0x08D8D200
         and before[0xD8D200:0xD8D2E8] == after[0xD8D200:0xD8D2E8], 'Actual pre-existing persisted eligibility read')
    constructors = absolute(after, 0x08015B74)
    transitions = absolute(after, 0x08015CC8) - BUS
    need(absolute(after, constructors + 22 * 12) == 0 and absolute(after, constructors + 23 * 12) != 0,
         'Distinct unavailable mode22 and implemented mode23')
    source_rows = [source[0x74FA30 + mode * 6:0x74FA30 + (mode + 1) * 6] for mode in (3, 4, 23)]
    need(tuple(after[transitions + mode * 6 + offset] for mode, offset in ((3, 0), (4, 5), (23, 0))) ==
         (source_rows[0][0], source_rows[1][5], source_rows[2][0]) == (4, 23, 20), 'Installed route follows the three source transition rows')
    return dict(writes=len(spans), code_bytes=code_hi - code_lo, inbound_allocation_matches=0,
                exact_relocated_assets=len(moves), full_image_inverse=True, initial_routes=[3, 4, 23, 20])


def initialized(rom, sym, assets, language, marker):
    m = scene.empty(rom)
    for address, count in ((0x02000000, 0x10000), (0x06000000, 0x18000), (0x07000000, 0x400)):
        scene.fill(m, address, bytes(count))
    m.put(0x04000006, 160, 2)
    m.put(0x0300112F, 0xA0 + LANGUAGES.index(language), 1)
    m.put(CONFIG, 3, 2)
    m.r[11] = m.r[2] = 0
    scene.invoke(m, 0x080908A0)
    for slot in range(5):
        item = PRES + slot * 0x50
        need(m.get(item + 0x48) == assets[language + '_p0'] and m.get(item + 0x4C) == 0x08090878
             and m.get(item + 0x0E, 2) == slot, 'Actual full initializer builds all five language presentations')
    keep = scene.allocate_native(m, 0x08015AB4, 0xF0000000)
    scene.invoke(m, 0x08090BF4)
    header = POOL + 0x118
    need(keep == POOL and m.get(header) == sym['m23_title_init_callback'] and m.get(0x03001338, 2) == 3,
         'Real constructor allocates one title owner and its palette task beside the common dispatcher')
    reads = []
    def step(keys=0):
        m.put(CUR, header)
        m.put(0x030012CA, 0, 2)
        m.put(0x0300130A, keys, 2)
        m.r[11] = 0
        stop = m.r[14]
        pc = m.run(m.get(header), {stop, 0x0837DB60})
        if pc == 0x0837DB60:
            need(m.r[0] == 26 and m.r[1] == m.r[13] and not reads, 'Single actual eligibility read into its private stack buffer')
            reads.append(m.r[0])
            scene.fill(m, m.r[1], marker)
            m.r[0] = 0
            m.run(m.r[14], {stop})
    return m, keep, header, step, reads


def dispatch(m, keep):
    m.put(CUR, keep)
    m.r[5] = CONFIG
    sp = m.r[13]
    m.r[13] -= 4
    m.put(m.r[13], m.r[14])
    m.run(0x08015AE4, {m.r[14]}, max_steps=512)
    need(m.r[13] == sp and scene.memory(m, CONFIG + 4, 6) == bytes(6), 'Native dispatcher clears the three request words')
    return m.get(CONFIG, 2)


def title_route(rom, m, language, opened):
    sym = m['symbols']
    vm, keep, hdr, step, reads = initialized(rom, sym, m['asset_pointers'], language,
                                            b'BS15M23\x01' if opened else b'\xff' * 8)
    phase = hdr + 0x18
    for _ in range(60):
        step()
    need(vm.get(hdr) == 0x08090C7C and reads == [26] and vm.get(phase + 0x1C) == opened,
         'Native prompt timer and cached actual reader result')
    step(0x20)
    need(vm.get(hdr) == sym['m23_title_enter_root'], 'Native Start accepts the new title root')

    def to_idle():
        for tick in range(1, 161):
            step()
            if vm.get(hdr) == sym['m23_title_idle']:
                return tick
        raise ValueError('Bounded menu slide did not complete')

    slide = to_idle()
    need(slide == 96 and vm.get(0x030012CA, 2) == m['simultaneous_root_parts'][language], 'All five native rows simultaneously staged')
    need(scene.memory(vm, 0x05000220, 32) == scene.memory(vm, 0x03002C38, 32)
         and scene.memory(vm, 0x05000240, 32) == scene.memory(vm, 0x03002C18, 32), 'Actual corrected selected and unselected palette copies')
    for _ in range(4):
        step(4)
    step(0x40)
    to_idle()
    need(vm.get(phase + 4, 1) == 2 and vm.get(PRES + 0x0E, 2) == 10
         and vm.get(PRES + 0x5E, 2) == (9 if opened else 10), 'Unavailable mode22 and separately persisted Shoot eligibility')
    step(4)
    step(0x40)
    if not opened:
        need(vm.get(hdr) == sym['m23_title_idle'] and vm.get(CONFIG + 4, 2) == 0, 'Locked row refuses the ordinary A')
        return dict(language=language, open=False, root_parts=m['simultaneous_root_parts'][language], request=None)
    need(vm.get(hdr) == sym['m23_title_confirm_exit'], 'Normal A on the eligible Shoot entry')
    window = [vm.get(0x030012BC + i, 1) for i in range(4)]
    vm.run(0x0801155C, {0x080116DC}, max_steps=1000)
    physical = [vm.get(a, 2) for a in (0x04000000, 0x04000042, 0x04000046)]
    need(window == [72, 72, 87, 87] and physical == [0x5B00, 0x5050, 0x5F5F],
         'Actual shared VBlank projection and exact physical WIN1 coordinates')
    for ticks in range(1, 100):
        step()
        if vm.get(0x03001338, 2) == 1:
            break
    need(ticks == 51 and not vm.get(hdr + 0x10, 2) & 2
         and vm.get(keep + 0x10, 2) & 2
         and scene.memory(vm, CONFIG + 4, 6) == pack('<3H', 1, 0, 0)
         and vm.get(CONFIG + 0x1A, 2) == 8, 'Window completion retires both title tasks and produces exact source config bit8')
    need(dispatch(vm, keep) == 4, 'Actual shared dispatcher enters native character select')
    constructors = absolute(rom, 0x08015B74)
    ctor = absolute(rom, constructors + 4 * 12)
    need(ctor == 0x080818C0, 'Registered native character-select constructor')
    vm.r[11] = 0
    scene.invoke(vm, ctor)
    headers = [POOL + i * 0x118 for i in range(1, 7)]
    ch = headers[0]
    vm.put(CUR, ch)
    vm.r[5] = ch + 0x18
    vm.put(vm.r[5], 0, 2)
    vm.run(0x08081C64, {0x08081CD4}, max_steps=512)
    need(vm.get(ch + 0x18, 2) == 5, 'Actual native bit8 selector stores choice5')
    terminal = (0x08082D50, 0x08082438, 0x080827E8, 0x080820C8, 0x08083118)
    vm.put(0x03004738, 0, 2)
    for owner, addr in zip(headers[1:], terminal, strict=True):
        vm.put(CUR, owner)
        scene.invoke(vm, addr)
    need(vm.get(0x03004738, 2) == 0xF80, 'Actual five native predecessor retirement producers')
    vm.put(CUR, ch)
    scene.invoke(vm, 0x08081F70)
    need(vm.get(0x03001338, 2) == 1 and scene.memory(vm, CONFIG + 4, 6) == pack('<3H', 1, 5, 0)
         and dispatch(vm, keep) == 23, 'Physical ordinary mode23 transition with only the common native owner retained')
    return dict(language=language, open=True, root_parts=m['simultaneous_root_parts'][language],
                native_window=dict(shadow=window, physical=physical, exit_ticks=ticks), actual_mode_trace=[3, 4, 23],
                native_selection_request=[1, 5, 0], character_select_retirement_mask=0xF80)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    need(not a.report.exists(), 'Fresh report')
    work = ROOT / 'build'
    directory = work / 'mode23-title-scene-r2-20261117'
    rom = exact(directory / 'component.gba', TITLE)
    before = exact(work / 'mode23-eligible-scene-20261117/component.gba', ELIGIBLE)
    m = json.loads(exact(directory / 'manifest.json', MANIFEST))
    visual = json.loads(exact(work / 'mode23-title-visual-r2-independent-20261117/final.json', PREVIEW_CHECK))
    atlasdir = work / 'mode23-title-assets-r2-20261117'
    atlas = exact(atlasdir / 'assets.bin', visual['assets_sha256'])
    metadata = json.loads(exact(atlasdir / 'manifest.json', visual['manifest_sha256']))
    source = exact(a.source, SOURCE)
    packed = composition(before, rom, m, atlas, metadata, source)
    lifecycle = json.loads(exact(work / 'mode23-scene-independent-r3-20261117/final.json', SCENE_CHECK))
    need(lifecycle['component_sha256'] == 'B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE',
         'Independent prior scene cleanup and native mode23 to20 evidence preserved by complete inverses')
    paths = [title_route(rom, m, lang, False) for lang in LANGUAGES]
    paths.append(title_route(rom, m, 'digicode', True))
    report = dict(status='MODE23_CORRECTED_TITLE_INSTALLED_INDEPENDENT_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  installed_sha256=TITLE, manifest_sha256=MANIFEST, immutable_scene_lifecycle_sha256=SCENE_CHECK,
                  placement=packed, actual_ARM_paths=paths, native_full_title_initializer_executed=True,
                  author_fixtures_repeated=False, EEPROM_device_modeled=True, actual_BizHawk_executed=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()

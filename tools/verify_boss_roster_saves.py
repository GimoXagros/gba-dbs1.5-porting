"""Verify each winner's physical EEPROM, then reopen a copy in a new headless core."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import time

from run_flow_release import BIZHAWK, DONOR, PrivateDesktopProcess, ROOT, digest


def verify(directory, rom_hash):
    report = json.loads((directory / 'report.json').read_text())
    fighter = report['fighter']
    assert report['outcome'] == 'PASS' and report['rom'] == rom_hash
    assert digest(directory / 'loaded.bin') == digest(directory / 'probe.gba') == rom_hash
    assert digest(directory / 'events.txt') == report['trace_sha256']
    assert digest(directory / 'driver.lua') == report['script_sha256']
    source = directory / 'data/104/probe.SaveRAM'
    raw = source.read_bytes()
    assert digest(source) == report['save_out'] and report['save_in'] == DONOR
    # BizHawk presents physical EEPROM blocks in serial order.
    data = b''.join(raw[i:i + 8][::-1] for i in range(0, 200, 8))
    assert int.from_bytes(data[192:196], 'little') == sum(data[:192])
    mask = int.from_bytes(data[16:18], 'little')
    # The WSC serializer masks the clear word to 14 bits on the next save.
    assert mask == (1 | (1 << fighter)) & 0x3fff
    out = directory / 'cold'
    out.mkdir(exist_ok=False)
    alias = Path('W:/') / out.relative_to(ROOT.resolve())
    cfg = json.loads((directory / 'config.json').read_text())
    for i, entry in enumerate(cfg['PathEntries']['Paths']):
        location = out / 'data' / str(i)
        location.mkdir(parents=True)
        entry['Path'] = (alias / 'data' / str(i)).as_posix()
    settings = out / 'config.json'
    settings.write_text(json.dumps(cfg), encoding='utf8')
    shutil.copyfile(source, out / 'data/104/probe.SaveRAM')
    exe = ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe'
    assert digest(exe) == BIZHAWK
    script = alias / 'cold.lua'
    shutil.copyfile(ROOT / 'tools/bizhawk_boss_roster_cold.lua', script)
    call = ['--gdi', f'--config={(alias / "config.json").as_posix()}', f'--lua={script.as_posix()}',
            f'--userdata=out:{alias.as_posix()};mask:{mask}', (alias.parent / 'probe.gba').as_posix()]
    with PrivateDesktopProcess(exe, call, exe.parent) as process:
        deadline = time.monotonic() + 150
        while not (out / 'done').exists() and time.monotonic() < deadline:
            time.sleep(.3)
        assert (out / 'done').read_text() == 'PASS'
        assert process._wait_process(process.process.hProcess, 20000) == 0
    observed = (out / 'observed.txt').read_text().split()
    result = dict(fighter=fighter, sha256=rom_hash, eeprom_sha256=digest(source),
                  expected_clear=f'{mask:04X}', loaded_record=observed[0], loaded_configuration=observed[1],
                  checksum_passes=int(observed[2]), title_frame=int(observed[3]), visible=False)
    (out / 'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(fighter, observed, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--rom-sha256', required=True)
    p.add_argument('--ids', type=int, nargs='+', default=range(15), choices=range(15))
    p.add_argument('--workers', type=int, default=3)
    args = p.parse_args()
    root = args.directory.resolve()
    assert root.is_relative_to((ROOT / 'build').resolve())
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda n: verify(root / f'id{n:02}-form0', args.rom_sha256), args.ids))


if __name__ == '__main__':
    main()

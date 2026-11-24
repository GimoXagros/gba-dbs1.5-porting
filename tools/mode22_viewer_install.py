"""Plan native mode22 resources, FC song and dispatch on a caller-owned full image."""
import hashlib
import json
import struct
from pathlib import Path
from mode23_linker import compose
from mode22_source_scene import assembly as primitives
from mode22_viewer import assembly as viewer
from mode22_viewer_graphics import assembly as graphics

BASE = 0x08000000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
RESOURCES = 'DB1DD2EB60C3E918B526FE226EF6FC1E9269004E2DD4100BB0AF2F073E1099FA'
AUDIO = '5D17177D067EFD454F0E6849C355AED731192B2D67368F00654B28B0EF610CD5'
LOADERS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
CALLBACKS = ('m22_init', 'm22_create', 'm22_render', 'm22_controller', 'm22_line_irq')


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def plan(source, before, allocator, snapshot_reader, resources, resource_manifest, audio, audio_manifest):
    assert allocator.native is before and sha(source) == SOURCE
    assert sha(resource_manifest) == RESOURCES and sha(audio_manifest) == AUDIO
    rm, am = json.loads(resource_manifest), json.loads(audio_manifest)
    assert rm['bundle_sha256'] == sha(resources) and am['bundle_sha256'] == sha(audio)
    writes = []
    pointers = {}
    for row in rm['objects']:
        start, count = row['offset'], row['size']
        data = resources[start:start+count]
        assert len(data) == count and sha(data) == row['sha256']
        offset = allocator.allocate(count, 'mode22 '+row['label'], 4)
        writes.append((offset, data, row['label']))
        pointers[row['label']] = BASE+offset
    audio_at = allocator.allocate(len(audio), 'mode22 FC audio', 4)
    linked_audio = bytearray(audio)
    for fixup in am['local_u32_fixups']:
        at, target = fixup['offset'], fixup['relative_target']
        assert 0 <= at <= len(audio)-4 and 0 <= target < len(audio)
        struct.pack_into('<I', linked_audio, at, BASE+audio_at+target)
    writes.append((audio_at, bytes(linked_audio), 'mode22 FC audio'))
    previous_table = 0x08D9D940
    assert all(struct.unpack_from('<I', before, address)[0] == previous_table for address in LOADERS)
    assert before.count(struct.pack('<I', previous_table)) == len(LOADERS)
    table_at = previous_table-BASE
    songs = before[table_at:table_at+122*8] + linked_audio[:8]
    new_table = allocator.allocate(len(songs), '123 native songs', 4)
    writes.append((new_table, songs, '122 previous songs and new FC'))
    for address in LOADERS:
        writes.append((address, struct.pack('<I', BASE+new_table), 'MP2K song table reader'))
    parts = (primitives(source), viewer(snapshot_reader, 122), graphics(rm, pointers))
    provisional, _, _ = compose(parts, 0x08F00000, CALLBACKS)
    code_at = allocator.allocate(len(provisional), 'mode22 viewer and tables', 4)
    code, symbols, link = compose(parts, BASE+code_at, CALLBACKS)
    assert len(provisional) == len(code)
    writes.append((code_at, code, 'mode22 viewer and tables'))
    modes = 0xDB4400
    callbacks = modes+22*12
    dispatch = modes+24*12+22*4
    transitions = modes+24*16
    assert before[callbacks:callbacks+12] == bytes(12) and before[dispatch:dispatch+4] == bytes(4)
    assert before[transitions+18:transitions+24] == bytes.fromhex('04040e021300')
    assert before[transitions+132:transitions+138] == bytes(6)
    assert source[0x74FA42:0x74FA48] == bytes.fromhex('04160e021300')
    assert source[0x74FAB4:0x74FABA] == bytes.fromhex('140000000000')
    writes += [(callbacks, struct.pack('<3I', symbols['m22_init'], symbols['m22_create'], 0x080159B0), 'mode22 callbacks'),
               (dispatch, struct.pack('<I', 0x08015B40), 'mode22 normal dispatcher'),
               (transitions+19, bytes((22,)), 'source title choice1 to Tamer Tag'),
               (transitions+132, bytes((20,)), 'Tamer Tag to title background')]
    intervals=sorted((at,at+len(data)) for at,data,_ in writes)
    assert all(a[1] <= b[0] for a,b in zip(intervals,intervals[1:]))
    return writes,dict(symbols=symbols,link=link,snapshot_reader=snapshot_reader,resource_addresses=pointers,
                       audio_sha256=sha(audio),audio_address=BASE+audio_at,song_table=BASE+new_table,
                       FC_native_id=122,source_task_priorities=[0xF100,0x1000],
                       new_global_RAM_bytes=0,body_sha256=sha(code),source_sha256=SOURCE)

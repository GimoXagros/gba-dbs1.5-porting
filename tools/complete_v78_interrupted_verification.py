"""Finish only the missing verification tail of the interrupted second v78 build."""
import argparse
import ast
import dis
import hashlib
import json
import runpy
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = '07B5A946051F4E823F1AAB9B7A8A1B3D7BC3FD7C29E4AA686C3059EC8E82158C'
CHECKER = '9718A08F8FE17AB75FD2C0AA2860DE15BA5E898026225F184C4FE73FC92539D8'
PREFLIGHT = 'B583043DF32936875C409AE14FECAB2925854CCA9F5DA8D861D91A9A1791CAC0'
MISSING = {'build-manifest.json'} | {'intermediate/' + n + '.json' for n in (
    'digicode-font', 'digicode-resource-verification', 'evolution-music-author-verification',
    'evolution-music-integration-verification', 'evolution-music-pause-verification',
    'evolution-transition-verification', 'impmon-evolution-verification',
    'language-native-inventory', 'shoot-child-rectangle-verification',
    'shoot-display-epoch-verification', 'shoot-initializer-p1-verification',
    'shoot-owner-link-verification', 'shoot-palette-calls-verification',
    'shoot-sram-boundary', 'title-language-verification')}
sha = lambda b: hashlib.sha256(b).hexdigest().upper()


def inventory(folder):
    files = sorted(p for p in folder.rglob('*') if p.is_file())
    assert all(p.suffix.lower() not in ('.sav', '.state', '.saveram') for p in files)
    return {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    option = parser.parse_args()
    assert not option.report.exists()
    a = ROOT / 'build/repro-v78-20261116-a'
    b = ROOT / 'build/repro-v78-20261116-b'
    assert not option.report.resolve().is_relative_to(a) and not option.report.resolve().is_relative_to(b)
    source = ROOT / 'tools/build_current_candidate.py'
    checker = ROOT / 'tools/verify_impmon_main_inventory.py'
    assert sha(source.read_bytes()) == MAIN and sha(checker.read_bytes()) == CHECKER
    preflight = ROOT / 'build/impmon-main-preflight-independent-20261116/preflight.json'
    assert sha(preflight.read_bytes()) == PREFLIGHT
    prior = (ROOT / 'build/repro-v77-final-audit-20261116/audit.json').read_bytes()
    assert sha(prior) == '0EBBA5EFBEA7292990F54E7E138C1527E853BF58047BEF73260B6BBFF352ECFE'
    old = json.loads(prior)
    check = runpy.run_path(str(checker))
    pins = {**old['source_tool_sha256'], **check['PINS']}
    assert all(sha((ROOT / p).read_bytes()) == h for p, h in pins.items())
    ai, bi = inventory(a), inventory(b)
    assert len(ai) == 325 and len(bi) == 309 and ai.keys() - bi.keys() == MISSING
    assert not bi.keys() - ai.keys() and all(ai[p] == h for p, h in bi.items())
    assert (ROOT / 'build/repro-v78-20261116-a.log').read_text().rstrip().endswith(check['FINAL'])
    assert (ROOT / 'build/repro-v78-20261116-b.log').read_text().rstrip().endswith('[build] verify_shoot_native_scene_connection.py')
    scope = runpy.run_path(str(source))
    # Pin the same explicitly authorized inputs used by both original launches.
    inputs = Path('C:/Users/김기호/Downloads/JUS')
    args = types.SimpleNamespace(gba=inputs / 'Digimon - Battle Spirit (USA).gba',
        wsc10=inputs / 'Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc',
        wsc15=inputs / 'Digimon Tamers - Battle Spirit Ver 1.5.wsc',
        font=inputs / 'jus-kr-project/local/vendor/galmuri/dist/Galmuri11-Condensed.bdf',
        font_license=inputs / 'jus-kr-project/local/vendor/galmuri/dist/LICENSE.txt')
    for name, constant in [('gba', 'GBA_SHA256'), ('wsc10', 'WSC10_SHA256'),
            ('wsc15', 'WSC15_SHA256'), ('font', 'FONT_SHA256'), ('font_license', 'FONT_LICENSE_SHA256')]:
        scope['require_hash'](getattr(args, name), scope[constant], name)
    scope.update(args=args, output=b.resolve())
    tree = ast.parse(source.read_bytes())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    boundary = next(i for i, n in enumerate(fn.body) if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'rectangle_review')
    path_nodes = [n for n in fn.body[:boundary] if isinstance(n, ast.Assign)
        and isinstance(n.value, ast.BinOp) and isinstance(n.value.op, ast.Div)]
    tail = fn.body[boundary:]
    assert ast.unparse(tail[1].value.args[0]) == "'verify_shoot_child_attack_rectangle_production.py'"
    fn.name = 'finish_verification'
    fn.body = path_nodes + tail
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    exec(compile(module, str(source), 'exec'), scope)
    function = scope['finish_verification']
    required = {i.argval for i in dis.get_instructions(function) if i.opname == 'LOAD_GLOBAL'}
    assert required <= scope.keys() | set(vars(__import__('builtins')))
    report = dict(status='V78_VERIFICATION_TAIL_PREFLIGHT_PASS', main_sha256=MAIN,
        checker_sha256=CHECKER, source_pins=pins, existing_b=bi, expected_missing=sorted(MISSING),
        first_resumed_source_line=tail[0].lineno, resumed_calls=[n.value.args[0].value for n in tail
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
            and n.value.func.id == 'run'], original_b_exit_status='lost/interrupted', emulator_launched=False)
    if option.execute:
        assert function() == 0
        after = inventory(b)
        assert after == ai and inventory(a) == ai
        assert all(after[p] == h for p, h in bi.items())
        assert all(sha((ROOT / p).read_bytes()) == h for p, h in pins.items())
        report.update(status='V78_VERIFICATION_TAIL_COMPLETE', resumed_exit_status=0,
            files_each=len(after), prior309_unchanged=True, complete_inventory=after)
    option.report.parent.mkdir(parents=True, exist_ok=True)
    with option.report.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(report['status'], sha(option.report.read_bytes()))


if __name__ == '__main__':
    main()

"""Assemble lossless 2x game screenshots in menu order across all four languages."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROWS = (
    ('title', '타이틀 · 시작 안내'),
    ('main', '메인 메뉴'),
    ('versus', '친구와 대전 · 버전 선택'),
    ('options', '설정'),
    ('sound', '설정 · 사운드 테스트'),
    ('erase', '설정 · 데이터 지우기 선택'),
    ('collection', '컬렉션 · 해금 후'),
    ('tag', '테이머 태그 · 보유 태그 없음'),
    ('solo-select', '혼자 대전 · 캐릭터 선택'),
    ('dark', 'D-ARK · 캐릭터 선택'),
    ('shoot-select', '디지몬 슈트 · 캐릭터 선택'),
)
LANGUAGES = ('영어', '일본어', '한국어', '디지코드')


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def render(folders, font, bold_font, earned_folders=None):
    regular = ImageFont.truetype(str(font), 24)
    bold = ImageFont.truetype(str(bold_font), 28)
    title = ImageFont.truetype(str(bold_font), 38)
    pad, gap, width, height = 32, 12, 480, 320
    pitch = height + 66
    rows = [(name,label,False) for name,label in ROWS]
    if earned_folders:
        rows.insert(1,('title','타이틀 · 태그 획득 후',True))
        rows.insert(next(i for i,row in enumerate(rows) if row[0]=='tag')+1,
                    ('tag','테이머 태그 · 복원된 보상',True))
    sheet = Image.new('RGB', (pad*2 + width*4 + gap*3, 163 + len(rows)*pitch), '#151821')
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 16), '디지몬 배틀 스피릿 Ver. 1.5  /  메뉴 검수', font=title, fill='#f4f5f7')
    sources = []
    rom = None
    for lang, folder in enumerate(folders):
        report = json.loads((folder/'launch.json').read_bytes())
        assert report['language']==lang and report['outcome']=='PASS' and report['loaded_rom_exact']
        assert report['script_unchanged'] and not report['visible'] and not report['guest_writes']
        if rom is None:
            rom = report['rom_sha256']
        assert report['rom_sha256']==rom
        x = pad + lang*(width+gap)
        draw.text((x, 103), LANGUAGES[lang], font=bold, fill='#fed67c')
        earned=earned_folders[lang] if earned_folders else None
        if earned:
            award_report=json.loads((earned/'launch.json').read_bytes())
            assert award_report['language']==lang and award_report['rom_sha256']==rom and award_report['outcome']=='PASS'
            assert award_report['loaded_rom_exact'] and award_report['script_unchanged'] and not award_report['visible']
            assert award_report['copied_campaign_eeprom']!=report['copied_campaign_eeprom']
        for i,(name,label,from_earned) in enumerate(rows):
            top = 153 + i*pitch
            if lang==0:
                draw.text((pad,top), label, font=regular, fill='#e3e7eb')
            filename = name + '.png'
            path = (earned if from_earned else folder)/filename
            raw = path.read_bytes()
            assert digest(raw)==(award_report if from_earned else report)['files'][filename]
            with Image.open(path) as frame:
                assert frame.size==(240,160)
                pixels = frame.convert('RGB').resize((width,height),Image.Resampling.NEAREST)
            sheet.paste(pixels,(x,top+39))
            sources.append(dict(language=lang,menu=name,earned_tag=from_earned,file=str(path),sha256=digest(raw)))
    draw.text((pad, 70), 'GBA 실제 화면  ·  원본 240 × 160 픽셀을 2배로 확대  ·  ROM '+rom[:8],
              font=regular, fill='#bdc6d7')
    return sheet, dict(rom_sha256=rom,columns=LANGUAGES,source_screenshots=sources)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders',nargs=4,type=Path)
    parser.add_argument('--font',type=Path,required=True)
    parser.add_argument('--bold-font',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--earned-folders',nargs=4,type=Path)
    args=parser.parse_args()
    sheet,report=render(args.folders,args.font,args.bold_font,args.earned_folders)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(args.output)
    report['sheet_sha256']=digest(args.output.read_bytes())
    args.output.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS',len(report['source_screenshots']),sheet.size,report['sheet_sha256'])

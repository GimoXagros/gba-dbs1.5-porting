# gba-dbs1.5-porting

*Digimon Tamers: Battle Spirit Ver. 1.5*의 콘텐츠와 동작을 USA GBA 엔진으로 옮기는 개발 저장소입니다. 완성본은 아직 아닙니다.

## 현재 상태

현재 주 빌드는 **v90**입니다. 원본에서 따로 만든 v89 빌드 두 벌에 원더스완 1.5의 영문 메뉴 그래픽을 적용했고, 결과물 513개가 모두 일치했습니다. ROM SHA-256은 `8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869`입니다. [영문 메뉴와 이름판 검수](records/english-menu-pixel-review-20261124.md).

v90에서 11단계 체크포인트를 이어 플레이해 컬렉션을 열고, Digimon Shoot 7라운드를 클리어한 뒤 타이틀로 돌아왔습니다. 게임을 완전히 껐다 켜도 영문 메뉴에 DIGIMON SHOOT가 표시됐습니다. 엔딩 보상과 테이머 태그 연동은 개발 중입니다. [실행 기록](records/collection-seven-round-final-20261124.md).

## 이전 v78 검증 기록

v78에서는 추가 캐릭터의 진화 경로를 검증했습니다. 추가 캐릭터의 진화 동작 표가 기존 11명 기준으로 남아 있어 잘못된 애니메이션 번호와 음악 요청을 만들던 원인을 고쳤습니다. 원더스완 1.5의 15명 자료를 실제 소비자에 연결하고 기본 모드의 임프몬 진화 경로도 복원했습니다. [통합 기록](records/evolution-runtime-integration-v78.md).

v78 빌드는 **16MiB**, ROM SHA-256은 `C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1`입니다. 독립 생성한 두 빌드의 **325개 파일과 125개 매니페스트 항목**이 일치합니다. A는 전체 빌드를 종료 코드 0으로 마쳤습니다. B는 파일 생성 후 중단됐습니다. 기존 파일 309개를 보존한 채 남은 검증만 재개해 종료 코드 0을 확인했습니다. B의 원래 종료 코드는 확인할 수 없습니다. [독립 빌드 검수](records/repro-v78-inventory-qa-20261117.md).

기존 6E 검증에 이어 나머지 6C·6D·6F 모두 창 없는 실제 대전에서 일시정지·같은 곡 재개·자연 진화 종료·스테이지 음악 복귀를 확인했습니다. CPU 임프몬 도전 대전까지는 승인된 D스피릿 보조만 사용했습니다. ID14도 메모리 개입 없이 일반 조작으로 수정 전 잘못된 번호와 수정 후 정상 번호 115/25 및 정지·재개·복귀를 비교했습니다. 별도 일반 점프로 [공중 종료도 비교](records/evolution-id14-air-actual-independent-qa-20261117.md)했습니다. [임프몬 검수](records/evolution-music-6f-event-table-runtime-qa-20261116.md) · [ID14 검수](records/evolution-id14-event-table-runtime-qa-20261116.md).

원본·GBA 네 곡씩의 [전체 재생 비교](records/bgm-all-four-capture-qa-20261110.md)는 v77에서 완료했습니다. 파형 위상·양자화 등 플랫폼 차이가 있어 완전한 청감 일치는 주장하지 않습니다. 실제 플레이 시험은 호스트 음소거 상태에서 재생 상태와 제어 흐름을 확인했습니다.

Shoot의 공격 격파→종료→IRQ→정리→후속 mode8은 [v76의 승인된 보스 HP 1회 개입 시험](records/shoot-native-terminal-display-store-capture-qa-20261110.md)에서 확인했습니다. 가장 이른 counter1 IRQ도 [추가 검수](records/shoot-counter1-actual-audit-20261110.md)를 통과했습니다. 이 기록은 당시 실행 결과입니다. v78에서 모든 시험을 반복한 것은 아닙니다. 기존 `E5`의 최초 원인, 일반 움직임·카메라, 전체 콘텐츠와 네 언어 최종 QA는 남아 있습니다.

1.5 타이틀과 네 언어 결과 그림은 [이전 v67 기록](records/title-result-integration-v67.md)에 남아 있습니다. 한국어·디지코드 승리와 무승부는 일본어판 원본 `WIN`·`DRAW`를 사용합니다.

**1.5 원본 기능과 실행 안정성을 우선하며 요청에 따라 번역·그래픽·타이틀 작업도 병행합니다.** 이미지로 된 글자는 픽셀 제작 전문가와 별도 QA 에이전트가 원본 규격과 결과를 검토합니다.

## 재개와 작업 기록

- [현재 작업 인계](ASTRA_HANDOFF.md)
- [재개 지점](RESUME.md)
- [검증 범위와 미완료 항목](PORT_AUDIT.md)
- [작업 기록](WORK_LOG.md)
- [실행 오류와 검증 증거](records/runtime-repair-20261023.md)

실행 검사는 창을 표시하지 않고 진행합니다. 세이브 사용과 시험 개입은 각 실행 기록에 명시합니다. v77 실행은 제공 세이브 없이 진행했습니다. 원본 ROM·생성 ROM·세이브·메모리 덤프·캡처·로컬 의존성은 GitHub에 올리지 않습니다. 이 저장소는 소스, 검증 도구, 해시와 작업 기록을 관리합니다.

## 로컬 빌드

검증된 체크포인트를 체크아웃한 뒤 Pillow·Capstone·Keystone이 설치된 Python으로 실행합니다. 주 빌더가 호출하는 이미지 검사·디스어셈블·어셈블 도구에서 이 의존성을 사용합니다. v77 검수 환경은 Python 3.12.14 / Pillow 13.0.0입니다. 입력 파일과 폰트의 지정 해시는 인계서 및 빌더에서 확인할 수 있습니다.

```powershell
python tools/build_current_candidate.py "<USA-GBA-original>" "<WSC-1.0-original>" "<WSC-1.5-original>" "<new-output-directory>" --font "<Galmuri11-Condensed.bdf>" --font-license "<LICENSE.txt>"
```

빌더는 입력·중간 결과·최종 해시가 다르면 중단하며 이미 파일이 있는 출력 폴더를 덮어쓰지 않습니다. 새 체크포인트는 두 개의 빈 출력 폴더에서 전체 빌드를 완료하고 모든 상대 경로와 해시를 비교한 뒤 기록합니다. 개발 중 작업 트리에는 아직 검증되지 않은 변경이 있을 수 있습니다.

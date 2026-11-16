# gba-dbs1.5-porting

*Digimon Tamers: Battle Spirit Ver. 1.5*의 콘텐츠와 동작을 USA GBA 엔진으로 옮기는 개발 저장소입니다. 완성본은 아직 아닙니다.

## 현재 상태

최신 재현 체크포인트는 **v77**입니다. 원본 진화 BGM 네 그룹과 캐릭터별 선택을 복원하고, 새 곡의 일시정지·재개에 필요한 현재 음악 기록을 고쳤습니다. [음악 통합 기록](records/original-evolution-bgm-integration-v77.md)을 참고하세요.

주 빌드는 **16MiB**, ROM SHA-256은 `C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278`입니다. 두 전체 빌드의 산출물 **319개와 매니페스트 항목 123개**가 일치합니다. 한 폴더에 나중에 생긴 세이브 한 개는 내용을 읽지 않고 제외·보존했습니다. 당시 프로세스 종료 코드는 유실되어 완료 매니페스트와 실제 산출물을 확인했습니다. [독립 빌드 검수](records/repro-v77-inventory-qa-20261116.md).

창 없는 한국어 설정→일반 전투→WIN에서 화면 8장과 128줄 진행 기록이 v76과 같았습니다. 실제 진화 BGM `6E` 재생과 진화 종료 후 스테이지 음악 복귀도 확인했습니다. 음악 관련 IWRAM 차이와 작성자를 추적하지 않은 스택 두 워드는 그대로 기록했습니다. [실제 전투·음악 검수](records/result-v77-capture-qa-20261116.md).

원본·GBA 네 곡씩의 [전체 재생 비교](records/bgm-all-four-capture-qa-20261110.md)는 끝까지 수행했습니다. 파형 위상·양자화 등 플랫폼 차이가 있어 완전한 청감 일치는 주장하지 않습니다. 새 곡 `6E`의 실제 Start 정지·재개와 자연 스테이지 음악 복귀도 [별도 시험](records/evolution-music-pause-capture-qa-20261116.md)에서 확인했습니다. 다른 세 곡의 실제 진화·정지·재개 경로까지 관찰했다는 뜻은 아닙니다.

Shoot의 공격 격파→종료→IRQ→정리→후속 mode8은 [v76의 승인된 보스 HP 1회 개입 시험](records/shoot-native-terminal-display-store-capture-qa-20261110.md)에서 확인했습니다. 가장 이른 counter1 IRQ도 [추가 검수](records/shoot-counter1-actual-audit-20261110.md)를 통과했습니다. 이 과거 실행 증거를 v77에서 전부 다시 수행한 것으로 해석하지 않습니다. 기존 `E5`의 최초 원인, 일반 움직임·카메라, 전체 콘텐츠와 네 언어 최종 QA는 남아 있습니다.

1.5 타이틀과 네 언어 결과 그림은 [이전 v67 기록](records/title-result-integration-v67.md)에 남아 있습니다. 한국어·디지코드 승리와 무승부는 일본어판 원본 `WIN`·`DRAW`를 사용합니다.

**1.5 원본 기능과 실행 안정성을 우선하며, 요청에 따라 번역·그래픽·타이틀 작업도 병행합니다.** 이미지로 된 글자는 픽셀 제작 전문가와 별도 QA 에이전트가 원본 규격과 결과를 검토합니다.

## 재개와 작업 기록

- [현재 작업 인계](ASTRA_HANDOFF.md)
- [재개 지점](RESUME.md)
- [검증 범위와 미완료 항목](PORT_AUDIT.md)
- [작업 기록](WORK_LOG.md)
- [실행 오류와 검증 증거](records/runtime-repair-20261023.md)

실행 검사는 창을 표시하지 않고 진행합니다. 세이브 사용과 시험 개입은 각 실행 기록에 명시하며, 이번 v77 실행은 제공 세이브 없이 진행했습니다. 원본 ROM·생성 ROM·세이브·메모리 덤프·캡처·로컬 의존성은 GitHub에 올리지 않습니다. 이 저장소는 소스, 검증 도구, 해시와 작업 기록을 관리합니다.

## 로컬 빌드

검증된 체크포인트를 체크아웃한 뒤, Pillow·Capstone·Keystone이 설치된 Python으로 실행합니다. 주 빌더가 호출하는 이미지 검사·디스어셈블·어셈블 도구에서 이 의존성을 사용합니다. v77 검수 환경은 Python 3.12.14 / Pillow 13.0.0입니다. 입력 파일과 폰트의 지정 해시는 인계서 및 빌더에서 확인할 수 있습니다.

```powershell
python tools/build_current_candidate.py "<USA-GBA-original>" "<WSC-1.0-original>" "<WSC-1.5-original>" "<new-output-directory>" --font "<Galmuri11-Condensed.bdf>" --font-license "<LICENSE.txt>"
```

빌더는 입력·중간 결과·최종 해시가 다르면 중단하며 이미 파일이 있는 출력 폴더를 덮어쓰지 않습니다. 새 체크포인트는 두 개의 빈 출력 폴더에서 전체 빌드를 완료하고 모든 상대 경로와 해시를 비교한 뒤 기록합니다. 개발 중 작업 트리에는 아직 검증되지 않은 변경이 있을 수 있습니다.

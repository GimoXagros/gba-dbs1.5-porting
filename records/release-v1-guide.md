# Digimon Battle Spirit Ver. 1.5 — GBA 포팅 패치

## 한국어

1. 보유한 **Digimon – Battle Spirit (USA)** 원본을 준비한다. 원본 크기는 4,194,304바이트, SHA-256은 `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED`다.
2. 기존 GBA 세이브를 백업한다. 이전 버전을 사용했더라도 미국판 원본에서 다시 시작한다. Floating IPS의 **Apply Patch**에서 `DBS15-GBA-v1.0.3.bps`, 미국판 원본, 새 출력 파일을 차례로 선택한다. 원더스완 세이브는 원더스완용이다.
3. 생성된 GBA 파일은 16,777,216바이트다. `manifest.json`의 ROM SHA-256과 일치하는지 확인한다. 복원한 세이브를 사용할 때는 사용하는 에뮬레이터가 요구하는 GBA EEPROM 형식과 파일명을 유지한다.
4. **OPTIONS → 언어**에서 영어·일본어·한국어·디지코드를 선택한다. **전투 보조**에서 1인 일반전 D-스피릿을 0~999로 고정하거나 보스 체력을 1로 만들 수 있다. 둘 다 기본은 꺼짐이다. 숫자는 방향키 좌우로 1씩, L/R로 100씩 조절한다. **저장**을 눌러 적용한다.
5. 미국판과 통신할 때는 포팅판의 **2P BATTLE → VS VER B•S**를, 이 릴리스끼리 연결할 때는 양쪽에서 **VS VER1.5**를 선택한다. 각 플레이어에게 독립된 저장 공간이 필요하다. 호환 대전에서는 미국판이 지원하는 캐릭터와 무대를 사용한다. 포팅판 전용 진화·태그 교환은 확장 대전에서 사용할 수 있다.
6. **D-ARK**에서 캐릭터를 선택하면 통신 대기 화면이 나타난다. 단독 플레이에서는 **B**로 타이틀에 돌아갈 수 있다. 실물 D-ARK 기기와의 데이터 교환은 지원 범위 밖이다.

## English

Use a clean 4 MiB USA copy of *Digimon – Battle Spirit* matching the SHA-256 above. Back up your GBA save first. For an upgrade, start again from the same clean USA file. In Floating IPS, choose **Apply Patch**, select `DBS15-GBA-v1.0.3.bps`, select the USA input, and save to a new GBA file. Compare the resulting 16 MiB file with the output SHA-256 in `manifest.json`. Use the GBA EEPROM format expected by your emulator.

Choose **OPTIONS** to change the language or save optional single-player assists. Both assists default to off. Select **VS VER B•S** to play against the original USA cartridge software. Choose **VS VER1.5** on both copies of this release for the expanded link mode. Keep separate saves for the two players.

In **D-ARK**, confirm a character to see the accessory waiting screen. In standalone play, press **B** to return to the title. This release covers the disconnected scene only.

## 공개 테스트와 버그 제보 / Playtest reports

무보조 전체 캠페인의 밸런스와 장시간 플레이, 플래시카트 및 실물 케이블은 배포 후 검수 대상이다. 문제가 생기면 릴리스 버전과 패치 해시, 기기나 에뮬레이터·코어 버전, 양쪽 게임 종류와 메뉴 선택, 언어, 전투 보조, 재현 순서, 기대한 결과와 실제 결과를 적어 준다.

For a bug report, include the release and patch hash, device or emulator/core, both games and link menu selections, language, assist settings, reproduction steps, and expected and observed results. A written description is sufficient. Keep personal saves and ROMs private.

Galmuri fonts © 2019–2025 Lee Minseo. See `Galmuri-OFL.txt` for the included license and credits.

# v78 두 산출물 및 중단된 B 검증 후속 독립 감사

## 실행 이력의 경계

- A는 `build/repro-v78-20261116-a`에서 별도 전체 빌드가 종료 코드 0으로 끝났다. 원래 로그의 마지막 줄은 최종 ROM `C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1`에 대한 `[build] PASS`다.
- B는 `build/repro-v78-20261116-b`에서 시작한 별도 전체 빌드였으나 11월 16일에서 17일로 넘어가는 사이 세션이 끊겼다. 원래 프로세스의 종료 코드는 회수하지 못했다. 원래 로그는 `verify_shoot_native_scene_connection.py` 호출에서 끝나며, 전체 빌드가 중단 없이 성공했다고 주장할 수 없다.
- 후속 실행 전 B에는 309개 파일이 있었고, 같은 상대 경로의 A 309개와 각각 SHA-256이 일치했다. B에만 있는 파일이나 다른 내용의 파일은 없었다. 없던 16개는 최종 `build-manifest.json`과 `intermediate/`의 검증 보고서 15개뿐이었다. 빠진 경로의 전체 목록은 [후속 검증 사전 보고서](../build/v78-continuation-20261117/preflight.json)에 고정했다.

## 제한된 후속 검증

`tools/complete_v78_interrupted_verification.py` (`845CCE1E3184F49ED5FFF72D0B5247BDDF741CB92DE6E96AAB73AFD8739FCDA6`)는 메인 빌더 `07B5A946051F4E823F1AAB9B7A8A1B3D7BC3FD7C29E4AA686C3059EC8E82158C`의 AST에서 첫 미완료 지점인 1269행 `rectangle_review`부터 끝까지의 원래 검증 구문을 실행했다. 앞부분에서는 경로 변수 대입만 재구성했다. 사전 단계는 B의 기존 309개 파일을 전부 A와 대조하고 메인·검수기·기존 소스와 입력의 해시를 고정했다. A 산출물을 B로 복사하거나 전체 빌더를 다시 실행하지 않았다.

후속 검증의 15개 원래 도구 호출은 종료 코드 0으로 끝났고, 15개 보고서와 매니페스트가 생겼다. [완료 보고서](../build/v78-continuation-20261117/completion.json) `5D211B2F33A9AE6B42DDBD64DBE203943B1879EBF40E431F00CCE072BD2FAF2E`는 원래 B 종료 상태를 `lost/interrupted`, 후속 검증 종료 상태를 `0`으로 각각 기록한다. 후속 실행 후 B의 325개 파일은 A의 325개와 전부 SHA-256이 같고, 원래 B 309개 파일도 그대로다.

## 독립 완성본 감사

동결된 `tools/verify_impmon_main_inventory.py` (`9718A08F8FE17AB75FD2C0AA2860DE15BA5E898026225F184C4FE73FC92539D8`)를 후속 실행 완료 뒤 별도로 실행했다. [전체 감사 결과](../build/repro-v78-final-audit-20261117/audit.json) `C59C5FA1B43994A24C6F3851B03A25A658E3C8394EEA1E0CE555BBF1085AF97B`는 `EVOLUTION_TWO_BUILD_INVENTORY_PASS`다.

- A와 B 각각 정확히 325개 파일, 빌드 매니페스트의 실제 파일 폐쇄 각각 125개 항목을 검증했다.
- v77의 319개 기존 산출물은 보존됐다. 공유 경로 중 내용이 바뀐 것은 `build-manifest.json`, `current-candidate.gba`, `current-candidate.json` 세 개뿐이다. 새 상대 경로는 사전 예상과 같은 여섯 개다.
- 진화 접촉 조건의 1바이트와 동작 표의 109바이트 변경을 각각 전체 16MiB 역변환으로 검증했다. 최종 ROM 해시는 `C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1`이다.

이 판정은 **두 완성 산출물의 동일성 및 검증 후속 완료**를 뜻한다. B 원래 전체 프로세스가 종료 코드 0으로 끝났다는 판정은 아니다. 실제 6C·6D·6F·ID14 대전 관찰은 별도 기록에 있으며, 이 감사에서 에뮬레이터나 이전 전체 의미 검증을 다시 실행하지 않았다. 과거 E5 원인과 최종 포트 완성 여부는 여전히 미확정이다.

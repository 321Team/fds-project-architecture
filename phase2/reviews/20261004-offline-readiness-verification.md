# Phase2 로컬 선행 검증 및 수정 결과
기준: 2026-10-04 KST. AI: CODEX_ASSISTED.
검증 시작 architecture#8 HEAD: e957eab6f5e146721f3439efe7230f6ded295b61.
수정 collector commit: c2451973ad99ea9d7192e7f6b0d1d73b576dcf56.
작성자 검증이며 독립 리뷰/승인/Runtime 인수를 대신하지 않는다.

## 결론
현장 SSH/계정·비용 입력 없이 가능한 소스 검증을 수행했다. AWS read-only collector의 오류 처리·수집완전성 결함3종을 수정하고 offline11개 시험을 통과했다. Harbor 현장 수집 절차는 Bash 문법과5개 mock경로를 확인했다.
실제 AWS/ROSA/Harbor Runtime·자격증명·리소스 쓰기·유료 생성·Apply/Merge는 수행하지 않았다. Freeze HOLD 유지.

## 수정 전 재현과 수정 후 결과
| 결함 | 수정 전 실제 offline 결과 | 수정 |
|---|---|---|
| 잘못된 identity 형식 | list identity/non-string ARN에서 AttributeError2개 | 명시적 STOP, STS1회 후 추가 AWS호출0 |
| RC0 malformed/scalar JSON | 두경로가 COMPLETE/RC0로 오판정 | 원래 AWS RC0/원문 bytes 유지, INVALID_RESPONSES 및 PARTIAL/RC2 |
| timeout partial raw | partial stdout 유실 | TimeoutExpired.stdout/stderr 보존, RC124 및 부분실패 |

수정 전11개: 정상6 / 실패3 / 예외2. 수정 후11개: PASS11, RC0.
AWS 명령목록·account/role/member·출력경로·조회 범위·권한은 확대하지 않았다. JSON object/list format 검사는 actual 응답 값/서비스 schema·readiness 평가가 아니다. 예: quota조회{}도 format은 valid이며 값의완전성은 별도 수신 심사 대상이다.
AWS write/ROSA 호출 또는 credential 수집을 추가하지 않았다.

## 로컬 시험 범위와 재현
환경: Windows 실행환경의 bundled Python3.12 + Git Bash/OpenSSL3.5.6. AWS subprocess는 unittest.mock으로 전부 대체했다.
[offline 시험 파일](../runbooks/test_phase2_readiness_capture.py), [collector](../runbooks/phase2-readiness-capture.py).
동일 디렉터리에서 `python3 test_phase2_readiness_capture.py`. 실제 AWS를 호출하지 않는다.
11개는 정상수집/manifest size·hash, 고정read목록, root/다른account/미승인member, identity list/ARN integer, GetRoledenied, malformedJSON/nullJSON, timeout부분원문을 포함한다.
AST parse PASS. AWS CLI 실제 설치/서비스 query·권한/계정상태 검증은 NOT_RUN.
이번 수정으로 과거 source의 independent review가 새 코드를 승인한 것으로 취급하지 않는다.

## Harbor read-only intake 검증
[현장 절차](../runbooks/20261004-harbor-d22-readonly-intake.md)의 Bash 블록을 추출해 `bash -n` RC0을 확인했다.
5경로: 정상RC0, TLS실패RC3, timeoutRC3, expiry실패RC4, Root파일hash불일치RC2.
TLS·x509 실행은 openssl mock wrapper, 인증서는 이미 확보한 공개Root를 testfixture로 사용했다. 정상경로 SHA256SUMS 생성, 잘못된Root에서 수집디렉터리 미생성, 모든 수집파일에 mock session-material sentinel 미잔존을 확인했다.
현장 script 자체의 명령·설정은 변경하지 않았다. local mock은 CA경로·출력디렉터리만 test경로로 치환했고 실제host/OpenSSLhandshake·leaf/SAN검증·OStrust·Robot/이미지 pull은 수행하지 않았다.
Git Bash hostname은 Linux `hostname -s` 동작과 달라 context hostfield까지 현장 인수됐다고 주장하지 않는다. mock 실행기의 Windows path·UTF8 설정 실패를 보정한 뒤 최종5경로를 통과했다. 이를 현장 코드결함이나 실제TLS실패로 기록하지 않는다.

## 문서·입력 정합성
최초HEAD의 변경14파일을 immutable ref로 읽었다. 저장소 recursive tree(truncated=false) 기준 상대 Markdown link14개의 대상존재를 확인했고 missing0. 외부링크·anchor내용·변경하지 않은 전파일의 정합성까지 검사한 것은 아니다.
CA JSON은 기존 공개 CERTIFICATE-only 입력을 유지했다. D22 field actual PENDING, 기존 P1자원기준 승인과 새ROSA capacity gate, #110 공급망선택 승인과 actual Delivery완료의 구분은 유지한다.
수집 runbook의 source-ref를 수정 collector commit으로 변경했다. 과거 f140ddcda... 실행본을 이번 hardened source라고 혼용하지 않는다.

## 잔여와 다음 실행
| 독립적으로 준비한 것 | 외부입력이 필요한 것 |
|---|---|
| collector 오류 수정·offline회귀 | code/mixed independent review 후 담당1인의 실제AWS조회 |
| Harbor Bash문법·실패경로 mock | 하영 current leaf/Robotmetadata 및 OS/currentCI trust 관측 |
| 기존 CA/digest/resource·결정 연결 | 재환/CI/HBR 최종 build-scan-push remote digest 승인 연결 |
| 비용정보 수신 항목 정의 | 사용자10-06부터 한도·통화·기간·누적·집계시각 텍스트 |

이번 결과를 STATIC/MOCK scope로 PR8에 인계한다. 독립 code review PENDING, CI여부는 최종HEAD 조회결과로 별도 기록한다. 현장임의접속·credential요청·기존P1타세션Runtime중복·티켓AC/담당/일정 변경은 수행하지 않는다.

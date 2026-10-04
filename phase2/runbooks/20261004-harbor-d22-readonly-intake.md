# D22 現場 read-only 입력 수집 및 승인 연결
기준: 2026-10-04 KST. AI: CODEX_ASSISTED.
상태: RUNBOOK_DRAFT / FIELD_EXECUTION=NOT_RUN / D22_FINAL=PENDING.
대상: [D22 계약 후보](../reviews/20261004-harbor-d22-input-contract.md). Phase1 타 세션 Runtime 작업을 재실행하지 않는다.

## 1. 기존 결정과 남은 검증
| 구분 | 확보한 근거 | 이번 필요 결과 |
|---|---|---|
| TLS 설계 | D19 #64 설계 승인; 공개 Root 확보·hash 대조 | 현재 Harbor leaf/SAN/chain/expiry; Runner OS/current runtime 범위 구분 |
| Robot 정책 | #13 finite30days 및 Lead50일 철회·rotation 계획 | 실제 principal/project/access/disabled/expiry 관측. 새 P2 principal 발급은 별도 결정 |
| 이미지 공급망 | #110 DEC01~04 승인/Done, Wolfi apko Python3.13·source merge | 최종 on-prem build/scan→push→registry digest→배포 승인 연결 |
| 기존 앱 자원 | #15 comment5910524397: 현재 a7093136/5e2a081c 기준 baseline 확정 | 현재 spec/새 이미지 회귀·ROSA platform/allocatable/N-1·surge 별도 |

공급망 결정이 미승인이라서 작업이 막혀 있다는 표현은 사용하지 않는다. Source/Decision 승인과 최종 registry manifest/P2 승인은 별도다. #110의 P1 signed attestation 플랫폼 제약 및 P2/별도 Decision 인계도 유지하며 이번에 이미지 서명 강제를 신설하지 않는다.

## 2. 실행 위치·전제
- TLS 수집: 기존 승인 client인 control01 또는 cicd-runner01. 작업자가 이미 가진 로그인 범위에서 수행한다. 아래 명령은 Linux Bash/OpenSSL3·coreutils/awk이며 Windows PowerShell에 직접 붙이지 않는다.
- 현재 이 assistant 세션에는 해당 host의 SSH 실행 경로/인증이 제공되지 않았다. 아래 host 명령은 작성만 했고 실제 실행·실제 leaf 확보는 하지 않았다.
- PKI 공개 Root PEM을 안전하게 로컬 파일로 준비한다. [pinned 공개 Root](https://github.com/321Team/fds-project-evidence/blob/51b0bac5b8558fce2b34103d5737f2c8c66dfbdb/evidence/P1-MON-01/monitor01-pki-20260919/fds-root-ca.crt). 아래 D22_CA는 그 공개 파일의 실제 절대 경로로 지정한다.
- Root 파일 SHA256 예상값: 20ddfa5e92c346aaf46fc30179fbc0b069e256effd2615a9f4308a8fe719053f. 다른 파일이면 TLS 수집 STOP.
- 설치·trust 갱신·Robot 발급/회전·secret 조회·pull/push·Kubernetes create/apply·firewall 변경은 이 수집 범위 밖이다. 기존 타 세션 적용창과 중복 실행하지 않는다.

## 3. public leaf 수집 — 고정 CA/고정 목적지
실행 전에 D22_CA만 실제 공개 Root 파일 절대경로로 바꾼다. env 전체·auth 파일을 출력하지 않는다.
```bash
(
set -u
umask 077
D22_CA='/actual/absolute/path/fds-root-ca.crt'
test -f "$D22_CA" || { echo 'STOP: public Root file missing'; exit 2; }
d22_expected='20ddfa5e92c346aaf46fc30179fbc0b069e256effd2615a9f4308a8fe719053f'
d22_actual="$(sha256sum "$D22_CA")" || exit 2
d22_actual="${d22_actual%% *}"
test "$d22_actual" = "$d22_expected" || { echo 'STOP: Root file hash mismatch'; exit 2; }
for d22_tool in openssl timeout awk sha256sum mktemp; do
  command -v "$d22_tool" >/dev/null || { echo "STOP: missing $d22_tool"; exit 2; }
done
d22_out="$(mktemp -d "$HOME/d22-harbor-ro-XXXXXXXX")" || exit 2
{
  TZ=Asia/Seoul date --iso-8601=seconds
  hostname -s
  id -un
  openssl version
  printf 'ROOT_PEM_SHA256=%s\n' "$d22_actual"
} > "$d22_out/context.txt"

# stdout은 공개 CERTIFICATE 블록만 저장한다.
# s_client의 session/keying-material 상세 stdout을 raw 파일로 저장하지 않는다.
timeout 20s openssl s_client -connect 10.1.93.54:443 \
  -servername harbor.fds.internal -verify_hostname harbor.fds.internal \
  -verify_return_error -CAfile "$D22_CA" -showcerts -no_ticket \
  </dev/null 2>"$d22_out/tls-diagnostics.txt" |
  awk '/-----BEGIN CERTIFICATE-----/{keep=1} keep{print} /-----END CERTIFICATE-----/{keep=0}' \
  > "$d22_out/server-chain.pem"
d22_pipeline=("${PIPESTATUS[@]}")
printf 'TLS_RC=%s\nFILTER_RC=%s\n' "${d22_pipeline[0]}" "${d22_pipeline[1]}" > "$d22_out/status.txt"
if test "${d22_pipeline[0]}" -ne 0 || test "${d22_pipeline[1]}" -ne 0; then
  printf 'STOP: TLS failed; preserve results at %s\n' "$d22_out"
  exit 3
fi
awk '/-----BEGIN CERTIFICATE-----/{keep=1} keep{print} /-----END CERTIFICATE-----/{exit}' \
  "$d22_out/server-chain.pem" > "$d22_out/leaf.pem"
openssl x509 -in "$d22_out/leaf.pem" -noout -subject -issuer -serial -dates \
  -fingerprint -sha256 -ext subjectAltName > "$d22_out/leaf-metadata.txt" || exit 4
openssl x509 -in "$d22_out/leaf.pem" -checkend 0 -noout > "$d22_out/expiry-check.txt" 2>&1 || exit 4
(
cd "$d22_out" || exit 4
sha256sum context.txt status.txt server-chain.pem leaf.pem leaf-metadata.txt \
  expiry-check.txt tls-diagnostics.txt > SHA256SUMS
) || exit 4
printf 'READONLY_CAPTURE=%s\nSTATE=CAPTURED_REVIEW_REQUIRED\n' "$d22_out"
)
```

정상 수집: TLS_RC0/FILTER_RC0, leaf 파싱·현재 유효성 성공, SAN에 harbor.fds.internal, 예상 Root로 이름/chain 검증 성공. 이는 **고정 CA를 명시한 endpoint TLS** 범위이며 OS 기본 trust/Podman/runtime 로그인·cold-pull PASS가 아니다.
미응답/timeout/검증실패는 RC·진단을 보존하고 PENDING/FAIL 원인을 분류한다. insecure/HTTP·hostname bypass로 재시도하지 않는다. 파일은 현장 개인 디렉터리에 보존하고 리뷰 후 공개 인증서/필요한 diagnostics만 인계한다. 오류로 checksum 생성 전 중단되면 해당 디렉터리를 같은 방식으로 로컬 해시해 실패 증적을 보존한다.

## 4. Runner OS trust 및 IP/FQDN 계약
별도 OS trust 읽기 전용 검증은 같은 OpenSSL client에서 CAfile 인자 없이 수행하되, 이 프로세스가 환경 CA 설정을 사용했는지와 OS default paths를 확인해 기록한다. 임의 SSL_CERT_FILE/SSL_CERT_DIR을 설정하거나 전체 env를 덤프하지 않는다. 결과를 단순 OS 전체 PASS로 확대하지 않는다.
P1 endpoint10.1.93.54와 P2 후보harbor.fds.internal은 이름·runtime certs.d key·auth registry key가 다르다. 위 FQDN 검사 성공으로 기존 IP 소비 경로를 전환하지 않는다. IP 검증이 필요하면 별도 approved IP client 수집에서 verify_ip10.1.93.54/noservername으로 기록한다.
Podman OS/registry trust 상세는 #13의 기존 실행 증적을 우선 소비하고, D19 full consumer 검증은 담당 runbook으로 수행한다. 본 read-only 준비에서 login/pull을 반복하지 않는다.

## 5. Robot 필드만 전달 — HBR Lead 기존 UI 세션
Harbor2.13.1의 기존 승인 UI에서 Account/Project Robot metadata를 읽어 아래 필드만 수기 기록한다. 관리자 비밀번호/Robot secret을 전달하거나 새 API 토큰을 발급할 필요가 없다.
토큰/secret export·refresh·rotation·account edit·delete를 누르지 않는다. 전체 JSON/API 응답·HAR·cookie·auth header·Secret 화면은 수집하지 않는다.

| 필드 | 기록값 |
|---|---|
| observed_at_kst / observer / installed_version | 실제 조회값 |
| project / principal / enabled 또는 disabled | 실제 조회값 |
| create time / expiry / duration 표시 | 화면 실제값·timezone, 30일 정책과 대조 |
| exact access list | resource/action별 actual; pull-only와 push+pull 분리 |
| consumer reference | namespace/SA/secret 이름 또는 Runner 승인 reference; 비밀 원문 제외 |
| rotation | 계획/완료/미실행을 구분, 새 principal·구 credential 회수 증적 reference |
| result | current metadata OBSERVED / authorization/runtime NOT_TESTED 등 |

만료 후 credential positive/negative를 이 read-only 단계에서 시험하지 않는다. 기존 #13 rotation 계획(10-12~13)을 P2 신규 계정 발급 일정으로 바꾸지 않는다.

## 6. 최종 APP 이미지 승인 연결 — 재환/CI·HBR 입력
| 대상 | 필요한 연결 |
|---|---|
| source | 실제 build의 approved app SHA 및 독립 code review/merge |
| build | Runner run ID·job·원본 manifest·source/supply pin |
| scan | exact image identity·Trivy DB 관측시각/identity·HIGH/CRITICAL 결과, 승인 예외가 있다면 CVE/digest/expiry/approver |
| registry | fds/repository + remote digest/media type/platform; local config ID·archive SHA와 구분 |
| release | 배포 manifest image@digest·APP/Delivery handoff 승인·이전 rollback digest |
| P2 | 선택 namespace/SA·arbitrary UID actual 시험·D22 logical/Final 결정 |

P1 관측 a7093136/5e2a081c는 9/30 Resource baseline의 승인 시험 대상이다. #110은 당시 운영 python3.12의 HIGH44로 공급망 전환을 선택했다. HIGH44를 두 digest 각각의 현재 scan 결과로 단정하지 않는다. 두 digest의 P2 보안 적합성은 신규 최종 scan/source lineage로 판단한다.
이미지 build/scan/Push는 #13/#16 기존 Delivery 작업에서 나온 결과를 소비한다. 이 세션에서 중복 Delivery를 시작하지 않는다.

## 7. 인수·중단·복구
모든 결과에 KST/host/observer/source ref·RC·공개 PEM 파일hash/DER지문·원본 hash/size를 연결한다. local 해시는 바이트 무결성이며 independent review나 actual truth 전체 검증이 아니다.
read-only 수집 실패 시 설정을 바꾸지 않고 실패 결과·미확인 범위를 보존한다. 이번 수집에는 서버 rollback 대상 변경이 없다. 개인 디렉터리는 결과 인수 후 현장 보존 정책으로 정리하고, 공유 경로/시스템 인증서/운영 파일을 삭제하지 않는다.
D22 입력 수용=#42 Lead, Code/mixed PR 및 모든 evidence PR 독립 리뷰는 기존 governance 유지. live leaf/Robot metadata·final app digest 승인 연결 전 Final/P2 trust GO를 기록하지 않는다.

## 근거
- [D19 설계 #64](https://github.com/321Team/fds-project-baseline/issues/64), [Robot 계획](https://github.com/321Team/fds-project-baseline/issues/13#issuecomment-5927104283).
- [공급망 결정 확정](https://github.com/321Team/fds-project-baseline/issues/110#issuecomment-5856632297), [추가 조건 승인](https://github.com/321Team/fds-project-baseline/issues/110#issuecomment-5855626610).
- [기존 이미지 자원기준 확정](https://github.com/321Team/fds-project-baseline/issues/15#issuecomment-5910524397), [부하 기준 v2](https://github.com/321Team/fds-project-baseline/issues/15#issuecomment-5885861552).
- [OpenSSL3 s_client 공식](https://docs.openssl.org/3.0/man1/openssl-s_client/): verify_return_error·CAfile·hostname 및 showcerts 사용. showcerts 출력 자체는 검증된 chain이라는 뜻이 아니다.

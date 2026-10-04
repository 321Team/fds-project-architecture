# Harbor D22 입력 계약 후보
기준일: 2026-10-04 KST. revision 3: current leaf·Robot 현장 readback, source hash 대조 및 consumer rotation 검증 연결. AI: CODEX_ASSISTED.
상태: LOGICAL_CONTRACT=PROPOSED / D22_FINAL=PENDING / ROSA_RUNTIME=NOT_RUN / ARCHITECTURE_FREEZE=HOLD.
수정 전 architecture PR8 HEAD: e4131e4c6ccf0f7a735025c7c1dce5da8306eb1d.
#42 기존 일정·AC·담당을 변경하지 않는다. Final(10-15)은 #38 Basic Ready 이후 실제 route/TLS/credential/pull 증적으로 완성한다. 생성 전 logical 계약과 생성 후 actual 인수를 구분한다.

## 1. 현재 확보한 원본과 한계
| 입력 | 확인 근거 | 인정 범위 |
|---|---|---|
| Harbor 이름/주소 | infra-dns 5f7505f9613e4b94aedd4bcdaba52f2b3f1a5f19, zones/fds.internal.zone: harbor=10.1.93.54, db=10.1.93.55 | Git 원본. live DNS 응답/route 성공 아님 |
| CSR 이름 | infra-pki f8bded5c02b4497452da0a3117fc7e08aab8f9bb, pki/harbor-csr.cnf: CN harbor.fds.internal; SAN harbor.fds.internal/harbor01/10.1.93.54 | CSR 요청값. 현재 서버 leaf SAN/issuer/expiry/fingerprint 증명 아님 |
| Harbor 버전/기존 pull 계정 | baseline #14 comment5927832146: Harbor2.13.1, fds 프로젝트 robot$worker pull-only, Worker 범위 보고 | Phase1 보고. ROSA 권한 재사용·CP 허용·current metadata 확정 아님 |
| Robot 정책 | baseline #13 comment5659049448: finite30days, Never 미채택; scan 및 CRITICAL/HIGH 차단 | 기존 정책을 소비. 실제 계정 expiry/readback은 1.4 확보; rotation 완료 별도 |
| Phase1 allowlist source | infra-ansible PR63 badbe29440916ec3ec79da8fc81722c2e6c4e75b, OPEN | 소스 존재. merge/apply/실제443 허용 아님 |
| 현재 trust 상태 차이 | #16 comment5964396337은 TLS BLOCK 표기; #13 comment5947371286/5947598139는 10-02 Podman Push/Pull 성공 보고 | IF-09 시험 성공은 인정; Runner OS trust/current CI/CD/HCP trust는 별도 미검증. #16 표현 정합 필요 |
| 공개 CA/fingerprint | evidence main 51b0bac5b8558fce2b34103d5737f2c8c66dfbdb의 공개 Root PEM 확보·로컬 X509 파싱 및 hash 재계산 | 아래 1.1에 실제 값/후보 JSON. current Harbor leaf 검증·HCP 신뢰 수용은 PENDING |

#16의 Kubernetes TokenRequest audience 미고정은 deploy 인증 문제다. Harbor Robot scope와 동일한 인증항목으로 합치지 않는다. #13 AC03의 static/mock 성공도 P2 registry runtime 성공을 의미하지 않는다.

### 1.1 이번 실제 확보값과 소비 경계
검색 API 4건은 무결과였다. 이를 자료 부재로 판단하지 않고 main의 recursive tree(truncated=false)와 파일 원본으로 확인했다.
증적 기준 commit: `51b0bac5b8558fce2b34103d5737f2c8c66dfbdb`, fds-msa main: `5120b7df72d24ada3dbcf23fc0292fb58ae778af`.

**공개 Root CA 확보**
[Root PEM](https://github.com/321Team/fds-project-evidence/blob/51b0bac5b8558fce2b34103d5737f2c8c66dfbdb/evidence/P1-MON-01/monitor01-pki-20260919/fds-root-ca.crt), [동일 증적 README](https://github.com/321Team/fds-project-evidence/blob/51b0bac5b8558fce2b34103d5737f2c8c66dfbdb/evidence/P1-MON-01/monitor01-pki-20260919/README.md).
PEM blob: `0cfb3414d71c4501621e6c4aa6f72b29d317f355`.
- Subject/Issuer: `CN=FDS Project Root CA 2026, OU=Project PKI, O=FDS, C=KR`.
- Serial: `3F4570F7333F7601C592B1FF385204AB831559A5`.
- NotBefore/NotAfter UTC: `2026-09-15T02:45:04Z` / `2031-09-14T02:45:04Z`.
- PEM UTF-8 LF 파일 SHA256: `20ddfa5e92c346aaf46fc30179fbc0b069e256effd2615a9f4308a8fe719053f`.
- 인증서 DER SHA256 fingerprint: `6a75baf4dbe03ef24cce944e616384d318f7ca919cd7bd914624b4cebac06b10`.
Windows .NET X509 파싱·SHA256 계산 결과가 기존 README와 #13 승인 Root 파일 해시에 일치했다. current Harbor leaf 서명/chain 또는 HCP 지원·신뢰 승인까지 검증한 것은 아니다. 서로 다른 hash 형식을 혼용하지 않는다.

[HCP 공개 CA JSON 후보](../inputs/harbor-additional-trusted-ca.candidate.json)를 기존 공개 PEM에서 생성했다. key=`harbor.fds.internal`, value=확보한 PEM, 공개 CERTIFICATE 블록만 포함한다. secret/private key 없음. 실제 endpoint가 IP 이름으로 유지되면 이 FQDN key가 맞는지 별도 결정해야 한다. 기존 IP 인증 secret/Podman trust 경로를 FQDN으로 자동 전환하지 않는다. PKI 수용 + live leaf 검증 + exact HCP 지원 및 코드/설정 리뷰 전에 create/edit에 사용하지 않는다.

**Robot metadata/계획 확보**
[HBR Lead comment5927104283](https://github.com/321Team/fds-project-baseline/issues/13#issuecomment-5927104283): 50일 제안 철회, worker 10-16/push 10-18 만료 보고, 10-12~13 새30일 rotation 계획. 기존 consumer는 fds-app/monitoring-api/monitoring-node의 harbor-pull-secret3개와 Runner push 자격이다. 이 날짜는 Lead 보고/계획이다. actual expiry API readback은 1.4에 추가했으며 rotation 완료는 여전히 별도다.
[10-02 comment5947371286](https://github.com/321Team/fds-project-baseline/issues/13#issuecomment-5947371286): fds-app/harbor-pull-secret의 registry=`10.1.93.54`, principal=`robot$worker`, default SA imagePullSecrets 없음. P2 namespace/SA/principal 발급승인으로 재사용하지 않는다.

**관측된 P1 image digest 확보**
[10-02 HA 원본](https://github.com/321Team/fds-project-evidence/blob/51b0bac5b8558fce2b34103d5737f2c8c66dfbdb/evidence/P1-HA-01/received-20261002T0232Z/control01/ha22-20261002/pre-images.txt):
- `10.1.93.54/fds/transaction-api@sha256:a7093136d12640da00570c18ed278eacbb8e9ba3637c7d509571346eac45cc33`
- `10.1.93.54/fds/fds-engine@sha256:5e2a081cd51a957c3fad038b3eab07884c446ea3c2a814a905e3f41c24f67369`
이는 Pod spec image 참조 관측이며 registry remote manifest/imageID·scan·approved source lineage·P2 승격을 완결하지 못한다. 중앙 Delivery 신규 이미지 digest와 연결되기 전 approved P2 입력으로 사용하지 않는다.
IF-09 공식 시험 digest `7a3b263c938493c827d8295e64f23d9386ffcbea75516ea03a6b65196636bfc6`는 Alpine 시험 이미지이며 앱 이미지 대체물이 아니다. 공식 Run hbr-20261002-161052-d57ab5dc는 유지; 보조 Run을 공식으로 교체하지 않는다.

**trust 상태 정정**
10-02 HBR Lead AC02 PASS 및 보조 Run Push/Pull·wrong credential negative 성공 기록이 있으므로 Runner 모든 trust가 FAIL이라는 단정은 사용하지 않는다. 10-03 #16 BLOCK 표기와 scope 차이를 해소해야 한다. HBR Podman IF-09=보고 PASS, D19 OS+Runtime 전체/current CI/CD=미검증, ROSA=NOT_RUN. 이번에 actual live host 재시험은 수행하지 않았다.

### 1.2 승인 근거 후속 및 현장 수집
[D19 #64](https://github.com/321Team/fds-project-baseline/issues/64)는 TLS 설계 승인/Done이며 current leaf 설치·consumer trust actual 완료와 구분한다.
[#110 결정 확정](https://github.com/321Team/fds-project-baseline/issues/110#issuecomment-5856632297) 및 [Review Owner 추가조건 확인](https://github.com/321Team/fds-project-baseline/issues/110#issuecomment-5855626610)에서 Wolfi/apko Python3.13 공급망 선택과 구현 경계가 승인됐다. 이를 다시 결정승인 대기로 기록하지 않는다. 최종 on-prem Build/Scan/Harbor remote digest/배포·P2 승인은 아직 별도다.
기존 P1 두 digest는 [#15 9/30 resource baseline 확정](https://github.com/321Team/fds-project-baseline/issues/15#issuecomment-5910524397)의 시험 대상이며 두 앱 각3 replicas, container requests250m/256Mi·limits500m/512Mi다. 이 자원 승인은 P2 보안·arbitrary UID·N-1 capacity 승인과 같지 않다. #110의 당시 python3.12 HIGH44 보고를 각각의 digest에 대한 current scan이라고 단정하지 않는다.
#110의 10-05 전환 목표는 역사 기록이다. 최신 #15는 #52의 10-05 비근무 일정과 별도 날짜확인을 명시하므로 이번에 현장 실행일을 새로 확정하지 않는다.

[현장 read-only 수집 runbook](../runbooks/20261004-harbor-d22-readonly-intake.md)에 current public leaf/chain·metadata 수집 명령, Robot UI 필드-only 인계, 최종 build/scan/digest 승인 연결표와 실패 중단 기준을 준비했다. 현 세션에는 현장 host SSH/인증 경로가 없어 actual 명령 실행은 NOT_RUN이다. 기존 P1 타 세션 Runtime과 별도로 조회 결과를 소비하며 변경·재시험을 중복하지 않는다.

### 1.3 current Harbor leaf 현장 readback — 2026-10-04
사용자 제공 터미널 출력, 관측시각 **2026-10-04T15:37:03+09:00**.
host=cicd-runner01, user=server01_cicd-runner, OpenSSL3.5.8 (library3.5.8).
실제 실행은 대화 제공본: child Bash+if, CA 실제 경로/가독성 확인·도구 사전 검사, capture 경로 조기 출력 보정. source 전체파일 hash는 미수신이므로 PR8의 원문 그대로 실행했다고 단정하지 않는다.

| 항목 | 실제 제공값/판정 범위 |
|---|---|
| capture path | /home/server01_cicd-runner/d22-harbor-ro-34OMzIfp |
| 명시한 Root PEM | /home/server01_cicd-runner/.config/containers/certs.d/10.1.93.54/ca.crt |
| Root 파일 SHA256 | 20ddfa5e92c346aaf46fc30179fbc0b069e256effd2615a9f4308a8fe719053f, 기대값 일치 |
| TLS/FILTER RC | 0 / 0; fixed IP10.1.93.54:443에 SNI 및 verify_hostname=harbor.fds.internal, verify_return_error + 지정Root 사용 |
| Subject | C=KR, O=FDS, OU=Harbor, CN=harbor.fds.internal |
| Issuer | C=KR, O=FDS, OU=Project PKI, CN=FDS Project Root CA2026 |
| Leaf serial | 1000 (OpenSSL hex 표기) |
| 유효기간 UTC | 2026-09-15 04:00:08 ~ 2027-09-15 04:00:08 |
| Leaf DER SHA256 지문 | 61617af3574f37c70a2d9c7f284a75f82c844ae3eaf599cb3d0ec649126ebeaf |
| SAN | DNS harbor.fds.internal / DNS harbor01 / IP10.1.93.54 |
| 현장 무결성 | SHA256SUMS에 포함된 context/status/server-chain/leaf/metadata/expiry/diagnostics 7개 모두 성공 |
| 추가 출력 | Certificate will not expire; D22_RESULT_READBACK=OK |

판정: **PINNED_CA_FQDN_TLS=PASS_USER_READBACK / FIELD_SHA256_CHECK=PASS_7_USER_READBACK**.
이는 제공된 명령/출력 범위의 정상 CA·이름·chain 및 현재 유효성 검사다. IP 직접검증은 별도 -verify_ip 실행을 하지 않았으므로 SAN 존재만 인정한다. fixed IP 접속이라 DNS resolution 성공 증적도 아니다.
원본 PEM/diagnostics/SHA256SUMS 전체파일의 수신 및 assistant 재해시·독립 evidence 리뷰는 **PENDING**. 사용자 제공 출력의 현장 hash 성공과 원본 직접검증을 구분한다.
OS 기본 trust, Podman current login/pull, Robot 실제 인증/rotation, ROSA worker trust/cold-pull, 최종 APP approved digest는 별도 잔여다. Robot 권한·만료 metadata 후속 관측은 1.4에 기록한다. D22 Final/Freeze 및 P1 AC 전체를 PASS로 승격하지 않는다.

### 1.4 Robot API 현장 readback 및 rotation 연결 — 2026-10-04
관측시각 **2026-10-04T16:36:20.591261+09:00**, 실행 host/user는 사용자 터미널 기준 cicd-runner01 / server01_cicd-runner.
사용자가 기존 admin 계정으로 GET `https://10.1.93.54/api/v2.0/robots` 조회를 수행했다. admin 비밀번호·Robot secret은 이 문서에 포함하지 않는다.

| 항목 | robot$worker | robot$push |
|---|---|---|
| id / level | 2 / system | 3 / system |
| disable | false | false |
| permission kind / namespace | project / fds | project / fds |
| repository actions | pull | push, pull |
| effect | null | 두 action 모두 null |
| duration | 30 | 30 |
| expires_at (API integer) | 1792137757 | 1792311415 |
| expires_at KST | 2026-10-16 17:02:37+09:00 | 2026-10-18 17:16:55+09:00 |

system 수준 계정이지만 출력된 permission은 fds 프로젝트 범위다. effect=null은 collector가 API 필드 부재/null을 그대로 표현한 것으로 allow/deny를 새로 추론하지 않는다. duration=30 및 expiry는 기존 정책·Lead 보고와 부합하지만 실제 rotation 완료를 입증하지 않는다.

추적·무결성:
- [실행 스크립트 고정 버전](https://github.com/321Team/fds-project-architecture/blob/d866d324721634b1ebee7556e3bedf952a6914fe/phase2/runbooks/harbor-robot-readonly.py), [실행 절차](../runbooks/20261004-harbor-robot-readonly.md).
- 출력 script_sha256=`62c3c8c806c1426f4a369028dad94040c4a444d08d1fcde0d853be0bedf37c42`. assistant가 GitHub 지정 버전 UTF-8 원문 SHA256을 재계산해 일치를 확인했다. 이는 보고된 source hash 대조이며 현장 실행파일 직접 수신 검증과 구분한다.
- root_pem_sha256=`20ddfa5e92c346aaf46fc30179fbc0b069e256effd2615a9f4308a8fe719053f`.
- capture=`/home/server01_cicd-runner/d22-robot-ro-tk4okf2d`.
- state=CAPTURED_REVIEW_REQUIRED, missing_or_not_visible=[], D22_ROBOT_EXIT_CODE=0.
- 사용자 후속 출력: `sha256sum -c SHA256SUMS` → `robot-metadata.json: 성공`, `D22_ROBOT_CHECKSUM=OK` (2026-10-04 16:43 KST 대화 수신; 검사 자체 타임스탬프는 미제공).
- 첨부 robot-metadata.json / SHA256SUMS는 assistant 다운로드 접근 오류로 직접 읽기·재해시하지 못했다. JSON 원본 파일 hash 값/size는 미확보이며 대화 JSON 재구성을 원본 파일로 취급하지 않는다.

판정: **ROBOT_METADATA=PASS_USER_READBACK / FIELD_SHA256_CHECK=PASS_USER_READBACK / REPORTED_SOURCE_HASH=MATCH_PINNED_SOURCE / RAW_INDEPENDENT_REHASH=PENDING**.
고정 IP에 대한 pinned CA HTTPS 성공은 이 스크립트/출력 범위의 IP 이름·chain 검증을 지지한다. DNS/OS default trust/Robot 자체 인증 및 Worker push 거부/ROSA 인수까지 확대하지 않는다. 추가 API 재수집은 현재 입력 정리에 필요하지 않다.

### 1.5 기존 rotation 계획과 consumer별 실행·검증 연결
[Lead 계획](https://github.com/321Team/fds-project-baseline/issues/13#issuecomment-5927104283)을 2026-10-04 재조회했다. **10-12~10-13은 기존 일정(안)**이며 새 확정 일정으로 바꾸지 않는다. 아래는 해당 계획을 소비하는 검증 절차 제안이며 실제 재발급·Secret 갱신·회수는 수행하지 않았다.

| 기존 consumer | 갱신 대상 | 실행 전 확인 / 완료 증적 |
|---|---|---|
| fds-app | harbor-pull-secret / worker 자격 | 실제 workload SA·imagePullSecrets 참조 확인; 새 자격 갱신 후 승인 digest 시험 Pod pull·Ready와 node/시각/RC |
| monitoring-api | harbor-pull-secret / worker 자격 | 실제 소비 workload·SA 확인; 해당 namespace 새 자격으로 승인 digest pull·Ready |
| monitoring-node | harbor-pull-secret / worker 자격 | 실제 소비 workload·SA 확인; 해당 namespace 새 자격으로 승인 digest pull·Ready |
| Runner | robot$push 자격 | 실제 CI/Podman credential 보관·참조 위치를 값 없이 확인; 새 자격으로 승인 시험 repository push 및 같은 digest pull |

1. 기존 HBR/consumer 담당과 실행창을 확정하고, 위 네 consumer의 실제 참조와 안전 채널을 확인한다. Runner credential 경로 및 monitoring SA는 현재 관측되지 않았으므로 추측해 고정하지 않는다.
2. 기존 30일 기준으로 재발급하고, 새 principal/id·duration·expiry·permission metadata 및 비밀값 없는 승인된 credential 식별정보를 남긴다. 파일 checksum과 credential fingerprint는 서로 다른 증적으로 취급한다.
3. consumer를 갱신하고 각 consumer가 **새 credential**을 사용했는지 결속한다. 기존 Running Pod 생존만으로 pull 성공을 인정하지 않는다. worker pull 및 push 거부, Runner push/pull은 기존 승인 시험 절차와 연결한다.
4. 전체 consumer 성공 확인 후 이전 credential의 사용 불가/회수 상태와 임시 시험 자원 정리를 기록한다. 동일 계정 secret 재발급이 이전 secret을 즉시 무효화할 수 있으므로 중첩 유효기간을 가정하지 않는다.
5. 실패하면 다음 갱신/신규 rollout을 중단하고 정상 workload를 보존한다. 이전 자격의 유효성이 확인될 때만 복원을 사용하며, 이미 무효화됐다면 새 자격 복구·재배포 경로로 처리한다. 삭제·재발급 방식과 복구 절차는 실행 전 담당자가 확정한다.
6. 기존 #13 AC-06에 실행시각/대상/metadata/시험결과/hash/리뷰를 연결한다. admin 비밀번호 회전은 [기존 범위 결정](https://github.com/321Team/fds-project-baseline/issues/13#issuecomment-5926234788)에 따라 비차단 후속이며 이번 작업에 새 필수조건으로 추가하지 않는다.

현재 **ROTATION=NOT_VERIFIED / CONSUMER_REFRESH=NOT_VERIFIED / P2_PRINCIPAL_DECISION=PENDING**.
기존 P1 principal의 P2 공유나 새 계정 발급을 이 관측 기록으로 승인하지 않는다.

## 2. D22 필수 12개 입력
| # | 계약 후보/채울 값 | 현재 상태·담당 입력 |
|---:|---|---|
| 1 | 기존 On-Prem Harbor primary 조건부 재사용 | 권욱 #42 Lead 결정 PENDING |
| 2 | harbor.fds.internal:443 / fds / 앱별 repository; exact repo 목록은 portable base 및 approved image 연결 | 이름·프로젝트는 P1 근거 있음; P1 앱 repository/digest는 1.1 확보; P2 approved 목록 재환/권욱 PENDING |
| 3 | Runner push와 ROSA worker pull principal 분리. P2 전용 project pull-only Robot 제안; 기존 robot$worker 공유 자동승인 금지. Push principal은 필요한 project push+pull만 | 기존 principal actual metadata는 1.4 PASS_USER_READBACK; rotation 검증 연결은 1.5. P2 책임·principal 결정 PENDING |
| 4 | 검토된 공개 issuing/root CA bundle, hostname→PEM JSON을 HCP additional trusted CA 입력으로 고정; leaf 이름/chain/만료 검증 | 공개 Root/hash·JSON 후보 확보; current leaf는1.3 PASS_USER_READBACK. 원본 intake·exact HCP 지원·P2 trust 수용 PENDING |
| 5 | approved scan/provenance와 동일 image@sha256 digest 배포. mutable tag만으로 승인/rollback 금지; index와 architecture별 manifest 구분 | 재환 APP exact digest/scan/lineage PENDING |
| 6 | Runner10.250.10.20→Harbor10.1.93.54 TCP443, host/Podman 각 trust 및 push 인증 확인 | HBR Podman IF09 보고 PASS; OS/current CI/CD 및 allowlist readback 하영 PENDING |
| 7 | 각 승인 ROSA worker actual node-pull source→Harbor443, VPN/FORWARD/return 및 HCP node trust | #38 inventory, #37 transport, #42 Harbor 소비; 생성 전 tuple 규칙/생성 후 IP 증적 |
| 8 | 신규 pull 실패 시 새 rollout STOP. 이미 실행 중 정상 workload/이전 approved digest 보존. cloud mirror는 별도 승인·동일 digest·접속/인증 증적이 있을 때만 후보 | 자동 failover/새 cloud registry 생성 승인 없음 |
| 9 | 이미지 크기×노드/캐시 미스/교체 횟수, hybrid transfer 및 선택 mirror storage/egress; 고정/변동 비용 분리 | 금액 입력은 사용자 10-06부터 텍스트 제공; 한도/잔여/기간 미확인 HOLD |
| 10 | 비밀은 승인 secret store/reference만 기록. namespace/SA imagePullSecret 범위, 만료·회수·rotation 및 담당. 전역 pull-secret 변경은 필요성 별도 판단 | P1 principal metadata는 1.4 확보; consumer 연결은 1.5. 실제 SA/보관 reference 및 P2 입력 PENDING; token/private key 원문 Git 금지 |
| 11 | source SHA + raw 관측 KST/환경/RC + sanitized 결과 + raw hash/size + 시험ID + 독립 evidence review 연결 | leaf/Robot은 1.3~1.4 USER_READBACK 확보; raw 독립 재해시·evidence 리뷰 및 P2 actual 인수 PENDING |
| 12 | logical 선택/전제 수용 → Basic Ready 이후 Final GO/NO_GO 기록. 이후 실제 cold-pull/실패·복구 인수 상태 별도 | #42 Lead 판정 PENDING; 최종 성공·승인 미기록 |

P2 전용 Robot은 신규 제안이며 기존 P1 계정을 폐기하거나 즉시 발급하라는 지시가 아니다. finite30days 정책을 유지하되 실제 expiry와 시험/운영기간의 충돌은 만료 전 rotation·검증·회수 일정으로 해결한다. Robot에는 관리권한을 부여하지 않는다. Robot token의 최초 전달/갱신은 비밀 채널로 수행하고 이 문서에는 principal metadata와 reference만 남긴다.

## 3. 경로와 trust의 분리
- Harbor host 설치/복구/leaf key·CSR 및 Worker 입력은 기존 하영 책임, CA signing/trust·Runner 입력은 기존 권욱 책임을 소비한다. #42 source adapter 제안은 Harbor host 기존 운영 담당을 바꾸지 않는다.
- source reconciliation 후보와 연결하되 DB5432와 Harbor443 actor/port tuple은 별도다. node의 kubelet/runtime pull은 Pod 내부 egress 시험/NetworkPolicy PASS만으로 입증할 수 없다.
- fds.internal outbound DNS→10.1.93.52/53 계약은 [양방향 DNS 후보](20261004-private-management-bidirectional-dns-contract.md)를 소비한다. DNS source 레코드만으로 ROSA live lookup 성공을 선언하지 않는다.
- leaf SAN/chain/current expiry 및 신뢰할 CA fingerprint를 실제 관측해 source와 대조한다. self-signed 우회, insecure registry, TLS 검증 생략 금지.
- ROSA HCP 공식 additional trusted CA 입력은 hostname을 key, 공개 PEM을 value로 하는 JSON이다. 지원 exact version/CLI 입력을 하영이 고정한다. 생성 전에 준비하며, 생성 후 registry 설정 변경은 전체 machine pool node rollout을 유발할 수 있어 PDB/용량/source 갱신/허용창을 포함한 별도 변경으로 취급한다.
- registry allowed/blocked 설정을 추가할 경우 공식 플랫폼 payload registry를 보존하고 지원 제약을 확인한다. Harbor만 허용하여 플랫폼 pull을 막는 후보를 승인값으로 만들지 않는다.

## 4. 실제 인수 계획
| 시험 | 필요한 실제 증적 | 판정 |
|---|---|---|
| DNS/route | ROSA worker 이름응답, 실제 node-source, VPN·양 gateway·Harbor return/443 허용 readback | source 미분류/비대칭/잘못된 DNS면 STOP |
| TLS | Runner host/Podman 및 ROSA node pull에서 이름·chain 검증; 공개 CA/leaf fingerprint·expiry | 각각 성공 필요; curl만 성공은 pull PASS 아님 |
| 인증 | P2 pull-only 성공, 승인 테스트 repository에서 push 권한 부재; Runner 최소 push scope | 앱 namespace/SA secret 범위와 expiry 확인; 운영 태그 변경 금지 |
| Cold pull | 승인 namespace에서 approved digest 신규 시험 Pod, imagePullPolicy Always + 실제 registry request/필요 layer 다운로드 또는 해당 digest 없는 승인 신규 worker 관측 | Always/Event만으로 캐시 미스 증명 금지. 공용 node image 삭제/drain 금지 |
| 업무 | 같은 digest의 arbitrary UID 실제 Running/Ready, API→engine→DB 기대 결과 | admission/HTTP200만으로 무결성 PASS 금지 |
| 부정/복구 | 분리된 시험 namespace/SA의 잘못된 credential 등 승인 실패조건, 신규 rollout STOP, 복구 후 같은 digest pull/업무 재확인 | cluster 전역 credential/운영 secret 변경 금지; 사전 허용창·cleanup |
| 교체/장애 | worker replacement source reconciliation 후 새 cold-pull; Relay outage/DNS 영향 및 복구 순서 | cached image 생존을 cold-pull/HA 성공으로 인정하지 않음 |

cloud mirror를 선택한다면 digest 보존을 직접 확인한다. registry의 index/manifest 변환이나 재빌드로 digest가 바뀌면 동등 이미지라고 선언하지 말고 새 scan/lineage/승인을 받는다. mirror 구축·replication·비용은 현재 승인/구현된 상태가 아니다.

## 5. 결정·리뷰·실행 권위
#42 권욱 Lead가 D22 선택 및 Runtime/인수 판정을 기록한다. 논리 문서 판단을 매번 별도 독립 승인해야 한다는 새 규칙을 만들지 않는다.
infra-pki POLICY의 Code/mixed PR 독립 리뷰와 fds-project-evidence 모든 PR 독립 리뷰는 유지한다. 자신의 코드/증적을 스스로 독립 승인하지 않는다. PR8은 기존 코드가 포함된 mixed 변경이므로 최신 범위의 독립 리뷰가 여전히 PENDING이다.
#42 logical 입력 수용, 구현 PR 독립 리뷰, Final GO/NO_GO, 실제 시험 및 evidence 리뷰를 서로 다른 상태로 남긴다. 최종 일정/AC를 앞당기거나 P1 4/4 요구를 축소하지 않는다.

즉시 인계할 입력:
- 권욱: 확보한 공개 CA bundle/fingerprint의 P2 trust 수용 및 secret reference·P2 Robot 분리/권한/rotation 제안 수용 여부, D22 logical 선택.
- 하영: live Harbor leaf/Robot metadata·Runner OS/current CI/CD trust 증적 정합, exact HCP CA 입력 지원, node-pull source/용량·rollout 제약.
- 재환: approved app repo/digest·scan/lineage·namespace/SA 및 portable base 소비 계약.
- 금액 수신 후: 통화/한도/기간/누적/집계시각을 비용표에 연결하고 total-to-complete/허용시간 재산정.

STATIC=원본·역할·상태 대조. CI=해당 신규 문서 실행 미수행. FIELD_READONLY=USER_READBACK (1.3~1.4), ASSISTANT_RUNTIME/APPLY/MERGE=NOT_RUN. 실제 값 없이 Final/Freeze GO로 승격하지 않는다.

## 6. 근거
- [D22 #42](https://github.com/321Team/fds-project-baseline/issues/42), [P1 Harbor #13](https://github.com/321Team/fds-project-baseline/issues/13), [finite30days 결정](https://github.com/321Team/fds-project-baseline/issues/13#issuecomment-5659049448).
- [P1 Harbor 입력](https://github.com/321Team/fds-project-baseline/issues/14#issuecomment-5927832146), [CI/CD runtime 장애](https://github.com/321Team/fds-project-baseline/issues/16#issuecomment-5964396337), [allowlist PR63](https://github.com/321Team/infra-ansible/pull/63).
- [DNS pinned source](https://github.com/321Team/infra-dns/blob/5f7505f9613e4b94aedd4bcdaba52f2b3f1a5f19/zones/fds.internal.zone), [CSR pinned source](https://github.com/321Team/infra-pki/blob/f8bded5c02b4497452da0a3117fc7e08aab8f9bb/pki/harbor-csr.cnf), [PKI governance](https://github.com/321Team/infra-pki/blob/f8bded5c02b4497452da0a3117fc7e08aab8f9bb/docs/POLICY.md).
- [Red Hat HCP registry CA/rollout](https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/images/image-configuration-hcp), [Harbor Robot scope](https://goharbor.io/docs/main/working-with-projects/project-configuration/create-robot-accounts/)（개념 참고; 설치2.13.1의 exact UI/API는 실제 확인）.

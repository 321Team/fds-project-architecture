# Phase 2 — 이권욱 AWS 콘솔 착수 및 개인 후속 작업
기준: 2026-10-03T16:11:40.539+09:00 KST. 연결된 #34/#35/#36/#40/#42 body+comments와 architecture PR8 HEAD53c41a1102a292eda61c02d79e4e34ee23135314 재조회.
상태: CONSOLE_HANDOFF_READY / 실제 AWS 조회·MFA 실행은 사용자 결과 수신 전 NOT VERIFIED / Architecture Freeze HOLD.
AI 사용: CODEX_ASSISTED. 이 파일은 실행 안내이며 개인 역할을 타인에게 재배정하거나 팀 공용 새 정책을 만들지 않는다.

## 1. 이번 실행 범위
이권욱은 현재 접근 가능한 AWS 콘솔에서 읽기 전용 입력을 확보한다. 본인 IAM MFA가 미등록이면 본인 자격증명 관리 권한 내에서 등록 가능(인프라 Create와 별개). 이미 등록된 MFA는 재등록/교체하지 않는다.
Codex는 수신 근거의 시각·계정·리전·범위·누락을 확인하고 기존 Issue/PR/Decision에 연결한다. 실제 콘솔을 조회하거나 실행했다고 먼저 표시하지 않는다.
AWS/ROSA paid resource Create/Apply는 Freeze/Cost GO 전 금지. 장기 Access Key 발급, 타인 MFA 대리 등록, Administrator 직접 부여, SCP 수정/우회, 유료 Support 변경·ROSA 구매/구독·약관 활성화는 이번 read-only 입력 수집에 포함하지 않는다.

## 2. 먼저 수행할 순서
로그인: 프로젝트 member account의 본인 IAM user/승인 role. root 세션이면 일반 작업을 멈추고 본인 계정으로 전환; root 통제는 외부 Owner 범위다.
Regional 화면은 Asia Pacific (Seoul) ap-northeast-2. IAM/Billing은 global 화면이므로 Seoul selector가 없다는 이유로 실패 처리하지 않는다.
첫 묶음은 M01~M03만. 기존 quota100은 증액 요청하지 않는다.

| ID | 콘솔 경로 | 확인 / 정상·제한 판정 | 반환값 |
|---|---|---|---|
| M01 | IAM → Users → 본인 → Security credentials → MFA | 현재 MFA가 assigned인지 확인. 없으면 본인 권한 범위에서 Assign MFA device로 등록, 본인 authenticator/passkey로 완료. 등록 후 로그인 성공 확인. 권한 denied면 그대로 중단·기록. IAM 전체사용자목록 권한이 없으면 본인 My security credentials 화면 사용 | identity type, 본인 MFA assigned YES/NO, 재로그인 SUCCESS/NOT_RUN/DENIED, KST |
| M02 | Billing and Cost Management → Bills → 2026-10; Credits(접근 가능 시) | 조회 가능한 서비스 비용 subtotal과 credits/tax/total을 각각 구분, 데이터 기간/last update 기록. 이전/누적 프로젝트 비용 자료가 있으면 별도로 포함. net bill=0은 gross=0 아님. Credit 잔액/만료/적용 서비스 범위 확인; $500 ceiling을 credit 보장액으로 사용하지 않음 | month-to-date gross/source/coverage, credit balance/expiry/eligible-services 또는 UNVERIFIED, billing as-of KST |
| M03 | AWS ROSA console → 현재 overview/prerequisite 화면 | 이미 Enabled인지, prerequisite 표시/Marketplace 권한 오류·기존 subscription 여부를 조회만. Enable ROSA/Subscribe/Purchase/Create cluster 누르지 않음. 미활성화라 prerequisite 값을 못 보면 NOT_ENABLED/NOT_VISIBLE 기록 | enabled status, displayed prerequisite failures, access error category, KST |

MFA 등록 중 QR/secret seed/OTP를 캡처·전달·Git에 기록하지 않는다. 완료 상태 화면만 남긴다.
Bills 접근이 막히면 Cost Explorer 차단 API를 반복하지 않는다. 교육기관 management-account Owner의 서비스별 gross 비용·credit 적용범위·갱신시각 리포트가 대체 입력이다. 연락/요청은 사용자가 담당하고 이 안내로 자동 외부 메시지를 보내지 않는다.
Cost Explorer enable 화면은 읽기 전용 PASS가 아니므로 Launch/Enable을 눌러 설정하지 않는다. 활성화는 계정 설정 및 관련 monitor/subscription 생성 동작을 포함할 수 있다.
ROSA enable은 Marketplace/역할/정보공유 상태를 변경할 수 있다. 무료 초기 HCP contract가 있다는 사실만으로 이번 수집의 조회 범위로 간주하지 않는다.

## 3. 다음 묶음: quota/role/지원 조건
| ID | 경로 | 확인할 값 / 중단·누락 처리 |
|---|---|---|
| M04 | Service Quotas → Amazon EC2 → Running On-Demand Standard instances | L-1216C47A Applied Value100 유지 여부만 확인. 기존 100 적용근거 있음; Request increase 불필요. 이후 VPC/EBS/ELB quotas는 선택 worker/endpoint/LB 수에 맞춰 Lead가 검토. managed Site-to-Site quota는 D21 선택경로의 blocker 아님 |
| M05 | IAM → Roles → FDS-* (조회 가능 시) | ReadOnly-Audit/IaC-Operator/Network-Operator 실제 존재·정책/trust/MFA조건·본인 assignment 조회. role 없으면 NOT_FOUND, 목록 denied면 UNVERIFIED. role 생성/정책수정·권한확대는 #35 reviewed IAM handoff로 분리 |
| M06 | ROSA/Marketplace 기존 subscription 및 현재 AWS Support plan 표시 화면 | 현재 상태/오류/추가 비용 및 서비스 준비 제약을 기록. 구매/plan 변경하지 않음. exact supported ROSA version/type/pool/egress/암호화는 Red Hat OCM/ROSA CLI 또는 Lead의 read-only 입력 필요; AWS 콘솔만으로 모두 검증했다고 처리하지 않음 |
| M07 | EC2/VPC 관련 기존 inventory 화면, 필요 범위만 | 이전 Seoul EC2/NAT/EIP/VPN/TGW/ELBv2/RDS 조회 범위에서 no resources 관측됨. 값이 바뀌었거나 비용 차이가 있을 때 delta 확인. 같은 empty inventory를 gross=0 증거로 사용하지 않음 |

M04~M07에서 AccessDenied/SCP는 권한·가시성 차이로 기록하고 정책을 바꾸지 않는다. 3인 MFA의 각 본인 확인은 별개이며 M01 이권욱 완료를 3인 완료로 승격하지 않는다.
CloudTrail Event History 확인 기록은 durable trail/log retention 증명이 아니다. account audit retention gate는 #35에 유지한다.

## 4. 이권욱 개인 후속 — 누락 방지
현재 업무 Lead를 유지하며 Support 입력수집을 본인 Runtime 실행 책임으로 확대하지 않는다.

| 순서 | 본인 할 일 / 책임 | 완료조건 |
|---|---|---|
| U1 지금 | #35 본인 MFA·AWS 콘솔 입력/Cost 확인 | M01~M03 실제 결과와 KST. 부족 입력은 UNVERIFIED/Owner 명시 |
| U2 병행 | #36 D21 final raw/cleanup 전달 | 종료·flush 후 생성된 responder final raw 8706bytes와 기대 SHA, initiator/Phase-A/cleanup 원본·수집 provenance 전달. PSK/key/token 원문 제외. 수신 hash 확인·독립 증적 리뷰와 실제 publication은 이후 단계 |
| U3 입력 수신 후 | #42 D22 Registry 결정 | platform/APP producer 입력, endpoint·push/pull principal·trust·digest·paths·fallback·credential ref·gross cost·source refs의 현재 12출력 확정. Harbor의 기존 TLS/firewall 차단을 숨기지 않음 |
| U4 Private 선택 시 | #40 D23 필수 DNS subset 결정 | zone/source/Resolver 또는 승인 equivalent·route·SG/TLS·비용·복구를 명시. 전체 P1 DNS와 Private 접근 필수부분 분리 |
| U5 설계 입력 충족 후 | #34 Architecture Freeze/Cost GO | 논리계약·exact sizing·관리/source/egress/Secret·복구·비용/teardown 및 충돌 0. 생성 후 actual ID와 source 관측을 설계 동결 전 순환 blocker로 만들지 않음 |
| U6 대상 변경 후 | 지정된 코드/증적 검토 또는 독립 reviewer 인계 | 본인이 작성/실행한 코드·증적은 이하영/이재환 중 실제 독립자 검토. 본인 technical review는 독립 승인 아님 |
| U7 Gate 충족 후 | #112 최신 recollect/current pointer/정본 발행 판단 | 이번 PR8/Issue변경 포함 최신 snapshot, WBS/문서/manifest/ZIP 전체정합, 필요한 실제 검토·발행. 불변 docs-v3.1.20 원문/byte 수정 금지 |

U2 기대 responder: d21-ike-observer-20261003T042646Z.log / 8706bytes / SHA256 e5f754a3d66c6fe452605ff914a6294e87aa85bf6a345ec0fadb981f18745cb0.
bdcd9564...는 intermediate/non-canonical; 이번 문서 작성은 raw 수신·재해시·publication 완료가 아니다.
Secret 포함 원본은 Git 편입 STOP. 접근제한 원본과 sanitized derivative provenance를 구분하며 편집한 파일을 원본 canonical hash라고 표시하지 않는다.

담당자에게 넘길 입력:
- 이하영 #35/#38: IAM role/policy·backend, ROSA version/quota/STS-OIDC, AZ별 pool/steady+failure capacity, egress/PrivateLink/Secret 지원, 비용산정·실제 platform runtime.
- 이재환 #37/#43/#47/#50: 관리 source/return route, stable DB source 모델, portable workload/동일 image·데이터/회귀·복구.
- 이권욱은 Decision/Architecture/Cost/추적성 판단과 지정 검토·발행을 맡으며 타인의 Runtime AC acceptance를 대신 표시하지 않는다.

## 5. 결과 전달 형식
첫 회차는 아래 값과 비밀값 없는 완료/조회 화면만 제출한다. 계정은 개인 채팅에서 대상 일치 확인이 가능하게 전달하되 공개 증적에는 필요 범위만 기록한다.
- 조회 시각(KST):
- 로그인: 본인 IAM user / 승인 role / root(중단)
- Regional 화면: ap-northeast-2
- M01 MFA: ASSIGNED / NOT_ASSIGNED / ACCESS_DENIED; 재로그인:
- M02 Bills: 조회가능 / DENIED; 비용 기간·service subtotal·credit·tax·total·as-of(구분):
- Credits: 잔액·만료·ROSA/AWS 서비스 적용범위 / UNVERIFIED:
- M03 ROSA: ENABLED / NOT_ENABLED / UNVERIFIED; 표시 prerequisite 실패:
- 권한 오류: action/service/reason만. Secret/QR/OTP/token/private key/로그인 비밀번호 제외.
확인 안 된 값은 0 또는 PASS로 채우지 않는다. 실제 조회/반영 전 CI/RUNTIME/MERGE/PUBLICATION을 상향하지 않는다.

## 공식 참고
- 본인 IAM MFA: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html
- ROSA enable/preconditions: https://docs.aws.amazon.com/rosa/latest/userguide/set-up.html
- ROSA Marketplace boundary: https://docs.aws.amazon.com/rosa/latest/userguide/integration-marketplace.html
- ROSA underlying service quotas: https://docs.aws.amazon.com/general/latest/gr/rosa.html
- Bills/credits 구분: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-exploring-data.html
- CE enable 동작: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-enable.html

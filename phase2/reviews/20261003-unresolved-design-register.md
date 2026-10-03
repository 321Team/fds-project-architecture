# Phase 2 설계 미확정 / 검증 / 실제 관측 분리 점검
기준 사용자 요청: 2026-10-03 17:59:41 KST. 최신 GitHub 재조회 기반 / READ-ONLY ASSESSMENT.
CODEX_ASSISTED. 이 문서는 사양 승인·담당 재배정·AC 변경·Freeze·Apply 승인이 아니다.
기준 architecture PR8 입력 HEAD: 9ab889f29ecff09ee417f9063067c7879b633dc8.

## Source
- baseline #34/#35/#37/#38/#40/#42/#43/#47/#50 본문, #34/#37/#38/#40/#42/#43/#47 최신 comments.
- phase2/reviews/20261003-design-ritp-deep-review.md at above exact HEAD (F01~F09).
- 사용자 AWS readback delta는 #35/#38 comments의 USER_REPORTED 원본으로 구분. Assistant AWS API 직접조회 아님.
- 최근 실제 관측: 권욱 FDS-ReadOnly-Audit session 및 metadata 조회 PASS; EC2 quota100, AMI available owner일치, 기본VPC172.31/16, project network 미관측; ELB role 미존재 및 ROSA page autoCreate denied. Activation 완료/SUPPORT/Red Hat account linkage는 미확인.
- #34의 사양표/상단deepreview와 #40/#42 등의 오래된 본문, 시간순 comment delta가 함께 존재. 아래 충돌/미정 항목은 임의 해소하지 않음.

## A. 생성 전에 고정할 설계/계약
| 항목 | 실제 남은 결정 | 근거/입력 책임(기존 유지) | 닫는 조건 |
|---|---|---|---|
| ROSA 모델/지원 version | HCP vs Classic, 지원 channel/version 선택; HCP는 우선 후보일 뿐 승인값 아님 | #34 권욱, #38 하영 | 지원 제약·계정 조건·비용·R/I/T/P 동등성 비교 후 authority 반영 |
| Worker sizing/topology | type, AZ별 pool count/node count, worker root/storage, platform+workload 및 교체여유 | #38 하영→#34 | supported sizing+수용 failure-domain+gross견적; 3poolx1/m5.2xlarge/300GiB 추정값 자동승격 금지 |
| ROSA 네트워크/egress | standard/restricted/zero-egress, NAT 수·AZ·EIP, VPC endpoint/required external endpoints, Pod/Service CIDR 및 host prefix | #35/#38 하영→#34 | 정확 installmode/version의 지원 subnet/route/endpoint 계약, source/보안/비용 대조 |
| public subnet 적용 범위 | 확정 transport-a1개가 selected ROSA install path 요구에 충분한지; 필요시 추가 public subnet의 CIDR/AZ 별도결정 | #35/#38→#34 | AWS 표준 HCP 설명과 Red Hat private install 절차 적용대상 구분; 무조건 public3개/무조건1개 확정 금지 |
| API/Ingress/관리 접근 | Public/Private, 승인client/Runner source, private endpoint SG/ports, OAuth/Route/TLS termination와 source-preservation mapping | #38 하영, #37/#43 재환→#34 | 승인 source/port/route/return 및 ingress spoof/bypass/engine·metrics 외부DENY 시험계약 |
| Private 필수 DNS subset | resolver방식/zone소유/forwarding/source TCPUDP53/장애복구/비용; Runner10.250.10.20은 현재selector밖 | #40 권욱; #35/#37/#38 입력 | 선택 Private mode를 실제 사용할 DNS+route 계약. 전체 D23 P1 자동승격이나 IP/TLS우회 금지 |
| inner forwarding 구현 계약 | Relay SG+host/vpn-gw 정책, authenticated SA+tuple, management 신규예외, 실제 최소source 생성규칙 | #37 재환,#35 하영 | default deny/no-inner-NAT 및 API→DB5432,engine→DBDENY를 구현가능한 tuple/영구규칙으로 연결 |
| DB source 안정성 | node교체/Pod이동/recovery 후 허용source-set 생성·갱신 규칙 또는 지원 egress adapter | #47/#43 재환,#38 하영 | 단일관측IP/wholeVPC 고정 금지; CNIsource/selector/pg_hba allowlist 구분 및 positive/negative/recovery acceptance |
| D22 Registry | Primary Harbor/cloud, endpoint/repo, push/pull actors, trust/digest/fallback, credential ref, 비용 | #42 권욱; #38 하영,#43/#46/#47 입력 | #42의12필수출력 계약. 최신 Harbor readiness 재확인; old TLS/firewall 지적의 현재해소는 원본대조 없이 단정하지 않음 |
| managed security/recovery/관측 | Secret/KMS/key권한·삭제방지·복구, app/DB backup/restore/migration, metrics/alerts/TLS/원본 export | #38 하영 및 기존 관련 producer→#34 | Phase1 요구와 관리형서비스 동등증적 mapping. gp3암호화로etcd/Secret PASS 금지; 접근제약으로 요구삭제 금지 |
| 비용/운영 입력 | 교육장 정확한도·기간/범위, 일별금액 출처/집계시각/제출방법, runtimeduration/teardown잔존, NAT/DNS/Registry 총비용 | #34 권욱/#35 하영 | 안내한도 준수+매일사용보고 합의 적용. 별도 교육장사용승인/Billing관리권 확보 요구하지 않음. 문서400/450/500과 실제교육장한도 일치 미확인 |
| 업무·데이터 회귀 경계 | 동일DB P1/P2 test ID/account/mutation window/migration owner, source/digest/transaction/DB/raw chain | #43/#47/#50 재환→#34 | 기존Rule·기대값·보존정책 유지 및 허용차이/복구검증; ACK/HTTP200만으로무결성PASS 금지 |

NAT1대는 supported install path·별도 SPOF 위험수용·비용/보안 검증 전 후보. D21 단일Relay 수용이 NAT SPOF 수용까지 뜻하지 않는다.
필수DNS는 Private access를 선택할 때의 conditional dependency이며 #40 전체P1범위/일정을 임의변경하지 않는다.
선택 version은 create 전에 정하고 실제 runtime version은 create 후 대조한다.

## B. 이미 정한 intent / 아직 검증·구현이 남은 부분
- D21 FINAL/aws_ec2_eip_relay, Region/VPC/private3/transport-a, Relay type/IP/AMI/owner/gp3encrypted40GiB/EIP1/publicSSHdeny/SSM: 확정 설계입력. AMI/계정AZ/quota는 사용자 최신 metadata 대조 범위PASS.
- IPsec envelope10.1.93/24↔10.20/16은 확정. 신규 FORWARD defaultdeny/noinnerNAT/API→DB5432/engineDBdeny는 보존 계약. exact stable sources와 신규 management 예외는 미결.
- runAsNonRoot/noPrivilegeEscalation/ROrootfs/seccompRuntimeDefault/dropALL은 보존 계약. fixedUID/GID는 Phase2 정본요구 아님.
- portable base/OpenShift overlay 방향 존재; #38 PG03는 restricted-v2 arbitraryUID의 실제Running/Ready/업무 검증 미완료. admission/static만으로 해소 불가. SharedLab와ROSA런타임 별도.
- state4경계(network/vpn/rosa-prereq/rosa-runtime)+S3native use_lockfile는 설계확정. exact bucket/key/encryption/credential/permission의실행입력은 #35의plan/Apply전 확정.
- 실제IAM 조회role/config권한적용 및 권욱session확인은 account runtime scope. PR8독립리뷰, 다른2인의MFA/role검증, operatorrole/plan은 별도 미완료.
- ELB role 미존재/autoCreate denied는 준비미완료. topology 선택값 자체가 미정이라는 사실과 분리; 실제 activation/지원계정조건은 설계안 feasibility 입력.

## C. 생성 후 실제 관측값 — 그 값 부재만으로 Freeze를 순환차단하지 않음
VPC/subnet/route/Relayinstance/ENI/EIP allocation/publicIP/SG actual IDs, ROSAClusterID/API·Ingress실제FQDN/private endpoint, assignedPodUID/nodeIP/실제DBegresssource.
생성 전 생성규칙/관측/제한/갱신/인수계약을 고정하고 생성 후 actual을 연결한다.
PSK/token/privatekey 원문은GitHub에기록하지 않는다. credential reference·rotation/access contract만 기록.

## D. 문서 충돌/역사 snapshot 주의
1. #35 body에 WORK_ROLE=NOT_ASSIGNED 등 이전bootstrap snapshot이 있음. 최신 comment는 공통조회role설정+권욱사용PASS; operator role는 별도PENDING.
2. #34/#40 IP-only/D23P1 본문과 private-access 필수DNS comment를 함께읽어야함. Private mode 미확정이므로 어느한쪽으로 자동확정하지 않음.
3. #42 D22 final이 #38 actual BasicReady를 소비하는 기존계획과 Freeze전 Registry security/interface 계약 요구에는 시점 긴장 존재. Freeze전 논리선택/소비조건과 runtime actual endpoint/증적을 분리하는 단계계약이 필요; 기존 일정/담당/AC를 이 문서로 임의변경하지 않음.
4. #34 body/deepreview의400target/450hardstop/500ceiling은 문서값. 최신사용자 비용운영은 교육장한도+일별보고, 별도사용승인불필요. 정확교육장수치 미수신 상태에서 같거나폐기됐다고 단정하지 않음.
5. deepreview16:01 snapshot의 accountRuntimeNOT_RUN 표기는 당시 assistant환경기준. 이후 IAM config/사용자readback은 최신#35/#38에있음. ROSA/workload runtimeNOTRUN은유지.
6. D21 final raw publication, baseline112 recollect, architecture main/publication 및 exacthead independentreview는 설계미확정값과 별개추적. 기존B5/B6를삭제하지 않음.
7. GitOps/Compliance/RHOAI 등 P1nonblocking을 새P0Freeze조건으로추가하지 않는다.

## E. 권장 닫기 순서
1. #38 supportedHCP/Classic/version + actualplatformcapacity/accountSupport/linkage 입력.
2. #34 ROSA모델/APIIngress/egress 후보선정 → #40 PrivateDNS/관리source경로 → subnet/NAT/endpoint/cost비교.
3. #37/#47 최소forward/stableDBsource/actor분리 계약과 #42 D22단계handoff정리.
4. #38/#43 arbitraryUID·managedSecret/recovery/observability mapping 및데이터회귀계약.
5. #34 authority충돌0/필수설계미정0 → Freeze. #35 backend/operator/검토된plan 등 실행gate충족 후paidApply.
작성/static/mock/CI/계정조회/ROSARuntime/Review/Merge/Publication은별도상태로유지.

공식대조:
- https://docs.aws.amazon.com/rosa/latest/userguide/getting-started-hcp.html
- https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-aws-private-creating-cluster
AWSstandard가이드의AZ별public/private와RedHatprivate클러스터 subnetselection설명은 적용mode/version을맞춰대조한다.
이 문서점검=STATIC, 독립리뷰PENDING, FreezeHOLD. AWS/ROSA유료자원생성/plan/apply/workloadruntime/merge/mainpublication 수행없음.

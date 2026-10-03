# Phase 2 권장 설계 R/I/T/P 심층 리뷰
기준 시점: 2026-10-03T16:01:14.873+09:00 (KST)
분류: AUTHOR TECHNICAL REVIEW / REVISED DESIGN CANDIDATE / Architecture Freeze HOLD
책임: #34 이권욱; 플랫폼/IaC #35/#38 이하영; VPN/App/Hybrid #37/#43/#47/#50 이재환.
AI 사용: CODEX_ASSISTED. 자체/AI 검토는 독립 코드·증적 리뷰를 대체하지 않는다.

## 1. 판정과 적용 범위
HCP + Private API/Ingress + 표준 outbound egress + aws_ec2_eip_relay 방향은 Phase 1의 workload/security/evidence intent와 양립한다.
그러나 2026-10-03 대화 권장안은 수정·구체화가 필요하므로 AS-IS Freeze는 부적합하다. 최종 판정은 DESIGN_DIRECTION=CONDITIONALLY_SUITABLE / DESIGN_REVIEW=CHANGES_REQUIRED / ARCHITECTURE_FREEZE=HOLD.
설계 이름이나 provider 선택만으로 R/I/T 보존 또는 Portability Runtime PASS를 선언하지 않는다.
기존 D21 FINAL과 이미 합의된 R/I/T/P·보안 불변조건은 유지한다. 신규 topology/egress/pool/registry/DNS/source/Secret adapter는 이 문서로 승인값이 되지 않는다.

이 리뷰는 현재 원본 설계·Issue body와 최신 comments, 소스 파일, 증적 PR metadata를 대조한 것이다. 이번 세션에서 Phase 1 서버 또는 과거 raw archive를 재실행/재해시하지 않았다.
Phase 1의 검증된 범위는 보존하되, Phase 1 전체 완료로 확대하지 않는다. #15 local endpoint 보장 NOT MET, #16 Delivery Runtime 미검증, #19 Secretbox rollback 미충족 등은 별도 잔여로 이어진다. P2로 이전한다고 P1 잔여가 해소되지 않는다.

## 2. 최신 원본과 출처
조회는 비원자적이다. 설계·실행 전 해당 HEAD/Decision 변경을 다시 확인한다.

| 대상 | 이번 조회 원본 / 확인 범위 |
|---|---|
| baseline main | 67ba6cf8a7f187e2dfcf188e4b2c55a853993778; baseline/FDS_Project_Implementation_Baseline_v3.1.20.md |
| architecture PR8 | 검토 전 HEAD 1516a04f4103b75fa2a955b063dadb6589f99975; phase2/README.md blob 2a64d6063d5d06ee93765b8d987d41b5ca0856f2 |
| fds-msa main | 5120b7df72d24ada3dbcf23fc0292fb58ae778af; main과 compare identical |
| API Dockerfile | blob 2d76aa5645df9285ec9958b293335694584640b5; digest-pinned build inputs/hashed offline wheel install/USER 10001:999 |
| engine Dockerfile | blob 4336f8ccd9c6cefe287ffcc5decf1a3d65079d69; 동일 build boundary/USER 10001:999 |
| API main.py | blob 6a00b1e86e92b842e71412144d83db3863c02cb6; /livez 무외부호출, /readyz DB 확인 |
| engine rules.py | blob 53c48bb7ee84f606835efcf05b36451aba9ddbf0; KST 및 Rule/source draft 주석 |
| 앱 계약 | docs/transaction-api_fds-engine_contract_v1.0.md blob 8e6ef012b337662ed681ac302ba2a23485ee236d; DRAFT/OPEN과 현재 정본 차이를 보존 |
| E2E 기준선 | evidence PR68 merged, HEAD 25610231d78d5fe804540ed78da6149c16a9189b; 24 PASS와 API/DB 22건 대조는 해당 회차/이미지/경로에 한정 |
| source 보존 기준선 | evidence PR86 merged, HEAD 54cecab819146e906fef526454d10028c7241392; Pod 관측 .50/HTTP200 3 worker positive 범위 |
| Terraform PR3 | ebfc56e25125784187e36a0c1dd2ca0463e82acd; scaffold STATIC 기록, PLAN/APPLY 아님 |
| ROSA PR2 | f5f0db1c50e83b7c9bb5242de9090fdd15cf5720; admission-only, PG03 Runtime 미실행 |
| baseline PR112 | ccaa841c39b75497d17e793b79b248b41c5308e4; 이전 follow-up snapshot, 본 리뷰 변경은 아직 미포함 |
| evidence PR104 | feea4288f96d92c3e058d59d8dbf7f124c8bfdf8; pre-VPN/HTTPS egress만, final IKE raw 아님 |

최신 티켓: baseline #15/#16/#19/#20와 #34/#37/#38/#40/#42/#43/#47/#50. #15/#16/#19/#34/#38의 최신 comments를 포함했다.
이 문서가 원본 evidence나 기존 독립 리뷰를 대체하지 않는다. 미존재 references/upstream/kubernetes/fds-engine-deployment.yaml 조회는 실패했으며 읽은 파일로 포함하지 않는다.

## 3. 보존 계약과 adapter mapping
| R/I/T/P 계약 | Phase 1 기준 | Phase 2 adapter / 필수 검증 |
|---|---|---|
| Reproducibility | source/base/lock/wheels/build/scan 승인 입력, 고정 fixture·기대값·배포/복구 절차 | 공통 build 결과 digest 사용; renderer/CLI/provider/module/version·overlay·입력 revision 고정; 승인 source에서 재생성한 manifest hash와 적용 대상 확인 |
| Integrity: 공급 | Test→Build→Scan→Push→Deploy→Health/E2E, TLS/권한·digest 결박 | registry 주소만 변경해 scan·trust·pull actor·runtime imageID를 생략하지 않음. rebuild면 새 digest/source/scan/회귀 lineage |
| Integrity: 업무/데이터 | API→engine:8001, API→db01:5432, engine→DB/External DENY; Rule·응답·DB row·migration·실패정책 | 동일 fixture 및 기대 결과; 정상 HTTP만으로 PASS 금지. 신규 namespace별 시험 ID로 history-sensitive Rule 오염 방지 |
| Integrity: 보안 | 최소 SA/RBAC, non-root/RO rootfs/drop ALL/seccomp, source 보존·최소 허용, Secret 보호 | restricted-v2 arbitrary UID, 승인 ingress/CNI/Secret adapter 동등성, default-deny·TLS·RBAC/credential negative |
| Traceability | Decision/Issue/PR/source/run/image/환경/AC/raw/manifest/독립리뷰 연결 | P1 기준과 P2 결과를 별도 환경/회차로 유지; 동일 Transaction ID의 API/engine/DB 연결, metrics는 승인 집계 상관관계로 기록 |
| Portability | 기존 R/I/T 기준 | 같은 portable image/base/business tests를 두 플랫폼에서 실행; provider IDs는 adapter input. 변경이 필요한 항목은 이유·영향·출처·회귀를 명시 |

Metrics에 Transaction ID label을 무단 추가하지 않는다. 기존 집계형 관측과 요청/응답·로그·DB 식별자 연결을 구분한다.
managed HCP의 host 접근/etcd 직접 조회/복구 권한은 P1과 다르다. 접근 불가능한 증적은 실제 관리형 서비스 증적과 mapping/한계를 기록하며 단순 N/A로 지우지 않는다.

## 4. 발견사항 / 수정 / 재검증
### F01 — HCP MachinePool 설명 오류 [수정 필수]
대화의 “하나의 pool로 3 AZ” 권고를 철회·정정한다. 공식 HCP architecture는 machine pool마다 단일 AZ/private subnet이다.
수정 후보: 3-AZ worker 배치를 선택하면 AZ별 pool을 만들고 공통 template으로 동일 설정을 관리한다. 총 3 worker/각1은 용량·지원 검증 전 후보이고 승인된 exact sizing은 아니다.
HCP는 ingress/registry/platform monitoring도 worker에서 실행하므로 앱 requests만으로 worker를 산정하지 않는다.
재검증: target version machinepool 지원, AZ/subnet inventory, platform+workload steady/transient capacity, drain/replacement/PDB·spread. worker 3/AZ 배치만으로 end-to-end HA PASS 금지.

### F02 — 단일 NAT가 보안/가용성 보존을 자동 보장하지 않음 [Freeze 전]
단일 NAT 권고는 조건부 후보다. NAT는 destination authorization 또는 host firewall이 아니다.
표준 platform required egress와 application egress를 별도 관리한다. Pod 인터넷 egress 및 engine DB/External DENY를 유지하고 platform endpoint 필요를 이유로 app allow-all을 추가하지 않는다.
기본 private route 0.0.0.0/0→NAT와 더 구체적인 10.1.93.0/24→Relay ENI를 구분한다. DB/Harbor traffic은 NAT Gateway를 통과하지 않아야 한다. management 경로 변경 시 승인 prefix에 대해서만 추가.
NAT Gateway 별도 EIP/IPv4 비용은 D21 Relay EIP 1과 별도다. Relay를 Internet NAT/proxy/DNS 복합 서버로 임의 재사용하지 않는다.
공식 AWS 일반 HCP 가이드는 AZ별 public/private subnet을 설명하지만 Red Hat private creation은 private subnet만 선택한다. 이번 목표 private HCP/version/install mode에 적용되는 정확 subnet·egress prerequisite를 #35/#38에서 확인한다. 이미 확정된 transport-a만으로 모든 install 요구가 충족됐다고 선언하지 않음; 필요 subnet은 별도 입력결정.
단일 NAT는 a-AZ egress SPOF/cross-AZ 경로를 가진다. D21 단일 Relay 위험수용이 NAT 위험수용까지 포함하지 않는다.
재검증: active routes/flow/source, app External negative, platform endpoint positive, cross-AZ 비용 및 허용 failure-domain. 기존 HA AC를 충족 못하면 per-AZ NAT 또는 지원 zero-egress로 재산정; 예산 때문에 AC 축소 금지.

### F03 — Private 관리 접근/DNS/PrivateLink SG 미완성 [Freeze 전]
Runner 10.250.10.20은 현재 selector 10.1.93.0/24 밖이다. Runner→mgmt gateway→vpn-gw 경로/return route와 source를 read-only로 확인하고, narrow management prefix 변경 또는 승인 VPC 실행 adapter 중 하나를 결정해야 한다.
현재 입력으로 Runner 관리 /32 추가를 승인한 것은 아니다. SNAT로 기존 selector에 맞추거나 관리망 전체를 임의 개방하지 않는다.
필수 private API/OAuth/Ingress FQDN의 resolution/TLS용 DNS subset은 P0 접근 prerequisite; 전체 D23 P1을 자동 P0로 바꾸지 않음.
HCP private API endpoint 기본 SG는 Machine CIDR만 허용한다. 외부 source는 지원 version에서 추가 SG를 연결한다(공식 문서 4.17.2+). 기본 SG 수정/제거 금지; 문서의 외부 API 예시는 TCP443이므로 P1 API6443을 기계적으로 복사하지 않는다.
정확 port/endpoint는 생성 후 실제 API URL/read-back으로 확정하며 문서 예시 hostname/IP를 실행 입력으로 쓰지 않는다.
재검증: DNS TCP/UDP53 최소 source, private hosted names/auth redirects/SNI+CA, 승인 Runner login/namespace-local apply, 비승인 source/expired credential DENY, 양방향 route. resolver 장애 시 TLS를 끄는 fallback 금지.

### F04 — 외부 진입/source identity의 동등성 누락 [Freeze 전 계약 / 생성 후 실증]
P1 SEC-AC04 .50/32→Worker30080 source preservation은 현재 유지된 요구다. OCP Route/NLB/router로 adapter를 바꾸면 원본 client source·gateway/router source·DB source·업무 payload source_ip를 구분한다.
X-Forwarded-For 또는 요청 body source_ip를 읽었다는 사실은 network source preservation의 증명이 아니다. trusted proxy/header 처리·spoof negative·approved client set·metrics 외부 차단·TLS termination/내부 암호화 경계를 입력으로 고정한다.
P1의 NodePort/Local/local endpoint 구현을 P2 portable base로 강제하지 않되, 상위 source/entry authorization intent와 health-based endpoint 제외/복구 보장은 보존해야 한다. 해당 semantic 변경은 IF02 adapter mapping/Decision/필요 ICR로 처리한다.
재검증: 승인/비승인 진입 source, forged header, direct service bypass, 외부 engine/metrics 접근 DENY, worker replacement 후 readiness/route/backend 복귀. P1 local endpoint 보장 잔여를 Route 선택으로 소급 PASS 처리 금지.

### F05 — 안정적인 DB source contract 미결 [Freeze 전 모델 / Runtime actual]
고정 Node IP 1회 관측으로 allowlist를 동결하면 worker 교체 때 깨진다. 승인된 최소 source-set 생성 규칙 또는 지원 stable egress adapter를 논리 계약으로 먼저 선택하고 actual 값은 생성 후 관측한다.
EgressIP는 선택 후보이고 ROSA CNI/AWS 조건·권한·할당/이동 가능 subnet·실패복구를 확인해야 한다. cluster-scoped 설정을 Shared OCP에 임의 적용하지 않는다. gateway inner-NAT 금지와 CNI source-transform 승인 계약을 구분한다.
NetworkPolicy는 additive이므로 default-deny 파일 하나만 확인하면 부족하다. 선택 Pod에 적용되는 전체 policy union과 추가 SG union, host forwarding을 검토한다.
Node가 두 app의 source를 공유해도 engine의 DB credential 부재와 workload egress DENY를 보존한다.
재검증: fresh connection으로 API save/query positive, engine/미승인 source/port negative, plaintext/bypass negative, Pod 이동·worker replacement·VPN recovery 후 동일 결과. timeout만으로 차단 주체를 확정하지 않는다.

### F06 — Harbor 재사용의 기존 차단사항 [D22 GO 전]
#16 최신 기록: Runner Harbor TLS trust BLOCK, HBR firewall allowlist 미완, token audience exact 승인값 미고정. 따라서 “기존 Harbor이므로 READY”로 처리 불가.
Harbor primary는 조건부 권고: Runner system/Podman CA verify, 실제 node image-pull source/return route, pull-only robot과 push principal 분리, CA 배포·만료/폐기·digest/scan 연결을 닫은 뒤 선택한다.
node의 image pull은 app Pod NetworkPolicy만으로 통제되지 않는다. node SG/route/Harbor firewall 관측을 별도로 한다.
Registry fallback은 같은 approved digest와 별도 endpoint/trust/credential/비용을 가진 명시적 Decision으로 구성하며 자동 tag fallback 또는 재build를 허용하지 않는다.
Harbor 준비가 일정 내 안 되면 #42의 Cloud Registry 대안을 비교하되 새 IAM/auth adapter와 동등 bytes/digest 입증 후 선택한다.
재검증: Runner push/pull, ROSA cold pull·worker replacement pull, anonymous/pull-principal push DENY, VPN outage/recovery. cache hit만으로 registry runtime PASS 금지.

### F07 — arbitrary UID / 동일 image 검증 부족 [PG03]
현재 Dockerfile USER10001:999는 기본값이다. 이 값 자체가 arbitrary UID 불가라는 증거는 아니며, overlay에서 runAsUser/runAsGroup를 없앴다는 사실도 호환 PASS가 아니다.
먼저 같은 approved digest로 restricted-v2 arbitrary UID Running/Ready/health/업무, RO rootfs, /tmp 등 최소 write mounts, effective UID/GID/SCC와 imageID를 관측한다.
실패하면 필요한 filesystem 권한/entrypoint만 수정하고 공통 image를 재build/scan한다. 이때 새 digest를 P1과 P2 양쪽에서 회귀 검증하거나 승인된 변경 lineage/범위를 기록한다. 같은 tag를 사용했다는 이유로 동일 image라 하지 않는다.
재검증: non-root/no escalation/dropALL/RuntimeDefault/SA token 부재, image pull·filesystem·probes, namespace recreate, cleanup. custom/broad SCC·root·RO rootfs 해제로 우회 금지.

### F08 — managed Secret/backup/recovery/monitoring 증적 mapping 누락 [Freeze 전 계약]
P1 baseline은 Secretbox 원문비노출·key 관리와 P2 KMS v2 목표를 가진다. 현재 #19 backup 편입은 확인됐지만 rollback은 NOT MET이다. 예방 rotation risk accepted와 노출 credential 대응은 별개다.
HCP custom KMS 문서는 worker root encryption과 etcd encryption 입력을 구분한다. encrypted gp3만으로 Secret encryption을 증명할 수 없고, 문서의 default etcd encryption만으로 KMS v2 목표 완료를 선언하지 않는다.
#38에서 default/CMK/지원 KMS 구현·key owner/IAM/삭제방지·운영제약·비용·감사/read-back 증적을 매핑하고, #125의 후속 수신 의무는 Receiver Record가 있을 때만 승계로 표시한다.
관리형 control plane에 P1 self-managed host 변경/etcd restore 절차를 그대로 실행하지 않는다. 지원되는 service recovery와 app/DB backup+restore를 별도 계약으로 기록한다.
P1 업무 metrics9091/9090, Prometheus RBAC·TLS·engine/metrics 외부미노출, alert/failure-recovery 관측은 보존 대상이다. HCP monitoring으로 대체할 경우 query/retention/alert/권한·원본 export 가능성을 검증한다. 관리형 서비스를 쓴다는 이유로 관측 계약 삭제 금지.
재검증: Secret value 제외 설정/IAM evidence, unauthorized read DENY, expiry/revocation, application config+secret-reference recovery, DB restore/migration 일치, business metrics·alert/recovery. 새 cluster-wide Operator는 필요성/비용/권한 승인 없이 추가하지 않는다.

### F09 — 재현성/무결성/추적성의 최종 연결 미완 [구현 및 인수 전]
Snapshot/source pin→approved build inputs→scan→digest→registry→rendered manifest→actual imageID→case/transaction/DB/schema→raw evidence→independent review→publication을 연결한다.
DB/migration 실행 owner와 기존 schema compatibility를 고정한다. 동일 On-Prem DB에 P1/P2 동시 쓰기 시 별도 test account/ID namespace·mutation window·row diff·cleanup/보존을 정의한다.
Rule R01/R07의 순서/누적 history와 KST 경계/offset fixture를 동일하게 유지하고 naive-time INFO나 Known Issue를 P2에서 PASS로 바꾸지 않는다. fail-open 기대는 #4/#5 최신 승인/구현 차이 확인 후 고정하며 IPsec 실패로 임의 fail-closed 변경하지 않는다.
TLS/latency 차이를 이유로 timeout/실패정책을 바꾸면 별도 영향결정·동일 fixture 회귀가 필요하다.
reproduce는 cloud IP/Pod UID/log timestamp가 바이트 동일함을 의미하지 않는다. 동일 승인 입력과 절차에서 동일 의미의 업무·보안 결과를 얻고 환경 차이를 설명할 수 있어야 한다.
D21 final responder 기대값은 8706 bytes/e5f754a3d66c6fe452605ff914a6294e87aa85bf6a345ec0fadb981f18745cb0; 이번 raw 미수신/재해시 미실시. bdcd9564...는 intermediate. PR104 성공을 final IKE publication 또는 production Child SA PASS로 승격 금지.

## 5. 수정된 권장 설계
Primary candidate: HCP / Private API+Ingress / AZ별 공통-template worker pools / 표준 platform egress / aws_ec2_eip_relay.
단일 NAT1은 supported private-install prerequisite·별도 SPOF 수용·보안 및 비용 검증 시에만 채택. 그 조건을 충족 못하면 per-AZ NAT 또는 supported private zero-egress를 비교한다.
DB/Harbor hybrid routes는 internet NAT와 분리; Relay SG+host/vpn-gw default-deny/authenticated IPsec tuple을 유지.
Harbor reuse는 trust/firewall/node pull 조건부 후보이고 D22 PENDING. DNS subset+Runner source/route+PrivateLink 추가 SG는 private access 선행조건.
Exact ROSA version/type/count/storage/Pod-Service CIDR/backend bucket+keys/management prefix/egress source/KMS mode는 아직 확정하지 않는다.
비용은 gross accrued+remaining P0+teardown residual; target400/hard-stop450/reserve50/ceiling500 유지. 48시간 실행 예시는 일정/Cost GO 승인값 아님. 실제 10-15~22 Runtime 계획을 임의 압축하지 않는다.

## 6. 동결과 실행 Gate를 분리한 후속 절차
| 단계 | 담당 | 완료조건 / 허용 행동 |
|---|---|---|
| G-F1 read-only 입력 | 이하영 #35/#38 + 이재환 #37/#43/#47 | supported version/pool/subnet/quota/IAM/OIDC, workload+platform capacity, 관리 source/route/DNS, egress/Secret 지원, latest approved app/digest/DB state 수집 |
| G-F2 계약 확정 | 이권욱 #34/#40/#42, 각 producer | F01~F08 논리설계/보안동등성/availability·source-set 모델/Registry·DNS handoff/시험·복구 계획, exact sizing+cost+teardown 결정; 권위표의 PENDING을 실제 근거로만 정정 |
| G-F3 Architecture Freeze | #34 Lead 이권욱 | 사양 충돌·미확정 필수 설계 입력 0, 관련 Decision과 implementation handoff 일치, 비용 gate 충족. 코드/증적 독립 리뷰는 해당 정책대로 별도 수행 |
| G-I1 구현 준비 | 이하영 #35/#38, 이재환 #37/#43 | author branch IaC/base/overlay/host policy, static/mock/CI 및 필요한 exact-head 독립 코드 리뷰; 미확정 변수를 fail-closed 차단 |
| G-I2 유료 실행 | 해당 실행 Lead | Freeze/Cost GO 및 기존 Stage-A/MFA/선행 gate 충족 후 승인 resource 생성. actual resource ID/endpoint/source 관측 및 approved bounded allowlist 연결 |
| G-R 실제 인수 | #38/#43/#46/#47/#50 Leads | positive/negative/arbitrary UID/replacement/recovery/data/observability·digest/raw, 기존 AC 충족. Shared OCP 결과는 LAB-PRECHECK |
| G-P 증적/발행 | 기존 producer·독립 reviewer·발행 Lead | final raw/hash/intake/secret exclusion·AC mapping 독립 리뷰, exact-head merge, current pointer/release 새 snapshot publication 및 cleanup read-back |

생성해야 알 수 있는 actual Cluster/ENI/EIP/endpoint/assigned UID/source 값이 아직 없다는 사실 자체를 Freeze 전의 순환 blocker로 만들지 않는다.
다만 그 값을 어떻게 생성·관측·제한·검증할지에 관한 논리 계약과 승인 범위는 Freeze 전에 고정한다.
Runtime PASS를 Freeze 전에 요구하지 않는다. 현 PG03 Shared OCP prerequisite는 #38 current authority를 따르되 ROSA 인수와 분리한다.
현재 환경에는 aws/rosa/oc/terraform command가 없고 callable AWS/ROSA account session을 확인하지 못했다. G-F1 account Runtime/read-back은 NOT RUN이며 이를 위한 신규 자원/권한/비용 작업을 수행하지 않았다.

## 7. 상태 / 독립 검토
STATIC=설계/소스/권위·공식 문서 대조 수행, CHANGES_REQUIRED; 전체 설계 PASS 아님.
MOCK=이번 문서 변경 대상 없음; 이전 ROSA input mock 결과를 새 Runtime 검증으로 재사용하지 않음.
CI=이번 문서 HEAD 확인 후 별도 기록; 실행 없이 PASS 금지.
RUNTIME=AWS/ROSA/Shared OCP 신규 실행 NOT RUN; PLAN/APPLY/CREATE NOT RUN.
REVIEW=author review 완료, 독립 승인 PENDING. Architecture PR8 조회 시 reviews0.
MERGE=이번 설계 미병합. PUBLICATION=GitHub draft branch에 후보 기록, main/canonical release 미발행.
B1~B6의 기존 차단은 각 대응 조건까지 유지; F01 정정만으로 그 전체가 해소되지 않는다.

## 8. 공식 기술 근거 (2026-10-03 조회)
- HCP machine pool single-AZ, platform worker components: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws_classic_architecture/4/html/architecture/rosa-architecture-models
- HCP private creation / supported additional endpoint SG: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-aws-private-creating-cluster
- HCP prerequisites / required platform egress: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/prepare_your_environment/rosa-hcp-prereqs
- AWS HCP VPC/NAT guide: https://docs.aws.amazon.com/rosa/latest/userguide/getting-started-hcp.html
- HCP private zero-egress alternative: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-egress-zero-install
- Root volume vs etcd KMS: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-creating-cluster-with-aws-kms-key
- Supported egress IP candidate: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/tutorials/cloud-experts-consistent-egress-ip
- NetworkPolicy union / NAT/source semantics: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Service/infrastructure fees: https://aws.amazon.com/rosa/pricing/
공식 문서의 예시/기본값을 이번 project 승인값으로 사용하지 않는다. 정확 version/account 지원은 G-F1에서 read-only 재확인한다.

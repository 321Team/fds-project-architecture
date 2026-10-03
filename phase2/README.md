# Phase 2 Current Architecture / R-I-T-P Contract
기준: 2026-10-03T15:10:46.525+09:00 · 상태: CANDIDATE / Architecture Freeze HOLD
책임: #34 이권욱(Architecture), #35/#38 이하영(IaC/ROSA), #37/#43/#47 이재환(VPN/App/Hybrid).
AI 사용: CODEX_ASSISTED. 문서 작성·기술검토는 독립 코드/증적 승인을 대체하지 않는다.

## 1. 목적과 권위
Phase 1에서 검증한 재현성·무결성·추적성 intent를 보존하고, 실행 플랫폼 교체 후 같은 workload/security/evidence 계약의 성립을 검증한다. AWS/ROSA/OCI 값은 provider/platform adapter이다. HCP 또는 Classic 선택만으로 Portability PASS가 되지 않는다.
현재 승인값은 baseline #34/#36의 D21 authority이다. 미확정 topology/access/egress/DB source 값은 이 문서의 권고를 승인값으로 사용하지 않는다. Freeze, resource creation, Runtime acceptance, 정본 publication은 별도 단계다.
원본 #34~#50, Terraform #2/#3, ROSA #2, baseline #112, evidence #104를 재조회했다. Snapshot은 비원자적이며 마지막 재조회와 HEAD 변화는 PR에서 다시 확인한다.

## 2. Confirmed Transport Adapter
- D21=FINAL; OCI Primary=NO-GO(project suitability), 기술불가가 아님.
- Selected adapter=aws_ec2_eip_relay. OCI pathcheck는 기술 reference이며 AWS production tunnel이 아님.
- IKEv2, On-Prem initiator, explicit IKE ID, dynamic public source, stable cloud EIP, NAT-T.
- Region ap-northeast-2; VPC 10.20.0.0/16.
- private-a 10.20.10.0/24 / ap-northeast-2a / apne2-az1.
- private-b 10.20.20.0/24 / ap-northeast-2b / apne2-az2.
- private-c 10.20.30.0/24 / ap-northeast-2c / apne2-az3.
- public-transport-a 10.20.110.0/24 / ap-northeast-2a / apne2-az1.
- Relay 10.20.110.10, t3.medium, ami-079a2667364cee804(owner 125523088429), gp3 40 GiB encrypted.
- EIP 1, auto public IPv4 disabled, source/destination check=false.
- Public SSH DENY; SSM/bootstrap management. Public IKE UDP/500,4500만(단일 관측 /32를 peer identity로 사용하지 않음).
- selector 10.1.93.0/24 <-> 10.20.0.0/16은 transport envelope이며 application authorization 아님.
- AWS route authority=Terraform: 10.1.93.0/24 -> Relay ENI.
- db01 return route: 10.20.0.0/16 via 10.1.93.51. Harbor return route는 D22 Go 때만.
- Logical state boundaries network/vpn/rosa-prereq/rosa-runtime; S3 use_lockfile=true. Exact bucket/key PENDING.
- 단일 Relay P0 SPOF는 D21 범위의 수용이며 restart/rekey/rebuild/reboot recovery를 #37 Done 전 증명한다.

## 3. B1 최종 결정을 위한 입력안 — 승인 전 PROPOSED
2026-10-03 후속 심층리뷰: [권장 설계 R/I/T/P 대조·수정·동결 Gate](reviews/20261003-design-ritp-deep-review.md)가 구체적인 권장안 검토를 보완한다. 판정은 DESIGN_DIRECTION=CONDITIONALLY_SUITABLE / DESIGN_REVIEW=CHANGES_REQUIRED / 전체 Freeze HOLD이다.
대화의 단일 MachinePool 3-AZ 권고는 정정: HCP pool은 단일 AZ/subnet이며 AZ별 공통 template pool을 후보로 검토한다. 단일 NAT는 별도 SPOF/지원·보안·비용 조건부 후보이다. PrivateLink 추가 SG, ingress/source 보존, 기존 Harbor 차단, managed Secret/복구·관측 adapter mapping을 닫기 전 신규값을 CONFIRMED로 소비하지 않는다.
권장 순서: HCP를 우선 비교하되 Private API/Private Ingress, 실제 지원 version, worker capacity, egress, private access DNS, Cost-to-Complete를 묶어서 판단한다.
3 MachinePool×1, m5.2xlarge, root 300 GiB, Pod/Service CIDR는 이 문서에서 확정하지 않는다.

| 선택 | 공식 제약/구조 | R/I/T/P·일정 판단 | 선정 조건 |
|---|---|---|---|
| HCP | control plane은 Red Hat 관리 계정; 고객 worker 인프라; 최소 worker 2, Multi-AZ 요건 별도 확인 | 현재 P0 workload/security/delivery/hybrid 증적은 worker/API 중심이므로 적합 후보; control-plane host 증적은 별도 제약 | PG-01~09와 동일 workload Cost GO 충족 |
| Classic | 고객 계정 control-plane/infra/worker; Single-AZ 최소 7 EC2, Multi-AZ 최소 9 EC2 footprint | 관리 구조는 익숙하지만 비용·quota·운영 경계가 늘어남; workload 이식성이 자동 개선되지는 않음 | HCP에서 필수 증적/기능을 확보 못하며 Classic 비용·quota·일정 충족 |
| Private API + Private Ingress | VPC 연결, DNS, 인증·TLS 필요 | 외부노출 최소 intent 유지 권장; Runner/관리단 경로가 선행조건 | DNS/route/source contract와 실제 readiness 확보 |
| Public API / Private Ingress | 관리 endpoint public 경계 별도 검토 | private DNS 비용 절감만으로 선택하지 않음 | 기존 security intent와 정식 exposure decision이 일치할 때만 |

| Egress 후보 | 계약/비용 항목 | 현재 판정 |
|---|---|---|
| NAT + supported required egress allowlist | NAT는 address translation이며 destination policy가 아님; endpoint/port allowlist는 지원되는 별도 통제로 구현. NAT hourly/data/public IPv4/cross-AZ 비용 포함 | 짧은 PoC의 실행 단순성 비교안; NAT 수/배치/허용 endpoints 미확정 |
| Private HCP egress-zero + required VPC endpoints | 공식 zero_egress workflow의 regional registry/endpoint·DNS·기능 제약을 정확 version에 결박; endpoint hourly/AZ/processing 및 telemetry/operator 비용 포함 | 보안 우선 비교안; egress-zero를 endpoint 0개/무료/완전 air-gap으로 해석 금지 |
| Proxy/firewall restricted egress | 지원되는 proxy/egress configuration, CA trust/NO_PROXY/필수 도메인, 장애·비용 추가 | 필요할 때만; Relay를 인터넷 NAT/proxy로 재사용하지 않음 |

비용: ROSA service fee=worker vCPU 합/4×$0.171/h, HCP 추가 $0.25/h. AWS EC2/EBS/LB/NAT/endpoints/DNS/IPv4/transfer/로그/Relay/잔여 teardown 별도.
동일 workload·availability·runtime 시간으로 HCP/Classic 비교. project gross accrued + remaining P0 + teardown residual을 산정하며 missing billing=0으로 대체하지 않는다.
현재 Cost 입력의 실제 gross/accrual/runtime hours/worker/storage/network counts가 null이다. Target ≤$400 / Hard Stop $450 / Reserve $50 / Ceiling $500 유지. Cost GO 미충족.

Read-only 부족 입력:
1. 계정/ROSA subscription 준비, region별 exact supported version/machine types, STS/OIDC/permissions boundary/SCP, quota read-back.
2. 승인 workload requests/limits와 AZ/recovery AC에 맞는 worker count/type/storage; subnet IP 여유/CIDR overlap.
3. NAT와 zero-egress required endpoint 목록·지원 조건·서울 단가·runtime 시간·gross/accrual·cleanup 잔여.
4. Private API/Ingress DNS 실제 이름·해석 구조, Runner/관리단 source route, identity/TLS.
현 실행 환경에는 AWS/ROSA CLI/connector session이 없으므로 계정 API 재조회는 NOT RUN. 기존 #35 W0를 현재 계정 사실로 승격하지 않는다.

### Private DNS의 P0 의존성
Private access 선택 시 API/OAuth/Ingress FQDN과 TLS SNI/이름 검증에 필요한 DNS는 P0 prerequisite다. #40 D23의 IP-only 기본안으로 충족했다고 처리하지 않는다.
권장 비교안은 승인 On-Prem resolver -> Route53 Resolver inbound endpoint(private routing, TCP/UDP 53, 최소 source)이다. VPC CIDR+2로 On-Prem query 직접 전달은 AWS 지원 경로가 아니다.
더 단순한 VPC 내부 실행 경로를 선택할 경우 Runner 위치/전송·증적 계약을 별도 비교하고 현재 Runner를 임의 이동하지 않는다.
D23의 전체 Hybrid DNS 기능/P1 scope는 유지하며, mandatory private access DNS subset만 #34/#38 create 전 Gate로 연결한다. 유료 endpoint 생성은 Freeze/Cost GO 전 금지.
주의: 현재 protected selector의 On-Prem 10.1.93.0/24에는 Runner 10.250.10.20과 관리망 10.250.10.0/24가 포함되지 않는다. 기존 management routing/source read-back과 승인된 management interface 결정 없이는 IPsec selector 확대·mgmt SNAT로 우회하지 않는다.

## 4. B2 Inner forwarding Interface Contract — implementation handoff
원칙: 신규 forwarding default deny; Relay/vpn-gw01 내부 masquerade/SNAT/DNAT 없음. Outer NAT-T와 inner application source NAT를 혼동하지 않는다.
현재 IP/port 최소 flow intent를 구체화하며 정확 source set을 추정해서 deploy하지 않는다.

| Flow ID | Actor / 목적지 | 집행층 | Ready 조건 |
|---|---|---|---|
| IF-18-DB | transaction-api 승인 path -> db01 10.1.93.55 TCP/5432 | workload NetworkPolicy + source contract + Relay/vpn-gw forwarding + DB firewall/pg_hba/인증 | stable DB source contract와 기존 TLS/DB auth 입력 read-back |
| IF-REG | D22 On-Prem Harbor 선택 시 승인 image-pull producer -> 10.1.93.54 TCP/443 | Registry actor/source 별도 정책 + gateways + Harbor TLS/auth | #42 D22 선택 및 actual image-pull source 관측 |
| IF-MGMT-DNS | Private API/Ingress 선택 시 승인 DNS resolver -> exact inbound endpoint TCP/UDP53 | #40 subset + #35 SG/route + gateway 정책 | B1의 DNS/source/management route 동결 |
| IF-MGMT-API | 승인 Runner/관리단 -> exact API/OAuth/Ingress endpoints·필수 port | #38/#46 access adapter, route·인증/TLS | source가 selector에 포함되는지 확인; 별도 management contract 승인 |
| DENY-DB-ENGINE | fds-engine -> db01 TCP/5432 | workload identity NetworkPolicy + 분리 DB credentials; source-level 정책 보조 | shared Node source를 앱 identity로 오인하지 않음 |
| DENY-OTHER | 나머지 신규 source/destination/port/방향 | gateways default deny + 최소 SG + workload 정책 | active/permanent rules와 route read-back |

SG는 cloud boundary를 제한하지만 tunnel 안의 app authorization과 host FORWARD를 대신하지 않는다. fds-engine과 transaction-api가 같은 node egress IP를 쓰면 SG/DB IP allowlist로 두 app을 구분할 수 없다. Workload identity deny와 DB 인증 경계를 함께 검증한다.
Public IKE 허용은 UDP500/4500 outer packet용이다. Decrypted forwarding에는 authenticated IPsec policy/SA 및 승인 tuple을 확인한다. 같은 ens160으로 복호화 packet이 재전송될 수 있으므로 NIC/zone만으로 trust를 판정하지 않는다.
Return은 승인 연결의 stateful established reply에 한정; 새로운 On-Prem->Cloud forwarding은 별도 승인 없으면 deny. 정책 갱신 시 기존 conntrack 상태가 deny 검증을 우회하지 않도록 fresh connections로 시험하고 필요한 tuple 정리는 영향검토 후 수행한다.

Producer/handoff:
- #35 Terraform: explicit route/ENI source-dest-check/SG/NACL, actual resource IDs, state component/source SHA. broad all-protocol forwarding/egress는 최소 flow contract 대체 불가.
- #37 host bootstrap: SELinux Enforcing/firewalld enabled, exact IPsec/forward policy, no-inner-NAT, ip_forward 및 redirect/rp_filter의 platform-specific 근거; 현재 pre-VPN baseline과 차이를 별도 기록.
- #38/#43 platform/workload: default deny, app/SA/namespace label과 필수 business flows, DNS/Registry exception.
- #47 DB: observed stable source set/return route/DB firewall+pg_hba+auth/TLS read-back.
- 소비 전에 tuple policy input에 source set, destination, port/protocol, direction, SA binding, owner, Decision ref, revision/hash, negative tests를 고정. unresolved field가 있으면 render/apply STOP.

Runtime acceptance: approved DB TCP/business positive, engine->DB negative, unapproved source/port negative, plaintext/bypass negative, asymmetric route/SA down negative, restart/rekey/reboot/rebuild 이후 같은 security intent 및 source contract. 원본 commands/RC/host/time/source+config SHA/pcap 로그·cleanup·active/permanent read-back를 보존.
중단: unexpected NAT/source 확대, 무인증 forwarding, TLS/SELinux/firewall 우회, 미확정 source/route, 비용 gate 미충족. 복구는 사전 보존한 승인 policy/config로만 원복하고 자원 제거/route 및 SG read-back를 남긴다.

## 5. B3 failure-domain-stable DB source acceptance
selector, actual egress source, DB authorization allowlist는 세 별도 필드다.
권장: 실제 source 변환/할당 메커니즘을 관측한 뒤, 승인 failure domain에서 변하지 않는 최소 source-set을 계약화한다. 단일 IP 고정 또는 whole VPC allowlist를 먼저 선택하지 않는다.
필수 기록: Pod UID/node/AZ, imageID/digest, node/Pod/egress IP 매핑, CNI egress 동작, route/SA, DB에 도달한 실제 source, source-set 생성 규칙·갱신 owner·revision, credential actor.
ROSA CNI source translation이 있으면 gateway no-inner-NAT와 분리해 관측하고 approved platform adapter source-transform 계약 여부를 명시한다. 미승인 translation을 암묵 허용하지 않는다.
다른 노드로 Pod 재배치, worker replacement/rebuild와 승인 recovery 후 source를 재관측한다. Shared Lab에서는 다른 조 Node drain/reboot/cluster-wide egress 변경 금지; 허용되지 않은 failure condition은 실제 ROSA에서 재검증한다.
Candidate 모델: 최소 승인 node/worker source-set + app deny/auth, 또는 지원되는 stable egress adapter. Whole private subnet이 최소인지 근거 없이 확대하지 않음. Egress feature 권한·지원/복구 제약은 #38이 검증한다.
PASS는 해당 failure domain에서 positive 유지, engine/unapproved source DENY 유지, return route/NAT/TLS intent 보존, 증적 completeness와 independent review 확인 시만.

## 6. B4 portable workload / arbitrary UID acceptance
Canonical base: Deployment, ClusterIP Service, ConfigMap/Secret references, application SA/RBAC intent, 표준 NetworkPolicy와 probes/resources/business contract. image는 immutable digest. Secret 값·cloud endpoint·fixed UID/GID는 base에 넣지 않는다.
OpenShift overlay: namespace/team, Route와 TLS 정책, registry pull/trust, 환경별 CIDR/DNS/network policy, storage 필요한 경우 StorageClass mapping. HCP/Classic별 app manifest 복제 없음.
Security intent: runAsNonRoot=true, allowPrivilegeEscalation=false, readOnlyRootFilesystem=true, seccompProfile=RuntimeDefault, capabilities drop ALL, automountServiceAccountToken=false(기존 application intent). runAsUser=10001/runAsGroup=999를 P2 canonical requirement로 승격하지 않음.
Image filesystem/entrypoint가 arbitrary UID에서 읽기/실행·필수 write volume에 접근하는지 검증. root 또는 custom/broad SCC로 우회 금지. Writable paths는 승인된 최소 emptyDir/PVC로 분리하며 RO rootfs를 끄지 않는다.
PG-03 W0 sequence: exact source/image/namespace authority -> fixed UID vs portable server admission -> 승인 namespace-local 실제 workload -> Pod Running/Ready + health/business smoke + assigned UID/GID/SCC/securityContext/imageID 관측 -> RO filesystem/필수 쓰기 경로·engine DB deny -> owned-resource cleanup read-back.
Admission-only probe는 Pod Running/Ready, image pull, filesystem, health를 검증하지 않는다. T1 비정상 RC는 원본 error로 SCC/네트워크/RBAC/auth 실패를 구분한다.
현재 infra-rosa#2는 admission-only; 입력검증 3건 수정·MOCK 점검을 수행했으나 PG-03=HOLD. 실제 image digest/namespace/접근 session/허용 runtime manifest가 아직 필요하다.
W0 Shared OCP PASS는 LAB-PRECHECK이며 ROSA Runtime PASS를 대체하지 않는다. #38 Basic Ready/#43/#46/#47/#50의 각 실제 gate는 유지.

## 7. B5 권위·snapshot 정합성
Terraform#2의 managed S2S/CGW/VGW-TGW/quota 5 vCPU W0 기록은 역사 snapshot으로 보존하고 current implementation input에서 supersede한다. refresh PR에서 current D21/readiness header와 README 책임/경계를 정렬한다.
Terraform#3=resource block 없는 scaffold. exact ebfc56e25125784187e36a0c1dd2ca0463e82acd의 fmt/init(-backend=false,-lockfile=readonly)/validate author PASS는 유지하되 resource readiness나 Plan/Apply로 확대하지 않는다.
baseline#112의 11:53 snapshot 이후 D21 FINAL/static PASS/본 follow-up 변경은 delta로 수집한다. 전체 14 repo/78 Issue snapshot 재수집·WBS/문서/manifest/ZIP 재생성까지 완료했다고 주장하지 않는다.
docs-v3.1.20은 실제 published release. 기존 release byte/asset/hash는 불변. CANDIDATE/COLLECTING/발행보류 표현은 당시 역사이며 v3.1.21/current-pointer 후보에서 publication status와 readiness를 분리한다.
architecture main dd90efc09d5ab16e170499374736df97c7ea5559는 Phase1 중심. 이 파일은 Phase2 current candidate PR이며 병합·정본 발행은 미완료.

## 8. B6 D21 evidence intake / integrity chain
기대 canonical responder: d21-ike-observer-20261003T042646Z.log / 8706 bytes / SHA256 e5f754a3d66c6fe452605ff914a6294e87aa85bf6a345ec0fadb981f18745cb0.
bdcd9564...는 tcpdump 종료 전 intermediate/non-canonical. 위 final SHA는 최신 #36/PR104에 기록된 기대값이며 현재 세션은 raw byte를 확보하지 못해 재해시 NOT VERIFIED.
필요 원본: Phase-A UDP500/4500 arrival, initiator/responder final IKE logs, responder final capture, exit/termination 시간·RC, cleanup(양측 connection/SA=0, temporary host rules/OCI NSG 제거) raw read-back, source/config version+commands/time/host, collection sidecar.
완성 절차: producer가 tcpdump 종료/flush·RC 확인 -> 원본 바이트 hash/size -> authorized transfer -> received hash/size exact match -> metadata/민감정보 검사(PSK/key/token 포함 원본은 Git 편입 중단) -> manifest와 registry -> 독립 evidence review -> merge/publication.
Secret 포함 raw는 재작성한 파일을 canonical original로 표시하지 않는다. 별도 접근제한 원본+sanitized derivative provenance와 기대 hash를 구분한다.
PR104는 pre-VPN baseline/dynamic HTTPS egress만. 원본 4개는 unchanged blob으로 main registry 충돌을 해소하며 final IKE 자료를 합성하거나 PR104 scope를 조용히 확대하지 않는다.
D21 IKE_AUTH round-trip은 intentional mismatched one-time PSK로 authentication failure를 관측한 기술 pathcheck. peer authentication 성공/production Child SA/tunnel UP은 NOT PROVEN.
현 main에서 final IKE 원본 파일을 찾지 못했으므로 final publication HOLD. metadata/expected hash 등록만으로 raw evidence publication PASS가 되지 않는다.

## 9. Gate별 남은 조건
| Gate | 현재 | Owner / 해제조건 |
|---|---|---|
| B1 Architecture selection | HOLD | #34 이권욱 / #35/#38 이하영: version/quota/capacity/egress/access/DNS/cost 실제 입력과 결정 |
| B2 forwarding | CONTRACT CANDIDATE; implementation/runtime pending | #35 이하영 + #37 이재환: exact source tuple/host policy/IaC/positive-negative-recovery |
| B3 stable source | HOLD | #38 이하영/#47 이재환: source mapping/failure-domain test/DB authorization |
| B4 PG01~03 | HOLD | #43 이재환/#38 이하영: portable base+overlay와 arbitrary UID Running/Ready |
| B5 traceability | DELTA/REFRESH CANDIDATE | #112/architecture owner: 최신 input recollect 및 independent code review/lead publication |
| B6 final evidence | HOLD | D21 producer 이권욱, 독립 reviewer 이하영/이재환: raw bytes/cleanup/hash/review/merge |

STATIC 문서/코드 점검 및 MOCK만 해당 범위로 보고한다. CI는 실제 exact-head run별 확인; checks 0건≠PASS. AWS/ROSA PLAN/APPLY/CREATE/RUNTIME 미실행. Architecture Freeze 전 유료 작업 금지.

## 10. 공식 근거 (2026-10-03 조회)
- ROSA 지역/quotas: https://docs.aws.amazon.com/general/latest/gr/rosa.html
- ROSA 비용/Classic footprint: https://aws.amazon.com/rosa/pricing/
- HCP private creation: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-aws-private-creating-cluster
- HCP egress-zero: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-egress-zero-install
- On-Prem private DNS: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-overview-DSN-queries-to-vpc.html
- Inbound resolver: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-forwarding-inbound-queries.html
지원 문서의 예시값은 구현값 아님. CLI/current account read-back과 해당 version의 제약을 최종 승인 전에 다시 결박한다.

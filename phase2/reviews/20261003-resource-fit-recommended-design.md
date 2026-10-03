# Phase 2 단일 권장 구성 — 자원·R/I/T/P 기준
기준시각: 2026-10-03 21:00 KST. 리뷰 반영 revision 3 (원본 후보 HEAD 9850a32, 이전 revision2 c421733). AI: CODEX_ASSISTED.
상태: RECOMMENDED_CANDIDATE / DESIGN_REVIEW=CHANGES_REQUIRED / ARCHITECTURE_FREEZE=HOLD.
이 문서는 담당자가 선택지를 다시 설계하지 않도록 제공하는 구체 입력안이다. 신규 제안은 Decision 승인값이 아니며, 독립 리뷰와 #34/#38 authority 반영 전 구현에 소비하지 않는다.

## 1. 권장 결론
기존 On-Prem DB/Harbor/Runner를 보존하고, application 실행 플랫폼만 ROSA HCP로 변경한다.
권장 모델은 **HCP + 3-AZ private workers + Private API/Ingress + AZ별 NAT egress + 기존 AWS EC2/EIP Relay**다.
이 선택은 workload 이식성을 검증하는 프로젝트 목적에 맞춰 고객 계정 control-plane 운영 범위를 줄인다. control-plane host 접근이나 기존 host 기반 증적이 필수이면 managed-service adapter로 동등 intent를 입증할 수 있는지 먼저 확인한다. 증적 확보 불가를 숨기거나 무결성 요구를 삭제하지 않는다.

## 2. 이미 가진 자원과 미생성 자원
| 자원 | 실제 확인/기존 authority | 이번 사용 |
|---|---|---|
| AWS 계정/조회 역할 | 774055931866; gwonuk의 FDS-ReadOnly-Audit assume 및 EC2/Quota 조회 성공. 다른 2인 MFA/assume 미검증 | 사람 MFA 기반 read-only 조사; 구축 역할과 분리 |
| 서울 EC2 Standard quota | L-1216C47A=100 vCPU 사용자 actual readback | 추가 quota 신청 선행 요구 없음. 다른 quota/실제 용량은 별도 확인 |
| 서울 기존 VPC | vpc-09c8159d7a476bc5c / 172.31.0.0/16 및 기본 subnet 4개 | 프로젝트 VPC로 임의 재사용하지 않음 |
| 프로젝트 cloud 자원 | 조회 범위에서 NAT/VPCE/EC2/EIP 없음; 프로젝트 10.20/16 VPC 미관측 | 아래 신규 구성은 아직 생성되지 않음 |
| Relay AMI | ami-079a2667364cee804, owner 125523088429, available/x86_64/ebs readback | D21 확정 Relay에 사용; ROSA worker AMI로 사용하지 않음 |
| On-Prem DB | db01 10.1.93.55:5432 | P1/P2 동일 DB 계약; 별도 RDS/Cloud DB 신규 도입 없음 |
| Harbor / VPN gateway | Harbor 10.1.93.54:443, vpn-gw01 10.1.93.51 | Registry 후보 재사용 / D21 On-Prem initiator |
| 기존 Runner / DNS | Runner 10.250.10.20, DNS 10.1.93.52/53 설계 입력 | 위치 보존. 실제 권한·route·TLS/readiness 재검증 |
| Shared OCP | 공용 multi-tenant Lab | namespace-local arbitrary UID 실제 Running/Ready 선검증; ROSA 인수 대체 불가 |

On-Prem의 CPU/RAM/스토리지 현재 inventory와 승인 application requests/limits의 완성본은 이번 수집에서 확보하지 못했다. 이미 가진 자원의 용량을 임의 수치로 기입하지 않는다. #43 최신 댓글은 권위 있는 portable deployment base가 아직 없다고 기록한다. fds-msa 코드 검색 무결과도 요청량이 0이라는 근거가 아니다.

## 3. 담당자가 검토할 단일 입력안
| 항목 | 권장 입력 | 승인/검증 경계 |
|---|---|---|
| 모델/리전 | ROSA HCP, ap-northeast-2, 2a/2b/2c | 모델은 신규 권장; Region/AZ mapping은 기존 authority |
| Worker | AZ별 single-AZ MachinePool 1개, 각 1 node; 총 3 × m5.xlarge(4 vCPU/16 GiB), autoscaling OFF | 초기 sizing 제안. 현재 지원 version/type/pool 제약 및 workload capacity 확인 전 동결 불가 |
| Worker root disk | 각 300 GiB encrypted EBS; 지원 volume type/옵션 정확 pin | Red Hat 예제의 값은 sizing 참고일 뿐 프로젝트 승인/최소요건 아님. 앱 데이터 PVC/백업과 분리 |
| VPC/private subnet | 10.20.0.0/16; 10.20.10.0/24, 10.20.20.0/24, 10.20.30.0/24; az1/az2/az3 | 기존 확정값 유지 |
| Public subnet | 기존 public-transport-a 10.20.110.0/24 유지; b=10.20.120.0/24, c=10.20.130.0/24 추가 제안 | b/c는 신규값. a의 NAT/Relay 공존은 역할/route/SG 분리. 선택한 private HCP workflow의 public subnet 제출 요구 확인 |
| Egress | 표준 supported egress; NAT Gateway 각 AZ 1개(총 3), private 기본 route는 같은 AZ NAT | 추가 egress AZ SPOF/cross-AZ 의존성 방지 목적. NAT 자체는 목적지 허용정책이 아님 |
| 필수 외부통신 | 플랫폼 공식 required egress 목록과 앱 최소허용을 분리, 지원되는 통제/관측으로 집행 | zero-egress/완전 air-gap이라고 표현하지 않음. 강제 domain allowlist가 필수이면 지원 proxy/firewall 모델을 결정하기 전 HOLD |
| API/Ingress | 모두 Private; API/OAuth/업무 Route의 인증·TLS 이름 검증 유지 | 실제 endpoint/port는 생성 후 관측. Public 전환이나 TLS 우회로 준비 부족을 해결하지 않음 |
| Private DNS | On-Prem DNS -> inbound Resolver(2 AZ/2 IP); VPC Resolver -> outbound Resolver(2 AZ/2 IP) -> On-Prem DNS 10.1.93.52/53 | 쌍방향 이름 보존 후보. inbound는 API/OAuth/Ingress domain, outbound는 승인 On-Prem zone만 조건부 전달. route/selector/SG/FORWARD/return을 방향별 정의; 총 endpoint IP4 비용 포함 |
| 관리 경로 | 기존 Runner/관리단의 명시된 source -> API/OAuth/Ingress/DNS 최소경로 | Runner 10.250.10.20은 현재 selector 밖. narrow management route/selector 변경결정과 return path를 동결 전 승인; inner SNAT 금지 |
| ROSA version | 해당 계정/리전에서 HCP 생성 가능한 supported stable exact version 1개 pin | 현재 목록을 확보하지 못했으므로 숫자를 발명하지 않음. version별 PrivateLink external access SG 지원 등 확인 |
| Machine/Pod/Service CIDR | machine CIDR=10.20.0.0/16 후보; Pod/Service CIDR/host prefix는 선택한 HCP version/workflow의 read-only 지원 기본값을 수집해 명시 pin | machine CIDR/VPC 정합과 모든 On-Prem/Runner/기존 VPC overlap 검사. 지원 기본값 미조회이므로 숫자 발명 금지; 정확 값은 pre-create 입력 |
| Relay | 기존 t3.medium, 10.20.110.10, AMI 위 값, gp3 40 GiB encrypted, EIP1 | 확정값 유지; public SSH 금지, management SSM 우선; source-dest-check=false, auto IPv4 off. peer는 explicit IKE ID로 인증; dynamic public source용 outer UDP500/4500 ingress 0.0.0.0/0은 D21 위험수용 계약 참조 |
| DB source 모델 | 최소 per-worker source-set + 엄격히 제한된 inventory reconciliation을 우선 설계검토 | 사람의 매 IP 승인이 아니라 source 생성·폐기 규칙과 권한을 사전 승인하는 신규 후보. 구현/독립 리뷰 전 자동 grant 금지; 실제 source 관측과 recovery SLA 검증 전 HOLD |
| Registry | 기존 Harbor primary 재사용 권장, approved immutable digest와 TLS/pull-only robot | D22 미확정. HCP registry-config-additional-trusted-ca에 hostname→공개 CA PEM JSON, pull-only robot secret은 승인 앱 namespace/SA 범위. TLS/firewall/audience 잔여 해소 및 실제 cold-pull 전 READY 아님; insecure 우회 금지 |
| Workload | 하나의 Kubernetes base + OpenShift overlay; 동일 API/engine business contract | image digest, probes/ports, requests/limits를 실제 source와 연결 |
| State | network / vpn / rosa-prereq / rosa-runtime; S3 native use_lockfile=true | exact bucket/key/권한/보존을 plan 전 고정; Secret 원문 저장·출력 금지 |

3-worker는 총 12 vCPU/48 GiB의 **물리 사양**이다. 플랫폼/OS reserved와 DaemonSet/Ingress/monitoring/registry 사용량을 빼기 전 수치다. Kubernetes node allocatable에는 OS/system reservation이 이미 반영될 수 있으므로 이를 두 번 차감하지 않고, allocatable에서 실제 platform requests와 app/surge/recovery requests를 비교한다.
1-worker 상실 시 남는 물리 사양 8 vCPU/32 GiB만으로 N-1 용량 PASS를 선언하지 않는다.
동결 수용식: 승인 앱 requests + 배포 surge + 복구 여유가 남은 worker allocatable에서 platform requests를 제외한 용량에 들어가야 하고, topology/PDB/replica/volume constraints까지 배치 가능해야 한다. Freeze 전에는 지원 사양과 P1 live 요청량으로 사전 산정하고, 생성 후 실제 allocatable로 재검증한다.
이 검증이 실패하면 같은 모델에서 worker type/count를 재산정하고 비용표·Decision을 갱신한다. m5.2xlarge를 자동 승인 fallback으로 만들지 않는다.
Relay 단일 SPOF는 D21의 기존 수용 범위다. NAT3/worker3이 전체 경로 HA를 의미하지 않는다. 재기동/rekey/rebuild 시험은 유지한다.

## 4. R/I/T/P 심층 적합성 및 훼손 방지
| 기준 | 유지할 계약 | 설계상 보존 방법 / PASS 증거 |
|---|---|---|
| 무결성 | 같은 approved image/업무 처리/DB 기대 결과/최소 보안 | digest 배포, scan·provenance, non-root/no-escalation/RO rootfs/RuntimeDefault/drop ALL, DB auth/TLS/NetworkPolicy; API→engine→DB 행/이력과 기존 기대값 비교 |
| 추적성 | Decision→Issue→source→실행→raw→hash→독립review | exact SHA와 KST, 환경/host/command/RC, 변경 사유, raw/manifest/cleanup. 실제 관측·모의·승인 상태를 분리 |
| 재현성 | 삭제·재생성·배포·복구 후 같은 계약 성립 | pin된 IaC/tool/provider/version/이미지/설정, state 4경계, reviewed plan, source-set 갱신 규칙, 재생성 후 positive/negative 및 integrity 재검증 |
| 이식성 | AWS/ROSA 값은 adapter, workload/security/evidence intent는 공통 | K8s base와 OpenShift Route/SCC/DNS/storage/managed-control-plane adapter 분리; arbitrary UID 실제 실행; provider hostname/IP/UID를 canonical workload로 승격하지 않음 |

동일 digest의 arbitrary UID 실행을 먼저 시험한다. 실제 실패로 image 수정이 필요하면 새 digest/scan/lineage를 만들고 Phase1과 Phase2 양쪽 회귀를 수행한다. fixed UID 제거나 admission PASS는 Runtime PASS가 아니다.
Managed ROSA Secret/etcd encryption, key ownership/IAM/deletion, backup/restore, audit/monitoring 증적을 Phase1 intent에 매핑해야 한다. EBS encryption으로 이 통제가 모두 PASS라고 쓰지 않는다.
P1/P2 동일 DB 시험은 test ID/account/mutation window/migration owner/expected rows/보존·정리를 공유 계약으로 관리한다. HTTP200만으로 data integrity PASS 처리 금지.

### 최소 forwarding/source 계약
- transaction-api 승인 path -> db01 TCP5432만; fds-engine -> DB DENY. engine에는 DB credential을 배포하지 않는다.
- Relay SG + Relay host FORWARD + vpn-gw01 FORWARD + DB firewall/pg_hba를 같은 versioned tuple manifest에서 인계한다.
- authenticated IPsec SA/policy와 승인 source/destination/port/direction을 모두 확인. 나머지 신규 forwarding default deny.
- selector 10.1.93.0/24↔10.20.0.0/16은 transport envelope; application allowlist가 아니다.
- gateway inner SNAT/masquerade/DNAT 금지. Internet NAT와 CNI 관측 source-transform을 별도 계약으로 기록.
- node-source 공유 시 IP alone은 API/engine을 구별 못한다. 모든 additive NetworkPolicy와 DB 인증을 함께 검증한다.
- source-set은 승인 cluster/pool/AZ/subnet/ENI provenance와 actual source mapping으로 생성한다. 태그만으로 승인하지 않는다. 기존 매 IP 사람 승인 절차는 자동 worker 교체와 충돌하므로 대체 후보: source 분류·갱신 규칙/최대 cardinality/overlap 수/권한을 사전 독립 승인→inventory reconciliation→DB/gateway/Harbor(각 actor·port 별도) 동기화 readback→업무 검증→퇴역 source 제거. 구현 미완료 상태에서 자동 grant는 금지한다. 미분류 IP/과대 set/API 오류/동기화 불일치 시 fail-closed와 alert; broad /24 자동 fallback 금지.
- 갱신 platform inventory producer=#38, network/VPN 정책=#37, DB/Harbor 소비·검증=#47와 #42. 이재환 1인의 수동 IP 승인에 복구를 의존하지 않도록 운영 권한/대체 담당/실패복구와 최대 갱신·서비스 복구시간(SLA)을 #38/#47에서 Freeze 전 승인한다. SLA 수치와 자동화 구현은 PENDING. source revision/전후 diff/expiry/raw RC/negative test를 보존한다. autorepair를 무조건 끄거나 지원 업그레이드를 차단해 해결하지 않는다.
- Harbor443은 D22 승인 후 node image-pull source에만. Private DNS/API는 별도 승인 관리 flow이며 DB envelope에 몰래 포함하지 않는다.
- SELinux Enforcing/firewall/TLS 유지. SA down/plaintext/new-source/engine/미허용 port 부정시험과 Pod 재배치/worker replacement/VPN복구 후 정합 시험 필수.

## 5. 비용과 일정: 담당자가 사용할 계산 기준
교육장 한도 준수 + 매일 사용금액 리포트가 사용자 최신 합의다. 별도 교육장 유료구축 승인이나 팀 Billing/CE/Budget 관리자 권한을 선행조건으로 만들지 않는다.
기존 문서의 $400/$450/$500는 역사/내부 정책 입력이며 교육장 한도와의 일치는 미확인이다. 정확한 교육장 한도·기간·리포트 data source를 기존 기록과 대조해 현행 cost authority를 정렬한다. 미조회 금액은 0이 아니다.
12 worker vCPU의 ROSA service fee는 3×$0.171 + HCP $0.25 = **$0.763/시간 (ROSA service fee만, 총액 아님)**. 24시간 $18.312; 192시간 예시 $146.496. 이는 service fee만이다.
192시간은 단가 비교 시나리오이며 실제 사용시간 승인이나 기존 10-15 Basic Ready/10-19 Full/10-22 후속 일정을 대체하지 않는다.

전체 비용표에는 다음을 포함한다:
- m5.xlarge×3 + Relay t3.medium; worker EBS 총900 GiB + Relay40 GiB, 실제 볼륨 종류/시간.
- NAT3의 hourly/data processing, Relay EIP1 + NAT public IPv4 최소3, 추가 실제 public IPv4.
- Resolver inbound2 + outbound2=총4 IP: 공식 $0.125/ENI-hour 기준 $0.50/h, 192h=$96 + query. inbound만이면 $0.25/h/$48이나 outbound를 삭제한 승인 설계 변경 없이는 이 낮은 금액을 채택하지 않는다. internal LB/PrivateLink/endpoints와 processing 별도.
- state/evidence/backup storage, KMS/로그/전송/cross-AZ, subscription/support 조건 및 cleanup residual.
- replacement/upgrade surge, 실패 재시도와 teardown 시간. 서울 현재 단가와 교육장 actual/accrual을 확인 후 total-to-complete 산정.

한도를 넘으면 security를 약화하거나 NAT3→1을 조용히 변경하지 않는다. 유휴 시간/시험 순서/해당 위험수용 Decision을 조정하고 다시 검토한다.
ROSA 실제 runtime은 불필요하게 일찍 만들지 않고 Shared OCP 선검증·코드·raw intake를 먼저 준비한다. teardown은 증적 보존 후 수행하고 NAT/EIP/endpoint/EBS/LB 잔여까지 확인한다.


### DNS·Registry·source·스토리지 보완 계약
- 이름 보존 권장: Harbor/DB의 기존 승인 FQDN을 사용하며 On-Prem authoritative DNS로 outbound conditional forwarding. 정확 FQDN/zone/TLS SAN을 P1 원본에서 확인한다. Harbor를 IP로 바꾸거나 hosts 고정/Pod DNS의 임의 전면 변경으로 TLS/DNS 의존성을 숨기지 않는다. inbound domain과 outbound On-Prem zone을 분리해 forwarding loop를 부정시험한다.
- outbound Resolver source는 endpoint ENI IP set이며 worker source-set과 다르다. 목적지 DNS52/53 TCP/UDP53만, 승인 return route/SA에 결박한다. inbound DNS source도 On-Prem resolver52/53이며 Runner source10.250.10.20과 다르다. 관리 selector 추가결정과 기존 DNS flow 모두 explicit tuple로 관리.
- HCP CA 주입 우선 경로: 공식 `rosa create/edit cluster --registry-config-additional-trusted-ca <JSON-file>`; registry hostname를 key로 public CA PEM을 value로 작성. 정확 CLI/OCM version 지원과 생성 시 CA 입력을 먼저 pin한다. 이 예시는 실행 승인이 아니며 create/edit 미실행.
- CA는 trust anchor 공개 인증서만; private key·robot token은 CA JSON에 넣지 않는다. namespace pull secret은 안전한 별도 secret 전달/최소 SA 참조; 원문 출력/commit 금지. `image.config.openshift.io` 직접 편집을 HCP의 지원 API로 가정하지 않는다.
- 공식 HCP 문서상 registry 설정 변경은 전체 MachinePool rollout/노드 재생성을 유발할 수 있다. CA를 생성 전 준비하고, 사후 변경은 worker source reconciliation·Harbor allowlist·surge capacity·동일 digest cold-pull을 같이 리뷰한다. CA/SAN 오류 negative, pull-only push DENY, replacement 뒤 cold-pull 및 no-insecure 확인.
- 최소 per-worker 자동갱신 후보와 EgressIP/전용 subnet source 모델 비교를 Freeze 전 #38/#47에서 마무리한다. EgressIP는 Pod traffic과 kubelet node image-pull을 하나로 해결하지 않으므로 Harbor source는 별도 유지. 공식 ROSA tutorial/Classic 문서의 HCP 언급만으로 현재 계정·버전 지원과 cross-AZ failover를 PASS로 확정하지 않는다.
- 전용 subnet source 모델은 다른 ENI 배제 조건부터 검증해야 한다. 현재 private subnet에는 worker 외 Resolver/PrivateLink/LB ENI도 필요할 수 있으므로 '다른 ENI 없음'을 사실로 채택하거나 기존 /24를 바로 DB 허용하지 않는다.
- 앱 storage 분류: transaction-api/fds-engine의 업무 정본은 On-Prem DB에 보존; 임시 쓰기는 승인 최소 emptyDir. 실제 P1 live PVC 사용 여부를 read-only로 확인한다. 새 durable app PVC를 임의 추가하지 않는다.
- EBS PVC는 AZ 제약이 있어 반대 AZ로 볼륨을 즉시 이동할 수 있다고 가정하지 않는다. PVC actor/StorageClass/binding/accessMode/zone·backup·restore·RPO/RTO를 목록화하고 같은 AZ replacement 또는 승인 restore를 인수한다. worker OS300GiB를 앱 백업으로 간주하지 않는다. 플랫폼 자체 PVC/monitoring도 용량·복구 목록에 포함한다.
- Relay 장애는 DB·Harbor cold-pull·VPN 경유 DNS에도 영향. replacement와 Relay outage가 겹치는 순서, DNS timeout/cache TTL, cached image 의존 제거를 시험하고 회복 후 approved positives/engine negative/data rows를 재확인한다.
- D21 dynamic public source 관측은 pathcheck 수준이며 인증된 production Child SA 지속성을 증명하지 않는다. public source 변경 중 장시간 유지/rekey/DPD 복구를 #37 production runtime gate로 남긴다. Freeze 전에는 시험 방법·시간·판정·책임을 고정; 아직 미생성 tunnel의 성공을 Freeze 입력으로 요구하지 않는다.
- #37 [인수순서1~10](https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5964501246)을 소비하며 db01 return10.20/16 via10.1.93.51을 readback. Issue 제목의 managed Site-to-Site 용어는 이재환 Lead의 D21 scope 정렬 handoff로 남기며 이번 문서에서 서비스 자체를 재선정하지 않는다.

### Account readiness / quota 완료조건
- ELB service-linked role: 최신 제공 증적은 successful ListRoles exactname=[] 및 자동 CreateServiceLinkedRole DENIED. #35 이하영이 재조회→exact role/service·IAM 영향·독립 review→권한이 있는 account bootstrap 실행자에게 인계→GetRole/ListRoles readback. 실행 주체는 reviewed bootstrap 담당으로 고정해야 하며 FDS-ReadOnly-Audit에 write를 추가하지 않는다.
- ELB role 준비는 유료 infra create 전 완료할 account gate. AWS/RedHat linkage/subscription/support/STS-OIDC/SCP/operator IAM 모두 확인 후 인계. 계정 준비 완료와 Architecture Freeze를 구분하며 현재 write 실행 미수행.
- 이름별 quota: EC2 Standard on-demand vCPU(applied100), EC2-VPC EIP(계획 Relay1+NAT3=4 + account 사용량/교체 여유), VPC/IGW/NAT gateways per AZ/ENI, subnet available IPs, EBS 선택 volume-type storage/IOPS/snapshots, ELB NLB/ALB/targetgroups/listeners, Route53 Resolver endpoints/IPs/rules, PrivateLink interface endpoints/SG per ENI. 실제 supported architecture의 required quota 리스트와 대조한다. 100vCPU/console summary를 이 전체 PASS로 확대하지 않는다.

### Cost-to-complete 입력표와 계산
| 비용 항목 | 수량 | 단가/현재 상태 |
|---|---:|---|
| ROSA service | worker12vCPU + HCP1 | $0.763/h 공개가격 재조회 필요시 유지 |
| Resolver endpoint IP | inbound2+outbound2 | $0.125/IP-h ×4=$0.50/h, query 별도 |
| EC2 | m5.xlarge3 + t3.medium1 | 서울 Linux On-Demand SKU/단가 PENDING |
| EBS root | worker900GiB + Relay40GiB | worker volume type/서울 GB-month 단가 PENDING; PVC 별도 |
| NAT | 3 | 서울 hourly/GB 처리 단가 PENDING |
| Public IPv4 | 최소4 | 현재 공식 단가/SKU 대조 PENDING; 추가 allocation 포함 |
| LB/PrivateLink/기타 endpoints | 지원 모델의 실제 필요 수 | 수량·hour/processing PENDING |
| Variable/residual | transfer/queries/log/storage/KMS/surge/cleanup | 사용량·단가·최소/보수 추정 PENDING |

확인된 service+DNS 고정 소계만 **$1.263/h**, 192h=$242.496이다. 이것도 총액 아님. 미확인 단가를 0으로 대체하지 않는다.
총 고정 hourly `F=1.263 +3*p_m5+1*p_t3+EBS_hour+3*p_nat+4*p_ipv4+LB_hour+VPCE_hour+other_fixed`.
EBS GB-month 단가는 공급자 prorating 기준으로 hour 환산하고 사용시간이 다르면 자원별 시간을 곱한다.
허용 동일 가동시간 `H_max=(education_limit-accrued-variable_reserve-cleanup_reserve)/F`(분자≤0이면 추가 소비 STOP); 한도·잔여·단가 미확인이면 H_max=PENDING.
실제 비용은 자원별 running hours·surge 및 account 교육장 집계를 연결한다. $400 안팎 같은 리뷰의 미검증 추정은 예산 GO 근거로 사용하지 않는다.
이권욱은 교육장 한도/기간/일일 리포트 근거 연결; 이하영은 architecture count·서울 SKU와 계산표 재검증. 팀 Billing권한이 없어도 교육장 제공 수치로 가능하나 실제 제공 없이는 accrued를 발명하지 않는다.

## 6. 담당자별 바로 할 일과 완료조건
| 담당 | 다음 행동 | 완료조건 |
|---|---|---|
| 이권욱 #34/#40/#42 | 이 단일안의 R/I/T/P 동등성·관리 DNS/route subset·Harbor logical D22 입력·비용 계약 정렬 | 지원/용량/보안 차이를 Decision에 명시, 독립 리뷰, exact inputs 반영; 스스로 independent approval 금지 |
| 이하영 #35/#38 | 계정 HCP stable version/type·AZ offering·named quota/support/subscription/link/STS-OIDC, ELB role, sizing·source reconciliation·registry CA 지원 확인; network/IAM IaC 준비 | read-only 원본+capacity/cost 표; ELB role 미존재/activation UNVERIFIED 해소는 별도 reviewed bootstrap; exact input/plan 검토 |
| 이재환 #37/#43/#47 | P1 live 요청량·replica/probe/port/PVC read-only 수집, portable base/UID; #37 peer ID·Libreswan·양 gateway forwarding·db01 return route와 인수순서1~10; source/DB·VPN복구 | LAB 실제 Running/Ready/업무 증적, source-set 갱신/negative test 구현; ROSA에서는 새로 runtime 인수 |
| 사용자 이권욱 | 현 read-only 역할로 지원 version/type/계정 상태 수집 지원; 교육장 안내 한도·기간·일일 리포트 근거 연결; D21 final raw 제공 | 토큰/PSK/key 원문 없는 원본 관측과 final raw hash/size 검증. 같은 개인 MFA 조회를 다시 수행할 필요 없음 |
| 산출물별 독립 Reviewer | 변경된 최신 HEAD의 설계/코드/증적 범위 리뷰 | 실제 승인 기록. Terraform#3 승인과 evidence#104 승인은 해당 exact HEAD/기존 scope에만 적용 |

P1 live 입력 handoff: #43 본 작업(10-16~19)보다 먼저 #34 최초 Freeze 심사 전에 requests/limits·replica·probe·port·PVC/source revision을 수집한다. 제안 checkpoint는 10-12 18:00 KST이며 Lead 일정 확정은 PENDING; 기존 #43 start/end/AC를 앞당겨 변경한 것이 아니다. 이재환의 즉시 read-only 준비 의사를 소비한다. API access/RBAC 부족이면 원본 error/RC와 수집 가능 항목을 남기고 capacity HOLD. missing request/limit를 0으로 처리하지 않고 LimitRange/defaulted actual spec과 관측 peak를 구분한다.

D22는 logical registry/trust/credential/digest/fallback 계약을 Freeze 전 준비하고 실제 cluster endpoint/cold-pull 결과는 Basic Ready 이후 완성한다. 현재 10-15 Final 일정·AC를 임의 수정하지 않고 단계별 authority 차이를 기록한다.
D23 전체 P1 기능을 P0로 변경하지 않는다. Private 접속의 mandatory DNS subset만 pre-create 계약에 포함한다.


### 추가 리뷰 반영: CLI/콘솔 조회 및 증적 수집
하영 [추가 의견](https://github.com/321Team/fds-project-architecture/pull/8#issuecomment-5968593648)의 조회방법·credential/민감정보·team전체setup부담을 보완했다.
권장: 기존 MFA FDS-ReadOnly-Audit **CloudShell 1인 실행**으로 AWS고정조회 원본/RC/KST/hash 수집 + Red Hat 콘솔의 HCPversion/type/연결상태 별도 관측. 팀원 전체 로컬CLI설치나 새 장기키/ROSA토큰 저장을 선행조건으로 만들지 않는다.
[실행·증적 handoff](../runbooks/20261003-readiness-evidence-capture.md), [AWS read-only script](../runbooks/phase2-readiness-capture.py).
수집자는 하영 #35/#38 Lead 또는 이미 역할세션 가능한 권욱 대행. 실제 수집/계정결과 판단/증적review는 미완료.
- 이미 확인한 EC2Standard100/AMI/VPC를 재시험하는 대신 미확인 EIP/NAT등quota·현재EIP/NATusage·ELBrole·EC2offering/type만 고정조회한다. PrincipalSTS는 매실행guard이므로 다시 확인한다.
- 예상account/assumedrole/member guard; root/다른계정·role/session STOP. commandargs고정, AWSwrite/ROSA호출/권한확대/토큰처리 없음. globalIAMmetadata+regionalAWS범위 구분.
- AWSCLI원본과 CONSOLE_OBSERVATION은 다른증적. screenshot도 SHA검증가능하지만 파일무결성만 입증하며 actualAPI진실성/전체runtime준비를 입증하지 않는다.
- raw에 accountID/ARN/IPmetadata가 포함될 수 있어 자동Git편입 금지. 원본보존+접근제한, 검토후sanitized derivative에 원본/파생sha·size와field별provenance 기록. Secrets/token/PSK/privatekey 발견시 publicationSTOP. cache/env/HAR/cookie/token을 수집하지 않는다.
- RedHat권한은 AWSreadonly와 별개. 이번 collector에는 rosa list/verify/create/login조차 포함하지 않으며 exactsupport는console관측+공식constraints와대조.
- readonlyscript는 실제계정에 실행하지 않았고 로컬 AST+5개MOCK경로만 검증했다. 조회RC0는수집완전성일뿐 GO아님; GetRoleDENIED와 ListRolesempty 구분. 부분실패/timeout은RC/원본을 보존해 PENDING으로인계.
이 절차는 PR8의 현재준비조회 handoff이며 개인협업지침을 새팀공용정책으로 승격하지 않는다.

## 7. 설계 고정과 후속 절차
1. 아래 남은 입력을 채우고 신규 후보값을 #34/#38 및 해당 Decision에 독립 검토와 함께 승인한다.
2. 현재 HOLD 해소를 확인한 뒤 Architecture Freeze를 기록한다. 선택한 모델/보안 계약을 고정하고 actual IDs는 post-create evidence로 남긴다.
3. author branch IaC/portable base 구현→static/CI→독립 code review→exact backend/권한과 계획 검토.
4. Freeze 이후 승인 범위에서 구축→Basic Ready→ROSA runtime/복구/동일 DB 정합 인수.
5. evidence 원본 검증→독립 evidence review→필요 gate 충족 시 merge→current architecture/정본 publication. 단계별 상태를 분리한다.

잔여 차단:
- supported exact version/type/AZ/pool 조건, 승인 requests/limits와 N-1 capacity, CIDR/egress 필수목록·집행 계약.
- Private management route/selector/return + DNS + external PrivateLink SG 지원 계약.
- Harbor TLS/firewall/audience, arbitrary UID actual execution, managed encryption/recovery/관측 동등성.
- 교육장 한도·기간과 서울 full total-to-complete/허용 가동시간, subscription/link/STS-OIDC 및 구축 권한.
- ELB service-linked role account gate: absent 관측 + create denial을 reviewed bootstrap/actual readback으로 해소; EIP4와 이름별 quota 확인.
- per-worker source reconciliation 구현·권한·SLA, Harbor HCP CA 입력, 양방향 DNS 및 AZ고정 PVC 복구 계약. production SA의 동적 source 지속성·복합장애 인수는 Freeze 후 actual runtime gate.
- D21 final raw/cleanup integrity intake 및 현재 snapshot·authority 정렬(B5/B6).
이 목록은 runtime IP가 없다는 이유로 Freeze를 순환 차단하는 것이 아니다.

## 8. 리뷰별 처리 상태
| 리뷰 지적 | 반영 내용 | 현재 판정 |
|---|---|---|
| 재환1 source 자동교체 | per-IP 사후 사람승인 대신 사전 승인 rule+제한 inventory reconciliation 후보, EgressIP/subnet 비교·node-pull 분리 | 설계 보완, 모델승인·구현·SLA·runtime PENDING |
| 재환2 dynamic public IP | explicit IKE ID/outerUDP500·4500 0/0/D21 risk 및 장시간·DPD/rekey 인수 | 문서 누락 보완; production runtime NOT_RUN |
| 재환3 CA | HCP 공식 create/edit registry CA JSON 경로, pull secret 범위, rollout/source 영향 | 공식 경로 확인; exact account support/cold-pull PENDING |
| 재환4/5 inputs·VPN 담당 | pre-Freeze read-only P1 sizing checkpoint 제안, #37 인수1~10과 return route/peer/FORWARD 명시 | 담당 연결 보완; 날짜확정·원본수집·실행 PENDING |
| 재환6 표현 | publicSSH금지/SSM우선, machine CIDR, service-only 바로 표시 | 문구 보완 |
| 하영1 DNS | inbound+outbound 4IPs, 도메인/방향/source/return/loop 방지 | 설계 후보 보완; exact zone/route Decision PENDING |
| 하영2 비용 | full항목·hourly공식·H_max, DNS 가격·소계 | 미검증 total을 발명하지 않음; 서울 나머지 단가/한도 입력 PENDING |
| 하영3 PVC | OSdisk vsPVC 분리, AZ affinity/분류/restore/RPO-RTO | 검증계약 보완; live PVC inventory/실제복구 PENDING |
| 하영4 계정 | ELBrole 생성주체/준비gate·명칭별quota/EIP4 | handoff 보완; successful bootstrap/readback PENDING |

추가 하영CLI/콘솔의견: 단일실행자/고정AWS조회/raw+hash/ROSA별도관측/민감정보분리 절차와 실제copy가능한 collector 준비. 절차·코드작성 STATIC/MOCK만 완료, AWS actual수집·독립코드review는 PENDING.

기존 reviewer COMMENTED/의견은 APPROVED가 아니며, 이 revision의 독립 재리뷰가 필요하다. reviewer의 미확인 autorepair/EgressIP/가격 주장도 actual 지원/관측 전 확정하지 않는다.

## 8.1 최신 확인과 상태
조회 HEAD: architecture#8 ca0779ae4f4f9b3dc40c2cceef8badec242e3a71; infra-rosa#2 f5f0db1c50e83b7c9bb5242de9090fdd15cf5720.
#38/#42/#43/#47 댓글을 재조회했다. 이전 deep review와 unresolved register를 대체 삭제하지 않으며 이 파일의 신규 후보 sizing/NAT/subnet/source 갱신 규칙을 추가 리뷰 대상으로 둔다.
STATIC=문서 논리·권위/수치/상태 대조; CI=이 신규 설계 후보에 대한 실행 NOT_RUN; RUNTIME=ROSA/production Child SA/이 구성 NOT_RUN.
IAM user supplied runtime read scope PASS는 유지. ROSA page의 자동 CreateServiceLinkedRole 시도는 OBSERVED_DENIED이며 성공 구축 아님.
REVIEW=신규 설계 독립 승인 PENDING; MERGE=NOT_RUN; PUBLICATION=author branch GitHub candidate만, main/정본 release 미발행.
D21 expected final: 8706 bytes / e5f754a3d66c6fe452605ff914a6294e87aa85bf6a345ec0fadb981f18745cb0. raw 재해시 미수행; intermediate bdcd9564...는 canonical 아님.

## 9. 근거
- [현재 #38 authority](https://github.com/321Team/fds-project-baseline/issues/38), [#43 base 상태](https://github.com/321Team/fds-project-baseline/issues/43#issuecomment-5948126338), [#47 source contract](https://github.com/321Team/fds-project-baseline/issues/47).
- [R/I/T/P deep review](20261003-design-ritp-deep-review.md), [미확정 register](20261003-unresolved-design-register.md).
- [AWS HCP 생성/네트워크 공식 문서](https://docs.aws.amazon.com/rosa/latest/userguide/getting-started-hcp.html): 표준 workflow의 AZ별 public/private, NAT 권고 및 supported offerings 조회. exact private workflow/version과 조정 필요.
- [Red Hat worker 예제](https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/learning_about_rosa/creating-a-cluster-workshop): m5.xlarge/300GiB 예제. 예제 version4.14.36을 현재 승인값으로 사용하지 않음.
- [AWS M5 사양](https://aws.amazon.com/ec2/instance-types/m5/), [ROSA service 가격](https://aws.amazon.com/rosa/pricing/).

- [재환 exact-head 리뷰](https://github.com/321Team/fds-project-architecture/pull/8#pullrequestreview-5400010956), [하영 리뷰 의견](https://github.com/321Team/fds-project-architecture/pull/8#issuecomment-5968359308).
- [HCP registry CA 및 rollout 공식](https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/images/image-configuration-hcp), [DNS 쌍방향 endpoint 공식](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-choose-vpc.html), [Resolver 가격](https://aws.amazon.com/route53/pricing/).

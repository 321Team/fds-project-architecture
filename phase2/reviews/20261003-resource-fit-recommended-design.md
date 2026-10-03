# Phase 2 단일 권장 구성 — 자원·R/I/T/P 기준
기준시각: 2026-10-03 18:17 KST. AI: CODEX_ASSISTED.
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
| VPC/private subnet | 10.20.0.0/16; 10.20.10/20/30.0/24; az1/az2/az3 | 기존 확정값 유지 |
| Public subnet | 기존 public-transport-a 10.20.110.0/24 유지; b=10.20.120.0/24, c=10.20.130.0/24 추가 제안 | b/c는 신규값. a의 NAT/Relay 공존은 역할/route/SG 분리. 선택한 private HCP workflow의 public subnet 제출 요구 확인 |
| Egress | 표준 supported egress; NAT Gateway 각 AZ 1개(총 3), private 기본 route는 같은 AZ NAT | 추가 egress AZ SPOF/cross-AZ 의존성 방지 목적. NAT 자체는 목적지 허용정책이 아님 |
| 필수 외부통신 | 플랫폼 공식 required egress 목록과 앱 최소허용을 분리, 지원되는 통제/관측으로 집행 | zero-egress/완전 air-gap이라고 표현하지 않음. 강제 domain allowlist가 필수이면 지원 proxy/firewall 모델을 결정하기 전 HOLD |
| API/Ingress | 모두 Private; API/OAuth/업무 Route의 인증·TLS 이름 검증 유지 | 실제 endpoint/port는 생성 후 관측. Public 전환이나 TLS 우회로 준비 부족을 해결하지 않음 |
| Private DNS | On-Prem DNS -> Route53 Resolver inbound endpoint, 최소 2 AZ/2 IP; source DNS 서버만 TCP/UDP53 | 유료 endpoint 비용 포함. VPC CIDR+2 직접 forwarding 금지; 필요한 domain만 조건부 전달 |
| 관리 경로 | 기존 Runner/관리단의 명시된 source -> API/OAuth/Ingress/DNS 최소경로 | Runner 10.250.10.20은 현재 selector 밖. narrow management route/selector 변경결정과 return path를 동결 전 승인; inner SNAT 금지 |
| ROSA version | 해당 계정/리전에서 HCP 생성 가능한 supported stable exact version 1개 pin | 현재 목록을 확보하지 못했으므로 숫자를 발명하지 않음. version별 PrivateLink external access SG 지원 등 확인 |
| Pod/Service CIDR | 생성 workflow의 supported defaults를 명시적으로 export/pin, 기존 연결망 전체와 overlap 검사 | exact CIDR/host prefix는 사전 네트워크 inventory와 지원값 확인 후 입력. runtime IDs와 다른 pre-create 입력 |
| Relay | 기존 t3.medium, 10.20.110.10, AMI 위 값, gp3 40 GiB encrypted, EIP1 | 확정값 유지; no public SSH/SSM, source-dest-check=false, auto IPv4 off |
| DB source 모델 | 승인 worker inventory에 결박된 최소 source-set과 controlled replacement 갱신 | 한 번 본 IP/whole VPC 고정 금지. actual CNI source 관측 후 모델 일치 여부 인수; 미일치하면 HOLD |
| Registry | 기존 Harbor primary 재사용 권장, approved immutable digest와 TLS/pull-only robot | D22 미확정. P1 TLS/firewall/audience 잔여 해소 전 READY 아님. fallback은 same digest·별도 trust/credential 승인된 후에만 |
| Workload | 하나의 Kubernetes base + OpenShift overlay; 동일 API/engine business contract | image digest, probes/ports, requests/limits를 실제 source와 연결 |
| State | network / vpn / rosa-prereq / rosa-runtime; S3 native use_lockfile=true | exact bucket/key/권한/보존을 plan 전 고정; Secret 원문 저장·출력 금지 |

3-worker는 총 12 vCPU/48 GiB의 **물리 사양**이다. 플랫폼/OS reserved와 DaemonSet/Ingress/monitoring/registry 사용량을 빼기 전 수치다.
1-worker 상실 시 남는 물리 사양 8 vCPU/32 GiB만으로 N-1 용량 PASS를 선언하지 않는다.
동결 수용식: 승인 앱 requests + 배포 surge + 복구 여유가 실제 남은 worker allocatable에서 platform 예약분을 뺀 용량에 들어가야 하고, topology/PDB/replica/volume constraints까지 배치 가능해야 한다.
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
- source-set은 승인 worker provenance/tag/inventory와 actual source mapping으로 생성한다. replacement: 새 source 관측→정책 diff/승인→DB/gateway 동기화 readback→업무 검증→퇴역 source 제거. 임의 /24 확대나 미승인 자동 grant 금지.
- 갱신 담당 #38/#47, revision/변경량/유효기간/negative test를 보존한다. 갱신 지연의 fail-closed 업무중단 가능성은 복구 절차와 인수에 포함한다.
- Harbor443은 D22 승인 후 node image-pull source에만. Private DNS/API는 별도 승인 관리 flow이며 DB envelope에 몰래 포함하지 않는다.
- SELinux Enforcing/firewall/TLS 유지. SA down/plaintext/new-source/engine/미허용 port 부정시험과 Pod 재배치/worker replacement/VPN복구 후 정합 시험 필수.

## 5. 비용과 일정: 담당자가 사용할 계산 기준
교육장 한도 준수 + 매일 사용금액 리포트가 사용자 최신 합의다. 별도 교육장 유료구축 승인이나 팀 Billing/CE/Budget 관리자 권한을 선행조건으로 만들지 않는다.
기존 문서의 $400/$450/$500는 역사/내부 정책 입력이며 교육장 한도와의 일치는 미확인이다. 정확한 교육장 한도·기간·리포트 data source를 기존 기록과 대조해 현행 cost authority를 정렬한다. 미조회 금액은 0이 아니다.
12 worker vCPU의 ROSA service fee는 3×$0.171 + HCP $0.25 = **$0.763/시간**. 24시간 $18.312; 192시간 예시 $146.496. 이는 service fee만이다.
192시간은 단가 비교 시나리오이며 실제 사용시간 승인이나 기존 10-15 Basic Ready/10-19 Full/10-22 후속 일정을 대체하지 않는다.

전체 비용표에는 다음을 포함한다:
- m5.xlarge×3 + Relay t3.medium; worker EBS 총900 GiB + Relay40 GiB, 실제 볼륨 종류/시간.
- NAT3의 hourly/data processing, Relay EIP1 + NAT public IPv4 최소3, 추가 실제 public IPv4.
- Resolver inbound 2 IP hourly/query, internal load balancer/PrivateLink/endpoints와 processing.
- state/evidence/backup storage, KMS/로그/전송/cross-AZ, subscription/support 조건 및 cleanup residual.
- replacement/upgrade surge, 실패 재시도와 teardown 시간. 서울 현재 단가와 교육장 actual/accrual을 확인 후 total-to-complete 산정.

한도를 넘으면 security를 약화하거나 NAT3→1을 조용히 변경하지 않는다. 유휴 시간/시험 순서/해당 위험수용 Decision을 조정하고 다시 검토한다.
ROSA 실제 runtime은 불필요하게 일찍 만들지 않고 Shared OCP 선검증·코드·raw intake를 먼저 준비한다. teardown은 증적 보존 후 수행하고 NAT/EIP/endpoint/EBS/LB 잔여까지 확인한다.

## 6. 담당자별 바로 할 일과 완료조건
| 담당 | 다음 행동 | 완료조건 |
|---|---|---|
| 이권욱 #34/#40/#42 | 이 단일안의 R/I/T/P 동등성·관리 DNS/route subset·Harbor logical D22 입력·비용 계약 정렬 | 지원/용량/보안 차이를 Decision에 명시, 독립 리뷰, exact inputs 반영; 스스로 independent approval 금지 |
| 이하영 #35/#38 | 계정 HCP stable version/instance type·AZ offering·quota/support/subscription/link/STS-OIDC와 exact worker sizing 확인; network/IAM IaC 준비 | read-only 원본+capacity/cost 표; ELB role 미존재/activation UNVERIFIED 해소는 별도 reviewed bootstrap; exact input/plan 검토 |
| 이재환 #37/#43/#47 | 승인 base requests/limits·arbitrary UID 실제 실행, tuple/source-set/DB 공유 시험·복구 구현 | LAB 실제 Running/Ready/업무 증적, source-set 갱신/negative test 구현; ROSA에서는 새로 runtime 인수 |
| 사용자 이권욱 | 현 read-only 역할로 지원 version/type/계정 상태 수집 지원; 교육장 안내 한도·기간·일일 리포트 근거 연결; D21 final raw 제공 | 토큰/PSK/key 원문 없는 원본 관측과 final raw hash/size 검증. 같은 개인 MFA 조회를 다시 수행할 필요 없음 |
| 산출물별 독립 Reviewer | 변경된 최신 HEAD의 설계/코드/증적 범위 리뷰 | 실제 승인 기록. Terraform#3 승인과 evidence#104 승인은 해당 exact HEAD/기존 scope에만 적용 |

D22는 logical registry/trust/credential/digest/fallback 계약을 Freeze 전 준비하고 실제 cluster endpoint/cold-pull 결과는 Basic Ready 이후 완성한다. 현재 10-15 Final 일정·AC를 임의 수정하지 않고 단계별 authority 차이를 기록한다.
D23 전체 P1 기능을 P0로 변경하지 않는다. Private 접속의 mandatory DNS subset만 pre-create 계약에 포함한다.

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
- 교육장 한도·기간과 total-to-complete, subscription/link/STS-OIDC 및 구축 권한.
- D21 final raw/cleanup integrity intake 및 현재 snapshot·authority 정렬(B5/B6).
이 목록은 runtime IP가 없다는 이유로 Freeze를 순환 차단하는 것이 아니다.

## 8. 최신 확인과 상태
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

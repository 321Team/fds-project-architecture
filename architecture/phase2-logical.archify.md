# 2차 논리 아키텍처 {#phase2-logical-page}

AWS ROSA HCP로 확장하는 확정 설계와 실제 검증 대상을 구분합니다.

@answer scope="docs-v3.1.22 / 2026-10-19 / 새 서버 시험 아님"
@meta locale=ko style=clean quality_profile=showcase
@source baseline title="변환 기준 공개 아키텍처" url=https://github.com/321Team/fds-project-architecture/tree/517b51fcafd572e5f0296774ccd0ad21b23553a2
@source scope title="정본과 검증 범위" url=https://321team.github.io/fds-project-architecture/canonical-status.html

## 구성과 설명 경로 {#phase2-logical-diagram}

@diagram architecture id=system-map source=phase2-logical.architecture.json title="2차 논리 아키텍처"

@steps id=reading-paths
| primary-path | 주요 트랜잭션 경로 | 외부 HTTPS → IGW → 공개 Ingress LB → OpenShift Router에서 TLS 종료 → transaction-api HTTP 8000 → fds-engine TCP 8001. 외부는 /api·/readyz 두 Route만 공개합니다. Router 이후는 종단간 TLS가 아니며 앱·플랫폼 정책의 합산 허용/차단 검증은 별도입니다. | system-map | client |
| db-path | DB 통신 경로 | 거래 API만 기존 PostgreSQL 5432에 접근합니다. Worker private_a 서브넷 → Relay → IPsec → 교육장 VPN 게이트웨이 → DB 경로와 복귀 경로를 시험창에서 적용·원복합니다. 출발 /24 범위는 앱 정책·DB 인증·실행 증적으로 보완하며 엔진 DB 접근과 VPC 전체 허용은 금지합니다. | system-map | txapi |
| ipsec-vpn | IPsec VPN · Hybrid Transit | 교육장 VPN 게이트웨이가 연결을 시작하고 AWS Libreswan Relay가 응답합니다. IKEv2/IPsec UDP 500/4500 NAT-T를 사용하며 터널이 없으면 평문 우회를 차단합니다. 승인된 시험창의 연결·허용/차단·복구 증적은 설계 확정과 별개입니다. | system-map | relay |
| netpol | NetworkPolicy (fds-app) | 기본 Ingress/Egress 차단 위에 DNS, Router→거래 API, API→엔진 8001, API→DB 5432의 필요한 경로만 허용하는 설계입니다. probe용 route-exposed 정책과 앱 정책을 구분하고 합산 결과를 확인합니다. Worker의 Harbor 이미지 pull은 Pod NetworkPolicy로 통제했다고 주장하지 않습니다. | system-map | netpol |
| cicd-image | CI/CD · 이미지 Pull | GitHub 작업 → 온프렘 Runner → Harbor 이미지 공급. Runner는 공개 관리 API 443과 제한된 배포 계정으로 Deployment2·Service2·Route2만 변경합니다. Worker는 VPN을 통해 Harbor에서 내려받고, ECR은 검증된 경우 수동 전환합니다. TLS·인증·digest 오류 시 신규 배포를 중단하고 정상 Pod를 보존합니다. | system-map | github |
| platform | 접근통제 · 모니터링 | 역할별 권한과 restricted-v2 호환 앱 실행을 사용합니다. 배포 계정은 Secret·권한·보안 정책·클러스터 전체를 변경하지 않습니다. 플랫폼 모니터링을 사용하고 UWM은 꺼져 있으며, monitoring-api는 예약 Namespace입니다. 앱 지표 수집은 현재 범위 밖이며 실제 UID·권한 검증은 별도입니다. | system-map | idp |

## 적용 기준과 확인 범위 {#acceptance-status}

@callout level=note title="2차 설계 확정"
| docs-v3.1.22(2026-10-19)의 확정 설계입니다. 단일 가용영역은 Worker 배치 범위이며, 클라우드 통합 검증과 최종 인수는 별도입니다. |
| 이번 변경은 도면의 표현·생성 방식을 통일한 것이며 실제 서버 시험을 새로 수행한 결과가 아닙니다. |

## 확정 설계 (논리) {#details-1}

- Namespace: fds-app · monitoring-api · ci-cd (monitoring-api는 NS·RBAC만, 워크로드 없음)
- 관리자·조회자·모니터링 담당 권한 분리
- SCC restricted-v2, custom SCC 없음
- fds-engine은 DB 직접 접속 없음

## 실환경 검증과 보류 항목 {#details-2}

- 이미지 공급안(Harbor Primary + ECR 수동 전환) Runtime 대기
- Runner 직접 배포 채택 · API 접속 경로·동작 확인 대기
- VPN Route ON 전에는 DB·pull 경로 없음
- 기본 차단·앱 허용 정책은 확정 설계. 실제 합산 정책·허용/거부 검증 별도
- 2026-10-15 당시 조건의 제한 VPN 시험에서 터널 수립, 비허용 Relay 출발지의 DB 5432/22 차단, stop/start와 양쪽 원복 기록을 제출 자료 범위에서 수용했습니다. 상시 터널 운영이나 상위 인수 완료를 뜻하지 않습니다.
- 최신 nft 허용표 전체와 API의 DB 업무 경로, Worker의 Harbor 이미지 pull을 포함한 통합 검증은 대기 상태입니다. 최종 SSM 세션 조회 원문과 별도 최종 AWS route 재조회가 없는 자료 한계를 유지하며, 이번 문구 교정은 새 서버 시험 결과가 아닙니다.

## NetworkPolicy (fds-app) {#details-3}

- NP-00 기본 차단: Ingress·Egress 전부
- NP-01 DNS: openshift-dns 53/5353만
- NP-02는 probe용 route-exposed Pod 정책. 앱은 해당 라벨 없이 별도 앱 정책 사용
- NP-03 onprem-egress API → db01/32 5432. node pull은 Pod 정책과 별도
- 앱 NP(fds-msa): transaction-api → fds-engine 8001

## IPsec VPN {#details-4}

- AWS EC2 Relay 1대 (단일 장애점 위험 유지)
- vpn-gw01 개시 ⇄ Relay 응답, IKEv2 PSK · UDP 500/4500 NAT-T
- 터널 대역 10.1.93.0/24 ⇄ 10.20.0.0/16, Route 전파 없음(static)
- 허용: worker → db01 5432 (+Harbor 443은 이미지 공급안), 온프렘 개시 신규 연결은 차단
- SA 없으면 drop (평문 우회 차단)
- Relay는 public 10.20.110.0/24, DB 출발지는 worker private_a 10.20.10.0/24

## Phase 1 대비 {#details-5}

- kubeadm+Calico → ROSA HCP
- Prometheus/Grafana 자체 운영 → 플랫폼 모니터링
- 외부 노출은 /api · /readyz 2개만
- 진입: IGW → Ingress LB → Router(edge TLS 종료) → Pod

## 구성요소별 사양과 확인 조건 {#details-6}

- 외부 사용자 · HTTPS
- AWS Ingress LB · external · 예상 1(생성 후 확인) · public 10.20.110.0/24 · 인터넷 → IGW → LB → Router
- OpenShift Router · openshift-ingress · Route 2개(/api, /readyz) · edge TLS 종료(이후 HTTP) · Service의 Endpoint(Pod)로 직접 전달 · 워커 노드(private_a)에서 동작
- transaction-api ×3 · fds-app · ROSA 클러스터 fds-rosa-hcp › fds-app · NP-00 기본 전부 차단
- fds-engine ×3 · 외부 Route 없음 · ROSA 클러스터 fds-rosa-hcp › fds-app · NP-00 기본 전부 차단
- htpasswd IdP + RBAC · MFA 아님 · admin/view · ROSA 클러스터 fds-rosa-hcp
- openshift-monitoring · UWM 끔 · ROSA 클러스터 fds-rosa-hcp
- ci-cd/fds-deployer · NS Role만 · ROSA 클러스터 fds-rosa-hcp › ci-cd
- GitHub · 소스 · 워크플로
- self-hosted Runner · 관리망 10.250.10.20 · 온프레미스
- Harbor · 주 저장소 · P2 pull만 · 온프렘 10.1.93.0/24 · 이미지 공급안: Harbor Primary + ECR 수동 전환 (Runtime 대기)
- db01 PostgreSQL · 온프렘 · 온프렘 10.1.93.0/24 · 10.1.93.55:5432 · 복귀 경로 10.20.0.0/16 via vpn-gw01 .51 (시험창에서 적용·원복)
- AWS Relay EC2 · Libreswan · 응답자 · AWS VPC 10.20.0.0/16 › public_transport_a · UDP 500/4500 · NAT-T · AWS EC2 중계 확정 · SA 없으면 drop (fail-closed)
- vpn-gw01 · .51 · Libreswan · 개시자 · 온프렘 10.1.93.0/24 · IKEv2 PSK · 터널 대역 10.1.93.0/24 ⇄ 10.20.0.0/16 · 신규 연결은 VPC→온프렘만
- NetworkPolicy 00~03 · 00 기본 차단(Ingress·Egress) · 01 DNS(openshift-dns 53/5353) · 02 Router → route-exposed Pod · 03 onprem-egress API → db01/32 5432 · 앱/플랫폼 정책 합산 검증 별도 · node pull은 별도 통제
- monitoring-api · Namespace · RBAC만 · ROSA 클러스터 fds-rosa-hcp › monitoring-api · 현재 워크로드 없음(Prometheus/Grafana 자체 운영 대신 플랫폼 모니터링, UWM 끔)
- Worker ×3 · private_a · Harbor HTTPS 이미지 다운로드는 노드 경로이며 Pod NetworkPolicy와 별도 · 실제 pull 검증 필요

## 관련 문서 {#navigation}

[문서 목록](https://321team.github.io/fds-project-architecture/) · [서비스 흐름](https://321team.github.io/fds-project-architecture/overview.html) · [정본과 검증 범위](source:scope)

도면의 구성 요소와 사양은 변환 기준 공개 아키텍처를 따릅니다.[](source:baseline)

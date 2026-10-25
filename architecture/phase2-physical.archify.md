# 2차 물리·네트워크 아키텍처 {#phase2-physical-page}

AWS ROSA HCP로 확장하는 확정 설계와 실제 검증 대상을 구분합니다.

@answer scope="docs-v3.1.22 / 2026-10-19 / 새 서버 시험 아님"
@meta locale=ko style=clean quality_profile=showcase
@source baseline title="변환 기준 공개 아키텍처" url=https://github.com/321Team/fds-project-architecture/tree/517b51fcafd572e5f0296774ccd0ad21b23553a2
@source scope title="정본과 검증 범위" url=https://321team.github.io/fds-project-architecture/canonical-status.html

## 구성과 설명 경로 {#phase2-physical-diagram}

@diagram architecture id=system-map source=phase2-physical.architecture.json title="2차 물리·네트워크 아키텍처"

@steps id=reading-paths
| ingress | 외부 진입 경로 | 외부 사용자 HTTPS → IGW → Ingress LB(public_transport_a, external) → 워커의 Router Pod(TLS 종료) → transaction-api. | system-map | users |
| db-path | DB 통신 경로 | 거래 API만 기존 PostgreSQL 5432에 접근합니다. Worker private_a 서브넷 → Relay → IPsec → 교육장 VPN 게이트웨이 → DB 경로와 복귀 경로를 시험창에서 적용·원복합니다. 출발 /24 범위는 앱 정책·DB 인증·실행 증적으로 보완하며 엔진 DB 접근과 VPC 전체 허용은 금지합니다. | system-map | workers |
| image-pull | 이미지 Pull | Worker가 Relay·IPsec·교육장 VPN 게이트웨이를 거쳐 Harbor 443에서 이미지를 내려받는 확정 설계입니다. 보안그룹·방화벽·복귀 경로, 전용 인증·strict TLS·cold-pull과 전환/복귀는 실환경 검증 대상입니다. ECR은 준비된 경우 NAT·IGW를 경유해 수동 전환하며 VPN·DB 복구를 대신하지 않습니다. | system-map | workers |
| egress | 인터넷 Egress | private_a/b/c 0.0.0.0/0 → NAT GW(EIP fds-nat) → IGW → ECR·S3 등 리전 서비스. ECR/S3용 VPC Endpoint 없음. Relay EIP는 egress 우회 경로가 아님. | system-map | workers |
| control-plane | 컨트롤플레인 연결 | Worker는 PrivateLink를 통해 Red Hat 관리 영역의 ROSA HCP 제어 영역에 연결합니다. 4.22.17 고정, Worker 단일 AZ 3대는 관리 제어 영역의 단일 AZ를 의미하지 않습니다. Runner는 공개 관리 API 443에 직접 접근하며 인증·CA·권한·동작 검증은 별도입니다. | system-map | workers |

## 적용 기준과 확인 범위 {#acceptance-status}

@callout level=note title="2차 설계 확정"
| docs-v3.1.22(2026-10-19)의 확정 설계입니다. 단일 가용영역은 Worker 배치 범위이며, 클라우드 통합 검증과 최종 인수는 별도입니다. |
| 이번 변경은 도면의 표현·생성 방식을 통일한 것이며 실제 서버 시험을 새로 수행한 결과가 아닙니다. |

## 확정 설계 (물리) {#details-1}

- ROSA HCP · 공개 API/Ingress · Worker 단일 AZ 2a
- Worker 3대 private_a · NAT 1개 공용 (private_b/c는 생성만, 미사용)
- 진입: 인터넷 → IGW → Ingress LB → Router Pod · 출구: NAT → IGW
- 이미지 공급안: Harbor Primary + ECR 수동 전환 (Runtime 대기)
- machine 10.20.0.0/16 · pod 10.128.0.0/14 · svc 172.30.0.0/16

## 실환경 검증·보류 · 점선 {#details-2}

- 이미지 공급: Harbor 443의 허용·인증·cold-pull·전환/복귀 검증 별도
- OADP → S3 백업은 보류 · 실제 복원 검증 없음
- Runner 직접 배포 채택 · API 접속 경로·동작 확인 대기
- 온프렘 경로는 승인된 시험창에서 적용·시험·원복. DB·Harbor 복귀 경로 각각 검증
- VPCE·LB 개수: 생성 후 readback

## 그리지 않은 것 {#details-3}

- 추가 Hybrid DNS 보류 · public DNS/IP 및 엄격한 TLS 검증 유지
- 계정번호·EIP·리소스 ID는 공유용으로 생략

## 구성요소별 사양과 확인 조건 {#details-4}

- 외부 사용자 · 인터넷 · HTTPS /api /readyz
- ROSA HCP 컨트롤플레인 · Red Hat 관리 계정 · Red Hat 관리 · 4.22.17 고정
- NAT GW ×1 · EIP fds-nat · az1 단일 · private_a/b/c의 0.0.0.0/0 대상 · Relay EIP와 별개(Relay는 egress 우회 경로 아님)
- Ingress LB · external · 예상 1(생성 후 readback) · public_transport_a(kubernetes.io/role/elb) · IGW 경유 진입 → Router Pod(워커)
- Relay EC2 (Libreswan) · t3.medium · 암호화 gp3 40GiB · 10.20.110.10 · EIP 1:1 NAT · source_dest_check=false · SG: UDP 500/4500, DB 5432 / 조건부 Harbor 443; private_a 출발·허용/원복 검증 별도 · 단일 장애점 위험 유지
- PrivateLink VPCE · 예상 1 · 생성 후 확인 · AWS ap-northeast-2 · VPC 10.20.0.0/16 (Worker는 2a만 사용) › private_a 10.20.10.0/24
- Worker m5.xlarge ×3 · 암호화 gp3 300GiB · IMDSv2 required · autoscaling=false / auto_repair=true · max_surge=1 / max_unavailable=0 · AWS ap-northeast-2 · VPC 10.20.0.0/16 (Worker는 2a만 사용) › private_a 10.20.10.0/24 · MachinePool workers
- private_b 10.20.20.0/24 (2b) · private_c 10.20.30.0/24 (2c) · Terraform으로 생성 · ROSA 미사용(role tag 없음) · 0.0.0.0/0 → az1 NAT만
- self-hosted Runner · 10.250.10.20 · 온프렘 10.1.93.0/24 · 관리망 10.250.10.0/24 · Harbor 443 image push
- vpn-gw01 · 10.1.93.51 · 온프렘 10.1.93.0/24 · 관리망 10.250.10.0/24
- Harbor · 10.1.93.54:Harbor 443 Primary(Runtime 대기) · 복귀 경로 10.20.0.0/16 via .51(허용·인증·원복 검증 필요) · Relay 보안그룹·방화벽의 443 허용과 복귀 검증 별도
- db01 PostgreSQL · 10.1.93.55:5432 · 복귀 경로 10.20.0.0/16 via vpn-gw01 .51 (시험창에서 적용·원복)
- Internet Gateway · VPC 출입구 · 외부 사용자 → Ingress LB 진입과 NAT GW 인터넷 출구가 모두 통과
- AWS 리전 서비스(VPC 밖) · ECR: 이미지 공급안(Harbor Primary + ECR 수동 전환, Runtime 대기) · S3: OADP 백업 보류 · ECR/S3용 VPC Endpoint 없음 → NAT·IGW 경유 443

## 관련 문서 {#navigation}

[문서 목록](https://321team.github.io/fds-project-architecture/) · [서비스 흐름](https://321team.github.io/fds-project-architecture/overview.html) · [정본과 검증 범위](source:scope)

도면의 구성 요소와 사양은 변환 기준 공개 아키텍처를 따릅니다.[](source:baseline)

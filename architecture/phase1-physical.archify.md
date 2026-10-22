# 1차 물리·네트워크 아키텍처 {#phase1-physical-page}

교육장 Kubernetes의 서비스·운영 구성과 조건부 인수 범위를 설명합니다.

@answer scope="docs-v3.1.22 / 2026-10-19 / 새 서버 시험 아님"
@meta locale=ko style=clean quality_profile=showcase
@source baseline title="변환 기준 공개 아키텍처" url=https://github.com/321Team/fds-project-architecture/tree/517b51fcafd572e5f0296774ccd0ad21b23553a2
@source scope title="정본과 검증 범위" url=https://321team.github.io/fds-project-architecture/canonical-status.html

## 구성과 설명 경로 {#phase1-physical-diagram}

@diagram architecture id=system-map source=phase1-physical.architecture.json title="1차 물리·네트워크 아키텍처"

@steps id=reading-paths
| hosts | 8대 호스트 배치 | 호스트별 VM 책임 배치입니다. 전체 호스트의 최신 VM 목록을 재조사한 자료는 아닙니다. | system-map | server01 |
| network | 업무망과 관리망 | 내부 source NAT 금지와 관리망 복귀 경로를 유지합니다. FDS workload VM은 VMnet8에 연결하지 않습니다. | system-map | management |
| workloads | 앱 분산 관측 | 10월 19일 후속 기록에서 Worker마다 API 1개·엔진 1개를 관측했습니다. 과거 Worker 3 집중 배치와 구분합니다. | system-map | server05 |
| shared-risk | 공유 서비스와 장애 영향 | Worker 3 로컬 모니터링 저장소와 Server 8 공유 서비스의 단일 호스트 장애 영향을 유지합니다. | system-map | server07 |

## 적용 기준과 확인 범위 {#acceptance-status}

@callout level=note title="1차 조건부 인수"
| 배치 기준과 실행 관측의 구분: 아래 호스트 배치는 정본이 상속한 설계이며, API·엔진의 Worker별 분산은 2026-10-19 11:15~11:32 KST 후속 기록을 따릅니다. 10월 18일 Worker 3 집중 배치는 과거 관측입니다. |
| 이번 변경은 도면의 표현·생성 방식을 통일한 것이며 실제 서버 시험을 새로 수행한 결과가 아닙니다. |

## 네트워크 경계 {#details-1}

- VMnet0 10.1.93.0/24: 서비스 진입, 제어 노드와 Worker, Harbor·DB·DNS를 연결합니다.
- VMnet1 10.250.10.0/24: 관리 게이트웨이를 통한 승인된 작업 경로. 내부 source NAT 금지와 관리망 복귀 경로를 유지합니다.
- FDS workload VM은 VMnet8에 연결하지 않습니다. 모든 호스트의 현재 적용 상태를 재확인한 것은 아닙니다.

## 장애·복구의 범위 {#details-2}

- API와 엔진은 각각 3개 복제본의 노드별 분산 관측이 있습니다. 모든 장애 상황의 무중단을 입증하지 않습니다.
- 모니터링 핵심 3종은 단일 복제본과 Worker 3 로컬 저장소에 의존하며, 다른 Worker로 저장소가 자동 이동하지 않습니다.
- Edge·Harbor·DB가 Server 8에 함께 배치돼 호스트 장애의 공동 영향을 고려해야 합니다.
- 2차 VPN 게이트웨이는 1차 구현 배치에 포함하지 않습니다.

## 관리·운영 VM {#details-3}

- Server 01: 관리 게이트웨이, Ansible, Runner, 외부 모니터, Kubernetes API LB, DNS 1.
- Server 08: nginx edge, Harbor, PostgreSQL, DNS 2. 두 호스트는 관리·공유 서비스의 책임을 분리합니다.

## 관련 문서 {#navigation}

[문서 목록](https://321team.github.io/fds-project-architecture/) · [서비스 흐름](https://321team.github.io/fds-project-architecture/overview.html) · [정본과 검증 범위](source:scope)

도면의 구성 요소와 사양은 변환 기준 공개 아키텍처를 따릅니다.[](source:baseline)

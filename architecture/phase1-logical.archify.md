# 1차 논리 아키텍처 {#phase1-logical-page}

교육장 Kubernetes의 서비스·운영 구성과 조건부 인수 범위를 설명합니다.

@answer scope="docs-v3.1.22 / 2026-10-19 / 새 서버 시험 아님"
@meta locale=ko style=clean quality_profile=showcase
@source baseline title="변환 기준 공개 아키텍처" url=https://github.com/321Team/fds-project-architecture/tree/517b51fcafd572e5f0296774ccd0ad21b23553a2
@source scope title="정본과 검증 범위" url=https://321team.github.io/fds-project-architecture/canonical-status.html

## 구성과 설명 경로 {#phase1-logical-diagram}

@diagram architecture id=system-map source=phase1-logical.architecture.json title="1차 논리 아키텍처"

@steps id=reading-paths
| transaction | 거래 처리 | HTTP 진입과 API의 판정·저장 경로입니다. 탐지 엔진은 DB에 직접 접근하지 않습니다. | system-map | client |
| images | 이미지 공급 | Runner가 검사한 이미지를 Harbor에 공급하고 Worker가 내려받습니다. | system-map | runner |
| management | 클러스터 관리 | 서비스 진입용 nginx와 관리용 HAProxy를 구분합니다. API LB는 TLS를 종료하지 않습니다. | system-map | admin |
| operations | 관측과 복구 | 모니터링 단일 복제본과 Worker 3 로컬 저장소 의존성을 유지합니다. 조건부 인수는 모든 실패 경로의 검증을 뜻하지 않습니다. | system-map | monitoring |

## 적용 기준과 확인 범위 {#acceptance-status}

@callout level=note title="1차 조건부 인수"
| 1차 프로젝트는 조건부 최종 인수·종결 되었습니다. 구성 설명과 관측 시점의 시험 결과를 구분하며, 남은 보안·복구 한계를 없어진 것으로 표시하지 않습니다. |
| 이번 변경은 도면의 표현·생성 방식을 통일한 것이며 실제 서버 시험을 새로 수행한 결과가 아닙니다. |

## 서비스와 데이터 경로 {#details-1}

- nginx HTTP 80 → Worker NodePort 30080 → API Service 80 / Pod 8000. 1차 edge HTTPS는 미충족입니다.
- API → 탐지 엔진 8001 / API → PostgreSQL 5432. 엔진의 DB 직접 접근은 차단합니다.
- 10월 19일 배포 후 Worker마다 API 1개·엔진 1개가 관측됐습니다. 전 구간 무손실·지속 가용성을 보장하지 않습니다.

## 운영·관측의 한계 {#details-2}

- 10월 19일 11:30:58 KST에 정확한 관측 대상 23/23을 확인했습니다. 지속 정상·실패 주입·전체 경보 경로 검증과 구분합니다.
- 기존 백엔드 제외·복귀 검증, 이미지 검사·전송·배포 기록을 연결합니다. 과거 취약점 검사 결과를 현재 DB 기준의 재검사로 해석하지 않습니다.

## 보안·자동화 {#details-3}

- 기본 통신 차단과 필요한 경로 허용, 역할별 접근권한, 비밀정보 분리, 승인된 Ansible 관리 작업을 적용 대상으로 다룹니다. 부팅 시 보호 전환, 인증정보 회전, 일부 Probe 실패 전이와 전체 자동화 호출 경로의 검증 한계는 유지합니다.

## 백업·복구 {#details-4}

- PostgreSQL의 기존 덤프·격리 복원·업무 확인·원복 기록을 연결합니다. 모니터링은 단일 복제본·Worker 3의 로컬 저장소에 의존하므로 다른 노드로 자동 복구된다고 표현하지 않습니다.

## 모니터링 구성 {#details-5}

- 클러스터의 Prometheus·Alertmanager·Grafana와 노드 지표, 별도 외부 Watchdog를 구분합니다.
- 10월 19일의 23/23 대상 관측을 전체 경보 경로 검증이나 지속 정상으로 해석하지 않습니다.

## 관련 문서 {#navigation}

[문서 목록](https://321team.github.io/fds-project-architecture/) · [서비스 흐름](https://321team.github.io/fds-project-architecture/overview.html) · [정본과 검증 범위](source:scope)

도면의 구성 요소와 사양은 변환 기준 공개 아키텍처를 따릅니다.[](source:baseline)

# Phase 2 source 재맞춤 SEC 결정 검토안 v1.0
기준: 2026-10-04 13:55 KST부터 조회. 입력 HEAD: architecture PR8 `fe73bac2914c3c54f868c999617a742c652eaec9`.
작성: 이권욱 / CODEX_ASSISTED. 상태: PROPOSED / SEC_DECISION=PENDING / OWNER_ACCEPTANCE=PENDING / FREEZE=HOLD.
이 파일은 결정 검토안이며 새 Decision ID 발행·권한 부여·담당 변경·서버 적용·독립 승인 기록이 아니다.

## 1. 검토 요청과 권장안
기존 단일 권장 구성 revision4의 source 계약을 구현 가능한 세부 안으로 정리한다.
**권장: 승인된 source 생성·폐기 규칙 + read-only diff + 사람이 시작하는 도메인별 제한 적용.**
기존 On-Prem 자원과 최소 per-worker source 모델을 유지하면서 상시 다중 도메인 쓰기 자격증명 신규 도입을 줄이는 목적이다.
노드 자동 교체 때 IP마다 정책 재승인을 받지 않고, 사전 승인 규칙을 만족하는 inventory로 생성한 diff를 승인 실행자가 확인한다.
미분류 source·기존 규칙 밖 변경·권한/actor/port 확대는 새 변경 검토 대상이며 이 절차로 자동 허용하지 않는다.

이 방식도 무인 자동 복구가 아니다. 아래 응답·복구시간과 대체 담당을 수용할 수 없으면 선택을 재검토해야 한다.
autorepair/지원 업그레이드를 무조건 끄거나 source를 전체 VPC/subnet으로 넓혀 해결하지 않는다.

## 2. 확정된 경계와 새 제안
| 구분 | 내용 |
|---|---|
| 보존 경계 | transaction-api→db01 TCP5432, engine→DB DENY; Harbor pull은 별도 actor/443; DNS source 별도 |
| 보존 경계 | no-inner-NAT, 신규 forwarding default deny, SELinux/firewall/TLS 유지; IP 하나로 app identity를 대신하지 않음 |
| 기존 후보 | worker inventory의 최소 source-set, 교체 시 readback·positive/negative·DB 정합 재검증 |
| 신규 제안 | 아래 실행 장소·실행/대체 담당·권한 wrapper·작업창·시간 목표·domain adapter 분담 |
| 미확인 | 실제 계정/SSM/sudo/SSH 접근, exact policy/files/rules·현재 source mapping·지원 CNI/ROSA 모델 |
| 비용 입력 | 사용자 2026-10-04 합의: 10-06(화)부터 텍스트 전달. 한도·통화·기간·누적액·집계시각 수신 대기; 비용 승인/GO 아님 |

## 3. 실행 장소·사람·구현 책임 제안
ansible01은 **read-only inventory/diff와 실행 조정의 우선 후보**다. 현재 접근·계정·권한 검증은 미실시다.
운영 계정명·키·sudo 정책을 추정하지 않는다. 각 대상 host의 domain owner가 검토된 adapter를 실행한다.
공통 도구가 하나의 credential로 여러 host의 root/DB superuser 권한을 갖지 않는다.

| 영역 | 구현/주 실행 제안 | 대체 실행 제안 | 허용 범위 |
|---|---|---|---|
| #38 inventory·공통 diff/검증 도구 | 이하영 Lead / 이권욱 Support | 이권욱 | 승인 cluster/pool/node/ENI metadata와 source manifest 생성·검증 |
| #37 Relay/vpn-gw host adapter | 이재환 | 이하영 | 이번 source tuple의 FORWARD 허용 집합·readback·자기 변경 rollback |
| #47 DB adapter | 이재환, 기존 DB 권한 주체 확인 | 이하영, DB 담당 수용 필요 | 기존 인증/TLS를 유지한 source 정책 갱신·readback |
| #42 Harbor source adapter | 이권욱, 실제 Harbor 권한 주체 확인 | 이재환 | 승인 worker pull source의 443 정책 갱신·readback |

모든 세부 분담·대체자 권한은 각 Lead 수용 PENDING이다. 기존 티켓 Lead/Support/일정/AC는 변경하지 않는다.
#47 소비 측 DB readback·negative/정합 시험과 구현 검증은 분리한다. 같은 사람이 adapter를 작성·실행해도 독립 승인으로 표기하지 않는다.
SEC 승인 권위/독립 Reviewer는 현행 governance에서 확인 후 기록한다. 이하영 또는 이재환이라는 이유만으로 자기 작성 범위의 독립 승인자가 된다고 가정하지 않는다.

## 4. 영역별 최소 권한 안
| 영역 | 요구 기능 | 명시적으로 제외할 기능 | 검토해야 할 실제 입력 |
|---|---|---|---|
| AWS inventory | 기존 FDS-ReadOnly-Audit의 허용 metadata 조회 + 필요한 ROSA/node inventory의 별도 승인 읽기 | 현재 조회 역할에 SG/IAM/ROSA/SSM 쓰기 추가, 새 장기 access key | 필요한 exact read action과 리소스 범위·계정/리전/cluster |
| Relay | 대상 host의 승인 policy fragment/set·precheck·apply·readback·rollback | route/SG/NACL/IKE peer 변경, 임의 shell/root, NAT/TLS/SELinux 완화 | 지원 관리 경로(SSM 우선), exact document/wrapper·instance·실행 계정 |
| vpn-gw01 | 승인 source별 forwarding set만 | 전체 firewall flush, broad /24 grant, NAT 추가 | SSH/기존 인증 경로·전용 계정·wrapper 경로·sudo command allowlist |
| db01 | 기존 source firewall 및 필요시 pg_hba source 항목만 | DB data/schema/role 변경, DB superuser credential, auth/TLS mode 완화 | 현재 owner·정확 파일/규칙·원자적 반영/검증·필요 reload 범위 |
| Harbor host | worker image-pull source의 TCP443 정책만 | robot/password/CA/Harbor 서비스 설정 변경, Runner push 권한 변경 | Harbor host firewall/변경 경로·기존 P1 허용 source 보존 |

wrapper는 immutable version/경로를 pin하고 실행자가 wrapper나 설정 디렉터리를 임의 수정할 수 없게 설계한다.
사용자 입력을 shell 문자열로 실행하거나 전체 임의 명령을 허용하는 sudo/SSM 경로는 검토안의 허용 범위가 아니다.
Linux의 단기 접근은 신규 grant의 적용·회수 또는 기존 승인 접근의 작업창 제한을 구분한다. sudo 캐시 종료만으로 SSH 키/영구 sudo 권한이 회수됐다고 쓰지 않는다.
AWS 임시 credential의 자연 만료와 세션 중단/권한 회수를 구분한다. 정확 역할·SSM 정책·수명·종료 검증 방법은 지원 여부와 조직 통제 조회 후 결정한다.
**이 단계에서는 권한 정책이나 wrapper 배포를 실행하지 않는다.**

## 5. 명시적 적용 입력과 사전 중단 조건
실행 묶음은 다음 필드를 가진 검토된 manifest로 고정한다. 이 문서는 합성 manifest를 실제 inventory로 생성하지 않는다.
- run ID, KST 시각, 도구/source SHA, 승인 규칙 revision/Decision ref, 실행자·승인 범위
- cluster/pool/AZ/subnet/node/ENI provenance, inventory 수집시각/RC/원본 참조·hash
- actor별 source/destination/protocol/port/direction, route/SA/CNI actual source mapping
- domain별 전 정책 revision/hash, 신규/퇴역 source diff, 최대 cardinality/허용 교체 겹침·만료
- backup 참조/size/hash, apply/readback/rollback 명령·version, 작업창/권한 만료·회수 방법

미확정 필드·API 오류·stale inventory·태그만으로 소유 판정·actor 혼합·source provenance 불일치·cardinality 초과·drift면 APPLY STOP.
기존 P1 source/정책은 삭제하거나 묵시적으로 P2 집합에 흡수하지 않는다. manifest는 이번 P2 소유 변경만 식별한다.
필요한 pool/source cardinality는 승인 node 수+승인 surge/교체 겹침에서 산정한다. 숫자를 기본 4나 /24로 발명하지 않는다.

## 6. 정상·부분실패·복구 절차
1. **Observe:** 승인 read-only session에서 worker/node inventory와 actual source mapping을 수집한다. source 변화 감지/알림은 아직 구현되지 않았으며 실제 생성 전에는 계약만 검토한다.
2. **Validate:** manifest·rule·provenance·cardinality·actor 분리·입력 신선도 및 policy diff를 검사한다. 이 단계까지 target write 0.
3. **Recheck:** 적용 직전 inventory/각 target revision을 다시 읽어 lock/동시 변경 통제를 확인한다. 변경되면 새 diff로 재검토한다.
4. **Authorize:** 정해진 실행자/작업창에만 각 domain 접근을 활성화하거나 기존 승인 접근을 확인한다. 미승인 credential 생성/공유 금지.
5. **Backup/Apply:** 각 domain owner가 pre-change backup·syntax/precheck 후 자기 fragment를 적용한다. 각 단계 RC/readback을 보존한다. rollback 불가/백업 미확보는 시작 중단 조건이다.
6. **Verify:** 도메인별 실제 정책이 exact manifest와 일치하는지 확인하고, 새 연결로 API save/query·동일 DB 기대 행/이력·engine/미승인 source/port deny·TLS/no-inner-NAT를 검증한다. Harbor는 immutable digest cold-pull/pull-only push deny를 별도 확인한다.
7. **Retire:** positive 유지와 퇴역 판정 뒤 옛 source 제거·readback. 장애 시 기존 허용 source를 무작정 먼저 제거하거나 겹침을 무기한 유지하지 않는다.
8. **Close:** 임시 권한/세션·작업창·source 겹침 정리와 실제 readback, 증적·독립 리뷰를 연결한다.

부분실패는 모든 domain에 걸친 원자적 transaction이 아니다. 성공 domain·실패 domain을 구분해 다음 grant/retire를 중단하고 이번 변경만 이전 승인 revision으로 원복한다.
rollback 직전에도 drift/다른 작업의 변경을 확인한다. 안전하게 복구할 수 없으면 변경을 잠그고 경보·담당 인계; 불완전 상태를 PASS로 표시하지 않는다.
실제 불일치가 남으면 허용범위를 넓히지 않고 새 source 경로 fail-closed를 유지한다. 업무 중단 영향과 가능한 승인된 이전 source 경로를 원본 증적으로 기록한다.
연결 종료/conntrack 정리는 해당 tuple의 영향 검토 뒤 수행한다. fresh connection negative 없이 과거 연결 성공/timeout만으로 정책 인수를 선언하지 않는다.

## 7. 시간·작업창 검토값 — 새 제안, 승인/보장 아님
반자동 채택 판단을 쉽게 하기 위한 **교육 프로젝트 시험 운영 목표 제안**이다. 실제 성능·기존 AC·SLA와 동일하다는 근거가 없으며 담당자가 수용하거나 근거와 함께 수정해야 한다.

| 구간 | 신규 목표 후보 |
|---|---|
| source 변화 감지·알림 | 5분 이내 |
| 주/대체 담당 응답 | 알림 후 10분 이내 |
| inventory/diff 재검증 | 응답 후 5분 이내 |
| domain apply/readback | diff 확정 후 5분 이내 |
| 업무 positive/negative·DB 정합 확인 | readback 후 5분 이내 |
| 업무복구 총목표 | 감지 대상 변화부터 30분 이내(5+10+5+5+5) |
| 퇴역 source·신규 임시 grant 회수 | 업무복구 후 10분 이내; 정확 세션 수명은 SEC 별도 결정 |
| 승인 운영 작업창 | 담당자 수용 후 명시. 무인/야간 복구 보장 없음 |

대체자는 주 담당 미응답 구간 안에 escalation을 받아 응답시간에 포함돼야 한다.
목표 초과 시 원인 구간과 실제 시간을 기록하고 새 변경 적용을 멈춰 모델/권한/대체 경로를 재검토한다. 30분을 맞추기 위해 검증을 생략하거나 scope를 늘리지 않는다.
read-only 감지 5분·domain apply 5분도 구현/Runtime 미검증이다. 승인 전 polling/job/새 notification 서비스는 만들지 않는다.
계획 교체는 사전 작업창·source overlap/만료를 검토하고, 비계획 교체는 실제 autorepair 가능성과 담당 대응을 함께 시험한다.
worker 교체+Relay 장애/SA down에서 경로 자체가 회복되지 않으면 source 도구로 해결했다고 판정하지 않는다. #37 VPN 복구시간과 별도/합산 기록한다.

## 8. 검증·증적·보완 Gate
| 단계 | 필요한 증거 | 현재 |
|---|---|---|
| STATIC 설계 | source·권한·구현/소비 분리, 승인 경계와 복구 논리 대조 | 이번 문서 작성·대조 |
| STATIC 코드 | wrapper/validator·입력 검증·권한 정책·명령 제한·secret 누출·재실행/동시 변경 | NOT_RUN, 코드 아직 없음 |
| MOCK | 정상 diff, stale/provenance/cardinality 오류, 미승인 actor·부분실패·rollback drift·만료·재실행 | NOT_RUN |
| RUNTIME | 지원 환경에서 실제 source/정책/업무/negative·시간·교체/복합장애·권한 회수 | NOT_RUN |
| REVIEW/SEC | 독립 작성범위 확인·사람 수용·결정 ID/승인 기록 | PENDING |
| MERGE/PUBLICATION | 필수 검증·승인 충족 후 별도 | NOT_RUN |

원본은 명령/RC/KST/host/source·config SHA/전후 diff/readback/backup·cleanup과 실제 시간으로 추적한다.
password/token/private key/PSK/OTP는 수집하지 않는다. 원본 민감 메타데이터와 마스킹 파생본의 접근 범위·lineage/size/hash를 구분한다.
해시나 문서 readback은 무결성/반영 확인이며 업무복구·권한 회수 성공이 아니다.

Freeze 전 닫을 항목: 방식·권한 경계·주/대체 실행자·세부 분담·시간 목표·시험 방법을 해당 authority에 승인하고 필요한 pre-create 지원조건을 확인한다.
ROSA 생성 후에만 가능한 worker actual source/재생성 Runtime/복구시간은 post-create gate다. 아직 없는 node IP로 Freeze를 순환 차단하지 않는다.
도구 apply 준비 판정은 exact policy/files/session/입력·backup/rollback·코드/모의/독립 검토까지 충족해야 한다.

## 9. 사람 결정에 필요한 최소 항목
| 항목 | 제안 | 확정 근거 |
|---|---|---|
| 방식 | 반자동 우선 | #34/#38 및 SEC 권위 수용 PENDING |
| 실행 장소 | ansible01 조정 + 각 domain owner 실행 | 접속/계정/권한 사전 조회 PENDING |
| 구현/대체자 | §3 표 | 각 Lead 수용 PENDING |
| 권한 경계 | §4 domain wrapper·기존 read role 유지 | exact policy/files/리소스·만료/회수 지원 확인 PENDING |
| 시간 목표 | 총30분 후보·정리10분 후보 | 담당자 수용 및 Runtime 실측 PENDING |
| 독립 Reviewer/승인 권위 | 작성자와 범위 분리 | 현 governance와 SEC 결정 기록 PENDING |
| 비용 | 10-06부터 사용자 텍스트 수신 | 총액/허용 가동시간 판단 PENDING |

지금은 담당자에게 검토할 구체 안을 제공하는 단계다. 권한 추가·유료 구축·실제 서버 정책 변경은 수행하지 않는다.

## 10. 근거
- [설계 revision4 입력 HEAD](https://github.com/321Team/fds-project-architecture/blob/fe73bac2914c3c54f868c999617a742c652eaec9/phase2/reviews/20261003-resource-fit-recommended-design.md)
- [재환 재리뷰 새1/2](https://github.com/321Team/fds-project-architecture/pull/8#pullrequestreview-5403923382)
- [직전 반영 기록](https://github.com/321Team/fds-project-architecture/pull/8#issuecomment-5976676268)
- [#38 handoff](https://github.com/321Team/fds-project-baseline/issues/38#issuecomment-5976679098), [#47 handoff](https://github.com/321Team/fds-project-baseline/issues/47#issuecomment-5976679224)
- [#37 VPN/forwarding](https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5968506170), [#42 D22](https://github.com/321Team/fds-project-baseline/issues/42#issuecomment-5968506461)

이번 범위의 근거는 저장소 계약·리뷰와 사용자 요청이다. AWS/ROSA/SSM 현재 지원/계정 권한 조회나 실제 Linux 파일 inspection은 수행하지 않았다.

# Phase 2 설계 리뷰 발표 대본 v1.6

- 대상 PPT: FDS_Phase2_Business_Review_v1.10.pptx
- PPT SHA256: `9049766299593b9aada0079ccf4a2d3dc60ebed5af178c332a5e6630e521f2e8`
- 청중: 코오롱베니트, Red Hat 파트너 검토. 발표자는 교육생 팀
- 관계 범위: 사용자 지정 검토 관계. 이번 자료는 Red Hat 공식 인증이나 프로젝트 계약 체결이 아님
- 이전 PPT: FDS_Phase2_Business_Review_v1.6.1.pptx, SHA256 `003a550c20f23f1bc308c0810ffdbd6e816d547ecbf4dc12eafb6a6e571b81ee`
- 현황 기준: 2026-10-06 22:10 KST 재확인. 상태 승격 없음
- 발표 출발 기준: Phase 1 인수 및 기반서비스 인계 완료
- 구성: 본편 1~6장 약 7~8분. 부록 7~12장은 질문에 따라 선택해 설명합니다.

## 이번 갱신의 적용 범위

v1.3의 수용 문안과 담당자·목표일·P0/P1·인수조건을 유지합니다. 이번 v1.4는 6장만 결정표로 바꿉니다. 우선안은 기존 대본의 검토안이며 새 배정·기한·완료 선언이 아닙니다. 소스 병합·사용자 보고·실제 환경 인수를 구분하며, 이번 자료 갱신은 서버 적용이나 티켓 변경을 포함하지 않습니다.

22:10 KST 재확인: infra-terraform PR3은 merged, HEAD `ebfc56e25125784187e36a0c1dd2ca0463e82acd`, merge `2026-10-06T04:30:18Z`. fds-project-baseline PR137은 Draft/open, HEAD `72d798d5c784bf2270566b60374d1632d3152981`. #35 본문은 정본 커밋 `979facb98de8ca1f1e2ce22f38b27ac3366f3fc3`를 유지합니다. main에서 읽은 정본 §2 일정은 v1.3과 같았고, main 트리 SHA `f1e66492ca87f21d99d9848ab8606cd08185b9ff`와의 전체 파일 일치는 이번 조회에서 해시 대조하지 않았습니다. 새 AWS·서버·ROSA 실행은 없습니다.

| 항목 | 확인된 진전 | 실제 환경 후속 |
| --- | --- | --- |
| 인프라·플랫폼 | AWS 자원 생성 코드 없는 골격과 앱 허용 검사 코드를 각각 병합. [S6a/S6b] | 실제 자원 코드·상태 저장소·계획/적용·실제 앱 검증 |
| 앱·작업 인계 | 앱 사양과 배포 제어 코드 준비. [S5/S11/S12/S14] | 공통 배포 파일·실행 계정 호환·최소 DB 선행·실제 배포/복구 |
| VPN·관리 | 관문 재부팅·외부 UDP/IKE 사전 관측. [S15/S22] | AWS 터널 인증·지속/복구·관리 지원·신규 DNS 경로 |
| 권한·비용 | 정책 후보·대상 확인 도구 병합, 구축 입력 권장안. [S21] | 실제 권한·생성 방식·전체 완료비용·한도·가동시간 |

전체 설계 확정은 보류입니다. Terraform과 ROSA 사전 검사 PR의 최신 HEAD·main·승인 및 병합 상태, 앱 readiness 코드, 관련 운영 기록을 재조회했습니다. 신규 AWS·서버·ROSA 실행이나 원본 현장 수집 파일의 독립 재검증은 수행하지 않았습니다.

## 본편 발표 대본

읽을 대본입니다. 티켓 번호와 해시, 내부 상태 코드는 읽지 않습니다. 그 경계는 아래 발표자 참고에 둡니다.

### 01. Phase 2 설계 리뷰

예상 40초. 화면 안내: 표지의 네 카드, DB 연결·이미지 배포·ROSA 방식·작업 창을 가리킵니다.

코오롱베니트 여러분, Red Hat 파트너 검토 자리라 저희 교육생 팀이 Phase 2 설계를 설명드리겠습니다. Phase 1에서 데이터베이스와 기반서비스 인수는 마쳤습니다. 오늘은 구축 전에 정해 주셨으면 하는 네 가지만 먼저 말씀드리겠습니다.

첫째, 앱이 준비됐다고 보기 전에 최소 데이터베이스 연결 창이 필요합니다. 둘째, Harbor는 아직 후보이므로 정해지기 전에는 배포 서버가 직접 배포합니다. 셋째, ROSA 생성 경로는 하나로 정하고, 비용은 아직 확정이 아닙니다. 넷째, 지원 인계와 작업 창만 오늘 정하고 담당과 기한은 바꾸지 않습니다.

### 02. 업무 흐름과 데이터 책임

예상 60초. 화면 안내: 누가 기록하고, 누가 DB에 가면 안 되는지를 말합니다.

사용자가 거래를 요청하면 거래 접수 서비스가 분석 서비스에 위험 판정을 요청하고 결과를 받습니다. 거래와 판정 결과를 기존 데이터베이스에 남기는 것도 거래 접수 서비스입니다.

분석 서비스는 데이터베이스에 직접 붙지 않게 했습니다. 나가는 통신을 정책으로 막고, 접속정보도 주지 않습니다. 거래 서비스는 연결되고 분석 서비스는 막히는지를 같이 시험하겠습니다.

실행 환경은 Red Hat의 AWS 관리형 OpenShift인 ROSA입니다. 앱과 데이터베이스 연결은 이재환이 맡고, 정상 거래와 장애·복구를 같은 환경에서 확인합니다.

### 03. 실행 환경과 배포 책임

예상 70초. 화면 안내: VPN 업무 경로, 파란 이미지 공급선, 청록 배포 명령선을 구분합니다.

기존 서버와 AWS 서울을 암호화된 VPN으로 연결합니다. AWS의 EC2 중계 서버에서 Libreswan을 쓰는 방식을 골랐고, 클라우드의 거래 서비스가 이 길로 기존 데이터베이스에 갑니다.

이하영이 AWS 네트워크와 중계 서버를 Terraform으로 만들 예정입니다. ROSA를 어떤 방식으로 만들지, 어떤 권한이 필요한지는 오늘 따로 정해 주셨으면 합니다. 지금은 인프라 골격과 앱 허용 검사 도구만 소스에 반영했고, 실제 자원과 클러스터는 아직 만들지 않았습니다.

VPN과 앱·데이터베이스 통합은 이재환이, 자동 검사·배포와 기록 취합은 이권욱이 맡습니다. 파란 선은 검사한 이미지를 저장소에 올려 ROSA에 공급하는 길입니다. 청록 선은 배포 서버인 Runner가 배포와 복구 명령을 보내는 길입니다. Harbor는 재사용 후보이고, 최종 선택과 인증은 아직입니다.

### 04. 환경별 구현 순서와 P0/P1 경계

예상 95초. 화면 안내: 목표 일정과 환경, DB 선행조건, 담당자 집중 구간을 설명합니다.

10월 8일은 구축에 필요한 입력과 초기 인프라를 넘기는 목표입니다. 실제 자원 코드, 계정, 권한, 상태 저장소, 비용 조건을 받아 계획을 만들고, 그 계획을 본 뒤 적용합니다. 14일은 전체 인프라와 VPN을 확인하고, ROSA는 15일부터 19일까지 만들어 검증하는 목표입니다.

앱 작업은 16일과 19일, 근무일 이틀입니다. 공통 배포 파일과 플랫폼이 주는 실행 계정이 맞는지 준비해야 합니다. 거래 서비스가 준비됐다고 보려면 실제 데이터베이스 연결이 필요해서, 그 전에 최소 연결을 받는 순서를 오늘 정리해 주셨으면 합니다.

20일에는 정상 배포, 검사 실패 시 차단, 이전 이미지로 복구를 확인합니다. 21일은 데이터베이스 전체 통합, 22일은 같은 ROSA에서 업무와 장애를 다시 보는 목표입니다. 날짜는 이미 끝났다는 뜻이 아닙니다.

꼭 해야 하는 업무 경로가 우선 범위입니다. 그 뒤 운영 확장은 배포 검증 후 여력을 보고 넣고, 부족하면 미룹니다. 23일 산출물 정리와 26일 종료 목표는 유지합니다.

### 05. 사전 작업 진행 현황

예상 100초. 화면 안내: 확인된 준비와 실제 환경의 남은 작업을 짝지어 설명합니다.

권한과 네트워크 정책 후보, 비교 도구는 리뷰 후 소스에 반영됐습니다. 실제 권한을 적용하고 각 담당자가 본인 역할로 써 보는 단계는 남았습니다. 상태 저장소와 중계 서버 관리 입력은 권장안이지, 확정은 아닙니다.

AWS 인프라는 상태를 네 덩어리로 나누는 골격만 있습니다. 자원을 만드는 코드는 아직 없고, 문법 검사만 했습니다. 앱이 플랫폼에서 허용되는지를 보는 도구도 반영했습니다. 계획을 적용하고 클러스터와 앱을 실행하는 일은 이후입니다.

배포와 복구, 승인, 중복 실행 방지 코드도 반영됐습니다. 공통 배포 파일과 실행 계정 호환, 실제 인증과 배포 연결은 남았습니다.

VPN 관문은 재부팅 후에도 유지됐고, 바깥에서 연결 협상 패킷이 오가는 것은 봤습니다. 인증은 일부러 틀린 키로 실패했고, AWS와의 실제 업무 터널은 아직입니다. 터널의 허용과 차단, 유지와 복구, 이름 조회와 관리 접속을 이어서 확인하겠습니다.

### 06. 이번 리뷰의 확정 항목과 인계

예상 80초. 화면 안내: 카드 네 장을 순서대로 읽고, 정해 주시면 그 조건으로 가겠다고 말합니다.

정해 주시면 그 조건으로 구축하겠습니다. 정하지 못한 항목은 보류입니다.

첫째, DB 연결입니다. 앱 판정 전에 최소 DB 창을 정하는 안을 올립니다. 출발지는 사내 VPN 또는 클라우드 안입니다. 창을 정하지 못하면 20일과 21일 일정을 다시 맞춥니다. 중계 서버 관리가 안 되면 만드는 일과 접속·복구가 끊깁니다. 선택한 운영체제의 원격 관리 지원은 아직 확인 중이고, 실패로 단정하지는 않습니다. 안 되면 지원되는 운영체제와 검토된 초기 설정으로 바꾸려 하며, 외부 SSH를 열어 우회하지는 않겠습니다.

둘째, 이미지 배포입니다. Harbor는 후보입니다. 정해지기 전에는 Runner가 직접 배포합니다. 승인 이미지와 실제 실행 이미지가 같은지도 맞춰 보겠습니다. 수신 조건이 없으면 20일 배포 검증은 보류입니다.

셋째, ROSA 방식입니다. Terraform 또는 rosa CLI 중 하나로 만들려 합니다. 총비용은 미확정입니다. 확인 전에는 유료 생성을 보류합니다.

넷째, 작업 창입니다. 재환님 구간은 지원 인계와 변경 창만 정합니다. 담당과 기한은 유지합니다. 다른 작업과 겹치면 작업 창을 나누겠습니다.


## 회의 결정 기록 — 6장

이 표는 발표 중 채울 기록입니다. 우선안을 채택해도 담당·목표일·인수조건은 변하지 않습니다. 빈칸은 미결이며 완료가 아닙니다.

| 결정 | 우선 검토안 | 회의 결과 | 미결 시 다음 조치 |
| --- | --- | --- | --- |
| DB·관리 접속 | 앱 판정 전 최소 DB 창. 출발지는 VPN 또는 내부 클라이언트 |  | 20일·21일 재정렬, 관리 실패 시 지원 OS 변경안 |
| 이미지·배포 | Harbor 후보 유지, Runner 직접 배포 |  | 수신 조건·digest 대조 전 G5 착수 보류 |
| 플랫폼·비용 | rhcs 또는 rosa CLI 단일 경로. 총액 미확정 |  | 방식·한도·가동시간 전 유료 생성 보류 |
| 집중 구간 | 지원 인계·변경 창만 확정. 담당·기한 불변 |  | 경로 전환·DB 후속 창 분리. P1은 별도 |

## 부록 설명 대본

7~12장은 질문이 나온 부분을 선택해 설명합니다.

### 07. 물리 구성과 구축 입력

예상 50초. 화면 안내: 주소·생성 방식·관리 지원과 공유 호스트 위험을 설명합니다.

표의 주소와 사양은 만들 때 넣을 입력입니다. 실제 클라우드 자원 이름은 만든 뒤에 확인해 넘기겠습니다. ROSA를 어떻게 만들지, 지원 구성과 권한, 비용은 오늘 정할 항목입니다.

중계 서버는 원격 관리가 되는지도 확인해야 합니다. 데이터베이스, Harbor, 이름 서버 하나, VPN 관문이 같은 서버를 쓰고 있어서, 그 서버가 멈추면 업무와 이미지 공급, VPN이 같이 영향받을 수 있습니다. 다른 이름 서버는 별도 서버에 있습니다. 이 배치가 자동 전환까지 된다는 뜻은 아닙니다.

### 08. 작업 인계와 단계별 완료 기준

예상 55초. 화면 안내: 앱에 필요한 DB 입력과 배포·통합 인수의 차이를 설명합니다.

연결 확인에서는 이하영이 만든 인프라와 이재환이 확인한 VPN 허용·차단·복구 결과를 다음 작업에 넘깁니다. 앱은 최소 데이터베이스 연결을 받은 뒤 준비 상태를 보고, 그다음 배포 검증으로 갑니다.

20일에는 정상 배포, 검사 실패 시 차단, 이전 이미지 복구를 확인합니다. 데이터베이스 전체 통합은 21일, 같은 환경의 업무·장애 재확인은 22일 목표입니다. 이후 원본 기록과 비용, 삭제 결과를 모읍니다.

코드가 반영된 것과 실제로 인수된 것은 다릅니다. 도구 검사나 소스 반영만으로 단계가 끝났다고 말하지 않겠습니다.

### 09. 사전 작업의 검증 범위와 잔여

예상 70초. 화면 안내: 정적·모의·병합과 실제 실행을 구분하고 DNS 실패 원인의 미확인을 설명합니다.

AWS 인프라 골격은 자원 생성 코드가 0개이며 계획·적용·실제 자원은 미실행입니다. 앱 허용 조건 검사 도구는 정적·모의 검사와 소스 병합까지 진행했고, 실제 클러스터 허용 검사·앱 실행·이미지 수신·전체 실행 계정 호환성은 남았습니다.

앱 공통 배포 파일은 미준비이며, 배포 제어 코드는 실제 인증·관리 API·실행 흐름과 연결해야 합니다. 네트워크 정책 후보와 수집 도구의 소스 병합도 실제 권한 적용·접속 성공과 구분합니다.

VPN 관문 재부팅과 UDP·IKE 사전 관측은 운영 기록으로 확인했습니다. 인증은 예상 실패였고 실제 AWS 터널 인수는 미실행입니다. 신규 DNS 접근은 확보되지 않았으며, 이것이 어느 장비의 의도된 차단인지는 아직 확인하지 못했습니다. 현재 출발지·반환 경로·허용 범위를 확인해야 합니다.

전체 설계 확정과 저장소 선택, 지원·용량·비용도 잔여입니다. 이 자료의 상태 확인은 원본 기록 조회이며 새로운 서버 실행 결과가 아닙니다.

### 10. 전체 아키텍처 ① 업무·연결

예상 55초. 화면 안내: 업무 진입점, 암호화 물리 경로, 서비스별 DB 책임을 설명합니다.

이 그림은 논리 업무 흐름과 물리 연결을 합친 큰그림입니다. 클라우드의 거래 접수 서비스가 위험 판정 결과를 돌려받고, AWS 중계 서버와 기존 VPN 관문을 통해 DB에 거래·판정 결과를 저장합니다.

이하영은 자원 생성과 플랫폼, 이재환은 VPN과 앱·DB 통합을 담당합니다. 분석 서비스의 DB 송신을 통신 정책으로 차단하고 DB 접속정보도 주지 않습니다. DB에서 관측하는 실제 출발지는 구축 후 확인합니다.

실선은 P0 필수 경로입니다. 업무 진입점을 사설로 선택하면 시험 클라이언트도 승인된 사설 경로가 필요하므로, 출발지와 DNS·TLS를 확정합니다. 실제 연결·차단·복구 결과로 검증합니다.

### 11. 전체 아키텍처 ② 배포·관리

예상 50초. 화면 안내: 이미지 공급과 Runner 직접 배포, P0 관리 접속 조건을 설명합니다.

파란 경로는 GitHub 소스에서 검사·생성한 업무 프로그램 이미지를 저장소에 등록하고 ROSA가 받는 흐름입니다. 청록 경로는 Runner가 직접 배포와 복구 명령을 전달하는 흐름입니다. 배포할 승인 이미지와 실제 실행 이미지의 식별값을 맞춰 확인합니다.

아래는 관리 접속의 선행조건입니다. Runner의 관리망은 DB 보호망 밖에 있으므로 별도의 승인 경로와 통신 대상, 최소 DNS와 인증을 확정해야 합니다. 이 조건은 P0이며, 전체 DNS 운영 확장인 P1과 구분합니다. 준비된 배포 코드를 실제 ROSA 연결과 시험에 이어 붙입니다.

### 12. 전체 아키텍처 ③ P1 운영 확장

예상 50초. 화면 안내: 배포 검증 뒤 도입 판단과 회색 점선의 확장 범위를 설명합니다.

회색 점선 영역은 P1 운영 확장입니다. 필수 배포 검증 이후 지원·권한·비용과 P0 작업 여력을 확인해 도입 범위를 결정합니다. 이권욱은 환경 간 이름 조회 확장과 설정 기반 자동 배포, 이하영은 백업·복구 도구와 운영 기능·보안 기준 점검을 담당합니다.

설정 기록을 기준으로 자동 배포하는 방식의 후보 도구는 Argo CD입니다. 도입 결정 전에는 Runner 직접 배포를 유지합니다. 조건이 부족하면 근거와 재개 조건을 기록해 유예하고, AI 운영 플랫폼도 유예를 우선합니다. P1을 유예하더라도 P0 필수 이름 조회와 비밀정보 보호·복구 조건은 계속 충족합니다.

## 예상 질문과 답변

**20일 배포 검증과 21일 DB 통합이 충돌합니까?**

거래 서비스의 정상 준비 상태에는 실제 DB 연결이 필요합니다. 21일은 전체 통합 검증 목표이며 DB가 그날 처음 개통된다는 뜻은 아닙니다. 앱 정상 판정 전에 최소 DB 경로와 접속정보 참조의 생산자·소비자·작업 창을 확정하는 안을 우선 검토합니다. 이 순서를 확보할 수 없다면 일정 재정렬을 결정해야 합니다. 정상 상태·실패 차단·복구 기준은 유지합니다.

**Terraform으로 ROSA까지 구축됐습니까?**

현재는 AWS 자원 코드 0개의 인프라 골격과 별도의 앱 허용 검사 코드가 병합된 상태입니다. 실제 계획·적용·클러스터 생성은 미실행입니다. ROSA는 Terraform의 rhcs 방식인지 rosa CLI 방식인지, IAM/OIDC와 생성·삭제 책임을 구축 전에 확정해야 합니다.

**하영님의 승인과 병합은 무엇을 의미합니까?**

하영의 독립 GitHub APPROVE는 각각 인프라 골격과 사전검사 코드 범위입니다. 권욱은 Lead로 병합 판단을 기록했고 소스 병합을 확인했습니다. 실제 자원 적용·클러스터 실행·AC 인수·설계 확정 해제는 별도 판단입니다. 수행하지 않은 CI나 실제 실행을 통과로 표시하지 않습니다.

**앱 작업이 두 근무일이면 어떻게 진행합니까?**

공통 배포 파일과 실행 계정 호환성, 플랫폼 기본 준비·저장소 선택·승인 이미지·DB 참조 입력이 선행해야 합니다. 기존 플랫폼 지원 역할의 구체적 생산·인계 범위와 기존 경로 전환·DB 보안 후속의 변경 창을 먼저 정합니다. 남은 구현량 없이 불가능하다고 단정하거나 이 자료에서 담당·기한을 변경하지 않습니다.

**VPN 사전 관측은 실제 연결 성공입니까?**

관문 준비·재부팅 유지와 OCI 관측 경로의 UDP·IKE 왕복 기록은 있습니다. PSK 불일치로 인증은 예상 실패였고 실제 업무 터널은 형성되지 않았습니다. AWS 중계 서버에서 인증·업무 허용/차단·지속성·재수립·복구를 별도로 검증해야 합니다. evidence104의 편입 범위는 초기 기반과 HTTPS 공인 IP 관측입니다.

**중계 서버 관리 접속에서 무엇을 더 확인합니까?**

CentOS Stream 10의 공식 SSM 지원은 확인되지 않았고 실제 실패를 단정하지도 않습니다. 관리 프로그램 설치·Agent Online·승인 세션·재부팅과 복구를 확인합니다. 실패 시 지원 가능한 OS/AMI와 검토된 초기 설정으로 변경하는 안을 먼저 검토합니다. 서버 재생성 시에는 새 식별값으로 관리 권한을 재결속하고 본인 MFA 접속·옛 대상 거부·VPN 설정 재적용을 확인합니다.

**비용과 종료 기준은 확정됐습니까?**

아직 전체 완료비용과 교육장 적용 한도를 확정하지 못했습니다. HCP·3개 가용영역·NAT3개는 검토 후보이며 미확인 $350~450 추정을 확정 수치로 채택하지 않았습니다. 서비스·서버·스토리지·DNS·NAT·공인 주소·로드밸런서·전송 비용과 실제 가동시간을 계산하고, 적용 한도·남은 가동 가능시간·생성 및 삭제 시점을 유료 실행 전에 확정합니다.

**사설 업무 경로의 시험 클라이언트는 어디에 둡니까?**

출발지는 미정입니다. 온프레미스라면 선택한 VPN 경로를 검토하고, 승인된 클라우드 내부 클라이언트도 가능합니다. 출발지·서브넷·DNS·TLS·허용 경로를 정한 뒤 통합 시험의 입력으로 인계합니다.

**Harbor와 Argo CD는 이미 선택됐습니까?**

Harbor는 재사용 후보로 저장소 최종 선택·신뢰·인증과 실제 ROSA 이미지 수신 검증이 남았습니다. Argo CD는 배포 검증 후 조건부 P1 도입 대상이며, 도입 결정과 변경승인 전에는 Runner 직접 배포를 유지합니다.

**P1을 종료일까지 완료하지 못하면 어떻게 됩니까?**

P0 필수 인수와 종료 목표를 보호하고, 지원·권한·비용·작업 여력이 부족한 P1은 유예 근거와 재개 조건을 기록합니다. P0 최소 DNS·비밀정보 보호·필수 복구는 계속 충족해야 합니다.

## 발표자 참고: 구현·검증 범위

본 절은 본편에서 읽지 않습니다. 질문 대응과 원본 검토에 사용합니다.

### 01. Phase 2 하이브리드 클라우드 설계 리뷰

발표 출발 문구는 사용자가 지정한 사업 설명 기준을 유지한다. 이 자료 작성은 프로젝트 티켓 상태·인수 기록·정본을 변경하는 행위가 아니다. 목표 구성은 실측 비용 절감·성능 개선을 주장하지 않는다.

### 02. 업무 흐름과 데이터 책임

transaction-api → fds-engine 판정 요청·결과, transaction-api → PostgreSQL 거래·판정 결과 저장. fds-engine의 DB 직접 접근 금지. ROSA Pod별 egress NetworkPolicy와 DB credential 미부여를 함께 구현한다. NetworkPolicy는 허용 합집합이므로 다른 광역 허용 정책·selector도 확인한다. 실제 DB 관측 source는 구성에 따라 검증하며 모두 node IP라고 단정하지 않는다. credential 미부여가 TCP 차단 시험을 대체하지 않는다.

### 03. 실행 환경과 배포 책임

P0는 Runner-direct. Registry는 배포 명령의 실행 주체가 아니다. Terraform AWS provider만으로 ROSA 생성 방식을 확정하지 않는다. Terraform rhcs 또는 rosa CLI의 단일 관리 경로·IAM/OIDC 생성 책임·state 소유·재생성/삭제를 #35/#38 기존 범위에서 결정한다. 현재 도구 선택·새 provider 추가·실행 승인을 이 발표로 대신하지 않는다.

### 04. 환경별 구현 순서와 P0/P1 경계

정본 v3.1.21 §2: Architecture/Stage-A 조건부10/8, IaC10/8~14, VPN10/12~14, G4=10/14, ROSA BASIC_READY 목표10/15·Full10/19, APP10/16~19(주말 제외 2근무일), G5/Delivery10/20, Hybrid10/21, G6/E2E10/22, Review/teardown10/23, Close10/26. 10/9 비근무·주말 근무 없음. reviewed plan은 apply 전 조건이며 첫 plan 전에 reviewed plan을 요구하지 않는다. transaction-api /readyz는 실제 DB SELECT1 실패 시503. /livez·Running·모의DB·readiness 우회로 G5 기준을 낮추지 않는다. 최소 DB 경로 생산자·소비자·승인 창을 확정하며 #47 전체 인수는10/21 유지. #19 기존 경로 전환은10/15 목표 제안·Ready backend 조건 미충족으로 HOLD, 실행 예약 아님. #11 DB 보안 위험수용 재판단 상한10/20; #47 적용·음성시험 별도 변경 창. #15의10/19 별도 기한은 현재 원본 확인되지 않아 추가하지 않는다. 새 배정·일정·실행 권한을 이 자료로 변경하지 않는다.

### 05. 사전 작업 진행 현황

Terraform PR3 HEAD ebfc56e25125784187e36a0c1dd2ca0463e82acd / merge·현재main1f166d5c27ff24316887ae8ee2f2211fbb9a1a7d, 소스 병합13:30:18KST. Terraform1.16.4/aws6.66.0, resource0, backend bucket/key placeholder, network/vpn/rosa-prereq/rosa-runtime 4논리state경계. FMT·INIT backend=false/lockfile readonly·VALIDATE PASS는 작성자 CloudShell 보고·해당 독립 리뷰 범위. PLAN/APPLY/RUNTIME/CI=NOT_RUN. 하영 APPROVED5399738915는 scaffold 한정, 권욱 COMMENTED5423796110는 Lead 병합 판단. ROSA PR2 HEAD b66f412c35e756fc35ee5963eb9ad55dc845b14b / merge·현재maina37b10628cd59427c45dd28e2f6bd924891e1c54, 소스 병합13:30:24KST. Namespace 조회·oc create --dry-run=server의 generic UID/SCC admission 코드이며 실제 Pod/cluster 생성·image pull·앱 SA/volume/UID Running/Ready 미검증. 하영 APPROVED5412755375는 pre-check 코드·MOCK 범위, 권욱 COMMENTED5423796214는 병합 판단. CI=NOT_RUN, PG03=HOLD. #43 PORTABLE_BASE=NOT_READY, PG03=HOLD, BASIC_READY/PENDING, registry decision PENDING, APP_RUNTIME=NOT_RUN. PR140/141/142/143/144의 소스 병합·사용자 stdout은 actual role grant/SSM Runtime과 구분한다. 18:43:54 사용자 stdout은 승인3태그 중계 inventory0·Network role ABSENT·기본 세션 문서 ABSENT_OR_UNAVAILABLE이며 전체 EC2 부재·원본독립확인 아님. #35 6013969064 backend/KMS/profile/생성책임은 PROPOSED. #37 6014247521은 소비 관점 이견 없음이며 #35 채택 대체 아님. 유료 중계 생성 시점을 VPN10/12~14 창 직전으로 맞추자는 의견은 검토 안건이며 기존10/8 목표를 변경하지 않는다.

### 06. 이번 리뷰의 확정 항목과 인계

ROSA rhcs/rosa CLI 방식은 생성 전 미확정 입력. IaC permissions 로컬 DRAFT 전체 JSON 직접 수신·감사 미수행, REPLACE_ 잔여는 작성자 입력이며 Terraform backend 예제는 원본 확인됨. 부분 초안 리뷰는 실제 ID 생성 전에도 진행하되 placeholder 적용 금지. CentOS Stream10은 AWS 지원표에서 확인되지 않음, 실패 단정 없음. SSM Agent Online/실제 승인 문서 세션/재부팅 확인, 실패 시 지원 OS/AMI·검토된 bootstrap 변경안 우선, 공개 SSH 우회 금지. 역할 분리는 기존 생성/VPN/PMO 책임의 검토안이며 새 배정·기한 아님. UDP500/4500 외부0.0.0.0/0 계약은 동적 공인IP 대응 외부 접속 범위이며 내측 업무 전체 허용 아님; IKE ID+PSK 인증·ChildSA·허용/차단·장시간·DPD/rekey·공인IP변경·재부팅/재생성 복구 필요. 교육장 한도와400/450/500 역사 예산값 관계 미확정. HCP·3AZ·NAT3은 후보, $350~450 미검증 추정은 채택하지 않음. 신규 유료 실행 전 전체 비용·cost-to-finish·H_max·정리 조건확정. Private Ingress 시험 출발지·subnet/source·DNS·TLS·승인 경로 결정 필요.

### 07. 물리 구성과 구축 입력

정본 물리 배치: server08에 db01·harbor01·dns02·vpn-gw01, dns01은server01. AMI/type/AZ/10.20.110.10/EIP1/gp3 encrypted40GiB 입력은 현재 source 계약이며 생성 완료 아님. SSM 세션 KMS 미사용 결정이 state/EBS 암호화 결정을 대신하지 않음. 첫 실제 생성/readback에 SourceDestCheck=false·IMDSv2·EBS KmsKeyId·profile·Agent Online·승인 세션 문서 owner/type/version/content SHA 필요. PSK를 user_data/TF변수/state/AMI에 넣지 않는다. Agent Online 이후 승인 세션에서 conn/PSK 적용. 변경은 영향·작업 창·회귀·원복 절차 적용.

### 08. 작업 인계와 단계별 완료 기준

단계 목표 유지: G4 전체IaC+VPN10/14, ROSA basic10/15/full10/19, APP10/16~19, G5Delivery10/20, HybridDB10/21, G6E2E10/22. 승인 image digest와 actual Pod imageID, 플랫폼 API/Namespace/Context/짧은 인증 입력·Health 계약을 인계한다. 최소 DB 선행 인계가 #47 전체 AC를 선취·축소하는 것은 아니다. 실행자와 독립 검토자 기준은 기존 프로젝트 기준 적용. 증적 원본·hash는 무결성과 Runtime 성공을 구분한다.

### 09. 사전 작업의 검증 범위와 잔여

VPN #37 5964427918/5964438526: 관문 준비·재부팅 유지 보고. 5964908273/5965537470: OCI 관측 경로 UDP500/4500·IKE_SA_INIT/NAT-T/IKE_AUTH 왕복, PSK mismatch에 따른 AUTH expected failure, ChildSA0. evidence104 범위는pre-VPN baseline·HTTPS 공인IP 관측이며 최종UDP/IKE 원본 편입 아님. #40 5978867156은 DNS 과거raw재해시와 source 계약 정리, 신규Runner→DNS L3·source·정책 drift미확정. 접근실패를DENY PASS로승격하지 않음. CI가0건이면NOT_RUN. PR53/54/55는library소스 병합이며 transport/workflow/credential/승인원본/claim-Adapter/checkpoint/cleanup·Runtime 잔여, 단일POSIXRunner제약. PR137 HEAD72d798d5c784bf2270566b60374d1632d3152981 Draft/open/미병합·ARCHITECTURE_FREEZE=HOLD. 이번자료는계정/서버/클러스터시험·정본/티켓수정없음.

### 10. 전체 아키텍처 ① 업무·연결

업무 사용자 노드는ROSA 밖에 있으며 화살표는업무요청 관계다. Private Ingress 미정이며 on-prem VPN 또는VPC내부 등승인경로·source/DNS/TLS를결정한다. EC2+EIP Libreswan selected방식유지, 관리형VPN/VGW/TGW재선정 아님. Pod별egressNetworkPolicy+noDBcredentials의차단설계, API허용·engine차단을실제시험. source/NAT모델은실측·지원 확인 후고정한다. P0실선은구축완료표시 아님.

### 11. 전체 아키텍처 ② 배포·관리

파란실선=image supply, 청록실선=Runner-direct Deploy/rollback control, 청록점선=P0미확정접속조건, 회색점선=P1선택경계. Runner관리망10.250.10.20은DB보호selector10.1.93.0/24밖; 별도관리Route/source/DNS계약필요. privateAPI/OAuth/Ingress필수이름조회·TLS·namespace/context/API·short-livedcredential·승인digest/actualimageID인계. Registry는배포명령실행주체아님. #120 Go전Runnerdirect유지.

### 12. 전체 아키텍처 ③ P1 운영 확장

P1도입은G5후여력기반지원/권한/비용판단·기존변경승인후진행. GitOpsGo전Runner-direct유지, Go면DeliveryCR·권한·Gitsource·reconciliation/rollback·Operator공급조건승인. OADP+S3/Operator/HybridDNS/Compliance의정확한도입일은결정후확정,10/26이전강제아님. RHOAI유예우선. P0최소DNS·Secret보호·필수복구는면제되지않음.

## 원본 근거와 확인 범위

대상 PPT SHA256: `82ff3a2dfa3b110bc095c15bdaa2154f91afa643a00fdc2bf51a01fb9b2de649`

이전 PPT SHA256: `003a550c20f23f1bc308c0810ffdbd6e816d547ecbf4dc12eafb6a6e571b81ee`

정본 기준 commit: `979facb98de8ca1f1e2ce22f38b27ac3366f3fc3`. 실제 진행 상태는 원본 PR·운영 기록의 최신 조회 범위로 읽습니다.

**[S1] 정본 v3.1.21 / Baseline·기존 계획 기준**

- 원문: https://github.com/321Team/fds-project-baseline/blob/979facb98de8ca1f1e2ce22f38b27ac3366f3fc3/baseline/FDS_Project_Implementation_Baseline_v3.1.21.md
- 확인 범위: 기준 commit 979facb98de8ca1f1e2ce22f38b27ac3366f3fc3. 현재 PPT의 설계·담당·일정 기준을 유지.

**[S2] 후보 코드 독립 리뷰·병합 (PR140)**

- 원문: https://github.com/321Team/fds-project-baseline/pull/140
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/35#issuecomment-6010347040
- 확인 범위: HEAD ee50c3e560f422849435a1718d9171274b37ad63; merge b5d8b88f676d7e0a5f586478347bae3a4b6a4746; 2026-10-06 14:58:36 KST. 독립 APPROVED 5424206556은 후보 코드 범위.

**[S3] 중앙 후보 검사 사용자 stdout (PR140)**

- 원문: https://github.com/321Team/fds-project-baseline/pull/140#issuecomment-6009619140
- 확인 범위: 실행 2026-10-06 13:50:55.355960 KST. 후보 5개 NO_FINDINGS, identity-side 22건 기대 충족(허용4/거부18). 실제 trust·업무 권한·grant·Apply는 별도.

**[S4] #37 / Relay 운영 입력 및 후속 심층리뷰**

- 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-6010498202
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-6010632111
- 확인 범위: 이재환 운영 입력 제출 후 방향 수용·초안 준비 허용. 최종 정책·SSM Runtime·production VPN 인수 미완료. #35의 앞선 '입력 미수신' 기록 이후 새 Network 입력으로 구분.

**[S5] infra-cicd PR53 / 코어·입력 검사 병합**

- 원문: https://github.com/321Team/infra-cicd/pull/53#issuecomment-6009419537
- 관련 원문: https://github.com/321Team/infra-cicd/pull/53#pullrequestreview-5422924526
- 확인 범위: PR53 HEAD3bc9c9d091b4bdcaa9af6bb85de17e1bd34c7373; merge39e59842dc6b225d3a5d53278bddf0ae50b70cbb; 13:30:09 KST. 라이브러리 코어와 승인 입력 검사 병합, 실제 Runtime 미연결.

**[S6a] AWS Terraform 골격 PR3**

- 원문: https://github.com/321Team/infra-terraform/pull/3
- 관련 원문: https://github.com/321Team/infra-terraform/pull/3#pullrequestreview-5399738915
- 관련 원문: https://github.com/321Team/infra-terraform/pull/3#issuecomment-6009420279
- 확인 범위: HEAD ebfc56e25125784187e36a0c1dd2ca0463e82acd; 현재 main/merge 1f166d5c27ff24316887ae8ee2f2211fbb9a1a7d. 자원 생성 코드 0개·4개 논리 state 경계·backend placeholder. fmt/init(-backend=false)/validate는 exact HEAD 작성자 보고. PLAN/APPLY/RUNTIME/CI 미실행. hayeounglee 독립 APPROVED 5399738915는 scaffold 한정, GWONUK COMMENTED 5423796110은 Lead 병합 판단. 소스 반영만 완료.

**[S6b] OpenShift 앱 허용 조건 검사 PR2**

- 원문: https://github.com/321Team/infra-rosa/pull/2
- 관련 원문: https://github.com/321Team/infra-rosa/pull/2#pullrequestreview-5412755375
- 관련 원문: https://github.com/321Team/infra-rosa/pull/2#issuecomment-6009420443
- 확인 범위: HEAD b66f412c35e756fc35ee5963eb9ad55dc845b14b; 현재 main/merge a37b10628cd59427c45dd28e2f6bd924891e1c54. generic UID/SCC server-side dry-run 코드·정적/모의 검사 범위. hayeounglee 독립 APPROVED 5412755375는 pre-check 코드 한정, GWONUK COMMENTED 5423796214는 Lead 병합 판단. 실제 앱 admission·Pod·image pull·SA/volume·UID Running/Ready/health 미실행, PG03 HOLD, CI 미실행.

**[S7] 상세 설계 후보·설계 확정 보류 (PR137)**

- 원문: https://github.com/321Team/fds-project-baseline/pull/137
- 확인 범위: HEAD 72d798d5c784bf2270566b60374d1632d3152981. 조회 시 Draft/open/merged=false. 전체 설계 확정 보류 유지.

**[S8] 배포 이미지 저장소 선택·Delivery / 기존 잔여 계약**

- 원문: https://github.com/321Team/fds-project-baseline/issues/42#issuecomment-5977390034
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/46#issuecomment-5948127003
- 확인 범위: Harbor CA/FQDN 일부 사용자 확인과 실제 P2 cold-pull·배포 이미지 저장소 선택 Final을 구분. Delivery portability PARTIAL과 실제 ROSA 배포를 구분.

**[S9] AWS 공식 Systems Manager 지원 OS 표**

- 원문: https://docs.aws.amazon.com/systems-manager/latest/userguide/operating-systems-and-machine-types.html
- 확인 범위: 2026-10-06 공식 문서 재조회: CentOS Stream은9 명시. 선택된10의 실제 SSM 실패를 뜻하지 않으며 지원·설치·첫 접속은 잔여.

**[S10] 네트워크 업무 권한 검토용 부분 초안 병합**

- 원문: https://github.com/321Team/fds-project-baseline/pull/141
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/35#issuecomment-6011488238
- 확인 범위: HEAD b240f835627b0cea59a52b681eb72ceadba57c00 / merge711ad113246cf9ae6c18918ce702e3c8d3bc569c /16:23:48 KST. 독립 리뷰5424796438은3파일 부분 초안 source 범위. 최종 정책/중앙 검증/grant/각 본인 SSM Runtime 미실행. IaC 부분 입력 수신, actual JSON 로컬 미커밋·backend/key/KMS/profile/implementation/API 잔여.

**[S11] 배포 승인·인증 유효시간 검사 코드 병합**

- 원문: https://github.com/321Team/infra-cicd/pull/54
- 관련 원문: https://github.com/321Team/infra-cicd/pull/54#pullrequestreview-5424669935
- 확인 범위: HEAD7b49626d1c1f33a6fd70e7cecec273a2387e0e44 / mergec637b9d5d47eca942de1c1e67883579b8e8f60af /16:00:09 KST. 독립 리뷰·병합은 library 코드 범위이며 실제 토큰 발급/API/Runtime 미실행.

**[S12] 계획별 배포 승인·중복 실행 방지 코드 병합**

- 원문: https://github.com/321Team/infra-cicd/pull/55
- 관련 원문: https://github.com/321Team/infra-cicd/pull/55#pullrequestreview-5425003879
- 확인 범위: HEAD3dbdc05ffd20c836caab8e2b6b42133c2d415423 / merge2d8356eff60b9e4e04b12e40da061f49e7fb9e10 /16:17:29 KST. 독립 승인 범위는 library·시험·설계 문서. CI 시험 기록을 대조했으며 본 작업에서 재실행하지 않음. 단일 POSIX Runner 전용, claim-Adapter/transport/승인 원본/철회/checkpoint/credential/cleanup/workflow 잔여.

**[S13] 설정 기반 자동 배포 도입 범위와 실행 경계**

- 원문: https://github.com/321Team/fds-project-baseline/issues/120
- 확인 범위: 정본 v3.1.21의 배포 검증 후 여력 기반·유예 우선 P1. 도입 결정 전 Runner-direct 유지, 도입 시 별도 Delivery CR·권한·Git source·복구·Operator 공급 조건 승인.

**[S14] 앱 준비와 실제 DB readiness**

- 원문: https://github.com/321Team/fds-project-baseline/issues/43
- 관련 원문: https://github.com/321Team/fds-msa/blob/9658255ce9e39167cc8876a38b98aeb1f0311694/transaction-api/app/main.py
- 관련 원문: https://github.com/321Team/fds-msa/blob/9658255ce9e39167cc8876a38b98aeb1f0311694/transaction-api/app/db.py
- 확인 범위: APP portable base NOT_READY·PG03 HOLD·실제 Runtime NOT_RUN. 최신 앱 main 9658255ce9e39167cc8876a38b98aeb1f0311694: DB SELECT1 실패 시 /readyz503. 최소 DB 입력을 앱 정상 판정 전에 인계하고 전체 DB 통합10/21은 유지.

**[S15] VPN 관문·UDP/IKE 사전 관측**

- 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5965537470
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5964427918
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5964438526
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5964908273
- 관련 원문: https://github.com/321Team/fds-project-evidence/pull/104#issuecomment-5966011431
- 확인 범위: 관문 준비·재부팅 유지 보고와 OCI UDP/IKE 왕복 관측은 별도 기록. PSK 불일치 인증 예상 실패·ChildSA0. evidence104는 초기 기반·HTTPS 공인 IP 관측이며 실제 AWS 업무 터널 인수 아님.

**[S16] 신규 DNS 접근과 경로 미확정**

- 원문: https://github.com/321Team/fds-project-baseline/issues/40#issuecomment-5978867156
- 확인 범위: 기존 DNS 원본 무결성과 신규 Runner/local router/vpn-gw 현재 L3/source/정책 drift를 구분. 접근 실패가 의도된 차단이라는 인수 증명은 없음.

**[S17] 작업 집중 구간·기존 경로 전환·DB 보안 후속**

- 원문: https://github.com/321Team/fds-project-baseline/issues/19#issuecomment-6012871977
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/11#issuecomment-5989172773
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/47
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/50
- 확인 범위: 10/15 기존 경로 전환은 목표 제안·Ready local endpoint 조건 미확보로 HOLD. DB 보안 후속 재판단 상한10/20, 전체통합10/21·E2E10/22. 기존 담당/AC 유지, 지원·변경 창은 리뷰 안건.

**[S18] 비용 한도·잔여 가동시간 판정**

- 원문: https://github.com/321Team/fds-project-baseline/blob/979facb98de8ca1f1e2ce22f38b27ac3366f3fc3/tests/FDS_Test_Strategy_v3.1.21.md
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/34
- 확인 범위: 400/450/500 역사 예산값과 교육장 한도의 관계 미확정. HCP·3AZ·NAT3은 후보. 전체 단가·실제 가동시간·cost-to-finish/H_max 입력 후 유료 생성 판단, 미검증 $350~450 추정 채택 안 함.

**[S19] 서비스별 송신 차단의 공식 원칙**

- 원문: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- 확인 범위: Kubernetes 공식 문서 재조회. NetworkPolicy는 허용의 합집합이므로 모든 적용 egress 정책·selector 확인. engine DB credential 미부여와 함께 실제 API 연결·engine DB 차단을 검증.

**[S20] ROSA 클러스터 생성 방식의 결정**

- 원문: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/creating-a-red-hat-openshift-service-on-aws-cluster-with-terraform
- 관련 원문: https://docs.aws.amazon.com/rosa/latest/userguide/getting-started-hcp.html
- 확인 범위: Red Hat 공식 Terraform 절차의 rhcs·account/operator role·OIDC와 AWS CLI 절차를 구분. 현재 AWS 골격만으로 ROSA 생성 방식을 확정하지 않음.

**[S21] 최신 Network 후보·binding 확인 소스**

- 원문: https://github.com/321Team/fds-project-baseline/pull/143
- 관련 원문: https://github.com/321Team/fds-project-baseline/pull/144
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/35#issuecomment-6013662958
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/35#issuecomment-6013969064
- 확인 범위: PR143 후보 소스 merge1059713f1a56a1a9d0d88aa37470c5e582e1d580, PR144 수집기 HEAD7b10b072afe7f102449745e0c48b97de1e7d7a9b/merge4e068c0a555a83f97e83f8214178952e9d2dd243. 실제 grant/최종 정책 적용/SSM 미실행. 18:43:54 사용자 stdout scoped inventory0는 전체EC2 부재 아님. raw/manifest 독립 미수신; backend/KMS/profile 권장안은 제안.

**[S22] 중계 서버 인계·비밀정보·재생성 복구**

- 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-6014247521
- 관련 원문: https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-6014503123
- 확인 범위: #37의 소비 관점 이견 없음은 #35 채택 결정과 구분. PSK를 user_data/TF변수/state/AMI에 넣지 않음. Agent Online 뒤 승인 세션 적용. 재생성 후 실제 새 ARN 결속·본인 MFA 접속/옛 ARN 거부·conn/PSK 재적용. 유료 생성 창 조정은 검토 안건.

**[S23] 사설 업무 진입점과 시험 출발지**

- 원문: https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/cluster_administration/configuring-private-connections
- 확인 범위: Private Ingress 선택 시 승인된 사설 경로 필요. 온프레미스 VPN 또는 승인된 클라우드 내부 클라이언트 등 출발지/subnet/DNS/TLS 계약을 결정.


## v1.10 장표 동기화

2026-10-06 22:36 KST. 대본 1장·6장을 장표 카드 문구와 맞췄습니다. 다이어그램 글자 크기와 화살표, 흰 검토 시안 통일은 표현만 바꿨고 담당·목표일·인수조건·미완료 상태는 그대로입니다. 2~5장과 부록 7~12장 읽을 문안은 유지합니다.

# Private 관리 경로·양방향 DNS 계약 검토안 v1.0
기준: 2026-10-04 14:13 KST부터 조회. 입력 HEAD: architecture PR8 `8b8916963b0b084760b97ad70d245e43df3a8892`.
작성: 이권욱 / CODEX_ASSISTED. 상태: PROPOSED / ROUTE_DNS_DECISION=PENDING / FREEZE=HOLD.
실제 route/selector/SG/BIND/Resolver 적용·계정 권한 변경·새 Decision 발행은 수행하지 않는다.

## 1. 단일 권장 경로
기존 Runner 위치를 유지하고 **Runner 승인 source /32를 보존하는 routed 경로**를 VPN에 연결한다.
On-Prem DNS52/53은 cluster의 정확한 API/OAuth/Ingress domain만 AWS inbound Resolver로 전달한다.
AWS outbound Resolver는 승인 On-Prem Harbor/DB 이름의 zone만 DNS52/53으로 전달한다.
기존 default-deny/no-inner-NAT·인증/TLS 이름 검증을 유지한다. public API 전환·hosts 고정·광역 subnet 허용으로 준비 부족을 우회하지 않는다.

Runner 10.250.10.20과 VPN gateway 10.1.93.51 사이의 **실제 L3 연결/next hop은 미확인**이다.
host-only VMnet 주소가 있다는 이유로 연결 가능하다고 단정하지 않는다. 이 경로의 readback/승인 전 selector나 cloud return route를 적용하지 않는다.
routed 경로를 확보할 수 없다면 관리 source/Runner 배치 adapter를 정식 재검토한다. VMware NAT로 바뀐 source를 암묵 승인하지 않는다.

## 2. 권위 차이와 처리안
#40 본문은 P0 DB/Harbor IP Endpoint 기본, DNS P1 결정10-16, #48은 Go+P0/G5 이후 capacity 조건이다.
최근 PR8/#40 댓글은 Private API/Ingress의 필수 DNS subset을 pre-create contract로 연결한다.
**댓글/후보 문서가 기존 본문·일정·AC를 이미 변경했다고 해석하지 않는다.**

제안:
- #34/#38에서 Private access에 필요한 관리 DNS subset의 구성·수용조건·구현 책임/선행순서를 별도 결정한다.
- #40에는 D23 전체 P1 범위와 subset의 근거/경계를 정렬한다. #48 전체를 P0로 승격하거나 기존10-16 일정을 임의 변경하지 않는다.
- pre-create에는 endpoint 모델·zone 식별 방법·route/selector/source/SG·시험/비용 계약을 확정한다.
- 생성 후 실제 endpoint/ENI/IP·FQDN/TLS·readiness를 관측하고 **관리 접속/Basic Ready 인계 전** 필수 DNS를 구현·검증한다.
- AWS endpoint를 실제 생성하려면 Freeze/Cost·해당 실행 gate 충족이 필요하다. 이 문서는 생성 승인이 아니다.
- Harbor/DB의 기존 승인 FQDN 보존을 위해 outbound를 권장하지만, 이것을 최종 승인 D23 값으로 소비하지 않는다.

## 3. 이름 권위와 전달 범위
| 구분 | 권위/경로 제안 | 고정 전 필요한 입력 |
|---|---|---|
| ROSA API·OAuth·Ingress | 선택 모델의 AWS/ROSA 관리 DNS, On-Prem→inbound Resolver | API/OAuth/Route 실제 이름과 authoritative zone/CNAME chain·VPC 연결 여부 |
| On-Prem Harbor·DB | 기존 authoritative DNS52/53, VPC→outbound Resolver→DNS52/53 | 승인 FQDN·zone·A/CNAME·TTL·Harbor TLS SAN/CA |
| Runner·승인 관리자 | 기존 승인 DNS52/53에 query | Runner resolver 설정·query source·관리자 별도 source/접속경로 |
| 기타 일반 DNS | 기존 정책 유지 | 이번 subset 밖의 forwarding 확대 금지 |

`fds.internal`은 과거 설계 입력이다. 현재 Harbor/DB의 authoritative zone/SAN을 실제 원본에서 확인하기 전 그대로 생성하지 않는다.
ROSA domain을 전체 `openshiftapps.com` 또는 루트 `.`로 광역 forward하지 않는다. 실제 cluster zone과 CNAME 의존성을 식별해 최소 suffix/이름 정책을 검토한다.
inbound가 조회하는 zone은 해당 VPC에서 해석 가능해야 한다. PHZ인 경우 VPC association 확인; 임의 split-horizon zone을 만들어 vendor record를 대체하지 않는다.
같은 suffix가 양방향 forwarding rule에 들어가지 않도록 zone 목록·우선순위·loop 검증을 고정한다.
기존 DNS recursion ACL을 AWS 전체/0.0.0.0/0에 개방하지 않는다. outbound source만 승인된 recursion/query 범위에 추가하는 후보이며 zone transfer 권한과 분리한다.

## 4. 방향별 최소 flow
endpoint의 actual IP/FQDN/ID는 생성 후 관측한다. 아래 IN/OUT/API/INGRESS 기호는 실제값이 없는 placeholder이며 deploy 입력이 아니다.

| ID | source→destination | protocol/port 후보 | 승인·검증 경계 |
|---|---|---|---|
| LOCAL-DNS | Runner10.250.10.20→DNS52/53 | TCP/UDP53 | local routed 경로·DNS ACL·source 보존 확인; VPN 없이 local 구간 |
| DNS-IN | DNS10.1.93.52/53→IN-A/IN-B | TCP/UDP53 | inbound SG·VPN 양 gateway·return route |
| DNS-OUT | OUT-A/OUT-B endpoint ENI→DNS52/53 | TCP/UDP53 | outbound SG·VPN FORWARD·DNS ACL·return; worker source와 별도 |
| MGMT-API | Runner10.250.10.20/32→API PrivateLink | **TCP443 우선 후보** | 공식 HCP 예시443; 실제 선택 version/endpoint port 확인 |
| MGMT-AUTH | 승인 관리 actor→OAuth/console·필요 인증서비스 | HTTPS443 후보 | 실제 redirect/domain·identity 통신 inventory로 분리 |
| MGMT-INGRESS | 승인 actor→private ingress/업무 Route | TLS443 후보 | private LB/SG·Route/RBAC/TLS·source transform 관측 |
| REPLY | 위 허용 flow의 응답 | 실제 TCP/UDP state·ephemeral 반환 | SG/NACL·host firewall·양방향 route 검증 |
| DENY | 기타 source/destination/port/new direction | deny | API·DB·Harbor와 DNS 예외 혼합 금지 |

HCP 공식 PrivateLink 문서의 추가 SG는 TCP443이며 ROSA4.17.2 이상 지원이라고 명시한다(2026-10-04 조회).
이는 현재 계정 supported stable version 선정이나 생성 endpoint 확인을 대신하지 않는다. Phase1 LB6443을 그대로 복제하지 않는다.
지원되는 **추가 SG**를 사용하며 기본 managed endpoint SG 수정/삭제 금지. 실제 version/SG support 미확인이면 HOLD.
API 추가 SG만으로 OAuth/Ingress/관리 인증 전체를 허용했다고 처리하지 않는다. 각각의 managed endpoint/LB/port와 source 경계를 확인한다.
관리자 source는 아직 미확정이며 Runner /32를 모든 사람의 source로 사용하지 않는다. 관리자 목록·브라우저 경로/접속 위치를 별도 승인한다.
Ingress proxy/LB 뒤 observed source는 원본 client와 다를 수 있다. TLS와 trusted proxy/header 계약을 #38/#43에 연결하며 IP alone을 사용자 identity로 승격하지 않는다.

## 5. route·VPN selector 변경 후보
현재 D21 envelope: On-Prem10.1.93.0/24↔Cloud10.20.0.0/16. Runner10.250.10.20은 포함되지 않는다.
기존 DNS52/53은 이 On-Prem envelope 안이지만, envelope 포함이 application 허용을 의미하지 않는다.

| 구간 | 후보 변경/보존 | 필요한 원본 |
|---|---|---|
| Runner→vpn-gw | cloud10.20/16 목적지의 승인된 routed path | Runner ip/route·actual next hop, 두 LAN 사이 router/forwarding·source capture |
| vpn-gw→Runner 반환 | 10.250.10.20/32을 actual local next hop으로 반환 | vpn-gw route·로컬 중계 장비 route/ACL |
| VPN 관리 envelope | 10.250.10.20/32↔10.20/16을 추가 후보로 검토 | 양 peer exact selector 지원·Child SA/IKE 계약·route/xfrm·기존 SA 영향 |
| AWS 반환 | 관리 endpoint가 속한 route table에 10.250.10.20/32→Relay ENI 후보 | actual endpoint subnet route table/association·IaC/state ownership |
| DNS envelope | 기존10.1.93/24↔10.20/16 유지 | inbound/outbound ENI subnet별 route10.1.93/24→Relay·On-Prem 반환 |
| 신규 reverse flow | OUT endpoint→DNS52/53 TCP/UDP53만 명시 승인 | #37 default-deny reverse 정책과 exact exception·stateful reply |

관리 envelope의 cloud10.20/16은 transport 범위이고 허용 tuple은 actual 관리 endpoint/port로 제한한다. On-Prem 관리망 전체10.250.10/24로 넓히지 않는다.
route table에 있거나 SA에 포함되는 것만으로 허용되지 않는다. Relay SG/host FORWARD/vpn-gw/target SG/ACL·인증을 모두 대조한다.
outbound DNS는 **Cloud에서 시작하는 신규 flow**다. 기존 On-Prem initiated flow의 reply로 잘못 분류하지 않는다.
no-inner-NAT 유지: protected 관리/DNS flow를 SNAT하지 않으며 인터넷 NAT 경로와 분리한다.
NACL은 실제 stateless 반환/ephemeral 범위를 확인한다. SG stateful 동작을 NACL/host firewall에 그대로 가정하지 않는다.
Selector/return route 후보는 source reconciliation SEC안의 적용 scope 밖인 **별도 네트워크 변경결정**이다. source updater로 route/selector를 몰래 수정하지 않는다.

## 6. Resolver 배치·지원조건
AWS 공식 문서: inbound와 outbound 각 endpoint에 다른 AZ의 최소2개 IP 필요; 양방향 후보는 endpoint2개/IP4개.
private-a/private-b를 우선 배치 후보로 삼되 supported subnet/available IP/ENI·zone routing과 #35 IaC 입력을 확인한다.
Inbound SG는 DNS52/53 source TCP/UDP53, outbound SG는 목적지 DNS52/53 TCP/UDP53만 후보로 검토한다.
수동 ENI IP 고정이나 ENI 태그만으로 owner를 인증하지 않는다. 실제 endpoint/ENI/VPC/subnet/AZ/route association을 추적한다.
Resolver outbound rule은 승인 zone+targetDNS52/53으로 설정하고 해당 project VPC에 associate한다.
Kubernetes/ROSA Pod DNS는 지원되는 기본 cluster DNS→VPC resolver 경로를 우선 보존한다. 공용 OCP cluster DNS 또는 Pod별 dnsPolicy를 임의 변경하지 않는다.
On-Prem에서 VPC+2 주소 직접 query로 inbound endpoint를 대체하지 않는다. 이 검토안은 VPN 경유 endpoint 경로를 선택한다.
두 AZ endpoint도 공통 Relay 장애를 피하지 못한다. DNS HA와 전체 hybrid 경로 HA를 구분한다.

## 7. 검증·수집·복구 순서
사전 read-only 수집:
- Runner/vpn-gw/DNS의 인터페이스·route·resolver 설정/ACL과 기존 policies를 **승인 계정/경로에서** 필요한 필드만 수집. SSH key/PSK/SecretData를 수집하지 않는다.
- 현재 AWS read-only metadata·선택 HCP version support와 SG/route ownership 확인.
- DNS authoritative zone/FQDN/SAN/public CA fingerprint 및 P1 관련 원본 연결.
현재 접속 세션/권한이 없으므로 실제 수집 명령 실행·결과 확보는 NOT_RUN이다.

승인 후 구현: 원본 backup/hash→IaC/host/BIND precheck→검토된 route/selector/SG·Resolver/zone-rule subset→domain별 readback→아래 시험.
syntax 실패·route/source 확대·managed SG 수정·TLS/SELinux 우회·loop·drift면 중단한다.
복구는 이번 change의 zone-rule/추가SG/route/selector fragment만 exact 이전 상태로 돌리고 readback한다.
다른 팀/기존 P1 DNS·VPN/SA를 flush하거나 endpoint 전체를 무조건 삭제하지 않는다. Terraform state와 host 변경 복구를 분리한다.

| 시험 | 성공 기준 |
|---|---|
| On-Prem→AWS UDP/TCP | DNS52/53 각각에서 API/OAuth/Route 실제 이름·CNAME chain이 올바른 private target으로 해석 |
| AWS→On-Prem UDP/TCP | 승인 workload/node 경로에서 Harbor/DB 이름이 권위 응답과 일치, endpoint source readback |
| Runner→API | query+TLS 이름검증+승인 인증/RBAC 성공; 직접 endpoint IP/TLS 우회 사용 금지 |
| OAuth/Ingress | redirect·인증·업무 Route TLS 성공; API SG 성공으로 대체하지 않음 |
| 미승인 source/zone/port | 접근 거부 근거를 실제 정책/로그로 확인; timeout만으로 deny 주체 PASS 금지 |
| loop·truncated 응답 | 허용 범위 내 query로 forwarding loop 부재·TCP fallback 확인 |
| DNS1대/endpoint IP1개 장애 | 승인 환경에서 실제 client failover/cache TTL·복구 관측; 무단 AWS ENI 삭제/공용 노드 장애주입 금지 |
| Relay/SA 장애·회복 | DNS cache hit와 live query 구분; recovery 후 cold query/TLS·기존 DB positive/engine negative 회귀 |
| 재실행·원복 | source/config revision 고정, 중복 rule 없음·drift STOP·원복 readback |

실측 timeout/retry/cache TTL/RTO 수용값은 PENDING이다. source SEC의30분 목표를 DNS SLA로 자동 적용하지 않는다.
증적은 KST/host/actor/commandRC/sourceSHA/tuple/zone-rule·SG/route/SA revision·query answer/TLS·policy readback·cleanup을 연결한다.
원본/민감 메타데이터 접근 범위와 마스킹 파생본 lineage/hash를 분리한다.

## 8. 담당 연결·남은 결정
| 영역 | 기존 책임 연결 | 완료조건 |
|---|---|---|
| #34/#40 권욱 | mandatory subset과 D23 전체 P1 scope 정렬 | 정확 zone/source·routing 후보와 구현 시점/권위 수용 |
| #35/#38 하영 | Resolver/IaC/PrivateLink·API/Ingress 지원·cloud 반환 | supported version/ports·계정 readback·exact route/SG/입력 |
| #37 재환 | Runner L3 연결·양 peer selector·host forwarding/return | next hop source 보존·reverse DNS exception·회귀/복구 계약 |
| #46 delivery 담당 | Runner target adapter·kube context/단기 credential | private DNS/TLS/RBAC 통과와 실제 deploy 증적 |
| #42 registry 담당 | 기존 Harbor 이름/SAN/CA/source | D22 logical 입력과 cold-pull 일치 |
| #48 conditional DNS | 전체 기능은 기존 Go/capacity 계약 유지 | 최소 subset 구현을 이 티켓에 맡길지 별도 책임 분리할지 authority 수용 |

즉시 필요한 최솟값: Runner→vpn-gw의 실제 routed next hop, DNS52/53 zone/ACL, Harbor/DB 승인 FQDN/SAN, supported HCP API port/SG 조건, mandatory subset 책임/시점.
실제 endpoint/ENI/IP는 생성 후 관측값이다. 이 값이 아직 없다는 이유로 설계 검토를 순환 차단하지 않는다.
새 source/selector/권한/일정은 승인 전 후보다. independent REVIEW=PENDING / STATIC 문서대조 / CI·MOCK·RUNTIME·APPLY·MERGE·정본PUBLICATION=NOT_RUN.

## 9. 근거 — 2026-10-04 조회
- [#40 current authority](https://github.com/321Team/fds-project-baseline/issues/40), [후속 DNS subset](https://github.com/321Team/fds-project-baseline/issues/40#issuecomment-5968506333), [#48 conditional contract](https://github.com/321Team/fds-project-baseline/issues/48)
- [#37 VPN](https://github.com/321Team/fds-project-baseline/issues/37#issuecomment-5968506170), [#46 adapter](https://github.com/321Team/fds-project-baseline/issues/46#issuecomment-5948127003)
- [HCP private / additional SG §7.4](https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/4/html/install_clusters/rosa-hcp-aws-private-creating-cluster): TCP443·ROSA4.17.2 이상·기본SG변경금지. 현재계정지원은 미확인.
- [AWS endpoint 고려사항](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-choose-vpc.html): endpoint마다 다른AZ 최소2IP·PHZ/VPC 연결.
- [AWS outbound query 경로](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-overview-forward-vpc-to-network.html): endpoint ENI·zone별rule·VPC association·TCP/UDP53.
- [AWS inbound query 경로](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-overview-forward-network-to-vpc.html).

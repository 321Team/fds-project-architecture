# Phase 2 조회·증적 수집 — CloudShell 1인 실행 + ROSA 콘솔 관측
기준: 2026-10-03 21:00 KST. 2026-10-04 후속: collector guard/JSON format·timeout 증적 보존 수정. AI: CODEX_ASSISTED.
상태: EXECUTION_CANDIDATE / AWS 실제 실행 NOT_RUN / 독립 REVIEW PENDING / Freeze HOLD.
연계: [하영 추가 의견](https://github.com/321Team/fds-project-architecture/pull/8#issuecomment-5968593648), #35/#38/#34.
이번 PR8 후속 조회에 한정한 실행안이며 개인 Codex 지침을 팀 공용 정책으로 승격하지 않는다.

## 1. 선택한 방식과 책임
- 권장: 담당 1명(하영 #35/#38 Lead, 이미 세션 가능한 권욱 대행 가능)이 MFA로 FDS-ReadOnly-Audit 역할 전환한 **서울 CloudShell**에서 고정 AWS 조회를 실행한다.
- 팀원 모두의 로컬 CLI/MFA profile 구축, 장기 access key 발급, ROSA CLI 설치를 추가 요구하지 않는다. 기존 권욱 assume/EC2Standard100/AMI/VPC 확인을 이번 새 준비절차 때문에 반복하지 않는다.
- CloudShell은 콘솔 임시권한을 사용하는 경로이며 role을 바꾸면 별도 environment가 된다. root 세션에서 이 수집을 실행하지 않는다. script는 예상 account/role/member session을 검사하고 root/다른계정/다른role을 거부한다.
- AWS 조회역할은 Red Hat 권한을 제한하지 않는다. 이번 script에는 rosa/ocm 호출·토큰 입력·verify·create·login이 없다.
- 정확 HCP 지원 version/type/구독 연결은 Red Hat 콘솔에서 별도 관측한다. EC2 offering/type 응답으로 ROSA 지원을 대체하지 않는다.
- 현재 계정 role은 AWS write가 불허지만 사람/콘솔·외부 CLI 전체 동작을 자동으로 안전하게 만든다는 의미가 아니다. ROSA 사전조건 페이지는 자동 ELB CreateServiceLinkedRole 시도가 실제 거부된 이력이 있으므로 페이지 관측을 무조건 read-only API만 실행한 것으로 표현하지 않는다.

## 2. AWS 고정 조회 범위
[수집 script](phase2-readiness-capture.py)의 검토 대상 source commit:
`c2451973ad99ea9d7192e7f6b0d1d73b576dcf56` (실행파일 SHA256도 capture.json에 기록).
명령은 CLI args 배열로 전달하고 shell 실행/외부 command 입력을 받지 않는다.

| 입력 | 고정 조회 | 해석 |
|---|---|---|
| Principal | sts get-caller-identity | account/assumed role/member guard; 매 실행 세션 안전 확인 |
| CLI version | aws --version | tool version capture |
| EIP | ec2 list-service-quotas의 Elastic IP 이름 filter + describe-addresses | 실제 quota code/name/value와 사용 inventory. code를 기억으로 하드코딩하지 않음 |
| 기타 named quota | vpc/elasticloadbalancing/ebs/route53resolver list-service-quotas | 표준vCPU100 별도 재시험 없음; applicable quotas/사용량/최대surge 판단 별도 |
| Worker | describe-instance-type-offerings(m5.xlarge,2a/2b/2c) + describe-instance-types | EC2 지원/사양만; 즉시 구매 capacity 보장이나 ROSA pool 지원 PASS 아님 |
| ELB role | ListRoles exactname + GetRole metadata | GetRole DENIED는 부재증거 아님. 성공목록/empty와 별도 해석 |
| NAT | describe-nat-gateways id/VPC/subnet/state | quota perAZ와 현재usage 비교. []로 계정총비용0 판정 금지 |

Plan/Apply/Subscribe/SLR생성/권한변경/Quota증액/CloudShell환경생성은 script에 포함하지 않는다.
EIP4와 실제추가 필요·삭제예정 NAT 상태·role존재·quota 적용치가 같아야 readiness인수 가능. quota목록 성공만으로 GO 금지.

## 3. 실행 순서와 정상/실패 판정
실행 위치: 예상 역할로 전환한 ap-northeast-2 CloudShell. AWS CLI/Python3가 이미 사용 가능해야 한다.
1. source SHA가 위 값인 [원본 script](https://github.com/321Team/fds-project-architecture/blob/c2451973ad99ea9d7192e7f6b0d1d73b576dcf56/phase2/runbooks/phase2-readiness-capture.py)를 읽고 CloudShell editor에 동일 내용으로 `phase2-readiness-capture.py` 저장한다. GitHub 개인토큰을 shell history나 Issue에 넣지 않는다. CLI설치/새credential 파일 생성 불필요.
2. root가 아닌 예상 역할 세션인지 확인한 상태에서 아래 실행. 파일을 편집했다면 original source로 주장하지 말고 변경분 검토 후 별도 revision 기록.
```bash
python3 phase2-readiness-capture.py --source-ref c2451973ad99ea9d7192e7f6b0d1d73b576dcf56
```
3. 출력 DIRECTORY는 실행마다 새로 생성된다. 권한 umask077/raw dir0700, 기존경로 덮어쓰기 없음. 명령별 stdout 원문 bytes, stderr 원문 bytes, RC·command·KST와 CLIversion/scriptSHA/sourceSHA를 보존한다.
4. `manifest.json`에는 raw/capture 파일별 path·size·SHA256, 콘솔 출력에는 manifest 자체 SHA256을 별도로 기록한다. manifest는 자기자신을 포함하지 않는다. 최종 transferred bytes에서 size/hash를 다시 확인한다.

정상: RC0 / AWS_READONLY_CAPTURE_COMPLETE = 고정조회 응답을 수집했다는 뜻만. architecture/account준비·Runtime PASS 아님.
부분 실패: RC2 / AWS_READONLY_CAPTURE_PARTIAL, 실패/거부명령과 INVALID_RESPONSES 목록을 확인. AWS RC0이어도 stdout이 잘못된 JSON 또는 object/list가 아니면 capture는 PARTIAL이다. 원래 AWS RC와 bytes를 보존하며 이 format 검사는 실제 quota 값/권한/readiness 판정을 대체하지 않는다. 성공원본/RC/denial을 함께 보존하고 해당입력은 PENDING.
identity/source-ref 실패: STOP, readiness 추가조회 미실행. 최초STS조회는 guard를 위해 수행될 수 있다. root로 바꾸거나 권한을 넓혀 재시도하지 않는다.
각 AWS호출 timeout35초, connect10/read20초; timeout/CLI오류는 실패행으로 기록한다. timeout의 partial stdout/stderr bytes도 보존한다. AWS write를 수행하지 않아 infrastructure rollback은 필요하지 않다. 남은 비용자원을 없앴다고 해석하지 않는다.
스크립트 재실행은 새 directory를 만들므로 기존원본 보존. 로컬 증적 cleanup은 승인된 소유경로만 대상으로 하고, 업로드·수신해시·보존정책 확인 전 삭제하지 않는다.

## 4. ROSA 콘솔 별도 수집표
| 입력 | 남길 관측 |
|---|---|
| HCP exact version | account·region·HCP선택 상태, 지원목록과 stable/channel/lifecycle 표기, 관측 KST |
| Machine type / pools | 선택 version에서 m5.xlarge 가능 여부, AZ/pool count·root storage 지원·제약 |
| AWS↔Red Hat linkage / ROSA 활성화 | explicit enabled/link/subscription/support 상태 또는 확인못한 이유; 일반 nextsteps 문구는 완료증거 아님 |
| CA 등록/egress/private access | exact version/CLI/OCM의 지원 방식. 문서설명과 actual선택가능성을 구분 |
| 변경시도 여부 | 화면 refresh가 자동write시도/denial을 발생시키면 API명·RC/오류·시각을 기록. Enable/Create/Submit 클릭은 이 조회scope에 포함하지 않음 |

스크린샷도 파일 bytes의 SHA256 검증은 가능하다. 다만 해시는 **화면파일이 바뀌지 않았음**을 검증하며 AWS응답 진실성/전체상태/재조회 성공을 증명하지 않는다.
가능하면 원본 screenshot/export + 위 구조화 관측표 + 재현 가능한 화면 경로/선택조건/KST를 함께 보존한다. 계정·region·선택version이 보이지 않으면 부족항목 명시.
브라우저 devtools HAR/쿠키/Authorizationheader/sessionstorage export는 수집하지 않는다. Red Hat token/로그인화면 credential은 촬영·편입하지 않는다.
화면값을 API rawJSON으로 변환해 `RAW_AWS`라고 표시하지 않는다. 종류: `AWS_CLI_RAW`, `CONSOLE_OBSERVATION`, `SANITIZED_DERIVATIVE`, `MOCK`.

## 5. 민감정보·publication 경계
- 이 script는 credential/profile/cache/env/SSMparameter/Secret/S3object/IAMpolicy 본문을 읽지 않는다. credential백업/토큰로그도 만들지 않는다.
- 원본 응답에는 account ID/ARN/public-privateIP/resourceID/metadata가 포함될 수 있다. 토큰/PSK/privatekey와 같지는 않지만 접근범위와 공개필요성을 검토한다.
- `raw/`와 manifest는 자동 Git add/PR/evidence publication 하지 않는다. 실행자 통제경로에 저장 후 권한·scope·민감정보 inspection, 독립 evidence review를 거친다.
- 필요한 마스킹은 원본을 덮어쓰지 않고 derivative로 만든다. 원본SHA/size, derivativeSHA/size, 제거field·이유·처리tool/sourceSHA·담당·시각을 sidecar에 기록. 원본에 Secret이 발견되면 publication STOP, 원본은 제한접근으로 격리; Secret자체를 sidecar에 인용하지 않음.
- rawdata hash 비교는 수집/전송 integrity일 뿐 작성·CI·runtime·review·merge/publication을 대신하지 않는다.
- PR8 IAM/설계 문서를 읽었다는 것과 새 capture 코드 독립리뷰/실제 실행은 구분한다. 새 코드에 reviewer 승인을 만들어 넣지 않는다.

## 6. 이번 작성/검증과 남은 작업
STATIC: Python AST, 고정 AWSread목록/guard/출력·민감정보범위 점검 PASS.
MOCK: 기존5경로 결과는 원래 source 범위. 2026-10-04 collector 수정에서는 root/foreignaccount/unapprovedmember + non-object identity/non-string ARN의 추가조회 STOP, 정상수집/manifest, GetRoleDENIED, RC0 malformed/scalar JSON, timeout partial bytes 보존, 고정read목록의11경로 PASS. [재현 가능한 offline 시험](test_phase2_readiness_capture.py): `python3 test_phase2_readiness_capture.py` (동일 디렉터리에 collector 필요, subprocess mock만 사용). 테스트 명령은 실제 AWS를 실행하지 않는다. 실제 AWS query/permission/state PASS 아님.
CI NOT_RUN / AWS 실제추가조회 NOT_RUN / ROSA Runtime NOT_RUN / 독립 REVIEW PENDING / MERGE·canonical PUBLICATION NOT_RUN.
다음: 담당1인 실제 AWS수집→ROSA console 관측→기대quota/capacity/support와 대조→raw intake/review→#35/#38에 결과와 부족입력 인계.
아직 필요한 full서울단가/교육장한도·기간·gross/accrued·source model/code/SLA·P1live capacity·UID실행은 이capture로 자동해소되지 않는다. Freeze HOLD 유지.

공식:
- [CloudShell 임시권한·role전환](https://docs.aws.amazon.com/cloudshell/latest/userguide/security_iam_service-with-iam.html)
- [ServiceQuotas CLI](https://docs.aws.amazon.com/cli/latest/reference/service-quotas/list-service-quotas.html)

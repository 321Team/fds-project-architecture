# 팀 3인 IAM bootstrap 보완 / 조회 역할 일괄 연결
기준: 2026-10-03 17:04:49 KST 사용자 CloudShell 출력. CODEX_ASSISTED.
상태: 실행 준비 / 사용자 실행 결과 대기 / 독립 리뷰 PENDING.
이 파일 편입 또는 IAM readback은 Architecture Freeze/Runtime acceptance/리뷰 승인이 아니다.

## 범위와 현재 사실
- 사용자: 321team-gwonuk, 321team-hayeoung, 321team-jaehwan. Path=/.
- 세 사람 모두 FDS-Human-Bootstrap 소속. group inline FDS-SelfService-Password-MFA만 관측.
- 사용자 직접 managed/inline policy 없음, permission boundary 없음.
- MFA device count: 권욱1, 하영0, 재환0. device count와 MFA 로그인/role assumption은 다른 검증이다.
- Access key count: 세 사람 모두0. 키를 생성하지 않는다.
- 기존 policy는 암호 변경 권한을 이미 포함한다. 암호 권한이 전혀 없다는 이전 가정은 적용하지 않는다. 계속 거부되면 암호 정책 불일치/현재 세션/조직 제한을 원본 오류로 확인한다.
- 기존 policy는 MFA 없이 DeactivateMFADevice/DeleteVirtualMFADevice를 허용한다. 보완 정책은 MFA 없는 장치 해제/삭제를 명시 Deny한다.
- 본인 MFA 생성 이름은 자신의 사용자명으로 시작해야 한다. 예: 321team-gwonuk-phone. 취소로 남은 미할당 MFA 장치 정리는 관리자가 해당 장치만 확인하여 처리한다.
- 새 FDS-ReadOnly-Audit 역할: 위 세 principal만 신뢰, MFA 필수, max session3600초. 서울 EC2/network/ELB/quota metadata + 자체 역할 정책 조회 + CloudShell 실행용 최소 API만 허용.
- 전체 AWS ReadOnlyAccess 또는 Administrator/PowerUser 정책을 붙이지 않는다. Secret/SSM parameter/S3 object 내용 읽기, Billing 변경, quota 증액, IaC/ROSA operator 권한을 추가하지 않는다.
- CloudShell 환경 생성은 CLI 실행을 위한 shell 권한이며 프로젝트 VPC/EC2/ROSA 생성 권한이 아니다. 사용자 CloudShell 이용은 이 역할로 전환 후 서울 리전에서 수행한다.
- IAM/SCP 등 추가 제한으로 일부 조회/CloudShell 실행이 거부될 수 있다. 넓은 정책으로 우회하지 않고 exact denied action을 후속 검토한다.
- ROSA AWS activation/subscription 조회와 Red Hat org 권한 전체를 이 inventory 역할이 보장하는 것은 아니다.

## 비용 운영 계약 정정
교육장 별도 유료 사용승인은 불필요. 교육장 안내 한도 준수 및 매일 사용금액 보고가 합의사항.
프로젝트 팀에 Billing/CE/Budget 관리권을 필수로 요구하지 않는다. 정확한 한도 수치/집계 범위/리포트 출처는 아직 이 대화에 미제공.
Architecture Freeze와 독립 리뷰/보안/검토된 plan 조건은 유지한다. Freeze 전 프로젝트 유료 Create/Apply 금지.
기존 20261003-gwonuk-console-readiness 안내의 M02는 교육장 데이터/기존 합의에 따른 일별 보고 handoff로 정정; 별도 교육장 사용승인 요구는 superseded.

## 실행
AWS 계정774055931866의 루트 콘솔 CloudShell Bash에서 아래 블록을 한 번 복사/실행한다.
AWS CLI/Python3 필요; 해당 조합은 사용자가 직전 조회에 성공했다. 이 저장소 파일을 원격 fetch하여 자동실행하지 않는다.
현재 snapshot과 정확히 일치할 때만 실행한다. 동명 역할/다른 policy/member가 있으면 STOP하며 자동 덮어쓰지 않는다.
기존 group policy를 CloudShell에 0600 파일로 백업한 후 IAM role/group policy만 수정한다. 자동 rollback은 실패 시 각 단계를 시도하며 실패 항목은 ROLLBACK_CHECK_REQUIRED로 출력한다.
루트 IAM 수정 및 이후 대상 역할 사용도 실제 조직 SCP가 허용해야 한다.
role 생성/정책 grant는 조회 작업용 bootstrap 설정이다. operator 권한/paid infrastructure 실행 승인이 아니다.

```bash
python3 - <<'PY'
import copy, datetime, hashlib, json, os, subprocess
A = "774055931866"
G = "FDS-Human-Bootstrap"
P = "FDS-SelfService-Password-MFA"
R = "FDS-ReadOnly-Audit"
RP = "FDS-Inventory-ReadOnly-v1"
GP = "FDS-Assume-ReadOnly-Audit-v1"
U = ["321team-gwonuk", "321team-hayeoung", "321team-jaehwan"]
def call(*args, missing=False):
    p = subprocess.run(["aws", *args, "--output", "json", "--no-cli-pager"],
                       capture_output=True, text=True)
    if p.returncode:
        if missing and "(NoSuchEntity)" in p.stderr:
            return None
        raise RuntimeError(p.stderr.strip())
    return json.loads(p.stdout or "{}")
def doc(x): return json.dumps(x, separators=(",", ":"), sort_keys=True)
def sha(x): return hashlib.sha256(doc(x).encode()).hexdigest()
def allow(sid, actions, resource, condition=None):
    s = dict(Sid=sid, Effect="Allow", Action=actions, Resource=resource)
    if condition: s["Condition"] = condition
    return s
identity = call("sts", "get-caller-identity")
if identity["Account"] != A or identity["Arn"] != "arn:aws:iam::"+A+":root":
    raise SystemExit("STOP: expected project account root session.")
group = call("iam", "get-group", "--group-name", G)
if sorted(x["UserName"] for x in group["Users"]) != sorted(U):
    raise SystemExit("STOP: group membership changed.")
old = call("iam", "get-group-policy", "--group-name", G,
           "--policy-name", P)["PolicyDocument"]
expected = {"Version":"2012-10-17","Statement":[
    allow("ViewAccountPasswordPolicy",
          ["iam:GetAccountPasswordPolicy","iam:ListAccountAliases"], "*"),
    allow("ManageOwnPassword", ["iam:GetUser","iam:ChangePassword"],
          "arn:aws:iam::*:user/${aws:username}"),
    allow("ManageOwnMFA", ["iam:ListMFADevices","iam:EnableMFADevice",
          "iam:ResyncMFADevice","iam:DeactivateMFADevice"],
          "arn:aws:iam::*:user/${aws:username}"),
    allow("ManageOwnVirtualMFA", ["iam:CreateVirtualMFADevice",
          "iam:DeleteVirtualMFADevice"], "arn:aws:iam::*:mfa/${aws:username}"),
    allow("ListVirtualMFA", ["iam:ListVirtualMFADevices"], "*")
]}
if old != expected:
    raise SystemExit("STOP: bootstrap policy differs from supplied snapshot.")
for user in U:
    x = call("iam","get-user","--user-name",user)["User"]
    groups = call("iam","list-groups-for-user","--user-name",user)["Groups"]
    if (x["Path"] != "/" or x.get("PermissionsBoundary") or
        [g["GroupName"] for g in groups] != [G] or
        call("iam","list-attached-user-policies","--user-name",user)["AttachedPolicies"] or
        call("iam","list-user-policies","--user-name",user)["PolicyNames"]):
        raise SystemExit("STOP: user permission snapshot changed: "+user)
if call("iam","list-attached-group-policies","--group-name",G)["AttachedPolicies"]:
    raise SystemExit("STOP: group managed policies changed.")
if call("iam","list-group-policies","--group-name",G)["PolicyNames"] != [P]:
    raise SystemExit("STOP: group inline policies changed.")
if call("iam","get-role","--role-name",R,missing=True) is not None:
    raise SystemExit("STOP: role already exists; do not overwrite it.")

mfa = {"Bool":{"aws:MultiFactorAuthPresent":"true"}}
new = copy.deepcopy(old)
for s in new["Statement"]:
    if s["Sid"] == "ManageOwnMFA":
        s["Action"].append("iam:GetMFADevice")
    if s["Sid"] == "ManageOwnVirtualMFA":
        s["Resource"] = "arn:aws:iam::"+A+":mfa/${aws:username}*"
new["Statement"] += [
    allow("ViewAccountSummary", ["iam:GetAccountSummary"], "*"),
    allow("ViewOwnAccessKeyMetadata", ["iam:ListAccessKeys"],
          "arn:aws:iam::"+A+":user/${aws:username}"),
    {"Sid":"DenyMFARemovalWithoutMFA","Effect":"Deny",
     "Action":["iam:DeactivateMFADevice","iam:DeleteVirtualMFADevice"],
     "Resource":"*",
     "Condition":{"BoolIfExists":{"aws:MultiFactorAuthPresent":"false"}}}
]
trust = {"Version":"2012-10-17","Statement":[{
    "Effect":"Allow","Principal":{"AWS":["arn:aws:iam::"+A+":user/"+u for u in U]},
    "Action":"sts:AssumeRole","Condition":mfa
}]}
inventory = {"Version":"2012-10-17","Statement":[
    allow("SeoulNetworkAndComputeInventory", [
        "ec2:DescribeInstances","ec2:DescribeInstanceTypes",
        "ec2:DescribeInstanceTypeOfferings","ec2:DescribeImages",
        "ec2:DescribeAvailabilityZones","ec2:DescribeVpcs",
        "ec2:DescribeSubnets","ec2:DescribeRouteTables",
        "ec2:DescribeNetworkInterfaces","ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules","ec2:DescribeAddresses",
        "ec2:DescribeNatGateways","ec2:DescribeInternetGateways",
        "ec2:DescribeVolumes","ec2:DescribeVpcEndpoints",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "cloudshell:CreateEnvironment","cloudshell:CreateSession",
        "cloudshell:GetEnvironmentStatus","cloudshell:StartEnvironment",
        "cloudshell:PutCredentials",
        "servicequotas:GetServiceQuota","servicequotas:ListServiceQuotas",
        "servicequotas:ListRequestedServiceQuotaChangeHistory"
    ], "*", {"StringEquals":{"aws:RequestedRegion":"ap-northeast-2"}}),
    allow("InspectThisAuditRole", ["iam:GetRole","iam:ListRolePolicies",
          "iam:GetRolePolicy"], "arn:aws:iam::"+A+":role/"+R)
]}
switch = {"Version":"2012-10-17","Statement":[
    allow("AssumeApprovedInventoryRole", ["sts:AssumeRole"],
          "arn:aws:iam::"+A+":role/"+R, mfa)
]}
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = "fds-bootstrap-backup-"+stamp+".json"
fd = os.open(backup, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
with os.fdopen(fd,"w") as f: json.dump(old,f,indent=2)
created = changed = linked = False
try:
    call("iam","create-role","--role-name",R,
         "--assume-role-policy-document",doc(trust),"--max-session-duration","3600",
         "--description","321Team Seoul metadata inventory only; MFA required",
         "--tags","Key=Team,Value=321Team","Key=Project,Value=fds-hybrid")
    created = True
    call("iam","put-role-policy","--role-name",R,"--policy-name",RP,
         "--policy-document",doc(inventory))
    call("iam","put-group-policy","--group-name",G,"--policy-name",P,
         "--policy-document",doc(new))
    changed = True
    call("iam","put-group-policy","--group-name",G,"--policy-name",GP,
         "--policy-document",doc(switch))
    linked = True
    checks = [
        call("iam","get-group-policy","--group-name",G,"--policy-name",P)["PolicyDocument"] == new,
        call("iam","get-group-policy","--group-name",G,"--policy-name",GP)["PolicyDocument"] == switch,
        call("iam","get-role-policy","--role-name",R,"--policy-name",RP)["PolicyDocument"] == inventory,
        call("iam","get-role","--role-name",R)["Role"]["AssumeRolePolicyDocument"] == trust
    ]
    if not all(checks): raise RuntimeError("Policy readback mismatch.")
    print(json.dumps({"STATUS":"IAM_CONFIG_READBACK_PASS",
        "BACKUP":backup,"ROLE":R,"BOOTSTRAP_SHA256":sha(new),
        "TRUST_SHA256":sha(trust),"INVENTORY_SHA256":sha(inventory),
        "ASSUME_GRANT_SHA256":sha(switch),
        "MFA_COUNTS":{u:len(call("iam","list-mfa-devices",
                        "--user-name",u)["MFADevices"]) for u in U},
        "ASSUME_ROLE_RUNTIME":"NOT_TESTED","INDEPENDENT_REVIEW":"PENDING",
        "PAID_RESOURCE_CREATE_APPLY":"NOT_RUN"},indent=2))
except Exception as e:
    print("STOP:",str(e))
    # Keep attempting each rollback step even if an earlier one fails.
    steps = []
    if linked: steps.append(("iam","delete-group-policy","--group-name",G,"--policy-name",GP))
    if changed: steps.append(("iam","put-group-policy","--group-name",G,"--policy-name",P,
                              "--policy-document",doc(old)))
    if created:
        steps += [("iam","delete-role-policy","--role-name",R,"--policy-name",RP),
                  ("iam","delete-role","--role-name",R)]
    for step in steps:
        try: call(*step)
        except Exception as rollback_error: print("ROLLBACK_CHECK_REQUIRED:",str(rollback_error))
    print("BACKUP:",backup)
    raise SystemExit(1)
PY
```

## 정상 판정 및 후속
1. STATUS=IAM_CONFIG_READBACK_PASS: configuration equality 확인까지만 PASS. MFA sign-in/role assumption 아직 NOT_TESTED.
2. 각 사용자 본인 IAM console 로그인, My security credentials에서 MFA 확인/등록. MFA 등록 후 로그아웃하여 MFA로 재로그인.
3. Switch role: Account774055931866 / Role FDS-ReadOnly-Audit. 루트 세션으로 역할 전환 성공을 시험하지 않는다.
4. 역할 전환 후 서울 EC2/VPC/Service Quotas 조회; 필요 시 CloudShell에서 다음 실행:
```bash
aws sts get-caller-identity --query Arn --output text --no-cli-pager
aws ec2 describe-vpcs --region ap-northeast-2 --query 'Vpcs[].{VpcId:VpcId,Cidr:CidrBlock}' --output json --no-cli-pager
aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A --region ap-northeast-2 --query 'Quota.Value' --output text --no-cli-pager
```
expected principal=assumed-role/FDS-ReadOnly-Audit/...; quota는 최신 실제 조회값을 사용한다. 기존 기록100과 다르면 차이를 기록한다.
5. Negative: MFA 없이는 role trust가 거부하는 설계다. Create/Delete 또는 유료 API 호출로 거부 시험을 하지 않는다. 독립 Reviewer가 policy/trust 및 실패 경로를 확인한다.
6. 실행 결과에는 KST시각, config hash, 각 담당자 MFA 로그인/Assume 결과를 구분한다. QR/OTP/credentials를 공개하지 않는다.
7. 아래 복구는 자동rollback 실패 또는 명시적 revert시에만 사용한다. script 출력 BACKUP의 실제 파일명을 지정한다.
```bash
aws iam delete-group-policy --group-name FDS-Human-Bootstrap --policy-name FDS-Assume-ReadOnly-Audit-v1
aws iam put-group-policy --group-name FDS-Human-Bootstrap --policy-name FDS-SelfService-Password-MFA --policy-document file://ACTUAL_BACKUP_FILE.json
aws iam delete-role-policy --role-name FDS-ReadOnly-Audit --policy-name FDS-Inventory-ReadOnly-v1
aws iam delete-role --role-name FDS-ReadOnly-Audit
```
백업 복원은 기존 MFA 삭제 제한 부족도 복원하므로 사고 복구용이다. 다른 사양으로 임의 교체하지 않는다.

## 검증 상태
STATIC=source/control flow review + Python AST parse PASS. MOCK 및 AWS 실행 미실시.
CI=미확인 / IAM_CONFIG_RUNTIME=사용자 실행 대기 / MFA_SIGNIN_ASSUMEROLE=미시험 / INDEPENDENT_REVIEW=PENDING /
PROJECT_RUNTIME=NOT_RUN / MERGE=NOT_RUN / MAIN_PUBLICATION=NOT_RUN.
담당: 각 본인 MFA/role login; #35 Lead 이하영; 변경 author 이권욱/AI 지원, 독립 리뷰 별도 담당.

"""Phase 2 AWS readiness capture. AWS reads only; no ROSA token handling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone, timedelta

ACCOUNT = "774055931866"
REGION = "ap-northeast-2"
ROLE = "FDS-ReadOnly-Audit"
MEMBERS = {"321team-gwonuk", "321team-hayeoung", "321team-jaehwan"}
KST = timezone(timedelta(hours=9))
SLR = "AWSServiceRoleForElasticLoadBalancing"
COMMANDS = [
    ("eip-quota", ["service-quotas", "list-service-quotas", "--service-code", "ec2",
        "--query", "Quotas[?contains(QuotaName, 'Elastic IP')]"]),
    ("vpc-quotas", ["service-quotas", "list-service-quotas", "--service-code", "vpc"]),
    ("elb-quotas", ["service-quotas", "list-service-quotas", "--service-code", "elasticloadbalancing"]),
    ("ebs-quotas", ["service-quotas", "list-service-quotas", "--service-code", "ebs"]),
    ("resolver-quotas", ["service-quotas", "list-service-quotas", "--service-code", "route53resolver"]),
    ("worker-offerings", ["ec2", "describe-instance-type-offerings",
        "--location-type", "availability-zone",
        "--filters", "Name=instance-type,Values=m5.xlarge",
        "Name=location,Values=ap-northeast-2a,ap-northeast-2b,ap-northeast-2c"]),
    ("worker-type", ["ec2", "describe-instance-types", "--instance-types", "m5.xlarge"]),
    ("elb-role-list", ["iam", "list-roles", "--query",
        "Roles[?RoleName=='" + SLR + "'].{Name:RoleName,Arn:Arn,Path:Path}"]),
    ("elb-role-get", ["iam", "get-role", "--role-name", SLR, "--query",
        "Role.{Name:RoleName,Arn:Arn,Path:Path,CreateDate:CreateDate}"]),
    ("eip-inventory", ["ec2", "describe-addresses", "--query",
        "Addresses[].{AllocationId:AllocationId,PublicIp:PublicIp,AssociationId:AssociationId}"]),
    ("nat-inventory", ["ec2", "describe-nat-gateways", "--query",
        "NatGateways[].{Id:NatGatewayId,VpcId:VpcId,SubnetId:SubnetId,State:State}"]),
]

def invoke(args):
    cmd = ["aws", *args, "--region", REGION, "--output", "json", "--no-cli-pager",
           "--cli-connect-timeout", "10", "--cli-read-timeout", "20"]
    if args == ["--version"]:
        cmd = ["aws", "--version"]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=35)
        return cmd, p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return cmd, 124, b"", b"CAPTURE_TIMEOUT; response not available"
    except OSError as exc:
        return cmd, 127, b"", ("CLI_EXECUTION_FAILED: " + type(exc).__name__).encode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-ref", required=True)
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_ref):
        raise SystemExit("STOP: source-ref must be the immutable GitHub commit SHA.")
    cmd, rc, stdout, stderr = invoke(["sts", "get-caller-identity"])
    if rc:
        raise SystemExit("STOP: identity lookup failed; no further AWS reads performed.")
    try:
        ident = json.loads(stdout)
    except (ValueError, TypeError):
        raise SystemExit("STOP: invalid identity response.")
    prefix = "arn:aws:sts::" + ACCOUNT + ":assumed-role/" + ROLE + "/"
    arn = ident.get("Arn", "")
    if ident.get("Account") != ACCOUNT or not arn.startswith(prefix):
        raise SystemExit("STOP: expected account and assumed read-only role; root/IAM sessions rejected.")
    if arn[len(prefix):] not in MEMBERS:
        raise SystemExit("STOP: session name not in approved member set; inspect identity, do not broaden policy.")
    os.umask(0o077)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    base = Path("fds-readiness-" + stamp)
    raw = base / "raw"
    raw.mkdir(parents=True, mode=0o700)
    rows = []
    def save(name, command, result_rc, out, err):
        suffix = ".stdout.txt" if name == "aws-cli-version" else ".stdout.json"
        (raw / (name + suffix)).write_bytes(out)
        (raw / (name + ".stderr.txt")).write_bytes(err)
        rows.append({"id": name, "command": command, "rc": result_rc,
                     "captured_kst": datetime.now(KST).isoformat(),
                     "scope": "AWS_READ_ONLY; NOT_ROSA_RUNTIME"})
    save("caller", cmd, rc, stdout, stderr)
    _, vrc, vout, verr = invoke(["--version"])
    save("aws-cli-version", ["aws", "--version"], vrc, vout, verr)
    for name, arguments in COMMANDS:
        command, result_rc, out, err = invoke(arguments)
        save(name, command, result_rc, out, err)
    denied = [r["id"] for r in rows if r["rc"] != 0]
    status = "AWS_READONLY_CAPTURE_PARTIAL" if denied else "AWS_READONLY_CAPTURE_COMPLETE"
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary = {"status": status, "source_ref": args.source_ref, "script_sha256": script_sha,
               "region": REGION, "commands": rows, "failed_or_denied": denied,
               "interpretation": "Capture completeness only; architecture/account readiness not adjudicated.",
               "ROSA_VERSION_TYPE_SUPPORT": "NOT_COLLECTED_AWS_API_IS_NOT_ROSA_AUTHORITY",
               "ROSA_RUNTIME": "NOT_RUN", "RESOURCE_WRITE": "NOT_RUN",
               "PUBLICATION": "NOT_RUN", "REVIEW": "PENDING"}
    (base / "capture.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = []
    for path in sorted(base.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            manifest.append({"path": path.relative_to(base).as_posix(), "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()})
    manifest_path = base / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"STATUS": status, "DIRECTORY": str(base),
        "MANIFEST_SHA256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "FAILED_OR_DENIED": denied, "PUBLICATION": "NOT_RUN"}, indent=2))
    return 2 if denied else 0

if __name__ == "__main__":
    raise SystemExit(main())

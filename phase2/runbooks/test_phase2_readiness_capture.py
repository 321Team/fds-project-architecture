import contextlib, hashlib, importlib.util, io, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import subprocess
SOURCE=Path(__file__).with_name("phase2-readiness-capture.py")
spec=importlib.util.spec_from_file_location("collector",SOURCE)
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
SHA="e957eab6f5e146721f3439efe7230f6ded295b61"
GOOD={"Account":collector.ACCOUNT,"Arn":f"arn:aws:sts::{collector.ACCOUNT}:assumed-role/{collector.ROLE}/321team-gwonuk"}
class CollectorTests(unittest.TestCase):
    def run_case(self, identity=GOOD, mode="normal"):
        calls=[]
        self.last_calls=calls
        def fake(cmd,**kwargs):
            calls.append(cmd)
            if cmd[1:3]==["sts","get-caller-identity"]:
                return subprocess.CompletedProcess(cmd,0,json.dumps(identity).encode(),b"")
            if cmd==["aws","--version"]:return subprocess.CompletedProcess(cmd,0,b"aws-cli/2 MOCK",b"")
            if "get-role" in cmd:
                if mode=="denied":return subprocess.CompletedProcess(cmd,254,b"",b"AccessDenied MOCK")
                if mode=="malformed":return subprocess.CompletedProcess(cmd,0,b"{broken",b"")
                if mode=="scalar":return subprocess.CompletedProcess(cmd,0,b"null",b"")
                if mode=="timeout":raise subprocess.TimeoutExpired(cmd,35,output=b'{"partial":',stderr=b"partial diagnostic")
            return subprocess.CompletedProcess(cmd,0,b"{}",b"")
        old=os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            try:
                os.chdir(td)
                with patch.object(sys,"argv",["capture","--source-ref",SHA]),patch.object(collector.subprocess,"run",side_effect=fake),contextlib.redirect_stdout(io.StringIO()):
                    rc=collector.main()
                base=next(Path(td).glob("fds-readiness-*"))
                summary=json.loads((base/"capture.json").read_text())
                manifest=json.loads((base/"manifest.json").read_text())
                for row in manifest:
                    data=(base/row["path"]).read_bytes()
                    self.assertEqual(len(data),row["bytes"]);self.assertEqual(hashlib.sha256(data).hexdigest(),row["sha256"])
                raw={p.name:p.read_bytes() for p in (base/"raw").iterdir()}
                return rc,summary,raw,calls
            finally:os.chdir(old)
    def expect_stop(self,identity):
        with self.assertRaises(SystemExit) as e:self.run_case(identity)
        self.assertIn("STOP",str(e.exception))
        self.assertEqual(len(self.last_calls),1, "guard must stop before subsequent AWS calls")
    def test_valid_capture_and_manifest(self):
        rc,s,raw,calls=self.run_case()
        self.assertEqual(rc,0);self.assertEqual(s["RESOURCE_WRITE"],"NOT_RUN")
        self.assertEqual(len(calls),len(collector.COMMANDS)+2)
        self.assertEqual(s["status"],"AWS_READONLY_CAPTURE_COMPLETE")
    def test_root_guard(self):self.expect_stop({"Account":collector.ACCOUNT,"Arn":f"arn:aws:iam::{collector.ACCOUNT}:root"})
    def test_other_account_guard(self):self.expect_stop({**GOOD,"Account":"000000000000"})
    def test_unapproved_member_guard(self):self.expect_stop({**GOOD,"Arn":GOOD["Arn"].replace("321team-gwonuk","unapproved")})
    def test_non_object_identity_guard(self):self.expect_stop([])
    def test_non_string_arn_guard(self):self.expect_stop({**GOOD,"Arn":42})
    def test_denied_read_is_partial(self):
        rc,s,raw,calls=self.run_case(mode="denied")
        self.assertEqual(rc,2);self.assertIn("elb-role-get",s["failed_or_denied"])
    def test_rc_zero_malformed_response_is_partial(self):
        rc,s,raw,calls=self.run_case(mode="malformed")
        self.assertEqual(rc,2);self.assertEqual(raw["elb-role-get.stdout.json"],b"{broken")
        self.assertEqual(next(r for r in s["commands"] if r["id"]=="elb-role-get")["rc"],0)
    def test_rc_zero_scalar_response_is_partial(self):
        rc,s,raw,calls=self.run_case(mode="scalar");self.assertEqual(rc,2)
    def test_timeout_preserves_partial_bytes(self):
        rc,s,raw,calls=self.run_case(mode="timeout")
        self.assertEqual(rc,2);self.assertEqual(raw["elb-role-get.stdout.json"],b'{"partial":')
        self.assertIn(b"partial diagnostic",raw["elb-role-get.stderr.txt"])
    def test_fixed_read_commands(self):
        permitted={"list-service-quotas","describe-instance-type-offerings","describe-instance-types","list-roles","get-role","describe-addresses","describe-nat-gateways"}
        for _,args in collector.COMMANDS:self.assertIn(args[1],permitted)
if __name__=="__main__":unittest.main(verbosity=2)

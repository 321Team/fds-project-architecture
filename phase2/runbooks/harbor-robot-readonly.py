#!/usr/bin/env python3
"""D22 Harbor Robot metadata intake; GET only, no credential/raw-body files."""
import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
import ssl
import sys
import tempfile
import warnings
from datetime import datetime, timezone, timedelta
from urllib import request, error

CA = Path("/home/server01_cicd-runner/.config/containers/certs.d/10.1.93.54/ca.crt")
CA_SHA = "20ddfa5e92c346aaf46fc30179fbc0b069e256effd2615a9f4308a8fe719053f"
BASE = "https://10.1.93.54/api/v2.0/robots"
TARGETS = ("robot$worker", "robot$push")
KST = timezone(timedelta(hours=9))

class Stop(Exception):
    pass

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Stop("HTTP redirect refused")

def require(value, typ, label):
    if type(value) is not typ:
        raise Stop("Missing or invalid metadata: " + label)
    return value

def select_robot(raw):
    require(raw, dict, "robot")
    result = {}
    for key, typ in (("id", int), ("name", str), ("level", str),
                     ("disable", bool), ("expires_at", int)):
        result[key] = require(raw.get(key), typ, key)
    duration = raw.get("duration")
    if duration is not None:
        require(duration, int, "duration")
    result["duration"] = duration
    permissions = require(raw.get("permissions"), list, "permissions")
    result["permissions"] = []
    for p in permissions:
        require(p, dict, "permission")
        entry = {k: require(p.get(k), str, k) for k in ("kind", "namespace")}
        entry["access"] = []
        for a in require(p.get("access"), list, "access"):
            require(a, dict, "access entry")
            item = {k: require(a.get(k), str, k) for k in ("resource", "action")}
            # Keep omitted effect explicit; do not infer allow.
            effect = a.get("effect")
            if effect is not None:
                require(effect, str, "effect")
            item["effect"] = effect
            entry["access"].append(item)
        result["permissions"].append(entry)
    exp = result["expires_at"]
    if exp > 0:
        try:
            result["expires_at_kst"] = datetime.fromtimestamp(exp, KST).isoformat()
        except (ValueError, OverflowError, OSError):
            raise Stop("Invalid expiry timestamp") from None
    else:
        result["expires_at_kst"] = None
    return result

def collect(opener, auth):
    found, seen = {}, set()
    # An empty page confirms end of traversal; do not trust short pages alone.
    for page in range(1, 102):
        req = request.Request(BASE + "?page=" + str(page) + "&page_size=100",
                              headers={"Authorization": auth, "Accept": "application/json"},
                              method="GET")
        with opener.open(req, timeout=20) as response:
            if response.status != 200:
                raise Stop("Unexpected HTTP status")
            body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            raise Stop("API response too large")
        try:
            rows = json.loads(body)
        except (ValueError, UnicodeError):
            raise Stop("Invalid API JSON") from None
        require(rows, list, "robot list")
        if not rows:
            return found
        if page > 100:
            raise Stop("Pagination limit; incomplete capture")
        for row in rows:
            require(row, dict, "robot entry")
            rid = require(row.get("id"), int, "id")
            name = require(row.get("name"), str, "name")
            if rid in seen:
                raise Stop("Duplicate robot ID across pages; retry capture")
            seen.add(rid)
            if name in TARGETS:
                if name in found:
                    raise Stop("Duplicate target name")
                found[name] = select_robot(row)
    raise Stop("Incomplete pagination")

def main():
    os.umask(0o077)
    try:
        ca_bytes = CA.read_bytes()
    except OSError:
        raise Stop("Root CA file missing or unreadable") from None
    if hashlib.sha256(ca_bytes).hexdigest() != CA_SHA:
        raise Stop("Root CA hash mismatch")
    # Trust only the pinned public CA bytes; verify IP SAN and certificate chain.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(cadata=ca_bytes.decode("ascii"))
    opener = request.build_opener(request.ProxyHandler({}),
                                  request.HTTPSHandler(context=ctx), NoRedirect())
    if not sys.stdin.isatty():
        raise Stop("Run this saved file directly from an interactive terminal")
    user = input("Existing Harbor metadata reader username: ").strip()
    if not user or ":" in user:
        raise Stop("Invalid username")
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        password = getpass.getpass("Harbor password / OIDC CLI secret (hidden): ")
    if not password:
        raise Stop("Empty credential")
    auth = "Basic " + base64.b64encode((user + ":" + password).encode()).decode()
    del password
    found = collect(opener, auth)
    del auth
    missing = [name for name in TARGETS if name not in found]
    report = {
        "state": "PARTIAL_MISSING_TARGETS" if missing else "CAPTURED_REVIEW_REQUIRED",
        "captured_at_kst": datetime.now(KST).isoformat(),
        "endpoint": BASE,
        "root_pem_sha256": CA_SHA,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "missing_or_not_visible": missing,
        "robots": [found[name] for name in TARGETS if name in found],
        "scope": "Metadata only; no login/pull/push or authorization acceptance test."
    }
    output = Path(tempfile.mkdtemp(prefix="d22-robot-ro-", dir=str(Path.home())))
    encoded = (json.dumps(report, ensure_ascii=True, indent=2) + "\n").encode()
    (output / "robot-metadata.json").write_bytes(encoded)
    (output / "SHA256SUMS").write_text(
        hashlib.sha256(encoded).hexdigest() + "  robot-metadata.json\n", encoding="ascii")
    print(encoded.decode(), end="")
    print("READONLY_CAPTURE=" + str(output))
    return 2 if missing else 0

def run():
    try:
        return main()
    except error.HTTPError as exc:
        print("STOP: HTTP " + str(exc.code) + " (check existing account visibility/permissions)")
    except error.URLError:
        print("STOP: TLS or connection failed; no insecure fallback")
    except Stop as exc:
        print("STOP: " + str(exc))
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        print("\nSTOP: Credential input cancelled or hidden input unavailable")
    except Exception:
        # Do not print raw response, request headers, credentials or traceback.
        print("STOP: Local/API processing error; no raw diagnostic emitted")
    return 2

if __name__ == "__main__":
    sys.exit(run())

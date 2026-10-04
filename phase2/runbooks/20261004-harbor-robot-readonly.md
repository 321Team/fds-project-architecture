# D22 Harbor Robot metadata read-only capture

Source contract: [Harbor v2.13.1 API](https://github.com/goharbor/harbor/blob/v2.13.1/api/v2.0/swagger.yaml), GET /robots, Robot/RobotPermission/Access schemas.

## Run on cicd-runner01

Save [harbor-robot-readonly.py](harbor-robot-readonly.py) as
/home/server01_cicd-runner/harbor-robot-readonly.py using GitHub Raw/download and your existing file transfer method.
Requires Python 3 and an interactive terminal. The known CA path and expected PEM SHA256 are already configured.

```bash
if python3 /home/server01_cicd-runner/harbor-robot-readonly.py; then
  printf 'D22_ROBOT_EXIT_CODE=0\n'
else
  d22_robot_rc=$?
  printf 'D22_ROBOT_EXIT_CODE=%s\n터미널은 유지됩니다.\n' "$d22_robot_rc"
fi
```

Use an existing Harbor account that can read the relevant Robot metadata. Enter its password or OIDC CLI secret only at the hidden prompt; do not paste it into chat. This does not ask for either target Robot secret. No account creation, credential rotation, permission changes, POST/PUT/PATCH/DELETE, login/pull/push tests.

The wrapper reports the child exit code without changing parent shell options; its final shell status is not the collector status. Run the complete if block.

## Output and interpretation

Output directory: ~/d22-robot-ro-<random>, mode 0700; files mode 0600:
- robot-metadata.json: allowlisted metadata for exact names robot$worker and robot$push.
- SHA256SUMS: checksum of that JSON file.

Share the printed metadata and READONLY_CAPTURE / D22_ROBOT_EXIT_CODE lines. No raw API body, password, authorization header, description, or secret field is written. Console JSON escapes control characters.

CAPTURED_REVIEW_REQUIRED means both names were captured, not that privilege/expiry policy passed.
PARTIAL_MISSING_TARGETS (exit 2) means missing or not visible to the account; not proof of global absence. HTTP 401/403 stops; use the existing access process, do not create grants for this script.

expires_at is preserved as the API integer; positive values also have a KST rendering. Zero/negative values remain explicit without guessing their meaning. disable, duration, permission kind/namespace/resource/action/effect are preserved. Omitted effect is null, not inferred allow. Compare actual project permissions and expiry with the input contract after capture.

HTTPS connects directly to 10.1.93.54 and verifies its IP SAN using only pinned CA bytes. Ambient proxies and redirects are disabled. GET list pagination is bounded to 100 data pages plus an empty-page check; repeated IDs and malformed metadata stop capture. Results are not an atomic snapshot if accounts change while paging.

## Validation

10 local offline unittest cases passed on 2026-10-04: pagination and secret omission; missing targets; duplicate IDs; invalid JSON; missing fields; wrong scalar types; disabled/expired metadata; negative expiry; redirects; safe 401/403 diagnostics. No live Harbor API call performed by the author.
Run: python3 -m unittest discover -s phase2/runbooks -p test_harbor_robot_readonly.py

Code review pending; Phase 2 Freeze HOLD remains. This collector supplies metadata evidence only.

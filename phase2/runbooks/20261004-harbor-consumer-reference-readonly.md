# D22 consumer 참조 사전 확인 — 2026-10-04

상태: SOURCE_REVIEWED / LIVE_REFERENCE_PENDING / ROTATION_NOT_RUN.
기존 [D22 입력 계약](../reviews/20261004-harbor-d22-input-contract.md) 1.4~1.5를 보완한다.
자격 재발급/Secret 변경/Pod 생성 명령은 포함하지 않는다.

## 1. 고정 소스에서 확인한 consumer

infra-monitoring main 관측 commit: `01f7d59e215627652c6a32b669261feadac45c82`.
아래는 모두 Pod template에 imagePullSecrets=harbor-pull-secret을 명시한다.

| namespace | workload | serviceAccountName | 원본 |
|---|---|---|---|
| monitoring-node | DaemonSet/node-exporter | node-exporter-sa | [node-exporter.yaml](https://github.com/321Team/infra-monitoring/blob/01f7d59e215627652c6a32b669261feadac45c82/kubernetes/monitoring/node-exporter.yaml) |
| monitoring-api | Deployment/prometheus | prometheus-sa | [prometheus.yaml](https://github.com/321Team/infra-monitoring/blob/01f7d59e215627652c6a32b669261feadac45c82/kubernetes/monitoring/prometheus.yaml) |
| monitoring-api | Deployment/grafana | grafana-sa | [grafana.yaml](https://github.com/321Team/infra-monitoring/blob/01f7d59e215627652c6a32b669261feadac45c82/kubernetes/monitoring/grafana.yaml) |
| monitoring-api | Deployment/alertmanager | alertmanager-sa | [alertmanager-deploy.yaml](https://github.com/321Team/infra-monitoring/blob/01f7d59e215627652c6a32b669261feadac45c82/kubernetes/monitoring/alertmanager-deploy.yaml) |
| monitoring-api | Deployment/kube-state-metrics | kube-state-metrics-sa | [kube-state-metrics.yaml](https://github.com/321Team/infra-monitoring/blob/01f7d59e215627652c6a32b669261feadac45c82/kubernetes/monitoring/kube-state-metrics.yaml) |

fds-msa main `5120b7df72d24ada3dbcf23fc0292fb58ae778af`의 관련 YAML은 references/upstream 아래에 있으므로 current 배포 소스 증명으로 사용하지 않는다. fds-app의 기존 기대 SA는 transaction-api-sa / fds-engine-sa이며 실제 연결은 아래 현장 조회로 확인한다.

infra-cicd main `07f7f26d306056203e057b43bdf5234a2de2b8ae`의 `.github/workflows/app-test-build-scan.yml`, `tools/delivery/app_workflow.py`에서 authfile / REGISTRY_AUTH / HARBOR_ / podman login 문자열은 찾지 못했다. 이 제한된 조회를 credential 부재로 판단하지 않는다.
실제 IF-09/CI 실행 환경의 authfile 지정·실행 사용자 연결은 미확인이다.

## 2. control01에서 실제 참조 조회

기존 승인 kubeconfig를 사용하는 control01에서만 실행한다. 먼저 표시되는 context가 대상 클러스터인지 확인한다.
Runner에 kubeconfig를 복사하지 않는다. GET만 수행하며 Secret의 data/stringData/annotation 원문을 출력하지 않는다.
권한 부족이면 중단하고 기존 운영자에게 동일 조회를 요청한다. 새 RBAC를 만들지 않는다.

```bash
if kubectl config current-context; then
  printf '표시된 context가 대상 클러스터인지 확인 후 다음 블록을 실행하세요.\n'
else
  printf 'STOP: 기존 kubeconfig/context 확인 필요\n'
fi
```

context를 확인한 뒤 아래 블록 전체를 실행한다.

```bash
if bash --noprofile --norc <<'D22_CONSUMER_RO'
set +u
set +e
set +o pipefail
test "$(hostname -s)" = k8s-control01 || { printf 'STOP: control01에서 실행\n'; exit 2; }
command -v kubectl >/dev/null || exit 2
TZ=Asia/Seoul date --iso-8601=seconds
for ns in fds-app monitoring-api monitoring-node; do
  printf '\nNAMESPACE=%s\n' "$ns"
  kubectl --request-timeout=20s -n "$ns" get deployments,daemonsets,statefulsets     -o 'jsonpath={range .items[*]}{.kind}{"/"}{.metadata.name}{" SA="}{.spec.template.spec.serviceAccountName}{" PULL_SECRETS="}{.spec.template.spec.imagePullSecrets[*].name}{"\n"}{end}' || exit 2
  kubectl --request-timeout=20s -n "$ns" get serviceaccounts     -o 'jsonpath={range .items[*]}{.metadata.name}{" PULL_SECRETS="}{.imagePullSecrets[*].name}{"\n"}{end}' || exit 2
  kubectl --request-timeout=20s -n "$ns" get pods     -o 'jsonpath={range .items[*]}{.metadata.name}{" SA="}{.spec.serviceAccountName}{" PULL_SECRETS="}{.spec.imagePullSecrets[*].name}{" NODE="}{.spec.nodeName}{"\n"}{end}' || exit 2
  kubectl --request-timeout=20s -n "$ns" get secret harbor-pull-secret     -o 'jsonpath={.metadata.name}{" TYPE="}{.type}{" UID="}{.metadata.uid}{" RV="}{.metadata.resourceVersion}{"\n"}' || exit 2
done
D22_CONSUMER_RO
then
  printf 'D22_CONSUMER_READ_RC=0\n'
else
  d22_consumer_rc=$?
  printf 'D22_CONSUMER_READ_RC=%s\n터미널은 유지됩니다.\n' "$d22_consumer_rc"
fi
```

RC0는 조회 성공이다. 위 소스와 실제 workload/SA/Secret 참조가 일치하는지 별도로 검토한다.
빈 template SA는 default 적용 가능성이 있으므로 실제 Pod/SA 출력을 함께 본다.
Secret metadata만으로 내부 registry/principal 또는 최신 credential 적용을 판정하지 않는다.
목록은 deployments/daemonsets/statefulsets/current pods 범위이며 Job/CronJob 등 모든 consumer의 완전한 inventory를 보장하지 않는다.
실패 시 변경된 클러스터 자원은 없으므로 rollback은 필요 없다. 오류를 해결한 뒤 실패 namespace부터 재조회한다.

## 3. Runner 자격 파일 후보 — 내용 조회 금지

cicd-runner01의 server01_cicd-runner 계정에서 실행한다. 파일 존재·권한만 조회하며 내용/해시/환경 전체를 출력하지 않는다.

```bash
if bash --noprofile --norc <<'D22_RUNNER_REF'
set +u
set +e
set +o pipefail
test "$(hostname -s)" = cicd-runner01 || exit 2
test "$(id -un)" = server01_cicd-runner || exit 2
for p in "/run/user/$(id -u)/containers/auth.json"   "/home/server01_cicd-runner/.config/containers/auth.json"   "/home/server01_cicd-runner/.docker/config.json"; do
  if [ -e "$p" ]; then
    stat -c 'CANDIDATE=%n OWNER=%U MODE=%a TYPE=%F' -- "$p" || exit 2
  else
    printf 'CANDIDATE_ABSENT=%s\n' "$p"
  fi
done
printf 'ACTIVE_AUTHFILE_BINDING=NOT_VERIFIED\n'
D22_RUNNER_REF
then
  printf 'D22_RUNNER_REF_RC=0\n'
else
  d22_ref_rc=$?
  printf 'D22_RUNNER_REF_RC=%s\n터미널은 유지됩니다.\n' "$d22_ref_rc"
fi
```

파일 존재는 실제 사용 증명이 아니다. 기존 IF-09/CI 담당자가 실행 명령의 --authfile,
REGISTRY_AUTH_FILE/XDG 경로 지정, 실행 사용자, 임시 authfile 생성·제거 여부를 확인하여 **경로와 방식만** 전달한다.
shell history, process argv 전체, env 전체, auth.json, dockerconfigjson은 공유하지 않는다.
환경변수/옵션 미지정 기본 경로를 실제 소비 위치로 자동 확정하지 않는다.

## 4. 실행 전 결정 기록

기존 Lead 10/12~13 일정(안)을 유지한다. 아래 미확인 항목을 확인한 다음 실제 rotation으로 넘어간다.
- HBR/consumer 담당: 실제 실행창, 새 30일 expiry 및 동일 계정 refresh/재발급 방식.
- workload 담당: namespace별 실제 소비 SA/Secret, 승인 시험 digest, 시험 자원 cleanup.
- Runner 담당: 실제 사용 authfile/reference 및 교체 방법.
- 공동: 이전 credential 즉시 무효화 여부, 실패 시 정상 workload 보존 및 새 자격 복구 방법.

문서 작성·소스 조회만 수행했다. 위 명령은 현장 실행하지 않았으며 live reference/rotation/인수 PASS로 표시하지 않는다.

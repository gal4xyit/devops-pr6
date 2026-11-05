#!/usr/bin/env bash
set -Eeuo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export DEPLOY_IMAGE="${1:?Usage: bash scripts/deploy.sh IMAGE}"
python_bin="${PYTHON_BIN:-python3}"
compose=(docker compose -f compose.yaml -f compose.deploy.yaml)
rollback_image="devops-pr6:rollback"

if [[ "$DEPLOY_IMAGE" == "$rollback_image" ]]; then
    echo "The rollback tag is reserved; pass a new commit-tagged image."
    exit 1
fi

mkdir -p reports

collect_logs() {
    local phase="$1"
    local container_id
    "${compose[@]}" ps -a > "reports/${phase}-containers.txt" 2>&1 || true
    "${compose[@]}" logs --no-color --timestamps web \
        > "reports/${phase}-container.log" 2>&1 || true
    container_id=$("${compose[@]}" ps -a -q web) || return 0
    if [[ -n "$container_id" ]]; then
        docker inspect --format '{{json .State}}' "$container_id" \
            > "reports/${phase}-state.json" 2>&1 || true
    fi
}

finish() {
    local status=$?
    collect_logs final
    exit "$status"
}
trap finish EXIT

docker image inspect "$DEPLOY_IMAGE" > /dev/null

base_url=$(
    "${compose[@]}" config --format json |
        "$python_bin" -c 'import json, sys; port = json.load(sys.stdin)["services"]["web"]["ports"][0]["published"]; print(f"http://127.0.0.1:{port}")'
)

previous_id=""
container_id=$("${compose[@]}" ps -q web)
if [[ -n "$container_id" ]]; then
    previous_id=$(docker inspect --format '{{.Image}}' "$container_id")
    docker image tag "$previous_id" "$rollback_image"
    echo "Saved previous image: $previous_id"
    collect_logs before
fi

verify_deployment() {
    local phase="$1"
    local expected_id actual_id expected_version container_id

    "${compose[@]}" up -d --no-build --pull never \
        --force-recreate --wait --wait-timeout 60 web || return 1

    container_id=$("${compose[@]}" ps -q web) || return 1
    actual_id=$(docker inspect --format '{{.Image}}' "$container_id") || return 1
    expected_id=$(docker image inspect --format '{{.Id}}' "$DEPLOY_IMAGE") || return 1
    if [[ "$actual_id" != "$expected_id" ]]; then
        echo "ERROR: running image does not match the requested image."
        return 1
    fi

    expected_version=$(
        docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$DEPLOY_IMAGE" |
            sed -n 's/^APP_VERSION=//p'
    ) || return 1
    if [[ -z "$expected_version" ]]; then
        echo "ERROR: image does not define APP_VERSION."
        return 1
    fi

    "$python_bin" scripts/check_http.py "$base_url" "$expected_version" \
        > "reports/${phase}-http.log" 2>&1 || {
            cat "reports/${phase}-http.log"
            return 1
        }
    cat "reports/${phase}-http.log"

    "$python_bin" -m pytest tests/infra -v \
        --junitxml="reports/${phase}-testinfra.xml" || return 1
}

echo "Deploying: $DEPLOY_IMAGE"
if verify_deployment deploy; then
    echo "DEPLOY SUCCESS: $DEPLOY_IMAGE"
    exit 0
fi

echo "DEPLOY FAILED: collecting diagnostics before rollback."
collect_logs failed

if [[ -n "$previous_id" ]]; then
    export DEPLOY_IMAGE="$rollback_image"
    echo "Restoring previous image: $previous_id"
    if verify_deployment rollback; then
        echo "ROLLBACK SUCCESS: previous image restored and verified."
    else
        echo "ROLLBACK FAILED: inspect reports and container logs."
    fi
else
    echo "No previous image exists; stopping the failed deployment."
    "${compose[@]}" stop web || true
fi

exit 1
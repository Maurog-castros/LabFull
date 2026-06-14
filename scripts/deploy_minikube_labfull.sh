#!/usr/bin/env bash

set -euo pipefail

require_var() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required variable: ${name}" >&2
    exit 1
  fi
}

require_var MINIKUBE_HOST
require_var MINIKUBE_USER
require_var PUBLIC_URL

PUBLIC_DASHBOARD_URL="${PUBLIC_DASHBOARD_URL:-https://ministack.maurocastro.cl}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_DIR="${K8S_DEPLOY_DIR:-/opt/labfull}"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=yes)
SSH_TARGET="${MINIKUBE_USER}@${MINIKUBE_HOST}"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keyscan -H "$MINIKUBE_HOST" >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
chmod 600 "$HOME/.ssh/known_hosts"

echo "Syncing workspace to ${SSH_TARGET}:${REMOTE_DIR}"
tar -C "$ROOT_DIR" -cf - \
  app-web \
  backend-fastapi \
  bd \
  docker-compose.yml \
  k8s \
  scripts \
  README.md \
  Jenkinsfile \
  Jenkinsfile.aws \
  .gitignore \
  | ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "mkdir -p '$REMOTE_DIR' && tar -C '$REMOTE_DIR' -xf -"

echo "Deploying LabFull on Ubuntu host"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "MINIKUBE_PROFILE='${MINIKUBE_PROFILE:-}' REMOTE_DIR='$REMOTE_DIR' PUBLIC_URL='$PUBLIC_URL' PUBLIC_DASHBOARD_URL='$PUBLIC_DASHBOARD_URL' APPLY_PUBLIC_PROXY='${APPLY_PUBLIC_PROXY:-0}' bash -s" <<'REMOTE_EOF'
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-labfull}"

echo "Working directory: ${REMOTE_DIR}"
cd "${REMOTE_DIR}"

command -v minikube >/dev/null
command -v kubectl >/dev/null
command -v docker >/dev/null

if ! minikube profile list | grep -qE "^[[:space:]]*${MINIKUBE_PROFILE}[[:space:]]"; then
  if minikube profile list | grep -qE "^[[:space:]]*labfull[[:space:]]"; then
    echo "Requested profile '${MINIKUBE_PROFILE}' not found. Falling back to 'labfull'."
    MINIKUBE_PROFILE="labfull"
  fi
fi

if ! minikube status -p "${MINIKUBE_PROFILE}" >/dev/null 2>&1; then
  minikube start -p "${MINIKUBE_PROFILE}" --driver=docker
fi

minikube -p "${MINIKUBE_PROFILE}" addons enable ingress
minikube -p "${MINIKUBE_PROFILE}" addons enable dashboard
kubectl config use-context "${MINIKUBE_PROFILE}" >/dev/null

eval "$(minikube -p "${MINIKUBE_PROFILE}" docker-env)"

docker build -t labfull-backend:minikube ./backend-fastapi
docker build -t labfull-frontend:minikube ./app-web

kubectl apply -f ./k8s/secret.example.yaml
kubectl apply -f ./k8s/configmap.yaml
kubectl apply -f ./k8s/postgres-service.yaml
kubectl apply -f ./k8s/postgres-deployment.yaml
kubectl apply -f ./k8s/backend-service.yaml
kubectl apply -f ./k8s/backend-deployment.yaml
kubectl apply -f ./k8s/frontend-service.yaml
kubectl apply -f ./k8s/frontend-deployment.yaml
kubectl apply -f ./k8s/ingress.yaml
DASHBOARD_HOST="$(printf '%s' "${PUBLIC_DASHBOARD_URL}" | sed -E 's#^https?://##; s#/.*$##')"
DASHBOARD_HOST="${DASHBOARD_HOST}" bash ./scripts/apply_dashboard_ingress.sh

kubectl rollout restart deployment/backend-deployment
kubectl rollout restart deployment/frontend-deployment

kubectl rollout status deployment/postgres-deployment --timeout=300s
kubectl rollout status deployment/backend-deployment --timeout=300s
kubectl rollout status deployment/frontend-deployment --timeout=300s

echo "Deployment completed inside Minikube profile ${MINIKUBE_PROFILE}"
echo "Ingress host: ${PUBLIC_URL}"
kubectl get ingress labfull-ingress
kubectl get ingress -n kubernetes-dashboard ministack-dashboard-ingress

if [ "${APPLY_PUBLIC_PROXY}" = "1" ]; then
  DASHBOARD_HOST="${DASHBOARD_HOST}" MINIKUBE_PROFILE="${MINIKUBE_PROFILE}" bash ./scripts/configure_ministack_proxy.sh
fi

if command -v curl >/dev/null; then
  echo "Checking public dashboard route: ${PUBLIC_DASHBOARD_URL}"
  HTTP_STATUS="$(curl -k -sS -o /tmp/ministack-dashboard-check.html -w '%{http_code}' --connect-timeout 10 "${PUBLIC_DASHBOARD_URL}" || true)"
  if [ "${HTTP_STATUS}" = "404" ] && grep -qi 'DMZ proxy' /tmp/ministack-dashboard-check.html; then
    echo "Public proxy is not routing ${DASHBOARD_HOST} to Minikube ingress yet." >&2
    echo "Run with APPLY_PUBLIC_PROXY=1 or add ${DASHBOARD_HOST} to the DMZ Nginx proxy." >&2
    exit 1
  fi
  echo "Public dashboard HTTP status: ${HTTP_STATUS}"
fi
REMOTE_EOF

#!/usr/bin/env bash

set -euo pipefail

DASHBOARD_HOST="${DASHBOARD_HOST:-ministack.maurocastro.cl}"
DASHBOARD_NAMESPACE="${DASHBOARD_NAMESPACE:-kubernetes-dashboard}"
INGRESS_NAME="${DASHBOARD_INGRESS_NAME:-ministack-dashboard-ingress}"

kubectl get namespace "${DASHBOARD_NAMESPACE}" >/dev/null

if kubectl -n "${DASHBOARD_NAMESPACE}" get service kubernetes-dashboard-kong-proxy >/dev/null 2>&1; then
  DASHBOARD_SERVICE="kubernetes-dashboard-kong-proxy"
elif kubectl -n "${DASHBOARD_NAMESPACE}" get service kubernetes-dashboard >/dev/null 2>&1; then
  DASHBOARD_SERVICE="kubernetes-dashboard"
else
  echo "Dashboard service not found in namespace ${DASHBOARD_NAMESPACE}" >&2
  kubectl -n "${DASHBOARD_NAMESPACE}" get services >&2
  exit 1
fi

SERVICE_PORTS="$(kubectl -n "${DASHBOARD_NAMESPACE}" get service "${DASHBOARD_SERVICE}" -o jsonpath='{range .spec.ports[*]}{.port}{"\n"}{end}')"
if printf '%s\n' "${SERVICE_PORTS}" | grep -qx '443'; then
  DASHBOARD_PORT="443"
  BACKEND_PROTOCOL="HTTPS"
elif printf '%s\n' "${SERVICE_PORTS}" | grep -qx '80'; then
  DASHBOARD_PORT="80"
  BACKEND_PROTOCOL="HTTP"
else
  echo "Dashboard service ${DASHBOARD_SERVICE} has no 80/443 port" >&2
  kubectl -n "${DASHBOARD_NAMESPACE}" get service "${DASHBOARD_SERVICE}" -o wide >&2
  exit 1
fi

cat <<YAML | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${INGRESS_NAME}
  namespace: ${DASHBOARD_NAMESPACE}
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "${BACKEND_PROTOCOL}"
    nginx.ingress.kubernetes.io/proxy-ssl-verify: "off"
spec:
  ingressClassName: nginx
  rules:
    - host: ${DASHBOARD_HOST}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ${DASHBOARD_SERVICE}
                port:
                  number: ${DASHBOARD_PORT}
YAML

kubectl -n "${DASHBOARD_NAMESPACE}" get ingress "${INGRESS_NAME}" -o wide

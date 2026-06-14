#!/usr/bin/env bash

set -euo pipefail

DASHBOARD_HOST="${DASHBOARD_HOST:-ministack.maurocastro.cl}"
MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-labfull}"
DMZ_PROXY_DIR="${DMZ_PROXY_DIR:-/home/mauro/Dev/infra/maurocastro-dmz/proxy}"
DMZ_PROXY_CONTAINER="${DMZ_PROXY_CONTAINER:-maurocastro-dmz-proxy}"
DASHBOARD_FORWARD_PORT="${DASHBOARD_FORWARD_PORT:-8086}"

command -v minikube >/dev/null
command -v kubectl >/dev/null
command -v docker >/dev/null

kubectl config use-context "${MINIKUBE_PROFILE}" >/dev/null
kubectl get service -n kubernetes-dashboard kubernetes-dashboard >/dev/null

if ! ss -ltn | grep -q ":${DASHBOARD_FORWARD_PORT} "; then
  nohup kubectl --context "${MINIKUBE_PROFILE}" \
    --address 0.0.0.0 \
    -n kubernetes-dashboard \
    port-forward service/kubernetes-dashboard "${DASHBOARD_FORWARD_PORT}:80" \
    > /tmp/ministack-dashboard-port-forward.log 2>&1 &
  sleep 2
  if ! ss -ltn | grep -q ":${DASHBOARD_FORWARD_PORT} "; then
    cat /tmp/ministack-dashboard-port-forward.log >&2 || true
    echo "Dashboard port-forward failed on ${DASHBOARD_FORWARD_PORT}" >&2
    exit 1
  fi
fi

mkdir -p "${DMZ_PROXY_DIR}/conf.d"
cat > "${DMZ_PROXY_DIR}/conf.d/ministack.conf" <<NGINX
server {
    listen 8080;
    server_name ${DASHBOARD_HOST};

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name ${DASHBOARD_HOST};

    ssl_certificate     /etc/letsencrypt/live/maurocastro-dmz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/maurocastro-dmz/privkey.pem;
    include /etc/nginx/snippets/ssl-params.conf;

    location / {
        proxy_pass http://172.20.0.1:${DASHBOARD_FORWARD_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
NGINX

docker exec "${DMZ_PROXY_CONTAINER}" nginx -t
docker restart "${DMZ_PROXY_CONTAINER}" >/dev/null

echo "Public proxy route enabled: ${DASHBOARD_HOST} -> http://172.20.0.1:${DASHBOARD_FORWARD_PORT}"

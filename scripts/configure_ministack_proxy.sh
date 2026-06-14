#!/usr/bin/env bash

set -euo pipefail

DASHBOARD_HOST="${DASHBOARD_HOST:-ministack.maurocastro.cl}"
MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-labfull}"
NGINX_CONF_PATH="${NGINX_CONF_PATH:-/etc/nginx/conf.d/ministack-dashboard.conf}"
PROXY_SCHEME="${PROXY_SCHEME:-https}"

command -v minikube >/dev/null
command -v nginx >/dev/null
command -v sudo >/dev/null

MINIKUBE_IP="$(minikube -p "${MINIKUBE_PROFILE}" ip)"

if [ "${PROXY_SCHEME}" = "https" ]; then
  TLS_CERT_PATH="${TLS_CERT_PATH:-/etc/letsencrypt/live/${DASHBOARD_HOST}/fullchain.pem}"
  TLS_KEY_PATH="${TLS_KEY_PATH:-/etc/letsencrypt/live/${DASHBOARD_HOST}/privkey.pem}"
  if [ ! -r "${TLS_CERT_PATH}" ] || [ ! -r "${TLS_KEY_PATH}" ]; then
    echo "TLS certificate not found for ${DASHBOARD_HOST}" >&2
    echo "Set TLS_CERT_PATH/TLS_KEY_PATH or issue the certificate before enabling HTTPS proxy." >&2
    exit 1
  fi
  LISTEN_BLOCK='listen 443 ssl http2;'
  TLS_BLOCK='
    ssl_certificate '"${TLS_CERT_PATH}"';
    ssl_certificate_key '"${TLS_KEY_PATH}"';'
else
  LISTEN_BLOCK='listen 80;'
  TLS_BLOCK=''
fi

TMP_CONF="$(mktemp)"
cat > "${TMP_CONF}" <<NGINX
server {
    ${LISTEN_BLOCK}
    server_name ${DASHBOARD_HOST};
${TLS_BLOCK}

    location / {
        proxy_pass http://${MINIKUBE_IP};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
NGINX

sudo install -m 0644 "${TMP_CONF}" "${NGINX_CONF_PATH}"
rm -f "${TMP_CONF}"

sudo nginx -t
sudo systemctl reload nginx

echo "Public proxy route enabled: ${DASHBOARD_HOST} -> http://${MINIKUBE_IP}"

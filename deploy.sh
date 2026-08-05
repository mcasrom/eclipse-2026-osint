#!/usr/bin/env bash
# Despliegue de Eclipse 2026 OSINT (flujo server-directo: editar aquí -> commit -> push)
set -euo pipefail
cd "$(dirname "$0")"

echo "== PM2 restart eclipse-api =="
pm2 restart eclipse-api --update-env >/dev/null 2>&1 || \
  pm2 start ./venv/bin/python --name eclipse-api -- -m uvicorn server:app --host 127.0.0.1 --port 8700
pm2 save >/dev/null 2>&1

echo "== Nginx reload =="
sudo nginx -t >/dev/null && sudo nginx -s reload

echo "== Salud =="
sleep 2
curl -s http://127.0.0.1:8700/health
echo
echo "Desplegado. El contenido estático lo sirve nginx directamente."

#!/usr/bin/env bash
# One-shot installer for Ubuntu 24.04 EC2. Run as: sudo bash setup.sh
# Optional: export DASHBOARD_PASSWORD / OPENAI_API_KEY before running.
set -euo pipefail
REPO=https://github.com/hemant20255-cloud/world-affairs-intelligence-agent.git
BRANCH=${BRANCH:-main}
APP=/opt/intel

apt-get update -y
apt-get install -y python3-venv python3-pip git nginx

if [ -d "$APP/.git" ]; then git -C "$APP" pull; else git clone -b "$BRANCH" "$REPO" "$APP"; fi
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install -q --upgrade pip
"$APP/venv/bin/pip" install -q -r "$APP/dashboard/requirements.txt"

# secrets file (root-only)
cat > /etc/intel-dashboard.env <<ENV
DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
ENV
chmod 600 /etc/intel-dashboard.env

cp "$APP/dashboard/deploy/intel-dashboard.service" /etc/systemd/system/
cp "$APP/dashboard/deploy/nginx.conf" /etc/nginx/sites-available/intel
ln -sf /etc/nginx/sites-available/intel /etc/nginx/sites-enabled/intel
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable --now intel-dashboard
systemctl restart nginx
echo "Done. Open http://<EC2-public-IP>/"

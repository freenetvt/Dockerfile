#!/usr/bin/env bash
set -euo pipefail

UUIDS_URL="${UUIDS_URL:-https://raw.githubusercontent.com/freenetvt/Dockerfile/main/proxy_gen/uuids.txt}"
TMP_UUIDS="/tmp/uuids.txt"
XRAY_CFG="/usr/local/etc/xray/config.json"

mkdir -p "$(dirname "$XRAY_CFG")"

echo "Fetching UUIDs from: $UUIDS_URL"
if curl -fsSL "$UUIDS_URL" -o "$TMP_UUIDS"; then
    echo "Downloaded uuids.txt successfully."
else
    echo "Warning: Could not download uuids.txt, falling back to local or default UUID."
    if [ -f "/app/proxy_gen/uuids.txt" ]; then
        cp "/app/proxy_gen/uuids.txt" "$TMP_UUIDS"
    fi
fi

python3 - "$TMP_UUIDS" "$XRAY_CFG" << 'EOF'
import json
import sys
from pathlib import Path

uuid_path = Path(sys.argv[1])
out_cfg_path = Path(sys.argv[2])

uuids = []
if uuid_path.exists():
    for line in uuid_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            uuids.append(s)

if not uuids:
    uuids = ["0cb18223-88b2-4e9f-a223-9cb4d9fe3a9a"]

vless_clients = [
    {"id": u, "email": f"vless_{i+1}@railway", "level": 0}
    for i, u in enumerate(uuids)
]
vmess_clients = [
    {"id": u, "alterId": 0, "email": f"vmess_{i+1}@railway", "level": 0}
    for i, u in enumerate(uuids)
]
trojan_clients = [
    {"password": u, "email": f"trojan_{i+1}@railway", "level": 0}
    for i, u in enumerate(uuids)
]

xray_config = {
    "log": {"loglevel": "warning"},
    "inbounds": [
        {
            "tag": "vless-in",
            "listen": "127.0.0.1",
            "port": 10001,
            "protocol": "vless",
            "settings": {
                "clients": vless_clients,
                "decryption": "none"
            },
            "streamSettings": {
                "network": "ws",
                "wsSettings": {"path": "/vless-ws"}
            }
        },
        {
            "tag": "vmess-in",
            "listen": "127.0.0.1",
            "port": 10002,
            "protocol": "vmess",
            "settings": {
                "clients": vmess_clients
            },
            "streamSettings": {
                "network": "ws",
                "wsSettings": {"path": "/vmess-ws"}
            }
        },
        {
            "tag": "trojan-in",
            "listen": "127.0.0.1",
            "port": 10003,
            "protocol": "trojan",
            "settings": {
                "clients": trojan_clients
            },
            "streamSettings": {
                "network": "ws",
                "wsSettings": {"path": "/trojan-ws"}
            }
        }
    ],
    "outbounds": [
        {"protocol": "freedom", "tag": "direct"},
        {"protocol": "blackhole", "tag": "block"}
    ]
}

out_cfg_path.write_text(json.dumps(xray_config, indent=2), encoding="utf-8")
print(f"Wrote {len(uuids)} UUIDs to {out_cfg_path}")
EOF

nginx -g "daemon off;" &
NGINX_PID=$!

xray run -c "$XRAY_CFG" &
XRAY_PID=$!

trap "kill $NGINX_PID $XRAY_PID 2>/dev/null || true; wait" EXIT TERM INT
wait -n $NGINX_PID $XRAY_PID

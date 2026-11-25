import os
from urllib.parse import quote

UUID = os.getenv("VLESS_UUID", "e72e8b72-2362-4f86-ad48-ddac27b2bcba").strip()
DOMAIN = os.getenv("RAILWAY_DOMAIN", "your-app.up.railway.app").strip()
PORT = os.getenv("VLESS_PORT", "443").strip()
PATH = os.getenv("WS_PATH", "/vless-ws").strip()
REMARK = os.getenv("CONFIG_REMARK", "Railway-VLESS").strip()

if not PATH.startswith("/"):
    PATH = "/" + PATH

encoded_path = quote(PATH, safe="")
encoded_remark = quote(REMARK, safe="")

vless_link = (
    f"vless://{UUID}@{DOMAIN}:{PORT}"
    f"?encryption=none&security=tls&sni={DOMAIN}&fp=chrome"
    f"&type=ws&host={DOMAIN}&path={encoded_path}#{encoded_remark}"
)

with open("vless_config.txt", "w", encoding="utf-8") as f:
    f.write(vless_link + "\n")

print("Saved vless_config.txt successfully.")

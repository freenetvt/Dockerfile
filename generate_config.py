import base64
import os
import uuid
from urllib.parse import quote

DOMAIN = os.getenv("RAILWAY_DOMAIN", "your-app.up.railway.app").strip()
PORT = os.getenv("VLESS_PORT", "443").strip()
PATH = os.getenv("WS_PATH", "/vless-ws").strip()
REMARK_PREFIX = os.getenv("CONFIG_REMARK_PREFIX", "Railway-VLESS").strip()

# می‌توانید UUIDهای دلخواه را با کاما در VLESS_UUIDS بدهید یا تعداد را در CONFIG_COUNT مشخص کنید
RAW_UUIDS = os.getenv("VLESS_UUIDS", "e72e8b72-2362-4f86-ad48-ddac27b2bcba").strip()
CONFIG_COUNT = int(os.getenv("CONFIG_COUNT", "1"))

if not PATH.startswith("/"):
    PATH = "/" + PATH

encoded_path = quote(PATH, safe="")

uuids = [u.strip() for u in RAW_UUIDS.split(",") if u.strip()]
while len(uuids) < CONFIG_COUNT:
    uuids.append(str(uuid.uuid4()))

links = []
for idx, uid in enumerate(uuids, start=1):
    remark = f"{REMARK_PREFIX}-{idx}"
    encoded_remark = quote(remark, safe="")
    link = (
        f"vless://{uid}@{DOMAIN}:{PORT}"
        f"?encryption=none&security=tls&sni={DOMAIN}&fp=chrome"
        f"&type=ws&host={DOMAIN}&path={encoded_path}#{encoded_remark}"
    )
    links.append(link)

plain_text = "\n".join(links) + "\n"
base64_text = base64.b64encode(plain_text.strip().encode("utf-8")).decode("utf-8") + "\n"

with open("vless_configs.txt", "w", encoding="utf-8") as f_txt:
    f_txt.write(plain_text)

with open("vless_base64.txt", "w", encoding="utf-8") as f_b64:
    f_b64.write(base64_text)

print(f"Generated {len(links)} VLESS configs -> vless_configs.txt & vless_base64.txt")

import base64
import json
import os
from urllib.parse import quote

DOMAIN = os.getenv("RAILWAY_DOMAIN", "your-app.up.railway.app").strip()
PORT = int(os.getenv("PROXY_PORT", "443").strip())
PATH = os.getenv("WS_PATH", "/vless-ws").strip()
REMARK_PREFIX = os.getenv("CONFIG_REMARK_PREFIX", "Railway").strip()
PROTOCOLS = [
    p.strip().lower()
    for p in os.getenv("PROTOCOLS", "vless,vmess,trojan").split(",")
    if p.strip()
]

DEFAULT_UUIDS = [
    "0cb18223-88b2-4e9f-a223-9cb4d9fe3a9a",
    "73fd1322-87a8-4676-b423-50cfac840f47",
    "891f805e-0108-42eb-a238-3a57f457f137",
    "affdf229-cad3-4463-93aa-de63dac52944",
    "acfb031e-f33b-4010-a515-27608a864b42",
    "d84e818a-75bd-4987-aa41-06686c9ddf55",
    "a91956be-9e4f-4d1f-9036-2c5eebffd668",
]

RAW_UUIDS = os.getenv("PROXY_UUIDS", "").strip()
uuids = (
    [u.strip() for u in RAW_UUIDS.split(",") if u.strip()]
    if RAW_UUIDS
    else DEFAULT_UUIDS
)

if not PATH.startswith("/"):
    PATH = "/" + PATH

encoded_path = quote(PATH, safe="")


def build_link(proto: str, uid: str, remark: str) -> str:
    encoded_remark = quote(remark, safe="")
    if proto == "vless":
        return (
            f"vless://{uid}@{DOMAIN}:{PORT}"
            f"?encryption=none&security=tls&sni={DOMAIN}&fp=chrome"
            f"&type=ws&host={DOMAIN}&path={encoded_path}#{encoded_remark}"
        )
    if proto == "vmess":
        vmess_payload = {
            "v": "2",
            "ps": remark,
            "add": DOMAIN,
            "port": str(PORT),
            "id": uid,
            "aid": "0",
            "scy": "auto",
            "net": "ws",
            "type": "none",
            "host": DOMAIN,
            "path": PATH,
            "tls": "tls",
            "sni": DOMAIN,
            "fp": "chrome",
        }
        encoded_json = base64.b64encode(
            json.dumps(vmess_payload, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")
        return f"vmess://{encoded_json}"
    if proto == "trojan":
        return (
            f"trojan://{uid}@{DOMAIN}:{PORT}"
            f"?security=tls&sni={DOMAIN}&fp=chrome"
            f"&type=ws&host={DOMAIN}&path={encoded_path}#{encoded_remark}"
        )
    raise ValueError(f"Unsupported protocol: {proto}")


links = []
for idx, uid in enumerate(uuids, start=1):
    proto = PROTOCOLS[(idx - 1) % len(PROTOCOLS)]
    remark = f"{REMARK_PREFIX}-{proto.upper()}-{idx}"
    links.append(build_link(proto, uid, remark))

plain_text = "\n".join(links) + "\n"
base64_text = (
    base64.b64encode(plain_text.strip().encode("utf-8")).decode("utf-8") + "\n"
)

with open("configs.txt", "w", encoding="utf-8") as f_txt:
    f_txt.write(plain_text)

with open("sub_base64.txt", "w", encoding="utf-8") as f_b64:
    f_b64.write(base64_text)

print(
    f"Generated {len(links)} multi-protocol configs -> configs.txt & sub_base64.txt"
)

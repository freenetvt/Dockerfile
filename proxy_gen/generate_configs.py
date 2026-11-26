import base64
import json
import os
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_DOMAINS = ["dockerfile-production-b82427c4.up.railway.app"]
DEFAULT_UUIDS = [
    "0cb18223-88b2-4e9f-a223-9cb4d9fe3a9a",
    "73fd1322-87a8-4676-b423-50cfac840f47",
    "891f805e-0108-42eb-a238-3a57f457f137",
    "affdf229-cad3-4463-93aa-de63dac52944",
    "acfb031e-f33b-4010-a515-27608a864b42",
    "d84e818a-75bd-4987-aa41-06686c9ddf55",
    "a91956be-9e4f-4d1f-9036-2c5eebffd668",
]


def load_kv_config(filename: str = "config.txt") -> dict[str, str]:
    settings: dict[str, str] = {}
    p = BASE_DIR / filename
    if not p.exists():
        return settings

    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        settings[key.strip().upper()] = value.strip()
    return settings


def get_setting(cfg: dict[str, str], key: str, default: str = "") -> str:
    upper_key = key.upper()
    if upper_key in cfg and cfg[upper_key] != "":
        return cfg[upper_key]
    env_val = os.getenv(upper_key, "").strip()
    if env_val != "":
        return env_val
    return default


def load_lines(
    filename: str, cfg: dict[str, str], cfg_key: str, fallback: list[str]
) -> list[str]:
    p = BASE_DIR / filename
    if p.exists():
        lines = [
            line.strip()
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if lines:
            return lines

    raw_val = get_setting(cfg, cfg_key, "")
    if raw_val:
        items = [x.strip() for x in raw_val.split(",") if x.strip()]
        if items:
            return items

    return fallback


cfg = load_kv_config("config.txt")

port = int(get_setting(cfg, "PORT", "443"))
path = get_setting(cfg, "PATH", "/vless-ws")
if not path.startswith("/"):
    path = "/" + path

remark_prefix = get_setting(cfg, "REMARK_PREFIX", "Railway")
security = get_setting(cfg, "SECURITY", "tls")
fp = get_setting(cfg, "FP", "chrome")
forced_address = get_setting(cfg, "ADDRESS", "")
forced_host = get_setting(cfg, "HOST", "")
forced_sni = get_setting(cfg, "SNI", "")

protocols_raw = get_setting(cfg, "PROTOCOLS", "vless,vmess,trojan")
protocols = [p.strip().lower() for p in protocols_raw.split(",") if p.strip()] or ["vless"]

domains = load_lines("domains.txt", cfg, "DOMAINS", DEFAULT_DOMAINS)
uuids = load_lines("uuids.txt", cfg, "UUIDS", DEFAULT_UUIDS)

encoded_path = quote(path, safe="")


def build_link(
    proto: str, target: str, host: str, sni: str, uid: str, remark: str
) -> str:
    encoded_remark = quote(remark, safe="")
    sec_param = f"&security={security}" if security else ""
    sni_param = f"&sni={sni}" if sni else ""
    fp_param = f"&fp={fp}" if fp else ""
    host_param = f"&host={host}" if host else ""

    if proto == "vless":
        return (
            f"vless://{uid}@{target}:{port}"
            f"?encryption=none{sec_param}{sni_param}{fp_param}"
            f"&type=ws{host_param}&path={encoded_path}#{encoded_remark}"
        )
    if proto == "vmess":
        vmess_payload = {
            "v": "2",
            "ps": remark,
            "add": target,
            "port": str(port),
            "id": uid,
            "aid": "0",
            "scy": "auto",
            "net": "ws",
            "type": "none",
            "host": host,
            "path": path,
            "tls": security if security in ("tls", "none") else "tls",
            "sni": sni,
            "fp": fp,
        }
        encoded_json = base64.b64encode(
            json.dumps(vmess_payload, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")
        return f"vmess://{encoded_json}"
    if proto == "trojan":
        return (
            f"trojan://{uid}@{target}:{port}"
            f"?{sec_param.lstrip('&')}{sni_param}{fp_param}"
            f"&type=ws{host_param}&path={encoded_path}#{encoded_remark}"
        )
    raise ValueError(f"Unsupported protocol: {proto}")


links: list[str] = []
vless_links: list[str] = []
counter = 1
vless_counter = 1

for domain in domains:
    target = forced_address if forced_address else domain
    host = forced_host if forced_host else domain
    sni = forced_sni if forced_sni else domain
    for uid in uuids:
        proto = protocols[(counter - 1) % len(protocols)]
        remark = f"{remark_prefix}-{proto.upper()}-{counter}"
        links.append(build_link(proto, target, host, sni, uid, remark))
        counter += 1

        if "vless" in protocols:
            vless_remark = f"{remark_prefix}-VLESS-{vless_counter}"
            vless_links.append(
                build_link("vless", target, host, sni, uid, vless_remark)
            )
            vless_counter += 1

plain_text = "\n".join(links) + ("\n" if links else "")
base64_text = (
    base64.b64encode(plain_text.strip().encode("utf-8")).decode("utf-8") + "\n"
    if links
    else ""
)
vless_text = "\n".join(vless_links) + ("\n" if vless_links else "")

(BASE_DIR / "configs.txt").write_text(plain_text, encoding="utf-8")
(BASE_DIR / "sub_base64.txt").write_text(base64_text, encoding="utf-8")
(BASE_DIR / "vless.txt").write_text(vless_text, encoding="utf-8")

print(
    f"Saved to {BASE_DIR} | Generated {len(links)} configs | vless={len(vless_links)} | domains={len(domains)} | uuids={len(uuids)}"
)

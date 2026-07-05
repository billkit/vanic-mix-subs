#!/usr/bin/env python3
"""
build_common_sub.py — 生成 Shadowrocket / Daed / Loon 等通用订阅
核心：把 mihomo 私有字段 stripping 成标准 Clash 字段，去掉 reality-opts/pbk/sid/ech 等
"""
from __future__ import annotations
import yaml, urllib.request, datetime, pathlib, sys

REPO = "https://raw.githubusercontent.com/Vanic24/VPN/main"
FILES = ["8EB", "9PB", "Lifetime", "Sub3", "Filter"]
NA = "https://www.gstatic.com/generate_204"
OUT = pathlib.Path(__file__).parent / "vanic_common_sub.yaml"

# 这些是 mihomo/Clash Meta 私有扩展，通用订阅必须去掉
META_ONLY_FIELDS = {
    "reality-opts", "pbk", "sid", "ech", "cipher", "country", "delay",
    "allowInsecure", "tls-enabled", "client-fingerprint", "servername",
    "grpc-opts", "h2-opts", "http-opts", "smux", "shadow-tls-opts",
    "ss-plugin", "ss-plugin-opts", "plugin-opts",  # 某些客户端不认 plugin-opts
}
# 需要改名的字段（通用订阅统一用 skip-cert-verify）
RENAME_FIELDS = {
    "insecure": "skip-cert-verify",
    "tls-enabled": "tls",
}

def fetch(name):
    url = f"{REPO}/{name}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return yaml.safe_load(r.read().decode("utf-8"))

def clean_proxy(p):
    """去掉私有字段，改名通用字段"""
    out = {}
    for k, v in p.items():
        if k in META_ONLY_FIELDS:
            continue
        if k in RENAME_FIELDS:
            k = RENAME_FIELDS[k]
        # 字符串布尔值归一
        if isinstance(v, str) and v in ("0", "1", "true", "false"):
            v = v in ("1", "true")
        out[k] = v
    return out

def main():
    raw = {}
    for f in FILES:
        print(f"[fetch] {f}")
        cfg = fetch(f)
        raw[f] = [clean_proxy(p) for p in cfg["proxies"]]

    # 去重
    seen, deduped = set(), []
    n_before = 0
    for f in FILES:
        n_before += len(raw[f])
        for p in raw[f]:
            key = (p.get("server"), p.get("port"), p.get("type"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(p)
    print(f"[dedup] {n_before} -> {len(deduped)}")

    # 分组（保持简洁，避免过多组）
    groups = [
        {"name": "🌍 全线路", "type": "select",
         "proxies": ["⚡️ 自动测速"] + [f"📦 {f}" for f in FILES]},
        {"name": "⚡️ 自动测速", "type": "url-test",
         "proxies": [p["name"] for p in deduped],
         "url": NA, "interval": 300, "tolerance": 50},
    ]
    for f in FILES:
        names = [p["name"] for p in deduped if p["name"].endswith(f" | {f}")]
        if names:
            groups.append({"name": f"📦 {f}", "type": "url-test",
                           "proxies": names, "url": NA, "interval": 300, "tolerance": 50})

    out = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "warning",
        "ipv6": True,
        "proxies": deduped,
        "proxy-groups": groups,
        "rules": [
            "DOMAIN-SUFFIX,google.com,🌍 全线路",
            "DOMAIN-SUFFIX,youtube.com,🌍 全线路",
            "DOMAIN-SUFFIX,github.com,🌍 全线路",
            "GEOIP,CN,DIRECT",
            "MATCH,🌍 全线路",
        ],
    }

    header = (
        f"# Vanic24/VPN 通用订阅 · {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"# 节点: {len(deduped)}  策略组: {len(groups)}\n"
    )
    content = header + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False)
    OUT.write_text(content, encoding="utf-8")
    print(f"[write] {OUT} ({len(content)} bytes)")

    # 打印类型分布
    types = {}
    for p in deduped:
        types[p.get("type", "?")] = types.get(p["type"], 0) + 1
    print("types:", types)

if __name__ == "__main__":
    main()

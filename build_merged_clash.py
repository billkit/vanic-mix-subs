#!/usr/bin/env python3
"""
build_merged_clash.py — 合并 Vanic24/VPN 的 6 个 Clash 文件为单一订阅
输出: vanic_merged.yaml (Clash Meta / Daed 可直接导入)
"""
from __future__ import annotations
import yaml, urllib.request, datetime, pathlib

REPO = "https://raw.githubusercontent.com/Vanic24/VPN/main"
FILES = ["8EB", "9PB", "Lifetime", "Sub3", "Filter", "MIX"]
OUT = pathlib.Path(__file__).parent / "vanic_merged.yaml"

RENAME = {"insecure": "skip-cert-verify", "tls-enabled": "tls"}

def fetch(name):
    with urllib.request.urlopen(f"{REPO}/{name}", timeout=30) as r:
        return yaml.safe_load(r.read().decode())

def normalize(p):
    out = dict(p)
    # Clash Meta 用 socks5 而不是 socks
    if out.get("type") == "socks":
        out["type"] = "socks5"
    for old, new in RENAME.items():
        if old in out:
            out[new] = out.pop(old)
    for k in ("skip-cert-verify", "tls", "udp"):
        if k in out and isinstance(out[k], str) and out[k] in ("0", "1", "true", "false"):
            out[k] = out[k] in ("1", "true")
    return out

def main():
    raw = {}
    for f in FILES:
        print(f"[fetch] {f}")
        cfg = fetch(f)
        raw[f] = [normalize(p) for p in cfg["proxies"]]

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
    print(f"[dedup] {n_before} -> {len(deduped)} ({n_before - len(deduped)} suppressed)")

    rules = fetch(FILES[0])["rules"]

    groups = [
        {"name": "🌍 全线路选择", "type": "select",
         "proxies": ["⚡️ 全自动测速"] + [f"📦 {f}" for f in FILES]},
        {"name": "⚡️ 全自动测速", "type": "url-test",
         "proxies": [p["name"] for p in deduped],
         "url": "https://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50},
    ]
    for f in FILES:
        names = [p["name"] for p in deduped if p["name"].endswith(f" | {f}")]
        if names:
            groups.append({"name": f"📦 {f}", "type": "url-test",
                           "proxies": names, "url": "https://www.gstatic.com/generate_204",
                           "interval": 300, "tolerance": 50})

    out = {
        "port": 7890, "socks-port": 7891, "allow-lan": False,
        "mode": "rule", "log-level": "warning", "ipv6": True,
        "external-controller": "127.0.0.1:9090",
        "proxies": deduped, "proxy-groups": groups, "rules": rules,
    }

    header = (
        f"# 合并 Vanic24/VPN 订阅（含 MIX）\n"
        f"# 源: {', '.join(FILES)}\n"
        f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"# 节点: {len(deduped)} (去重前 {n_before})  策略组: {len(groups)}\n"
    )
    content = header + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False)
    OUT.write_text(content, encoding="utf-8")
    print(f"[write] {OUT} ({len(content)} bytes)")

    types = {}
    for p in deduped:
        types[p.get("type", "?")] = types.get(p["type"], 0) + 1
    print("types:", types)

if __name__ == "__main__":
    main()
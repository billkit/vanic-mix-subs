#!/usr/bin/env python3
"""
build_merged.py — 合并 Vanic24/VPN 仓库的 6 个 Clash 文件为单一订阅
源:  MIX / 8EB / 9PB / Lifetime / Sub3 / Filter
输出: vanic_merged.yaml (Daed 可直接吃的 Clash Meta 配置)

规则:
- 跳过 MIX (socks5 only, mihomo 不支持入站 socks5)
- 按 (server, port, type) 去重, 保留首条
- 节点按来源文件分组成独立 url-test
- 顶层分组: 选择线路 (select, 所有源文件子组入口)
- rules 复用任一文件即可 (6 个文件 rules 数量一致)
"""
from __future__ import annotations
import yaml, urllib.request, datetime, pathlib

REPO = "https://raw.githubusercontent.com/Vanic24/VPN/main"
FILES = ["8EB", "9PB", "Lifetime", "Sub3", "Filter"]   # MIX 被显式排除
NA = "https://www.gstatic.com/generate_204"
OUT = pathlib.Path(__file__).parent / "vanic_merged.yaml"


def fetch_yaml(name):
    url = f"{REPO}/{name}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return yaml.safe_load(r.read().decode("utf-8"))


def normalize_proxy(p):
    """剥离 mihomo 老版本不喜欢的字段 (cipher/country/allowInsecure/delay 等),
    避免新版解析卡壳. 同时把 insecure 的 '0'/'1' 字符串归一为 bool."""
    drop = {"cipher", "country", "delay", "allowInsecure"}
    out = {k: v for k, v in p.items() if k not in drop}
    for k in ("insecure", "skip-cert-verify", "tls-enabled"):
        if k in out and isinstance(out[k], str) and out[k] in {"0", "1"}:
            out[k] = (out[k] == "1")
    return out


def main():
    raw = {}
    for f in FILES:
        print(f"[fetch] {f}")
        cfg = fetch_yaml(f)
        # 归一化 + 改名加后缀 (避免命名冲突: 原文件已带 '| 8EB' 之类后缀的就不用改)
        cleaned = []
        for p in cfg["proxies"]:
            np = normalize_proxy(p)
            tag = f" | {f}" if f" | {f}" not in np["name"] else ""
            np["name"] = np["name"] + tag
            cleaned.append(np)
        raw[f] = {"proxies": cleaned}

    # 去重, 保留首条 (server/port/type 三元组)
    seen, deduped = set(), []
    n_before = 0
    for f in FILES:
        n_before += len(raw[f]["proxies"])
        for p in raw[f]["proxies"]:
            key = (p.get("server"), p.get("port"), p.get("type"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(p)

    print(f"[dedup] {n_before} -> {len(deduped)} proxies ({n_before - len(deduped)} duplicate suppressed)")

    # 也用 rules (任一文件即可, 内容完全一致)
    rules_cfg = fetch_yaml(FILES[0])
    rules = rules_cfg["rules"]

    # proxy-groups: 每个文件一个 url-test, 顶层 select 包了所有子组 + 入口"自动选择"
    groups = []

    # 给个总开关 (手动选择)
    groups.append({
        "name": "🌍 全线路选择",
        "type": "select",
        "proxies": ["⚡️ 全自动测速"] + [
            f"📦 {f}" for f in FILES
        ],
    })

    # 全自动测速 (跨所有文件)
    groups.append({
        "name": "⚡️ 全自动测速",
        "type": "url-test",
        "proxies": [p["name"] for p in deduped],
        "url": NA,
        "interval": 300,
        "tolerance": 50,
    })

    # 按文件分组
    for f in FILES:
        names = [p["name"] for p in raw[f]["proxies"] if (p.get("server"), p.get("port"), p.get("type")) in seen]
        # 计算去重后属于本文件的节点
        # 上面有顺序问题, 重做: 用 deduped 的子集
        names = [p["name"] for p in deduped if p["name"].endswith(f" | {f}")]
        if not names:
            continue
        groups.append({
            "name": f"📦 {f}",
            "type": "url-test",
            "proxies": names,
            "url": NA,
            "interval": 300,
            "tolerance": 50,
        })

    # 顶部运行时
    header = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "warning",
        "ipv6": True,
        "external-controller": "127.0.0.1:9090",
    }

    out = {}
    out.update(header)
    out["proxies"] = deduped
    out["proxy-groups"] = groups

    # 更新 rules 中的旧策略名 "选择线路" -> "🌍 全线路选择"
    # 注意规则可能 2 段 ("DOMAIN,x,选择线路") 或 3 段 ("IP-CIDR,x,y,no-resolve") 或 4 段
    new_rules = []
    old = "选择线路"
    new = "🌍 全线路选择"
    for r in rules:
        if not isinstance(r, str):
            new_rules.append(r)
            continue
        # 通用: 把 "选择线路" 子串(verbatim, 不带逗号的情况) 替换为新名
        # IP-CIDR 等最后一列就是策略名
        parts = r.split(",")
        if parts[-1].strip() == old:
            parts[-1] = new
            new_rules.append(",".join(parts))
        elif old in r and r.endswith(old):
            # 兜底: 4 段规则的 IP-CIDR,no-resolve 这种, 选择线路 在倒数第二段
            new_rules.append(r[:-len(old)] + new)
        else:
            new_rules.append(r)
    out["rules"] = new_rules

    # 头部注释
    comment = (
        f"# 合并 Vanic24/VPN 订阅\n"
        f"# 源: {', '.join(FILES)} (MIX socks5 因 mihomo 不支持入站 socks5 已排除)\n"
        f"# 生成时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"# 节点: {len(deduped)} (去重前 {n_before})  策略组: {len(groups)}\n"
    )
    OUT.write_text(comment + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False),
                   encoding="utf-8")
    print(f"[write] {OUT}  ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

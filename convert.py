#!/usr/bin/env python3
"""
convert.py — 把 Vanic24/VPN 的 MIX YAML 转成 Daed/Clash Meta 可用的通用订阅 YAML

输入:  https://raw.githubusercontent.com/Vanic24/VPN/refs/heads/main/MIX
输出:  ./vanic_mix_clash_subscription.yaml

保留项:
- proxies (socks5 节点)
- proxy-groups (策略组: 选择线路 + 自动选择)
- rules (原始全部规则)
剥除项 (本地运行时配置, 订阅里不该有):
- mixed-port, tun, dns, external-controller, profile, allow-lan
"""
from __future__ import annotations
import pathlib, re, sys, datetime, urllib.request, os

SRC_URL = os.environ.get("SRC_URL") or "https://raw.githubusercontent.com/Vanic24/VPN/refs/heads/main/MIX"
OUT_PATH = pathlib.Path(__file__).parent / "vanic_mix_clash_subscription.yaml"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "vanic-mix-converter/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def strip_custom_fields(line: str) -> str:
    """移除 YAML 节点上不兼容的 _auth/_security/_sni/_network/_path 字段"""
    return re.sub(r'(password: "[^"]*", username: "[^"]*"), _[^,}]+', r'\1', line)


HEADER_TEMPLATE = """# Clash 订阅 - 自动转换自 Vanic24/VPN @ MIX
# 源: {src}
# 转换时间: {ts}
# 节点类型: socks5 (60)
# 兼容客户端: Daed / Clash Verge / mihomo / Stash / Clash Meta for Android
# 注意: 节点密码多为公开弱口令, 仅供测试用
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: warning
ipv6: true
"""


def convert(src: str) -> str:
    lines = src.splitlines()

    def find_idx(prefix: str) -> int:
        for i, l in enumerate(lines):
            if l.startswith(prefix):
                return i
        return -1

    p, g, r = find_idx("proxies:"), find_idx("proxy-groups:"), find_idx("rules:")
    if -1 in (p, g, r):
        raise ValueError("源文件缺少 proxies / proxy-groups / rules 段")

    proxies_block = "\n".join(strip_custom_fields(l) for l in lines[p:g]).rstrip() + "\n"
    groups_block = "\n".join(lines[g:r]).rstrip() + "\n"
    rules_block = "\n".join(lines[r:]).rstrip() + "\n"

    header = HEADER_TEMPLATE.format(
        src=SRC_URL,
        ts=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
    return header + "\n" + proxies_block + "\n" + groups_block + "\n" + rules_block


def main() -> int:
    print(f"[fetch] {SRC_URL}")
    src = fetch(SRC_URL)
    out = convert(src)
    OUT_PATH.write_text(out, encoding="utf-8")
    print(f"[write] {OUT_PATH}  ({len(out)} bytes, {len(out.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

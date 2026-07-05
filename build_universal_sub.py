#!/usr/bin/env python3
"""
build_universal_sub.py — 生成 Shadowrocket / Dae / Loon / QuantumultX 通用订阅
输出: vanic_universal.txt (base64) + vanic_universal.yaml (可读)
原理: 把 Clash 节点转成标准 URI 格式，再 base64 编码
"""
from __future__ import annotations
import json, yaml, urllib.request, datetime, pathlib, sys, base64, urllib.parse

REPO = "https://raw.githubusercontent.com/Vanic24/VPN/main"
FILES = ["8EB", "9PB", "Lifetime", "Sub3", "Filter"]
OUT_DIR = pathlib.Path(__file__).parent

META_ONLY = {"cipher", "country", "delay", "allowInsecure", "client-fingerprint",
             "servername", "reality-opts", "ech", "tls-enabled", "grpc-opts",
             "h2-opts", "http-opts", "smux", "shadow-tls-opts",
             "ss-plugin", "ss-plugin-opts", "plugin-opts", "_auth", "_security", "_sni", "_network", "_path"}

def fetch(name):
    with urllib.request.urlopen(f"{REPO}/{name}", timeout=30) as r:
        return yaml.safe_load(r.read().decode())

def clean(p):
    out = {}
    for k, v in p.items():
        if k in META_ONLY:
            continue
        if k == "insecure":
            k = "skip-cert-verify"
        if isinstance(v, str) and v in ("0", "1", "true", "false"):
            v = v in ("1", "true")
        out[k] = v
    return out

# ── URI 生成器 ──────────────────────────────────────────

def to_vless_uri(p):
    """VLESS → vless://uuid@host:port?..."""
    q = {"encryption": "none", "type": p.get("network", "tcp")}
    if p.get("tls") is True or p.get("security") in ("tls", "reality"):
        q["security"] = p.get("security", "tls")
    if p.get("sni"):
        q["sni"] = p["sni"]
    if p.get("fp"):
        q["fp"] = p["fp"]
    if p.get("flow"):
        q["flow"] = p["flow"]
    # reality 额外参数
    if p.get("security") == "reality":
        if p.get("pbk"):
            q["pbk"] = p["pbk"]
        if p.get("sid"):
            q["sid"] = p["sid"]
    # ws-opts
    ws = p.get("ws-opts", {})
    if isinstance(ws, dict):
        if ws.get("path"):
            q["path"] = ws["path"]
        h = ws.get("headers", {})
        if isinstance(h, dict) and h.get("Host"):
            q["host"] = h["Host"]
    # grpc-opts
    grpc = p.get("grpc-opts", {})
    if isinstance(grpc, dict):
        if grpc.get("grpc-service-name"):
            q["serviceName"] = grpc["grpc-service-name"]

    # skip-cert-verify
    if p.get("skip-cert-verify") is True:
        q["allowInsecure"] = "1"
    elif p.get("skip-cert-verify") is False:
        q["allowInsecure"] = "0"

    query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in q.items())
    return f"vless://{p['uuid']}@{p['server']}:{p['port']}?{query}#{urllib.parse.quote(p['name'])}"


def to_trojan_uri(p):
    q = {}
    if p.get("sni"):
        q["sni"] = p["sni"]
    if p.get("skip-cert-verify") is True:
        q["allowInsecure"] = "1"
    elif p.get("skip-cert-verify") is False:
        q["allowInsecure"] = "0"
    if p.get("udp") is True:
        q["udp"] = "true"
    if p.get("type") == "ws":
        q["type"] = "ws"
        ws = p.get("ws-opts", {})
        if isinstance(ws, dict):
            if ws.get("path"):
                q["path"] = ws["path"]
            h = ws.get("headers", {})
            if isinstance(h, dict) and h.get("Host"):
                q["host"] = h["Host"]
    if p.get("type") == "grpc":
        q["type"] = "grpc"
        grpc = p.get("grpc-opts", {})
        if isinstance(grpc, dict) and grpc.get("grpc-service-name"):
            q["serviceName"] = grpc["grpc-service-name"]
    query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in q.items())
    return f"trojan://{urllib.parse.quote(p['password'])}@{p['server']}:{p['port']}?{query}#{urllib.parse.quote(p['name'])}"


def to_ss_uri(p):
    """ss://base64(method:password)@host:port#name"""
    method = p.get("method", "aes-256-gcm")
    password = p["password"]
    userinfo = base64.b64encode(f"{method}:{password}".encode()).decode()
    q = {}
    if p.get("skip-cert-verify") is True:
        q["allowInsecure"] = "1"
    if p.get("udp") is True:
        q["udp"] = "true"
    # plugin
    plugin = p.get("plugin")
    if plugin:
        q["plugin"] = plugin
        plugin_opts = p.get("plugin-opts", "")
        if plugin_opts:
            q[plugin.replace("-", "_") + "_opts"] = plugin_opts
    query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in q.items()) if q else ""
    suffix = f"?{query}" if query else ""
    return f"ss://{userinfo}@{p['server']}:{p['port']}{suffix}#{urllib.parse.quote(p['name'])}"


def to_vmess_uri(p):
    """vmess://base64(json)"""
    obj = {
        "v": "2",
        "ps": p["name"],
        "add": p["server"],
        "port": str(p["port"]),
        "id": p["uuid"],
        "aid": str(p.get("alterId", 0)),
        "net": p.get("network", "tcp"),
        "type": "none",
        "host": "",
        "path": "",
        "tls": "tls" if p.get("tls") is True else "",
    }
    if p.get("sni"):
        obj["sni"] = p["sni"]
    if p.get("skip-cert-verify") is True:
        obj["allowInsecure"] = "1"
    if p.get("fp"):
        obj["fp"] = p["fp"]
    if p.get("ws-opts"):
        ws = p["ws-opts"]
        obj["path"] = ws.get("path", "/")
        h = ws.get("headers", {})
        if isinstance(h, dict) and h.get("Host"):
            obj["host"] = h["Host"]
    b64 = base64.b64encode(json.dumps(obj).encode()).decode()
    return f"vmess://{b64}"


def to_hysteria2_uri(p):
    """hysteria2://password@host:port/?params#name"""
    password = p["password"]
    q = {}
    if p.get("skip-cert-verify") is True:
        q["insecure"] = "1"
    elif p.get("skip-cert-verify") is False:
        q["insecure"] = "0"
    if p.get("sni"):
        q["sni"] = p["sni"]
    if p.get("udp") is True:
        q["udp"] = "true"
    # obfs
    if p.get("obfs"):
        q["obfs"] = p["obfs"]
    if p.get("obfs-password"):
        q["obfs-password"] = p["obfs-password"]
    if p.get("pinSHA256"):
        q["pinSHA256"] = p["pinSHA256"]
    query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in q.items())
    return f"hysteria2://{urllib.parse.quote(password)}@{p['server']}:{p['port']}/?{query}#{urllib.parse.quote(p['name'])}"


def to_anytls_uri(p):
    """anytls://password@host:port/?params#name"""
    q = {}
    if p.get("skip-cert-verify") is True:
        q["insecure"] = "1"
    elif p.get("skip-cert-verify") is False:
        q["insecure"] = "0"
    if p.get("sni"):
        q["sni"] = p["sni"]
    if p.get("fp"):
        q["fp"] = p["fp"]
    if p.get("udp") is True:
        q["udp"] = "true"
    query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in q.items())
    return f"anytls://{urllib.parse.quote(p['password'])}@{p['server']}:{p['port']}/?{query}#{urllib.parse.quote(p['name'])}"


def to_http_uri(p):
    """http://user:pass@host:port#name 或 http://host:port#name"""
    auth = ""
    if p.get("username") and p.get("password"):
        auth = f"{urllib.parse.quote(p['username'])}:{urllib.parse.quote(p['password'])}@"
    q = {}
    if p.get("skip-cert-verify") is True:
        q["allowInsecure"] = "1"
    if p.get("tls") is True:
        q["tls"] = "true"
    query = ("?" + "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in q.items())) if q else ""
    return f"http://{auth}{p['server']}:{p['port']}{query}#{urllib.parse.quote(p['name'])}"


def to_socks_uri(p):
    """socks5://user:pass@host:port#name"""
    auth = ""
    if p.get("username") and p.get("password"):
        auth = f"{urllib.parse.quote(p['username'])}:{urllib.parse.quote(p['password'])}@"
    return f"socks5://{auth}{p['server']}:{p['port']}#{urllib.parse.quote(p['name'])}"


def node_to_uri(p):
    t = p.get("type", "")
    if t == "vless":
        return to_vless_uri(p)
    elif t == "trojan":
        return to_trojan_uri(p)
    elif t == "ss":
        return to_ss_uri(p)
    elif t == "vmess":
        return to_vmess_uri(p)
    elif t == "hysteria2":
        return to_hysteria2_uri(p)
    elif t == "anytls":
        return to_anytls_uri(p)
    elif t == "http":
        return to_http_uri(p)
    elif t == "socks":
        return to_socks_uri(p)
    else:
        return None


def main():
    import json

    raw = {}
    for f in FILES:
        print(f"[fetch] {f}")
        cfg = fetch(f)
        raw[f] = [clean(p) for p in cfg["proxies"]]

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

    uris = []
    skipped = []
    for p in deduped:
        # 跳过明显无效节点
        t = p.get("type", "")
        password = p.get("password", "")
        
        # hysteria2: 密码必须是真实值（排除占位符/URL）
        if t == "hysteria2" and (not password or "/" in password or password.startswith("http")):
            skipped.append((t, p["name"], f"invalid password: {password[:50]}"))
            continue
        
        # socks5/http: 必须有真实认证信息
        if t in ("socks", "http"):
            has_auth = bool(p.get("username")) and bool(p.get("password"))
            if not has_auth:
                skipped.append((t, p["name"], "missing auth"))
                continue
        
        uri = node_to_uri(p)
        if uri:
            uris.append(uri)
        else:
            skipped.append((t, p["name"], "unsupported"))

    if skipped:
        print(f"[skip] {len(skipped)} invalid/unsupported:")
        for item in skipped[:10]:
            if len(item) == 3:
                t, n, reason = item
                print(f"  {t}: {n} ({reason})")
            else:
                t, n = item
                print(f"  {t}: {n}")

    # 输出 txt
    txt_content = "\n".join(uris) + "\n"
    txt_b64 = base64.b64encode(txt_content.encode()).decode()

    # 输出可读 yaml
    out = {
        "subscription": {
            "name": "Vanic24/VPN 通用订阅",
            "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_count": len(uris),
            "skipped": len(skipped),
        },
        "nodes_txt": txt_content,
        "nodes_base64": txt_b64,
    }
    yaml_content = yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False)

    (OUT_DIR / "vanic_universal.txt").write_text(txt_content, encoding="utf-8")
    (OUT_DIR / "vanic_universal_base64.txt").write_text(txt_b64, encoding="utf-8")
    (OUT_DIR / "vanic_universal.yaml").write_text(yaml_content, encoding="utf-8")

    print(f"[txt] {len(txt_content)} bytes, {len(uris)} nodes")
    print(f"[b64] {len(txt_b64)} bytes")
    print(f"[yaml] {len(yaml_content)} bytes")
    print("\n前5条:")
    for u in uris[:5]:
        print(" ", u[:120])


if __name__ == "__main__":
    main()

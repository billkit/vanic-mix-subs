#!/usr/bin/env python3
"""
vanic-sub.py — 从 Vanic24/VPN 抓取节点，起 HTTP 订阅服务
用法: python3 vanic-sub.py [端口] [输出文件]
默认端口 8787，输出 vanic_sub.yaml
"""
import sys, yaml, urllib.request, datetime, pathlib, socket, http.server, threading

REPO = "https://raw.githubusercontent.com/Vanic24/VPN/main"
FILES = ["8EB", "9PB", "Lifetime", "Sub3", "Filter"]
NA = "https://www.gstatic.com/generate_204"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("vanic_sub.yaml")

def fetch(name):
    url = f"{REPO}/{name}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return yaml.safe_load(r.read().decode("utf-8"))

def normalize(p):
    drop = {"cipher", "country", "delay", "allowInsecure"}
    out = {k: v for k, v in p.items() if k not in drop}
    for k in ("insecure", "skip-cert-verify", "tls-enabled"):
        if k in out and isinstance(out[k], str) and out[k] in {"0", "1"}:
            out[k] = (out[k] == "1")
    return out

def build():
    raw = {}
    for f in FILES:
        print(f"[fetch] {f}")
        cfg = fetch(f)
        cleaned = []
        for p in cfg["proxies"]:
            np = normalize(p)
            tag = f" | {f}" if f" | {f}" not in np["name"] else ""
            np["name"] = np["name"] + tag
            cleaned.append(np)
        raw[f] = {"proxies": cleaned}

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
    print(f"[dedup] {n_before} -> {len(deduped)} ({n_before - len(deduped)} suppressed)")

    groups = [
        {"name": "🌍 全线路选择", "type": "select",
         "proxies": ["⚡️ 全自动测速"] + [f"📦 {f}" for f in FILES]},
        {"name": "⚡️ 全自动测速", "type": "url-test",
         "proxies": [p["name"] for p in deduped],
         "url": NA, "interval": 300, "tolerance": 50},
    ]
    for f in FILES:
        names = [p["name"] for p in deduped if p["name"].endswith(f" | {f}")]
        if names:
            groups.append({"name": f"📦 {f}", "type": "url-test",
                           "proxies": names, "url": NA, "interval": 300, "tolerance": 50})

    out = {
        "port": 7890, "socks-port": 7891, "allow-lan": False,
        "mode": "rule", "log-level": "warning", "ipv6": True,
        "external-controller": "127.0.0.1:9090",
        "proxies": deduped, "proxy-groups": groups,
        "rules": [
            "DOMAIN-SUFFIX,google.com,🌍 全线路选择",
            "DOMAIN-SUFFIX,youtube.com,🌍 全线路选择",
            "DOMAIN-SUFFIX,github.com,🌍 全线路选择",
            "DOMAIN-SUFFIX,githubusercontent.com,🌍 全线路选择",
            "DOMAIN-SUFFIX,googleapis.cn,🌍 全线路选择",
            "GEOIP,CN,DIRECT",
            "MATCH,🌍 全线路选择",
        ],
    }
    header = (f"# Vanic24/VPN 通用订阅 · {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
              f"# 节点: {len(deduped)} ({n_before} 去重后)\n")
    content = header + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, default_flow_style=False)
    OUT.write_text(content, encoding="utf-8")
    print(f"[write] {OUT} ({len(content)} bytes)")
    return OUT

class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass   # 禁用所有日志

    def do_GET(self):
        if self.path.strip("/") == OUT.name or self.path == "/":
            path = str(OUT.resolve())
            with open(path, "rb") as f:
                size = f.seek(0, 2)
                f.seek(0)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(size))
                self.end_headers()
                self.wfile.write(f.read())
        else:
            self.send_error(404)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

if __name__ == "__main__":
    yaml_path = build()

    # 获取本机 IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()

    print(f"\n订阅地址: http://{ip}:{PORT}/{OUT.name}")
    print(f"Daed 直接填上面链接，或手动访问 http://{ip}:{PORT}/ 查看")
    print(f"Ctrl+C 停止服务\n")

    server = http.server.HTTPServer(("0.0.0.0", PORT), SilentHandler)
    server.serve_forever()
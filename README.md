# vanic-mix-subs 📦

每 6 小时自动拉取 [Vanic24/VPN](https://github.com/Vanic24/VPN) 仓库的 5 个 Clash 订阅文件，
合并去重后输出一个 Daed / mihomo 通用订阅。

> **跳过 MIX**：该文件全是 socks5 节点，mihomo 内核不支持 socks5 入站代理，无法使用。

## 产物

- [`vanic_merged.yaml`](./vanic_merged.yaml) — Daed / Clash Verge / Stash / Clash Meta for Android 直接吃

合并源（去重前 571，去重后 ~563）：

| 文件 | 节点 | 协议 |
|---|---|---|
| 8EB | 50 | trojan / vless |
| 9PB | 420 | anytls / hysteria2 |
| Lifetime | 12 | vless / trojan / ss / vmess |
| Sub3 | 34 | vless |
| Filter | 47 | hysteria2 / trojan / vless |

策略组：
- 🌍 全线路选择 (select，含所有 📦 子组入口)
- ⚡️ 全自动测速 (url-test, 全部 563 节点)
- 📦 8EB / 📦 9PB / 📦 Lifetime / 📦 Sub3 / 📦 Filter (各自的 url-test)

## 怎么用
**Daed / Clash Verge / Clash Meta 内核：**
```
订阅 URL: https://raw.githubusercontent.com/billkit/vanic-mix-subs/main/vanic_merged.yaml
```

## 本地运行
```bash
python3 build_merged.py
```

## 调度
GitHub Actions 每 6 小时（cron `13 */6 * * *`）自动跑一次 + 手动触发。

源码声明：源仓库仅用于个人研究/测试，不保证节点可用性。

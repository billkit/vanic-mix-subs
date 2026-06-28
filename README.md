# vanic-mix-subs 📦

每 6 小时自动把 [Vanic24/VPN@MIX](https://raw.githubusercontent.com/Vanic24/VPN/refs/heads/main/MIX) 转成 Daed / Clash Meta / mihomo 通用可用的订阅 YAML。

## 产物
- [`vanic_mix_clash_subscription.yaml`](./vanic_mix_clash_subscription.yaml) — Daed/Clash Verge/Stash 直接吃的配置

## 怎么用
**Daed / Clash Meta / Verge：**
订阅 URL 填：
```
https://raw.githubusercontent.com/<owner>/vanic-mix-subs/main/vanic_mix_clash_subscription.yaml
```

## 本地运行
```bash
python3 convert.py            # 用默认源
SRC_URL=<自定义源> python3 convert.py
```

## 调度
GitHub Actions 每 6 小时（cron `13 */6 * * *`）自动跑一次 + 手动触发。
上游变更时也会自动 commit。

源码声明：源仓库仅用于个人研究/测试，不保证节点可用性。

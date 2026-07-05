# Vanic24/VPN → Dae/Daed 通用订阅

把 [Vanic24/VPN](https://github.com/Vanic24/VPN) 的 Clash 节点转换成 Dae/Daed 能直接识别的通用订阅格式。

## 产物

- `vanic_universal.txt` — 纯文本，每行一个节点 URI
- `vanic_universal_base64.txt` — base64 编码，Dae/Shadowrocket/Loón 直接订阅
- `vanic_universal.yaml` — 元数据（节点数、协议分布、更新时间）

## 支持的协议

```
vless / hysteria2 / anytls / trojan / ss / vmess
```

## 本地使用

```bash
pip install pyyaml
python3 build_universal_sub.py
```

输出 3 个文件，用 `vanic_universal_base64.txt` 作为订阅链接。

## Dae/Daed 配置

```nginx
subscription {
    vanic: 'http://你的服务器:8888/vanic_universal_base64.txt'
}
```

或直接在客户端导入 base64 链接。

## 节点说明

- 来源：8EB / 9PB / Lifetime / Sub3 / Filter（跳过 MIX）
- 去重：按 (server, port, type) 去重
- 过滤：自动跳过无效节点（空密码、缺失认证等）

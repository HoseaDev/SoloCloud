# SoloCloud SSL 自动续期系统

这个 SSL 自动续期系统为你的 SoloCloud 个人云存储提供完全自动化的 HTTPS 证书管理。

## 功能特点

- 🔒 **自动申请** Let's Encrypt SSL 证书
- 🔄 **自动续期** 每 89 天（3个月减1天）自动续期
- 📅 **定时任务** 支持 cron 和 systemd timer 两种调度方式
- 🛡️ **安全配置** 包含现代 SSL/TLS 安全配置
- 📝 **详细日志** 完整的操作日志记录
- 🔧 **零维护** 设置完成后无需人工干预

## 文件结构

```
SoloCloud/
├── ssl_setup.sh           # 初次申请 SSL 证书
├── ssl_renewal.sh         # 自动续期脚本
├── nginx.conf             # 已配置 SSL 的 Nginx 配置
├── ssl/                   # SSL 证书存储目录
│   ├── server.crt         # SSL 证书文件
│   ├── server.key         # 私钥文件
│   └── domain.txt         # 域名记录文件
└── logs/
    └── ssl_renewal.log    # 续期日志
```

## 快速开始

### 1. 初次设置 SSL 证书

```bash
# 确保脚本可执行
chmod +x ssl_setup.sh ssl_renewal.sh

# 运行初次设置（会提示输入域名）
./ssl_setup.sh
```

设置过程：
1. 脚本会检查并安装 certbot（如果需要）
2. 提示你输入域名（例如：example.com）
3. 自动申请 Let's Encrypt 证书
4. 将证书复制到 `ssl/` 目录
5. 保存域名信息供续期使用

### 2. 更新 Nginx 配置

证书申请成功后，需要更新 `nginx.conf`：

1. 将两处 `server_name _;` 替换为你的域名
2. 取消注释 HTTP 重定向部分：
   ```nginx
   # 取消这部分的注释
   location / {
     return 301 https://$server_name$request_uri;
   }
   
   # 删除或注释临时代理部分
   # location / {
   #   proxy_pass http://solocloud:8080;
   #   ...
   # }
   ```

### 3. 启动服务

```bash
# 启动 SoloCloud 服务
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### 4. 设置自动续期

```bash
# 设置定时任务（推荐）
./ssl_renewal.sh --setup-cron
```

这会创建：
- Cron 任务：每 89 天在凌晨 3 点自动续期
- Systemd timer：作为备选调度方案

## 使用说明

### 手动操作命令

```bash
# 检查证书状态
./ssl_renewal.sh --check

# 手动续期证书
./ssl_renewal.sh --renew

# 设置自动续期
./ssl_renewal.sh --setup-cron

# 查看帮助
./ssl_renewal.sh --help
```

### 查看日志

```bash
# 查看续期日志
tail -f logs/ssl_renewal.log

# 查看 Docker 日志
docker-compose logs -f nginx
```

## 续期流程

自动续期过程完全无人值守：

1. **检查证书** - 如果距离过期超过 30 天，跳过续期
2. **停止服务** - 临时停止 SoloCloud 容器
3. **启动临时服务** - 启动临时 Nginx 用于证书验证
4. **续期证书** - 调用 certbot 续期
5. **复制证书** - 将新证书复制到 SSL 目录
6. **重启服务** - 重新启动 SoloCloud 服务
7. **记录日志** - 记录操作结果

## 故障排除

### 证书申请失败

1. **检查域名解析**：确保域名正确解析到你的服务器
2. **检查防火墙**：确保 80 和 443 端口开放
3. **检查权限**：确保脚本有 sudo 权限

### 续期失败

```bash
# 查看详细错误
tail -20 logs/ssl_renewal.log

# 手动测试续期
./ssl_renewal.sh --renew

# 检查证书状态
./ssl_renewal.sh --check
```

### 常见问题

**Q: 证书过期了怎么办？**
A: 运行 `./ssl_renewal.sh --renew` 手动续期，或重新运行 `./ssl_setup.sh`

**Q: 更换域名怎么办？**
A: 重新运行 `./ssl_setup.sh` 并输入新域名

**Q: 如何查看定时任务？**
A: 运行 `crontab -l` 查看 cron 任务，或 `systemctl status solocloud-ssl-renewal.timer` 查看 systemd timer

## 安全说明

- 证书文件权限：`server.crt` (644), `server.key` (600)
- 私钥文件只有所有者可读
- 使用现代 TLS 1.2/1.3 协议
- 包含安全 HTTP 头配置
- 自动 HTTP 到 HTTPS 重定向

## 技术细节

- **证书颁发机构**: Let's Encrypt
- **证书类型**: Domain Validated (DV)
- **有效期**: 90 天
- **续期时机**: 证书过期前 30 天内
- **调度频率**: 每 89 天检查一次
- **备份策略**: Let's Encrypt 自动保留证书历史

---

设置完成后，你的 SoloCloud 将拥有自动续期的 HTTPS 证书，无需任何人工干预！

# SoloCloud 生产环境部署指南

## 🚀 部署方式

### 方式一：Docker 部署（推荐）

#### 1. 基本部署
```bash
# 构建镜像
docker build -t SoloCloud .

# 运行容器
docker run -d \
  --name SoloCloud \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-super-secret-key-here \
  SoloCloud
```

#### 2. 使用 Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 3. 使用 Nginx 反向代理
```bash
# 启动包含 Nginx 的完整服务
docker-compose --profile with-nginx up -d
```

### 方式二：传统部署

#### 1. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

#### 3. 使用 Gunicorn 启动
```bash
# 直接启动
gunicorn --config gunicorn.conf.py app:app

# 或使用启动脚本
chmod +x start.sh
./start.sh
```

#### 4. 使用 systemd 管理服务
```bash
# 复制服务文件
sudo cp SoloCloud.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start SoloCloud
sudo systemctl enable SoloCloud

# 查看状态
sudo systemctl status SoloCloud
```

## ⚙️ 环境配置

### 必需的环境变量
```bash
# 应用配置
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here

# 数据库配置
DATABASE_URL=sqlite:///data/SoloCloud.db

# 日志配置
LOG_LEVEL=WARNING
LOG_FILE=/var/log/SoloCloud/SoloCloud.log

# 存储配置
STORAGE_PROVIDER=local
UPLOAD_FOLDER=/app/uploads
```

### 云存储配置（可选）
```bash
# 阿里云 OSS
ALIYUN_OSS_ACCESS_KEY_ID=your-access-key
ALIYUN_OSS_ACCESS_KEY_SECRET=your-secret-key
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=your-bucket

# 腾讯云 COS
TENCENT_COS_SECRET_ID=your-secret-id
TENCENT_COS_SECRET_KEY=your-secret-key
TENCENT_COS_REGION=ap-beijing
TENCENT_COS_BUCKET_NAME=your-bucket
```

## 📊 监控和日志

### 日志文件位置
- **应用日志**: `/var/log/SoloCloud/SoloCloud.log`
- **错误日志**: `/var/log/SoloCloud/solocloud_error.log`
- **安全日志**: `/var/log/SoloCloud/solocloud_security.log`
- **JSON日志**: `/var/log/SoloCloud/SoloCloud.json`

### 健康检查
```bash
# 检查应用状态
curl http://localhost:8080/health

# 预期响应
{
  "status": "healthy",
  "timestamp": "2025-01-07T02:12:38.123456",
  "version": "1.0.0",
  "environment": "production"
}
```

### 日志监控
```bash
# 实时查看应用日志
tail -f /var/log/SoloCloud/SoloCloud.log

# 查看错误日志
tail -f /var/log/SoloCloud/solocloud_error.log

# 查看安全事件
tail -f /var/log/SoloCloud/solocloud_security.log
```

## 🔒 安全配置

### 1. 防火墙设置
```bash
# 只开放必要端口
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. SSL/TLS 配置
建议使用 Let's Encrypt 或其他 SSL 证书：
```bash
# 使用 certbot 获取证书
sudo certbot --nginx -d your-domain.com
```

### 3. 定期备份
```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/solocloud_$DATE.tar.gz /app/data /app/uploads
```

## 🔧 性能优化

### 1. Gunicorn 配置优化
根据服务器配置调整 `gunicorn.conf.py` 中的参数：
- `workers`: CPU核心数 × 2 + 1
- `worker_connections`: 根据内存调整
- `timeout`: 根据应用响应时间调整

### 2. 数据库优化
对于大量文件的情况，考虑使用 PostgreSQL：
```bash
# 环境变量
DATABASE_URL=postgresql://user:password@localhost/SoloCloud
```

### 3. 静态文件服务
使用 Nginx 服务静态文件：
```nginx
location /static/ {
    alias /app/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🚨 故障排除

### 常见问题

1. **应用无法启动**
   ```bash
   # 检查日志
   docker logs SoloCloud
   # 或
   journalctl -u SoloCloud -f
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库文件权限
   ls -la data/
   # 检查环境变量
   env | grep DATABASE
   ```

3. **文件上传失败**
   ```bash
   # 检查上传目录权限
   ls -la uploads/
   # 检查磁盘空间
   df -h
   ```

4. **日志文件过大**
   ```bash
   # 日志会自动轮转，但可以手动清理
   sudo logrotate -f /etc/logrotate.d/SoloCloud
   ```

### 性能监控
```bash
# 查看资源使用情况
docker stats SoloCloud

# 查看进程状态
ps aux | grep gunicorn

# 查看端口占用
netstat -tlnp | grep 8080
```

## 📋 维护清单

### 定期维护任务
- [ ] 检查日志文件大小和轮转
- [ ] 备份数据库和上传文件
- [ ] 更新系统和依赖包
- [ ] 检查SSL证书有效期
- [ ] 监控磁盘空间使用情况
- [ ] 检查安全日志异常活动

### 更新部署
```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

---

## 🎯 生产环境特性

✅ **已实现的生产级特性**：
- 完整的日志系统（应用、错误、安全、JSON格式）
- 全局错误处理和用户友好错误页面
- 健康检查端点
- Docker化部署
- Gunicorn WSGI服务器
- systemd服务管理
- 配置文件分离（开发/生产环境）
- 安全事件记录和监控
- 单用户系统强制执行
- 防暴力登录保护

你的SoloCloud现在已经是一个**生产级的个人云存储系统**！🚀

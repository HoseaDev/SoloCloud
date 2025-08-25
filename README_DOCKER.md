# 🐳 SoloCloud Docker 部署指南

## 📋 快速开始

### 1. 基础部署
```bash
# 克隆项目
git clone https://github.com/yourusername/SoloCloud.git
cd SoloCloud

# 复制环境配置
cp .env.example .env

# 编辑配置（必须修改SECRET_KEY）
nano .env

# 启动服务
./docker-start.sh start
```

### 2. 使用启动脚本
```bash
./docker-start.sh start    # 启动服务
./docker-start.sh stop     # 停止服务
./docker-start.sh restart  # 重启服务
./docker-start.sh rebuild  # 重新构建
./docker-start.sh logs     # 查看日志
./docker-start.sh status   # 查看状态
```

## 🔧 配置说明

### 自定义数据存储位置

在 `.env` 文件中配置数据存储路径：

```bash
# 使用绝对路径
DATA_PATH=/mnt/storage/solocloud/data
UPLOADS_PATH=/mnt/storage/solocloud/uploads
LOGS_PATH=/var/log/solocloud

# 或使用相对路径（默认）
DATA_PATH=./data
UPLOADS_PATH=./uploads
LOGS_PATH=./logs
```

### 存储位置示例

#### 示例1：使用外部硬盘
```bash
# .env 配置
DATA_PATH=/mnt/external-disk/solocloud/data
UPLOADS_PATH=/mnt/external-disk/solocloud/uploads
LOGS_PATH=/mnt/external-disk/solocloud/logs
```

#### 示例2：使用 NAS 存储
```bash
# 先挂载 NAS
sudo mount -t nfs nas-server:/solocloud /mnt/nas-solocloud

# .env 配置
DATA_PATH=/mnt/nas-solocloud/data
UPLOADS_PATH=/mnt/nas-solocloud/uploads
LOGS_PATH=/mnt/nas-solocloud/logs
```

#### 示例3：使用不同磁盘分离存储
```bash
# 数据库放在 SSD
DATA_PATH=/mnt/ssd/solocloud/data

# 文件放在大容量 HDD
UPLOADS_PATH=/mnt/hdd/solocloud/uploads

# 日志放在系统盘
LOGS_PATH=/var/log/solocloud
```

## 🚀 生产环境部署

### 使用生产配置
```bash
# 使用生产环境专用配置
docker-compose -f docker-compose.prod.yml up -d
```

### 生产环境数据路径
生产环境建议使用固定的系统路径：
```bash
# .env 生产配置
DATA_VOLUME_PATH=/var/lib/solocloud/data
UPLOADS_VOLUME_PATH=/var/lib/solocloud/uploads
LOGS_VOLUME_PATH=/var/lib/solocloud/logs
SSL_VOLUME_PATH=/etc/solocloud/ssl
```

## 📊 资源配置

### CPU 和内存限制
```bash
# .env 配置
CPU_LIMIT=2              # 最大使用 2 个 CPU 核心
CPU_RESERVATION=0.5      # 预留 0.5 个核心
MEMORY_LIMIT=2G          # 最大使用 2GB 内存
MEMORY_RESERVATION=512M  # 预留 512MB 内存
```

### 根据服务器配置调整

#### 小型服务器（1核2G）
```bash
CPU_LIMIT=1
MEMORY_LIMIT=1G
NGINX_CPU_LIMIT=0.5
NGINX_MEMORY_LIMIT=256M
```

#### 中型服务器（4核8G）
```bash
CPU_LIMIT=3
MEMORY_LIMIT=4G
NGINX_CPU_LIMIT=1
NGINX_MEMORY_LIMIT=1G
```

#### 大型服务器（8核16G+）
```bash
CPU_LIMIT=6
MEMORY_LIMIT=8G
NGINX_CPU_LIMIT=2
NGINX_MEMORY_LIMIT=2G
```

## 🔒 安全配置

### 启用 HTTPS
```bash
# 1. 准备证书文件
mkdir -p ssl
cp your-cert.crt ssl/server.crt
cp your-cert.key ssl/server.key

# 2. 配置 .env
FORCE_HTTPS=true
SSL_PATH=./ssl

# 3. 重启服务
docker-compose restart
```

### 修改默认端口
```bash
# .env 配置
APP_PORT=8888    # 应用端口
HTTP_PORT=8080   # HTTP 端口
HTTPS_PORT=8443  # HTTPS 端口
```

## 🛠️ 高级配置

### 使用 PostgreSQL 替代 SQLite
```bash
# .env 配置
DATABASE_URL=postgresql://solocloud:password@postgres:5432/solocloud

# 启用 postgres 服务（编辑 docker-compose.yml 取消注释）
```

### 配置云存储
```bash
# 阿里云 OSS
STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ACCESS_KEY_ID=your-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-key-secret
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=your-bucket
```

## 📝 维护操作

### 备份数据
```bash
# 备份脚本
./migrate.sh backup

# 或手动备份
tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/
```

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动
./docker-start.sh rebuild
```

### 查看日志
```bash
# 实时日志
docker-compose logs -f

# 仅查看应用日志
docker-compose logs -f solocloud

# 查看最近100行
docker-compose logs --tail=100
```

## ❓ 常见问题

### 1. 权限问题
```bash
# 确保目录有正确权限
sudo chown -R 1000:1000 data/ uploads/ logs/
```

### 2. 端口占用
```bash
# 检查端口占用
sudo netstat -tlnp | grep :80

# 修改端口
# 编辑 .env 文件中的 HTTP_PORT 和 HTTPS_PORT
```

### 3. 磁盘空间不足
```bash
# 清理 Docker 缓存
docker system prune -a

# 清理日志
truncate -s 0 logs/*.log
```

## 📧 支持

如有问题，请提交 Issue 或联系维护团队。
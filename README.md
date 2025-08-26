# 🌤️ SoloCloud

一个简洁实用的**个人云存储系统**，支持文件管理、笔记记录、随心记录等功能，专为个人使用设计。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg)

## ✨ 主要功能

### 📁 文件管理
- **文件上传**: 支持拖拽上传，显示上传进度，无文件类型限制
- **URL下载**: 支持通过URL直接下载文件到服务器
- **文件预览**: 图片和视频可在线预览，自动生成缩略图
- **文件管理**: 下载、删除、查看文件信息
- **文件搜索**: 按文件名搜索文件
- **文件分享**: 生成临时分享链接，可设置过期时间和访问次数

### 📝 笔记功能
- **简单笔记**: 创建、编辑、删除文本笔记
- **标签管理**: 为笔记添加标签，用逗号分隔
- **时间记录**: 自动记录创建和更新时间
- **分页显示**: 笔记列表支持分页浏览

### 💬 随心记录
- **文字记录**: 快速记录想法和灵感，类似微信聊天界面
- **文件记录**: 在记录中上传和分享文件
- **时间排序**: 按时间顺序显示所有记录
- **删除管理**: 可删除不需要的记录

### ☁️ 多云存储
- **本地存储**: 默认存储方式
- **阿里云 OSS**: 支持阿里云对象存储
- **腾讯云 COS**: 支持腾讯云对象存储
- **七牛云**: 支持七牛云存储
- **坚果云**: 支持WebDAV协议访问坚果云
- **存储设置**: 可在Web界面中配置和切换存储后端

### 🔒 安全特性
- **单用户系统**: 专为个人使用设计，系统只允许一个用户账号
- **登录保护**: 防止暴力破解，多次失败后会临时封禁IP
- **会话管理**: 安全的用户会话管理
- **自动协议适应**: 自动检测HTTP/HTTPS访问并调整安全设置

### 📱 响应式设计
- **移动适配**: 支持手机和平板访问
- **现代界面**: 基于Bootstrap 5的清洁界面
- **多视图模式**: 文件支持网格和列表两种显示模式

## 🛠️ 技术栈

- **后端**: Python 3.11+ + Flask 2.3+ + SQLAlchemy
- **数据库**: SQLite（默认）/ PostgreSQL（可选）
- **前端**: Bootstrap 5 + 原生 JavaScript
- **文件处理**: Pillow + OpenCV（缩略图生成）
- **云存储**: 支持阿里云OSS、腾讯云COS、七牛云、坚果云
- **部署**: Docker + Docker Compose + Nginx
- **Web服务器**: Gunicorn + Nginx

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/HoseaDev/SoloCloud.git
cd SoloCloud

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 SECRET_KEY 等配置
nano .env

# 3. 启动服务
docker compose up -d

# 4. 访问应用
open http://localhost
```

### 方式二：使用启动脚本

```bash
./docker-start.sh start    # 启动服务
./docker-start.sh stop     # 停止服务
./docker-start.sh restart  # 重启服务
./docker-start.sh rebuild  # 重新构建
./docker-start.sh logs     # 查看日志
./docker-start.sh status   # 查看状态
```

### 方式三：传统部署

```bash
# 1. 环境要求
# Python 3.11+, pip, virtualenv

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
nano .env

# 5. 启动应用
python app.py
# 或使用 Gunicorn
gunicorn --config gunicorn.conf.py app:app
```

---

## 🔧 配置说明

### 基础配置（.env 文件）

```bash
# 应用配置（必需）
SECRET_KEY=your-secret-key-here  # 必须修改！
DEBUG=false                       # 生产环境设为false

# 数据库配置
DATABASE_URL=sqlite:////app/data/SoloCloud.db

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/SoloCloud.log

# 存储配置
STORAGE_PROVIDER=local
UPLOAD_FOLDER=/app/uploads
```

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

#### 存储配置示例

<details>
<summary>使用外部硬盘</summary>

```bash
# .env 配置
DATA_PATH=/mnt/external-disk/solocloud/data
UPLOADS_PATH=/mnt/external-disk/solocloud/uploads
LOGS_PATH=/mnt/external-disk/solocloud/logs
```
</details>

<details>
<summary>使用 NAS 存储</summary>

```bash
# 先挂载 NAS
sudo mount -t nfs nas-server:/solocloud /mnt/nas-solocloud

# .env 配置
DATA_PATH=/mnt/nas-solocloud/data
UPLOADS_PATH=/mnt/nas-solocloud/uploads
LOGS_PATH=/mnt/nas-solocloud/logs
```
</details>

<details>
<summary>使用不同磁盘分离存储</summary>

```bash
# 数据库放在 SSD
DATA_PATH=/mnt/ssd/solocloud/data

# 文件放在大容量 HDD
UPLOADS_PATH=/mnt/hdd/solocloud/uploads

# 日志放在系统盘
LOGS_PATH=/var/log/solocloud
```
</details>

### 云存储配置

<details>
<summary>阿里云 OSS</summary>

```bash
STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ACCESS_KEY_ID=your-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-key-secret
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=your-bucket
```
</details>

<details>
<summary>腾讯云 COS</summary>

```bash
STORAGE_PROVIDER=tencent_cos
TENCENT_COS_SECRET_ID=your-secret-id
TENCENT_COS_SECRET_KEY=your-secret-key
TENCENT_COS_REGION=ap-beijing
TENCENT_COS_BUCKET_NAME=your-bucket
```
</details>

<details>
<summary>七牛云</summary>

```bash
STORAGE_PROVIDER=qiniu
QINIU_ACCESS_KEY=your-access-key
QINIU_SECRET_KEY=your-secret-key
QINIU_BUCKET_NAME=your-bucket
QINIU_DOMAIN=your-domain.com
```
</details>

<details>
<summary>坚果云 WebDAV</summary>

```bash
STORAGE_PROVIDER=jianguoyun
JIANGUOYUN_WEBDAV_URL=https://dav.jianguoyun.com/dav
JIANGUOYUN_USERNAME=your-username
JIANGUOYUN_PASSWORD=your-app-password
```
</details>

---

## 🚀 生产环境部署

### 使用生产配置

```bash
# 使用生产环境专用配置
docker compose -f docker-compose.prod.yml up -d
```

### 资源配置

Docker Compose 会自动适应服务器资源，无需手动调整。但如果需要，可以通过环境变量自定义：

```bash
# .env 配置
CPU_LIMIT=2              # 最大使用 2 个 CPU 核心
MEMORY_LIMIT=2G          # 最大使用 2GB 内存
CPU_RESERVATION=0.5      # 预留 0.5 个核心
MEMORY_RESERVATION=512M  # 预留 512MB 内存
```

### HTTPS 配置

#### 方式一：使用 Let's Encrypt（推荐）

```bash
# 1. 运行SSL设置脚本
./ssl_setup.sh yourdomain.com youremail@example.com

# 2. 设置自动续期
./ssl_renewal.sh --setup-cron

# 3. 检查证书状态
./ssl_renewal.sh --check
```

#### 方式二：使用自有证书

```bash
# 1. 准备证书文件
mkdir -p ssl
cp your-cert.crt ssl/server.crt
cp your-cert.key ssl/server.key

# 2. 重启服务
docker compose restart nginx
```

---

## 🔐 自动协议适应

SoloCloud 支持**自动协议适应**功能，系统会自动检测用户的访问方式并调整安全设置：

### 主要特性

1. **自动检测访问协议**
   - HTTP访问：Cookie不设置Secure标志
   - HTTPS访问：Cookie自动设置Secure标志
   - IP访问：支持通过IP地址直接访问

2. **智能URL生成**
   - 生成的文件URL自动匹配用户的访问协议
   - 无需手动配置

3. **简化配置**
   - 无需设置FLASK_ENV
   - 无需配置FORCE_HTTPS
   - 系统自动适应环境

### 安全建议

- 生产环境推荐使用HTTPS
- 系统会在HTTPS下自动启用所有安全特性
- 开发环境可以使用HTTP进行测试

---

## 🔄 数据迁移

### 数据存储位置
- **数据库**: `data/SoloCloud.db`
- **用户文件**: `uploads/` 目录
- **日志文件**: `logs/` 目录
- **配置文件**: `.env` 文件

### 迁移工具

```bash
# 数据备份和恢复
./migrate.sh backup                    # 创建数据备份
./migrate.sh restore <备份文件>         # 从备份恢复数据

# 跨机器迁移
./migrate.sh export                    # 创建迁移包

# 部署方式转换
./migrate.sh local-to-docker           # 本地Python → Docker
./migrate.sh docker-to-local           # Docker → 本地Python
```

### 跨服务器迁移

```bash
# 在源服务器
./migrate.sh export

# 传输到目标服务器
scp backups/solocloud_migration_*.tar.gz user@target:/path/

# 在目标服务器
tar -xzf solocloud_migration_*.tar.gz
docker compose up -d
```

---

## 📝 使用说明

### 首次使用
1. 启动应用后，访问 `http://localhost`
2. 系统会自动跳转到首次设置页面
3. 创建管理员账号（用户名和密码）
4. 登录后即可使用所有功能

### 文件管理
- 拖拽文件到上传区域或点击选择文件
- 支持批量上传，显示上传进度
- 支持任何文件格式，无限制
- 支持通过URL下载文件
- 点击文件可预览（图片/视频）或下载

### 存储设置
- 点击侧边栏的"存储设置"
- 可在本地存储和云存储之间切换
- 配置云存储参数后点击"测试连接"验证

---

## 🛠️ 维护操作

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose down
docker compose up -d --build
```

### 查看日志

```bash
# 实时日志
docker compose logs -f

# 查看最近100行
docker compose logs --tail=100

# 仅查看应用日志
docker compose logs -f solocloud
```

### 备份数据

```bash
# 使用备份脚本
./migrate.sh backup

# 或手动备份
tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/
```

---

## ❓ 常见问题

### 权限问题

```bash
# 如果遇到权限错误
chmod -R 777 logs data uploads

# 或设置正确的用户权限
chown -R 1000:1000 data/ uploads/ logs/
```

### 端口占用

```bash
# 检查端口占用
netstat -tlnp | grep :80

# 修改端口（编辑 .env）
HTTP_PORT=8080
HTTPS_PORT=8443
```

### Docker 命令格式

新版 Docker 使用 `docker compose`（中间有空格），而不是 `docker-compose`：

```bash
# 正确
docker compose up -d

# 错误（旧版本）
docker-compose up -d
```

---

## 🏗️ 项目结构

```
SoloCloud/
├── app.py                 # 主应用文件
├── cloud_storage.py       # 云存储管理
├── config.py             # 配置管理
├── logging_config.py     # 日志配置
├── error_handlers.py     # 错误处理
├── requirements.txt      # Python依赖
├── .env.example          # 环境变量示例
├── docker-compose.yml    # Docker编排（开发/通用）
├── docker-compose.prod.yml # Docker编排（生产）
├── Dockerfile           # Docker镜像
├── nginx.conf          # Nginx配置
├── ssl_setup.sh        # SSL证书安装脚本
├── ssl_renewal.sh      # SSL证书续期脚本
├── migrate.sh          # 数据迁移脚本
├── templates/          # HTML模板
│   ├── index.html     # 主页面
│   ├── storage_settings.html # 存储设置
│   ├── login.html     # 登录页面
│   └── errors/        # 错误页面
├── static/            # 静态资源
│   └── app.js         # 前端脚本
├── uploads/           # 上传文件目录
├── data/              # 数据库目录
├── logs/              # 日志目录
└── ssl/               # SSL证书目录
```

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Bootstrap](https://getbootstrap.com/) - 前端 UI 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python ORM
- [Docker](https://www.docker.com/) - 容器化平台
- [Nginx](https://nginx.org/) - Web服务器
- 各云存储服务提供商的 API 支持

---

## 📧 支持

如有问题，请提交 [Issue](https://github.com/HoseaDev/SoloCloud/issues) 或联系维护团队。
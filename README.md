# 🌤️ SoloCloud

一个简洁实用的**个人云存储系统**，支持文件管理、笔记记录、随心记录等功能，专为个人使用设计。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg)

## ✨ 主要功能

### 📁 文件管理
- **文件上传**: 支持拖拽上传，显示上传进度
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
- **腾讯云 COS**: 支持腾讯云对象存储(未测试)
- **七牛云**: 支持七牛云存储(未测试)
- **坚果云**: 支持WebDAV协议访问坚果云(未测试)
- **存储设置**: 可在Web界面中配置和切换存储后端

### 🔒 安全特性
- **单用户系统**: 专为个人使用设计，系统只允许一个用户账号
- **登录保护**: 防止暴力破解，多次失败后会临时封禁IP
- **会话管理**: 安全的用户会话管理

### 📱 响应式设计
- **移动适配**: 支持手机和平板访问
- **现代界面**: 基于Bootstrap 5的清洁界面
- **多视图模式**: 文件支持网格和列表两种显示模式

## 🛠️ 技术栈

- **后端**: Python 3.11+ + Flask 2.3+ + SQLAlchemy
- **数据库**: SQLite（默认）
- **前端**: Bootstrap 5 + 原生 JavaScript
- **文件处理**: Pillow + OpenCV（缩略图生成）
- **云存储**: 支持阿里云OSS、腾讯云COS、七牛云、坚果云
- **部署**: 支持Docker和传统部署

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/solocloud.git
cd solocloud

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 SECRET_KEY 等配置

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
open http://localhost:8080
```

### 方式二：传统部署

```bash
# 1. 环境要求
# Python 3.11+, pip, virtualenv

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑配置文件
```

### 🔧 环境配置

#### 基础配置（必需）
```bash
# 应用安全配置
SECRET_KEY=af0705d30f1be97c76c6299c5eced10e3787d7d9a64a5cadfad88b4d75a400db
FLASK_ENV=production

# 数据库配置
DATABASE_URL=sqlite:///data/solocloud.db

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/solocloud.log
```

#### 存储后端配置（可选）

<details>
<summary>📁 本地存储（默认）</summary>

```bash
STORAGE_PROVIDER=local
UPLOAD_FOLDER=uploads
```
</details>

<details>
<summary>☁️ 阿里云 OSS</summary>

```bash
STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ACCESS_KEY_ID=your-access-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET_NAME=your-bucket-name
```
</details>

<details>
<summary>☁️ 腾讯云 COS</summary>

```bash
STORAGE_PROVIDER=tencent_cos
TENCENT_COS_SECRET_ID=your-secret-id
TENCENT_COS_SECRET_KEY=your-secret-key
TENCENT_COS_REGION=ap-beijing
TENCENT_COS_BUCKET_NAME=your-bucket-name
```
</details>

<details>
<summary>☁️ 七牛云</summary>

```bash
STORAGE_PROVIDER=qiniu
QINIU_ACCESS_KEY=your-access-key
QINIU_SECRET_KEY=your-secret-key
QINIU_BUCKET_NAME=your-bucket-name
QINIU_DOMAIN=your-domain.com
```
</details>

<details>
<summary>☁️ 坚果云 WebDAV</summary>

```bash
STORAGE_PROVIDER=jianguoyun
JIANGUOYUN_WEBDAV_URL=https://dav.jianguoyun.com/dav
JIANGUOYUN_USERNAME=your-username
JIANGUOYUN_PASSWORD=your-app-password
```
</details>

### 🚀 启动应用

#### 开发环境
```bash
# 开发模式启动
FLASK_ENV=development python app.py

# 或使用Flask命令
flask run --host=0.0.0.0 --port=8080
```

#### 生产环境
```bash
# 使用Gunicorn启动
gunicorn --config gunicorn.conf.py app:app

# 或使用启动脚本
chmod +x start.sh
./start.sh

# 使用systemd管理（Linux）
sudo systemctl start solocloud
```

---

## 🏗️ 生产环境部署

### Docker部署（推荐）
```bash
# 使用Docker Compose
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 生产环境部署
详细的部署指南请参考：[DEPLOYMENT.md](DEPLOYMENT.md)

包含Docker部署、systemd服务配置、Nginx配置等内容。

---

## 🔧 项目结构

```
SoloCloud/
├── app.py                 # 主应用文件
├── cloud_storage.py       # 云存储管理
├── config.py             # 配置管理
├── logging_config.py     # 日志配置
├── error_handlers.py     # 错误处理
├── requirements.txt      # Python依赖
├── .env.example          # 环境变量示例
├── templates/            # HTML模板
│   ├── index.html       # 主页面
│   ├── storage_settings.html # 存储设置
│   ├── login.html       # 登录页面
│   └── errors/          # 错误页面
├── static/              # 静态资源
│   └── app.js           # 前端脚本
├── uploads/             # 本地上传目录
├── logs/                # 日志文件
├── docker-compose.yml   # Docker编排
└── Dockerfile          # Docker镜像
```

## 📝 使用说明

### 首次使用
1. 启动应用后，访问 `http://localhost:8080`
2. 系统会自动跳转到首次设置页面
3. 创建管理员账号（用户名和密码）
4. 登录后即可使用所有功能

### 文件管理
- 拖拽文件到上传区域或点击选择文件
- 支持批量上传，显示上传进度
- 点击文件可预览（图片/视频）或下载
- 可生成分享链接，设置过期时间

### 存储设置
- 点击侧边栏的“存储设置”
- 可在本地存储和云存储之间切换
- 配置云存储参数后点击“测试连接”验证

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Bootstrap](https://getbootstrap.com/) - 前端 UI 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python ORM
- 各云存储服务提供商的 API 支持
OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your-bucket-name
```

### 4. 运行应用
```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 使用说明

### 文件上传
1. 点击侧边栏的"上传文件"
2. 选择存储方式（本地存储或阿里云OSS）
3. 拖拽文件到上传区域或点击选择文件
4. 可选填写文件描述
5. 文件将自动上传并显示进度

### 文件管理
- **查看文件**: 在文件管理页面浏览所有文件
- **预览文件**: 点击预览按钮查看图片和视频
- **下载文件**: 点击下载按钮下载文件
- **删除文件**: 点击删除按钮移除文件
- **筛选文件**: 使用左侧筛选器按类型查看文件

### 笔记管理
1. 点击侧边栏的"笔记"
2. 点击"新建笔记"创建笔记
3. 填写标题、内容和标签
4. 保存后可以编辑或删除笔记

## 项目结构

```
SoloCloud/
├── app.py              # 主应用文件
├── requirements.txt    # Python依赖
├── .env.example       # 环境变量示例
├── README.md          # 项目说明
├── templates/         # HTML模板
│   └── index.html     # 主页面
├── static/            # 静态资源
│   └── app.js         # 前端JavaScript
└── uploads/           # 本地文件存储目录（自动创建）
    ├── images/        # 图片文件
    ├── videos/        # 视频文件
    ├── files/         # 其他文件
    └── thumbnails/    # 缩略图
```

## API接口

### 文件相关
- `POST /api/upload` - 上传文件
- `GET /api/files` - 获取文件列表
- `GET /api/files/<id>` - 下载文件
- `GET /api/files/<id>/thumbnail` - 获取缩略图
- `DELETE /api/files/<id>` - 删除文件

### 笔记相关
- `GET /api/notes` - 获取笔记列表
- `POST /api/notes` - 创建笔记
- `GET /api/notes/<id>` - 获取笔记详情
- `PUT /api/notes/<id>` - 更新笔记
- `DELETE /api/notes/<id>` - 删除笔记

## 注意事项

1. **文件大小限制**: 默认最大上传文件大小为1GB
2. **OSS配置**: 如果不配置阿里云OSS，只能使用本地存储
3. **数据库**: 默认使用SQLite，数据存储在 `solocloud.db` 文件中
4. **安全性**: 生产环境请修改SECRET_KEY并使用HTTPS

## 扩展功能

可以考虑添加的功能：
- 用户认证和权限管理
- 文件分享功能
- 全文搜索
- 文件版本管理
- 批量操作
- 移动端适配

## 许可证

MIT License

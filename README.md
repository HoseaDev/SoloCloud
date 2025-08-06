# SoloCloud - 个人云存储系统

一个功能完整的个人云存储系统，支持图片、视频、文档存储，在线预览，笔记管理，以及本地存储和阿里云OSS双重存储方案。

## 功能特性

### 📁 文件管理
- **多格式支持**: 图片(PNG, JPG, JPEG, GIF)、视频(MP4, AVI, MOV, WMV, FLV)、文档(PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT)
- **在线预览**: 图片和视频支持在线预览
- **双重存储**: 支持本地存储和阿里云OSS存储
- **缩略图生成**: 自动为图片生成缩略图
- **文件管理**: 上传、下载、删除、查看文件信息

### 📝 笔记系统
- **富文本笔记**: 创建、编辑、删除笔记
- **标签管理**: 支持为笔记添加标签
- **时间记录**: 自动记录创建和更新时间

### 🎨 用户界面
- **现代化设计**: 基于Bootstrap 5的响应式界面
- **多视图模式**: 支持网格和列表两种文件显示模式
- **拖拽上传**: 支持拖拽文件上传
- **分页显示**: 文件和笔记支持分页浏览

## 技术栈

- **后端**: Python Flask + SQLAlchemy
- **前端**: HTML5 + Bootstrap 5 + JavaScript
- **数据库**: SQLite
- **云存储**: 阿里云OSS
- **图片处理**: Pillow

## 安装和运行

### 1. 环境要求
- Python 3.7+
- pip

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
复制 `.env.example` 为 `.env` 并填入相应配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
# Flask配置
SECRET_KEY=your-secret-key-here

# 阿里云OSS配置（可选，如果只使用本地存储可以不配置）
OSS_ACCESS_KEY_ID=your-oss-access-key-id
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

1. **文件大小限制**: 默认最大上传文件大小为100MB
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

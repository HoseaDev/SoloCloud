FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash SoloCloud

# 创建必要的目录并设置权限
RUN mkdir -p logs uploads data \
    && mkdir -p uploads/images uploads/videos uploads/audio uploads/files uploads/archives uploads/code uploads/thumbnails uploads/chat uploads/chat_thumbnails \
    && chmod +x start.sh \
    && chown -R SoloCloud:SoloCloud /app \
    && chmod -R 755 /app/logs /app/uploads /app/data

# 切换到非root用户
USER SoloCloud

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令 - 使用初始化脚本
CMD ["sh", "-c", "python3 docker-init.py && exec ./start.sh"]

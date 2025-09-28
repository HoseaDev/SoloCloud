# 多阶段构建 - 构建阶段
FROM python:3.11-slim-bookworm as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖（强制使用 IPv4）
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# 运行阶段
FROM python:3.11-slim-bookworm

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# 安装运行时依赖（强制使用 IPv4）
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r solocloud && useradd -r -g solocloud solocloud

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY --chown=solocloud:solocloud . .

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/uploads /app/data \
    && chown -R solocloud:solocloud /app \
    && chmod 755 /app /app/logs /app/uploads /app/data

# 切换到非root用户（暂时禁用，以root运行）
# USER solocloud

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8080/health || exit 1

# 启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
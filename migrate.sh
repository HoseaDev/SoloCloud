#!/bin/bash

# SoloCloud 数据迁移脚本
# 用法: ./migrate.sh [backup|restore|export|docker-to-local|local-to-docker]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份
backup_data() {
    log_info "开始备份数据..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/solocloud_backup_$TIMESTAMP.tar.gz"
    
    # 检查数据目录是否存在
    if [[ ! -d "data" ]]; then
        log_warning "data目录不存在，创建空目录"
        mkdir -p data
    fi
    
    if [[ ! -d "uploads" ]]; then
        log_warning "uploads目录不存在，创建空目录"
        mkdir -p uploads
    fi
    
    if [[ ! -d "logs" ]]; then
        log_warning "logs目录不存在，创建空目录"
        mkdir -p logs
    fi
    
    # 打包数据
    tar -czf "$BACKUP_FILE" \
        data/ uploads/ logs/ \
        .env* *.py *.yml *.txt *.md *.sh \
        templates/ static/ \
        2>/dev/null || true
    
    log_success "备份完成: $BACKUP_FILE"
    echo "备份大小: $(du -h "$BACKUP_FILE" | cut -f1)"
}

# 恢复数据
restore_data() {
    if [[ -z "$2" ]]; then
        log_error "请指定备份文件路径"
        echo "用法: $0 restore <backup_file>"
        exit 1
    fi
    
    BACKUP_FILE="$2"
    
    if [[ ! -f "$BACKUP_FILE" ]]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi
    
    log_info "开始恢复数据从: $BACKUP_FILE"
    
    # 创建当前状态的备份
    log_info "创建当前状态备份..."
    backup_data
    
    # 恢复数据
    tar -xzf "$BACKUP_FILE"
    
    log_success "数据恢复完成"
}

# 导出用于迁移
export_for_migration() {
    log_info "准备迁移包..."
    
    mkdir -p "$BACKUP_DIR"
    EXPORT_FILE="$BACKUP_DIR/solocloud_migration_$TIMESTAMP.tar.gz"
    
    # 停止服务（如果在运行）
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps | grep -q "Up"; then
            log_info "停止Docker服务..."
            docker-compose down
        fi
    fi
    
    # 打包完整项目
    tar -czf "$EXPORT_FILE" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='backups' \
        . 2>/dev/null || true
    
    log_success "迁移包已创建: $EXPORT_FILE"
    echo "包大小: $(du -h "$EXPORT_FILE" | cut -f1)"
    echo ""
    echo "迁移步骤:"
    echo "1. 将此文件传输到目标机器"
    echo "2. 在目标机器上解压: tar -xzf $(basename "$EXPORT_FILE")"
    echo "3. 运行相应的启动命令"
}

# Docker转本地运行
docker_to_local() {
    log_info "从Docker迁移到本地运行..."
    
    # 停止Docker容器
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps | grep -q "Up"; then
            log_info "停止Docker容器..."
            docker-compose down
        fi
    fi
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请先安装Python"
        exit 1
    fi
    
    # 安装依赖
    if [[ -f "requirements.txt" ]]; then
        log_info "安装Python依赖..."
        pip3 install -r requirements.txt
    fi
    
    # 创建必要目录
    mkdir -p data uploads logs
    
    log_success "迁移完成，可以使用 'python3 app.py' 启动"
}

# 本地转Docker运行
local_to_docker() {
    log_info "从本地运行迁移到Docker..."
    
    # 检查Docker环境
    if ! command -v docker &> /dev/null; then
        log_error "未找到Docker，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "未找到docker-compose，请先安装"
        exit 1
    fi
    
    # 停止可能运行的Python进程
    log_info "检查并停止Python进程..."
    pkill -f "python.*app.py" || true
    
    # 确保数据目录存在
    mkdir -p data uploads logs
    
    # 构建并启动Docker
    log_info "构建Docker镜像..."
    docker-compose build
    
    log_info "启动Docker容器..."
    docker-compose up -d
    
    log_success "迁移完成，Docker容器已启动"
    echo "使用 'docker-compose logs -f' 查看日志"
}

# 显示帮助
show_help() {
    echo "SoloCloud 数据迁移工具"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  backup              - 创建数据备份"
    echo "  restore <file>      - 从备份文件恢复数据"
    echo "  export              - 创建迁移包（用于跨机器迁移）"
    echo "  docker-to-local     - 从Docker迁移到本地Python运行"
    echo "  local-to-docker     - 从本地Python迁移到Docker运行"
    echo "  help                - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 backup"
    echo "  $0 restore backups/solocloud_backup_20240808_104925.tar.gz"
    echo "  $0 export"
    echo "  $0 docker-to-local"
    echo "  $0 local-to-docker"
}

# 主逻辑
case "${1:-help}" in
    backup)
        backup_data
        ;;
    restore)
        restore_data "$@"
        ;;
    export)
        export_for_migration
        ;;
    docker-to-local)
        docker_to_local
        ;;
    local-to-docker)
        local_to_docker
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac

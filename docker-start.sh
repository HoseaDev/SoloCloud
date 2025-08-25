#!/bin/bash

# SoloCloud Docker 启动脚本
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 .env 文件
check_env_file() {
    if [ ! -f .env ]; then
        print_warn ".env 文件不存在，正在从模板创建..."
        cp .env.example .env
        print_info "已创建 .env 文件，请编辑配置后重新运行"
        print_info "编辑命令: nano .env 或 vim .env"
        exit 1
    fi
}

# 检查 SECRET_KEY
check_secret_key() {
    if grep -q "your-secret-key-here-please-change-this" .env; then
        print_error "请修改 .env 中的 SECRET_KEY！"
        print_info "可以使用以下命令生成随机密钥:"
        echo "python -c 'import secrets; print(secrets.token_hex(32))'"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    # 从 .env 文件读取路径配置
    source .env
    
    # 创建数据目录
    mkdir -p ${DATA_PATH:-./data}
    mkdir -p ${UPLOADS_PATH:-./uploads}
    mkdir -p ${LOGS_PATH:-./logs}
    mkdir -p ${SSL_PATH:-./ssl}
    mkdir -p ${NGINX_LOGS_PATH:-./logs/nginx}
    
    # 创建上传子目录
    for subdir in images videos audio files archives code thumbnails chat chat_thumbnails; do
        mkdir -p ${UPLOADS_PATH:-./uploads}/$subdir
    done
    
    print_info "目录创建完成"
}

# 构建镜像
build_image() {
    print_info "构建 Docker 镜像..."
    docker-compose build --no-cache
    print_info "镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    docker-compose up -d
    print_info "服务启动完成"
}

# 检查服务状态
check_services() {
    print_info "检查服务状态..."
    sleep 5
    
    if docker-compose ps | grep -q "Up"; then
        print_info "服务运行正常"
        
        # 获取端口配置
        source .env
        HTTP_PORT=${HTTP_PORT:-80}
        HTTPS_PORT=${HTTPS_PORT:-443}
        APP_PORT=${APP_PORT:-8080}
        
        echo ""
        print_info "==================================="
        print_info "SoloCloud 已成功启动！"
        print_info "==================================="
        print_info "访问地址:"
        print_info "  HTTP:  http://localhost:${HTTP_PORT}"
        if [ -f "${SSL_PATH:-./ssl}/server.crt" ]; then
            print_info "  HTTPS: https://localhost:${HTTPS_PORT}"
        fi
        print_info "  直接访问: http://localhost:${APP_PORT}"
        print_info ""
        print_info "查看日志: docker-compose logs -f"
        print_info "停止服务: docker-compose down"
        print_info "==================================="
    else
        print_error "服务启动失败，请检查日志"
        docker-compose logs --tail=50
        exit 1
    fi
}

# 显示帮助
show_help() {
    echo "SoloCloud Docker 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start       启动所有服务（默认）"
    echo "  stop        停止所有服务"
    echo "  restart     重启所有服务"
    echo "  rebuild     重新构建并启动"
    echo "  logs        查看日志"
    echo "  status      查看服务状态"
    echo "  clean       清理所有容器和镜像"
    echo "  help        显示此帮助信息"
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            check_env_file
            check_secret_key
            create_directories
            start_services
            check_services
            ;;
        stop)
            print_info "停止服务..."
            docker-compose down
            print_info "服务已停止"
            ;;
        restart)
            print_info "重启服务..."
            docker-compose restart
            print_info "服务已重启"
            ;;
        rebuild)
            check_env_file
            check_secret_key
            create_directories
            build_image
            start_services
            check_services
            ;;
        logs)
            docker-compose logs -f
            ;;
        status)
            docker-compose ps
            ;;
        clean)
            print_warn "清理所有容器和镜像..."
            docker-compose down -v --rmi all
            print_info "清理完成"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
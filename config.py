import os
from datetime import timedelta

def is_docker():
    """简单检测是否在Docker中运行"""
    return os.path.exists('/.dockerenv')

class Config:
    """统一配置 - 自动适应环境"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置 - 环境变量优先，否则自动检测
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        'sqlite:////app/data/SoloCloud.db' if is_docker() else f'sqlite:///{os.path.abspath("data/SoloCloud.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max file size
    
    # 上传配置 - 环境变量优先，否则自动检测
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or (
        '/app/uploads' if is_docker() else 'uploads'
    )
    
    # 存储配置
    STORAGE_PROVIDER = os.environ.get('STORAGE_PROVIDER') or 'local'
    
    # 会话配置 - 自动适应HTTP/HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # SESSION_COOKIE_SECURE 将在运行时根据实际协议设置
    
    # 调试模式 - 通过环境变量控制
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'yes']
    TESTING = os.environ.get('TESTING', 'False').lower() in ['true', '1', 'yes']
    
    # 日志配置 - 环境变量优先，否则自动检测
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or ('DEBUG' if DEBUG else 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE') or (
        '/app/logs/SoloCloud.log' if is_docker() else 'logs/SoloCloud.log'
    )
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

# 为了向后兼容，保留原有的配置映射
class DevelopmentConfig(Config):
    """开发环境配置（向后兼容）"""
    pass

class ProductionConfig(Config):
    """生产环境配置（向后兼容）"""
    pass

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 配置映射
config = {
    'development': Config,  # 现在都使用统一的Config
    'production': Config,   # 现在都使用统一的Config
    'testing': TestingConfig,
    'default': Config
}
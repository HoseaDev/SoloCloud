import os
from datetime import timedelta

def is_docker():
    """简单检测是否在Docker中运行"""
    return os.path.exists('/.dockerenv')

class Config:
    """基础配置 - 自动检测环境，优先使用环境变量"""
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
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # 开发环境
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 日志配置 - 环境变量优先，否则自动检测
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or (
        '/app/logs/SoloCloud.log' if is_docker() else 'logs/SoloCloud.log'
    )
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置 - 继承基础配置的自动适应能力"""
    DEBUG = False
    TESTING = False
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # 生产环境日志级别（路径继承自基础配置）
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

import logging
import logging.handlers
import os
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'action'):
            log_entry['action'] = record.action
            
        return json.dumps(log_entry, ensure_ascii=False)

class SoloCloudLogger:
    """SoloCloud专用日志管理器"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化日志系统"""
        # 创建日志目录
        log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/SoloCloud.log'))
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置根日志级别
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
        
        # 清除现有处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        detailed_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        )
        json_formatter = JSONFormatter()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        
        # 文件处理器（详细日志）
        file_handler = logging.handlers.RotatingFileHandler(
            app.config.get('LOG_FILE', 'logs/SoloCloud.log'),
            maxBytes=app.config.get('LOG_MAX_BYTES', 10*1024*1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        
        # JSON日志处理器（结构化日志）
        json_log_file = app.config.get('LOG_FILE', 'logs/SoloCloud.log').replace('.log', '.json')
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10*1024*1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        json_handler.setLevel(log_level)
        json_handler.setFormatter(json_formatter)
        
        # 错误日志处理器
        error_log_file = app.config.get('LOG_FILE', 'logs/SoloCloud.log').replace('.log', '_error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10*1024*1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # 安全日志处理器
        security_log_file = app.config.get('LOG_FILE', 'logs/SoloCloud.log').replace('.log', '_security.log')
        security_handler = logging.handlers.RotatingFileHandler(
            security_log_file,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10*1024*1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(detailed_formatter)
        
        # 配置应用日志记录器
        app_logger = logging.getLogger('SoloCloud')
        app_logger.setLevel(log_level)
        app_logger.addHandler(console_handler)
        app_logger.addHandler(file_handler)
        app_logger.addHandler(json_handler)
        app_logger.addHandler(error_handler)
        
        # 配置安全日志记录器
        security_logger = logging.getLogger('SoloCloud.security')
        security_logger.setLevel(logging.WARNING)
        security_logger.addHandler(security_handler)
        security_logger.addHandler(console_handler)
        
        # 配置Flask日志
        app.logger.handlers = []
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(log_level)
        
        # 配置Werkzeug日志
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.WARNING)
        
        app.logger.info("日志系统初始化完成")

def get_logger(name='SoloCloud'):
    """获取日志记录器"""
    return logging.getLogger(name)

def log_user_action(action, user_id=None, ip_address=None, details=None):
    """记录用户操作"""
    logger = get_logger('SoloCloud.user_action')
    extra = {
        'action': action,
        'user_id': user_id,
        'ip_address': ip_address
    }
    message = f"用户操作: {action}"
    if details:
        message += f" - {details}"
    logger.info(message, extra=extra)

def log_security_event(event, ip_address=None, details=None, level='warning'):
    """记录安全事件"""
    logger = get_logger('SoloCloud.security')
    extra = {
        'action': 'security_event',
        'ip_address': ip_address
    }
    message = f"安全事件: {event}"
    if details:
        message += f" - {details}"
    
    log_func = getattr(logger, level.lower(), logger.warning)
    log_func(message, extra=extra)

def log_system_event(event, details=None):
    """记录系统事件"""
    logger = get_logger('SoloCloud.system')
    message = f"系统事件: {event}"
    if details:
        message += f" - {details}"
    logger.info(message)

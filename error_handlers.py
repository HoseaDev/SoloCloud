from flask import render_template, request, jsonify, current_app
import logging
import traceback
from datetime import datetime
import uuid

def init_error_handlers(app):
    """初始化全局错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """400 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Bad Request")
        
        if request.is_json:
            return jsonify({
                'error': 'Bad Request',
                'message': '请求格式错误',
                'error_id': error_id
            }), 400
        
        return render_template('errors/400.html', 
                             error_id=error_id,
                             message='请求格式错误'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Unauthorized")
        
        if request.is_json:
            return jsonify({
                'error': 'Unauthorized',
                'message': '需要登录访问',
                'error_id': error_id
            }), 401
        
        return render_template('errors/401.html',
                             error_id=error_id,
                             message='需要登录访问'), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Forbidden")
        
        if request.is_json:
            return jsonify({
                'error': 'Forbidden',
                'message': '没有访问权限',
                'error_id': error_id
            }), 403
        
        return render_template('errors/403.html',
                             error_id=error_id,
                             message='没有访问权限'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """404 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Not Found")
        
        if request.is_json:
            return jsonify({
                'error': 'Not Found',
                'message': '请求的资源不存在',
                'error_id': error_id
            }), 404
        
        return render_template('errors/404.html',
                             error_id=error_id,
                             message='请求的页面不存在'), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """413 错误处理 - 文件过大"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Request Entity Too Large")
        
        if request.is_json:
            return jsonify({
                'error': 'File Too Large',
                'message': '上传文件过大，请选择较小的文件',
                'error_id': error_id
            }), 413
        
        return render_template('errors/413.html',
                             error_id=error_id,
                             message='上传文件过大，请选择较小的文件'), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """429 错误处理 - 请求过于频繁"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Rate Limit Exceeded")
        
        if request.is_json:
            return jsonify({
                'error': 'Rate Limit Exceeded',
                'message': '请求过于频繁，请稍后再试',
                'error_id': error_id
            }), 429
        
        return render_template('errors/429.html',
                             error_id=error_id,
                             message='请求过于频繁，请稍后再试'), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """500 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Internal Server Error")
        
        if request.is_json:
            return jsonify({
                'error': 'Internal Server Error',
                'message': '服务器内部错误',
                'error_id': error_id
            }), 500
        
        return render_template('errors/500.html',
                             error_id=error_id,
                             message='服务器内部错误'), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        """502 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Bad Gateway")
        
        if request.is_json:
            return jsonify({
                'error': 'Bad Gateway',
                'message': '网关错误',
                'error_id': error_id
            }), 502
        
        return render_template('errors/502.html',
                             error_id=error_id,
                             message='网关错误'), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """503 错误处理"""
        error_id = str(uuid.uuid4())[:8]
        log_error(error, error_id, "Service Unavailable")
        
        if request.is_json:
            return jsonify({
                'error': 'Service Unavailable',
                'message': '服务暂时不可用',
                'error_id': error_id
            }), 503
        
        return render_template('errors/503.html',
                             error_id=error_id,
                             message='服务暂时不可用'), 503
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理所有未捕获的异常"""
        error_id = str(uuid.uuid4())[:8]
        
        # 记录详细错误信息
        logger = logging.getLogger('SoloCloud.error')
        logger.error(f"未处理异常 [{error_id}]: {str(error)}", extra={
            'error_id': error_id,
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'url': request.url,
            'method': request.method,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # 如果是开发环境，重新抛出异常以显示调试信息
        if current_app.debug:
            raise error
        
        if request.is_json:
            return jsonify({
                'error': 'Internal Server Error',
                'message': '服务器内部错误',
                'error_id': error_id
            }), 500
        
        return render_template('errors/500.html',
                             error_id=error_id,
                             message='服务器内部错误'), 500

def log_error(error, error_id, error_type):
    """记录错误信息"""
    logger = logging.getLogger('SoloCloud.error')
    logger.error(f"{error_type} [{error_id}]: {str(error)}", extra={
        'error_id': error_id,
        'error_type': error_type,
        'url': request.url,
        'method': request.method,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'timestamp': datetime.utcnow().isoformat()
    })

class SoloCloudException(Exception):
    """SoloCloud自定义异常基类"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

class ValidationError(SoloCloudException):
    """验证错误"""
    def __init__(self, message, payload=None):
        super().__init__(message, 400, payload)

class AuthenticationError(SoloCloudException):
    """认证错误"""
    def __init__(self, message, payload=None):
        super().__init__(message, 401, payload)

class AuthorizationError(SoloCloudException):
    """授权错误"""
    def __init__(self, message, payload=None):
        super().__init__(message, 403, payload)

class ResourceNotFoundError(SoloCloudException):
    """资源不存在错误"""
    def __init__(self, message, payload=None):
        super().__init__(message, 404, payload)

class RateLimitError(SoloCloudException):
    """频率限制错误"""
    def __init__(self, message, payload=None):
        super().__init__(message, 429, payload)

class StorageError(SoloCloudException):
    """存储错误"""
    def __init__(self, message, payload=None):
        super().__init__(message, 500, payload)

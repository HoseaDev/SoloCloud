from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime, timedelta
import cv2
import numpy as np
from PIL import Image
import oss2
from dotenv import load_dotenv
import mimetypes
import jwt
import secrets

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solocloud.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录访问此页面'

# 本地存储配置
UPLOAD_FOLDER = 'uploads'
# 移除文件格式限制，允许上传任何类型的文件
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

# 阿里云OSS配置
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')

# 初始化数据库
db = SQLAlchemy(app)

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'files'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'thumbnails'), exist_ok=True)

# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MediaFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, video, document
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    storage_type = db.Column(db.String(20), nullable=False)  # local, oss
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('files', lazy=True))

class ShareLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('media_file.id'), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    access_count = db.Column(db.Integer, default=0)
    max_access = db.Column(db.Integer, default=0)  # 0表示无限制
    is_active = db.Column(db.Boolean, default=True)
    
    file = db.relationship('MediaFile', backref=db.backref('share_links', lazy=True))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.String(500))  # 用逗号分隔的标签
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('notes', lazy=True))

class ChatMessage(db.Model):
    """聊天记录模型 - 类似微信对话的个人记录"""
    id = db.Column(db.Integer, primary_key=True)
    message_type = db.Column(db.String(20), nullable=False)  # text, image, video, file
    content = db.Column(db.Text)  # 文字内容（对于文字消息）
    file_path = db.Column(db.String(500))  # 文件路径（对于文件消息）
    file_name = db.Column(db.String(255))  # 原始文件名
    file_size = db.Column(db.Integer)  # 文件大小
    thumbnail_path = db.Column(db.String(500))  # 缩略图路径（对于图片/视频）
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('chat_messages', lazy=True))

# Flask-Login用户加载器
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 工具函数
def allowed_file(filename):
    # 允许上传任何类型的文件，只要有文件名即可
    return filename and filename.strip() != ''

def get_file_type(filename):
    # 处理没有扩展名的文件
    if '.' not in filename:
        return 'document'
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    # 图片类型
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'ico'}:
        return 'image'
    # 视频类型
    elif ext in {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', '3gp', 'ogv', 'm4v'}:
        return 'video'
    # 音频类型
    elif ext in {'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma'}:
        return 'audio'
    # 文档类型
    elif ext in {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt', 'ods', 'odp'}:
        return 'document'
    # 压缩文件
    elif ext in {'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'}:
        return 'archive'
    # 代码文件
    elif ext in {'py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'rs', 'swift'}:
        return 'code'
    # 其他类型统一归类为文档
    else:
        return 'document'

def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """为图片创建缩略图"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
        return True
    except Exception as e:
        print(f"创建图片缩略图失败: {e}")
        return False

def create_video_thumbnail(video_path, thumbnail_path, size=(200, 200)):
    """为视频创建缩略图（提取第一帧）"""
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return False
        
        # 读取第一帧
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"无法读取视频第一帧: {video_path}")
            return False
        
        # 将OpenCV的BGR格式转换为PIL的RGB格式
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # 创建缩略图
        pil_image.thumbnail(size, Image.Resampling.LANCZOS)
        pil_image.save(thumbnail_path, optimize=True, quality=85)
        
        return True
        
    except Exception as e:
        print(f"创建视频缩略图失败: {e}")
        return False

def upload_to_oss(file_path, object_name):
    """上传文件到阿里云OSS"""
    try:
        if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME]):
            return False, "OSS配置不完整"
        
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        
        result = bucket.put_object_from_file(object_name, file_path)
        return result.status == 200, result.request_id
    except Exception as e:
        return False, str(e)

# 路由
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            return render_template('login.html', error='用户名和密码不能为空')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'message': '登录成功', 'redirect': url_for('index')})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'error': '用户名或密码错误'}), 401
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            if request.is_json:
                return jsonify({'error': '所有字段都是必填的'}), 400
            return render_template('register.html', error='所有字段都是必填的')
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'error': '用户名已存在'}), 400
            return render_template('register.html', error='用户名已存在')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'error': '邮箱已被注册'}), 400
            return render_template('register.html', error='邮箱已被注册')
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        if request.is_json:
            return jsonify({'message': '注册成功', 'redirect': url_for('index')})
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/storage-config')
@login_required
def get_storage_config():
    """获取当前存储配置信息"""
    # 这里可以从配置文件或环境变量读取
    # 目前返回默认配置
    config = {
        'current_storage': 'local',
        'storage_name': '本地存储',
        'storage_icon': 'bi-hdd',
        'available_storages': [
            {'type': 'local', 'name': '本地存储', 'icon': 'bi-hdd'},
            {'type': 'oss', 'name': '阿里云OSS', 'icon': 'bi-cloud'}
        ]
    }
    
    # 检查是否配置了OSS
    if os.getenv('OSS_ACCESS_KEY_ID'):
        config['current_storage'] = 'oss'
        config['storage_name'] = '阿里云OSS'
        config['storage_icon'] = 'bi-cloud'
    
    return jsonify(config)

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    # 使用默认配置的存储方式（可以后续从配置文件读取）
    storage_type = 'local'  # 默认使用本地存储
    description = ''  # 移除文件描述功能
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        original_filename = secure_filename(file.filename)
        
        # 处理没有扩展名的文件
        if '.' in original_filename:
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        else:
            # 没有扩展名的文件，直接使用UUID作为文件名
            unique_filename = f"{uuid.uuid4().hex}"
        
        file_type = get_file_type(original_filename)
        
        # 根据文件类型确定存储路径
        if file_type == 'image':
            subfolder = 'images'
        elif file_type == 'video':
            subfolder = 'videos'
        elif file_type == 'audio':
            subfolder = 'audio'
        elif file_type == 'archive':
            subfolder = 'archives'
        elif file_type == 'code':
            subfolder = 'code'
        else:
            subfolder = 'files'
        
        local_path = os.path.join(UPLOAD_FOLDER, subfolder, unique_filename)
        
        # 保存文件到本地
        file.save(local_path)
        file_size = os.path.getsize(local_path)
        
        # 创建缩略图（对图片和视频）
        thumbnail_path = None
        if file_type == 'image':
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_path = os.path.join(UPLOAD_FOLDER, 'thumbnails', thumbnail_filename)
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            if create_thumbnail(local_path, thumbnail_path):
                print(f"图片缩略图创建成功: {thumbnail_path}")
            else:
                thumbnail_path = None
        elif file_type == 'video':
            # 为视频生成第一帧缩略图
            thumbnail_filename = f"thumb_{unique_filename.rsplit('.', 1)[0] if '.' in unique_filename else unique_filename}.jpg"
            thumbnail_path = os.path.join(UPLOAD_FOLDER, 'thumbnails', thumbnail_filename)
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            if create_video_thumbnail(local_path, thumbnail_path):
                print(f"视频缩略图创建成功: {thumbnail_path}")
            else:
                thumbnail_path = None
        
        final_path = local_path
        
        # 如果选择OSS存储，上传到OSS
        if storage_type == 'oss':
            oss_object_name = f"{subfolder}/{unique_filename}"
            success, result = upload_to_oss(local_path, oss_object_name)
            if success:
                final_path = oss_object_name
                # 可以选择删除本地文件以节省空间
                # os.remove(local_path)
            else:
                return jsonify({'error': f'OSS上传失败: {result}'}), 500
        
        # 保存到数据库
        media_file = MediaFile(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=file_type,
            mime_type=file.mimetype or mimetypes.guess_type(original_filename)[0] or 'application/octet-stream',
            file_size=file_size,
            storage_type=storage_type,
            file_path=final_path,
            thumbnail_path=thumbnail_path,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(media_file)
        db.session.commit()
        
        return jsonify({
            'message': '文件上传成功',
            'file_id': media_file.id,
            'filename': original_filename,
            'file_type': file_type,
            'storage_type': storage_type
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400

@app.route('/api/files')
@login_required
def list_files():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    file_type = request.args.get('type')  # image, video, document
    search = request.args.get('search', '').strip()  # 搜索关键词
    sort_by = request.args.get('sort_by', 'upload_time')  # 排序字段
    sort_order = request.args.get('sort_order', 'desc')  # 排序方向
    
    query = MediaFile.query.filter_by(user_id=current_user.id)
    
    # 文件类型筛选
    if file_type:
        query = query.filter_by(file_type=file_type)
    
    # 搜索功能
    if search:
        query = query.filter(MediaFile.original_filename.contains(search))
    
    # 排序功能
    if sort_by == 'filename':
        sort_column = MediaFile.original_filename
    elif sort_by == 'file_size':
        sort_column = MediaFile.file_size
    elif sort_by == 'file_type':
        sort_column = MediaFile.file_type
    else:  # 默认按上传时间排序
        sort_column = MediaFile.upload_time
    
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    files = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'files': [{
            'id': f.id,
            'filename': f.filename,
            'original_filename': f.original_filename,
            'file_type': f.file_type,
            'file_size': f.file_size,
            'storage_type': f.storage_type,
            'upload_time': f.upload_time.isoformat(),
            'description': f.description,
            'thumbnail_path': f.thumbnail_path,
            'has_thumbnail': f.thumbnail_path is not None
        } for f in files.items],
        'total': files.total,
        'pages': files.pages,
        'current_page': page
    })

@app.route('/api/files/<int:file_id>')
def get_file(file_id):
    media_file = MediaFile.query.get_or_404(file_id)
    
    if media_file.storage_type == 'local':
        return send_file(media_file.file_path)
    else:
        # 对于OSS存储的文件，返回下载URL
        # 这里需要根据实际情况实现OSS文件访问
        return jsonify({'error': 'OSS文件访问功能待实现'}), 501

@app.route('/api/thumbnail/<int:file_id>')
def get_thumbnail(file_id):
    media_file = MediaFile.query.get_or_404(file_id)
    
    if media_file.thumbnail_path and os.path.exists(media_file.thumbnail_path):
        return send_file(media_file.thumbnail_path)
    else:
        return jsonify({'error': '缩略图不存在'}), 404

@app.route('/api/files/<int:file_id>/thumbnail')
def get_file_thumbnail(file_id):
    # 兼容性API
    return get_thumbnail(file_id)

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    media_file = MediaFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    # 删除本地文件
    if media_file.storage_type == 'local' and os.path.exists(media_file.file_path):
        os.remove(media_file.file_path)
    
    # 删除缩略图
    if media_file.thumbnail_path and os.path.exists(media_file.thumbnail_path):
        os.remove(media_file.thumbnail_path)
    
    # 从数据库删除记录
    db.session.delete(media_file)
    db.session.commit()
    
    return jsonify({'message': '文件删除成功'})

# 文件分享功能
@app.route('/api/files/<int:file_id>/share', methods=['POST'])
@login_required
def create_share_link(file_id):
    media_file = MediaFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json() or {}
    expires_hours = data.get('expires_hours', 168)  # 默认7天
    max_access = data.get('max_access', 0)  # 默认无限制
    
    # 生成唯一的分享令牌
    token = secrets.token_urlsafe(32)
    
    # 处理永久分享链接（expires_hours=0表示永久）
    if expires_hours == 0:
        expires_at = datetime(2099, 12, 31, 23, 59, 59)  # 设置为远未来日期表示永久
    else:
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    share_link = ShareLink(
        token=token,
        file_id=file_id,
        expires_at=expires_at,
        max_access=max_access
    )
    
    db.session.add(share_link)
    db.session.commit()
    
    share_url = url_for('shared_file', token=token, _external=True)
    
    return jsonify({
        'message': '分享链接创建成功',
        'share_url': share_url,
        'token': token,
        'expires_at': expires_at.isoformat() if expires_hours != 0 else 'permanent',
        'expires_hours': expires_hours,
        'is_permanent': expires_hours == 0,
        'max_access': max_access
    })

@app.route('/api/files/<int:file_id>/shares')
@login_required
def list_share_links(file_id):
    media_file = MediaFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    shares = ShareLink.query.filter_by(file_id=file_id, is_active=True).all()
    
    return jsonify({
        'shares': [{
            'id': s.id,
            'token': s.token,
            'share_url': url_for('shared_file', token=s.token, _external=True),
            'created_time': s.created_time.isoformat(),
            'expires_at': s.expires_at.isoformat(),
            'access_count': s.access_count,
            'max_access': s.max_access,
            'is_expired': s.expires_at < datetime.utcnow()
        } for s in shares]
    })

@app.route('/api/shares/<int:share_id>', methods=['DELETE'])
@login_required
def delete_share_link(share_id):
    share_link = ShareLink.query.get_or_404(share_id)
    
    # 确保只有文件所有者可以删除分享链接
    if share_link.file.user_id != current_user.id:
        return jsonify({'error': '无权限删除此分享链接'}), 403
    
    share_link.is_active = False
    db.session.commit()
    
    return jsonify({'message': '分享链接已删除'})

@app.route('/shared/<token>')
def shared_file(token):
    share_link = ShareLink.query.filter_by(token=token, is_active=True).first_or_404()
    
    # 检查链接是否过期
    if share_link.expires_at < datetime.utcnow():
        return render_template('error.html', error='分享链接已过期'), 410
    
    # 检查访问次数限制
    if share_link.max_access > 0 and share_link.access_count >= share_link.max_access:
        return render_template('error.html', error='分享链接访问次数已达上限'), 410
    
    # 增加访问次数
    share_link.access_count += 1
    db.session.commit()
    
    media_file = share_link.file
    
    # 如果是图片或视频，直接返回文件
    if media_file.file_type in ['image', 'video']:
        if media_file.storage_type == 'local':
            return send_file(media_file.file_path)
        else:
            # 对于OSS文件，这里需要实现OSS文件访问
            return jsonify({'error': 'OSS文件访问功能待实现'}), 501
    else:
        # 对于其他文件类型，显示下载页面
        return render_template('shared_file.html', file=media_file, share_link=share_link)

# 笔记相关路由
@app.route('/api/notes', methods=['GET'])
@login_required
def list_notes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'notes': [{
            'id': n.id,
            'title': n.title,
            'content': n.content[:200] + '...' if len(n.content) > 200 else n.content,
            'created_time': n.created_time.isoformat(),
            'updated_time': n.updated_time.isoformat(),
            'tags': n.tags.split(',') if n.tags else []
        } for n in notes.items],
        'total': notes.total,
        'pages': notes.pages,
        'current_page': page
    })

@app.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    note = Note(
        title=data['title'],
        content=data['content'],
        tags=','.join(data.get('tags', [])),
        user_id=current_user.id
    )
    
    db.session.add(note)
    db.session.commit()
    
    return jsonify({
        'message': '笔记创建成功',
        'note_id': note.id
    })

@app.route('/api/notes/<int:note_id>')
@login_required
def get_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    
    return jsonify({
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'created_time': note.created_time.isoformat(),
        'updated_time': note.updated_time.isoformat(),
        'tags': note.tags.split(',') if note.tags else []
    })

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的数据'}), 400
    
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.tags = ','.join(data.get('tags', []))
    note.updated_time = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': '笔记更新成功'})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'message': '笔记删除成功'})

# 聊天记录模块 API
@app.route('/api/chat/messages')
@login_required
def get_chat_messages():
    """获取聊天记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
        ChatMessage.created_time.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'messages': [{
            'id': m.id,
            'message_type': m.message_type,
            'content': m.content,
            'file_name': m.file_name,
            'file_size': m.file_size,
            'file_path': m.file_path,
            'thumbnail_path': m.thumbnail_path,
            'created_time': m.created_time.isoformat()
        } for m in messages.items],
        'total': messages.total,
        'pages': messages.pages,
        'current_page': page
    })

@app.route('/api/chat/messages', methods=['POST'])
@login_required
def create_chat_message():
    """创建聊天记录消息"""
    # 处理文字消息
    if request.content_type and 'application/json' in request.content_type:
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'error': '消息内容不能为空'}), 400
        
        message = ChatMessage(
            message_type='text',
            content=data['content'],
            user_id=current_user.id
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': '消息发送成功',
            'chat_message': {
                'id': message.id,
                'message_type': message.message_type,
                'content': message.content,
                'created_time': message.created_time.isoformat()
            }
        })
    
    # 处理文件消息
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 生成唯一文件名
            original_filename = secure_filename(file.filename)
            
            # 处理没有扩展名的文件
            if '.' in original_filename:
                file_ext = original_filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            else:
                unique_filename = f"{uuid.uuid4().hex}"
            
            file_type = get_file_type(original_filename)
            
            # 聊天文件存储在独立的目录中
            chat_folder = os.path.join(UPLOAD_FOLDER, 'chat')
            os.makedirs(chat_folder, exist_ok=True)
            
            local_path = os.path.join(chat_folder, unique_filename)
            file.save(local_path)
            file_size = os.path.getsize(local_path)
            
            # 创建缩略图（对于图片和视频）
            thumbnail_path = None
            if file_type == 'image':
                thumbnail_filename = f"thumb_{unique_filename}"
                thumbnail_path = os.path.join(UPLOAD_FOLDER, 'chat_thumbnails', thumbnail_filename)
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                if create_thumbnail(local_path, thumbnail_path):
                    print(f"聊天图片缩略图创建成功: {thumbnail_path}")
                else:
                    thumbnail_path = None
            elif file_type == 'video':
                thumbnail_filename = f"thumb_{unique_filename.rsplit('.', 1)[0] if '.' in unique_filename else unique_filename}.jpg"
                thumbnail_path = os.path.join(UPLOAD_FOLDER, 'chat_thumbnails', thumbnail_filename)
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                if create_video_thumbnail(local_path, thumbnail_path):
                    print(f"聊天视频缩略图创建成功: {thumbnail_path}")
                else:
                    thumbnail_path = None
            
            # 保存到数据库
            message = ChatMessage(
                message_type=file_type,
                file_path=local_path,
                file_name=original_filename,
                file_size=file_size,
                thumbnail_path=thumbnail_path,
                user_id=current_user.id
            )
            
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'message': '文件上传成功',
                'chat_message': {
                    'id': message.id,
                    'message_type': message.message_type,
                    'file_name': message.file_name,
                    'file_size': message.file_size,
                    'created_time': message.created_time.isoformat()
                }
            })
        else:
            return jsonify({'error': '文件类型不支持'}), 400
    
    return jsonify({'error': '无效的请求'}), 400

@app.route('/api/chat/files/<int:message_id>')
@login_required
def get_chat_file(message_id):
    """获取聊天文件"""
    message = ChatMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    
    if message.file_path and os.path.exists(message.file_path):
        return send_file(message.file_path, as_attachment=True, download_name=message.file_name)
    else:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/api/chat/thumbnails/<int:message_id>')
@login_required
def get_chat_thumbnail(message_id):
    """获取聊天文件缩略图"""
    message = ChatMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    
    if message.thumbnail_path and os.path.exists(message.thumbnail_path):
        return send_file(message.thumbnail_path)
    else:
        return jsonify({'error': '缩略图不存在'}), 404

@app.route('/api/chat/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_chat_message(message_id):
    """删除聊天记录消息"""
    message = ChatMessage.query.filter_by(id=message_id, user_id=current_user.id).first_or_404()
    
    # 删除文件（如果存在）
    if message.file_path and os.path.exists(message.file_path):
        try:
            os.remove(message.file_path)
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    # 删除缩略图（如果存在）
    if message.thumbnail_path and os.path.exists(message.thumbnail_path):
        try:
            os.remove(message.thumbnail_path)
        except Exception as e:
            print(f"删除缩略图失败: {e}")
    
    db.session.delete(message)
    db.session.commit()
    
    return jsonify({'message': '消息删除成功'})

if __name__ == '__main__':
    with app.app_context():
        # 检查数据库是否存在，如果不存在或表结构不匹配才重新创建
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # 检查是否有必要的表
            required_tables = ['user', 'media_file', 'note', 'share_link']
            tables_exist = all(table in tables for table in required_tables)
            
            if tables_exist:
                # 检查media_file表结构
                media_file_columns = [col['name'] for col in inspector.get_columns('media_file')]
                has_user_id = 'user_id' in media_file_columns
                
                if has_user_id:
                    print("✅ 数据库结构正常，保持现有数据")
                else:
                    print("⚠️  表结构不匹配，重新创建数据库")
                    db.drop_all()
                    db.create_all()
            else:
                print("🛠️  初始化数据库表")
                db.create_all()
                
        except Exception as e:
            print(f"🛠️  数据库初始化错误，重新创建: {e}")
            db.drop_all()
            db.create_all()
        
        # 创建管理员用户（如果不存在）
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@solocloud.local')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("👤 管理员用户已创建")
        else:
            print("👤 管理员用户已存在")
    
    app.run(debug=True, host='0.0.0.0', port=8080)

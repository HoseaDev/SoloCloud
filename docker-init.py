#!/usr/bin/env python3
"""
SoloCloud Docker 初始化脚本
自动处理目录权限和环境配置，避免手动授权
"""

import os
import sys
import stat
import subprocess
from pathlib import Path

def setup_directories():
    """创建并设置目录权限"""
    print("🔧 Setting up SoloCloud directories...")
    
    # 定义需要创建的目录
    directories = [
        '/app/logs',
        '/app/data', 
        '/app/uploads',
        '/app/uploads/images',
        '/app/uploads/videos',
        '/app/uploads/audio',
        '/app/uploads/files',
        '/app/uploads/archives',
        '/app/uploads/code',
        '/app/uploads/thumbnails',
        '/app/uploads/chat',
        '/app/uploads/chat_thumbnails'
    ]
    
    # 创建目录
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
            return False
    
    # 设置权限（简化处理，只确保写权限）
    try:
        for directory in directories:
            if os.path.exists(directory):
                # 设置目录权限为755 (rwxr-xr-x)，但忽略chown错误
                try:
                    os.chmod(directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    print(f"✅ Set permissions for: {directory}")
                except PermissionError:
                    print(f"⚠️  Permission warning for {directory}, but continuing...")
        
        return True
    except Exception as e:
        print(f"⚠️  Permission setup had issues but continuing: {e}")
        return True  # 继续执行，不因权限问题而失败

def setup_environment():
    """设置Docker环境变量"""
    print("🌍 Setting up environment variables...")
    
    # Docker环境下的会话配置
    env_vars = {
        'FLASK_ENV': 'production',
        'FLASK_APP': 'app.py',
        'SESSION_COOKIE_SECURE': 'false',
        'SESSION_COOKIE_HTTPONLY': 'true', 
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_DOMAIN': '',
        'DOCKER_ENV': 'true'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ Set {key}={value}")
    
    return True

def check_permissions():
    """检查目录权限是否正确"""
    print("🔍 Checking directory permissions...")
    
    directories = ['/app/logs', '/app/data', '/app/uploads']
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"❌ Directory does not exist: {directory}")
            return False
        
        if not os.access(directory, os.W_OK):
            print(f"❌ No write permission for: {directory}")
            return False
        
        print(f"✅ Permissions OK for: {directory}")
    
    return True

def main():
    """主函数"""
    print("🚀 SoloCloud Docker Initialization")
    print("=" * 50)
    
    # 设置目录
    if not setup_directories():
        print("❌ Directory setup failed")
        sys.exit(1)
    
    # 设置环境变量
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # 检查权限
    if not check_permissions():
        print("❌ Permission check failed")
        sys.exit(1)
    
    print("=" * 50)
    print("✅ SoloCloud initialization completed successfully!")
    print("🎯 Ready to start the application")
    
    return True

if __name__ == '__main__':
    main()

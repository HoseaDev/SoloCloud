#!/usr/bin/env python3
"""
密码重置脚本 - 用于忘记密码时重置用户密码
使用方法: python reset_password.py <用户名> <新密码>
"""
import sys
import os
sys.path.insert(0, '.')

from app import app, db, User

def reset_user_password(username, new_password):
    """重置用户密码"""
    with app.app_context():
        try:
            # 查找用户
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"❌ 用户 '{username}' 不存在")
                return False
            
            # 验证新密码长度
            if len(new_password) < 6:
                print("❌ 新密码至少需要6个字符")
                return False
            
            # 重置密码
            user.set_password(new_password)
            db.session.commit()
            
            print(f"✅ 用户 '{username}' 的密码已成功重置")
            print(f"📧 邮箱: {user.email}")
            print(f"🕒 创建时间: {user.created_time}")
            print(f"🔑 新密码: {new_password}")
            print("\n⚠️  请妥善保管新密码，建议用户登录后立即修改")
            
            return True
            
        except Exception as e:
            print(f"❌ 重置密码时发生错误: {e}")
            return False

def list_all_users():
    """列出所有用户"""
    with app.app_context():
        try:
            users = User.query.all()
            if not users:
                print("📭 系统中没有用户")
                return
            
            print(f"👥 系统中共有 {len(users)} 个用户:")
            print("-" * 60)
            for user in users:
                print(f"用户名: {user.username}")
                print(f"邮箱: {user.email}")
                print(f"创建时间: {user.created_time}")
                print(f"状态: {'活跃' if user.is_active else '禁用'}")
                print("-" * 60)
                
        except Exception as e:
            print(f"❌ 获取用户列表时发生错误: {e}")

def main():
    if len(sys.argv) == 1:
        print("🔧 SoloCloud 密码重置工具")
        print("=" * 50)
        print("使用方法:")
        print("  python reset_password.py <用户名> <新密码>    # 重置指定用户密码")
        print("  python reset_password.py --list              # 列出所有用户")
        print("\n示例:")
        print("  python reset_password.py admin newpassword123")
        print("  python reset_password.py --list")
        return
    
    if sys.argv[1] == '--list':
        list_all_users()
        return
    
    if len(sys.argv) != 3:
        print("❌ 参数错误")
        print("使用方法: python reset_password.py <用户名> <新密码>")
        return
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    print(f"🔄 正在重置用户 '{username}' 的密码...")
    success = reset_user_password(username, new_password)
    
    if success:
        print("\n🎉 密码重置完成！用户现在可以使用新密码登录。")
        print("💡 建议用户登录后立即在设置中修改为自己的密码。")
    else:
        print("\n💥 密码重置失败，请检查错误信息。")

if __name__ == '__main__':
    main()

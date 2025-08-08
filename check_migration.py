#!/usr/bin/env python3
"""
SoloCloud 迁移检查工具
用于验证迁移前后的数据完整性
"""

import os
import sqlite3
import hashlib
import json
from pathlib import Path
from datetime import datetime

class MigrationChecker:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.data_dir = self.base_path / "data"
        self.uploads_dir = self.base_path / "uploads"
        self.logs_dir = self.base_path / "logs"
        self.db_path = self.data_dir / "SoloCloud.db"
    
    def calculate_file_hash(self, file_path):
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def get_directory_info(self, directory):
        """获取目录信息"""
        if not directory.exists():
            return {"exists": False, "files": [], "total_size": 0}
        
        files_info = []
        total_size = 0
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                files_info.append({
                    "path": str(file_path.relative_to(directory)),
                    "size": size,
                    "hash": self.calculate_file_hash(file_path),
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return {
            "exists": True,
            "file_count": len(files_info),
            "total_size": total_size,
            "files": files_info
        }
    
    def get_database_info(self):
        """获取数据库信息"""
        if not self.db_path.exists():
            return {"exists": False, "tables": [], "records": 0}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 获取每个表的记录数
            table_info = {}
            total_records = 0
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                table_info[table] = count
                total_records += count
            
            # 获取数据库大小
            db_size = self.db_path.stat().st_size
            
            conn.close()
            
            return {
                "exists": True,
                "size": db_size,
                "hash": self.calculate_file_hash(self.db_path),
                "tables": table_info,
                "total_records": total_records
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}
    
    def generate_snapshot(self):
        """生成当前状态快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "database": self.get_database_info(),
            "uploads": self.get_directory_info(self.uploads_dir),
            "logs": self.get_directory_info(self.logs_dir),
            "environment": {
                "is_docker": os.path.exists('/.dockerenv'),
                "python_version": os.popen('python3 --version 2>/dev/null || python --version').read().strip(),
                "working_directory": str(self.base_path.absolute())
            }
        }
        
        return snapshot
    
    def save_snapshot(self, filename=None):
        """保存快照到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"migration_snapshot_{timestamp}.json"
        
        snapshot = self.generate_snapshot()
        
        # 确保备份目录存在
        backup_dir = self.base_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        snapshot_path = backup_dir / filename
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 快照已保存: {snapshot_path}")
        return snapshot_path
    
    def compare_snapshots(self, snapshot1_path, snapshot2_path):
        """比较两个快照"""
        try:
            with open(snapshot1_path, 'r', encoding='utf-8') as f:
                snapshot1 = json.load(f)
            with open(snapshot2_path, 'r', encoding='utf-8') as f:
                snapshot2 = json.load(f)
        except Exception as e:
            print(f"❌ 读取快照文件失败: {e}")
            return
        
        print(f"\n📊 快照比较报告")
        print(f"快照1: {snapshot1['timestamp']} ({snapshot1_path})")
        print(f"快照2: {snapshot2['timestamp']} ({snapshot2_path})")
        print("=" * 60)
        
        # 比较数据库
        self._compare_database(snapshot1['database'], snapshot2['database'])
        
        # 比较上传文件
        self._compare_directory(snapshot1['uploads'], snapshot2['uploads'], "上传文件")
        
        # 比较日志文件
        self._compare_directory(snapshot1['logs'], snapshot2['logs'], "日志文件")
    
    def _compare_database(self, db1, db2):
        """比较数据库信息"""
        print("\n🗄️  数据库比较:")
        
        if not db1.get('exists') and not db2.get('exists'):
            print("  两个快照都没有数据库文件")
            return
        
        if db1.get('exists') != db2.get('exists'):
            print(f"  ⚠️  数据库存在性不同: {db1.get('exists')} -> {db2.get('exists')}")
            return
        
        if 'error' in db1 or 'error' in db2:
            print(f"  ❌ 数据库访问错误")
            return
        
        # 比较记录数
        if db1['total_records'] != db2['total_records']:
            print(f"  ⚠️  总记录数变化: {db1['total_records']} -> {db2['total_records']}")
        else:
            print(f"  ✅ 总记录数一致: {db1['total_records']}")
        
        # 比较表结构
        tables1 = set(db1['tables'].keys())
        tables2 = set(db2['tables'].keys())
        
        if tables1 != tables2:
            print(f"  ⚠️  表结构变化:")
            if tables1 - tables2:
                print(f"    删除的表: {tables1 - tables2}")
            if tables2 - tables1:
                print(f"    新增的表: {tables2 - tables1}")
        
        # 比较哈希值
        if db1.get('hash') != db2.get('hash'):
            print(f"  ⚠️  数据库文件内容发生变化")
        else:
            print(f"  ✅ 数据库文件内容一致")
    
    def _compare_directory(self, dir1, dir2, name):
        """比较目录信息"""
        print(f"\n📁 {name}比较:")
        
        if not dir1.get('exists') and not dir2.get('exists'):
            print(f"  两个快照都没有{name}目录")
            return
        
        if dir1.get('exists') != dir2.get('exists'):
            print(f"  ⚠️  {name}目录存在性不同: {dir1.get('exists')} -> {dir2.get('exists')}")
            return
        
        # 比较文件数量
        if dir1['file_count'] != dir2['file_count']:
            print(f"  ⚠️  文件数量变化: {dir1['file_count']} -> {dir2['file_count']}")
        else:
            print(f"  ✅ 文件数量一致: {dir1['file_count']}")
        
        # 比较总大小
        if dir1['total_size'] != dir2['total_size']:
            print(f"  ⚠️  总大小变化: {dir1['total_size']} -> {dir2['total_size']} bytes")
        else:
            print(f"  ✅ 总大小一致: {dir1['total_size']} bytes")
    
    def print_status(self):
        """打印当前状态"""
        print("🔍 SoloCloud 当前状态检查")
        print("=" * 50)
        
        # 检查数据库
        db_info = self.get_database_info()
        if db_info['exists']:
            if 'error' in db_info:
                print(f"❌ 数据库: 存在但无法访问 ({db_info['error']})")
            else:
                print(f"✅ 数据库: {db_info['total_records']} 条记录")
                for table, count in db_info['tables'].items():
                    print(f"   - {table}: {count} 条记录")
        else:
            print("❌ 数据库: 不存在")
        
        # 检查上传目录
        uploads_info = self.get_directory_info(self.uploads_dir)
        if uploads_info['exists']:
            print(f"✅ 上传文件: {uploads_info['file_count']} 个文件 ({uploads_info['total_size']} bytes)")
        else:
            print("⚠️  上传目录: 不存在")
        
        # 检查日志目录
        logs_info = self.get_directory_info(self.logs_dir)
        if logs_info['exists']:
            print(f"✅ 日志文件: {logs_info['file_count']} 个文件 ({logs_info['total_size']} bytes)")
        else:
            print("⚠️  日志目录: 不存在")
        
        # 检查环境
        is_docker = os.path.exists('/.dockerenv')
        print(f"🌍 运行环境: {'Docker' if is_docker else '本地Python'}")

def main():
    import sys
    
    checker = MigrationChecker()
    
    if len(sys.argv) < 2:
        print("SoloCloud 迁移检查工具")
        print("\n用法:")
        print("  python check_migration.py status          - 显示当前状态")
        print("  python check_migration.py snapshot        - 创建状态快照")
        print("  python check_migration.py compare <file1> <file2> - 比较两个快照")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        checker.print_status()
    elif command == "snapshot":
        checker.save_snapshot()
    elif command == "compare":
        if len(sys.argv) != 4:
            print("用法: python check_migration.py compare <snapshot1> <snapshot2>")
            return
        checker.compare_snapshots(sys.argv[2], sys.argv[3])
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()

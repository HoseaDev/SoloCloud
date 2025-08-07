"""
多云存储支持模块
支持阿里云OSS、腾讯云COS、七牛云、坚果云等主流云存储服务
"""

import os
import mimetypes
from abc import ABC, abstractmethod
from typing import Tuple, Optional

# 云存储提供商枚举
STORAGE_PROVIDERS = {
    'local': '本地存储',
    'aliyun_oss': '阿里云 OSS',
    'tencent_cos': '腾讯云 COS',
    'qiniu': '七牛云',
    'jianguoyun': '坚果云'
}

class CloudStorageBase(ABC):
    """云存储基类"""
    
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """上传文件到云存储"""
        pass
    
    @abstractmethod
    def delete_file(self, remote_path: str) -> Tuple[bool, str]:
        """从云存储删除文件"""
        pass
    
    @abstractmethod
    def get_file_url(self, remote_path: str) -> str:
        """获取文件访问URL"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已正确配置"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """测试存储连接"""
        pass

class LocalStorage(CloudStorageBase):
    """本地存储"""
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        # 本地存储不需要上传，文件已经在本地
        return True, "本地存储成功"
    
    def delete_file(self, remote_path: str) -> Tuple[bool, str]:
        try:
            if os.path.exists(remote_path):
                os.remove(remote_path)
                return True, "删除成功"
            return True, "文件不存在"
        except Exception as e:
            return False, str(e)
    
    def get_file_url(self, remote_path: str) -> str:
        # 本地存储返回None，让Flask直接提供文件
        return None
    
    def is_configured(self) -> bool:
        return True
    
    def test_connection(self) -> Tuple[bool, str]:
        return True, "本地存储连接正常"

class AliyunOSSStorage(CloudStorageBase):
    """阿里云OSS存储"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import oss2
            self.oss2 = oss2
        except ImportError:
            self.oss2 = None
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        if not self.oss2:
            return False, "请安装oss2库: pip install oss2"
        
        try:
            auth = self.oss2.Auth(
                self.config['access_key_id'],
                self.config['access_key_secret']
            )
            bucket = self.oss2.Bucket(
                auth,
                self.config['endpoint'],
                self.config['bucket_name']
            )
            
            result = bucket.put_object_from_file(remote_path, local_path)
            return result.status == 200, result.request_id
        except Exception as e:
            return False, str(e)
    
    def delete_file(self, remote_path: str) -> Tuple[bool, str]:
        if not self.oss2:
            return False, "请安装oss2库"
        
        try:
            auth = self.oss2.Auth(
                self.config['access_key_id'],
                self.config['access_key_secret']
            )
            bucket = self.oss2.Bucket(
                auth,
                self.config['endpoint'],
                self.config['bucket_name']
            )
            
            result = bucket.delete_object(remote_path)
            return result.status == 204, "删除成功"
        except Exception as e:
            return False, str(e)
    
    def get_file_url(self, remote_path: str) -> str:
        # 构建OSS文件访问URL
        bucket_name = self.config['bucket_name']
        endpoint = self.config['endpoint'].replace('https://', '').replace('http://', '')
        return f"https://{bucket_name}.{endpoint}/{remote_path}"
    
    def is_configured(self) -> bool:
        required_keys = ['access_key_id', 'access_key_secret', 'endpoint', 'bucket_name']
        return all(self.config.get(key) and str(self.config.get(key)).strip() for key in required_keys)
    
    def test_connection(self) -> Tuple[bool, str]:
        if not self.oss2:
            return False, "请安装oss2库: pip install oss2"
        
        if not self.is_configured():
            return False, "配置信息不完整"
        
        try:
            auth = self.oss2.Auth(
                self.config['access_key_id'],
                self.config['access_key_secret']
            )
            bucket = self.oss2.Bucket(
                auth,
                self.config['endpoint'],
                self.config['bucket_name']
            )
            
            # 尝试列出bucket信息来测试连接
            bucket_info = bucket.get_bucket_info()
            return True, f"连接成功，Bucket: {bucket_info.name}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

class TencentCOSStorage(CloudStorageBase):
    """腾讯云COS存储"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            from qcloud_cos import CosConfig, CosS3Client
            self.CosConfig = CosConfig
            self.CosS3Client = CosS3Client
        except ImportError:
            self.CosConfig = None
            self.CosS3Client = None
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        if not self.CosConfig:
            return False, "请安装cos-python-sdk-v5库: pip install cos-python-sdk-v5"
        
        try:
            config = self.CosConfig(
                Region=self.config['region'],
                SecretId=self.config['secret_id'],
                SecretKey=self.config['secret_key']
            )
            client = self.CosS3Client(config)
            
            response = client.upload_file(
                Bucket=self.config['bucket_name'],
                LocalFilePath=local_path,
                Key=remote_path
            )
            return True, "上传成功"
        except Exception as e:
            return False, str(e)
    
    def delete_file(self, remote_path: str) -> Tuple[bool, str]:
        if not self.CosConfig:
            return False, "请安装cos-python-sdk-v5库"
        
        try:
            config = self.CosConfig(
                Region=self.config['region'],
                SecretId=self.config['secret_id'],
                SecretKey=self.config['secret_key']
            )
            client = self.CosS3Client(config)
            
            client.delete_object(
                Bucket=self.config['bucket_name'],
                Key=remote_path
            )
            return True, "删除成功"
        except Exception as e:
            return False, str(e)
    
    def get_file_url(self, remote_path: str) -> str:
        bucket_name = self.config['bucket_name']
        region = self.config['region']
        return f"https://{bucket_name}.cos.{region}.myqcloud.com/{remote_path}"
    
    def is_configured(self) -> bool:
        required_keys = ['secret_id', 'secret_key', 'region', 'bucket_name']
        return all(self.config.get(key) and str(self.config.get(key)).strip() for key in required_keys)
    
    def test_connection(self) -> Tuple[bool, str]:
        if not self.CosConfig:
            return False, "请安装cos-python-sdk-v5库: pip install cos-python-sdk-v5"
        
        if not self.is_configured():
            return False, "配置信息不完整"
        
        try:
            config = self.CosConfig(
                Region=self.config['region'],
                SecretId=self.config['secret_id'],
                SecretKey=self.config['secret_key']
            )
            client = self.CosS3Client(config)
            
            # 尝试获取bucket信息来测试连接
            response = client.head_bucket(Bucket=self.config['bucket_name'])
            return True, f"连接成功，Bucket: {self.config['bucket_name']}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

class QiniuStorage(CloudStorageBase):
    """七牛云存储"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            from qiniu import Auth, put_file, BucketManager
            self.qiniu_auth = Auth
            self.put_file = put_file
            self.BucketManager = BucketManager
        except ImportError:
            self.qiniu_auth = None
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        if not self.qiniu_auth:
            return False, "请安装qiniu库: pip install qiniu"
        
        try:
            auth = self.qiniu_auth(
                self.config['access_key'],
                self.config['secret_key']
            )
            token = auth.upload_token(self.config['bucket_name'], remote_path)
            
            ret, info = self.put_file(token, remote_path, local_path)
            if info.status_code == 200:
                return True, "上传成功"
            else:
                return False, f"上传失败: {info.text_body}"
        except Exception as e:
            return False, str(e)
    
    def delete_file(self, remote_path: str) -> Tuple[bool, str]:
        if not self.qiniu_auth:
            return False, "请安装qiniu库"
        
        try:
            auth = self.qiniu_auth(
                self.config['access_key'],
                self.config['secret_key']
            )
            bucket_manager = self.BucketManager(auth)
            
            ret, info = bucket_manager.delete(self.config['bucket_name'], remote_path)
            if info.status_code == 200:
                return True, "删除成功"
            else:
                return False, f"删除失败: {info.text_body}"
        except Exception as e:
            return False, str(e)
    
    def get_file_url(self, remote_path: str) -> str:
        domain = self.config['domain']
        return f"https://{domain}/{remote_path}"
    
    def is_configured(self) -> bool:
        required_keys = ['access_key', 'secret_key', 'bucket_name', 'domain']
        return all(self.config.get(key) and str(self.config.get(key)).strip() for key in required_keys)
    
    def test_connection(self) -> Tuple[bool, str]:
        if not self.qiniu_auth:
            return False, "请安装qiniu库: pip install qiniu"
        
        if not self.is_configured():
            return False, "配置信息不完整"
        
        try:
            auth = self.qiniu_auth(
                self.config['access_key'],
                self.config['secret_key']
            )
            bucket_manager = self.BucketManager(auth)
            
            # 尝试获取bucket信息来测试连接
            ret, info = bucket_manager.buckets()
            if info.status_code == 200 and self.config['bucket_name'] in ret:
                return True, f"连接成功，Bucket: {self.config['bucket_name']}"
            else:
                return False, f"Bucket '{self.config['bucket_name']}' 不存在或无权限访问"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

class JianguoyunStorage(CloudStorageBase):
    """坚果云存储（WebDAV）"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import requests
            self.requests = requests
        except ImportError:
            self.requests = None
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        if not self.requests:
            return False, "请安装requests库: pip install requests"
        
        try:
            url = f"{self.config['webdav_url']}/{remote_path}"
            
            with open(local_path, 'rb') as f:
                response = self.requests.put(
                    url,
                    data=f,
                    auth=(self.config['username'], self.config['password'])
                )
            
            if response.status_code in [200, 201, 204]:
                return True, "上传成功"
            else:
                return False, f"上传失败: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def delete_file(self, remote_path: str) -> Tuple[bool, str]:
        if not self.requests:
            return False, "请安装requests库"
        
        try:
            url = f"{self.config['webdav_url']}/{remote_path}"
            
            response = self.requests.delete(
                url,
                auth=(self.config['username'], self.config['password'])
            )
            
            if response.status_code in [200, 204]:
                return True, "删除成功"
            else:
                return False, f"删除失败: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def get_file_url(self, remote_path: str) -> str:
        # 坚果云需要通过分享链接访问，这里返回WebDAV路径
        return f"{self.config['webdav_url']}/{remote_path}"
    
    def is_configured(self) -> bool:
        required_keys = ['webdav_url', 'username', 'password']
        return all(self.config.get(key) and str(self.config.get(key)).strip() for key in required_keys)
    
    def test_connection(self) -> Tuple[bool, str]:
        if not self.requests:
            return False, "请安装requests库: pip install requests"
        
        if not self.is_configured():
            return False, "配置信息不完整"
        
        try:
            # 尝试发送PROPFIND请求来测试WebDAV连接
            response = self.requests.request(
                'PROPFIND',
                self.config['webdav_url'],
                auth=(self.config['username'], self.config['password']),
                timeout=10
            )
            
            if response.status_code in [200, 207]:  # 207 Multi-Status is normal for PROPFIND
                return True, "连接成功，坚果云WebDAV服务正常"
            else:
                return False, f"连接失败: HTTP {response.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

class CloudStorageManager:
    """云存储管理器"""
    
    def __init__(self):
        self.providers = {
            'local': LocalStorage,
            'aliyun_oss': AliyunOSSStorage,
            'tencent_cos': TencentCOSStorage,
            'qiniu': QiniuStorage,
            'jianguoyun': JianguoyunStorage
        }
    
    def get_storage_client(self, provider: str, config: dict) -> Optional[CloudStorageBase]:
        """获取存储客户端"""
        if provider not in self.providers:
            return None
        
        storage_class = self.providers[provider]
        return storage_class(config)
    
    def test_storage_connection(self, provider: str, config: dict) -> Tuple[bool, str]:
        """测试存储连接"""
        storage_client = self.get_storage_client(provider, config)
        if not storage_client:
            return False, f"不支持的存储提供商: {provider}"
        
        return storage_client.test_connection()
    
    def get_storage(self, provider: str) -> Optional[CloudStorageBase]:
        """获取当前配置的存储实例"""
        # 从环境变量获取配置
        config = self._get_provider_config(provider)
        return self.get_storage_client(provider, config)
    
    def _get_provider_config(self, provider: str) -> dict:
        """从环境变量获取存储提供商配置"""
        if provider == 'local':
            return {}
        elif provider == 'aliyun_oss':
            return {
                'access_key_id': os.getenv('ALIYUN_OSS_ACCESS_KEY_ID'),
                'access_key_secret': os.getenv('ALIYUN_OSS_ACCESS_KEY_SECRET'),
                'endpoint': os.getenv('ALIYUN_OSS_ENDPOINT'),
                'bucket_name': os.getenv('ALIYUN_OSS_BUCKET_NAME')
            }
        elif provider == 'tencent_cos':
            return {
                'secret_id': os.getenv('TENCENT_COS_SECRET_ID'),
                'secret_key': os.getenv('TENCENT_COS_SECRET_KEY'),
                'region': os.getenv('TENCENT_COS_REGION'),
                'bucket_name': os.getenv('TENCENT_COS_BUCKET_NAME')
            }
        elif provider == 'qiniu':
            return {
                'access_key': os.getenv('QINIU_ACCESS_KEY'),
                'secret_key': os.getenv('QINIU_SECRET_KEY'),
                'bucket_name': os.getenv('QINIU_BUCKET_NAME'),
                'domain': os.getenv('QINIU_DOMAIN')
            }
        elif provider == 'jianguoyun':
            return {
                'webdav_url': os.getenv('JIANGUOYUN_WEBDAV_URL'),
                'username': os.getenv('JIANGUOYUN_USERNAME'),
                'password': os.getenv('JIANGUOYUN_PASSWORD')
            }
        else:
            return {}
    
    def get_available_providers(self) -> dict:
        """获取可用的存储提供商"""
        return STORAGE_PROVIDERS.copy()

# 全局存储管理器实例
storage_manager = CloudStorageManager()

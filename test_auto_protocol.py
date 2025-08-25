#!/usr/bin/env python3
"""
测试自动协议适应功能
"""

import requests
import sys

def test_protocol_adaptation():
    """测试不同协议访问"""
    
    # 测试配置
    base_urls = [
        "http://localhost:8080",    # HTTP直接访问
        "http://localhost:80",       # HTTP通过Nginx
        # "https://localhost:443",   # HTTPS（如果配置了证书）
    ]
    
    print("=" * 50)
    print("SoloCloud 自动协议适应测试")
    print("=" * 50)
    
    for base_url in base_urls:
        print(f"\n测试 {base_url}:")
        try:
            # 测试健康检查
            response = requests.get(f"{base_url}/health", timeout=5, verify=False)
            if response.status_code == 200:
                print(f"  ✅ 健康检查通过")
                data = response.json()
                print(f"     状态: {data.get('status')}")
                print(f"     版本: {data.get('version')}")
            else:
                print(f"  ❌ 健康检查失败: {response.status_code}")
            
            # 检查Cookie设置
            response = requests.get(base_url, timeout=5, verify=False)
            cookies = response.cookies
            print(f"  📍 Cookie设置:")
            for cookie in cookies:
                print(f"     {cookie.name}: Secure={cookie.secure}, HttpOnly={cookie.has_nonstandard_attr('HttpOnly')}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  无法连接到 {base_url}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("测试说明:")
    print("1. HTTP访问时，Cookie的Secure应该为False")
    print("2. HTTPS访问时，Cookie的Secure应该为True")
    print("3. 系统应该自动适应访问协议，无需手动配置")
    print("=" * 50)

if __name__ == "__main__":
    test_protocol_adaptation()
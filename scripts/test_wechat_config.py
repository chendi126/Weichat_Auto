#!/usr/bin/env python3
"""
测试微信公众号凭证是否有效
"""

import requests
import sys
import yaml
from pathlib import Path

# 从配置文件读取
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

wechat_config = config.get("wechat", {})
APP_ID = wechat_config.get("app_id", "")
APP_SECRET = wechat_config.get("app_secret", "")

def test_access_token():
    """测试获取 access_token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        
        print("📝 测试结果：")
        print(f"状态码: {response.status_code}")
        print(f"返回内容: {result}")
        
        if "access_token" in result:
            print("\n✅ 凭证有效！")
            print(f"access_token: {result['access_token'][:20]}...")
            print(f"有效期: {result['expires_in']}秒")
            return True
        else:
            print("\n❌ 凭证无效！")
            print(f"错误码: {result.get('errcode')}")
            print(f"错误信息: {result.get('errmsg')}")
            
            # 常见错误码说明
            errcode = result.get('errcode')
            if errcode == 40001:
                print("\n💡 提示: AppSecret 错误，请检查是否复制正确")
            elif errcode == 40125:
                print("\n💡 提示: AppID 无效，请检查是否正确")
            elif errcode == 40002:
                print("\n💡 提示: 请确保 grant_type 参数正确")
            
            return False
            
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("微信公众号凭证测试")
    print("=" * 50)
    print(f"\nAppID: {APP_ID}")
    print(f"AppSecret: {APP_SECRET[:8]}...{APP_SECRET[-8:]}")
    print()
    
    success = test_access_token()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 你的微信公众号凭证是正确的")
        print("问题出在平台的集成配置上")
    else:
        print("❌ 你的微信公众号凭证有问题")
        print("请检查 AppID 和 AppSecret")
    print("=" * 50)
    
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
测试平台微信公众号集成配置
"""

from coze_workload_identity import Client

def test_wechat_integration():
    """测试微信公众号集成"""
    print("=" * 60)
    print("测试平台微信公众号集成")
    print("=" * 60)

    try:
        client = Client()

        # 方法1：获取集成凭证
        print("\n📝 方法1：获取集成凭证")
        try:
            access_token = client.get_integration_credential("integration-wechat-official-account")
            if access_token:
                print(f"✅ 成功获取 access_token: {access_token[:20]}...")
            else:
                print("❌ access_token 为空")
        except Exception as e:
            print(f"❌ 获取凭证失败: {e}")

        # 方法2：获取所有集成列表（如果支持）
        print("\n📝 方法2：检查项目环境变量")
        try:
            env_vars = client.get_project_env_vars()
            print(f"找到 {len(env_vars)} 个环境变量:")

            wechat_vars = [v for v in env_vars if 'wechat' in v.key.lower() or 'weixin' in v.key.lower()]
            if wechat_vars:
                print(f"\n找到 {len(wechat_vars)} 个微信相关变量:")
                for var in wechat_vars:
                    print(f"  - {var.key}: {'已配置' if var.value else '未配置'}")
            else:
                print("\n❌ 未找到微信相关环境变量")

        except Exception as e:
            print(f"❌ 获取环境变量失败: {e}")

        client.close()

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_wechat_integration()

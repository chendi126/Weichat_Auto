#!/usr/bin/env python3
"""
诊断微信公众号集成配置
"""

import sys
from coze_workload_identity import Client


def main():
    print("=" * 70)
    print("微信公众号集成配置诊断")
    print("=" * 70)

    # 步骤1：测试集成凭证获取
    print("\n【步骤1】测试微信公众号集成凭证获取")
    print("-" * 70)

    try:
        client = Client()
        access_token = client.get_integration_credential("integration-wechat-official-account")
        print("✅ 成功获取 access_token")
        print(f"   Token 长度: {len(access_token)} 字符")
        print(f"   Token 前缀: {access_token[:20]}...")
        client.close()
        return 0
    except Exception as e:
        error_msg = str(e)

        if "Integration credential request failed with status 500" in error_msg:
            print("❌ 平台集成服务返回 500 错误")
            print("\n可能原因：")
            print("  1. 微信公众号集成未在项目管理中启用")
            print("  2. 集成凭证（AppID 和 AppSecret）未配置")
            print("\n解决方法：")
            print("  1. 登录 Coze 平台项目管理页面")
            print("  2. 进入「集成」→「微信公众号」")
            print("  3. 点击「启用」按钮")
            print("  4. 填写微信公众号的 AppID 和 AppSecret")
            print("  5. 保存配置")
            print("\n获取 AppID 和 AppSecret 的方法：")
            print("  1. 登录微信公众平台：https://mp.weixin.qq.com")
            print("  2. 进入「设置与开发」→「基本配置」")
            print("  3. 在「开发者ID」中可以看到 AppID")
            print("  4. 点击「AppSecret」后的「重置」或「获取」按钮")
            print("  5. 扫码验证后即可获得 AppSecret")

        elif "40164" in error_msg or "IP地址不在白名单中" in error_msg:
            print("❌ IP地址不在白名单中（错误码40164）")
            print("\n解决方法：")
            print("  1. 登录微信公众平台：https://mp.weixin.qq.com")
            print("  2. 进入「设置与开发」→「基本配置」→「IP白名单」")
            print("  3. 添加以下IP段：")
            print("     - 115.190.0.0/16")
            print("     - 115.191.0.0/16")
            print("     - 101.126.0.0/16")
            print("  4. 保存配置")

        elif "48001" in error_msg or "api 功能未授权" in error_msg:
            print("❌ 公众号未获得发布接口权限")
            print("\n解决方法：")
            print("  1. 登录微信公众平台")
            print("  2. 进入「设置与开发」→「开发者中心」")
            print("  3. 检查接口权限状态，确保已获得「草稿箱」和「发布」接口权限")

        else:
            print(f"❌ 获取凭证失败: {error_msg}")

        print("\n" + "=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

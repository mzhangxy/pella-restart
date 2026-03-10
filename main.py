import os
import requests

# ================= 配置区 =================
# 你的目标服务器实例 ID
TARGET_SERVER_ID = "9dbd8fbc687149208257283116ed74d5"
# ==========================================

def get_clerk_token(client_val, client_uat, session_id):
    """直接向 Clerk API 请求最新鉴权 Token"""
    print("🔄 正在直接向 Clerk 后端 API 申请最新 Token...")
    
    # 动态拼接包含你 session_id 的专属获取 Token 接口
    url = f"https://clerk.pella.app/v1/client/sessions/{session_id}/tokens?_clerk_api_version=2025-11-10"
    
    # 伪造请求头，完全模拟浏览器发出的纯 API 请求
    headers = {
        "Origin": "https://www.pella.app",
        "Referer": "https://www.pella.app/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        # 直接把三个核心环境变量拼装成 Cookie
        "Cookie": f"__client={client_val}; __client_uat={client_uat}; clerk_active_context={session_id};"
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            token = response.json().get('jwt')
            if token:
                print("✅ 成功获取到 Clerk 授权 Token！")
                return token
        else:
            print(f"❌ 获取 Token 失败，状态码: {response.status_code}")
            print("详细响应:", response.text)
    except Exception as e:
        print(f"❌ 网络异常: {e}")
    return None

def trigger_remote_redeploy(token, server_id):
    """发送重启指令"""
    print(f"\n🚀 开始向服务器发送重启/开机指令...")
    url = "https://api.pella.app/server/redeploy"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    multipart_data = {
        "id": (None, server_id)
    }
    
    try:
        response = requests.post(url, headers=headers, files=multipart_data)
        if response.status_code == 200:
            print("✅ 远程指令发送成功！服务器正在重启。")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print("详细信息:", response.text)
    except Exception as e:
        print(f"❌ 请求发生网络异常: {e}")

def main():
    print("🌐 启动纯 API 自动化控制程序 (极速版)...")
    
    client_val = os.environ.get('PELLA_CLIENT', '')
    client_uat_val = os.environ.get('PELLA_CLIENT_UAT', '')
    active_context = os.environ.get('PELLA_ACTIVE_CONTEXT', '')
    
    if not (client_val and client_uat_val and active_context):
        print("⚠️ 环境变量缺失！请确保 GitHub Secrets 已配置。")
        return
        
    # 1. 绕过前端页面，直接抓取 Token
    token = get_clerk_token(client_val, client_uat_val, active_context)
    
    if token:
        # 2. 携带 Token 发送动作指令
        trigger_remote_redeploy(token, TARGET_SERVER_ID)
    else:
        print("❌ 任务终止。")

if __name__ == "__main__":
    main()

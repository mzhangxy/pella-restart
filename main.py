import os
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# ================= 配置区 =================
# 你的目标服务器实例 ID
TARGET_SERVER_ID = "9dbd8fbc687149208257283116ed74d5"
# ==========================================

def trigger_remote_redeploy(token, server_id):
    """
    接收动态拦截到的 Token，向服务器发送开机/重启指令
    """
    print(f"\n🚀 开始向服务器发送重启/开机指令...")
    url = "https://api.pella.app/server/redeploy"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 构造 multipart/form-data 表单数据
    multipart_data = {
        "id": (None, server_id)
    }
    
    try:
        response = requests.post(url, headers=headers, files=multipart_data)
        
        if response.status_code == 200:
            print("✅ 远程指令发送成功！服务器正在处理 redeploy 请求。")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print("详细信息:", response.text)
    except Exception as e:
        print(f"❌ 请求发生网络异常: {e}")

def main():
    print("🌐 启动云端无头浏览器环境...")
    
    co = ChromiumOptions()
    co.headless() 
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--blink-settings=imagesEnabled=false')
    
    # 🚨 【新增】完美伪装成你本地的浏览器指纹，防止 Clerk 因环境突变踢出登录
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36')
    
    page = ChromiumPage(co)
    
    try:
        print("📍 正在访问 Pella 建立域名上下文...")
        page.get('https://www.pella.app/')
        page.wait.load_start()
        
        client_val = os.environ.get('PELLA_CLIENT', '')
        client_uat_val = os.environ.get('PELLA_CLIENT_UAT', '')
        active_context = os.environ.get('PELLA_ACTIVE_CONTEXT', '')
        
        if client_val and client_uat_val and active_context:
            print("🍪 读取到环境变量，正在注入 3 个 Clerk 核心身份凭证...")
            cookies_to_set = [
                {'name': '__client', 'value': client_val, 'domain': '.pella.app'},
                {'name': '__client_uat', 'value': client_uat_val, 'domain': '.pella.app'},
                {'name': 'clerk_active_context', 'value': active_context, 'domain': 'www.pella.app'} # 调整为更精确的域名
            ]
            page.set.cookies(cookies_to_set)
            print("✅ 凭证注入完成！")
        else:
            print("⚠️ 未检测到完整的身份环境变量，请检查 GitHub Secrets 配置！")

        listen_url = 'clerk.pella.app/v1/client/sessions'
        page.listen.start(listen_url)
        
        # 🚨 【关键修改】直接强行访问后台控制面板，强制触发 Clerk 身份校验！
        print("⏳ 正在闯入后台面板 (/servers)，等待拦截身份 Token...")
        page.get('https://www.pella.app/servers')
        
        # 稍微延长一点超时时间，给 React 渲染和 Clerk 通讯留足余地
        packet = page.listen.wait(timeout=20)
        
        if packet and packet.request.method == 'POST':
            print("🎯 成功拦截到 Clerk 认证响应！")
            try:
                res_body = packet.response.body
                token = res_body.get('client', {}).get('sessions', [{}])[0].get('lastActiveToken', {}).get('jwt')
                
                if token:
                    print("🔑 成功提取到动态授权 Token！")
                    trigger_remote_redeploy(token, TARGET_SERVER_ID)
                else:
                    print("⚠️ 抓到了目标请求，但未在预期路径中找到 Token 字段。")
            except Exception as e:
                print(f"❌ 解析 Token JSON 失败: {e}")
        else:
            print("❌ 拦截超时或未抓到 POST 请求。")
            # 【新增排错】检查是不是因为 Cookie 无效被踢回了主页或登录页
            print(f"当前页面最终停留的 URL: {page.url}")
            print(f"当前页面标题: {page.title}")

    finally:
        print("\n任务结束，正在清理浏览器进程...")
        page.quit()

if __name__ == "__main__":
    main()

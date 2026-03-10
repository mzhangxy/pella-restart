import os
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# ================= 配置区 =================
# 你的目标服务器实例 ID（从之前的截图中提取）
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
        # 注意：使用 files 参数会让 requests 自动设置正确的 multipart/form-data Content-Type 和 boundary
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
    
    # 配置无头浏览器参数，确保在 GitHub Actions 的 Linux 环境中正常运行
    co = ChromiumOptions()
    co.headless() 
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    
    # 禁用图片和不必要的资源加载，加快脚本执行速度
    co.set_argument('--blink-settings=imagesEnabled=false')
    
    page = ChromiumPage(co)
    
    try:
        # 1. 初始化域名上下文，这是写入 Cookie 的前置条件
        print("📍 正在访问 Pella 建立域名上下文...")
        page.get('https://www.pella.app/')
        page.wait.load_start()
        
        # 2. 读取 GitHub Secrets 注入的 Clerk 核心凭证
        client_val = os.environ.get('PELLA_CLIENT', '')
        client_uat_val = os.environ.get('PELLA_CLIENT_UAT', '')
        
        if client_val and client_uat_val:
            print("🍪 读取到环境变量，正在注入 Clerk 身份凭证...")
            cookies_to_set = [
                {'name': '__client', 'value': client_val, 'domain': '.pella.app'},
                {'name': '__client_uat', 'value': client_uat_val, 'domain': '.pella.app'}
            ]
            page.set.cookies(cookies_to_set)
            print("✅ 凭证注入完成！")
        else:
            print("⚠️ 未检测到完整的 PELLA_CLIENT 或 PELLA_CLIENT_UAT 环境变量，请检查 GitHub Secrets 配置！")

        # 3. 启动后台网络监听，目标：Clerk 会话接口
        listen_url = 'clerk.pella.app/v1/client/sessions'
        page.listen.start(listen_url)
        
        # 4. 带着已注入的 Cookie 重新刷新主页，触发面板请求最新的 Token
        print("⏳ 正在刷新面板网页，等待拦截身份 Token...")
        page.get('https://www.pella.app/')
        
        # 设置 15 秒超时，防止在未登录或触发验证码时死等卡住 Action
        packet = page.listen.wait(timeout=15)
        
        if packet and packet.request.method == 'POST':
            print("🎯 成功拦截到 Clerk 认证响应！")
            
            try:
                res_body = packet.response.body
                # 按照 Clerk 的标准 JSON 结构提取 jwt token
                token = res_body.get('client', {}).get('sessions', [{}])[0].get('lastActiveToken', {}).get('jwt')
                
                if token:
                    print("🔑 成功提取到动态授权 Token！")
                    trigger_remote_redeploy(token, TARGET_SERVER_ID)
                else:
                    print("⚠️ 抓到了目标请求，但未在预期路径中找到 Token 字段。")
                    print("实际响应体前 200 个字符:", str(res_body)[:200])
                    
            except Exception as e:
                print(f"❌ 解析 Token JSON 失败: {e}")
        else:
            print("❌ 拦截超时或未抓到 POST 请求。")
            print("可能原因：Cookie 已过期、环境变量未正确读取，或者触发了 Cloudflare 人机验证。")
            # 打印当前页面的标题，帮助排错
            print("当前页面标题:", page.title)

    finally:
        print("\n任务结束，正在清理浏览器进程...")
        page.quit()

if __name__ == "__main__":
    main()

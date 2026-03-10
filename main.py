import os
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

TARGET_SERVER_ID = "9dbd8fbc687149208257283116ed74d5"

def trigger_remote_redeploy(token, server_id):
    """发送远程开机/重启指令"""
    print(f"\n🚀 开始向服务器发送重启/开机指令...")
    url = "https://api.pella.app/server/redeploy"
    
    headers = {
        "Authorization": f"Bearer {token}",
        # 伪装一下 User-Agent 降低被拦截的风险
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 构造 multipart/form-data 表单数据（对应你最后一张图的内容）
    multipart_data = {
        "id": (None, server_id)
    }
    
    try:
        response = requests.post(url, headers=headers, files=multipart_data)
        if response.status_code == 200:
            print("✅ 远程指令发送成功！服务器正在重启/启动。")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print("详细信息:", response.text)
    except Exception as e:
        print(f"❌ 请求发生网络异常: {e}")
    pass

def main():
    print("🌐 启动云端无头浏览器...")
    co = ChromiumOptions()
    co.headless() # 必须开启无头模式
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    page = ChromiumPage(co)
    
    # 1. 先访问一下目标域名，建立上下文，否则无法写入 Cookie
    print("📍 正在初始化域名上下文...")
    page.get('https://www.pella.app/')
    page.wait.load_start()
    
    # 2. 从环境变量中读取并注入你的专属 Cookie
    pella_cookies = os.environ.get('PELLA_COOKIES', '')
    if pella_cookies:
        print("🍪 正在注入登录凭证 (Cookies)...")
        page.set.cookies(pella_cookies)
    else:
        print("⚠️ 未检测到 PELLA_COOKIES 环境变量，可能无法绕过登录！")

    # 3. 启动监听
    listen_url = 'clerk.pella.app/v1/client/sessions'
    page.listen.start(listen_url)
    
    # 4. 带着 Cookie 重新访问面板主页，触发 Token 刷新
    print("⏳ 正在访问 Pella 控制台，等待拦截身份 Token...")
    page.get('https://www.pella.app/')
    
    # 🚨 关键修复：设置 timeout=15 秒，避免无限卡死！
    packet = page.listen.wait(timeout=15)
    
    if packet and packet.request.method == 'POST':
        print("🎯 成功拦截到 Clerk 认证响应！")
        try:
            res_body = packet.response.body
            # 提取 token
            token = res_body.get('client', {}).get('sessions', [{}])[0].get('lastActiveToken', {}).get('jwt')
            
            if token:
                print("🔑 成功提取到授权 Token！")
                trigger_remote_redeploy(token, TARGET_SERVER_ID)
            else:
                print("⚠️ 未找到 Token 字段。")
        except Exception as e:
            print(f"❌ 解析 Token 失败: {e}")
    else:
        print("❌ 拦截超时 (15秒)。页面可能未登录，或者被 Cloudflare 验证码拦截了。")
        # 调试用：打印当前页面源码或截图，看看是不是卡在验证码了
        # print(page.html) 

    page.quit()

if __name__ == "__main__":
    main()

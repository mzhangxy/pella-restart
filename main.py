import json
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless() # 开启无头模式
co.set_argument('--no-sandbox') # 解决 Linux 运行权限问题
co.set_argument('--disable-gpu') 

page = ChromiumPage(co)

# ================= 配置区 =================
# 填入你刚才截图里的那个实例 ID
TARGET_SERVER_ID = "9dbd8fbc687149208257283116ed74d5"
# ==========================================

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

def main():
    print("🌐 启动 DrissionPage 浏览器环境...")
    # 初始化浏览器（这里为了调试方便，默认会显示浏览器窗口。若想无头运行，可配置 ChromiumOptions）
    page = ChromiumPage()
    
    # 启动监听：拦截前往 clerk.pella.app 申请 Token 的 POST 请求
    listen_url = 'clerk.pella.app/v1/client/sessions'
    page.listen.start(listen_url)
    
    print("⏳ 正在访问 Pella 控制台，等待拦截身份 Token...")
    page.get('https://www.pella.app/') # 也可以直接访问你的 dashboard 页面
    
    # 只要网页加载并尝试获取会话，就能抓到这个包
    packet = page.listen.wait()
    
    if packet and packet.request.method == 'POST':
        print("🎯 成功拦截到 Clerk 认证响应！")
        
        try:
            # Clerk 的响应通常是一个 JSON，里面包含了 jwt 字段
            # 注意：实际响应结构可能略有不同，如果不成功，我们需要打印 packet.response.body 看看具体结构
            res_body = packet.response.body
            
            # 通常 token 会藏在这个 JSON 的 client -> sessions -> lastActiveToken -> jwt 类似的位置
            # 这是一个常见的结构示例，具体需要根据你抓到的 JSON 来微调：
            token = res_body.get('client', {}).get('sessions', [{}])[0].get('lastActiveToken', {}).get('jwt')
            
            # 如果上面这种提取方式失败，你可以在控制台打印出完整的 res_body 自己寻找一下键名
            # print(json.dumps(res_body, indent=2))
            
            if token:
                print("🔑 成功提取到授权 Token！")
                # 拿到 Token 后，立刻调用我们的重启函数
                trigger_remote_redeploy(token, TARGET_SERVER_ID)
            else:
                print("⚠️ 抓到了包，但没有在预期的字段找到 Token，请检查 JSON 结构。")
                print("实际响应体:", res_body)
                
        except Exception as e:
            print(f"❌ 解析 Token 失败: {e}")
    else:
        print("⚠️ 未能拦截到目标请求或请求超时。")

    print("\n任务结束，关闭浏览器。")
    page.quit()

if __name__ == "__main__":
    main()

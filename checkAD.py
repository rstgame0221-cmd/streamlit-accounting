from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from ldap3 import Server, Connection, ALL

app = Flask(__name__)

# LINE Bot 設定（v2 SDK）
LINE_CHANNEL_SECRET = '你的ChannelSecret'
LINE_CHANNEL_ACCESS_TOKEN = '你的ChannelAccessToken'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# AD 設定
AD_SERVER = 'your_ad_server'
AD_USER = 'domain\\admin_user'
AD_PASS = 'admin_password'
BASE_DN = 'dc=company,dc=com'

def check_ad_lock(username: str) -> bool:
    """查詢帳號是否被鎖"""
    server = Server(AD_SERVER, get_info=ALL)
    conn = Connection(server, user=AD_USER, password=AD_PASS, auto_bind=True)
    
    conn.search(BASE_DN, f'(&(sAMAccountName={username})(lockoutTime>=1))', attributes=['sAMAccountName'])
    return bool(conn.entries)

# LINE Webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    text = event.message.text.strip()
    
    if text.lower().startswith("查帳號"):
        try:
            username = text.split()[1]
        except IndexError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入帳號，例如：查帳號 jdoe")
            )
            return
        
        if check_ad_lock(username):
            reply = f"⚠️ 帳號 {username} 已被鎖定，請聯絡 IT 解鎖"
        else:
            reply = f"✅ 帳號 {username} 正常"
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入『查帳號 帳號』來查詢")
        )

if __name__ == "__main__":
    app.run(port=5000)
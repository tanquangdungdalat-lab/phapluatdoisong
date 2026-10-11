from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = "2113543425188211580:RXGnBdzXejYgttFkksUOmsNOpkHjVuPfllTtTafwKUOtZwurofvVOMZPBSxEXUWu"
ZALO_API = "https://openapi.zalo.me/v3.0/bot/message"

@app.route('/')
def home():
    return "✅ Bot Nhân Dân GenZ đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📥 Nhận dữ liệu:", data)
    
    event_name = data.get("event_name", "")
    
    if event_name == "message.text.received":
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        sender = message.get("from", {})
        sender_name = sender.get("display_name", "bạn")
        
        # Bỏ tag @Bot ở đầu
        if "@Bot AI Nhân Dân GenZ" in text:
            text = text.replace("@Bot AI Nhân Dân GenZ", "").strip()
        
        print(f"📝 Lệnh sau khi xử lý: [{text}]")
        
        if text == "/start":
            send_message(chat_id, "group", f"👋 Xin chào {sender_name}!\n✅ Bot Nhân Dân GenZ đã sẵn sàng!\nGõ /giup để xem các lệnh có sẵn.")
        
        elif text == "/giup":
            help_text = """📋 Danh sách lệnh có sẵn:
/start — Bắt đầu
/giup — Xem trợ giúp
/echo [nội dung] — Bot sẽ lặp lại nội dung của bạn"""
            send_message(chat_id, "group", help_text)
        
        elif text.startswith("/echo "):
            echo_text = text[6:].strip()
            if echo_text:
                send_message(chat_id, "group", f"🔊 {echo_text}")
            else:
                send_message(chat_id, "group", "⚠️ Vui lòng nhập nội dung!\nVí dụ: /echo Xin chào")
    
    return jsonify({"status": "success"}), 200

def send_message(recipient_id, recipient_type, message_text):
    try:
        headers = {
            "Authorization": f"Bearer {BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id, "type": recipient_type},
            "message": {"text": message_text}
        }
        response = requests.post(ZALO_API, json=payload, headers=headers)
        print(f"📤 Gửi tin nhắn: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Lỗi gửi tin nhắn: {type(e).__name__} - {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

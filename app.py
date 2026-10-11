from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = "2113543425188211580:RXGnBdzXejYgttFkksUOmsNOpkHjVuPfllTtTafwKUOtZwurofvVOMZPBSxEXUWu"
SECRET_TOKEN = "NhanDanGenZ_2026"
ZALO_API = "https://bot.zaloapp.com/v3/message"

@app.route('/')
def home():
    return "✅ Bot Nhân Dân GenZ đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📥 Nhận dữ liệu:", data)
    
    # Xử lý ai đó tham gia nhóm
    if data.get("event_type") == "user_join_group":
        user_name = data["user"].get("display_name", "bạn")
        group_id = data["group"]["id"]
        welcome_msg = f"""🎉 Chào mừng {user_name} đã tham gia nhóm! 🇻🇳

📰 Tin tức • ⚖️ Pháp luật • 🏙️ Đời sống xã hội
Cùng nhau học hỏi và chia sẻ kiến thức nhé! ✨

Gõ /giup để xem các lệnh có sẵn!"""
        send_message(group_id, "group", welcome_msg)
    
    # Xử lý tin nhắn văn bản
    if data.get("event_type") == "message":
        message_text = data["message"].get("text", "").strip()
        user_name = data["sender"].get("display_name", "bạn")
        group_id = data.get("group", {}).get("id")
        
        if not group_id:
            return jsonify({"status": "ok"}), 200
        
        # Lệnh /start
        if message_text == "/start":
            send_message(group_id, "group", f"👋 Xin chào {user_name}! Bot Nhân Dân GenZ đã sẵn sàng!\nGõ /giup để xem hướng dẫn.")
        
        # Lệnh /giup
        elif message_text == "/giup":
            help_text = """📋 Danh sách lệnh:
/start — Bắt đầu
/giup — Xem trợ giúp
/echo [nội dung] — Bot sẽ lặp lại nội dung của bạn"""
            send_message(group_id, "group", help_text)
        
        # Lệnh /echo
        elif message_text.startswith("/echo "):
            echo_text = message_text[6:].strip()
            if echo_text:
                send_message(group_id, "group", f"🔊 {echo_text}")
            else:
                send_message(group_id, "group", "⚠️ Nhập nội dung sau /echo\nVí dụ: /echo Xin chào")
    
    return jsonify({"status": "ok"}), 200

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
        print(f"📤 Gửi tin nhắn: {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = "2113543425188211580:RXGnBdzXejYgttFkksUOmsNOpkHjVuPfllTtTafwKUOtZwurofvVOMZPBSxEXUWu"
SECRET_TOKEN = "NhanDanGenZ_2026"

# ✅ Dùng link chính thức này
ZALO_API = "https://bot.zaloapp.com/v3/message"

@app.route('/')
def home():
    return "✅ Bot Nhân Dân GenZ đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get("X-Zalo-Secret-Token") != SECRET_TOKEN:
        return jsonify({"status": "unauthorized"}), 403
    
    data = request.json
    print("📥 Nhận dữ liệu:", data)
    
    if data.get("event_type") == "user_join_group":
        user_name = data["user"].get("display_name", "bạn")
        group_id = data["group"]["id"]
        
        welcome_msg = f"""🎉 Chào mừng {user_name} đã tham gia nhóm! 🇻🇳

📰 Tin tức • ⚖️ Pháp luật • 🏙️ Đời sống xã hội
Cùng nhau học hỏi và chia sẻ kiến thức nhé! ✨"""
        
        send_message(group_id, "group", welcome_msg)
    
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
        print(f"📤 Gửi tin nhắn: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

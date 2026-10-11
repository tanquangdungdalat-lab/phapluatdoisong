from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

BOT_TOKEN = "2113543425188211580:RXGnBdzXejYgttFkksUOmsNOpkHjVuPfllTtTafwKUOtZwurofvVOMZPBSxEXUWu"
ZALO_API = "https://openapi.zalo.me/v3.0/bot/message"

# Lưu số lần vi phạm
violation_count = {}
MAX_VIOLATION = 3

# === DANH SÁCH TỪ KHÓA CẨN ===
# Từ khóa nội dung không phù hợp
BAD_WORDS = [
    "18+", "xxx", "sex", "porn", "đồi trụy", "khiêu dâm",
    "trần trụi", "ảnh nóng", "video nóng", "người lớn"
]

# Mẫu phát hiện link
LINK_PATTERN = re.compile(r'(https?://|www\.|t\.me/|zalo\.me/|bit\.ly/)', re.IGNORECASE)

@app.route('/')
def home():
    return "✅ Bot Nhân Dân GenZ đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📥 Nhận dữ liệu:", data)
    
    event_name = data.get("event_name", "")
    
    # Tin nhắn văn bản nhận được
    if event_name == "message.text.received":
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        sender = message.get("from", {})
        sender_id = sender.get("id")
        sender_name = sender.get("display_name", "bạn")
        
        # Bỏ tag @Bot ở đầu
        bot_mentioned = "@Bot AI Nhân Dân GenZ" in text
        if bot_mentioned:
            text = text.replace("@Bot AI Nhân Dân GenZ", "").strip()
        
        print(f"📝 Tin nhắn từ {sender_name}: [{text}]")
        
        # ⚠️ KIỂM TRA NỘI DUNG TRƯỚC TIÊN
        is_violation = False
        violation_msg = ""
        
        # 🔗 Phát hiện link
        if LINK_PATTERN.search(text):
            is_violation = True
            violation_msg = f"🚫 {sender_name}, không được gửi link bên ngoài vào nhóm!"
        
        # 🔞 Phát hiện từ ngữ nhạy cảm
        else:
            for word in BAD_WORDS:
                if word.lower() in text.lower():
                    is_violation = True
                    violation_msg = f"🚫 {sender_name}, nội dung này không phù hợp với quy định nhóm!"
                    break
        
        # XỬ LÝ VI PHẠM
        if is_violation and not bot_mentioned:
            violation_count[sender_id] = violation_count.get(sender_id, 0) + 1
            count = violation_count[sender_id]
            
            if count >= MAX_VIOLATION:
                send_message(chat_id, "group", 
                    f"{violation_msg}\n\n🚫 {sender_name} đã vi phạm {count} lần (đã quá giới hạn {MAX_VIOLATION} lần).\nSẽ bị đuổi ra khỏi nhóm!")
                del violation_count[sender_id]
            else:
                send_message(chat_id, "group", 
                    f"{violation_msg}\n⚠️ Lần vi phạm thứ {count}/{MAX_VIOLATION}\nQuá {MAX_VIOLATION} lần sẽ bị đuổi ra khỏi nhóm!")
        
        # === LỆNH BOT ===
        elif bot_mentioned or text.startswith("/"):
            # Lệnh trợ giúp
            if text == "/giup" or text == "":
                help_text = """📋 Danh sách lệnh:

🔹 /giup — Xem trợ giúp
🔹 /danhsach — Xem danh sách vi phạm
🔹 /xoa [tên] — Xóa số lần vi phạm

⚠️ Quy định tự động:
🚫 Không gửi link bên ngoài
🚫 Không gửi nội dung không phù hợp
🔔 Vi phạm 3 lần sẽ bị đuổi ra khỏi nhóm!"""
                send_message(chat_id, "group", help_text)
            
            # Xem danh sách vi phạm
            elif text == "/danhsach":
                if violation_count:
                    msg = "📋 Danh sách số lần vi phạm:\n"
                    for uid, cnt in violation_count.items():
                        msg += f"• ID thành viên: {uid[-6:]} — {cnt} lần\n"
                    send_message(chat_id, "group", msg)
                else:
                    send_message(chat_id, "group", "✅ Chưa có ai vi phạm nội quy!")
            
            # Xóa số lần vi phạm
            elif text.startswith("/xoa "):
                target_info = text[5:].strip()
                send_message(chat_id, "group", f"✅ Đã xóa số lần vi phạm cho: {target_info}!")
    
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
        print(f"📤 Gửi tin nhắn: {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi gửi tin nhắn: {type(e).__name__} - {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

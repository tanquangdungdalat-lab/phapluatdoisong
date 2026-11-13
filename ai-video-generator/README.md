# AI Video Generator Module

Module độc lập minh họa quy trình tạo video tin tức, không thay đổi ứng dụng Flask hiện có ở thư mục gốc.

## Thành phần

- Frontend Next.js: <http://localhost:3005>
- FastAPI và Swagger UI: <http://localhost:8005> và <http://localhost:8005/docs>
- Celery worker: xử lý tác vụ nền, giới hạn một tác vụ đồng thời để phù hợp với một GPU.
- Redis: broker và backend kết quả, chỉ bind ra localhost ở cổng `6380`.

## Yêu cầu

Cần Docker Engine và Docker Compose plugin (`docker compose`).

## Chạy thử

```bash
cd ai-video-generator
docker compose up --build -d
docker compose ps
```

Mở <http://localhost:3005>, nhập tiêu đề/nội dung, chọn tỉ lệ và tạo tác vụ. Xem API tại <http://localhost:8005/docs>.

Dừng dịch vụ:

```bash
docker compose down
```

Dừng và xóa cả dữ liệu Redis:

```bash
docker compose down -v
```

## API

- `POST /api/v1/videos/generate` nhận `{ "title": "...", "content": "...", "aspect_ratio": "16:9" }` và trả mã tác vụ.
- `GET /api/v1/videos/status/{task_id}` trả trạng thái, tiến độ hoặc kết quả.
- `GET /health` kiểm tra API.

Chỉ chấp nhận tỉ lệ `16:9` và `9:16`; tiêu đề tối đa 200 ký tự, nội dung tối đa 20.000 ký tự.

## Giới hạn hiện tại và triển khai model thật

Đây là MVP chạy được để kiểm tra luồng giao diện → API → Redis/Celery → kết quả. Worker hiện **giả lập** xử lý bằng thời gian chờ và trả một video mẫu; video đó không được tạo từ nội dung gửi lên. Module chưa kết nối ComfyUI/Wan/Hunyuan, chưa lưu video lên S3/MinIO và chưa có đăng nhập, phân quyền, giới hạn chi phí hay lưu lịch sử bền vững. Không triển khai công khai như dịch vụ sản xuất trước khi bổ sung các phần này và cấu hình HTTPS, xác thực, giới hạn tài nguyên, giám sát, chính sách lưu dữ liệu và kiểm thử.

Để nối model thật, thay các bước demo trong `backend/worker.py` bằng tích hợp provider/ComfyUI có timeout và xử lý lỗi; lưu file đầu ra vào object storage rồi trả URL có kiểm soát truy cập. Cấu hình GPU/model phụ thuộc môi trường máy chạy worker và cần kiểm thử riêng.

## Cấu hình

Có thể đặt `CORS_ORIGINS` thành danh sách origin cách nhau bằng dấu phẩy khi chạy Compose, ví dụ `CORS_ORIGINS=https://your-domain.example`. `NEXT_PUBLIC_API_URL` là URL API mà trình duyệt người dùng có thể truy cập; giá trị được đưa vào lúc build frontend. Không đặt secret hoặc API key vào biến `NEXT_PUBLIC_*`.

Redis không được công bố ra mạng ngoài. Backend hiện được công bố trên cổng `8005`; nên đặt reverse proxy HTTPS và bảo vệ API bằng xác thực trước khi mở rộng ra Internet.

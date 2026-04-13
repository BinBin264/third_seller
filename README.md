# third_seller

Telegram shop bot: đồng bộ sản phẩm từ bot nguồn (Telethon), áp markup giá theo env, và cung cấp `/menu` + flow đặt hàng qua bot của bạn (python-telegram-bot).

## Tính năng chính

- Đồng bộ sản phẩm từ bot nguồn qua `/menu` (parse inline buttons) → lưu DB.
- Tăng giá tự động theo `PRICE_MARKUP` (đơn vị %).
- Forward thông báo cập nhật kho từ bot nguồn tới toàn bộ user đã `/start` (có rewrite giá trong nội dung).
- Bot bán hàng: `/start`, `/menu`, chọn sản phẩm/số lượng, tạo mã đơn + QR VietQR.

## Yêu cầu

- Python (local) hoặc Docker
- Telegram Bot Token (BotFather)
- Telethon API ID/HASH + số điện thoại để đăng nhập Telethon

## Cấu hình

Tạo file `.env` (không commit) dựa trên `.env.example`.

Biến quan trọng:

- `BOT_TOKEN`: token bot Telegram.
- `ADMIN_ID`, `ADMIN_USERNAME`: admin hỗ trợ.
- `TELETHON_API_ID`, `TELETHON_API_HASH`, `TELETHON_PHONE`: Telethon credentials.
- `SOURCE_BOT`: username bot nguồn (vd `mmoshopacc_bot`).
- `TRIGGER_KEYWORD`: chỉ forward các tin có chứa keyword này (mặc định: `Cập nhật kho hàng`).
- `PRICE_MARKUP`: % markup giá (vd `25`).
- `DB_PATH`: đường dẫn SQLite DB.
- `TELETHON_SESSION_PATH`: đường dẫn session Telethon (không cần đuôi `.session`).

## Chạy local (không Docker)

```bash
cd /path/to/third_seller
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Chạy bằng Docker Compose

```bash
cd /path/to/third_seller
docker compose up --build -d
docker compose logs -f
```

DB nằm ở `./data/` và Telethon session file sẽ được giữ lại theo mount trong `docker-compose.yml`.

## Deploy Render (Background Worker + Persistent Disk)

Repo đã có sẵn `render.yaml`.

- Tạo service bằng Render Blueprint (trỏ tới repo).
- Tạo Persistent Disk (Render sẽ tạo theo `render.yaml`) mount tại `/var/data`.
- Set env vars (Secrets) theo `.env` của bạn.

Mặc định `render.yaml` set:

- `DB_PATH=/var/data/shop.db`
- `TELETHON_SESSION_PATH=/var/data/telethon_session`

## Ghi chú vận hành

- Nếu Telethon chưa đăng nhập, lần đầu có thể cần flow đăng nhập/OTP (tùy cấu hình Telethon).
- Forward hiện tại **chỉ chạy khi message từ `SOURCE_BOT` chứa `TRIGGER_KEYWORD`**.


# 📖 KTSTOCK - Hướng Dẫn Sử Dụng

## 1. Cài Đặt

```bash
# Clone repo
git clone https://github.com/your-repo/KTSTOCK.git
cd KTSTOCK

# Cài dependencies
pip install -e ".[dev]"

# Cấu hình
cp .env.example .env
# Chỉnh sửa .env: thêm GEMINI_API_KEY

# Chạy ứng dụng
streamlit run src/app/main.py
```

## 2. Đăng Nhập

- **Tài khoản mặc định**: `admin` / `Admin@123`
- Tạo tài khoản mới ở tab "Đăng ký"

## 3. Các Tính Năng Chính

### 📊 Dashboard
- Xem chỉ số VN-Index, HNX, UPCOM real-time
- BTC/USDT ticker từ Binance
- Top cổ phiếu giao dịch

### 📈 Phân Tích Cổ Phiếu
- **Tab Biểu đồ**: Candlestick + Moving Averages + Volume
- **Tab Kỹ thuật**: RSI, MACD, Stochastic, tín hiệu tổng hợp
- **Tab Cơ bản**: Thông tin công ty, chỉ số tài chính
- **Tab AI**: Phân tích bằng Gemini AI

### ₿ Phân Tích Crypto
- Candlestick chart theo interval (1D, 4H, 1H, 15m)
- Top 20 crypto theo volume
- Technical analysis + AI

### 🔍 Bộ Lọc Cổ Phiếu
- 5 preset: Giá trị, Tăng trưởng, Cổ tức, Momentum, Volume breakout
- Custom filters: thêm/xóa bộ lọc tùy ý

### 💼 Danh Mục Đầu Tư
- Tạo portfolio, thêm vị thế
- Xem P/L tổng hợp + biểu đồ tròn phân bổ
- Tối ưu hóa Markowitz (Monte Carlo simulation)

### 🔔 Cảnh Báo
- 7 loại: giá vượt/dưới ngưỡng, RSI, volume, MACD
- Thông báo in-app, Telegram, Email

### 🤖 AI Insights
- Chat trực tiếp với Gemini AI về thị trường
- Tạo báo cáo thị trường tự động

### ⚙️ Cài Đặt
- Chuyển ngôn ngữ (VI/EN)
- Quản lý cache
- Đổi mật khẩu

## 4. Phím Tắt

| Phím | Chức năng |
|------|-----------|
| Sidebar menu | Chuyển trang |
| 🌐 VI/EN | Đổi ngôn ngữ |
| 🚪 Logout | Đăng xuất |

## 5. FAQ

**Q: Dữ liệu cập nhật bao lâu?**
A: Dữ liệu cổ phiếu cache 1 giờ, crypto ticker cache 30 giây.

**Q: Cần internet không?**
A: Có. Tuy nhiên, dữ liệu đã tải sẽ lưu trong SQLite để dùng offline.

**Q: API key Gemini ở đâu?**
A: Cấu hình trong file `.env` với biến `GEMINI_API_KEY`.

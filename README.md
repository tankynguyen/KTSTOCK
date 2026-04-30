# 📊 KT Stock Analyzer (KTSTOCK)

> Nền tảng phân tích chứng khoán & crypto thông minh — Python + Streamlit + AI

[![Tests](https://img.shields.io/badge/tests-67%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![Streamlit](https://img.shields.io/badge/streamlit-latest-red)]()

## ✨ Tính năng

### 📊 Thị trường
- **Dashboard** real-time: VN-Index, HNX, UPCOM, BTC/USDT
- **Candlestick chart** với Moving Averages + Volume
- **Top 20 crypto** theo volume từ Binance

### 📐 Phân tích kỹ thuật (15+ chỉ báo)
- RSI, MACD, Bollinger Bands, Stochastic, ADX, ATR
- Ichimoku Cloud, OBV, VWAP, SMA/EMA/WMA
- **Tín hiệu tổng hợp** (Buy/Sell/Hold) với confidence scoring

### 📋 Phân tích cơ bản
- P/E, P/B, P/S, PEG, EV/EBITDA
- ROE, ROA, Gross/Net Margin, D/E
- **DCF Valuation** (Discounted Cash Flow)

### 🤖 AI & Machine Learning
- **Gemini AI**: Phân tích cổ phiếu/crypto, tóm tắt tin, chat
- **XGBoost**: Dự đoán giá với 25 features kỹ thuật
- **Sentiment Analysis**: Phân tích cảm xúc VI + EN

### 🔍 Công cụ
- **Bộ lọc cổ phiếu**: 5 preset + custom filters
- **Portfolio Manager**: CRUD + Markowitz optimizer (Monte Carlo)
- **Cảnh báo**: 7 điều kiện + Telegram/Email notification
- **Export**: Excel + CSV

### 🔐 Bảo mật
- Đăng nhập/đăng ký với bcrypt hash
- RBAC 4 cấp: Admin → Analyst → User → Guest
- Session management (24h token)

## 🚀 Cài đặt nhanh

```bash
git clone https://github.com/your-repo/KTSTOCK.git
cd KTSTOCK
pip install -e ".[dev]"
cp .env.example .env    # Cấu hình API keys
streamlit run src/app/main.py
```

**Tài khoản mặc định**: `admin` / `Admin@123`

## 📁 Cấu trúc dự án

```
KTSTOCK/
├── src/
│   ├── ai/          # Gemini, XGBoost, Sentiment
│   ├── app/         # Streamlit UI (14 pages)
│   ├── auth/        # Authentication & RBAC
│   ├── charts/      # Plotly chart engine
│   ├── core/        # Analysis, Screener, Portfolio, Alerts
│   ├── data/        # Connectors, Models, Repositories, Database
│   ├── services/    # Cache, Async, Notification, Export
│   └── utils/       # Config, Logger, Constants, Helpers
├── tests/           # 67 unit tests
├── docs/            # Documentation
└── pyproject.toml   # Configuration
```

## 🛠️ Công nghệ

- **Core**: Python 3.11+, Streamlit
- **Data**: vnstock (Free + Sponsored), Binance API, pandas
- **AI**: Google Gemini, XGBoost, scikit-learn
- **Charts**: Plotly (candlestick, technical, pie, gauge, heatmap)
- **Database**: SQLite (15 tables, WAL mode)
- **Cache**: 3-layer (Memory → File → Parquet)

## 📖 Tài liệu

- [Thiết kế hệ thống](docs/design/system_architecture.md)
- [Hướng dẫn sử dụng](docs/guides/user_guide.md)
- [Hướng dẫn phát triển](docs/guides/developer_guide.md)
- [Quy trình phát triển](docs/processes/development_workflow.md)

## 🧪 Testing

```bash
python -m pytest tests/ -v              # Chạy tests
python -m pytest tests/ --cov=src       # Với coverage
```

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

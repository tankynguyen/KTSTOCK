# 📐 KTSTOCK - Thiết Kế Hệ Thống

## 1. Tổng Quan

KTSTOCK là nền tảng phân tích chứng khoán & crypto thông minh, được xây dựng với kiến trúc 6-layer.

## 2. Kiến Trúc

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer                  │
│    Streamlit UI │ Charts │ i18n │ Components      │
├─────────────────────────────────────────────────┤
│              Authentication Layer                │
│         Auth Manager │ RBAC │ Sessions            │
├─────────────────────────────────────────────────┤
│              Business Logic Layer                │
│  Technical │ Fundamental │ Screener │ Portfolio   │
│           Alert Engine │ Sentiment                │
├─────────────────────────────────────────────────┤
│              AI & ML Layer                       │
│    Gemini │ XGBoost │ Sentiment NLP               │
├─────────────────────────────────────────────────┤
│              Data Integration Layer              │
│  vnstock Free │ vnstock Sponsored │ Binance WS    │
├─────────────────────────────────────────────────┤
│              Data & Cache Layer                  │
│     SQLite (WAL) │ File Cache │ Parquet Cache     │
└─────────────────────────────────────────────────┘
```

## 3. Database Schema

- **15 tables**: users, sessions, symbols, price_history, portfolios, positions, alerts, alert_history, ai_analysis, watchlists, app_config, cache_metadata, news_articles, user_settings, audit_log
- **SQLite WAL mode** cho concurrent reads
- **Thread-safe** connection manager (Singleton pattern)

## 4. Data Flow

```
User Request → Streamlit UI → Auth Check → Business Logic
    ↓
Repository Pattern → Cache Check → Connector (API) → Database
    ↓
Response → Chart Engine → UI Render
```

## 5. Cache Strategy

| Layer | Storage | TTL | Use Case |
|-------|---------|-----|----------|
| Memory | RAM dict | 30s-5m | Real-time quotes |
| File | Pickle | 1h-24h | Historical data |
| DataFrame | Parquet | 24h | Large datasets |

## 6. Auth & RBAC

| Role | Level | Permissions |
|------|-------|-------------|
| Admin | 3 | Full access + user management |
| Analyst | 2 | All analysis + AI + export |
| User | 1 | Basic analysis + portfolio |
| Guest | 0 | View dashboard only |

## 7. Connector Architecture

```
StockRepository
  ├── VnstockSponsoredConnector (ưu tiên)
  ├── VnstockFreeConnector (fallback)
  └── SQLite DB (offline cache)

CryptoRepository
  ├── BinanceConnector (REST + WebSocket)
  └── SQLite DB (offline cache)
```

## 8. AI Integration

- **Gemini**: Stock/crypto analysis, news summary, market reports, chat
- **XGBoost**: Price prediction with 25 technical features
- **Sentiment**: Rule-based Vietnamese + English keyword analysis

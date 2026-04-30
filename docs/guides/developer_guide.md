# 🛠️ KTSTOCK - Hướng Dẫn Phát Triển

## 1. Cấu Trúc Mã Nguồn

```
src/
├── ai/           → AI & ML (providers, models, services)
├── app/          → Streamlit UI (main, pages, components, i18n)
├── auth/         → Authentication & RBAC
├── charts/       → Chart engines (Plotly)
├── core/         → Business logic (analysis, screener, portfolio, alerts)
├── data/         → Data layer (connectors, models, repositories, database)
├── services/     → Service layer (cache, async, notification, export)
└── utils/        → Utilities (config, logger, constants, helpers, decorators)
```

## 2. Quy Tắc Code

### Naming
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Patterns
- **Repository Pattern**: `data/repositories/` — tách data access khỏi business logic
- **Singleton**: `DatabaseManager`, `CacheService` — 1 instance duy nhất
- **Strategy**: Connectors — swap giữa Free/Sponsored/Binance
- **Decorator**: `@timer`, `@retry`, `@require_role` — cross-cutting concerns

### Conventions
- Tất cả text UI phải dùng `t("key", lang)` cho i18n
- API keys bắt buộc trong `.env`, không hardcode
- Mọi DB query qua `DatabaseManager`, không dùng raw sqlite3
- Log qua `loguru`, không dùng `print()`

## 3. Thêm Tính Năng Mới

### Bước 1: Tạo connector (nếu cần data mới)
```python
# src/data/connectors/new_connector.py
class NewConnector(BaseConnector):
    def connect(self): ...
    def get_historical_data(self, symbol, start, end): ...
```

### Bước 2: Tạo business logic
```python
# src/core/analysis/new_analysis.py
class NewAnalysis:
    def analyze(self, df): ...
```

### Bước 3: Tạo page UI
```python
# src/app/pages/new_page.py
def render_new_page():
    st.markdown("### New Page")
    ...
```

### Bước 4: Thêm route vào main.py
```python
elif page == "new_page":
    from src.app.pages.new_page import render_new_page
    render_new_page()
```

### Bước 5: Thêm i18n keys
```json
// locales/vi.json
"nav.new_page": "Trang mới"
```

### Bước 6: Viết unit tests
```python
# tests/unit/test_new.py
class TestNewAnalysis:
    def test_analyze(self): ...
```

## 4. Chạy Tests

```bash
# Chạy tất cả
python -m pytest tests/ -v

# Chạy 1 file
python -m pytest tests/unit/test_analysis.py -v

# Với coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## 5. Database Migration

Schema SQL ở `src/data/database/schema.sql`. Khi thêm table:
1. Thêm CREATE TABLE vào schema.sql
2. Xóa `data/ktstock.db`
3. Chạy lại app → DB tự tạo lại

## 6. Deploy

```bash
# Streamlit Community Cloud
# 1. Push code lên GitHub
# 2. Vào share.streamlit.io → Deploy
# 3. Cấu hình secrets (API keys)
```

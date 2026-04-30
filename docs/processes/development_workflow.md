# 🔄 KTSTOCK - Quy Trình Phát Triển

## Quy Trình Nhận Yêu Cầu Mới

```
1. 📋 Nhận yêu cầu → Phân tích → Tạo Issue/Task
2. 📐 Thiết kế → Xác định files ảnh hưởng → Review
3. 💻 Implement → Code → Unit tests
4. ✅ Verify → Chạy tests → Test UI → Review
5. 📝 Document → Cập nhật docs → Changelog
6. 🚀 Deploy → Push → CI/CD → Verify production
```

## Git Branch Strategy

```
main          ← Production (stable)
  └── dev     ← Development
       ├── feature/xxx   ← Tính năng mới
       ├── fix/xxx       ← Bug fixes
       └── hotfix/xxx    ← Production fixes
```

## Commit Message Format

```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore
Scope: auth, data, analysis, ui, ai, core

Examples:
  feat(analysis): add Ichimoku indicator
  fix(auth): resolve session timeout issue
  docs(guides): update user guide with screener
```

## Code Review Checklist

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] No new deprecation warnings
- [ ] i18n keys added for new UI text
- [ ] API keys not hardcoded
- [ ] Docstrings on public functions
- [ ] Logger used instead of print()

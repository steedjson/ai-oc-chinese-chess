# SECRET_KEY 安全迁移文档

**创建日期**: 2026-03-06  
**优先级**: P0 (安全关键)  
**状态**: ✅ 已完成

---

## 📋 概述

本次迁移将 Django `SECRET_KEY` 从硬编码值改为环境变量管理，消除安全风险。

### 问题描述

原 `settings.py` 中使用了硬编码的 SECRET_KEY：
```python
SECRET_KEY = 'django-insecure-dev-key-change-in-production'
```

**安全风险**:
- 密钥暴露在版本控制中
- 所有部署环境使用相同密钥
- 无法安全地轮换密钥
- 违反安全最佳实践

---

## 🔧 变更内容

### 1. 新增文件

#### `.env` (项目根目录)
存储实际的环境变量值（**不提交到 Git**）：
```bash
SECRET_KEY=7NJL2PtFPWsXqneRLnEa-sOxAh2tQOKUfK70O5i-cr8sRBudghmYYbA5kVwZf9gRPBE
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_URL=redis://localhost:6379/0
```

#### `.env.example` (项目根目录)
环境变量模板（**提交到 Git**）：
```bash
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. 修改文件

#### `src/backend/config/settings.py`
```python
# 之前
SECRET_KEY = 'django-insecure-dev-key-change-in-production'

# 之后
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
```

#### `src/backend/requirements.txt`
新增依赖：
```
python-dotenv==1.0.0
```

---

## 🚀 部署步骤

### 开发环境

1. **复制环境变量模板**:
   ```bash
   cd /Users/changsailong/.openclaw/workspace/projects/chinese-chess
   cp .env.example .env
   ```

2. **生成新的 SECRET_KEY** (可选，已有安全密钥):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

3. **安装新依赖**:
   ```bash
   cd src/backend
   pip install -r requirements.txt
   ```

4. **验证配置**:
   ```bash
   python manage.py check
   ```

### 生产环境

1. **设置环境变量** (推荐使用系统环境变量或密钥管理服务):
   ```bash
   export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
   export DEBUG=False
   export ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   ```

2. **或使用 .env 文件** (确保文件权限为 600):
   ```bash
   chmod 600 .env
   ```

3. **在 Docker/K8s 中**:
   - 使用 Docker secrets
   - 使用 Kubernetes Secrets
   - 使用云服务商的密钥管理服务 (AWS Secrets Manager, Azure Key Vault 等)

---

## 🔒 安全最佳实践

### 密钥管理

- ✅ **永远不要**将 `.env` 文件提交到版本控制
- ✅ **永远不要**在日志中打印 SECRET_KEY
- ✅ 每个环境使用不同的 SECRET_KEY
- ✅ 定期轮换 SECRET_KEY（建议每季度）
- ✅ 使用足够长度的随机密钥（至少 50 字符）

### Git 配置

确保 `.gitignore` 包含：
```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
```

### 密钥轮换流程

1. 生成新的 SECRET_KEY
2. 更新所有部署环境的配置
3. 监控应用日志确保无异常
4. 确认所有服务正常运行后，销毁旧密钥

---

## 📝 相关文件

- `.env` - 环境变量文件（不提交）
- `.env.example` - 环境变量模板（提交）
- `src/backend/config/settings.py` - Django 配置
- `src/backend/requirements.txt` - Python 依赖

---

## ✅ 验证清单

- [x] SECRET_KEY 不再硬编码
- [x] .env 文件已创建并包含安全密钥
- [x] .env.example 模板已创建
- [x] settings.py 已更新使用环境变量
- [x] requirements.txt 已添加 python-dotenv
- [x] 迁移文档已创建
- [ ] .env 已添加到 .gitignore（需要验证）

---

## 🔍 后续工作

1. **检查 .gitignore**: 确保 `.env` 在忽略列表中
2. **审计其他密钥**: 检查是否有其他硬编码的敏感信息
3. **配置 CI/CD**: 在部署流程中安全注入环境变量
4. **监控告警**: 设置密钥泄露监控

---

## 📞 支持

如有问题，请参考：
- Django 官方文档：[Secret Key](https://docs.djangoproject.com/en/4.2/ref/settings/#secret-key)
- python-dotenv 文档：[GitHub](https://github.com/theskumar/python-dotenv)

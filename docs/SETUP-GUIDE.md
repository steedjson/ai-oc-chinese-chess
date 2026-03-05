# 中国象棋 - 开发环境搭建指南

**最后更新**：2026-03-03  
**适用版本**：v1.0.0

---

## 📋 前置要求

### 系统要求

| 操作系统 | 最低要求 | 推荐配置 |
|---------|---------|---------|
| macOS | 10.15+ | 12.0+ |
| Linux | Ubuntu 20.04+ | Ubuntu 22.04+ |
| Windows | 10 | 11 |

### 软件要求

| 软件 | 版本要求 | 验证命令 |
|------|---------|---------|
| Python | ≥ 3.11 | `python --version` |
| pip | ≥ 23.0 | `pip --version` |
| Git | ≥ 2.30 | `git --version` |
| Redis | ≥ 6.0 | `redis-server --version` |
| PostgreSQL | ≥ 14 | `psql --version` |

---

## 🚀 安装步骤

### 步骤 1：克隆项目

```bash
git clone <repository-url>
cd chinese-chess
```

### 步骤 2：创建 Python 虚拟环境

**macOS/Linux**：
```bash
# 使用 Python 3.11+ 创建虚拟环境
python3.11 -m venv .venv

# 或者使用 pyenv（推荐）
pyenv install 3.12.4
pyenv local 3.12.4
python -m venv .venv
```

**Windows**：
```bash
py -3.11 -m venv .venv
```

### 步骤 3：激活虚拟环境

**macOS/Linux**：
```bash
source .venv/bin/activate
```

**Windows**：
```bash
.venv\Scripts\activate
```

激活后，命令行前缀应显示 `(.venv)`。

### 步骤 4：安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装后端依赖
pip install -r src/backend/requirements.txt
```

### 步骤 5：配置环境变量

创建 `.env` 文件（在 `src/backend/` 目录下）：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/chinese_chess

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# Django 配置
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# JWT 配置
JWT_EXPIRATION_HOURS=2
```

### 步骤 6：数据库迁移

```bash
cd src/backend

# 创建数据库
createdb chinese_chess

# 运行迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

### 步骤 7：启动开发服务器

```bash
# 在 src/backend/ 目录下
python manage.py runserver
```

访问 http://localhost:8000/admin/ 验证安装。

---

## ✅ 验证安装

### 1. 检查 Python 版本

```bash
source .venv/bin/activate
python --version
# 应输出：Python 3.11.x 或 Python 3.12.x
```

### 2. 检查依赖安装

```bash
pip list | grep Django
# 应输出：Django 5.0.0
```

### 3. 检查健康检查端点

```bash
curl http://localhost:8000/api/v1/health/
```

预期响应：
```json
{
    "status": "healthy",
    "components": {
        "django": {"status": "healthy", "version": "5.0.0"},
        "database": {"status": "healthy", "backend": "..."},
        "cache": {"status": "healthy", "backend": "..."},
        "python": {"status": "healthy", "version": "3.12.x"}
    }
}
```

### 4. 运行测试

```bash
cd src/backend
pytest --ds=config.settings.test -v
```

---

## 🔧 常见问题

### 问题 1：Python 版本过低

**错误**：`Python 3.9.6 is not supported. Minimum version is 3.11.`

**解决**：
```bash
# 安装 pyenv（macOS/Linux）
brew install pyenv

# 安装 Python 3.12
pyenv install 3.12.4

# 设置项目 Python 版本
pyenv local 3.12.4

# 重新创建虚拟环境
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r src/backend/requirements.txt
```

### 问题 2：虚拟环境未激活

**错误**：`ModuleNotFoundError: No module named 'django'`

**解决**：
```bash
# 激活虚拟环境
source .venv/bin/activate

# 验证
which python
# 应指向 .venv/bin/python
```

### 问题 3：数据库连接失败

**错误**：`connection refused to server: localhost:5432`

**解决**：
```bash
# 启动 PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# 创建数据库
createdb chinese_chess
```

### 问题 4：WebSocket 连接 403

**错误**：WebSocket 连接返回 403 错误

**解决**：
1. 确保使用有效的 JWT Token
2. Token 应通过 URL 参数传递：`/ws/game/{game_id}/?token={your_token}`
3. 检查 Token 是否过期

---

## 📚 下一步

- [ ] 阅读 [架构设计文档](architecture.md)
- [ ] 阅读 [需求文档](requirements.md)
- [ ] 查看 [功能规划](features/)
- [ ] 运行测试套件

---

## 🆘 获取帮助

如有问题，请：
1. 查看 [BUGFIX-REPORT.md](BUGFIX-REPORT.md) 了解已知问题和修复
2. 查看项目文档目录
3. 联系开发团队

---

**文档维护者**：高级开发工程师  
**最后审核**：2026-03-03

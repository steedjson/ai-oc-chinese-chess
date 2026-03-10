# 模块依赖关系图

> 最后更新：2026-03-06  
> 分析工具：`scripts/dependency_analyzer.py`

## 📊 概览

| 指标 | 数量 | 状态 |
|------|------|------|
| 总模块数 | 83 | - |
| 循环依赖 | 0 | ✅ 良好 |
| 孤立模块 | 26 | ⚠️ 需关注 |
| 过度依赖模块 | 14 | ⚠️ 需优化 |
| 核心模块 | 7 | ✅ 稳定 |

## 🎯 模块分层

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (App Layer)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   health    │  │   manage    │  │   scripts   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    功能层 (Feature Layer)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    games    │  │  ai_engine  │  │ matchmaking │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   puzzles   │  │daily_challenge│                         │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     核心层 (Core Layer)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    users    │  │config       │  │ websocket   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │authentication│  │   common    │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 模块目录结构

```
src/backend/
├── config/              # 核心配置层
│   ├── settings.py      # Django 配置
│   ├── urls.py          # 主路由
│   ├── asgi.py          # ASGI 配置
│   └── wsgi.py          # WSGI 配置
│
├── common/              # 公共工具层
│   ├── exceptions.py    # 自定义异常
│   └── health.py        # 健康检查
│
├── users/               # 用户核心层
│   ├── models.py        # 用户模型
│   ├── serializers.py   # 序列化器
│   ├── views.py         # 视图
│   └── urls.py          # 路由
│
├── authentication/      # 认证层
│   ├── services.py      # 认证服务
│   ├── views.py         # 认证视图
│   └── urls.py          # 认证路由
│
├── websocket/           # WebSocket 核心层
│   ├── config.py        # WebSocket 配置
│   ├── consumers.py     # 消费者
│   ├── routing.py       # 路由
│   └── middleware.py    # 中间件
│
├── games/               # 游戏功能层
│   ├── models.py        # 游戏模型
│   ├── consumers.py     # 游戏消费者
│   ├── engine.py        # 游戏引擎
│   ├── fen_service.py   # FEN 服务
│   ├── chat.py          # 聊天功能
│   ├── spectator.py     # 观战功能
│   └── ranking_*.py     # 排名系统
│
├── ai_engine/           # AI 引擎层
│   ├── models.py        # AI 游戏模型
│   ├── services.py      # AI 服务
│   ├── engine_pool.py   # 引擎池
│   ├── consumers.py     # AI 消费者
│   └── tasks.py         # 异步任务
│
├── matchmaking/         # 匹配系统层
│   ├── models.py        # 匹配模型
│   ├── queue.py         # 匹配队列
│   ├── algorithm.py     # 匹配算法
│   ├── elo.py           # ELO 等级分
│   └── consumers.py     # 匹配消费者
│
├── puzzles/             # 谜题功能层
│   ├── models.py        # 谜题模型
│   ├── services.py      # 谜题服务
│   └── views.py         # 谜题视图
│
├── daily_challenge/     # 每日挑战层
│   ├── models.py        # 挑战模型
│   ├── services.py      # 挑战服务
│   └── views.py         # 挑战视图
│
└── health/              # 健康检查层
    └── views.py         # 健康检查端点
```

## 🔗 核心依赖关系

### 高频被依赖模块 (Core Modules)

这些模块是系统的核心基础设施，被多个模块依赖：

| 模块 | 被依赖次数 | 说明 |
|------|-----------|------|
| `users` | 9 | 用户模型和认证基础 |
| `websocket.config` | 6 | WebSocket 配置中心 |
| `config` | 6 | Django 应用配置 |
| `ai_engine.config` | 6 | AI 引擎配置 |
| `games` | 5 | 游戏核心模块 |
| `puzzles` | 4 | 谜题模块 |
| `authentication` | 4 | 认证服务 |

### 过度依赖模块 (需优化)

这些模块导入了过多其他模块，可能存在职责过重的问题：

| 模块 | 导入数量 | 建议 |
|------|---------|------|
| `websocket.middleware` | 8 | 考虑拆分中间件职责 |
| `websocket.consumers` | 5 | 正常，WebSocket 消费者需要多模块协作 |
| `health.views` | 5 | 正常，健康检查需要访问多模块状态 |
| `matchmaking.consumers` | 5 | 正常，匹配逻辑复杂 |
| `games.consumers` | 5 | 正常，游戏消费者需要多模块支持 |
| `games.websocket_reconnect*` | 5 | 考虑合并两个重连实现 |

## 📈 可视化图表

### Graphviz DOT 格式

生成的 DOT 文件：[`dependencies.dot`](./dependencies.dot)

使用 Graphviz 生成 PNG：
```bash
dot -Tpng docs/architecture/dependencies.dot -o docs/architecture/dependencies.png
```

### HTML 交互式图表

打开交互式依赖图：[`dependency-graph.html`](./dependency-graph.html)

在浏览器中打开该文件，可以：
- 拖拽和缩放查看模块关系
- 点击节点查看模块详情
- 不同颜色表示不同层级（绿色=核心层，蓝色=功能层，橙色=应用层）

## 🔄 循环依赖分析

**状态：✅ 无循环依赖**

当前未发现模块间的循环依赖，这是一个良好的架构信号。

### 保持无循环依赖的建议

1. **依赖倒置**：高层模块不应依赖低层模块，都应依赖抽象
2. **接口隔离**：使用接口或抽象类定义模块边界
3. **定期审查**：在 CI/CD 中集成依赖分析，防止新引入循环依赖

## ⚠️ 孤立模块分析

发现 26 个孤立模块（既没有导入其他模块，也没有被其他模块导入）：

### 可能需要关注的孤立模块

| 模块 | 类型 | 建议 |
|------|------|------|
| `common` | 工具模块 | 检查是否被正确使用 |
| `common.exceptions` | 异常定义 | 应被全局导入使用 |
| `games.fen_service` | 服务模块 | 检查是否被游戏引擎使用 |
| `games.ranking_services` | 服务模块 | 检查是否被排名视图使用 |
| `games.serializers` | 序列化器 | 应被视图使用 |
| `games.views` | 视图 | 应被路由使用 |
| `users.models` | 模型 | 应被其他模块使用 |
| `users.serializers` | 序列化器 | 应被视图使用 |

**注意**：部分孤立模块可能是由于分析工具只追踪模块级 import，而 Django 的很多依赖是通过字符串引用（如 `settings.AUTH_USER_MODEL`）实现的，这是正常现象。

## 💡 重构建议

### 高优先级

1. **合并重连实现**
   - `games.websocket_reconnect.py` 和 `games.websocket_reconnect_optimized.py` 功能重复
   - 建议保留优化版本，删除旧版本

2. **清理未使用导入**
   - 检查 `websocket.middleware` 的 8 个导入是否都必要
   - 考虑将中间件拆分为更专注的组件

### 中优先级

3. **统一序列化器位置**
   - 各 app 的 serializers.py 都是孤立的
   - 考虑集中管理或确保被正确引用

4. **优化配置模块**
   - `ai_engine.config` 被依赖 6 次，确保配置清晰文档化
   - 考虑将配置拆分为通用配置和 AI 特定配置

### 低优先级

5. **文档化模块边界**
   - 为每个模块添加 `__init__.py` 文档字符串
   - 明确说明模块的公共 API

## 🚀 CI/CD 集成

### 在 CI 中自动检查依赖

```yaml
# .github/workflows/dependency-check.yml
name: Dependency Check

on: [push, pull_request]

jobs:
  dependency-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Run dependency analysis
        run: |
          python scripts/dependency_analyzer.py \
            --root src/backend \
            --output-dir docs/architecture \
            --format json
      
      - name: Check for cycles
        run: |
          python -c "
          import json
          with open('docs/architecture/dependency-analysis.json') as f:
              data = json.load(f)
          if data['cycles']:
              print('❌ Found cyclic dependencies!')
              exit(1)
          print('✅ No cyclic dependencies')
          "
      
      - name: Upload dependency graph
        uses: actions/upload-artifact@v3
        with:
          name: dependency-graph
          path: docs/architecture/
```

### 依赖变更检测

在 PR 中添加检查：

```bash
# 比较当前分支与 main 分支的依赖变化
python scripts/dependency_analyzer.py --format json
git checkout main
python scripts/dependency_analyzer.py --format json --output-dir /tmp/main-deps
# 使用 diff 工具比较两个 JSON 文件
```

## 📝 使用说明

### 运行依赖分析

```bash
# 基本用法
cd projects/chinese-chess
python3 scripts/dependency_analyzer.py

# 指定输出目录
python3 scripts/dependency_analyzer.py --output-dir docs/architecture

# 只生成特定格式
python3 scripts/dependency_analyzer.py --format dot  # 只生成 DOT
python3 scripts/dependency_analyzer.py --format html # 只生成 HTML
python3 scripts/dependency_analyzer.py --format json # 只生成 JSON

# 指定项目根目录
python3 scripts/dependency_analyzer.py --root src/backend
```

### 输出文件

| 文件 | 格式 | 用途 |
|------|------|------|
| `dependencies.dot` | Graphviz DOT | 生成静态图表 |
| `dependency-graph.html` | HTML | 交互式可视化 |
| `dependency-analysis.json` | JSON | 数据分析和 CI 集成 |
| `DEPENDENCY-GRAPH.md` | Markdown | 本文档 |

## 🔧 工具实现细节

分析工具位于：[`scripts/dependency_analyzer.py`](../scripts/dependency_analyzer.py)

### 核心功能

1. **AST 解析**：使用 Python ast 模块解析 import 语句
2. **依赖图构建**：构建有向图表示模块依赖
3. **循环检测**：使用 DFS 算法检测循环依赖
4. **层级分析**：根据模块路径自动分层
5. **可视化输出**：生成 DOT、HTML、JSON 多种格式

### 排除模式

默认排除以下路径：
- `venv/` - Python 虚拟环境
- `__pycache__/` - Python 缓存
- `migrations/` - Django 迁移文件
- `node_modules/` - Node.js 依赖
- `tests/` - 测试文件
- `test_*.py` - 测试脚本

---

## 📚 相关文档

- [模块分析报告](./MODULE-ANALYSIS.md) - 详细的模块分析和建议
- [架构设计文档](./ARCHITECTURE.md) - 系统架构设计
- [Django 最佳实践](../../docs/django/README.md) - Django 开发规范

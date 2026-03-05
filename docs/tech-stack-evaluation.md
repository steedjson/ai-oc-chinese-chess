# 🛠️ 中国象棋项目 - 技术栈评估与选型

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**最后更新**：2026-03-03  
**状态**：已完成  
**作者**：architect agent

---

## 1. 前端技术栈评估与选择

### 1.1 前端框架

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **React 18** | 生态最丰富、TypeScript 支持优秀、组件化成熟、人才储备多 | Hooks 学习曲线、版本迭代快 | ⭐⭐⭐⭐⭐ |
| **Vue 3** | 上手简单、文档友好、性能优秀 | 生态略小于 React、企业级应用案例较少 | ⭐⭐⭐⭐ |
| **Svelte** | 无虚拟 DOM、编译时优化、代码量少 | 生态较小、社区资源有限 | ⭐⭐⭐ |
| **SolidJS** | 性能最佳、响应式原理先进 | 生态非常小、生产案例少 | ⭐⭐ |

**✅ 最终选择：React 18 + TypeScript**

**理由**：
- 项目架构已明确采用 React
- TypeScript 提供类型安全，减少运行时错误
- 丰富的组件库和工具链支持
- 便于后续招聘和协作

---

### 1.2 状态管理

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Zustand** | 轻量 (1KB)、API 简洁、TypeScript 友好、无样板代码 | 功能相对简单、DevTools 需额外配置 | ⭐⭐⭐⭐⭐ |
| **Redux Toolkit** | 功能完善、DevTools 强大、生态成熟 | 样板代码多、学习曲线陡、包体积大 | ⭐⭐⭐ |
| **Jotai** | 原子化状态、性能优秀、TypeScript 友好 | 概念新颖、学习成本 | ⭐⭐⭐⭐ |
| **Valtio** | 响应式代理、简洁 API | 社区较小、文档不够完善 | ⭐⭐⭐ |
| **Context + Hooks** | 零依赖、原生支持 | 性能问题、不适合复杂状态 | ⭐⭐ |

**✅ 最终选择：Zustand**

**理由**：
- 轻量级，符合项目零预算约束
- API 简洁，开发效率高
- 完美的 TypeScript 支持
- 适合中小型项目的状态管理需求

**使用示例**：
```typescript
import { create } from 'zustand'

interface GameState {
  fen: string
  turn: 'red' | 'black'
  status: 'waiting' | 'playing' | 'finished'
  setFen: (fen: string) => void
  makeMove: (from: string, to: string) => void
}

export const useGameStore = create<GameState>((set) => ({
  fen: 'start_position',
  turn: 'red',
  status: 'waiting',
  setFen: (fen) => set({ fen }),
  makeMove: (from, to) => set((state) => ({
    fen: updateFen(state.fen, from, to),
    turn: state.turn === 'red' ? 'black' : 'red'
  }))
}))
```

---

### 1.3 UI 组件库

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Ant Design** | 组件丰富、企业级质量、文档完善、中文友好 | 包体积大、样式定制复杂 | ⭐⭐⭐⭐⭐ |
| **MUI (Material-UI)** | 设计精美、组件齐全、主题系统强大 | 风格偏西式、包体积大 | ⭐⭐⭐⭐ |
| **Chakra UI** | 样式系统灵活、TypeScript 友好、可访问性好 | 组件数量较少、国内使用少 | ⭐⭐⭐⭐ |
| **Headless UI** | 无样式、完全可控、轻量 | 需自行实现样式、开发成本高 | ⭐⭐⭐ |
| **Naive UI** | 国产、TypeScript 原生、主题丰富 | 社区相对较小 | ⭐⭐⭐⭐ |

**✅ 最终选择：Ant Design 5.x**

**理由**：
- 组件最丰富，覆盖后台管理所有需求
- 中文文档完善，学习成本低
- 企业级质量，稳定性有保障
- 支持后台管理端 Ant Design Pro 模板

**备选方案**：用户端可使用 Tailwind CSS 自定义样式，减少包体积

---

### 1.4 构建工具

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Vite** | 极速启动、热更新快、生产优化好、配置简单 | 插件生态相对 Webpack 较小 | ⭐⭐⭐⭐⭐ |
| **Webpack 5** | 生态最成熟、插件丰富、高度可配置 | 配置复杂、构建速度慢 | ⭐⭐⭐ |
| **Turbopack** | 性能最佳、Rust 编写 | 早期阶段、不稳定 | ⭐⭐ |
| **Parcel** | 零配置、易用 | 可定制性差、生态小 | ⭐⭐⭐ |

**✅ 最终选择：Vite 5.x**

**理由**：
- 开发体验极佳，秒级启动
- 生产构建优化优秀
- 对 TypeScript、CSS Modules 原生支持
- 符合项目快速迭代需求

---

### 1.5 棋盘渲染库

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **自定义 SVG + CSS** | 完全可控、矢量图清晰、动画流畅、无依赖 | 开发成本高、需自行实现规则 | ⭐⭐⭐⭐⭐ |
| **chessboard.js** | 成熟稳定、API 完善 | 针对国际象棋、需改造 | ⭐⭐ |
| **xiangqiboardjs** | 专为象棋设计、开箱即用 | 维护状态不明、样式固定 | ⭐⭐⭐ |
| **Canvas 渲染** | 性能优秀、适合复杂动画 | 开发成本高、缩放模糊 | ⭐⭐⭐ |
| **PixiJS** | 2D 渲染引擎、性能极佳 | 过度设计、学习成本 | ⭐⭐ |

**✅ 最终选择：自定义 SVG + CSS Animation**

**理由**：
- 完全自主可控，无第三方依赖风险
- SVG 矢量图，移动端和高清屏表现优秀
- CSS Animation 实现流畅走棋动画
- 可深度定制 UI 风格

**实现方案**：
```typescript
// 棋盘组件结构
interface BoardProps {
  fen: string
  onMove: (from: string, to: string) => void
  orientation?: 'red' | 'black'
  showHints?: boolean
}

// 棋子 SVG 组件
const Piece: React.FC<{ type: string; color: string; position: string }> = ({ 
  type, color, position 
}) => (
  <g className={`piece ${color}-${type}`} data-position={position}>
    <circle cx="25" cy="25" r="22" fill={color === 'red' ? '#c00' : '#111'} />
    <text x="25" y="32" textAnchor="middle" fill="white" fontSize="20">
      {getPieceChar(type)}
    </text>
  </g>
)
```

---

### 1.6 HTTP 客户端

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Axios + React Query** | 功能完善、缓存机制、重试、TypeScript 支持 | 需学习两个库 | ⭐⭐⭐⭐⭐ |
| **Fetch + SWR** | 轻量、React 官方推荐、简洁 | 功能相对简单 | ⭐⭐⭐⭐ |
| **Axios 单独** | 成熟稳定、拦截器强大 | 无内置缓存机制 | ⭐⭐⭐ |
| **Ky** | 轻量、现代 API | 生态较小 | ⭐⭐⭐ |

**✅ 最终选择：Axios + TanStack Query (React Query)**

**理由**：
- Axios 提供请求拦截、错误处理
- React Query 提供缓存、重试、背景更新
- 完美适配 RESTful API
- 减少手动状态管理

---

### 1.7 WebSocket 客户端

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Native WebSocket + 自定义封装** | 零依赖、完全可控、轻量 | 需自行实现重连、心跳 | ⭐⭐⭐⭐⭐ |
| **Socket.IO Client** | 功能完善、自动重连、房间支持 | 需服务端配合、包体积大 | ⭐⭐⭐ |
| **ReconnectingWebSocket** | 自动重连、轻量 | 功能单一 | ⭐⭐⭐ |

**✅ 最终选择：Native WebSocket + 自定义封装**

**理由**：
- 服务端使用 Django Channels，原生 WebSocket 即可
- 自行实现重连、心跳机制，完全可控
- 减少不必要的依赖

---

### 1.8 前端技术栈总结

| 类别 | 技术选型 | 版本 | 备注 |
|------|---------|------|------|
| **框架** | React | 18.x | + TypeScript 5.x |
| **构建工具** | Vite | 5.x | 快速开发和构建 |
| **状态管理** | Zustand | 4.x | 轻量状态管理 |
| **UI 组件库** | Ant Design | 5.x | 后台管理端 |
| **样式方案** | Tailwind CSS + CSS Modules | - | 用户端自定义样式 |
| **路由** | React Router | 6.x | 官方推荐 |
| **HTTP 客户端** | Axios | 1.x | 请求处理 |
| **数据缓存** | TanStack Query | 5.x | 服务端状态管理 |
| **WebSocket** | Native WebSocket | - | 自定义封装 |
| **棋盘渲染** | 自定义 SVG | - | 完全自主可控 |
| **图表库** | ECharts | 5.x | 数据统计可视化 |
| **代码规范** | ESLint + Prettier | 最新 | 代码质量保障 |

---

## 2. 后端技术栈评估与选择

### 2.1 Web 框架

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Django** | 成熟稳定、自带 Admin、ORM 强大、生态完善、Channels 集成 | 同步为主、包体积大 | ⭐⭐⭐⭐⭐ |
| **FastAPI** | 异步高性能、自动文档、TypeScript 风格 | 生态较新、无内置 Admin | ⭐⭐⭐⭐ |
| **Flask** | 轻量灵活、易上手 | 需自行组装组件、扩展管理复杂 | ⭐⭐⭐ |
| **Sanic** | 异步高性能、类 Flask API | 生态小、社区资源有限 | ⭐⭐⭐ |

**✅ 最终选择：Django 5.x**

**理由**：
- 项目架构已明确采用 Django
- 自带 Admin 后台，节省开发成本
- ORM 成熟，减少 SQL 注入风险
- Django Channels 提供 WebSocket 支持
- 安全机制完善（CSRF、XSS 防护）

---

### 2.2 API 框架

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Django REST Framework** | 与 Django 深度集成、序列化强大、认证完善、文档好 | 学习曲线、性能一般 | ⭐⭐⭐⭐⭐ |
| **Django Ninja** | 类似 FastAPI、异步支持、自动文档 | 生态较新、社区小 | ⭐⭐⭐⭐ |
| **Tastypie** | 老牌、稳定 | 功能落后、维护缓慢 | ⭐⭐ |

**✅ 最终选择：Django REST Framework (DRF) 3.14+**

**理由**：
- 与 Django 无缝集成
- 序列化器强大，支持嵌套序列化
- 内置认证、权限、限流机制
- 社区活跃，问题容易解决

---

### 2.3 WebSocket 框架

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Django Channels** | 与 Django 深度集成、支持 ASGI、路由系统完善 | 学习曲线、调试复杂 | ⭐⭐⭐⭐⭐ |
| **Socket.IO + Flask** | 功能完善、客户端库丰富 | 需额外框架、协议非标准 | ⭐⭐⭐ |
| **FastAPI WebSocket** | 异步原生、简洁 | 功能相对简单 | ⭐⭐⭐⭐ |

**✅ 最终选择：Django Channels 4.x**

**理由**：
- 与 Django 项目无缝集成
- 支持 Consumer 类，类似 Django View
- 内置路由系统和组播功能
- 支持 Redis 作为通道层

---

### 2.4 异步框架

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **asyncio (内置)** | Python 内置、与 Channels 兼容 | API 较底层 | ⭐⭐⭐⭐⭐ |
| **AnyIO** | 支持多后端、抽象良好 | 额外依赖 | ⭐⭐⭐ |

**✅ 最终选择：asyncio (Python 内置)**

**理由**：
- Python 3.11+ asyncio 性能优秀
- Django Channels 基于 asyncio
- 无需额外依赖

---

### 2.5 任务队列

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Celery** | 功能最完善、支持定时任务、监控完善、生态成熟 | 配置复杂、依赖 Redis/RabbitMQ | ⭐⭐⭐⭐⭐ |
| **RQ (Redis Queue)** | 轻量、基于 Redis、配置简单 | 功能较少、无定时任务 | ⭐⭐⭐⭐ |
| **Huey** | 轻量、支持定时任务、配置简单 | 生态较小 | ⭐⭐⭐⭐ |
| **Django Q2** | Django 集成好、配置简单 | 社区较小 | ⭐⭐⭐ |

**✅ 最终选择：Celery 5.x + Redis**

**理由**：
- 功能最完善，支持多种队列
- 支持定时任务 (Celery Beat)
- 监控工具完善 (Flower)
- 与 Django 集成成熟

**任务队列设计**：
```python
# config/celery.py
from celery import Celery

app = Celery('chinese_chess')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 队列配置
CELERY_TASK_ROUTES = {
    'apps.games.tasks.calculate_rating': {'queue': 'game'},
    'apps.users.tasks.send_email': {'queue': 'email'},
    'apps.ai.tasks.analyze_position': {'queue': 'ai'},
}
```

---

### 2.6 AI 引擎集成

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **python-stockfish** | 封装完善、API 简洁、活跃维护 | 需安装 Stockfish 二进制 | ⭐⭐⭐⭐⭐ |
| **python-chess + Stockfish** | 灵活、可自定义 | 需自行封装 | ⭐⭐⭐⭐ |
| **直接调用 Stockfish CLI** | 无依赖、完全可控 | 开发成本高 | ⭐⭐⭐ |

**✅ 最终选择：python-stockfish + Stockfish 16**

**理由**：
- 封装完善，API 简洁
- 支持难度等级配置
- 支持 FEN 格式
- 活跃维护

**集成方案**：
```python
class StockfishService:
    """Stockfish 引擎服务"""
    
    DIFFICULTY_MAP = {
        1: {'skill_level': 0, 'think_time': 0.5},
        5: {'skill_level': 8, 'think_time': 1.5},
        10: {'skill_level': 20, 'think_time': 5.0},
    }
    
    def __init__(self, difficulty: int = 5):
        config = self.DIFFICULTY_MAP.get(difficulty, self.DIFFICULTY_MAP[5])
        self.engine = Stockfish(
            path="/usr/games/stockfish",
            depth=15,
            parameters={
                "Skill Level": config['skill_level'],
                "Move Overhead": 100,
                "Threads": 2,
                "Hash": 128,
            }
        )
    
    def get_best_move(self, fen: str) -> str:
        self.engine.set_fen_position(fen)
        return self.engine.get_best_move()
```

---

### 2.7 后端技术栈总结

| 类别 | 技术选型 | 版本 | 备注 |
|------|---------|------|------|
| **Web 框架** | Django | 5.x | 核心框架 |
| **API 框架** | Django REST Framework | 3.14+ | RESTful API |
| **WebSocket** | Django Channels | 4.x | 实时对战 |
| **ASGI 服务器** | Daphne | 4.x | WebSocket 服务 |
| **WSGI 服务器** | Gunicorn | 21.x | HTTP 服务 |
| **任务队列** | Celery | 5.x | 异步任务 |
| **定时任务** | Celery Beat | 5.x | 周期性任务 |
| **AI 引擎库** | python-stockfish | 最新 | Stockfish 封装 |
| **AI 引擎** | Stockfish | 16.x | 象棋引擎 |
| **Python 版本** | Python | 3.11+ | 性能优化 |
| **代码规范** | Black + Flake8 | 最新 | 代码格式化 |

---

## 3. 数据库技术栈评估与选择

### 3.1 关系型数据库

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **PostgreSQL** | ACID 事务、JSON 支持、扩展性强、索引丰富、免费 | 配置略复杂 | ⭐⭐⭐⭐⭐ |
| **MySQL 8** | 流行、文档多、性能好 | JSON 支持较弱、扩展性一般 | ⭐⭐⭐⭐ |
| **SQLite** | 零配置、轻量、嵌入式 | 不适合生产、并发差 | ⭐⭐ |
| **MariaDB** | MySQL 分支、开源 | 生态略小于 MySQL | ⭐⭐⭐⭐ |

**✅ 最终选择：PostgreSQL 15+**

**理由**：
- JSONB 支持，适合存储棋局走法历史
- 丰富的索引类型（部分索引、包含索引）
- 支持读写分离和逻辑复制
- 扩展性强（未来可加 PostGIS 等）

---

### 3.2 缓存数据库

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Redis** | 数据结构丰富、发布订阅、持久化、集群支持 | 内存成本高 | ⭐⭐⭐⭐⭐ |
| **Memcached** | 简单、高性能、多线程 | 功能单一、无持久化 | ⭐⭐⭐ |
| **Valkey** | Redis 分支、完全开源 | 生态较新 | ⭐⭐⭐⭐ |

**✅ 最终选择：Redis 7+**

**理由**：
- 支持 Sorted Set，适合匹配队列
- 发布订阅功能，支持实时通知
- 持久化支持，数据不丢失
- 集群和哨兵模式，高可用

---

### 3.3 棋谱存储方案

| 方案 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **PostgreSQL JSONB** | 事务支持、查询方便、无需额外存储 | 大文件性能一般 | ⭐⭐⭐⭐⭐ |
| **MinIO/S3 对象存储** | 适合大文件、成本低、可扩展 | 查询不便、需额外服务 | ⭐⭐⭐ |
| **文件系统** | 简单、零成本 | 备份困难、查询差 | ⭐⭐ |

**✅ 最终选择：PostgreSQL JSONB**

**理由**：
- 棋局数据量适中（每局<100KB）
- JSONB 支持高效查询和索引
- 事务保证数据一致性
- 简化架构，无需额外存储

---

### 3.4 数据库技术栈总结

| 类别 | 技术选型 | 版本 | 用途 |
|------|---------|------|------|
| **主数据库** | PostgreSQL | 15.x | 核心业务数据 |
| **缓存** | Redis | 7.x | 缓存、Session、队列 |
| **开发环境** | SQLite | 3.x | 本地开发（可选） |
| **ORM** | Django ORM | 5.x | 数据访问 |
| **数据库迁移** | Django Migrations | - | 模式管理 |
| **连接池** | PgBouncer | 1.x | 生产环境连接池 |

---

## 4. AI 引擎技术栈评估与选择

### 4.1 Stockfish 集成方案

| 方案 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **python-stockfish 库** | 封装完善、API 简洁、活跃维护 | 需安装二进制 | ⭐⭐⭐⭐⭐ |
| **UCI 协议直接通信** | 完全可控、无依赖 | 开发成本高、易出错 | ⭐⭐⭐ |
| **Stockfish 作为独立服务** | 解耦、可独立扩展 | 架构复杂、通信开销 | ⭐⭐⭐ |

**✅ 最终选择：python-stockfish 库**

**理由**：
- 成熟的 Python 封装
- 支持 UCI 协议所有功能
- 活跃维护，问题及时修复

---

### 4.2 难度等级设计

**10 级难度映射表**：

| 难度 | 名称 | Skill Level | 思考时间 | 深度限制 | Elo 预估 |
|------|------|-------------|---------|---------|---------|
| 1 | 入门 | 0 | 0.5s | 5 | 400 |
| 2 | 新手 | 2 | 0.5s | 7 | 600 |
| 3 | 初级 | 4 | 1.0s | 9 | 800 |
| 4 | 入门 | 6 | 1.0s | 11 | 1000 |
| 5 | 中级 | 8 | 1.5s | 13 | 1200 |
| 6 | 中级 | 10 | 1.5s | 15 | 1400 |
| 7 | 高级 | 12 | 2.0s | 17 | 1600 |
| 8 | 高级 | 14 | 2.0s | 19 | 1800 |
| 9 | 大师 | 16 | 3.0s | 21 | 2000+ |
| 10 | 大师 | 20 | 5.0s | 25 | 2200+ |

**实现方案**：
```python
@dataclass
class DifficultyConfig:
    name: str
    skill_level: int
    think_time_ms: int
    depth: int
    elo_estimate: int

DIFFICULTY_CONFIGS = {
    1: DifficultyConfig("入门", 0, 500, 5, 400),
    2: DifficultyConfig("新手", 2, 500, 7, 600),
    3: DifficultyConfig("初级", 4, 1000, 9, 800),
    4: DifficultyConfig("入门", 6, 1000, 11, 1000),
    5: DifficultyConfig("中级", 8, 1500, 13, 1200),
    6: DifficultyConfig("中级", 10, 1500, 15, 1400),
    7: DifficultyConfig("高级", 12, 2000, 17, 1600),
    8: DifficultyConfig("高级", 14, 2000, 19, 1800),
    9: DifficultyConfig("大师", 16, 3000, 21, 2000),
    10: DifficultyConfig("大师", 20, 5000, 25, 2200),
}

class AIService:
    def __init__(self, difficulty: int = 5):
        config = DIFFICULTY_CONFIGS[difficulty]
        self.engine = Stockfish(
            path=settings.STOCKFISH_PATH,
            depth=config.depth,
            parameters={
                "Skill Level": config.skill_level,
                "Move Overhead": config.think_time_ms,
                "Threads": 2,
                "Hash": 128,
            }
        )
```

---

### 4.3 AI 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                      AI 服务层                                │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  API 接口    │  │  任务队列    │  │   Stockfish 引擎    │ │
│  │  - 最佳走法  │  │  - Celery   │  │   - 难度 1-10       │ │
│  │  - 棋局评估  │  │  - 异步执行  │  │   - 思考时间控制     │ │
│  │  - 走棋提示  │  │  - 超时处理  │  │   - 深度限制         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              引擎池管理 (多实例)                      │   │
│  │  - 实例 1: 难度 1-3 (低配置)                          │   │
│  │  - 实例 2: 难度 4-6 (中配置)                          │   │
│  │  - 实例 3: 难度 7-10 (高配置)                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.4 AI 引擎技术栈总结

| 类别 | 技术选型 | 版本 | 备注 |
|------|---------|------|------|
| **引擎** | Stockfish | 16.x | 开源最强象棋引擎 |
| **Python 封装** | python-stockfish | 最新 | UCI 协议封装 |
| **难度等级** | 自定义 10 级 | - | Skill Level 0-20 |
| **部署方式** | Docker 容器 | - | 多实例引擎池 |
| **调用方式** | Celery 异步 | - | 避免阻塞主线程 |

---

## 5. 部署与运维技术栈

### 5.1 容器化

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Docker** | 标准容器、生态成熟、文档丰富 | 需学习 Dockerfile | ⭐⭐⭐⭐⭐ |
| **Podman** | 无守护进程、更安全 | 生态较小 | ⭐⭐⭐⭐ |
| **LXC** | 轻量、系统级容器 | 配置复杂 | ⭐⭐⭐ |

**✅ 最终选择：Docker + Docker Compose**

**理由**：
- 行业标准，文档和工具丰富
- Docker Compose 简化多服务编排
- 便于 CI/CD 集成

---

### 5.2 容器编排

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Docker Compose** | 简单、适合单机、开发友好 | 不支持集群、功能有限 | ⭐⭐⭐⭐⭐ |
| **Kubernetes** | 功能强大、自动伸缩、高可用 | 复杂、学习成本高 | ⭐⭐⭐ |
| **Docker Swarm** | 内置、简单 | 功能较少、生态小 | ⭐⭐⭐ |

**✅ 最终选择：Docker Compose（初期） → Kubernetes（扩展期）**

**理由**：
- 项目初期用户量少，Docker Compose 足够
- 简化部署和运维
- 后期可根据需要迁移到 K8s

---

### 5.3 CI/CD

| 选项 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **GitHub Actions** | 免费、与 GitHub 集成、生态丰富 | 分钟数限制 | ⭐⭐⭐⭐⭐ |
| **GitLab CI** | 功能强大、自托管 | 需自建 GitLab | ⭐⭐⭐⭐ |
| **Jenkins** | 灵活、插件丰富 | 配置复杂、维护成本高 | ⭐⭐⭐ |
| **CircleCI** | 易用、性能好 | 免费额度有限 | ⭐⭐⭐⭐ |

**✅ 最终选择：GitHub Actions**

**理由**：
- 项目托管在 GitHub，无缝集成
- 免费额度足够个人项目使用
- 丰富的 Action 市场

**CI/CD 流程**：
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        run: |
          docker build -t chinese-chess-backend:latest ./src/backend
          docker push ${{ secrets.DOCKER_REGISTRY }}/chinese-chess-backend:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        run: |
          ssh ${{ secrets.SERVER_HOST }} "cd /app && docker-compose pull && docker-compose up -d"
```

---

### 5.4 监控

| 类别 | 技术选型 | 版本 | 用途 |
|------|---------|------|------|
| **应用监控** | Prometheus + Grafana | 最新 | 指标收集和可视化 |
| **日志收集** | ELK Stack (Elasticsearch + Logstash + Kibana) | 8.x | 集中日志 |
| **简化方案** | Loki + Promtail + Grafana | 最新 | 轻量日志方案 |
| **APM** | Sentry | 最新 | 错误追踪 |
| **健康检查** | Django Health Check | - | 服务健康状态 |

**✅ 最终选择**：
- **初期**：Sentry（错误追踪）+ Django 日志
- **扩展期**：Prometheus + Grafana + Loki

---

### 5.5 部署与运维技术栈总结

| 类别 | 技术选型 | 版本 | 阶段 |
|------|---------|------|------|
| **容器化** | Docker | 24.x | 全程 |
| **编排** | Docker Compose | 2.x | 初期 |
| **编排** | Kubernetes | 1.28+ | 扩展期 |
| **CI/CD** | GitHub Actions | - | 全程 |
| **监控** | Sentry | 最新 | 初期 |
| **监控** | Prometheus + Grafana | 最新 | 扩展期 |
| **日志** | Django 日志 + Loki | - | 初期→扩展期 |
| **反向代理** | Nginx | 1.24+ | 全程 |
| **SSL** | Let's Encrypt | - | 免费证书 |

---

## 6. 第三方服务评估（可选）

### 6.1 社交分享

| 服务 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **自建分享系统** | 零成本、完全可控、数据私有 | 开发成本、无社交图谱 | ⭐⭐⭐⭐⭐ |
| **ShareThis** | 开箱即用、支持多平台 | 免费版有广告、数据不私有 | ⭐⭐⭐ |
| **AddToAny** | 免费、简洁 | 功能有限 | ⭐⭐⭐ |

**✅ 最终选择：自建分享系统**

**理由**：
- 符合零预算约束
- 生成分享链接 + 二维码即可
- 无需依赖第三方

---

### 6.2 支付（未来扩展）

| 服务 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Stripe** | 全球支持、API 友好、文档完善 | 中国大陆支持有限 | ⭐⭐⭐⭐ |
| **支付宝** | 中国大陆普及、接入简单 | 仅限中国 | ⭐⭐⭐⭐⭐ |
| **微信支付** | 中国大陆普及 | 接入较复杂 | ⭐⭐⭐⭐ |
| **PayPal** | 全球支持、用户信任 | 手续费高、体验一般 | ⭐⭐⭐ |

**⏸️ 暂缓**：项目初期不包含付费功能，后期根据需求选择

---

### 6.3 CDN

| 服务 | 优势 | 劣势 | 评分 |
|------|------|------|------|
| **Cloudflare** | 免费额度大、全球节点、DDoS 防护 | 国内访问慢 | ⭐⭐⭐⭐⭐ |
| **阿里云 CDN** | 国内速度快、与阿里云集成 | 收费、配置复杂 | ⭐⭐⭐⭐ |
| **七牛云** | 国内、对象存储 +CDN 一体 | 免费额度有限 | ⭐⭐⭐⭐ |

**✅ 最终选择：Cloudflare（初期）**

**理由**：
- 免费额度足够初期使用
- 自带 DDoS 防护
- 配置简单

---

### 6.4 第三方服务总结

| 服务 | 技术选型 | 阶段 | 备注 |
|------|---------|------|------|
| **社交分享** | 自建 | 初期 | 分享链接 + 二维码 |
| **支付** | 暂缓 | - | 后期考虑支付宝 |
| **CDN** | Cloudflare | 初期 | 免费额度 |
| **对象存储** | MinIO (自建) | 初期 | 头像、棋局文件 |
| **邮件服务** | SMTP (自建) | 初期 | 使用 Gmail/163 SMTP |

---

## 7. 技术风险与应对方案

### 7.1 技术风险识别

| 风险 ID | 风险描述 | 可能性 | 影响 | 风险等级 |
|--------|---------|--------|------|---------|
| **TR-001** | WebSocket 连接不稳定，断线频繁 | 中 | 高 | 🔴 高 |
| **TR-002** | Stockfish 引擎性能不足，高并发响应慢 | 中 | 高 | 🔴 高 |
| **TR-003** | 匹配算法不合理，等待时间过长 | 中 | 中 | 🟡 中 |
| **TR-004** | 棋局状态同步问题，出现不一致 | 中 | 高 | 🔴 高 |
| **TR-005** | 前端棋盘渲染性能差，动画卡顿 | 低 | 中 | 🟡 中 |
| **TR-006** | 数据库查询慢，API 响应超时 | 中 | 中 | 🟡 中 |
| **TR-007** | Redis 单点故障，缓存失效 | 低 | 高 | 🟡 中 |
| **TR-008** | 安全漏洞（SQL 注入、XSS、CSRF） | 低 | 高 | 🟡 中 |
| **TR-009** | 跨平台兼容性问题 | 高 | 中 | 🟡 中 |
| **TR-010** | 第三方依赖停止维护 | 低 | 中 | 🟢 低 |

---

### 7.2 风险应对方案

#### TR-001: WebSocket 连接不稳定

**应对措施**：
1. 实现心跳机制（30 秒间隔）
2. 实现自动重连（指数退避，最多 5 次）
3. 服务端连接状态检测（90 秒无心跳判定掉线）
4. 断线后状态恢复（从数据库同步最新状态）

```typescript
// 前端重连实现
class WebSocketManager {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect() {
    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = 1000 * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, delay);
      }
    };
  }

  async reconnect(gameId: string) {
    // 请求服务端同步最新状态
    const state = await fetch(`/api/games/${gameId}/state/`);
    this.syncState(state);
  }
}
```

---

#### TR-002: Stockfish 引擎性能不足

**应对措施**：
1. 实现引擎池（多实例并行）
2. 限制思考时间和深度
3. 使用 Celery 异步执行，避免阻塞
4. 高难度 AI 使用独立队列

```python
# 引擎池实现
class EnginePool:
    def __init__(self, pool_size: int = 4):
        self.pool = [StockfishService(difficulty=5) for _ in range(pool_size)]
        self.available = asyncio.Queue(maxsize=pool_size)
        
    async def acquire(self, difficulty: int) -> StockfishService:
        engine = await self.available.get()
        engine.set_difficulty(difficulty)
        return engine
    
    def release(self, engine: StockfishService):
        self.available.put_nowait(engine)
```

---

#### TR-003: 匹配算法不合理

**应对措施**：
1. 动态扩大搜索范围（±100 → ±300 分）
2. 设置最大等待时间（3 分钟）
3. 匹配超时后推荐 AI 对战
4. 监控匹配成功率，持续优化

```python
async def find_opponent(user_rating: int, timeout: int = 180) -> Optional[int]:
    rating_range = 100
    elapsed = 0
    
    while elapsed < timeout:
        opponents = await redis.zrangebyscore(
            'match:queue',
            user_rating - rating_range,
            user_rating + rating_range
        )
        
        if opponents:
            return opponents[0]
        
        rating_range = min(rating_range + 50, 300)
        await asyncio.sleep(30)
        elapsed += 30
    
    return None  # 匹配超时
```

---

#### TR-004: 棋局状态同步问题

**应对措施**：
1. 服务端权威验证（所有走棋服务端验证）
2. 走棋序列号（防止乱序）
3. 定期状态同步（每 10 步同步一次完整状态）
4. 冲突检测和解决

```python
class GameService:
    async def make_move(self, game_id: str, move: Move, sequence: int):
        game = await self.get_game(game_id)
        
        # 验证序列号
        if sequence != game.expected_sequence:
            raise InvalidMoveError("走棋序列号不匹配")
        
        # 验证走棋合法性
        if not self.is_valid_move(game.fen, move):
            raise InvalidMoveError("无效走棋")
        
        # 更新状态
        game.apply_move(move)
        game.expected_sequence += 1
        await game.save()
```

---

#### TR-005: 前端棋盘渲染性能

**应对措施**：
1. 使用 SVG 而非 Canvas（矢量图清晰）
2. CSS Animation 而非 JS 动画（GPU 加速）
3. 虚拟滚动（只渲染可见区域）
4. 防抖和节流（减少不必要的渲染）

```typescript
// 使用 React.memo 优化渲染
const Board = React.memo(({ fen, onMove }: BoardProps) => {
  const pieces = useMemo(() => parseFen(fen), [fen]);
  
  return (
    <svg viewBox="0 0 450 500" className="board">
      {pieces.map((piece) => (
        <Piece
          key={piece.position}
          piece={piece}
          onClick={() => onMove(piece.position)}
        />
      ))}
    </svg>
  );
});
```

---

#### TR-006: 数据库查询慢

**应对措施**：
1. 建立合理索引（见架构文档）
2. 使用 select_related 和 prefetch_related
3. 只查询需要的字段（only/defer）
4. 热点数据缓存到 Redis

```python
# 优化查询
games = Game.objects.select_related('red_player', 'black_player')\
    .only('id', 'fen_current', 'status', 'created_at')\
    .filter(status='playing')\
    .order_by('-created_at')[:20]
```

---

#### TR-007: Redis 单点故障

**应对措施**：
1. 开发环境：单机 Redis
2. 测试环境：Redis Sentinel（主从 + 自动故障转移）
3. 生产环境：Redis Cluster（3 主 3 从）

```yaml
# Redis Sentinel 配置
redis-master:
  image: redis:7
  command: redis-server

redis-slave:
  image: redis:7
  command: redis-server --slaveof redis-master 6379

redis-sentinel:
  image: redis:7
  command: redis-sentinel /usr/local/etc/redis/sentinel.conf
```

---

#### TR-008: 安全漏洞

**应对措施**：
1. 使用 Django ORM（防止 SQL 注入）
2. DRF 序列化器验证输入
3. Django 内置 CSRF、XSS 防护
4. 定期安全扫描

```python
# 输入验证
class MoveSerializer(serializers.Serializer):
    from_pos = serializers.CharField(max_length=2)
    to_pos = serializers.CharField(max_length=2)
    
    def validate_from_pos(self, value):
        if not re.match(r'^[a-i][0-9]$', value):
            raise ValidationError("无效的位置格式")
        return value
```

---

#### TR-009: 跨平台兼容性

**应对措施**：
1. 响应式设计（移动端优先）
2. 多浏览器测试（Chrome、Firefox、Safari、Edge）
3. 使用 CSS Grid + Flexbox
4. 真机测试（iOS、Android 主流机型）

```css
/* 响应式布局 */
.board-container {
  width: 100%;
  max-width: 450px;
  aspect-ratio: 9 / 10;
}

@media (max-width: 480px) {
  .board-container {
    max-width: 100%;
  }
}
```

---

#### TR-010: 第三方依赖停止维护

**应对措施**：
1. 选择活跃维护的库（检查 GitHub 提交记录）
2. 关键依赖准备备选方案
3. 定期更新依赖版本
4. 核心功能自主实现（如棋盘渲染）

| 依赖 | 备选方案 |
|------|---------|
| python-stockfish | python-chess + 自封装 |
| Django Channels | FastAPI WebSocket |
| Ant Design | MUI / 自定义组件 |
| Zustand | Jotai / Redux Toolkit |

---

### 7.3 风险监控计划

| 风险 | 监控指标 | 告警阈值 | 负责人 |
|------|---------|---------|--------|
| WebSocket 稳定性 | WS 断线率 | > 5% | 后端 |
| AI 响应时间 | P95 延迟 | > 3s | 后端 |
| 匹配成功率 | 3 分钟内匹配成功比例 | < 80% | 后端 |
| API 响应时间 | P95 延迟 | > 200ms | 后端 |
| 前端性能 | 首屏加载时间 | > 2s | 前端 |
| 错误率 | API 5xx 错误比例 | > 1% | 后端 |

---

## 8. 最终技术栈决策表

### 8.1 前端技术栈

| 类别 | 最终选择 | 版本 | 备选方案 |
|------|---------|------|---------|
| **框架** | React | 18.x | Vue 3 |
| **语言** | TypeScript | 5.x | JavaScript |
| **构建工具** | Vite | 5.x | Webpack 5 |
| **状态管理** | Zustand | 4.x | Jotai |
| **UI 组件库** | Ant Design | 5.x | MUI |
| **样式方案** | Tailwind CSS + CSS Modules | - | Styled Components |
| **路由** | React Router | 6.x | - |
| **HTTP 客户端** | Axios + TanStack Query | 1.x + 5.x | Fetch + SWR |
| **WebSocket** | Native WebSocket | - | Socket.IO |
| **棋盘渲染** | 自定义 SVG | - | xiangqiboardjs |
| **图表库** | ECharts | 5.x | Recharts |

---

### 8.2 后端技术栈

| 类别 | 最终选择 | 版本 | 备选方案 |
|------|---------|------|---------|
| **Web 框架** | Django | 5.x | FastAPI |
| **API 框架** | Django REST Framework | 3.14+ | Django Ninja |
| **WebSocket** | Django Channels | 4.x | FastAPI WebSocket |
| **ASGI 服务器** | Daphne | 4.x | Uvicorn |
| **WSGI 服务器** | Gunicorn | 21.x | - |
| **任务队列** | Celery | 5.x | RQ |
| **AI 引擎库** | python-stockfish | 最新 | python-chess |
| **AI 引擎** | Stockfish | 16.x | GNU Chess |
| **Python 版本** | Python | 3.11+ | - |

---

### 8.3 数据库技术栈

| 类别 | 最终选择 | 版本 | 备选方案 |
|------|---------|------|---------|
| **主数据库** | PostgreSQL | 15.x | MySQL 8 |
| **缓存** | Redis | 7.x | Memcached |
| **ORM** | Django ORM | 5.x | SQLAlchemy |
| **连接池** | PgBouncer | 1.x | - |

---

### 8.4 部署与运维技术栈

| 类别 | 最终选择 | 版本 | 备选方案 |
|------|---------|------|---------|
| **容器化** | Docker | 24.x | Podman |
| **编排** | Docker Compose | 2.x | Kubernetes |
| **CI/CD** | GitHub Actions | - | GitLab CI |
| **反向代理** | Nginx | 1.24+ | Caddy |
| **监控** | Sentry + Grafana | 最新 | Datadog |
| **日志** | Loki | 最新 | ELK |
| **CDN** | Cloudflare | - | 阿里云 CDN |

---

### 8.5 技术栈全景图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           技术栈全景图                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         前端层 (Frontend)                        │   │
│  │  React 18 + TypeScript | Vite 5 | Zustand | Ant Design 5        │   │
│  │  Tailwind CSS | React Router 6 | Axios + React Query            │   │
│  │  自定义 SVG 棋盘 | ECharts 5                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         网关层 (Gateway)                         │   │
│  │                    Nginx 1.24 + Let's Encrypt SSL                │   │
│  │                    Cloudflare CDN + DDoS 防护                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                   ┌────────────────┴────────────────┐                  │
│                   ▼                                 ▼                  │
│  ┌─────────────────────────┐       ┌─────────────────────────────────┐ │
│  │     API 服务层           │       │      WebSocket 服务层            │ │
│  │   Django 5 + DRF 3.14   │       │   Django Channels 4 + Daphne    │ │
│  │   Gunicorn 21 (8 workers)│       │                                 │ │
│  └─────────────────────────┘       └─────────────────────────────────┘ │
│                   │                                 │                   │
│                   └────────────────┬────────────────┘                  │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       业务逻辑层 (Services)                      │   │
│  │   UserService | GameService | MatchService | AIService          │   │
│  │   BoardService | RankService | TutorialService | SocialService  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       数据访问层 (Data Access)                   │   │
│  │              Django ORM | Redis Client | Celery                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                   ┌────────────────┼────────────────┐                  │
│                   ▼                ▼                ▼                  │
│  ┌─────────────────────┐ ┌─────────────────┐ ┌───────────────────────┐ │
│  │   PostgreSQL 15     │ │    Redis 7      │ │    MinIO (对象存储)   │ │
│  │   (主从复制)         │ │   (Sentinel)    │ │    - 头像文件         │ │
│  │   - 业务数据         │ │   - 缓存        │ │    - 棋局文件         │ │
│  │   - 棋局记录         │ │   - Session     │ │                       │ │
│  │   - 用户数据         │ │   - 匹配队列     │ │                       │ │
│  └─────────────────────┘ └─────────────────┘ └───────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       AI 引擎层 (AI Engine)                      │   │
│  │              Stockfish 16 + python-stockfish                    │   │
│  │              Celery 异步调用 | 引擎池管理                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       运维层 (DevOps)                            │   │
│  │   Docker 24 | Docker Compose 2 | GitHub Actions                 │   │
│  │   Sentry (错误追踪) | Grafana + Loki (监控日志)                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. 技术选型决策记录 (ADR)

### ADR-001: 选择 React 而非 Vue

**日期**：2026-03-03  
**状态**：已采纳

**背景**：需要选择前端框架

**决策**：选择 React 18 + TypeScript

**理由**：
- 生态更丰富，组件库和工具链完善
- TypeScript 支持更好，类型安全
- 人才储备多，便于后续协作
- 项目架构文档已明确采用 React

**后果**：
- ✅ 享受 React 生态红利
- ⚠️ 需要学习 Hooks 和函数式组件

---

### ADR-002: 选择 Django 而非 FastAPI

**日期**：2026-03-03  
**状态**：已采纳

**背景**：需要选择后端框架

**决策**：选择 Django 5.x

**理由**：
- 自带 Admin 后台，节省开发成本
- ORM 成熟，减少 SQL 注入风险
- Django Channels 提供 WebSocket 支持
- 安全机制完善（CSRF、XSS 防护）
- 项目架构文档已明确采用 Django

**后果**：
- ✅ 快速开发，安全性高
- ⚠️ 同步为主，高并发场景需优化

---

### ADR-003: 选择 PostgreSQL 而非 MySQL

**日期**：2026-03-03  
**状态**：已采纳

**背景**：需要选择关系型数据库

**决策**：选择 PostgreSQL 15+

**理由**：
- JSONB 支持，适合存储棋局走法历史
- 丰富的索引类型
- 支持读写分离和逻辑复制
- 扩展性强

**后果**：
- ✅ 灵活的 JSON 存储，强大的查询能力
- ⚠️ 配置略复杂于 MySQL

---

### ADR-004: 选择 Docker Compose 而非 Kubernetes

**日期**：2026-03-03  
**状态**：已采纳

**背景**：需要选择容器编排方案

**决策**：初期使用 Docker Compose，后期可迁移 K8s

**理由**：
- 项目初期用户量少，Docker Compose 足够
- 简化部署和运维
- 学习成本低

**后果**：
- ✅ 快速部署，运维简单
- ⚠️ 后期扩展需迁移到 K8s

---

## 附录

### A. 依赖清单

**前端核心依赖**：
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.0",
    "antd": "^5.12.0",
    "tailwindcss": "^3.4.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.12.0",
    "echarts": "^5.4.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@types/react": "^18.2.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0"
  }
}
```

**后端核心依赖**：
```txt
# requirements.txt
Django==5.0.0
djangorestframework==3.14.0
django-cors-headers==4.3.0
channels==4.0.0
channels-redis==4.2.0
daphne==4.0.0
gunicorn==21.2.0
celery==5.3.0
redis==5.0.0
psycopg2-binary==2.9.9
python-stockfish==3.29.0
sentry-sdk==1.38.0
```

---

### B. 开发环境要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **CPU** | 4 核 | 8 核 + |
| **内存** | 8GB | 16GB + |
| **存储** | 20GB | 50GB SSD |
| **Python** | 3.11 | 3.11+ |
| **Node.js** | 18.x | 20.x LTS |
| **Docker** | 20.x | 24.x |

---

### C. 文档历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| v1.0 | 2026-03-03 | architect agent | 初始版本，完成技术栈评估与选型 |

---

**阶段 3 完成** ✅

**技术栈评估完成！** 下一步进入**阶段 4 详细设计**，进行数据库详细设计、API 详细设计、前端组件设计等。

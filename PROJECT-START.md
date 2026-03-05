# 🚀 中国象棋项目 - 开始指南

**项目位置**：`~/.openclaw/workspace/projects/chinese-chess/`

---

## 📁 项目目录

```
~/.openclaw/workspace/projects/chinese-chess/
├── README.md                # 项目说明
├── PROJECT-START.md         # 开始指南（本文件）
├── docs/                    # 项目文档
│   └── requirements.md      # 需求文档（阶段 1 输出）
├── src/
│   ├── backend/             # Django 后端
│   ├── frontend-admin/      # 后台管理端前端
│   └── frontend-user/       # 用户端前端
├── tests/                   # 测试文件
└── scripts/                 # 脚本文件
```

---

## 🎯 阶段 1：需求分析

**工作目录**：`cd ~/.openclaw/workspace/projects/chinese-chess/`

**执行命令**：
```bash
cd ~/.openclaw/workspace/projects/chinese-chess/

sessions_spawn --runtime subagent --mode run \
  --agent planner \
  --model bailian/qwen3.5-plus \
  --task "分析中国象棋项目需求，输出到 docs/requirements.md，包括：

1. 项目背景和目标
2. 目标用户群体
3. 核心功能列表（用户端 + 后台管理端）
4. 用户故事（优先级排序：P0/P1/P2）
5. 成功标准（可测量指标）
6. 风险和约束"
```

**输出文件**：`docs/requirements.md`

**完成标准**：
- [ ] 需求文档完成
- [ ] 用户故事优先级明确
- [ ] 成功标准可测量

**完成后**：告诉人家 `阶段 1 完成`

---

## 📝 后续阶段

### 阶段 2：架构设计
```bash
sessions_spawn --agent architect --model bailian/qwen3-max \
  --task "设计中国象棋系统架构，输出到 docs/architecture.md"
```

### 阶段 3：技术选型
```bash
sessions_spawn --agent architect --model bailian/qwen3-max \
  --task "评估中国象棋技术栈，输出到 docs/tech-stack-evaluation.md"
```

### 阶段 4：功能规划
```bash
sessions_spawn --agent planner --model bailian/qwen3.5-plus \
  --task "规划 [功能名称] 实现，输出到 docs/features/[name]-plan.md"
```

### 阶段 5：TDD 实现
```bash
sessions_spawn --agent tdd-guide --model bailian/qwen3-coder-plus \
  --task "使用 TDD 实现 [功能名称]"
```

### 阶段 6：代码审查
```bash
sessions_spawn --agent code-reviewer --model bailian/qwen3-coder-plus \
  --task "审查 [模块名称] 代码"
```

### 阶段 7：安全审查
```bash
sessions_spawn --agent security-reviewer --model bailian/qwen3-coder-plus \
  --task "审查中国象棋项目安全性"
```

### 阶段 8：文档编写
```bash
sessions_spawn --agent doc-updater --model bailian/qwen3.5-plus \
  --task "编写中国象棋项目文档"
```

### 阶段 9：部署上线
```bash
sessions_spawn --agent build-error-resolver --model bailian/qwen3-coder-next \
  --task "协助部署中国象棋项目"
```

---

## 💡 使用提示

1. **每个阶段完成后**：告诉人家 `阶段 X 完成`
2. **人家会引导**：进入下一阶段
3. **文档位置**：所有文档在 `docs/` 目录
4. **代码位置**：所有代码在 `src/` 目录

---

**项目位置**：`~/.openclaw/workspace/projects/chinese-chess/`  
**创建时间**：2026-03-02  
**维护者**：小屁孩（御姐模式）

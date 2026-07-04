# <项目名称>

## 项目目标

<用 2-3 句话说明项目背景、目标用户、核心业务价值和当前阶段。>

## 当前阶段

- 阶段：`<phase-name>`
- 主目标：<本阶段最重要的可用闭环>
- 主线技术栈：<前端技术栈> + <后端技术栈> + <数据存储>
- 主线目录：<前端主线目录>、<后端主线目录>
- legacy fallback：<如无则填写“无”>

## 快速开始

1. 阅读项目入口：

```bash
cat AGENTS.md
cat AGENT/README.md
cat references/Harness/QUICKSTART.md
```

2. 安装依赖：

```bash
<install-command>
```

3. 启动开发环境：

```bash
<dev-command>
```

4. 运行验证：

```bash
<test-command>
```

## 推荐目录结构

```text
.
├── AGENT/                    # 通用 agent 规则
├── docs/                     # 产品、架构、接口、测试等正式文档
├── references/Harness/        # 工程治理、变更目录、角色与技能
├── <frontend-mainline>/       # 前端主线
├── <backend-mainline>/        # 后端主线
├── PLANS.md                   # 当前阶段执行看板
├── AGENTS.md                  # 仓库级开发约束
└── README.md
```

## 治理入口

- `AGENTS.md`：仓库级目标、阶段、主线目录和开发纪律。
- `AGENT/README.md`：通用规则入口。
- `references/Harness/QUICKSTART.md`：Harness 轻量入口。
- `references/Harness/changes/`：需求与变更追踪目录。
- `PLANS.md`：阶段计划与完成度看板。

## 开发原则

- 先规划后开发。
- 先输出设计方案。
- 未确认方案不得写代码。
- 小步迭代。
- 每个功能必须可测试。
- 每次修改必须更新文档。

## 验证命令

根据项目实际情况填写：

```bash
<lint-command>
<test-command>
<build-command>
```

## 文档同步

- 正式设计、架构、流程和需求变更同步到 `docs/`。
- 如使用 Obsidian，同步到 `<Obsidian 项目路径>/`。
- 任务完成、阶段变化或计划调整后同步更新 `PLANS.md`。

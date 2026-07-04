# Harness Quickstart

本文件是 agent 和开发者进入 AgentPM Harness 执行层的轻量入口。它不替代根目录 `AGENTS.md`、`CODEX.md` 或 `AGENT/` 中的通用原则规则。

## 默认阅读顺序

1. 先读根目录 `AGENTS.md`。
2. 在 Codex 中执行时，再读根目录 `CODEX.md`。
3. 需要通用规则时，读 `AGENT/README.md` 以及对应的 `AGENT/*_RULES.md`。
4. 为本次开发变更创建或更新 `references/Harness/changes/` 记录，再读本文件和 `references/Harness/rules/` 判断轻量/完整流程与交付门禁。

## Harness 职责

Harness 负责 AgentPM 开发变更的执行层治理：

- 判断轻量流程或完整闭环流程。
- 维护 `changes/` 变更目录。
- 约束 `change.md`、`request.md`、`api-contract.md`、`smoke-checklist.md`、`summary.md` 等交付产物。
- 明确验证命令和最终交付说明。

通用产品、架构、工程、测试和 Review 原则不在 Harness 中重复维护。

## 流程判定

### 默认先建轻量流程记录

任何开发变更都必须先有变更记录。以下任务默认只需要 `change.md`：

- 页面表现、布局、样式、文案调整。
- 非业务性静态信息调整。
- 小型共享组件抽取，不改变业务状态流转。
- 纯文档、模板或治理入口优化。

轻量记录路径：

```text
references/Harness/changes/<version>/<change-id>/change.md
```

如果变更风险在实施过程中升级，再从该目录继续补齐完整闭环所需文件。

### 升级完整闭环流程

命中以下任一条件时，必须补齐对应产物：

- 新增或修改后端 API：补 `api-contract.md`。
- 新增或修改数据库或持久化结构：补 `db-migrations.sql` 与 `rollback.sql`。
- 修改多页面流程、权限、角色、登录态、关键操作准入或核心状态流转：补 `flow.md` 与 `impact.md`。
- 发布级交付或架构调整：补完整十文件闭环。

完整闭环需求默认要求写明用户故事、端到端主路径、故事边界和可独立验收标准。

## 常用验证命令

AgentPM 常用验证命令：

```bash
cd backend && python -m pytest
cd frontend && npm run build
```

## 交付答复要求

最终答复必须包含：

- 本次采用“轻量流程”还是“完整闭环流程”。
- 修改范围摘要。
- 实际运行的验证命令和结果。
- 若未运行某项验证，说明原因。

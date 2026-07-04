# Code Rule

本文件是 Harness 执行层的编码适配说明，不重复维护通用工程原则。

## 主规则来源

通用工程原则以项目根目录的 `AGENT/ENGINEERING_RULES.md` 为准，包括：

- 小步迭代
- 最小范围修改
- Karpathy-style engineering rules
- 禁止猜测业务规则
- 禁止无验证交付
- 禁止越界重构
- 文档同步要求

## 本文件职责

本文件只补充 Harness 执行时与代码变更有关的落地要求：

- 代码变更必须先创建或更新变更目录，再判断采用轻量流程还是完整闭环流程。
- 低风险变更也必须补 `change.md`。
- 涉及 API、数据库、权限、多页面流程或核心状态流转时，必须升级完整闭环流程。
- 涉及 API 变化时，先更新 `api-contract.md`，再实现代码。
- 涉及数据库或持久化结构时，补 `db-migrations.sql` 与 `rollback.sql`。
- 最终交付必须写明验证命令和结果。

## 与 AGENT 规则的关系

若本文件与 `AGENT/ENGINEERING_RULES.md` 出现冲突，以 `AGENT/ENGINEERING_RULES.md` 的通用工程原则为准；Harness 只负责补充当前变更目录和交付门禁。

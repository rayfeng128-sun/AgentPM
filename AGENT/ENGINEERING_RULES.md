# Engineering Rules

## 目标

工程规则用于约束 agent 如何写代码、控制变更范围、避免过度设计，并显式纳入 Karpathy-style 工程原则。

## 基本原则

- 先规划后开发。
- 先输出设计方案。
- 未确认方案不得写代码。
- 小步迭代。
- 每个功能必须可测试。
- 每次影响需求、架构、流程或交付结论的修改必须更新文档。

标准流程：

```text
Plan -> Review -> Grooming -> Design -> Coding -> Testing -> Documentation
```

## Karpathy-style Rules

这些规则用于降低 LLM 编码常见风险：

- Keep it simple：优先选择最小可行实现，不主动引入复杂抽象。
- Make surgical changes：只修改完成当前任务必需的文件和行为。
- Do not guess business rules：没有依据的业务规则必须标记为假设，不得固化进正式实现。
- Prefer existing patterns：优先沿用项目已有目录、命名、工具和测试风格。
- Avoid premature abstraction：只有真实重复和真实复杂度出现时才抽象。
- Write boring code：业务系统优先清晰、稳定、可维护，不追求炫技。
- Verify before claiming done：没有测试、构建或冒烟证据，不得声称完成。
- Surface assumptions：关键假设必须写到文档、注释、契约或最终说明中。
- Preserve user work：不得回滚或覆盖用户未要求修改的内容。
- Refactor only inside scope：发现大问题可以记录，但不要顺手重构整个系统。

## 编码规则

- 命名优先体现业务语义，而不是技术细节。
- 共享逻辑优先复用已有工具或模块，避免复制粘贴。
- 注释只解释不自明边界、过渡假设或后续接入点。
- 新代码应覆盖加载态、空态、错误态和权限态中的关键路径。
- 前端页面不得直接操作底层 HTTP 细节。
- 后端 controller 不承载复杂业务组装。
- 接口返回结构应保持稳定，变更必须记录契约。

## 变更控制

- 禁止直接重构整个系统。
- 禁止一次性修改多个无关模块。
- 禁止删除已有功能，除非有明确替代方案和回退说明。
- 禁止只改代码不补记录。
- 禁止用“后面再补文档”绕过当前任务产物要求。

## 交付要求

最终交付必须说明：

- 本次采用轻量流程还是完整闭环流程。
- 修改范围。
- 验证命令和结果。
- 未验证项及原因。
- 遗留风险和后续建议。


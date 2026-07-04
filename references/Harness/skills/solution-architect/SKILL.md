---
name: solution-architect
description: 用于影响分析、边界设计、规则适配和实施路径判断
---

# 方案架构技能

## 目标

在不偏离当前技术阶段的前提下，为一次变更明确影响范围、边界和落地方式，并确保需求切分围绕用户故事而不是单个页面。

## 必读规则

- `references/Harness/QUICKSTART.md`

命中完整闭环升级条件时继续阅读：

- `AGENTS.md`
- `references/Harness/AGENTS.md`
- `references/Harness/rules/Project-Arch.md`
- `references/Harness/rules/Dev-Process-Rule.md`
- `references/Harness/rules/Change-Management-Rule.md`

## 输入

- 轻量流程：`changes/<version>/<change-id>/change.md`
- 完整闭环流程：`request.md`、`prototype.md`、`stitch-link.md`、`flow.md`

## 步骤

1. 读取当前需求与原型基线，先确认需求主语是否是用户故事与端到端闭环。
2. 先判断是否命中完整闭环升级条件。
3. 明确受影响的前端、后端、Mock/demo、权限、测试和文档范围。
4. 轻量流程在 `change.md` 中补充故事边界判断和验证要求。
5. 完整闭环流程在 `impact.md` 中说明当前阶段落地方案、故事闭环达成方式与未来真实后端边界。
6. 如发现现有规则缺口，先更新 `references/Harness/rules/` 再推进实现。
7. 对需要接口变更的需求先冻结 `api-contract.md`。

## 输出

- 轻量流程：`change.md` 中的边界判断
- 完整闭环流程：`impact.md`
- 边界判断
- 规则修订建议

## 禁止事项

- 强行引入未经确认的新技术栈
- 在无依据时发明业务规则
- 默许“页面已实现”替代“故事已闭环”
- 跳过影响分析直接拆开发任务
- 命中升级条件仍停留在轻量流程

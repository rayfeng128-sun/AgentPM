---
name: requirement-analyst
description: 用于需求整理、原型映射、流程说明和需求目录前置产物输出
---

# 需求分析技能

## 目标

把原始需求、产品文档、截图/原型和现有仓库状态整理成下游可直接执行的输入，默认以用户故事和端到端闭环作为需求定义主语。

## 必读规则

- `references/Harness/QUICKSTART.md`

命中完整闭环升级条件时继续阅读：

- `AGENTS.md`
- `references/Harness/AGENTS.md`
- `references/Harness/rules/Dev-Process-Rule.md`
- `references/Harness/rules/Change-Management-Rule.md`

## 输入

- 用户需求说明
- `docs/product/*.md`
- 现有实现代码

## 步骤

1. 在 `changes/<version>/<change-id>/` 下建立需求目录。
2. 判断本次需求采用轻量流程还是完整闭环流程。
3. 轻量流程在 `change.md` 中先写清用户故事、故事边界，再补目标、范围、原型来源、影响、验收、验证和风险。
4. 完整闭环流程在 `request.md` 中写清用户故事、业务背景、目标、范围、非目标、故事边界、端到端主路径和验收标准。
5. 完整闭环流程在 `prototype.md` 中整理页面结构、字段语义、关键状态与主要操作，作为故事实现的界面基线。
6. 完整闭环流程在 `stitch-link.md` 中记录外部原型链接或本地替代基线。
7. 完整闭环流程在 `flow.md` 中补齐主路径、异常路径和前后置条件。

## 输出

- 轻量流程：`change.md`
- 完整闭环流程：`request.md`、`prototype.md`、`stitch-link.md`、`flow.md`

## 禁止事项

- 不看产品或设计基线就整理需求
- 把单个原型页直接当作默认需求单位，不说明用户价值与闭环
- 跳过需求目录直接口头交接
- 把未确认问题隐藏不写
- 用轻量流程掩盖应升级的接口、权限、数据库或跨模块流程影响

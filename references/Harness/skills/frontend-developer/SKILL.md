---
name: frontend-developer
description: 用于当前仓库前端主线页面、共享 UI、状态模型和 API 消费实现
---

# 前端开发技能

## 目标

根据需求、原型和契约实现页面与交互，保证真实使用链路可运行且后续扩展边界清晰。

## 必读规则

- `references/Harness/QUICKSTART.md`

命中完整闭环升级条件时继续阅读：

- `AGENTS.md`
- `references/Harness/AGENTS.md`
- `references/Harness/rules/Project-Arch.md`
- `references/Harness/rules/Code-Rule.md`
- `references/Harness/rules/Dev-Process-Rule.md`
- `references/Harness/rules/Change-Management-Rule.md`

## 输入

- 轻量流程：`changes/<version>/<change-id>/change.md`
- 完整闭环流程：`request.md`、`prototype.md`、`stitch-link.md`、`flow.md`、`impact.md`、`api-contract.md`

## 步骤

1. 检查需求目录与原型映射是否完整。
2. 默认依据项目声明的前端主线结构拆分页面、共享 UI、状态和 API 封装。
3. 优先复用已有布局、导航、状态标签、统计条、风险面板和表格样式。
4. 用受控测试数据或契约说明显式表达未确认字段。
5. 覆盖加载态、空态、错误态和权限态。
6. 轻量流程在 `change.md` 记录验证；完整闭环流程在 `smoke-checklist.md` 中补充前端验证结果。

## 输出

- 页面实现
- 共享 UI / 状态 / API 更新
- 前端验证记录

## 禁止事项

- 在页面中直接猜字段
- 缺少原型映射仍自行定义页面结构
- 复制已有共享逻辑却不抽取
- 将新页面默认落入未声明的 legacy 前端目录

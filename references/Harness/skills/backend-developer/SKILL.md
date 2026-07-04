---
name: backend-developer
description: 用于当前仓库后端主线和接口承载能力实现
---

# 后端开发技能

## 目标

在当前阶段维护项目声明的后端主线服务，为真实业务闭环和后续生产化后端接入提供稳定边界。

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
- 完整闭环流程：`request.md`、`flow.md`、`impact.md`、`api-contract.md`

## 步骤

1. 检查接口契约是否已冻结。
2. 默认在项目声明的后端主线结构内实现最小变更，不额外扩散架构。
3. 对过渡型接口显式标记临时承载性质与后续收敛边界。
4. 补最小自动化验证或运行验证说明。
5. 在需求目录中记录对后续持久化、权限和外部系统接入的边界。

## 输出

- 后端主线代码变更
- 接口承载实现
- 后续边界说明

## 禁止事项

- 引入当前阶段不需要的复杂抽象
- 未更新契约就先改接口
- 把临时实现伪装成真实持久化能力
- 将新接口默认落入未声明的 legacy 后端目录

# Architecture Rules

## 目标

架构规则用于约束 agent 如何判断目录职责、模块边界、依赖方向和技术文档要求。

## 项目结构

每个项目应明确：

- 主线前端目录
- 主线后端目录
- 文档目录
- 变更记录目录
- legacy fallback 目录
- 外部集成或基础设施目录

示例：

```text
<project-root>/
  AGENTS.md
  PLANS.md
  docs/
    product/
    architecture/
    process/
  references/
    Harness/
      rules/
      changes/
```

## 依赖方向

- UI / route 只负责页面编排，不直接承载复杂业务规则。
- 前端页面应通过 store、API client 或业务 API 模块访问后端。
- 后端 controller 只处理 HTTP 边界，不直接访问 repository、store、job store 或外部 demo 服务。
- service 负责业务编排，repository 只负责持久化访问。
- 公共层只放通用能力，不放业务域专属规则。

## 架构决策

涉及以下情况时必须先设计再实现：

- 新增模块或改变模块边界。
- 新增 API、数据库、权限或跨模块流程。
- 引入新技术栈、中间件或外部系统。
- 抽离共享组件、共享服务或基础设施能力。
- 迁移 legacy fallback 到主线实现。

## 技术架构文档

架构文档应回答：

- 当前使用什么技术栈。
- 系统由哪些节点组成。
- 前端、后端、数据、集成分别负责什么。
- 本地开发、测试、预发布和生产拓扑是什么。
- 哪些能力已实现，哪些仍是规划。

必须明确区分：

- 当前已实现
- 当前计划内
- 历史 fallback
- 未来规划 / 未落地

## 禁止事项

- 禁止在没有需求依据时新增复杂架构。
- 禁止一次性跨多个无关模块大重构。
- 禁止把规划态内容写成已实现事实。
- 禁止让公共层沉积业务域规则。
- 禁止架构变更后不更新架构文档。


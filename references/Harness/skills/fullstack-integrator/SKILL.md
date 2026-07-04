---
name: fullstack-integrator
description: 用于联调、结构校验、冒烟验证和交付收口
---

# 全链路集成技能

## 目标

确保一次变更具备完整产物、可运行验证和可交付总结。

## 必读规则

- `references/Harness/QUICKSTART.md`

命中完整闭环升级条件时继续阅读：

- `AGENTS.md`
- `references/Harness/AGENTS.md`
- `references/Harness/rules/Dev-Process-Rule.md`
- `references/Harness/rules/Change-Management-Rule.md`

## 输入

- 轻量流程：`change.md`
- 完整闭环流程：需求目录十件套
- 代码实现结果
- 运行与测试命令

## 步骤

1. 检查本次选定流程的需求目录文件是否齐全。
2. 运行相关测试、结构校验或本地启动命令。
3. 轻量流程在 `change.md` 中记录验证结果；完整闭环流程在 `smoke-checklist.md` 中记录关键路径、异常路径和结果。
4. 完整闭环流程在 `summary.md` 中记录实现内容、验证结论、残余风险和后续边界。
5. 只有在文档与验证都完整时，才宣布交付闭环。

## 输出

- 冒烟记录
- 交付总结
- 最终结论

## 禁止事项

- 缺少验证就宣布完成
- 需求目录不闭环仍判定可交付
- 忽略已知风险和边界

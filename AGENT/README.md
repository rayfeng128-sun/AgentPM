# Agent Rules

本目录存放可复用的 agent 开发治理规则。默认只启用第一批核心规则，避免规则过细导致前置阅读成本过高。

## 默认阅读顺序

1. `PRODUCT_RULES.md`
2. `ARCHITECTURE_RULES.md`
3. `ENGINEERING_RULES.md`
4. `TEST_RULES.md`
5. `REVIEW_RULES.md`

## 设计原则

- 产品规则定义“做什么”和“为什么做”。
- 架构规则定义“放哪里”和“边界是什么”。
- 工程规则定义“怎么写”和“哪些行为禁止”。
- 测试规则定义“怎么证明它可用”。
- Review 规则定义“怎么判断可以交付”。

专项规则如 Git、安全、UI、Prompt 可按项目需要再启用，不作为所有项目默认强规则。


# 变更目录说明

本目录用于管理 AgentPM 仓库的版本化需求变更。

如果要先理解当前需求体系与阅读顺序，再进入具体变更目录，优先看：

- [docs/README.md](../../../docs/README.md)
- [references/Harness/changes/v-template/README.md](v-template/README.md)

使用规则：

- 先建版本目录，再建需求目录。
- 任何开发变更都必须落到一个实际需求目录，不能只保留模板。
- 默认按用户故事和端到端闭环切分需求，原型页只作为辅助基线。
- 默认按风险选择轻量流程或完整闭环流程。
- 轻量变更目录只需补齐 `change.md`。
- 命中接口、数据库、权限、多页面流程、架构或发布级交付时，必须升级完整闭环流程并补齐十件套或对应升级文件。
- 页面型需求必须登记产品文档、截图、原型或设计基线来源。
- 所有交付结论都要落回对应需求目录。

轻量流程推荐起步方式：

1. 复制 `v-template/TECH-000-lightweight-template/`
2. 重命名为新的 `<TYPE>-<SEQ>-<slug>`
3. 补齐 `change.md`

当前 AgentPM 的实际变更记录应放到例如 `v0.1.0/` 这样的版本目录下，而不是继续停留在 `v-template/`。

完整闭环流程推荐起步方式：

1. 复制 `v-template/FEAT-000-template/`
2. 重命名为新的 `<TYPE>-<SEQ>-<slug>`
3. 逐个补齐十件套内容

# 项目指令迁移记录

**日期：** 2026-07-18

**状态：** complete

## 原因

仓库根目录曾存在 `AGENTS.md`，其中混合了用户级 GitHub 信任、理论入口、网页推导工作流和仿真器开发边界。GitHub 可信目标属于用户级 Codex 配置，不应由项目仓库自行声明；其余规则也应由对应领域文档拥有。

## 迁移结果

| 原内容 | 迁移后的权威位置 |
|---|---|
| `Persenz1` GitHub namespace 与 `Spine_Sim_V3` 可信远端 | 用户级 `C:\Users\23635\.codex\AGENTS.md`；不进入本仓库版本控制 |
| 当前理论权威、proposed/accepted 边界、P0 和 B→C 阻断 | [`theory/README.md`](../theory/README.md) |
| 网页推导提示词编写与产物回收 | [`PROMPT_AUTHORING_GUIDE.md`](../archive/web_pro_derivation_2026-07-17/docs/derivation_workflow/guides/PROMPT_AUTHORING_GUIDE.md) 与 [`RUN_ARTIFACT_HANDLING_GUIDE.md`](../archive/web_pro_derivation_2026-07-17/docs/derivation_workflow/guides/RUN_ARTIFACT_HANDLING_GUIDE.md) |
| 仿真器模块顺序、需求/实现分窗、M06 只读边界和首版标签 | [`docs/simulator_development/README.md`](simulator_development/README.md)、[`SIMULATOR_MODULE_PLAN.md`](simulator_development/SIMULATOR_MODULE_PLAN.md) 与 [`REQUIREMENTS_DISCUSSION_WORKFLOW.md`](simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md) |

仓库根 `AGENTS.md` 已删除。当前仿真器提示词不再要求读取该文件，而是直接读取对应的权威入口。

旧 `AGENTS.md` 只作为迁移线索进行复核，没有整体搬运：理论条目已被更完整的现行 `theory/README.md` 覆盖；网页推导条目属于已完成归档的历史流程，不恢复为当前项目规则，归档中的旧窗口提示词也保持原样以保存审计上下文；仿真器条目则按当前 M00 冻结与实现验收状态和现行工作流重写到开发入口。

## 时效性复核

Git 历史显示，项目 `AGENTS.md` 的最后一次内容更新是提交 `de26cb2`（2026-07-17 15:40 +08:00）；仿真器提示词随后在 `265a182` 更新，M00 冻结需求在 `3af780d` 写入，M00 基础软件实现与验收又在 `777ba4d`（2026-07-18）提交。因此旧文件不能作为当前仿真进度或门状态的权威来源。

- 理论条目与现行 `theory/README.md` 一致的部分不重复搬运；以后直接维护理论入口；
- 网页推导条目只解释已完成的归档流程，不作为当前默认任务入口；
- 仿真器条目按 M00 已冻结且基础软件实现已验收、M01–M08 尚未冻结/实现的实际状态重写；
- GitHub 信任来自用户确认，独立于项目进度，故只保存在用户级 Codex 配置。

## 历史文件说明

`M00_FOUNDATION_REQUIREMENTS 1.0.0` 冻结时确实读取了当时的仓库 `AGENTS.md`。后续文档维护只把该历史引用指向本迁移记录，不改变 M00 已冻结的配置、结果 API、schema、重放或验收语义。

# 仿真器开发任务入口

**版本：** 0.1.3
**状态：** m00-requirements-frozen / m00-implementation-accepted / m01-requirements-frozen / m01-implementation-not-started
**适用范围：** 第一版无实验数据的 A/B 趋势选型仿真器，以及后续受限 C 层诊断

本目录把仿真器开发拆成“需求讨论窗口”和“实现窗口”两个阶段。当前已冻结并实现 M00，其基础软件合同已通过验收；M01 需求已经冻结但尚未实现，后续物理模块也未实现，仓库仍不包含表面、接触或其他求解器物理。

## 1. 第一版目标

第一版必须能在没有任何实测输入文件时完成一次可重放的合成实验：

`配置解析 → 带来源与可信尺度的解析/合成 SurfaceRealization → 单刺 A-M0 → 阵列 B-M0 → 参数/种子实验矩阵 → 原始结果与摘要落盘 → 绘图模块离线读取并出图`。

结果只服务参数选型、趋势判断和方案排序，统一标记为 `DEV_PRIOR / synthetic_surface / no_damage / not_certifiable`。不要求拟合真实壁面绝对承载，也不把正式 C 偏心承载作为首版完成条件。

理论与工程事实入口统一从 [`theory/README.md`](../../theory/README.md) 进入。层内实现以 `theory/modules/` 为权威，`theory/interfaces/` 是嵌入合同的独立镜像；工程事实与文献反向复核使用 `theory/evidence_reassessment/` 工作副本。归档保留完整源和历史运行，不作为普通开发任务的默认输入。

本目录的 `0.1.2` 对齐 `MECHANISM_DERIVATION_FORMAL 0.2.0-proposed` 新增的故事桥接，但不提升其规范等级。后续冻结需求必须把输入分成 `FIXED_ENGINEERING`、`ACCEPTED_AUTHORITY`、`PROPOSED_SUPPLEMENT`、`DEV_POLICY` 和 `VALIDATION_ONLY`；proposed 的表面合同、接触阶段分栏、释放—再接触路径、阵列诊断和执行器端口桥只能作为结构性补充或验证义务，不能静默覆盖 accepted 1.0。

## 2. 文件导航

- [仿真器模块规划](SIMULATOR_MODULE_PLAN.md)：模块边界、依赖顺序、参数与输出职责、首版完整实验定义；
- [需求讨论工作流](REQUIREMENTS_DISCUSSION_WORKFLOW.md)：每个讨论窗口的统一规则、冻结产物和绘图数据缺口流程；
- [逐模块需求讨论提示词](prompts/requirements_discussion/README.md)：复制到各自新窗口使用；
- [已冻结需求](requirements/)：`M00_FOUNDATION_REQUIREMENTS 1.0.0` 与 `M01_SURFACE_REQUIREMENTS 1.0.0`；
- [实现窗口提示词](implementation_prompts/)：当前已有 M00 与 M01；
- [M00 实施追踪与验收](implementation/M00_FOUNDATION_TRACEABILITY.md)：记录基础包、测试、性能和解释边界；
- [项目指令迁移记录](../PROJECT_INSTRUCTION_MIGRATION_2026-07-18.md)：说明旧项目级 `AGENTS.md` 的拆分位置和历史引用处理。

## 3. 推荐窗口顺序

1. `M00_FOUNDATION`：基础契约、配置、结果外壳；
2. `M01_SURFACE`：解析与合成表面；
3. `M02_NUMERICS`：延拓、事件、事务和重放；
4. `M03_SINGLE_SPINE`：A-M0 单刺；
5. `M04_ARRAY_UNIT`：B-M0 阵列单元；
6. `M05_EXPERIMENT_RUNNER`：设计矩阵和批量运行；
7. `M06_PLOTTING`：只读绘图与动态配方；
8. `M07_FIRST_RELEASE_INTEGRATION`：首版完整合成实验；
9. `M08_C_DIAGNOSTIC`：首版之后的 C 合同安全诊断，不阻塞前八项。

每个需求讨论窗口结束后必须停止。实现提示词只能根据该窗口最终冻结的需求生成，不能用当前通用规划直接开始编码。

## 4. 当前进度

| 模块 | 需求 | 实现 |
|---|---|---|
| M00 FOUNDATION | `1.0.0 frozen` | completed / acceptance passed（仅基础软件范围） |
| M01 SURFACE | `1.0.0 frozen` | 未开始；下一实现窗口 |
| M02–M05 | 未冻结 | 未开始 |
| M06 PLOTTING | 未冻结；M00 ResultReader 已提供，仍待 M01–M05 demo | 未开始 |
| M07 | 未冻结 | 未开始 |
| M08 | deferred；不阻塞首版 A/B | 未开始 |

本表只记录开发门状态，不用单个 `complete` 替代各模块后续应保存的理论、代码、数值和实验成熟度。

## 5. 开发执行边界

- 仿真器规划和实现从本文件进入，并遵循 [需求讨论工作流](REQUIREMENTS_DISCUSSION_WORKFLOW.md)；
- 每个模块先开需求讨论窗口，冻结需求后再另开实现窗口，不得从通用规划直接编码；
- 严格遵守 [M00→M07 依赖和冻结门](SIMULATOR_MODULE_PLAN.md)，M08 C 诊断延期且不阻塞首版 A/B；
- M06 绘图只读取版本化 ResultReader/API，不调用仿真内部对象、不修改 canonical 结果、不重跑仿真；数据缺口必须形成版本化 `PLOT_DATA_GAP_REQUEST`，由源模块在独立任务中处理；
- 首版结果始终标记为 `DEV_PRIOR / synthetic_surface / no_damage / not_certifiable`，不得索要不存在的实验数据或把开发先验提升为实测材料参数。

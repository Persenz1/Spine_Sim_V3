# 逐模块需求讨论提示词

**版本：** 0.1.2

这些提示词用于新建“需求讨论窗口”，不用于实现。推荐按顺序复制正文：

| 顺序 | 模块 | 提示词 | 结果 |
|---:|---|---|---|
| 1 | M00 FOUNDATION | [M00_FOUNDATION_REQUIREMENTS_DISCUSSION.md](M00_FOUNDATION_REQUIREMENTS_DISCUSSION.md) | 基础配置、对象、结果 API 与 schema |
| 2 | M01 SURFACE | [M01_SURFACE_REQUIREMENTS_DISCUSSION.md](M01_SURFACE_REQUIREMENTS_DISCUSSION.md) | 表面参数、查询、输出和图形 |
| 3 | M02 NUMERICS | [M02_NUMERICS_REQUIREMENTS_DISCUSSION.md](M02_NUMERICS_REQUIREMENTS_DISCUSSION.md) | 延拓、事件、事务和诊断 |
| 4 | M03 SINGLE SPINE | [M03_SINGLE_SPINE_REQUIREMENTS_DISCUSSION.md](M03_SINGLE_SPINE_REQUIREMENTS_DISCUSSION.md) | A-M0 参数、状态、输出和图形 |
| 5 | M04 ARRAY UNIT | [M04_ARRAY_UNIT_REQUIREMENTS_DISCUSSION.md](M04_ARRAY_UNIT_REQUIREMENTS_DISCUSSION.md) | B-M0 选型参数、逐针/单元输出和图形 |
| 6 | M05 EXPERIMENT RUNNER | [M05_EXPERIMENT_RUNNER_REQUIREMENTS_DISCUSSION.md](M05_EXPERIMENT_RUNNER_REQUIREMENTS_DISCUSSION.md) | 计算实验矩阵、运行与排名输入 |
| 7 | M06 PLOTTING | [M06_PLOTTING_REQUIREMENTS_DISCUSSION.md](M06_PLOTTING_REQUIREMENTS_DISCUSSION.md) | 只读 reader、动态 recipe 与数据缺口 |
| 8 | M07 FIRST RELEASE INTEGRATION | [M07_FIRST_RELEASE_INTEGRATION_REQUIREMENTS_DISCUSSION.md](M07_FIRST_RELEASE_INTEGRATION_REQUIREMENTS_DISCUSSION.md) | 第一版完整无实验数据闭环 |
| 9 | M08 C DIAGNOSTIC | [M08_C_DIAGNOSTIC_REQUIREMENTS_DISCUSSION.md](M08_C_DIAGNOSTIC_REQUIREMENTS_DISCUSSION.md) | 延期 C 合同诊断与安全拒绝 |

规则：

- 前置 requirements 未冻结时，不开始下游讨论；
- 讨论窗口不得编码；
- 实现提示词由对应讨论窗口根据冻结需求生成；
- 每个窗口结束后停止，不自动开始下一个模块；
- M08 不阻塞 M07；
- 当前理论和工程事实从 `theory/README.md` 与 `theory/evidence_reassessment/` 工作副本读取，不修改归档源；
- `theory/interfaces/` 是模块内嵌公共合同的独立镜像，不得与 `theory/modules/` 形成第二套物理。
- 每个冻结决定都要使用工作流定义的 `FIXED_ENGINEERING / ACCEPTED_AUTHORITY / PROPOSED_SUPPLEMENT / DEV_POLICY / VALIDATION_ONLY` 来源身份；
- proposed 机理桥只能形成 additive schema、诊断、验证或明确 deferred/amendment，不得静默替换 accepted；
- 提交前精确暂存本模块产物并检查 cached diff，禁止把其他窗口的工作区改动一并提交。

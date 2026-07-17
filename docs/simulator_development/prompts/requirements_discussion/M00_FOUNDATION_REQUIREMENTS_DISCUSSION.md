# M00 FOUNDATION 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M00_FOUNDATION_REQUIREMENTS

本窗口只讨论并冻结 M00 FOUNDATION（基础契约、配置、结果 API）的需求。不得编写求解器或绘图代码，不得自动开始 M01 或实现阶段。

项目定位是爪刺参数选型和趋势筛选，不是绝对承载数字孪生。第一版没有任何实验数据，必须支持 synthetic_surface + no_damage + DEV_PRIOR 的完整 A/B 合成实验。绘图模块以后只能读取结果 API，不能调用或参与仿真，因此 M00 必须先提供稳定、可扩展且可重放的数据外壳。

开始前完整读取：
1. AGENTS.md；
2. README.md、theory/README.md；
3. docs/simulator_development/README.md；
4. docs/simulator_development/SIMULATOR_MODULE_PLAN.md；
5. docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md；
6. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
7. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
8. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
9. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
10. theory/system/SYSTEM_INTEGRATED_MODEL.md，重点核对第 25–30、40–45 节，但不得只凭摘要猜测全局对象边界。

权威顺序：正式工程事实 > accepted system/module/contracts。复核报告中的 P0 是实现安全边界；proposed 文件可提供闭合建议，但不得静默改写 accepted 1.0。DEV_BOOTSTRAP_PROFILE 只是开发配置，不是真实材料标定。

讨论方式：
- 先根据仓库证据提出一版明确默认方案和你认为必须由用户决定的少量事项；
- 每轮最多问 1–3 个会真正改变需求的问题；
- 不询问实验数据；
- 分轮讨论“配置/单位与身份”“状态与事务对象”“结果存储和读取 API”“schema 演化与重放”“性能和验收”；
- 持续维护 accepted/rejected/deferred/unresolved 决策表。

本窗口必须关闭的问题：
1. 配置文件层级、覆盖顺序、严格校验和 resolved config；
2. 内部 N–mm–MPa 单位规范化及输入单位策略；
3. run/case/design/seed/surface/state/event/receipt 的 ID 与 hash；
4. immutable、accepted、trial cache、event、transaction、output 的所有权边界；
5. accepted points、committed events、rejected trials、summary 的物理隔离；
6. canonical result bundle 的语义结构、存储格式候选、分块、压缩与数值精度；
7. ResultWriter/ResultReader 的公共能力和字段元数据查询；
8. null/unavailable/unsupported/numerical_failure/physical_infeasible 的区分；
9. deterministic replay manifest、版本和来源哈希；
10. additive 与 breaking schema 变更及旧结果读取策略；
11. 各物理模块怎样注册扩展字段而不反向依赖 M00；
12. M00 自身的单元测试、schema 测试、重放测试和最小性能要求。

硬边界：
- M00 不拥有任何接触、摩擦、梁、阵列或 C 层物理；
- 不把 trial 值写成 accepted 曲线；
- 不允许隐式单位、frame、reference point 或参数默认；
- 不用单个 complete/success 布尔值掩盖成熟度和失败分类；
- 不为绘图预先删减原始字段。

只有用户明确确认“冻结/按这个做”后，才：
1. 写 docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md；
2. 按 REQUIREMENTS_DISCUSSION_WORKFLOW.md 的最小结构完成需求、基础输出合同和验收标准；
3. 根据冻结内容生成 docs/simulator_development/implementation_prompts/M00_FOUNDATION_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验链接、字段语义和与系统输出外壳的一致性；
5. 提交并推送需求产物；
6. 报告需求版本、提交号和实现提示词路径后停止。

不得在本窗口实现 M00。
```

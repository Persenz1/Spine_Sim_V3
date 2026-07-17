# M02 NUMERICS 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M02_NUMERICS_REQUIREMENTS

本窗口只讨论并冻结 M02 NUMERICS（延拓、事件、事务和重放服务）的需求。不得编码，不得替 A/B 选择或改写物理本构。

第一版必须能在无实验数据下可靠推进 A/B 的非光滑准静态路径。M02 是数值与状态协调服务：它可以求残量、定位事件、管理 trial/commit，但不能拥有摩擦、梁、弹簧或阵列载荷共享规律。

开始前完整读取：
1. AGENTS.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00_FOUNDATION_REQUIREMENTS.md；
4. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
5. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
6. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
7. theory/system/SYSTEM_INTEGRATED_MODEL.md；
8. theory/modules/A_INTEGRATED_MODEL.md 与 B_INTEGRATED_MODEL.md 中残量、事件、事务、失败分类和输出章节。

讨论方式：
- 先给出一版最小而不偷换物理的数值服务边界；
- 每轮最多询问 3 个影响 API、诊断粒度或运行成本的问题；
- 依次讨论“延拓与求解”“事件”“事务/重放”“诊断输出/图”“验收”；
- 数值值均视为起点，最终通过收敛冻结，不通过实验拟合。

本窗口必须关闭的问题：
1. continuation target、accepted step 与 trial step 的对象和调用关系；
2. 初始/最大/最小步长及增长、缩短和重试策略；
3. 残量块、缩放、绝对/相对容差与互补/graph 质量；
4. Newton/线搜索/信赖域或可替代算法的首版范围；
5. signed event guard、方向、括区、求根和事件最早性；
6. B 曲线平衡路径每个事件探测点必须重求 uz，A event fraction 只作 predictor；
7. 同时事件、依赖偏序、同位置级联和 Zeno 防护；
8. trial/prepare/commit/rollback 的无副作用与幂等；
9. commit receipt、rollback token 和 deterministic replay；
10. rejected trial diagnostics 与 accepted/event 输出分离；
11. numerical_failure、physical_infeasible、contract_rejection、domain_error 的分类；
12. 首批图：残量迭代、步长、事件括区、精化误差、失败统计；
13. 解析根、事件顺序、rollback、重复调用和精化收敛测试。

硬边界：
- Newton 收敛不等于物理稳定，Newton 失败不等于物理无解；
- trial、事件探测和 rollback 不推进路径、时间、功、事件号或状态；
- 不用大罚刚度冒充严格刚性物理；
- 不用固定步长端点布尔变化替代最早事件定位；
- M02 不决定 A/B 的活动分支物理意义，只执行模块提供的残量、guard 和提交意图。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md；
2. 定义公共数值请求/响应、事件/事务对象、诊断输出和失败语义；
3. 生成 docs/simulator_development/implementation_prompts/M02_NUMERICS_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验与 M00 状态对象、A/B 事件策略和 profile 起点一致；
5. 提交推送并报告后停止。

不得在本窗口实现求解器。
```

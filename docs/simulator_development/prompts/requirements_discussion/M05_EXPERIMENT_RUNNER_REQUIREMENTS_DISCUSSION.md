# M05 EXPERIMENT RUNNER 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M05_EXPERIMENT_RUNNER_REQUIREMENTS
PROMPT_VERSION: 0.1.3

本窗口只讨论并冻结 M05 EXPERIMENT RUNNER（实验矩阵、批量执行、摘要与排名输入）的需求。不得编码，不得修改 M01/M03/M04 的物理。

第一版没有任何实测数据。这里的“实验”是可重放的计算实验：以宽先验和公共随机数比较设计趋势。M05 只组织 case 和读取模块结果，不拥有表面生成、接触、单刺或阵列本构。

开始前完整读取：
1. README.md、theory/README.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00–M04 requirements；
4. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
5. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
6. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
7. theory/system/SYSTEM_INTEGRATED_MODEL.md 第 25–30、36–37、43–45 节；
8. M03/M04 的 canonical output contracts。

讨论方式：
- 先提出 smoke/development/screening 三档默认实验设计；
- 每轮最多问 3 个与计算预算、首批对照或排名输出有关的问题；
- 分轮讨论“实验问题/因素”“case 生成与 seed”“运行/恢复”“摘要与排名”“绘图数据/验收”；
- 不要求用户提供实验数据，也不设计微观参数反演。

本窗口必须关闭的问题：
1. experiment/design/case/replicate/seed 的身份和层级；
2. 哪些因素是首版对照、全扫描或延期；
3. smoke 4 seeds、development 16、screening 64 及顺序加样策略；
4. common random numbers 的配对范围；
5. 单刺、刚性阵列、弹簧阵列分别进入哪些实验组；
6. 是否完整跑 100 mm、怎样定义调试短程且不混入正式结果；
7. case matrix 展开、配置 hash、去重和缓存；
8. 并发、检查点、恢复、中断、重试和单 case 失败隔离；
9. completed/failed/unavailable/skipped 的严格含义；
10. 原始结果引用与 experiment-level index；
11. geometric candidate、loaded contact 和首次 load-bearing 事件怎样区分，怎样记录伪挂接、释放、再接触和同一次 episode；
12. 首次有效挂接距离的非参数生存/风险曲线、100 mm 未挂接右删失和可选参数化模型的显式 opt-in；
13. 允许派生的峰值、多峰、正功、释放—再挂接间距、episode 持续距离、Neff、加载不均和计算成本摘要；
14. 排名、置信区间、seed 收敛和排名翻转，不固定单一综合评分；
15. 结果 provenance、来源身份与 DEV_PRIOR/synthetic_surface/no_damage/not_certifiable 标签；
16. M06 需要的筛选、分组和分面字段；
17. 小型端到端 fixture、右删失、恢复重放、并发确定性和统计验收。

首版完整实验矩阵应保持“小而完整”，至少覆盖：
- 一个解析事件表面和一个合成随机表面族；
- 单刺 baseline；
- 一个代表性转置阵列对照；
- rigid vs independent spring；
- 至少两个会改变选型趋势的设计参数；
- 多个公共 seed；
- 一个预期失败或 unavailable case，用于证明分类正确。

硬边界：
- 不把 case 失败自动重试到改变物理配置；
- 不用失败样本静默补零；
- 不把同一高采样轨迹的点当独立 replicate；
- 不把 geometric candidate、零力接触或短暂摩擦稳定直接计作有效挂接；
- 不把 100 mm 内未挂接样本删除或当作零距离，必须保留右删失；
- 不把单个 seed 的最大峰当设计结论；
- 不在 M05 重新计算低层物理或修改 canonical raw；
- 第一版不包含正式 C Fcrit 排名。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M05_EXPERIMENT_RUNNER_REQUIREMENTS.md；
2. 冻结实验配置、case schema、运行档、摘要、排名输入和验收；
3. 生成 docs/simulator_development/implementation_prompts/M05_EXPERIMENT_RUNNER_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验与 M00–M04、profile 和绘图读取需求闭合；
5. 提交推送并报告后停止。

提交前严格执行 REQUIREMENTS_DISCUSSION_WORKFLOW 的 Git 安全交接：只精确暂存本任务文件，检查 cached diff，禁止使用 git add -A/git add .，不得纳入其他窗口的工作区改动。

不得在本窗口编码或运行正式实验。
```

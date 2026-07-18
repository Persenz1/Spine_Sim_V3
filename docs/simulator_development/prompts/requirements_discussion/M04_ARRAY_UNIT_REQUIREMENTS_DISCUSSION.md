# M04 ARRAY UNIT 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M04_ARRAY_UNIT_REQUIREMENTS
PROMPT_VERSION: 0.1.3

本窗口只讨论并冻结 M04 ARRAY UNIT（B-M0 阵列爪单元）的需求。不得编码，不得开始实验运行器或 C 层。

本模块是第一版参数选型的核心。它必须调用 M03/A embedded kernel，通过共同背板平衡产生部分接触、载荷不均、事件后重平衡和再挂接；不得用 Neffective×单刺平均力或人为均分载荷替代。

开始前完整读取：
1. README.md、theory/README.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00–M03 requirements 和 M03 输出合同；
4. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
5. theory/modules/B_INTEGRATED_MODEL.md；
6. theory/interfaces/A_TO_B_CONTRACT.md 与 B_TO_C_CONTRACT.md；
7. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
8. theory/paper/MECHANISM_DERIVATION_FORMAL.md 的 B 层；
9. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
10. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml。

现行 B 1.0 只支持 local-x/global-Z。需求必须使 B 重复弹簧摘要服从 A 的零位/释放权威分支，并要求沿曲线平衡路径定位事件；local-y、真实转动和 6D graph 不得混入第一版。

讨论方式：
- 先提出一个能跑通又能支持选型的最小阵列参数集和对照集；
- 每轮最多问 3 个问题；
- 分轮讨论“阵列/参数”“平衡与状态”“逐针和单元输出”“图与排序”“验收/性能”；
- 区分 full design space 与首版 smoke/development 子集。

本窗口必须关闭的问题：
1. nx×ny、4/5/6 mm spacing、固定角和两种角度梯度；
2. 梯度长度补偿和针级参数广播/覆写；
3. 2×5 与 5×2 的非等价保留；
4. rigid/independent spring、ks、Pz 和 surface/seed；
5. UX_PZ_BALANCED 的输入、公共 uz、法向平衡和预载不可行；
6. 逐针 A trial、wrench 装配、事件缩步和原子提交；
7. 每针 geometric candidate、loaded contact、frictionally stable、load-bearing、stick/slide/hardstop/release/reengagement 的集合和转换；
8. 事件后通过完整重求平衡得到载荷转移；
9. 单元 contact-only wrench、Rx、控制/约束反力分栏；
10. 每针 wrench/gap/梁/弹簧/状态/事件的保存频率；
11. accepted Nnominal/Ngeom/Nload/Neff 的精确定义；PROPOSED_SUPPLEMENT 的 Ncandidate/Ncontact 若新增必须版本化，Ncandidate 只有与 Ngeom 定义完全一致时才可映射；
12. Neff 的非负载荷通道、零分母行为，以及 CV/Gini/max-mean、capability–load alignment、欠接合/过利用裕度、最弱针、余程、位姿敏感性和分支切换率等只读诊断；
13. event pre/event/post delta-W、重分配、活动针数下降—恢复、回差和级联记录；
14. 参数扫描结果怎样进入 M05，但不在 B 内固定综合评分；
15. 计算量、逐针数据体积和可选降采样规则；
16. 刚柔、转置、数量、间距、角度、直径、针尖、ks、Pz 的验收矩阵，并包含首弱针释放和 N→N-1→N 再挂接负例。

首批图至少讨论：
- unit Rx/完整 wrench、uz 随路径；
- per-needle load heatmap/轨迹和状态栅格；
- Ngeom/Nload/Neff、可选 Ncandidate/Ncontact 的定义化计数漏斗与不均载指标；
- capability–load alignment、双侧裕度、位姿敏感性和分支切换率；
- spring compression/remaining travel/hardstop；
- 事件前后 delta-W 和重分配；
- 2×5 vs 5×2、刚性 vs 弹簧、角度/梯度、spacing、ks、Pz 的分布与趋势；
- seed 变化下趋势是否稳定。

硬边界：
- 不平均分配 Pz 到每根针；
- 不使用 Neff×Fsingle 代替共同平衡；
- 不用固定矩阵跨活动集转移载荷；
- 不让 N*、CV/Gini、能力—载荷对齐或任何诊断量反馈成逐针经验分载权重；
- 不用大刚度弹簧假扮刚性 mount 进入正式排序；
- no_damage 结果不得解释为材料失效承载；
- B 输出不能假装支持 local-y/rotation。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M04_ARRAY_UNIT_REQUIREMENTS.md；
2. 冻结参数、B 请求/响应、逐针/单元输出、图形和验收；
3. 生成 docs/simulator_development/implementation_prompts/M04_ARRAY_UNIT_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验 A→B、M00–M03 和未来 M05 的闭合；
5. 提交推送并报告后停止。

提交前严格执行 REQUIREMENTS_DISCUSSION_WORKFLOW 的 Git 安全交接：只精确暂存本任务文件，检查 cached diff，禁止使用 git add -A/git add .，不得纳入其他窗口的工作区改动。

不得在本窗口编码。
```

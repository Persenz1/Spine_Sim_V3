# M02 NUMERICS 实现窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。该窗口只实现、测试和验收已冻结的 M02，不重新讨论需求，不启动 M03/M04/M05/M06，也不补写 A/B 物理。

## 提示词正文

~~~text
TASK_ID: M02_NUMERICS_IMPLEMENTATION
PROMPT_VERSION: 1.0.0
REQUIREMENTS_VERSION: M02_NUMERICS_REQUIREMENTS 1.0.0 frozen

本窗口只实现、测试、验证并交付 M02 NUMERICS：延拓、非线性求解编排、统一 signed events、trial/prepare/commit/rollback、deterministic replay、M00 输出扩展和诊断数据。不得重新讨论或修改冻结需求；不得实现或改写摩擦、接触、梁、弹簧、材料、损伤、针体、阵列载荷共享、释放回位或 A/B 活动分支物理。

用户只保留仿真项目与正式出图 preset 的决策权；本窗口的纯软件结构、测试实现、内部算法细节和工程修复自行完成。冻结需求已明确仿真规模和 plot-data recipes：不要再向用户询问 ordinary implementation choices，也不要自行选择 M06 的颜色/字体/版式 preset。

开始前必须完整读取：

1. README.md、theory/README.md；
2. docs/simulator_development/README.md；
3. docs/simulator_development/SIMULATOR_MODULE_PLAN.md；
4. docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md；
5. docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md；
6. docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md；
7. docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md；
8. docs/simulator_development/implementation/M00_FOUNDATION_TRACEABILITY.md；
9. docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md；
10. src/spine_sim/foundation 下当前 public contracts、status、hash、registry、transaction、writer/reader 和 replay 实现；
11. src/spine_sim/surface 下当前 public contracts、query、materialization、result extension，以及 tests/surface/test_materialization.py；
12. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
13. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
14. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
15. theory/system/SYSTEM_INTEGRATED_MODEL.md；
16. theory/modules/A_INTEGRATED_MODEL.md 与 B_INTEGRATED_MODEL.md 中 residual、quality、event、transaction、failure 和 output 章节；
17. theory/paper/MECHANISM_DERIVATION_FORMAL.md 的释放/再接触与事件驱动章节，只按 PROPOSED_SUPPLEMENT/VALIDATION_ONLY 使用。

权威顺序：正式工程事实和 accepted system/A/B > M00/M01/M02 frozen 软件合同 > DEV_POLICY 数值起点。Formal 0.2.0-proposed 只能形成已批准的 additive protocol、capability gate 和 validation fixture，不能覆盖 accepted 物理。

实现前：

- 运行 git status --short，保留所有既有工作区改动；
- 核对当前分支、Python/runtime、依赖和 origin，但不要 pull、reset、checkout 或清理用户文件；
- 先形成简短计划和 M02 requirement-to-test traceability 草稿；
- 使用现有 Python 3.12 src layout；生产代码放在 src/spine_sim/numerics，测试放在 tests/numerics；
- runtime numerics package 不得导入 A/B/M03/M04/M05/M06 内部包；
- M01 与 M02 是同级服务。生产 M02 不计算 QueryFootprint、不拥有 tile；M01 集成测试通过 mock physical owner 调用 M01 public API；
- 不修改 theory accepted 文件、archive 或冻结需求；
- 如果发现 M00/M01 当前代码明确违反其 frozen contract，可做最小、回归覆盖、可追踪的兼容性修复；不得借此改变 M00/M01 语义。若需要 semantic change，返回明确 blocker，不要自行升级合同；
- base runtime 不得依赖 plotting package。M02 输出绘图数据，不实现 M06；
- 不引入网络服务、数据库或非必要重依赖。新增依赖必须说明必要性、license、runtime 边界和无依赖 fallback/capability 行为。

必须实现：

A. typed public contracts 和严格校验

- ContinuationTarget、ContinuationAdvanceRequest/Response、ContinuationSession/handle；
- TrialStep、TrialPhase、PhysicalEvaluationRequest/Response、opaque trial state ref、RollbackToken；
- ResidualBlock、HardInequalityQuality、ComplementarityQuality、GraphQuality、derivative capability；
- EventChannelRegistration、EventProbeRequest/Result、EventBracket、EventEarliestnessCertificate、LocatedEventGroup、SimultaneousEventGroup、EventDependencyEdge、CascadeRound；
- PreparedCandidate、ordered intent batch、prepare token ref、CommitReceipt ref；
- failure family、reason code、diagnostic level、replay decision records；
- 所有对象带 schema version、stable semantic ID/hash、unit/status/source/maturity/certification metadata；
- 严格拒绝缺单位、缺 scale、NaN/Inf、错误 parent/version/hash、重复/冲突 ID、dependency cycle 和非法状态转换；
- M00 core state/event/receipt identity 只能引用，不能复制成竞争 schema。

B. continuation 和 trial engine

- 支持 frozen 的 MONOTONE_SCALAR_TARGET；PSEUDO_ARCLENGTH、多参数自由 continuation 和动态积分明确 UNSUPPORTED；
- characteristic_length_mm 必须由请求显式提供；M02 不导入或猜测 Rt；
- 实现 h0=0.5 Lref、hmax=1.0、hmin=0.001、easy 两步后×1.5、hard/数值 retry×0.5、同 parent 12 retry；
- easy: <=8 Newton、零 backtrack、无 event/warning；hard: >20 Newton 或 >=3 backtrack；
- event step 清空 easy streak，事件定位允许小于 regular hmin，绝不能因 hmin 跳事件；
- accepted、trial、target 三类对象严格分开；没有 receipt 不创建 AcceptedStepRecord；
- predictor 只作初值并完整记录，不能直接成为 event/accepted solution；
- trial、event probe、line search、retry 和 rollback 不推进 path/time/slip/damage/work/event/peak/cycle/state。

C. residual、质量和非线性 solve

- 分块保存 raw values/unit/norm/reference norm/atol/rtol/scale/normalized norm/hard flag；
- 硬门逐块执行 raw_norm <= atol + rtol*reference_norm；总 merit 不得覆盖 hard block；
- N、N*mm、mm、角、能量、KKT/graph 单位隔离，moment 必须有显式 atol 或 force tolerance × reference length；
- 默认 force atol=1e-6 N、rtol=1e-5、normalized NCP/graph atol=1e-8；全部进入 resolved config/hash；
- 实现 smooth damped Newton 和 semismooth/generalized Newton；
- 实现 Armijo line search: c1=1e-4、contraction=0.5、max backtracks=20、min factor=2^-20；
- max Newton iterations=50；保存 linear solve residual、rank/condition warning 和算法切换；
- production owner 必须声明 generalized derivative capability；finite difference 只限 VALIDATION_ONLY/debug，不能静默用于非光滑 production；
- trust-region 只实现 typed adapter/capability hook，完整 backend 返回 UNSUPPORTED；
- 严格刚性 fixture 返回 graph/set-valued/degenerate 语义，禁止大 penalty 冒充刚度；
- Newton convergence 与 owner 物理 stability/uniqueness/feasibility 分轴。

D. unified event engine

- 注册 raw dimensional signed guard、zero、admissible side、RISING/FALLING/EITHER/TOUCH、applicability、detection/certificate capability、dependencies 和 post-side callback；
- event probe 只有在该位置完整 equilibrium/quality 通过后才合法；
- 支持 sign-change bracket、touch/stationary enclosure、swept/no-event/Lipschitz/probe-spacing certificate；只有端点同号不得宣称无事件；
- 实现 bracket-preserving Brent，异常退回 bisection，max 80 iterations，位置 tol=0.01 Lref；
- 证明所有适用通道的最早性，保留 simultaneous tolerance=0.01 Lref 内全部事件；
- ID 只作无依赖记录的确定性排序，不能当物理优先级；
- 支持接触建立/释放、摩擦边界/真实滑移、支持迁移、弹簧原长/硬限位、swept collision、再接触、材料/针体/domain/quality 和 B 活动集等 owner-defined event kinds，不在 M02 解释这些含义；
- B curve mock 必须验证每个 scan/bracket/root/event probe 都重求 nonlinear uz(x)；故意错误的 A event fraction 只能当 predictor；
- coverage 不足返回 M02_EVENT_COVERAGE_UNAVAILABLE，root/earliestness 未闭合时拒绝 trial，不跨过事件。

E. event/post、simultaneous 和 cascade

- event point pre-side、transition 后 event/post-side 均从 parent/owner contract 完整重组和求解；
- 不复用旧 wrench、pose、Jacobian、graph multiplier、damage preview、residual 或 intents；
- dependency DAG 分层，独立事件联合评价，cycle contract rejection；
- 每轮同位置重新注册/评价所有适用 guard；max 50 rounds；
- repeated state hash、event-signature oscillation、zero-progress intent 触发 M02_ZENO_CANDIDATE；不跳事件；
- release owner 只可返回 EXPLICIT_RETURN_PATH、HOLD_AT_RELEASE_POSE、UNSUPPORTED 或 UNAVAILABLE；
- 没有显式路径时不得瞬时回零、自动重挂、清 path/time/work/slip/damage/history；
- 有 EXPLICIT_RETURN_PATH 时对整条 swept path 使用相同 earliest-event 和 transaction 规则；Formal 协议保持 PROPOSED_SUPPLEMENT/VALIDATION_ONLY。

F. transaction、receipt 和 rollback

- trial → owner intents/rollback tokens → candidate freeze → M00 prepare → atomic commit → receipt；
- prepare 校验 parent/version/hash、registry/config、read/write sets、DamageStore conflicts、events、quality、idempotency 和 persistence，但无状态 publication；
- commit 原子发布全部 owner states、shared history/DamageStore、work ledger、accepted point、events、M02 extension 和 receipt；
- same idempotency key + same candidate 返回原 receipt；same key + different candidate conflict；
- rollback 幂等；已 committed receipt 不可 rollback；
- 在 evaluate、prepare、commit marker、receipt、rollback 各阶段做故障注入，证明无部分 accepted state；
- 可用 snapshot hash/side-effect sentinel 检测 owner 违规；不得靠测试后 reset 掩盖 side effect。

G. deterministic replay

- 扩展 M00 ReplayManifest，记录 target/step decisions、步长原因、predictor、iterations、line search、residual blocks、event probes/brackets/earliestness、B probe balance hashes、DAG/cascade/state hashes、intents/tokens/receipts 和 backend/profile；
- 实现 BITWISE_REPLAY 与 SEMANTIC_REPLAY verifier/report；
- serial/parallel owner order、case order、cold/warm M01 cache、tile/query/materialization order不改变单 case semantic result；
- canonical reduction/order 与线程设置显式；
- mismatch 返回结构化字段 diff，不只返回 pass/fail。

H. M00 result extension 和诊断隔离

- 注册 owner M02、namespace m02 的 ResultExtensionDescriptor；
- 实现 frozen requirement §14.2 的全部 datasets；
- accepted step、committed event、rejected trial 和 receipt 分别引用 M00 core base，不创建竞争 identity；
- COMPACT/STANDARD/FULL 三档严格按冻结语义；诊断级别不能改变 solve；
- accepted physical curves/energy/peak/design summaries 不能消费 rejected trial/event probe；
- failure_family 至少区分 NUMERICAL_FAILURE、PHYSICAL_INFEASIBLE、CONTRACT_REJECTION、DOMAIN_ERROR、TRANSACTION_FAILURE；
- PHYSICAL_INFEASIBLE 只有 owner proof 可产生；UNAVAILABLE/UNSUPPORTED 保持独立 capability axis；
- M01 reason code 原样保留并映射 domain family；
- 字段 metadata 完整声明 semantics/class/dtype/shape/unit/frame/reference/index/status/source/maturity/storage；
- ResultWriter/Reader round trip、MANIFEST_ONLY/FULL、relations、hash 和 replay 均测试。

I. M01 public compatibility adapter tests

- M02 production 不拥有 QueryFootprint；validation physical owner 使用 M01 public derive_query_footprint/query/materialization API；
- swept geometry 包含全部 tip、body/installation swept envelope；guard 使用 probe/trusted/derivative/tile/clearance max；
- 不硬编码单刺 10 mm，不硬编码阵列宽度；
- 五类 fixture：SINGLE_SPINE、ARRAY_2X2_S4、ARRAY_2X6_S6、ARRAY_6X2_S6、ARRAY_6X6_S6；
- 每条路径完整 100 mm、起终点有 guard、逻辑 parent 150×150 mm；域外保留 M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN，不 wrap/clamp/crop/缩短；
- 路径 footprint 可以完整声明，但 tile 按 probe lazy materialize；禁止创建全域 Rt/10 dense array；
- ahead Rt/5、event/support Rt/8、acceptance witness Rt/10；coverage 不足先 refine/extend；
- 同 realization 的 narrow/wide overlap、预先宽域/动态扩域、cold/warm cache、tile/query order、serial/parallel 结果一致；
- surface_scale_reference_Rt_mm 固定，不随扫描 tip Rt 自动变；probe radius 0.05/0.10 mm 不改变 surface identity；
- 缓存/物化是非 canonical 性能副作用，不能成为 accepted history。

J. 随机地形三级兼容面板

- scenario 使用独立 SurfaceRealization；按 H、Sq/reference-Rt、lc/reference-Rt、anisotropy、direction、seed 做 balanced maximin/common-random-number panel；
- M02_M01_SMOKE_4：4×5=20 条完整 100 mm paths，FULL，加入快速相关回归；
- M02_M01_STANDARD_64：64×5=320 条完整 paths，STANDARD，是模块验收硬门；
- M02_M01_STRESS_256：256×5=1280 条完整 paths，本实现窗口至少完整运行一次；全量可 COMPACT，但固定 32×5 witness 用 STANDARD，失败自动完整诊断；
- 路径必须逐步 lazy query、包含 event probe、overlap/cold-warm/order 和选定 Rt/5→Rt/8→Rt/10 witness；不能只生成地形不走路径；
- 记录每个 panel 的 scenario IDs、surface/footprint identities、独立样本数、query/step/event 数、失败分类、wall time、peak RSS、M01/M02 cache 和 artifact size；
- Rt/8→Rt/10 起点门：event position <=0.01 Rt、适用 unique support <=0.02 Rt、normal <=1°、fixture force/work summary <=1%、event order 完全一致；不通过必须继续 refine 或失败，不能放宽来过测试。

K. 参数扫描负载接口验证，但不实现 M05

- M02 service 必须能被外部 caller 以流式 case plan 调用；不要创建 production scheduler/ranker；
- 验证冻结负载描述可表达：16×4=64 单刺预筛、64×4=256 阵列初筛、16×16=256 细筛、最终 4×1000=4000 paired paths，必要时 4×4000=16000；
- 1000/4000 是共享 terrain scenario IDs，不是四个方案各自抽不同地形；
- DEV profile 64→128→256→512 作为中间 checkpoint，1000 为正式基础，4000 为不稳定时扩展；
- 用 cheap deterministic synthetic owner 验证 4000/16000 plan 可流式、暂停、恢复、replay，不要求运行尚不存在的 A/B 全物理；
- 不把 numerical failure 当设计性能，不实现 binary success 或 composite score；只保留 hard gates、Pareto-ready raw metrics、失败和成本分轴；
- 大批量 COMPACT，同一固定 5% paired scenarios STANDARD，所有 failures 完整诊断。

L. 解析、事件、事务和精化验收

- 线性/非线性解析根、crossing、rising/falling、tangency/touch；
- endpoints same sign with two interior roots；
- nonlinear B uz(x) + deliberately bad A predictor；
- 大步/减半步 event order 不变、earliest root、simultaneous set、dependency DAG/cycle、cascade/Zeno；
- release→return sweep→recontact 不漏检；owner no path 时 hold/unavailable；
- event/post 回调计数和 response hash 证明完整重算；
- repeat trial、rollback、prepare/commit/idempotency 和 fault injection；
- strict rigid graph/no penalty；
- h/h2/h4、event tolerance、Rt/5→Rt/8→Rt/10 refinement convergence；
- numerical failure、physical infeasible、contract/domain/transaction/unavailable 反例；
- serial/parallel and bitwise/semantic replay；
- 所有测试失败输出结构化 reason，不只返回 bool。

M. plot-data recipes、README、reports 和 traceability

- 提供 residual iterations、step size、event bracket、release-recontact chain、refinement error、failure statistics 六类 recipe 的字段/过滤 contract；
- 不选择用户正式 plot preset，不要求 matplotlib；可生成 CSV/JSON/Result bundle evidence；
- 在 src/spine_sim/numerics/README.md 写简短“## 输出概览”：消费者、datasets、索引、单位、status/source/maturity、ResultReader 最小读取示例；
- 生成 docs/simulator_development/implementation/M02_NUMERICS_TRACEABILITY.md；
- 生成 reports/m02/M02_VALIDATION_REPORT.md 和机器可读摘要；
- 生成 reports/m02/M02_PERFORMANCE_REPORT.md/JSON；
- 生成 reports/m02/M02_ACCEPTANCE_REPORT.md；
- 生成一个 VALIDATION_ONLY canonical result bundle，并由 ResultReader 读回；大型生成 artifact 默认不追踪，文档给出可重建命令；
- 报告必须明确 experimentally_validated=NOT_ASSESSED/BLOCKED_UNAVAILABLE、not_certifiable，mock/synthetic owner 不是 A/B 物理实现。

明确禁止：

- 实现或复制 A/B 残量、摩擦图、梁/弹簧、材料、阵列共享规律；
- M02 根据 residual 最小值替 A/B 选择物理分支；
- Newton converged 当 stable，Newton failed 当 physical infeasible；
- 大 penalty 当 rigid physics；
- 固定步长端点布尔替代 event bracket/earliestness；
- B event probe 复用 uz 或把 A fraction 当根；
- event switch 后复用旧 trial response；
- trial/event/rollback 推进 path/time/slip/damage/work/event/peak/state；
- 无 receipt 发布 accepted point/event；
- release 自动清零 pose/history 或跨步再挂接；
- M02 计算 QueryFootprint/阵列宽度、crop/rerandomize surface、为省数据缩短 100 mm path；
- 一张随机地形当多个独立样本；四个最终方案使用不同随机面板；
- 把 rejected trial 混入物理曲线/功/排名；
- 实现 M05 scheduler/ranker、M06 正式绘图 preset 或启动 M03/M04；
- 修改 accepted theory、archive、冻结需求或无关文件。

建议实现顺序：

1. contracts/status/reason/hash 和 traceability skeleton；
2. residual quality + continuation + nonlinear engine；
3. event registry/probe/bracket/earliestness/cascade；
4. transaction adapter/idempotency/replay；
5. M00 extension/reader diagnostics；
6. M01 compatibility owner 与 20-path smoke；
7. 全解析/故障/精化测试；
8. 320 standard 和 1280 stress panel；
9. 4000/16000 streaming-plan scalability fixture；
10. README、reports、canonical demo、全量回归和安全提交。

完成前必须：

1. 运行全部 M00/M01 regression 和新增 M02 tests；
2. 运行 lint、format-check、type、build、schema、link、import-boundary、replay 和 demo checks；
3. 完整运行 20/320/1280 M01 compatibility panels，并保存可审计报告；
4. 运行 4000/16000 streaming scalability fixture；
5. 核对 requirement-to-test traceability 第 18 节无漏项；
6. 核对 M00 state/receipt/output、M01 footprint/LOD/cache、A/B event/B-uz/proposed-release 和 DEV profile 一致；
7. 重新读取 git status --short，保留所有无关工作区改动；
8. 只精确暂存 M02 implementation、tests、README、scripts、traceability/reports 和本窗口明确批准的最小 M00/M01 compatibility fix；
9. 禁止 git add -A、git add .；
10. 执行 git diff --cached --name-only、git diff --cached --check，并逐文件检查 cached diff；
11. 不提交、不格式化、不回退任何无关改动；
12. 提交推送前核对当前分支和 origin 是用户已授权的 Persenz1/Spine_Sim_V3；
13. 提交并推送；
14. 报告 commit、实际文件、tests、20/320/1280 panel、4000/16000 plan fixture、性能/内存、canonical bundle、reports、capability unavailable 和残余风险；
15. 停止，不开始 M03、M04、M05 或 M06。
~~~

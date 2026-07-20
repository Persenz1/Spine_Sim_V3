# M03 SINGLE_SPINE 实现窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。该窗口只实现、测试和验收已冻结的 M03，不重新讨论需求，不启动 M04 阵列、M05 实验编排或 M06 正式绘图系统。

## 提示词正文

~~~text
TASK_ID: M03_SINGLE_SPINE_IMPLEMENTATION
PROMPT_VERSION: 1.0.0
REQUIREMENTS_VERSION: M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 frozen

本窗口只实现、测试、验证并交付 M03 SINGLE_SPINE：A-M0 本征单刺核、standalone 单刺驱动器、accepted A→B embedded adapter、M00/M02 输出扩展、验证证据和最小 plot-data/validation figure pack。不得重新讨论或修改冻结需求；不得开始 B 阵列、阵列载荷共享、M05 scheduler/ranker 或 M06 正式交互绘图。

用户只保留仿真项目和正式出图项目规划的决策权。冻结需求已经确定技术参数、扫描规模、状态、raw输出、图数据和验收；ordinary implementation choices、内部软件结构、测试fixture、性能修复和报告组织自行完成，不再向用户询问。不得索要实验数据，不得把DEV宽先验称为标定值。

第一版物理主线固定为：`no_damage + rigid Signorini/Coulomb + Euler–Bernoulli + A-authoritative mount`。只能做解析/合成表面上的趋势和参数选型；不得声称预测真实砖面破坏、针体安全或阵列承载能力。

开始前必须完整读取：

1. README.md、theory/README.md；
2. docs/simulator_development/README.md；
3. docs/simulator_development/SIMULATOR_MODULE_PLAN.md；
4. docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md；
5. docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md；
6. docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md；
7. docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md；
8. docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md；
9. docs/simulator_development/implementation/M00_FOUNDATION_TRACEABILITY.md、M01_SURFACE_TRACEABILITY.md、M02_NUMERICS_TRACEABILITY.md；
10. src/spine_sim/foundation、surface、numerics 的public contracts、status/reason、registry、transaction、query、result extension、writer/reader和replay实现；
11. 对应tests、scripts、reports和canonical demo入口；
12. theory/evidence_reassessment/README.md与engineering_fixed_context.md；
13. theory/modules/A_INTEGRATED_MODEL.md；
14. theory/interfaces/A_TO_B_CONTRACT.md；
15. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
16. theory/paper/MECHANISM_DERIVATION_FORMAL.md；
17. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
18. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml。

权威顺序固定为：正式工程事实 > accepted A/A→B 1.0.0 > M00/M01/M02/M03 frozen 软件合同 > DEV_POLICY。Formal 0.2.0-proposed 只允许按冻结需求列出的 `PROPOSED_SUPPLEMENT` 使用；不得静默升级accepted状态或接口。

复核硬约束：

- 姿态采用冻结的global-left-multiply P0闭合，并标`PROPOSED_SUPPLEMENT`；禁止对global a0二次旋转；
- `ATTACHED_STICK`只要求当前客观滑移增量/速率为零，不要求历史累计滑移为零；
- A权威spring zero branch不能照抄B旧摘要；
- 释放后不能瞬时清零梁/弹簧并跨到新接触；必须显式swept return path，或停在release pose；
- event point切换branch后完整重组和重求，不能复用旧response；
- nearest support必须全候选/local-minimum/empty-ball/邻域比较，不能只取API第一项；
- damage和needle strength certification关闭且显式unavailable。

实现前：

- 运行`git status --short`，记录并保留所有既有工作区改动；
- 核对当前分支、Python/runtime、依赖和origin，但不要pull、reset、checkout或清理用户文件；
- 先形成简短计划和M03 requirement-to-test traceability草稿；
- 使用现有Python 3.12 src layout；生产代码放在`src/spine_sim/single_spine`，测试放在`tests/single_spine`；若仓库现有命名规范要求等价路径，记录理由且不改变模块边界；
- runtime single-spine package只依赖M00/M01/M02公共API，不导入M04/M05/M06内部包；
- 不修改theory accepted文件、archive或任何frozen requirements；
- 如果M00/M01/M02当前实现明确违反其frozen contract，只允许最小、回归覆盖、可追踪的兼容修复；需要semantic change时返回blocker，不自行升级合同；
- solver/base runtime不得依赖plotting package；validation figure生成器放在dev/report边界，通过ResultReader只读canonical result；
- 不引入网络服务、数据库或非必要重依赖。新增依赖必须说明必要性、license、runtime边界和无依赖fallback/capability行为。

必须实现：

A. typed contracts、配置和parameter provenance

- `IntrinsicSingleSpineKernel`、`EmbeddedSingleSpineTrialRequest`/accepted `SingleSpineTrialResponse` adapter；
- `StandaloneSingleSpineRunRequest/Response`、resolved initial pose/search/preload/drag/release policy；
- immutable needle/contact/beam/mount/no-damage/numerical parameter bundles；
- frozen baseline：Rt=.05 mm、d=.8 mm、L=4 mm、alpha=60 deg、beta=0、E=210000 MPa、nu=.30、mu=.40、Pz=.5 N standalone、speed=1 mm/s、travel=100 mm、bending on、independent spring ks=.5 N/mm、travel 0–4 mm；
- frozen grids和36 distinct trend-case plan按requirements §4精确生成，保留12条交互记录与6条共享case的引用关系，去重且不扩为全笛卡尔；
- fixed/wide-prior/design/numerical/validation参数角色和authority/provenance分别保存；
- runtime defaults全部展开到resolved config/hash，无隐藏默认；
- 严格拒绝缺单位、NaN/Inf、非法frame/reference、非法alpha/beta、重复柔顺、rigid+有效ks、bending-off E/nu无意义case和embedded per-spine Pz；
- 所有对象带schema version、stable semantic ID/hash、unit/status/source/certification metadata，并分别保存`theory_defined`、`code_implemented`、`numerically_verified`、`experimentally_validated`四栏成熟度；不得合并成completed bool。

B. 坐标、复合针几何和M01 adapter

- 实现工程a0(alpha,beta)和global/local transforms；beta接口保留但首版非零beta返回明确unsupported，除非frozen accepted接口已允许只读表达；
- 用global-left-multiply closed pose计算tip center/current axis；provenance=`PROPOSED_SUPPLEMENT`；
- 复合针包含finite spherical cap、cone、shaft/EB centerline envelope和mount envelope；
- 由完整当前和swept geometry派生M01 QueryFootprint，禁止硬编码10 mm或创建全域dense grid；
- 使用M01 public query/materialization API保留nearest、co-minimal、previous-active、nearby switch candidates及query receipt；
- 校验local minimum/empty-ball/full candidate comparison、finite cap legality、feature/chart和nonsmooth/nonunique status；
- 每个trial/event probe/return sweep检查cone/shaft/mount碰撞；body collision终止pure-tip model，不能当tip load；
- ahead Rt/5、event/support Rt/8、acceptance witness Rt/10；coverage不足refine/extend，仍不足返回原M01 reason/GEOMETRY_UNCERTAIN；
- surface_scale_reference_Rt固定.05 mm；扫描tip Rt不改变surface identity；禁止crop/wrap/rerandomize。

C. rigid Signorini/Coulomb接触图

- 实现多支持gap、normal/tangent basis、normal/tangential multipliers、Signorini complementarity和3D Coulomb/SOC；
- 接触normal compliance固定0；数值regularization/penalty若内部需要，只能是numerical并必须做收敛，不能成为物理参数或能量；
- objective slip相对midpoint/current tangent plane计算；support migration、rolling、friction boundary和committed sliding分开；
- friction cone reached后先求one-sided all-stick redistribution；只有该分支不可行且max-dissipation sliding闭合才提交slip onset；
- open/zero-load/positive-load、多支持/非唯一/集合值分支均返回严格graph质量；
- M03定义physical residual/branch/guard/post-side callbacks，数值迭代、bracket和transaction交给M02，不复制numerics engine。

D. Euler–Bernoulli梁和A权威mount

- 实现accepted 3D EB tip translation/rotation、root force/moment、section resultants、beam energy和model validity；
- bending-on为主，off只使beam deformation/energy为零；root resultants和strength unavailable仍返回；
- Timoshenko和corotational仅作为VALIDATION_ONLY reference/fixture，不加入production model registry；
- 实现`RIGID_LOCKED`、`AT_ORIGINAL_LENGTH`、`COMPRESSING`、`HARD_STOP`四分支：原长不拉、interior ks*delta、4 mm hard stop含非负constraint reaction；
- rigid mount使用constraint/set-valued语义，不用大penalty伪造；
- 输出spring compression/remaining travel/force/reaction/energy；
- 审计梁、spring、contact compliance只计一次；contact-only wrench不重复加root/spring reaction；
- model validity超界返回STRUCTURAL_MODEL_OUT_OF_RANGE，不伪装设计性能。

E. intrinsic kernel和accepted A→B adapter

- 唯一public B call mode为`embedded_constitutive_trial`，逻辑签名和accepted fields原样兼容A_TO_B 1.0.0；request精确保留`contract_id`、`contract_version`、`call_mode`、`needle_identity`、`surface_query_handle`、`base_pose_n`、`prescribed_base_increment`、`immutable_single_spine_state_n`、`shared_damage_store_snapshot`、`parameter_bundle`、`trial_identity`、`requested_tangent_mode`、`event_location_config`、`quality_request`和`continuation_hint`；
- request预检contract/version/identity/frame/unit/kinematic subspace/history/surface/parameter/coverage和duplicate load；
- embedded open只返回zero contact wrench+OPEN_RESPONSE；不得搜索Pz平衡；
- trial side-effect free：不推进path/time/slip/work/cycle/event/history，不修改surface或damage snapshot；
- response完整返回accepted wrench、geometry/contact、structure、material/damage capability、state/event、linearization、diagnostics和transaction fields；
- `wrench_A_on_B`为contact-only global 6D wrench at declared O，`direction=A_on_B`，`opposite_wrench_B_on_A`严格取负，accepted `grip_resistance_Rx=-ex·F`；保存reference transport/work invariance；
- rigid/degenerate分支返回wrench uniqueness、rank/nullspace和opaque graph handle，不能把representative当unique；
- tangent按branch返回smooth/generalized one-sided/branch-dependent/secant/set-valued/unavailable，禁止强制对称；
- no-damage保留accepted material字段但不产生damage intents/write set；
- 所有A intents/rollback handles通过M02/M00事务协调，只有armed commit才更新accepted history。

F. standalone driver

- undeformed beam、spring original length、open状态开始；沿+Z回退直到full-body certified clearance满足requirements §6.1公式，保存resolved pose和controlling feature；
- 固定ux=0，用NESTED_Z_SEARCH沿-global-Z定位最早legal finite-cap zero-load contact；每probe完整重求/检查body/query quality；
- 从TIP_ZERO_LOAD以eta 0→1做Pz=.5 N preload homotopy，每点重求uz；不能直接跳载；
- preload成功后沿+local-x累计100 mm；speed=1 mm/s，drag clock=x_total/speed；
- trial/retry/probe/rollback不推进；release/recontact/new cycle不重置x/time/work/slip/event history；
- 精确实现frozen `PROPOSED_SUPPLEMENT` `LIFT_OFF_RESEARCH_V1`：UNLOAD_AT_FIXED_X将仍有效的normal target同伦降到0（release事件优先）→UNLOCK_AT_RELEASE关闭force controller且pose连续→LIFT_OFF_AT_FIXED_X沿+global-Z到full-body gap达到g_start且remaining recoverable energy低于resolved work/energy resolution→RESEARCH_AT_FIXED_X沿同一Z走廊找最早finite-cap zero-load contact→RELOAD_AT_FIXED_X完成0→.5 N同伦→恢复剩余drag；
- 每个operation segment声明interpolation、path coordinate、swept envelope、guards、quality gate和termination，并经M02 earliest-event/transaction；operation speed未声明时physical operation time必须unavailable；
- low-level release/collision/recontact由A拥有，standalone只编排outer operations；
- 某branch没有return path或lift/research触发fatal/quality/Zeno gate时停在最后committed release/operation pose，保留deformation/energy/history，返回HOLD_AT_RELEASE_POSE、remaining travel和明确reason；禁止instant reset和假完成；
- recontact zero-load进入新cycle，但只有重新preload为positive loaded contact才提交REATTACHED_ENTRY/reengagement。

G. states、five-stage funnel和events

- 原样实现accepted主状态：OPEN、TIP_ZERO_LOAD、PRELOAD_BUILD、ATTACHED_STICK、ATTACHED_SLIDE、REATTACHED_ENTRY、RELEASE_TRANSITION、REVERSIBLE_RETURN、TRAVEL_COMPLETE；
- `HOLD_AT_RELEASE_POSE`只作为standalone operation terminal status；
- 实现per-support contact motion、spring、beam/model、no-damage、strength unavailable和quality/solve正交状态；
- operation phases按frozen PROPOSED_SUPPLEMENT实现；
- 独立输出geometric_candidate、loaded_contact、frictionally_stable、load_bearing、release/reengagement lifecycle，均带reason/evidence/criteria version；
- 禁止任何模糊`engaged`或binary `success`字段；candidate_any/robust只作方向裕度diagnostic；
- task load-bearing要求loaded+frictionally admissible+accepted feasible branch+positive scale-aware R_task，canonical task为+local-x；
- 注册contact/load/release、friction/slip、support/chart/cap、spring、collision、domain/quality、preload、return segment、swept collision、recontact/reengagement、travel complete signed events；
- raw dimensional guards、direction/admissible side、touch/crossing、coverage certificate、simultaneous/cascade和post-side callbacks完整；
- event point后完整重求；数值失败保持failure axis，不能变成physical release/infeasible。

H. work、energy、residual和capability

- 每accepted increment保存base/standalone actuator input work、delta Ubeam、delta Uspring、friction dissipation、returned/released recoverable energy和closure error；
- rigid contact physical energy=0，material dissipation=0仅因NO_DAMAGE_MODEL；
- release先记录remaining stored energy；只有explicit path实际变化才能记returned energy；hold时不能消失；
- residual blocks保留raw/unit/reference/atol/rtol/scale/normalized norm/hard quality，接入M02 gate；
- complementarity/SOC/graph/geometric/beam/spring/work/Jacobian分别报告；
- material damage/failure/fracture-energy字段typed NOT_APPLICABLE/empty，failure_prediction_allowed=false；
- yield/fracture margins和strength certification为null+NEEDLE_STRENGTH_UNAVAILABLE；root resultants仍返回；
- 全部结果带DEV_PRIOR/synthetic_or_analytic/no_damage/not_certifiable，experimentally_validated=NOT_ASSESSED。

I. M00 result extension和raw隔离

- 注册owner M03、namespace m03的ResultExtensionDescriptor；
- 精确实现requirements §11冻结datasets：run_requests、accepted_state_history、support_candidate_history、contact_support_history、committed_event_payloads、release_operation_history、rejected_diagnostics、work_ledger、contact_cycle_records、capability_status、derived_summaries、plot_recipe_manifest；
- 引用M00 core accepted/event/receipt和M02 event/trial identity，不复制竞争identity/schema；
- accepted points、committed events、rejected trial/probe严格隔离；default reader/plot不消费rejected；
- COMPACT/STANDARD/FULL按frozen语义；任何过滤、降采样、peak或summary是derived并保留raw links/definition hash；
- 每accepted point/event/rejected row具备requirements §11字段；每个field metadata显式声明semantics/class、dtype、shape、unit、frame、reference、index、raw/derived/diagnostic归属、null/unavailable政策、cadence、schema、source和四栏成熟度；
- ResultWriter/Reader roundtrip、relations/hash、MANIFEST_ONLY/FULL、replay和schema evolution测试；
- trial/rollback不产生AcceptedStepRecord、committed event、cycle/peak/work/path进展。

J. summaries、plot recipes和validation evidence

- 提供versioned summaries：first loaded/load-bearing distance、right censoring、false-engagement episodes、release-recontact/reengagement spacing、cycles/path fractions、multi-peak raw links、positive work/dissipation/returned energy；
- peak不是binary success，不生成composite score、阵列排名或统计置信区间；
- 提供frozen八类machine-readable recipes：response overview、state bands、five-stage bands、local geometry、structure/spring、event zoom/multi-peak、quality/work、parameter trends；
- default accepted raw+committed events、无平滑；rejected显式opt-in；x/time不因release reset；
- local geometry evidence保存surface sample/reference、support/normal/tangent/axis/cap/cone/shaft/mount/task direction所需字段，使M06无需调用solver；
- filter contract覆盖surface/case/parameters/state/cycle/event/frame/source/capability；
- 生成最小静态validation figure pack，至少包含Rx-x、Rx-t、uz-x/full forces、state bands、five-stage+release chain、local geometry、beam/spring、event zoom、多峰、residual/complementarity/work、Rt/d/alpha/mu/ks paired trends；
- validation renderer通过ResultReader只读结果，不被solver import；不选择M06正式颜色/字体/出版preset。

K. surface/case campaigns

- analytic suite：plane、slope、convex/concave spherical cap、constructed multi-peak/nearest-switch；全部VALIDATION_ONLY；
- primary medium synthetic按frozen H=.7、rms/refRt=1、lc/refRt=20、anisotropy=1、direction=0、seed=30301运行36 distinct trend cases；
- gentle seed30302和sharp seed30303各运行baseline 100 mm smoke；
- paired cases必须共享realization/domain/path/query policy；seed是固定见证，不是统计样本；
- 每case完成100 mm，或返回明确physical/capability/domain termination；numerical failure不能成为趋势值；
- case-by-case streaming、pause/resume/replay；不得同时保留全部FULL history或创建150×150 mm Rt/10 dense grid；
- 报告每case accepted/trial/event/query counts、wall time、peak RSS、cache和artifact size。

L. tests和负例

- 按requirements §16逐条建立requirement-to-test mapping，不能只写happy path；
- geometry analytic、finite cap、full candidate、local-minimum、body collision、quality/LOD/refinement；
- Signorini open/zero/loaded、candidate-zero-force、mu=0、stick boundary/true slide、loaded-not-stable、stable-not-bearing、rolling/migration；
- EB analytic/symmetry/energy、Timoshenko/corotational reference、bending off、spring zero/interior/stop/unload、rigid graph和compliance dedup；
- initial clearance/search/preload/100 mm/time mapping；release→swept return→recontact/reload；no-path hold；history not reset；
- same-sign endpoints with interior events、touch、large/half step event order、simultaneous/DAG/cascade、event/post recompute；
- standalone/embedded equivalence、open zero wrench、duplicate Pz rejection、action-reaction/reference/work；
- trial/rollback/prepare/commit/idempotency/fault injection和accepted/event/rejected isolation；
- step/event/LOD refinement，Rt/8→Rt/10 thresholds按requirements §16.1；
- work/energy/residual closure、ResultReader roundtrip、summary rebuild、rejected exclusion；
- explicit damage/strength unavailable和not-certifiable labels；
- serial/parallel、cold/warm cache、query order semantic determinism和replay。

M. documentation、reports和traceability

- 在`src/spine_sim/single_spine/README.md`写简明输出概览、调用模式、owner边界、datasets、units/frame/reference、status/source/maturity、ResultReader最小示例；
- 生成`docs/simulator_development/implementation/M03_SINGLE_SPINE_TRACEABILITY.md`；
- 生成`reports/m03/M03_VALIDATION_REPORT.md`及机器可读摘要；
- 生成`reports/m03/M03_PERFORMANCE_REPORT.md/JSON`；
- 生成`reports/m03/M03_ACCEPTANCE_REPORT.md`；
- 生成一个VALIDATION_ONLY canonical result bundle并由ResultReader读回；大型generated artifacts默认不追踪，但报告提供可重建命令和hash；
- 报告逐项说明参数来源、36-case去重和12条交互记录的共享引用、surface identities、完成/hold/failure、图recipe、性能/内存、damage/strength unavailable和remaining risks；
- 明确本模块尚未运行阵列，M04阵列广泛候选和最终4种方案未开始。

明确禁止：

- 实现B阵列、共同平衡、load sharing、阵列候选或四方案定型；
- 实现M05 scheduler/statistical ranker/Pareto或M06正式交互plot preset；
- material damage、fracture energy、real brick failure、needle yield/fracture certification；
- embedded per-spine Pz或让B调用standalone driver；
- 把candidate/contact/friction-stable/peak当load-bearing或success；
- 创建`engaged`合并bool、binary success或composite score；
- release后instant reset pose/deformation/energy/history，或无return path仍自动再挂接；
- reset 100 mm path/time/work/slip/event/cycle；
- contact-only wrench重复叠加beam/spring/root reactions；
- 梁、spring、contact/penalty compliance重复计入；
- 把penalty值当物理刚度；
- nearest API第一项直接作为唯一支持；
- filtered/summary/rejected替代accepted raw；
- Newton converged当stable、Newton failed当physical infeasible；
- crop/wrap/rerandomize M01 surface，或随tip Rt改变surface realization；
- 让B/C反向修改A parameters/history/constitutive branch；
- 修改accepted theory、frozen requirements、archive或无关文件。

建议实现顺序：

1. contracts/status/reason/config/provenance和traceability skeleton；
2. coordinate/composite geometry/M01 adapter和analytic fixtures；
3. rigid contact/Coulomb graph；
4. EB beam/A spring/residual/work；
5. intrinsic kernel、states/events、A→B adapter；
6. M02 transaction/continuation/event/replay integration；
7. standalone search/preload/drag/release protocol；
8. M00 result extension/reader/summaries/plot recipes；
9. analytic/negative/refinement/fault tests和canonical demo；
10. 36-case medium campaign、gentle/sharp smoke、validation figures、reports和全量回归。

完成前必须：

1. 运行全部M00/M01/M02 regression和新增M03 tests；
2. 运行lint、format-check、type、build、schema、link、import-boundary、replay和demo checks；
3. 完整运行analytic suite、medium 36 distinct cases和gentle/sharp smoke；
4. 对所有非完成case区分physical/domain/capability/numerical/transaction，不得删掉或补造趋势值；
5. 核对requirement-to-test traceability对M03 requirements §16无漏项；
6. 核对M00 identity/result/transaction、M01 query/LOD/surface identity、M02 event/transaction/replay和accepted A→B request/response/wrench/Pz边界闭合；
7. 核对所有PROPOSED_SUPPLEMENT字段有明确source/maturity且未修改accepted接口；
8. 重新读取`git status --short`，保留所有无关工作区改动；
9. 只精确暂存M03 implementation、tests、README、scripts、traceability/reports和本窗口明确批准的最小M00/M01/M02兼容修复；
10. 禁止`git add -A`和`git add .`；
11. 执行`git diff --cached --name-only`、`git diff --cached --check`并逐文件检查cached diff；
12. 不提交、不格式化、不回退任何无关改动；
13. 提交推送前核对当前分支和origin是用户已授权的`Persenz1/Spine_Sim_V3`；
14. 提交并推送；
15. 报告commit、实际文件、tests、analytic/36/gentle/sharp outcomes、性能/内存、canonical bundle、figures/reports、unavailable capabilities和剩余风险；
16. 停止，不开始M04、M05或M06。
~~~

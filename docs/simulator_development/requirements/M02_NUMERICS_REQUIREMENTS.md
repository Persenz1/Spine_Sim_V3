# M02 NUMERICS 冻结需求

**任务 ID：** `M02_NUMERICS_REQUIREMENTS`

**需求版本：** `1.0.0`

**提示词来源版本：** `0.1.3`

**冻结日期：** `2026-07-18`

**状态：** `FROZEN`

**模块所有者：** `M02_NUMERICS`

**适用范围：** 无实验数据阶段的 A/B 非光滑准静态路径；数值、事件、事务与重放服务

**前置门：** `M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen`、`M01_SURFACE_REQUIREMENTS 1.0.0 frozen`

**后续窗口：** [M02 实现窗口提示词](../implementation_prompts/M02_NUMERICS_IMPLEMENTATION_WINDOW_PROMPT.md)

本文冻结 M02 的软件服务边界、公共请求/响应、数值起点、事件协议、事务/重放、诊断输出及验收。本文不冻结或改写任何摩擦、梁、弹簧、接触、阵列载荷共享或释放回位本构；所有数值值都是 `DEV_POLICY` 起点，必须通过解析、步长、表面分辨率、事件顺序、能量/残量和随机样本收敛后才能升级。

---

## 1. 权威输入、目标和来源身份

### 1.1 实际读取的权威输入

冻结前已完整读取并交叉核对：

1. `README.md`、`theory/README.md`；
2. `docs/simulator_development/README.md`；
3. `docs/simulator_development/SIMULATOR_MODULE_PLAN.md`；
4. `docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md`；
5. `docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md`，`1.0.0 frozen`；
6. `docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md`，`1.0.0 frozen`；
7. `docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md` 及当前 M01 公共 footprint/materialization API 和对应测试；
8. `theory/review/DERIVATION_VERIFICATION_2026-07-17.md`；
9. `theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md`；
10. `theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml`，schema `0.1.0`；
11. `theory/system/SYSTEM_INTEGRATED_MODEL.md`，`1.0.0 accepted`；
12. `theory/modules/A_INTEGRATED_MODEL.md` 中残量、质量、事件、事务、失败和输出合同；
13. `theory/modules/B_INTEGRATED_MODEL.md` 中共同平衡残量、曲线事件探测、活动集、共享事务、失败和输出合同；
14. `theory/paper/MECHANISM_DERIVATION_FORMAL.md` 中释放/再接触和事件驱动章节。

第 14 项只能以 `PROPOSED_SUPPLEMENT / VALIDATION_ONLY` 身份形成附加协议、验证 fixture 或 capability gate，不得覆盖 accepted system/A/B。M01 的实现快照只用于兼容性校验，不把当前实现细节提升为新的物理权威。

### 1.2 第一版目标

第一版必须在没有实验数据时可靠推进 A/B 的非光滑、事件驱动、准静态路径，并满足：

- 物理所有者提供残量、严格不等式/graph 质量、signed guard、分支和提交意图；
- M02 负责求解编排、变步长延拓、最早事件定位、同位置级联、trial/prepare/commit/rollback 协调和确定性重放；
- 任何 trial、事件探测、重试或 rollback 都不推进路径、物理时间、累计滑移、损伤、功、循环、峰值、事件号或 accepted state；
- accepted step 只有在 M00 原子 commit 返回 receipt 后存在；
- 数值收敛、物理可行、物理稳定、capability availability 和 certification 分轴记录；
- 能支撑单刺、阵列以及大规模随机表面上的后续筛选，而不把筛选或排名规律塞进 M02。

### 1.3 来源身份映射

| 内容 | 来源身份 | 约束 |
|---|---|---|
| M00 state/ID/hash/result/transaction/replay 语义 | `ACCEPTED_AUTHORITY` | M02 只能扩展，不能创建竞争身份或削弱原子性 |
| M01 SurfaceRealization、足迹、LOD、tile/cache 语义 | `ACCEPTED_AUTHORITY` | M02 不拥有地形；只消费物理所有者返回的公开 identity/quality/coverage 引用 |
| A/B 残量、guard、活动分支和 transition intent 的物理意义 | `ACCEPTED_AUTHORITY` | M02 执行，不解释、不替换 |
| 步长、残量、Newton、事件和随机样本起点 | `DEV_POLICY` | 不可认证；只由数值收敛调整，不由实验拟合 |
| 本文公共软件合同、失败语义和诊断分层 | `ACCEPTED_AUTHORITY` | 本次需求冻结形成的软件权威 |
| 释放—回位—扫掠—再接触附加路径协议 | `PROPOSED_SUPPLEMENT` | owner 显式声明后才可用；缺失时 hold/unavailable，禁止 M02 猜测 |
| 解析根、构造地形、故障注入和 mock owner | `VALIDATION_ONLY` | 不能宣称真实物理或材料有效性 |

---

## 2. 范围、非目标和依赖方向

### 2.1 M02 负责

- 单调标量 continuation target 的分段推进与 accepted/trial step 管理；
- 平滑 Newton 与非光滑 semismooth/generalized Newton 编排；
- 分块残量缩放、线搜索、重试、步长增长/缩短和数值质量门；
- typed signed event channel 注册、探测、括区、求根、最早性证明、同时事件和依赖偏序；
- event point、分支切换后 event/post 一侧的完整重求；
- 同位置事件级联、循环检测和 Zeno 防护；
- side-effect-free trial、prepare、commit、rollback、receipt 和幂等协调；
- 数值决策级 deterministic replay；
- accepted/event、rejected trial、transaction 和 replay 诊断的严格隔离；
- 供 M06 绘图和 M05 批量调度消费的 canonical raw 数值输出；
- 与 M00、M01 公共合同以及 A/B callback 语义的集成验收。

### 2.2 M02 不负责

- 不拥有或定义摩擦图、Signorini/Coulomb、接触柔顺、梁、弹簧、硬限位、材料、损伤、针体强度或阵列载荷共享规律；
- 不决定 A/B 活动分支的物理意义、优先级、稳定性或成功标准；
- 不生成 SurfaceRealization，不派生针/阵列扫掠几何，不选择 M01 的物理查询能力；
- 不把大罚刚度解释为严格刚性物理，不用隐藏正则化制造有限刚度；
- 不用固定步长端点布尔变化代替连续区间内最早事件定位；
- 不把 Newton 收敛等同于物理稳定，不把 Newton 失败等同于物理无解；
- 不自动清零释放 pose、路径、时间、功、DamageStore、累计滑移或历史；
- 不把未实现回位路径替换成瞬时回零、跨步再挂接或凭空生成弹道；
- 不调度参数扫描、不筛选方案、不定义综合分数；这些属于 M05/验证决策层；
- 不选择正式图形风格预设；M02 只冻结绘图所需 raw 数据和 recipe 语义，正式 preset 属于用户与 M06；
- 不实现动态冲击、惯性、速度相关接触、pseudo-arclength、全 SE(3) C 层或认证判断。

### 2.3 依赖方向

```text
M00 Foundation contracts / ResultWriter / atomic persistence
        ↑                         ↑
        │                         │
M02 Numerics service ← callbacks from M03/A and M04/B
        │                         │
        │                  public M01 queries are used by the physical owner
        ↓
M05 case scheduling / M06 plot recipes / later C consumers
```

运行时 M02 不得反向导入 A/B/M03/M04/M05/M06 内部 package。M01 与 M02 保持同级服务：A/B 物理 owner 持有 M01 query handle、派生扫掠 footprint 并在 M02 请求的 trial/event probe 中返回 geometry quality/coverage 引用。M02 不直接计算单刺或阵列宽度。

---

## 3. 术语、坐标、单位和对象关系

### 3.1 规范术语

| 术语 | 冻结定义 |
|---|---|
| `ContinuationTarget` | 从一个 receipt-backed accepted parent 出发的不可变目标；声明控制坐标、方向、目标、特征长度和 owner 集合 |
| `AcceptedStepRecord` | 只有原子 commit 成功后才存在的 accepted point 数值扩展；必须引用 M00 `AcceptedPointBase` 和 receipt |
| `TrialStep` | 从 accepted parent 派生的无副作用尝试；可以被重复、细分、事件定位或丢弃 |
| `TrialEvaluation` | 物理 owner 对指定 trial 请求返回的残量、质量、guard、opaque candidate state 和 intents；不是 accepted state |
| `EventProbe` | 在已声明路径坐标处完整求平衡并评价 guard 的 trial；不是端点插值 |
| `LocatedEventGroup` | 已满足括区、根、最早性和同时性判据的一组事件候选；提交前仍是 trial |
| `PreparedCandidate` | 数值、事件、物理 owner 和事务一致性均通过、已可交给 M00 prepare 的不可变候选 |
| `CommitReceipt` | M00 对原子 publication 的唯一成功证明；没有 receipt 就没有 accepted step/event |
| `RollbackToken` | owner 对 trial 私有资源/意图的 opaque 撤销能力；rollback 必须幂等且不影响 accepted state |
| `NumericalTrialCache` | 可丢弃、非 canonical、不得承载物理历史的求解辅助缓存 |

### 3.2 规范单位和路径方向

- 沿用 M00 registry：长度 `mm`、力 `N`、力矩 `N*mm`、功 `N*mm`、时间 `s`；
- continuation 坐标必须携带 unit、frame/reference（如适用）和实际遍历方向；
- 第一版要求一个单调标量 continuation 坐标；A standalone 和 B `UX_PZ_BALANCED` 的典型坐标为拖曳位移，B 的 `u_z` 是每次 probe 重求的平衡未知量，不是第二个 continuation target；
- 每个 target 必须显式传入 `characteristic_length_mm` 及其 parameter/source identity。DEV profile 下通常由物理 owner 传入相应 `Rt`，但 M02 不读取、猜测或把 `Rt` 硬编码进数值服务；
- 事件位置使用沿实际遍历方向单调增加的 `oriented_path_position_mm` 或等价 owner 映射。目标反向时仍以 trial fraction `lambda: 0→1` 判定“最早”。

### 3.3 accepted、trial 和 target 的调用关系

```text
receipt-backed parent accepted state
    └─ create ContinuationTarget
         └─ propose TrialStep(TARGET_PROBE)
              ├─ owner TrialEvaluation(s)
              ├─ nonlinear solve / quality gate
              ├─ event coverage and earliest-event search
              │    └─ EVENT_PROBE → EVENT_POINT → POST_EVENT_SIDE/CASCADE_ROUND
              ├─ reject + retry from the same parent
              └─ PreparedCandidate
                    └─ M00 prepare → atomic commit → CommitReceipt
                           └─ AcceptedStepRecord/new accepted parent
```

一个 `ContinuationTarget` 可产生任意多个 `TrialStep`，但一个 accepted step 恰好引用一个 parent receipt、一个最终 candidate hash 和一个 commit receipt。事件定位子 trial 不消耗 accepted step index。

---

## 4. DEV 数值参数表和所有权

下列值是首版实现起点，不是材料参数、实验拟合量或认证阈值。所有值进入 resolved config、run fingerprint、diagnostics 和 replay manifest。

| 参数 ID | 起点 | 所有者/来源 | 冻结语义 |
|---|---:|---|---|
| `M02.CONTINUATION.INITIAL_STEP_OVER_LREF` | `0.5` | `DEV_POLICY` | 新 target 的常规初始步 |
| `M02.CONTINUATION.MAXIMUM_STEP_OVER_LREF` | `1.0` | `DEV_POLICY` | 常规 accepted step 上限 |
| `M02.CONTINUATION.MINIMUM_STEP_OVER_LREF` | `0.001` | `DEV_POLICY` | 常规 trial 下限；精确事件子步可更小 |
| `M02.CONTINUATION.GROWTH_FACTOR` | `1.5` | 本次冻结 `DEV_POLICY` | 连续两个 easy accepted steps 后增长 |
| `M02.CONTINUATION.SHRINK_FACTOR` | `0.5` | 本次冻结 `DEV_POLICY` | hard step 的下一步或 numerical retry |
| `M02.CONTINUATION.MAX_RETRIES_PER_PARENT` | `12` | 本次冻结 `DEV_POLICY` | 同一 accepted parent 的数值重试上限 |
| `M02.CONTINUATION.EASY_NEWTON_MAX` | `8` | 本次冻结 `DEV_POLICY` | 且无 backtrack/event 才算 easy |
| `M02.CONTINUATION.HARD_NEWTON_MIN` | `21` | 本次冻结 `DEV_POLICY` | `>20` 次迭代为 hard |
| `M02.CONTINUATION.HARD_BACKTRACK_MIN` | `3` | 本次冻结 `DEV_POLICY` | `>=3` 次 backtrack 为 hard |
| `M02.RESIDUAL.FORCE_ATOL_N` | `1.0e-6` | DEV profile | 力块默认绝对容差 |
| `M02.RESIDUAL.DEFAULT_RTOL` | `1.0e-5` | DEV profile | 力块及 owner 未覆盖块的相对起点 |
| `M02.QUALITY.NORMALIZED_NCP_ATOL` | `1.0e-8` | 本次冻结 `DEV_POLICY` | 经 owner 显式尺度化后的无量纲互补质量起点 |
| `M02.QUALITY.NORMALIZED_GRAPH_ATOL` | `1.0e-8` | 本次冻结 `DEV_POLICY` | 经 owner 显式尺度化后的无量纲 graph 距离起点 |
| `M02.SOLVER.MAX_NEWTON_ITERATIONS` | `50` | DEV profile | 每次完整非线性求解上限 |
| `M02.LINE_SEARCH.ARMIJO_C1` | `1.0e-4` | 本次冻结 `DEV_POLICY` | merit 充分下降起点 |
| `M02.LINE_SEARCH.CONTRACTION` | `0.5` | 本次冻结 `DEV_POLICY` | backtrack 缩放 |
| `M02.LINE_SEARCH.MAX_BACKTRACKS` | `20` | 本次冻结 `DEV_POLICY` | 单 Newton step 上限 |
| `M02.LINE_SEARCH.MIN_FACTOR` | `2^-20` | 本次冻结 `DEV_POLICY` | 低于该值判定 line-search exhausted |
| `M02.EVENT.POSITION_TOL_OVER_LREF` | `0.01` | DEV profile | bracket 宽度和事件位置起点 |
| `M02.EVENT.SIMULTANEOUS_TOL_OVER_LREF` | `0.01` | 本次冻结 `DEV_POLICY` | 初版与位置容差相同，独立记录 |
| `M02.EVENT.MAX_BRACKET_ITERATIONS` | `80` | DEV profile | bracket-preserving root solver 上限 |
| `M02.EVENT.MAX_SAME_POSITION_CASCADE` | `50` | DEV profile | 同位置级联硬上限 |
| `M02.DIAGNOSTICS.DEFAULT_LEVEL` | `STANDARD` | 本次冻结 | 开发和正式模块验收默认 |
| `M02.CACHE.DEFAULT_PER_CASE_MIB` | `256` | 本次冻结 `DEV_POLICY` | 仅 numerical trial cache；可配置且不含 M01 cache |

力矩块不得直接套用 N 容差。owner 必须提供 `moment_atol_N_mm` 或声明可追溯的 `force_atol_N × moment_reference_length_mm`。位移、角度、能量、KKT、互补乘积和 graph distance 同样必须有本单位容差及 scale identity；缺失即 `CONTRACT_REJECTION`，M02 不用隐式单位换算补齐。

---

## 5. 公共数值请求、响应和 owner protocol

### 5.1 `ContinuationTarget`

最低字段：

```text
target_id / schema_version
parent_accepted_state_id / parent_commit_receipt_id / parent_state_hash
continuation_coordinate_id / unit / start_value / target_value / direction
oriented_path_mapping_id / characteristic_length_mm / characteristic_length_source
control_mode = MONOTONE_SCALAR_TARGET
physical_owner_ids / required_event_channel_ids
resolved_numerics_config_id/hash
external_dependency_refs (surface/query/config identities only)
request_id/hash / idempotency_namespace
source identity / maturity / certification
```

第一版 `PSEUDO_ARCLENGTH`、多参数自由 continuation 和动态时间积分返回明确 `UNSUPPORTED`，不得降级成固定步长或另一个未声明控制模式。

### 5.2 `TrialStep`

最低字段：

```text
trial_id / target_id / parent_accepted_state_id
phase:
  TARGET_PROBE | EVENT_PROBE | EVENT_POINT | POST_EVENT_SIDE |
  CASCADE_ROUND | FINAL_CANDIDATE
attempt_index / retry_index / cascade_round
requested_coordinate / oriented_path_position_mm / trial_fraction
requested_step / predictor_refs / branch_request_refs
event_channel_subset / bracket_ref / simultaneous_group_ref
evaluation_cache_key / request_hash
accepted_state_advanced=false
```

`TrialStep` 不含可由 M02 修改的 accepted state。predictor 只能作为初值；不能作为 event point 或 accepted solution。

### 5.3 `PhysicalEvaluationRequest`

M02 向一个或多个物理 owner 发出：

```text
trial_step / immutable parent snapshot refs
evaluation_purpose / requested continuation coordinate
unknown iterate or predictor / active branch request
required residual block IDs / event channel IDs
required quality and one-sided checks
dependency/surface coverage refs
diagnostic level / replay decision context
```

### 5.4 `PhysicalEvaluationResponse`

owner 必须返回：

```text
response_id/hash / owner_id/version
opaque_trial_state_ref / rollback_token
unknown_vector metadata / residual blocks / generalized derivative capability
hard inequalities / complementarity quality / graph quality
signed guard samples / event applicability
candidate transition and ledger intents (provisional only)
read_set / write_set / dependency versions
surface realization/query/footprint/materialization/quality refs when used
physical feasibility proof ref or NOT_ASSESSED
capability/status/reason codes
determinism and source identity
```

重复相同 request 必须得到相同 semantic response，或返回明确 stale/conflict；不得推进任何物理历史。owner 可以更新私有、可丢弃 numerical cache，但 cache 命中与否不能改变 semantic response。

### 5.5 `ContinuationAdvanceRequest/Response`

公共服务的最小高层入口为“一次推进尝试”，不承诺一定产生 accepted step：

```text
advance(request: ContinuationAdvanceRequest,
        owner_port: PhysicalNumericsOwner,
        transaction_port: M00TransactionPort)
  -> ContinuationAdvanceResponse
```

response 联合类型：

- `ACCEPTED_STEP`：含 receipt-backed `AcceptedStepRecord`；
- `COMMITTED_EVENT_STEP`：含 receipt-backed accepted point、一个或多个 committed events 和 post-side state；
- `TARGET_COMPLETE`：当前 accepted parent 已在 target 容差内，无新提交；
- `REJECTED_RETRYABLE`：含下一建议步长和 rejected diagnostics，parent 不变；
- `TERMINAL_FAILURE`：含多轴状态、last valid receipt/state 和完整诊断；
- `UNAVAILABLE/UNSUPPORTED`：含 capability axis 和 reason，parent 不变。

---

## 6. 延拓、步长和重试策略

### 6.1 常规步长

1. 新 target 从 `0.5 Lref` 开始，并截断到剩余目标距离和 `1.0 Lref`；
2. 连续两个 accepted steps 同时满足 `Newton iterations <=8`、零 backtrack、无事件、无 quality warning，下一步乘 `1.5`；
3. `9–20` 次迭代且少于 3 次 backtrack 为 normal，下一步保持；
4. `>20` 次迭代或 `>=3` 次 backtrack 为 hard，当前步若满足全部接受门仍可提交，但下一步乘 `0.5`；
5. numerical rejection 从同一 parent 以 `0.5` 重试；retry 不改变 easy streak、路径或历史；
6. 同一 parent 达到 12 次 retry、下一步低于 `0.001 Lref`，或重复相同 failure signature 无进展时，返回 numerical failure；
7. event step 不按普通难步计数，提交后清空 easy streak，下一常规步不得增长；
8. 精确事件位置可以落在常规最小步以内；最小步不得用来跳过已括区事件。

### 6.2 accepted step 的硬门

只有全部成立才可 prepare：

- 每个 hard residual block 通过本单位 absolute/relative test；
- hard inequality、互补和 graph 质量通过；
- owner 声明的一侧 branch consistency 通过；
- event coverage 已证明本段无更早合法事件，或已定位最早事件组；
- domain/geometry/surface quality 可用于声明 scope；
- candidate read/write set、parent/version/hash 和 intents 完整；
- 无 NaN/Inf、未处理 capability 缺口或 transaction conflict；
- 若 owner 要求物理稳定性检查，必须由 owner 明确返回，Newton flag 不能代替。

### 6.3 predictor 规则

- predictor 可以来自上一 accepted tangent/secant、外推、A 的 event fraction 或 owner 自定义 seed；
- predictor ID、来源状态和误差诊断进入 replay；
- A-level event fraction 在 B 中只作 predictor；B 的根位置和最终 `u_z` 必须由 B 曲线平衡路径重求；
- predictor 越界、失效或导致错误分支时可以丢弃，不形成物理失败。

---

## 7. 残量块、缩放、互补和 graph 质量

### 7.1 `ResidualBlock`

每块最低字段：

```text
block_id / owner_id / physical_semantics
raw_values / raw_unit / reduction_norm
raw_norm / reference_norm
absolute_tolerance / relative_tolerance
scale_id / scale_value / normalized_norm
hard_acceptance: bool
source identity / branch / entity refs
```

块接受条件固定为：

```text
raw_norm <= absolute_tolerance + relative_tolerance * reference_norm
```

`reference_norm` 必须非负、同单位、由 owner 通过版本化规则提供，不能取当前 residual 自身来自动放宽门槛。M02 计算的 `normalized_norm` 和总 merit 只用于迭代与步长选择；总 merit 小不能覆盖任何 hard block 失败。

### 7.2 块类型和单位隔离

至少支持并分别报告：

- force equilibrium；
- moment equilibrium；
- kinematic/compatibility；
- load-control residual；
- complementarity/KKT；
- friction/contact graph distance；
- active-set/branch consistency；
- energy/work numerical closure；
- owner-defined hard quality block。

不同单位不能直接拼接。总 merit 使用每块显式 scale 后的无量纲量，默认块权重 1；非默认权重必须进入 config/hash，且只影响搜索，不改变原始硬门。

### 7.3 互补与 graph

owner 必须同时返回：

- 原始 primal feasibility、dual feasibility 和 complementarity product/映射残量；
- 原始 friction/contact graph distance、投影或广义方程质量；
- 各自单位、变量尺度、scale ID、绝对/相对容差和 active branch；
- 非光滑点的 set-valued/one-sided 状态，不得平均法向或伪光滑。

M02 的默认无量纲 NCP/graph absolute 起点为 `1e-8`，relative 起点为 `1e-5`；owner 仍必须提供从原始量到无量纲量的可追溯映射。缺映射、用 penalty residual 冒充严格 graph、或只返回布尔值均为 contract rejection。

---

## 8. 第一版非线性算法范围

### 8.1 必须实现

- 光滑 residual 的 damped Newton；
- 非光滑投影、NCP 和 graph residual 的 semismooth/generalized Newton；
- safeguarded merit line search，使用第 4 节参数；
- owner 提供的 analytic/generalized Jacobian、Jacobian-vector 或版本化 tangent capability；
- 可诊断的线性解、秩/条件警告和线性 residual；
- 对已合法括区的一维事件函数使用 bracket-preserving Brent，失效时退回 bisection；
- 对合法、显式声明的标量平衡子问题允许 bounded secant/Brent fallback。

### 8.2 能力边界

- production A/B owner 必须提供可用 generalized derivative capability；有限差分 Jacobian 只允许 `VALIDATION_ONLY` fixture 或显式 debug，不能在非光滑 production 路径静默启用；
- trust-region 只冻结 adapter 接口和诊断字段，第一版完整算法为 `UNSUPPORTED`；
- pseudo-arclength、deflation、多起点全局分支搜索和 dynamic solve 延期；
- owner 可以返回多个合法分支候选，M02 可按 owner 声明的 branch-enumeration contract 分别求解，但不得按最小 residual 自行赋予物理意义；
- Newton 收敛只表示数值方程达到门槛。物理稳定、唯一、集合值或 infeasible 必须由 owner 的独立证据字段给出。

---

## 9. 统一 signed event 请求

### 9.1 `EventChannelRegistration`

每个物理事件通道最低字段：

```text
channel_id / owner_id / entity_ids / event_kind
guard_id/version / raw_guard_unit / zero_level
admissible_side: NONNEGATIVE | NONPOSITIVE | BOTH_WITH_GRAPH_RULE
trigger_direction: RISING | FALLING | EITHER | TOUCH
applicability predicate ID / branch/state scope
detection_mode / no_event_certificate_capability
dependency_predecessors / transition_owner
post_event_side_request ID
event priority = none (semantic ordering is not numeric priority)
```

M02 不统一规定“正值必然可行”；owner 通过 `admissible_side` 声明。`trigger_direction` 按实际 target 遍历方向解释。每个 probe 保存 raw dimensional guard；缩放值只能用于求根，不能替代 raw 输出。

### 9.2 `EventProbeRequest/Result`

probe request 含 trial fraction、路径位置、parent、branch、所需 guard 集和 equilibrium quality。result 只有在该位置完整平衡与质量门通过后才是合法 guard sample。

特别冻结：

- B `UX_PZ_BALANCED` 曲线上的每个扫描点、括区端点、Brent/bisection probe 和 event point 都必须重新求 `u_z`；
- A 提供的 event fraction/线性插值只作 predictor，不得直接成为 B guard sample 或 event location；
- 若平衡未收敛，guard 值只能进入 rejected diagnostics，不能用于符号括区；
- surface/domain/quality coverage 不足时先请求 owner 扩展/精化；无法取得证明则返回 `EVENT_COVERAGE_UNAVAILABLE`，不得外推。

### 9.3 必须接入的物理 owner 事件族

统一协议必须能表达但不解释：

- 接触建立、零载接触、接触释放；
- 摩擦锥/graph 边界、一侧确认后的真实滑移；
- 支持面—边—顶点或最近特征迁移；
- 弹簧原长、压缩区进入/离开、硬限位进入/离开；
- 针尖、针体、锥段、安装座和环境的 swept collision；
- 释放后搜索、再接触和再预载通道；
- 材料、针体、几何、domain 和 quality guard；
- B 活动集变化、共享 DamageStore 冲突引发的重求请求。

事件注册不代表相应物理 capability 已实现。owner 必须通过 capability axis 明示 `SUPPORTED / UNAVAILABLE / UNSUPPORTED / NOT_APPLICABLE`。

---

## 10. 括区、求根、最早性和漏检防护

### 10.1 区间覆盖不是端点布尔

每个 attempted step 必须获得下列之一：

1. 所有适用通道的合法 root bracket/candidate enclosure；
2. owner 提供的区间 no-event certificate；
3. swept collision/clearance certificate；
4. 有版本的 Lipschitz/enclosure bound；
5. 对声明的检测模式足够的自适应 probe-spacing certificate。

只有端点 guard 同号不能证明区间无根。`TOUCH`、同号双根、释放后再接触和多个事件必须由 owner 的 detection/certificate capability 覆盖；否则该步不可接受。

### 10.2 求根

- 合法变号括区默认使用 Brent，保持 bracket；算法异常或插值不安全时退回 bisection；
- bracket 最大 80 次，结束条件至少包含路径宽度 `<=0.01 Lref` 和 guard/branch 一侧一致性；
- `TOUCH` 事件必须由 owner 提供 stationary/enclosure candidate 或可验证的 touch bracket，M02 不能从任意黑盒 guard 猜测切触根；
- 每次 root probe 都是新的 side-effect-free equilibrium trial；
- event point 必须保存最终 bracket、所有 probe、算法切换、guard raw 值、定位误差和 coverage certificate。

### 10.3 最早性

对所有适用通道：

1. 将根/根区间映射到 target-oriented `lambda∈[0,1]`；
2. 证明从 `lambda=0` 到候选最早 bracket 左端没有其他合法事件；
3. 保留位置在 simultaneous tolerance 内的全部事件；
4. 若某通道 coverage 不足、根未闭合或 B 平衡未重求，最早性未证明，当前 trial 必须拒绝；
5. semantic ID 只用于对相互独立记录生成确定性序列，不得作为物理优先级或丢弃同时事件的理由。

---

## 11. event/post 重求、同时事件、级联和释放—再接触

### 11.1 分支切换后的完整重求

定位事件后必须：

1. 在 event point 对 pre-event 侧完整求解并保存；
2. 收集所有 simultaneous transition intents；
3. 按依赖偏序形成候选 branch/active set；
4. 从同一 accepted parent 和 event coordinate 重新组装全部 unknown、残量、graph、guard、wrench、energy、quality 和 intents；
5. 对 event/post 一侧完整求解并检查 one-sided consistency；
6. 只有整组通过才进入 prepare。

旧 trial 的 wrench、pose、Jacobian、graph multiplier、damage preview 或 residual 不得被当成 post-event 解。若 post-side 用 infinitesimal/finite probe，offset 由 owner 声明并进入 hash；它不得暗中推进 accepted path/time。

### 11.2 同时事件和依赖偏序

- 根区间重叠或位置差在 `0.01 Lref` 内的事件形成 simultaneous candidate group；
- owner 提供依赖边，例如“先关闭旧支持再建立新支持”或“先联合损伤 intent 再重平衡”；
- M02 只做确定性拓扑排序和每层联合重求；依赖环为 contract rejection；
- 无依赖的事件必须联合评价，不能靠 ID 选择一个主事件；
- 多种合法 post-state 若可观察量不同，owner 必须返回 branch nonuniqueness/集合值，不得由 M02任选。

### 11.3 同位置级联和 Zeno 防护

每轮 transition 后在同一 event coordinate 重注册/重评全部适用 guard。以下任一触发 `M02_ZENO_CANDIDATE`：

- 级联超过 50 轮；
- state/branch semantic hash 重复且没有 guard margin 改善；
- event signature 有限周期振荡；
- 零位置进展下重复产生相同 transition intent。

Zeno 结果默认是 `NUMERICAL_FAILURE`/物理可行性 `NOT_ASSESSED`，不得跳过事件或强制跨过最小步。

### 11.4 释放和再接触能力门

释放后下一路径必须由物理 owner 返回以下之一：

- `EXPLICIT_RETURN_PATH`：版本化 pose/path/time mapping 和 swept geometry；
- `HOLD_AT_RELEASE_POSE`：停在释放 pose，继续保持历史；
- `UNSUPPORTED`：模型明确不支持；
- `UNAVAILABLE`：所需 CAD、控制路径、几何或数据缺失。

M02 不得：

- 自动把梁/弹簧/pose 瞬时清零；
- 清零累计路径、物理时间、功、DamageStore、滑移、循环或事件历史；
- 在下一个大步端点发现接触后跨步再挂接；
- 把 `UNAVAILABLE` 伪装成开放态成功或物理无解。

owner 提供 `EXPLICIT_RETURN_PATH` 时，M02 对完整 sweep 使用与常规路径相同的 signed guard、coverage、最早性、event/post 重求和 transaction 规则。Formal 文件中的释放—回位—扫掠—再接触协议只以 `PROPOSED_SUPPLEMENT / VALIDATION_ONLY` 接入。

---

## 12. trial、prepare、commit 和 rollback

### 12.1 状态机

```text
TRIAL_CREATED
  → OWNER_EVALUATED
  → NUMERICALLY_ELIGIBLE
  → EVENT_COMPLETE
  → CANDIDATE_FROZEN
  → PREPARED
  → COMMITTED(receipt)

任何未 commit 分支 → ROLLED_BACK 或 REJECTED
```

状态机转换必须可重入诊断，但 semantic commit 只能发生一次。

### 12.2 trial 无副作用

- trial 只读 immutable accepted snapshot；
- owner 私有可逆变量和历史副本只能存在于 opaque trial handle；
- path/time/slip/damage/work/event/peak/cycle/receipt 序号保持不变；
- 多次 evaluate、事件 probe、线搜索和 rollback 后 accepted state hash 必须 bitwise 不变；
- trial cache 可丢弃，不能成为重放所需的唯一信息。

### 12.3 prepare

M02 汇总 intents，M00 prepare 必须检查：

- parent state/receipt/version/hash；
- schema/registry/resolved-config/owner build hashes；
- ordered intents hash、read/write set 和 DamageStore 冲突；
- event coverage、最早性、post-side 和数值质量完成标记；
- idempotency key 与 candidate hash；
- staging/persistence 可用性。

prepare 不发布 accepted 数据、不增加序号、不推进账本。prepare token 失败或过期必须可 rollback。

### 12.4 atomic commit 和 receipt

一次成功 commit 必须同时发布：

- 所有 owner 的新 accepted physical state；
- 共享 DamageStore/历史和功账本增量；
- accepted point；
- 全部 simultaneous/cascade committed event；
- M02 数值扩展、lineage 和 commit receipt。

没有 M00 最终 commit marker/receipt 的 staging 数据均不是 accepted。相同 idempotency key + 相同 candidate hash 返回原 receipt；相同 key + 不同 candidate 必须 conflict。receipt 一旦发布，rollback token 不得撤销它。

### 12.5 rollback

- 对同一 token 调用一次或多次结果相同；
- token 已 rollback 后再次调用返回同一完成状态；
- 未知、跨 parent、跨 run 或与 committed receipt 关联的 token 必须明确拒绝；
- owner rollback failure 属于 transaction failure，必须保留 last valid accepted state，并启动资源清理诊断，但仍不得把 partial state 发布为 accepted。

---

## 13. deterministic replay

在 M00 `ReplayManifest` 基础上，M02 必须保存：

- target、accepted/trial step 和 parent/receipt 链；
- 每次提议步长、增长/缩短原因、retry 和 easy/hard streak；
- predictor 来源、unknown 初值、branch request；
- 每次 Newton/generalized Newton iteration、linear solve、line-search factor 和 merit；
- residual block raw/scaled quality、hard acceptance；
- event registrations、适用集合、probe、bracket、root method、earliestness certificate；
- B 每个 probe 的平衡 response hash 和 `u_z` 重求证明；
- simultaneous group、dependency DAG、cascade rounds 和 state hashes；
- owner response/intents/read-write sets/rollback/prepare/commit hashes；
- numerical backend、线程、canonical reduction order、floating-point profile 和 diagnostic level。

支持 M00 两级：

- `BITWISE_REPLAY`：同平台/backend/profile 下 step decisions、semantic IDs、events、accepted arrays 和 receipts 位级一致；
- `SEMANTIC_REPLAY`：兼容平台间 event set/order、failure family、branch/state 和 receipt lineage 一致，数值字段在版本化容差内一致。

case 串行/并行、owner 调用顺序、M01 tile/cache cold/warm 和 materialization 顺序不得改变单 case semantic result。差异必须形成字段级 replay report，不得只返回 false。

---

## 14. 诊断级别、输出隔离和失败语义

### 14.1 诊断级别

| 级别 | 保存内容 | 典型使用 |
|---|---|---|
| `COMPACT` | accepted 最终块摘要、committed event 最终 bracket、retry/failure 计数和 receipt refs | 1000/4000 随机地形大批量 |
| `STANDARD` | accepted 最终迭代、全部 event probe/bracket、每个 rejected retry 摘要、最终失败完整轨迹 | 默认开发、320 路径正式兼容验收 |
| `FULL` | 所有 nonlinear/line-search/owner trial 响应、临时 branch 和 transaction 细节 | 解析 smoke、故障注入和指定 witness |

所有级别都必须保留足以重放 semantic decisions 的 hashes/decision records；降低诊断级别不能改变求解路径或结果。

### 14.2 M00 扩展数据集

M02 注册 owner `M02`、namespace `m02` 的 `ResultExtensionDescriptor`，至少包含：

```text
m02.continuation_targets
m02.continuation_attempts
m02.accepted_step_numerics
m02.residual_block_summaries
m02.iteration_traces
m02.event_channel_registrations
m02.event_probes
m02.event_brackets
m02.event_earliestness_certificates
m02.simultaneous_event_groups
m02.event_dependencies
m02.cascade_rounds
m02.rejected_trial_diagnostics
m02.transaction_trace
m02.replay_steps
m02.failure_diagnostics
m02.refinement_studies
m02.m01_compatibility_results
```

accepted step 引用 M00 `AcceptedPointBase`，committed event 引用 `CommittedEventBase`，rejected trial 引用 `RejectedTrialBase`，receipt 引用 `CommitReceiptBase`。M02 不创建竞争 run/state/event/receipt ID。

### 14.3 accepted/event 与 rejected 分离

- accepted physical curves、功、峰值、设计摘要只消费 receipt-backed accepted points 和 committed events；
- rejected trials 只进入 diagnostics/failure summaries，`accepted_state_advanced=false`、`commit_receipt_id=null`；
- event probes 不是 committed events；
- numerical retries、line-search probes 和 rollback 不进入路径采样或设计排名；
- failure statistics 必须单独标明 denominator、diagnostic level 和是否包含 capability unavailable。

### 14.4 失败分类

M02 在 M00 多轴状态上增加 `failure_family`：

| failure family | 定义 | 物理结论 |
|---|---|---|
| `NUMERICAL_FAILURE` | nonlinear/linear/line-search/root/earliestness/retry/replay/Zeno 未完成 | 否；`physical_feasibility=NOT_ASSESSED` |
| `PHYSICAL_INFEASIBLE` | 物理 owner 在合同、域、事件和数值证据充分后返回版本化 proof | 是，但 M02 自己不能生成 |
| `CONTRACT_REJECTION` | schema、unit、scale、guard、依赖、parent/version/hash 或 side-effect 契约不合法 | 否 |
| `DOMAIN_ERROR` | continuation、geometry、surface footprint、query 或质量超出声明域 | 否；不能改成物理无解 |
| `TRANSACTION_FAILURE` | prepare/commit/persistence/rollback/receipt 一致性失败 | 否；last valid state 保持 |

capability `UNAVAILABLE/UNSUPPORTED` 是独立轴，不得压进 numerical failure 或 physical infeasible。

最低 reason codes：

```text
M02_NONLINEAR_NONCONVERGENCE
M02_LINE_SEARCH_EXHAUSTED
M02_LINEAR_SOLVE_FAILURE
M02_STEP_RETRY_EXHAUSTED
M02_EVENT_ROOT_NONCONVERGENCE
M02_EVENT_EARLIESTNESS_UNPROVEN
M02_EVENT_COVERAGE_UNAVAILABLE
M02_ZENO_CANDIDATE
M02_REPLAY_MISMATCH
M02_RESIDUAL_SCALE_MISSING
M02_EVENT_CHANNEL_CONTRACT_INVALID
M02_EVENT_DEPENDENCY_CYCLE
M02_STALE_PARENT
M02_OWNER_SIDE_EFFECT_DETECTED
M02_OWNER_PROVEN_PHYSICAL_INFEASIBLE
M02_PREPARE_REJECTED
M02_COMMIT_CONFLICT
M02_PERSISTENCE_FAILURE
M02_ROLLBACK_FAILURE
```

M01 的 `M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN` 等原始 reason 必须保留，并映射到 `DOMAIN_ERROR`，不能被 M02 改名丢失。

---

## 15. M01 地形、单刺/阵列宽度和随机兼容性

### 15.1 运行时边界

M02 不直接拥有 `QueryFootprint`。物理 owner 必须：

1. 从完整针尖、针体/安装座 swept envelope 和路径派生 geometry offsets；
2. 使用 M01 公共 guard 规则，guard 至少覆盖 probe radius、trusted-scale halo、derivative/search halo、tile halo 和 clearance guard 的最大值；
3. 让 M01 在 150 mm × 150 mm logical parent 内派生活动 footprint；
4. 在每个 trial/event probe 返回 `surface_realization_id`、`footprint_id`、query contract/version、LOD/trust/quality、coverage interval 和 materialization receipt refs；
5. footprint 越界时原样返回 M01 domain error，禁止 wrap、clamp、crop、重随机或缩短 100 mm 路径。

单刺常见窄域只是预期，不是硬编码 10 mm。2×2、2×6、6×2、6×6 等阵列必须由最外针尖、针体和 guard 自动增加宽度。M02 只看到 opaque coverage refs，不根据 `nx/ny/spacing` 计算宽度。

### 15.2 lazy materialization 和事件探测

- 100 mm 完整 logical footprint 可预先声明，但不得一次物化整条最细网格；
- 远前方保持未物化或带 omitted-band bound 的 coarse 表示；
- 前探默认使用 M01 `Rt/5`，event/support 区域 `Rt/8`，最终 acceptance witness `Rt/10`；
- M02 请求新的 probe 坐标时由 owner 确保所需 tile/halo 已覆盖，再返回合法 guard；
- bracket 中任一点 coverage 不足则先扩展/精化，不能对地形或 guard 外推；
- M01 cache/tile 是非 canonical 性能层，trial/rollback 不把 cache receipt 当物理提交。

### 15.3 同源窄/宽足迹不变量

同一 `SurfaceRealization` 上：

- 窄 footprint 与宽 superset footprint 的重叠坐标、导数、closest feature 和 query quality 必须一致；
- 从一开始使用宽 footprint 与按事件动态扩展 footprint，重叠区 event order、accepted result 和 failure classification 必须一致；
- cold/warm cache、tile 顺序、query 顺序和 case 并行度不得改变结果；
- `surface_scale_reference_Rt_mm` 固定且显式，不能随被扫描的针尖 `Rt` 自动变化；
- query probe radius `0.05/0.10 mm` 可在同一 realization 上改变查询与 LOD，但不能改变 surface identity。

### 15.4 随机地形兼容性三级规模

每个 scenario 是独立 `SurfaceRealization`，由 `(H, Sq/reference-Rt, lc/reference-Rt, anisotropy, direction, seed_id)` 唯一标识。面板使用分层 maximin/common-random-number 设计，均衡覆盖 gentle/medium/sharp、相关长度、各向异性、方向和 seed；不能生成一张地形重复冒充多个独立样本。

每个 realization 运行五类完整 100 mm footprint/path：

1. `SINGLE_SPINE`；
2. `ARRAY_2X2_S4`；
3. `ARRAY_2X6_S6`；
4. `ARRAY_6X2_S6`；
5. `ARRAY_6X6_S6`。

标签只定义验证 geometry fixture 的针数/间距；实际活动宽度仍由 M01 派生。三级规模：

| 面板 | 独立随机地形 | footprint 类 | 完整路径数 | 执行门 |
|---|---:|---:|---:|---|
| `M02_M01_SMOKE_4` | 4 | 5 | 20 | 每次相关改动；FULL |
| `M02_M01_STANDARD_64` | 64 | 5 | 320 | M02 模块正式验收硬门；STANDARD |
| `M02_M01_STRESS_256` | 256 | 5 | 1280 | release-candidate/扩展压力；本实现窗口至少完整运行一次 |

stress 面板全量可用 `COMPACT`，但至少固定 32 个 scenario ×5 footprint 使用 `STANDARD`，所有失败自动升级完整诊断。路径计数不等于 query 次数；每条路径必须包含逐步 lazy query、事件 probe、窄/宽 overlap、cold/warm 和选定 `Rt/5→Rt/8→Rt/10` witness，不得通过一次性生成全域 dense terrain 规避 M01 优化路径。

---

## 16. 分阶段钩爪参数筛选负载合同

本节冻结 M02 必须能够承载和正确诊断的仿真项目，不把选优逻辑变成 M02 物理。case scheduling/统计由 M05，物理指标由 A/B owner，M02 只保证每条路径的数值、事件、事务和重放。

### 16.1 阶段设计

| 阶段 | 设计组合 | 每组合地形 | 完整路径 | 设计目的 |
|---|---:|---:|---:|---|
| 单刺预筛 | 16 | 4 个共同随机场景 | 64 | `Rt(2) × d(2) × 安装角(4)` 全因子，先排查明显域/能力/数值问题 |
| 阵列初筛 | 64 | 4 个共同随机场景 | 256 | 48 个 maximin/D-optimal 覆盖点 +16 个强制成对 controls |
| 阵列细筛 | 16 | 16 个共同随机场景 | 256 | 8 个 robust Pareto survivors +4 个邻域点 +4 个审计/重复点 |
| 最终比较 | 4 | 同一组 1000 个随机地形 | 4000 | 配对比较、尾部事件和失败率统计 |
| 最终扩展 | 同 4 个 | 同一扩展到 4000 个随机地形 | 16000 | 只有排名/置信区间/稀有事件仍不稳定时触发 |

基础项目共 `4576` 条完整物理路径；触发 4000 地形扩展后共 `16576` 条。M02/M01 的 20/320/1280 数值兼容路径是独立的软件验收负载，不与上述物理筛选路径重复计数。

DEV profile 的 `64→128→256→512` 保留为最终四方案共享面板内的中间 checkpoint；用户批准的正式规模延伸为 `1000`，必要时直接扩展到 `4000`。1000/4000 表示独立 terrain scenario 数，四个方案必须运行相同 scenario IDs，因此分别产生 4000/16000 条 paired paths。某方案数值失败时不能只给该方案补一个新 seed；必须保留配对缺失和 failure status。

### 16.2 参数覆盖而非新本构

阵列设计从 DEV profile 已有参数网格抽样：`Rt`、针径、安装角、`nx/ny`、spacing、mount mode/弹簧刚度、单元主动推力和摩擦 sensitivity。M02 只把这些作为 opaque resolved case config 和 owner identity；不解释它们如何进入物理残量。

### 16.3 筛选输出原则

禁止二元“成功”和未经用户批准的 composite score。后续筛选使用 hard gates + Pareto/robust raw metrics，至少保留：

- 首次承载位置/右删失、`Rx` 曲线与分位数、正拖曳功；
- 承载持续区间、平台/保持率、释放—再接触间距和事件链；
- `Nload`、`Neff`、逐针载荷不均衡和活动集；
- 弹簧行程、硬限位、支撑迁移和 collision/domain/quality guard；
- event density、numerical failure、physical infeasible、capability unavailable 和运行成本，分别统计。

`NUMERICAL_FAILURE` 不得被当成方案物理性能差而淘汰。1000→4000 的扩展判定由 M05/验证层对 paired confidence、Pareto front、尾部失败率和两个连续 checkpoint 的稳定性作出；M02 只提供完整数据和可重放性。

大批量默认 `COMPACT`，每个方案对同一固定 5% scenario witness 使用 `STANDARD`，所有数值/事务/域失败自动保留完整 failure trace。

---

## 17. 首批图的数据合同

M02 不选择视觉 preset，但必须为下列 recipe 提供无歧义 raw/derived-ready 数据：

1. **残量迭代图：** iteration、block raw norm、tolerance、normalized norm、merit、linear residual、line-search factor；
2. **步长图：** attempted/accepted coordinate、requested/accepted step、retry、growth/shrink reason、event marker；
3. **事件括区图：** raw guard、unit、probe coordinate、bracket、root、方向、simultaneous band、equilibrium quality；
4. **释放—再接触事件链：** release pose、path mode、swept probes、contact/reload events、state/event/receipt lineage；
5. **精化误差图：** step、event tolerance、M01 LOD、root solver level 对事件位置、力/功摘要和顺序差异；
6. **失败统计图：** failure family、reason code、stage、design/surface/footprint、last valid state 和运行成本。

recipe ID、字段 ID、过滤规则、accepted/rejected 数据集边界和 source identity 必须版本化。正式颜色、字体、版式、面板布局和导出 preset 延期到用户与 M06；M02 验收不能因未选择美术 preset 而阻塞。

---

## 18. 测试和验收矩阵

### 18.1 解析残量和 continuation

- 标量线性、非线性和已知根系统；
- 平滑 Newton 与 semismooth NCP/投影 fixture；
- 分块 N/N·mm/mm/无量纲缩放，验证总 merit 不能掩盖 hard block；
- 0.5/1.0/0.001 `Lref`、easy×1.5、hard/retry×0.5、12 retry 和目标截断；
- h、h/2、h/4 精化下 accepted summary、功、残量和状态序列收敛；
- strict rigid/set-valued fixture 返回 graph/degeneracy，不出现隐藏 penalty stiffness。

### 18.2 事件根、顺序和漏检

- 解析 crossing root，rising/falling/either 方向；
- 解析 tangency/touch root；
- 端点同号但区间内两个根；
- 多通道不同位置，必须选择最早且保留最早性证书；
- 大步与减半步得到相同事件顺序和 simultaneous set；
- 故意缺 no-event certificate 时安全返回 coverage unavailable；
- bracket solver Brent→bisection fallback、80 次上限和 raw guard 记录；
- B mock 的 `u_z(x)` 非线性，故意提供错误 A predictor，验证每个 probe 都重求 `u_z` 且根正确；
- release—return sweep—recontact 的同号端点/双根 fixture，验证无漏检再接触。

### 18.3 event/post、同时事件和级联

- branch switch 后 event/post 全量残量、wrench、graph 和 intents 都重新调用；
- 同位置无依赖事件联合求解；
- 有依赖 DAG 分层求解；
- dependency cycle contract rejection；
- 50 轮上限、重复 state hash 和振荡触发 Zeno；
- owner 无回位路径时保持 release pose 或返回 unsupported/unavailable，路径/时间/历史不清零。

### 18.4 事务、幂等和故障注入

- 重复 trial 和任意顺序 rollback 后 accepted hash 不变；
- prepare 前后故障、commit marker 前后故障、receipt 写入故障和恢复；
- 相同 idempotency key/candidate 返回同 receipt；不同 candidate 冲突；
- committed receipt 不能 rollback；
- accepted state、DamageStore、event、功和 receipt 无部分可见；
- numerical failure、owner-proven physical infeasible、contract rejection、domain error、transaction failure 和 unavailable 的反例分类。

### 18.5 replay

- 相同请求重复调用 bitwise 一致；
- serial/parallel owner order 和 case order 不改变单 case semantic result；
- cold/warm M01 cache、tile/query/materialization 顺序不改变结果；
- 故意修改 backend/profile/config/owner hash 时产生结构化 replay mismatch；
- BITWISE 与 SEMANTIC 两级报告分别验证。

### 18.6 M01 随机地形兼容性

- 完整运行第 15.4 节 20、320 和一次 1280 路径面板；
- 五类 geometry envelope 的实际 footprint 宽度由 M01 API 派生并记录，不使用固定 10 mm；
- 同一 realization 的窄/宽 overlap bitwise/semantic 一致；
- 100 mm 起终点 guard、域外拒绝、不 wrap/clamp/缩短；
- lazy tile、ahead `Rt/5`、event `Rt/8`、acceptance `Rt/10`，不构造全域最细 dense array；
- probe radius 0.05/0.10 mm 不改变 surface identity；
- `Rt/8→Rt/10` witness 起点：event position 变化 `<=0.01 Rt`、适用的 unique support 位置 `<=0.02 Rt`、normal `<=1°`，力/功 fixture 摘要相对变化 `<=1%`，event order 完全一致；未通过则继续精化或明确失败，阈值以后仅按收敛修订。

### 18.7 输出、图数据和大负载可调度性

- M00 extension registry、metadata、ResultWriter/Reader round trip 和 rejected/accepted 隔离；
- 六类首批图所需字段完整，recipe 过滤不把 rejected trial 混入物理曲线；
- 1000/4000 terrain ×4 designs 的 execution plan 可流式分片、暂停、重放和合并，不要求本 M02 实现窗口运行尚不存在的 A/B 全物理；
- 使用 synthetic owner 验证 4000/16000 case plan 不需要在内存持有全 campaign；峰值 M02 cache 受每 case 256 MiB 配置约束且不随总 case 数增长；
- 报告硬件、OS、runtime、backend、线程、case/step/event 数、wall time、peak RSS、M01 cache、M02 cache、输出大小和各诊断级别成本。

---

## 19. schema/API 兼容和演化

- M02 public contracts、event schema、transaction schema、result extension 和 replay decision schema 均从 `1.0.0` 开始独立版本化；
- 增加可选诊断字段为 minor；改变 accepted、event、failure、idempotency、单位或默认算法语义为 major；
- reason code 只可新增或 deprecated，不可静默改义或复用；
- M00 core ID/status/receipt 字段不能被 M02 override；
- M01 public identity/quality/reason 原样引用，不复制为第二套 surface schema；
- owner callback 的 unknown/state/intent 内容保持 opaque，M02 只验证注册 metadata、hash、状态和数值块；
- reader 必须能拒绝未知 major、读取兼容 minor，并保留未知扩展字段。

---

## 20. 明确延期和禁止项

延期：

- pseudo-arclength、trust-region 完整 backend、deflation、多起点全局分支搜索；
- 动力学、冲击、惯性和弹道再接触；
- production finite-difference generalized Jacobian；
- C 的非零全局 X/45°、rocking 和正式 `Fcrit`；
- M05 正式批调度、统计停止和设计选择；
- M06 正式绘图 preset；
- 实验标定、材料认证和真实表面统计。

禁止：

- 大罚刚度冒充严格刚性物理；
- 端点布尔变化冒充最早事件定位；
- trial/event probe/rollback 推进任何 accepted history；
- B event probe 复用旧 `u_z` 或把 A event fraction 当根；
- 分支切换后复用旧 trial response；
- M02 自动选择 A/B 物理分支或修改其方程；
- release 后瞬时回零、跨步重挂接或清历史；
- 把 numerical failure 当 physical infeasible 或设计失败；
- 把一张随机地形重复算成多个独立样本；
- 为单刺硬编码宽度、为阵列固定裁剪宽度、crop normalization 或 footprint-relative rerandomization；
- 为降低数据量而截短 100 mm 路径、降低 guard、跳过 event probe 或构造与 M01 identity 不一致的新表面。

---

## 21. 决策日志和关闭状态

### 21.1 accepted

- target、trial 和 accepted step 是三个不同对象；accepted 只由 receipt 证明；
- 首版单调标量 continuation，B 曲线平衡中的 `u_z` 每 probe 重求；
- 0.5/1.0/0.001 `Lref`、1.5 增长、0.5 缩短、12 retry；
- 分块 raw + scaled residual、hard block、NCP/graph 双重质量；
- semismooth/generalized Newton + safeguarded line search；
- signed guard、方向、括区、touch/certificate、最早性和 Brent/bisection；
- 统一接触/释放/摩擦/迁移/限位/collision/recontact/domain/quality event channel；
- event/post 全量重求、simultaneous DAG、50 轮级联和 Zeno；
- M00 原子 prepare/commit/receipt，幂等 rollback/replay；
- accepted、committed events、rejected trials、transactions 和 diagnostics 分离；
- 20/320/1280 M01 随机地形兼容面板；
- 参数扫描 16→64→16→4，最终 4 方案共享 1000 地形，必要时 4000；
- M02 冻结 plot data/recipe，正式视觉 preset 留给用户与 M06。

### 21.2 rejected

- 固定步长；
- 只监控步长端点；
- 单一总 residual 阈值；
- penalty-only rigid branch；
- Newton flag 兼任物理稳定/不可行判断；
- trial 内直接写 accepted state；
- release 后自动 pose/history 清零；
- 单地形或非配对随机场景做最终方案比较；
- numerical failure 作为设计淘汰项；
- M02 自己计算阵列 footprint 或拥有 M01 tile。

### 21.3 deferred

见第 20 节。延期内容不阻塞 M02 `1.0.0`，但必须返回明确 capability status。

### 21.4 unresolved

`none`。物理参数、正式图形风格和后续统计停止阈值属于已明确转交的模块/决策层，不是 M02 未关闭需求。

---

## 22. 实现窗口完成判据

M02 实现只有同时满足以下条件才可关闭：

1. 公共 contracts、solver/event/transaction/replay/diagnostic 服务全部实现且无 A/B 物理反向依赖；
2. 第 18 节测试矩阵逐项有 requirement-to-test 追踪；
3. 解析根、事件顺序、同号双根/再接触、B 曲线重平衡、event/post 重求、rollback/幂等和精化收敛全部通过；
4. M00 canonical bundle、extension、receipt、reader 和 replay 通过；
5. M01 的 20/320/1280 随机兼容面板按规定运行并形成报告；
6. accepted/rejected/event/transaction 数据没有串类，failure family 反例通过；
7. 性能报告证明 case 流式、cache 有界、结果不受并行/cache/order 影响；
8. 模块 README 含简短 `## 输出概览`，字段、消费者、单位、索引、status/source/maturity 清楚；
9. 生成 M02 traceability、validation、performance 和 acceptance reports；
10. 保持 `experimentally_validated=NOT_ASSESSED/BLOCKED_UNAVAILABLE`、`not_certifiable`，不产生物理认证宣称；
11. 严格按 Git 安全交接只暂存 M02 文件，检查 cached diff，提交、推送并停止，不自动进入 M03/M04/M05/M06。

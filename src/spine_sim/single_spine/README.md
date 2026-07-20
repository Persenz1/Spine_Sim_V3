# M03 Single Spine

M03 实现 A-M0 单刺本征力学产品：复合针几何、M01 表面查询适配、刚性
Signorini/Coulomb 接触、Euler--Bernoulli 梁、A 权威 mount、事件/状态语义以及 M00
结果扩展。首版物理主线固定为 `no_damage`，只用于解析或合成表面的开发验证；它不是砖面破坏、针体安全或阵列承载认证模型。

当前状态是 implementation delivered / acceptance blocked / evidence incomplete。完整 100 mm driver 行为目前由注入式解析 constitutive fixture 覆盖，不能替代 `IntrinsicSingleSpineKernel` 的端到端完成证据；artifact-capable 本征 standalone history 已把 `KernelEvaluation` 随 accepted snapshot 传给 M00 publication，定向真实 clearance witness 的 5/5 个 normal-bearing candidates（含 non-active、local-minimum、empty-ball 证据）均由同一 receipt 持久化，并已有 fault rollback、idempotency 与 semantic replay 测试。冻结候选 schema 的 `normal_global` 不可为空，因此 `radial_normal_global=None` 的退化候选仍只能显式计为 unrepresentable，不能伪造法向量。独立梯形 actuator 输入功已实现，但真实平面 witness 对 `ΔU+D` 仍有 18.65% mismatch 并触发 hard quality failure；本征 kernel 目前提供 14 类 runtime guards，和 standalone guards 合计仍只覆盖冻结事件集合的一部分。最终 medium 36 + gentle/sharp 2 已全部执行并形成 38 条明确 capability termination，streaming 与定向 replay/cold-warm/slice 证据一致；但 0 个完成 100 mm、0 个 final M00 receipt、0 个趋势值。详细状态见 [`M03_SINGLE_SPINE_TRACEABILITY.md`](../../../docs/simulator_development/implementation/M03_SINGLE_SPINE_TRACEABILITY.md)。

## 两种调用模式

### Embedded constitutive trial

唯一供 B 使用的模式是 accepted `A_TO_B 1.0.0` 的
`embedded_constitutive_trial`。调用方用 `make_embedded_request(...)` 构造不可变 trial，随后调用
`IntrinsicSingleSpineKernel.evaluate_trial(...)`。kernel 只返回当前 trial 的 contact-only 响应与候选
event/intent；它不推进 path、time、slip、work、cycle 或 accepted history，也不修改 M01 surface 或
damage snapshot。B/M02 必须负责延拓、event bracket/cascade、accept/reject 与原子 commit。Embedded
request 禁止携带逐刺 `Pz` 或其他重复 normal-load 字段，open 分支也不会搜索 `Pz` 平衡。

### Standalone protocol

`make_standalone_request(...)` 冻结 standalone 协议：从 full-body certified clearance 开始，经
`NESTED_Z_SEARCH` 沿 `-global-Z` 找最早合法 finite-cap 零载接触，以 `eta=0..1` 同伦预载到
`0.5 N`，再沿 `+local-x` 以 `1 mm/s` 拖曳累计 `100 mm`。释放策略固定为
`LIFT_OFF_RESEARCH_V1`；释放路径不可用时保持最后 committed pose，并以
`HOLD_AT_RELEASE_POSE` 和显式 reason 结束。release operation speed 未声明，故其 physical
operation time 必须 unavailable。

`run_standalone_single_spine(request)` 是函数式入口；需要注入 kernel、event engine、resolved driver
config 或 return-path provider 时使用 `StandaloneSingleSpineDriver`。它拥有 outer-operation 编排，
并把 signed-root localization、earliestness、event pre/post/cascade 与 transaction 协调交给 M02；
本征 kernel 仍只执行 side-effect-free trial。`StandaloneExecution` 同时返回 public response 和
accepted/event/rejected/operation records；支持 artifact API 的 kernel 还会把真实 `KernelEvaluation`
保存在对应 trial snapshot。`persist_standalone_execution(...)` 优先从该 artifact 写出 full-candidate raw，
并将 accepted、event、operation、work、cycle、capability 和 run request 在同一 M00 transaction 中发布，
让 rejected diagnostics 走独立的无 receipt 原子路径。仅返回 public response 的注入式 kernel 继续走
response-only fallback；遇到 `radial_normal_global=None` 的退化候选时显式计数并跳过，绝不补造证据。

高级 request/value 类型保留在 `spine_sim.single_spine.contracts`；包根只重导出稳定的工厂、kernel、
campaign、result extension、summary 与 plot-recipe 入口。

## Owner 边界

| Owner | M03 可以依赖或提供的边界 |
|---|---|
| M00 | M00 拥有 schema registry、point/event/trial/receipt identity、writer、reader、integrity 与 commit receipt；M03 只注册 `m03` extension 和 receipt-backed records。 |
| M01 | M01 拥有 immutable surface realization、query/materialization、coverage/LOD、feature/chart 与 query receipt；M03 只根据完整 current/swept needle geometry 请求并消费这些证据。 |
| M02 | M02 拥有 nonlinear solve orchestration、continuation、earliest-event bracket/cascade、retry/rollback、transaction 与 replay；M03 只提供 physical residual、branch、guard、post-side callback 和 intent。 |
| M03 / A | M03 拥有单刺几何、接触图、梁、mount、单刺 state/event/capability、standalone outer-operation 协议，以及 `A_on_B` 本征响应。 |
| B / system | B 拥有阵列位姿/载荷映射、跨刺共享与 accepted A-to-B commit 协调；不得调用 standalone driver，也不得向 embedded request 注入逐刺 `Pz`。 |
| M04--M06 | 不属于 M03 runtime。阵列、多刺共享、scheduler/ranker 与正式交互绘图不得反向进入本包。M06/审计工具只经 M00 `ResultReader` 读取 canonical results。 |

## 单位、坐标与参考点

- 固定单位系统是 `N-mm-MPa`：长度 `mm`、力 `N`、力矩/功/能量 `N*mm`、应力/模量
  `MPa`、角度 `rad`、时间 `s`。不得用未声明单位的裸值替代合同字段。
- pose 使用 `GLOBAL` 表达、`M03_GLOBAL_LEFT_MULTIPLY_1` 复合规则和
  `M03_BASE_REFERENCE_O`。默认 local frame 为右手系：`e_x` 是任务/拖曳方向，
  `e_z=global-Z`，`e_y=global-Z cross e_x`。
- canonical wrench 顺序为 `(Fx, Fy, Fz, Mx, My, Mz)`，是 declared `O` 点、global frame
  下的 contact-only `A_on_B` 作用；`opposite_wrench_B_on_A` 必须逐分量严格取负。
  `grip_resistance_Rx=-e_x dot F`。改变参考点时必须保留 reference-transport/work invariance。
- `surface_scale_reference_Rt` 固定为 `0.05 mm`。扫描 tip `Rt` 不得更换、裁剪、wrap 或重新随机化
  M01 surface realization。

## 12 个 M00 extension datasets

所有表的 namespace/owner 为 `m03`/M03，并以 `run_id`、`case_id` 作为公共检索键。

| Dataset | 类别 | 内容与隔离语义 |
|---|---|---|
| `m03.run_requests` | transaction | resolved request/config、参数与 surface identity、output policy、receipt。 |
| `m03.accepted_state_history` | accepted | 每个 committed point 的 pose、几何、wrench、结构、状态、质量与 capability。 |
| `m03.support_candidate_history` | accepted | accepted point 的 nearest/co-minimal/switch support candidates 与 M01 证据。 |
| `m03.contact_support_history` | accepted | 每个 accepted support 的 gap、basis、multipliers、摩擦/滑移与 graph 状态。 |
| `m03.committed_event_payloads` | event | receipt-backed event 的 pre/event/post payload 与 guard/quality 证据。 |
| `m03.release_operation_history` | event | unload/unlock/lift/research/reload 等 outer-operation lifecycle。 |
| `m03.rejected_diagnostics` | rejected | trial/probe/retry/rollback 诊断；默认 reader/recipe 不可见且绝不推进 accepted 历史。 |
| `m03.work_ledger` | accepted | actuator input、beam/spring 能量、摩擦耗散、returned/released energy 与 closure。 |
| `m03.contact_cycle_records` | event | release、recontact、reload/reengagement 与累计 path/time 的 cycle lifecycle。 |
| `m03.capability_status` | accepted | damage、strength、failure prediction、model validity 等显式 capability/status。 |
| `m03.derived_summaries` | summary | 带 definition version/hash、raw links 与 right-censoring 的可重建摘要。 |
| `m03.plot_recipe_manifest` | summary | 八类 machine-readable recipe 的字段、过滤、分组、raw links 与缺失策略。 |

Accepted/event 数据必须由 commit receipt 支撑；rejected 行与 accepted/event 严格隔离。任何降采样、
peak 或 summary 都是 derived product，必须保留版本化定义和 canonical raw links。

## Status、source 与四栏 maturity

每条 M03 row 都保存 `schema_version`、多轴 `status`、`source_identity`、`maturity` 和
`certification_status`。`status` 分开表达 value presence、capability、attempt outcome、physical
feasibility、certification、reason/explanation/authority refs；数值收敛不能自动升级为物理可行、唯一或可认证。

`SourceIdentity` 必须从 `FIXED_ENGINEERING`、`ACCEPTED_AUTHORITY`、
`PROPOSED_SUPPLEMENT`、`DEV_POLICY`、`VALIDATION_ONLY` 中显式选择。M00 默认 reader identity
集合是 `FIXED_ENGINEERING`、`ACCEPTED_AUTHORITY` 和 `DEV_POLICY`；
`PROPOSED_SUPPLEMENT` 与 `VALIDATION_ONLY` 需要 `include_non_default=True`。

成熟度必须保留四栏，不能压成一个 `completed` 布尔值：

1. `theory_defined`
2. `code_implemented`
3. `numerically_verified`
4. `experimentally_validated`

默认 `m03_maturity()` 表示 theory 已定义、code 已实现并有证据，numerical verification 尚未评估，
experiment 始终 `NOT_ASSESSED`。只有实际生成并核验相应数值证据后，才可调用
`m03_maturity(numerically_verified=True)`；这仍不会提升实验栏或认证状态。

## ResultReader 最小示例

只通过 M00 只读接口消费 bundle；下面查询 receipt-backed accepted state，不读取 rejected rows：

```python
from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.reader import FilterSpec, OrderSpec, ResultReader

reader = ResultReader.open(
    "build/m03/M03_VALIDATION_ONLY.spine-result",
    verify_mode=VerifyMode.MANIFEST,
)
accepted = reader.query(
    "m03.accepted_state_history",
    fields=(
        "point_id",
        "commit_receipt_id",
        "accepted_point_index",
        "x_total_mm",
        "grip_resistance_rx_n",
        "primary_mechanical_state",
    ),
    filters=(FilterSpec("commit_receipt_id", "!=", ""),),
    ordering=(OrderSpec("accepted_point_index"),),
).read_all()
print(accepted.to_pylist())
```

读取 `m03.rejected_diagnostics` 必须显式传入 `include_diagnostics=True`；如果目标 row 的 source
不在默认集合中，还须传入 `include_non_default=True`。可先用 `list_fields`、`describe_fields` 和
`list_relations` 审计单位、frame/reference、source、maturity 与 M00 relations。

## Damage、strength 与认证边界

首版 material model 固定为 `no_damage`。Damage/failure/fracture-energy 字段必须以 typed
`NOT_APPLICABLE`/空值返回，且 `failure_prediction_allowed=False`；不得用数值零伪装“已计算且未损伤”。
`material_dissipation=0` 只说明 `NO_DAMAGE_MODEL` 不存在该耗散通道，不是材料安全证据。

Needle yield/fracture margin 和 strength certification 必须为 typed null，加
`NEEDLE_STRENGTH_UNAVAILABLE`；beam root force/moment 与 section resultants 仍应返回，但不能据此宣称
安全系数。所有 M03 解析/合成输出均为 `NOT_CERTIFIABLE`，实验成熟度为 `NOT_ASSESSED`；趋势、
analytic fixture、synthetic campaign 和 numerical verification 都不能替代目标墙面实验认证。

# M03 SINGLE_SPINE 验收报告

**任务：** `M03_SINGLE_SPINE_IMPLEMENTATION`

**需求：** `M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 frozen`

**验收日期：** 2026-07-20

**总体验收结论：** `NOT_ACCEPTED / BLOCKED_EVIDENCE_INCOMPLETE`

**范围标签：** `DEV_PRIOR / synthetic_or_analytic_surface / no_damage / not_certifiable`

## 判定摘要

M03 的代码面、typed contracts、解析 suite、standalone 编排、accepted A→B adapter、M00 extension、canonical validation demo、8 类 Reader-only recipes 和 38-case streaming runner 均已交付。全仓 574 项测试通过；当前产品代码、测试与脚本（`src tests scripts`）范围的 lint、format、strict mypy 与构建通过。

冻结的 medium 36 + gentle/sharp 2 已全部实跑并形成明确结果：38 个均为 `CAPABILITY_TERMINATION / CAPABILITY_UNAVAILABLE`，其中 37 个 `M01_RESOLUTION_REFINEMENT_REQUIRED`、1 个 `M03_GEOMETRY_UNCERTAIN`。初始 geometry failure 的原始 M01 reason 不再被缺失 tip guard 遮蔽。这使 §20.5 的“每个非完成 case 给出非数值伪装的明确终止”得到限定满足；但没有 case 完成 100 mm、没有 final M00 receipt、没有趋势值。真实 loaded-plane 独立功账本也以 18.65% mismatch 触发 hard rejection。

§20 是合取门。§16 完整矩阵、baseline 100 mm、功/事件/几何闭合与跨模块系统证据仍未同时满足，因此不得把局部测试、明确 capability termination、validation demo 或 Git 交接写成 `ACCEPTED`。

## 最终证据

| 证据 | 结果 | 解释边界 |
|---|---|---|
| 全仓回归 | `574 passed in 107.61 s`；M03 134，M00–M02/lower-module 440 | 证明现有 fixture 范围；不证明真实 100 mm |
| 静态/构建门 | `ruff check src tests scripts` 通过；同范围 132 files format-check；`mypy src/spine_sim scripts` 严格配置下 75 source files；wheel/sdist build 成功 | 软件质量门通过；历史 `archive/` 不在本次 Ruff 门范围；不提升物理成熟度 |
| 解析 suite | 6/6 cases、84/84 checks；87,085 B；SHA `88be8f67...8a033` | M01/M03 解析几何证据，不是 standalone mechanics |
| canonical validation | 1,748,393 B；semantic hash `ca29cc62...4106`；MANIFEST/FULL 通过 | embedded validation-only demo；1 accepted、1 event、1 rejected |
| validation figures | 8 recipes、16 files、0 data gaps；manifest internal `832a6aa4...bc63` | Reader-only 渲染可用；parameter-trends 是 demo |
| 38-case campaign | 38/38 outcome；293.063 s；37 M01 refinement required + 1 M03 geometry uncertain | 0 个 100 mm、0 receipt、0 trend；无 numerical failure 被当趋势 |
| streaming/replay | FULL history 1/1；pause/resume、slice、cold/warm 非易变证据一致 | 仅证明 capability-terminal rows；没有 committed 100 mm history |
| loaded-plane work | independent quadrature；normalized closure `0.1865128`；hard rejected | 功门诚实生效，但物理闭合失败 |
| damage/strength | no-damage；damage/fracture energy not applicable；needle strength unavailable | `experimentally_validated=NOT_ASSESSED`、`NOT_CERTIFIABLE` |

主要 machine-readable 产物：

- [`M03_ANALYTIC_SUITE.json`](../../build/m03/M03_ANALYTIC_SUITE.json)：SHA-256 `88be8f67d246266d9e5fc3f5c202036fb7984d41b30a80e079ce082284d8a033`。
- [`M03_CAMPAIGN_PLAN_ONLY.json`](../../build/m03/M03_CAMPAIGN_PLAN_ONLY.json)：SHA-256 `975d992214fb781dd8c86b826acf6a62e81c4e33e71306d76a653fb5762463c0`。
- [`M03_CAMPAIGN_RUN.json`](../../build/m03/M03_CAMPAIGN_RUN.json)：SHA-256 `425c7b95420c80cfe7269a89f19f0181d62b8e0eba71c5153851f63908db54dc`；replay ID `m03_campaign_replay_manifest:078bcf4bde3ae5572d2d2cd67817b4543998f8ef14d8a949aaac65bcbf139c73`。
- [`M03_VALIDATION_RUN.json`](../../build/m03/M03_VALIDATION_RUN.json)：SHA-256 `bd1f1632a62ac267999b2a78e804ad90eb14b0032aaaefa3c54d4dec696b085b`。
- [`spine_sim-0.4.0-py3-none-any.whl`](../../dist/spine_sim-0.4.0-py3-none-any.whl)：457,304 B，SHA-256 `2e924be86c2a73d6bb22dbb4f44fd1f3f38548c3218c3553bbaa4521541d21e5`。

## §16 验收矩阵

| 条款 | 状态 | 已有证据 | 未闭合项 |
|---|---|---|---|
| §16.1 geometry/query | `PARTIAL` | 6-case analytic suite；真实 M01 局部极大/鞍点拒绝；解析 plane `Rt/8→Rt/10` witness | rough/general `Rt/5→Rt/8→Rt/10`、弯曲中心线碰撞、完整 event-order refinement |
| §16.2 contact/friction | `PARTIAL` | open/zero/loaded、objective slip、all-stick redistribution、严格 maximum-dissipation/SOC、多支持顺序与 action/reaction tests | final deformed tip/support geometry 未重查询耦合；previous-active lineage 尚未由事务所有的 continuation evidence store 承载 |
| §16.3 beam/spring/dedup | `PARTIAL` | EB analytic/reference、bending-off、spring branches、rigid graph 与基本能量 tests | full-kernel 4 mm hard-stop、branch-consistent tangent/energy refinement 不完整 |
| §16.4 path/events | `PARTIAL` | same-sign/touch/simultaneous/cascade tests；strict pre/event/post commit gates；14 类本征 guards | 真实路径没有完整 32-kind one-sided event/post、release/recontact/reengagement evidence |
| §16.5 standalone/embedded/transaction | `PARTIAL` | duplicate Pz、open zero wrench、trial immutability、fault rollback、idempotency、accepted/event/rejected isolation、semantic slices | 无真实本征 100 mm 等价 prescribed-path 对照；campaign 无 canonical M00 commit receipt |
| §16.6 work/residual/output | `BLOCKED` | hard residual gate、12 datasets、Reader roundtrip、summary rebuild、damage/strength unavailable | loaded-plane work mismatch 18.65%；returned energy、operation raw guard 和 refinement closure 不完整 |
| §16.7 surfaces/trends | `PARTIAL` | analytic 6/6；38 个 case 均明确非数值终止；surface/path/query policy 配对 identity 保持 | 0 trend-eligible case，无法验证真实 `Rt,d,alpha,mu,ks` campaign trends |
| §16.8 performance/scheduling | `NOT_MET` | 38 案可调度；per-case metrics；FULL history 1/1；无 dense grid；semantic slices 一致 | 0 个 baseline 100 mm；冻结条款明确此项失败即验收失败 |

## §20 完成判据

| # | 判定 | 证据与理由 |
|---:|---|---|
| 1 | `PASS` | 本征核、standalone、A→B adapter 已交付；未实现 B 阵列。 |
| 2 | `PASS` | 参数/request/response/state/event/reason/output typed contracts 与负例校验已形成。 |
| 3 | `PARTIAL` | M00 extension、M01 adapter、M02 bridge 与 transaction persistence 已形成；degenerate candidate、full event path、operation evidence 与 campaign receipt 未闭合。 |
| 4 | `NOT_MET` | §16.6/§16.8 阻断，其他多项仍 partial。 |
| 5 | `PASS（限定 case-accounting）` | analytic 6/6；medium 36 + gentle/sharp 2 均实跑，并对每个非完成 case 给出 capability/domain 终止；没有 numerical failure 伪装。该项不等于 100 mm 或趋势通过。 |
| 6 | `PASS（validation-only 范围）` | canonical bundle 可回读，8 recipes/16 figures 可由 ResultReader-only 重建。 |
| 7 | `PASS` | traceability、validation、performance、acceptance 与机器 JSON 已生成，并区分 fixed/accepted/proposed/dev/validation 身份。 |
| 8 | `PASS` | 报告明确 `NOT_ASSESSED`、`NOT_CERTIFIABLE`、no-damage、strength unavailable 和 remaining risks。 |
| 9 | `PARTIAL` | full regression、lint、format、type、build、schema/import/demo 和本地 link checks 通过；capability-terminal replay slices 一致，但不存在 committed 100 mm campaign receipt 可做完整 replay。 |
| 10 | `PARTIAL` | 无 duplicate Pz、无竞争 schema、无 B/C 反向依赖，A→B force sign/action-reaction 已修正；deformed geometry、previous-active lineage、event/post 与 operation evidence 仍未系统闭合。 |
| 11 | `PASS（Git handoff）` | 本交付按精确 allowlist 暂存，并在提交前检查 cached diff；commit/push receipt 由最终交接回应给出。Git 交接不改变 §16 物理验收结论。 |
| 12 | `PASS` | M04、M05、M06 未开始。 |

由于 #4 为 `NOT_MET`，#3、#9、#10 为 `PARTIAL`，总体只能是 `NOT_ACCEPTED / BLOCKED_EVIDENCE_INCOMPLETE`。

## 阻断登记

| ID | 当前阻断 | 已有证据与关闭条件 |
|---|---|---|
| `M03-B01` | 退化候选 frozen-schema 不可表示 | 5/5 normal-bearing full candidates 已 receipt-backed 持久化并通过 rollback/idempotency/replay；`radial_normal_global=None` 无法填入 non-null `normal_global`，不得补造法向。需要新合同或兼容表示。 |
| `M03-B02` | 功/能量闭合失败 | signed trapezoidal actuator work 已独立计算，hard gate 会拒绝；真实平面 mismatch 18.65%。需修正力学/功一致性并闭合 return/released energy 与 step/event/LOD refinement。 |
| `M03-B03` | 最终变形几何和支持 lineage 不闭合 | candidate ID 已绑定 chart + 完整 receipt/evidence；需在 beam/mount 后重查询 deformed geometry 至收敛，并用事务所有、追加式的 continuation evidence store 承载 previous-active receipt lineage，无需改动冻结公共合同。 |
| `M03-B04` | Runtime event coverage 不完整 | 14 类本征 guards、standalone guards、strict pre/event/post gate 已有；需对适用的 32-kind registry 提供真实 M01-bound coverage 与 one-sided/post/cascade evidence。当前 campaign 在 geometry gate 已先终止，不能据此宣称事件矩阵通过。 |
| `M03-B05` | 100 mm、receipt 与趋势缺失 | 38 案已执行且分类完整；37 个 M01 refinement required、1 个 M03 geometry uncertain，仍是 0 个 100 mm、0 final M00 receipt、0 trend。需生成新的自适应 refinement receipts，并分离 current/co-minimal 与 nearby-switch probe quality；不能在失败 receipt 上补造 guard。 |
| `M03-B06` | 剩余 refinement/结构矩阵不完整 | 需补 rough/general LOD/event/work convergence、bent-centerline collision、full-kernel hard-stop 与完整 release-return lifecycle。 |
| `M03-B07` | Operation persistence 证据合同不完整 | operation row 仍可在声称 raw guard 由 event/trial 保留时保存 `raw_guard=null`，quality 也由 endpoint hard residual 间接推断；需保存直接 raw guard/quality lineage。 |

## 可以与不可宣称的范围

可以宣称：M03 软件实现和公共合同已形成；解析 suite 与 validation-only result/figure chain 通过；38 案均已执行并得到明确 capability termination；streaming 在该终止路径上有界，定向 replay/cold-warm/执行切片语义一致。

不可宣称：本征单刺完成 100 mm；功/能量闭合已通过；完整 contact/beam/mount/deformed geometry 和 32-event lifecycle 已验证；存在 `Rt,d,alpha,mu,ks` 真实趋势；能预测砖面损伤、针体强度、阵列承载或实验性能。

本次按用户明确授权执行精确暂存、commit 和 push；该 Git 交接只交付如实标记为 `NOT_ACCEPTED` 的 M03 实现与证据，不表示上述合取门已关闭。M04、M05、M06 不自动开始。

**最终判定：** `NOT_ACCEPTED / BLOCKED_EVIDENCE_INCOMPLETE`

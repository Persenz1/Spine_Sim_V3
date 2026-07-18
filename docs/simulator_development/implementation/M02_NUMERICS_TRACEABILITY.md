# M02 NUMERICS 实施与验收追踪

**任务：** `M02_NUMERICS_IMPLEMENTATION`
**冻结需求：** [`M02_NUMERICS_REQUIREMENTS 1.0.0`](../requirements/M02_NUMERICS_REQUIREMENTS.md)
**实施状态：** `IMPLEMENTED / SOFTWARE_ACCEPTANCE_PASSED`
**范围标签：** `DEV_POLICY / VALIDATION_ONLY / NOT_CERTIFIABLE`
**实验成熟度：** `experimentally_validated=BLOCKED_UNAVAILABLE`

M02 已实现数值编排、事件、事务、重放、M00 输出扩展和诊断合同。它只协调 physical owner 提供的残量、质量、signed guards、完整重组响应和有序意图，不实现 A/B 接触、摩擦、梁、弹簧、材料、损伤、针体或阵列载荷共享。mock/synthetic owner 是协议与规模 fixture，不是 A/B 物理实现。

## 验收快照

- 最终集成门为全仓 431 passed，其中 `tests/numerics` 238 passed、foundation+surface regression 193 passed；ruff、format-check、configured-strict mypy 与 package build 0.3.0 全部通过。
- 三档 M01 public compatibility panel 全部实际运行通过：4×5=20、64×5=320、256×5=1280 条完整 100 mm 路径，失败数均为 0。
- replay audit 对 2 cases/26 decisions 验证 exact BITWISE、semantic order invariance、M01 cold/warm 非语义差异和 backend/config/owner hash 结构化负例，`overall_pass=true`。
- 64/256/256/4000/16000 case plans 全部可 lazy iteration、暂停/恢复、分片合并和 replay；M02 cache 固定为 65,536 bytes，campaign retention 为 0。
- 16,000-case M00 bundle 本地生成并以 FULL Reader 回读：16,000 replay rows、63 isolated rejected diagnostics、7,626,762 bytes；生成 artifact 默认不追踪。
- canonical demo 本地生成并通过 MANIFEST/FULL 校验和 ResultReader 回读：20 个 M02 extension datasets 注册、1 个 receipt-backed accepted step、1 个 isolated rejected diagnostic、六类 recipe 的 15 个 query projections 均满足。

详细数值见 [验证报告](../../../reports/m02/M02_VALIDATION_REPORT.md)、[性能报告](../../../reports/m02/M02_PERFORMANCE_REPORT.md)和[验收报告](../../../reports/m02/M02_ACCEPTANCE_REPORT.md)；机器可读摘要为 [validation JSON](../../../reports/m02/M02_VALIDATION_SUMMARY.json) 与 [performance JSON](../../../reports/m02/M02_PERFORMANCE_REPORT.json)。

## 需求—实现—测试矩阵

| 冻结需求 | 实现 | 测试/可审计证据 | 状态 |
|---|---|---|---|
| §3–5 typed contracts、metadata、身份/单位/hash/state transition | `contracts.py`, `config.py` | `test_contracts.py`, `test_continuation.py` | PASS |
| §6 target/trial/accepted 隔离、步长、retry、predictor | `continuation.py` | `test_continuation.py`：h0/hmax/hmin、easy/hard、12 retry、event sub-hmin、无 history advance | PASS |
| §7 block residual、N/N·mm/mm/graph/NCP hard gates | `quality.py` | `test_quality_nonlinear.py`：raw/scaled gates、moment tolerance、strict graph/no penalty | PASS |
| §8 smooth/semismooth Newton、Armijo、derivative capability | `nonlinear.py` | `test_quality_nonlinear.py`：linear/nonlinear analytic roots、backtrack、FD validation gate、trust-region unavailable | PASS |
| §9–10 signed event、coverage、touch、Brent/bisection、最早性 | `events.py` | `test_events.py`：crossing/direction/touch/同号双根/no-certificate/B rebalance/order | PASS |
| §11 event/post、simultaneous DAG、cascade/Zeno、return sweep | `events.py` | `test_events.py`：完整重组 hashes、DAG/cycle、50 rounds、release→recontact、hold/unavailable | PASS |
| §12 trial/prepare/commit/rollback、receipt、幂等和故障注入 | `transaction.py`, `service.py` 及最小 M00 atomic extension hook | `test_transaction.py`, `test_service.py`, `test_extension_transaction_diagnostics.py` | PASS |
| §13 BITWISE/SEMANTIC replay、canonical order、字段级 diff | `replay.py` | `test_replay.py`, `run_m02_replay_validation.py`；2 cases/26 decisions audit | PASS |
| §14 三档 diagnostics、failure family、accepted/event/rejected 隔离 | `result_extension.py` 与 typed status/failure contracts | `test_result_extension.py`, writer fault/diagnostic tests；20 datasets/relations/metadata | PASS |
| §15 M01 public compatibility、footprint/LOD/cache 不变量 | `m01_compatibility.py` | `test_m01_compatibility.py`；20/320/1280 audit panels | PASS |
| §16 外部 streaming case-plan contract，不实现 M05 | `streaming.py` | `test_streaming.py`；64/256/256/4000/16000 实跑报告 | PASS |
| §17 六类 plot-data recipes，不绘图/不选 preset | `plot_recipes.py` | `test_plot_recipes.py`；canonical demo 的六类 Reader query | PASS |
| §18.1 解析残量/continuation/refinement/strict graph | core solver、`refinement.py` | `test_quality_nonlinear.py`, `test_continuation.py`, `test_refinement.py` | PASS |
| §18.2 crossing/touch/同号双根/B 曲线重平衡/再接触 | unified event engine | `test_events.py` structured positive/negative fixtures | PASS |
| §18.3 event/post 全重求、DAG/cycle、cascade/Zeno | event/cascade engine | callback count/response hash/state signature tests | PASS |
| §18.4 rollback/receipt/idempotency/fault injection | M02 coordinator + M00 writer adapter | evaluate/prepare/data/event/receipt/marker/rollback fault matrix | PASS |
| §18.5 order/cache invariance 与两级 replay | replay manifest/verifier | unit tests + replay audit 正/负例 | PASS |
| §18.6 20/320/1280 M01 panels 与 Rt/8→Rt/10 witness | validation-only M01 public adapter | 三份实际 panel audit；路径、query、event、cache、refinement checks | PASS |
| §18.7 M00 round trip、recipes、4000/16000 bounded streaming | result extension、demo、streaming writer/reader | FULL bundle readback、六 recipes、7,626,762-byte 16k bundle | PASS |
| §19 schema/API evolution 与 import boundaries | versioned contracts/extension | `test_import_boundaries.py`, `test_result_extension.py` | PASS |
| §20 deferred/forbidden capabilities | typed `UNSUPPORTED/UNAVAILABLE` paths | pseudo-arclength/trust-region/FD/release-path negative tests | PASS |
| §22 README、traceability、validation/performance/acceptance reports | 本 README、模块 README、reports | README registry-ID test、JSON parse、links/commands/diff checks | PASS |

`PASS` 表示冻结的软件语义由实现和证据覆盖；明确返回 `UNSUPPORTED/UNAVAILABLE` 的 deferred capability 也是合同规定的安全结果。它不表示 deferred backend 已实现，更不表示 A/B 物理或实验成熟度已通过。

## 可重放证据命令

从仓库根目录执行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
.venv/bin/mypy src/spine_sim scripts
.venv/bin/python -m build

.venv/bin/python -m spine_sim.numerics.demo_validation_only \
  build/M02_VALIDATION_ONLY.spine-result

.venv/bin/python scripts/run_m02_m01_compatibility.py \
  --panel smoke --output build/m02/M02_M01_SMOKE_4.json
.venv/bin/python scripts/run_m02_m01_compatibility.py \
  --panel standard --output build/m02/M02_M01_STANDARD_64.json
.venv/bin/python scripts/run_m02_m01_compatibility.py \
  --panel stress --output build/m02/M02_M01_STRESS_256.json

.venv/bin/python scripts/run_m02_replay_validation.py \
  --output build/m02/M02_REPLAY_VALIDATION.json
.venv/bin/python scripts/run_m02_streaming_validation.py \
  --output build/m02/M02_STREAMING_VALIDATION.json \
  --bundle-output build/m02/M02_STREAMING_VALIDATION.spine-result
```

`build/` 下 canonical/streaming bundles 与三份大型 panel audit JSON 都是可重建机器产物，不签入仓库。仓库内的两份小型 summary JSON 保存本次实际观测值、环境和解释边界。

## §18 实跑证据摘要

| 证据 | 结果 | 关键观测 |
|---|---|---|
| repository test gates | PASS | full 431；numerics 238；foundation+surface 193 |
| M02_M01_SMOKE_4 | PASS | 20 paths；180 queries；20 event probes；0 failures；0.413745 s |
| M02_M01_STANDARD_64 | PASS | 320 paths；2,880 queries；320 probes；0 failures；3.725565 s |
| M02_M01_STRESS_256 | PASS | 1,280 paths；11,520 queries；1,280 probes；0 failures；14.108047 s |
| deterministic replay | PASS | 2 cases；26 decisions；exact/order/cache positive cases与 4 类 structured mismatch gates |
| 4000 case plan | PASS | 19,831 steps；5,972 events；1 buffered case；65,536-byte M02 cache |
| 16000 case plan | PASS | 79,538 steps；23,954 events；1 buffered case；pause/replay/merge MATCHED |
| 16k M00 bundle | PASS | 16,000 replay rows；63 FULL failure diagnostics；FULL Reader；7,626,762 bytes |
| canonical demo | PASS | 34 datasets（20 M02）；1 receipt；2 events；six recipes / 15 queries |

wall time 与 RSS 是 2026-07-18 在报告所列本机上的观察值，不是跨平台 SLA；synthetic injected numerical failures 用来验证分类和 FULL retention，不是设计性能或物理不可行。

## 能力与成熟度边界

| 项目 | 关闭状态 |
|---|---|
| 单调标量 continuation、Newton 编排、signed events、transaction/replay | `SUPPORTED`，限 owner protocol 与已声明 capability |
| pseudo-arclength、多参数 continuation、完整 trust-region backend | `UNSUPPORTED`，按冻结需求延期 |
| production finite-difference generalized derivative | `UNSUPPORTED`；只允许 VALIDATION_ONLY/debug |
| A/B contact/friction/beam/spring/material/damage/array physics | `NOT_IMPLEMENTED_BY_M02` |
| M05 scheduler/ranker、binary success/composite score | `NOT_IMPLEMENTED` |
| M06 plotting preset/rendering | `NOT_IMPLEMENTED`；只交付只读 data recipes |
| source identity | `DEV_POLICY / VALIDATION_ONLY` |
| experimental maturity | `BLOCKED_UNAVAILABLE` |
| certification | `NOT_CERTIFIABLE` |

数值测试、随机地形兼容性、性能和 canonical bundle 都不能解除实验/认证阻断。后续 capability 必须由其 owner 模块和独立冻结需求激活。

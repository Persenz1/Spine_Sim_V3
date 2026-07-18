# M02 Numerics 验证报告

**需求基线：** [`M02_NUMERICS_REQUIREMENTS 1.0.0`](../../docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md)
**证据身份：** `DEV_POLICY / VALIDATION_ONLY`
**软件验证结论：** `PASS`
**实验成熟度：** `experimentally_validated=BLOCKED_UNAVAILABLE`
**认证结论：** `NOT_CERTIFIABLE`

本报告验证 M02 的数值编排、signed-event、event/post、事务、重放、M00 extension、M01 公共兼容性和流式负载合同。它没有实现或验证 A/B 接触、摩擦、梁、弹簧、材料、损伤、针体、阵列共享或设计承载；解析、mock 与 synthetic owner 不是 A/B 物理实现。逐项映射见 [M02 traceability](../../docs/simulator_development/implementation/M02_NUMERICS_TRACEABILITY.md)，机器可读摘要见 [M02_VALIDATION_SUMMARY.json](M02_VALIDATION_SUMMARY.json)。

## §18 数值与事件覆盖

最终集成门为全仓 `431 passed`：`tests/numerics` 238 passed，foundation+surface regression 193 passed。下列 M02 覆盖均包含在该结果中：

- 单调标量 continuation 的 h0=0.5 Lref、hmax=1.0 Lref、regular hmin=0.001 Lref、easy 两步 ×1.5、hard/retry ×0.5、12 retry、目标截断及 event localization 小于 regular hmin；
- target、trial、accepted point 严格分离，predictor/retry/probe/rollback 不推进 accepted history；
- N、N·mm、mm、dimensionless graph/NCP block 的 raw/scaled hard gates，总 merit 不能掩盖失败 hard block；
- smooth damped Newton、semismooth/generalized Newton、Armijo backtrack、linear/condition evidence、production finite-difference rejection和 trust-region typed unavailable；
- strict rigid/set-valued graph fixture，不引入 penalty stiffness；
- crossing、RISING/FALLING/EITHER、touch、同号端点双根、coverage unavailable、最早根与 simultaneous band；
- 每次 B validation probe 重求 nonlinear balance，故意错误的 A predictor 不决定根；
- event/post 完整重组、独立 simultaneous joint evaluation、dependency DAG/cycle、cascade round limit 和 Zeno；
- release→explicit return sweep→recontact 同号双根路径；无 return path 时 hold 或 unavailable，不自动回零/重挂/清历史；
- h/h2/h4 与 Rt/8→Rt/10 的固定精化门，失败门不被放宽。

这些 fixture 的 `PASS` 是数值软件证据。Newton converged 仍不等于 owner 的稳定、唯一或物理可行；Newton failed 也不等于 physical infeasible。

## 事务、输出隔离和故障矩阵

事务测试覆盖 evaluate、M02 prepare 前后、M00 data/event write、receipt、manifest/commit marker、ack 和 rollback 前后故障。验证结果为：

- prepare 无 publication；只有 M00 commit receipt 可以建立 accepted point/event/extension 可见性；
- parent/version/hash、registry/config、owner build、read/write set、external lock、DamageStore 与 persistence gates 都在 prepare 检查；
- same idempotency key + same candidate 返回原 receipt；different candidate 冲突；
- rollback 幂等，已 committed receipt 不可 rollback；rollback failure 可重试且不发布 staging；
- owner side-effect sentinel、state/event/receipt lineage 和 marker recovery 防止部分 accepted state；
- receipt-backed accepted/event/transaction 与 null-receipt rejected diagnostics 分区；event probe 不是 committed event；
- failure family 分开保留 numerical、owner-proven physical infeasible、contract、domain、transaction 与 independent capability unavailable axes。

M00 writer extension fault tests同时证明 competing receipt 被拒绝、unmarked orphan 不可见且 recovery 清理、rejected base 与 extension 作为一个 diagnostic group 发布。

## Canonical demo 与 ResultReader

实际执行：

```bash
.venv/bin/python -m spine_sim.numerics.demo_validation_only \
  /tmp/m02-evidence/M02_VALIDATION_ONLY.spine-result
```

本地快照结果：

| 项目 | 结果 |
|---|---:|
| bundle size | 1,675,441 bytes |
| registered datasets | 34 total / 20 M02 |
| MANIFEST integrity | 25 files / 1 marker / PASS |
| FULL integrity | 25 files / 1 marker / PASS |
| M00 receipts | 1 |
| receipt-backed accepted steps | 1 |
| lineage events | 2 |
| isolated rejected diagnostics | 1 |
| recipe requirement/query checks | 6 recipes / 15 query projections / PASS |
| local bundle semantic hash | `32169444e52b3069d52fb5101697a517e8479facbd66c14f9b90fc8ec422d0b8` |

accepted query 只返回非空 M00 receipt ref；rejected query 返回 `accepted_state_advanced=false` 与 `commit_receipt_id=null`。demo 还检查 extension→M00 point/event/trial/receipt relations、manifest/FULL semantic identity，并让残量、步长、事件 bracket、释放—再接触、精化误差、失败统计六类只读 recipe 的 15 个 projection 全部经 `ResultReader.query(...).read_all()` 得到非空结果；该路径不导入绘图库、不渲染图，M06 可直接按版本化字段与过滤合同解析。

快照在 dirty integration tree 上生成。bundle provenance 包含 Git commit/dirty 状态，因此最终提交后重建的 bundle semantic hash 应随 provenance 改变；这不是数值重放 mismatch。bundle 不签入仓库，以报告末尾命令重建。

## M01 公共兼容面板

三个面板通过独立进程顺序运行，均使用 M01 public footprint/query/materialization API；每个 scenario 有独立 SurfaceRealization，五类 geometry fixtures 共享该 scenario，路径长度均为 100 mm。

| Panel | 诊断策略 | scenarios × fixtures | paths | queries | event probes | materialization requests | failures | wall time | peak RSS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M02_M01_SMOKE_4 | FULL | 4 × 5 | 20 | 180 | 20 | 420 | 0 | 0.413745 s | 224,186,368 B |
| M02_M01_STANDARD_64 | STANDARD | 64 × 5 | 320 | 2,880 | 320 | 6,720 | 0 | 3.725565 s | 224,169,984 B |
| M02_M01_STRESS_256 | COMPACT + 32 STANDARD witnesses | 256 × 5 | 1,280 | 11,520 | 1,280 | 26,880 | 0 | 14.108047 s | 224,186,368 B |

面板进一步检查：

- SINGLE_SPINE、ARRAY_2X2_S4、ARRAY_2X6_S6、ARRAY_6X2_S6、ARRAY_6X6_S6 footprint 由 owner 完整 geometry envelope 与 M01 API 派生，不硬编码 10 mm；
- 100 mm 起终点 guard、lazy Rt/5→Rt/8→Rt/10、narrow/wide overlap、cold/warm、tile/query order 和 0.05/0.10 mm probe radius identity；
- Rt/8→Rt/10 event/support/normal/force/work/order 的冻结门；
- domain 负例原样保留 `M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN`，不 wrap、clamp、crop、rerandomize 或缩短路径；
- normal path 没有建立完整 150 mm Rt/10 dense array，materialization receipt/cache order 不进入 semantic result。

三份完整 audit JSON 分别为 580,838、7,958,605 和 16,117,269 bytes，属于本地可重建大型明细，不签入仓库。面板的 owner 明确标为 `M02_VALIDATION_ONLY_M01_COMPATIBILITY_OWNER`；其 scope 只是 geometry/cache compatibility。

## Deterministic replay

实际 replay audit 对 2 cases、26 decisions 返回 `overall_pass=true`：

| Case | 预期 |
|---|---|
| exact repeat / BITWISE | equivalent，0 diff |
| reversed case/owner order / SEMANTIC | equivalent，0 semantic diff |
| M01 cold/warm materialization / BITWISE | equivalent；4 个 cache receipt diagnostics 被明确忽略 |
| versioned numeric tolerance / SEMANTIC | equivalent |
| same numeric change / BITWISE | non-equivalent，字段级 diff |
| backend/profile change | non-equivalent，29 个结构化差异 |
| config hash change | non-equivalent，3 个结构化差异 |
| owner contract hash change | non-equivalent，1 个结构化差异 |

bitwise chain hash 为 `13c86cdc7f475515d05e30570a9fb8db8a75fdf0ec8df0f974e462a18833e451`；semantic chain hash 为 `ddda4bc9cc91b7725f8fcf9b08c1ea47ce1616f044c4ce87f6b51d6555d1e78b`。diff 是字段级报告，不以单一 bool 隐藏原因。

## 流式规模与 M00 round trip

64、256、256、4,000 和 16,000 case plans 均验证 lazy iteration、cursor serialization、暂停/恢复、shard merge 和 replay。4×1000 与 4×4000 使用跨 design 共享 terrain scenario IDs；它们是 base/extension alternatives，不是将 20,000 cases 解释为同一正式 campaign。

带 M00 bundle 的实际运行：

| 项目 | 结果 |
|---|---:|
| validation status | PASSED |
| total wall time | 6.839539 s |
| process peak RSS | 239,230,976 bytes |
| M02 cache min / max | 65,536 / 65,536 bytes |
| cache growth across campaign sizes | 0 bytes |
| retained campaign cases | 0 |
| plan-evaluation max buffered cases | 1 |
| configured per-case cache limit | 268,435,456 bytes |
| 16k replay rows read back | 16,000 |
| isolated FULL failure diagnostics | 63 |
| transaction batch / max buffered bytes | 256 / 655,184 |
| M00 bundle size | 7,626,762 bytes |
| FULL Reader round trip | PASSED |

63 个 failures 是按固定周期注入的 `NUMERICAL_FAILURE` fixtures，验证 failure 升级为 FULL、accepted state 不推进和 replay digest；`physical_feasibility=NOT_ASSESSED`。它们不是物理不可行、不是设计性能，也没有 replacement-seed/ranking 语义。完整资源数据见 [性能报告](M02_PERFORMANCE_REPORT.md)。

## 测试与重建命令

最终全仓门实际为 431 passed；numerics 238 passed，foundation+surface 193 passed；ruff、format-check、configured-strict mypy 和 build 0.3.0 均通过。固定命令为：

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

大型 panel JSON 和 bundles 均在 `build/m02/` 本地重建，不追踪。仓库保存的是小型机器摘要、Markdown 结论和生成代码。

## 成熟度与解释边界

- `experimentally_validated=BLOCKED_UNAVAILABLE`；
- certification = `NOT_CERTIFIABLE`；
- physical feasibility = `NOT_ASSESSED`，除非未来 physical owner 给出版本化 proof；
- source identity = `DEV_POLICY / VALIDATION_ONLY`；
- pseudo-arclength、多参数 continuation、完整 trust-region、production finite differences 仍为明确 deferred/unsupported；
- M05 scheduler/ranker、binary success/composite score 和 M06 visual preset/rendering 未实现；
- 本报告中的时间/RSS 是指定机器的单次本地回归观察，不是跨平台 SLA。

数值、兼容性与性能 `PASS` 不会提升任何 A/B/C 物理成熟度或实验认证状态。

# M02 Numerics 验收报告

**需求基线：** [`M02_NUMERICS_REQUIREMENTS 1.0.0 frozen`](../../docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md)
**技术范围结论：** `ACCEPTED`
**证据身份：** `DEV_POLICY / VALIDATION_ONLY`
**实验成熟度：** `experimentally_validated=BLOCKED_UNAVAILABLE`
**认证结论：** `NOT_CERTIFIABLE`

M02 在冻结的软件范围内通过验收：typed contracts、continuation、nonlinear orchestration、unified events、event/post cascade、M00 transaction、deterministic replay、20-dataset result extension、M01 compatibility panels、streaming plans 和六类只读 plot-data recipes 均有实现与证据。此 `ACCEPTED` 不包含 A/B 物理、不解除实验阻断，也不授权进入未冻结模块的实现。

## §22 完成判据

| 判据 | 证据 | 结论 |
|---|---|---|
| 1. public contracts/services 完成且无 A/B reverse dependency | `src/spine_sim/numerics/`；import-boundary tests；M01 compatibility harness 明确 validation-only | ACCEPTED |
| 2. §18 requirement-to-test 无漏项 | [M02 traceability](../../docs/simulator_development/implementation/M02_NUMERICS_TRACEABILITY.md)逐项映射 §18.1–18.7 | ACCEPTED |
| 3. analytic/event/B rebalance/event-post/rollback/refinement | 全仓 431 passed；numerics 238、foundation+surface 193；结构化正/负 fixtures | ACCEPTED |
| 4. M00 bundle/extension/receipt/Reader/replay | canonical demo MANIFEST/FULL；atomic extension fault matrix；replay audit | ACCEPTED |
| 5. M01 20/320/1280 panels | 三档实跑均 `overall_pass=true`；0 failures | ACCEPTED |
| 6. accepted/rejected/event/transaction 分离 | receipt-backed accepted/event；null-receipt rejected；Reader opt-in与relation tests | ACCEPTED |
| 7. bounded streaming/performance | 4k/16k pause/replay/merge MATCHED；65,536-byte fixed M02 cache；16k FULL bundle | ACCEPTED |
| 8. module README 输出概览 | [numerics README](../../src/spine_sim/numerics/README.md)列出消费者、20 datasets、索引、单位、metadata、Reader 例子、六 recipes | ACCEPTED |
| 9. traceability/validation/performance/acceptance reports | 本报告及同目录 Markdown/JSON evidence | ACCEPTED |
| 10. maturity/certification 不提升 | 全部报告明确 `BLOCKED_UNAVAILABLE / NOT_CERTIFIABLE`；synthetic/mock 非 A/B | ACCEPTED |
| 11. safe Git delivery | 本报告后由集成 owner 精确暂存、cached diff check、commit、push；不预写未产生 hash | RELEASE STEP |

第 11 项是仓库交付动作，不是软件语义。最终交付消息必须报告实际全仓门、commit 和 push；这些动作不应改写本报告的物理边界。

## 验收门

最终测试门：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q
431 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q tests/numerics
238 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q tests/foundation tests/surface
193 passed
```

提交前必须从仓库根目录重新执行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
.venv/bin/mypy src/spine_sim scripts
.venv/bin/python -m build
```

此外，ruff check、ruff format --check、configured-strict mypy 和 package build 0.3.0 均已通过。最终交付仍应在 commit 前确认同一命令退出码保持 0。

## Artifact 验收

| Artifact | 结果 |
|---|---|
| [M02_VALIDATION_REPORT.md](M02_VALIDATION_REPORT.md) / [JSON](M02_VALIDATION_SUMMARY.json) | §18 数值、事件、事务、replay、20/320/1280、canonical demo 全部有真实 evidence |
| [M02_PERFORMANCE_REPORT.md](M02_PERFORMANCE_REPORT.md) / [JSON](M02_PERFORMANCE_REPORT.json) | 4k/16k plan、bounded cache、M00 writer/reader round trip 与本机环境 |
| [M02 traceability](../../docs/simulator_development/implementation/M02_NUMERICS_TRACEABILITY.md) | 冻结行全部有 implementation/test/evidence，且均有关闭状态 |
| local canonical demo | 1,675,441-byte snapshot；MANIFEST/FULL PASS；34 datasets（20 M02）、1 receipt、2 events；六 recipes/15 queries |
| local 16k streaming bundle | 7,626,762 bytes；16,000 replay rows、63 FULL failure diagnostics；FULL Reader PASS |
| local panel audits | 580,838 / 7,958,605 / 16,117,269 bytes；分别覆盖 20/320/1280 paths |

大型 JSON 和 bundles 默认不追踪；仓库保存小型摘要和固定重建命令。canonical demo 的 Git provenance 会在最终 commit 后改变，因此 post-commit rebuild 的 bundle hash变化是预期行为。

## 功能判定

验收覆盖的 public software scope：

- MONOTONE_SCALAR_TARGET continuation 与冻结步长/retry 策略；
- raw/scaled residual hard gates、smooth/semismooth Newton、Armijo；
- dimensional signed guards、touch/certificate、earliest root、simultaneous/DAG/cascade/Zeno；
- event/post完整重组与 explicit return sweep；
- trial→prepare→atomic commit→receipt、rollback/idempotency/fault recovery；
- BITWISE/SEMANTIC replay 与字段级 mismatch；
- M00 20-dataset extension、relations、diagnostic retention/隔离；
- M01 five-fixture 100 mm compatibility panels；
- external caller 的 64/256/256/4000/16000 lazy plans；
- six read-only recipes；15 个 projection 均经 `ResultReader.query(...).read_all()` 非空回读，无 plotting dependency/preset。

以下明确 deferred 或属于其他 owner，因此安全的 `UNSUPPORTED/UNAVAILABLE/NOT_IMPLEMENTED` 是验收结论的一部分：

- pseudo-arclength、多参数 continuation、完整 trust-region、production finite-difference generalized Jacobian；
- A/B contact/friction/beam/spring/material/damage/needle/array physics；
- M05 scheduler/ranker、replacement policy、binary success/composite score；
- M06 rendering、颜色、字体、布局、正式 preset；
- target-surface acquisition、参数标定和实验认证。

## 性能判定

三档 compatibility panels 分别完成 20/320/1280 条 100 mm paths，wall time 0.413745/3.725565/14.108047 s，失败均为 0。streaming run 完成 4k 与 16k plans：

- plan evaluation 最多 1 buffered case，owner保留 0 campaign cases；
- M02 cache min=max=65,536 bytes，campaign-size growth=0；
- 4k/16k pause、replay、merge 均 MATCHED；
- 16k M00 transaction writer以 batch 256/655,184 bytes 上限写入；
- FULL Reader回读16,000 replay rows 和 63 isolated FULL diagnostics；
- bundle 7,626,762 bytes，总脚本 6.839539 s，process peak RSS 239,230,976 bytes。

这些数字证明 validation fixture 的可调度和 bounded cache，不是 production A/B 每 case 计算成本或跨平台 SLA。

## 物理与成熟度边界

- `experimentally_validated=BLOCKED_UNAVAILABLE`；
- certification = `NOT_CERTIFIABLE`；
- physical feasibility 默认 `NOT_ASSESSED`；
- mock/synthetic failure 不是 physical infeasible 或 design failure；
- compatibility panel 只证明 M01 geometry/cache/public API 协议；
- M02 不根据 residual 替 owner 选择物理 branch，不把 penalty 当 rigid physics，不从数值失败推断设计能力；
- M02 软件验收不得提升 A/B/C theory、parameter、material 或 experimental maturity。

## 关闭结论

M02 冻结技术范围 `ACCEPTED`，最终全仓门已通过。完成精确暂存、cached-diff 检查、提交和推送后应停止；下一步只能进入 M03 的独立需求讨论，不得从本报告自动开始 M03/M04/M05/M06 实现。

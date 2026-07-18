# M01 Surface 验收报告

**任务：** `M01_SURFACE_IMPLEMENTATION`
**冻结基线：** [`M01_SURFACE_REQUIREMENTS 1.0.0`](../../docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md)
**实施版本：** `spine-sim 0.2.0`
**验收判定：** `ACCEPTED`
**认证判定：** `NOT_CERTIFIABLE`

M01 在冻结边界内验收通过。这里的 `ACCEPTED` 只表示代码、数值验证、资源边界、canonical output 和文档满足 M01 实现窗口要求；它不表示真实表面已经实验验证，也不构成接触、摩擦、承载、材料失效或方案成功结论。

## 完成判据

| §18 判据 | 验收证据 | 判定 |
|---|---|---|
| 1. supported schema/provider/query/seed/tile/output/preview | typed contracts、analytic/synthetic evaluator、Philox replay、footprint/tile/cache、统一 query、M00 extension、两种 lazy preview 均有测试 | ACCEPTED |
| 2. measured/mesh 安全 unavailable | canonical demo 保存 `M01_MEASURED_IMPORT_DEFERRED` 与 `M01_EXTERNAL_MESH_IMPORT_DEFERRED`；两者 capability 均为 `UNAVAILABLE` | ACCEPTED |
| 3. §14 tests | 全量 `pytest` 178 passed；lint、format、strict typing 全通过 | ACCEPTED |
| 4. 三档 demo、图、bundle、报告、追踪 | 3 case、45/45 validation、六张由 1024² source grid 生成的 PNG、FULL Reader round trip、validation/performance/traceability artifacts 齐全 | ACCEPTED |
| 5. README 输出概览 | [`surface/README.md`](../../src/spine_sim/surface/README.md) 含 `## 输出概览`；测试把其中全部 `m01.*` ID 与冻结 registry 精确比对 | ACCEPTED |
| 6. 避免全域高分辨率正常路径 | demo 与 performance report 均为 `full_domain_rt10_dense_created=false`；narrow/wide overlap 为 0.0 mm | ACCEPTED |
| 7. 无越界语义或反向依赖 | AST/import tests 拒绝 future module/preview 反向依赖；pure-sphere record 的 forbidden contact-force count 为 0 | ACCEPTED |
| 8. 精确交付并停止 | 本报告之后只允许精确暂存、cached-diff 检查、提交和推送；不得自动开始 M02、M03 或 M06 | RELEASE STEP |

第 8 项是仓库交付动作，不预写尚未产生的 commit hash。其执行不会改变本报告所验收的技术内容；最终交付消息应报告实际 commit 与 push 结果。

## 质量门

验收时实际执行：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q
178 passed in 26.11s

.venv/bin/ruff check src tests scripts
All checks passed!

.venv/bin/ruff format --check src tests scripts
57 files already formatted

.venv/bin/mypy src/spine_sim scripts
Success: no issues found in 34 source files

.venv/bin/python -m build
Successfully built spine_sim-0.2.0.tar.gz and spine_sim-0.2.0-py3-none-any.whl
```

测试覆盖 contracts/provider、解析 family、不可微 feature set、Philox/golden replay、hierarchical Gaussian/PSD/Hermitian/real、synthetic unified query、footprint/LOD/tile/cache/corruption、complete sphere、validation-only mesh regression、M00 extension/Reader、preview、import boundaries、demo 和受控 performance fixture。

## Artifact 验收

| Artifact | 结果 |
|---|---|
| [`M01_VALIDATION_REPORT.md`](M01_VALIDATION_REPORT.md) | 45/45 canonical validation records 通过；完整数值和成熟度说明 |
| 本地 `M01_PERFORMANCE_REPORT.json` | `overall_pass=true`；13/13 checks true；64 MiB cache 受控；机器生成文件默认不追踪 |
| [`M01_SURFACE_TRACEABILITY.md`](../../docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md) | 所有冻结行有实现与测试/产物证据，无 `PLANNED` 项 |
| `build/M01_VALIDATION_ONLY.spine-result` | 23,441,100-byte canonical runtime artifact；FULL integrity PASS；可由固定命令重建 |
| 本地 `reports/m01/demo/` | gentle/medium/sharp 各 2D/3D PNG 及六份 plot manifest；默认不追踪 |
| package artifacts | `spine_sim-0.2.0.tar.gz` 与 `spine_sim-0.2.0-py3-none-any.whl` 构建成功 |

`build/`、`dist/`、机器可读性能 JSON、PNG 和 plot manifest 按仓库策略保持可重建且默认忽略；仓库只签入代码与 Markdown 文档，不依赖这些本地产物。

## 性能判定

当前机器快照记录总 fixture 0.377056108 s、256-point batch query 0.002523051 s、cache payload 286,848 bytes / 64 MiB budget、6 hits、7 misses、1 次 corruption regeneration。reported peak RSS 为 154,259,456 bytes。全部资源安全断言通过，包括：

- cache budget 64 MiB ≤ 512 MiB；
- resident payload 没有超过配置预算；
- 两种 footprint 的 Rt/5、Rt/8、Rt/10 均通过 bounded streaming 路径；
- cache corruption 被检测并确定性重建；
- normal path 没有创建完整 150 mm Rt/10 dense array。

这些时间值用于本机回归观察，不提升为跨平台实时性能承诺。

## 依赖与架构判定

foundation/base runtime 仍不依赖绘图库。为实现冻结的 M01 preview，原先“整个 `pyproject.toml` 不得出现 plotting package”的测试被精化为：base dependencies 明确拒绝 `matplotlib`/`plotly`，只有用户主动安装的 `preview` extra 声明 `matplotlib`。此外，import tests 证明 provider/query/writer/reader 的基础导入不会加载 plotting package，preview 通过 lazy import 隔离。

因此该测试演化保持了 M00 核心约束，同时准确容纳 M01 已冻结的 optional preview；详细说明见[追踪矩阵](../../docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md#optional-preview-依赖边界)。

## Deferred 与禁止提升

以下状态是验收结论的一部分，不是遗留错误：

- measured acquisition/import/query：`UNAVAILABLE / M01_MEASURED_IMPORT_DEFERRED`；
- arbitrary mesh/point-cloud production import/query：`UNAVAILABLE / M01_EXTERNAL_MESH_IMPORT_DEFERRED`；
- target-surface experimental maturity：`BLOCKED_UNAVAILABLE`；
- certification：`NOT_CERTIFIABLE` 或 availability record 上的 `CERTIFICATION_BLOCKED`；
- heightfield triangulation：只限 validation regression；
- synthetic tier：只能称 gentle/medium/sharp 与 `synthetic_unidentified`，不能映射为真实材料；
- contact、force、friction、cap/load、engagement、failure、success 与 M06 presentation：不属于 M01。

数值证据不能解除上述状态。任何未来能力激活都需要由其 owner 模块和独立需求窗口处理，不得静默改写本次 bundle 事实。

## 关闭结论

M01 技术范围 `ACCEPTED`。完成本次提交和推送后应停止，不继续实现 M02、M03 或 M06。

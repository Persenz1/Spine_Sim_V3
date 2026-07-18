# M01 SURFACE 实施与验收追踪

**任务：** `M01_SURFACE_IMPLEMENTATION`
**冻结需求：** [`M01_SURFACE_REQUIREMENTS 1.0.0`](../requirements/M01_SURFACE_REQUIREMENTS.md)
**实施状态：** `ACCEPTED`
**范围标签：** `DEV_POLICY / synthetic_unidentified / VALIDATION_ONLY / NOT_CERTIFIABLE`

M01 已实现冻结范围内的解析曲面、无材料身份合成随机场、统一纯几何查询、局部物化、M00 Result extension 和两种可选预览。验收对象不是材料模型、接触求解器或实验认证曲面；这些语义没有由本模块创建。

## 验收快照

- 完整 demo 在 150 mm × 150 mm logical parent 上生成 gentle、medium、sharp 三个共享 latent-noise identity、但 realization ID 各自独立的 case。
- canonical bundle 由 `ResultReader` 以 `FULL` 模式验证通过；45 条 validation record 全部通过，measured 和 arbitrary mesh 另有 2 条安全 unavailable 记录。
- 六张由 1024 × 1024 全域采样网格生成的 PNG 均已产出：三档各一张 `height_map_2d` 和一张 `oblique_3d_surface`。图只表达几何高度，不表达材料、接触、力、摩擦或成功判定。
- 受控性能 fixture 的 `overall_pass=true`；64 MiB cache 下 resident payload 为 286,848 bytes，且正常路径没有创建 150 mm 全域 Rt/10 dense array。
- 详细证据见 [`M01_VALIDATION_REPORT.md`](../../../reports/m01/M01_VALIDATION_REPORT.md)、[`M01_ACCEPTANCE_REPORT.md`](../../../reports/m01/M01_ACCEPTANCE_REPORT.md) 和机器可读的 [`M01_PERFORMANCE_REPORT.json`](../../../reports/m01/M01_PERFORMANCE_REPORT.json)。

## 需求—实现—测试矩阵

| 冻结需求 | 实现 | 验收测试/证据 | 状态 |
|---|---|---|---|
| §3、§5 strict source/spec/realization/query contracts 与 measured 能力门 | `src/spine_sim/surface/contracts.py`, `provider.py` | `tests/surface/test_contracts_provider.py`；demo unavailable records | PASS |
| §4 参数域、synthetic material label、150 mm parent、DEV 三档 | `contracts.py`, `synthetic.py`, `demo_validation_only.py` | `test_contracts_provider.py`, `test_synthetic.py`, 3-case full demo | PASS |
| §6 analytic family、光滑/不可微集合和 capability matrix | `analytic.py`, `query.py` | `test_analytic.py`, `test_query_geometry.py`；demo analytic fixtures | PASS |
| §7 Philox keyed profile、Box–Muller、latent identity 与 replay | `rng.py` | `test_rng_replay.py`；golden replay、seed/version identity tests | PASS |
| §5.3、§7 hierarchical Gaussian、PSD/variance/Hermitian/real、LOD nesting | `synthetic.py` | `test_synthetic.py`, `test_synthetic_query.py`；Parseval/real-construction records | PASS |
| §8 footprint、tile/halo、cache、corruption、boundary | `materialization.py` | `test_materialization.py`, `test_surface_performance.py`；性能报告 cache counters | PASS |
| §9 scalar/typed batch、height differential、neighborhood、SDF/closest | `query.py` | `test_query_geometry.py`, `test_synthetic_query.py` | PASS |
| §9.6 complete-sphere height envelope、generic clearance 和 co-support | `sphere.py` | `test_sphere_geometry.py`；50/100 µm 与 Rt/5-/8-/10 分级测试及 demo records | PASS |
| §6.3 validation-only heightfield triangulation adapter | `mesh_regression.py` | `test_mesh_regression.py`；`validation_only_heightfield_triangulation` record | PASS |
| §10 domain/quality/mask/reason code 分轴状态 | `contracts.py`, `query.py` | `test_contracts_provider.py`, `test_query_geometry.py`, `test_synthetic_query.py` | PASS |
| §11 M01 Result extension、metadata、relations、visualization arrays | `result_extension.py` | `test_result_extension.py`；canonical bundle FULL Reader round trip | PASS |
| §12 optional 2D/3D preview、low-pass、plot manifest | `surface/preview/` | `test_demo_preview.py`；[六张 demo 图](../../../reports/m01/demo/)及各自 plot manifest | PASS |
| §13 numerical/resource/performance limits | `materialization.py`, `scripts/run_m01_performance.py` | `test_surface_performance.py`, [`M01_PERFORMANCE_REPORT.json`](../../../reports/m01/M01_PERFORMANCE_REPORT.json) | PASS |
| §14 analytic/seed/tile/domain/schema/preview/full demo | `tests/surface/`, `demo_validation_only.py` | 45/45 validation records；六张由 1024² source grid 生成的 PNG；validation report | PASS |
| §15 compatibility/replay/version identity | public contracts、definition manifests、stable IDs | schema/API/replay tests；manifest-only 与 FULL Reader checks | PASS |
| §16 deferred/forbidden boundaries and no reverse imports | provider capability gates、validation-only mesh adapter、lazy preview | `test_import_boundaries.py`；两条固定 reason code | PASS |
| §18 README `## 输出概览` and top-level navigation | [`src/spine_sim/surface/README.md`](../../../src/spine_sim/surface/README.md)及顶层导航 | `test_result_extension.py` 自动比对 README ID 与 registry；docs link tests | PASS |

`PASS` 表示冻结语义已由实现和对应证据覆盖。measured/mesh 的 `UNAVAILABLE` 是冻结需求指定的安全结果，因此相关矩阵行通过；它不表示这些 production capability 已实现。

## 可重放证据命令

从仓库根目录执行：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
.venv/bin/mypy src/spine_sim scripts
.venv/bin/python -m build
.venv/bin/python -m spine_sim.surface.demo_validation_only build/M01_VALIDATION_ONLY.spine-result --preview-directory reports/m01/demo --grid-size 1024
.venv/bin/python scripts/run_m01_performance.py --report reports/m01/M01_PERFORMANCE_REPORT.json --preview-output build/M01_PERFORMANCE_HEIGHT_MAP.png
```

聚合测试数量不写入冻结追踪矩阵，避免增加测试后文档产生假性回退；最终提交门以全量命令退出码 0 为准。demo 的机器可读摘要位于生成目录的 `build/M01_DEMO_SUMMARY.json`，canonical bundle 位于 `build/M01_VALIDATION_ONLY.spine-result/`。

## Optional preview 依赖边界

M00 的 foundation 测试最初以“`pyproject.toml` 中完全不得出现 plotting package”保护核心运行时。M01 冻结需求明确允许隔离的 optional preview，因此该测试演化为解析 TOML 并分别检查：

1. `[project].dependencies` 仍不得包含 `matplotlib` 或 `plotly`；
2. 只有 `[project.optional-dependencies].preview` 可以声明 `matplotlib`；
3. 导入 provider/query/writer/reader 不会加载 `matplotlib`，surface evaluator 不反向导入 preview。

这次变化没有放松 foundation/base runtime 的无绘图依赖约束，只把 M01 明确允许的绘图能力放进用户主动安装的 extra；预览内部也保持 lazy import。

## 能力与成熟度边界

| 项目 | 关闭状态 |
|---|---|
| analytic 与 self-affine Gaussian synthetic | `SUPPORTED`，限纯几何/DEV 验证 |
| measured import/query | `UNAVAILABLE`，reason `M01_MEASURED_IMPORT_DEFERRED` |
| arbitrary mesh/point-cloud production import/query | `UNAVAILABLE`，reason `M01_EXTERNAL_MESH_IMPORT_DEFERRED` |
| heightfield triangulation | 只限 `VALIDATION_ONLY` regression，不是 production backend |
| source identity | `DEV_POLICY / synthetic_unidentified` 或 `VALIDATION_ONLY` |
| certification | `NOT_CERTIFIABLE`；availability 记录为 `CERTIFICATION_BLOCKED` |
| experimental maturity | `BLOCKED_UNAVAILABLE`，没有目标表面测量或实验可提升该状态 |
| contact/force/friction/material/failure/success | 不属于 M01，未实现、未输出、未推断 |

M01 到此关闭；后续不得从本状态自动扩张到 M02、M03 或 M06。

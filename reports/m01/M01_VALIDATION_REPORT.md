# M01 Surface 验证报告

**需求基线：** [`M01_SURFACE_REQUIREMENTS 1.0.0`](../../docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md)
**证据身份：** `VALIDATION_ONLY` / `DEV_POLICY synthetic_unidentified`
**验证结论：** `PASS`
**认证结论：** `NOT_CERTIFIABLE`
**实验成熟度：** `BLOCKED_UNAVAILABLE`

本报告验证 M01 的几何、随机场、物化、查询和输出合同。它不验证真实材料，不推断接触、摩擦、承载、失效、啮合角或“挂接成功”。需求到实现的逐项映射见 [`M01_SURFACE_TRACEABILITY.md`](../../docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md)。

## Canonical demo 结果

完整 demo 通过下列命令生成：

```bash
.venv/bin/python -m spine_sim.surface.demo_validation_only build/M01_VALIDATION_ONLY.spine-result --preview-directory reports/m01/demo --grid-size 1024
```

生成摘要：

| 项目 | 结果 |
|---|---:|
| logical parent / visualization window | 150 mm × 150 mm |
| visualization source grid | 1024 × 1024 |
| synthetic cases | 3（gentle / medium / sharp） |
| shared latent-noise identities | 1 |
| distinct surface realization IDs | 3 |
| canonical bundle | `build/M01_VALIDATION_ONLY.spine-result` |
| bundle size | 23,441,100 bytes |
| full integrity verification | PASS |
| Reader compatibility | `FULL_SCHEMA_SUPPORT` |
| elapsed time | 15.437006 s |
| validation records | 45 |
| passed / failed | 45 / 0 |
| full-domain Rt/10 dense array created | false |

canonical tables 的行数为：

| Dataset | Rows |
|---|---:|
| `m01.surface_realizations` | 3 |
| `m01.surface_provenance_steps` | 3 |
| `m01.surface_quality_bands` | 39 |
| `m01.surface_statistics` | 93 |
| `m01.surface_materialization_receipts` | 6 |
| `m01.surface_validation_results` | 45 |
| `m01.source_availability` | 2 |

三个 realization 使用同一个 `latent_noise_id`，同时各自持有不同的 `surface_realization_id`；因此参数档位比较保持 common-random-number 对应，而结果身份不混淆。三档标签均是形貌档位，不是材料名。

Reader 测试还验证了 M01 relations、manifest/FULL round trip，以及默认 catalog/query 不混入 validation/deferred diagnostics；只有显式请求 diagnostic/non-default 数据时才读取这些表。

## 数值与几何覆盖

45 条 bundle 内验证记录全部通过，覆盖以下证据族：

- 所有 supported analytic fixtures 的高度、梯度、法向和可用曲率；已知不可微 feature switch 保留 feature set，并把曲率明确标为 unavailable。
- self-affine Gaussian 三档的 coefficient Parseval/相对方差与 Hermitian 实值构造；`test_rng_replay.py` 与 `test_synthetic.py` 进一步证明 seed/generator/latent identity、serial/parallel bitwise replay、tile/query order、cache hit/miss 和 plot-before-query 均不改变 canonical 值。
- 100 mm 窄活动走廊与更宽 footprint 的重叠点一致性；三档观测到的最大高度差均为 0.0 mm。
- complete-sphere plane、slope、peak、pit、groove 和 multi-feature 纯几何；50 µm、100 µm probe 的 Rt/8—Rt/10 envelope/support/normal/topology 差异与 refine-before-certify gate 均通过。Rt/5、Rt/8、Rt/10 分级与 omitted-band/refinement 的完整组合由 sphere、synthetic 和 materialization 单元测试覆盖。
- `H_R` 与 `phi - R` 路径一致；输出中禁止 contact-force 字段的边界记录通过。
- validation-only heightfield triangulation regression 通过；该 adapter 没有成为 production query backend。

本报告没有把 coarse LOD 的阴性结果提升为接触证明，也没有让 visualization grid 成为 solver 的唯一几何。

## Footprint、LOD 与 cache

完整 demo 对 gentle、medium、sharp 分别使用同一对 footprint：一个沿 100 mm 路径的窄走廊和一个包含几何 offsets 的宽 footprint。每档均观测到：

- narrow/wide 重叠最大绝对误差为 0.0 mm；
- 首次 materialization 是 bounded tile miss，重复请求命中 memory cache；
- cache budget 为 512 MiB，单档 resident payload 为 58,880 bytes；
- `full_domain_rt10_dense_created=false`，正常路径没有构建全域高分辨率数组。

独立受控性能 fixture 进一步覆盖 Rt/5、Rt/8、Rt/10 两种 footprint 的六类请求、cache hit/miss、损坏检测与确定性重建。机器可读结果可按报告末尾命令在本地重建为 `M01_PERFORMANCE_REPORT.json`；该文件默认不追踪。

## Preview 证据

六张 PNG 都来自 1024 × 1024 的 150 mm 全域低通采样网格；PNG 的最终画布尺寸由 recipe 的 figure/DPI 决定。每张图都有相邻的 `.plot_manifest.json`，记录 recipe、source hash、低通方法、范围和不可认证状态。

| Tier | 2D height map | Oblique 3D surface |
|---|---|---|
| gentle | `demo/m01_gentle_2d.png` + manifest | `demo/m01_gentle_3d.png` + manifest |
| medium | `demo/m01_medium_2d.png` + manifest | `demo/m01_medium_3d.png` + manifest |
| sharp | `demo/m01_sharp_2d.png` + manifest | `demo/m01_sharp_3d.png` + manifest |

只注册了 `height_map_2d` 和 `oblique_3d_surface` 两种 recipe。测试同时证明非法的 contact-force heatmap 和真实材料标题会被拒绝，绘图前后 source hash 与查询结果不变。

## Performance 与资源快照

以下数值来自验收时本地生成的 `M01_PERFORMANCE_REPORT.json`，是指定机器上的可重放观察值，不是跨硬件实时 SLA；原始 JSON 默认不追踪：

| 指标 | 观测值 |
|---|---:|
| fixture/spec/realization | 0.003728916 s |
| six first tile requests | 0.080120466 s |
| six repeat cache hits | 0.001117157 s |
| corruption regeneration | 0.011129749 s |
| scalar query | 0.001842081 s |
| batch query, 256 points | 0.002523051 s |
| 128 × 128 visualization sample | 0.015988987 s |
| optional plot | 0.254509960 s |
| total fixture | 0.377056108 s |
| baseline RSS | 98,279,424 bytes |
| reported/resource peak RSS | 154,259,456 bytes |
| peak extra over baseline | 55,980,032 bytes |
| cache resident payload / budget | 286,848 / 67,108,864 bytes |
| cache hits / misses / regenerated | 6 / 7 / 1 |

报告中全部 13 项 checks 为 true，`overall_pass=true`。cache 配置为 64 MiB，低于冻结上限 512 MiB；payload 在预算内；corrupted entry 的状态为 `CORRUPTION_REGENERATED`；disk cache 未启用；正常路径仍未创建全域 Rt/10 dense array。

## Deferred source 与成熟度

`m01.source_availability` 保存两条明确记录：

| Request | Capability | Reason code | Certification |
|---|---|---|---|
| measured descriptor → realization/query | `UNAVAILABLE` | `M01_MEASURED_IMPORT_DEFERRED` | `CERTIFICATION_BLOCKED` |
| arbitrary mesh/point cloud → production import/query | `UNAVAILABLE` | `M01_EXTERNAL_MESH_IMPORT_DEFERRED` | `CERTIFICATION_BLOCKED` |

这两条记录是按冻结需求安全拒绝后的 PASS 证据，不是 production import 已完成。由于没有目标表面测量、校准链和实验数据，`experimentally_validated` 必须保持 `BLOCKED_UNAVAILABLE`；数值验证通过不能替代实验成熟度，synthetic realization 也不能提升为真实材料身份。

## 测试门快照

本报告生成时的仓库级验证结果：

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

最终关闭判定见 [`M01_ACCEPTANCE_REPORT.md`](M01_ACCEPTANCE_REPORT.md)。

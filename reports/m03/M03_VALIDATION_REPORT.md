# M03 SINGLE_SPINE 验证报告

**需求：** `M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 frozen`

**证据日期：** 2026-07-20

**验证结论：** `PARTIAL_EVIDENCE`

**总体验收：** `NOT_ACCEPTED / BLOCKED_EVIDENCE_INCOMPLETE`

**范围：** `DEV_PRIOR / synthetic_or_analytic_surface / no_damage / not_certifiable`

## 结论

M03 已交付 typed contracts、本征核、standalone 外层驱动、accepted A→B adapter、M00 result extension、解析 suite、38-case streaming runner、7 类 summary 与 8 类 Reader-only plot recipe。全仓 574 项测试、静态检查、类型检查和构建均通过。

最终 38-case 活动已全部执行并写出逐案结果，不再是 plan-only：36 个 medium、1 个 gentle、1 个 sharp 均以明确的非数值能力终止结束。其中 37 个为 `M01_RESOLUTION_REFINEMENT_REQUIRED`，1 个为 `M03_GEOMETRY_UNCERTAIN`；没有 numerical failure 被伪装成趋势值。初始 response 的原始 M01 reason 现在会在读取 tip guard 前保留，不再被次生的 event-coverage reason 遮蔽。但 0 个案例完成 100 mm、0 个具有 final M00 commit receipt、0 个可进入趋势，因此这轮执行满足“逐案明确终止”的审计要求，不满足 baseline 100 mm、真实趋势和 §16.8 性能门。

真实 loaded-plane witness 的独立功账本仍有 18.65% 闭合误差，并被 hard residual gate 正确拒绝。完整 deformed-geometry 重查询、previous-active receipt lineage、32 类 runtime one-sided event/post、退化 `normal=None` 候选 schema、returned-energy 生命周期及 rough/general refinement 仍未闭合。因此解析、schema、runner 和绘图证据不能提升为 M03 总体验收通过。

## 证据总览

| 证据 | 最终结果 | 能证明 | 不能证明 |
|---|---|---|---|
| 解析 suite | 6/6 cases、84/84 checks，`PASSED` | plane/slope/convex/concave/multi-peak/switch 的 M01 查询与 M03 几何适配 | 100 mm standalone、完整力学与实验真实性 |
| canonical validation bundle | MANIFEST/FULL 均通过；26 total / 12 M03 datasets；1 accepted、1 event、1 isolated rejected | M00 extension、隔离、回读、7 summaries、8 recipes | 完整 standalone/campaign accepted history |
| validation figures | 8 recipes，PNG+SVG 共 16 文件，0 data gaps | ResultReader-only 最小渲染路径 | M06 正式绘图或真实参数趋势 |
| 38-case plan | 36 primary + gentle/sharp 2；36 distinct bundles、12 interaction records、6 shared references | 冻结设计、去重、identity 与 cursor | 物理 outcome |
| 38-case execute | 38/38 逐案 outcome；全部明确 capability termination；0 numerical failure | §16.7/§20.5 所要求的非数值伪装终止分类 | 100 mm、canonical receipt、趋势、物理性能 |
| semantic slices | pause/resume、replay、独立 serial/parallel slices 与 cold/warm case 证据一致 | capability-terminal row 的确定性和可恢复编排 | committed 100 mm history 的重放 |
| loaded-plane work | 独立 signed quadrature；18.65% mismatch；hard reject | 符号、独立计算和质量门未放水 | 功/能量物理闭合 |

## 解析验证产物

命令：

```bash
.venv/bin/python scripts/run_m03_analytic_suite.py \
  --output build/m03/M03_ANALYTIC_SUITE.json
```

产物 [`M03_ANALYTIC_SUITE.json`](../../build/m03/M03_ANALYTIC_SUITE.json) 为 87,085 bytes，SHA-256 `88be8f67d246266d9e5fc3f5c202036fb7984d41b30a80e079ce082284d8a033`，suite ID 为 `m03_analytic_validation_suite:60a01df350e956b34fcce732a9750ab1a79ba2edf9679b29a3887d9858b83731`。

这些 fixture 全部为 `VALIDATION_ONLY`；其 6/6 通过只覆盖声明的解析几何与查询检查。

## Canonical bundle 与图证据

命令：

```bash
.venv/bin/python scripts/run_m03_validation.py \
  --bundle-output build/m03/M03_VALIDATION_ONLY.spine-result \
  --figure-output build/m03/validation_figures \
  --output build/m03/M03_VALIDATION_RUN.json \
  --formats png svg
```

最终产物：

| 项目 | 值 |
|---|---:|
| validation run JSON | 1,670 B；SHA-256 `bd1f1632a62ac267999b2a78e804ad90eb14b0032aaaefa3c54d4dec696b085b` |
| bundle directory | 1,748,393 B |
| bundle semantic hash | `ca29cc6278da732a14e3f7183cadc5457ff736f7b0d23415cf2362a853ac4106` |
| bundle manifest SHA-256 | `aa270a33a6fd50d5de19fa968b90af4d6d5fb85c0af20753cae6a3557f5a0c1a` |
| bundle build wall | 1.266883194 s |
| figure render wall | 2.255648565 s |
| total wall | 3.619386404 s |
| process peak RSS | 245,661,696 B |
| figure directory | 1,194,929 B |
| figure manifest internal hash | `832a6aa4b153e11f70b7a36430eb4bd7c5e2296609b29c98f485761f7729bc63` |
| figure manifest SHA-256 | `ff41d60c85bb2dd0318bda27e5a7334832f244ff1929a26f788a1656cf4c2ec7` |

[`M03_VALIDATION_ONLY.spine-result`](../../build/m03/M03_VALIDATION_ONLY.spine-result) 是最小 embedded analytic demo。它保存 12 个冻结 M03 datasets、7 个派生 summary 和 8 个 plot recipe，并由 M00 Reader 在 MANIFEST/FULL 模式回读。`parameter-trends` 图仍是 demo 数据，不是 38-case 物理趋势。

## 38-case 活动

命令：

```bash
.venv/bin/python scripts/run_m03_campaign.py \
  --plan-only \
  --output build/m03/M03_CAMPAIGN_PLAN_ONLY.json

.venv/bin/python scripts/run_m03_campaign.py \
  --execute \
  --output build/m03/M03_CAMPAIGN_RUN.json \
  --cursor-output build/m03/M03_CAMPAIGN_CURSOR.json
```

计划产物为 65,289 B，SHA-256 `975d992214fb781dd8c86b826acf6a62e81c4e33e71306d76a653fb5762463c0`。最终活动产物 [`M03_CAMPAIGN_RUN.json`](../../build/m03/M03_CAMPAIGN_RUN.json) 为 140,089 B，SHA-256 `425c7b95420c80cfe7269a89f19f0181d62b8e0eba71c5153851f63908db54dc`，campaign replay manifest ID 为 `m03_campaign_replay_manifest:078bcf4bde3ae5572d2d2cd67817b4543998f8ef14d8a949aaac65bcbf139c73`。

逐案终止分布：

| Surface role | 数量 | 100 mm 完成 | 最终 receipt | 趋势值 |
|---|---:|---:|---:|---:|
| PRIMARY_MEDIUM | 36 | 0 | 0 | 0 |
| GENTLE_SMOKE | 1 | 0 | 0 | 0 |
| SHARP_SMOKE | 1 | 0 | 0 | 0 |
| 合计 | 38 | 0 | 0 | 0 |

所有 38 行的 `terminal_status` 均为 `CAPABILITY_TERMINATION`，`failure_axis` 均为 `CAPABILITY_UNAVAILABLE`。37 行保留 M01 原始 `M01_RESOLUTION_REFINEMENT_REQUIRED`，另 1 行为 `M03_GEOMETRY_UNCERTAIN`。失败 query receipt 不足以签发 finite-cap raw guard；把 gap、gap-error 或 0 填进去都会伪造物理事件证据。活动文件里的 `completed_case_count=38` 表示 38 个执行请求都完成并形成结果行，不表示完成 100 mm；物理完成由 `execution_profile.completed_travel`、最终路径、remaining travel 和 canonical receipt 共同判定，本轮均为 false/null。

Runner 逐 case checkpoint，FULL history observed/allowed 为 1/1，未创建全域 dense grid。ordinal 0/1 的 pause/replay/resume、ordinal 2/3 的独立执行切片与同进程 cold/warm ordinal 0 均与最终整轮的 semantic case ID、case replay ID、execution profile、非易变 metrics 和 trend eligibility evidence 精确一致。这是 capability-terminal row 的 replay 证据；没有 committed 100 mm history 可供验证。

## 力、接触与功审计

Public wrench 已按 accepted A→B 约定保存为 contact-only `A_on_B`；每支持力、合力、反作用和 reference transport 一致。接触分支使用 objective slip，滑移分支验证严格 maximum-dissipation/SOC/normal feasibility，亚分辨率摩擦锥边界不再误提交滑移。

真实平面 `dz=-0.01 mm` 独立审计值：

| 量 | N·mm |
|---|---:|
| actuator input work | `4.32619527882e-5` |
| beam energy increment | `1.38051194592e-7` |
| spring energy increment | `3.32088486136e-5` |
| friction dissipation | `1.98339659972e-5` |
| closure error | `-9.91891301724e-6` |

normalized closure 为 `0.1865128`。该 trial 返回 `NUMERICAL_NONCONVERGENCE / NUMERICAL_FAILURE / REJECTED_TRIAL` 和 `M03_HARD_RESIDUAL_QUALITY_FAILED`；不会以 `OK`、`CONTINUABLE` 或 accepted point 混过去。较小的 validation-only demo increment 位于冻结 hard tolerance 内，只用于回读证据。

## 持久化、事件和剩余限制

Artifact-backed standalone publication 已在同一 M00 receipt 下保存 5/5 个 normal-bearing 候选，包括 non-active、local-minimum 和 empty-ball 证据，并覆盖 rollback、idempotent retry、rejected isolation 与 semantic replay。冻结 dataset 的 `normal_global` 不允许 null，因此 `radial_normal_global=None` 仍不可表示；实现必须继续显式报告，而不能补造法向。

Event publication 现在只允许非提交的 reduction probe；accepted adapter 会拒绝 failure、hard residual failure 和 `QUALITY_REJECTED`。Committed event 必须具有不同的 pre/event/post hashes、版本一致和 one-sided gate。真实本征 response 仍没有完整 one-sided proof，也没有覆盖全部 32 类路径，因此 campaign 在进入未经证明的 event path 前作能力终止是预期的诚实行为。

最终变形后的 tip/support geometry 尚未在 contact/beam/mount 解之后重新查询并迭代到一致；previous-active 所需的 feature/chart/point/query receipt lineage 也尚未由事务所有、追加式的 continuation evidence store 承载。operation row 的 `raw_guard`/quality 证据合同、return/released energy 累积、rough/general refinement、bent-centerline collision 与 full-kernel 4 mm hard-stop 也仍需关闭。

## 验证命令结果

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q`：574 passed in 107.61 s；其中 M03 134，lower-module 440。
- `.venv/bin/ruff check src tests scripts`：通过。
- `.venv/bin/ruff format --check src tests scripts`：132 files already formatted。
- `.venv/bin/mypy src/spine_sim scripts`：75 source files，无错误。
- `.venv/bin/python -m build`：wheel 与 sdist 构建成功。

机器可读汇总见 [`M03_VALIDATION_SUMMARY.json`](M03_VALIDATION_SUMMARY.json)，逐项门和 blocker 见 [`M03_ACCEPTANCE_REPORT.md`](M03_ACCEPTANCE_REPORT.md) 与 [M03 traceability](../../docs/simulator_development/implementation/M03_SINGLE_SPINE_TRACEABILITY.md)。

所有证据保持 `experimentally_validated=NOT_ASSESSED`、`NOT_CERTIFIABLE`。Damage/fracture energy 为 no-damage 下的 `NOT_APPLICABLE`；needle strength 为 `NEEDLE_STRENGTH_UNAVAILABLE`。M04、M05、M06 未开始。

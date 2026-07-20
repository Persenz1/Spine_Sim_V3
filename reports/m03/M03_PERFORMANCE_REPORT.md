# M03 SINGLE_SPINE 性能报告

**需求：** `M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 §16.8 / §20`

**证据日期：** 2026-07-20

**本机性能结论：** `EXECUTED_BOUNDED_BUT_BASELINE_INCOMPLETE`

**总体验收：** `NOT_ACCEPTED / BLOCKED_EVIDENCE_INCOMPLETE`

## 结论

最终 38-case runner 在本机 293.063 s 内完成全部执行请求并写出逐案 metric row，case-by-case streaming 的 FULL history observed/allowed 为 1/1，未创建全域 dense grid。逐案 wall 为 1.068–29.058 s，逐案 peak RSS 为 132.3–153.8 MB。pause/resume、replay、独立 serial/parallel slices 与 cold/warm 定向语义检查一致。

这些数字刻画的是早期 capability termination，而不是 100 mm 求解吞吐：38 个 case 全部在路径完成前终止，37 个为 `M01_RESOLUTION_REFINEMENT_REQUIRED`，1 个为 `M03_GEOMETRY_UNCERTAIN`；0 个 final M00 receipt、0 个趋势值。因此编排已可调度且内存有界，但冻结 §16.8 的“baseline 100 mm 必须可完成”仍失败，不能据约 7.7 s/case 外推完整路径成本。

## 环境与测量口径

| 项目 | 值 |
|---|---|
| OS | Linux 7.0.0-28-generic, x86_64 |
| Python | CPython 3.12.3 |
| CPU | AMD Ryzen AI 9 H 365，10 physical / 20 logical |
| memory | 32,711,241,728 B |
| base commit | `4e1239d0ddf1` |
| worktree | dirty integration tree |
| 口径 | local `DEV_POLICY / VALIDATION_ONLY` observation；不是跨平台 SLA |

RSS 为运行过程中采样到的进程峰值。case artifact size 是 transient FULL history 的 canonical JSON 大小；整轮只保留聚合 row，不同时保留全部 FULL histories。随机访问 spectral evaluator 没有 tile cache，因此 cache payload/hit/miss/regeneration 均为 0；这表示本次 surface backend 的适用事实，不表示缓存性能为零成本。

## 最终工作负载

| 工作负载 | 状态 | wall | peak RSS / artifact |
|---|---|---:|---:|
| analytic 6-case / 84-check suite | PASSED | 最终重建未独立采样 | 87,085 B JSON |
| canonical validation bundle | PASSED_WITHIN_DEMO_SCOPE | 1.266883 s | bundle 1,748,393 B |
| 8 recipes / 16 figure files | PASSED | 2.255649 s | figures 1,194,929 B |
| validation process total | PASSED | 3.619386 s | peak RSS 245,661,696 B |
| 38-case execute | 38 capability-terminal rows | 293.062942 s | aggregate JSON 140,089 B |

旧的 398 s 与 >190 s initial-pose 中止观察来自优化前/中间状态，不再代表最终 runner 的逐案可调度性，故不参与最终汇总。

## 38-case 资源汇总

命令：

```bash
.venv/bin/python scripts/run_m03_campaign.py \
  --execute \
  --output build/m03/M03_CAMPAIGN_RUN.json \
  --cursor-output build/m03/M03_CAMPAIGN_CURSOR.json
```

| Metric | Sum / overall | Min | Mean | Max |
|---|---:|---:|---:|---:|
| case wall time, s | 292.094030 | 1.068299 | 7.686685 | 29.057719 |
| peak RSS, B | — | 132,276,224 | 145,433,977 | 153,763,840 |
| transient FULL artifact, B | 157,254,765 | 3,829,201 | 4,138,283 | 15,233,981 |
| accepted count | 0 | 0 | 0 | 0 |
| trial count | 41 | 1 | 1.079 | 4 |
| committed event count | 0 | 0 | 0 | 0 |
| query count | 164 | 4 | 4.316 | 16 |

Runner outer wall 为 293.062942336 s。38 个 `semantic_case_result_id` 和 38 个 case replay IDs 均唯一。所有 case 都产生冻结的 16 个 metric 字段；终止分布是 38 个 `CAPABILITY_TERMINATION / CAPABILITY_UNAVAILABLE`，其中 37 个 `M01_RESOLUTION_REFINEMENT_REQUIRED`、1 个 `M03_GEOMETRY_UNCERTAIN`。初始 response 的原始 M01 failure axis/reason 会在读取物理 tip guard 前保留，不再被次生 reason 遮蔽。

[`M03_CAMPAIGN_RUN.json`](../../build/m03/M03_CAMPAIGN_RUN.json) 为 140,089 B，SHA-256 `425c7b95420c80cfe7269a89f19f0181d62b8e0eba71c5153851f63908db54dc`。campaign replay manifest ID 为 `m03_campaign_replay_manifest:078bcf4bde3ae5572d2d2cd67817b4543998f8ef14d8a949aaac65bcbf139c73`。

这里的 runner `completed_case_count=38` 是“38 个请求均形成终端 row”，不是“38 个 100 mm 完成”。所有 `completed_travel` 为 false、remaining travel 为 100 mm、final receipt 为 null、trend eligibility 为 false。

## Streaming 与确定性

最终 run 报告：

- checkpoint interval 为 1 case；
- maximum FULL histories observed/allowed 为 1/1；
- completed FULL history retained 为 0；
- 未创建 150×150 mm `Rt/10` dense grid；
- 38 案结束后 cursor 为 ordinal 38。

独立切片与整轮逐案结果对比：

| 检查 | Ordinal | 结果 |
|---|---:|---|
| pause → replay | 0 | semantic case ID、case replay ID、profile、非易变 metrics、trend evidence 精确一致 |
| resume | 1 | 同上 |
| 独立并行等价 slice | 2、3 | 同上；不据此宣称并行加速比 |
| same-process cold/warm | 0 | cold 7.385470757 s，warm 7.116122279 s；语义证据精确一致 |

该矩阵证明 capability-terminal rows 不因暂停、恢复、执行切片或 cache 温度改变语义。因为没有一条 committed 100 mm history，它不能替代完整路径 receipt replay。

## M01 查询性能修复

M01 closest/signed-distance 热点进行了等价调度优化：先把 frozen medium 5-probe/16-cell 微基准从 3.5456 s 降至 0.9208 s（约 3.85×），再通过 closest reuse、identity 和有界 cache 把同类 hot-path 观察降至约 0.33 s。Newton 投影点/残量 bitwise 相等，每个 query heap 的 lower bound/cell count 与 scalar reference 精确一致，response semantics 和 receipt ordering 保持不变。

这是本机微基准，不是跨硬件 SLA；它解释 runner 从“initial-pose 长时间无 row”恢复为可调度，但不关闭物理 100 mm、事件覆盖或功闭合门。

## Canonical/figure 资源

| 产物 | 大小 | SHA-256 / semantic hash |
|---|---:|---|
| `M03_ANALYTIC_SUITE.json` | 87,085 B | `88be8f67d246266d9e5fc3f5c202036fb7984d41b30a80e079ce082284d8a033` |
| `M03_CAMPAIGN_PLAN_ONLY.json` | 65,289 B | `975d992214fb781dd8c86b826acf6a62e81c4e33e71306d76a653fb5762463c0` |
| `M03_CAMPAIGN_RUN.json` | 140,089 B | `425c7b95420c80cfe7269a89f19f0181d62b8e0eba71c5153851f63908db54dc` |
| validation bundle | 1,748,393 B | semantic `ca29cc6278da732a14e3f7183cadc5457ff736f7b0d23415cf2362a853ac4106` |
| bundle manifest | 8,208 B | `aa270a33a6fd50d5de19fa968b90af4d6d5fb85c0af20753cae6a3557f5a0c1a` |
| validation figures | 1,194,929 B | manifest internal `832a6aa4b153e11f70b7a36430eb4bd7c5e2296609b29c98f485761f7729bc63` |

## §16.8 判定

| 条款 | 状态 | 证据/原因 |
|---|---|---|
| case-by-case streaming | PASS | 38 案逐案 checkpoint；FULL history 1/1 |
| 避免全域 dense grid | PASS | run 明确 `full_domain_dense_grid_created=false` |
| per-case metrics | PASS | 38 行均包含 16 个冻结 metrics |
| pause/resume/replay | PARTIAL | capability-terminal slices 精确一致；没有 committed 100 mm history |
| bounded scheduling | PASS（当前终止路径） | 38 案完成执行，RSS 有界；不外推完整路径 |
| baseline 100 mm | NOT_MET | 0/38 完成 100 mm，冻结条款明确该项失败即验收失败 |

因此性能执行不再是“campaign 未运行”，但 §16.8 整体仍为 `NOT_MET`。

机器可读版本见 [`M03_PERFORMANCE_REPORT.json`](M03_PERFORMANCE_REPORT.json)。所有数字均为合成/解析开发证据，`experimentally_validated=NOT_ASSESSED`、`NOT_CERTIFIABLE`；damage/strength capability 仍 unavailable，M04–M06 未开始。

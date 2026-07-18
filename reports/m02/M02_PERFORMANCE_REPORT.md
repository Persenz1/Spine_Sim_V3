# M02 Numerics 性能与规模报告

**需求基线：** M02 frozen §15.4、§16、§18.6、§18.7
**本机验证结论：** `PASS`
**证据身份：** `VALIDATION_ONLY`
**实验成熟度：** `experimentally_validated=BLOCKED_UNAVAILABLE`
**认证结论：** `NOT_CERTIFIABLE`

本报告记录 2026-07-18 的单机观察值，用于回归与 bounded-memory 证据，不是实时要求或跨平台 SLA。机器可读原始摘要见 [M02_PERFORMANCE_REPORT.json](M02_PERFORMANCE_REPORT.json)。所有 workload 使用 M01 compatibility mock 或 cheap deterministic synthetic owner；没有运行 A/B 物理。

## 环境

| 项目 | 值 |
|---|---|
| OS | Linux 7.0.0-28-generic, glibc 2.39 |
| machine / processor | x86_64 / x86_64 |
| Python | CPython 3.12.3 |
| physical / logical CPU | 10 / 20 |
| physical memory | 32,711,241,728 bytes |
| streaming backend | `M02_CHEAP_DETERMINISTIC_SYNTHETIC_OWNER` |
| synthetic owner threads | 1 |
| canonical reduction | `UINT256_SUM_XOR_AND_INTEGER_COUNTERS` |

面板各自在独立 Python 进程中顺序运行；streaming 指标来自一次同时写 16k M00 bundle 并 FULL 读回的进程。RSS 是脚本记录的 process/resource peak，包含 Python、NumPy、PyArrow 与导入成本。

## M01 compatibility panels

| Panel | paths | steps | queries | probes | materializations | cache hit/miss | failures | wall time | peak RSS | audit JSON |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SMOKE_4 | 20 | 60 | 180 | 20 | 420 | 240 / 180 | 0 | 0.413745 s | 224,186,368 B | 580,838 B |
| STANDARD_64 | 320 | 960 | 2,880 | 320 | 6,720 | 3,840 / 2,880 | 0 | 3.725565 s | 224,169,984 B | 7,958,605 B |
| STRESS_256 | 1,280 | 3,840 | 11,520 | 1,280 | 26,880 | 15,360 / 11,520 | 0 | 14.108047 s | 224,186,368 B | 16,117,269 B |

每条路径完整 100 mm。SMOKE 使用 FULL，STANDARD 使用 STANDARD，STRESS 使用 COMPACT 并固定 32 scenarios ×5 fixtures 的 STANDARD witness；失败会自动升级 FULL。三档均 `overall_pass=true`。

每个 panel 的 M01 validation cache 最大 resident payload 为 1,040 bytes，normal path 的 `full_domain_rt10_dense_created=false`。这里的 cache 数字是 compatibility harness 的小型、discardable validation cache，不应和 M01 production materialization budget或进程 RSS混为一谈。audit JSON 保存逐路径审计，因此文件大小随 panel 增长；三份大型明细只按命令重建。

## 4000/16000 case streaming

带 16k M00 writer/reader round trip 的完整脚本总耗时 6.839539 s，process peak RSS 239,230,976 bytes。plan evaluation 的 M02 cache 在全部 campaign size 上固定为 65,536 bytes：

| Stage | designs × terrains | cases | steps | events | injected numerical failures | plan wall | replay wall | cursor bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SINGLE_SPINE_PRESCREEN | 16 × 4 | 64 | 332 | 93 | 0 | 0.001770 s | 0.001743 s | 741 |
| ARRAY_INITIAL_SCREEN | 64 × 4 | 256 | 1,267 | 378 | 0 | 0.007082 s | 0.007115 s | 747 |
| ARRAY_FINE_SCREEN | 16 × 16 | 256 | 1,250 | 371 | 4 | 0.007056 s | 0.006965 s | 749 |
| FINAL_COMPARE_1000 | 4 × 1,000 | 4,000 | 19,831 | 5,972 | 14 | 0.135179 s | 0.108095 s | 767 |
| FINAL_EXTENSION_4000 | 4 × 4,000 | 16,000 | 79,538 | 23,954 | 63 | 0.417747 s | 0.418789 s | 778 |

每个 plan 的 pause/resume、replay 和 shard merge 均为 `MATCHED`；evaluation 最多持有 1 个 case，owner 保留 0 个 campaign cases，cache growth 为 0。配置的 per-case 上限为 268,435,456 bytes，观测 M02 cache 为上限的 1/4096。

4×1000 与 4×4000 是共享 terrain scenario IDs 的 base 与 extension alternatives；4,000 个 extension scenarios 保留前 1,000 个 identity。64→128→256→512→1000→4000 checkpoints 由 plan metadata 表达。该服务没有创建 production scheduler/ranker，也没有生成 binary success 或 composite score。

## M00 bundle 成本与隔离

streaming run 对 16,000-case extension 写入一个本地 M00 canonical bundle：

| 指标 | 观测值 |
|---|---:|
| transaction batch size | 256 |
| max transaction-buffered cases | 256 |
| max transaction-buffered bytes | 655,184 |
| replay rows | 16,000 |
| FULL rejected diagnostics | 63 |
| bundle size | 7,626,762 bytes |
| bundle semantic hash | `98c53b9283debcffa9bcdffb3d9afe01d25783d26279857126a1b87f11dd908c` |
| Reader query result hash | `b8a6821ba4a30199fd51327197808250c49cacf755496eac4ebe01bb8bda54f9` |
| FULL round trip | PASSED |

`max transaction-buffered cases=256` 是固定 flush batch；`max plan-evaluation buffered cases=1` 是 lazy case iterator。两者属于不同层，不矛盾。Reader 检查 case/ordinal coverage、semantic digest、diagnostic levels、63 个 failure rows 与 rejected-state isolation。

输出大小只针对本地 evidence bundle；production A/B records 的列数、事件密度和诊断分布尚不存在，不能由该数值外推。M01 cache 在 streaming fixture 中为 0，因为 cheap owner 故意不查询 M01；M01 integration cache 由前述 20/320/1280 panels 单独覆盖。

## 失败与成本分轴

ARRAY_FINE/4000/16000 中的 4/14/63 个失败由固定 validation period 确定性注入：

- failure family 为 `NUMERICAL_FAILURE`；
- `physical_feasibility=NOT_ASSESSED`；
- 失败自动保存 FULL diagnostics；
- 不生成 replacement seed，不将失败计入设计能力；
- raw response、secondary metric、runtime cost 与 diagnostic cost 保持独立轴。

因此 failure retention 通过不等于某个设计失败，更不等于 owner-proven `PHYSICAL_INFEASIBLE`。

## 可重建命令

```bash
.venv/bin/python scripts/run_m02_m01_compatibility.py \
  --panel smoke --output build/m02/M02_M01_SMOKE_4.json
.venv/bin/python scripts/run_m02_m01_compatibility.py \
  --panel standard --output build/m02/M02_M01_STANDARD_64.json
.venv/bin/python scripts/run_m02_m01_compatibility.py \
  --panel stress --output build/m02/M02_M01_STRESS_256.json

.venv/bin/python scripts/run_m02_streaming_validation.py \
  --output build/m02/M02_STREAMING_VALIDATION.json \
  --bundle-output build/m02/M02_STREAMING_VALIDATION.spine-result
```

`build/m02/` 的 panel audit JSON 和 streaming bundle 是大型可重建 artifacts，不签入仓库。若只需验证 plan/cache 而不写 bundle，可增加 `--no-m00-bundle`；但正式规模证据应保留一次带 bundle 的 FULL round trip。

## 判定

- 20/320/1280 M01 public compatibility panels：PASS；
- 4000/16000 lazy plan、pause/resume/replay/merge：PASS；
- M02 cache 固定、campaign retention 为零：PASS；
- 16k M00 writer/reader bounded batch round trip：PASS；
- cross-platform SLA：NOT CLAIMED；
- A/B physics performance：NOT ASSESSED；
- experimental validation：BLOCKED_UNAVAILABLE；
- certification：NOT_CERTIFIABLE。

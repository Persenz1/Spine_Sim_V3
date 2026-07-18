# M00 FOUNDATION 验收报告

**日期：** 2026-07-18
**冻结需求：** `M00_FOUNDATION_REQUIREMENTS 1.0.0`
**结论：** M00 软件范围验收通过
**解释标签：** `VALIDATION_ONLY / no_physics / not_certifiable`

## 检查结果

| 检查 | 实际结果 |
|---|---|
| Ruff | `All checks passed` |
| mypy strict | 16 个 source file，0 issue |
| 非性能 pytest | 70 passed，1 deselected，1.71 s |
| 性能 pytest | 1 passed，70 deselected，23.57 s |
| demo | 两个 accepted point、一个 committed event、一个 rejected trial、一个 summary、一个 extension、一个 Zarr v3 array；FULL integrity 通过 |
| package | wheel 构建成功；README 和 compatibility matrix 均包含在 wheel 中 |
| 文档/API/schema/link | registry ID、local link、公开 API signature、core metadata 完整性测试通过 |
| 架构边界 | 无 solver、surface、M01–M08 或 plotting 反向依赖 |

## 冻结性能夹具

环境为 20 logical CPU、32,714,612,736 bytes RAM、Linux x86_64、Python 3.12.3；依赖为 numpy 2.5.1、pyarrow 25.0.0、zarr 3.2.1、psutil 7.2.2。夹具包含 1,000 cases、1,009,000 accepted rows、事件、rejected diagnostic、逐实体子表和 chunked array。

| 指标 | 实测 | 门槛 | 结果 |
|---|---:|---:|---|
| writer | 24.407 s | ≤ 30 s | PASS |
| open + manifest catalog | 0.0813 s | ≤ 2 s | PASS |
| field catalog | 0.000216 s | ≤ 0.5 s | PASS |
| single case / 2 fields / 10,000 rows | 0.00339 s | ≤ 1 s | PASS |
| 8 float64 columns / 1,009,000 rows | 0.163 s | ≤ 5 s | PASS |
| 10 GiB logical chunk probe extra RSS | 8,441,856 bytes | ≤ 536,870,912 bytes | PASS |

原始精度指标、磁盘信息和逐项布尔检查可由验收命令在本地重建为 `M00_PERFORMANCE_REPORT.json`；机器生成 JSON 默认不追踪，也不以单一 pass 布尔值替代。

## 仍不可用或不适用

- 所有表面、接触、摩擦、梁、弹簧、阵列、损伤和 C 层物理；
- solver、物理事件定位、物理状态转换和物理认证；
- 数值物理验证与实验验证；
- M01–M08 模块实现及绘图配方；
- 远程对象存储、实时 UI、分布式 catalog 和跨不兼容 major 的自动迁移。

这些能力均不属于 M00 实现范围，没有被默认值、validation fixture 或 development prior 伪装成可用能力。

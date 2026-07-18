# M00 FOUNDATION 验收命令

**适用需求：** `M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen`
**解释边界：** 所有 demo、fault 和 performance fixture 均为 `VALIDATION_ONLY / no_physics / not_certifiable`。

## 干净环境

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

当前工作站带有与仓库无关的全局 pytest entry point，因此使用 pytest 官方环境开关禁止自动加载外部插件：

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -m 'not performance'
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -m performance
```

其余静态和运行检查：

```bash
.venv/bin/ruff check src tests scripts
.venv/bin/mypy src/spine_sim/foundation scripts/run_m00_performance.py
.venv/bin/python -m spine_sim.foundation.demo_validation_only build/M00_VALIDATION_ONLY.spine-result
.venv/bin/python scripts/run_m00_performance.py \
  build/M00_PERFORMANCE_FINAL.spine-result \
  --report reports/m00/M00_PERFORMANCE_REPORT.json
```

## 报告内容

性能报告记录硬件、OS、Python、关键依赖、磁盘/内存、fixture case/row 数、writer/open/catalog/single-case/八列扫描耗时，以及 10 GiB logical chunk stream 的额外 RSS。每个阈值单独给出结果，不用单一 pass 布尔值代替原始指标。

非性能测试覆盖 strict config、单位、ID/hash、来源/成熟度/多轴状态、registry、强类型 writer、reader、显式 join、array、lineage、plot gap、兼容/migration、replay、corruption 和五个事务故障点。架构测试检查 foundation/Reader 不反向导入未来物理、solver、surface 或 plotting package。

版本化验收摘要见 `reports/m00/M00_ACCEPTANCE_REPORT.md`；性能原始指标见 `reports/m00/M00_PERFORMANCE_REPORT.json`。

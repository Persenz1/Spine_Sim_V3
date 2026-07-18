# M00 FOUNDATION 实施与验收追踪

**任务：** `M00_FOUNDATION_IMPLEMENTATION`
**冻结需求：** `M00_FOUNDATION_REQUIREMENTS 1.0.0`
**实施状态：** completed / acceptance passed
**范围标签：** `VALIDATION_ONLY / DEV_POLICY / not_certifiable`

## 实施结果

1. 建立 Python 3.12 typed package `src/spine_sim/foundation`，实现无物理含义的公共值对象、严格配置、单位和内容身份。
2. 实现声明式 core/extension schema registry、字段元数据、relation catalog 与冻结快照。
3. 实现以 commit marker 为唯一可见性门槛的 per-case immutable shard、强类型 `ResultWriter`、恢复与完整性检查。
4. 实现只读 `ResultReader`、显式注册 join、lazy/batch 查询、array/lineage 和绘图数据缺口协议。
5. 实现 SemVer 兼容判定、只读 adapter、显式迁移 lineage 和 BITWISE/SEMANTIC replay 差异报告。
6. 完成 `VALIDATION_ONLY` demo、README 输出概览、旧 bundle fixture、五阶段故障注入、串并行不变性和冻结性能夹具。

## 需求—实现—测试矩阵

| 冻结需求 | 实际实现 | 验收证据 | 状态 |
|---|---|---|---|
| §3–4 严格配置、L0–L5、锁、覆盖、resolved config | `config.py`, `units.py` | `test_config.py`, `test_units_identity_models.py` | PASS |
| §5 SHA-256、UUIDv7、稳定内容身份、source hash | `canonical.py`, `models.py` | `test_units_identity_models.py`, demo lineage | PASS |
| §6 来源、四栏成熟度、多轴状态 | `models.py`, `registry.py` | `test_units_identity_models.py`, `test_registry.py` | PASS |
| §7 immutable/accepted/trial/event/transaction/output 边界 | `models.py`, `writer.py` | `test_transaction_faults.py`, `test_reader_bundle.py` | PASS |
| §8 JSON + Parquet + Zarr v3、per-case shard、完整性 | `storage.py`, `integrity.py`, `writer.py` | `test_reader_bundle.py`, demo full verify | PASS |
| §9 core schema、字段元数据、extension、relation、registry hash | `registry.py` | `test_registry.py`, registry snapshot | PASS |
| §10 强类型 ResultWriter、prepare/commit/rollback/幂等/恢复 | `writer.py` | `test_transaction_faults.py`, API signature check | PASS |
| §11 只读 ResultReader、catalog/query/series/events/array/lineage | `reader.py`, `plot_requirements.py` | `test_reader_bundle.py`, `test_docs_architecture.py` | PASS |
| §12 PATCH/MINOR/MAJOR、partial support、migration lineage | `evolution.py`, `schemas/compatibility_matrix.json` | `test_evolution_replay.py`, legacy fixture | PASS |
| §13 BITWISE/SEMANTIC replay、serial/parallel、layout invariance | `replay.py` | `test_evolution_replay.py`, `test_parallel_invariance.py` | PASS |
| §14 性能与资源边界 | `scripts/run_m00_performance.py` | `test_performance.py`, `reports/m00/M00_PERFORMANCE_REPORT.json` | PASS |
| §15.1–15.3 unit/schema/replay/fault/corruption | foundation package | 70 non-performance tests + 1 performance test | PASS |
| §15.4 最小无物理 bundle | `demo_validation_only.py` | generated/verified demo bundle and reader tests | PASS |
| §16 README `## 输出概览` 与引用校验 | `foundation/README.md` | registry-ID and local-link tests | PASS |
| §17 禁止物理/绘图/反向依赖 | package import boundary | AST import and dependency tests | PASS |
| §19 文档/API/schema/SYSTEM 外壳一致 | 本矩阵、验收报告、core registry | lint/type/schema/link/API/package checks | PASS |

## 验收解释边界

- M00 测试只证明基础软件合同被实现和运行；不提升任何 A/B/C 理论、数值或实验成熟度。
- demo、故障和性能 fixture 全部为 `VALIDATION_ONLY`，不得进入设计排名。
- `unavailable`、`unsupported`、`numerical_failure` 与 `physical_infeasible` 始终分轴保存，测试不作互相推断。
- M01–M08、求解器、物理事件定位、物理状态转换和绘图仍未实现；本任务没有自动开始 M01。

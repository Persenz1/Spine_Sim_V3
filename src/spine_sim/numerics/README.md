# M02 Numerics

M02 提供单调标量延拓、分块残量质量门、平滑/半光滑 Newton 编排、统一 signed event 定位、event/post 级联、M00 原子事务、确定性重放和诊断输出。物理 owner 提供残量、generalized derivative、guard、分支响应与有序意图；M02 不实现或改写 A/B 的接触、摩擦、梁、弹簧、材料、损伤或阵列载荷共享。

本模块当前身份为 `DEV_POLICY / VALIDATION_ONLY`。解析、mock 与 synthetic owner 证据只验证软件合同，`experimentally_validated=BLOCKED_UNAVAILABLE` 且 `NOT_CERTIFIABLE`。

## 输出概览

### 消费者与隔离规则

下游 M03/M04 physical owners 调用数值服务；M05 可流式提供 case plan；M06 和审计工具只能经 M00 `ResultReader` 读取版本化结果。accepted physical curves 只消费 receipt-backed accepted/event 行；trial、event probe、retry、line search 与 rollback 是 diagnostics，不能推进 accepted history、功、峰值或设计摘要。

COMPACT 保存 accepted 最终块摘要、committed event 最终 bracket、retry/failure 计数、receipt refs 和 semantic decision hashes；STANDARD 再保存 accepted 最终迭代、全部 probes/brackets、各 rejected retry 摘要与最终失败完整轨迹；FULL 保存所有 nonlinear/line-search/owner trial、临时 branch 与 transaction 细节。诊断级别只控制保留策略，不改变求解决策或 semantic hash。

### 20 个 M00 extension datasets

所有表都以 `run_id`、`case_id` 作为公共检索键；下表给出数据类、主键和主要关系索引。M02 只引用 M00 core point/event/trial/receipt identity，不创建竞争 ID。

| Dataset | 类别 | 主键 | 主要索引/关系 |
|---|---|---|---|
| `m02.continuation_targets` | index | `target_id` | case、parent accepted state、target coordinate |
| `m02.continuation_attempts` | rejected | `attempt_id` | target、trial、parent state、attempt/retry |
| `m02.accepted_step_numerics` | accepted | `numerics_record_id` | M00 point、receipt、event、replay step |
| `m02.residual_block_summaries` | accepted | `residual_summary_id` | point、receipt、iteration、block |
| `m02.iteration_traces` | accepted | `trace_id` | point、receipt、accepted iteration、block |
| `m02.rejected_iteration_traces` | rejected | `trace_id` | rejected trial、FULL nonlinear/line-search detail |
| `m02.event_channel_registrations` | index | `registration_id` | channel、owner、dependency/applicability |
| `m02.event_probes` | rejected | `probe_id` | channel、trial、event、coordinate |
| `m02.event_brackets` | event | `bracket_id` | committed event、receipt、left/root/right |
| `m02.rejected_event_brackets` | rejected | `bracket_id` | rejected trial、STANDARD/FULL bracket detail |
| `m02.event_earliestness_certificates` | rejected | `earliestness_certificate_id` | trial/event、selected channel、coverage |
| `m02.simultaneous_event_groups` | event | `simultaneous_group_id + event_id` | M00 event、point、receipt、dependency layer |
| `m02.event_dependencies` | event | `dependency_record_id` | predecessor/successor event、receipt |
| `m02.cascade_rounds` | event | `cascade_record_id` | cascade/event/point、round、receipt |
| `m02.rejected_trial_diagnostics` | rejected | `diagnostic_id` | M00 rejected trial、parent/last-valid state |
| `m02.transaction_trace` | transaction | `transaction_trace_id` | point/event/trial、prepare、receipt |
| `m02.replay_steps` | transaction | `replay_step_id + decision_index` | target/point/event/trial/receipt |
| `m02.failure_diagnostics` | rejected | `failure_diagnostic_id` | trial、family/reason/stage、last-valid state |
| `m02.refinement_studies` | summary | `study_id + sample_id` | point/event、step/LOD/root level |
| `m02.m01_compatibility_results` | summary | `compatibility_result_id` | panel/scenario/design/surface/footprint |

类别为 `rejected` 的表默认不可见，读取时必须显式设置 `include_diagnostics=True`；若其 source identity 不在默认集合中，还必须设置 `include_non_default=True`。非默认 transaction/summary 表同样要求 source opt-in。relations 负责把 extension 行连接到 M00 accepted point、committed event、rejected trial 和 commit receipt。

### 单位与 metadata

坐标和步长使用每条记录声明的 `coordinate_unit`；常规物理路径为 mm。raw residual/guard 使用 owner 声明的原生单位，字段 metadata 以 `declared_by_raw_unit` 或 `declared_by_raw_guard_unit` 表示，不允许跨 N、N·mm、mm、角度、能量或 graph/NCP block 混算。归一化量、hash、计数和布尔门为 `1`；精化摘要明确使用 N 与 N·mm；性能字段使用 s 和 byte。

每个字段注册 semantics、class、dtype/shape、unit、frame、reference point、indexing、status、source、maturity、sampling cadence 和 storage metadata。记录同时携带多轴 `status`、`source_identity`、`maturity` 与 `certification_status`；数值收敛不自动意味着物理稳定、唯一、可行或实验成熟。

### ResultReader 最小读取例

`DEV_POLICY` 数据需要显式 opt-in；下面只读取 receipt-backed accepted step，不读取 rejected diagnostics：

```python
from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.reader import FilterSpec, OrderSpec, ResultReader

reader = ResultReader.open(
    "build/M02_VALIDATION_ONLY.spine-result",
    verify_mode=VerifyMode.MANIFEST,
)
accepted = reader.query(
    "m02.accepted_step_numerics",
    fields=(
        "point_id",
        "commit_receipt_id",
        "accepted_point_index",
        "accepted_coordinate",
        "coordinate_unit",
        "accepted_step",
        "event_id",
    ),
    filters=(FilterSpec("commit_receipt_id", "!=", ""),),
    ordering=(OrderSpec("accepted_point_index"),),
    include_non_default=True,
).read_all()
print(accepted.to_pylist())
```

读取 rejected trial 时还必须传入 `include_diagnostics=True`。调用 `list_fields`、`describe_fields` 和 `list_relations` 可在查询前审计单位、source identity 与关系。

### 六类只读 plot-data recipes

`plot_recipes.py` 暴露六个版本化、只读的字段/过滤合同：残量迭代、步长、事件括区、释放—再接触链、精化误差和失败统计。每个 recipe 明确区分 physical、diagnostic overlay 与 validation query；physical query 不能消费 rejected rows。最小检查方式：

```python
from spine_sim.numerics.plot_recipes import m02_plot_recipes

for recipe in m02_plot_recipes():
    assert recipe.read_only
    assert reader.check_plot_requirements(recipe.requirements).satisfied
```

recipes 不导入 matplotlib/plotly，不渲染图，也不选择颜色、字体、版式或导出 preset；这些决策属于用户与 M06。字段缺口应形成版本化 plot-data gap request，由拥有数据语义的源模块处理。

# M00 FOUNDATION

本包实现 `M00_FOUNDATION_REQUIREMENTS 1.0.0` 的基础软件合同，不包含表面、接触、摩擦、梁、弹簧、阵列、损伤、C 层物理或绘图代码。所有首版结果仍须携带 `DEV_PRIOR / synthetic_surface / no_damage / not_certifiable`；本包自带示例严格标为 `VALIDATION_ONLY / no_physics / not_certifiable`。

实施权威入口为[冻结 M00 需求](../../../docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md)，理论权威边界从[理论导航](../../../theory/README.md)进入。

## 输出概览

M00 为 M01–M05 数据生产者提供强类型 `ResultWriter`，为 M06/M07 及其他离线消费者提供只读 `ResultReader`。canonical bundle 的核心 dataset 是：

- `core.accepted_points.common`：按 `run_id/case_id/accepted_point_index` 保存已提交点和 state/receipt lineage；
- `core.committed_events.events`：只保存已提交事件及 pre/event/post 引用；
- `core.rejected_trials.diagnostics`：与 accepted 数据物理隔离，必须显式 diagnostic opt-in；
- `core.summaries.case`：版本化摘要，普通摘要只允许消费 accepted point/committed event；
- `core.transactions.receipts`：原子发布和幂等重试证据；
- `validation_m00.arrays.sample_matrix`：demo 的 float64、validity/status 分离 Zarr v3 chunked array。

标量 ID 和状态字段使用单位 `1`、`frame/reference_point=NOT_APPLICABLE`；物理扩展字段必须显式声明 unit、frame 和 reference point，有向字段缺任一项均不能注册。`null` 只表示无值，原因由 `value_presence/capability_status/attempt_outcome/physical_feasibility/certification_status` 及 `reason_code` 分轴表达。`unavailable`、`unsupported`、`numerical_failure` 和 `physical_infeasible` 不互相推断。

最小 demo：

```bash
python -m spine_sim.foundation.demo_validation_only build/M00_VALIDATION_ONLY.spine-result
```

只读示例（demo 是 `VALIDATION_ONLY`，因此必须显式 opt-in）：

```python
from spine_sim.foundation import ResultReader

reader = ResultReader.open("build/M00_VALIDATION_ONLY.spine-result")
result = reader.query(
    "core.accepted_points.common",
    fields=("accepted_point_index", "accepted_state_id"),
    include_non_default=True,
)
print(result.read_all())
```

默认 catalog/query 不混入 rejected、`PROPOSED_SUPPLEMENT` 或 `VALIDATION_ONLY` 记录；diagnostic 和非默认来源必须分别显式启用。schema、record 和 run 均保留 requirement origin、runtime value provenance、authority refs、四栏成熟度及 certification。README 只作导航，machine-readable registry snapshot 才是字段权威。

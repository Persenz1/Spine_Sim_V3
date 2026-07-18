# M01 SURFACE

M01 把解析曲面和无材料身份的合成随机场封装为不可变、可重放的 `SurfaceRealization`，并提供高度/微分、邻域、最近特征、有符号距离和完整球纯几何查询。M01 不判断接触、摩擦、承载、材料失效或“挂接成功”。冻结范围见 [M01 需求](../../../docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md)，实施证据见 [追踪矩阵](../../../docs/simulator_development/implementation/M01_SURFACE_TRACEABILITY.md)。

## 输出概览

M03/A 是在线几何查询的主要消费者；M06 以后只通过 `ResultReader` 读取已经保存的 M01 字段。canonical bundle 默认只保存 compact realization manifest，不保存完整 150 mm 最细网格，也不保存每一个 transient query。

核心 dataset/array 为：

- `m01.surface_realizations`：spec、realization、seed/latent、generator、frame/domain、hash、质量、状态和四栏成熟度；
- `m01.surface_provenance_steps`、`m01.surface_quality_bands`、`m01.surface_statistics`：生成链、可信 q/波长带及带统计 scope 的 target/realized 证据；
- `m01.surface_materialization_receipts`、`m01.surface_validation_results`、`m01.source_availability`：tile/LOD/cache、VALIDATION_ONLY 指标和 measured/mesh deferred 诊断；
- `m01.visualization_height`、`m01.visualization_validity`、`m01.visualization_coordinates`：仅在显式选择时保存的可视化采样，不是 solver geometry。

表以 `run_id / case_id / surface_realization_id` 为主要索引（deferred source availability 没有 realization ID）；长度与高度为 mm，波数为 rad/mm，方向为 rad。几何量表达在 `M01_SURFACE_XY_HEIGHT_Z` frame、参考 `M01_LOGICAL_DOMAIN_ORIGIN`，名义墙面为 X–Y、外向为 +Z。每个查询另携带 realization/query identity、field-level capability/status、domain/quality、tolerance、residual/error bound、unit/frame/reference。

`measured` 与 production point-cloud/arbitrary-mesh 在 M01 只解析 schema，并以 `NULL + UNAVAILABLE + NOT_ATTEMPTED` 及 `M01_MEASURED_IMPORT_DEFERRED` / `M01_EXTERNAL_MESH_IMPORT_DEFERRED` 表达；域外、可信尺度不足、需要细化和近似失败也有独立 reason code，不会被解释为零高度、物理不可行或材料失败。

最小读取示例：

```python
from spine_sim.foundation import ResultReader

reader = ResultReader.open("build/M01_VALIDATION_ONLY.spine-result")
rows = reader.query(
    "m01.surface_realizations",
    fields=("case_id", "surface_realization_id", "family", "status"),
).read_all()
height = reader.open_array("m01.visualization_height", rows["case_id"][0].as_py()).read()
```

解析 fixture 使用 `VALIDATION_ONLY`；合成表面使用 `DEV_POLICY / synthetic_unidentified / not_certifiable`。`theory_defined`、`code_implemented`、`numerically_verified` 和 `experimentally_validated` 分栏保存；当前实验栏仍为 `BLOCKED_UNAVAILABLE`，任何 synthetic realization 都不可提升为真实材料或实验认证结果。

隔离的 optional preview 只提供 `height_map_2d` 与 `oblique_3d_surface`，安装方式为 `pip install 'spine-sim[preview]'`。不安装绘图库时，provider、query、writer 和 reader 仍可正常导入运行。

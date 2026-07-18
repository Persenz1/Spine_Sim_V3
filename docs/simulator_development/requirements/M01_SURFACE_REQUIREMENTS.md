# M01 SURFACE 冻结需求

**需求标识：** `M01_SURFACE_REQUIREMENTS`

**需求版本：** `1.0.0`

**状态：** `frozen`

**冻结日期：** `2026-07-18`

**适用实现：** M01 解析/合成表面提供者、几何查询、确定性物化和最小预览

**前置门：** `M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen`，M00 基础软件实现已通过验收

**后续窗口：** [M01 实现窗口提示词](../implementation_prompts/M01_SURFACE_IMPLEMENTATION_WINDOW_PROMPT.md)

## 1. 权威输入、目标和来源身份

### 1.1 实际读取的权威输入

本需求冻结前完整读取并核对了：

- [项目 README](../../../README.md) 与 [theory 阅读入口](../../../theory/README.md)；
- [仿真器开发入口](../README.md)、[模块规划](../SIMULATOR_MODULE_PLAN.md)与[需求讨论工作流](../REQUIREMENTS_DISCUSSION_WORKFLOW.md)；
- [M00 FOUNDATION 冻结需求 1.0.0](M00_FOUNDATION_REQUIREMENTS.md)；
- [证据复核入口](../../../theory/evidence_reassessment/README.md)与[工程固定上下文 1.0.0](../../../theory/evidence_reassessment/engineering_fixed_context.md)；
- [独立推导复核报告](../../../theory/review/DERIVATION_VERIFICATION_2026-07-17.md)；
- [开发期参数与标定政策](../../../theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)；
- [DEV_BOOTSTRAP_PROFILE 0.1.0](../../../theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml)；
- [A_INTEGRATED_MODEL 1.0.0](../../../theory/modules/A_INTEGRATED_MODEL.md)；
- [MECHANISM_DERIVATION_FORMAL 0.2.0-proposed](../../../theory/paper/MECHANISM_DERIVATION_FORMAL.md)中表面生成/采集、表面 realization、有限球尖、最近特征和验证相关内容。

权威顺序固定为：正式工程事实 > accepted system/A 的现行合同 > 本冻结 M01 软件服务合同。FORMAL 的 `SurfaceGenerationAndAcquisitionContract` 只形成 additive provenance、schema、质量和验证义务，身份为 `PROPOSED_SUPPLEMENT`；它不改写 accepted A 的 `SurfaceRealization`、有限球尖、接触或状态语义。

### 1.2 用户目标和第一版定位

M01 是给公式回归、事件构造和宽先验趋势筛选使用的确定性表面查询服务，不是独立的材料真实性模型。第一版：

- 支持解析表面和无材料身份的合成表面；
- 不读取白光轮廓仪或其他实测形貌；
- 不声称重建真实红砖、混凝土或任何指定材料；
- 用可重放 realization、按需查询和自适应局部细化避免保存完整高分辨率大域；
- 为后续 A/M03 提供几何证据，不返回接触、承载或方案结论；
- 提供一个最小预览器，使 M01 实现后能立即检查斜俯视 3D 地形和 2D 高度图；完整绘图系统仍属于 M06。

全部合成输出必须标记：

`DEV_PRIOR / synthetic_unidentified / not_certifiable`。

### 1.3 来源身份映射

| 身份 | M01 用途 |
|---|---|
| `FIXED_ENGINEERING` | N–mm–MPa 主单位、全局墙面坐标、150 × 150 mm 逻辑最大域、100 mm 最大拖动路径、针尖半径集合和 accepted A 的几何边界 |
| `ACCEPTED_AUTHORITY` | `SurfaceRealization` 不可变性、A1 查询质量/域状态、外正内负距离、完整球几何与支持集合、M00 身份/schema/status/ResultReader 合同 |
| `PROPOSED_SUPPLEMENT` | 共同 acquisition/generation provenance、PSD/可信带、实测预留字段、不确定带和针尖尺度覆盖记录；只能 additive |
| `DEV_POLICY` | self-affine Gaussian 宽先验、三档目标特征、生成/缓存/收敛策略、`not_certifiable` 和第一版能力门 |
| `VALIDATION_ONLY` | 已知解析解、最近特征切换、三角化回归、缺失掩膜和故障注入；不得作为材料或生产表面证据 |

参数所有权必须与来源身份分别保存。所有 runtime 值还必须保留 M00 要求的 `requirement_origin`、`value_provenance` 和具体 authority reference。

## 2. 范围、非目标、依赖和因果边界

### 2.1 M01 负责

- `analytic / synthetic / measured` 的共同 source schema、能力状态和迁移边界；
- 解析表面库和 self-affine Gaussian 合成表面；
- 不可变 `SurfaceSpec`、`SurfaceRealization`、查询句柄和 capability manifest；
- 高度、表面点、坡度、法向、可用时的曲率、邻域、域、质量、最近特征和有符号距离查询；
- complete-sphere 的纯几何包络/净空和候选支持集合，不解释为接触；
- 150 × 150 mm 逻辑域上的坐标锚定过程表面，以及按实验扫掠走廊生成的 lazy tile；
- realization/seed/generator/provenance/quality/statistics/query receipt 的 M00 扩展输出；
- 两种最小预览图和工程验证证据。

### 2.2 M01 不负责

- 实测仪器采集、点云/网格生产导入、材料真实性证明或红砖参数识别；
- 针尖球冠合法性、当前针轴、针体/锥段/安装座完整碰撞组合；
- Signorini 接触、摩擦、接触力、挂接成功、材料失效、承载或方案评分；
- 把表面坡度或法向命名为实际啮合角；
- 修改损伤后的表面、磨损、碎屑、切削或地形重网格化；
- M02 数值延拓、M03 单刺、M04 阵列、M05 实验调度或 M06 正式绘图配方；
- 用可视化网格替代查询 evaluator 或把缓存写入 accepted 物理历史。

因果链的边界为：

```text
M01 surface evidence
  -> M03/A geometric candidate and legal finite-tip support
  -> loaded contact
  -> frictionally stable
  -> load-bearing
  -> release/recontact
```

M01 只关闭第一项和 complete-sphere 的纯几何辅助。后续任何阶段 unavailable 时，不得回填为 M01 的布尔 `engaged/success`。

### 2.3 依赖方向

- M01 导入 M00 的配置、身份、status、registry、ResultWriter/Reader 公共协议；M00 不导入 M01。
- M03/A 只依赖 M01 公共查询协议，不解析其 generator、tile 或缓存内部对象。
- M01 预览器依赖 M01 公共采样接口；M01 evaluator 不依赖预览器或 M06。
- M06 以后只读 M00 ResultReader 中已保存的 M01 可视化样本；不得回调 surface evaluator 重新生成缺失数据。

## 3. 术语、坐标、单位和不可变身份

### 3.1 规范术语

| 对象 | 语义 |
|---|---|
| `SurfaceSourceDescriptor` | 描述 analytic/synthetic/measured 来源及其原始身份、坐标、处理链和能力，不保证能创建 realization |
| `SurfaceSpec` | 已规范化的 family、逻辑域、参数、generator/query contract 版本；参与 `surface_spec_id` |
| `LatentNoiseIdentity` | 与粗糙度滤波/缩放分离的标准化随机模态身份，用于 common random numbers |
| `SurfaceRealization` | 由 spec、seed、generator 版本和完整过程定义唯一确定的不可变表面函数 |
| `SurfaceQueryHandle` | 逻辑只读句柄；可持有可丢弃缓存，但不能改变 realization |
| `QueryFootprint` | 某次实验实际需要查询的扫掠包络和 guard，不改变表面本身 |
| `MaterializedTile` | 对同一 realization 的局部数值采样；是缓存/诊断，不是唯一几何定义 |
| `VisualizationSample` | 明确为绘图采样的规则网格；不能进入求解器几何路径 |

### 3.2 坐标、符号和单位

- 内部长度、高度、坐标、相关长度和针尖半径统一为 `mm`；角度为 `rad`；波数为 `rad/mm`；PSD 单位必须从采用的二维约定显式给出。
- 名义墙面为全局 `X–Y`，`+Z` 指向自由空间；高度场实体为 `z <= h(x,y)`。
- 欧氏有符号距离 `phi_omega(x)` 使用外正内负；表面为零集。
- source frame、surface frame、global frame 和 material-direction frame 必须以 M00 版本化 frame/transform ID 连接；不能只保存方向字符串。
- 材料主方向为 surface frame 中的单位向量或角度，并保存方向等价规则；各向同性时方向为 `NOT_APPLICABLE`。
- 法向为外法向。非光滑点必须返回全部共最小特征/法向或明确 unavailable，不得平均成伪法向。

### 3.3 三种互不混淆的域

1. `logical_parent_domain`：统一的 150 × 150 mm 表面坐标域；它是 realization 定义与 provenance 的一部分。
2. `active_query_footprint`：由针/阵列几何、100 mm 拖动路径和 guard 派生的实际计算走廊。
3. `materialized_tile_extent`：当前内存或可删缓存中已经采样的局部范围。

扩大活动窗口只能揭示同一 realization 的更多坐标。单刺窄走廊和阵列宽走廊的重叠部分必须相同；不得按裁剪窗口重新随机、去均值或归一化。

## 4. 参数表和所有权

### 4.1 公共与运行参数

| 名称 | 类型/单位 | 冻结默认或范围 | 所有权 | 来源身份 | 扫描 |
|---|---|---|---|---|---:|
| `surface_source_kind` | enum | `analytic / synthetic / measured` | DESIGN_VARIABLE | ACCEPTED_AUTHORITY | 是 |
| `surface_family` | enum | 第 6 节冻结 family；validation fixture 隔离 | DESIGN_VARIABLE | DEV_POLICY | 是 |
| `analytic_family_parameters` | typed record | 每 family 显式，无通用隐含值 | DESIGN_VARIABLE | DEV_POLICY | 是 |
| `logical_parent_domain_mm` | 2-vector | `[150, 150]` | FIXED_ENGINEERING | FIXED_ENGINEERING | 否 |
| `maximum_drag_path_mm` | length | `100` | FIXED_ENGINEERING | FIXED_ENGINEERING | 否 |
| `query_boundary_mode` | enum | 实验默认 `ERROR`; compatible regression 可显式 `PERIODIC` | NUMERICAL_CONFIGURATION | DEV_POLICY | 否 |
| `material_label` | string | synthetic 必须为 `synthetic_unidentified` | FIXED_ENGINEERING | DEV_POLICY | 否 |
| `active_query_footprint` | polygon/AABB | 运动扫掠包络 + guard 派生 | DESIGN_VARIABLE | FIXED_ENGINEERING | 随设计派生 |
| `footprint_guard_rule` | record/mm | probe、可信带、导数 halo、tile halo 的最大包络 | NUMERICAL_CONFIGURATION | DEV_POLICY | 否 |
| `source_frame_id/material_frame_id` | ID | 显式注册 | FIXED_ENGINEERING | ACCEPTED_AUTHORITY | 否 |
| `material_direction_rad` | angle/status | `0, pi/4, pi/2`；各向同性 N/A | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `target_feature_descriptor` | optional record/status | 档位或显式幅值/相关/方向目标；不含材料真实性声明 | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `surface_scale_reference_Rt_mm` | length | 显式；DEV 默认 `0.05`，不得随被测针尖自动改变 | DESIGN_VARIABLE | DEV_POLICY | 是 |
| `query_probe_radius_mm` | length | 由调用者提供；正式集合 `0.05, 0.10` | DESIGN_VARIABLE | FIXED_ENGINEERING | 是 |
| `preview_extent` | enum | `logical_domain / active_footprint / explicit_window` | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | 否 |
| `preview_grid_shape` | integer pair | 全域默认 `1024 × 1024`，可显式调低/调高 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | 否 |
| `tile_shape` | integer pair | 默认 `256 × 256`，含独立 halo | NUMERICAL_CONFIGURATION | DEV_POLICY | 否 |
| `memory_cache_budget_MiB` | positive | 默认 `512` | NUMERICAL_CONFIGURATION | DEV_POLICY | 否 |
| `persistent_tile_cache` | bool | 默认 `false`；启用时仍非 canonical、可删除 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | 否 |

`surface_scale_reference_Rt_mm` 只把 DEV profile 的无量纲宽先验物化为绝对 `Sq` 和 `lc`。比较 0.05/0.10 mm 针尖时必须保持同一个 surface realization，不能让针尖设计变化反向改变表面。

### 4.2 self-affine Gaussian 参数

| 名称 | 类型 | 冻结网格/默认 | 所有权 | 来源身份 | 扫描 |
|---|---|---|---|---|---:|
| `roughness_tier` | enum | `gentle / medium / sharp / explicit` | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `H` | dimensionless | `[0.5, 0.7, 0.9]`，基线 `0.7` | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `Sq_over_reference_Rt` | dimensionless | `[0.25, 1, 4]` | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `lc_over_reference_Rt` | dimensionless | `[5, 20, 80]` | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `anisotropy_ratio` | dimensionless | `[1, 2]` | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `anisotropy_direction_rad` | angle | `[0, pi/4, pi/2]`；ratio=1 时 N/A | DEV_PRIOR_UNCERTAINTY | DEV_POLICY | 是 |
| `root_seed/surface_seed_index` | integer | root 为显式 unsigned 128-bit；index 为 unsigned 64-bit；无隐含随机默认 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY | 是 |
| `q_min/q_max` | rad/mm | 从 parent domain 与声明最短波长显式派生并记录 | NUMERICAL_CONFIGURATION | DEV_POLICY | 收敛扫描 |
| `normalization_profile` | versioned enum | parent 定义零 DC、ensemble target Sq；禁止 realized crop normalization | NUMERICAL_CONFIGURATION | DEV_POLICY | 否 |
| `generator_id/version` | ID/SemVer | 强制显式并进入 realization identity | NUMERICAL_CONFIGURATION | ACCEPTED_AUTHORITY | 否 |

三档默认目标特征为：

| 档位 | `H` | `Sq/Rref` | `lc/Rref` | 解释边界 |
|---|---:|---:|---:|---|
| `gentle` | 0.9 | 0.25 | 80 | 相对平缓、长相关；不对应材料名称 |
| `medium` | 0.7 | 1 | 20 | 基线宽先验 |
| `sharp` | 0.5 | 4 | 5 | 相对尖锐、短相关；仍受 band limit |

档位用于快速生成接近目标宏观特征的三类输出；调用者可显式覆盖 H、Sq、lc、各向异性和方向。档位不是材料分类，也不使用单一 Ra 唯一决定三维表面。

### 4.3 分辨率参数和针尖尺度派生诊断

| 名称 | 冻结值/语义 | 所有权 | 来源身份 |
|---|---|---|---|
| `initial_delta_over_query_Rt` | `1/5` | NUMERICAL_CONFIGURATION | DEV_POLICY |
| `refinement_delta_over_query_Rt` | `1/8, 1/10` | NUMERICAL_CONFIGURATION | DEV_POLICY |
| `overview_resolution` | 只为可视化选择，不参与求解 | RUN_AND_PLOT_CONFIGURATION | DEV_POLICY |
| `lambda_min_declared_trust` | realization 声明的最短可信/表示波长 | DEV_PRIOR_UNCERTAINTY | PROPOSED_SUPPLEMENT |
| `tip_to_trusted_wavelength_ratio` | `Rt / lambda_min_declared_trust`，只记录不冒充真实性证明 | derived diagnostic | PROPOSED_SUPPLEMENT |
| `samples_per_trusted_wavelength` | `lambda_min_declared_trust / delta` | derived diagnostic | DEV_POLICY |
| `trusted_wavelengths_across_tip_diameter` | `2 Rt / lambda_min_declared_trust` | derived diagnostic | PROPOSED_SUPPLEMENT |

表中前三项为输入参数并遵守五类参数所有权；后三项是由 realization/query 计算的只读 diagnostic output，不是可覆盖参数。

对于 `Rt=0.05 mm`，三档局部采样间距分别为 0.010、0.00625、0.005 mm；对于 `Rt=0.10 mm`，分别为 0.020、0.0125、0.010 mm。它们是数值研究等级，不是实测分辨率声明。

## 5. source schema、能力门和 provenance

### 5.1 共同 schema

每个 `SurfaceSourceDescriptor` 至少具有：

```text
source_descriptor_id / schema_version / source_kind
source_identity / source_artifact_identity / raw_identity_sha256
source_frame_id / surface_frame_id / material_frame_id / transforms
canonical_unit_system / logical_domain / source_native_domain
material_label / material_direction / direction_equivalence
generator_or_acquisition_id / version
generation_or_processing_chain[]
boundary_manifest / quality_manifest / uncertainty_manifest
trusted_scale_or_wavenumber_bands[]
capability_status / attempt_outcome / reason_code
requirement_origin / value_provenance / authority_refs
four_column_maturity / certification_status
```

不存在的 raw artifact 必须使用 M00 的 `NOT_APPLICABLE` 状态，不能伪造 hash；未提供但未来可能有的字段使用 `NULL + UNAVAILABLE + NOT_ATTEMPTED + reason_code`，不能用空字符串、零或 NaN。

### 5.2 第一版能力矩阵

| source kind | schema | 创建 realization | 查询 | 第一版状态 |
|---|---:|---:|---:|---|
| `analytic` | 支持 | 支持 | 支持 | `SUPPORTED` |
| `synthetic` | 支持 | 支持 | 支持 | `SUPPORTED` |
| `measured` | 支持 | 禁止 | 禁止 | `UNAVAILABLE / M01_MEASURED_IMPORT_DEFERRED` |

`measured` descriptor 可以被严格解析、校验和报告缺项，但不得返回有效 `surface_realization_id` 或 query handle。source schema 的存在不表示已经支持实测导入或证明表面真实性。

### 5.3 synthetic 专用 provenance

必须保存：

- generator/algorithm ID、SemVer、代码 commit 和依赖版本；
- root seed、surface seed index、RNG profile、namespace、latent-noise ID；
- parent 周期域、公开边界模式、波数坐标与单位；
- FFT/谱系数归一化、零模、Hermitian 配对和实值构造规则；
- H、Sq、lc、各向异性、方向、q band 和 taper/roll-off；
- target PSD/方向谱/方差，以及 realized coefficient、audit sample 的回算统计与 scope；
- 方差 Parseval 误差、Hermitian/imaginary residual、tile/LOD 采样误差；
- realization definition hash 和实际物化 tile/sample receipts。

合成生成器使用二维 self-affine Gaussian 约定：在旋转后的各向异性波数坐标中，可信带内谱形满足版本化的

```text
q' = rotate(q, -theta)
l_parallel = lc * sqrt(anisotropy_ratio)
l_perpendicular = lc / sqrt(anisotropy_ratio)
q_eff^2 = (l_parallel * q'_parallel)^2
          + (l_perpendicular * q'_perpendicular)^2
C(q) = A * [1 + q_eff^2]^(-(1 + H)), q_min <= |q| <= q_max
```

方向 `theta` 是长相关轴，`lc` 是两主相关长度的几何平均。`q_min` 由 150 mm parent 基频和显式低频策略决定，`q_max = 2 pi / lambda_min_declared_trust`。`A` 使 ensemble variance 命中 target Sq；单个 realization 的 realized Sq 允许随机波动并必须回算报告，不能按活动窗口强制缩放。PSD 单位、离散积分、FFT 和卷积 normalization 必须写入 generator contract；不能依赖库默认。

不能对 150 mm parent 的最细采样格执行或保存一次全域 FFT。第一版生成器必须采用版本化的 hierarchical multiband spectral construction：

- 低频 band 可以在覆盖全 parent 的粗格上生成；
- 越高频的 band 使用越细的坐标锚定 lattice，只对活动 tile 加 halo 后用 overlap-save/overlap-add FFT convolution 或等价、经验证的 random-access spectral 算法物化；
- 每个 band 的 Gaussian driving noise 由 global lattice integer coordinate keyed，不由 tile-local seed 生成；
- 每个 band 的滤波器、kernel truncation、插值/导数规则、FFT normalization、Hermitian/real construction 和 truncation error bound 都进入 generator version；
- 所有 band 线性相加，因此输出仍是 Gaussian；target/realized PSD 必须证明 hierarchical synthesis 在声明 band 和误差内符合目标谱；
- 加密只启用新的高频 band；已有 band 的 lattice、noise 和值保持不变。

任何等价实现都必须同时通过 crop/order invariance、tile seam、target PSD、方差、Gaussian marginal、LOD nesting、内存上限和 error-bound 测试，不能以“未落盘”掩盖一次巨型全域数组或全域最细 FFT。

### 5.4 measured 预留字段

共同 schema 预留但第一版全部显式 unavailable：

```text
instrument_make_model / acquisition_principle / calibration_id
probe_geometry_or_tip_radius / MTF / SNR
native_point_spacing_x_y / native_sampling_layout
trusted_cutoff_by_direction / registration_error
detrend / interpolation / filtering / windowing steps
missing_data_mask / contamination_or_defect_labels
steep_slope_dropout / narrow_valley_access limitation
height_normal_position uncertainty bands
batch / location / track / material direction / holdout identity
raw point-cloud/grid/mesh artifact identities and byte hashes
```

未来 importer 必须保留原始 artifact、不可变处理 DAG 和每一步输入/输出 hash。插补值不能自动升级为真实形貌，原生点距不能自动等同物理可信分辨率。

## 6. 第一批表面族

### 6.1 analytic

第一版必须提供：

1. `plane`；
2. `slope_plane`；
3. `sinusoid_1d` 和可定向 `sinusoid_2d`；
4. `gaussian_bump`、`gaussian_pit`；
5. `multi_gaussian_feature`，能形成多峰和竞争支持；
6. `groove`，至少含 smooth/cosine、U 或 circular、V/piecewise-linear 变体；
7. `known_nearest_feature_switch`，构造已知面/边/顶点或多支持切换；
8. `spherical_cap_or_bowl`，仅作为 `VALIDATION_ONLY` 距离/曲率 fixture。

每个解析 family 必须声明参数域、光滑性、边界兼容性、exact/approximate/unavailable 能力和不可微集合。测试 fixture 的默认参数不得进入 DEV 物理扫描。

### 6.2 synthetic

第一版唯一随机 family 为 `self_affine_gaussian`。它是 band-limited、周期 parent domain 上定义、坐标锚定的 hierarchical multiband 过程表面。规则显示网格不是其唯一表示；同一 realization 的 continuous/band-limited evaluator、lazy tiles 和显式 visualization sampling 必须在各自声明 band 内一致。

### 6.3 三角网格边界

- 任意外部三角网格、点云和非单值表面生产导入第一版 `DEFERRED/UNAVAILABLE`。
- 第一版实现 `VALIDATION_ONLY` 的 `heightfield_triangulation_regression_adapter`：把解析高度场按显式分辨率三角化，使用三角形最近点/距离能力并验证向解析极限收敛。
- 该 adapter 不是新的生产 `source_kind`，不能让可视化网格成为求解器默认后端。
- 以后启用完整 mesh provider 时必须保持相同 `SurfaceQuery` envelope；若需要修改 accepted A 语义，必须先走 amendment，不得以 M01 schema minor 版本偷渡。

## 7. 随机种子、realization 和确定性

### 7.1 seed profile

第一版使用版本化的 counter/keyed RNG profile，而不是访问顺序敏感的顺序 RNG。默认 profile 冻结为 `M01_PHILOX4X64_10_KEYED_1`：使用 Philox-4x64-10。SHA-256 从以下 identity tuple 派生固定 128-bit key：

```text
root_seed
stream_namespace = "m01.surface"
surface_seed_index
latent_noise_namespace
frequency_band
component_or_pair_role
```

Philox counter 使用无碰撞的 canonical unsigned encoding 保存 global lattice/mode integer coordinates 和 block ordinal；signed coordinate 使用冻结的 zigzag encoding。这样可以批量生成 tile，而不需要按查询顺序推进 RNG 或为每个 sample 重新选择 key。key/counter 的字节序、字段宽度和越界拒绝都属于 profile。

uniform-to-normal 变换及 pair ordering 也必须有固定 `normal_transform_id/version`；默认使用版本化 Box–Muller pair mapping。同一 locked runtime/backend 要有 golden coefficient/sample fixture。绘图、tile ID、线程编号和查询顺序不得消耗或推进表面随机流。

### 7.2 common random numbers

- `latent_noise_id` 绑定标准化复谱噪声，不绑定 H/Sq/lc 滤波。
- 对设计趋势比较，可让不同 surface specs 共享 `latent_noise_id`，用同一潜在模态改变滤波/缩放；每个 spec/realization ID 仍不同。
- surface resolution refinement 保留全部已有低频模态，只增加确定性的高频模态；不得重新随机粗层。
- surface RNG namespace 与 M02/M05/plot RNG 完全分离。

### 7.3 身份和 hash

遵守 M00：

```text
surface_spec_id = hash(family, parent domain, normalized parameters,
                       generator/query contract versions)
seed_id = hash(RNG algorithm/version, namespace, original seed)
surface_realization_id = hash(surface_spec_id, seed_id,
                              latent_noise_id, generator version)
```

程序化表面的 `realization_definition_hash` 对完整函数定义负责；每个实际 tile/query/visualization sample 另有内容 hash、范围、dtype、shape 和 resolution receipt。generator 版本变化必须产生新 realization，不能用相同种子重解释旧 ID。cache 路径、命中状态、tile 访问顺序和绘图设置不进入 surface semantic identity。

### 7.4 replay 等级

- 同一锁定 runtime/backend/profile 内，manifest、谱系数身份、tile 值和 visualization sample 要求 bitwise replay。
- 不同硬件、并行度或被批准 backend 间至少要求 M00 `SEMANTIC_REPLAY`，并按字段容差报告差异。
- serial/parallel、不同 tile 顺序、不同 cache 命中和不同活动窗口必须得到相同重叠查询结果。

## 8. 逻辑大域、活动走廊和 lazy tile

### 8.1 活动走廊派生

实际查询范围为所有针尖及需要检查的针体几何沿运动路径的 swept envelope 并集，再加 guard：

```text
active_query_footprint = swept_geometry_envelope
                         dilated_by(max(probe radius,
                                        trusted-scale halo,
                                        derivative/search halo,
                                        tile halo,
                                        declared clearance guard))
```

单刺实验通常形成不超过约 10 mm 的窄走廊；该数值是预期资源形态，不是隐藏固定边界。阵列宽度从最外侧针/针体运动包络自动派生。起点和终点也必须加 guard。若请求 footprint 超出 150 × 150 mm 逻辑域，必须返回 `M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN`，不得静默扩大或缩短 100 mm 路径。

### 8.2 自适应分辨率

- 远离潜在接触区：不物化，或只使用明确标记的 overview/coarse bound；
- 扫掠前方：默认 `delta = Rt/5`；
- 可能支持、沟槽、多特征和事件区：细化到 `Rt/8`；
- 收敛敏感或代表性验收：细化到 `Rt/10`；
- 针离开后可以淘汰高分辨率 tile，需要时按 realization 原样重建。

粗层只有在携带对省略高频造成的高度、坡度或距离误差的保守界限时，才能证明“无潜在接触”。如果界限不能排除接触、体部碰撞或最近特征切换，必须先细化；不能靠粗网格直接推进后续物理。

### 8.3 tile、halo 和接缝

- tile 只采样 canonical coordinate-anchored field，不使用 tile-local seed。
- hierarchical band 的 driving noise 绑定 global lattice coordinate；tile 只决定物化窗口，不进入随机 key。
- tile 必须包含足够的 derivative/search halo，并明确 core 与 halo 范围。
- 相邻 core 在相同坐标和 LOD 上 bitwise 相等；跨 LOD 的共有低频部分不变。
- cache key 至少含 realization ID、generator/query version、LOD/band、tile integer coordinate、字段集合和 dtype。
- cache hash 失败时丢弃并重建；cache corruption 不能升级为物理不可行。

### 8.4 边界和周期

- synthetic generator 的 periodic parent construction 与 public query boundary 是两个字段。
- 实验查询默认 `ERROR`：域外返回 `OUT_OF_DOMAIN`，不得自动 wrap、clamp、补零或外推。
- `PERIODIC` 只对声明兼容的解析/合成 regression 显式启用；响应必须标记 `WRAPPED` 和原/映射坐标。
- 可视化可以裁剪，但不能以裁剪替代域状态。

## 9. SurfaceQuery 公共合同

### 9.1 创建和描述

公共能力至少包括以下语义；具体语言签名可在不改变语义时调整：

```text
validate_source_descriptor()
create_surface_spec()
create_realization()
describe_realization()
get_capability_manifest()
open_query_handle()
classify_domain()
query_height_differential()
query_neighborhood()
query_signed_distance()
query_closest_features()
query_spherical_envelope_or_clearance()
sample_tile()
sample_visualization_window()
```

查询必须支持标量和 typed batch；batch 不能通过广播/排序悄悄改变输入—输出对应关系。

### 9.2 共同 QueryResponse envelope

每个响应至少包含：

```text
surface_realization_id / surface_spec_id / query_contract_version
query_id / operation / requested_points_or_region_hash
capability = EXACT | APPROXIMATE | UNAVAILABLE
reference_semantics / method_id / method_version
value_presence / capability_status / attempt_outcome / reason_code
domain_status / mapped_coordinate_if_any
quality_status / quality_mask / trusted_scale_status
requested_tolerance / achieved_residual / error_bound / convergence_level
units / frame_id / reference_point
values and validity arrays
```

`EXACT` 只表示相对于声明的 analytic primitive 或 band-limited realization 精确，不表示真实材料准确。`APPROXIMATE` 必须携带 achieved residual、误差界和收敛证据；失败或超出可信尺度时返回 `UNAVAILABLE/GEOMETRY_UNCERTAIN`，不得返回无标签近似值。

### 9.3 高度和微分查询

高度场响应按请求阶数返回：

- `h(x,y)` 和表面点 `(x,y,h)`；
- gradient/slope `(dh/dx, dh/dy)`；
- 外法向；
- Hessian、主曲率、平均/高斯曲率，仅在 family 光滑、尺度可信且数值质量合格时；
- 不可微集合的 feature IDs、候选 one-sided gradients/normals 和质量状态；
- domain、validity、missing/quality mask、可信波长/采样间距。

曲率不可用不应使高度查询整体失败；必须按字段分别表达 capability/status。

### 9.4 邻域查询

邻域可以是 AABB、圆盘/球或明确 footprint，返回用于安全细化的：

- 高度/坡度/距离保守 bounds；
- 候选 feature IDs 和可微分片；
- 当前表示 band、omitted-band bounds 和建议下一 LOD；
- domain/missing/quality coverage；
- 是否足以 certify no-surface-intersection 的纯几何结论。

该结论不是接触状态，也不允许根据摩擦、载荷或材料强度做判断。

### 9.5 signed distance 和 closest feature

- `phi_omega(x)` 必须保持外正内负。
- closest query 必须返回全部在共最小容差内的 feature，不把多支持平均成一个点。
- 每个 feature 至少有 point、outward normal set、distance、feature ID/type、domain/quality 和 error。
- approximate closest 使用 bracket/trust-region 或等价可审计方法；必须检查全局候选覆盖和局部残量，不能只返回最近一次迭代。

第一版能力基线：

| family | height/derivatives | signed distance/closest |
|---|---|---|
| plane/slope | exact | exact |
| sinusoid | exact relative to analytic formula | approximate with convergence/error |
| Gaussian bump/pit/multi-feature | exact height；光滑处 exact derivatives | approximate；保留多候选 |
| piecewise V groove/switch fixture | exact piecewise；折线处 curvature unavailable | exact primitive feature search |
| smooth/U/cosine groove | exact height/derivatives where smooth | exact only for declared primitive variant，否则 approximate |
| spherical cap/bowl fixture | exact in declared primitive domain | exact |
| self-affine Gaussian | exact relative to represented band | approximate with band/search/error bounds |
| arbitrary measured/mesh | unavailable first release | unavailable first release |

### 9.6 complete-sphere 纯几何边界

M01 可以实现 accepted A 所需的纯几何 complete-sphere 查询：

- 高度场的最低合法球心包络 `H_R(xc,yc)` 及全部共最大支持；
- 通用距离路径的 `g_R(c) = phi_omega(c) - R`；
- 支持点、法向、feature IDs、质量、误差、域和分辨率等级；
- 两种路径零集/可行域的一致性验证。

`R` 是查询 probe，不进入 surface identity。M01 不接收针轴、球冠边界、摩擦、载荷或材料参数，也不判定 legal cap、loaded contact、frictionally stable、load-bearing 或 engagement angle。M03/A 组合 complete sphere、有限球冠、针体净空和力学；M01 只提供底层表面证据及可选几何加速。

## 10. 质量、可信尺度、缺失和错误

### 10.1 domain/quality 枚举

`domain_status` 至少包括：

```text
IN_DOMAIN / ON_BOUNDARY / WRAPPED / OUT_OF_DOMAIN
```

`quality_status` 至少包括：

```text
TRUSTED_FOR_DECLARED_SCALE
RESOLUTION_REFINEMENT_REQUIRED
MISSING_SOURCE_DATA
GEOMETRY_UNCERTAIN
NONSMOOTH_FEATURE_SET
```

quality mask 为逐点/逐 feature validity；缺失区域不能被当作零高度。synthetic 的“trusted”只表示满足其声明的 DEV band 和数值验证，不表示实验真实性。

### 10.2 冻结 reason codes

至少提供：

```text
M01_INVALID_SURFACE_SPEC
M01_MEASURED_IMPORT_DEFERRED
M01_EXTERNAL_MESH_IMPORT_DEFERRED
M01_QUERY_CAPABILITY_UNAVAILABLE
M01_OUT_OF_DOMAIN
M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN
M01_TRUST_SCALE_INSUFFICIENT
M01_RESOLUTION_REFINEMENT_REQUIRED
M01_GEOMETRY_UNCERTAIN
M01_QUERY_APPROXIMATION_FAILED
M01_REPLAY_MISMATCH
M01_CACHE_CORRUPTION_REGENERATED
```

`UNAVAILABLE/UNSUPPORTED/NUMERICAL_FAILURE/PHYSICAL_INFEASIBLE` 遵守 M00 区分。M01 的几何查询失败通常不能推出 `PHYSICAL_INFEASIBLE`。

## 11. canonical raw output 和 M00 扩展

### 11.1 extension

M01 注册 owner `M01`、namespace `m01`、SemVer 版本的 `ResultExtensionDescriptor`。不得覆盖 core 字段；run/case/design/seed/surface 身份引用 M00 公共 keys。第一版至少注册：

| dataset/array ID | 分类 | 主要内容 |
|---|---|---|
| `m01.surface_realizations` | canonical raw/index | spec/realization/seed/latent/generator/source/frame/domain/boundary/hash/quality/status/maturity |
| `m01.surface_provenance_steps` | canonical raw | 有序 generation/processing DAG、版本、参数、输入/输出 hash |
| `m01.surface_quality_bands` | canonical raw | q/lambda band、方向、依据、uncertainty/status |
| `m01.surface_statistics` | canonical raw + scope | target/realized mean、Sq、variance、PSD/方向谱和数值误差 |
| `m01.surface_materialization_receipts` | diagnostic | footprint、tile/LOD/band、halo、omitted bounds、content hash |
| `m01.surface_validation_results` | diagnostic | fixture、metric、tolerance、observed error、pass/fail/status/evidence |
| `m01.source_availability` | diagnostic | measured/mesh 等请求的 unavailable 状态和缺项 |
| `m01.visualization_height` | optional derived array | 明确选择 realization/window 的 height sample；不作 solver geometry |
| `m01.visualization_validity` | optional derived array | 与 height 同形的 validity/quality mask |
| `m01.visualization_coordinates` | optional derived arrays | x/y 坐标或规范 affine grid manifest |

不要求保存每一个运行时查询。M03 必须保存实际进入 accepted 接触结果的支持几何；M01 只保存 realization manifest 和按配置聚合的 query/materialization receipts。

### 11.2 realization 必备字段

至少包含：

```text
surface_spec_id / surface_realization_id / realization_schema_version
source_descriptor_id / source_kind / family / material_label
seed_id / latent_noise_id / RNG profile
generator_id / generator_version / query_contract_version
logical_domain / boundary modes / source-surface-material frame IDs
definition_hash / source_artifact_hash / provenance_chain_hash
capability_manifest_hash / quality_manifest_hash
target_statistics_ref / realized_statistics_ref / statistic_scope
four-column maturity / source identity / certification status
value/capability/attempt/reason status
```

### 11.3 target 与 realized 统计 scope

每个统计量必须标明：

- `TARGET_ANALYTIC`、`REALIZED_COEFFICIENT_FULL_PARENT`、`AUDIT_SAMPLE`、`ACTIVE_FOOTPRINT_SAMPLE` 或 `VISUALIZATION_SAMPLE`；
- 计算方法/version、window、detrend、bin、方向和 band；
- 样本数、dtype、误差/不确定性和 validity coverage。

不得把活动走廊或显示网格的样本统计冒充完整 parent realization 的真实统计。

### 11.4 存储策略

- 默认 canonical 存储 compact realization manifest，不保存完整高分辨率 150 × 150 mm 数组。
- memory/disk tile cache 是可删重建的非 canonical 数据；默认 disk cache 关闭。
- 只有 run/plot config 明确选择的 realization/window 才保存 visualization arrays，采用内容寻址去重。
- M06 若缺少所需 visualization sample，必须形成 `PLOT_DATA_GAP_REQUEST`；不能调用 M01 evaluator 补算。

## 12. 最小预览和后续绘图接口

### 12.1 M01 最小预览器

M01 实现必须提供隔离的轻量预览器，仅有两种 user-facing recipe：

1. `oblique_3d_surface`：斜俯视 3D 地形图；
2. `height_map_2d`：带坐标、单位和色标的 2D 高度图。

预览器：

- 只读取 M01 public visualization sampling/result fields；
- 不被 evaluator/query package 导入；删除预览依赖后，表面查询和结果写入仍完整工作；
- 输出独立 figure/plot manifest，记录 realization、window、sampling、vertical exaggeration、colormap、recipe/version 和 source data hash；
- 全域演示默认可采样 150 × 150 mm、1024 × 1024，不作为求解器分辨率；
- 全域粗预览必须使用与显示 Nyquist 匹配的显式 low-pass/area-average 采样，记录 visualization band；禁止把 full fine band 直接点采样到粗网格造成混叠；
- 允许 active footprint 和局部高分辨率窗口，但必须明显标注 extent/resolution；
- 不生成啮合角、接触力、挂接成功或材料图。

审美、主题、交互、批量配方和更多图种留给 M06。接口须可通过新 recipe/version additive 扩展，而不修改 SurfaceRealization schema。

### 12.2 后续啮合角图的数据边界

- M01 保存高度、法向、坡度、质量和 feature 数据，使后续模块可构造几何输入。
- geometry-only 局部方向不得命名为实际啮合角。
- M03/A 后续可输出 `finite_tip_geometric_candidate` 或 loaded-contact 语义；M06 再绘制并明确分栏。
- 第一版 M01 preview 不预留一个含糊的 `engagement_angle` 数组。

### 12.3 工程验收证据

实现验收还需产生代表性剖面、坡度/法向、分布、PSD/方向谱、可信带和分辨率收敛证据。它们可以是 `VALIDATION_ONLY` 报告/静态图，不扩张 M01 user-facing preview recipe；字段与脚本必须可重放，M06 以后决定正式样式。

## 13. 数值、收敛、内存和性能

### 13.1 分辨率收敛

对 `Rt/5 -> Rt/8 -> Rt/10` 至少比较：

- complete-sphere envelope/clearance；
- unique smooth support 的位置和法向；
- 多支持数、feature identity 和已知切换位置；
- distance/closest residual 和 error bound；
- domain/quality 判定。

DEV 默认代表性 acceptance：`Rt/8` 与 `Rt/10` 间 envelope/clearance 差不超过 `0.01 Rt`，unique support 位置差不超过 `0.02 Rt`，法向夹角不超过 `1 deg`，且 feature topology 在非切换区保持一致。若未满足，返回 refinement/uncertain，不得降低验收门后继续。

M01 只能验证几何收敛；接触事件、力和趋势排名的 surface-resolution 收敛由 M03/M05 后续追加。

### 13.2 合成谱数值验证

- Hermitian 配对和逆变换 imaginary residual 必须相对实值尺度不大于 `1e-12`，否则拒绝 realization。
- coefficient-space variance 与 Parseval 回算必须在 float64 规模化容差内一致；容差和归约顺序写入 generator contract。
- sampled PSD 不要求逐 bin 等于随机 target；必须报告 band/bin/window/sampling uncertainty，并用 ensemble 或统计包络验收谱形。
- normalization 只在 full parent coefficient definition 上执行一次；任何 tile、活动走廊或 preview 不得重新缩放。

### 13.3 资源边界

- 默认 tile cache payload 不超过 512 MiB；淘汰策略可改变性能但不得改变结果。
- 禁止创建 150 × 150 mm、`Rt/10` 的完整常驻数组作为正常路径。
- 100 mm 走廊必须流式/按需采样；内存峰值、tile 生成量、cache hit/miss 和重新生成量进入性能报告。
- 全域 preview 使用独立低分辨率采样；坐标 mesh 应避免不必要的三份 dense copies。
- 磁盘 cache 可禁用；启用时有显式预算、完整性 hash 和安全清理，不进入 canonical identity。
- serial/parallel 和 cache policy 改变不能影响 realization/query semantic hash。

性能验收记录硬件、OS、Python、依赖、线程、fixture、footprint、LOD、峰值 RSS、cache payload、生成/查询/绘图时间和输出大小；不能只给一个 pass 布尔值。

## 14. 测试和验收矩阵

### 14.1 analytic 与微分

- 全部 family 的解析高度、梯度、法向和可用曲率；
- 与尺度自适应有限差分比较；
- 非光滑点返回 feature set/curvature unavailable；
- exact SDF/closest primitives 的点、边、顶点和符号；
- approximate closest 的残量、误差和网格/容差收敛；
- known nearest-feature switch 和共最小支持不被平均。

### 14.2 complete-sphere 与针尖尺度

- plane/slope/峰/谷/沟槽/多峰的球包络；
- height-envelope 和 `phi-R` 零集/可行域一致；
- 50/100 um probe 的支持、法向和不可达窄谷；
- `Rt/5, Rt/8, Rt/10` 收敛、omitted-band bounds 和 refine-before-certify；
- sphere query 不接受/不返回 cap、摩擦、力或 engagement 状态。

### 14.3 synthetic、seed 和 tile

- target/realized PSD、directional spectrum、variance、zero mode、Hermitian 和实值误差；
- 相同 seed/spec/version 重放；不同 seed 区分；generator version 改变 ID；
- common-random-number latent modes 在 H/Sq/lc 扫描中保持对应；
- serial/parallel、query order、plot-before-query、cache hit/miss 不变；
- 窄/宽 footprint 重叠点一致；扩窗不重新归一化；
- LOD 低频嵌套、只增高频、tile seam/halo 和边界一致；
- corrupted cache 被验证、丢弃、重建，canonical 结果不变。

### 14.4 domain、quality 和 deferred

- IN/ON/WRAPPED/OUT 状态和禁止隐式 wrap/clamp/extrapolate；
- 缺失/质量 mask 不被当作零高度；
- requested scale 超出 trust band 时字段级 unavailable/uncertain；
- measured descriptor 可校验但创建/query 必须 `M01_MEASURED_IMPORT_DEFERRED`；
- arbitrary mesh/point-cloud import 必须安全拒绝；
- validation-only triangulation 随分辨率收敛且不成为默认 backend。

### 14.5 M00 schema、输出和预览

- namespace/owner/field metadata/relation 注册和 registry freeze；
- ID/hash/lineage/status/maturity/certification 与 M00 一致；
- manifest-only replay 和选定 visualization arrays 读回；
- ResultReader 能读取 M01 datasets/arrays，默认不混入 validation/deferred diagnostics；
- preview 只输出 3D/2D，图 manifest 完整且图前后 RNG/query 结果不变；
- 删除 plotting optional dependency 后 evaluator、writer、reader tests 仍通过；
- README `## 输出概览` 引用的 dataset/field ID 自动验证存在。

### 14.6 最小验收 demo

实现窗口必须生成 `VALIDATION_ONLY` demo，至少包含：

- plane、slope、sinusoid、峰/坑、沟槽和 feature-switch fixtures；
- gentle/medium/sharp 三个共享 latent-noise identity 的合成 realization，并各有独立 realization ID；
- 一个 100 mm 单刺式窄活动走廊和一个更宽阵列式 footprint 的重叠一致性检查；
- 50/100 um、Rt/5-/8-/10 的几何收敛；
- 150 × 150 mm 低分辨率全域 preview；
- 每个三档 realization 的 3D 和 2D 图；
- measured 和 arbitrary mesh unavailable 记录；
- M00 bundle/ResultReader round trip、性能报告和追踪矩阵。

demo 名称和图片不得使用真实材料名，不得产生接触力或啮合成功结论。

## 15. schema/API 兼容和迁移

- M01 extension 与 query contract 使用独立 SemVer；字段 additive、能力激活和 breaking change 分开判断。
- measured/mesh 未来从 unavailable 变为 supported，在公共 envelope 不变时可做 additive capability release；旧 bundle 仍保持原 unavailable 事实。
- generator 新版本不得修改旧 realization；旧实现必须由 pinned generator replay，或明确 `BLOCKED_UNAVAILABLE` 并给出 migration/evidence，不能静默重生成。
- 修改 frame、SDF 符号、SurfaceRealization 不可变性、complete-sphere 或 accepted A 支持语义属于 breaking/amendment review。
- visualization recipe 增加不改变 surface schema；删除/重命名已发布字段需 MAJOR 和 adapter/迁移说明。
- proposed measured provenance 永远位于 additive 字段/namespace，不得 shadow accepted geometry。

## 16. 明确延期和禁止项

第一版延期：

- 白光轮廓仪或其他仪器采集管线；
- 实测 grid/point cloud/mesh 生产导入和标定；
- 非高斯高度边际、宏观裂隙/污染真实性模型和材料分类器；
- 任意非高度场 mesh 的 production query backend；
- 表面随损伤、磨损、切削或碎屑演化；
- GPU/分布式 tile service；
- M06 完整主题、交互和批量绘图；
- 啮合角、接触状态、摩擦、材料和承载图。

严禁：

- 把 synthetic 档位命名为红砖/混凝土；
- 用单一 Ra 唯一生成三维表面；
- 让 visualization grid 成为 solver 唯一几何；
- 用 seed alone 作为可重放合同而不保存 generator/参数/version/hash；
- crop-dependent normalization、tile-local randomness 或查询顺序敏感 RNG；
- 用 coarse LOD 在无误差界时证明无接触；
- 返回接触力、挂接成功、材料失效、实际啮合角或方案评分；
- 在 M01 复制 A 的摩擦/强度本构或修改 accepted A 合同。

## 17. 决策日志和关闭状态

| 决策 | 结论 | 状态 |
|---|---|---|
| source kind | analytic/synthetic supported；measured schema-only unavailable | accepted |
| 首批 surface library | plane/slope/sinusoid/peak-pit/multi/groove/switch + validation sphere fixture | accepted |
| 随机场 | self-affine Gaussian，H/Sq/lc/anisotropy/direction/seed 宽先验 | accepted |
| 目标输出 | gentle/medium/sharp 三档，允许显式参数覆盖，不绑定材料名 | accepted |
| 大域与实验区域 | 150 mm logical parent；按 100 mm swept footprint + guard 懒生成 | accepted |
| 分辨率 | tip-local Rt/5、Rt/8、Rt/10，自适应 refine，overview 独立 | accepted |
| 存储 | compact manifest + seed/generator/hash；tile cache 可删；选定 visualization 样本才落盘 | accepted |
| sphere ownership | M01 complete-sphere pure geometry；M03/A cap/contact/load | accepted |
| mesh | validation-only triangulation regression；production import deferred | accepted |
| 预览 | M01 只提供斜俯视 3D 与 2D height map；扩展审美留 M06 | accepted |
| engagement heatmap | 后续 M03/A 生产语义、M06 绘图；M01 不输出含糊角度 | deferred to owner |

本需求没有 unresolved 产品决策。

## 18. 实现窗口完成判据

M01 实现窗口只有同时满足以下条件才完成：

1. 实现本需求全部 supported analytic/synthetic schema、provider、query、seed、tile、output 和 preview；
2. measured/mesh 生产分支按冻结 reason code 安全 unavailable；
3. 通过第 14 节 unit/schema/replay/convergence/performance/preview 测试；
4. 生成三档 demo、2D/3D 图片、M00 bundle、验证/性能报告和需求追踪矩阵；
5. 在 M01 模块 README 写入 M00 要求的 `## 输出概览`，并自动校验字段 ID；
6. 证明完整高分辨率 150 mm 数组不在正常路径创建，窄/宽 footprint 重叠一致；
7. 证明 M01 未引入接触、摩擦、材料、单刺/阵列求解或 M06 反向依赖；
8. 精确暂存、检查 cached diff、提交和推送后停止，不自动开始 M02、M03 或 M06。

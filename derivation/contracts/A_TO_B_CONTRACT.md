# A_TO_B_CONTRACT — A→B 冻结公共合同

> contract_id: `A_TO_B`  
> contract_version: `1.0.0`  
> A model: `A_INTEGRATED_MODEL 1.0.0`  
> engineering context: `1.0.0`  
> input context: `A_MODULE_CONTEXT 0.3.0 accepted`  
> integration prompt: `1.0.0`  
> run: `A_INTEGRATION-r01`  
> status: `accepted`

本文件可独立供 B 层实现和审查使用。标记 `BEGIN/END A_TO_B_PUBLIC_CONTRACT` 之间的正文与 `A_INTEGRATED_MODEL.md` 第 12 节逐字一致；文件头仅提供独立文档身份。

<!-- BEGIN A_TO_B_PUBLIC_CONTRACT -->

### A_TO_B 公共合同正文

#### 1. 规范身份、适用范围与版本约束

| 字段 | 冻结值 |
|---|---|
| `contract_id` | `A_TO_B` |
| `contract_version` | `1.0.0` |
| `A_model` | `A_INTEGRATED_MODEL 1.0.0` |
| `engineering_context` | `1.0.0` |
| `input_module_context` | `A_MODULE_CONTEXT 0.3.0 accepted` |
| `integration_prompt` | `1.0.0` |
| `run` | `A_INTEGRATION-r01` |
| `status` | `accepted` |
| 唯一公共调用模式 | `embedded_constitutive_trial` |

本合同中的“必须”表示调用方或实现方若不满足该条，即构成合同违约；“可”表示在保持全部强制语义的前提下允许实现差异。B 只能通过 `embedded_constitutive_trial` 调用 A 的 `intrinsic_single_spine_kernel`。`standalone_single_spine_driver` 只用于 A 层独立单刺验证和实验对比，不是 B 的公共入口，也不得由 B 间接调用以获得每针法向载荷。

本合同覆盖：A1 合法球冠几何和禁止碰撞，A2 单边接触、三维 Coulomb 摩擦、梁/轴向弹簧/可选局部接触柔顺，A3 滑移迁移、材料容量与不可逆损伤、针体强度、释放和再挂接的单刺本征响应。首版明确不包含显式裂纹扩展、碎屑或颗粒动力学、连续切削有限元、地形重网格化、针尖磨损、安装座内部真实结构有限元、导轨/框架柔性、惯性动力学和断针后的继续承载。

所有尚未固定的摩擦、接触柔顺、表面材料强度与断裂、针体牌号与强度、损伤核、搜索控制和数值容差必须由版本化参数 ID 表示。参数不足时 A 必须返回明确的 `MODEL_UNAVAILABLE` 或 `PARAMETER_UNAVAILABLE` 诊断；不得用隐藏默认值、无限强度或任意惩罚刚度替代。

#### 2. 公共坐标、参考点、wrench 方向与功共轭

##### 2.1 坐标和单位

公共结果默认表达在全局右手系

\[
\mathcal F_G=\{\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
\]

其中墙面名义平面为全局 \(X\)-\(Y\)，\(+\mathbf E_Z\) 从墙面指向背板和自由空间。针所属单元的局部基为

\[
\mathcal F_U=\{\mathbf e_x,\mathbf e_y,\mathbf E_Z\},
\qquad
\mathbf e_y=\mathbf E_Z\times\mathbf e_x,
\]

局部 \(+\mathbf e_x\) 从单元头部指向根部，也是搜索和拖拽方向。长度使用 mm，力使用 N，时间使用 s，角度使用 rad，力矩使用 N·mm，应力和弹性模量使用 MPa \(=\mathrm{N/mm^2}\)，平移刚度使用 N/mm。轴向弹簧输入若为 N/m，进入 A 前必须除以 \(1000\) 转为 N/mm。

##### 2.2 接触力与公共 wrench 的唯一方向

第 \(j\) 个支持点的接触力定义为**墙面对针**的力：

\[
\mathbf f_j^G
=\lambda_{n,j}\mathbf n_j
+\mathbf T_j\boldsymbol\lambda_{t,j},
\qquad
\lambda_{n,j}\ge 0,
\]

其中 \(\mathbf n_j\) 从墙体指向针尖/自由空间，\(\mathbf T_j=[\mathbf t_{1j}\ \mathbf t_{2j}]\)。针作用于墙的力为 \(-\mathbf f_j^G\)。

B 接收的唯一公共 wrench 定义为

\[
\boxed{
\mathbf W_{A\rightarrow B}^{G,O}
=
\begin{bmatrix}
\mathbf F_{A\rightarrow B}^{G}\\
\mathbf M_{A\rightarrow B}^{G,O}
\end{bmatrix}
}
\]

即**单刺 A 子系统对刚性背板 B 的作用 wrench**，在声明参考点 \(O\) 处、以声明坐标系表达。首版点接触没有独立接触偶矩，因此

\[
\boxed{
\mathbf F_{A\rightarrow B}^{G}
=\sum_j\mathbf f_j^G,
\qquad
\mathbf M_{A\rightarrow B}^{G,O}
=\sum_j(\mathbf p_j-\mathbf r_O)\times\mathbf f_j^G.
}
\]

该定义等于墙面对针的接触 resultant 运输到背板参考点；内部梁力、弹簧力和根部反力不再另加一次。背板对单刺的作用为

\[
\boxed{
\mathbf W_{B\rightarrow A}^{G,O}
=-\mathbf W_{A\rightarrow B}^{G,O}.
}
\]

在局部拖拽方向上，正的抓附阻力标量为

\[
\boxed{
R_x=-\mathbf e_x\cdot\mathbf F_{A\rightarrow B}.
}
\]

因此 \(R_x>0\) 表示 A 对背板的力抵抗 \(+\mathbf e_x\) 拖拽。B 不得对该 wrench 再做一次作用—反作用换号后又以同一方向装配。

##### 2.3 参考点和坐标变换

从参考点 \(O\) 变换到 \(O'\) 时

\[
\boxed{
\mathbf F^{O'}=\mathbf F^{O},
\qquad
\mathbf M^{O'}
=\mathbf M^{O}
+(\mathbf r_O-\mathbf r_{O'})\times\mathbf F.
}
\]

同一原点、从坐标系 \(F\) 旋转到全局 \(G\) 时

\[
\mathbf W^G=
\operatorname{diag}(\mathbf R_{GF},\mathbf R_{GF})\mathbf W^F.
\]

响应必须同时返回 `reference_point_id`、参考点全局坐标、`expressed_frame_id` 和单位。B 若需要其他参考点或坐标，应优先请求 A 重新表达；自行变换时必须使用上述公式，不能只旋转力而遗漏力矩平移项。

##### 2.4 功共轭

令背板参考点的规定刚体增量为

\[
\Delta\boldsymbol\xi_B^{G,O}
=
\begin{bmatrix}
\Delta\mathbf r_O\\
\Delta\boldsymbol\theta_B
\end{bmatrix}.
\]

A 对背板做的离散功为

\[
\boxed{
\Delta W_{A\rightarrow B}
=
(\mathbf W_{A\rightarrow B}^{G,O})^{\mathsf T}
\Delta\boldsymbol\xi_B^{G,O}.
}
\]

这正是 B 全局虚功或残量装配使用的符号。背板输入 A 子系统的功为其相反数：

\[
\boxed{
\Delta W_{\mathrm{in},A}^{\mathrm{base}}
=-\Delta W_{A\rightarrow B}.
}
\]

参考点变换时使用

\[
\Delta\mathbf r_{O'}
=
\Delta\mathbf r_O+
\Delta\boldsymbol\theta_B\times(\mathbf r_{O'}-\mathbf r_O),
\]

可保证 \(\mathbf W^{\mathsf T}\Delta\boldsymbol\xi\) 不变。坐标旋转也必须保持总功不变。

#### 3. 公共操作与输入合同

##### 3.1 只读试探操作

公共试探操作的逻辑签名为：

```text
SingleSpineTrialResponse evaluate_trial(
    EmbeddedSingleSpineTrialRequest request
)
```

`evaluate_trial` 必须是无永久副作用的确定性操作。相同合同版本、相同输入字节/语义、相同快照版本和相同数值配置必须返回相同物理分支或明确的非唯一集合；不得依赖针调用顺序、线程顺序或未声明随机数。

##### 3.2 必需输入

| 输入字段 | 必须内容与语义 |
|---|---|
| `contract_id`, `contract_version`, `call_mode` | 必须分别为 `A_TO_B`、兼容的 `1.0.0`、`embedded_constitutive_trial`。 |
| `needle_identity` | `needle_id`、所属单元 ID、几何 ID、结构参数 ID、材料参数 ID、针体强度参数 ID；针 ID 在一次 B 全局事务内唯一。 |
| `surface_query_handle` | 指向不可变 `SurfaceRealization` 的 `A1QueryHandle`，含表面版本、坐标、单位、质量和域信息。B 不得修改其表面数据或查询规则。 |
| `base_pose_n` | 当前接受状态下针基座/背板参考刚体位姿、声明参考点 \(O\)、表达坐标系和姿态版本。 |
| `prescribed_base_increment` | B 规定的共同刚体增量、增量参数化和插值规则。当前工程认证的 B 层运动子空间为单元局部 \(x\) 与全局 \(Z\) 平移；非零局部 \(y\) 或转动增量必须返回 `KINEMATIC_MODE_UNSUPPORTED`，不得静默接受。 |
| `immutable_single_spine_state_n` | A 生成的、不可由 B 修改的已接受单刺历史快照，含状态版本、活动支持、梁/弹簧状态、累计滑移、路径/循环/事件历史引用。 |
| `shared_damage_store_snapshot` | 当前全局试探使用的不可变共享损伤快照、版本号和内容哈希。所有针在同一 B 迭代轮必须看到同一声明快照，除非进入显式冲突联合重求解轮。 |
| `parameter_bundle` | 复合针几何、接触/摩擦、结构、局部接触柔顺、材料、损伤、针体强度和数值配置的不可变版本化参数包。未决项必须为明确值、候选模型 ID 或 `unavailable`。 |
| `trial_identity` | B 提供的 `global_step_id`、`global_trial_id`、`newton_iteration_id`、`caller_sequence_id`。它们只用于幂等性、陈旧检查和审计，不得改变物理解。 |
| `requested_tangent_mode` | `none`、`algorithmic`、`generalized_one_sided` 或 `secant`。A 可因分支条件降级，但必须在输出中说明。 |
| `event_location_config` | 是否定位事件、允许的事件类别、调用方建议最大共同增量和数值配置 ID。数值值不是工程事实。 |
| `quality_request` | 需要返回的残量、质量、不确定性、非唯一性和诊断级别。B 不得请求关闭致命质量检查。 |
| `continuation_hint` | 可选的 A 生成 opaque 延续句柄，用于保持与上一接受分支连续；B 不得解析或改写。 |

请求中**不得**包含“每根针 \(0.5\ \mathrm N\) 法向载荷”或任何等价的针级恒法向力约束。若出现 `per_spine_normal_force`、`single_spine_Pz` 或等价字段，A 必须返回 `CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD`。B 层每单元 \(0.5\)–\(2\ \mathrm N\) 的主动推力属于 B 的共同平衡外载，不属于本请求。

##### 3.3 输入前置条件

A 必须在物理求解前检查：

1. 合同、模型、工程事实和参数版本兼容；
2. `needle_id`、表面 ID、历史快照和损伤快照相互一致；
3. 所有长度、力、角度和刚度单位可无歧义转换；
4. 基座增量处于当前允许运动子空间；
5. 历史快照未被重复提交或由其他事务推进；
6. A1 查询包络覆盖完整针体扫掠区域；
7. 参数包没有隐藏默认值或同一物理部件的重复柔顺。

前置条件失败时不得进入 Newton 或材料更新。

#### 4. 输出合同

`SingleSpineTrialResponse` 至少包含以下字段组。

##### 4.1 规范 wrench 与作用—反作用

```text
wrench:
  direction: A_on_B
  force
  moment
  expressed_frame_id
  reference_point_id
  reference_point_position
  units: N, N_mm
  opposite_wrench_B_on_A
  grip_resistance_Rx
  wrench_uniqueness
  admissible_wrench_graph_handle   # 仅退化/集合值分支
```

`opposite_wrench_B_on_A` 必须严格等于 `-wrench_A_on_B`。`wrench_uniqueness` 取 `unique`、`representative_with_internal_nonuniqueness` 或 `set_valued_constraint`。当刚性针、刚性安装和刚性接触使反力不能由规定运动唯一确定时，A 可返回按连续性规则选取的代表 wrench，但必须同时返回 `set_valued_constraint`、秩/零空间诊断和 opaque `admissible_wrench_graph_handle`；B 不得把代表值当作唯一材料响应。

##### 4.2 几何与逐支持接触

```text
geometry_contact:
  active_support_ids
  near_contact_support_ids
  support_points
  support_feature_types_and_charts
  legal_cap_gap_by_support
  effective_gap_by_support
  contact_normals_and_tangent_bases
  contact_force_by_support
  normal_and_tangential_multipliers
  contact_motion_substate
  objective_slip_increment_trial
  accumulated_slip_if_committed_preview
  rolling_or_sliding_flag
  cap_legality_margin
  cone_gap / shaft_gap / mount_gap
  A1_quality / geometry_uncertainty / nonsmooth_flag
```

逐支持力方向必须与第 2.2 节一致。`accumulated_slip_if_committed_preview` 只是预览，不得在试探中写入已接受历史。

##### 4.3 结构、弹簧和针体强度

```text
structure:
  needle_bending_switch
  beam_model_id / model_validity
  beam_tip_translation / beam_tip_rotation
  beam_root_force / beam_root_moment
  beam_energy_trial
  mount_mode
  spring_state
  spring_compression
  spring_force
  remaining_spring_travel
  hard_stop_reaction
  optional_contact_compression_and_energy
  section_resultants
  yield_margin / fracture_margin
  needle_strength_status
```

`needle_bending=off` 只令梁变形和梁储能为零；针体截面内力与强度检查仍必须返回，除非强度适配器明确不可用。

##### 4.4 材料、损伤和耗散

```text
material_damage:
  material_model_id / evidence_status
  queried_patch_ids
  damage_read_set_with_versions
  trial_damage_intents
  damage_write_set
  initiation_utilization
  current_capacity_scale
  failure_mode_weights
  material_substate
  friction_dissipation_trial
  material_dissipation_trial
  released_recoverable_energy_trial
  damage_conflict_signature
```

`trial_damage_intents` 必须描述 A 局部损伤律产生的 opaque、可验证、单调试探更新，并绑定旧面片版本。它不是已提交损伤。损伤不得修改 A1 原始表面几何，也不得隐式降低摩擦系数、梁刚度或弹簧刚度。

##### 4.5 状态、事件和共同增量限制

```text
state_events:
  primary_mechanical_state
  per_contact_motion_states
  spring_substate
  material_substates
  needle_strength_substate
  quality_solve_state
  all_event_candidates
  simultaneous_event_set
  earliest_event_fraction
  event_fraction_bracket
  suggested_common_increment_fraction
  event_one_sided_consistency
  terminal_or_continuable
```

对输入增量 \(\Delta\boldsymbol\xi_B\)，事件路径定义为

\[
\boldsymbol\xi_B(\alpha)
=\boldsymbol\xi_B^n+\alpha\Delta\boldsymbol\xi_B,
\qquad
0\le\alpha\le1
\]

（有限转动若未来支持，必须使用请求中声明的群插值；本版本不认证转动增量）。`earliest_event_fraction` 是全部监控事件的最早共同位置；无事件时为 `null`。`suggested_common_increment_fraction` 必须位于 \((0,1]\)，且不得越过未处理事件。B 必须用所有针返回值的最小值限制共同增量。

`FRICTION_CONE_REACHED` 只表示锥边界；只有一侧全粘着问题不可行并找到最大耗散滑移分支时，才返回 `SLIP_ONSET_CONFIRMED`。支持点迁移不自动等于滑移，材料起始/软化不自动等于接触释放。

##### 4.6 切线或割线

```text
linearization:
  tangent_or_secant_matrix
  row_wrench_frame_and_reference
  column_increment_basis
  linearization_point
  tangent_status
  branch_id
  finite_difference_check_metadata
```

算法切线定义为

\[
\boxed{
\mathbf K_{A\rightarrow B}
=
\frac{\partial\mathbf W_{A\rightarrow B}}
{\partial\mathbf q_B}
}
\]

其中 \(\mathbf q_B\) 是请求中声明的规定增量坐标，矩阵行对应声明参考点/坐标的 6 维 wrench。`tangent_status` 只能取：

- `smooth_consistent`；
- `generalized_one_sided`；
- `branch_dependent`；
- `secant_only`；
- `constraint_set_valued`；
- `unavailable`。

A 不保证切线对称。摩擦、活动集、参考点运动和损伤均可使切线非对称或分支相关。B 必须按状态处理，不能以对称化替代真实切线。参考点改变时，切线除 wrench 运输外还可能含几何项；未经 A 明确确认，B 不得仅用静态 wrench 变换矩阵变换切线。

##### 4.7 残量、质量、不确定性和错误分类

```text
diagnostics:
  force_or_interface_residuals
  beam_residual
  spring_residual
  contact_SOC_residual
  geometric_closure_residual
  material_residual
  gap_and_friction_violations
  work_balance_error
  generalized_Jacobian_rank_and_condition
  force_distribution_nonuniqueness
  parameter_evidence_status
  surface_data_quality
  uncertainty_bounds
  error_class
  error_detail
```

`error_class` 至少区分：

| 类别 | 含义 | B 的允许处理 |
|---|---|---|
| `OK` | 试探响应满足合同。 | 进入全局装配。 |
| `OPEN_RESPONSE` | 无承载接触；embedded 模式不伪造恒力平衡，通常返回零 wrench。 | B 可继续改变共同位姿并重调。 |
| `EVENT_REDUCTION_REQUIRED` | 当前增量跨越可定位事件。 | 按最小事件分数减小共同增量。 |
| `OUT_OF_DOMAIN` | 表面查询超域。 | 停止物理排序；不得当作失效载荷。 |
| `GEOMETRY_UNCERTAIN` | 数据、法向、支持或可信尺度不足。 | 停止或换高保真几何；不得继续承载推断。 |
| `BODY_COLLISION_INVALID` | 锥段、针杆或安装座碰撞。 | 纯球尖模型终止。 |
| `MODEL_UNAVAILABLE` | 所需材料、强度、梁或运动学模型未提供/不适用。 | 作为未认证结果，不得假定无限能力。 |
| `PARAMETER_UNAVAILABLE` | 必需参数缺失。 | 补充参数或选择显式允许的模型分支。 |
| `EQUILIBRIUM_INFEASIBLE` | 已证明所有相容本征分支物理无解。 | B 可改变共同运动/活动集，不得改写为数值失败。 |
| `EQUILIBRIUM_DEGENERATE` | 有解但反力/分支退化或集合值。 | 使用集合值/非唯一诊断；不得假定普通光滑切线。 |
| `NUMERICAL_NONCONVERGENCE` | 尚未证明无解，算法未收敛。 | 减步、换数值配置或终止；不得改写为物理失效。 |
| `STALE_SNAPSHOT` | 历史或损伤快照版本陈旧。 | 丢弃结果并用最新快照重调。 |
| `DAMAGE_CONFLICT_REQUIRES_RESOLVE` | 多针试探写入同一损伤区域。 | 进入第 5.3 节联合重求解。 |
| `CONTRACT_VIOLATION` | 输入违反版本、单位、运动或载荷合同。 | 修正调用；不得继续装配。 |

##### 4.8 事务句柄

```text
transaction:
  opaque_trial_state_handle
  rollback_token
  provisional_commit_intent
  accepted_history_version_read
  damage_snapshot_version_read
  request_hash
  response_hash
  idempotency_key
```

`provisional_commit_intent` 不是已授权提交令牌。只有 B 接受全局步并完成批量冲突检查后，A 的事务协调器才能将其升级为一次性 `armed_commit_token`。

#### 5. 状态所有权与事务语义

##### 5.1 所有权

- A 拥有单刺状态模式、局部接触/结构/材料规律、历史字段语义、试探句柄和局部损伤更新规则。
- `SurfaceRealization` 和 A1 原始几何不可变；任何损伤只存在于独立 `DamageStore`。
- B 拥有共同背板运动、每单元主动推力、全局平衡、针间载荷共享、全局 Newton/活动集、共同增量接受和提交时机。
- B 可保存 A 返回的 opaque 历史快照，但不得直接修改其内容。
- 共享 `DamageStore` 的物理内容由 A 的材料层定义；B 负责多针冲突分组、联合重求解和全局原子提交调度。

##### 5.2 无副作用试探与回滚

`evaluate_trial` 只能读取已接受单刺历史和请求中的不可变损伤快照。任何试探不得永久增加：

- 累计滑移；
- 损伤或软化坐标；
- 摩擦/材料累计耗散；
- 总路径、物理时间或循环距离；
- 接触循环 ID、峰记录或事件序号；
- DamageStore 版本；
- A1 原始表面或物理参数。

回滚必须恢复到与调用前语义等价的状态；对可序列化状态应通过字节级哈希测试，对缓存等非物理对象至少通过语义级等价测试。数值缓存可丢弃或重建，但不得混入物理历史。

##### 5.3 多针共享损伤冲突

所有针在一个 B 全局迭代轮中首先针对同一声明快照试探。B 必须以 `damage_read_set`、`damage_write_set`、面片版本和空间核重叠检测冲突。

- 写集合不重叠时，可进入批量提交准备。
- 同一损伤面片或相互作用核被多个针写入时，B 不得按针调用顺序覆盖，也不得把各针损伤增量简单相加。
- B 必须把冲突针组成 `damage_conflict_group`，将全部 opaque `trial_damage_intents` 提交给 A 的损伤事务协调器；A 按同一局部损伤律生成一个确定性的共享试探快照或返回不可联合。
- B 随后必须用该共享试探快照重新调用所有受影响针，并重新求多针共同平衡，直到接触力、损伤和全局残量一致。
- 调用顺序、线程顺序和针 ID 排列不得改变最终共享损伤状态；若物理分支确实非唯一，必须显式返回非唯一，而不是顺序依赖。

A 负责损伤律；B 负责发现耦合、组织共同迭代和决定是否接受全局步。

##### 5.4 原子提交

B 只有在以下条件同时满足后才能请求提交：

1. 多针共同平衡及 B 自身残量通过；
2. 所有针的试探响应来自同一最终 `global_trial_id` 和相容快照；
3. 所有事件已按共同最小增量处理；
4. 所有损伤冲突已联合重求解；
5. 没有 `OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN`、`BODY_COLLISION_INVALID`、陈旧快照或未处理数值失败；
6. B 明确接受该全局步。

提交协议为：

```text
prepare_atomic_commit(accepted_trial_responses)
    -> armed_commit_token | conflict_or_stale_error

commit_atomic(armed_commit_token)
    -> new_single_spine_history_versions
       new_shared_damage_store_version
       commit_receipt
```

`commit_atomic` 必须要么同时提交全部针历史和共享 DamageStore，要么不提交任何一项。内部写入顺序采用确定性规范顺序用于审计，但重叠损伤必须在准备阶段已联合解决，不能靠顺序覆盖。令牌一次性使用、绑定请求/响应哈希和快照版本；重复提交必须幂等返回原收据或拒绝，不得重复累计历史。

任一针响应失效、B 全局残量失败、提交前版本变化或存储失败时，全部试探回滚。B 不得只提交“成功的针”。

#### 6. B 的调用义务与禁止事项

B 必须：

1. 对刚性背板中的所有针施加相同的声明共同增量，并由 B 层求共同平衡；
2. 在 B 外层装配每单元 \(0.5\)–\(2\ \mathrm N\) 主动推力，而不是在 A 内逐针施加；
3. 读取并传播 wrench 方向、参考点、坐标、单位、事件分数、质量、不确定性和切线状态；
4. 对所有针取最早事件分数，减小共同增量并重新调用；
5. 对集合值/非唯一响应使用 A 返回的图或诊断，不把代表值伪装成唯一材料曲线；
6. 只在全局步接受后执行原子提交。

B 不得：

- 给每根针强制 \(0.5\ \mathrm N\) 法向载荷，或把每单元主动推力平均分到各针；
- 重建或替换 A1 表面/球尖几何、A2 Signorini–Coulomb 摩擦与柔顺、A3 滑移迁移/材料/损伤/释放；
- 把 A 的逐针峰值或平均峰值乘以有效针数作为阵列承载；
- 假定算法切线永远光滑、对称、正定或可用；
- 在未接受全局步时提交滑移、损伤、路径、循环、耗散或事件历史；
- 丢弃 `event_fraction`、质量、不确定性、模型不可用、参数不可用或非唯一状态；
- 把 `NUMERICAL_NONCONVERGENCE` 改写为材料失效、接触释放或零承载；
- 把体部碰撞转为新的承载接触；
- 在 DamageStore 冲突时按调用顺序覆盖；
- 直接修改 opaque 状态、事务令牌或 A 生成的延续句柄。

#### 7. 合同一致性与验收测试

实现进入 B 前必须至少通过以下测试。所有测试都应记录合同版本、参数包、坐标、单位、容差和结果哈希。

| 测试 | 验收要求 |
|---|---|
| 作用—反作用 | `wrench_A_on_B + wrench_B_on_A = 0`，逐分量在残量容差内。 |
| 参考点变换 | 在两个参考点直接重算与公式运输结果一致；力矩使用 N·mm，不能遗漏平移项。 |
| 坐标旋转 | 同一物理构型在旋转坐标中力、力矩、接触分量和状态相容，标量功与能量不变。 |
| 基座增量—wrench 功共轭 | 有限差分外功与 A 内部储能、摩擦耗散、材料耗散和可恢复能返回的离散平衡一致；数值残差单列。 |
| standalone/embedded 等价 | 用外部标量法向平衡器包围 embedded 核，在相同基座路径和 \(P_z=0.5\ \mathrm N\) 下，结果与 `standalone_single_spine_driver` 一致；embedded 请求自身不含 \(0.5\ \mathrm N\)。 |
| 无副作用重复调用 | 同一请求重复调用，已接受历史、DamageStore、累计滑移/耗散/路径/事件序号不变，响应确定或明确非唯一。 |
| rollback 一致性 | 回滚后可序列化物理状态哈希与试探前一致；缓存变化不影响语义结果。 |
| tangent/finite difference | 光滑分支算法切线与中心/单侧有限差分一致；事件、摩擦和损伤分支必须正确标为广义、分支相关、割线、集合值或不可用。 |
| 共享损伤顺序不变性 | 调换针调用顺序、并行顺序和针 ID 排序，联合重求解后的共享损伤、耗散和全局响应不变，或明确报告物理非唯一。 |
| event fraction 重现 | 用返回的最早 `event_fraction` 缩小共同增量后，完整重求解在同一位置和容差内重现相同事件集合及一侧状态。 |
| 单位转换 | N/m 到 N/mm、\(\mu\mathrm m\) 到 mm、度到 rad 的转换不改变物理结果；错误或混合单位被拒绝。 |
| \(0.5\ \mathrm N\) 不重复施加 | embedded 调用中不存在单刺法向力残量；B 外层施加每单元推力后，单针/多针合力只计算一次。 |
| open response | 完全分离时 embedded 返回 `OPEN_RESPONSE`、零接触 wrench 和接近事件信息，不伪造非零恒力静态平衡。 |
| 刚性集合值分支 | 全刚性且反力不唯一的构造例返回 `constraint_set_valued`/退化诊断，B 不会把任意有限惩罚斜率当作物理刚度。 |
| 失败分类 | 构造案例分别触发域外、几何不确定、体碰撞、模型/参数缺失、物理无解和数值未收敛，分类不互相替换。 |
| 原子提交 | 任一针或存储步骤失败时所有针和 DamageStore 均保持旧版本；成功时只增加一次并产生唯一收据。 |

#### 8. 兼容性与变更规则

- B 必须拒绝未知的主版本；其他次版本或预发布版本是否兼容由显式兼容表决定，不能只比较字符串大小。
- 新增可选诊断字段可在不改变语义时向后兼容；改变 wrench 方向、参考点默认、单位、事件分数定义、状态所有权、提交语义或每针载荷边界必须升级合同主版本。
- 参数包、材料模型和数值配置可独立升级，但响应必须回传完整版本 ID。
- 本合同已作为 A→B 推导规范接受并冻结；实际实现进入 B 求解器前仍必须完成第 7 节适用的合同测试，并继续关闭集成模型第 10–11 节列出的实现、参数和实验缺口。“规范已接受”不等于代码或实验已验证。

<!-- END A_TO_B_PUBLIC_CONTRACT -->

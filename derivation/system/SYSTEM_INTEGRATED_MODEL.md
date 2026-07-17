# SYSTEM_INTEGRATED_MODEL — A/B/C 全局机理集成规范

> 任务：`SYSTEM_INTEGRATION`  
> 模型版本：`1.0.0`  
> run_id：`SYSTEM_INTEGRATION-r01`  
> 状态：`accepted`（系统理论与接口集成完成；代码、数值和实验未认证）  
> 唯一主输出：`SYSTEM_INTEGRATED_MODEL.md`

---

## 0. 规范身份、输入基线与规范词

### 0.1 输入基线与完整性

本文件以以下五份实际上传文件为唯一输入。表中的 SHA-256 只用于标识本轮上传工件，不改变文件内的正式版本语义。

| 权威顺序 | 规范基线 | 实际上传文件 | 版本与状态 | 上传工件 SHA-256 |
|---:|---|---|---|---|
| 1 | `engineering_fixed_context` | `engineering_fixed_context.md` | `1.0.0 current` | `6c1225d3137f8095673b78e1dc8a76acdb0ae73247ec7c49e720cfcc56bb03cb` |
| 2 | `A_INTEGRATED_MODEL` | `A_INTEGRATED_MODEL.md` | `1.0.0 accepted` | `0679f5bfe71d2ff5b2521414a39b41c6b94f23f54227d19bd38a964960088ccc` |
| 3 | `B_INTEGRATED_MODEL` | `B_INTEGRATED_MODEL.md` | `1.0.0 accepted` | `d64a387956b4d8b2317817c7429d1a57e594bab436fc5f1c9547126c95dd43ad` |
| 4 | `C_INTEGRATED_MODEL` | `C_INTEGRATED_MODEL.md` | `1.0.0 accepted` | `8439835281ed61344de106082f8e6826c9a993d8767fb7845633510cdfe5b589` |
| 5 | `SYSTEM_INTEGRATION_PROMPT` | `SYSTEM_INTEGRATION_PROMPT.md` | `1.0.0` | `7f8644bb268969e9bd2d6138e6ba0e59f8fabbb820c49563f91e37daccf4e34f` |

内嵌公共合同为：

- `A_TO_B 1.0.0 accepted`，权威正文位于 `A_INTEGRATED_MODEL 1.0.0`；
- `B_TO_C 1.0.0 accepted`，权威正文位于 `B_INTEGRATED_MODEL 1.0.0`。

本轮已完整读取五份输入的工程事实、低层机理、公共合同、状态、事件、事务、验证、风险和未决登记。未使用额外论文、未上传快照、独立合同或隐藏默认值。

### 0.2 权威顺序

发生冲突时必须按以下顺序处理：

1. `engineering_fixed_context 1.0.0 current`；
2. A、B、C 各自所属的 accepted 集成模型；
3. A→B 仅以 `A_TO_B 1.0.0 accepted` 为接口权威；
4. B→C 仅以 `B_TO_C 1.0.0 accepted` 为接口权威；
5. C 的系统公共接口、偏心加载理论和安全拒绝语义；
6. 本文件中的系统集成映射和调度推导。

同一物理量若仅名称、表达坐标或参考点不同，必须通过显式别名、刚体变换或参考点运输统一，不得建立第三个可演化副本。无法由权威顺序消解的实质冲突必须进入未决登记，不能静默任选。

### 0.3 规范词

- **必须**：实现或调用不满足即构成规范或合同违约；相关候选不得装配或提交。
- **不得**：明确禁止的实现、推断或状态转换。
- **仅当**：列出的全部前置条件均成立时才允许执行。
- **可**：不改变物理所有权、合同语义、历史和认证边界的实现选择。
- **accepted**：已由输入基线正式接受的理论/数据合同；不等于源代码、参数、数值或实验已验证。
- **unavailable**：所需量没有足够模型、参数、边界或证据；不得以零值替代。

---

# 第一篇：系统对象、范围与闭合等级

## 1. 唯一系统算子和规范对象

### 1.1 唯一系统主路径

系统主路径固定为：

\[
\boxed{
\text{SurfaceRealization/A1 query}
\rightarrow
\mathcal K_A^{\rm intrinsic}
\rightarrow
\mathcal B^{\rm embedded}
\rightarrow
\mathcal G_C
\rightarrow
\text{raw simulation--experiment outputs}
}
\]

系统层的唯一顶层物理算子定义为

\[
\boxed{
\mathcal G_{\rm SYS}:
\left(
\mathsf S_{\rm SYS}^{n},
\mathsf R_{\rm SYS},
\Theta_{\rm SYS},
\mathcal B_{\rm boundary}
\right)
\mapsto
\left(
\mathsf S_{\rm SYS}^{\rm trial/accepted},
\mathcal O_{\rm raw},
\mathcal E_{\rm SYS},
\mathcal K_{\rm SYS},
\Sigma_{\rm SYS}
\right)
}
\]

其中：

- `SystemAcceptedState` 是系统主路径唯一 accepted state；
- 其物理核心是 accepted C 模型的唯一 `CAcceptedState`；
- 四个 B accepted snapshots、全部 A opaque accepted states 和一个共享 `DamageStore` 由该 C 状态中的 `low_level_accepted_bundle` 绑定；
- 系统层只保存该组合的不可变原子清单、账本索引、认证和提交收据，不建立第二份可修改的 C/B/A/DamageStore 状态；
- `SystemRequest` 只允许调用 accepted C 公共操作：初始化预紧、推进预紧、推进偏心加载、查询 accepted state 和形成能力结果。

### 1.2 standalone 驱动的系统位置

A、B standalone 驱动是验证执行器，不是第二套系统物理：

```text
StandaloneValidationHarness
  A_SINGLE_SPINE_PROFILE
    -> standalone_single_spine_driver
    -> same intrinsic_single_spine_kernel used by B

  B_ARRAY_UNIT_PROFILE
    -> standalone_continuous_unit_driver
    -> same embedded_array_unit kernel and same A embedded calls used by C
```

它们必须满足：

- A standalone 在本征核外施加唯一的单刺 `0.5 N` 主动法向推力；
- B standalone 在 B 外层施加每单元 `0.5–2 N` 主动推力；
- C 只调用 `embedded_array_unit_trial`，不得调用任何 standalone 驱动；
- standalone 运行拥有独立运行 ID、独立 accepted 历史和独立 `DamageStore` 分支；
- standalone 结果只能形成 `StandaloneValidationRecord`，不得直接替换或推进 `SystemAcceptedState`；
- 通过等价边界测试证明二者共享同一低层核，而不是维护两套接触、结构、损伤或事件实现。

### 1.3 系统阶段

系统主路径采用 C 已接受的阶段语义，不新建竞争物理状态：

```text
SystemStage:
  PRELOAD_SEARCH
  PRELOAD_EVENT_RESOLUTION
  PRELOAD_ACCEPTED_LOCKED
  ECCENTRIC_CONTRACT_AUDIT
  ECCENTRIC_LOAD_TRIAL
  ECCENTRIC_EVENT_RESOLUTION
  ECCENTRIC_LOAD_ACCEPTED
  PHYSICAL_TERMINATED
  UNCERTIFIED_STOPPED
  NUMERICAL_OR_TRANSACTION_STOPPED
```

`ECCENTRIC_CONTRACT_AUDIT` 是调用前认证阶段，不是物理路径增量。其失败不得生成新的 accepted 物理节点。

## 2. 闭合等级与当前在线能力

### 2.1 分层闭合结论

| 层级 | 当前结论 | 能否作为在线物理能力 |
|---|---|---:|
| 工程事实和物理依赖 | 全局一致，权威顺序明确 | 是，作为只读约束 |
| A 单刺理论、状态、事件、事务及 A→B 合同 | `accepted` | 合同层可调用；代码未验证 |
| B 阵列理论、共同平衡、事件、事务及 B→C 合同 | `accepted` | x/Z 合同层可调用；代码未验证 |
| C 同步预紧理论与 x/Z 调用路径 | 已集成 | 当前合同运动范围内可表达 |
| C 自动预紧停止与锁定 | 规范已定义 | 仅当停止策略、阈值和 `s_max` 由版本化配置提供并认证时可形成合格锁定态 |
| C 偏心加载六维理论、稳定性、事件、峰值和事务 | 已集成 | 理论可用，但当前 B 1.0 不支持正式非零路径 |
| 正式非零 `+X`、`45°` 或 rocking | B 1.0 缺少局部 y、动态姿态和完整 twist | 不可在线运行；必须安全拒绝 |
| 求解器源代码 | 本轮未提供 | 否 |
| 数值收敛、故障注入、确定性重放 | 测试规范已定义 | 未执行 |
| 参数标定、CAD、表面和材料数据 | 存在未决项 | 未认证 |
| 实验验证 | 输出合同已定义 | 未执行 |

### 2.2 B 1.0/C 偏心加载缺口

`B_TO_C 1.0.0 accepted` 仅认证每个单元的局部 x 与全局 Z 平移：

\[
\mathcal V_i=\operatorname{span}\{\mathbf e_{x_i},\mathbf E_Z\}.
\]

四单元平移子空间交集只有

\[
\bigcap_{i=1}^{4}\mathcal V_i=\operatorname{span}\{\mathbf E_Z\}.
\]

因此：

- 非零全局 `+X` 使单元 3、4 需要局部 y；
- 非零 `45°` 使四个单元均需要局部 y；
- rocking 还需要动态单元姿态、针轴/针尖姿态、三维碰撞/表面查询和旋转事件。

在任何正式非零偏心加载物理调用前，系统必须计算四单元完整理论 twist。若任一单元存在未认证局部 y 或转动，必须返回：

```text
primary_status = C_CONTRACT_EXTENSION_REQUIRED
accepted_state = unchanged
delta_P_increment_accepted = 0
B/A accepted histories advanced = false
DamageStore advanced = false
events/work/curve/peak advanced = false
F_crit = null
F_crit_confirmed = false
```

该安全拒绝不表示零承载、物理无平衡、物理失稳、不可恢复脱附、数值失败或抓附失败。

### 2.3 当前可执行阶段的精确边界

1. A standalone 和 B standalone 的调用、状态和事务规范完整，但实现通过状态仍为未验证。
2. C 同步预紧的逐步 x/Z trial 在 `B_TO_C 1.0.0` 运动合同内可表达。
3. 若 C1 停止阈值、保持规则或 `s_max` 缺失，系统不得自动接受预紧锁定态，也不得回退使用 100 mm；应返回未认证状态并保留最后安全 accepted state。
4. 正式非零偏心加载在当前合同下只能执行合同覆盖审计和安全拒绝，不能产生反力曲线或能力结论。
5. B 2.x 最小扩展只有在实现、验证和正式接受后，才能把偏心加载升级为在线物理能力。

## 3. 范围与排除项

### 3.1 本文件负责

- A→B→C 的变量、状态、历史、事件、切线/graph、质量和事务映射；
- 全局、单元、针、接触和材料坐标、参考点和刚体变换；
- 单位、作用—反作用、wrench 装配和功方向；
- 系统 accepted/trial/rollback/prepare/commit 原子语义；
- standalone 与系统主路径的核复用边界；
- 全局事件、损伤 fixed point、同位置级联、终止和能力证据；
- 实验原始输出、验证矩阵、未决问题和实现交接。

### 3.2 本文件不得负责

- 不重写 A 的球尖接触、摩擦、梁、轴向弹簧、材料、损伤或针体强度；
- 不重写 B 的阵列共同平衡、活动集、载荷共享或事件后重分配；
- 不重写 C 的预紧、六维平衡、稳定性或峰值定义；
- 不新增框架、导轨、传动链或 rocking 弹性；
- 不引入显式裂纹、碎屑、颗粒动力学、地形重网格、针尖磨损、惯性、大角度脱落或绕 Z 扭转扫描；
- 不固定材料、表面、损伤、数值、停止、峰值、样本数、砂纸目数、验证误差、成功阈值或综合评分；
- 不批准 B 2.x，不声明代码、数值或实验已通过。

---

# 第二篇：完整依赖链与所有权

## 4. 调用图与禁止反向修改

### 4.1 系统主路径调用图

```text
SystemRequest / immutable run manifest
  -> CSystemRequest
     -> C trial and global kinematics
        -> four embedded_array_unit_trial calls
           -> B1 immutable array mapping
           -> B2 unit equilibrium/residual/graph
           -> B3 unit event/damage/cascade candidate
              -> all configured A embedded_constitutive_trial calls
                 -> SurfaceRealization / A1 queries
                 -> A contact/structure/material/strength trial
        -> C wrench transport and global assembly
        -> global event reduction / cross-unit DamageStore fixed point
        -> stability / termination / peak audit
        -> prepare all A/B/C intents
        -> one atomic global commit or full rollback
  -> raw accepted output and experiment package
```

依赖方向必须单向。下游只能消费上游公共合同，不得解析 opaque 状态后反向修改物理。

### 4.2 物理与软件所有权矩阵

| 对象或机制 | 唯一物理所有者 | 系统层权限 | 下游禁止事项 |
|---|---|---|---|
| 工程固定事实、扫描集合、范围和排除项 | `engineering_fixed_context` | 校验、绑定、版本记录 | 静默改写固定事实 |
| `SurfaceRealization` 原始几何、域、质量和查询 | A1/表面层 | 只读句柄和版本 | 用损伤改写原始几何；按材料复制接触逻辑 |
| 合法球冠、支持点、法向、间隙、非承载体碰撞 | A1 | 读取状态和事件 | B/C 重新计算或平均法向 |
| 单边接触、Coulomb 摩擦、支持迁移和客观滑移 | A | 读取 wrench、状态、事件、graph | B/C 另建摩擦锥或重新判滑移 |
| 局部接触柔顺、针梁、针级轴向弹簧、硬限位 | A | 读取状态、能量和净 wrench | B/C 再加等效刚度、梁力、弹簧力或限位反力 |
| 表面材料容量、损伤演化和材料耗散 | A 材料层 | 调度冲突和原子事务 | B/C 直接减强、相加、取最大或顺序覆盖损伤 |
| 针体屈服/断裂和结构模型适用性 | A 强度/结构层 | 读取裕度和事件 | 高层用墙面材料失效代替针体强度 |
| 阵列格点、角度梯度、实际针长、拓扑和配置哈希 | B1 | 只读配置 | C 另建阵列几何或用统一 4 mm 覆盖梯度阵列 |
| 全阵列共同背板兼容、活动集和 contact-only 装配 | B2 | 提供单元运动和控制参数 | C 指定逐针位移、活动集或逐针力 |
| 每单元恒主动推力平衡、normal graph 和切线凝聚 | B2 | 调用、读取残量/graph | C 平均分配 `P_i` 或忽略残量 |
| 单元内事件定位、重分配、DamageStore 调度和级联 | B3 | 组织跨单元归约 | C 用固定转移矩阵、邻接权重或旧峰值转移载荷 |
| 共同径向搜索 `s`、预紧停止、锁定 `s_stop` | C | 调用 C 公共接口、持有 accepted state | A/B 选择 C 停止阈值或把 100 mm 当 C 上限 |
| 整爪刚体运动、加载点约束、六维平衡和稳定性 | C | 系统调度和认证 | 反向下推为 A/B 接触机理；引入隐藏支承 |
| 四单元 wrench 运输、整体事件、里程碑和峰值 | C | 输出、审计、原子事务 | 四个单元峰值求和或旋转旧 wrench |
| 全局身份、不可变运行清单、调用顺序、持久化和收据 | 系统调度层 | 唯一拥有 | 物理层用调用顺序决定分支 |
| 实验加载协议、传感器坐标、速度/时间和真实约束 | 外部控制/实验层 | 版本化绑定和输入 | 在缺失时用隐藏默认值补齐 |
| 二元成功阈值和综合评分 | validation/设计决策层，当前未定义 | 仅保存原始量供后续使用 | A/B/C 自动输出成功或单一评分 |

### 4.3 不可变、试探和提交后演化

| 生命周期 | 对象 | 允许操作 |
|---|---|---|
| `immutable` | 工程事实、模型/合同版本、表面原始几何、A/B/C 配置、参数包、参考点、变换、系统边界清单 | 只读；变化必须创建新运行或显式版本迁移 |
| `trial-only` | A/B/C 可逆候选、Newton/活动集、事件括区间、trial DamageStore、候选姿态、候选功/曲线/峰值、rollback token | 可反复重建；不得进入 accepted 历史 |
| `prepare-only` | provisional intents、读写集合、候选哈希、armed tokens | 只验证一致性和持久化可用性；不得推进物理 |
| `commit-only` | 路径、时间、累计滑移、DamageStore、耗散、事件号、级联、曲线、峰值、里程碑、accepted states、收据 | 一个原子提交中同时演化；失败则全部不变 |
| `derived` | `R_x`、`Q_s`、作用线、CoP、`N_eff`、裕度、能力摘要、滤波曲线 | 从 accepted 原始量派生；不得反写物理状态 |
| `unresolved` | 未固定阈值、参数、模型选择、速度和误差 | 显式 ID、范围、候选或 `unavailable`；不得硬编码 |

### 4.4 opaque 状态规则

- A 的 accepted 单刺状态由 A 拥有；B/C/系统只能持有句柄、版本和公共摘要。
- B 的 accepted 单元状态由 B 拥有；C/系统只能持有句柄、版本和公共摘要。
- C 的 `CAcceptedState` 对系统调用者 opaque；系统不得解析后修改低层字段。
- `DamageStore` 内容由 A 材料层定义；B/C/系统只传递快照、版本、哈希、读写集合和 opaque intents。
- 任何层级的 opaque 句柄不得在释放、脱离、再挂接、阶段切换或回滚时重置；只有新独立试验或新 `SurfaceRealization` 从无损状态开始。

---

# 第三篇：全局状态、对象和变量字典

## 5. 规范数据对象

### 5.1 `SystemAcceptedState`

```text
SystemAcceptedState:
  identity:
    system_state_id
    parent_system_state_id_optional
    system_model_version = 1.0.0
    run_id = SYSTEM_INTEGRATION-r01
    operation_profile = C_SYSTEM_MAIN_PATH
    stage
    primary_status
    all_status_codes[]
    commit_receipt_id
  canonical_c_state:
    CAcceptedState_handle
    c_state_id
    c_state_hash
  atomic_low_level_manifest:
    B_snapshot_handles[4]
    B_snapshot_versions[4]
    A_opaque_bundle_handles[4]
    A_state_version_manifest
    shared_DamageStore_handle
    shared_DamageStore_version
    shared_DamageStore_hash
    atomic_bundle_hash
  immutable_bindings:
    engineering_context_id/version/hash
    A/B/C model and contract versions
    surface/configuration/parameter IDs and hashes
    frame/reference-point/transform registry
    unit and residual-scaling registry
    system_boundary_and_authorized_constraint_manifest
  accepted_ledgers:
    event_ledger_handle
    damage_and_cascade_ledger_handle
    work_energy_error_ledger_handle
    raw_curve_handle_optional
    peak_and_milestone_ledger_handle_optional
    branch_lineage_handle_optional
  certification:
    contract_coverage
    model_parameter_geometry_domain_status
    stability_evidence
    deterministic_replay_manifest
    last_valid_system_state_id
    legal_next_operations
```

约束：

1. `canonical_c_state` 是唯一物理当前状态；`atomic_low_level_manifest` 只是对其低层组合的不可变索引和一致性哈希，不得包含第二份可修改状态。
2. C、四个 B、全部 A 和共享 `DamageStore` 必须由同一 `commit_receipt_id` 或同一原子收据链证明同时可见。
3. 任一版本或哈希不匹配均为 `STALE_SNAPSHOT` 或 `CONTRACT_VIOLATION`，不得自动修复。

### 5.2 试探与事务对象

```text
SystemTrialContext:
  parent_SystemAcceptedState
  immutable_run_manifest
  requested_C_operation
  proposed_path_and_pose
  four_B_trial_requests
  four_raw_B_trial_responses
  all_A_trial_handles_opaque
  one_shared_trial_DamageStore
  transported_wrenches
  global_residual_or_graph
  event_brackets_and_simultaneous_groups
  damage_fixed_point_and_cascade_state
  stability_quality_work_peak_trial_ledgers
  rollback_tokens
  provisional_intents
  prepare_eligibility
```

```text
SystemTransactionBundle:
  parent_state_id / receipt_id
  final_candidate_hash
  four_B_provisional_intents
  all_internal_A_provisional_intents
  one_shared_DamageStore_intent
  C_path_pose_state_intent
  event_damage_cascade_intent
  work_energy_error_intent
  curve_peak_milestone_intent
  version_transform_unit_replay_manifest
  prepare_tokens
  global_idempotency_key
```

```text
SystemEventRecord:
  event_id / hierarchy / entity_id / source_event_ids
  path_kind / dimensional_event_value / units
  path_bracket / event_fraction / fraction_basis
  pre_event_accepted_state_id
  event_point_trial_id
  post_event_accepted_state_id_optional
  one_sided_states
  simultaneous_group_id / causal_dependencies
  DamageStore_pre_trial_post_versions
  pre_point_post_wrench_pose_graph
  recovery / stability / certification
  localization_error
  committed / commit_receipt_id_optional
```

```text
StandaloneValidationRequest:
  profile = A_SINGLE_SPINE | B_ARRAY_UNIT
  independent_run_id
  immutable_surface_geometry_parameter_bindings
  standalone_accepted_state_handle_optional
  independent_DamageStore_branch
  path_control_and_requested_raw_outputs
  deterministic_replay_request
```

```text
StandaloneValidationRecord:
  profile = A_SINGLE_SPINE | B_ARRAY_UNIT
  independent_run_id
  immutable_bindings
  standalone_accepted_state_handle
  complete_raw_path_and_event_history
  equivalence_boundary_reference
  DamageStore_branch
  receipts / hashes / certification
```

### 5.3 事务不变量

- trial、Newton、线搜索、事件定位、DamageStore fixed point 和同位置级联均从同一 parent accepted state 构造。
- trial 之间不得串接未接受 A/B/C 历史。
- `prepare` 只验证版本、读写集合、候选哈希和持久化可用性。
- 全局 commit 要么同时提交 C、四个 B、全部 A、一个 `DamageStore`、事件、功、曲线和峰值，要么全部回滚。
- 同一幂等性键重复请求只能返回原收据或安全拒绝，不能重复累计历史。

## 6. 全局变量字典

下列表中的“生命周期”同时规定提交与回滚规则。`accepted` 表示只在原子提交后演化；`trial` 表示可回滚；`immutable` 表示运行内只读；`derived` 表示不得反写；`unresolved` 表示不得用默认零值替代。

### 6.1 身份、表面、几何和配置

| 规范名/符号 | 类型 | 物理含义与方向 | 所有者 → 消费者 | 坐标/参考点/单位 | 生命周期 | A/B/C 原字段或别名 |
|---|---|---|---|---|---|---|
| `SurfaceRealization` | opaque object | 150 mm × 150 mm 高度场主线或完整网格分支；原始几何不被损伤修改 | A1 → A/B/C/system | 全局/表面坐标；mm | immutable | 同名 |
| `A1QueryHandle` | opaque handle | 高度/三维几何、法向、坡度、曲率、域、质量、邻域查询 | A1 → A | 返回全局几何量 | immutable logical; cache ephemeral | 同名 |
| `CompositeNeedleGeometry` | record | 球冠、锥段、针杆、安装座和安全间隙；仅球冠承载 | A → B | 针/基座坐标；mm、rad | immutable | `TipGeometry`, `NeedleBodyGeometry` |
| `SpineParameterBundle` | versioned record | 接触、摩擦、梁、弹簧、材料、损伤、针体强度和数值配置 | A → B/system | N、mm、MPa、N/mm 等 | immutable/unresolved fields explicit | 同名 |
| `B1UnitConfiguration` | opaque/config record | 阵列格点、实际针长、角度模式、拓扑、安装模式和哈希 | B1 → B/C/system | `F_A`；mm、rad | immutable | 同名 |
| `NeedleStaticRecord[i]` | record | 针 ID、格点、轴、实际 `L_i,d_i,R_t` 和参数绑定 | B1 → A/B | `F_A/F_N`；mm、rad | immutable | 同名 |
| `CGeometryBinding` | record | C、四个 `O_i/O_Ai`、安装旋转、加载点和偏置 | C → system | `F_G`；mm | immutable | 同名 |
| `TransformRecord` | versioned record | 源/目标坐标、源/目标参考点、旋转、平移和版本 | system/C/B | 明确声明 | immutable | `T_C_from_A`, `T_UA`, `R_Gi` |
| `SystemBoundaryManifest` | record | 法向执行器、径向驱动、加载器和真实约束的对象、端点、作用线和授权 | external/C → system | `F_G`；N、N·mm、mm | immutable；缺失为 unavailable | `normal_actuator_boundary_manifest`, `authorized_constraint_manifest` |
| `P_i` | scalar[4] | 第 i 单元恒主动广义推力，正值作用于单元为 `-P_i E_Z` | external/C → B | N | immutable per run or explicit control transition | `P_i_N`, `P_z` |

### 6.2 A 单刺层变量

| 规范名/符号 | 类型 | 物理含义与方向 | 所有者 → 消费者 | 坐标/参考点/单位 | 生命周期 | A/B/C 原字段或别名 |
|---|---|---|---|---|---|---|
| `AcceptedSingleSpineState` | opaque state | 单刺可逆机械状态和不可逆历史 | A → B/C manifest | 声明坐标/参考点 | accepted only | `immutable_single_spine_state_n` |
| `T_B`, `Δξ_B` | pose/twist | B 规定的针基座位姿和增量；embedded 不含针级恒力 | B → A | 声明参考点；mm、rad | trial input | `base_pose_n`, `prescribed_base_increment` |
| `g_j` | scalar | 支持间隙；`g>0` 分离，`g=0` 接触边界 | A1/A → B summary | 接触支持；mm | trial/accepted raw | `legal_cap_gap`, `effective_gap` |
| `f_j` | vector | 墙面对针的接触力；法向从墙指向针/自由空间 | A → B | `F_G` 或接触基；N | trial/accepted raw | `contact_force_by_support` |
| `λ_nj, λ_tj` | scalar/vector | 正法向乘子和切向摩擦乘子 | A | 接触基；N | trial/accepted raw | 同名/normal and tangential multipliers |
| `Δs_j`, `ℓ_s` | vector/scalar | 客观切向滑移增量和累计弧长；支持迁移可为零滑移滚动 | A → B summary | 接触切基；mm | increment trial; cumulative accepted | `objective_slip_increment`, `accumulated_slip` |
| `η_b=(u_b,θ_b)` | vector | 露出针梁变形；bending off 时为零但强度仍检查 | A | 针/全局；mm、rad | trial/accepted reversible | `beam_tip_translation/rotation` |
| `δ_s`, `r_H` | scalar | 针级轴向弹簧压缩和 4 mm 硬限位反力 | A → B | 针轴；mm、N | trial/accepted reversible; hard-stop event | `spring_compression`, `hard_stop_reaction` |
| `DamageIntent_A` | opaque intent | A 材料律产生的单调 trial 损伤更新 | A → B/A coordinator | 材料面片坐标 | trial only; commit in batch | `trial_damage_intents` |
| `W_AonB^{O}` | wrench | 单刺 A 子系统对背板 B 的净作用；梁/弹簧/限位已包含 | A → B | 声明 frame 和 `O`；N、N·mm | trial/accepted output | `wrench.direction=A_on_B` |
| `R_x` | scalar | 正抓附阻力，`R_x=-e_x·F_AonB` | A/B derived | 单元局部 x；N | derived | `grip_resistance_Rx` |
| `K_A`, `G_A` | matrix/graph | 位姿—wrench 光滑切线、一侧切线、割线或集合值约束图 | A → B | 行为 wrench；列为规定增量 | trial/accepted-derived, validity-bound | `tangent_or_secant_matrix`, `admissible_wrench_graph_handle` |
| `AEventSet` | event set | 接触、滑移、迁移、材料、强度、限位、释放和再挂接候选 | A → B | 原始有量纲量和 fraction | trial; committed by upper transaction | `all_event_candidates`, `simultaneous_event_set` |
| `ATrialTransaction` | handles | trial handle、rollback token、provisional intent | A → B | opaque | trial/prepare/commit | `transaction` |

### 6.3 B 阵列单元层变量

| 规范名/符号 | 类型 | 物理含义与方向 | 所有者 → 消费者 | 坐标/参考点/单位 | 生命周期 | A/B/C 原字段或别名 |
|---|---|---|---|---|---|---|
| `q_U=[u_x,u_z]^T` | vector | 当前 B 1.0 认证的共同背板坐标；`+u_z` 远离墙面 | B/C → A | `F_A/O_A`；mm | accepted/trial | 同名 |
| `r_z` | scalar | `E_Z^T F_U-P_i`；唯一分支法向平衡残量 | B → C | N | trial/accepted diagnostic | 同名 |
| `N_U` | graph | 刚性/退化 normal resultant admissible graph | B → C | N | trial/accepted-derived | `normal_resultant_graph_handle` |
| `u_z(P_i,u_x)` | scalar/graph state | B 在 `UX_PZ_BALANCED` 中求得的共同法向位置 | B → C | mm | trial then accepted | `u_z_solution_if_solved` |
| `W_U^{O_A}` | wrench | 全部针 `A_on_B` 运输到 `O_A` 后的 contact-only 净和 | B → C | declared frame, `O_A`; N、N·mm | trial/accepted | `contact_only_wrench` |
| `R_x^U` | scalar | 单元 x 位移控制反力/抓附阻力 | B → C | 局部 x；N | derived | `control_reactions.R_x_N` |
| `R_y^c, M^c` | force/moment | 当前禁止 y/转动自由度的约束反力诊断 | B → C | 单元基；N、N·mm | derived; not contact assembly | `constraints` |
| `UnitAcceptedSnapshot` | opaque state | B 单元状态，内含全部 A opaque states 和历史引用 | B → C/system | `q_U` + versions | accepted only | `opaque_accepted_unit_snapshot_handle` |
| `UnitCapabilityState` | opaque/local operator | 绑定历史、姿态、分支、DamageStore 和 trust region 的局部算子 | B → C | `F_A/O_A`; N、N·mm | derived from accepted; invalidated by dependencies | 同名/capability |
| `K_Wq^raw`, `K_W,x|P` | matrix | raw 2-DOF 单元切线及恒推力凝聚切线 | B → C | declared row/column bases | trial/derived; branch-bound | `raw_K_Wq`, `condensed_K_W_x_given_P_i` |
| `BEventSet` | event set | 单元内部最早事件、同时组、事件后一侧和级联 | B → C | path fraction + raw quantities | trial; committed globally | `events` |
| `BTrialTransaction` | handles | rollback、provisional intent、读写集合和 prepare eligibility | B → C | opaque | trial/prepare | `transaction` |

### 6.4 C 与系统层变量

| 规范名/符号 | 类型 | 物理含义与方向 | 所有者 → 消费者 | 坐标/参考点/单位 | 生命周期 | C 原字段或别名 |
|---|---|---|---|---|---|---|
| `s` | scalar | 四单元共同向中心搜索坐标，`u_xi=s` | C → B/system | 各局部 +x；mm | accepted/trial path | `COMMON_SEARCH_S` |
| `s_stop` | scalar | 合格预紧原子提交后冻结的共同径向坐标 | C/system | mm | accepted immutable during load | `s_stop_mm` |
| `δ_P` | scalar | 加载点沿规定方向的偏心位移路径坐标 | C/system | P 点；mm | accepted/trial path | `ECCENTRIC_LOAD_DELTA_P` |
| `q_C=[u_X,u_Y,u_Z,θ_X,θ_Y,θ_Z]` | vector | 十字刚体位姿；首版 `θ_Z=0` | C/system | C；mm、rad | accepted/trial | 同名 |
| `η_i` | scalar[4] optional | 经机构绑定的法向执行器相对行程；不是针级弹簧 | C/external | 端点作用线；mm | unavailable unless certified | 同名 |
| `Q_s^drive` | scalar | 共同径向驱动所需正反力，`ΣR_xi` | C/system | 与 `s` 共轭；N | derived/accepted ledger | 同名 |
| `p_X,p_Y,Δ_X,Δ_Y` | scalars | 对置预紧与不平衡诊断，不替代完整 wrench | C/system | N | derived | `pair_preload_and_imbalance` |
| `W_i^{G,C}` | wrench[4] | 各 B contact-only wrench 运输到 C 后的值 | C/system | `F_G`, C；N、N·mm | trial/accepted | `contact_only_W_i_at_C` |
| `W_contact^{G,C}` | wrench | 四单元 contact-only 和，恰好装配一次 | C/system | `F_G`, C；N、N·mm | trial/accepted | `summed_contact_only_W_at_C` |
| `λ_P` | scalar | 加载器作用于爪体的功共轭反力幅值 | C/system/experiment | P 点方向；N | trial/accepted | `lambda_P`, `F_reaction` |
| `W_load^{G,C}` | wrench | `λ_P[d; r_P×d]`，加载器作用于爪；爪对加载器取负 | C/system | `F_G`, C；N、N·mm | trial/accepted | `loading_W` |
| `μ_rig, μ_mode` | multipliers | 真实授权试验架约束和模式约束乘子 | C/system | 对应广义坐标 | trial/accepted diagnostic | `mode_and_rig_multipliers` |
| `r_W/G_W` | residual/graph | 理论偏心加载六维平衡或集合值包含关系 | C/system | C；N、N·mm 分块 | trial; accepted only if certified | `residual_or_graph` |
| `CUnitContinuationCapsule` | opaque local object | 单元局部响应、graph、事件距离和回调条件 | C/system | bound metadata | derived; invalidation strict | `capsule_handles` |
| `F_crit` | scalar/null | 稳定可达分支上反力上确界；证据闭合才确认 | C/system/experiment | N | derived final result | `CMaximumCapacityResult.F_crit_N` |

### 6.5 共享历史、质量、实验和事务变量

| 规范名 | 类型 | 物理含义 | 所有者 → 消费者 | 单位/参考 | 生命周期 | 源字段 |
|---|---|---|---|---|---|---|
| `DamageStore` | opaque shared store | 固定材料坐标中的轻量不可逆损伤历史 | A material; B/C schedule → system | patch/material frame | accepted only; trial copy rollback | 同名 |
| `EventLedger` | append-only ledger | 所有原始事件、括区间、同时组、前/点/后状态和收据 | A/B/C sources; C/system commits | mixed dimensional values | accepted only | `event_ledger_handle` |
| `WorkEnergyLedger` | ledger | 外部功、层间端口审计、储能、耗散、释放能和数值误差 | A/B/C/system | N·mm | accepted only | `work_energy_error_ledger` |
| `RawCurveStore` | append-only series | 未滤波 accepted 力—位移/姿态/状态曲线 | C/system | declared units | accepted only | `accepted_curve_handle` |
| `PeakLedger` | ledger | 全部局部峰、尖峰、平台、多峰和当前观测最大值 | C/system | N、mm | accepted only; candidates trial | `peak_ledger` |
| `QualityBundle` | record | 残量、域、几何、碰撞、模型、参数、稳定性、不确定性 | producing layer → system | raw units + normalized diagnostics | trial/accepted | `diagnostics`, `quality_and_certification` |
| `CommitReceipt` | immutable receipt | 证明 A/B/C/DamageStore/账本原子可见的版本组合 | transaction layer → all | IDs/hashes | immutable accepted | 同名 |
| `ReplayManifest` | record | 输入、调用、浮点归约、版本和哈希的确定性重放清单 | system | no unit | immutable per accepted step | `deterministic_replay_manifest` |
| `ExperimentSample` | raw record | 传感器、位移、姿态、事件、状态、质量和不确定性 | experiment/system | declared | immutable raw | C public outputs / A/B histories |
| `TimeMapping` | function/status | A/B 为 `t=x/(1 mm/s)`；C 速度未固定时 unavailable | external/system | s | derived only if protocol exists | `physical_time`, C time channel |


---

# 第四篇：坐标、参考点、单位、作用—反作用与功

## 7. 唯一坐标和参考点链

### 7.1 坐标系

全局右手系为

\[
\mathcal F_G=\{C,\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
\]

墙面名义平面为 X–Y，`+Z` 从墙面指向背板和自由空间。第 i 个单元工程局部系和 B 公共阵列系分别为

\[
\mathcal F_i=\{O_i,\mathbf e_{x_i},\mathbf e_{y_i},\mathbf E_Z\},
\qquad
\mathcal F_{A_i}=\{O_{A_i},\mathbf e_{x_i},\mathbf e_{y_i},\mathbf E_Z\},
\]

其中

\[
\mathbf e_{y_i}=\mathbf E_Z\times\mathbf e_{x_i}.
\]

正式编号为：

| 单元 i | `e_xi` | `e_yi` | 工程参考点 `O_i` |
|---:|---|---|---|
| 1 | `+E_X` | `+E_Y` | `C-40 E_X` |
| 2 | `-E_X` | `-E_Y` | `C+40 E_X` |
| 3 | `+E_Y` | `-E_X` | `C-40 E_Y` |
| 4 | `-E_Y` | `+E_X` | `C+40 E_Y` |

局部到全局旋转为

\[
\boxed{
\mathbf R_{Gi}=
\begin{bmatrix}
\mathbf e_{x_i}&\mathbf e_{y_i}&\mathbf E_Z
\end{bmatrix},
\quad
\mathbf R_{Gi}^{\mathsf T}\mathbf R_{Gi}=\mathbf I,
\quad
\det\mathbf R_{Gi}=+1.
}
\]

第 i 个单元第 j 根针的针轴框架为 `F_Nij`，接触支持 k 的局部框架为

\[
\mathcal F_{C_{ijk}}=\{\mathbf n_{ijk},\mathbf t_{1,ijk},\mathbf t_{2,ijk}\}.
\]

针轴从安装座出口指向球心：

\[
\boxed{
\mathbf a_{ij}
=
\cos\alpha_{ij}\cos\beta_{ij}\,\mathbf e_{x_i}
+
\cos\alpha_{ij}\sin\beta_{ij}\,\mathbf e_{y_i}
-
\sin\alpha_{ij}\,\mathbf E_Z.
}
\]

当前正式扫描 `β=0`，但底层字段必须保留 `β`。

### 7.2 `O_i`、`O_A`、C 和 P

- `O_i` 是工程单元安装参考点；
- `O_Ai` 是 B 的唯一公共单元 wrench 参考点，即未加载规则针尖球心格点的几何中心；
- 两者不得默认重合。

定义局部偏置

\[
\boldsymbol\rho_{A/i}^{i}=\overrightarrow{O_iO_{A_i}}.
\]

预紧参考构型中，从 C 到 `O_Ai` 的向量为

\[
\boxed{
\mathbf r_{A_i/C}^{0}
=-40\,\mathbf e_{x_i}
+\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i}.
}
\]

只有当绑定文件明确给出 `ρ_A/i=0`，且参考点 ID、几何哈希和版本完全一致时，才允许令 `O_Ai=O_i`。

加载点 P 相对 C 为

\[
\boxed{
\mathbf r_P^0=50\,\mathbf E_Z\ {\rm mm},
\qquad P=C+\mathbf r_P^0.
}
\]

中央 80 mm × 80 mm 区域不与墙面接触；它仅通过 `r×F` 形成力臂。

### 7.3 刚体变换链

系统记录的规范变换链为

\[
{}^G\mathbf T_{N_{ij}}
=
{}^G\mathbf T_C
{}^C\mathbf T_{O_i}
{}^{O_i}\mathbf T_{A_i}
{}^{A_i}\mathbf T_{N_{ij}}.
\]

当前 B 1.0 中：

- `{}^C T_Oi` 和安装方向为静态；
- B 只认证单元局部 x 与全局 Z 平移；
- 不允许通过改变坐标表达来伪装真实姿态更新。

理论偏心加载中，当前刚体关系为

\[
\mathbf r_{A_i/C}^{G}=\mathbf R_C\mathbf r_{A_i/C}^{0},
\qquad
\mathbf p_{A_i}^{G}=\mathbf p_C+\mathbf r_{A_i/C}^{G},
\]

但把该动态姿态传入 B 需要尚未接受的 B 2.x 完整 twist 接口。

## 8. Wrench 运输、Jacobian 对偶和功不变

### 8.1 通用参考点运输

设源 wrench 在源坐标 `F_s`、源参考点 `O_s` 表达，目标坐标为 `F_t`、目标参考点为 `O_t`。定义

\[
\mathbf r_{O_s/O_t}^{t}=\overrightarrow{O_tO_s}
\]

在目标坐标中的表示，则

\[
\boxed{
\begin{aligned}
\mathbf F_t&=\mathbf R_{ts}\mathbf F_s,\\
\mathbf M_t^{O_t}
&=\mathbf R_{ts}\mathbf M_s^{O_s}
+\mathbf r_{O_s/O_t}^{t}\times\mathbf F_t.
\end{aligned}
}
\]

只旋转力、不旋转力矩，或遗漏参考点平移项，均为合同错误。

### 8.2 A→B 装配

第 j 根针的 A 公共输出是 `A_on_B`：

\[
\mathbf W_{A_{ij}\rightarrow B_i}^{O_{ij}}
=
\begin{bmatrix}
\mathbf F_{ij}\\
\mathbf M_{ij}^{O_{ij}}
\end{bmatrix}.
\]

B 必须将每个净 wrench 运输到同一 `O_Ai` 后恰好求和一次：

\[
\boxed{
\mathbf W_{U_i}^{O_{A_i}}
=
\sum_j
\mathcal T_{O_{ij}\rightarrow O_{A_i}}
\mathbf W_{A_{ij}\rightarrow B_i}^{O_{ij}}.
}
\]

`W_Ui` 已包含接触、针梁、针级弹簧和硬限位内部反力的净结果。B 不得再加这些分量。

### 8.3 B→C 装配

第 i 个单元的 contact-only wrench 运输到 C：

\[
\boxed{
\begin{aligned}
\mathbf F_i^{G,C}&=\mathbf R_{G S_i}\mathbf F_i^{S_i},\\
\mathbf M_i^{G,C}&=
\mathbf R_{G S_i}\mathbf M_i^{S_i,O_A}
+\mathbf r_{A_i/C}^{G}\times\mathbf F_i^{G,C}.
\end{aligned}
}
\]

其中 `S_i` 是 B 响应显式声明的源表达坐标；在当前静态安装的 B 1.0 局部坐标响应中，`S_i=\mathcal F_{A_i}` 且 `\mathbf R_{G S_i}=\mathbf R_{Gi}`。若响应声明其他源坐标，必须使用同一版本的显式变换，不能靠名称推断。

整爪 contact-only wrench 为

\[
\boxed{
\mathbf W_{\rm contact}^{G,C}
=
\sum_{i=1}^{4}\mathbf W_i^{G,C}.
}
\]

每个 B wrench 只运输和装配一次。当前唯一装配策略 ID 为

```text
CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1
```

### 8.4 完整 twist 与 Jacobian 对偶

理论 C 刚体增量

\[
\Delta\boldsymbol\xi_C^G
=
\begin{bmatrix}
\Delta\mathbf u_C^G\\
\Delta\boldsymbol\theta^G
\end{bmatrix}
\]

在 `O_Ai` 产生

\[
\Delta\mathbf u_{A_i}^{G}
=
\Delta\mathbf u_C^G
+
\Delta\boldsymbol\theta^G\times\mathbf r_{A_i/C}^{G}.
\]

单元局部完整 twist 为

\[
\boxed{
\Delta\boldsymbol\xi_{A_i}^{i}
=
\mathbf J_i\Delta\boldsymbol\xi_C^G,
\qquad
\mathbf J_i=
\begin{bmatrix}
\mathbf R_{iG}&-\mathbf R_{iG}[\mathbf r_{A_i/C}^{G}]_\times\\
\mathbf0&\mathbf R_{iG}
\end{bmatrix}.
}
\]

Wrench 对偶为

\[
\boxed{
\mathbf W_i^{G,C}=\mathbf J_i^{\mathsf T}\mathbf W_i^{i,O_A}.
}
\]

必须检查

\[
\boxed{
\left(\mathbf W_i^{i,O_A}\right)^{\mathsf T}
\Delta\boldsymbol\xi_{A_i}^{i}
=
\left(\mathbf W_i^{G,C}\right)^{\mathsf T}
\Delta\boldsymbol\xi_C^G.
}
\]

检查必须同时使用原始有量纲绝对误差和版本化相对误差。该式不授权 B 1.0 接受完整 twist；它只是坐标和功一致性条件。

## 9. 力、反力、主动输入和作用—反作用

| 量 | 规范方向与定义 | 所有权 | 是否进入 C contact-only 总和 |
|---|---|---|---:|
| 接触力 `f_j` | 墙面对针；法向从墙指向针/自由空间 | A | 通过 `A_on_B` 净 wrench 间接进入一次 |
| `A_on_B` | 单刺 A 子系统对 B 背板的净作用 | A 输出，B 消费 | 是，经 B 求和一次 |
| `B_on_A` | `-A_on_B` | A 作用—反作用检查 | 否 |
| 单元 `contact_only_wrench` | 全部 `A_on_B` 在 `O_A` 的和 | B | 是，经 C 运输一次 |
| `R_x` | `-e_x^T F_U`；正值抵抗 `+x` 拖拽/搜索 | B/A derived | 不作为第二份 wrench；用于驱动反力和输出 |
| `P_i` | 正值时主动广义力作用于单元为 `-P_i E_Z` | 外部/C 输入，B 平衡 | 否；它是控制参数，不是第二份墙面力 |
| `r_zi` | `E_Z^T F_i-P_i` 或 normal graph 距离 | B | 否；平衡残量 |
| `Q_s^contact` | `Σ e_xi^T F_i = -ΣR_xi` | C derived | 否；contact-only 对共同 s 的广义力 |
| `Q_s^drive` | `-Q_s^contact=ΣR_xi` | C/径向驱动 | 否；独立功通道 |
| `λ_P` | 加载器作用于爪体、沿规定正位移方向的力幅值 | C/加载器 | 作为独立外部 loading wrench |
| 爪对加载器 | `-λ_P b_P`；力和力矩同时反号 | C/实验 | 传感器反力约定 |
| B x 控制反力 | 维持规定 `u_x` 的反力诊断 | B | 否 |
| B y/转动约束反力 | 当前运动子空间被禁止方向的诊断 | B | 否；不得解释为额外爪刺承载 |
| C 真实约束反力 | 仅在系统边界清单明确授权时允许非零 | C/实验架 | 独立分栏；不得隐藏 |
| 未授权模式乘子 | 必须为零；非零时拒绝候选 | C | 不得加入平衡能力 |

加载方向和加载器 wrench 为

\[
\hat{\mathbf d}_X=\mathbf E_X,
\qquad
\hat{\mathbf d}_{45}=\frac{\mathbf E_X+\mathbf E_Y}{\sqrt2},
\]

\[
\boxed{
\mathbf b_P(\hat{\mathbf d})=
\begin{bmatrix}
\hat{\mathbf d}\\
\mathbf r_P^G\times\hat{\mathbf d}
\end{bmatrix},
\qquad
\mathbf W_{\rm load}^{G,C}=\lambda_P\mathbf b_P.
}
\]

`F_reaction=λ_P` 表示加载器作用于爪体、与正位移共轭的幅值；爪体作用于传感器的 wrench 必须整体取负。

## 10. 单位、规范化和残量缩放

### 10.1 规范单位

| 量 | 规范单位 |
|---|---|
| 长度、位移、行程、事件括区间、损伤局部化位移 | mm |
| 力、平移广义反力 | N |
| 力矩、功、能量 | N·mm |
| 时间 | s |
| 角度 | rad |
| 应力、强度、弹性模量 | MPa = N/mm² |
| 平移刚度 | N/mm |
| 转动刚度 | N·mm/rad |
| 断裂能 | N/mm |
| 无量纲裕度、利用率、事件分数、置信度 | 1 |

### 10.2 唯一换算边界

- 针尖 `50/100 μm` 在配置进入 A/B 内核前唯一转换为 `0.05/0.10 mm`；
- 弹簧 `100–2000 N/m` 在配置进入内核前唯一转换为 `0.1–2.0 N/mm`；
- 角度在三角函数前唯一转换为 rad；
- 下游公共接口只传规范值和规范单位，C/系统不得再次换算；
- 输入原值、原单位、转换器版本和转换结果必须保留用于审计。

### 10.3 残量缩放

N 与 N·mm 不得直接组成未缩放欧氏范数。六维残量可使用版本化尺度矩阵

\[
\widehat{\mathbf r}_W=\mathbf S_W\mathbf r_W,
\]

其中 `S_W` 必须绑定明确长度尺度和 `residual_scaling_id/version`。接受判据仍必须逐个原始物理分量检查。归一化量只服务数值求解，不能替代有量纲事件阈值或物理结论。

## 11. 系统功和能量去重账本

### 11.1 账本边界

系统必须同时维护：

1. **外部边界功账本**：径向驱动、四个法向执行器、偏心加载器和真实授权约束；
2. **层间端口审计账本**：A_on_B 和 B contact-only 的 wrench–twist 功，用于检查运输和装配，不再加入外部功总和；
3. **A 内部能量账本**：接触、针梁、针级弹簧储能，摩擦/材料耗散和释放能；
4. **数值误差账本**：残量、积分、事件定位和浮点归约误差，绝不能解释为物理耗散。

### 11.2 唯一功通道

| 通道 | 增量定义 | 唯一所有者 | 系统求和规则 |
|---|---|---|---|
| A 基座输入功 | `-W_AonB · dξ_B` | A | 层间端口审计；不与 B/C 外部功再相加 |
| A 接触/梁/弹簧储能 | `dU_c,dU_b,dU_s` | A | 作为内部储能一次 |
| 摩擦耗散 | `dD_f≥0` | A | 一次 |
| 材料损伤耗散 | `dD_m≥0` | A | 一次 |
| 释放可恢复能 | `dE_returned≥0` | A | 单列，不计摩擦或材料耗散 |
| 理想硬限位/刚性约束 | 相对约束方向位移为零时功为零 | A/B | 不创建第二份能量 |
| B standalone 控制功 | `R_x du_x-P_i du_z` | B driver | standalone 外部功；与 A 端口功做一致性检查，不重复求和 |
| C 径向驱动功 | `dW_s=Q_s^drive ds` | C | C 预紧外部功一次 |
| 法向理想广义力功 | `dW_Pi^ideal=-P_i du_zi^port` | B/C | 审计量；真实端点未绑定时不升级为完整执行器功 |
| 法向认证相对功 | `dW_Pi^cert=P_i dη_i` | 外部/C | 仅当端点、作用线、对象和符号认证后进入外部总功 |
| 偏心加载器功 | `dW_load=λ_P dδ_P` | C | 偏心阶段外部功一次 |
| 真实授权约束功 | `μ dq_constraint` | C/实验架 | 独立分栏；理想零位移约束应为零 |
| 未授权乘子功 | 诊断 | C | 必须为零；非零则候选拒绝 |
| 数值误差 | `ε_work, ε_quad, ε_float` | 各求解层 | 单列，不补足物理耗散 |

### 11.3 trial、释放和同位置级联

- trial、Newton、回溯、事件定位和 rollback 不累计任何物理功、储能差量或耗散。
- 释放时可逆梁/弹簧/接触能按 A 规则记入 `released_recoverable_energy`；损伤、累计滑移和耗散不回退。
- 同位置级联允许 `dχ=0` 而 `du_z`、姿态或 `dη_i` 非零，因此路径驱动功可为零，但法向执行器功和低层能量变化不必为零。
- 级联 fixed point 完成并全局 commit 前，全部账本量保持 trial 状态。

---

# 第五篇：模块接口与全局 schema

## 12. A→B 精确映射

### 12.1 唯一入口

B 只能调用：

```text
embedded_constitutive_trial / evaluate_trial(
  EmbeddedSingleSpineTrialRequest
) -> SingleSpineTrialResponse
```

A standalone driver 不属于 A→B 接口。embedded 请求中出现 `per_spine_normal_force`、`single_spine_Pz` 或等价逐针 `0.5 N` 字段时，必须返回 `CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD`。

### 12.2 请求映射

| A 请求字段组 | B 的生产来源 | A 的使用 | 系统约束 |
|---|---|---|---|
| 合同、模型和 trial identity | B 全阵列 trial | 版本、幂等和陈旧校验 | 调用顺序 ID 只审计，不影响物理 |
| `needle_identity` | `NeedleStaticRecord` | 绑定几何、结构、材料和强度参数 | 针 ID 唯一；终止针仍保留 fast path |
| `surface_query_handle` | B 配置中的 A1 bundle | 几何、域、质量和碰撞查询 | 原始表面只读 |
| `base_pose_n`, `prescribed_base_increment` | B 当前共同背板运动 | A 本征边界 | 当前只允许局部 x 与全局 Z 平移 |
| `immutable_single_spine_state_n` | B 的 A opaque bundle | 读取 accepted 单刺历史 | B/C 不得解析修改 |
| `shared_damage_store_snapshot` | B 当前共同快照 | 读取材料历史，输出 intents | 同一试探轮全部针读同一版本 |
| `parameter_bundle` | B immutable config | 接触/结构/材料/强度/数值 | 缺失项显式 unavailable |
| tangent/event/quality request | B2/B3 求解需求 | 返回切线/graph、事件和质量 | 不得关闭致命检查 |
| continuation hint | A 上次返回的 opaque 句柄 | 分支连续性 | B 不得改写 |

### 12.3 响应映射

| A 响应字段组 | B 的规范消费 | B 不得做 |
|---|---|---|
| `wrench.direction=A_on_B` | 运输到 `O_A` 并求和一次 | 再换号后以同方向装配；另加梁/弹簧/接触力 |
| 几何/逐支持接触 | 形成活动集、事件、质量和原始历史 | 重新求法向、平均多支持或把碰撞当承载 |
| 梁/弹簧/硬限位/强度 | 保存状态、行程、事件、能量摘要 | 再建等效梁/弹簧/限位反力 |
| 材料、Damage intents 和耗散 | 构造读写冲突图，交给 A 协调器 | 直接写 DamageStore、增量相加或取最大 |
| 状态和事件 | 归约针级最早事件和单元同时组 | 用总 if/else 删除并发事件 |
| tangent/secant/graph | B2 Newton、凝聚和能力局部预测 | 强制对称、跨事件外推、把代表值当唯一 |
| diagnostics/error class | 致命筛查、失败分类和质量传播 | 将 unavailable/numerical 改写为零承载或物理失效 |
| transaction handles | B trial/prepare/rollback | 在单元或 C 未接受前提交 |

### 12.4 A→B 状态和事务映射

```text
AcceptedSingleSpineState_n
  -> read-only A trial
  -> TrialStateHandle + DamageIntent + RollbackToken + ProvisionalIntent
  -> B common equilibrium/event/damage checks
  -> prepare as part of unit/global batch
  -> atomic commit or rollback
```

A 负责损伤律；B 负责多针冲突分组和共同重求；C 负责跨单元 fixed point 和全局提交时机。

## 13. B→C 精确映射

### 13.1 唯一入口和事务端点

C 的唯一 B 物理入口：

```text
embedded_array_unit_trial(request) -> EmbeddedUnitTrialResponse
```

事务控制端点只执行 prepare/commit/rollback，不构成第二个物理入口：

```text
prepare_embedded_unit_commit(...)
commit_global_B_bundle(...)
rollback_embedded_unit_trial(...)
```

### 13.2 C→B 请求映射

| 请求字段组 | C 的来源 | B 的消费与限制 |
|---|---|---|
| identity/versions/hashes | `SystemAcceptedState` 和 immutable manifest | 校验合同、配置、参数、状态和幂等性 |
| B/A accepted handles | C accepted low-level bundle | 只读；不得由 C 修改 |
| shared `DamageStore` | 同一 accepted 快照 | 四单元应读取同一版本 |
| `P_i` | C/external immutable control | B 外层平衡一次；不得广播为逐针力 |
| control mode | C 阶段 | B 1.0 仅 `UX_PZ_BALANCED` 或 `PRESCRIBED_XZ_RESIDUAL` |
| target x/Z motion | C 同步预紧或受限耦合 | 每个候选事件位置完整重求 |
| frame/reference/transform | C geometry binding | B 输出 `O_A` contact-only；动态转动当前拒绝 |
| event/tangent/capability request | C 求解和审计 | B 可升级为完整逐针重求 |
| replay and cross-unit context | system/C | 确定性输出和跨单元损伤协调 |

C 请求不得包含逐针力、`P_i/N`、逐针活动集、经验载荷转移、C 自算损伤、A/B 参数覆盖或未声明单位。

### 13.3 B→C 响应映射

| B 响应字段组 | C 的规范消费 | 失效条件 |
|---|---|---|
| response identity | 绑定全局 trial、单元和版本 | 任一不匹配即 stale/contract error |
| contact-only wrench | 运输到 C 并装配一次 | 参考点、frame、方向或单位不明时不得装配 |
| action line/CoP/free couple | 仅作原始诊断和实验输出 | 不存在或非唯一时必须 unavailable |
| active/control/constraint fields | 独立分栏 | 不得加入 contact-only 总和 |
| balance residual/normal graph | C 预紧接受和耦合残量 | 未通过不能标 balanced |
| raw/condensed tangent、secant、graph | 局部预测或 Newton | 分支、trust region、姿态、DamageStore 或事件变化即失效 |
| state summary and raw per-needle handles | 事件、退化、实验输出 | 状态标签不得代替原始量 |
| remaining travel and recoverability | 安全门控和后续路径 | standalone 余程不得当作 C 搜索上限 |
| event groups and fraction | 全局最早事件和同时组 | C 不得丢弃 B 原始组 |
| DamageStore intents/read-write sets | 跨单元 fixed point | C 不得自行合并物理 |
| diagnostics/certification | 致命筛查和分类 | unavailable/numerical 不得转物理失效 |
| transaction handles | 全局 prepare/commit/rollback | 普通 trial 不得携带永久 commit 结果 |

### 13.4 `UnitCapabilityState` 的有效性

`UnitCapabilityState` 仅在以下全部不变时可用于 trust region 内局部预测：

- B/A accepted state；
- `DamageStore` 版本；
- 表面、参数和配置；
- 当前姿态、参考点和变换；
- 控制模式和 `P_i`；
- 活动集、粘滑、弹簧、材料、强度和恢复分支；
- branch、one-sided direction 和 trust region；
- 未跨事件括区间且未接近域/碰撞/模型边界。

任一条件变化，或需要精确损伤、作用线、恢复性、峰值、显著退化、局部 y、转动或 rocking 时，必须完整回调 B。

## 14. C→系统与实验公共 schema

### 14.1 顶层请求

```text
SystemRequest:
  identity:
    system_model_version
    run_id
    request_idempotency_key
  operation:
    INITIALIZE_PRELOAD
    ADVANCE_PRELOAD
    ADVANCE_ECCENTRIC_LOAD
    QUERY_ACCEPTED_STATE
    FINALIZE_CAPACITY_RESULT
  accepted_SystemAcceptedState_handle_optional
  design_surface_parameter_bindings
  P_i_N[4]
  preload_policy_and_s_max
  loading_direction_and_delta_P
  rocking_and_system_boundary
  event_damage_stability_peak_branch_numerical_configs
  requested_raw_outputs
  deterministic_replay_request
```

### 14.2 顶层响应

```text
SystemResponse:
  primary_status / all_status_codes
  stage
  accepted_SystemAcceptedState_handle | last_valid_state_handle
  canonical_CAcceptedState_handle
  path_and_pose
  preload_public_view
  reaction_wrenches_and_F_reaction
  four_unit_contact_only_distribution
  raw_B_response_handles
  events_damage_degradation_milestones
  work_energy_quality_uncertainty
  raw_curve_handle / peak_candidates
  maximum_capacity_result | unconfirmed_status
  versions / hashes / commit_receipt / replay_manifest
  contract_extension_requirement_optional
```

### 14.3 公开和内部字段

公开字段必须包括原始路径、位姿、完整 wrench、四单元分配、逐针/逐单元状态摘要、事件、DamageStore 版本、残量、质量、功、能量、不确定性、曲线、峰值候选和认证。Newton 缓存、线搜索工作区、未提交 DamageStore 内容、可变 opaque 对象、临时峰值拟合和内部令牌不得作为可修改公共状态。

## 15. 当前运动合同和 B 2.x 最小交接

### 15.1 当前支持表

| 运动/操作 | `B_TO_C 1.0.0` | 系统处理 |
|---|---:|---|
| 单元局部 x 平移 | 支持 | 正常 B trial |
| 全局 Z 平移/单元 z | 支持 | 正常 B trial |
| C 同步预紧 `u_xi=s` | 支持 | 可执行，停止策略另行认证 |
| 纯全局 Z 的构造测试 | 支持 | 仅验证用途 |
| 单元局部 y 平移 | 不支持 | `C_CONTRACT_EXTENSION_REQUIRED` |
| 单元真实转动 | 不支持 | 安全拒绝 |
| rocking `θ_X/θ_Y` | 不支持 | 安全拒绝 |
| 正式非零 `+X` | 不支持完整四单元运动 | 安全拒绝，零推进 |
| 正式非零 `45°` | 不支持完整四单元运动 | 安全拒绝，零推进 |
| 完整 6D tangent/graph | 不支持 | 不得由 x/Z 结果外推 |

### 15.2 B 2.x 最小扩展：`required extension / not accepted`

以下是实现交接所需的最小扩展要求，不是当前合同：

```text
required_upstream_extension:
  contract_id: B_TO_C
  required_major_version: 2
  status: REQUIRED_EXTENSION_NOT_ACCEPTED

  backward_compatibility:
    - all valid B_TO_C 1.0.0 x/Z requests retain identical semantics
    - existing reference points, units, status and transaction semantics remain
    - SE3 fields are mandatory only for SE3 modes

  new_control_modes:
    - PRESCRIBED_SE3_RESIDUAL
    - SE3_WITH_FORCE_BALANCED_NORMAL_STROKE  # optional, hardware-bound

  request_kinematics:
    - accepted_T_G_from_A
    - target_T_G_from_A or full_base_twist_increment[6]
    - frozen_internal_s_stop separate from rigid twist
    - local x/y/z and rotation components
    - optional eta_i with endpoint/boundary certification
    - SE3 interpolation and event-fraction basis

  geometry_surface_collision:
    - dynamic unit frame
    - updated needle axes and tip poses
    - full 3D collision/domain queries
    - rocking pose certification domain

  response:
    - contact_only_wrench_at_O_A[6]
    - full motion residuals and separated control/constraint reactions
    - raw/condensed/one-sided 6D tangent or admissible graph
    - rank/nullspace/branch/trust region
    - translation/rotation/collision/domain event candidates
    - action line / CoP / free-couple availability
    - capability, stability and full-callback requirements
    - wrench-twist power checks

  history_damage_transaction:
    - unchanged opaque A/B histories
    - shared DamageStore intents and fixed point
    - simultaneous event and cascade semantics
    - prepare / atomic commit / rollback / idempotency
```

正式接受门槛至少包括：B 1.0 x/Z 逐位兼容、任意小 twist 功对偶、6D tangent/一侧割线有限差分、动态姿态几何/碰撞/事件、DamageStore 确定性、最早事件重算、并行顺序不变、rollback 零累计和未支持运动保留 last-valid state。


---

# 第六篇：统一阶段、残量/graph 与单步算法

## 16. 路径、时间和阶段边界

### 16.1 四类路径不得混用

| 路径 | 规范坐标 | 物理范围/终点 | 时间映射 | accepted 历史所有者 |
|---|---|---|---|---|
| A 单刺 standalone | `x_A=u_x-u_x,start` | 连续 0–100 mm；脱离不重置 | `t=x_A/(1 mm/s)` | A standalone driver |
| B 单元 standalone | `χ_B=u_x-u_x,start` | 连续 0–100 mm；脱离不重置 | `t=χ_B/(1 mm/s)` | B standalone driver |
| C 同步预紧 | `s` | 由版本化停止策略和 `s_max` 限定；均未固定默认值 | 无固定速度时 `unavailable` | C/SystemAcceptedState |
| C 偏心加载 | `δ_P` | 从锁定 `s_stop` 出发，沿合法稳定可达分支推进 | 无固定速度时 `unavailable` | C/SystemAcceptedState |

A/B 的 100 mm 和 1 mm/s 只属于直线拖拽验证路径。C 不得继承该终点或速度。

### 16.2 C 主路径阶段转换

```text
PRELOAD_SEARCH
  -> PRELOAD_EVENT_RESOLUTION
  -> PRELOAD_SEARCH
  -> PRELOAD_ACCEPTED_LOCKED
  -> ECCENTRIC_CONTRACT_AUDIT
  -> ECCENTRIC_LOAD_TRIAL
  -> ECCENTRIC_EVENT_RESOLUTION
  -> ECCENTRIC_LOAD_ACCEPTED
  -> ...
  -> PHYSICAL_TERMINATED
```

异常分支：

```text
any trial stage
  -> UNCERTIFIED_STOPPED
  -> NUMERICAL_OR_TRANSACTION_STOPPED
```

异常停止保留最后一个有效 accepted state，不形成新的物理历史节点。`C_CONTRACT_EXTENSION_REQUIRED` 属于认证停止，且零路径推进。

## 17. 嵌套方程和变量角色

### 17.1 A 本征层

A 接受规定基座位姿/增量、accepted 单刺状态、共享损伤快照、A1 查询和参数包，返回本征 trial：

\[
\mathcal K_A^{\rm intrinsic}
(T_B^n,\Delta q_B,\mathsf Z_A^n,\mathcal D^n,\mathcal Q_{A1},\Theta_A)
\mapsto
\mathcal R_A^{\rm trial}.
\]

A embedded 中：

- 规定量：基座运动、表面/参数/历史快照；
- A 内部未知量：由 accepted A 模型拥有的接触、梁、弹簧、材料活动变量；
- 后处理：`A_on_B`、强度裕度、事件、切线/graph、质量和事务意图；
- 禁止量：逐针恒法向推力残量。

### 17.2 B 单元层

B 1.0 共同坐标为

\[
\mathbf q_U=[u_x,u_z]^{\mathsf T}.
\]

`UX_PZ_BALANCED` 中，给定 `u_x,P_i`，B 求 `u_z`：

\[
\boxed{
 r_z(u_z;u_x,P_i)=\mathbf E_Z^{\mathsf T}\mathbf F_U(u_x,u_z)-P_i=0
}
\]

或

\[
\boxed{
0\in\mathcal N_U(u_x,u_z)-P_i.
}
\]

`PRESCRIBED_XZ_RESIDUAL` 中 `u_x,u_z,P_i` 均规定，B 只返回 `r_z`/graph 距离；残量未通过时不得称为平衡。

B 的输出 `W_U`、`R_x`、约束反力、切线/graph、事件和能力均是同一全阵列解的输出，不是第二套方程。

### 17.3 C 同步预紧层

规定：`s*`、四个 `P_i`、rocking off、四个 accepted B/A snapshots 和同一 `DamageStore`。硬约束为

\[
\boxed{u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s.}
\]

B 分别求各 `u_zi` 或 normal graph。C 计算：

\[
R_{x_i}=-\mathbf e_{x_i}^{\mathsf T}\mathbf F_i,
\qquad
Q_s^{\rm drive}=\sum_iR_{x_i},
\]

以及完整 contact-only wrench、预紧质量和安全门控。`Q_s`、成对预紧和支承需求是后处理/控制反力，不是新的墙面接触力。

正常锁定仅当

\[
G_{\rm stop}=G_{\rm valid}\land G_{\rm plateau}\land G_{\rm gain}\land
G_{\rm weak}\land G_{\rm safe}\land G_{\rm persist}\land G_{\rm range}
\]

全部通过，并且事件、损伤、功、质量和原子提交闭合。阈值、窗口、置信规则和 `s_max` 缺失时，不得假定 `G_stop=true`。

### 17.4 C 偏心加载理论层

加载点路径约束为

\[
\boxed{
\mathbf b_P^{\mathsf T}\Delta\mathbf q_C=\Delta\delta_P.
}
\]

理论六维平衡为

\[
\boxed{
\mathbf0\in
\sum_{i=1}^{4}\mathbf J_i^{\mathsf T}\mathcal W_i
+\lambda_P\mathbf b_P
+\mathbf W_{\rm other,authorized}
+\mathbf C_{\rm mode}^{\mathsf T}\boldsymbol\mu_{\rm mode}
+\mathbf C_{\rm rig}^{\mathsf T}\boldsymbol\mu_{\rm rig}.
}
\]

- 规定量：`δ_P` 增量、加载方向、`s_stop`、rocking/边界模式；
- 待求量：允许的 `q_C` 分量、`λ_P`、可选 `η_i` 和 admissible graph 分支；
- 乘子：仅真实授权约束允许非零；
- 后处理：四单元载荷、稳定性、事件、峰值和能力；
- 当前 B 1.0 下该层在非零正式路径进入物理求解前即被合同审计阻断。

### 17.5 变量角色总表

| 层级/阶段 | 规定量 | 主要未知量 | 乘子/graph | 后处理与诊断 |
|---|---|---|---|---|
| A embedded | 基座位姿/增量、accepted A、DamageStore、参数 | A accepted 机理定义的内部变量 | 接触/刚性/材料 graph | `A_on_B`、事件、切线、能量、质量 |
| A standalone | `u_x`, `P_z=0.5 N` | 外层 `u_z` + A 内部变量 | 预载同伦/事件分支 | `R_x`, 100 mm 曲线、时间 |
| B embedded balanced | `u_x,P_i` | 共同 `u_z` + 全部 A trial | normal graph、活动分支 | contact-only、`R_x`、状态、事件 |
| B prescribed residual | `u_x,u_z,P_i` | A/B 内部 trial | residual/graph | 残量、wrench、切线/graph |
| B standalone | 路径 `χ_B`, `P_i` | 每步 `u_z` + A/B 内部 | 事件/损伤/级联 | 单元曲线、逐针历史、时间 |
| C preload | `s,P_i` | 四个 B 的 `u_zi`/graph | 退化 graph | `Q_s`, 预紧质量、停止门控 |
| C load theory | `δ_P,direction,s_stop` | `q_C,λ_P,η_i?` | 6D graph、授权约束乘子 | 稳定曲线、事件、峰值、`F_crit` |

## 18. 统一单步算法

以下伪代码规定调用顺序和事务边界，不规定编程语言。`SYSTEM_EXECUTE` 是内部调度门面，其输入是互斥并集 `ExecutionRequest = SystemRequest | StandaloneValidationRequest`：第 14.1 节的公开 `SystemRequest` 只能选择 `C_SYSTEM_MAIN_PATH`，A/B standalone 必须使用第 5.2 节的 `StandaloneValidationRequest`，且不得携带或推进 C 的 `SystemAcceptedState`。

```text
FUNCTION SYSTEM_EXECUTE(execution_request, accepted_or_validation_state):

  0. SELECT_EXECUTION_PROFILE
     - 按请求 schema 令 request=execution_request，并拒绝跨 schema 字段。
     - profile ∈ {A_SINGLE_SPINE_STANDALONE,
                  B_ARRAY_UNIT_STANDALONE,
                  C_SYSTEM_MAIN_PATH}.
     - standalone profile 创建独立 ValidationRun；不得读取或修改
       C SystemAcceptedState 的物理历史。

  1. VALIDATE_IDENTITY_VERSION_AND_SCHEMA
     - 校验 engineering context、A/B/C 模型、A_TO_B、B_TO_C、run_id。
     - 校验单位、frame、reference point、transform、configuration、
       parameter、surface、state 和 DamageStore hashes。
     - 校验 idempotency key、parent receipt 和 deterministic replay manifest。
     - 缺失必需字段不得补默认值。

  2. FREEZE_IMMUTABLE_INPUTS
     - 冻结 SurfaceRealization、A1 handles、A/B/C configurations、参数包、
       geometry binding、P_i、system boundary、numerical/event configs。
     - 冻结 parent accepted state 和一个 DamageStore snapshot。
     - 数值缓存可重建，但不得进入物理状态。

  3. DISPATCH_STANDALONE_VALIDATION_IF_REQUESTED
     if A standalone:
       - 调用 standalone_single_spine_driver；其内部只调用 intrinsic A kernel。
       - 使用唯一 0.5 N 外层法向推力、100 mm 路径和 1 mm/s 时间映射。
       - 依 A 事务原子接受；输出 StandaloneValidationRecord；return。
     if B standalone:
       - 调用 standalone_continuous_unit_driver；其内部只调用 B kernel 和 A embedded。
       - 使用每单元 P_i、100 mm 路径和 1 mm/s 时间映射。
       - 依 B/A/DamageStore 单元事务接受；输出记录；return。

  4. VALIDATE_C_STAGE_TRANSITION
     - 只允许 C accepted 状态声明的 legal_next_operations。
     - PRELOAD 阶段 path_kind=COMMON_SEARCH_S。
     - LOAD 阶段必须已有 PRELOAD_ACCEPTED_LOCKED 和 immutable s_stop。

  5. BUILD_CANDIDATE_KINEMATICS
     if PRELOAD:
       - propose s_target=s_n+Δs；令所有 u_xi=s_target；rocking=off。
       - 为四单元构造 UX_PZ_BALANCED 请求。
     if ECCENTRIC:
       - 保持 s=s_stop, ds=0。
       - 由 C 刚体运动和 O_A/C 变换计算四单元完整 local twist。

  6. MOTION_CONTRACT_COVERAGE_AUDIT
     - 必须在任何非零偏心 B 物理调用前执行。
     - 若任一 local y 或 rotation 非零且 B_TO_C=1.0.0：
         return C_CONTRACT_EXTENSION_REQUIRED；
         accepted state、δ_P、A/B、DamageStore、event、work、curve、peak 全不变。
     - 禁止 x/Z 投影、旋转旧 wrench、固定针姿态或经验能力域替代。

  7. CHOOSE_LOCAL_PREDICTION_OR_FULL_CALLBACK
     - 仅在 capsule validity key、branch、trust region、event distance、
       pose、DamageStore、control mode 和 quality 全部有效时可局部预测。
     - 任一事件/姿态/历史/合同/参考点变化或需要精确损伤、作用线、
       稳定性、退化、峰值时，强制完整 B trial。
     - 局部预测不得提交低层历史。

  8. RUN_SIDE_EFFECT_FREE_B_TRIALS
     - 四个单元从同一 parent SystemAcceptedState 和同一 DamageStore snapshot 调用。
     - B 对每根配置针从同一 accepted A state 调用 A embedded trial。
     - 可并行执行，但规范归约不依赖返回顺序。

  9. A_LEVEL_FATAL_SCREEN_AND_ASSEMBLY
     - A 在装配前筛查 contract/stale/kinematic/domain/geometry/collision/
       model/parameter 状态。
     - 任何致命 A 响应不得作为零力针装配。
     - B 将有效 A_on_B wrench 各运输到 O_A 并求和一次。

 10. SOLVE_B_COMMON_EQUILIBRIUM_OR_GRAPH
     - PRELOAD/standalone balanced: 给定 u_x,P_i，求 u_z 或 normal graph。
     - prescribed residual: 评估 r_z/graph distance，未通过不能标 balanced。
     - 每个 Newton/graph 探测都从同一 accepted A/B snapshot 重新调用；
       不串接未接受历史。

 11. TRANSPORT_B_WRENCHES_AND_CHECK_POWER
     - 按每个 response 的 source frame、O_A、target C、transform version 运输。
     - 检查 action/reaction、reference transport 和 wrench–twist power invariance。
     - 失败为合同/变换错误；全部 trial rollback。

 12. ASSEMBLE_C_RESIDUAL_OR_PRELOAD_DIAGNOSTICS
     if PRELOAD:
       - 计算 R_xi、Q_s、成对预紧、不平衡和完整 contact-only wrench。
       - 评估预紧质量、安全和停止候选，但不提前提交。
     if ECCENTRIC under a future accepted full-twist contract:
       - 装配 contact-only、loading 和明确授权的其他 wrench。
       - 求 q_C、λ_P、可选 η_i 和 6D graph。
       - 未授权模式/试验架乘子必须为零。

 13. GLOBAL_FATAL_STATUS_SCREEN
     - 按认证优先级处理 contract/stale、unsupported、domain/geometry/collision、
       model/parameter/boundary unavailable、damage/transaction 和 numerical。
     - 未认证状态不得改写为物理无解、失稳、不可恢复或零能力。

 14. REDUCE_GLOBAL_EARLIEST_EVENT
     - 收集所有 A/B 事件以及 C pose/graph/stability/collision/domain/
       constraint/parameter 事件分数。
     - γ_global = minimum legal event fraction。
     - 若 γ_global<1：rollback 当前全部 trial；缩短共同路径增量；
       从同一 parent accepted state 回到步骤 5。
     - 不得缩放旧 u_z、pose、wrench、graph、damage 或 λ_P。

 15. BUILD_SIMULTANEOUS_EVENT_GROUP
     - 保留 B 单元内部 simultaneous groups。
     - 根据事件括区间重叠、路径容差和 DamageStore 依赖构造跨单元组。
     - 规范排序只用于哈希和重放，不决定物理先后。

 16. RESOLVE_POST_EVENT_SIDE
     - 在事件点生成 pre-event、event-point 和 post-event-side trials。
     - 按依赖偏序重算：geometry/support -> stick/slip/spring ->
       material/strength -> DamageStore -> B equilibrium -> C balance/stability。
     - 不允许用总 if/else 删除同位置事件。

 17. COORDINATE_SHARED_DAMAGE_FIXED_POINT
     - 收集所有 opaque intents、read/write sets 和 kernel-overlap signatures。
     - 交给 A/B damage coordinator；C/system 不直接修改损伤。
     - 共同 trial DamageStore 改变时，从 parent state 重调所有受影响单元；
       刚性十字主线默认四单元全调。
     - 直到 DamageStore hash、四单元 response、event group 和 global residual 一致。
     - 未收敛返回 DAMAGE_CONFLICT_UNRESOLVED 或 NUMERICAL_NONCONVERGENCE；rollback。

 18. RESOLVE_SAME_POSITION_CASCADE
     - 允许 d(path)=0，而 u_z、pose、η、contact 和 damage 改变。
     - 重复完整 B callbacks、damage coordination 和 C balance。
     - 使用状态哈希、最大级联轮数、最小有效变化和 Zeno 防护。
     - 重复状态无进展时数值停止；不得跳过事件。

 19. CLASSIFY_PHYSICS_STABILITY_AND_RECOVERABILITY
     - 区分 algebraic balance、degenerate graph、one-sided stability、
       recoverable detachment、irrecoverable detachment、physical no-equilibrium。
     - Newton convergence 不能证明物理稳定；Newton failure 不能证明物理无解。

 20. CHECK_RESIDUALS_QUALITY_WORK_AND_HISTORY
     - 检查所有原始有量纲残量、硬不等式、质量和不确定性。
     - 检查单位只换算一次、contact-only 只装配一次、P_i 不重复。
     - 检查功账本、非负耗散、释放能和数值误差分栏。
     - 检查 path/time/slip/damage/dissipation/event number/peak 的单调性；
       trial 中这些 accepted 值必须保持不变。

 21. DECIDE_CONTINUE_STOP_OR_REJECT
     if PRELOAD:
       - 先处理致命、数值、不可恢复和安全边界。
       - 若 s_max 缺失且请求自动终止：C_STOP_UNCERTIFIED。
       - 若达到 s_max 但门控不全：C_PRELOAD_SEARCH_LIMIT_UNQUALIFIED。
       - 仅当 G_stop 全部通过，形成 PRELOAD_ACCEPTED_LOCKED candidate。
     if ECCENTRIC under supported contract:
       - 区分 stable continue、recoverable detachment、physical no-equilibrium、
         instability、irrecoverable detachment 和 physical boundary。
       - 首次反力下降、首针事件、首单元退化或首峰均不自动终止。

 22. UPDATE_TRIAL_CURVE_PEAK_AND_MILESTONES
     - 仅对合同、平衡、稳定和质量通过的 candidate 建立 trial intent。
     - 保存 first needle failure、first unit significant degradation、
       reaction-drop、all peak candidates 和 terminal evidence。
     - trial/rejected points 不进入 accepted curve 或 observed maximum。

 23. CHECK_F_CRIT_EVIDENCE
     - 只有物理终止后无合法稳定分支、分支探索穷尽、明确物理边界证明
       无更高路径，或保守上界闭合时，才允许 F_crit_confirmed=true。
     - 合同扩展、模型/参数、域、稳定性、数值或事务停止时：
       F_crit=null；保留 current_observed_stable_max 和 peak candidates。

 24. PREPARE_GLOBAL_TRANSACTION
     - 组装 C、四个 B、全部 A、一个 DamageStore、events、work、curve、peak intents。
     - 校验最终 candidate hash、read/write sets、versions、transforms、units、replay。
     - 任一 prepare 失败，rollback all。

 25. ATOMIC_COMMIT_OR_FULL_ROLLBACK
     - 一个 global commit 使全部物理状态和账本同时可见。
     - 任一持久化或 receipt 失败，parent accepted state 完全不变。
     - 同 idempotency key 重试不得重复累计。

 26. BUILD_CANONICAL_RESPONSE
     - 成功：返回新 SystemAcceptedState、完整原始输出和 commit receipt。
     - 拒绝/失败：返回 last-valid state、全部状态码和精确分类。
     - 不得用聊天摘要、单一峰值或单一状态标签替代原始记录。
```

### 18.1 事件定位和全量重调不变量

- 每次事件括区探测都必须重新求 A/B/C 当前完整候选；
- `UX_PZ_BALANCED` 中事件分数缩短后必须重新求 `u_z`；
- C 全局增量缩短、姿态变化、DamageStore 变化或控制模式变化后，相关旧响应全部陈旧；
- 刚性四单元主线默认四个单元全部重调；
- 任何低层 event/cascade/graph 都不得通过线性插值旧 wrench 处理。

---

# 第七篇：事件、优先级、终止和恢复

## 19. 认证优先级和物理事件偏序

### 19.1 致命认证筛查

主摘要状态按以下顺序选择，但 `all_status_codes` 和所有同位置物理事件必须完整保留：

```text
CONTRACT_VIOLATION / STALE_SNAPSHOT
-> C_CONTRACT_EXTENSION_REQUIRED / KINEMATIC_MODE_UNSUPPORTED
-> OUT_OF_DOMAIN / GEOMETRY_UNCERTAIN / BODY_COLLISION_INVALID
-> MODEL_UNAVAILABLE / PARAMETER_UNAVAILABLE / ACTUATOR_OR_BOUNDARY_UNCERTIFIED
-> DAMAGE_CONFLICT_UNRESOLVED / TRANSACTION_ERROR
-> NUMERICAL_NONCONVERGENCE / MINIMUM_STEP_EXHAUSTED / ZENO_CANDIDATE
-> certified physical classifications
-> event reduction/rebalance
-> accepted continuation/lock/termination
```

只有合同、模型、参数、域、几何、事件定位、数值和稳定性充分时，才允许使用物理无解、物理失稳、不可恢复脱附或 `F_crit` 结论。

### 19.2 非致命事件依赖偏序

```text
几何支持与接触合法性
  -> 粘滑、支持迁移和弹簧/硬限位分支
  -> 材料容量和针体强度
  -> 共享 DamageStore
  -> B 全阵列共同平衡和重分配
  -> C 四单元整体平衡
  -> 稳定性、退化、峰值和终止审计
```

该偏序只规定事件后一侧的重算依赖，不决定并发事件的物理先后。物理先后只由合法路径上的最早事件位置确定。

## 20. 事件、状态和恢复矩阵

### 20.1 针级和接触级

| 事件/状态 | 原始进入量 | 一侧要求 | 可恢复性 | 是否可直接提交 | 下一动作 |
|---|---|---|---|---:|---|
| `OPEN` | 无正压合法支持 | wrench 可为零；embedded 不施加恒力 | 可搜索/再挂接 | 作为完整候选可提交 | 上层改变共同位姿 |
| `TIP_CONTACT_ESTABLISH` | 合法球冠 gap 到 0；mm | 接触后侧重新求全耦合 | 通常可恢复 | 仅事件闭环后 | 建立零载或承载支持 |
| `CONTACT_LOAD_ONSET` | `λ_n` 从 0 正向进入；N | 正压和硬不等式满足 | 可恢复 | 事件后候选 | 更新承载集合 |
| `FRICTION_CONE_REACHED` | `μλ_n-||λ_t||=0`；N | 先求一侧全粘着 | 仅候选 | 否 | 判断是否真实滑移 |
| `SLIP_ONSET_CONFIRMED` | 全粘着不可行且客观滑移非零 | 最大耗散、耗散非负 | 可继续但历史相关 | 事件后 | 提交滑移一次 |
| `ROLLING_NO_SLIP` | 支持位置变、客观滑移为 0 | 不产生摩擦耗散 | 可恢复 | 是 | 保留支持迁移 |
| `SUPPORT_CHART_SWITCH/MIGRATION` | 特征或图表边界 | 新旧支持和一侧状态完整 | 通常可恢复 | 事件后 | 完整重求 |
| `CAP_LEGALITY_LOSS` | 球冠合法裕度到 0；mm | 枚举新支持或打开 | 可恢复/释放 | 事件后 | 支持切换或释放 |
| `SPRING_ORIGINAL_LENGTH` | `δ_s=0`；mm | 不允许拉力 | 可恢复 | 事件后 | 保持零或释放 |
| `SPRING_HARD_STOP_ENTER` | `4-δ_s=0`；mm | 不再增加压缩；合法限位 graph | 可离开 | 事件后 | 切换刚性限位 |
| `SPRING_HARD_STOP_LEAVE` | 限位反力消失/回弹 | 回到内部或零长分支 | 可恢复 | 事件后 | 完整重求 |
| `MATERIAL_INITIATION` | 材料利用率到容量；1 | 产生 trial intent 并重平衡 | 损伤不可逆，承载可继续 | 协调后 | DamageStore fixed point |
| `MATERIAL_SOFTENING_UPDATE` | 损伤一致性条件 | 单调、耗散非负 | 历史不可逆 | 协调后 | 完整 A/B/C 重求 |
| `MATERIAL_FULL_FAILURE` | 软化坐标到终点；mm | 以残余容量重求 | 可能继续或释放 | 事件后 | 不自动判脱附 |
| `NEEDLE_YIELD_LIMIT` | 强度裕度到 0；1 | 同位置事件仍保留 | 首版该针分支终止 | 事件后 | B/C 重分配 |
| `NEEDLE_FRACTURE_LIMIT` | 断裂裕度到 0；1 | 同位置事件仍保留 | 首版不可恢复 | 事件后 | B/C 重分配 |
| `CONTACT_RELEASE` | 正压力到 0 且打开侧/分支消失 | 释放后 gap/graph 合法 | 可恢复 | 事件后 | 回位并继续共同路径 |
| `REENGAGED` | 先前开放针重新建立承载 | 读取旧 DamageStore | 可继续，历史不重置 | 事件后 | 新 accepted 分支 |

### 20.2 单元、整体、认证和事务级

| 状态/事件 | 进入条件 | 恢复/终止语义 | 是否推进 accepted 历史 | 下一动作 |
|---|---|---|---:|---|
| `BALANCED_UNIQUE` | B 残量通过且分支唯一 | 可继续 | 候选通过全局条件后 | 上层继续 |
| `BALANCED_DEGENERATE` | graph 含目标但反力/分支集合值 | 保留 graph，不伪造唯一 | 条件性 | 分支策略或未认证 |
| `EVENT_REDUCTION_REQUIRED` | 目标增量跨越更早事件 | 非物理终止 | 否 | 全局缩步和全量重调 |
| `EVENT_REBALANCE_REQUIRED` | 事件点后平衡/损伤/级联未闭合 | 非物理终止 | 否 | 继续 fixed point |
| `UNIT_DETACHED_RECOVERABLE` | 当前无承载但有合法域、余程和 continuable 针 | 继续搜索/再挂接 | 可在事件后提交 | C 重平衡并继续 |
| `UNIT_DETACHED_IRRECOVERABLE_CANDIDATE` | B 认为单元无恢复路径 | 不自动等于整体不可恢复 | 仅事件后 | C 证明全局路径 |
| `FIRST_NEEDLE_FAILURE` | 首个认证材料/强度类针事件提交 | 里程碑，不是单元失败 | 是，随事件 commit | 继续重分配 |
| `FIRST_UNIT_SIGNIFICANT_DEGRADATION` | 版本化单元退化函数跨阈值 | 里程碑，不是整体峰值 | 仅阈值已认证 | 继续加载 |
| `FIRST_REACTION_DROP` | accepted 稳定曲线首次合法下降 | 曲线里程碑，不是峰值确认 | 是 | 峰后继续 |
| `GLOBAL_REACTION_PEAK_CANDIDATE` | 左右 accepted/事件极限满足峰候选 | 不是物理终止 | 是，作为候选 | 继续探索 |
| `C_PRELOAD_ACCEPTED_LOCKED` | `G_stop` 全通过且原子 commit 成功 | 正常阶段终点 | 是 | 审计偏心合同 |
| `C_PRELOAD_SEARCH_LIMIT_UNQUALIFIED` | 达 `s_max` 但停止门控未全通过 | 可保存安全终态但不标合格 | 条件性 | 结束预紧，不进入正式能力 |
| `C_PRELOAD_SAFETY_LIMIT` | 下一步越过安全边界 | 保留最后安全 state | 否 | 停止 |
| `C_STOP_UNCERTIFIED` | 阈值、模型、参数、边界或稳定性不足 | 不作物理失败结论 | 否 | 补全输入后重试 |
| `C_CONTRACT_EXTENSION_REQUIRED` | 非零正式加载需要局部 y/转动 | 安全拒绝，不是零能力 | 否，全部零推进 | 接口升级 |
| `C_PHYSICAL_EQUILIBRIUM_INFEASIBLE` | 有效模型下穷尽 admissible 分支无平衡 | 物理终止候选 | 终止状态可提交 | 能力证据审计 |
| `C_PHYSICAL_INSTABILITY` | 平衡可存在但所有合法一侧稳定分支消失 | 物理终止候选 | 终止状态可提交 | 能力证据审计 |
| `C_DETACHMENT_RECOVERABLE` | 当前整体失载但有合法继续/再挂接路径 | 必须继续 | 可提交事件后状态 | 继续加载/搜索 |
| `C_DETACHMENT_IRRECOVERABLE` | 已证明无合法稳定承载/再挂接路径 | 物理终止候选 | 终止状态可提交 | 能力证据审计 |
| `C_PHYSICAL_BOUNDARY_REACHED` | 达明确授权几何/结构边界 | 物理终止候选 | 是 | 审计是否确认能力 |
| `C_MAXIMUM_CAPACITY_CONFIRMED` | 终止/分支覆盖证据闭合 | 最终能力结论 | 是 | 形成结果 |
| `NUMERICAL_NONCONVERGENCE` | 尚不能证明物理可行/无解，算法未收敛 | 非物理结论 | 否 | 减步或换配置 |
| `DAMAGE_CONFLICT_UNRESOLVED` | 共享损伤 fixed point 未形成 | 非物理结论 | 否 | rollback |
| `TRANSACTION_ERROR` | prepare/commit/持久化失败 | 非物理结论 | 否 | rollback/幂等重试 |

本表中的“终止状态可提交”只允许提交满足第 47 节全部 accepted 不变量的最后有效状态、合法事件点/边界状态及其终止证据账本；不可行平衡 trial、失稳一侧 trial 或其他不满足 accepted 不变量的候选本身绝不得提交为物理状态。若终止只在越界一侧得到证明，保留 last-valid accepted state，并以独立 terminal evidence/ledger 记录终止分类。

## 21. 全局最早事件、同时组和级联

### 21.1 最早事件

对共同路径增量，系统收集所有合法候选分数：

\[
\boxed{
\gamma_{\rm SYS}=
\min(
\gamma_{A},\gamma_{B_1},\ldots,\gamma_{B_4},
\gamma_{\rm pose},\gamma_{\rm graph},\gamma_{\rm stability},
\gamma_{\rm collision},\gamma_{\rm domain},\gamma_{\rm constraint},
\gamma_{\rm parameter}).
}
\]

不适用的通道必须标 `not_applicable`，不得伪造为零。若 `γ<1`，当前目标 trial 全部回滚，缩短共同路径并从同一 accepted state 重求。

### 21.2 同时事件组

满足任一条件时进入同一全局 simultaneous group：

- 事件括区间重叠；
- 路径位置差在版本化同时容差内；
- A/B 已声明同一内部 simultaneous ID；
- DamageStore 读写或核重叠使事件物理耦合；
- 单元事件与整体 graph/stability 事件同位置。

规范排序仅用于哈希：

```text
(path_coordinate, hierarchy, unit_slot, needle/support, source_event_id)
```

### 21.3 同位置级联和 Zeno 防护

同位置级联必须保存状态哈希、事件转换键和级联轮数。终止条件仅为：

- fixed point 稳定；
- 明确物理终止；
- 未认证终止；
- 数值终止。

最小步、最大定位轮数、最大级联轮数和状态变化阈值是数值安全参数，不是物理上限。达到防护条件时必须返回数值状态，不能跳过事件。

## 22. 峰值、终止和 `F_crit`

### 22.1 峰值与终止不等价

以下关系必须始终成立：

```text
first needle failure != unit failure
first unit degradation != global peak
first reaction drop != final peak
local peak != global peak
global peak != physical termination
current zero load != irrecoverable detachment
```

允许的峰值类型包括光滑局部峰、非光滑事件尖峰、平台区间、稳定分支端点、集合值区间、再挂接二次峰和多个局部峰。原始曲线不得被单调包络覆盖。

### 22.2 当前观测最大值

仅在 accepted、稳定、合同和质量通过的状态上更新：

\[
F_{\max,n+1}^{\rm obs}
=\max(F_{\max,n}^{\rm obs},\lambda_{P,n+1}).
\]

它不是最终能力。

### 22.3 最终能力

\[
\boxed{
F_{\rm crit}
=\sup_{\mathsf s\in\mathcal B_{\rm stable,reachable}}
F_{\rm reaction}(\mathsf s).
}
\]

`F_crit_confirmed=true` 仅当以下至少一项有充分证据：

1. 已定位物理终止，且无其他合法稳定分支；
2. 版本化分支探索政策已穷尽所有可达稳定分支；
3. 达到明确物理边界，且余程、再挂接和分支证据证明不能出现更高稳定反力；
4. 保守能力上界与当前峰闭合。

合同扩展、模型/参数、域/碰撞、作用线、稳定性、数值或事务停止时，输出：

```text
current_observed_stable_max = retained
peak_candidates = retained
F_crit = null
F_crit_confirmed = false
```

## 23. 各路径终止矩阵

| 路径 | 正常终止 | 安全/未认证终止 | 物理终止 | 时间处理 |
|---|---|---|---|---|
| A standalone | 精确 100 mm `TRAVEL_COMPLETE` | 域、几何、模型/参数、数值、预载不可行 | A 认证针体/几何/本征无解边界 | accepted 路径对应 100 s |
| B standalone | 精确 100 mm `COMPLETED_PATH` | 运动不支持、域/几何、模型/参数、事务、数值 | 单元无解、失稳、不可恢复脱附、体碰撞 | accepted 路径对应 100 s |
| C preload | `C_PRELOAD_ACCEPTED_LOCKED` | 阈值或 `s_max` 缺失、上限未达标、安全边界、数值/事务 | 经认证的预载不可行/不可恢复 | 无速度则 unavailable |
| C eccentric | 经证据闭合的物理终止和能力结果 | `C_CONTRACT_EXTENSION_REQUIRED`、模型/参数/稳定性/域/数值/事务 | 全局无解、失稳、不可恢复脱附、物理边界 | 无速度则 unavailable |


# 第八篇：物理去重审计与实验原始输出合同

## 24. 柔顺、载荷、损伤、耗散和失效去重审计

### 24.1 审计原则

系统层必须满足“一个物理位置、一个状态所有者、一个共轭端口、一个能量通道”。低层净 wrench 已经包含的内部反力，不得在高层以组件名义再次装配。诊断分解可以保留，但诊断量不得同时成为第二份外载或第二份耗散。

### 24.2 全局去重矩阵

| 物理位置或机理 | 唯一所有者 | 规范状态量 | 共轭力/位移或端口 | 储能/耗散/功 | 开关、边界或有效域 | 上游向下游返回的规范量 | 高层明确不得重复的内容 |
|---|---|---|---|---|---|---|---|
| `SurfaceRealization` 原始几何 | A1/表面后端 | 高度场或三角网格、法向、曲率、域、质量、不确定性 | 几何查询，无独立力端口 | 无；原始地形不因损伤改写 | 150 mm × 150 mm 高度场主线；完整网格次级分支 | 只读查询句柄、表面 ID/版本/质量 | B/C 不复制红砖、混凝土、砂纸接触逻辑；不把 DamageStore 写回地形 |
| 球形针尖—表面接触 | A 接触层 | gap、支持、法向乘子、切向乘子、支持图表 | 支持力与针尖相对运动 | 可选局部接触储能；摩擦耗散另列 | 只有合法球冠承载；刚性或经标定接触柔顺 | 每支持原始量和净 `A_on_B` wrench | B/C 不另加 Hertz、罚力、摩擦锥或“接触合力” |
| 三维 Coulomb 摩擦、粘滑和迁移 | A 摩擦/几何层 | stick/slip、客观滑移、支持迁移、切基历史 | 切向力/客观滑移 | 摩擦耗散，必须非负 | 摩擦参数和图表有效域 | 支持级事件、耗散、净 wrench | B/C 不重判滑移，不用总 wrench 再算第二份摩擦功 |
| 露出针梁 | A 结构层 | 梁端平移/转角、根部内力、模型有效性 | 梁截面 wrench/梁变形 | 梁储能 | `needle_bending=off/on`；梁模型有效域 | 已含梁作用的净 `A_on_B` wrench、梁状态摘要 | B/C 不加等效梁刚度、根部反力或隐藏框架柔顺；`off` 不关闭强度检查 |
| 针级轴向弹簧 | A mount 层 | \(\delta_s\)、弹簧力、剩余行程 | 轴向力/压缩 | 弹簧储能 | `AXIAL_SPRING_MOUNT`；只压缩、0–4 mm、无预压和拉力 | 已含弹簧作用的净 wrench、压缩/余程/事件 | B/C 不再加 \(k_s\delta_s\)；C 的执行器行程不得替代该弹簧 |
| 刚性针级安装 | A 约束 graph | 精确锁定、秩、零空间、约束反力集合 | 约束 wrench/零相对位移 | 理想约束自身无独立储能 | `RIGID_MOUNT`，不得用大有限刚度伪装 | 净 wrench、graph、非唯一性 | B/C 不用罚刚度制造唯一载荷共享 |
| 4 mm 针级硬限位 | A mount 层 | hard-stop active、限位反力 | 限位反力/零增量压缩 | 理想限位边界功或 A 声明通道 | \(\delta_s=4\) mm；可离开；不自动失败 | 已含限位反力的净 wrench、进入/离开事件 | B/C 不再加限位反力，不在 4 mm 后继续弹簧压缩或储能 |
| 表面材料容量与损伤 | A 材料层 + 共享 `DamageStore` | 面片容量、不可逆变量、读写集合、版本 | 材料结果量/内部软化坐标 | 材料耗散 | 模型/参数版本；无愈合；新独立试验无损 | opaque damage intent、事件、耗散、版本/哈希 | B/C 不直接减强、相加、取最大、按调用顺序覆盖；不隐式改摩擦、梁、弹簧或地形 |
| 针体强度 | A 强度层 | 截面结果量、屈服/断裂裕度、终止标记 | 截面内力/结构状态 | 仅按 A 声明；不得把数值残量当耗散 | 强度参数和模型有效域 | 原始裕度、事件、terminal/continuable | B/C 不把接触释放等同断针，不以最小值合并墙体和针体失效 |
| A 单刺基座兼容 | A 本征核 | 规定基座位姿/增量、opaque A state | `A_on_B` wrench/基座 twist | A 端口功 | 当前只认证 B 传入的局部 x 与全局 Z 平移 | 净 wrench、graph/切线、事件、trial/transaction 句柄 | B 不在 A embedded 请求加入逐针 0.5 N；不串接未接受历史 |
| B 刚性背板共同运动 | B1/B2 | 单元共同 \(u_x,u_z\) 或相应 graph | 单元 contact-only wrench/背板 twist | B 端口功 | B 1.0 仅 x/Z | `contact_only_wrench`、残量/graph、分栏反力 | C 不给每针独立背板位移，不绕过 B 直接调用 A |
| B 阵列载荷共享 | B2 | 全针活动集、共同法向平衡、分支、graph | \(P_i\) 控制参数与 B contact response | 不新增独立“共享能量” | 部分接触、刚性集合值或柔顺分支 | 全阵列重求后的逐针/单元响应 | C 不等载，不用最近邻/固定权重/旧峰值转移，不用 \(N_{\rm eff}F_{\rm single}\) |
| B 事件后重分配和级联 | B3 | 事件前/点/后、DamageStore trial、级联 fixed point | 事件侧完整单元 response | 只提交最终 accepted 差量 | 最早事件、同时组、依赖偏序 | 完整事件组、后侧 response、provisional intent | C 不把“失效载荷包”人工分给剩余单元，不只重算触发针 |
| 每单元恒主动法向推力 \(P_i\) | B 外层控制；真实执行器边界由系统配置 | \(P_i\in[0.5,2]\) N | 理想广义力/法向端口位移 | 理想或经认证执行器功分栏 | 恒主动推力，不是恒实际接触合力 | B 控制输入、独立 actuator 字段 | A 请求无 \(P_i/N\)；C 外部墙面 contact 总和不得再次加 \(P_i\) |
| B 的 x 位移控制反力 | B 后处理/外部单元驱动 | \(R_x=-\mathbf e_x^T\mathbf F_U\) | \(R_x\,du_x\) | standalone 控制功 | 位移控制路径 | 分栏 `control_reactions` | 不加入 contact-only wrench 第二次 |
| B 的 y/转动约束反力 | B 后处理/规定子空间约束 | \(R_y^c,\mathbf M^c\) | 约束反力/被禁止运动 | 理想约束方向位移为零 | 仅说明 B 规定运动子空间 | 分栏 `constraints` | C 不把它们作为额外墙面承载；不把固定姿态当授权支承 |
| 十字无质量刚体 | C | \(\mathbf q_C\)、单元固定安装变换 | 四单元 contact-only wrench/C twist | 无弹性储能 | 首版刚体、小角度 rocking 可选 | C 位姿、Jacobian、全局装配 | 不新增框架、导轨、传动链或连接件柔顺 |
| 共同径向搜索与锁定 | C/真实径向驱动 | \(s,s_{\rm stop}\) | \(Q_s^{\rm drive}\,ds\) | 径向驱动功 | 四单元共用一个 s；锁定后 \(ds=0\) | 搜索反力、停止状态、锁定收据 | 不把径向锁定反力当墙面 contact，不把 100 mm 当 C 搜索上限 |
| rocking | C 的刚体自由度 | \(\theta_X,\theta_Y\) | 力矩/角位移 | 无弹性储能 | `rocking=off/on`；首版无 yaw、大角度 | 位姿、稳定性、模式状态 | 不加 rocking 弹簧；B 1.0 下不得旋转旧 wrench 伪装姿态响应 |
| 法向执行器真实端点/作用线 | 外部机构绑定；当前未决 | 源体、目标体、端点、相对行程、作用线 | 执行器力/相对行程 | 经认证执行器功，否则 `unavailable` | 必须版本化绑定 | 边界 manifest、功可用性 | 不从理想零力矩广义力推断 CAD wrench；不可用不得以零填充 |
| 偏心位移加载器 | C/外部试验装置 | \(\delta_P,\lambda_P,P=C+50\mathbf E_Z\) | \(\lambda_P\,d\delta_P\) | 加载器功 | `+X` 或 `45°`，准静态位移控制 | 加载器作用于爪的 wrench、反作用负号 | 不加入 contact-only，不把传感器反力与爪受力同号混用 |
| 真实试验架约束 | 外部边界配置 | 授权坐标和乘子 | 约束 wrench/对应运动 | 仅按明确边界记账 | 作用对象、点、方向必须明确 | `authorized_constraint_manifest` | 未授权乘子必须为零；不得为固定姿态暗加反力矩 |
| 系统数值残量与误差 | 系统/各层求解器 | 分块残量、积分/浮点误差 | 无物理共轭端口 | 单列误差，不是耗散 | 数值配置版本 | 质量账本 | 不得用数值误差补足摩擦/材料耗散或解释为物理失效 |

### 24.3 载荷装配的唯一计数规则

对任一 accepted 系统状态，计数必须满足：

\[
\boxed{
\mathbf W_{\rm wall}^{G,C}
=\sum_{i=1}^{4}
\mathcal T_{O_{A_i}\rightarrow C}
\left(
\sum_{j\in U_i}
\mathcal T_{O_{ij}\rightarrow O_{A_i}}
\mathbf W_{A_j\rightarrow B_i}
\right)
}
\]

其中每个 A 净 wrench 在其 B 单元中出现一次，每个 B contact-only wrench 在 C 中出现一次。以下量不在该和式中：\(P_i\)、x 控制反力、y/转动约束反力、共同径向驱动、加载器和真实试验架约束。这些量必须在各自独立栏中进入相应系统边界残量。

### 24.4 能量计数规则

系统总账只汇总已提交的以下不重叠通道：

\[
\Delta W_{\rm ext}
=\Delta W_s^{\rm drive}
+\Delta W_{\rm load}
+\sum_i\Delta W_{P_i}^{\rm certified/ideal}
+\Delta W_{\rm authorized\ constraints},
\]

\[
\Delta W_{\rm ext}
=\Delta U_{\rm contact}
+\Delta U_{\rm beam}
+\Delta U_{\rm spring}
+\Delta D_{\rm friction}
+\Delta D_{\rm material}
+\Delta E_{\rm release/hardstop}
+\varepsilon_{\rm numerical}.
\]

若真实法向执行器功不可认证，其通道必须为 `unavailable` 并给出原因；不得以理想功和认证功同时相加。trial、事件括区探测、Newton、线搜索、回滚和重复幂等调用均不进入累计账本。

## 25. 实验原始输出的统一外壳

### 25.1 每个运行必须保存的不可变元数据

```text
ExperimentRunEnvelope:
  run_id / trial_id / specimen_id / replicate_id
  operation_kind
  engineering_context_version = 1.0.0
  A_model_version = 1.0.0 accepted
  A_TO_B_contract_version = 1.0.0 accepted
  B_model_version = 1.0.0 accepted
  B_TO_C_contract_version = 1.0.0 accepted
  C_model_version = 1.0.0 accepted
  system_model_version = 1.0.0
  source_file_hashes
  solver_build_id | unavailable
  numerical/event/stability/branch/feature config IDs
  surface_realization_id/version/hash/seed/domain/quality
  geometry/configuration/CAD IDs and hashes
  material/contact/friction/damage/strength parameter IDs
  unit and coordinate convention IDs
  reference point and transform manifest
  actuator/loader/rig boundary manifest
  uncertainty model IDs
  initial accepted state IDs and DamageStore version/hash
  deterministic replay manifest
```

任何缺失的工程、材料、数值或试验配置必须显式记录为 `unavailable/unresolved`，不得省略字段或填入隐含默认值。

### 25.2 每个 accepted 点的公共记录

```text
AcceptedPointRecord:
  accepted_state_id / parent_state_id / commit_receipt_id
  path_kind / path_coordinate / accepted_increment
  physical_time_s | unavailable
  full pose and all prescribed/solved coordinates
  all force and moment components with direction semantics
  expressed frames / reference points / units / transport IDs
  raw residual blocks and graph distance
  branch/rank/nullspace/tangent-or-graph/trust-region status
  per-needle and per-unit state summaries plus raw handles
  DamageStore version/hash and accepted damage delta summary
  event sequence, simultaneous group and cascade IDs
  stored energy / dissipation / release / external work / numerical error
  domain/geometry/collision/model/parameter/stability quality
  uncertainty bounds and certification level
  request/response hashes and replay manifest
```

### 25.3 每个事件必须保存的公共记录

```text
ExperimentEventRecord:
  event_id / source A-B-C event IDs
  hierarchy and entity IDs
  raw dimensional event function and unit
  numerical scaling ID (not a physical threshold)
  path bracket / event fraction basis / localization error
  pre-event accepted state
  event-point trial state
  post-event accepted state or rejection reason
  simultaneous group / dependency edges / cascade round
  pre/event/post wrench, pose, branch and graph
  pre/trial/post DamageStore versions and conflict summary
  recoverability / stability / terminal classification
  work-energy delta and transaction receipt
  all status codes, uncertainty and certification
```

未提交事件必须只进入 `rejected_trial_diagnostics`，并明确 `committed=false`；不得混入实验对比的 accepted 事件序列。

## 26. 单刺连续拖拽输出合同

### 26.1 路径和时间

A standalone 的主路径为：

\[
0\le x_{\rm total}\le100\ \mathrm{mm},
\qquad t=x_{\rm total}/(1\ \mathrm{mm/s}).
\]

只有 accepted 子步推进路径和时间。释放、可逆回位和再挂接不重置总路径或物理时间。

### 26.2 每个 accepted 点必须保存

- \(u_x,u_z,x_{\rm total},t\)、搜索/预载/粘着/滑移/释放/再搜索分段距离；
- 基座、梁根、针尖球心和针尖轴姿态；合法球冠 gap、支持点、法向、切基、体部最小间隙；
- 每支持墙对针力、`A_on_B` 完整 wrench、\(R_x\)、作用—反作用检查和参考点运输记录；
- 梁位移/转角/根部内力、弹簧压缩/余程/硬限位、局部接触压缩；
- 接触、滚动、滑移、材料、针体强度、释放和再挂接的全部正交状态；
- 逐面片 DamageStore 版本/摘要、累计客观滑移、摩擦/材料耗散和释放可恢复能；
- 本征残量、standalone 法向平衡残量、切线/graph、秩、条件数和质量；
- 接触循环、全部局部峰、事件括区、同时组、事务收据和不确定性。

仅保存峰值、单个“挂接成功”标签或滤波曲线不合格。

## 27. 阵列单元连续拖拽输出合同

### 27.1 路径和时间

B standalone 的主路径为：

\[
0\le\chi=u_x-u_x^0\le100\ \mathrm{mm},
\qquad t=\chi/(1\ \mathrm{mm/s}).
\]

只有单元级原子 commit 后推进 \(\chi,t\)。事件定位、法向 Newton、损伤协调和级联不增加时间。

### 27.2 每个 accepted 点必须保存

- \(u_x,u_z,\chi,t,P_z\)，以及 `UX_PZ_BALANCED` 残量或 normal graph；
- B 的 `contact_only_wrench` 在 \(O_A\) 的全部六分量、\(R_x\)、主动推力、x 控制反力、y/转动约束反力的分栏；
- 每根针的 `A_on_B` wrench、参考点运输、gap、支持、载荷、粘滑、梁、弹簧、硬限位、材料和强度状态；
- \(N_{\rm nominal},N_{\rm geom},N_{\rm load},N_{\rm eff}\) 及明确命名的载荷不均指标，但这些仅为派生诊断；
- raw/凝聚切线、割线或 graph、rank/nullspace/branch/trust region；
- 事件前/点/后逐针 \(\Delta\mathbf W_i\)、载荷重分配、再挂接、DamageStore 冲突和级联；
- 外部控制功、A 内储能/耗散/释放和数值误差；
- 单元 accepted state、全部 A opaque handles、DamageStore 版本、事务收据和重放清单。

## 28. 十字对爪同步预紧输出合同

### 28.1 独立变量与时间

主路径坐标是共同搜索 \(s\)，不是 A/B 的 standalone 拖拽 \(x\)。工程事实未固定 C 搜索速度，因此：

```text
path_coordinate = s_mm
physical_time_s = unavailable
```

只有试验协议明确给出且版本化绑定共同搜索速度或时间戳时，才可产生 C preload 时间通道；不得自动沿用 1 mm/s。

### 28.2 每个 accepted 搜索点必须保存

- \(s\)、四个 \(u_{x_i}=s\)、各 \(u_{z_i}\)、四个 \(P_i\)；
- 四个 B 原始 response handles、各 `contact_only_wrench` 在 \(O_A\) 和运输到 C 后的六分量；
- \(R_{x_i}\)、\(Q_s^{\rm drive}\)、\(p_X,p_Y,\Delta_X,\Delta_Y\) 及完整 C 点 contact-only wrench；
- 四单元逐针状态、活动集、graph、行程、DamageStore、事件、级联和能力摘要；
- 停止门控的所有原始特征、下界、置信、裕度、窗口和配置 ID；
- `G_valid/G_plateau/G_gain/G_weak/G_safe/G_persist/G_range` 的逐项结果；
- 停止阈值或 \(s_{\max}\) 未配置时的 `unavailable` 字段和未认证状态；
- 径向驱动功、理想/认证法向执行器功、低层储能/耗散、功误差；
- 四个 B/A snapshots、共享 DamageStore、事件/能量账本和全局提交收据。

### 28.3 锁定点必须保存

`C_PRELOAD_ACCEPTED_LOCKED` 记录必须额外保存：

- 唯一 \(s_{\rm stop}\)；
- 生成锁定态的全部门控证据及配置版本；
- 四个单元的完整历史相关 `UnitCapabilityState`，不可简化为四个峰值；
- 加载阶段的零点、位姿、参考点、四单元状态和 DamageStore 分支根；
- 径向坐标冻结规则和允许继续演化的低层状态清单。

到搜索上限但门槛未满足，应记录 `C_PRELOAD_SEARCH_LIMIT_UNQUALIFIED`；不得冒充正常锁定，也不得以 100 mm 自动补充上限。

## 29. 十字对爪偏心加载输出合同

### 29.1 已获合同支持时的 accepted 点

未来仅在兼容的 B 2.x 或更高合同正式接受后，每个 accepted 偏心点必须保存：

- \(\delta_P\)、加载方向、加载点 P、加载器作用于爪的 \(\lambda_P\) 和完整 wrench；
- C 的六维位姿、rocking 模式、四单元完整 local twist 和动态姿态；
- 四个 B contact-only wrench 在各 \(O_A\) 及 C 点表达、作用线/CoP/free couple 可用性；
- 四单元和全部针的接触、滑移、损伤、强度、释放、再挂接、行程和分支；
- 六维残量/graph、授权与未授权乘子、稳定性、一侧切线/割线、branch/trust region；
- 首针失效、首单元显著退化、首次反力下降、全部峰值候选、峰后分支和终止证据；
- 共享 DamageStore fixed point、同位置级联、功/能量/耗散/误差、事务收据；
- `current_observed_stable_max`、`F_crit`、确认标志、证据类型和不确定性。

偏心加载速度当前未固定；无试验协议时 `physical_time_s=unavailable`，不得沿用 A/B 的 1 mm/s。

### 29.2 当前 B 1.0 下的安全拒绝记录

在当前 accepted 合同下，正式非零 `+X`、`45°` 或 rocking 请求不得生成 accepted 偏心曲线点。系统只生成一个认证拒绝记录：

```text
CertificationRejectionRecord:
  status = C_CONTRACT_EXTENSION_REQUIRED
  requested_delta_P_increment
  required_local_twists[4]
  unsupported_components_by_unit
  current_contract = B_TO_C 1.0.0 accepted
  last_valid_preload_state_id
  accepted_state_unchanged = true
  accepted_delta_P_increment = 0
  A_B_states_advanced = false
  DamageStore_advanced = false
  events_advanced = false
  work_energy_advanced = false
  curve_peak_advanced = false
  F_crit = null
  F_crit_confirmed = false
  interpretation_exclusions:
    - not_zero_capacity
    - not_physical_no_equilibrium
    - not_physical_instability
    - not_irrecoverable_detachment
    - not_numerical_failure
    - not_binary_grasp_failure
```

该记录可以进入运行审计日志，但不能进入物理 accepted 曲线或峰值统计。

## 30. 原始数据保真与后处理边界

1. 原始连续力、位移、姿态、参考点、逐针/逐单元状态和事件必须永久可追溯；
2. 滤波、平滑、对齐、峰值检测和综合特征必须保存独立版本和参数；
3. 非因果滤波不得用于在线事件判定；
4. 派生的有效针数、评分、平台指数或二元判据不得替换原始记录；
5. 传感器 wrench 必须运输到与模型相同参考点，且明确“加载器作用于爪”与“爪作用于传感器”的负号；
6. 仿真和实验的 \(\delta_P=0\) 必须绑定同一个锁定预紧状态定义；
7. 比较 `+X` 与 `45°` 时必须从独立复制的同一预紧态分叉，不能继承另一方向的损伤；
8. 当前验证目标是趋势、方案排序和机理解释，不得以一次偶然峰值覆盖完整历史。

# 第九篇：全局验证矩阵

## 31. 验证状态的规范表达

验证记录必须把下列状态严格分开：

```text
SPEC_DEFINED             # 本文件已定义要求、输入、判据和预期
IMPLEMENTED_NOT_RUN      # 已实现但本轮未运行；本文件不能自行声称
PASSED_WITH_EVIDENCE     # 有版本化测试结果和证据包
FAILED                   # 已运行且未满足判据
BLOCKED_UNAVAILABLE      # 模型、参数、CAD、合同或设备不足
NOT_APPLICABLE
```

本文件当前仅能确认 `SPEC_DEFINED`。没有上传求解器、测试报告、参数标定或实验数据，因此所有实现、数值和实验项目均不得标为 `PASSED_WITH_EVIDENCE`。

## 32. 坐标、单位、接口和去重验证

| ID | 验证构造 | 必须检查的原始量 | 规范预期 | 规范状态 | 本轮实现证据状态 |
|---:|---|---|---|---|---|
| V-SYS-001 | 四个单元静态安装矩阵 | \(R^TR\)、det、局部 x/y/Z 方向 | 每个矩阵属于 SO(3)，编号置换不改几何 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-002 | 任意非零参考点偏置 | 力、源/目标力矩、偏置向量 | \(M'=RM+r\times RF\)；不能只旋转力 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-003 | 随机合法 wrench/twist | 源端和目标端 \(W^T\xi\) | 功在坐标旋转和参考点运输下不变 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-004 | A 接触作用—反作用 | `A_on_B`、`B_on_A` | 六分量严格相反；B 只装配 `A_on_B` | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-005 | 加载器作用—反作用 | 爪受载 wrench、传感器反力 wrench | 力和力矩同时反号 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-006 | 单位输入混合 | μm/mm、N/m/N/mm、deg/rad、MPa | 仅在配置入口换算一次，内部规范单位不再换算 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-007 | N 与 N·mm 残量 | 原始分量、缩放矩阵、尺度 ID | 逐物理分量接受；不得直接无尺度欧氏合并 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-008 | A 单针净 wrench 分解 | 接触、梁、弹簧、硬限位组件与净量 | B 只装配净 `A_on_B` 一次 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-009 | B 单元到 C 装配 | 逐针净 wrench、B contact-only、C 总和 | 每级只运输/求和一次 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-010 | 主动推力计数 | A 请求、B 控制、C 外部墙面总和 | A embedded 无逐针载荷；\(P_i\) 只在 B 外层一次；C 不再加 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-011 | 控制/约束分栏 | contact、actuator、x control、y/rotation constraints | 四栏互不包含，装配策略为 `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1` | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-012 | 固定姿态但无真实支承 | 未授权乘子、六维残量 | 未授权乘子必须为零，否则候选拒绝 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-013 | 功账本通道追踪 | 外功、三类储能、两类耗散、释放、误差 | 每个通道只出现一次；数值误差不作耗散 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-014 | 法向执行器端点未绑定 | ideal work、certified work、原因 | certified 通道为 `unavailable`，不得零填充或重复相加 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |

## 33. A、B 内核等价与阵列机理验证

| ID | 验证构造 | 必须检查的原始量 | 规范预期 | 规范状态 | 本轮实现证据状态 |
|---:|---|---|---|---|---|
| V-SYS-015 | A standalone 对 embedded 外包法向平衡 | 接触状态、\(u_z\)、wrench、事件、损伤、功 | 同搜索/同伦/路径下逐步等价，证明 0.5 N 未重复 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-016 | B standalone 对 embedded 外包单元事务 | q、wrench、逐针状态、事件、DamageStore | 相同路径与接受边界下物理结果等价；仅提交时机不同 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-017 | 全开放阵列、\(P_z>0\) | wrench、法向残量、合法 z 搜索域 | 返回继续搜索或穷尽后的预载不可行，不伪造平衡 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-018 | 一针先接触、其余开放 | O/N/G/L 集合、逐针载荷、单元 wrench | 真实部分接触和非均载，不把开放针置为“失效” | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-019 | 对称柔顺阵列 | 弹簧压缩、逐针载荷、总法向力 | 在唯一对称分支上满足对称；容许表面破缺后的非均载 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-020 | 完全刚性同高多针 | graph、rank、nullspace、代表值 | 保留集合值，不以罚刚度或针 ID 伪造唯一等载 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-021 | 弹簧原长/内部/4 mm/离开 | \(\delta_s\)、弹簧力、硬限位反力、事件 | 无拉力；硬限位可承载且可离开；达到 4 mm 不自动失败 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-022 | `needle_bending=off/on` | 梁状态、净 wrench、强度裕度 | off 仅去掉梁柔顺/储能，不去掉针体强度 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-023 | `2×5` 与 `5×2` 同一表面 | 有向分离、活动集、wrench、事件 | 独立结果；不得旋转或重采样表面使其人为等价 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-024 | 一针材料/强度事件后余针承载 | 事件前后 \(\Delta W_i\)、法向闭合、单元状态 | 全阵列重求；首针失效不等于单元失败 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-025 | 接触释放—继续搜索—再挂接 | 路径、时间、DamageStore、面片 ID、载荷 | 路径和损伤不重置；新支持读取既有损伤 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-026 | 作用线/CoP 边界 | 力、自由力偶、参考平面、交点 | 无唯一点时返回轴线或 `not_available`，不伪造 CoP | SPEC_DEFINED | BLOCKED_UNAVAILABLE |

## 34. 事件、损伤、级联和事务验证

| ID | 验证构造 | 必须检查的原始量 | 规范预期 | 规范状态 | 本轮实现证据状态 |
|---:|---|---|---|---|---|
| V-SYS-027 | 大步跨单一事件 | 原始事件函数、括区、分数、前/点/后状态 | 缩步到最早事件并从同一 accepted state 全量重调 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-028 | 多针/多单元同时事件 | 各括区、同时组、依赖边、调用顺序 | 同时事件全部保留；偏序只规定后侧重算顺序 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-029 | 物理事件与稳定性事件接近 | 路径位置、括区、稳定性侧 | 按最早合法路径定位；不得由摘要 if/else 删除另一事件 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-030 | 同一 DamageStore 非冲突 intents | read/write set、哈希、响应 | 可联合形成同一 trial 快照，顺序不影响结果 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-031 | 写—写、写—读和核重叠冲突 | 冲突图、协调轮、四单元重调 | 调用 A/B 协调器，禁止最后写者覆盖 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-032 | DamageStore 顺序置换 | 串行、并行、单元排列后的 accepted hash | 最终状态、事件组、损伤和功相同 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-033 | 三轮同位置级联 | 每轮状态哈希、事件、残量、DamageStore | 稳定 fixed point 或明确分类停止；不漏事件 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-034 | Zeno/重复状态构造 | 事件转换键、最小步、级联轮数 | 返回数值停止，不静默跳过物理事件 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-035 | 相同 A trial 重复调用 | accepted state、滑移、损伤、功、事件号 | 完全无永久副作用 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-036 | 相同 B embedded trial 重复调用 | B/A states、DamageStore、路径/时间、能量 | 完全无永久副作用 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-037 | C Newton/线搜索反复试探 | 全部低层版本和历史 | 未全局 commit 前不推进任何物理历史 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-038 | 全局最小事件后回滚 | 四 B tokens、C trial、DamageStore intents | 四单元和 C 全回滚；旧 wrench 不缩放复用 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-039 | prepare 阶段故障注入 | 四单元 token、DamageStore、路径、账本 | 全部不提交，last-valid state 不变 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-040 | commit 中任一持久化故障 | 版本可见性、收据、恢复日志 | 原子全回滚或事务层保证无部分可见状态 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-041 | 同幂等键重复提交 | receipt、状态版本、历史长度 | 返回原收据或安全拒绝，不重复累计 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-042 | 串行/并行确定性重放 | 物理解、graph、事件组、hash、receipt | 结果一致；执行完成顺序不决定物理分支 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |

## 35. C 路径、合同覆盖、稳定性和能力验证

| ID | 验证构造 | 必须检查的原始量 | 规范预期 | 规范状态 | 本轮实现证据状态 |
|---:|---|---|---|---|---|
| V-SYS-043 | 四单元同步预紧 | 四个 \(u_{x_i}\)、各 \(u_{z_i}\)、\(P_i\)、wrench | 唯一共同 s；各单元允许不同接触/法向位置 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-044 | 对称预紧 | \(R_{x_i}\)、\(Q_s\)、完整 C wrench | 全局面内力可相消而径向驱动反力非零 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-045 | 停止门控缺阈值 | 门控字段、配置 ID、last valid state | 返回未认证，不用隐藏默认或 100 mm | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-046 | 到 \(s_{\max}\) 未达标 | 停止门控、上限、状态 | `C_PRELOAD_SEARCH_LIMIT_UNQUALIFIED`，不标正常合格 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-047 | 正常预紧锁定 | 门控证据、事务收据、\(s_{\rm stop}\) | 锁定后 ds=0，但 A/B 状态和 DamageStore可继续演化 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-048 | B 1.0 下非零 `+X` | 四单元所需 local x/y/rotation | 单元 3/4 需要 y；返回 `C_CONTRACT_EXTENSION_REQUIRED` | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-049 | B 1.0 下非零 `45°` | 四单元 local x/y | 四单元均需要 y；安全拒绝 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-050 | B 1.0 下 rocking | local rotation、动态姿态需求 | 安全拒绝；不得旋转旧 wrench | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-051 | 三类合同拒绝的零推进 | state IDs、\(\delta_P\)、DamageStore、事件、功、曲线、峰值 | 全部保持不变；拒绝不解释为零能力或物理失败 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-052 | 未来 B 2.x x/Z 向后兼容 | 1.0 与 2.x 相同请求/响应 | 所有合法 x/Z 语义、参考点、事务和结果保持兼容 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-053 | 未来 B 2.x 任意小 full twist | 输入/输出 6D twist/wrench、功 | 完整 SE(3) 端口功对偶通过 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-054 | 未来 B 2.x 6D tangent/graph | 一侧有限差分、branch、rank/nullspace | 有效域内一致；跨事件不伪造光滑切线 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-055 | 未来 B 2.x 动态姿态 | 针轴、针尖、体碰撞、表面查询、事件 | 姿态更新真实进入 A/B 查询，不仅重表达旧 wrench | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-056 | 固定姿态候选 | 六维残量、未授权乘子 | 自然满足力矩平衡，否则拒绝 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-057 | rocking 候选（未来合同） | \(\theta_X,\theta_Y\)、一侧稳定性、碰撞 | 由力矩平衡决定，rocking 无弹性储能 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-058 | Newton 收敛但稳定性不通过 | 残量、恢复切线/graph、扰动方向 | 分类为物理失稳或稳定性未认证，不因代数根而接受 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-059 | Newton 不收敛但分支未穷尽 | 迭代、括区、branch coverage | `NUMERICAL_NONCONVERGENCE`，不得写成物理无解 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-060 | 物理无平衡证明 | 全部 admissible branches/graph | 仅在模型/参数/数值充分时给物理无解 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-061 | 首针失效后稳定继续 | 事件、四单元重平衡、反力曲线 | 继续加载，不自动终止或确认峰值 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-062 | 首单元显著退化后稳定继续 | 退化函数、稳定分支、曲线 | 记录里程碑并继续，除非独立终止条件成立 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-063 | 首次反力下降后再升高 | 全部 accepted 曲线点/峰值候选 | 保留多峰和二次峰，首降不等于全局峰 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-064 | 稳定峰后渐进脱附 | 峰后点、事件、稳定性、恢复性 | 继续到物理终止或覆盖证据闭合 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-065 | 可恢复脱附—再挂接 | 零/低载状态、剩余行程、再挂接分支 | 不判不可恢复；合法时继续 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-066 | 不可恢复脱附证明 | 所有活动针、余程、branch、DamageStore | 只有无合法稳定再挂接路径时确认 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-067 | 多分支能力上界未闭合 | current max、峰候选、coverage | \(F_{\rm crit}=null\)，保留当前观测最大值 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-068 | 终止/上界证据闭合 | 终止证据、branch coverage、峰区间 | 才允许 `F_crit_confirmed=true` | SPEC_DEFINED | BLOCKED_UNAVAILABLE |

## 36. 收敛、统计和实验对齐验证

| ID | 验证构造 | 必须检查的原始量 | 规范预期 | 规范状态 | 本轮实现证据状态 |
|---:|---|---|---|---|---|
| V-SYS-069 | 高度场/网格加密 | gap、法向、事件、wrench、峰值、损伤 | 在声明可信带内进入稳定平台；不足时几何未认证 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-070 | 位移步长收敛 | 事件位置、状态序列、功、峰值 | 减步后事件和 accepted 曲线收敛 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-071 | 事件容差敏感性 | 同时组、前/点/后状态 | 容差变化不应改变可分辨物理顺序；不确定性需报告 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-072 | DamageStore fixed-point 容差 | 损伤版本、wrench、级联轮数 | 响应和事件进入稳定平台 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-073 | 稳定性一侧增量尺度 | 恢复功/切线/graph | 结论在有效尺度区间一致 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-074 | 分支枚举/延拓策略 | branch lineage、当前峰、终止 | 增加覆盖不应降低已证实的可达集合；未穷尽则不确认 Fcrit | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-075 | 随机样本顺序增加 | 均值/分位数/置信区间、设计排序 | 样本数由统计稳定性关闭，不硬编码 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-076 | 仿真—实验坐标对齐 | 传感器/C/P 变换、方向、零点 | 同参考点、同坐标、正确作用—反作用 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-077 | 预紧零点对齐 | \(s_{\rm stop}\)、初始 wrench、DamageStore | 实验与仿真从同定义锁定态开始 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-078 | 原始数据和滤波对照 | 原始/滤波曲线、滤波器版本、相位 | 原始通道永久保留；非因果滤波不判在线事件 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-079 | 单刺/单元时间映射 | accepted 位移与时间戳 | 1 mm/s 映射只用于 A/B standalone | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-080 | C 时间未给协议 | s/δP、时间字段 | `unavailable`；不得自动套用 1 mm/s | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-081 | 趋势和排序比较 | 参数方向、方案排序、置信区间 | 优先验证趋势/排序/机理，不拟合单次偶然峰值 | SPEC_DEFINED | BLOCKED_UNAVAILABLE |
| V-SYS-082 | 二元成功/综合评分请求 | 原始输出、阈值配置 | 当前不自动产生；阈值未批准则 `unavailable` | SPEC_DEFINED | BLOCKED_UNAVAILABLE |

## 37. 最小实现验收包

首次实现审查至少必须提供以下版本化证据包，缺一不得把“规范已定义”升级为“实现已通过”：

1. V-SYS-001–014 的坐标、单位、功和去重报告；
2. V-SYS-015–026 的 A/B 等价、部分接触、刚性 graph、柔顺和再挂接报告；
3. V-SYS-027–042 的事件、DamageStore、故障注入和确定性事务报告；
4. V-SYS-043–051 的 C 预紧和 B 1.0 安全拒绝报告；
5. 若申请接受 B 2.x，追加 V-SYS-052–057；
6. 若申请数值能力认证，追加 V-SYS-058–075；
7. 若申请实验趋势认证，追加 V-SYS-076–082 及原始数据清单。

测试报告必须给出输入哈希、求解器版本、数值配置、原始残量、事件记录、accepted state/receipt 链和失败复现步骤，不能只给“pass”布尔值。

# 第十篇：未决问题、风险与实现交接

## 38. 未决问题登记

下表中的“规范已定义”只表示接口、状态和安全处理位置明确，不表示参数、代码或证据已经闭合。任何关闭必须由表中指定责任层完成并生成可审计版本。

| ID | 未决项 | 当前状态 | 主要影响 | 当前安全处理 | 阻断阶段 | 允许关闭责任层 | 客观关闭条件 |
|---:|---|---|---|---|---|---|---|
| U-SYS-001 | B 全 twist、局部 y 和动态姿态 | `required extension / not accepted` | 正式 `+X`、`45°` 和 rocking 无法调用低层真实 response | `C_CONTRACT_EXTENSION_REQUIRED`，accepted 状态和全部历史零推进 | C 正式非零偏心加载、Fcrit | B 合同/实现 + C 接受审查 | B 2.x 版本化合同正式接受；V-SYS-052–057 及兼容、事件、功、事务测试通过 |
| U-SYS-002 | 动态姿态下针轴、针尖、表面和非承载体碰撞查询 | 未实现/未认证 | rocking 和偏心运动可能产生错误几何、作用线和事件 | B 1.0 下禁止运行；不得旋转旧 wrench | C 偏心、rocking | A/B 几何实现 | 完整 SE(3) 扫掠查询、姿态事件和 CAD 回归有版本化证据 |
| U-SYS-003 | B 2.x 的 6D tangent/secant/admissible graph | 未接受 | C 六维 Newton、稳定性和事件预测无可信局部算子 | 完整回调不可用则拒绝，不以 x/Z 外推 | C 偏心数值求解和稳定性 | B | 一侧有限差分、功对偶、rank/nullspace、跨事件失效规则通过验证 |
| U-SYS-004 | 真实法向执行器端点、作用线、源/目标体和系统边界 | 未固定 | 完整执行器 wrench、力矩和真实功不确定 | 仅记录理想广义力功；认证相对功为 `unavailable` | 依赖执行器 wrench 的全局平衡和能量认证 | 机械/CAD/控制 + 系统集成 | CAD 和机构图冻结；双端作用—反作用、相对行程和功测试通过；边界 manifest 版本化 |
| U-SYS-005 | C1 停止能力特征和聚合 | 结构已定义，配置未固定 | 无法判断“足够好”的同步预紧 | 保留原始能力特征；无配置返回 `C_STOP_UNCERTIFIED` | 合格锁定预紧态 | C/validation | 单元仿真与实验留出集上，特征、保守下界、置信和鲁棒性方案正式批准 |
| U-SYS-006 | C1 停止阈值、保持窗口、滞回和置信门槛 | 未固定 | 预紧停止位置可能任意或过拟合 | 不设默认；不得读取未来曲线 | 合格锁定预紧态 | C/validation | 版本化策略经训练/留出分离、灵敏度和复现实验批准 |
| U-SYS-007 | C 最大搜索距离 \(s_{\max}\) | 未固定 | 无法给 C 搜索硬上限或上限未达标分类 | 不沿用 A/B 的 100 mm；缺失则未认证 | C 预紧在线完成 | C/机械/validation | 基于单元有效搜索、机械行程、碰撞和安全边界正式冻结；回归验证精确终止 |
| U-SYS-008 | 高碳钢具体牌号、\(E,\nu,\sigma_y,\sigma_u\) 和根部应力集中 | 未标定 | 梁柔顺和针体上限无法定量认证 | 参数 ID 或 `unavailable`；不假定无限强 | A/B/C 定量承载和针体失效 | A/材料/实验 | 材质证明、成品针弹性与破坏试验、必要的局部 FE/系数验证 |
| U-SYS-009 | 表面 PSD、高度分布、相关长度、各向异性、非高斯和可信分辨率 | 未标定 | 接触事件统计、阵列方向效应和随机置信不确定 | 版本化 `SurfaceRealization`；不足返回 `GEOMETRY_UNCERTAIN` | 所有材料专属预测和统计排序 | A1/测量/实验 | 多位置三维测量、仪器 MTF/SNR、可信波段和多分辨率收敛通过审查 |
| U-SYS-010 | 红砖/混凝土/砂纸摩擦参数及方向/位置分布 | 未标定 | 粘滑、反力、损伤和峰值不可信 | 参数包或 `unavailable` | 定量抓附和事件预测 | A/实验 | 同针尖、载荷、环境下起滑试验，区分未损与已损表面并留出验证 |
| U-SYS-011 | 局部接触柔顺 | 未固定 | 峰前斜率和储能可能与梁/弹簧重复 | 刚性主线；柔性分支关闭或显式 `unavailable` | 柔性接触定量曲线 | A/实验 | 微加载试验扣除仪器、夹具、梁和弹簧柔顺后可辨识，刚性极限测试通过 |
| U-SYS-012 | 表面局部强度、材料容量域、断裂能、残余容量和损伤核 | 未标定 | 材料起始、峰后、再挂接和耗散不可信 | 显式模型 ID；可用 `no_damage` 对照，但不得假装已标定 | 材料失效和 Fcrit 定量认证 | A/材料/实验 | 局部压/剪/混合及峰后试验、能量正则、核/网格/步长客观性和留出验证 |
| U-SYS-013 | DamageStore 跨针/跨单元协调器实现 | 语义 accepted，代码未验证 | 并发损伤可能顺序依赖或部分提交 | opaque intents + fixed-point + 全局原子事务；失败则回滚 | 损伤运行和渐进失效 | A/B/事务实现 | 冲突图、顺序置换、并行重放、故障注入和收敛测试通过 |
| U-SYS-014 | 砂纸具体目数和批次 | 未固定 | 表面族实验设计不完整 | 目数仅作为可扩展标签 | 砂纸方案比较 | 工程/实验 | 材料清单冻结并测量实际批次表面 |
| U-SYS-015 | 复合针体和安装座真实 CAD、球冠连接、锥长/角和安全间隙 | 未闭合 | 纯针尖构型可能实际不可装配或先碰撞 | 缺失即几何/碰撞未认证；不得假定零挠度安全 | A/B/C 几何认证 | 机械/CAD/A1 | CAD 导入、制造公差、变形扫掠和解析/网格碰撞回归通过 |
| U-SYS-016 | 梯度阵列安装孔/滑块布局与真实基座偏置 | 未闭合 | 规则球心与实际安装座可能冲突 | 保留真实反算偏置，不以规则孔假设覆盖 | 梯度阵列可制造性 | 机械/B1 | 机械设计、装配公差和几何哈希冻结，CAD 包络测试通过 |
| U-SYS-017 | 弹簧回缩是否改变露出梁长 | 主线固定 L；候选拓扑未决 | 梁刚度、针尖路径和碰撞不同 | 不混合拓扑；可变 L 分支关闭 | 相关柔顺阵列定量结果 | 机械/A | CAD 或位移测量确认，建立独立模型 ID 并做能量/几何回归 |
| U-SYS-018 | 弹簧刚度离散扫描点 | 范围 fixed，离散点 unresolved | 参数研究成本和最优区间 | 接受任一合法 0.1–2.0 N/mm 配置，不硬编码网格 | 设计扫描 | B/研究计划 | 扫描与自适应加密计划批准，参数 ID 固定 |
| U-SYS-019 | 每单元 \(P_i\) 离散扫描点 | 范围 fixed，离散点 unresolved | 预紧和承载设计空间不完整 | 接受任一合法 0.5–2 N 配置 | B/C 设计扫描 | B/C/研究计划 | 实验与扫描计划批准，明确四单元是否同值或独立组合 |
| U-SYS-020 | 数值初始/最小/最大步长和增长规则 | 未固定 | 事件漏检、成本和终止误判 | 版本化配置；达到最小步返回数值停止 | 所有在线路径 | 各求解器/validation | V-SYS-069–074 的收敛平台和压力测试通过 |
| U-SYS-021 | 残量、graph、功、事件、同时组和级联容差 | 未固定 | 平衡、事件顺序和能量认证敏感 | 原始有量纲量永久保存；数值尺度不作物理阈值 | 所有认证结论 | 各求解器/validation | 解析案例、有限差分、敏感性和跨精度复现通过 |
| U-SYS-022 | 稳定性定义的数值实现和 trust region | 理论已定义，未实现验证 | 代数根可能被误判为稳定 | 未认证时返回 `STABILITY_UNCERTIFIED` | C 偏心、Fcrit | C/numerics | 一侧扰动、增量功、graph 强正则与构造失稳案例通过 |
| U-SYS-023 | 分支枚举与覆盖停止政策 | 未固定 | 多峰和 Fcrit 可能漏支 | 未穷尽时保留 `F_crit=null` | 最终能力确认 | A/B/C numerics | 分支 lineage、覆盖上界、对称/非对称构造和重放验证通过 |
| U-SYS-024 | 原子持久层、prepare/commit/rollback 和恢复协议 | 合同已定义，未实现验证 | 部分提交、历史重复或损伤不一致 | 无可靠事务层则不得形成 accepted 多层状态 | 所有 embedded 运行 | 系统/存储 | V-SYS-035–042 故障注入、崩溃恢复、幂等和跨平台重放通过 |
| U-SYS-025 | 随机样本数和种子停止规则 | 未固定 | 设计排序置信不足 | 顺序增加 realization；输出置信区间，不硬编码 N | 统计结论 | 研究设计/validation | 预注册统计功效或排序稳定平台达到批准标准 |
| U-SYS-026 | C 预紧和偏心实验速度、时间戳协议 | 未固定 | C 时间曲线和速率效应无法比较 | C 以位移为主；时间 `unavailable` | C 力—时间实验对比 | 实验/控制 | 设备协议冻结，时钟同步和位移—时间映射验证通过 |
| U-SYS-027 | 仿真—实验允许误差与验证指标 | 未固定 | 不能宣布定量通过/失败 | 只报告残差、置信和趋势 | 实验认证等级 | validation | 工程批准误差预算、重复性、趋势/排序判据和留出方案 |
| U-SYS-028 | 二元抓附成功阈值 | 明确未定义 | 无法自动给 success/failure | 只输出原始连续量和事件 | 二元评价 | validation/工程决策 | 经实验批准且版本化；不得回写低层物理 |
| U-SYS-029 | 综合性能评分 | 明确未定义 | 无法自动单值排序多目标 | 不输出固定综合分；保留原始指标 | 综合决策 | validation/设计决策 | 目标、权重、归一化、鲁棒性和审计方案正式批准 |
| U-SYS-030 | 源代码、自动测试和目标实验 | 未提供 | 规范不能直接执行或验证 | 明确 `not verified` | 全部实现/数值/实验等级 | 各实现/实验团队 | 完成第 37 节证据包并通过独立审查 |

## 39. 主要系统风险

| 风险 | 可能后果 | 当前控制 | 残余风险 |
|---|---|---|---|
| 将 accepted 理论误写为已实现 | 产生不可复现的能力结论 | 认证等级分栏，验证矩阵默认未通过 | 需发布流程强制检查证据包 |
| 将 B 1.0 安全拒绝误写为零承载 | 错误淘汰设计或判断失效 | 独立 `C_CONTRACT_EXTENSION_REQUIRED` 和解释排除列表 | 上层 UI/分析脚本仍需防误读测试 |
| 用 x/Z 投影或旋转旧 wrench 临时跑偏心 | 忽略局部 y、姿态、碰撞和事件，结果无物理意义 | 明确禁止，合同审计先于任何物理调用 | 需要接口层硬拒绝和回归 |
| 主动推力或内部反力重复装配 | 承载、功和法向平衡双算 | `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`、去重矩阵 | 需端到端端口计数测试 |
| 集合值刚性响应被代表值掩盖 | 载荷共享和稳定性顺序依赖 | graph、rank/nullspace 和非唯一状态必须保留 | graph 数据结构和求解器尚未实现验证 |
| 损伤并发顺序依赖 | 不同线程产生不同峰值和历史 | 同快照读取、冲突图、fixed point、原子提交 | 协调器数值/物理唯一性仍待验证 |
| 事件带或步长不当 | 漏接触、错序、跳过级联或假峰 | 原始事件量、括区、全量重调、Zeno 防护 | 容差和性能仍待收敛研究 |
| 未授权支承隐藏承载 | 固定姿态下产生虚假反力矩和能力 | 未授权乘子必须为零，真实约束独立 manifest | 试验架边界需实物核对 |
| 执行器作用线未闭合 | 功和力矩账本不完整 | ideal/certified 功分栏，缺失标 unavailable | 可能阻断全局能量或平衡认证 |
| CAD/体碰撞不完整 | 纯针尖模型在不可实现姿态继续 | 几何/CAD 缺失即未认证 | 动态姿态扫掠实现工作量较大 |
| 参数不可辨识或多柔顺共线 | 用同一斜率同时拟合接触、梁、弹簧 | 按物理位置分离标定和去重 | 需要专门实验设计 |
| 只比较峰值 | 忽略持续能力、再挂接、多峰和渐进失效 | 强制保存完整 accepted 曲线和事件 | 后处理流程需禁止删除原始数据 |
| 峰值被误当 Fcrit | 分支未覆盖即过度声明能力 | current observed max 与 confirmed Fcrit 分开 | 分支覆盖和终止证明成本高 |
| 时间通道误用 | 把 C 位移路径误映射为 1 mm/s | A/B 与 C 时间规则显式分离 | 数据处理脚本需按 operation_kind 校验 |
| 随机样本不足 | 方案排序不稳、偶然表面主导 | realization 独立、顺序增加样本和置信区间 | 样本停止规则尚未批准 |

## 40. 推荐数据对象

实现必须保持以下对象边界。名称可按语言风格调整，但语义和所有权不得改变。

```text
Immutable layer:
  EngineeringContextIdentity
  SurfaceRealization
  A1QueryHandle
  CompositeNeedleGeometry
  SpineParameterBundle
  B1UnitConfiguration
  CGeometryBinding
  BoundaryAndActuatorManifest
  NumericalAndPolicyConfiguration

Accepted physical state layer:
  AcceptedSingleSpineState            # A-owned, opaque upstream
  UnitAcceptedSnapshot                # B-owned, includes A handles
  DamageStoreSnapshot                 # one shared accepted version
  CAcceptedState                      # C-owned, binds four B/A + DamageStore
  SystemAcceptedStateManifest         # system atomic manifest, no duplicate physics

Trial layer:
  EmbeddedSingleSpineTrialRequest/Response
  EmbeddedUnitTrialRequest/Response
  CTrialRequest/Response
  SystemTrialContext
  NumericalTrialCache                 # never a physical state

Event/history layer:
  AEventRecord
  BEventRecord
  CEventRecord
  GlobalSimultaneousEventGroup
  DamageCascadeLedger
  WorkEnergyLedger
  AcceptedCurveLedger
  PeakAndCapacityLedger

Transaction layer:
  RollbackToken
  ProvisionalCommitIntent
  ArmedCommitToken
  GlobalCommitBundle
  CommitReceipt
  DeterministicReplayManifest

Output layer:
  StandaloneValidationRecord
  ExperimentRunEnvelope
  AcceptedPointRecord
  ExperimentEventRecord
  CertificationRejectionRecord
  CMaximumCapacityResult
```

对象必须携带 schema 版本、物理模型版本、合同版本、单位、表达框架、参考点、配置哈希、父 accepted state、DamageStore 版本和请求/响应哈希。opaque 对象不得被上层反序列化后局部修改。

## 41. 推荐模块依赖和调用顺序

### 41.1 编译/运行依赖方向

```text
surface_backend
  -> A_intrinsic_kernel
  -> B_array_kernel
  -> C_cross_gripper_kernel
  -> system_orchestrator
  -> raw_output_and_validation_layer

transaction_service and replay_service
  are cross-cutting services,
  but may not own or alter physical constitutive laws.
```

禁止反向依赖：A 不读取 B/C 平衡；B 不读取 C 峰值/停止决定来改写 A；C 不解析 A 本构；验证层不修改 accepted 物理状态。

### 41.2 初始化顺序

1. 载入并验证 `engineering_fixed_context` 身份；
2. 载入 A/B/C 模型和 A→B/B→C 合同版本；
3. 完成一次单位规范化，冻结表面、几何、参数、CAD 和边界对象；
4. 构造 A 无损初态和一个共享 DamageStore；
5. 构造每个 B 单元配置及其 A opaque bundles；
6. 构造 C 几何绑定、四个单元安装变换和加载点；
7. 生成初始 `SystemAcceptedStateManifest` 和提交收据；
8. 只有所有哈希和参考点闭合后才能进入物理 trial。

### 41.3 在线单步顺序

```text
freeze parent accepted state
-> validate identity/units/reference points/contracts
-> build C or standalone path target
-> build per-unit kinematics
-> audit motion coverage before physical calls
-> side-effect-free B trials
-> side-effect-free A trials inside each B
-> transport and assemble contact-only wrenches
-> solve B/C residuals or graphs
-> reduce global earliest event
-> rollback and re-call on shortening
-> group simultaneous events
-> coordinate shared DamageStore fixed point
-> resolve same-position cascades
-> classify stability/physics/certification
-> update trial work, curve, peak and milestones
-> prepare all intents
-> atomic commit or complete rollback
-> publish accepted record and receipt
```

任何缓存、预测或局部 capsule 只能减少计算量，不能跳过合同覆盖、完整事件定位、DamageStore 协调、功检查或提交条件。

## 42. B 2.x 版本升级门槛

B 2.x 只能在以下条件全部满足后，由正式版本流程接受：

1. 合同 ID 主版本升级且明确兼容策略；
2. B 1.0 的所有合法 x/Z 请求和输出语义逐位或在规定容差内兼容；
3. 请求支持完整基座 twist/SE(3) 姿态和明确插值；
4. 动态针轴、针尖、表面、合法球冠和全部非承载体碰撞查询闭合；
5. 返回完整 contact-only 6D wrench、残量/graph、rank/nullspace/branch/trust region；
6. 6D tangent/一侧割线/graph 带参考点、坐标、单位和有效域；
7. 平移、旋转、碰撞、域和稳定性事件可按同一路径分数定位；
8. wrench–twist 功对偶和作用—反作用测试通过；
9. 共享 DamageStore、同时事件、级联和全局事务语义保持不变；
10. 未支持运动继续安全拒绝并保持 last-valid state；
11. V-SYS-052–057、027–042 和相关几何测试形成证据包；
12. C 集成审查明确批准新合同后，才能把 `C_ECCENTRIC_LOAD_CONTRACT_SUPPORTED` 设为真。

在此之前，本文件中的 B 2.x 字段仅是实现交接要求，不是当前 accepted 能力。

## 43. 最小回归测试集

每次修改以下任一层时必须运行对应最小回归；重大版本还必须运行第 37 节完整证据包。

| 修改层 | 最小回归 |
|---|---|
| 坐标、参考点或单位 | V-SYS-001–007、009、013 |
| A 接触/结构/材料 | V-SYS-004、008、015、021–026、027、035、069–071 |
| B 共同平衡/graph | V-SYS-009–012、016–025、027–034、036、038 |
| DamageStore/事务 | V-SYS-030–042 |
| C 预紧 | V-SYS-043–047、076–077、080 |
| C 合同审计 | V-SYS-048–051 |
| B 2.x/偏心 | V-SYS-052–068 |
| 峰值/能力 | V-SYS-061–068、074 |
| 输出/实验对齐 | V-SYS-076–082 |

回归结果必须绑定代码提交、编译器/平台、随机种子、配置、输入哈希和 commit receipt；失败不能通过更新“金标准”而不解释物理差异。

## 44. 禁止使用临时降阶替代的清单

以下做法无论标记为“临时”“保守”或“用于先跑通”均不得进入正式 accepted 主线：

1. 把 C 所需局部 y 或转动投影到 B 1.0 的 x/Z；
2. 在新姿态下只旋转旧 B wrench，不重求 A/B；
3. 固定针轴、针尖和碰撞几何却宣称 rocking 已求解；
4. 用四个单元峰值求和、最小值或经验缩放代替整体六维平衡；
5. 用 \(N_{\rm eff}\times F_{\rm single}\) 代替阵列共同平衡；
6. 失效后按等载、最近邻、距离或固定矩阵转移载荷；
7. 将 \(P_i\) 平均为逐针法向载荷或在 C 再添加一次；
8. 以大有限刚度替代严格刚性 mount/接触 graph；
9. 用当前活动集的固定 LP/能力域跨事件外推；
10. 用隐藏框架、导轨或姿态反力矩闭合六维残量；
11. 将未认证模型/参数/几何响应置零后继续装配；
12. 把 Newton 失败改写为物理无解或把负切线单独改写为失稳；
13. 把首针失效、首单元退化、首次反力下降或首峰直接当终止；
14. 在合同、模型、稳定性或分支未闭合时报告 \(F_{\rm crit}\)；
15. 在 C 自动套用 100 mm 搜索距离或 1 mm/s 时间映射；
16. 在 trial、事件定位或回滚期间累计滑移、损伤、路径、时间、功、事件号或峰值；
17. 用最后写者、相加或取最大合并 DamageStore intents；
18. 只保存滤波曲线、峰值、有效针数、评分或二元标签而丢弃原始连续历史。

任何原型若使用上述降阶，只能存在于与正式模型隔离的实验性分支，并必须明确 `not_certifiable/not_comparable`；其结果不得进入设计排序、能力确认或实验验证基线。

# 第十一篇：系统闭合结论与强制自检

## 45. 系统认证状态对象

系统实现必须使用累积证据标签而不是一个含混的 `complete` 布尔值：

```text
SystemCertificationLevel:
  SYSTEM_THEORY_DEPENDENCY_INTEGRATED
  A_TO_B_CONTRACT_ACCEPTED
  B_TO_C_XZ_CONTRACT_ACCEPTED
  C_PRELOAD_KINEMATICALLY_SUPPORTED
  C_PRELOAD_POLICY_CERTIFIED
  C_ECCENTRIC_CONTRACT_EXTENSION_REQUIRED
  C_ECCENTRIC_CONTRACT_SUPPORTED
  IMPLEMENTATION_VERIFIED
  NUMERICALLY_VERIFIED
  EXPERIMENTALLY_TREND_VALIDATED
  QUANTITATIVELY_VALIDATED
```

本文件当前可声明：

```text
SYSTEM_THEORY_DEPENDENCY_INTEGRATED = true
A_TO_B_CONTRACT_ACCEPTED = true
B_TO_C_XZ_CONTRACT_ACCEPTED = true
C_PRELOAD_KINEMATICALLY_SUPPORTED = true
C_PRELOAD_POLICY_CERTIFIED = false unless external versioned policy is supplied and validated
C_ECCENTRIC_CONTRACT_EXTENSION_REQUIRED = true for any formal nonzero +X/45deg/rocking request under B_TO_C 1.0.0
C_ECCENTRIC_CONTRACT_SUPPORTED = false
IMPLEMENTATION_VERIFIED = false
NUMERICALLY_VERIFIED = false
EXPERIMENTALLY_TREND_VALIDATED = false
QUANTITATIVELY_VALIDATED = false
```

这些标签不替代每次请求的主状态、全部状态码、事件和质量记录。

## 46. 四级闭合结论

### 46.1 理论/规范依赖链

结论：**全局一致**。

- 表面、A 单刺、B 阵列和 C 整爪的物理所有权单向且无反向覆盖；
- A→B 和 B→C 的变量、状态、事件、历史、graph/切线、质量和事务均有唯一映射；
- 坐标、参考点、单位、`A_on_B`、contact-only、主动推力、控制/约束反力和功方向已统一；
- 接触、梁、弹簧、硬限位、损伤、强度、载荷共享、整爪平衡和能量通道均有唯一所有者；
- 全局 accepted/trial/event/prepare/commit/rollback 语义已闭合；
- A/B standalone 与系统 embedded 路径共用低层核而不形成第二套物理。

“理论一致”不等于所有参数、代码或试验已经完成。

### 46.2 当前 accepted 合同下可在线表达的阶段

在存在实际求解器实现、所需参数和数值配置的前提下，当前合同覆盖：

1. A standalone 的单刺搜索、0.5 N 预载和 100 mm 连续拖拽；
2. B standalone 的单元 0.5–2 N 恒主动推力平衡和 100 mm 连续拖拽；
3. C 的四单元共同 x 搜索和各单元 Z 法向平衡；
4. C 预紧事件、共享损伤、级联、全局原子提交和原始输出；
5. 只有在停止策略、阈值和 \(s_{\max}\) 已版本化提供并认证时，形成合格 `C_PRELOAD_ACCEPTED_LOCKED`；否则只能安全停止或返回未认证状态。

纯全局 Z 的受限构造测试和零增量重放也在 B 1.0 子空间内，但它们不构成正式偏心承载路径。

### 46.3 阻断正式偏心运行的精确接口缺口

`B_TO_C 1.0.0 accepted` 只接受单元局部 x 与全局 Z 平移，不接受：

- 单元局部 y 平移；
- 单元真实转动；
- 动态针轴和针尖姿态；
- 动态表面/碰撞查询；
- 完整 6D tangent/secant/admissible graph。

非零 `+X` 路径使横置单元 3、4 需要局部 y；非零 `45°` 使四个单元均需要局部 y；任意 rocking 需要真实转动和动态几何。因此正式请求必须在物理调用前返回：

```text
C_CONTRACT_EXTENSION_REQUIRED
```

并满足：

```text
accepted state unchanged
accepted delta_P increment = 0
A/B states unchanged
DamageStore unchanged
events/work/energy/curve/peak unchanged
F_crit = null
F_crit_confirmed = false
```

该状态不表示零承载、物理无平衡、物理失稳、不可恢复脱附、数值失败或抓附失败。

### 46.4 关闭缺口所需的最小扩展与接受条件

最小扩展是 B 2.x 的版本化完整 twist/动态姿态接口，至少包括：

- 完整 SE(3) 基座运动和插值；
- 动态针/表面/碰撞几何；
- contact-only 6D wrench；
- 完整残量/graph、rank/nullspace/branch/trust region；
- 6D tangent/一侧割线和功对偶；
- 平移、旋转、碰撞、域和事件定位；
- 保持 A/B opaque history、共享 DamageStore、级联和原子事务；
- B 1.0 x/Z 向后兼容和未支持运动的安全拒绝。

仅当第 42 节全部门槛和相应验证证据通过、且新合同正式 accepted 后，C 才能把非零偏心路径从“理论已定义、合同阻断”升级为“合同可运行”。代码实现、数值认证和实验认证仍是独立后续证据等级。

## 47. 全局不变量清单

任一 accepted 系统状态必须同时满足：

1. 工程、模型、合同、配置、参考点、单位和状态版本相容；
2. 表面/几何/参数对象在同一运行内不可变，DamageStore 只通过新 accepted 版本演化；
3. C、四个 B、全部 A 和一个共享 DamageStore 绑定同一全局收据；
4. 每个 A 净 wrench 在 B 中只装配一次，每个 B contact-only wrench 在 C 中只装配一次；
5. \(P_i\)、径向驱动、加载器、x 控制和真实约束各自分栏；
6. 未授权约束乘子为零；
7. wrench 均携带作用方向、表达坐标、参考点和单位；
8. 参考点运输和 wrench–twist 功不变检查通过；
9. 所有低层 trial 从同一 parent accepted state 和声明 DamageStore 构造；
10. 事件按全局最早路径定位，同时事件不被 if/else 删除；
11. DamageStore fixed point 和同位置级联已闭合；
12. 物理、未认证、数值和事务状态严格区分；
13. 路径、时间、滑移、损伤、耗散、事件号、曲线和峰值只在全局 commit 后推进；
14. A/B 100 mm/1 mm/s 与 C 的 s/δP/未决时间严格分离；
15. `F_crit_confirmed=true` 时存在充分、可重放的稳定可达分支和终止/上界证据。

任一不变量不满足，候选不得成为 accepted 状态。

## 48. 输出前强制自检结果

| 序号 | 自检项目 | 审计结论 | 文件内证据位置 |
|---:|---|---|---|
| 1 | 是否完整阅读五个上传文件 | 是；工程事实、A、B、C 和本提示词全部读取，输入哈希已记录 | 第 0.1 节 |
| 2 | 输入清单、版本和 accepted 状态是否一致 | 是；`engineering 1.0.0 current`、A/B/C `1.0.0 accepted`、提示词 `1.0.0`、run_id 一致 | 第 0.1–0.2 节 |
| 3 | A→B、B→C 的变量、状态、事件、历史、切线/graph 和事务是否逐项映射 | 是；公共入口、请求、响应、opaque 状态、DamageStore、事件和 transaction 均有映射 | 第 12–15 节及第 6–7 节 |
| 4 | 是否存在同一状态、柔顺、载荷、损伤、失效、耗散或反力被计算两次 | 规范审计未发现允许的重复；明确了每一物理位置的唯一所有者和禁止重复项 | 第 24 节 |
| 5 | 坐标、参考点、单位、作用—反作用、力矩运输和功方向是否一致 | 是；建立全局/单元/针/接触变换链、参考点运输和功不变检查 | 第 8–11 节 |
| 6 | \(P_i\)、contact-only、径向驱动、加载器和约束是否正确分栏 | 是；当前外部墙面装配只允许 `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1` | 第 9、13、24 节 |
| 7 | accepted/trial/rollback/prepare/commit 是否闭合 | 是；系统 accepted manifest 绑定 C/B/A/DamageStore，提交全成功或全回滚 | 第 5、18、40–41 节 |
| 8 | 事件优先级、同时组、损伤 fixed point、级联和终止是否保留低层事件 | 是；致命认证先筛，物理事件按最早路径和依赖偏序处理，原始 A/B 事件不丢失 | 第 19–23 节 |
| 9 | A/B 100 mm/1 mm/s 与 C 的 s/δP/时间未决是否严格区分 | 是；A/B 仅 accepted standalone 路径映射时间，C 无协议时为 `unavailable` | 第 16、23、26–29 节 |
| 10 | 实验原始连续量、逐针/逐单元状态和事件是否保留 | 是；四类路径均定义 accepted 点、事件、损伤、能量、质量、收据和不确定性 | 第 25–30 节 |
| 11 | 是否保留 B 1.0 运动缺口和 `C_CONTRACT_EXTENSION_REQUIRED` 零推进 | 是；非零 `+X`/`45°`/rocking 均在物理调用前安全拒绝 | 第 2.2、15、18、29.2、46.3 节 |
| 12 | 是否避免把 B 2.x 建议写成已接受事实 | 是；始终标为 `required extension / not accepted`，并给出正式升级门槛 | 第 15.2、42、46.4 节 |
| 13 | 是否区分理论闭合、合同在线闭合、代码、数值和实验认证 | 是；认证标签和验证矩阵分别报告 | 第 2、31–37、45–46 节 |
| 14 | 是否保留全部未决问题、风险和客观关闭条件 | 是；逐项给出状态、影响、安全处理、阻断阶段、责任层和关闭证据 | 第 38–39 节 |
| 15 | 是否只生成 `SYSTEM_INTEGRATED_MODEL.md` 且未开始后续任务 | 是；本文件为唯一主输出，不包含源代码、候选工程事实、独立合同、YAML、后续提示词或额外附件 | 本节及文件身份 |

## 49. 最终规范结论

`SYSTEM_INTEGRATED_MODEL 1.0.0` 已在规范层完成 A/B/C 的全局机理集成：

- 形成唯一系统算子、唯一 accepted state 组合、唯一事件/损伤/事务主链；
- 统一坐标、参考点、单位、wrench、作用—反作用、功和能量；
- 冻结 A→B→C 的接口映射、所有权、调用顺序、事件循环和原子提交；
- 明确 A/B standalone 与系统 embedded 的共同低层核及不同接受边界；
- 给出四类实验所需的原始连续输出和全局验证矩阵；
- 保留全部参数、CAD、数值、统计、实验和评价未决项；
- 明确保留当前 B 1.0 对正式偏心加载的能力缺口与安全拒绝语义。

因此，本系统的**理论/规范依赖链已全局一致**；当前 accepted 合同下可表达 A/B standalone 和 C 同步预紧的 x/Z 主路径，但 C 合格停止仍依赖未固定的版本化策略。正式非零偏心加载仍被 B 1.0 的局部 y/动态姿态/full twist 缺口阻断，必须零历史推进地返回 `C_CONTRACT_EXTENSION_REQUIRED`。B 2.x 只有通过版本化扩展、兼容、功、事件、损伤、事务和验证门槛并正式接受后，才可解除该阻断。本文件不声称源代码、数值收敛、参数标定或实验验证已经完成。

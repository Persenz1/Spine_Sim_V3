# B_TO_C_CONTRACT

| 元数据 | 值 |
|---|---|
| `contract_id` | `B_TO_C` |
| `contract_version` | `1.0.0` |
| `B model` | `B_INTEGRATED_MODEL 1.0.0` |
| `engineering context` | `1.0.0` |
| `upstream contract` | `A_TO_B 1.0.0 accepted` |
| `input context` | `B_MODULE_CONTEXT 0.3.0 accepted` |
| `integration prompt` | `B_INTEGRATION_PROMPT 1.0.0` |
| `run` | `B_INTEGRATION-r01` |
| `status` | `accepted` |

> 用途：供 C 层在不阅读 B 内部推导的情况下，正确调用无副作用 B 单元试探、装配 contact-only wrench、处理事件/损伤并执行四单元原子提交。文件头不属于公共合同正文；标记块内正文与集成模型逐字一致。

<!-- BEGIN B_TO_C_PUBLIC_CONTRACT -->
## B→C 公共合同正文

### 0. 规范词、身份与适用性

本合同使用以下规范词：

- **必须/不得**：互操作性要求；违反即为 `CONTRACT_VIOLATION`，结果不得装配或提交。
- **应**：除非返回明确的降级状态与理由，否则必须满足。
- **可**：不改变强制语义的实现选择。
- **已认证**：本合同与输入基线明确覆盖的运动、状态、方程和数据语义。
- **未认证**：不能作为零承载或物理失效处理；必须返回明确状态并保留最后有效接受状态。

合同身份固定为：

| 字段 | 值 |
|---|---|
| `contract_id` | `B_TO_C` |
| `contract_version` | `1.0.0` |
| `B_model` | `B_INTEGRATED_MODEL 1.0.0` |
| `engineering_context` | `1.0.0` |
| `upstream_contract` | `A_TO_B 1.0.0 accepted` |
| `input_context` | `B_MODULE_CONTEXT 0.3.0 accepted` |
| `integration_prompt` | `B_INTEGRATION_PROMPT 1.0.0` |
| `run` | `B_INTEGRATION-r01` |
| `status` | `accepted` |

兼容性规则：

1. C 必须校验上述版本、配置哈希、参数包哈希、表面版本、接受状态版本和共享 DamageStore 版本。
2. 任一主版本不匹配、状态陈旧、单位或参考点不明确时，不得容错猜测；返回 `CONTRACT_VIOLATION` 或 `STALE_SNAPSHOT`。
3. 本已接受的理论/数据合同不等于代码、材料参数、真实 CAD 或实验已经验证。
4. 工程事实中的未决量继续以显式参数、模型 ID、配置 ID 或 `unavailable` 表达；C 不得用本合同补成唯一默认值。

### 1. 层级边界、公共调用与认证运动子空间

#### 1.1 唯一物理调用入口

C 的唯一 B 物理入口是无副作用的：

```text
embedded_array_unit_trial(request) -> EmbeddedUnitTrialResponse
```

该入口从不可变接受快照出发，完成当前请求所需的 B1 几何映射、逐针 accepted A→B embedded 调用、B2 全阵列装配与平衡/残量、B3 事件定位、单元内部同时事件、共享损伤意图、同位置级联及最终候选构造。它只返回试探结果、回滚令牌和 provisional commit intent；**不得永久推进任何 A/B 历史**。

`standalone_continuous_unit_driver` 只用于 B 层验证和单元实验对比，负责 1 mm/s 时间映射、最大 100 mm 连续路径、单元级接受与提交。它不是 C 的入口，C 不得通过它绕过全局事务。

C 不得直接调用 A，也不得重建或覆盖 A 的球尖接触、摩擦、梁、轴向弹簧、材料、损伤、释放或再挂接机理。

#### 1.2 事务控制端点

以下端点仅执行事务控制，不构成新的物理入口：

```text
prepare_embedded_unit_commit(provisional_intent, global_acceptance_manifest)
  -> armed_commit_token | prepare_failure

commit_global_B_bundle(global_bundle_manifest, armed_commit_tokens)
  -> atomic_commit_receipts | global_rollback

rollback_embedded_unit_trial(rollback_token)
  -> rollback_receipt
```

`prepare` 不得改变物理历史；`commit_global_B_bundle` 必须把全部参与单元、其内部 A 状态和共享 DamageStore 作为一个原子包提交。任一失败必须完整回滚。

#### 1.3 当前认证运动子空间

当前认证的单元广义坐标为

\[
\boxed{
\mathbf q_U=
\begin{bmatrix}
u_x\\u_z
\end{bmatrix},
\qquad
\Delta\boldsymbol\xi_U^{G,O_A}
=
\mathbf H_U\Delta\mathbf q_U,
\qquad
\mathbf H_U=
\begin{bmatrix}
\mathbf e_x&\mathbf E_Z\\
\mathbf0&\mathbf0
\end{bmatrix}.
}
\]

方向固定为：

- `+u_x`：单元头部指向根部，也是搜索/拖拽方向；
- `+u_z`：远离墙面；向墙压入为 `du_z<0`；
- 当前 B 不认证局部 y 平移、单元姿态转动、背板翘曲或局部弯曲。

支持的控制模式为：

| `control_mode` | C 规定量 | B 处理 | 可返回的平衡声明 |
|---|---|---|---|
| `UX_PZ_BALANCED` | 目标 `u_x` 或 `Δu_x`、每单元 `P_i` | B 求共同 `u_z`，满足唯一残量或集合值 graph | `BALANCED_UNIQUE` 或 `BALANCED_DEGENERATE` |
| `PRESCRIBED_XZ_RESIDUAL` | 目标 `u_x,u_z` 或 `Δq_U`、`P_i` | B 在该姿态进行完整全阵列试探，返回 `r_z` 或 graph 距离；不把未闭合残量称为平衡 | 仅在残量/graph 通过时可声明平衡 |

第二种模式是 B2 内层规定姿态评估的正式公开化，用于 C 将单元法向残量纳入更大的耦合方程；它不新增低层物理。

#### 1.4 rocking 能力边界

- `rocking=off`：C 可使用各单元固定安装方向及上述 x/z 平移语义。
- `rocking=on`：若 C 请求真实单元姿态更新、针轴旋转、参考框架转动或由整爪转动引起的非纯 x/z 基座增量，当前合同必须返回 `KINEMATIC_MODE_UNSUPPORTED` 或 `MODEL_UNAVAILABLE`。
- C 不得把真实转动投影成 x/z 平移、冻结旧姿态后旋转旧 wrench、或仅改变坐标表达而宣称完整 rocking 已被求解。
- 关闭该缺口需要版本化的 B 六维/转动运动扩展、逐针姿态更新、碰撞/表面查询、事件、切线与验证合同；不属于本版本。

### 2. 坐标、参考点、单位、wrench 与功共轭

#### 2.1 规范框架

| 框架 | 定义 | 所有权 |
|---|---|---|
| \(\mathcal F_G=\{\mathbf E_X,\mathbf E_Y,\mathbf E_Z\}\) | 全局墙面框架，`+Z` 指向背板/自由空间 | 工程事实 |
| \(\mathcal F_U=\{\mathbf e_x,\mathbf e_y,\mathbf E_Z\}\) | 单元方向框架，\(\mathbf e_y=\mathbf E_Z\times\mathbf e_x\) | B/C 静态安装 |
| \(\mathcal F_A=\{O_A,\mathbf e_x,\mathbf e_y,\mathbf E_Z\}\) | 阵列格点与 B 公共 wrench 参考框架 | B |
| \(\mathcal F_{N_i}\) | 第 i 根针的轴向正交框架 | B1/A，只读给 C |
| \(\mathcal F_{C_{ij}}\) | 第 i 根针第 j 个支持的局部接触框架 | A，C 不得重建 |

本合同的规范单元参考点为 `O_A`：未加载针尖球心规则格点的几何中心。C 使用其他整爪参考点时，必须通过版本化刚体变换运输 wrench，不能改写 B 的参考点定义。

#### 2.2 公共计算单位

公共单位固定为：

| 量 | 单位 |
|---|---|
| 长度、位移、行程 | mm |
| 力 | N |
| 时间 | s |
| 角度 | rad |
| 力矩 | N·mm |
| 应力/强度 | MPa |
| 线刚度 | N/mm |

工程输入只在 B 配置规范化时换算一次：

\[
50/100\ \mu{\rm m}\rightarrow0.05/0.10\ {\rm mm},
\qquad
100\text{--}2000\ {\rm N/m}\rightarrow0.1\text{--}2.0\ {\rm N/mm}.
\]

C 不得再次换算这些规范值。

#### 2.3 `A_on_B` 与 contact-only 单元 wrench

A 对第 i 根针返回 `A_on_B`：单刺 A 子系统对 B 刚性背板的净 wrench。该净量已经包含 A 所有的局部接触、针梁、轴向弹簧和硬限位内部反力结果。B 只运输并求和：

\[
\boxed{
\mathbf W_U^{G,O_A}
=
\sum_i\mathbf W_i^{G,O_A}
=
\begin{bmatrix}
\mathbf F_U\\
\mathbf M_U^{O_A}
\end{bmatrix}.
}
\]

`W_U` 是 **contact-only** 单元合 wrench，不包含：

- 主动法向执行器广义力；
- x 位移控制反力；
- y 平移或三转动约束反力；
- C 外部载荷或整爪约束。

若第 i 根针的 wrench 在 `O_i` 表达，运输为

\[
\mathbf F^{O_A}=\mathbf F^{O_i},
\qquad
\mathbf M^{O_A}
=
\mathbf M^{O_i}
+
(\mathbf r_{O_i}-\mathbf r_{O_A})\times\mathbf F.
\]

坐标旋转和参考点运输必须同时应用于力与力矩。

#### 2.4 C 的 wrench 运输

设 C 的整爪装配参考点为 \(O_C\)，从单元表达坐标到 C 坐标的旋转为 \(\mathbf R_{CU}\)，且 \(\mathbf r_{O_A/O_C}^{C}\) 是 C 坐标中从 \(O_C\) 指向 \(O_A\) 的向量，则

\[
\boxed{
\mathbf F_C=\mathbf R_{CU}\mathbf F_U,
\qquad
\mathbf M_C^{O_C}
=
\mathbf R_{CU}\mathbf M_U^{O_A}
+
\mathbf r_{O_A/O_C}^{C}\times\mathbf F_C.
}
\]

C 必须保存变换 ID、版本、源/目标参考点和表达坐标。对当前 `rocking=off`，安装旋转为静态版本化变换；真实动态转动不在本合同认证范围。

#### 2.5 功不变条件

对同一刚体运动，wrench 与 twist 变换必须满足

\[
\boxed{
(\mathbf W_U^{O_A})^{\mathsf T}\Delta\boldsymbol\xi_U^{O_A}
=
(\mathbf W_C^{O_C})^{\mathsf T}\Delta\boldsymbol\xi_C^{O_C}.
}
\]

B 返回的功检查字段和 C 的参考点运输测试必须验证该标量不变。只旋转力、不运输力矩，或用错误的位移参考点，均为合同错误。

#### 2.6 主动推力、控制和约束量

主动推力参数 \(P_i>0\) 对应理想广义力

\[
\mathbf F_{\rm act}=-P_i\mathbf E_Z,
\qquad
\mathbf W_{\rm act}^{G,O_A}
=
\begin{bmatrix}
-P_i\mathbf E_Z\\\mathbf0
\end{bmatrix}.
\]

该零力矩表达只是当前理想广义力模型，不声明真实执行器作用线或 CAD 位置。唯一响应分支上的法向平衡为

\[
\boxed{\mathbf E_Z^{\mathsf T}\mathbf F_U=P_i.}
\]

正抓附阻力和约束诊断为

\[
R_x=-\mathbf e_x^{\mathsf T}\mathbf F_U,
\quad
R_y^c=-\mathbf e_y^{\mathsf T}\mathbf F_U,
\quad
\mathbf M^c=-\mathbf M_U
\]

（各转动分量按单元基展开）。这些字段必须与 `contact_only_wrench` 分栏返回。

#### 2.7 C 的唯一装配规则

1. **整爪外部墙面接触平衡**：C 只把每个单元的 `contact_only_wrench` 运输并装配一次。
2. **主动推力 \(P_i\)**：它是 B 本构/平衡的控制参数和执行器功/选型输出；当前整爪外部墙面 wrench 装配不得再把 `W_act` 加到 `contact_only_wrench`，否则会重复施加载荷。
3. **x 控制与 y/转动约束反力**：是维持 B 规定控制/运动子空间的诊断或内部乘子，不得作为额外墙面承载加到整爪接触 wrench。
4. 若未来 C 显式建模执行器实体、作用线及其对其他刚体的反力，必须使用新的版本化扩展合同；本合同的零力矩理想广义力不得被解释为已知 CAD wrench。
5. C 必须在结果中记录采用的装配策略 ID；当前唯一合法值为 `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`.

### 3. C→B 输入合同

每次 `embedded_array_unit_trial` 请求必须包含以下对象；缺失必需字段不得以默认值补齐。

#### 3.1 身份、配置和版本

```text
identity:
  gripper_instance_id
  unit_instance_id
  unit_slot_id
  global_step_id
  global_trial_id
  global_newton_iteration_id
  global_event_sequence_id
  caller_sequence_id
versions:
  contract_id / contract_version
  B_model_version
  engineering_context_version
  A_TO_B_contract_version
  B1_configuration_schema_version
hashes:
  unit_config_hash
  geometry_hash
  parameter_bundle_hash
  run_binding_hash
  state_compatibility_hash
  request_idempotency_key
```

`caller_sequence_id` 仅用于审计，不能决定物理分支。

#### 3.2 不可变配置与环境绑定

```text
configuration:
  B1UnitConfiguration_handle
  NeedleStaticRecord_bundle_handle
  mount_mode
  needle_bending_switch
  formal_scan_policy_id
surface:
  surface_realization_id / version
  A1QueryHandle_bundle
  domain / quality / uncertainty identifiers
parameters:
  contact / friction / beam / spring / material / damage / strength IDs
  numerical_config_id / event_config_id / capability_feature_config_id
```

C 不得在此覆盖逐针低层摩擦、材料、梁、弹簧或损伤参数。参数缺失必须显式为 `unavailable`。

#### 3.3 接受状态与共享损伤快照

```text
accepted_state:
  opaque_accepted_unit_snapshot_handle
  accepted_state_id / commit_receipt_id
  q_U_n / accepted_path_coordinate_if_applicable
  per_needle_opaque_A_state_bundle_handle
  per_needle_accepted_history_versions
damage:
  shared_damage_snapshot_handle
  shared_damage_snapshot_version
  shared_damage_content_hash
```

所有字段只读。C 不得解析或修改 A/B opaque 状态或 DamageStore。

#### 3.4 框架与参考点

```text
frames:
  source_unit_frame_id
  O_A_reference_point_id
  expressed_frame_id
  T_C_from_A_id / version / transform
  C_assembly_reference_point_id
  static_installation_orientation_id
```

对当前认证版本，`T_C_from_A` 的旋转部分必须与固定安装方向相容；请求中的动态单元转动触发 `KINEMATIC_MODE_UNSUPPORTED`。

#### 3.5 试探运动、控制和插值

```text
trial_kinematics:
  control_mode: UX_PZ_BALANCED | PRESCRIBED_XZ_RESIDUAL
  q_U_n
  target_u_x or target_q_U
  requested_increment
  interpolation_rule
  path_fraction_basis
  P_i_N
  event_side_request
  continuation_hint_optional
```

规则：

- `UX_PZ_BALANCED` 中，事件分数以共同切向路径为基准；每个候选分数都必须重新求 `u_z`，不能线性缩放旧 `u_z`。
- `PRESCRIBED_XZ_RESIDUAL` 中，事件分数以声明的 x/z 仿射路径为基准。
- `P_i` 只在 B 外层出现，不得生成逐针力、逐针预载或逐针载荷分配字段。
- 插值规则当前只认证允许子空间内的平移；其他规则明确拒绝。

#### 3.6 请求的响应层级

```text
requested_response:
  trial_phase:
    PROBE_TO_TARGET |
    EVENT_POINT |
    POST_EVENT_CANDIDATE |
    FINAL_ACCEPTANCE_CANDIDATE
  tangent_mode:
    NONE | RAW | CONDENSED_AT_CONSTANT_P | SECANT | ADMISSIBLE_GRAPH
  capability_mode:
    NONE | LOCAL_HISTORY_DEPENDENT | FULL_RAW_SUMMARY
  event_location_required
  full_needle_resolve_requested
  quality_and_certification_request
  deterministic_replay_request
  cross_unit_damage_coordination_context_optional
```

B 有权在满足完整回调条件时把局部预测请求升级为完整针级重求解；不得为满足性能请求而返回超出有效域的低维近似。

#### 3.7 C 不得提供的输入

请求中不得出现：

- 逐针指定力、平均分配力或活动针强制集合；
- 失效针载荷转移权重、邻接载荷矩阵或旧峰值分配；
- C 自行计算的损伤增量或 DamageStore 写入；
- 对 A 低层摩擦、材料、梁、弹簧、硬限位或强度参数的临时覆盖；
- 通过大有限刚度伪装刚性 mount 的参数；
- 任何未声明单位或隐式符号换向。

### 4. B 对 C 保证的内在求解语义

#### 4.1 几何和逐针请求唯一性

B 使用唯一的规则格点与针级几何定义：

\[
\mathbf c^0_{rc}=
\begin{bmatrix}
\left(\frac{n_x-1}{2}-r\right)s\\
\left(c-\frac{n_y-1}{2}\right)s\\
0
\end{bmatrix},
\]

\[
\lambda_r=\frac{r}{n_x-1},
\qquad
\alpha_r=(1-\lambda_r)\alpha_{\rm root}+\lambda_r\alpha_{\rm head},
\]

\[
\mathbf a_{rc}
=
\cos\alpha_{rc}\cos\beta_{rc}\,\mathbf e_x
+
\cos\alpha_{rc}\sin\beta_{rc}\,\mathbf e_y
-
\sin\alpha_{rc}\,\mathbf E_Z,
\]

\[
L_{rc}=
\begin{cases}
4\ {\rm mm}, & \text{固定角模式},\\[2mm]
\dfrac{4\sin80^\circ}{\sin\alpha_r}\ {\rm mm}, & \text{规定梯度模式},
\end{cases}
\qquad
\mathbf b^0_{rc}=\mathbf c^0_{rc}-L_{rc}\mathbf a_{rc}.
\]

B 保证实际 `L_rc` 同时绑定几何、碰撞、梁、强度和力臂。C 不得另建格点或用统一 4 mm 覆盖梯度阵列。

每一完整试探轮，全部配置针：

- 从同一接受单元快照出发；
- 读取同一声明的共享 DamageStore 快照；
- 使用相同共同背板增量及对应的静态针级安装变换；
- 只调用 A 的 `embedded_constitutive_trial`；
- 不接收 `P_i/N` 或任何逐针法向预载；
- 包括开放、零载荷、硬限位、退化和终止针；终止针可使用 A 的确定性 fast path，但不得从响应集合消失。

#### 4.2 单元平衡与 graph

唯一分支在 `UX_PZ_BALANCED` 模式下满足

\[
\boxed{
r_z(u_z;u_x,P_i)
=
\mathbf E_Z^{\mathsf T}\sum_j\mathbf F_j(u_x,u_z)-P_i=0.
}
\]

刚性/退化分支使用

\[
\boxed{
0\in\mathcal N_U(u_x,u_z)-P_i,
\qquad
d_z=\operatorname{dist}(P_i,\mathcal N_U).
}
\]

若 graph 可行但反力不唯一，B 返回 `BALANCED_DEGENERATE`、graph handle、秩、零空间和代表值状态；不得用罚刚度或针 ID 选择伪唯一解。

在 `PRESCRIBED_XZ_RESIDUAL` 模式，B 返回同一 `r_z` 或 `d_z`，但只有其通过声明容差时才可标记为平衡。

#### 4.3 刚性与独立轴向弹簧

- `RIGID_MOUNT` 是精确轴向约束分支，不由“大有限刚度”实现。
- `AXIAL_SPRING_MOUNT` 的 A 状态满足
  \[
  0\le\delta_{s,j}\le4\ {\rm mm},\qquad
  f_{s,j}\ge0,
  \]
  内部分支可表示为
  \[
  f_{s,j}=k_{s,j}\delta_{s,j}+\lambda_{h,j},
  \qquad
  \lambda_{h,j}\ge0,\quad
  \lambda_{h,j}(4-\delta_{s,j})=0,
  \]
  其中实际接触释放、零压缩和硬限位切换由 A 的 admissible branch/graph 决定。
- 维持接触若需要负压缩或拉簧力，A 必须释放相应轴向约束或接触；B/C 不得允许弹簧伸长承拉。
- 局部接触、针梁、轴向弹簧和硬限位反力已经包含在 A 返回的净 `A_on_B` wrench 中，B/C 均不得重复相加。

#### 4.4 切线、割线和恒推力凝聚

在固定、唯一且可线性化分支上，

\[
\mathbf K_{Wq}^{\rm raw}
=
\frac{\partial\mathbf W_U}{\partial\mathbf q_U}
=
\sum_j\mathbf K_j
=
\begin{bmatrix}
\mathbf K_{W,x}&\mathbf K_{W,z}
\end{bmatrix}.
\]

令

\[
k_{zx}
=
\mathbf E_Z^{\mathsf T}\mathbf K_{F,x},
\qquad
k_{zz}
=
\mathbf E_Z^{\mathsf T}\mathbf K_{F,z}.
\]

仅当 `k_zz` 可逆、分支唯一且 tangent status 合格时，

\[
\frac{du_z}{du_x}\bigg|_{P_i}
=
-\frac{k_{zx}}{k_{zz}},
\]

\[
\boxed{
\mathbf K_{W,x\mid P_i}
=
\mathbf K_{W,x}
-
\mathbf K_{W,z}\frac{k_{zx}}{k_{zz}}.
}
\]

切线可非对称、非正定或不可用。跨事件、集合值分支、近奇异 `k_zz` 或参考点几何项未认证时，B 必须返回一侧切线、割线、graph 或 `TANGENT_UNAVAILABLE`，不得伪造普通一致切线。

#### 4.5 事件分数与重求解

每根针返回的建议共同增量分数为 \(\gamma_j\in(0,1]\)，单元归约为

\[
\boxed{\gamma_U=\min_j\gamma_j.}
\]

若 \(\gamma_U<1\)：

1. 当前目标试探不可提交；
2. B 返回全部事件候选、括区间和规范同时事件组；
3. C 必须参与跨单元归约；
4. 缩短后必须重新调用受全局平衡影响的全部单元；
5. B 在新的共同目标重新求全部针和 `u_z`/残量；不得缩放旧 wrench、旧 `u_z` 或旧损伤意图。

单元内部的同时事件由 B 归约；跨单元同时事件由 C 归约，但不得丢弃 B 的原始事件组。

#### 4.6 事件后重平衡、损伤和级联

在事件坐标上，B 按以下依赖偏序重算：

```text
接触支持/几何分支
  -> 粘滑/支持迁移与弹簧内部/硬限位分支
  -> 当前力状态下的材料容量与针体强度
  -> 共享损伤协调
  -> 全阵列共同平衡与容量复核
```

该偏序不删除同时事件。事件后一侧、DamageStore 协调或级联轮每次都重新调用全阵列并重新装配平衡。B 不使用等载、全局均分、最近邻均分、距离权重或失效针旧峰值包。

同一位置级联允许 `du_x=0` 而 `du_z` 改变；只有达到稳定 fixed point、明确物理终止、未认证终止或数值终止后才返回最终候选。

### 5. B→C 输出合同

`EmbeddedUnitTrialResponse` 必须包含下列分栏。字段不可用时应返回 `not_applicable/unavailable` 及原因，不能伪造零值。

#### 5.1 响应身份与可追溯性

```text
response_identity:
  unit_instance_id / unit_slot_id
  request_hash / response_hash
  global_step_id / global_trial_id / global_newton_iteration_id
  B_internal_trial_id / event_group_id / cascade_id
  versions_read
  deterministic_replay_manifest
```

#### 5.2 contact-only 合 wrench

```text
contact_only_wrench:
  force_N[3]
  moment_Nmm[3]
  direction_semantics: A_on_B
  expressed_frame_id
  reference_point_id: O_A
  units
  wrench_uniqueness
  action_reaction_check
  reference_transport_work_check
```

作用—反作用相反量可作为检查字段返回，但 C 装配必须使用 `A_on_B`。

#### 5.3 合力作用线、作用点与压力中心

当 \(\|\mathbf F_U\|>0\) 时，B 可返回中心轴：

\[
\mathbf r_\perp
=
\frac{\mathbf F_U\times\mathbf M_U^{O_A}}
{\|\mathbf F_U\|^2},
\qquad
\mathbf M_\parallel
=
\frac{\mathbf F_U^{\mathsf T}\mathbf M_U^{O_A}}
{\|\mathbf F_U\|^2}\mathbf F_U.
\]

输出规则：

- `resultant_central_axis` 在力非零且数值质量合格时可用；
- 仅当 \(\mathbf M_\parallel\) 在声明容差内为零时，wrench 可由单一纯力作用线表示；
- 单一“作用点”仍沿力方向不唯一，只有与声明参考平面相交且该直线不平行于平面时才可返回唯一交点；
- `center_of_pressure` 必须声明参考平面、定义、存在性、唯一性和质量；
- 力近零、存在不可忽略自由力偶、平面平行、交点越界或 graph 非唯一时必须返回 `not_available`，不得伪造点。

#### 5.4 主动、控制与约束分栏

```text
active_normal_actuator:
  P_i_N
  ideal_generalized_force
  ideal_wrench_at_O_A
  action_line_status: UNRESOLVED_IDEAL_GENERALIZED_FORCE
control_reactions:
  R_x_N
  x_displacement_control_force_vector
constraints:
  y_translation_reaction_N
  rotational_reaction_moment_Nmm[3]
assembly_policy:
  CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1
```

#### 5.5 坐标、平衡和 graph

```text
kinematics_and_balance:
  control_mode
  q_U_n / q_U_trial / accepted_to_trial_increment
  P_i_N
  u_z_solution_if_solved
  r_z_N or normal_graph_distance_N
  normal_resultant_graph_handle
  balance_status
  uniqueness / branch_id
  rank / nullspace_handle / condition_indicator
  certification_level
```

#### 5.6 切线、割线与 graph

```text
linearization:
  raw_K_Wq
  generalized_K_Qq
  k_zx / k_zz
  condensed_K_W_x_given_P_i
  secant_optional
  admissible_graph_handle_optional
  tangent_status
  branch / one_sided_direction
  source_and_target_reference_points
  expressed_frame / units
  validity_domain / trust_region
  finite_difference_or_consistency_metadata
```

任何线性化必须带参考点、坐标、单位、分支和有效域。

#### 5.7 单元内部状态摘要

```text
state_summary:
  unit_main_state
  transaction_phase
  active_support_summary
  load_bearing_summary
  stick_slip_mixed_summary
  spring_interior_and_hardstop_summary
  material_and_strength_event_summary
  recoverable_and_terminal_needle_summary
  N_nominal / N_geom / N_load / N_eff
  N_hardstop / N_invalid / N_degenerate
  load_inequality_metrics_by_named_channel
```

状态标签不能替代原始 gap、力、摩擦裕度、弹簧压缩、强度裕度和 graph。

#### 5.8 行程、损伤和历史摘要

```text
remaining_capacity:
  per_needle_spring_compression_mm_summary
  per_needle_spring_remaining_travel_mm_summary
  hardstop_identity_set
  remaining_standalone_drag_mm_if_applicable
  remaining_certified_trial_path_mm
  unit_search_recoverability
damage_and_history:
  DamageStore_version / snapshot_hash
  damage_read_set_summary / write_set_summary
  conflict_signature
  recent_event / cascade / reengagement_summary
  opaque_full_history_handle
  accepted_state_id / commit_receipt_id
```

`remaining_standalone_drag_mm` 只在同一 standalone 路径定义下使用；不得把它当成尚未固定的 C 整爪最大搜索距离。

#### 5.9 历史相关能力接口

```text
capability:
  response_type: HISTORY_DEPENDENT_LOCAL_OPERATOR
  local_wrench_or_graph
  valid_branch
  trust_region
  predicted_event_distance_and_bracket
  damage_version_dependency
  state_version_dependency
  quality_and_uncertainty
  full_unit_resolve_callback_requirement
  callback_reason_codes[]
```

该接口不是无记忆极限面，不得只给峰值或有效刺数。

#### 5.10 事件输出

```text
events:
  all_event_candidates[]
  unit_simultaneous_event_group
  earliest_event_fraction
  event_fraction_basis
  suggested_common_increment_fraction
  event_brackets
  pre_event / event_point / post_event phase status
  cascade_groups[]
  recoverability
  terminal_or_continuable
```

所有并发事件均记录；依赖偏序只决定重算顺序。

#### 5.11 质量、失败和认证

```text
diagnostics:
  all_status_codes[]
  primary_status
  residuals
  energy_and_work_ledger
  numerical_error_ledger
  domain / collision / geometry quality
  model / parameter availability
  equilibrium feasibility / physical stability
  nonuniqueness / degeneracy
  certification_level
  last_valid_accepted_state_id
```

`NUMERICAL_NONCONVERGENCE`、`MODEL_UNAVAILABLE`、`OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN`、`BODY_COLLISION_INVALID` 和 `KINEMATIC_MODE_UNSUPPORTED` 均不得改写为物理失效或零承载。

#### 5.12 事务输出

```text
transaction:
  opaque_trial_handle
  rollback_token
  provisional_commit_intent
  provisional_intent_is_prepare_eligible
  damage_read_write_sets
  cross_unit_conflict_signature
  versions_read
  request_response_hashes
  idempotency_key
```

`armed_commit_token` 只在 C 提交全局接受清单后由 `prepare_embedded_unit_commit` 返回；普通 trial response 不得提前携带可直接提交的永久令牌。

### 6. 功、能量和质量账本

#### 6.1 单元外部控制功

B 对 standalone 或可解释的嵌入路径返回

\[
\boxed{
\Delta W_{\rm ext}
=
\int R_x\,du_x
-
\int P_i\,du_z.
}
\]

由于向墙压入 `du_z<0`，主动推力项可为正输入功。

#### 6.2 A 子系统输入功

按 `A_on_B` 方向，输入全部 A 子系统的基座功为

\[
\boxed{
\Delta W_{\rm in,A}^{\rm base}
=
-\sum_j\int
(\mathbf W_j^{G,O_A})^{\mathsf T}
\mathbf H_U\,d\mathbf q_U.
}
\]

B 只装配 A 返回的能量通道：

- 梁、轴向弹簧和可选局部接触的可恢复储能；
- 摩擦和材料损伤耗散；
- A 定义的释放可恢复能/能量汇；
- 硬限位和理想约束的功边界；
- 数值残量和积分误差。

#### 6.3 试探无副作用

C 全局 Newton、事件定位、回溯、并行顺序变化和重复同键调用不得累计：

- 路径或时间；
- 滑移、循环或再挂接计数；
- 材料损伤；
- 摩擦/材料耗散；
- 事件号；
- DamageStore 版本。

只有全局原子提交收据中的最终差量进入接受历史。数值残量、积分误差和浮点归约误差必须单列，不能伪装成材料耗散。

#### 6.4 同位置级联

同一位置级联有 `du_x=0`，但重新平衡可有 `du_z≠0`，故 `-P_i du_z` 不必为零。C/B 必须保留该功项，不得假定零外功。

### 7. 局部预测、完整回调与能力有效域

#### 7.1 可使用局部低维响应的必要条件

只有以下条件同时成立时，C 才可在返回的 trust region 内使用局部切线、割线或 graph：

1. 请求的参考点、坐标、控制模式、`P_i` 参数化与返回量一致；
2. 当前活动支持、粘滑、弹簧、材料和强度分支不变；
3. DamageStore、逐针接受状态、表面和参数版本不变；
4. 预测增量不跨越任何事件括区间；
5. 切线/graph 状态和 `k_zz` 质量合格；
6. C 的运动仍位于 x/z 认证子空间；
7. 结果未接近域边界、体碰撞、模型有效域或未认证状态；
8. C 未要求精确逐针损伤冲突、级联或恢复判断。

#### 7.2 强制完整 B 回调条件

满足任一条件时，C 必须重新调用完整 `embedded_array_unit_trial`，不得外推旧摘要：

- 预测或实际跨越接触建立/释放、摩擦边界、真实滑移起始、支持迁移、材料起始/软化、针体强度、硬限位或再挂接事件；
- 活动集、分支、DamageStore 或任一接受状态版本改变；
- graph 集合值、切线不可用/奇异/超出有效域；
- 超出 trust region 或改变控制模式；
- 快照陈旧；
- 接近碰撞、域边界或几何质量下降；
- C 请求局部 y、转动或 rocking；
- 需要精确逐针裕度、共享损伤、级联、作用点或能量判断；
- `full_unit_resolve_callback_requirement=true`。

#### 7.3 禁止的能力简化

C 不得：

- 把 `UnitCapabilityState` 当成无记忆极限面；
- 用四个单元峰值简单相加；
- 用 `N_eff`、活动针数或平均单刺力代替 contact-only wrench；
- 假定切线全局有效、唯一、对称或光滑；
- 删除 opaque 历史句柄后继续推进历史相关状态。

### 8. 四单元事件归约、共享损伤与全局重求解

#### 8.1 跨单元最早事件

设四个单元返回 \(\gamma_{U_i}\)，C 必须计算

\[
\boxed{
\gamma_C=\min_{i=1,\ldots,4}\gamma_{U_i}.
}
\]

若 \(\gamma_C<1\)：

1. 当前四单元目标全部不可提交；
2. C 缩短共同整爪增量；
3. C 重新计算每个单元的合法 x/z 试探输入；
4. C 重新调用所有受整体平衡影响的单元；当前刚性四单元整体问题默认要求四个单元全部重调；
5. C 不得只更新触发最早事件的单元，也不得缩放旧 wrench。

#### 8.2 跨单元同时事件

C 在不丢弃各 B 单元原始事件组的前提下，将事件括区间重叠或位于全局同时事件容差内的单元事件组成跨单元规范事件组。规范排序只用于哈希和重放，不决定物理先后。

单元内部事件依赖由 B 处理；跨单元共同运动、全局力/力矩平衡及全局事件接受由 C 处理。

#### 8.3 跨单元共享 DamageStore

若四单元共享同一墙面 DamageStore，C 必须：

1. 收集各 B 返回的 opaque damage intents、read/write sets、核重叠签名和版本；
2. 检查跨单元写—写、写—读和损伤核重叠；
3. 把全部冲突意图交给 B/A 共享损伤协调器；C 不得自行相加、取最大值或按调用顺序覆盖；
4. 获取共同 trial DamageStore 或明确非唯一/未解决状态；
5. 用该共同 trial snapshot 重新调用全部受损伤与全局平衡影响的单元；
6. 重复直到损伤快照、冲突图、四单元响应和 C 全局残量形成一致 fixed point。

跨单元冲突未解决时返回 `DAMAGE_CONFLICT_UNRESOLVED`，全部 trial 回滚。

### 9. 嵌套事务和全局原子提交

#### 9.1 三层无副作用边界

1. A embedded trial 对单刺接受历史无副作用；
2. B embedded unit trial 对整个单元及 DamageStore 接受历史无副作用；
3. C 全局 Newton、事件归约和损伤协调期间，所有 B/A provisional intents 均不可永久提交。

#### 9.2 prepare 条件

只有下列条件全部满足，C 才可对四单元 provisional intents 发起 `prepare`：

- C 的全局力/力矩/运动残量通过；
- 所有 B 单元残量或 graph 条件通过；
- 全局最早事件及同时事件组完整；
- 单元内部和跨单元损伤冲突已协调；
- 所有版本、请求/响应哈希和幂等性键一致；
- 质量、能量和认证要求通过；
- 没有 `KINEMATIC_MODE_UNSUPPORTED`、模型/参数/几何/域/碰撞、陈旧、事务或数值致命状态；
- 四单元最终候选对应同一全局试探和同一 DamageStore trial snapshot。

#### 9.3 原子提交

C 必须把四单元、其内部 A 状态、共享 DamageStore、事件账本和能量账本放入一个 `global_bundle_manifest`。提交语义为：

```text
all prepare succeed
  -> issue one atomic global commit
  -> all four unit receipts and one shared damage receipt become visible
otherwise
  -> rollback every unit trial and shared damage trial
  -> no accepted version advances
```

任一单元、C 全局残量、版本、持久化或收据失败时，不能只提交“成功单元”。同一提交幂等性键的重复请求只能返回原收据或安全拒绝，不能重复累计物理历史。

#### 9.4 rollback

C 在以下任一情况必须 rollback 全部相关 trial：

- 缩短全局增量；
- Newton/事件分支被拒；
- 更早事件被发现；
- DamageStore trial 改变；
- 任一版本陈旧；
- C 全局残量或质量失败；
- 用户/求解器放弃当前 global trial。

### 10. C 的强制义务

C 必须：

1. 使用版本化坐标变换将每个 `A_on_B` contact-only wrench 运输到整爪参考点，并验证功不变；
2. 按 `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1` 恰好装配一次 contact-only wrench；
3. 把 \(P_i\)、x 控制反力和 y/转动约束反力保留为独立字段，不重复加入外部墙面 wrench；
4. 尊重切线/graph 的分支、有效域、非唯一性、单位和参考点；
5. 保留 B 返回的原始事件、活动针、剩余行程、损伤、质量、失败和 opaque 历史句柄；
6. 在全局接受前保持全部 B trial 无副作用；
7. 对全局最早事件缩短共同增量并重调全部受影响单元；
8. 对共享 DamageStore 冲突组织联合协调；
9. 只有全局条件通过后才准备并原子提交；
10. 对未认证运动或状态显式终止/扩展，不得静默降维；
11. 保存请求/响应哈希、版本、变换和提交收据以支持确定性重放；
12. 区分代数平衡存在、物理稳定、可恢复脱附、不可恢复脱附、未认证和数值失败。

### 11. C 的禁止事项

C 不得：

- 重新定义 A 的接触、摩擦、材料、损伤、针梁、轴向弹簧、硬限位、释放或再挂接；
- 重新定义 B 的共同法向平衡、活动集、载荷共享、失效重分配、级联或再挂接；
- 直接修改逐针 A 状态、B opaque 状态或 DamageStore；
- 给逐针分配 \(P_i/N\)、指定逐针力或活动针集合；
- 用邻接图、距离权重、等载或旧峰值包转移失效载荷；
- 用有限大刚度替代 `RIGID_MOUNT`；
- 把四个单元峰值相加或用低维摘要替代强制完整回调；
- 把 `NUMERICAL_NONCONVERGENCE`、`MODEL_UNAVAILABLE`、`PARAMETER_UNAVAILABLE`、`OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN`、`BODY_COLLISION_INVALID` 或 `KINEMATIC_MODE_UNSUPPORTED` 改写为物理失效或零承载；
- 通过旋转旧 wrench、不重求针级状态来伪装 rocking 支持；
- 按单元调用顺序覆盖跨单元损伤；
- 在 C 全局接受前提交任一单元；
- 丢弃非唯一 graph、原始事件或失败代码，只保留单一摘要值。

### 12. 状态、失败分类与认证优先级

#### 12.1 致命认证优先级

主摘要状态按以下类别选取，但 `all_status_codes` 必须完整保留：

```text
CONTRACT_VIOLATION / STALE_SNAPSHOT
-> KINEMATIC_MODE_UNSUPPORTED
-> OUT_OF_DOMAIN / GEOMETRY_UNCERTAIN / BODY_COLLISION_INVALID
-> MODEL_UNAVAILABLE / PARAMETER_UNAVAILABLE
-> DAMAGE_CONFLICT_UNRESOLVED / TRANSACTION_ERROR
-> NUMERICAL_NONCONVERGENCE
-> UNIT_DETACHED_IRRECOVERABLE / PHYSICAL_INSTABILITY / EQUILIBRIUM_INFEASIBLE
-> EQUILIBRIUM_DEGENERATE
-> EVENT_REDUCTION_REQUIRED / EVENT_REBALANCE_REQUIRED
-> CASCADE_STABILIZED / REENGAGED / AT_TRAVEL_LIMIT
-> BALANCED_UNIQUE / CONTINUE_SMOOTH
```

该优先级只决定摘要，不能删除并发状态。

#### 12.2 关键语义

- `EQUILIBRIUM_INFEASIBLE`：在模型、几何和参数可用条件下，已穷尽当前 admissible 分支并证明无代数平衡。
- `PHYSICAL_INSTABILITY`：可有代数平衡，但 A/B 的一侧稳定性或 admissible graph 证明不存在可继续的稳定准静态分支；不能仅由负切线或 Newton 失败推断。
- `UNIT_DETACHED_RECOVERABLE`：当前无承载，但存在 continuable 针、合法搜索域和剩余路径。
- `UNIT_DETACHED_IRRECOVERABLE`：已证明剩余合法路径无法再挂接，或全部针终止。
- `NUMERICAL_NONCONVERGENCE`：尚不能证明物理无解，算法未收敛。
- `EQUILIBRIUM_DEGENERATE`：平衡存在但反力/分支集合值或秩退化。
- `AT_TRAVEL_LIMIT`：至少一根弹簧位于 4 mm 硬限位，不自动等于单元失败。

### 13. 合同验证矩阵

以下测试是合同实现验收前的最低验证要求；本已接受文件只冻结测试定义，不声称实现已通过。

| 编号 | 测试 | 必须检查的结果 |
|---:|---|---|
| C01 | 单元作用—反作用、参考点运输、坐标旋转 | `A_on_B` 方向一致；运输后力矩正确；功标量不变 |
| C02 | `contact_only`、主动推力、控制和约束分栏 | 整爪接触装配不漏算、不重复；`P_i` 不再加入 contact-only |
| C03 | standalone driver 与一个 embedded kernel 的外部驱动等价边界 | 在相同接受/提交序列上，接受状态与原始历史一致 |
| C04 | 相同 B trial 重复调用、rollback 和幂等性 | 无路径、时间、滑移、损伤、耗散或事件号累计 |
| C05 | C 四单元串行/并行及调用顺序置换 | 响应在单元映射下相同，或返回同一明确非唯一集合 |
| C06 | 单元内部与跨单元 event fraction 归约 | 得到同一全局最早事件和完整同时事件组；缩短后全部重调 |
| C07 | 光滑分支切线/有限差分 | raw 与凝聚切线在有效域内一致；参考点与单位正确 |
| C08 | 跨事件、graph 非唯一、切线奇异 | 强制完整回调或返回 graph，不外推旧切线 |
| C09 | 跨单元共享 DamageStore 冲突 | 联合协调、受影响单元重求解、调用顺序不覆盖 |
| C10 | 全局原子提交故障注入 | 任一 prepare/commit/持久化失败后四单元和 DamageStore 全部不变 |
| C11 | 运动子空间 | 合法 x/z 通过；局部 y、单元转动或 rocking 请求明确拒绝 |
| C12 | 单位唯一换算 | `R_t` 和 `k_s` 只换算一次；输出单位与 schema 一致 |
| C13 | `P_i` 所有权 | A 请求中无逐针法向载荷；B 外层只施加一次 |
| C14 | 刚性 mount | 使用精确 graph/约束；不存在“大有限刚度”正式分支 |
| C15 | 作用点存在性 | 非零自由力偶、零力或平面平行时不伪造单一作用点 |
| C16 | 失败分类注入 | 域外、几何不确定、碰撞、参数缺失、物理无解、物理失稳、退化和数值未收敛分别触发 |
| C17 | 同位置级联能量 | `du_x=0` 时仍保留 `-P_i du_z`，数值残量不计材料耗散 |
| C18 | C 缩短全局步 | 不缩放旧 `u_z`/wrench；四单元从同一接受快照重求 |
| C19 | 低维能力状态 | trust region、事件距离、版本依赖与完整回调标志完整 |
| C20 | rocking 防伪 | 旋转旧 wrench 或冻结姿态的方案必须被测试拒绝 |

### 14. 未决扩展与关闭条件

| 未决项 | 当前安全处理 | 关闭条件 |
|---|---|---|
| 真实法向执行器作用线和力矩 | 仅返回零力矩理想广义力；外部接触装配只用 contact-only | CAD/机构定义、作用—反作用对象和功测试形成新合同版本 |
| `rocking=on` 的真实单元转动 | `KINEMATIC_MODE_UNSUPPORTED` | B 支持姿态更新、逐针转动、碰撞/表面查询、切线与验证 |
| 局部 y 平移和完整 6D 单元响应 | 明确拒绝 | 扩展运动学和 A/B 接口并重新认证 |
| 刚性 admissible graph 的具体数据结构 | 返回版本化 handle；不可用则 `MODEL_UNAVAILABLE` | 联合 graph 查询、序列化、秩/零空间和测试通过 |
| 跨四单元 DamageStore 协调实现 | C 仅组织，B/A 协调器决定物理合并 | 确定性冲突测试与全局原子提交故障注入通过 |
| C 搜索停止阈值与最大搜索距离 | 不由 B 合同固定；B 仅返回原始历史和候选能力 | C1 后续根据单元仿真/实验正式确定 |
| 成功阈值、综合评分和能力特征阈值 | 保留原始连续量及 feature config | 验证目标和统计方案经正式审查 |
| 材料、表面、损伤、摩擦、接触刚度和数值容差 | 显式参数/模型 ID 或 unavailable | 文献、测量、标定和收敛验证关闭 |
<!-- END B_TO_C_PUBLIC_CONTRACT -->

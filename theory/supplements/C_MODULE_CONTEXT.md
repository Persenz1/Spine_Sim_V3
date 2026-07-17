# 大模块 C：十字主动对爪同步预紧与偏心承载算子——截至 C3 的完整上下文

> 大模块：`C`
> 当前完成阶段：`C3 — 单元渐进失效、整体重分配与最大承载`
> 上下文版本：`0.3.0`
> 工程事实版本：`engineering_fixed_context 1.0.0`
> 上游合同：`B_TO_C 1.0.0 accepted`
> 基线：`C_MODULE_CONTEXT 0.2.0 accepted`
> 提示词版本：`C3 1.0.0`
> 运行：`C3-r01`
> 当前状态：`accepted`

## 0. 文档性质、权威顺序与当前结论

本文件是大模块 C 在已接受 C1、C2 基础上完成 C3 理论推导后的最新完整滚动上下文。第 1–15 节完整继承 C1 的同步搜索、内部预紧、停止、跨单元事件、共享损伤和原子事务；第 16–30 节完整继承 C2 的刚体运动学、偏心加载点、六维 wrench 装配、固定姿态/小角度摇摆、稳定平衡与 B 合同覆盖审计；第 31–48 节新增 C3 的历史相关单元状态压缩、针级事件传播、四单元递归再平衡、渐进剥离、稳定反力曲线、最大承载、峰后终止、实验输出和大模块 C 集成交接。第 29 节是 C2 当时对 C3 的历史交接清单，已由第 31–48 节逐项处理；不得据此把 C3 新内容误读为独立增量文件。

权威顺序固定为：

1. `engineering_fixed_context 1.0.0`：固定坐标、十字几何、共同径向锁定、各单元主动法向推力、偏心加载点/方向、rocking 开关、输出要求、损伤边界和首版排除；
2. `B_TO_C 1.0.0 accepted`：冻结当前 B 唯一入口、x/z 认证运动子空间、contact-only wrench、历史相关 graph、事件、共享 DamageStore 和嵌套事务；
3. `C_MODULE_CONTEXT 0.2.0 accepted`：冻结 C1+C2 的完整初态、刚体/wrench/功定义、稳定性、失败分类和 B 运动合同缺口；
4. `MECHANISM_MODULE_PLAN` 与 `C3_PROMPT 1.0.0`：规定 C3 必答问题、边界、完成判据和四文件输出合同；
5. 本地文献 23、28：文献 23 只提供活动集 `7→6→7` 切换、剩余分支增载和力阶跃的特殊基准；文献 28 只提供给定活动集的整体力/力矩平衡、单爪能力约束和最大最小裕度骨架；
6. GPT 通用知识：用于历史相关集合值响应、非光滑事件定位、分支延拓、一侧稳定性、峰值确认、可达性和原子事务语义；不引入未经批准的工程数值。

C3 形成的渐进承载试探与终止算子为

$$
\boxed{
\mathcal P_{C3}:
\left(
\mathcal S_{C2,n},
\Delta\delta_P,
\hat{\mathbf d},
\{P_i\}_{i=1}^{4},
\mathcal D_n,
\Theta_{\mathrm{event}},
\Theta_{\mathrm{stability}},
\Theta_{\mathrm{peak}}
\right)
\mapsto
\left(
\mathcal S_{C3,n+1}^{\mathrm{trial/accepted}},
F_{\mathrm{reaction}},
\mathcal E_{C3},
\mathcal M_{C3},
\Sigma_{C3}
\right)
}
$$

其中 `S_C2,n` 是完整 `C2AcceptedState` 或其后继 `C3AcceptedState` 中嵌入的完整 C2 物理状态；`E_C3` 保留 B 单元内部事件组并形成跨单元事件/级联记录；`M_C3` 保存首个针失效、首个单元显著退化、最弱分支、稳定峰值候选、峰后分支和终止证据；`Sigma_C3` 明确区分平衡接受、事件缩步、退化 graph、合同/运动未认证、物理无平衡、物理失稳、可恢复/不可恢复脱附、数值失败和事务失败。

**当前最重要的认证结论保持不变**：C3 的完整理论状态机、数据合同、事件重平衡、稳定分支峰值和终止定义已经形成；但 `B_TO_C 1.0.0` 只认证单元局部 x 与全局 Z 平移。正式 `+X`、`45°` 墙面内加载必然要求至少部分单元的局部 y 平移，真实 rocking 还要求动态姿态、针轴、表面和碰撞更新。因此，在 B 2.x 等完整 twist/姿态扩展实现并被接受前，任何非零正式 C3 加载必须返回 `C3_CONTRACT_EXTENSION_REQUIRED`（或继承的上游未认证状态），保留最后有效 `C1PreloadState/C2AcceptedState`，不得推进 `delta_P`、DamageStore、事件、功、峰值账本或 `F_crit` 确认。该安全拒绝不是零承载、物理失效或不可恢复脱附。

---

# 第一篇：C1 已接受基线（完整继承）

以下第 1–15 节保留 C1 accepted 内容。它们定义 C2 的唯一合法预紧初态和事务边界。

## 1. 范围、边界与必须遵守的工程事实

### 1.1 C1 已覆盖的物理与算法问题

C1 已定义：

- 四个单元局部坐标到全局十字参考点 $C$ 的静态安装变换；
- B 规范参考点 $O_A$ 与工程几何参考点 $O_i$ 的显式、版本化偏置；
- contact-only wrench 的力、力矩、参考点运输和 wrench–twist 功不变检查；
- 唯一共同径向搜索坐标 $s$ 及四单元同步位移约束；
- 与 $s$ 功共轭的共同驱动广义反力，而不是错误地相加相反方向的全局力；
- 每单元恒定法向主动推力 $P_i$ 下的 B 无副作用调用；
- contact-only wrench、主动推力、径向控制反力和其他约束反力的所有权分栏；
- 对置分支内部预紧、全局接触残量和搜索支承反力诊断；
- 四单元最早事件、同时事件、共享损伤 fixed point、同位置级联和全局原子提交；
- 参数化、可计算且不硬编码数值的停止策略；
- 阈值和最大搜索距离的离线反推流程；
- 正常停止后的 `C1PreloadState`、径向锁定和 C2/C3 交接。

### 1.2 C1 明确不处理的内容

以下内容不属于本阶段：

- 球尖接触、摩擦、针梁、轴向弹簧、材料失效、逐针载荷共享和 B 内部级联的重新推导；
- 直接调用 A 或解析、改写 A/B opaque 状态；
- 加载点离墙 $50\ \mathrm{mm}$ 的偏心外载平衡；
- $+X$ 与 $45^\circ$ 工况下的整体反力曲线和最大承载；
- $\theta_X,\theta_Y$ 小角度摇摆；当前 B 合同对此未认证；
- 偏心加载下单元渐进剥离、四单元再平衡和峰后终止；
- 框架/导轨有限元、传动链真实刚度、惯性动力学、大角度倾覆或绕 $Z$ 扭转；
- 未经标定的停止阈值、搜索上限、综合评分、材料参数、表面参数和数值容差。

### 1.3 必须继承的工程事实 ID

| 类别 | 必须遵守的事实 ID | C1 中的作用 |
|---|---|---|
| 层级边界 | `PROJECT.ARCHITECTURE.PHYSICAL_LEVELS`、`PROJECT.ARCHITECTURE.DEPENDENCY` | C 只能调用 B，不能重建 A/B 低层机理。 |
| 全局/单元坐标 | `COORDINATE.GLOBAL.FRAME`、`COORDINATE.UNIT.FRAME` | 固定 $\mathbf E_X,\mathbf E_Y,\mathbf E_Z$ 与局部 $+x_i$。 |
| 十字几何 | `GEOMETRY.CROSS.LAYOUT` | 固定四方向、$O_i$ 和 $80\times80\ \mathrm{mm}$ 中央空区。 |
| 搜索同步 | `LOAD.CROSS.SEARCH_SYNCHRONIZATION` | 四单元只有一个共同 $s$；不得独立搜索。 |
| 法向推力 | `LOAD.NORMAL.ACTUATOR_OUTPUT`、`LOAD.NORMAL.CROSS_GRIPPER` | $P_i$ 是每单元主动广义推力，范围各自为 $0.5$–$2\ \mathrm N$。 |
| 运动边界 | `KINEMATICS.CROSS.RIGID_REFERENCE` | C1 主线为 `rocking=off`；真实 rocking 不得伪装。 |
| 数值事件 | `NUMERICS.DRAG.VARIABLE_STEP` | 非光滑事件需要缩步和定位。 |
| 输出边界 | `PROJECT.OUTPUTS.NO_BINARY_SUCCESS` | 当前不定义二元成功，只保留连续量和事件。 |
| 损伤 | `DAMAGE.MEMORY.LIGHTWEIGHT` | 同一次连续过程保留共享轻量损伤，新独立样本重置。 |
| 未决项 | `UNRESOLVED.C1.STOP_THRESHOLD`、`UNRESOLVED.C1.MAX_SEARCH_DISTANCE` | 阈值和上限必须显式配置/标定，不能硬编码。 |
| 首版排除 | `SCOPE.FIRST_RELEASE.EXCLUSIONS` | 禁止越界到框架柔性、惯性、大角度运动等。 |

---

## 2. 坐标、参考点、符号与单位

### 2.1 全局基、四个单元局部基和固定安装矩阵

全局右手基为

$$
\mathcal F_G=\{C,\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
$$

其中墙面名义平面为 $X$–$Y$，$+Z$ 从墙面指向背板。正式编号采用

$$
\begin{aligned}
\mathbf e_{x_1}&=+\mathbf E_X,&
\mathbf e_{x_2}&=-\mathbf E_X,&
\mathbf e_{x_3}&=+\mathbf E_Y,&
\mathbf e_{x_4}&=-\mathbf E_Y,\\
\mathbf e_{y_i}&=\mathbf E_Z\times\mathbf e_{x_i}.
\end{aligned}
$$

因此

$$
\begin{aligned}
\mathbf e_{y_1}&=+\mathbf E_Y,&
\mathbf e_{y_2}&=-\mathbf E_Y,&
\mathbf e_{y_3}&=-\mathbf E_X,&
\mathbf e_{y_4}&=+\mathbf E_X.
\end{aligned}
$$

从第 $i$ 个单元局部分量到全局分量的静态旋转为

$$
\boxed{
\mathbf R_{Gi}
=
\begin{bmatrix}
\mathbf e_{x_i}&\mathbf e_{y_i}&\mathbf E_Z
\end{bmatrix}
}
$$

即

$$
\mathbf R_{G1}=\begin{bmatrix}1&0&0\\0&1&0\\0&0&1\end{bmatrix},\quad
\mathbf R_{G2}=\begin{bmatrix}-1&0&0\\0&-1&0\\0&0&1\end{bmatrix},
$$

$$
\mathbf R_{G3}=\begin{bmatrix}0&-1&0\\1&0&0\\0&0&1\end{bmatrix},\quad
\mathbf R_{G4}=\begin{bmatrix}0&1&0\\-1&0&0\\0&0&1\end{bmatrix}.
$$

四个矩阵均必须满足

$$
\mathbf R_{Gi}^{\mathsf T}\mathbf R_{Gi}=\mathbf I,
\qquad
\det\mathbf R_{Gi}=+1.
$$

工程几何参考点为

$$
\boxed{
\mathbf O_i=\mathbf C-40\,\mathbf e_{x_i}\ \mathrm{mm}
}
$$

即

$$
\begin{aligned}
\mathbf O_1&=(-40,0,z_C)\ \mathrm{mm},&
\mathbf O_2&=(+40,0,z_C)\ \mathrm{mm},\\
\mathbf O_3&=(0,-40,z_C)\ \mathrm{mm},&
\mathbf O_4&=(0,+40,z_C)\ \mathrm{mm}.
\end{aligned}
$$

### 2.2 B 规范参考点 $O_A$ 与工程参考点 $O_i$

`B_TO_C` 将 $O_A$ 定义为未加载针尖球心规则格点的几何中心；工程事实中的 $O_i$ 是十字安装参考点。二者不得默认同点。

定义版本化偏置

$$
\boldsymbol\rho_{A/i}^{i}
=
\overrightarrow{O_iO_{A_i}}
$$

并令其在第 $i$ 个单元局部基中表达。则从 $C$ 指向 $O_{A_i}$ 的全局向量为

$$
\boxed{
\mathbf r_{A_i/C}^{G}
=
-40\,\mathbf e_{x_i}
+
\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i}
}
$$

请求必须携带：

- `O_i_reference_point_id`；
- `O_A_reference_point_id`；
- $\boldsymbol\rho_{A/i}^{i}$；
- `transform_id/version`；
- `geometry_hash` 与 `unit_config_hash`。

只有当绑定文件显式给出 $\boldsymbol\rho_{A/i}^{i}=\mathbf0$ 且哈希匹配时，才可把 $O_A$ 与 $O_i$ 视为同点。

### 2.3 Wrench 旋转、参考点运输与 twist 对偶变换

设 B 返回的第 $i$ 个 contact-only wrench 在源表达框架 $\mathcal F_{S_i}$、参考点 $O_{A_i}$ 表达：

$$
\mathbf W_i^{S_i,O_A}
=
\begin{bmatrix}
\mathbf F_i^{S_i}\\
\mathbf M_i^{S_i,O_A}
\end{bmatrix}.
$$

从源框架到全局框架的旋转记为 $\mathbf R_{GS_i}$。若 B 已按合同返回全局表达，则 $\mathbf R_{GS_i}=\mathbf I$；若返回单元局部表达，则 $\mathbf R_{GS_i}=\mathbf R_{Gi}$。C 不得猜测，必须读取 `expressed_frame_id`。

运输到全局参考点 $C$：

$$
\boxed{
\begin{aligned}
\mathbf F_i^{G,C}&=\mathbf R_{GS_i}\mathbf F_i^{S_i},\\
\mathbf M_i^{G,C}&=\mathbf R_{GS_i}\mathbf M_i^{S_i,O_A}
+\mathbf r_{A_i/C}^{G}\times\mathbf F_i^{G,C}.
\end{aligned}
}
$$

对应同一刚体增量，若 $C$ 点的 twist 增量为

$$
\Delta\boldsymbol\xi_C^G=
\begin{bmatrix}
\Delta\mathbf u_C^G\\
\Delta\boldsymbol\theta^G
\end{bmatrix},
$$

则 $O_{A_i}$ 点在源框架中的增量为

$$
\boxed{
\begin{aligned}
\Delta\boldsymbol\theta^{S_i}
&=\mathbf R_{GS_i}^{\mathsf T}\Delta\boldsymbol\theta^G,\\
\Delta\mathbf u_{A_i}^{S_i}
&=\mathbf R_{GS_i}^{\mathsf T}
\left(
\Delta\mathbf u_C^G
+\Delta\boldsymbol\theta^G\times\mathbf r_{A_i/C}^{G}
\right).
\end{aligned}
}
$$

必须验证功不变：

$$
\boxed{
\left(\mathbf W_i^{S_i,O_A}\right)^{\mathsf T}
\Delta\boldsymbol\xi_{A_i}^{S_i}
=
\left(\mathbf W_i^{G,C}\right)^{\mathsf T}
\Delta\boldsymbol\xi_C^{G}
}
$$

数值验收同时检查绝对误差和相对误差；容差属于 `numerical_config_id`，当前未固定。

### 2.4 公共单位和符号方向

公共单位继承 `B_TO_C`：

| 量 | 单位 |
|---|---|
| 长度、位移、行程、事件距离 | mm |
| 力、广义平移反力 | N |
| 力矩 | N·mm |
| 角度 | rad |
| 时间 | s |
| 刚度 | N/mm |
| 无量纲裕度、置信度和比例 | 1 |

方向约定：

- $+s$：四个单元各自沿局部 $+x_i$ 向十字中心搜索；
- $+u_{z_i}$：远离墙面，向墙压入为 $du_{z_i}<0$；
- $P_i>0$：主动执行器施加 $-P_i\mathbf E_Z$；
- B 返回 `A_on_B`：A/墙面接触子系统作用于单元背板的 wrench；
- 正抓附阻力
  $$
  R_{x_i}=-\mathbf e_{x_i}^{\mathsf T}\mathbf F_i^G,
  $$
  当接触阻碍 $+s$ 时 $R_{x_i}>0$。

### 2.5 主要符号

| 符号 | 含义 | 单位 |
|---|---|---|
| $s$ | 唯一共同径向搜索坐标 | mm |
| $\Delta s$ | 当前共同试探增量 | mm |
| $P_i$ | 第 $i$ 单元恒定法向主动推力 | N |
| $u_{z_i}$ | 第 $i$ 单元法向位置 | mm |
| $\mathbf W_i^{G,C}$ | 第 $i$ 单元运输到 $C$ 的 contact-only wrench | N, N·mm |
| $R_{x_i}$ | 第 $i$ 单元沿自身搜索轴的正阻力 | N |
| $Q_s^{\mathrm{contact}}$ | contact-only wrench 对共同 $s$ 的广义力 | N |
| $Q_s^{\mathrm{drive}}$ | 驱动器为维持正向搜索所需的广义反力 | N |
| $p_X,p_Y$ | 两组对置分支的内部轴向预紧幅值 | N |
| $\Delta_X,\Delta_Y$ | 两组对置分支的轴向不平衡量 | N |
| $\gamma_{U_i}$ | 第 $i$ 单元建议的共同增量分数 | 1 |
| $\gamma_C$ | 四单元全局最早事件分数 | 1 |
| $\mathbf A_i$ | 第 $i$ 单元多通道 C1 能力特征 | 按通道声明 |
| $A_G$ | 版本化聚合后的 C1 预紧质量特征 | 配置声明 |
| $m_i$ | 第 $i$ 单元最弱归一化裕度 | 1 |
| $m_{\min}$ | 四单元最弱分支裕度 | 1 |
| $s_{\max}$ | C1 搜索上限，待标定 | mm |

---

## 3. 输入、输出、状态和数据模型

### 3.1 必需输入

每个 C1 全局试探必须具备：

1. 四个不可变 B 已接受快照及内部 A opaque 状态句柄；
2. 共同已接受坐标 $s_n$、目标 $s^*$ 或 $\Delta s$；
3. 四个 $P_i$，每个均独立位于工程范围 $0.5$–$2\ \mathrm N$；
4. 四套静态安装变换和 $O_A\rightarrow C$ 参考点运输；
5. 同一个共享 DamageStore 已接受快照、版本与哈希；
6. B、工程事实、参数、表面、配置和状态兼容性版本；
7. B 控制模式：`UX_PZ_BALANCED` 或 `PRESCRIBED_XZ_RESIDUAL`；
8. 事件、数值、能力特征和停止策略配置 ID；
9. `rocking=off` 认证声明；
10. 幂等性键和确定性重放清单。

缺失必需字段不得由 C 以默认值补齐。缺失 $s_{\max}$、阈值配置、材料/表面/模型参数时返回 `PARAMETER_UNAVAILABLE`/`STOP_UNCERTIFIED`，不得借用 B 的 $100\ \mathrm{mm}$。

### 3.2 必需输出

C1 输出至少包括：

- 四个原始 `EmbeddedUnitTrialResponse` 或不可丢失句柄；
- 四个运输到 $C$ 的 contact-only wrench；
- 全局 contact-only 合 wrench 与分量残量；
- 每单元 $R_{x_i}$、$u_{z_i}$、balance/graph、状态、行程、损伤和能力；
- $Q_s^{\mathrm{contact}}$、$Q_s^{\mathrm{drive}}$、$p_X,p_Y,\Delta_X,\Delta_Y$；
- 约束/控制闭合所需的诊断反力，且明确不属于额外墙面承载；
- 跨单元最早事件、同时事件组、损伤冲突图和 fixed-point 状态；
- 平台、边际收益、最弱分支、安全和行程指标；
- 功/能量、残量、质量、认证、版本、哈希和事务令牌；
- 一个互斥主决策状态及完整正交诊断码。

### 3.3 历史变量与持久范围

C1 是历史相关过程，以下量只能在全局原子提交后推进：

- $s$ 和已接受路径长度；
- 四个 B 单元及其内部 A 状态版本；
- 每针接触、滑移、失效、再挂接、弹簧和硬限位历史；
- 共享 DamageStore；
- 事件序号、级联序号和停止判据保持窗口；
- 功/能量账本；
- 请求/响应哈希和提交收据。

Newton 试探、事件定位、回溯、并行调用和重复幂等性键均不得累计上述历史。

### 3.4 `C1SearchRequest`

```text
C1SearchRequest:
  identity:
    gripper_instance_id
    global_step_id / global_trial_id / global_newton_iteration_id
    global_event_sequence_id / caller_sequence_id
    request_idempotency_key
  versions_and_hashes:
    engineering_context_version = 1.0.0
    B_TO_C_contract_version = 1.0.0
    B_model_version
    configuration / geometry / parameter / surface / state hashes
    transform_bundle_id / version
  common_path:
    s_n_mm
    target_s_mm | requested_delta_s_mm
    interpolation_rule
    path_fraction_basis
    event_side_request
  units[4]:
    unit_slot_id / instance_id
    P_i_N
    control_mode
    accepted_B_snapshot_handle
    accepted_A_bundle_handle
    q_U_n
    surface_realization_id / version
    unit_config_hash / parameter_bundle_hash
    T_G_from_A_id / version / transform
  damage:
    shared_damage_snapshot_handle / version / content_hash
  policy:
    stop_policy_id / version
    capability_feature_config_id / version
    aggregation_config_id / version
    window / hysteresis / confidence config IDs
    s_max_mm
  requested_response:
    B trial phase
    tangent / graph / capability modes
    event location and full-unit-resolve flags
    deterministic replay request
```

约束：

- 四个 `target_u_x` 必须由同一 $s$ 映射；
- 不得出现逐针力、$P_i/N$、逐针活动集、C 自算损伤增量或低层参数覆盖；
- `caller_sequence_id` 只用于审计，不决定物理分支；
- 请求真实转动、局部 $y$ 平移或 rocking 时立即返回未认证状态。

### 3.5 `C1SearchTrialResponse`

```text
C1SearchTrialResponse:
  identity_and_trace:
    request_hash / response_hash
    global and per-unit trial IDs
    versions_read / deterministic_replay_manifest
  raw_unit_responses:
    EmbeddedUnitTrialResponse[4] | lossless handles
  transformed_contact_wrenches:
    W_i_at_C[4]
    summed_contact_only_wrench_at_C
    reference_transport_work_checks[4]
  preload_and_control:
    R_x_i[4]
    Q_s_contact / Q_s_drive
    p_X / p_Y / Delta_X / Delta_Y
    search_support_wrench_required
    active_normal_actuator_fields[4]
    control_and_constraint_reactions[4]
  balance_and_state:
    u_z_i / residual_or_graph[4]
    balance status / rank / nullspace / branch[4]
    recoverability / travel / hardstop / quality[4]
  events_and_damage:
    all unit event groups
    gamma_U_i / gamma_C
    cross-unit simultaneous event group
    damage conflict graph / coordination iteration / fixed-point status
  stop_features:
    A_i multi-channel features
    A_G and validity
    m_i / m_min
    plateau / marginal-gain / persistence indicators
    safety and travel margins
  diagnostics:
    all_status_codes / primary_status
    residual, work, energy and numerical error ledgers
    certification and last valid accepted state
  transaction:
    rollback tokens[4]
    provisional commit intents[4]
    shared damage provisional intent
    prepare eligibility / global bundle draft
```

不可用字段必须写 `unavailable/not_applicable` 及原因，不能伪造为零。

### 3.6 `C1PreloadState`

```text
C1PreloadState:
  identity:
    preload_state_id / commit_receipt_id
    s_stop_mm
    stop_primary_status / all reason codes
  accepted_bundle:
    accepted_B_snapshots[4]
    accepted_A_opaque_handles[4]
    accepted_q_U_and_control_modes[4]
    shared_DamageStore_version / hash
  transforms:
    static installation transforms[4]
    O_A_to_C transport IDs / versions
  accepted_mechanics:
    contact_only_wrench_at_C[4]
    summed_contact_only_wrench / residual
    R_x_i / Q_s_drive / pair preload and imbalance
    u_z_i / balance graph and branch data
    active, control and constraint fields kept separate
  capability_and_safety:
    A_i / A_G / m_i / m_min
    remaining search and spring travel
    damage / hardstop / collision / domain quality summaries
    stop-condition evidence for every gate
  history:
    accepted events / cascades / reengagement summaries
    power and energy ledger
    request-response hashes / deterministic replay manifest
  lock_and_handoff:
    radial lock rule: u_x_i = s_stop for all i
    variables allowed to continue evolving through B/A
    rocking support boundary
    C2/C3 full-callback conditions
```

`C1PreloadState` 是 C2/C3 的唯一预紧初态。任何下游重置 $s$、清空 DamageStore、重建单刺状态或只保留四个峰值均为合同违反。

---

## 4. 共同搜索约束、虚功和内部预紧

### 4.1 唯一共同径向坐标

四个单元严格满足

$$
\boxed{
 u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s
}
$$

以及

$$
\Delta u_{x_i}=\Delta s,
\qquad i=1,\ldots,4.
$$

共同的是运动学路径坐标，不共同的是：

- $u_{z_i}$ 或法向残量；
- contact-only wrench；
- 活动集、粘滑、损伤和再挂接历史；
- 弹簧压缩、硬限位和剩余行程；
- 事件距离、能力和最弱裕度；
- 平衡分支和 graph 非唯一性。

四个地形方向不同导致响应不同是预期结果，不是同步约束违反。

C1 当前不固定物理搜索速度，在线算法只使用共同路径坐标、位移增量和事件位置。B standalone 路径中的 $1\ \mathrm{mm/s}$ 时间映射不得继承为 C1 搜索速度；若未来需要时间控制，必须以新的版本化驱动策略显式加入。共同零点也必须由请求绑定：四个 B 快照的 `u_x=0` 必须对应同一 C1 搜索起点，不能用隐藏的单元偏置制造“表面上相同的 $s$”。

### 4.2 与 $s$ 功共轭的广义力

第 $i$ 个单元因 $ds$ 产生的平移虚位移为

$$
\delta\mathbf u_i^G=\mathbf e_{x_i}\,\delta s.
$$

contact-only wrench 对共同坐标的虚功为

$$
\delta W_{\mathrm{contact}}
=
\sum_{i=1}^{4}
\mathbf F_i^{G}\cdot\mathbf e_{x_i}\,\delta s
=
Q_s^{\mathrm{contact}}\,\delta s,
$$

因此

$$
\boxed{
Q_s^{\mathrm{contact}}
=
\sum_{i=1}^{4}\mathbf e_{x_i}^{\mathsf T}\mathbf F_i^G
=
-\sum_{i=1}^{4}R_{x_i}
}
$$

理想位移控制驱动器的反向广义力为

$$
\boxed{
Q_s^{\mathrm{drive}}
=-Q_s^{\mathrm{contact}}
=
\sum_{i=1}^{4}R_{x_i}
}
$$

在 $ds>0$ 且各分支阻碍搜索时，$Q_s^{\mathrm{drive}}>0$，驱动输入功为

$$
\delta W_s^{\mathrm{drive}}
=Q_s^{\mathrm{drive}}\,ds>0.
$$

该标量不能由四个全局力直接求和代替。对称对置分支的全局面内力可以相消，但 $Q_s^{\mathrm{drive}}$ 仍非零。

### 4.3 法向主动推力功与径向搜索功分离

第 $i$ 个单元主动法向广义力为

$$
\mathbf F_{\mathrm{act},i}=-P_i\mathbf E_Z.
$$

其功为

$$
\boxed{
\delta W_{P_i}=-P_i\,du_{z_i}
}
$$

向墙压入时 $du_{z_i}<0$，故该项可为正输入功。C1 的外部控制功账本为

$$
\boxed{
\Delta W_{\mathrm{control}}
=
\int Q_s^{\mathrm{drive}}\,ds
-
\sum_{i=1}^{4}\int P_i\,du_{z_i}
}
$$

`contact_only_wrench` 已包含 A 内部接触、针梁、弹簧和硬限位的净反力；$P_i$ 只作为 B 外层控制参数和独立功通道出现，不能再次加入 contact-only 墙面装配。

### 4.4 对置分支内部预紧与不平衡

定义逐单元轴向正阻力 $R_{x_i}$ 后，两组对置分支的内部预紧幅值为

$$
\boxed{
 p_X=\frac{R_{x_1}+R_{x_2}}{2},
 \qquad
 p_Y=\frac{R_{x_3}+R_{x_4}}{2}
}
$$

对应轴向不平衡量为

$$
\boxed{
 \Delta_X=R_{x_2}-R_{x_1},
 \qquad
 \Delta_Y=R_{x_4}-R_{x_3}
}
$$

在理想纯轴向情形：

$$
\mathbf F_{12,\parallel}^G
=(-R_{x_1}+R_{x_2})\mathbf E_X
=\Delta_X\mathbf E_X,
$$

$$
\mathbf F_{34,\parallel}^G
=(-R_{x_3}+R_{x_4})\mathbf E_Y
=\Delta_Y\mathbf E_Y.
$$

理想对称状态满足 $R_{x_1}=R_{x_2}$、$R_{x_3}=R_{x_4}$，故全局面内轴向合力为零；同时

$$
Q_s^{\mathrm{drive}}
=2(p_X+p_Y)>0
$$

可以成立。这严格区分了“整体面内合力为零”和“内部预紧/驱动反力为零”。

实际响应可能含横向、法向和力矩分量，故必须另行装配完整 contact-only wrench：

$$
\boxed{
\mathbf W_{\mathrm{contact}}^{G,C}
=
\sum_{i=1}^{4}\mathbf W_i^{G,C}
}
$$

$p_X,p_Y,\Delta_X,\Delta_Y$ 只是轴向诊断，不能替代完整 wrench。

### 4.5 搜索阶段的控制/约束闭合诊断

C1 在 `rocking=off` 和规定 $s$ 下对参考体施加理想运动约束。异质地形可使 $\mathbf W_{\mathrm{contact}}^{G,C}$ 出现非零面内残量、横向分量或力矩。定义

$$
\boxed{
\mathbf W_{\mathrm{support,req}}^{C1}
=-\mathbf W_{\mathrm{contact}}^{G,C}
}
$$

作为“规定运动搜索装置/机器人基体为保持当前试探姿态所需的闭合 wrench”诊断。该量：

- 不是额外墙面接触能力；
- 不得再次加到 contact-only wrench 中提高承载；
- 不证明实际导轨或框架能够承担该载荷；
- 只说明当前规定运动问题需要何种控制/约束反力；
- 必须随 `active_normal_actuator`、`x_displacement_control`、`y/rotation constraints` 分栏记录。

停止策略可配置对面内残量、对置不平衡和约束反力的最大允许裕度，但其阈值当前未固定。C2 必须从 contact-only wrench 和明确的执行器/约束模型重新建立整体平衡，不能把该诊断当成免费外部支承。

---

## 5. B 单元调用、平衡语义和装配规则

### 5.1 唯一 B 物理入口

C1 只能调用

```text
embedded_array_unit_trial(request) -> EmbeddedUnitTrialResponse
```

该入口必须从不可变已接受快照出发，无副作用地完成 B1 几何映射、逐针 A embedded 调用、B2 平衡/残量、B3 事件定位、损伤意图和同位置级联候选构造。

C1 不得：

- 调用 `standalone_continuous_unit_driver` 作为在线物理入口；
- 直接调用 A；
- 指定逐针力、逐针预载或活动集合；
- 读取或修改 opaque 状态和 DamageStore；
- 用 $N_{\mathrm eff}$、平均单刺力或四个单元峰值替代 B 响应；
- 缩放旧 wrench、旧 $u_z$ 或旧损伤意图生成新试探。

离线标定可以读取 B 层已经正式生成的连续单元结果，但这不改变 C 在线唯一入口。

### 5.2 `UX_PZ_BALANCED`

在主线控制模式中，C 给定

$$
u_{x_i}=s,
\qquad
P_i,
$$

B 求 $u_{z_i}$，唯一分支满足

$$
\boxed{
 r_{z_i}(u_{z_i};s,P_i)
 =
 \mathbf E_Z^{\mathsf T}\mathbf F_i(s,u_{z_i})-P_i=0
}
$$

退化分支满足集合值 graph：

$$
0\in\mathcal N_{U_i}(s,u_{z_i})-P_i.
$$

C 必须保留：

- `BALANCED_UNIQUE` 或 `BALANCED_DEGENERATE`；
- $r_{z_i}$ 或 graph 距离；
- rank、nullspace、代表分支和条件指标；
- 质量、域和认证状态。

graph 可行但反力不唯一时，不能按单元 ID、调用顺序或最小范数静默选伪唯一解。若停止特征要求标量，必须使用配置声明的保守集合映射，例如对 admissible graph 取能力下界，并保留原 graph 句柄。

### 5.3 `PRESCRIBED_XZ_RESIDUAL`

当未来更高层规定 $s,u_{z_i}$ 时，B 返回完整单元试探和法向残量/graph 距离。只有

$$
|r_{z_i}|\le\varepsilon_{z}
$$

或 graph 距离通过配置容差时，才可称为平衡。未闭合残量不能因数值接近、求解器退出或代表值存在而改写为 `BALANCED`。

C1 的常规同步搜索优先使用 `UX_PZ_BALANCED`。`PRESCRIBED_XZ_RESIDUAL` 用于：

- 验证法向平衡；
- 外层耦合迭代的残量评估；
- 事件点/退化 graph 的一致性检查；
- 为 C2 预留规定姿态接口。

### 5.4 每个共同试探点的四单元调用表

| 项目 | 单元 1 | 单元 2 | 单元 3 | 单元 4 |
|---|---|---|---|---|
| 共同切向坐标 | $s^*$ | $s^*$ | $s^*$ | $s^*$ |
| 法向主动推力 | $P_1$ | $P_2$ | $P_3$ | $P_4$ |
| 接受快照 | $\mathcal H_{U_1,n}$ | $\mathcal H_{U_2,n}$ | $\mathcal H_{U_3,n}$ | $\mathcal H_{U_4,n}$ |
| 表面/方向 | 各自绑定 | 各自绑定 | 各自绑定 | 各自绑定 |
| DamageStore | 同一版本 $\mathcal D_n$ | 同一版本 | 同一版本 | 同一版本 |
| B 输出 | $\mathcal R_{U_1}$ | $\mathcal R_{U_2}$ | $\mathcal R_{U_3}$ | $\mathcal R_{U_4}$ |
| 可不同量 | $u_z,W,$事件、能力、行程、状态 | 同左 | 同左 | 同左 |

四个调用可串行或并行，但必须：

- 从同一全局接受步开始；
- 使用匹配各自单元的接受快照；
- 读取同一共享损伤版本；
- 采用同一目标 $s^*$；
- 不以调用完成顺序决定事件或损伤先后。

### 5.5 `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`

C1 唯一合法装配策略为：

1. 将四个 `A_on_B` contact-only wrench 各运输一次到 $C$；
2. 求和得到 $\mathbf W_{\mathrm{contact}}^{G,C}$；
3. 将 $P_i$、$R_{x_i}$、横向和转动约束反力保留为独立字段；
4. 不把任何上述控制/约束量再次加入墙面 contact-only wrench。

必须记录

```text
assembly_policy_id: CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1
```

若未来显式建模真实执行器实体、作用线和对其他刚体的反力，必须升级合同；当前零力矩理想广义力不等价于已知 CAD wrench。

### 5.6 局部切线、割线与完整回调

C1 只有在以下条件同时成立时，才可在 B 返回的 trust region 内使用局部切线、割线或 graph：

- 参考点、表达框架、控制模式和 $P_i$ 参数化一致；
- 活动支持、粘滑、弹簧、材料和强度分支不变；
- DamageStore、接受状态、表面和参数版本不变；
- 预测增量不跨越事件括区间；
- 切线/graph 状态和 $k_{zz}$ 质量合格；
- 运动仍在 x/z 认证子空间；
- 不需要精确损伤冲突、级联、作用点或恢复判断。

出现任一事件、graph 非唯一、切线奇异、快照陈旧、域/碰撞边界、DamageStore 改变、控制模式改变、真实 rocking 请求或 `full_unit_resolve_callback_requirement=true` 时，必须完整回调 B。

---

## 6. 跨单元事件、共享损伤和嵌套事务

### 6.1 全局最早事件

第 $i$ 个单元对当前共同增量返回

$$
\gamma_{U_i}\in(0,1].
$$

C1 归约为

$$
\boxed{
\gamma_C=\min_{i=1,\ldots,4}\gamma_{U_i}
}
$$

若 $\gamma_C<1$：

1. 当前四单元目标全部不可提交；
2. 当前所有 trial 回滚或丢弃；
3. 将共同目标缩短到事件括区间/事件点；
4. 四个单元从同一接受快照和同一 DamageStore 重新试探；
5. 重新求各自 $u_{z_i}$、wrench、事件和损伤意图；
6. 不得只重调最早事件单元；
7. 不得按 $\gamma_C$ 缩放旧 $u_z$、旧 wrench、旧切线或旧损伤。

### 6.2 跨单元同时事件

C1 保留每个 B 单元的原始 `unit_simultaneous_event_group`，再将映射到共同 $s$ 后满足以下任一条件的事件组成跨单元同时事件组：

- 事件括区间相交；
- 事件点距离不超过版本化 $\varepsilon_s^{\mathrm{sim}}$；
- B/A 协调器声明为同一共享损伤冲突核中的耦合事件。

规范排序仅用于哈希和确定性重放，可采用

```text
(event_s, unit_slot_id, B_event_group_id, local_event_id)
```

但排序不得决定物理先后。物理更新仍遵守 B 冻结的依赖偏序：几何支持 → 粘滑/弹簧分支 → 材料/强度 → 共享损伤 → 全阵列平衡。

### 6.3 共享 DamageStore 协调 fixed point

若四个单元共享墙面 DamageStore，C1 对每轮试探执行：

1. 收集四单元的 opaque damage intents、read/write sets、核重叠签名和版本；
2. 构造跨单元写—写、写—读和损伤核重叠图；
3. 将冲突意图交给 B/A 共享损伤协调器；
4. 协调器返回共同 trial DamageStore $\mathcal D^{(m+1)}$ 或明确非唯一/失败状态；
5. 从同一全局接受状态，用 $\mathcal D^{(m+1)}$ 重调全部受影响单元；当前刚性四单元问题默认重调四个单元；
6. 重复直到 DamageStore 内容哈希、冲突图、四单元响应和 C1 指标一致；
7. 若达到配置迭代/误差边界仍不一致，返回 `DAMAGE_CONFLICT_UNRESOLVED` 或 `STOP_NUMERICAL`，全部回滚。

C 不得自行相加损伤、取最大值、按调用顺序覆盖或直接写 DamageStore。

### 6.4 同位置级联

事件点上可出现

$$
ds=0,
\qquad
du_{z_i}\ne0.
$$

因此：

- 四单元仍需重新平衡；
- $-P_i\,du_{z_i}$ 仍必须进入功账本；
- 接触释放、材料失效、硬限位和再挂接可在同一 $s$ 形成级联；
- 每轮级联均从同一事件点的最新共同 trial DamageStore 重新调用 B；
- 只有形成稳定 fixed point、明确物理终止、未认证终止或数值终止后，才可构造最终候选。

### 6.5 prepare、原子提交与回滚

只有下列条件全部满足，C1 才可对四个 provisional intents 发起 prepare：

- 共同 $s$ 和四个控制模式一致；
- 四个 B 平衡/graph 条件通过；
- wrench 运输和功不变检查通过；
- 全局最早/同时事件完整；
- DamageStore 冲突已协调；
- 同位置级联已稳定；
- 停止指标使用的是当前一致候选；
- 版本、哈希、幂等性键和认证通过；
- 没有致命合同、运动、模型、参数、域、碰撞、损伤或数值状态。

提交包必须包含：

```text
global_bundle_manifest:
  four B provisional intents
  all internal A provisional states
  one shared DamageStore provisional intent
  accepted event/cascade ledger
  power and energy ledger
  stop-decision evidence
  versions / hashes / replay manifest
```

语义为：

```text
all prepare succeed
  -> one atomic global commit
  -> four unit receipts + one shared damage receipt become visible
otherwise
  -> rollback every trial
  -> no accepted version advances
```

重复同一幂等性键只能返回原收据或安全拒绝，不能重复累计路径、损伤、耗散或事件号。

### 6.6 不同终止状态的提交政策

| 状态 | 候选是否可提交 | 规则 |
|---|---|---|
| `CONTINUE_SEARCH` | 是 | 当前一致、认证、事件闭合的正常步原子提交后继续。 |
| `STOP_PRELOAD_ACCEPTED` | 是 | 停止条件全部满足，提交后生成 `C1PreloadState`。 |
| `STOP_AT_SEARCH_LIMIT_UNQUALIFIED` | 条件性 | 若 $s=s_{\max}$ 的当前状态认证且安全，可提交为“上限未达标”终态；不得标成功。 |
| `STOP_SAFETY_LIMIT` | 只提交最后安全状态 | 越界试探回滚；若当前状态安全而下一合法步将越界，可提交当前状态后停止。 |
| `STOP_IRRECOVERABLE` | 条件性 | 只有已定位、已协调并证明不可恢复的物理事件终态可提交。 |
| `STOP_UNCERTIFIED` | 否 | 保留最后有效接受状态，不提交未认证候选。 |
| `STOP_NUMERICAL` | 否 | 算法未收敛不等于物理失败，保留最后有效状态。 |

---

## 7. C1 能力特征、最弱分支与联合停止策略

### 7.1 停止策略的基本原则

C1 停止不是“总力超过阈值”。正常停止必须同时满足：

1. C1 预紧质量进入经定义的平台/接近最大区；
2. 继续搜索的乐观边际收益已足够低；
3. 最弱分支达到最低裕度；
4. 没有过预紧、不可接受损伤、强度/行程/碰撞/域/认证问题；
5. 条件在规定窗口、事件侧和统计置信规则下持续成立；
6. $s\le s_{\max}$，且候选可以确定性重放并原子提交。

所有阈值、窗口、滞回、置信水平、归一化尺度和 $s_{\max}$ 均属于版本化策略配置。缺失配置时不得继续以隐式默认值运行。

### 7.2 每单元多通道能力特征 $\mathbf A_i$

C1 只从 B 合同允许的字段构造能力特征。定义

$$
\boxed{
\mathbf A_i(s)
=
\Phi_{\chi_A}
\left(
\mathcal R_{U_i}(s)
\right)
}
$$

其中 `capability_feature_config_id = χ_A` 必须声明每个通道的：名称、单位、正方向、归一化尺度、有效分支、trust region、缺失值处理和是否参与平台/安全/最弱门槛。

允许的原始输入至少包括：

| 通道类别 | 允许来源 | 典型单位 | 使用边界 |
|---|---|---|---|
| 当前轴向阻力 | $R_{x_i}$、contact-only wrench | N | 不能单独代表最终能力。 |
| 局部历史相关能力 | B `capability` local operator/graph | 配置声明 | 必须保留分支、trust region 和回调条件。 |
| 事件距离 | predicted event distance/bracket | mm | 接近事件时不得外推旧切线。 |
| 承载/活动状态 | load-bearing、active support summaries | 离散/计数 | 不得用 $N_{\mathrm eff}$ 单独评分。 |
| 剩余搜索/弹簧行程 | certified path、spring travel | mm | B standalone 100 mm 不得充当 C 上限。 |
| 损伤/强度/碰撞/域质量 | B diagnostics 和 margin summaries | 1 或配置单位 | 缺失或未认证时正常停止禁用。 |
| graph/切线质量 | rank、nullspace、condition、uncertainty | 1 | 非唯一时采用集合下界或标记不可用。 |
| 持续性 | 已接受历史中的承载持续路径 | mm | 只使用已接受历史，不能偷看未来。 |

若某通道为集合值 graph，标量化必须采用配置声明的集合泛函，例如

$$
A_{ic}^{\mathrm{LB}}
=
\inf_{a\in\mathcal A_{ic}} a,
$$

并保留原 graph。若下界不存在或不可信，则该通道为 `unavailable`，不能用代表值伪装确定能力。

### 7.3 整体 C1 预紧质量 $A_G$

定义

$$
\boxed{
A_G(s)
=
\mathcal A_{\chi_G}
\left(
\mathbf A_1,\mathbf A_2,\mathbf A_3,\mathbf A_4,
\Delta_X,\Delta_Y
\right)
}
$$

`aggregation_config_id = χ_G` 必须明确：

- 输出单位或无量纲化方式；
- 对单元和对置不平衡的保守处理；
- graph 非唯一和缺失值处理；
- 随机不确定性和置信区间；
- 该量只是 C1 方向无关预紧质量或指定方向集合的代理，绝不等同于 C2/C3 最终六维最大承载。

首版可评估的保守候选为

$$
A_G^{\mathrm{cons}}(s)
=
\min_{i=1,\ldots,4} a_i^{\mathrm{LB}}(s),
$$

其中 $a_i$ 是配置声明的同量纲/归一化单元特征。该候选避免用强分支掩盖弱分支，但它仍需离线验证后才能成为正式策略。无论采用何种聚合，必须始终输出四个原始 $\mathbf A_i$。

### 7.4 最弱分支裕度

对每个需要门控的通道 $c$，定义有符号归一化裕度：

- 下限型约束：
  $$
  \widehat m_{ic}
  =\frac{y_{ic}-b_c}{\sigma_c};
  $$
- 上限型约束：
  $$
  \widehat m_{ic}
  =\frac{b_c-y_{ic}}{\sigma_c}.
  $$

其中 $b_c$ 是版本化边界，$\sigma_c>0$ 是尺度；两者均不得硬编码。正值表示在安全侧，零表示边界，负值表示违反。

单元和全局最弱裕度为

$$
\boxed{
 m_i(s)=\min_{c\in\mathcal C_m}\widehat m_{ic}(s),
 \qquad
 m_{\min}(s)=\min_{i=1,\ldots,4}m_i(s)
}
$$

不可用、未认证、非唯一但无保守下界的通道令 $m_i$ 无效；正常停止不得把无效值当成正裕度。

### 7.5 平台/接近最大区

离线标定对每个设计—表面—方向—推力—模型配置组建立稳健参考能力

$$
A_{G,\mathrm{ref}}
=
\operatorname{RobustReference}_{\chi_{\mathrm{ref}}}
\left(
\{A_G^{(r)}(s):s\in\mathcal D_{\mathrm{safe}}^{(r)}\}_{r=1}^{N}
\right),
$$

它可以是训练样本安全域内峰值/平台值的保守分位数或下置信界，但具体统计量必须由配置声明。

在线只使用当前和已接受历史。对事件分辨后的因果窗口 $\mathcal W_k$ 计算稳健估计 $\widetilde A_G(s_k)$ 及下置信界 $L_A(s_k)$，定义

$$
\boxed{
\rho_A(s_k)
=
\frac{L_A(s_k)}{A_{G,\mathrm{ref}}}
}
$$

平台接近条件为

$$
\rho_A(s_k)\ge\eta_A,
$$

其中 $\eta_A$ 未固定。若 $A_{G,\mathrm{ref}}\le0$、配置不匹配或参考域外，则平台指标无效。

### 7.6 继续搜索边际收益

在最近的已接受、事件分辨状态上计算一侧稳健割线。记所有合法点对斜率为

$$
 g_{ab}
 =
 \frac{\widetilde A_G(s_b)-\widetilde A_G(s_a)}{s_b-s_a},
 \qquad
 s_a<s_b\le s_k.
$$

定义其乐观上界

$$
\boxed{
 g_A^{U}(s_k)
 =
 \operatorname{UpperConfidence}_{\chi_g}
 \left(\{g_{ab}\}_{(a,b)\in\mathcal W_k}\right)
}
$$

单位为 $A_G/\mathrm{mm}$。只有当

$$
 g_A^{U}(s_k)\le\eta_g
$$

时，才可认为继续搜索的边际收益足够低。使用上置信界的原因是：若乐观估计仍低，停止结论更保守。

规则：

- 不跨未定位事件直接使用光滑导数；
- 重大滑脱、损伤或分支变化后重置受影响的保持窗口；
- 短暂峰值不触发停止；
- 非单调曲线使用稳健窗口统计和保持长度，不强迫单调化；
- 再挂接后可重新建立窗口；
- 多个平台取第一个同时通过全部门槛的区间，而不是第一个局部峰值。

### 7.7 安全、损伤和行程裕度

定义安全门槛集合

$$
\mathcal C_{\mathrm{safe}}
=
\{
\text{过预紧},
\text{材料/针体强度},
\text{DamageStore},
\text{弹簧剩余行程},
\text{硬限位},
\text{认证搜索行程},
\text{体碰撞},
\text{表面域/几何质量},
\text{模型/参数可用性}
\}.
$$

全局安全裕度为

$$
\boxed{
 m_{\mathrm{safe}}
 =
 \min_{i,c\in\mathcal C_{\mathrm{safe}}}
 \widehat m_{ic}
}
$$

注意：

- `AT_TRAVEL_LIMIT` 不自动等于失败，但若继续搜索需要越过硬限位或无剩余合法路径，则触发安全/不可恢复停止；
- 已发生 `BODY_COLLISION_INVALID`、`OUT_OF_DOMAIN` 或 `GEOMETRY_UNCERTAIN` 属于未认证候选，不能作为正常安全停止状态提交；
- “即将达到边界”可在最后安全状态触发 `STOP_SAFETY_LIMIT`；
- 安全裕度阈值和预测提前量均待标定。

### 7.8 保持窗口、滞回和统计置信

为避免单点误触发，正常停止条件必须在下列任一版本化规则下持续成立：

- 累计接受路径长度至少 $\ell_{\mathrm{hold}}$；
- 至少 $K_{\mathrm{hold}}$ 个独立接受状态；
- 在最近重大事件之后重新满足最小保持条件；
- 对随机样本/测量噪声采用声明的下置信界；
- 退出阈值与进入阈值分离形成滞回，防止反复停止/继续。

$\ell_{\mathrm{hold}}$、$K_{\mathrm{hold}}$、置信水平和滞回宽度当前均未固定。

### 7.9 正常停止逻辑

定义布尔门槛：

$$
\begin{aligned}
G_{\mathrm{valid}}&:\ \text{四单元、DamageStore、变换、功和事务均认证};\\
G_{\mathrm{plateau}}&:\ \rho_A\ge\eta_A;\\
G_{\mathrm{gain}}&:\ g_A^U\le\eta_g;\\
G_{\mathrm{weak}}&:\ L[m_{\min}]\ge m_{\mathrm{req}};\\
G_{\mathrm{safe}}&:\ L[m_{\mathrm{safe}}]>0;\\
G_{\mathrm{persist}}&:\ \text{保持/滞回/置信规则通过};\\
G_{\mathrm{range}}&:\ s\le s_{\max}.
\end{aligned}
$$

正常停止候选为

$$
\boxed{
G_{\mathrm{stop}}
=
G_{\mathrm{valid}}
\land G_{\mathrm{plateau}}
\land G_{\mathrm{gain}}
\land G_{\mathrm{weak}}
\land G_{\mathrm{safe}}
\land G_{\mathrm{persist}}
\land G_{\mathrm{range}}
}
$$

只有原子提交成功后，主状态才从候选变为 `STOP_PRELOAD_ACCEPTED`。

### 7.10 主决策状态与优先级

| 主状态 | 触发条件 | 物理含义 |
|---|---|---|
| `CONTINUE_SEARCH` | 有合法剩余路径，正常停止门槛未全部成立 | 继续共同搜索。 |
| `STOP_PRELOAD_ACCEPTED` | $G_{\mathrm{stop}}$ 成立且原子提交成功 | 合格预紧初态。 |
| `STOP_AT_SEARCH_LIMIT_UNQUALIFIED` | $s=s_{\max}$，但平台/最弱/保持等未达标 | 到上限但不合格，不能标成功。 |
| `STOP_SAFETY_LIMIT` | 下一合法步将越过过预紧、损伤、强度、行程或碰撞安全边界 | 在最后安全状态停止。 |
| `STOP_IRRECOVERABLE` | 策略要求的关键分支已证明无合法再挂接路径 | 物理不可恢复。 |
| `STOP_UNCERTIFIED` | 合同、运动、模型、参数、几何、域、碰撞或状态认证失败 | 不能得出物理失败结论。 |
| `STOP_NUMERICAL` | 事件、平衡、损伤 fixed point 或事务算法未收敛 | 算法失败，不等于物理无解。 |

主状态优先级遵守上游合同：合同/陈旧 → 运动不支持 → 域/几何/碰撞 → 模型/参数 → 损伤/事务 → 数值 → 不可恢复/物理失稳 → 退化/事件 → 正常平衡。全部正交诊断码必须保留。

### 7.11 弱分支例外政策

默认政策要求四个单元均通过最弱分支门槛。不得仅凭 $\sum_i R_{x_i}$ 或 $A_G$ 总量放宽弱分支。

若未来 C2/C3 证明某一载荷方向下可以由其他分支安全代偿，例外必须：

- 由版本化方向能力优化策略显式声明；
- 使用 C2/C3 完整整体平衡和能力域，而非 C1 峰值相加；
- 经过留出样本和实验验证；
- 在 `C1PreloadState` 中记录适用方向和失效代价；
- 不反向修改本版 C1 默认门槛。

---

## 8. 从 B 单元数据反推阈值和“尽可能短”的搜索距离

### 8.1 离线数据生成与来源边界

离线策略构造必须覆盖正式设计空间中与 C1 有关的组合：

- 阵列尺寸、方向和针距；
- 固定角或梯度角；
- 针径、针尖半径；
- 刚性或独立轴向弹簧安装；
- 弹簧刚度采样；
- 针弯曲开关；
- 表面类别、表面实现、随机种子和方向；
- 每单元 $P_i$；
- 材料、摩擦、损伤和数值配置版本。

数据可以由 B 层正式的连续单元运行产生；C1 在线运行仍只能调用 `embedded_array_unit_trial`。每条离线轨迹必须保存原始：

- contact-only wrench 和 $R_x(s)$；
- balance/graph、活动/承载状态；
- 事件、滑移、失效、再挂接和硬限位；
- DamageStore 与损伤摘要；
- 弹簧压缩和剩余行程；
- 首次有效承载位置；
- 峰值、持续距离和平台候选；
- 能力特征及其有效域；
- 质量、域、碰撞、模型和参数状态。

不能只保存峰值或最终点。

### 8.2 四方向样本组合与相关性

四个方向不得默认独立同分布。离线组合应尽可能保留：

- 同一墙面实现中相隔 $90^\circ$ 的方向相关性；
- 同一空间区域的共享 DamageStore 或相邻区域相关性；
- 表面各向异性；
- 相同制造批次和参数包的共同不确定性；
- 四个单元不同历史的条件相关性。

若只能使用独立单元轨迹拼接，必须将“独立拼接”标为近似数据模式，并在真实四方向表面/实验上另行验证，不能把 IID 假设写成正式事实。

### 8.3 离线特征计算

对每个样本组合 $r$：

1. 按同一候选共同坐标网格/事件点对齐四条单元轨迹；
2. 构造 $\mathbf A_i^{(r)}(s)$、$A_G^{(r)}(s)$、$m_i^{(r)}(s)$ 和 $m_{\min}^{(r)}(s)$；
3. 计算过预紧、损伤、强度、行程、碰撞和认证安全裕度；
4. 对非单调曲线保留所有事件，不以单调包络替换原始历史；
5. 用稳健窗口计算平台比、边际增益和保持条件；
6. 对短暂峰值、滑脱—再挂接和多个平台分别标记；
7. 找到同时满足全部候选门槛的第一个 $s$：

$$
\boxed{
 s_{\mathrm{first}}^{(r)}(\Theta)
 =
 \inf\{s:\ G_{\mathrm{stop}}^{(r)}(s;\Theta)=\mathrm{true}\}
}
$$

若集合为空，记录为“该配置在当前上限内无合格停止点”，不能丢弃样本。

### 8.4 策略参数选择

候选策略参数记为

$$
\Theta
=
\{\eta_A,\eta_g,m_{\mathrm{req}},\ell_{\mathrm{hold}},
\text{hysteresis},\text{confidence},s_{\max},\ldots\}.
$$

可采用以下约束优化结构选择“尽可能短”的策略：

$$
\boxed{
\min_{\Theta}
\operatorname{RobustStatistic}
\left(\{s_{\mathrm{first}}^{(r)}(\Theta)\}\right)
}
$$

约束为：

$$
\Pr\left(m_{\min}\ge m_{\mathrm{req}}\right)
\ge 1-\alpha_m,
$$

$$
\Pr\left(m_{\mathrm{safe}}\le0\right)
\le\alpha_s,
$$

以及平台保持、误停止率、未达标率和重放一致性要求。$\alpha_m,\alpha_s$ 等均为待审查统计配置，不在本轮固定。

### 8.5 留出验证和实验闭环

参数选择必须采用分层留出：

- 留出随机种子；
- 留出表面实现/空间区域；
- 留出表面类别或方向组合；
- 留出制造/参数批次；
- 最终用未来单元和四单元实验验证。

重采样应以独立表面实现/实验批次为单位，而不是把同一曲线上的相邻点当成独立样本。输出至少包括：

- $s_{\mathrm{first}}$ 分布和置信区间；
- 正常停止、上限未达标、安全停止、不可恢复和未认证比例；
- 最弱分支和安全裕度分布；
- 对阈值、窗口和 $s_{\max}$ 的敏感性；
- 训练/验证条件与正式使用条件的覆盖差异。

### 8.6 $s_{\max}$ 的确定原则

$s_{\max}$ 是离线策略的一部分，不等于 B 单元连续拖拽的 $100\ \mathrm{mm}$。候选确定方式为：

1. 在安全域内计算合格停止位置分布；
2. 选择能覆盖目标比例样本、同时不显著增加损伤/行程耗尽风险的上界；
3. 报告区间和未达标概率，而不是只给单值；
4. 在留出数据和实验中复核；
5. 经工程事实审批后才能成为正式固定值。

当前安全处理：

- `UNRESOLVED.C1.STOP_THRESHOLD` 保持未决；
- `UNRESOLVED.C1.MAX_SEARCH_DISTANCE` 保持未决；
- 在线请求若缺失已审查的策略配置，返回 `STOP_UNCERTIFIED`；
- 禁止回退到 $100\ \mathrm{mm}$ 默认值。

### 8.7 离线与在线信息边界

离线可查看完整曲线以拟合策略；在线只能使用：

- 当前一致 trial；
- 已接受历史；
- 版本化离线参考量和置信区间；
- B 返回的合法局部预测、event bracket 和 trust region。

在线不得读取当前真实试验未来的 $A_G(s)$、未来事件或未来峰值。任何使用未来信息的算法只能用于离线标注和评估，不能进入在线停止器。

---

## 9. 停止后的锁定、状态继承和释放边界

### 9.1 径向锁定

正常停止后

$$
\boxed{
 u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s_{\mathrm{stop}}
}
$$

共同径向坐标被锁定。后续 C2/C3：

- 不得给四单元分配不同的径向位移；
- 不得把 $s$ 重置为零；
- 不得把单元退回初始表面位置；
- 不得清除停止前事件、损伤和弹簧行程历史。

“锁定”表示 C 层不再主动推进共同搜索坐标，不表示单刺、针梁、轴向弹簧或接触状态被冻结。

### 9.2 冻结/可演化表

| 量 | C1 停止后处理 | 所有权 |
|---|---|---|
| $s_{\mathrm{stop}}$ | 冻结并作为下游径向约束 | C |
| 四个静态安装变换 | 冻结版本；rocking 扩展前不改变 | 工程事实/B→C |
| 四个 B/A 已接受快照 | 原样继承；不得解析改写 | B/A |
| 共享 DamageStore | 原样继承同一接受版本 | A/B 协调器 |
| 活动集、粘滑、材料、再挂接状态 | 可在后续合法 B trial 中演化 | B/A |
| 弹簧压缩和剩余行程 | 保留历史，可随后续载荷演化 | B/A |
| $u_{z_i}$ | `UX_PZ_BALANCED` 下继续由 B 在恒 $P_i$ 下平衡；规定姿态模式下返回残量 | B/C 控制模式 |
| $P_i$ | 作为版本化控制输入保留；不得静默改变 | C/B 外层 |
| contact-only wrench | 当前值作为初态；后续必须回调 B 更新 | B 返回、C 装配 |
| 能力/最弱裕度 | 当前审计快照；不作为永久无记忆极限面 | C1/B |
| 事件、能量、哈希、收据 | 永久审计历史 | C1 事务层 |
| $\theta_X,\theta_Y$ | 未认证，不在 C1 激活 | C2 扩展 |

### 9.3 rocking 边界

当前 B 合同只认证局部 x 和全局 Z 平移。若 C2 请求真实 $\theta_X,\theta_Y$：

- 必须返回 `KINEMATIC_MODE_UNSUPPORTED`/`MODEL_UNAVAILABLE`；
- 不得旋转 C1 旧 wrench 代替针级姿态重求解；
- 不得把转动投影为四个旧 x/z 增量后宣称完整 rocking；
- 关闭缺口需要 B 的转动运动学、逐针姿态更新、碰撞/表面查询、事件和切线新合同。

### 9.4 后续释放边界

文献 20 支持“先卸内部张力，再主动抬离”的机构顺序。C1 只保留未来释放状态边界：

1. 解除/反向卸载共同径向锁定中的内部张力；
2. 在损伤和事件历史保留的条件下回调 B；
3. 再执行法向抬离或专用脱附机构；
4. 只有新独立试验才按工程事实重置 DamageStore。

停止时不得自动清除历史或直接抬离。

### 9.5 C2/C3 首次调用条件

首次下游调用必须校验：

- 同一 `C1PreloadState` ID 和提交收据；
- 四个 B/A 接受状态版本；
- 同一 DamageStore 版本；
- 相同几何、参数、表面和变换哈希；
- 径向锁定约束；
- `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`；
- rocking 是否仍关闭；
- 任何低维能力摘要是否仍在 trust region；
- 若事件、姿态、损伤或控制模式变化，完整回调 B。

---

## 10. 状态机和单步可执行流程

### 10.1 C1 全局主状态

搜索过程状态：

```text
INITIALIZED
  -> PROBE_TO_TARGET
  -> EVENT_REDUCTION_REQUIRED | DAMAGE_COORDINATION_REQUIRED | CANDIDATE_CONSISTENT
  -> EVENT_POINT
  -> POST_EVENT_REBALANCE
  -> SAME_POSITION_CASCADE
  -> CANDIDATE_CONSISTENT
  -> STOP_EVALUATION
  -> PREPARE_GLOBAL_COMMIT
  -> COMMITTED_CONTINUE | COMMITTED_STOP
```

异常分支：

```text
any trial state
  -> ROLLBACK_RETRY
  -> STOP_UNCERTIFIED
  -> STOP_NUMERICAL
  -> STOP_IRRECOVERABLE
```

停止阶段必须区分：

- `STOP_CRITERIA_PENDING`；
- `STOP_CANDIDATE`；
- `STOP_PRELOAD_ACCEPTED`；
- `STOP_AT_SEARCH_LIMIT_UNQUALIFIED`；
- `STOP_SAFETY_LIMIT`；
- `STOP_IRRECOVERABLE`；
- `STOP_UNCERTIFIED`；
- `STOP_NUMERICAL`。

### 10.2 每单元子状态

C1 不压缩掉 B 原始主状态。每单元至少保留：

- `balance_status`、branch、rank、nullspace；
- `UNIT_DETACHED_RECOVERABLE`/`UNIT_DETACHED_IRRECOVERABLE`；
- 活动/承载、粘滑、弹簧内部/硬限位；
- 材料/针体强度和损伤事件；
- 剩余路径和再挂接能力；
- 数值、能量、质量和认证等级。

必须原样保留且不得互相改写的上游状态码至少包括：

```text
CONTRACT_VIOLATION / STALE_SNAPSHOT
KINEMATIC_MODE_UNSUPPORTED
OUT_OF_DOMAIN / GEOMETRY_UNCERTAIN / BODY_COLLISION_INVALID
MODEL_UNAVAILABLE / PARAMETER_UNAVAILABLE
DAMAGE_CONFLICT_UNRESOLVED / TRANSACTION_ERROR
NUMERICAL_NONCONVERGENCE
EQUILIBRIUM_INFEASIBLE / PHYSICAL_INSTABILITY
EQUILIBRIUM_DEGENERATE
EVENT_REDUCTION_REQUIRED / EVENT_REBALANCE_REQUIRED
CASCADE_STABILIZED / REENGAGED / AT_TRAVEL_LIMIT
BALANCED_UNIQUE / CONTINUE_SMOOTH
```

其中未认证类映射到 C1 的 `STOP_UNCERTIFIED`，算法不收敛映射到 `STOP_NUMERICAL`；`EQUILIBRIUM_INFEASIBLE` 与 `PHYSICAL_INSTABILITY` 只有在模型、参数和数值均有效时才可进入物理终止判断；`UNIT_DETACHED_RECOVERABLE` 仍可继续搜索；`AT_TRAVEL_LIMIT` 不自动等于失败。原始 `all_status_codes` 始终随响应保留。

### 10.3 单步伪算法

```text
function C1_GLOBAL_STEP(accepted_preload_search_state, request):

  1. VALIDATE_AND_FREEZE
     - 校验工程事实、B_TO_C、B 模型、单位、参考点、哈希和 rocking=off。
     - 冻结 s_n、四个 B/A 接受快照、共享 DamageStore 和策略配置。
     - 若合同/快照/参数/运动不合法，返回 STOP_UNCERTIFIED，不推进历史。

  2. PROPOSE_COMMON_TARGET
     - 生成 s_star = s_n + Delta_s_request，限制在策略声明的候选域。
     - 对四单元生成同一 target_u_x = s_star；P_i 各自保留。

  3. SIDE_EFFECT_FREE_B_TRIALS
     - 从同一接受状态对四单元调用 embedded_array_unit_trial。
     - 收集完整响应、事件候选、gamma_U_i、DamageStore intents 和 rollback token。

  4. FATAL_STATUS_SCREEN
     - 按合同优先级识别合同、运动、域、几何、碰撞、模型、参数和数值状态。
     - 致命或未认证候选全部回滚；不得改写为零承载。

  5. GLOBAL_EARLIEST_EVENT
     - gamma_C = min_i gamma_U_i。
     - 若 gamma_C < 1：回滚当前目标，缩短共同增量；从同一接受状态重调四单元。

  6. WRENCH_TRANSPORT_AND_WORK_CHECK
     - 读取每个 expressed_frame_id 和 O_A。
     - 同时旋转力、运输力矩到 C。
     - 验证 wrench–twist 功不变；失败则合同错误并回滚。

  7. SIMULTANEOUS_EVENT_GROUPING
     - 保留 B 单元内部事件组。
     - 按共同 s 的括区间/容差构造跨单元事件组；排序仅用于哈希。

  8. SHARED_DAMAGE_FIXED_POINT
     - 构造跨单元冲突图并调用 B/A 损伤协调器。
     - 若 trial DamageStore 改变，使用新快照重调受影响单元（默认四单元）。
     - 迭代至 DamageStore、响应、事件和 C 指标一致；否则回滚并 STOP_NUMERICAL/UNCERTIFIED。

  9. EVENT_POINT_AND_CASCADE
     - 处理事件前侧、事件点、事件后侧。
     - 对 ds=0 的同位置级联重新平衡；保留 -P_i du_z_i 功项。
     - 直到稳定 fixed point 或明确终止。

 10. PRELOAD_AND_BALANCE_DIAGNOSTICS
     - 计算 R_x_i、Q_s_contact、Q_s_drive、p_X、p_Y、Delta_X、Delta_Y。
     - 装配完整 contact-only wrench 和 search_support_wrench_required。
     - 保持 P_i、控制和约束反力分栏。

 11. CAPABILITY_AND_STOP_FEATURES
     - 从合法 B 字段构造 A_i、A_G、m_i、m_min 和 safety margins。
     - 使用已接受历史更新平台、边际收益、保持窗口和置信指标。
     - 不使用未来真实状态，不跨未定位事件外推。

 12. DECIDE_PRIMARY_STATUS
     - 先判未认证/数值/不可恢复/安全边界。
     - 再判 s_max 未达标。
     - 最后判 G_stop；否则 CONTINUE_SEARCH。

 13. PREPARE_GLOBAL_BUNDLE
     - 只有当前候选一致、认证、事件/损伤闭合时才 prepare 四单元和共享 DamageStore。
     - 任一 prepare 失败，全部 rollback。

 14. ATOMIC_COMMIT_OR_ROLLBACK
     - 一个全局提交使四单元、内部 A、DamageStore、事件和能量账本同时可见。
     - 失败则全部不前进。

 15. BUILD_OUTPUT
     - 若继续：更新已接受 s、窗口和历史。
     - 若正常停止：构造 C1PreloadState。
     - 若其他终止：返回最后有效接受状态及明确原因。
```

### 10.4 确定性重放

相同输入快照、参数、表面、变换、策略和幂等性键应满足：

- 串行、并行和单元调用顺序置换得到相同接受结果；
- 若物理 graph 非唯一，返回同一明确非唯一集合/句柄，而不是不同的静默代表值；
- 重复调用不累计路径、损伤、耗散、事件或版本；
- 规范事件排序和哈希一致；
- 原子提交收据可验证完整四单元和 DamageStore 版本。

---

## 11. 参数、证据与标定状态

### 11.1 证据分类表

| 项目 | 当前来源 | 当前状态 | 迁移边界 |
|---|---|---|---|
| 四方向、$O_i$、80 mm 几何 | 工程事实 | 已固定 | 不得被文献改写。 |
| 唯一共同 $s$ | 工程事实 | 已固定 | 不允许四单元独立径向位移。 |
| 每单元 $P_i=0.5$–$2$ N 范围 | 工程事实 | 范围已固定 | 具体离散值仍由扫描计划确定。 |
| B 唯一入口、wrench 和事务 | `B_TO_C 1.0.0` | accepted | C 不得重建 B 内部物理。 |
| Wrench/twist 对偶变换 | B 合同 + 多体力学通用知识 | 本轮明确化 | 参考点、表达框架和单位必须版本化。 |
| 对置预紧和能力权衡 | 文献 09 | 趋势/结构证据 | 论文独立刺、对称、各向同性假设不迁移。 |
| 再挂接状态骨架 | 文献 09 | 趋势证据 | 实际响应由 B 历史相关显式求解。 |
| 中心同步径向搜索和串联柔顺 | 文献 20 | 机构证据 | 16 车架机构不能变成四单元独立 $u_x$。 |
| 分支非均匀分载 | 文献 20 | 实验证据 | 不提供四单元停止公式或完整 6D wrench。 |
| 虚功广义力、事件归约、原子事务 | GPT 通用知识 + B 合同 | 本轮推导 | 需实现测试，当前不声称代码通过。 |
| 稳健平台、最弱分支和置信门槛 | GPT 统计/优化知识 | 候选方法族 | 阈值、统计量和覆盖率必须离线验证。 |
| $s_{\max}$ 和停止阈值 | 未决登记项 | unresolved | 禁止用 100 mm 或论文数值代替。 |
| 真实执行器作用线 | 未决 | unavailable | 当前仅有理想广义力。 |
| rocking | B 合同未认证 | unavailable | 需要新合同版本。 |

### 11.2 文献 09 的使用与禁止外推

可迁移：

- 对置分支以内部切向预紧换取其他方向能力的结构；
- 柔顺、初始预载和硬止挡的权衡；
- 挂接位置—剩余行程—增载—失效/再挂接的状态骨架；
- 增大预紧可能增加挂接，同时消耗剩余切向/行程裕度。

不可直接迁移：

- 混凝土、屋面瓦、80 目砂纸的参数数值；
- 独立刺和左右同分布假设；
- 忽略失效后载荷重分配、相关失效和级联；
- 二维对置安全域作为本项目四单元最终能力域；
- 任何论文最优预载、弹簧或行程数值。

### 11.3 文献 20 的使用与禁止外推

可迁移：

- 中心机构同时驱动多个径向分支搜索；
- 挂接分支通过串联柔顺继续增载，其他分支仍可适应表面；
- 多尺度柔顺和非均匀分载；
- 先卸中心张力、再主动抬离的释放顺序。

不可直接迁移：

- 将 16 个车架的局部机械停止变成四个单元不同 $u_x$；
- 岩石拉脱均值作为红砖参数；
- 车架二维力矩式作为四单元闭合平衡；
- 外部钓线/导轨反力作为本项目墙面承载；
- 论文演示值作为 C1 停止阈值或 C2 最大承载。

### 11.4 外部公开知识

本轮只额外使用了公开机器人学中 SE(3) 旋转、twist/wrench 对偶和参考点运输的通用定义，用于交叉检查 B 合同公式。外部资料不引入任何新工程数值。

### 11.5 未决参数和关闭条件

| 未决项 | 当前接口 | 关闭条件 |
|---|---|---|
| `UNRESOLVED.C1.STOP_THRESHOLD` | `stop_policy_id/version` 中显式 unavailable 或候选参数 | B 连续仿真、留出样本和单元/四单元实验通过审查。 |
| `UNRESOLVED.C1.MAX_SEARCH_DISTANCE` | `s_max_mm` 无默认值 | 同上，并证明不直接沿用 100 mm。 |
| 能力特征和聚合器 | `capability_feature_config_id`、`aggregation_config_id` | 灵敏度、可解释性、重放和验证通过。 |
| 窗口、滞回和置信策略 | 独立配置 ID | 非单调、事件和随机样本测试通过。 |
| 全局残量/对置不平衡阈值 | 诊断字段 | 机构约束和未来 C2 平衡边界明确。 |
| 事件/同时事件容差 | `event_config_id` | 收敛和事件顺序不变性测试通过。 |
| 损伤 fixed-point 容差/上限 | `damage_coordination_config_id` | B/A 协调器实现和故障注入通过。 |
| 真实执行器作用线 | `UNRESOLVED_IDEAL_GENERALIZED_FORCE` | CAD、作用—反作用对象和功测试形成新合同。 |
| rocking | 明确拒绝 | B 六维/转动扩展合同和验证完成。 |
| 材料、摩擦、损伤、表面参数 | 参数包 ID 或 unavailable | 文献、测量和实验标定。 |
| 代码/实验完成状态 | 当前仅定义测试 | 实现、数值和实物测试实际通过后更新。 |

---

## 12. 验证矩阵

> 当前状态：以下测试定义已形成，但没有求解器实现和目标实验数据，因此不得声称“测试已通过”。正式实现必须逐项给出输入、容差、期望结果和实际结果。

| 编号 | 测试 | 理论/构造输入 | 必须检查的结果 |
|---:|---|---|---|
| C1-V01 | 四向基与几何 | 四个 $\mathbf R_{Gi}$、$O_i$ | 正交、$\det=+1$；$O_i$ 构成 $80\times80\ \mathrm{mm}$ 中央空区。 |
| C1-V02 | $O_A\rightarrow C$ 运输 | 随机非零力、力矩和 $\boldsymbol\rho_{A/i}$ | 力矩包含 $\mathbf r\times\mathbf F$；不能把 $O_A$ 默认成 $O_i$。 |
| C1-V03 | Wrench–twist 功不变 | 随机 wrench、平移和小转角增量 | 源/目标参考点计算的功在容差内相同。 |
| C1-V04 | 同步约束 | 四个不同表面/历史快照，同一 $s$ | 四个 $u_{x_i}$ 和增量相同；$u_z$、wrench、事件和能力允许不同。 |
| C1-V05 | 对称内部预紧 | 对置单元完全相同、纯轴向 | 全局面内合力为零；$R_{x_i}>0$、$p_X/p_Y>0$、$Q_s^{drive}>0$。 |
| C1-V06 | 异质分支 | 令 $R_{x_1}\ne R_{x_2}$ 或含横向/力矩 | $\Delta_X$、完整 contact-only 残量和支承诊断被暴露，不能被总力掩盖。 |
| C1-V07 | 主动推力唯一所有权 | 每单元不同 $P_i$ | $P_i$ 只进入 B 外层一次；A 请求无 $P_i/N$；contact-only 装配不重复。 |
| C1-V08 | 平衡/graph 语义 | 唯一、退化和规定姿态残量案例 | 唯一/非唯一/未闭合残量分开；不按 ID 选伪唯一分支。 |
| C1-V09 | 最早事件缩步 | 单元 2 先触发 $\gamma<1$ | 全局目标拒绝，四单元共同缩步并从同一接受状态重调；旧 wrench/$u_z$ 不缩放。 |
| C1-V10 | 同时事件与调用顺序 | 两单元事件括区间重叠；置换调用顺序 | 原单元事件组保留；全局事件组/接受状态相同或返回同一非唯一集合。 |
| C1-V11 | 共享损伤冲突 | 跨单元写—写、写—读和核重叠 | 调用 B/A 协调器，共同 trial snapshot，受影响单元重求解，未按顺序覆盖。 |
| C1-V12 | 同位置级联功 | $ds=0$、某些 $du_z\ne0$ | 保留 $-P_i du_z$；数值残量不计入材料耗散。 |
| C1-V13 | 原子提交故障注入 | 任一 prepare/commit/持久化失败 | 四单元和 DamageStore 全部不前进；重试同键不重复累计。 |
| C1-V14 | 平台但弱分支不足 | $G_{plateau}=true$、$m_{min}<m_{req}$ | 不得正常停止，返回继续或相应边界状态。 |
| C1-V15 | 弱分支满足但边际收益高 | $m_{min}$ 通过、$g_A^U>\eta_g$ | 继续搜索。 |
| C1-V16 | 短暂峰值 | 单点高峰后滑脱 | 保持窗口/滞回阻止误停止。 |
| C1-V17 | 滑脱后再挂接 | 能力下降后重新上升 | 重大事件后重置受影响窗口，允许重新建立平台。 |
| C1-V18 | 多个平台 | 早期低平台、后期高平台 | 仅第一个同时通过参考比例、边际收益、最弱和安全门槛的区间可停止。 |
| C1-V19 | 安全边界 | 过预紧、强度、损伤、硬限位、碰撞预测 | 在最后安全状态 `STOP_SAFETY_LIMIT`；已无效候选不提交。 |
| C1-V20 | 上限未达标 | 到 $s_{max}$ 但平台/最弱未通过 | `STOP_AT_SEARCH_LIMIT_UNQUALIFIED`，不标成功；$s_{max}$ 不取 100 mm 默认。 |
| C1-V21 | 可恢复/不可恢复脱附 | 一单元当前无承载但有/无剩余合法路径 | 分别继续搜索或 `STOP_IRRECOVERABLE`，不混淆。 |
| C1-V22 | 失败分类 | 域外、几何不确定、碰撞、参数缺失、数值不收敛、物理无解 | 触发各自状态；数值不收敛不冒充物理失败。 |
| C1-V23 | 停止后继承 | 正常停止后首次 C2 回调 | $s_{stop}$ 不重置；B/A 状态、DamageStore、事件和行程完整继承。 |
| C1-V24 | 法向/径向自由度分离 | 停止后恒 $P_i$ 的新 B trial | 径向锁定不等于 $u_z$ 锁死；法向仍按控制模式平衡/返回残量。 |
| C1-V25 | rocking 防伪 | 请求真实 $\theta_X$ 或 $\theta_Y$ | 明确 `KINEMATIC_MODE_UNSUPPORTED`；旋转旧 wrench 的方案失败。 |
| C1-V26 | 统计留出 | 留出种子、表面和实验批次 | 报告误停止、未达标、安全停止和 $s_{first}$ 区间，不仅报告训练均值。 |
| C1-V27 | 确定性重放 | 相同幂等键，串行/并行和重试 | 返回同一收据/状态或同一非唯一集合，无历史重复累计。 |
| C1-V28 | 单位唯一性 | mm/N/N·mm 与 B 规范输入 | 不二次换算针尖半径、弹簧刚度或参考点；所有输出带单位。 |

### 12.1 解析检查

至少实现以下解析恒等式：

$$
\mathbf R_{Gi}^{\mathsf T}\mathbf R_{Gi}=\mathbf I,
\qquad
\det\mathbf R_{Gi}=1,
$$

$$
Q_s^{\mathrm{drive}}
=\sum_iR_{x_i},
$$

$$
R_{x_1}=R_{x_2},\ R_{x_3}=R_{x_4}
\Rightarrow
\Delta_X=\Delta_Y=0,
$$

以及 wrench–twist 功不变式。

### 12.2 数值收敛检查

实现阶段应分别扫描：

- 共同试探步长和最小事件步长；
- 事件括区间与同时事件容差；
- B 平衡/graph 容差；
- DamageStore fixed-point 容差和迭代上限；
- 停止窗口离散密度；
- 浮点并行归约顺序。

收敛结果必须显示主要状态、事件位置、$s_{stop}$、$A_G$、$m_{min}$ 和 DamageStore 不因数值设置的小幅变化而发生不可解释跳变。

### 12.3 表示一致性检查

同一物理状态在不同允许表达框架中应得到：

- 相同的全局 contact-only wrench；
- 相同的功；
- 相同的 $R_{x_i}$ 和 $Q_s^{drive}$；
- 相同的事件位置和停止主状态；
- 仅坐标分量表示不同。

---

## 13. C1 完成判据核对和已知风险

### 13.1 理论完成判据核对

| 判据 | 本文件落点 | 当前结论 |
|---|---|---|
| 四单元变换、参考点运输和功方向闭合 | 第 2 节 | 已形成可实现公式；未做代码验证。 |
| 唯一共同 $s$ 与单元独立响应闭合 | 第 4、5 节 | 已定义。 |
| 法向主动推力、内部预紧和控制反力分离 | 第 4.2–4.5、5.5 节 | 已定义。 |
| 对称零面内合力与非零预紧关系 | 第 4.4 节 | 已解析证明。 |
| 最早/同时事件、损伤和原子事务 | 第 6、10 节 | 已形成算法；未实现。 |
| 平台、边际收益、最弱和安全联合停止 | 第 7 节 | 已形成参数化策略族；阈值未标定。 |
| 搜索距离和阈值反推 | 第 8 节 | 已形成离线流程。 |
| 停止后锁定和历史继承 | 第 9 节 | 已定义 `C1PreloadState`。 |
| 失败分类和确定性重放 | 第 6、10、12 节 | 已定义。 |
| 不越权完成 C2/C3 | 第 1、14 节 | 已保持边界。 |

### 13.2 已知模型风险

1. 当前 B 不认证真实 rocking，因此 C2 的关键扩展仍可能改变四单元针级响应；
2. 真实执行器作用线和参考体受力未固定，C1 的支承 wrench 只能作为诊断；
3. 停止策略依赖 B 能力摘要的质量和可用裕度，若字段不足必须完整回调或扩展合同；
4. 四方向表面相关数据可能不足，独立拼接会低估共同极端事件；
5. 共享损伤协调器尚未实现，跨单元 fixed point 可能存在非唯一性或收敛困难；
6. 非单调、多平台和再挂接会使平台检测高度依赖事件分辨和保持窗口；
7. 文献 09、20 的数值不能迁移到红砖和本项目十字结构；
8. 当前没有代码和目标实验，所有验证状态均为“测试定义完成”。

### 13.3 不得静默删除的未决问题

- 停止阈值、能力参考和窗口配置；
- $s_{\max}$；
- 最弱分支最低裕度；
- 对置不平衡和 search-support wrench 的允许边界；
- 统计样本数、置信水平和留出方案；
- 共享 DamageStore 协调器实现；
- 真实执行器作用线；
- rocking 和完整 6D 单元运动；
- 材料、表面、摩擦、损伤和数值参数；
- 代码实现、单元实验和四单元实验。

---

## 14. 对 C2/C3 的交接合同

### 14.1 C2 可直接调用的内容

C2 可直接读取：

- `C1PreloadState` 和 $s_{\mathrm{stop}}$；
- 四个静态安装变换与 $O_A\rightarrow C$ 运输；
- 四个 B/A 接受快照和共享 DamageStore；
- 当前 contact-only wrench、$u_z$、balance/graph 和质量；
- 内部预紧、对置不平衡和控制/约束诊断；
- 能力特征、最弱裕度和完整回调条件；
- 事件、能量、版本、哈希和提交收据。

### 14.2 C2 必须原样继承的定义

- `A_on_B` contact-only 方向；
- `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`；
- $P_i$、径向控制和其他约束反力分栏；
- 唯一共同径向锁定 $u_{x_i}=s_{\mathrm{stop}}$；
- B 唯一入口和全局原子事务；
- graph 非唯一、事件和 DamageStore 语义；
- 未认证状态不能改写为零承载或物理失败。

### 14.3 C2 可以修改但必须显式说明的内容

- 外加载荷路径和加载点位移；
- 整爪参考体允许的平移/转动自由度；
- 若合同升级后，$\theta_X,\theta_Y$ 的真实运动学；
- 外层整体平衡残量和求解方法；
- 面向 $+X$、$45^\circ$ 的能力指标。

任何修改都必须新建版本化合同，不能用坐标旋转旧 wrench 代替低层重求解。

### 14.4 C2/C3 禁止重新定义的低层机理

下游不得重新定义：

- 单刺摩擦、材料强度、损伤、针梁、弹簧和硬限位；
- 阵列活动集、逐针载荷共享、事件后重分配和再挂接；
- C1 共同 $s$、原子提交和 DamageStore 协调；
- contact-only wrench 的作用方向、参考点和功语义。

### 14.5 C3 交接

C3 在偏心载荷渐进失效中必须：

- 从 C2 当前全局状态继续，而不是回到四个单元峰值；
- 将针级失效通过完整 B 回调传播到单元和整爪；
- 重复执行跨单元事件、DamageStore 协调和原子提交；
- 区分首个针失效、单元显著退化、整体峰值、物理失稳和数值失败；
- 不用四个单元峰值简单相加定义最大承载。

### 14.6 下一阶段仍需补齐的问题

C2 必须补齐：

- 加载点 $z_C+50\ \mathrm{mm}$ 的外部 wrench；
- $+X$ 和 $45^\circ$ 工况；
- 固定姿态整体平衡；
- rocking 扩展的合同缺口或安全拒绝路径；
- 位移控制反力曲线和稳定平衡存在性。

C3 必须补齐：

- 单元渐进剥离和四分支再平衡；
- 单元低维状态与完整 B 回调切换；
- 整体峰值和峰后终止；
- 与未来偏心拉力实验的输出合同。

---

## 15. C1 已接受内容的历史自检

- [x] 本节核对的是已接受的 C1 子算子完整内容；它在本滚动上下文中作为 C2 的不可丢失初态继续有效。
- [x] 工程事实、B 合同和本轮机理实现已分离。
- [x] 坐标、参考点、单位、wrench、twist 和功方向闭合。
- [x] 四单元只有一个 $s$，但各自法向、历史、事件、损伤和能力独立。
- [x] contact-only、$P_i$、径向控制和约束反力未重复装配。
- [x] 对称零面内合力与非零内部预紧/驱动反力未混淆。
- [x] 最早事件、同时事件、损伤 fixed point、回退和原子提交已形成可执行顺序。
- [x] 停止策略同时检查平台、边际收益、最弱分支、安全、行程和认证。
- [x] 阈值和 $s_{\max}$ 未硬编码，且未沿用 B 的 $100\ \mathrm{mm}$。
- [x] 正常停止、上限未达标、安全、不可恢复、未认证和数值停止相互分离。
- [x] `C1PreloadState` 明确径向锁定与 B/A 内部合法后续演化。
- [x] 未提前完成 C2 偏心平衡/rocking 或 C3 渐进失效。
- [x] 文献 09/20 的适用边界和不可迁移数值已保留。
- [x] 当前仅定义理论与测试，不虚构代码或实验已经通过。


> 注：第 14.6 节是 C1 当时给 C2 的交接清单；其项目已由下列第 16–30 节逐项处理。


---

# 第二篇：C2 偏心外载、整体小角度摇摆与六维平衡

## 16. C2 范围、边界与完成状态

### 16.1 本轮覆盖

C2 已形成以下理论对象：

- `C1PreloadState` 到偏心加载初态的无损继承；
- 十字参考体、加载点和四个 `O_A` 的刚体位姿/小增量 twist 映射；
- 内部锁定坐标 `s_stop`、整爪刚体运动和可选法向执行器相对行程的分解；
- `+X` 与 `45°` 两个正式方向的偏心外部 wrench；
- 四单元 contact-only wrench 到 C 的六维运输、80 mm 几何力臂和完整残量；
- 固定姿态与 `theta_X,theta_Y` rocking 的统一约束结构；
- `P_i`、加载执行器、内部锁定、可选测试架约束和 contact-only wrench 的所有权；
- 位移控制下的平衡/graph、事件、共享损伤、同位置级联、原子提交和确定性重放流程；
- 稳定平衡、退化、物理无解、物理失稳、未认证和数值失败的分离；
- 当前 `B_TO_C 1.0.0` 的精确覆盖审计及最小版本化扩展要求；
- `C2AcceptedState` 和 C3 无损交接。

### 16.2 本轮明确不处理

C2 不完成：

- A/B 内部摩擦、材料、针梁、轴向弹簧、损伤和逐针重分配的重新推导；
- C3 的单元显著退化后递归四分支重平衡、整体峰值定义和峰后终止；
- 框架/导轨有限元、真实传动链刚度、惯性动力学、大角度运动或绕 Z 扭转扫描；
- 未经 B 扩展认证的真实偏心加载历史推进；
- 摇摆角上限、稳定性容差、材料/表面数值、综合评分或成功阈值的硬编码；
- 用文献 17 的随机压力中心、论文峰值，或文献 28 的常数线性爪能力域替代 B 历史相关响应。

### 16.3 当前完成状态

- **理论推导**：已完成并经 `C2-r01` 审查接受；
- **现有 B 合同下的正式 C2 在线物理调用**：未认证；
- **B_TO_C 2.x 扩展实现**：未完成；
- **求解器代码、数值收敛和实验验证**：未完成；
- **工程事实变化**：无。本轮新增内容均属于机理、合同要求或未决实现，不进入工程固定事实。

## 17. C1 初态的无损继承、锁定与新增历史

### 17.1 C2 唯一初态

C2 只能从已原子提交的 `C1PreloadState` 开始。必须继承：

- `preload_state_id`、`commit_receipt_id` 和 `s_stop_mm`；
- 四个 B accepted snapshots、内部 A opaque handles 和控制模式；
- 同一共享 DamageStore 版本与内容哈希；
- 四个静态安装变换、`O_A→C` 运输 ID 和参考点；
- 当前 contact-only wrench、balance/graph、单元状态、剩余行程和能力摘要；
- C1 事件、级联、能量、请求/响应哈希和确定性重放清单。

任何下列操作均为合同违反：把 `s_stop` 归零、重新搜索、丢弃事件、重置 DamageStore、重新初始化弹簧或只保留四个峰值。

### 17.2 三类运动变量不得混淆

C2 将运动分为三类：

1. **内部共同径向锁定量**
   $$
   u_{x_i}^{\mathrm{internal}}=s_{\mathrm{stop}},\qquad d s=0.
   $$
   它是 C1 搜索历史坐标，不因 C2 整体加载而重新推进。

2. **十字参考体刚体运动**
   $$
   \mathbf q_C^6=
   \begin{bmatrix}
   u_X&u_Y&u_Z&\theta_X&\theta_Y&\theta_Z
   \end{bmatrix}^{\mathsf T}.
   $$
   首版正式模式固定 `theta_Z=0`，但保留其虚功残量以检测隐藏绕 Z 支承。

3. **可选的单元法向执行器相对行程** `eta_i`
   $$
   d\mathbf u_{A_i}^{\mathrm{act}}=-\mathbf E_Z\,d\eta_i
   $$
   的具体正号、端点和是否自由必须由版本化机构绑定说明。`eta_i` 不是工程事实新增；它只是区分“执行器相对行程自由”和“单元法向位置被刚体/机构锁定”的候选接口。未绑定时为 `unavailable`。

### 17.3 C2 新增接受历史

只有全局原子提交后，以下量才能推进：

- 累计加载点位移 `delta_P`；
- 十字参考体位姿和 rocking 角；
- 可选 `eta_i`；
- 四个 B/A accepted states 与 DamageStore；
- C2 事件、级联、稳定分支和反力曲线；
- 加载执行器功、主动执行器相对功和能量账本；
- C2 请求/响应哈希、提交收据和重放清单。

Newton、线搜索、事件定位、graph 分支枚举、损伤 fixed point、并行调用和同键重试均不得累计历史。

## 18. 十字参考体、四单元和加载点的刚体运动学

### 18.1 当前位姿与参考向量

以 C1 accepted 构型为 C2 零增量参考。第 i 个 B 规范参考点相对 C 的冻结向量为

$$
\boxed{
\mathbf r_{A_i/C}^{0}
=-40\,\mathbf e_{x_i}
+\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i}
}
$$

其中该向量已经绑定 C1 的 `s_stop` 状态和变换版本；C2 不得再次把 `s_stop` 加到几何位置上。

若十字参考体当前旋转为 `R_C`、平移为 `p_C`，则

$$
\mathbf r_{A_i/C}^{G}=\mathbf R_C\mathbf r_{A_i/C}^{0},
\qquad
\mathbf p_{A_i}^{G}=\mathbf p_C^{G}+\mathbf r_{A_i/C}^{G}.
$$

首版 rocking 使用小角度，但实现仍应保存当前旋转和版本，避免多步线性增量被误当作一次零姿态线性化。

### 18.2 点位移、局部 twist 与 Jacobian

C 点小增量 twist 为

$$
\Delta\boldsymbol\xi_C^G=
\begin{bmatrix}
\Delta\mathbf u_C^G\\
\Delta\boldsymbol\theta^G
\end{bmatrix}.
$$

刚体一阶运动给出

$$
\boxed{
\Delta\mathbf u_{A_i}^{G}
=
\Delta\mathbf u_C^{G}
+
\Delta\boldsymbol\theta^{G}\times\mathbf r_{A_i/C}^{G}
}
$$

若启用相对法向行程，则在送入 B 前另加声明的相对位移；它不能与刚体项合并后丢失所有权。

令当前单元旋转为 `R_Gi(q_C)`，则局部完整 twist 为

$$
\boxed{
\Delta\boldsymbol\xi_{A_i}^{i}
=
\mathbf J_i\Delta\boldsymbol\xi_C^G,
\qquad
\mathbf J_i=
\begin{bmatrix}
\mathbf R_{iG} & -\mathbf R_{iG}[\mathbf r_{A_i/C}^{G}]_\times\\
\mathbf 0 & \mathbf R_{iG}
\end{bmatrix}
}
$$

其中 `[r]_x v=r×v`。因此

$$
\begin{aligned}
\Delta u_{x_i}&=\mathbf e_{x_i}^{\mathsf T}
(\Delta\mathbf u_C+\Delta\boldsymbol\theta\times\mathbf r_i),\\
\Delta u_{y_i}&=\mathbf e_{y_i}^{\mathsf T}
(\Delta\mathbf u_C+\Delta\boldsymbol\theta\times\mathbf r_i),\\
\Delta u_{z_i}^{\mathrm{rigid}}&=\mathbf E_Z^{\mathsf T}
(\Delta\mathbf u_C+\Delta\boldsymbol\theta\times\mathbf r_i),\\
\Delta\boldsymbol\vartheta_i&=\mathbf R_{iG}\Delta\boldsymbol\theta.
\end{aligned}
$$

当前 B 1.0.0 只能接收第一式和第三式中的特定 x/z 平移，不能接收 `Delta u_yi` 或 `Delta vartheta_i`。

### 18.3 Wrench 对偶与功不变

若扩展后的 B 在单元当前框架和 `O_A` 返回

$$
\mathbf W_i^{i,O_A}=
\begin{bmatrix}\mathbf F_i^i\\\mathbf M_i^{i,O_A}\end{bmatrix},
$$

则运输到 C 的 wrench 为

$$
\boxed{
\mathbf W_i^{G,C}=\mathbf J_i^{\mathsf T}\mathbf W_i^{i,O_A}
=
\begin{bmatrix}
\mathbf R_{Gi}\mathbf F_i^i\\
\mathbf R_{Gi}\mathbf M_i^{i,O_A}
+
\mathbf r_{A_i/C}^{G}\times\mathbf R_{Gi}\mathbf F_i^i
\end{bmatrix}
}
$$

并必须满足

$$
\boxed{
(\mathbf W_i^{i,O_A})^{\mathsf T}\Delta\boldsymbol\xi_{A_i}^{i}
=
(\mathbf W_i^{G,C})^{\mathsf T}\Delta\boldsymbol\xi_C^{G}
}
$$

该式同时验证旋转、参考点运输和符号；只旋转旧力或旧 wrench 不能替代新姿态下的 B 重求解。

### 18.4 rocking 引起的四单元法向位置变化

在 `rho_A/i=0`、转轴取 C、忽略平移的解析检查中，

$$
\Delta u_{z_i}^{\mathrm{rock}}
=
\mathbf E_Z^{\mathsf T}
(\Delta\boldsymbol\theta\times[-40\mathbf e_{x_i}]).
$$

正式编号给出

$$
\boxed{
\begin{aligned}
\Delta u_{z_1}^{\mathrm{rock}}&=+40\,\Delta\theta_Y\ \mathrm{mm},\\
\Delta u_{z_2}^{\mathrm{rock}}&=-40\,\Delta\theta_Y\ \mathrm{mm},\\
\Delta u_{z_3}^{\mathrm{rock}}&=-40\,\Delta\theta_X\ \mathrm{mm},\\
\Delta u_{z_4}^{\mathrm{rock}}&=+40\,\Delta\theta_X\ \mathrm{mm}.
\end{aligned}
}
$$

正 `u_z` 远离墙面。因此正 `theta_Y` 使单元 1 远离、单元 2 靠墙；正 `theta_X` 使单元 3 靠墙、单元 4 远离。非零 `rho_A/i` 增加修正项

$$
\Delta u_{z_i}^{\rho}
=
\mathbf E_Z^{\mathsf T}
\left(
\Delta\boldsymbol\theta\times
\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i}
\right).
$$

具体“压紧”或“剥离”必须以 B 在当前历史、姿态和 DamageStore 下的完整响应确认；法向位移符号只给出运动趋势。

## 19. 正式加载方向、加载点运动和偏心外部 wrench

### 19.1 方向和加载点

正式方向为

$$
\hat{\mathbf d}_A=\begin{bmatrix}1&0&0\end{bmatrix}^{\mathsf T},
\qquad
\hat{\mathbf d}_B=\frac{1}{\sqrt2}\begin{bmatrix}1&1&0\end{bmatrix}^{\mathsf T}.
$$

加载点相对 C 为

$$
\mathbf r_P^0=50\mathbf E_Z\ \mathrm{mm}.
$$

在当前姿态，`r_P^G=R_C r_P^0`；小角度增量下

$$
\boxed{
\Delta\mathbf u_P
=
\Delta\mathbf u_C
+
\Delta\boldsymbol\theta\times\mathbf r_P^G
}
$$

位移控制条件为

$$
\boxed{
\hat{\mathbf d}^{\mathsf T}\Delta\mathbf u_P
=\Delta\delta_P.
}
$$

### 19.2 加载执行器的功共轭 wrench

定义 `lambda_P` 为加载执行器对十字参考体施加的有符号广义力；`lambda_P>0` 与正 `delta_P` 同向做正功。单位向量在 P 点形成 C 点 wrench 基向量

$$
\boxed{
\mathbf b_P(\hat{\mathbf d})=
\begin{bmatrix}
\hat{\mathbf d}\\
\mathbf r_P^G\times\hat{\mathbf d}
\end{bmatrix}
}
$$

故

$$
\mathbf W_{\mathrm{load}}^{G,C}=\lambda_P\mathbf b_P,
\qquad
\delta W_{\mathrm{load}}=\lambda_P\,d\delta_P.
$$

输出同时保存：

- `lambda_P`：加载装置作用于爪体的有符号力；
- `F_reaction=lambda_P`：在正向拉动下的所需加载力幅值；
- 爪体对加载装置的作用—反作用为 `-lambda_P d`。

不得把这三种符号混写。

### 19.3 两个工况的力矩检查

`+X` 工况：

$$
\boxed{
\mathbf r_P\times(F\mathbf E_X)=50F\mathbf E_Y\ \mathrm{N\,mm}.
}
$$

`45°` 工况：

$$
\boxed{
\mathbf r_P\times
\left(\frac{F}{\sqrt2}(\mathbf E_X+\mathbf E_Y)\right)
=
\frac{50F}{\sqrt2}
(-\mathbf E_X+\mathbf E_Y)\ \mathrm{N\,mm}.
}
$$

因此 X/Y 力矩分量大小相等、符号相反。若后处理改用“爪对加载器的反力”，全部力和力矩同时反号。

### 19.4 默认路径约束和可选试验架约束

默认策略 `PATH_ONLY_NO_SUPPORT_V1` 只规定 `d^T u_P=delta_P`。加载点与该方向正交的平移、参考体法向平移和允许的 rocking 由平衡求解；不自动产生正交支承力或支承力矩。

若真实试验架还固定某些位移/角度，必须提供：

- `constraint_id/version`；
- 被约束坐标和作用点；
- 对应反力/反力矩及功共轭关系；
- 传感器/机构是否真实存在；
- 该反力是否排除在爪刺承载能力之外。

未声明的约束乘子必须为零；否则候选不可接受。

## 20. 六维 contact-only 装配、80 mm 力臂与所有权

### 20.1 唯一 contact-only 装配

四个单元经当前姿态和参考点运输后

$$
\boxed{
\mathbf W_{\mathrm{contact}}^{G,C}
=
\sum_{i=1}^{4}\mathbf W_i^{G,C}.
}
$$

每个 `W_i` 必须保留：

- B 原始 wrench、表达框架和 `O_A`；
- 自由力偶和中心轴；
- 作用点/压力中心的存在性、唯一性和质量；
- graph 非唯一状态；
- 参考点运输功检查。

只有 B 合同的存在性条件通过时，才可使用单一点力近似。文献 17 的压力中心/四分支 wrench 只支持装配骨架；本项目作用点必须来自 B 的实际活动接触集。

### 20.2 80 mm 中央空区的力矩作用

中央空区不接触墙面；其作用是把分支参考点/作用线分开。令半跨距 `a=40 mm`，忽略 `rho` 和单元自身 moment，仅看 X 对置单元的 wall-normal 分量：

$$
\boxed{
M_Y^{(1,2)}=a(F_{z1}-F_{z2}).
}
$$

Y 对置单元给出

$$
\boxed{
M_X^{(3,4)}=a(F_{z4}-F_{z3}).
}
$$

完整力矩还包括：

1. 每单元 `M_i^{O_A}`；
2. `r_Ai/C × F_i` 的全部分量；
3. `rho_A/i` 修正；
4. 非法向力、横向力和自由力偶。

不得用 `80 mm × 论文峰值` 代替完整响应。

### 20.3 整体残量与无隐藏支承

定义

$$
\boxed{
\mathbf r_W
=
\mathbf W_{\mathrm{contact}}^{G,C}
+
\mathbf W_{\mathrm{load}}^{G,C}
+
\mathbf W_{\mathrm{other,authorized}}^{G,C}.
}
$$

接受平衡必须满足 `r_W=0` 或集合值 graph 包含零。`W_other,authorized` 的每一项必须记录物理对象、系统边界、作用点、方向、功和所有者。

若为了维持候选姿态所需的诊断支承为

$$
\mathbf W_{\mathrm{support,req}}=-\mathbf r_W,
$$

它只用于暴露缺口，不得自动加入平衡或承载能力。固定姿态、禁用 yaw 或数值约束都不授权免费反力矩。

### 20.4 `P_i`、内部锁定和系统边界

`P_i` 有三种不同角色，必须分栏：

1. **B 本构/状态输入**：影响接触、法向残量、损伤和 contact-only wrench；
2. **执行器功通道**：功取决于执行器两个端点的相对位移；
3. **可能的外部/内部 wrench**：取决于 C2 选取的系统边界和真实作用线。

当前 B 合同给出理想单元作用

$$
\mathbf W_{\mathrm{act},i}^{O_A}=
\begin{bmatrix}-P_i\mathbf E_Z\\\mathbf0\end{bmatrix},
$$

但 `action_line_status=UNRESOLVED_IDEAL_GENERALIZED_FORCE`。因此 C2 必须携带

```text
normal_actuator_boundary:
  source_body_id
  target_body_id
  endpoint_transforms
  action_line_certification
  external_to_equilibrium_boundary: true | false
```

- 若执行器力对所选整体边界是内部作用—反作用对，则净 wrench 不加入 `W_other`；
- 若执行器源体在边界外，才可把其对参考体的作用加入 `W_other`；
- 若作用线未认证，可用于理想模型审计，但任何依赖该力矩的结果必须标 `ACTUATOR_WRENCH_UNCERTIFIED`；
- 无论哪种边界，`P_i` 不得作为第二份墙面 contact wrench 增加爪刺能力。

C1 径向锁定反力在四单元—共同驱动系统内部成对出现；它维持 `s_stop`，不作为外部墙面能力。若锁定机构与加载装置之间存在外部支承路径，必须另建授权对象。

### 20.5 主动推力下实际法向接触量

C2 主线采用完整基座位姿试探。若法向执行器相对行程未作为自由平衡变量，则 B 返回的

$$
r_{P_i}=\mathbf E_Z^{\mathsf T}\mathbf F_i-P_i
$$

是传递到安装/控制结构的残量，而不是把 `F_zi` 强制改写为 `P_i`。因此 `P_i` 恒定不意味着实际 contact-only 法向合力恒定。

若未来机构绑定明确允许独立 `eta_i` 在恒推力下自由调整，可增加 `FORCE_BALANCED_NORMAL_STROKE` 分支并求 `r_Pi=0`；该分支必须与刚体位姿、行程、碰撞和功统一求解，不能静默替换主线。

## 21. 固定姿态、rocking 与受约束平衡的统一表达

### 21.1 完整候选坐标和模式约束

使用完整六维小增量坐标

$$
\Delta\mathbf q_C^6=
\begin{bmatrix}
\Delta\mathbf u_C\\
\Delta\boldsymbol\theta
\end{bmatrix}.
$$

模式约束写为

$$
\mathbf C_{\mathfrak m}\Delta\mathbf q_C^6=\mathbf0.
$$

- `rocking=off`：约束 `theta_X=theta_Y=theta_Z=0`；
- `rocking=on`：只约束 `theta_Z=0`，`theta_X,theta_Y` 自由；
- 首版始终禁止大角度和绕 Z 扫描。

加载路径为

$$
\mathbf b_P^{\mathsf T}\Delta\mathbf q_C^6=\Delta\delta_P.
$$

### 21.2 KKT/虚功形式和隐藏反力检测

令 `W_phys` 为 contact-only、明确边界下的主动执行器和其他真实外载之和。受约束平衡可写为

$$
\boxed{
\mathbf W_{\mathrm{phys}}
+
\lambda_P\mathbf b_P
+
\mathbf C_{\mathfrak m}^{\mathsf T}\boldsymbol\mu_{\mathfrak m}
+
\mathbf C_{\mathrm{rig}}^{\mathsf T}\boldsymbol\mu_{\mathrm{rig}}
=\mathbf0.
}
$$

其中：

- `lambda_P` 是授权加载执行器反力；
- `mu_m` 是为固定 rocking/yaw 模式所需的诊断乘子；默认接受条件要求 `mu_m=0`，否则说明模式依赖隐藏姿态支承；
- `mu_rig` 只在真实试验架约束被显式授权时允许非零，并必须从爪刺承载结果中分离。

这等价于直接检查完整六维 `r_W=0`。KKT 形式的价值是把“固定坐标”和“真实支承力”分开：固定角度本身不是承载来源。

### 21.3 固定姿态模式

`rocking=off` 时，C2 在 `theta_X=theta_Y=0` 的子空间搜索平移、加载反力、graph 分支和可选执行器行程，同时要求

$$
M_X=M_Y=M_Z=0
$$

且对应 `mu_m=0`。若接触与加载 wrench 无法自然闭合力矩，则返回 `C2_EQUILIBRIUM_INFEASIBLE_FIXED_POSE`，不能添加导轨或“固定姿态反力矩”。

### 21.4 rocking 模式

`rocking=on` 时，`theta_X,theta_Y` 是待求小量；对应的 X/Y 力矩平衡决定姿态。`theta_Z=0` 仍需满足 `M_Z=0` 或 `mu_Z=0`。若需要非零 yaw 反力矩才能闭合，则当前首版模式不可接受。

rocking 的线性化仅在版本化小角度/trust region 内有效；该角度上限尚未固定。超出范围必须完整重构几何并进入后续合同版本，不能累积小角度到大角度后继续宣称认证。

### 21.5 压紧/剥离配对

对于正 `+X` 外力，加载 wrench 有 `+M_Y`，contact/authorized wrench 需提供 `-M_Y`。忽略其他项时，这倾向于要求 `F_z2>F_z1`；正 `theta_Y` 正好使单元 2 向墙、单元 1 离墙。该关系只是符号一致性检查，实际分支由 B 历史响应决定。

`45°` 外载同时产生 `-M_X` 和 `+M_Y`，会同时耦合两组对置单元。不得预先断言哪一侧必然首先剥离。

## 22. 当前 `B_TO_C 1.0.0` 覆盖审计与最小扩展

### 22.1 四单元允许平移子空间的交集

当前第 i 单元允许的平移子空间为

$$
\mathcal V_i=\operatorname{span}\{\mathbf e_{x_i},\mathbf E_Z\}.
$$

四个方向的交集为

$$
\boxed{
\bigcap_{i=1}^{4}\mathcal V_i=\operatorname{span}\{\mathbf E_Z\}.
}
$$

因此除纯全局 Z 平移外，不存在一个非零整爪平移能同时落在四个单元的 x/z 认证子空间内。

### 22.2 `+X` 路径的局部分量

取 `Delta u_C=Delta u E_X`、无转动：

| 单元 | `Delta u_xi` | `Delta u_yi` | 当前合同 |
|---|---:|---:|---|
| 1 (`+X`) | `+Delta u` | 0 | x 可表达 |
| 2 (`-X`) | `-Delta u` | 0 | x 可表达 |
| 3 (`+Y`) | 0 | `-Delta u` | y 未认证 |
| 4 (`-Y`) | 0 | `+Delta u` | y 未认证 |

因此正式 `+X` 路径不能由 B 1.0.0 完整推进。

### 22.3 `45°` 路径的局部分量

对 `d=(E_X+E_Y)/sqrt2`，四个单元均出现非零局部 y 分量；所有单元都需要扩展运动。任何 rocking 还增加单元姿态转动和动态表面/碰撞查询。因此旋转旧 wrench、只投影 x/z 或冻结针姿态均为合同违反。

### 22.4 当前可做与不可做

当前 B 1.0.0 可用于：

- 校验 C1 accepted 静态状态；
- 零增量重放；
- 纯全局 Z 平移且无转动的受限构造测试；
- 比较坐标运输、功和数据结构；
- 返回明确未认证状态。

当前不能用于：

- 正式 `+X` 或 `45°` 偏心加载；
- 任意局部 y 平移；
- `theta_X/theta_Y` 导致的姿态、针轴、碰撞和表面更新；
- 由旧 x/z 响应推断完整六维切线或稳定性。

### 22.5 最小版本化扩展要求

建议独立审批 `B_TO_C 2.0.0`，保持 1.x 请求向后兼容。最小新增内容如下。

```text
required_contract:
  contract_id: B_TO_C
  required_major_version: 2
  compatibility:
    - every valid 1.0.0 x/z request retains identical semantics
    - new fields are mandatory only for SE3 modes

new_control_modes:
  PRESCRIBED_SE3_RESIDUAL
  SE3_WITH_FORCE_BALANCED_NORMAL_STROKE   # optional, hardware-bound

trial_kinematics:
  accepted_T_G_from_A
  target_T_G_from_A | full_base_twist_increment[6]
  internal_search_coordinate_s_stop_separate
  local_x_y_z_and_rotation_components
  optional_normal_actuator_relative_stroke
  interpolation_on_SE3_and_event_fraction_basis

geometry_and_surface:
  dynamic_unit_frame
  updated_needle_axes_and_tip_poses
  full collision and domain queries
  rocking small-angle/full-pose certification domain

response:
  contact_only_wrench_at_O_A[6]
  full motion residuals and control/constraint reactions
  raw/condensed/one-sided 6D tangent or admissible graph
  trust region and branch
  event candidates for translation/rotation/collision/domain
  capability, stability and callback requirements
  wrench-twist power checks

damage_and_transaction:
  unchanged opaque A/B histories
  shared DamageStore intents and fixed point
  event/cascade semantics
  prepare/atomic commit/rollback and idempotency
```

扩展必须验证：

- 1.0 x/z 请求逐位兼容；
- 任意小 twist 的功对偶；
- 完整切线与有限差分/一侧割线一致；
- 动态姿态下几何、碰撞、事件和 DamageStore 确定性；
- 串行/并行、缩步和回滚不改变接受历史；
- 未支持运动返回最后有效状态，不返回零承载。

### 22.6 安全拒绝路径

在扩展未接受前，任何正式 C2 非零加载请求必须：

1. 校验 C1 初态；
2. 计算四单元所需完整 twist；
3. 发现局部 y/转动后返回 `C2_CONTRACT_EXTENSION_REQUIRED`；
4. 保留 `last_valid_accepted_state=C1PreloadState`；
5. 不调用降阶物理替代，不推进 `delta_P`、DamageStore、能量或事件；
6. 可输出理论目标 twist 和缺失字段，供扩展实现测试。

## 23. C2 数据模型

### 23.1 `C2LoadRequest`

```text
C2LoadRequest:
  identity:
    gripper_instance_id
    c2_step_id / trial_id / newton_iteration_id
    event_sequence_id / caller_sequence_id
    request_idempotency_key
  baselines:
    C1PreloadState_id | current_C2AcceptedState_id
    commit_receipt_id
    B_TO_C_contract_id / version
    engineering_context_version
    C_module_context_version
  loading:
    direction_id: GLOBAL_POS_X | GLOBAL_POS_XY_45
    direction_vector_G
    delta_P_n_mm
    target_delta_P_mm | requested_increment_mm
    load_point_reference_id / r_P_mm
    interpolation_rule / event_side_request
  mode:
    rocking: off | on
    theta_Z: fixed_zero
    authorized_test_rig_constraints[]
    normal_actuator_kinematics_mode
    equilibrium_boundary_id
  state_and_units[4]:
    accepted_B_snapshot_handle
    accepted_A_bundle_handle
    P_i_N
    accepted_transform_T_G_from_A
    C1_internal_s_stop_mm
    surface / parameter / configuration / state hashes
  damage:
    shared_DamageStore_handle / version / hash
  policies:
    numerical / event / damage / stability config IDs
    small_angle_or_pose_trust_region_id
    residual_scaling_id
    deterministic_replay_request
  requested_response:
    full_B_trial_phase
    tangent / graph / capability / stability modes
    event_location_required
    full_unit_resolve_requested
```

缺失 B 扩展、作用线、模式或关键参数时，不得填默认值。

### 23.2 `C2LoadTrialResponse`

```text
C2LoadTrialResponse:
  identity_and_trace:
    request_hash / response_hash
    versions_read / deterministic_replay_manifest
  inherited_state_check:
    C1PreloadState_id / s_stop / accepted snapshots / DamageStore
  kinematics:
    q_C_trial[6]
    delta_P_trial
    u_P_trial
    theta_X / theta_Y / theta_Z
    per_unit_full_base_twist[4]
    per_unit_local_x_y_z_and_rotation[4]
    optional_eta_i[4]
  raw_unit_responses:
    EmbeddedUnitTrialResponse_or_SE3_extension_response[4]
  wrenches:
    contact_only_W_i_at_C[4]
    summed_contact_only_W_at_C
    loading_wrench_at_C
    authorized_other_wrenches[]
    full_residual_W
    required_unauthorized_support_diagnostic
    power_invariance_checks[4]
  reaction_and_distribution:
    lambda_P / F_reaction
    per_unit forces, moments, lines, point/CoP availability
    normal/tangential components and pair moment contributions
  balance_and_stability:
    algebraic_residual / graph_distance
    rank / nullspace / branch / condition
    mode_constraint_multipliers
    test_rig_multipliers
    one_sided_incremental_stability
    stability_certification
  events_and_damage:
    unit event groups / global earliest fraction
    cross-unit simultaneous group
    damage conflict graph / fixed-point status
    same-position cascades
  diagnostics:
    all_status_codes / primary_status
    contract coverage and missing extension fields
    domain / geometry / collision / model / parameter status
    energy / work / numerical error ledgers
    last_valid_accepted_state
  transaction:
    rollback tokens[4]
    provisional intents[4]
    shared damage provisional intent
    prepare eligibility / global bundle draft
```

### 23.3 `C2AcceptedState`

```text
C2AcceptedState:
  identity:
    c2_state_id / commit_receipt_id
    parent_C1PreloadState_id
    loading_direction_id
  accepted_path:
    delta_P_mm
    q_C[6]
    load_point_position
    rocking_mode / authorized_constraints
    lambda_P / F_reaction
  inherited_and_evolved_state:
    s_stop_mm_frozen
    accepted_B_snapshots[4]
    accepted_A_opaque_handles[4]
    shared_DamageStore_version / hash
    accepted transforms and current unit poses
  mechanics:
    contact_only_W_i_at_C[4]
    summed contact-only wrench
    authorized active/control fields separately
    per_unit balance/graph / loads / lines / CoP availability
    pair moment and weakest-branch diagnostics
  stability_and_quality:
    current branch / rank / nullspace
    one-sided stability evidence
    trust region / callback requirements
    remaining travel / collision / domain / model quality
  history:
    events / cascades / damage / reengagement
    loading and actuator work ledgers
    request-response hashes / replay manifest
  C3_handoff:
    first needle/unit event summaries
    current weakest branch
    full B callback conditions
    peak_not_yet_declared
```

### 23.4 `C2ContractExtensionRequirement`

该对象记录第 22.5 节的缺失能力、建议合同版本、兼容规则、验证要求和安全拒绝状态。它是推导产物，不代表正式合同已修改。

## 24. 整体平衡、graph、线性化和稳定性

### 24.1 非线性/集合值平衡问题

令未知量集合包括允许的 `q_C`、加载反力 `lambda_P`、可选 `eta_i` 和 B admissible graph 选择。C2 求

$$
\boxed{
\mathbf0\in
\mathcal R_{C2}
(\mathbf q_C,\lambda_P,\boldsymbol\eta;
\delta_P,\mathcal S_n,\mathcal D_n)
}
$$

其中包含：

- 六维 wrench 平衡；
- 加载点位移约束；
- 模式约束；
- 可选法向执行器平衡/行程 graph；
- 每单元 B admissible response/graph；
- 共享 DamageStore 一致性。

退化 graph 不能按单元 ID、调用顺序或最小范数静默选值。若存在多个物理分支，返回集合、分支句柄和连续性条件。

### 24.2 根求解与过定约束

无隐藏支承要求可能使固定姿态问题成为过定根问题。允许使用：

- semismooth Newton/KKT；
- 带约束的 trust-region root solve；
- 集合值 graph 枚举/互补求解；
- 加权最小二乘作为寻找根的数值手段。

但接受标准始终是每个有物理单位的残量分别通过版本化容差；不得因为最小二乘目标较小就把非零未授权 wrench 改写为平衡。残量缩放只用于条件数，不能改变物理门槛。

### 24.3 局部切线的整体装配

在唯一、事件外、姿态和 DamageStore 固定的分支上，扩展 B 返回每单元 `K_i=dW_i/dxi_i`。运输与几何项装配后，C 点切线为

$$
\mathbf K_C
=
\sum_i
\left(
\mathbf J_i^{\mathsf T}\mathbf K_i\mathbf J_i
+
\mathbf K_{\mathrm{geom},i}
\right)
+
\mathbf K_{\mathrm{authorized}}.
$$

`K_geom` 来自随姿态变化的参考向量和力；未经验证不得省略。跨事件、graph 非唯一、DamageStore 改变、碰撞/域边界或 B 标记 full resolve 时，旧切线失效。

### 24.4 一侧增量稳定性

代数根不等于稳定平衡。令 `N` 张成固定 `delta_P`、模式约束和真实约束下的自由扰动子空间；在唯一平滑分支上，先定义净物理 wrench 残量对自由位姿的切线

$$
\mathbf K_{\mathrm{res,red}}
=\mathbf N^{\mathsf T}\frac{\partial\mathbf r_W}{\partial\mathbf q_C}\mathbf N,
$$

再定义恢复刚度

$$
\mathbf K_{\mathrm{rest}}=-\mathbf K_{\mathrm{res,red}}.
$$

负号来自本文件的作用方向：稳定接触对正扰动产生反向净 wrench。一个保守的充分条件是所有非零 admissible 一侧扰动满足

$$
\boxed{
\delta\mathbf z^{\mathsf T}
\frac{\mathbf K_{\mathrm{rest}}+\mathbf K_{\mathrm{rest}}^{\mathsf T}}{2}
\delta\mathbf z>0.
}
$$

该式使用功共轭坐标；数值特征值需采用版本化长度尺度进行条件化，但正定性按合同一致的坐标变换作合同矩阵变换，不依赖任意单位拼接。

对摩擦、损伤和 graph 分支：

- 使用一侧切线/增量功或 graph 的局部强单调/强正则性；
- 若仅有非唯一根而无稳定性下界，返回 `C2_STABILITY_UNCERTIFIED`；
- 只有在模型、参数、事件定位和数值均认证，且所有可继续 admissible 分支均失去恢复方向时，才返回 `C2_PHYSICAL_INSTABILITY`；
- Newton 失败、负单个切线分量或秩下降本身不能证明物理失稳。

### 24.5 反力曲线

每次 accepted 步输出

$$
F_{\mathrm{reaction}}(\delta_P)=\lambda_P.
$$

C2 定义曲线生成和稳定分支标签，但不在本轮把峰值自动声明为最终最大承载。C3 才结合渐进失效、不可恢复分支和峰后终止定义 `F_crit`。

## 25. 准静态位移加载、事件、损伤和原子事务

### 25.1 单步算法

```text
function C2_GLOBAL_LOAD_STEP(accepted_state, request):

  1. VALIDATE_AND_FREEZE
     - 校验 C1/C2 state、s_stop、四个 B/A snapshots、DamageStore、变换、方向、模式和幂等键。
     - 冻结当前 accepted state；缺字段不得默认补齐。

  2. BUILD_RIGID_BODY_TRIAL
     - 提议 delta_P target、q_C、theta_X/theta_Y 和可选 eta_i。
     - 计算 P 与四个 O_A 的完整 twist、局部 x/y/z/rotation 分量。

  3. CONTRACT_COVERAGE_AUDIT
     - 对每单元检查当前 B 版本是否认证该完整运动。
     - B 1.0.0 遇局部 y/转动立即安全拒绝，不推进历史。

  4. SIDE_EFFECT_FREE_UNIT_TRIALS
     - 在扩展可用时，从同一 accepted state 和 DamageStore 调四个完整 B trial。
     - 收集 contact-only wrench、graph/残量、切线、事件、能力、损伤 intents 和 rollback tokens。

  5. WRENCH_TRANSPORT_AND_POWER_CHECK
     - 使用当前动态 frame 和 O_A→C 变换运输力与力矩。
     - 检查每单元 wrench–twist 功不变。

  6. ASSEMBLE_AUTHORIZED_WRENCHES
     - 装配 contact-only、加载点 wrench，以及边界明确的主动/真实约束 wrench。
     - 计算未授权支承诊断，不将其加入能力。

  7. COUPLED_BALANCE_SOLVE
     - 求 q_C、lambda_P、可选 eta/graph 使加载路径和六维平衡闭合。
     - 检查模式乘子、秩、条件、残量和作用线认证。

  8. GLOBAL_EARLIEST_EVENT
     - 归约四单元事件、姿态 trust region、域/碰撞和整体 graph 事件的最小 fraction。
     - 若 fraction<1，回滚全部，缩短 delta_P 增量，从同一 accepted state 重调全部受影响单元。

  9. SIMULTANEOUS_EVENT_GROUPING
     - 保留 B 单元内部事件组；按共同 delta_P/路径括区间构造跨单元组。
     - 排序只用于哈希，不决定物理先后。

 10. SHARED_DAMAGE_FIXED_POINT
     - 收集 opaque intents/read-write sets，调用 B/A 协调器。
     - DamageStore 改变后从同一 accepted state 重调受影响单元；当前刚体问题默认四单元全部重调。

 11. SAME_POSITION_CASCADE
     - 允许 d(delta_P)=0 而 q_C、eta_i、接触和 DamageStore 变化。
     - 重新平衡，直到稳定 fixed point、明确终止、未认证或数值失败。

 12. STABILITY_AND_QUALITY
     - 对当前一侧分支检查稳定性、域、碰撞、强度、行程、模型和参数质量。
     - 不以 Newton 失败替代物理结论。

 13. PREPARE_GLOBAL_BUNDLE
     - 只有整体残量、事件、损伤、功、稳定性和认证通过才 prepare 四单元与共享 DamageStore。

 14. ATOMIC_COMMIT_OR_ROLLBACK
     - 一次提交使 delta_P、q_C、四个 B/A states、DamageStore、事件和能量同时可见。
     - 任一失败全部回滚；同键重试不得重复累计。

 15. BUILD_RESPONSE
     - 输出反力、姿态、四单元载荷、graph、事件、质量和下一步完整回调条件。
```

### 25.2 事件分数

每单元对同一 C2 路径返回 `gamma_Ui`。C2 还可产生整体事件分数 `gamma_G`，包括模式 trust region、碰撞/域边界、加载路径约束秩变化和稳定分支终点。全局最早事件为

$$
\boxed{
\gamma_C=
\min(\gamma_{U_1},\ldots,\gamma_{U_4},\gamma_G).
}
$$

缩步后不得比例缩放旧姿态、旧 wrench、旧 graph 或旧损伤意图。

### 25.3 功和能量账本

加载执行器功为

$$
\Delta W_P^{\mathrm{load}}=\int\lambda_P\,d\delta_P.
$$

主动法向执行器的系统功取决于两个端点的相对位移。若 `eta_i` 是已认证相对行程且正号定义为减小间隙，则

$$
\Delta W_{P_i}=\int P_i\,d\eta_i
$$

的符号由接口定义；若只知道单端理想力而不知道源端运动，整体执行器功必须标 `unavailable`，不能用 `-P_i du_Ai` 冒充内部执行器功。

B/A 储能、摩擦/材料耗散、释放能和数值误差沿用上游分栏。数值残量和约束乘子功不得写成材料耗散。

### 25.4 原子提交

C2 全局提交包必须包含：

```text
C2_global_bundle_manifest:
  parent accepted state and delta_P target
  q_C / mode / authorized constraint manifest
  four B provisional intents and all internal A states
  one shared DamageStore provisional intent
  contact/load/authorized wrench and residual ledger
  event/cascade/stability ledger
  work and energy ledger
  versions / transforms / hashes / replay manifest
```

任一单元、整体平衡、稳定性、DamageStore、持久化或收据失败，全部历史不前进。

## 26. C2 主状态、失败分类和优先级

### 26.1 互斥主状态

| 主状态 | 含义 | 提交政策 |
|---|---|---|
| `C2_BALANCED_ACCEPTED` | 唯一或已声明分支的稳定平衡通过并原子提交 | 提交并继续加载 |
| `C2_BALANCED_DEGENERATE` | 平衡存在但 graph/分支非唯一；保守集合与选择条件完整 | 仅在策略允许且不静默选支时提交 |
| `C2_EVENT_REDUCTION_REQUIRED` | 当前目标跨越更早事件 | 不提交，缩步重调 |
| `C2_EVENT_REBALANCE_REQUIRED` | 位于事件点，需损伤/级联后重平衡 | 不提交中间态 |
| `C2_CONTRACT_EXTENSION_REQUIRED` | 当前 B 版本不认证局部 y/姿态/full twist | 不提交，保留最后有效状态 |
| `C2_STOP_UNCERTIFIED` | 模型、参数、作用线、稳定性、几何或域不足 | 不提交未认证候选 |
| `C2_EQUILIBRIUM_INFEASIBLE` | 模型/参数/数值有效，但无 admissible 六维平衡 | 可提交已定位的最后有效前态，不把它称数值失败 |
| `C2_PHYSICAL_INSTABILITY` | 代数根可存在，但所有 admissible 一侧稳定分支消失 | 仅在证据闭合时作为物理终止 |
| `C2_STOP_NUMERICAL` | 平衡、graph、事件或 damage fixed point 未收敛 | 不等于物理无解 |
| `C2_TRANSACTION_ERROR` | prepare/commit/持久化失败 | 全部回滚 |

### 26.2 摘要优先级

```text
CONTRACT_VIOLATION / STALE_SNAPSHOT
-> C2_CONTRACT_EXTENSION_REQUIRED / KINEMATIC_MODE_UNSUPPORTED
-> OUT_OF_DOMAIN / GEOMETRY_UNCERTAIN / BODY_COLLISION_INVALID
-> MODEL_UNAVAILABLE / PARAMETER_UNAVAILABLE / ACTUATOR_WRENCH_UNCERTIFIED
-> DAMAGE_CONFLICT_UNRESOLVED / TRANSACTION_ERROR
-> NUMERICAL_NONCONVERGENCE
-> PHYSICAL_INSTABILITY
-> EQUILIBRIUM_INFEASIBLE
-> STABILITY_UNCERTIFIED / EQUILIBRIUM_DEGENERATE
-> EVENT_REDUCTION_REQUIRED / EVENT_REBALANCE_REQUIRED
-> C2_BALANCED_ACCEPTED
```

`all_status_codes` 始终完整保留。

### 26.3 特殊失败语义

- 非零 `mu_m`：当前姿态/禁用 yaw 依赖隐藏支承；不是爪刺平衡；
- `required_support_wrench≠0`：只是一项诊断；
- `NUMERICAL_NONCONVERGENCE`：不能推断物理无解；
- `STABILITY_UNCERTIFIED`：不能推断物理失稳；
- `EQUILIBRIUM_INFEASIBLE`：必须在合同、模型、参数和数值均有效后才可用；
- `C2_CONTRACT_EXTENSION_REQUIRED`：当前正式 `+X/45°` 的预期主状态，直到 B 2.x 被接受。

## 27. 两个方向的对称性、证据与未决参数

### 27.1 理想四重对称

若四个单元、表面、`P_i`、C1 预紧、损伤和剩余行程完全相同且表面统计各向同性，则系统在 90° 旋转下等价；`+X` 与 `+Y` 结果应旋转对应。`45°` 同时调用两组对置分支，不能仅由对称性断言一定强于或弱于轴向加载。

### 27.2 实际非对称

以下因素会破坏四重对称：

- 方向性粗糙表面；
- `2×5` 与 `5×2` 等阵列方向；
- 不同 C1 事件、损伤、作用点和剩余行程；
- graph 非唯一和不同局部切线；
- `rho_A/i`、制造误差和 `P_i` 差异。

比较 `+X` 和 `45°` 必须使用同一 C1 生成策略、配对表面/随机种子和相同参数包，并保留四单元原始 wrench、姿态、事件和裕度。

### 27.3 文献 17 的迁移边界

可迁移：

- 多刺合力作用点/中心轴和分支 wrench 的装配结构；
- 对置分支和四分支 wrench 分量耦合；
- 不能逐分量独立取最大值。

不可迁移：

- 随机压力中心代替 B 活动接触集；
- `4.5 mm`、`mu=0.2`、每刺 `10 N`、每指 `10` 刺和岩面实测承载；
- 固定掌位姿、忽略弹簧/失效后的线性边界；
- 原文符号映射不一致的公式直接进入项目。

### 27.4 文献 28 的迁移边界

可迁移：

- 完整力/力矩平衡与单爪 admissible 能力约束；
- 最大化最小附着裕度的上层结构；
- 零净 wrench 与非零内部力可以共存；
- 姿态适应和转轴位置影响的低阶静力思想。

不可迁移：

- 常数 `f_min/f_max/theta_max/phi_max` 替代 B 历史响应；
- 被动腕参数、DIG 裕度和整机失败率作为本项目数值；
- 当前固定接触集 LP 提前替代 C3 渐进失效；
- 论文存在 rocking 机构即视为 B 已认证姿态运动。

### 27.5 GPT 通用知识的使用边界

本轮使用：

- 刚体点速度/小位移与 wrench 对偶变换；
- 虚功和受约束平衡乘子；
- KKT/graph 与无隐藏反力检测；
- 事件驱动缩步、fixed point 和原子事务；
- 一侧增量功的局部稳定性充分条件。

这些是通用方法，不固定项目阈值、作用线、角度上限或材料参数。

### 27.6 仍未关闭的参数和接口

| 未决项 | 当前处理 | 关闭条件 |
|---|---|---|
| B 全 twist/姿态合同 | `C2_CONTRACT_EXTENSION_REQUIRED` | B_TO_C 2.x 实现、集成和验证 |
| 法向执行器端点/作用线/系统边界 | 显式 unavailable 或 model-only | CAD/机构绑定和功测试 |
| `eta_i` 是否自由 | 版本化模式分支 | 机构自由度和控制策略确认 |
| rocking 小角度/trust region | 无默认值 | 几何误差、B 验证和实验标定 |
| 稳定性容差和长度尺度 | 配置 ID | 数值收敛和基准验证 |
| 整体残量、事件和 simultaneous 容差 | 配置 ID | 实现收敛测试 |
| 材料/表面/损伤参数 | 上游 unavailable | 文献、测量和实验标定 |
| 真实试验架约束 | 默认无支承 | 装置建模和传感器说明 |
| 代码/实验状态 | 未完成 | 实现与目标实验实际通过 |

## 28. C2 验证矩阵

> 当前仅定义测试，不声称代码或实验已经通过。

| 编号 | 测试 | 构造输入 | 必须结果 |
|---:|---|---|---|
| C2-V01 | 刚体点运动 | 随机 `u_C,theta` 与四个 `r_i` | `u_Ai=u_C+theta×r_i`；局部投影正确 |
| C2-V02 | Wrench–twist 功 | 随机 wrench/twist | `W_i^T xi_i=(J_i^T W_i)^T xi_C` |
| C2-V03 | rocking 四式 | `rho=0` | `(+40thetaY,-40thetaY,-40thetaX,+40thetaX)` |
| C2-V04 | `rho` 修正 | 非零版本化偏置 | 法向和力矩运输含偏置，不默认同点 |
| C2-V05 | `+X` 偏心 wrench | `F E_X` | `M_Y=+50F N·mm` |
| C2-V06 | `45°` 偏心 wrench | `F(E_X+E_Y)/sqrt2` | `M_X=-50F/sqrt2`、`M_Y=+50F/sqrt2` |
| C2-V07 | 作用—反作用 | 同一载荷换报告方向 | 力与力矩同时反号 |
| C2-V08 | 80 mm 力臂 | 成对法向力差 | `M_Y=40(Fz1-Fz2)`、`M_X=40(Fz4-Fz3)` |
| C2-V09 | 自由力偶 | 单元含非零 `M_parallel` | 不伪造单一作用点，完整 wrench 保留 |
| C2-V10 | 无隐藏支承 | 固定姿态且 contact 无法闭合外矩 | 非零 `mu_m`/无平衡，不能添加导轨反力 |
| C2-V11 | `P_i` 唯一所有权 | 四个不同 P | 只作为 B/功/授权边界字段；不重复墙面 wrench |
| C2-V12 | C1 无损继承 | 首次 C2 请求 | `s_stop`、B/A、DamageStore、事件和行程均不重置 |
| C2-V13 | B 1.0 `+X` 审计 | 纯 `+X` 平移 | 单元 3/4 局部 y，返回扩展要求 |
| C2-V14 | B 1.0 `45°` 审计 | 45° 平移 | 四单元含局部 y，拒绝降阶 |
| C2-V15 | rocking 防伪 | 非零 theta | 旧 wrench 旋转/仅 x-z 投影方案被拒绝 |
| C2-V16 | B 2.x 向后兼容 | 旧 x/z 基准 | 结果与 B 1.0 一致 |
| C2-V17 | 完整 twist 切线 | 事件外小扰动 | 6D 切线/一侧割线与有限差分一致 |
| C2-V18 | 固定/rocking 对比 | 对称初态 | off 角为零；on 由力矩平衡得到成对法向变化 |
| C2-V19 | yaw 排除 | 构造非零 Mz | `mu_Z≠0` 或无平衡，不能隐藏支承 |
| C2-V20 | 最早事件 | 某单元先触发 | 全局缩步、四单元从同一 accepted state 重调 |
| C2-V21 | 同时事件 | 两单元括区间重叠 | 保留原组并形成跨单元组，顺序置换不改结果 |
| C2-V22 | 共享损伤 | 跨单元冲突 | B/A 协调 fixed point；不按调用顺序覆盖 |
| C2-V23 | 同位置级联 | `d delta_P=0`、姿态/eta 变化 | 重新平衡并正确记功 |
| C2-V24 | 原子提交故障 | 任一 prepare/commit 失败 | delta_P、q_C、四单元和 DamageStore 全部不推进 |
| C2-V25 | 代数退化 | graph 多解 | 返回集合/分支，不按 ID 选解 |
| C2-V26 | 稳定性分类 | 稳定根、未认证、失稳分支 | 三种状态分离；Newton 失败不等于失稳 |
| C2-V27 | 失败分类 | 运动/模型/域/碰撞/物理/数值/事务注入 | 触发各自主状态并保留全部码 |
| C2-V28 | 90° 对称 | 理想 D4 输入旋转 | wrench、姿态、事件按旋转映射一致 |
| C2-V29 | 方向性破缺 | 2×5/5×2 或异质历史 | 允许非对称，但来源可追溯 |
| C2-V30 | `+X/45°` 配对比较 | 同一 C1 状态与随机样本 | 输出完整原始量，不用四峰值或总力代替 |

### 28.1 解析恒等式

至少自动检查：

$$
\mathbf J_i^{\mathsf T}\mathbf W_i
\text{ 的力矩项}
=
\mathbf R_{Gi}\mathbf M_i+\mathbf r_i\times\mathbf R_{Gi}\mathbf F_i,
$$

$$
\mathbf b_P^{\mathsf T}\Delta\mathbf q_C
=
\hat{\mathbf d}^{\mathsf T}\Delta\mathbf u_P,
$$

以及第 18.4、19.3、20.2 节全部符号式。

### 28.2 数值收敛

实现阶段扫描：

- 加载步长、事件最小步长和括区间；
- 六维残量缩放和容差；
- graph/互补容差；
- 共享损伤 fixed-point 容差；
- 姿态增量/trust region；
- 稳定性一侧扰动和长度尺度；
- 并行浮点归约顺序。

主要状态、事件位置、`F_reaction`、姿态、DamageStore 和分支不得因小幅数值设置变化发生不可解释跳变。

## 29. 对 C3 的交接

### 29.1 C3 唯一初态

C3 必须从当前 `C2AcceptedState` 继续，而不是回到 C1 或四个单元峰值。必须继承：

- `delta_P`、当前 `q_C`、rocking 模式和反力；
- 冻结 `s_stop`；
- 四个 B/A accepted states 和共享 DamageStore；
- 当前 contact-only wrenches、作用线/graph 和弱分支；
- 单元/针事件、剩余行程、损伤和稳定分支；
- 功、能量、版本、哈希和提交收据；
- B full callback 条件和合同认证状态。

### 29.2 C3 必须完成

- 针级事件导致单元能力显著退化后的完整 B 回调；
- 四单元递归再平衡和渐进剥离；
- 首个针失效、首个单元显著退化、整体峰值、物理失稳和不可恢复脱附的区分；
- `+X` 与 `45°` 稳定分支反力曲线和最终 `F_crit`；
- 峰后终止和实验输出合同。

### 29.3 C3 禁止事项

C3 不得：

- 把 C2 当前切线当全局无记忆极限面；
- 用四个单元峰值简单相加；
- 丢失姿态、DamageStore、事件或作用点；
- 在 B 运动扩展未认证时继续推进；
- 把数值不收敛冒充整体失稳。

## 30. C2 完成判据与输出前自检

### 30.1 完成判据核对

| 判据 | 当前结论 |
|---|---|
| C1 完整继承 | 已在第 1–17 节保留，未重置历史 |
| C/P/O_A 刚体运动学与功对偶 | 已形成显式 Jacobian 和对偶运输 |
| `+X/45°` 偏心 wrench | 力、矩和作用—反作用已闭合 |
| 六维 contact-only 装配 | 已定义，作用点存在性和自由力偶保留 |
| 无隐藏支承 | 以完整残量和模式乘子零条件实现 |
| 固定/rocking 统一模式 | 已由完整坐标、模式约束和 KKT 表达 |
| 四单元法向位置符号 | 已给出四个显式公式和 `rho` 修正 |
| `P_i` 所有权 | contact、执行器功、系统边界分栏 |
| 位移加载、事件、损伤、事务 | 已形成可编程单步顺序 |
| 稳定性和失败分类 | 代数根、退化、未认证、物理失稳和数值失败分离 |
| 当前 B 合同审计 | 已证明正式墙面内加载不在 1.0.0 认证子空间 |
| 最小 B 扩展 | 已列输入、输出、事件、功、事务和兼容测试 |
| 两方向预期 | 只给条件性结论，未未经求解排序 |
| C3 边界 | 保留渐进失效、峰值和峰后终止给 C3 |

### 30.2 最终自检

- [x] 输出是融合 C1+C2 的最新完整 C 模块上下文，而非 C2 增量。
- [x] `s_stop`、B/A opaque 状态、DamageStore、事件、功和收据未丢失。
- [x] 内部径向锁定与整体刚体运动分离。
- [x] `+X` 与 `45°` 的 `50 mm` 偏心力矩符号正确。
- [x] contact-only、`P_i`、加载执行器和约束反力未重复装配。
- [x] 固定姿态不借用免费反力矩；yaw 排除也需要零乘子。
- [x] rocking 四个法向位移公式及 `rho` 修正明确。
- [x] 当前 B 合同缺口被安全拒绝，没有旋转旧 wrench 或降阶伪装。
- [x] B 2.x 扩展只是候选要求，没有自称已修改正式合同。
- [x] 事件、DamageStore、同位置级联和原子提交形成闭环。
- [x] 稳定性未与代数根、Newton 收敛或单个负切线混淆。
- [x] 文献 17/28 的不可迁移数值未进入项目参数。
- [x] 工程事实无变化；未决参数保持显式。
- [x] 当前只声称理论与测试定义完成，不声称代码或实验通过。


---

# 第三篇：C3 单元渐进失效、整体重分配与最大承载

> 注：第 29 节是 C2 阶段形成的历史交接要求。本篇在不反向修改 C1/C2 已接受定义的前提下完成这些要求；第 31–48 节是当前阶段的正式解释。

## 31. C3 范围、边界与完成状态

### 31.1 本轮覆盖的物理与算法问题

C3 在 C2 偏心六维平衡之上新增：

- 从当前完整 `C2AcceptedState` 持续推进加载点位移，不重置 `s_stop`、姿态、单元历史、DamageStore 或事件账本；
- 将 B/A 返回的针级滑移、材料/针体强度、硬限位、释放、脱离和再挂接事件无损传播到单元级历史相关响应；
- 定义可回调、不可丢失原始历史的单元状态压缩接口；
- 定义局部低维切线/割线/graph 的可用条件，以及必须完整回调 B 的条件；
- 在任一针级、单元级或整体事件后，从同一全局 accepted state 重新调用四个单元并重新求解允许位姿、加载反力、共享损伤和六维平衡；
- 定义一侧压紧、对侧剥离的因果链，而不把法向位移趋势直接等同于分支失效；
- 分离首个针失效、首个单元显著退化、稳定反力峰值候选、最终临界能力、代数无平衡、物理失稳、可恢复脱附和不可恢复脱附；
- 构造 `+X` 与 `45°` 两个正式方向的历史相关稳定反力曲线；
- 定义非光滑峰、平台、多个局部峰、峰后稳定下降分支、再挂接二次峰及最终终止；
- 定义面向未来偏心拉力实验的连续量、事件、姿态、损伤、功、质量、版本和重放输出合同；
- 明确当前 B 1.0 运动子空间缺口下的 C3 安全拒绝路径。

### 31.2 本轮明确不处理

C3 不重新推导或实现：

- A 层球尖接触、摩擦、针梁、轴向弹簧、材料强度、损伤、脱离和再挂接；
- B 层逐针载荷共享、活动集、单元内部失效重分配、DamageStore 物理合并和级联规则；
- B 2.x 完整 twist/姿态扩展的实际合同审批、代码或验证；
- 框架、导轨和真实传动链柔性；
- 绕 Z 轴整爪扭转扫描、大角度翻转、惯性动力学或脱落后运动；
- 显式裂纹扩展、碎屑、地形重网格化和针尖磨损；
- 单一二元抓附成功阈值、综合评分或未经标定的显著退化百分比；
- 大模块 C 集成文件、全局集成模型、求解器代码、CAD 或控制器实现。

### 31.3 当前完成与认证状态

| 项目 | 当前状态 |
|---|---|
| C3 物理状态机、事件重平衡和数据合同 | 已完成并经 `C3-r01` 审查接受 |
| C1+C2 历史继承 | 已在本文件完整保留 |
| 工程事实变化 | 无；候选与 `engineering_fixed_context 1.0.0` 基线逐字一致 |
| B_TO_C 1.0 正式 `+X/45°` 在线加载 | 未认证，必须安全拒绝 |
| B 2.x 完整 twist/姿态扩展 | 未实现、未接受 |
| 显著退化阈值和峰值容差 | 未固定，保持配置化/不可用 |
| 数值求解器与代码测试 | 未实现，不声称通过 |
| 偏心拉力实验 | 未实施，不声称验证 |
| 大模块 C 集成 | 尚未开始；C3 完成不等于集成完成 |

### 31.4 C3 必须遵守的工程事实与上游合同

| 类别 | 必须遵守的 ID/合同 | C3 中的作用 |
|---|---|---|
| 层级边界 | `PROJECT.ARCHITECTURE.PHYSICAL_LEVELS`、`PROJECT.ARCHITECTURE.DEPENDENCY` | C 只能通过 B 调用低层物理。 |
| 连续原始输出 | `PROJECT.OUTPUTS.NO_BINARY_SUCCESS` | 保存曲线和事件，不擅自定义成功/失败。 |
| 坐标与十字几何 | `COORDINATE.GLOBAL.FRAME`、`COORDINATE.UNIT.FRAME`、`GEOMETRY.CROSS.LAYOUT` | 固定方向、参考点和 80 mm 力臂。 |
| 刚体/rocking | `KINEMATICS.CROSS.RIGID_REFERENCE` | 仅允许规定的小角度模式；无框架承载。 |
| 法向推力 | `LOAD.NORMAL.ACTUATOR_OUTPUT`、`LOAD.NORMAL.CROSS_GRIPPER` | 每个 `P_i` 为恒主动推力，不是恒接触合力。 |
| 同步搜索 | `LOAD.CROSS.SEARCH_SYNCHRONIZATION` | `s_stop` 锁定，不为四单元分配独立径向位移。 |
| 加载点/方向 | `LOAD.CROSS.ECCENTRIC_POINT`、`LOAD.CROSS.DIRECTIONS`、`LOAD.CROSS.ECCENTRIC_MOMENT` | 固定 50 mm 偏心和两个正式方向。 |
| 位移控制 | `LOAD.CROSS.DISPLACEMENT_CONTROL` | 由稳定反力曲线和临界状态定义能力。 |
| 数值事件 | `NUMERICS.DRAG.VARIABLE_STEP` | 事件附近缩步和定位；不改变物理加载速度。 |
| 损伤历史 | `DAMAGE.MEMORY.LIGHTWEIGHT` | 同一连续承载过程保留历史，新独立样本才重置。 |
| 首版排除 | `SCOPE.FIRST_RELEASE.EXCLUSIONS` | 禁止越界加入大角度、惯性、框架有限元等。 |
| 未决登记 | `UNRESOLVED.DAMAGE.EVOLUTION`、`UNRESOLVED.NUMERICS.EVENT_STEPS`、`UNRESOLVED.VALIDATION.ERROR_TOLERANCE` 等 | 缺失量必须显式 `unavailable`/待标定。 |
| 上游调用合同 | `B_TO_C 1.0.0 accepted` | 冻结唯一入口、contact-only wrench、事件、历史、损伤与事务。 |

## 32. C2 历史的无损继承、C3 输入输出与新符号

### 32.1 C3 唯一初态与连续后继

首次 C3 调用的唯一合法初态为已原子提交的 `C2AcceptedState`。后续每一步以此前已原子提交的 `C3AcceptedState` 为初态，而该对象必须嵌入并保留完整 C2 物理状态。必须继承：

- `parent_C1PreloadState_id`、`s_stop_mm` 和径向锁定规则；
- 当前累计 `delta_P`、加载方向、加载点位置、整体 `q_C` 和 rocking 模式；
- 四个 B accepted snapshots、内部 A opaque handles、当前单元姿态和变换；
- 同一共享 DamageStore 版本、哈希和读写依赖；
- 四个 contact-only wrench、自由力偶、作用线/作用点可用性、balance/graph 和当前分支；
- 针级/单元级事件、级联、再挂接、剩余弹簧/合法路径行程和恢复性；
- C1/C2 功、能量、数值误差、哈希、重放清单和提交收据；
- 当前 B 完整回调条件、合同覆盖状态和最后有效 accepted state。

不得进行以下“便捷初始化”：

- 将 `delta_P` 或 `q_C` 归零；
- 重新执行 C1 搜索或改变 `s_stop`；
- 清空 DamageStore 或重新生成表面；
- 丢弃 B/A opaque 历史，只保留当前 wrench、峰值、有效刺数或切线；
- 将旧 C2 wrench 旋转到新姿态而不回调 B；
- 把 C2 未认证状态作为 C3 零承载初态。

### 32.2 C3 新增持久历史

只有全局原子提交后，以下量才能推进：

- 当前 C3 稳定分支 ID、父分支和合法事件跳转；
- 已接受的 `delta_P`—`F_reaction` 原始曲线点；
- 针级、单元级和整体事件的序列、同时组、因果依赖和恢复性；
- `FIRST_NEEDLE_FAILURE`、`FIRST_UNIT_SIGNIFICANT_DEGRADATION` 等一次性里程碑；
- 当前已观测稳定反力最大值、峰值候选集合和候选不确定性；
- `F_crit_confirmed` 标志及确认所依据的终止/覆盖证据；
- 峰后分支、再平衡、再挂接和二次峰历史；
- 更新后的四个 B/A accepted states 与共享 DamageStore；
- C3 功、能量、误差、版本、哈希和提交收据。

Newton 迭代、线搜索、事件括区间、峰值定位、分支枚举、损伤 fixed point、并行试探、回滚和同键重试均不得累计这些历史。

### 32.3 C3 新符号与单位

| 符号 | 含义 | 单位 |
|---|---|---|
| `δ_P` | 沿正式方向的累计加载点位移 | mm |
| `Δδ_P` | 当前共同加载试探增量 | mm |
| `λ_P` | 加载器作用于爪体、与正 `δ_P` 功共轭的反力 | N |
| `F_reaction` | 正向位移控制所需的反力幅值；主线取 `λ_P` | N |
| `b` | 当前稳定分支 ID/句柄 | 1 |
| `H_i` | 第 i 单元完整 B/A opaque 历史与 accepted state | 数据对象 |
| `D` | 共享 DamageStore | 数据对象 |
| `G_i` | 第 i 单元当前历史相关 admissible response/graph | 集合值对象 |
| `m_{ic}` | 第 i 单元第 c 个归一化有符号裕度 | 1 |
| `m_i^{LB}` | 第 i 单元在当前 graph 上的保守最弱裕度下界 | 1 |
| `m_G^{LB}` | 当前整体局部能力对象的保守最小裕度 | 1 |
| `φ_{i,k}` | 第 i 单元第 k 个显著退化事件函数 | 按定义，通常 1 |
| `γ` | 当前共同加载路径上的事件分数 | 1 |
| `F_max^{obs}` | 已接受稳定历史中的当前最大观测反力 | N |
| `F_crit` | 所有经认证可达稳定分支上的临界反力 | N |
| `B_stable,reachable` | 经 accepted 历史与合法事件跳转可达的稳定状态集合 | 集合 |

角度、力矩和刚度单位继续沿用 C2：rad、N·mm 和 N/mm。任何归一化矩阵或尺度必须绑定配置 ID；不得把 N 与 N·mm 未经尺度化直接作欧氏范数。

### 32.4 必需输入

每个 C3 全局试探至少包含：

1. 完整当前 `C2AcceptedState` 或 `C3AcceptedState` 与提交收据；
2. 正式加载方向 `GLOBAL_POS_X` 或 `GLOBAL_POS_XY_45`；
3. 目标 `δ_P` 或 `Δδ_P`，以及事件侧/插值规则；
4. 四个 `P_i`、当前系统边界、rocking 模式和真实授权约束；
5. 四个 B/A accepted snapshots、当前姿态/参考点变换和表面/参数/配置哈希；
6. 同一共享 DamageStore accepted snapshot；
7. B 合同版本及完整运动覆盖声明；
8. 事件、损伤、稳定性、显著退化、峰值和数值配置 ID；
9. 允许的分支连续性/选择政策和幂等性键；
10. 要求的原始响应、graph、作用线、质量、功和确定性重放字段。

缺失字段不得默认补齐。尤其是 B 完整 twist 支持、显著退化阈值、峰值容差、rocking trust region、材料/表面参数或真实试验架约束缺失时，必须返回对应 `unavailable/uncertified`，不得采用论文数值或隐式百分比。

### 32.5 必需输出

每个试探/接受步至少输出：

- 四个原始 B responses 或无损句柄；
- 四个运输到 C 的 contact-only wrench、作用线/作用点可用性和功检查；
- 当前完整六维残量/graph、`q_C`、`λ_P` 和授权约束反力；
- 四单元活动/承载针摘要、逐针事件句柄、剩余行程和恢复性；
- 全局最早事件、同时事件组、共享损伤冲突图和同位置级联；
- 当前稳定性、分支、秩、零空间、条件数和认证等级；
- 首针/首单元里程碑、最弱分支和显著退化事件函数；
- 当前 `F_reaction`、峰值候选、`F_max^obs` 和 `F_crit` 是否可确认；
- 物理/未认证/数值/事务状态的完整分类；
- 功、能量、耗散、数值误差、版本、哈希、回滚/提交令牌；
- 最后有效 accepted state 和下一步强制完整回调条件。

不可用量必须返回 `unavailable` 及理由，不得以零代替。

## 33. 历史相关单元状态压缩与完整回调接口

### 33.1 压缩接口的目的和禁止退化

C3 需要在四单元整体求解中高效调用 B，但“压缩”只意味着建立可审计索引和局部预测对象，不意味着删除低层历史。定义 `C3UnitContinuationCapsule_i`：

```text
C3UnitContinuationCapsule:
  identity_and_versions
  raw_EmbeddedUnitTrialResponse_handle
  accepted_B_snapshot_handle
  accepted_A_opaque_bundle_handle
  DamageStore_dependency
  current_pose_and_reference_transform
  contact_only_wrench_and_graph
  resultant_axis_point_CoP_availability
  balance_branch_rank_nullspace_condition
  active_load_bearing_stick_slip_strength_hardstop_summary
  original_unit_event_group_handles
  local_tangent_secant_or_graph
  one_sided_direction_and_trust_region
  predicted_event_distance_and_bracket
  remaining_spring_and_certified_path_travel
  collision_domain_geometry_quality
  strength_damage_recovery_margins
  weakest_normalized_margin_and_residual_direction_capability
  uncertainty_and_certification
  full_unit_resolve_callback_requirement
  callback_reason_codes
```

该对象不得退化为：

- 单元峰值或固定极限面；
- 单个 6×6 切线；
- 当前有效刺数、平均单刺力或总接触数；
- 只含当前 wrench 而不含参考点和自由力偶；
- 只含显著退化标签而丢弃原始针级事件；
- 无 DamageStore、分支、trust region 或完整回调句柄的静态摘要。

### 33.2 历史相关局部 response/graph

在当前 accepted 历史 `H_i`、DamageStore `D`、分支 `b_i` 和控制/姿态模式固定时，B 单元局部响应可抽象为

$$
\boxed{
\left(\Delta\mathbf W_i,\Delta\mathcal H_i,\mathcal E_i\right)
\in
\mathcal G_i^{\mathrm{loc}}
\left(
\Delta\boldsymbol\xi_i;
\mathcal H_{i,n},
\mathcal D_n,
P_i,
\chi_i
\right)
}
$$

其中 `χ_i` 绑定参考点、表达框架、表面、参数、姿态、分支和数值配置。该关系可以是：

- 唯一光滑分支上的切线；
- 一侧切线或割线；
- 集合值 admissible graph；
- 只能通过完整 B trial 评价的黑盒历史算子。

任何事件、历史、DamageStore、姿态或控制模式变化都会改变 `G_i^loc` 的身份；旧对象必须立即失效。

### 33.3 局部低维响应的允许条件

只有以下条件全部满足时，C3 才可在 B 返回的 trust region 内使用局部切线、割线或 graph 进行预测、Newton 线性化、事件外步长控制或最弱分支审计：

1. B 扩展已认证本次完整基座 twist 和当前动态姿态；
2. 源/目标参考点、表达框架、单位、`P_i`、系统边界和控制模式完全一致；
3. accepted B/A states、DamageStore、表面、参数和变换版本未改变；
4. 活动支持、粘滑、弹簧内部/硬限位、材料、强度和恢复分支不变；
5. 预测增量不跨越任何针级、单元级、整体稳定性、姿态 trust region、碰撞、域或几何事件；
6. graph/切线的秩、条件、方向和质量满足配置；
7. 所需保守下界存在；集合值响应未被静默选成单值；
8. 当前任务不需要精确逐针损伤冲突、同位置级联、作用点、能量、恢复性或显著退化确认；
9. `full_unit_resolve_callback_requirement=false`。

局部预测只能用于产生候选或步长，不能直接永久更新 B/A 历史。

### 33.4 强制完整 B 回调条件

出现任一情况，四单元整体求解至少必须完整回调受影响单元；在刚性十字整体平衡中默认四个单元全部重调：

- 接触建立/释放、真实滑移起始、支持迁移、材料起始/软化、针体强度、硬限位、脱离或再挂接；
- 活动集、branch、DamageStore、accepted state、姿态、控制模式、系统边界或参考变换改变；
- graph 非唯一、切线奇异/不可用、超出 trust region；
- 接近碰撞、域边界、几何质量或小角度认证边界；
- 单元显著退化候选、整体峰值附近、峰后分支、稳定性或恢复性判断；
- 需要精确作用线、自由力偶、逐针裕度、损伤冲突或能量账本；
- B 返回 `full_unit_resolve_callback_requirement=true`；
- 当前 B 合同不认证所需局部 y/姿态运动。

### 33.5 压缩对象的有效性标识

每个 capsule 必须带有唯一有效性键：

```text
validity_key = hash(
  B_contract_version,
  B_model_version,
  accepted_B/A_state_ids,
  DamageStore_version,
  surface_and_parameter_hashes,
  current_unit_pose,
  O_A_to_C_transform,
  control_mode_and_P_i,
  branch_id,
  trust_region_id,
  numerical_config_id
)
```

任一组成量变化即禁止复用旧 capsule。仅修改显示坐标但不改变物理姿态时，可以重新表达同一 wrench；改变真实姿态时必须完整 B 重求解。

## 34. 偏心加载下压紧—剥离的闭合因果链

### 34.1 `+X` 工况的符号检查

正 `+X` 外载在 C 点产生

$$
\mathbf M_{\mathrm{ext}}=+50F\mathbf E_Y\ \mathrm{N\,mm}.
$$

contact-only 与其他授权 wrench 必须提供相反的 `-M_Y`。忽略单元自由力偶、横向力、`rho_A/i` 和其他项时，X 对置分支贡献

$$
M_Y^{(1,2)}=40(F_{z1}-F_{z2}),
$$

故符号一致性要求趋向 `F_{z2}>F_{z1}`。C2 的运动学检查表明正 `theta_Y` 使单元 1 远离墙面、单元 2 靠墙。这只说明一个可能的运动—力矩补偿方向；实际 `F_zi`、滑移、损伤、脱离或再挂接必须由当前完整 B response 和六维平衡确定。

Y 对置组即使不位于主要倾覆力矩平面，也仍可通过：

- 横向 contact-only 力；
- 单元自由力偶和作用线；
- 整体平移/rocking 耦合；
- DamageStore 与历史相关刚度；
- `rho_A/i` 和非对称地形；

参与平衡。不得先验冻结单元 3、4 的响应。

### 34.2 `45°` 工况的符号检查

`45°` 外载产生

$$
\mathbf M_{\mathrm{ext}}
=
\frac{50F}{\sqrt2}
\left(-\mathbf E_X+\mathbf E_Y\right)
\ \mathrm{N\,mm}.
$$

contact/authorized wrench 需同时提供 `+M_X` 和 `-M_Y`。在简化成对法向力矩中：

$$
M_X^{(3,4)}=40(F_{z4}-F_{z3}),
\qquad
M_Y^{(1,2)}=40(F_{z1}-F_{z2}).
$$

因此两组对置分支同时被耦合。实际 rocking 方向、靠墙/离墙侧和先失效身份仍受完整 B response、作用线、自由力偶、历史损伤和执行器边界控制，不得只用上述简化符号式判定。

### 34.3 每个接受步必须闭合的因果链

C3 必须能够逐项追踪：

```text
偏心加载点位移增加
  -> 外部 wrench 与允许整体位姿候选改变
  -> 四个 O_A 的完整基座 twist 和法向位置改变
  -> B 内逐针 gap、接触、粘滑、弹簧、强度和 DamageStore 响应改变
  -> 单元 contact-only wrench、作用线、graph、切线和剩余行程改变
  -> 四单元六维平衡与加载反力重新求解
  -> 一侧压紧/对侧释放、稳定状态或最早事件
  -> 事件定位、损伤协调、同位置级联
  -> 新的 accepted 稳定状态或明确终止
```

任何跳过 B 针级回调、只把旧载荷转移给其余单元的做法都会断开该因果链。

### 34.4 `P_i` 恒定的正确解释

每个 `P_i` 保持为恒主动广义推力，但：

- 实际 contact-only 法向合力可以随姿态和事件增加或减小；
- 靠墙侧可能增载，也可能因局部破坏而失去能力；
- 离墙侧可能释放、滑移、脱离，也可能在后续位移上再挂接；
- `P_i` 不得作为第二份墙面 wrench 加入整体平衡；
- `P_i` 的执行器功只有在端点和相对行程已认证时才能完整计算。

## 35. 针级事件、单元退化与里程碑定义

### 35.1 针级事件分类

C3 必须原样保留 B/A 的细分事件，不得把所有事件都称为“失效”。至少区分：

- `NEEDLE_CONTACT_ESTABLISHED`；
- `NEEDLE_STICK_TO_SLIP` / `NEEDLE_SLIP_MIGRATION`；
- `NEEDLE_MATERIAL_FAILURE`；
- `NEEDLE_STRENGTH_LIMIT`（针体或其他已定义强度事件）；
- `NEEDLE_SPRING_HARDSTOP`；
- `NEEDLE_CONTACT_RELEASED`；
- `NEEDLE_DETACHED_RECOVERABLE` / `NEEDLE_DETACHED_TERMINAL`；
- `NEEDLE_REENGAGED`；
- B 定义的同时事件组和同位置级联组。

`FIRST_NEEDLE_FAILURE` 只在本次 C3 路径中首次出现经 B/A 认证的材料、针体强度或其他明确“失效”事件时记录。首次滑移、硬限位或接触释放分别使用自己的里程碑；除非 B 明确将其分类为终止性强度/材料失效，否则不得升级为 `FIRST_NEEDLE_FAILURE`。

### 35.2 首个针失效不等于单元失败

发生针级事件后必须：

1. 定位事件点；
2. 完整回调 B，处理单元内部同时事件、损伤和重新平衡；
3. 获取事件后 contact-only wrench/graph、活动承载集合、剩余行程和恢复性；
4. 将四单元全部纳入整体重平衡；
5. 仅在单元显著退化事件函数被认证跨越时记录单元里程碑。

因此可能出现：

- 首针材料失效后单元仍有稳定承载；
- 单元当前 wrench 下降但其余针重新分担；
- 单元短暂脱离后在峰后路径再挂接；
- 单元能力显著退化早于、晚于或从不出现于整体峰值之前。

### 35.3 单元显著退化事件函数族

由于当前没有批准的唯一百分比，C3 定义一组版本化事件函数，而不是单一硬编码规则。对第 i 单元的当前历史相关能力通道 `c`，定义有符号归一化裕度：

$$
\widehat m_{ic}
=
\begin{cases}
\dfrac{y_{ic}-b_{ic}}{\sigma_{ic}}, & \text{下限型通道},\\[2mm]
\dfrac{b_{ic}-y_{ic}}{\sigma_{ic}}, & \text{上限型通道},
\end{cases}
$$

其中 `b_ic`、`sigma_ic>0`、事件侧和置信规则均由 `unit_degradation_policy_id/version` 给出。若响应为集合值 graph，则使用保守下界

$$
\boxed{
 m_i^{\mathrm{LB}}
 =
 \inf_{\mathbf w\in\mathcal G_i^{\mathrm{admissible}}}
 \min_{c\in\mathcal C_i}
 \widehat m_{ic}(\mathbf w)
}
$$

并保留原 graph。

允许的显著退化事件函数族包括：

1. **最弱裕度越界**
   $$
   \phi_i^{m}=m_i^{\mathrm{LB}}-m_{i,\mathrm{req}};
   $$
2. **指定方向残余能力下界越界**
   $$
   \phi_i^{C}=C_i^{\mathrm{LB}}(\hat{\mathbf d},\mathcal H_i)-C_{i,\mathrm{req}};
   $$
3. **当前方向不再属于承载 graph**；
4. **可恢复到不可恢复的离散转换**；
5. **经尺度化的事件前后有限跳变**
   $$
   \phi_i^{J}=J_{i,\mathrm{req}}-J_i,
   \qquad
   J_i=
   \left\|
   \mathbf S_W
   \left(\mathbf W_i^{+}-\mathbf W_i^{-}\right)
   \right\|_2,
   $$
   其中 `S_W` 负责 N/N·mm 的单位尺度化；
6. 由 B 返回的明确单元终止/graph 丧失事件。

阈值缺失、graph 无保守下界、质量不足或模型未认证时，返回 `UNIT_SIGNIFICANT_DEGRADATION_UNCERTIFIED`，同时继续保存全部原始连续量和针级事件；不得默认为 10%、20% 或论文参数。

### 35.4 `FIRST_UNIT_SIGNIFICANT_DEGRADATION`

该一次性里程碑仅在以下条件全部满足时记录：

- 事件函数版本和尺度完整；
- 事件前、事件点和事件后一侧状态通过完整 B 回调；
- DamageStore fixed point 和四单元重平衡完成；
- 事件函数由正侧跨越零或发生认证的离散不可逆转换；
- 当前候选通过合同、几何、域、数值和稳定性质量要求；
- 全局原子提交成功。

若多个单元事件括区间重叠，记录一个跨单元同时里程碑组，不按单元 ID 强制排序。

### 35.5 整体里程碑互不混淆

| 里程碑/状态 | 定义 | 不能等同于 |
|---|---|---|
| `FIRST_NEEDLE_FAILURE` | 首个认证材料/强度类针事件 | 首个滑移、首个单元失败、整体峰值 |
| `FIRST_UNIT_SIGNIFICANT_DEGRADATION` | 首个版本化单元退化事件面跨越 | 任意针事件或任意反力下降 |
| `GLOBAL_REACTION_PEAK_CANDIDATE` | 已接受稳定分支上的局部/区间峰值候选 | 最终 `F_crit` |
| `GLOBAL_CRITICAL_CAPACITY_CONFIRMED` | 合法终止/覆盖后确认的全可达稳定能力 | 当前最大观测值 |
| `GLOBAL_EQUILIBRIUM_INFEASIBLE` | 模型/参数/数值有效但无 admissible 代数平衡 | Newton 不收敛 |
| `GLOBAL_PHYSICAL_INSTABILITY` | 代数根可能存在但所有合法一侧稳定分支消失 | 单个负切线分量 |
| `GLOBAL_DETACHMENT_RECOVERABLE` | 当前失载但存在合法继续/再挂接稳定路径 | 物理终止 |
| `GLOBAL_DETACHMENT_IRRECOVERABLE` | 已证明无合法稳定承载/再挂接分支 | 合同/模型/参数缺失 |

## 36. 事件后的四单元非线性重平衡与最小整体能力对象

### 36.1 联立的历史相关整体问题

在当前 accepted 历史和 DamageStore 上，第 i 单元的 contact-only wrench 必须属于其历史相关 response/graph。C3 的整体平衡写为

$$
\boxed{
\mathbf0
\in
\sum_{i=1}^{4}
\mathbf J_i^{\mathsf T}
\mathcal W_i
\left(
\boldsymbol\xi_i,
\mathcal H_i,
\mathcal D,
P_i
\right)
+
\lambda_P\mathbf b_P
+
\mathbf W_{\mathrm{other,authorized}}
}
$$

并同时满足：

- 加载点位移约束；
- rocking/禁止 yaw/真实试验架约束；
- 每单元 B admissible graph；
- 共享 DamageStore 一致性；
- 行程、碰撞、域、模型和参数边界；
- 一侧稳定性；
- 无隐藏支承和功共轭检查。

该式不是把四个固定能力域相加；`W_i` 会随姿态、事件、损伤、分支和历史改变。

### 36.2 任一事件后的强制重平衡顺序

发生针级、单元级或整体事件后必须：

1. 在共同 `delta_P` 路径上定位最早事件，拒绝跨事件目标；
2. 从同一全局 accepted state、同一事件位置和同一 DamageStore 基线重新构造四个单元的完整 twist；
3. 对四个单元执行无副作用 B trial；
4. 协调所有 opaque damage intents，得到一致 trial DamageStore；
5. DamageStore 改变后重新调用全部受影响单元，刚性整体主线默认四单元全调；
6. 重新求允许 `q_C`、`lambda_P`、可选执行器相对行程和整体 graph；
7. 检查完整六维残量、功、稳定性、行程、碰撞、域、模型和参数；
8. 若触发同位置新事件，继续级联直到 fixed point 或明确终止；
9. 只有一致、认证、稳定的候选才可 prepare 并全局原子提交。

### 36.3 禁止的载荷转移规则

C3 不得使用：

- 将失效单元旧载荷平均分给其余三个单元；
- 最近邻、距离权重、固定分配矩阵或经验比例；
- 只重算触发事件单元、冻结其余三个单元；
- 四个单元旧峰值或旧切线按比例缩放；
- `N_eff × 平均单刺力`；
- 文献 23 的 `F_7/6` 作为正式一般规则；
- 文献 28 的常数线性爪能力域作为永久无记忆约束。

载荷重分配必须由位移兼容、状态相关 response/graph、整体姿态、接触约束和六维平衡自动产生。

### 36.4 文献 23 的等刚度特殊基准

文献 23 的 `7→6` 换载可写成一般特殊极限：若事件前有 `N` 个承载分支，失去一个载荷为 `F_lost` 的分支，剩余 `N-1` 个分支完全等刚度、经历相同位移增量且无其他状态变化，则

$$
\boxed{
\Delta F_k=\frac{F_{\mathrm{lost}}}{N-1},
\qquad k=1,\ldots,N-1.
}
$$

该式只用于构造解析回归测试。离开“等刚度、固定姿态、同增量、无滑移/损伤/行程变化”的极限后，本项目必须返回完整非等分重求解结果。论文中的足数、砂纸、脱离阻力和几何行程不进入项目参数。

### 36.5 文献 28 型最弱裕度骨架的正确迁移

在当前固定历史、固定活动集和局部有效域内，可把四个单元的 admissible wrench 集记为 `C_i^loc(c)`，其中 `c` 是统一归一化安全裕度。局部诊断可写成

$$
\boxed{
 c^{\star}
 =
 \sup\left\{
 c:\
 -\lambda_P\mathbf b_P
 -\mathbf W_{\mathrm{other,authorized}}
 \in
 \bigoplus_{i=1}^{4}
 \mathbf J_i^{\mathsf T}\mathcal C_i^{\mathrm{loc}}(c)
 \right\}
}
$$

其中 Minkowski 和（集合中各元素逐项相加形成的新集合）只是一种集合表示；实际 `C_i^loc` 可以非线性、非凸、集合值和历史相关。该对象：

- 只在当前 accepted 历史、姿态、活动集、DamageStore 和 trust region 内有效；
- 必须保留四个原始 B response；
- 只能作为最弱分支审计、事件预测和保守局部能力；
- 任何事件、历史、姿态或 DamageStore 变化后立即失效并重建；
- 不能替代完整 B 回调或定义全局永久能力域。

### 36.6 最小整体能力对象

定义 `C3LocalWrenchCapability`：

```text
C3LocalWrenchCapability:
  parent_C3AcceptedState_id
  loading_direction_and_path_constraint
  four_unit_capsule_ids
  four_local_admissible_wrench_graphs
  assembled_local_wrench_graph_at_C
  weakest_normalized_margin_LB
  residual_direction_capacity_LB_UB
  branch_rank_nullspace_condition
  trust_region_and_event_distance
  pose_and_DamageStore_dependency
  conservative_inner_approximation_flag
  omitted_branch_or_nonconvexity_risk
  full_rebuild_conditions
```

若只能构造保守内近似，必须输出其有效域和遗漏风险，不能宣称完整全局能力域已知。

## 37. 全局事件定位、同时事件、共享损伤与同位置级联

### 37.1 全局最早事件分数

对当前共同加载目标，每个单元返回 `gamma_Ui` 及原始事件括区间；C3 还必须构造整体级事件分数：

- `gamma_pose`：小角度/完整姿态 trust region 边界；
- `gamma_graph`：整体 graph 秩、分支或有效域变化；
- `gamma_stability`：稳定分支终点或一侧稳定性事件；
- `gamma_collision`：体碰撞或禁止碰撞边界；
- `gamma_domain`：表面域、几何质量或模型有效域边界；
- `gamma_constraint`：加载路径或真实约束秩变化；
- `gamma_parameter`：分段参数/模型切换已由配置显式定义时的边界。

全局最早物理/认证事件为

$$
\boxed{
\gamma_C
=
\min\left(
\gamma_{U_1},\ldots,\gamma_{U_4},
\gamma_{\mathrm{pose}},
\gamma_{\mathrm{graph}},
\gamma_{\mathrm{stability}},
\gamma_{\mathrm{collision}},
\gamma_{\mathrm{domain}},
\gamma_{\mathrm{constraint}},
\gamma_{\mathrm{parameter}}
\right).
}
$$

若 `gamma_C<1`：

1. 当前目标不可提交；
2. 四个单元 trial、整体姿态、DamageStore intents、峰值试探和事务意图全部回滚；
3. 将共同 `delta_P` 增量缩短到事件括区间/事件侧；
4. 从同一 accepted state 重新计算四单元完整 twist；
5. 重新调用 B、运输 wrench、协调损伤并求六维平衡；
6. 不得按 `gamma_C` 线性缩放旧 wrench、旧姿态、旧 graph、旧损伤或旧反力。

峰值定位可以产生单独的 `peak_bracket_fraction`，但它是曲线审计事件，不得覆盖更早的物理、合同、碰撞或稳定性事件。

### 37.2 同时事件组

C3 必须保留每个 B 返回的 `unit_simultaneous_event_group`，再根据共同加载路径构造跨单元事件组。事件满足以下任一条件时视为全局同时：

- 括区间相交；
- 事件位置差不超过版本化 `epsilon_deltaP_sim`；
- DamageStore 读写/核重叠表明它们在同一物理冲突核中耦合；
- 整体 graph/stability 事件与单元事件在同一定位容差内。

规范排序仅用于哈希和重放：

```text
(event_delta_P, hierarchy, unit_slot_id, B_event_group_id, local_event_id)
```

排序不得决定物理先后，也不得拆散 B 单元内部组。物理更新遵守上游依赖偏序，但所有同时事件均保留在记录中。

### 37.3 共享 DamageStore fixed point

跨单元损伤处理沿用并扩展 C1/C2：

1. 收集四个 B responses 的 opaque damage intents、read/write sets、核重叠签名和版本；
2. 构造跨单元写—写、写—读和核重叠冲突图；
3. 调用 B/A 共享损伤协调器，得到共同 trial DamageStore 或明确非唯一/失败状态；
4. DamageStore 内容或依赖改变后，从同一全局 accepted state 重新调用全部受影响单元；刚性十字主线默认四单元全调；
5. 重新求整体姿态、`lambda_P`、wrench graph 和稳定性；
6. 迭代到 DamageStore 哈希、四单元响应、事件组、整体残量和 C3 里程碑一致；
7. 达到配置上限仍不一致时返回 `DAMAGE_CONFLICT_UNRESOLVED` 或 `C3_STOP_NUMERICAL`，全部回滚。

C3 不得相加损伤变量、取最大值、按单元调用顺序覆盖或直接修改 DamageStore。

### 37.4 同位置级联

事件点可能满足

$$
d\delta_P=0,
\qquad
d\mathbf q_C\ne0,
\qquad
d\eta_i\ne0,
$$

并伴随接触、弹簧、损伤或再挂接改变。C3 必须在同一加载位置重复：

```text
完整 B 回调
 -> wrench 运输
 -> DamageStore 协调
 -> 六维重平衡
 -> 新事件归约
 -> 一侧稳定性检查
```

直到：

- 形成稳定 fixed point；
- 定位到新的更早事件侧；
- 证明物理无平衡/失稳/不可恢复；
- 遇到未认证、模型/参数、域/碰撞、数值或事务失败。

同位置级联中的加载点功为零，但法向执行器相对行程、内部弹性释放、摩擦/损伤耗散和数值误差可能非零；必须按所有权分栏记录。

### 37.5 事件前、点、后状态

每个可提交事件至少保存：

- `pre_event_state_id`：事件前最后 accepted 状态；
- `event_point_trial_id`：事件点一致 trial；
- `post_event_state_id`：事件后一侧通过平衡/稳定性并提交的状态，若存在；
- 左/右侧 wrench、反力、姿态、DamageStore 和分支；
- 事件括区间、定位误差、同时组和因果依赖；
- 是否改变活动集、graph、单元能力和恢复性；
- 是否形成峰值候选；
- 是否提交、回滚或终止。

不能用事件点的未提交试探代替 accepted 曲线点。

### 37.6 事件与摘要状态优先级

物理时间顺序由最小合法路径分数决定；摘要状态优先级只用于输出主码，不删除并发信息。C3 的致命摘要优先级为：

```text
CONTRACT_VIOLATION / STALE_SNAPSHOT
-> C3_CONTRACT_EXTENSION_REQUIRED / KINEMATIC_MODE_UNSUPPORTED
-> OUT_OF_DOMAIN / GEOMETRY_UNCERTAIN / BODY_COLLISION_INVALID
-> MODEL_UNAVAILABLE / PARAMETER_UNAVAILABLE / ACTUATOR_WRENCH_UNCERTIFIED
-> DAMAGE_CONFLICT_UNRESOLVED / TRANSACTION_ERROR
-> NUMERICAL_NONCONVERGENCE
-> GLOBAL_PHYSICAL_INSTABILITY
-> GLOBAL_EQUILIBRIUM_INFEASIBLE
-> GLOBAL_DETACHMENT_IRRECOVERABLE
-> STABILITY_UNCERTIFIED / EQUILIBRIUM_DEGENERATE
-> EVENT_REDUCTION_REQUIRED / EVENT_REBALANCE_REQUIRED
-> GLOBAL_DETACHMENT_RECOVERABLE / REENGAGED / CASCADE_STABILIZED
-> C3_BALANCED_ACCEPTED
```

`all_status_codes` 必须完整保存。峰值候选和里程碑是正交事件，不覆盖主状态。

## 38. 稳定可达分支、反力曲线、最大承载与峰后终止

### 38.1 稳定可达分支的定义

定义状态节点

$$
\mathsf s
=
\left(
\delta_P,
\mathbf q_C,
\{
\mathcal H_i
\}_{i=1}^{4},
\mathcal D,
\lambda_P,
 b
\right).
$$

`B_stable,reachable` 由以下规则构造：

1. 从同一合法 `C1PreloadState/C2AcceptedState` 出发；
2. 节点必须经合同、几何、域、模型、参数、平衡、功和稳定性认证；
3. 节点只能通过连续 accepted 位移步或已定位、已提交的合法事件跳转连接；
4. graph 非唯一时必须保留分支集合和选择条件，不按 ID 静默选解；
5. 未认证点、数值失败点、隐藏支承平衡、跨事件插值点和回滚试探不属于该集合；
6. 分支切换必须由物理事件、连续性规则或明确的集合值选择政策触发；
7. 每个方向和每个初态建立独立集合，不共享损伤历史。

### 38.2 反力曲线

每个 accepted 稳定节点输出

$$
\boxed{
F_{\mathrm{reaction}}(\delta_P)=\lambda_P
}
$$

并同时保存：

- 作用—反作用约定；
- 加载方向和加载点；
- 稳定分支 ID；
- 当前 `q_C`、rocking 角和授权约束；
- 四单元完整 contact-only wrench；
- 针级/单元级事件和 DamageStore；
- 残量、稳定性、质量、功和不确定性。

原始曲线不得用单调包络、峰值保持或平滑拟合替换。滤波只能生成派生显示通道，原始 accepted 数据必须保留。

### 38.3 峰值候选的类型

`GLOBAL_REACTION_PEAK_CANDIDATE` 可以由以下情况产生：

1. **光滑局部峰**：事件外同一稳定分支上，一侧斜率从正变负；
2. **非光滑尖峰**：事件点的左侧稳定反力不小于右侧稳定反力，且邻域内无更高 accepted 点；
3. **平台**：在版本化位移区间内，反力变化位于容差带且一侧斜率区间包含零；
4. **分支端点峰**：稳定分支在物理失稳/无平衡前终止，端点反力高于其一侧邻域；
5. **集合值峰区间**：graph 非唯一时只能给出保守上下界和分支条件。

用一侧导数表示的统一检查为

$$
D^-F(\delta_P^*)\ge0,
\qquad
D^+F(\delta_P^*)\le0,
$$

但事件点和离散数据应通过括区间、割线和误差界实现，不能假定经典可微。

### 38.4 峰值定位与记录规则

- 只使用 accepted 稳定点和经事件定位的合法左右极限；
- 试探点、未认证点和回滚点不得进入峰值账本；
- 峰值括区间必须同时受位移误差和反力误差控制；
- 多个局部峰全部保留，不能只留首峰或最大峰；
- 峰值附近默认强制完整 B 回调，不使用跨事件旧切线；
- 平台报告区间、代表值和上下界，而不是伪造唯一点；
- graph 非唯一且无选择政策时，报告 `PEAK_SET_VALUED_UNCERTIFIED` 或能力区间；
- `current_observed_stable_max` 与最终能力分开。

### 38.5 最大承载的正式定义

对固定设计、表面实现/种子、参数、C1 预紧初态、加载方向、模式和系统边界，定义

$$
\boxed{
F_{\mathrm{crit}}
=
\sup_{\mathsf s\in\mathcal B_{\mathrm{stable,reachable}}}
F_{\mathrm{reaction}}(\mathsf s).
}
$$

若上确界由某个 accepted 稳定状态达到，可报告 `max`；否则必须报告上确界及未达到原因。临界结果同时绑定：

- 峰值状态/区间和分支；
- 四单元临界载荷分配与作用线；
- 首针/首单元里程碑；
- DamageStore、姿态和剩余行程；
- 终止/覆盖证据；
- 步长、事件和反力不确定性。

不得用四个单元峰值之和、某固定活动集 LP 的最优值或当前观测最大值替代该定义。

### 38.6 候选峰与确认能力的分离

`F_max^obs` 更新规则：

$$
F_{\max,n+1}^{\mathrm{obs}}
=
\max\left(F_{\max,n}^{\mathrm{obs}},\lambda_{P,n+1}\right)
$$

仅对新原子提交的稳定状态执行。它只是已观测最大值。

`GLOBAL_CRITICAL_CAPACITY_CONFIRMED` 只有在以下之一成立时才可记录：

1. 已定位物理终止，且终止后不存在允许的稳定可达分支；
2. 已按版本化分支探索政策穷尽所有合法稳定分支；
3. 达到工程允许的明确物理边界，且剩余路径/再挂接/分支证据证明不能产生更高合法稳定反力；
4. 对集合值问题形成经审查的保守上界，证明当前峰值达到该上界。

若因合同扩展缺失、模型/参数缺失、域/碰撞/几何不确定、稳定性未认证、数值不收敛或事务失败而停止，必须保留峰值候选和 `F_max^obs`，但 `F_crit_confirmed=false`。

### 38.7 首峰后继续加载

首个峰值、首次反力下降或首个单元退化均不允许自动终止。位移控制应在以下条件下继续：

- 存在经认证的稳定可达分支；
- 未越过工程几何/结构边界；
- B/表面/参数/姿态模型仍在有效域；
- 事件和损伤可被定位并形成一致 fixed point；
- 继续路径未被证明不可恢复。

继续加载的目的包括捕捉：

- 渐进剥离；
- 四单元再平衡；
- 单元或针再挂接；
- 稳定下降分支；
- 二次峰和多个局部峰；
- 最终无平衡、失稳或不可恢复脱附。

### 38.8 物理终止条件

物理终止至少分为：

1. **`GLOBAL_EQUILIBRIUM_INFEASIBLE`**：合同、模型、参数和数值有效，当前加载位置不存在任何 admissible 六维代数平衡；
2. **`GLOBAL_PHYSICAL_INSTABILITY`**：代数根可以存在，但所有可达 admissible 分支在允许的一侧扰动下失去恢复性；
3. **`GLOBAL_DETACHMENT_IRRECOVERABLE`**：关键单元/整体失去承载，且在剩余合法行程、活动针、DamageStore、再挂接和其他分支中已证明不存在稳定承载路径；
4. **`GLOBAL_PHYSICAL_BOUNDARY_REACHED`**：达到已授权的几何/结构允许边界，并已定位最后稳定状态。

`GLOBAL_DETACHMENT_RECOVERABLE` 是事件/中间状态，不是终止：当前反力可接近零，但若存在合法继续位移、姿态调整或再挂接分支，应继续求解。

### 38.9 非物理停止不得冒充能力终点

以下状态必须保留最后有效 accepted state、峰值候选和“最终能力未确认”：

- `C3_CONTRACT_EXTENSION_REQUIRED` / `KINEMATIC_MODE_UNSUPPORTED`；
- `MODEL_UNAVAILABLE` / `PARAMETER_UNAVAILABLE`；
- `OUT_OF_DOMAIN` / `GEOMETRY_UNCERTAIN` / `BODY_COLLISION_INVALID`；
- `ACTUATOR_WRENCH_UNCERTIFIED` / `STABILITY_UNCERTIFIED`；
- `NUMERICAL_NONCONVERGENCE`；
- `DAMAGE_CONFLICT_UNRESOLVED`；
- `TRANSACTION_ERROR`、陈旧快照或哈希不一致。

这些状态不能被写成“抓附失败”“整体脱落”或 `F_crit`。

## 39. `+X` 与 `45°` 的分支作用、对称性和比较规则

### 39.1 理想 D4 对称边界

若四个单元完全相同，表面统计各向同性，`P_i`、C1 预紧、DamageStore、剩余行程、`rho_A/i` 和姿态均按 90° 旋转对应，则系统具有四重旋转对称：

- `+X` 与 `+Y` 的曲线、事件和临界状态应旋转对应；
- 单元身份应按旋转置换；
- wrench、作用线和 rocking 角按张量/向量规则变换；
- `F_crit` 幅值在数值容差内一致。

该测试只验证实现的一致性，不证明 `+X` 与 `45°` 等价。

### 39.2 `+X` 方向的分支作用

`+X` 外载主要通过 `M_Y` 使 X 对置组形成压紧/剥离差，但 Y 组仍通过横向力、自由力偶、姿态、作用线和历史相关 graph 参与。C3 必须保存：

- 单元 1/2 的法向差和轴向/横向响应；
- 单元 3/4 的横向能力和力矩贡献；
- 四单元最弱裕度；
- 首事件身份和事件后重分配；
- 峰后 Y 组是否增载或失效。

不得把 Y 组预设为常量或零贡献。

### 39.3 `45°` 方向的分支作用

`45°` 同时耦合 X/Y 两组。它可能：

- 将外力和倾覆需求分散到两组；
- 使两组同时接近横向、剥离或行程边界；
- 在对称条件下形成近似成对均匀分担；
- 在方向性表面和异质历史下触发更复杂的同时事件或级联。

因此“更分散”不自动等于“更强”。最终优劣只能由完整配对求解得到。

### 39.4 实际对称破缺来源

- `2×5` 与 `5×2` 阵列方向；
- 表面各向异性和有限样本；
- C1 预紧事件与 DamageStore；
- 不同作用线、自由力偶和 `rho_A/i`；
- 弹簧剩余行程、硬限位和针级损伤；
- graph 非唯一和局部切线差异；
- 制造/参数误差和不同 `P_i`。

每个非对称结果必须能追溯到上述原始量，不能只报告两个总峰值。

### 39.5 配对比较协议

比较 `+X` 和 `45°` 时必须：

1. 使用同一设计、参数包和工程事实版本；
2. 使用同一 C1 搜索/停止策略；
3. 对同一表面实现/随机种子构造等价初态，或明确使用独立试验并报告差异；
4. 每个方向从独立复制的无损初态开始，不能沿用另一方向造成的 DamageStore；
5. 保存完整四单元 wrench、姿态、事件顺序、里程碑和峰后路径；
6. 报告样本级配对差值和不确定性；
7. 不未经求解固定哪个方向更有利。

## 40. C3 数据模型

### 40.1 `C3LoadRequest`

```text
C3LoadRequest:
  identity:
    gripper_instance_id
    c3_step_id / trial_id / newton_iteration_id
    global_event_sequence_id / caller_sequence_id
    request_idempotency_key
  baselines:
    current_C2AcceptedState_id | current_C3AcceptedState_id
    parent_C1PreloadState_id
    commit_receipt_id
    engineering_context_version = 1.0.0
    B_TO_C_contract_id / version
    C_module_context_version = 0.3.0
    C_module_context_status = accepted
  loading:
    direction_id: GLOBAL_POS_X | GLOBAL_POS_XY_45
    direction_vector_G
    delta_P_n_mm
    target_delta_P_mm | requested_increment_mm
    load_point_reference_id / r_P_mm
    interpolation_rule / event_side_request
  mode_and_boundary:
    rocking: off | on
    theta_Z: fixed_zero
    authorized_test_rig_constraints[]
    equilibrium_boundary_id
    normal_actuator_kinematics_mode
  unit_states[4]:
    accepted_B_snapshot_handle
    accepted_A_opaque_bundle_handle
    P_i_N
    current_T_G_from_A
    frozen_s_stop_mm
    unit_capsule_id_optional
    surface / parameter / configuration / state hashes
  damage:
    shared_DamageStore_handle / version / hash
  policies:
    event / damage / numerical / stability config IDs
    unit_degradation_policy_id / version
    peak_policy_id / version
    branch_continuation_policy_id / version
    pose_trust_region_id
    residual_scaling_id
    deterministic_replay_request
  requested_response:
    full_B_trial_phase
    tangent / secant / graph / capability modes
    event_location_required
    full_unit_resolve_requested
    raw_curve_and_event_output_required
```

### 40.2 `C3UnitContinuationCapsule`

```text
C3UnitContinuationCapsule:
  identity / validity_key / versions
  raw_B_response_handle
  accepted_B_A_history_handles
  DamageStore_dependency
  pose_reference_frame_and_O_A_to_C_transform
  contact_only_wrench / central_axis / CoP / free_couple
  balance_graph_branch_rank_nullspace_condition
  active_and_load_bearing_needle_summaries
  stick_slip_material_strength_hardstop_reengagement_summaries
  original_event_and_cascade_handles
  tangent_secant_or_admissible_graph
  one_sided_direction / trust_region / event_bracket
  remaining_spring_and_certified_path_travel
  collision_domain_geometry_and_model_quality
  normalized_margins / residual_direction_capacity
  uncertainty_and_certification
  full_unit_resolve_callback_requirement / reason_codes
```

### 40.3 `C3LoadTrialResponse`

```text
C3LoadTrialResponse:
  identity_and_trace:
    request_hash / response_hash
    versions_read / replay_manifest
  inherited_state_check:
    parent_state_ids / s_stop / delta_P / q_C / DamageStore
  kinematics:
    q_C_trial[6] / delta_P_trial / load_point_position
    per_unit_full_base_twist[4]
    per_unit_local_components[4]
    optional_eta_i[4]
  raw_unit_responses:
    complete_B_responses_or_lossless_handles[4]
    unit_capsules[4]
  wrenches_and_balance:
    contact_only_W_i_at_C[4]
    summed_contact_only_W
    loading_W / authorized_other_W
    full_residual_or_graph
    unauthorized_support_diagnostic
    power_checks[4]
  reaction_and_distribution:
    lambda_P / F_reaction
    per_unit_force_moment_line_CoP
    normal_tangential_components
    pair_moment_contributions
  events_and_damage:
    all_unit_event_groups
    global_earliest_fraction / brackets
    cross_unit_simultaneous_group
    damage_conflict_graph / fixed_point
    same_position_cascades
  degradation_and_milestones:
    needle_event_milestones
    unit_degradation_event_functions
    weakest_unit_and_margin
    recoverability
  stability_and_peak:
    branch / rank / nullspace / condition
    one_sided_stability
    local_capability_object
    peak_candidate / bracket / uncertainty
    current_observed_stable_max_candidate
  diagnostics:
    all_status_codes / primary_status
    contract_coverage / missing_extension_fields
    domain_geometry_collision_model_parameter_status
    work_energy_numerical_error_ledgers
    last_valid_accepted_state
  transaction:
    rollback_tokens[4]
    provisional_unit_and_damage_intents
    provisional_event_and_peak_ledger
    prepare_eligibility / global_bundle_draft
```

### 40.4 `C3EventRecord`

```text
C3EventRecord:
  event_id / hierarchy / entity_id
  event_type / source_B_A_event_ids
  delta_P_bracket / event_fraction_basis
  pre_event_state_id
  event_point_trial_id
  post_event_state_id_optional
  pre_point_post_wrench_pose_graph
  simultaneous_group_id / causal_dependencies
  DamageStore_pre_trial_post_versions
  degradation_function_and_crossing
  stability_and_recoverability
  peak_candidate_relation
  localization_error_and_certification
  committed: true | false
  commit_receipt_id_optional
```

重复发生的滑移、脱离和再挂接每次均有新事件记录；“首次”里程碑只引用路径中第一个已提交合格事件。

### 40.5 `C3AcceptedState`

```text
C3AcceptedState:
  identity:
    c3_state_id / commit_receipt_id
    parent_state_id / parent_C1PreloadState_id
    loading_direction_id
  accepted_path:
    delta_P_mm / q_C[6] / load_point_position
    rocking_mode / authorized_constraints
    lambda_P / F_reaction
    stable_branch_id / parent_branch / transition_event
  inherited_and_evolved_state:
    frozen_s_stop_mm
    accepted_B_snapshots[4]
    accepted_A_opaque_handles[4]
    current_unit_poses_and_transforms[4]
    shared_DamageStore_version / hash
  mechanics:
    contact_only_W_i_at_C[4]
    summed_contact_only_W
    authorized_control_fields_separate
    per_unit_graph_load_line_CoP
    local_capability_object
  degradation_and_history:
    full_event_and_cascade_ledger
    first_needle_failure_record_optional
    first_unit_significant_degradation_record_optional
    weakest_unit / margins / recoverability
    remaining_travel / collision / domain / quality
  peak_ledger:
    accepted_curve_handle
    current_observed_stable_max
    peak_candidates[]
    F_crit_confirmed: true | false
    F_crit_value_optional
    confirmation_evidence_optional
  work_quality_trace:
    work_energy_error_ledgers
    stability_evidence
    versions / hashes / replay_manifest
  next_step:
    full_B_callback_conditions
    contract_extension_requirement
    legal_continuation_or_termination_status
```

### 40.6 `C3MaximumCapacityResult`

```text
C3MaximumCapacityResult:
  identity_and_versions
  direction / design / surface / seed / parameter_bundle
  parent_C1PreloadState_id / initial_C2_state_id
  F_crit_N | unconfirmed_status
  peak_delta_P_mm / branch_id / peak_type
  peak_bracket_and_uncertainty
  terminal_status_and_evidence
  critical_q_C_and_rocking_angles
  four_unit_critical_wrench_distribution
  critical_needle_and_unit_state_handles
  first_needle_and_first_unit_milestones
  DamageStore_and_remaining_travel
  complete_curve_and_event_handles
  work_energy_quality_certification
  final_accepted_state_id / commit_receipt_id
```

若能力未确认，`F_crit_N` 不得填当前最大值；应使用 `null/unavailable` 并单列 `current_observed_stable_max`。

## 41. C3 单步状态机、可执行流程与主状态

### 41.1 主状态机

```text
C3_READY
  -> VALIDATE_AND_FREEZE
  -> BUILD_COMMON_LOAD_TARGET
  -> CONTRACT_COVERAGE_AUDIT
  -> FOUR_UNIT_TRIALS
  -> COUPLED_BALANCE
  -> EVENT_REDUCTION_REQUIRED | DAMAGE_COORDINATION_REQUIRED | CANDIDATE_CONSISTENT
  -> EVENT_POINT
  -> POST_EVENT_FOUR_UNIT_REBALANCE
  -> SAME_POSITION_CASCADE
  -> CANDIDATE_CONSISTENT
  -> STABILITY_AND_DEGRADATION_CHECK
  -> PEAK_LEDGER_UPDATE
  -> PREPARE_GLOBAL_COMMIT
  -> COMMITTED_CONTINUE | COMMITTED_PHYSICAL_TERMINATION
```

异常分支：

```text
any trial state
  -> C3_CONTRACT_EXTENSION_REQUIRED
  -> C3_STOP_UNCERTIFIED
  -> C3_STOP_NUMERICAL
  -> C3_TRANSACTION_ERROR
  -> ROLLBACK_TO_LAST_ACCEPTED
```

### 41.2 单步伪算法

```text
function C3_PROGRESSIVE_LOAD_STEP(accepted_state, request):

  1. VALIDATE_AND_FREEZE
     - 校验 state/receipt、s_stop、delta_P、q_C、四个 B/A snapshots、DamageStore、
       变换、方向、模式、P_i、配置、版本和幂等性键。
     - 冻结当前 accepted state；缺失字段不得默认补齐。

  2. PROPOSE_COMMON_LOAD_TARGET
     - 构造 target_delta_P = delta_P_n + requested_increment。
     - 提议允许的 q_C、rocking 和可选 eta_i；保持内部 s_stop 不变。

  3. MOTION_CONTRACT_COVERAGE_AUDIT
     - 计算四单元完整基座 twist 和局部 x/y/z/rotation 分量。
     - 若当前 B 未认证局部 y/姿态，返回 C3_CONTRACT_EXTENSION_REQUIRED；
       不推进 delta_P、DamageStore、事件、功或峰值账本。

  4. CHOOSE_LOCAL_OR_FULL_UNIT_EVALUATION
     - 按第 33 节检查 capsule validity、trust region 和事件距离。
     - 仅事件外可用局部预测；任一强制条件触发完整 B trial。

  5. SIDE_EFFECT_FREE_FOUR_UNIT_TRIALS
     - 从同一 accepted state 和同一 DamageStore 调四单元。
     - 收集原始 response/graph、wrench、事件、损伤 intents、作用点和 rollback tokens。

  6. WRENCH_TRANSPORT_AND_POWER_CHECK
     - 使用当前动态姿态和 O_A→C 变换运输力与力矩。
     - 验证每单元 wrench–twist 功不变；失败即合同错误并回滚。

  7. ASSEMBLE_AUTHORIZED_WRENCHES_AND_SOLVE_BALANCE
     - 装配 contact-only、加载点和明确授权的其他 wrench。
     - 求 q_C、lambda_P、可选 eta_i 和 admissible graph，使加载路径与六维平衡闭合。
     - 任何未授权支承只作诊断，不加入能力。

  8. GLOBAL_EARLIEST_EVENT_REDUCTION
     - 归约针/单元、整体 graph/stability、姿态、碰撞、域和约束事件。
     - 若跨越事件：全部回滚、缩步、从同一 accepted state 重调四单元。

  9. SIMULTANEOUS_EVENTS_AND_SHARED_DAMAGE_FIXED_POINT
     - 保留 B 单元内部事件组，形成跨单元组。
     - 联合协调 opaque damage intents；DamageStore 改变后默认重调四单元。

 10. SAME_POSITION_CASCADE_AND_FOUR_UNIT_REBALANCE
     - 允许 d(delta_P)=0 而 q_C、eta、接触和 DamageStore 改变。
     - 重复完整 B 回调、六维平衡、事件和损伤，直到 fixed point 或明确终止。

 11. DEGRADATION_AND_MILESTONE_EVALUATION
     - 记录细分针事件；FIRST_NEEDLE_FAILURE 仅按定义触发。
     - 计算单元退化事件函数；阈值缺失则标 uncertified，不伪造事件。
     - 更新最弱分支、恢复性和局部能力对象。

 12. STABILITY_AND_PEAK_EVALUATION
     - 检查当前候选的一侧稳定性、graph 和质量。
     - 仅对可提交稳定候选更新峰值括区间；首个下降不自动终止。

 13. CLASSIFY_CONTINUATION_OR_TERMINATION
     - 区分继续、物理无平衡、物理失稳、可恢复/不可恢复脱附、
       合同/模型/参数/域/数值/事务失败。
     - 非物理停止保留 last accepted 和 F_crit unconfirmed。

 14. PREPARE_GLOBAL_BUNDLE
     - 只有残量、事件、损伤、功、稳定性、质量和认证全部通过，
       才 prepare 四单元、内部 A、DamageStore、C 路径/姿态、事件和峰值账本。

 15. ATOMIC_COMMIT_OR_ROLLBACK
     - 一个提交使全部历史同时可见；任一失败全部不前进。
     - 同幂等键重试返回原收据或安全拒绝，不重复累计。

 16. BUILD_RESPONSE_OR_MAXIMUM_RESULT
     - 若继续，返回新的 C3AcceptedState。
     - 若物理终止且覆盖证据闭合，确认 F_crit 并返回 C3MaximumCapacityResult。
     - 若未认证/数值失败，保留最后有效状态和“最终能力未确认”。
```

### 41.3 互斥主状态

| 主状态 | 含义 | 提交政策 |
|---|---|---|
| `C3_BALANCED_ACCEPTED` | 当前唯一/声明分支稳定平衡通过 | 原子提交并继续 |
| `C3_BALANCED_DEGENERATE` | 平衡存在但 graph 非唯一 | 仅在策略允许且不静默选支时提交 |
| `C3_EVENT_REDUCTION_REQUIRED` | 目标跨越更早事件 | 不提交，缩步重调 |
| `C3_EVENT_REBALANCE_REQUIRED` | 位于事件点，需损伤/级联/重平衡 | 不提交中间态 |
| `C3_CONTRACT_EXTENSION_REQUIRED` | B 版本不认证完整 twist/姿态 | 不提交，保留最后状态 |
| `C3_STOP_UNCERTIFIED` | 模型、参数、作用线、稳定性、域等不足 | 不提交未认证候选 |
| `C3_GLOBAL_EQUILIBRIUM_INFEASIBLE` | 有效模型下无代数平衡 | 物理终止候选 |
| `C3_GLOBAL_PHYSICAL_INSTABILITY` | 所有合法一侧稳定分支消失 | 物理终止候选 |
| `C3_GLOBAL_DETACHMENT_RECOVERABLE` | 当前失载但有合法恢复路径 | 事件后继续 |
| `C3_GLOBAL_DETACHMENT_IRRECOVERABLE` | 无合法稳定承载/再挂接路径 | 物理终止候选 |
| `C3_MAXIMUM_CAPACITY_CONFIRMED` | 物理终止/覆盖证据闭合并确认 `F_crit` | 提交终态与结果 |
| `C3_STOP_NUMERICAL` | 平衡、事件、损伤或分支算法未收敛 | 不等于物理失败 |
| `C3_TRANSACTION_ERROR` | prepare/commit/持久化失败 | 全部回滚 |

### 41.4 里程碑的提交语义

- 里程碑只在其对应事件后状态或物理终态原子提交成功时成为 accepted；
- 试探中发现后又被更早事件覆盖的里程碑必须回滚；
- 同时事件中的多个“首次”以同一同时组记录；
- 重放同一幂等键不得生成第二个首次记录；
- `GLOBAL_REACTION_PEAK_CANDIDATE` 可以在后续被更高峰超过，但历史记录不删除；
- `GLOBAL_CRITICAL_CAPACITY_CONFIRMED` 只能出现一次，除非以新的方向/初态/配置开始独立运行。

## 42. 功、能量、原子事务与确定性重放

### 42.1 加载功

加载点位移控制功为

$$
\boxed{
\Delta W_{\mathrm{load}}
=
\int_{\delta_{P,n}}^{\delta_{P,n+1}}
\lambda_P\,d\delta_P.
}
$$

峰后反力下降不改变该功的定义；若 `lambda_P` 保持正而位移继续正向，加载器仍对系统输入正功。

### 42.2 法向执行器和低层能量

- `P_i` 的完整执行器功只有在端点和相对行程 `eta_i` 已认证时可计算；
- 若只知道理想单端广义力，整体执行器功标为 `unavailable`；
- B/A 返回的梁/弹簧储能、摩擦/材料耗散、释放能和硬限位边界继续分栏；
- 同位置级联 `d delta_P=0` 时加载功可为零，但法向执行器相对功和内部耗散可非零；
- 数值残量、约束乘子功和浮点误差不得写成材料耗散。

### 42.3 C3 全局提交包

```text
C3_global_bundle_manifest:
  parent accepted state and target delta_P
  q_C / mode / authorized constraint manifest
  four B provisional intents and all internal A states
  one shared DamageStore provisional intent
  complete contact/load/authorized wrench ledger
  global event/simultaneous/cascade/degradation ledger
  stability and local capability evidence
  accepted curve point and peak ledger update
  work / energy / numerical error ledger
  versions / transforms / hashes / replay manifest
```

只有全部 prepare 成功才发出一个原子提交。任一单元、DamageStore、整体平衡、稳定性、事件、峰值账本、持久化或收据失败，全部历史不前进。

### 42.4 回滚边界

以下情况必须回滚当前全部 trial：

- 更早事件被发现；
- DamageStore trial 改变；
- Newton/graph 分支或峰值括区间被拒；
- 合同、版本、哈希或快照陈旧；
- 整体残量、功、稳定性、域、碰撞或质量失败；
- 用户/求解器缩步或放弃当前目标；
- prepare/commit 任一步失败。

回滚后 `delta_P`、`q_C`、四个 B/A states、DamageStore、事件号、损伤、耗散、曲线点、峰值和首次里程碑均保持不变。

### 42.5 确定性重放

相同 accepted 快照、配置、表面、变换、方向和幂等性键应满足：

- 串行/并行和单元调用顺序置换得到相同接受状态；
- graph 非唯一时返回同一明确集合/分支句柄；
- 同时事件组和规范哈希一致；
- 重试不重复累计路径、损伤、事件、功或峰值；
- 相同物理终态得到相同 `C3MaximumCapacityResult` 或同一明确的非唯一结果集合。

## 43. 面向未来偏心拉力实验的输出与对齐合同

### 43.1 每个方向和样本必须保存的元数据

- 设计 ID、阵列几何、安装模式、针/弹簧/材料参数包和模型开关；
- 表面类别、实现方法、空间区域、随机种子和 DamageStore 初始版本；
- 工程事实、B 合同、C 上下文、求解器、数值和策略版本；
- `C1PreloadState_id`、`s_stop`、四个 `P_i`、预紧事件和初始 DamageStore；
- 加载方向、加载点位置、rocking 模式、授权试验架约束和系统边界；
- 请求/响应哈希、提交收据和确定性重放清单。

### 43.2 连续机械量

每个 accepted 样本点至少输出：

- `delta_P`、`F_reaction`、完整六维外部/反力 wrench；
- C 点位姿、加载点位置和 `theta_X/theta_Y`；
- 四单元 contact-only force/moment、参考点、自由力偶、作用线/CoP 可用性；
- 每单元局部 x/y/z 力、实际法向/切向分量和成对力矩贡献；
- 四单元最弱裕度、局部能力对象、graph、分支和剩余行程；
- 逐针/单元活动、承载、粘滑、硬限位、损伤、脱离和再挂接摘要；
- 整体残量、稳定性、质量、功、能量、耗散和数值误差。

### 43.3 事件和临界结果

至少保存：

- 所有针级/单元级/整体事件的位移、反力、括区间和同时组；
- DamageStore 变化、级联轮数、再挂接和恢复性；
- `FIRST_NEEDLE_FAILURE`、其他首针事件和 `FIRST_UNIT_SIGNIFICANT_DEGRADATION`；
- 每个峰值候选、峰值类型、分支、误差和是否被后续峰超过；
- 确认的 `F_crit` 或“未确认”状态；
- 最后稳定状态和物理/非物理终止类型；
- 临界时四单元/针级状态句柄。

### 43.4 位移与时间

工程事实只固定单刺/阵列直线拖拽速度 `1 mm/s`；没有固定 C2/C3 偏心加载速度。因此：

- C3 主输出以加载点位移为独立变量；
- 不得把 A/B 的 `1 mm/s` 自动用于整爪偏心加载；
- 若实验协议提供加载速度/时间戳，可建立版本化 `t↔delta_P` 映射；
- 若无该协议，时间通道标 `unavailable`，但事件顺序和位移位置仍完整保存。

### 43.5 仿真—实验对齐规则

1. **加载点与方向**：传感器作用点必须与 `P=C+50 E_Z mm` 对齐，或通过刚体 wrench 运输到该点；
2. **位移零点**：`delta_P=0` 定义为同一已接受预紧初态，而不是接触前或设备通电时刻；
3. **作用—反作用**：加载器作用于爪与爪作用于传感器的力/矩同时反号，幅值一致；
4. **姿态测量**：明确 C 点、参考体和传感器坐标，必要时输出变换与不确定性；
5. **预紧初态**：记录 `s_stop`、四个 `P_i`、法向位置、初始 DamageStore 和初始 wrench；
6. **采样与滤波**：保存原始数据；滤波器、延迟、截止频率和相位性质版本化；非因果滤波不得用于在线事件判定；
7. **事件对齐**：优先按位移和传感器阶跃/图像事件联合对齐，不只按时间；
8. **重复样本**：以独立表面区域/种子/试验批次为统计单位，不把同一曲线相邻点当成独立样本；
9. **方向配对**：`+X/45°` 尽量使用配对表面和等价预紧初态；
10. **验证目标**：首先比较趋势、设计排序和机理解释，不强行拟合某一次偶然峰值。

### 43.6 禁止输出未经批准的综合结论

当前输出不得自动包含：

- 二元“抓附成功/失败”；
- 单一综合评分；
- 未经标定的安全系数；
- 由单次峰值推断的材料强度；
- 由不同方向独立样本直接得出的确定性优劣排序。

## 44. 参数、证据、迁移边界与未决问题

### 44.1 证据分类表

| 机理/参数 | 来源 | 当前状态 | 使用边界 |
|---|---|---|---|
| 十字坐标、80 mm 几何、50 mm 加载点、两个方向 | 工程事实 | fixed/fixed_set | 不得被论文改写。 |
| 每单元 `P_i=0.5–2 N` | 工程事实 | fixed_range | 是主动推力，不是恒接触合力。 |
| C1/C2 历史、刚体/wrench/稳定性 | `C_MODULE_CONTEXT 0.2.0 accepted` | accepted | 必须无损继承。 |
| B 唯一入口、contact-only wrench、graph、事件、损伤、事务 | `B_TO_C 1.0.0 accepted` | accepted | 只认证 x/z；不得隐式扩展。 |
| 活动集 `7→6→7` 与剩余分支增载/阶跃 | 文献 23 | 特殊基准 | 等刚度二维履带极限，不作正式分配规则。 |
| 给定活动集的整体力/矩平衡和最小裕度 | 文献 28 | 上层骨架 | 常数爪域和固定接触集不替代 B 历史响应。 |
| 非光滑事件定位、分支延拓、一侧稳定性、峰值确认 | GPT 通用知识 | 本轮推导方法 | 需配置、实现和收敛验证，不固定数值。 |
| 四单元事件后完整重平衡 | 上游合同 + 本轮推导 | 理论定义 | 不采用均分或固定权重。 |
| 单元显著退化事件函数族 | 本轮推导 | accepted | 阈值、尺度和通道待标定。 |
| `F_crit` 稳定可达分支定义 | 工程输出要求 + 本轮推导 | accepted | 只有合法终止/覆盖后可确认。 |
| B 完整 twist/姿态响应 | 未决合同扩展 | unavailable | 未实现前正式加载安全拒绝。 |
| 材料、摩擦、损伤、表面和数值参数 | 工程未决登记 | unresolved | 文献/测量/实验/收敛关闭。 |

### 44.2 文献 23 的可用结论与禁止迁移

可用：

- 活动接触集合变化应作为离散事件；
- 分支脱离后剩余分支可能出现载荷阶跃；
- 在等刚度、同位移增量极限中可得到等增量换载基准。

禁止直接迁移：

- `F_7/6` 作为一般四单元规则；
- 论文的足数、砂纸目数、脱离阻力、刺几何或速度作为项目参数；
- 二维履带平衡替代偏心六维平衡；
- 原文下标冲突公式直接编码。

### 44.3 文献 28 的可用结论与禁止迁移

可用：

- 给定活动集的完整力/力矩平衡；
- 单爪 admissible 能力约束和最小裕度审计；
- 零净 wrench 与非零内部预紧可共存；
- 姿态适应会改变分支载荷。

禁止直接迁移：

- 常数 `f_min/f_max/theta_max/phi_max`；
- 被动腕、外张 carriage 和 DIG 数值；
- 任一 carriage 反向即整体失败的保守简化；
- 固定活动集 LP 代替渐进失效和 DamageStore；
- 文献有姿态适应就视为 B 已认证 rocking。

### 44.4 GPT 通用知识的实际使用

本轮使用的通用知识包括：

- 历史相关本构/接触响应应由状态和事件路径共同定义；
- 非光滑系统用事件括区间、一侧状态和分支句柄避免跨事件外推；
- 准静态峰后路径可在位移控制下继续存在；
- 代数根、局部稳定性、可恢复性和数值收敛必须分开；
- 非光滑峰可用左右割线/一侧导数和区间定位；
- 原子事务保证多单元、DamageStore、事件和峰值账本同时可见；
- 配对样本和独立批次用于比较方向和设计趋势。

这些方法不提供项目专属阈值、材料常数、加载速度或能力数值。

### 44.5 仍未关闭的参数和接口

| 未决项 | 当前接口/安全状态 | 关闭条件 |
|---|---|---|
| B 全 twist/局部 y/姿态合同 | `C3_CONTRACT_EXTENSION_REQUIRED` | B 2.x 实现、接受和验证 |
| 真实法向执行器端点/作用线/系统边界 | `ACTUATOR_WRENCH_UNCERTIFIED` 或 model-only | CAD/机构绑定与功测试 |
| `eta_i` 是否自由 | 版本化模式，默认 unavailable | 机构自由度与控制确认 |
| rocking 小角度/姿态 trust region | 无默认值 | 几何误差、B 验证、实验标定 |
| 显著退化通道、阈值和尺度 | `unit_degradation_policy_id` | 仿真、实验和统计审查 |
| 峰值位移/反力容差与平台定义 | `peak_policy_id` | 步长收敛和噪声分析 |
| 分支探索/选择政策 | `branch_continuation_policy_id` | 非唯一基准与物理选择验证 |
| 事件/同时事件/损伤 fixed-point 容差 | 配置 ID | 数值收敛和顺序不变性测试 |
| 稳定性长度尺度和容差 | 配置 ID | 解析基准和一侧扰动验证 |
| 材料、表面、摩擦、损伤参数 | 上游参数包或 unavailable | 文献、测量和实验标定 |
| C3 偏心加载速度 | unavailable | 实验协议或工程事实审批 |
| 目标实验误差范围 | `UNRESOLVED.VALIDATION.ERROR_TOLERANCE` | 重复实验和统计方案 |
| 代码/实验通过状态 | 当前仅定义测试 | 实现和实际测试后更新 |

### 44.6 关闭未决项的一般规则

- 缺失阈值不得以论文值、整数百分比或“常用值”补齐；
- 缺失 B 运动不得用坐标旋转、投影或旧切线替代；
- 缺失材料/表面参数时保留参数化和不确定性；
- 未通过实现测试的理论验证不得写成“已通过”；
- 新证据若要改变工程事实，必须走独立候选、schema 映射和人工审批流程。

## 45. C3 最低验证矩阵

> 当前状态：以下测试的理论输入、预期结果和失败语义已定义；没有 B 2.x、C3 求解器或目标实验，因此不声称实现/实验已通过。

| 编号 | 测试 | 构造输入 | 必须检查的结果 |
|---:|---|---|---|
| C3-V01 | C2 无损继承 | 首次 C3 调用 | `s_stop`、`delta_P`、`q_C`、四个 B/A states、DamageStore、事件、行程、功和收据均不重置。 |
| C3-V02 | 偏心压紧/剥离符号 | `+X`、`45°` 简化对称状态 | 外矩、rocking 法向位移和成对法向力矩符号与 C2 一致。 |
| C3-V03 | 主动推力唯一所有权 | 四个不同 `P_i` | `P_i` 不与 contact-only wrench 重复；实际接触合力可变化。 |
| C3-V04 | 首针不等于单元失败 | 一针材料失效、其余针仍承载 | 只记录针事件，完整 B/四单元重平衡后单元仍可稳定。 |
| C3-V05 | 单元显著退化事件 | 事件函数跨零；另构造缺阈值 | 前者定位并记录；后者返回 uncertified，不默认百分比。 |
| C3-V06 | 文献 23 等刚度极限 | 等刚度、固定姿态、同增量 | 失去一个分支后剩余分支增量方向/等分基准一致；非等刚度时结果不同。 |
| C3-V07 | 拒绝经验分配 | 均分、邻接权重、固定矩阵方案 | 接口/测试明确拒绝，不进入正式结果。 |
| C3-V08 | 低维 trust region | 事件外小增量与完整 B 对照 | 局部切线/graph 与有限差分/一侧割线一致；跨事件强制回调。 |
| C3-V09 | 全局最早事件缩步 | 任一针/单元/整体事件先触发 | 目标拒绝，四单元从同一 accepted state 重调；旧 wrench/姿态/损伤不缩放。 |
| C3-V10 | 同时事件与调用顺序 | 跨单元括区间重叠；置换枚举顺序 | 原组保留并形成全局组；接受结果相同或返回同一非唯一集合。 |
| C3-V11 | 共享损伤 fixed point | 跨单元写—写、写—读、核重叠 | 联合协调，不按调用顺序覆盖；改变后重调受影响单元。 |
| C3-V12 | 同位置级联 | `d delta_P=0`、姿态/接触/DamageStore 变化 | 继续重平衡；加载功与执行器/内部能量正确分栏。 |
| C3-V13 | 四单元重平衡 | 单元 1 退化 | 单元 2–4、整体姿态和 `lambda_P` 全部更新；不能只重算单元 1。 |
| C3-V14 | 无隐藏支承 | 退化后 contact-only 无法闭合外载 | 返回无平衡/未认证，不添加导轨、固定姿态或 yaw 反力。 |
| C3-V15 | 局部能力对象失效 | 固定活动集复算后触发事件 | 事件前最小裕度可复算；事件后旧能力对象立即失效并重建。 |
| C3-V16 | 稳定峰值定位 | 平滑峰、尖峰、平台、多峰 | 正确分类、定位和保存；步长收敛后能力不发生不可解释跳变。 |
| C3-V17 | 峰后稳定分支 | 首峰后稳定下降 | 继续位移加载，不提前终止。 |
| C3-V18 | 再平衡二次峰/再挂接 | 峰后事件生成新稳定分支 | 保留原始下降和二次峰，不用单调包络覆盖。 |
| C3-V19 | 无平衡/失稳/数值分离 | 无根、根不稳定、Newton 失败 | 分别触发不同状态；数值失败不冒充物理结论。 |
| C3-V20 | 可恢复/不可恢复脱附 | 当前失载但有/无合法再挂接路径 | 前者继续；后者只有证据闭合后物理终止。 |
| C3-V21 | 合同覆盖审计 | B 1.0 遇局部 y/姿态更新 | 返回扩展要求并保留最后状态；旋转旧 wrench/仅 x-z 投影失败。 |
| C3-V22 | 原子提交故障注入 | 任一 prepare/commit/持久化失败 | `delta_P`、姿态、四单元、DamageStore、事件和峰值账本全部不推进。 |
| C3-V23 | 作用—反作用与实验对齐 | 同一加载换报告对象 | 力和力矩同时反号，峰值幅值一致；位移零点绑定同一预紧初态。 |
| C3-V24 | 方向对称性 | 理想 D4 输入旋转 90° | 曲线、事件、临界状态和单元身份按旋转对应。 |
| C3-V25 | `+X/45°` 配对比较 | 同设计、配对表面/种子 | 输出四单元原始量、事件和峰后路径，不只比较总峰值。 |
| C3-V26 | 输出可复现性 | 同快照、配置、幂等键重复 | 同一曲线/收据或同一明确非唯一集合；无历史重复累计。 |

### 45.1 解析/构造检查

至少自动检查：

$$
\mathbf r_P\times(F\mathbf E_X)=50F\mathbf E_Y,
$$

$$
\mathbf r_P\times\frac{F}{\sqrt2}(\mathbf E_X+\mathbf E_Y)
=
\frac{50F}{\sqrt2}(-\mathbf E_X+\mathbf E_Y),
$$

$$
M_Y^{(1,2)}=40(F_{z1}-F_{z2}),
\qquad
M_X^{(3,4)}=40(F_{z4}-F_{z3}),
$$

$$
\Delta F_k=F_{\mathrm{lost}}/(N-1)
$$

只在等刚度特殊基准成立，以及 wrench–twist 功不变和 `P_i` 唯一所有权。

### 45.2 数值收敛检查

实现阶段应独立扫描：

- 加载步长、最小事件步长和括区间；
- 同时事件容差；
- 六维残量和 graph 容差；
- DamageStore fixed-point 容差/迭代上限；
- 姿态 trust region；
- 一侧稳定性扰动和尺度；
- 峰值位移/反力容差、平台窗口；
- 分支探索策略；
- 并行浮点归约顺序。

主要事件、里程碑、`F_max^obs`、`F_crit`、峰值位置、终止类型、DamageStore 和四单元临界分配应随数值设置收敛；不收敛时只能报告数值不确定，不能给物理结论。

### 45.3 表示一致性检查

同一物理状态在允许的坐标/参考点表达下应得到：

- 相同 C 点总 contact-only wrench；
- 相同功；
- 相同 `lambda_P` 和稳定性；
- 相同事件位置、里程碑和 `F_crit`；
- 仅分量表达随坐标变换改变。

## 46. C3 完成判据核对、已知风险与当前结论

### 46.1 完成判据核对

| 判据 | 本文件落点 | 当前结论 |
|---|---|---|
| 融合 C1+C2+C3 的最新完整上下文 | 全文；第 0、31–48 节 | 已经 `C3-r01` 审查接受。 |
| C2 历史无损继承 | 第 32 节 | 已定义，不重置任何历史。 |
| 偏心载荷到针级/单元/整体因果链 | 第 34 节 | 已闭合。 |
| 单元状态压缩保留历史和回调 | 第 33、40 节 | 已定义。 |
| 首针不等于单元/整体失败 | 第 35 节 | 已严格分离。 |
| 事件后四单元完整重平衡 | 第 36、37、41 节 | 已形成可执行流程。 |
| 禁止均分/权重/旧峰值 | 第 36.3 节 | 已明确。 |
| 显著退化参数化且不硬编码 | 第 35.3–35.4、44 节 | 已定义，阈值 unresolved。 |
| 稳定反力曲线、非光滑峰和多峰 | 第 38 节 | 已定义。 |
| `F_crit` 与候选峰分离 | 第 38.5–38.6 节 | 已定义。 |
| 峰后继续和物理终止分类 | 第 38.7–38.9 节 | 已定义。 |
| `+X/45°` 作用和比较边界 | 第 39 节 | 未未经求解排序。 |
| 事件/损伤/级联/事务闭环 | 第 37、41、42 节 | 已形成。 |
| 当前 B 缺口安全拒绝 | 第 0、33、41、44 节 | 保持明确。 |
| 实验输出和对齐 | 第 43 节 | 已定义。 |
| 验证矩阵 | 第 45 节 | 测试定义完成；未实现。 |
| 不提前执行 C 集成 | 第 47 节 | 边界保持。 |

### 46.2 已知模型和实现风险

1. B 2.x 未存在，正式 `+X/45°` 在线曲线当前不可生成；
2. 单元显著退化依赖能力通道、尺度和阈值，错误配置会把普通事件升级为失败；
3. graph 非唯一、摩擦和损伤软化可能产生多个可达分支，分支探索不充分会低估 `F_crit`；
4. 稳定性只使用局部一侧信息时可能漏掉远处分支或有限扰动失稳；
5. DamageStore 跨单元 fixed point 可能非唯一或难收敛；
6. 作用线、自由力偶和真实法向执行器边界若处理错误，会产生隐藏支承或重复载荷；
7. 峰值和事件接近时，位移/反力误差会影响候选排序；
8. 表面随机性和方向相关性可能使样本量要求较高；
9. 文献 23/28 均不提供本项目材料、表面或逐针历史参数；
10. 当前无代码和目标实验，任何“通过”结论都不成立。

### 46.3 当前可给出的结论

- C3 理论算子已经把针级事件、单元退化、四单元再平衡、稳定反力曲线和最终能力放入同一历史相关、事件驱动和原子提交框架；
- 整体最大承载不能由四个单元峰值相加，也不能由固定活动集常数 LP 直接给出；
- 首针失效、单元显著退化和整体峰值没有必然同位关系；
- 位移控制下首峰后仍可能存在稳定下降、再平衡、再挂接和二次峰；
- `+X` 与 `45°` 的优劣必须按配对初态和完整四单元历史求解，当前不得固定；
- 在 B 运动扩展完成前，正式 C3 请求只能安全拒绝，不能输出物理 `F_crit`。

## 47. 对大模块 C 集成的交接合同

### 47.1 C 集成可直接调用的对象

- `C1PreloadState` 与径向锁定 `s_stop`；
- `C2AcceptedState` 的刚体运动、加载点、六维平衡和稳定性；
- `C3AcceptedState`、`C3EventRecord`、`C3UnitContinuationCapsule`；
- `C3LocalWrenchCapability` 和完整 B 回调条件；
- 稳定反力曲线、峰值候选和 `C3MaximumCapacityResult`；
- 四单元/B/A/DamageStore 的原子事务和重放句柄；
- 当前 B 合同扩展要求和所有 unresolved 配置。

### 47.2 必须原样继承的定义

- 全局/单元坐标、`O_i`、`O_A`、wrench 方向和功共轭；
- `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1`；
- `P_i`、加载执行器和约束反力的所有权分栏；
- 唯一共同径向锁定；
- B 唯一无副作用物理入口；
- graph 非唯一、事件、DamageStore 和原子事务语义；
- 首针/单元退化/峰值/失稳/脱附的分离；
- 未认证状态不得改写为零承载或物理失败。

### 47.3 可以修改但必须显式版本化的内容

- B 2.x 完整 twist/姿态合同；
- 显著退化、峰值、稳定性和分支策略配置；
- 真实法向执行器/试验架系统边界；
- 求解器数值算法和数据存储实现；
- 实验协议、加载速度和统计方案。

任何修改必须声明对 C1/C2/C3 兼容性、状态迁移和重放的影响。

### 47.4 C 集成不得重新定义的低层机理

- A 层接触、摩擦、梁、弹簧、材料、损伤、释放和再挂接；
- B 层阵列活动集、逐针载荷共享、失效后重分配和单元级级联；
- C1 的同步搜索、停止和预紧历史；
- C2 的刚体/wrench/稳定性和无隐藏支承原则；
- C3 的事件后完整四单元重平衡和 `F_crit` 可达稳定分支定义。

### 47.5 集成阶段仍需完成

- 把 C1、C2、C3 状态和主状态码统一成一个大模块 C 公共算子；
- 审查重复字段、单位、参考点、事件层级和事务边界；
- 形成 C 对更高层/实验的公共合同；
- 在 B 2.x 可用后实现并执行验证矩阵；
- 完成数值收敛、故障注入和实验对比；
- 仅在独立集成任务中输出 `C_INTEGRATED_MODEL.md`。

本轮不得自动开始上述集成。

## 48. C3 输出前最终自检

- [x] 本文件为融合 C1+C2+C3 的最新完整上下文，不是 C3 增量。
- [x] 文件头写明 C3、版本 0.3.0、工程事实 1.0.0、B_TO_C 1.0.0、基线 0.2.0、运行 C3-r01 和 accepted。
- [x] `s_stop`、`delta_P`、整体位姿、四个 B/A states、DamageStore、事件、行程、功、哈希和收据未丢失或重置。
- [x] 偏心外载、rocking 和压紧/剥离符号与 C2 一致。
- [x] contact-only、`P_i`、加载执行器和约束反力未重复装配。
- [x] 单元压缩对象保留原始历史、graph、事件、trust region 和完整回调条件。
- [x] 首个针失效未升级为单元或整体失败。
- [x] 任一事件后四单元、姿态、反力和 DamageStore 都完整重求；未使用均分、邻接权重或旧峰值缩放。
- [x] 文献 23 只作等刚度特殊基准，文献 28 只作当前活动集裕度骨架。
- [x] 首针失效、单元显著退化、峰值候选、`F_crit`、物理无平衡、物理失稳和可恢复/不可恢复脱附已分离。
- [x] 首个反力下降不直接终止；稳定峰后分支、再挂接和多个峰被保留。
- [x] 未认证、模型/参数、域/碰撞、稳定性、数值和事务失败未冒充物理终止。
- [x] 当前 B 合同缺口明确；未旋转旧 wrench、仅投影 x/z 或用论文能力域伪装支持。
- [x] 事件定位、同时事件、共享损伤、同位置级联、稳定性和原子提交形成闭环。
- [x] `+X/45°` 比较保留四单元原始量、事件顺序和峰后路径，未固定优劣。
- [x] 实验输出保留连续量和事件，不定义未经批准的二元成功或综合评分。
- [x] 工程事实无变化，所有 C3 新内容保持在模块上下文。
- [x] 当前只声称理论和测试定义完成，不声称代码、B 2.x 或实验已通过。
- [x] 未自动开始大模块 C 集成或全局集成。

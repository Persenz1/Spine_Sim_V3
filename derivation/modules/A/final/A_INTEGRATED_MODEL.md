# A_INTEGRATED_MODEL — 大模块 A 正式集成模型

> 大模块：`A`  
> 模型版本：`1.0.0`  
> 工程事实版本：`engineering_fixed_context 1.0.0`  
> 输入上下文：`A_MODULE_CONTEXT 0.3.0 accepted`  
> 集成提示词版本：`1.0.0`  
> 运行：`A_INTEGRATION-r01`  
> 状态：`accepted`  
> 任务性质：单刺大模块一致性集成、可执行算法规范与 A→B 合同冻结；不包含求解器源代码

---

## 1. 范围、规范对象、权威输入与禁止越界

### 1.1 模型位置与唯一目标

物理依赖链固定为

\[
\boxed{
\text{SurfaceRealization/A1 查询}
\rightarrow
\text{单刺算子 A}
\rightarrow
\text{阵列爪单元算子 B}
\rightarrow
\text{十字对爪算子 C}.
}
\]

本文件把已接受的 A1、A2、A3 重构为一个状态闭合、符号唯一、事件可排序、功方向一致、事务可回滚的单刺对象。A 只负责一根针及其局部表面区域的几何、接触、结构、滑移、材料、损伤、针体强度、释放和再挂接；不求多针共同平衡、不分配每单元主动推力、不求十字对爪整体 wrench。

A 的两个正式层次为：

\[
\boxed{
\mathcal K_A^{\rm intrinsic}:
(T_B^n,\Delta q_B,\mathsf Z_A^n,\mathcal D^{\rm snap},
\mathcal Q_{A1},\Theta_A)
\mapsto
\mathcal R_A^{\rm trial}
}
\]

和

\[
\boxed{
\mathcal D_A^{\rm standalone}:
(\mathsf Z_{\rm drv}^n,\mathcal K_A^{\rm intrinsic},
P_z=0.5\ {\rm N},\Delta u_x)
\mapsto
(\mathsf Z_{\rm drv}^{n+1},\mathcal O_{\rm trajectory}).
}
\]

- `intrinsic_single_spine_kernel` 接受规定基座位姿/增量，返回本征试探 wrench、状态、事件、切线/割线、损伤意图和质量诊断；它是 B 的唯一入口。
- `standalone_single_spine_driver` 在本征核外施加单刺 \(0.5\ \mathrm N\) 法向主动推力、搜索控制、预载同伦和连续 \(100\ \mathrm{mm}\) 路径；它只用于 A 层验证与单刺实验对比。

### 1.2 权威输入与冲突顺序

本模型只使用下列三份输入：

1. `engineering_fixed_context 1.0.0`：固定事实、范围、集合、开关、接口能力、排除项和未决登记的最高权威；
2. `A_MODULE_CONTEXT 0.3.0 accepted`：A1–A3 已接受机理、方程、证据边界、验证风险和未决问题的唯一机理输入；
3. `A_INTEGRATION_PROMPT 1.0.0`：本轮分层、集成、合同和输出要求。

若定义冲突，按上述顺序处理。通用坐标变换、残量装配和事务表达属于本轮集成推导，不升级为新的工程事实。任何尚未固定的数值均保留参数 ID、候选模型 ID 或 `unavailable`，不得硬编码。

### 1.3 工程固定边界

- 墙面名义平面为全局 \(X\)-\(Y\)，\(+Z\) 指向背板和自由空间。
- 单元局部 \(+x\) 从头部指向根部，也是搜索与拖拽方向；\(\mathbf e_y=\mathbf E_Z\times\mathbf e_x\)。
- 只有局部球形针尖承载；锥段、针杆、安装座只做禁止碰撞。
- \(R_t\in\{0.05,0.10\}\ \mathrm{mm}\)，\(d\in\{0.6,0.8\}\ \mathrm{mm}\)，固定角单针球心露出长度 \(L_e=4\ \mathrm{mm}\)。
- `needle_bending=off/on` 是正式开关；`off` 不关闭针体强度检查。
- 独立轴向弹簧 \(k_s\in[100,2000]\ \mathrm{N/m}\)，无预压、只压缩、\(0\le\delta_s\le4\ \mathrm{mm}\)，到限后为刚性硬限位。
- standalone 单刺主动推力固定 \(0.5\ \mathrm N\)；B 层每单元主动推力为 \(0.5\)–\(2\ \mathrm N\)，由 B 共同平衡。
- 拖拽速度 \(1\ \mathrm{mm/s}\) 只用于位移—时间映射；忽略惯性；路径上限 \(100\ \mathrm{mm}\)，脱离后不重置。
- 同一连续过程保留轻量不可逆损伤；新独立试验/新表面实现从无损开始；A1 原始几何不可被损伤重写。

### 1.4 首版排除项

本模型不包含显式裂纹扩展、碎屑/颗粒动力学、连续切削有限元、地形重网格化、针尖磨损、针杆/锥段分布承载、安装座内部真实结构有限元、导轨/框架柔性、惯性和冲击动力学、大角度脱落运动或复杂控制器。达到针体屈服/断裂、梁模型越界或纯球尖模型无效时，首版终止相应分支，不补造排除范围内的后续物理。

---

## 2. 集成决策与冲突消解

| 编号 | 重复或冲突 | 规范定义 | 对实现和下游的影响 |
|---|---|---|---|
| ID-01 | A2/A3 standalone 残量含 \(P_z=0.5\ \mathrm N\)，A3 又声明 B 可调用单刺残量 | \(P_z\) 只属于 `standalone_single_spine_driver`；`intrinsic_single_spine_kernel` 不组装针级恒法向力残量 | B 只收到位姿—wrench 本征响应；每单元 \(0.5\)–\(2\ \mathrm N\) 由 B 外层施加一次 |
| ID-02 | A1/A2/A3 各自把几何、力学、质量和失败混入“主状态” | 采用一个互斥主机械状态，接触运动、弹簧、材料、针体、质量/求解为正交子状态；事件为瞬时记录 | 状态组合闭合，数值失败不再被写成物理失效 |
| ID-03 | A1 支持查询与 A3 显式支持图表可能重复施加几何约束 | A1 是几何所有者；`query` 表示和 `chart` 表示二选一。图表方程替代同一支持的标量间隙查询，不与其重复装配 | 不会因“最近点 + 图表闭合”重复约束 |
| ID-04 | A2 中 \(\mathbf F_c\) 为墙对针，B 接口方向未冻结 | 内部 \(\mathbf f_j\) 保持“墙对针”；公共输出唯一为“单刺 A 对背板 B”的 wrench，准静态下等于接触 resultant 运输到背板参考点 | B 可直接装配，无隐式换号 |
| ID-05 | 接触合矩曾在针尖球心、梁根和背板参考点多处出现 | 内部按需要保留各参考点；公共参考点由请求声明，默认针基座/背板参考点 \(O_B\)，所有变换显式使用力矩运输公式 | B 不需要阅读 A 内部推导即可装配 |
| ID-06 | A2 的局部接触柔顺、梁柔顺、轴向弹簧可能被总斜率重复拟合 | 三者按物理位置串联、状态与能量独立；局部接触柔顺只能由扣除梁/弹簧/夹具后的局部试验标定 | 禁止用系统总斜率同时设置多个刚度 |
| ID-07 | A2 材料检查钩子与 A3 材料失效律重复 | A2 钩子仅提供接触结果量和针体内力；A3 是材料容量、软化、损伤和耗散的唯一所有者 | 材料失效只计算一次 |
| ID-08 | A3 损伤可能被理解为改写粗糙表面或降低摩擦/结构刚度 | DamageStore 是独立材料历史层；只缩减材料容量并记录材料耗散，不改 A1 几何、\(\mu\)、梁或弹簧 | 保证几何和耗散去重 |
| ID-09 | 针体屈服/断裂与墙面材料失效曾可能压缩成最小标量 | 两套约束和事件函数分别监控，在共同位置竞争；禁止无解释的 \(\min(F_{\rm wall},F_{\rm needle})\) | 可记录并发与先后，不丢失失效机理 |
| ID-10 | 复合针体碰撞可能被误认为材料失效或新接触 | 锥段、针杆、安装座碰撞为几何模型无效，固定优先级高于所有非致命事件，且不产生承载乘子 | 纯球尖模型立即终止 |
| ID-11 | 摩擦锥边界、支持迁移、材料启动都可能被误写为脱离 | 锥边界需一侧试探确认滑移；支持迁移可为滚动；材料启动/软化后必须完整重求平衡；释放需法向力/几何/平衡的一侧条件 | 状态转移不再由单一阈值触发 |
| ID-12 | 完全分离且 \(P_z>0\) 无静态平衡 | standalone 用受控几何搜索；embedded 只返回 `OPEN_RESPONSE`、零接触 wrench 和下一事件信息 | 不伪造分离态恒力平衡 |
| ID-13 | 全刚性分支可出现反力集合值，有限惩罚会伪造刚度 | 保留严格刚性分支；返回非唯一/集合值诊断、代表解和 opaque 约束图，切线状态为 `constraint_set_valued` | B 不能假定普通单值本构 |
| ID-14 | A3 单针试探与未来多针共享损伤提交可能顺序相关 | trial 只读快照并输出写意图；B 检测冲突，A 负责局部损伤律的联合试探，B 重求共同平衡并原子提交 | 多针调用顺序不得改变结果 |
| ID-15 | A1 数值缓存可能与物理历史混淆 | 缓存仅含 BVH、邻域、支持预测、Jacobians 和括区辅助；不进入 accepted history，不参与损伤/路径/耗散提交 | 回滚可丢弃缓存但必须恢复物理语义 |
| ID-16 | 弹簧回缩是否改变露出梁长存在两种实质拓扑 | 主线采用“弹簧位于梁根上游、梁长 \(L\) 固定”；若 CAD 证实固定出口回缩，则启用版本化 \(L(\delta_s)\) 分支 | 不混合两种拓扑，关闭条件为 CAD/实测 |
| ID-17 | 针弯曲关闭可能被误解为针体无内力或无限强 | `needle_bending=off` 只令 \(\boldsymbol\eta_b=0,U_b=0\)；接触 wrench 仍映射为截面内力并检查强度 | 刚性针仍可先屈服/断裂 |
| ID-18 | 释放回弹的储能可能被并入耗散 | 接触释放时梁、弹簧、接触可恢复能作为 `released_recoverable_energy` 单列；不计入摩擦或材料耗散 | 功平衡闭合且不虚增耗散 |

---

## 3. 唯一坐标、符号、单位、参考点和功方向

### 3.1 坐标基与变换

全局、单元、针和第 \(j\) 个接触局部基分别为

\[
\mathcal F_G=\{\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
\quad
\mathcal F_U=\{\mathbf e_x,\mathbf e_y,\mathbf E_Z\},
\]

\[
\mathcal F_N=\{\mathbf a,\mathbf b,\mathbf c\},
\quad
\mathcal F_{C_j}=\{\mathbf n_j,\mathbf t_{1j},\mathbf t_{2j}\}.
\]

针轴从安装座出口指向针尖球心：

\[
\boxed{
\mathbf a=
\cos\alpha\cos\beta\,\mathbf e_x+
\cos\alpha\sin\beta\,\mathbf e_y-
\sin\alpha\,\mathbf E_Z,
}
\]

规范上，\(\mathbf a_0\equiv\mathbf a\) 是未变形梁根与轴向弹簧的固定轴，\(\mathbf a_t\) 是梁转动后的当前针尖球冠轴。梁与弹簧的结构投影一律使用 \(\mathbf a_0\)；合法球冠查询使用 \(\mathbf a_t\)。

当前正式工况 \(\beta=0\)。旋转矩阵以列向量为目标基在全局中的表示：

\[
\mathbf R_{GU}=[\mathbf e_x\ \mathbf e_y\ \mathbf E_Z],
\quad
\mathbf R_{GN}=[\mathbf a\ \mathbf b\ \mathbf c],
\quad
\mathbf R_{GC,j}=[\mathbf n_j\ \mathbf t_{1j}\ \mathbf t_{2j}].
\]

同一参考点的 wrench 变换为

\[
\mathbf W^G=\operatorname{diag}(\mathbf R_{GF},\mathbf R_{GF})\mathbf W^F.
\]

### 3.2 间隙、力和作用—反作用

- \(g>0\)：分离；\(g=0\)：接触边界；刚性主线禁止 \(g<0\)。
- \(\mathbf n_j\) 从墙体指向针尖/自由空间。
- \(\mathbf f_j\) 是墙对针的力：

\[
\boxed{
\mathbf f_j
=\lambda_{n,j}\mathbf n_j+\mathbf T_j\boldsymbol\lambda_{t,j},
\qquad \lambda_{n,j}\ge0.
}
\]

- 针对墙为 \(-\mathbf f_j\)。
- 内部接触 resultant：

\[
\mathbf F_c=\sum_j\mathbf f_j,
\qquad
\mathbf M_c^{c_t}=\sum_j(\mathbf p_j-\mathbf c_t)\times\mathbf f_j.
\]

- 公共 A→B wrench 在背板参考点 \(O\) 处：

\[
\boxed{
\mathbf W_{A\to B}^{O}
=
\begin{bmatrix}
\mathbf F_c\\
\sum_j(\mathbf p_j-\mathbf r_O)\times\mathbf f_j
\end{bmatrix}.
}
\]

背板对 A 的接口 wrench 为其负值。

### 3.3 参考点变换

\[
\boxed{
\mathbf M^{O'}
=\mathbf M^O+(\mathbf r_O-\mathbf r_{O'})\times\mathbf F.
}
\]

参考点位移增量满足

\[
\Delta\mathbf r_{O'}
=\Delta\mathbf r_O+
\Delta\boldsymbol\theta\times(\mathbf r_{O'}-\mathbf r_O),
\]

从而总功不变。

### 3.4 单位与转换

| 量 | 内部单位 |
|---|---|
| 长度、位移、针尖半径、行程 | mm |
| 力 | N |
| 力矩 | N·mm |
| 时间 | s |
| 角度 | rad |
| 应力、弹性模量 | MPa \(=\mathrm{N/mm^2}\) |
| 平移刚度 | N/mm |
| 转动刚度 | N·mm/rad |
| 断裂能 | N/mm |
| 弹簧工程输入 | N/m，入核前除以 \(1000\) |
| 针尖工程输入 | \(\mu\mathrm m\)，入核前除以 \(1000\) |

所有角度必须带单位标签；度数进入三角函数前转为 rad。

### 3.5 离散功、储能和耗散

令 \(\Delta\boldsymbol\xi_B^O=[\Delta\mathbf r_O;\Delta\boldsymbol\theta_B]\)。embedded 模式中，背板输入 A 的功为

\[
\boxed{
\Delta W_{\rm in,A}^{\rm base}
=-(\mathbf W_{A\to B}^{O})_{\rm mid}^{\mathsf T}
\Delta\boldsymbol\xi_B^O.
}
\]

standalone 模式在只有 \(u_x,u_z\) 平移时，外执行器功为

\[
\boxed{
\Delta W_{\rm act}
=R_x^{\rm mid}\Delta u_x-P_z\Delta u_z,
\qquad P_z=0.5\ \mathrm N,
}
\]

且接受平衡上 \(\Delta W_{\rm act}=\Delta W_{\rm in,A}^{\rm base}\)。

统一离散功平衡为

\[
\boxed{
\Delta W_{\rm in,A}^{\rm base}
=
\Delta U_b+\Delta U_s+\Delta U_c
+\Delta D_f+\Delta D_m
+\Delta E_{\rm returned}
+\varepsilon_{\rm work}.
}
\]

其中

\[
\Delta D_f
=-\sum_j\boldsymbol\lambda_{t,j}^{\rm mid}\cdot
\Delta\mathbf s_j\ge0,
\]

\(\Delta D_m\ge0\) 为材料损伤耗散，\(\Delta E_{\rm returned}\ge0\) 是释放时离开已建模弹性储能的可恢复能预算。梁、弹簧和可选局部接触储能分别为 \(U_b,U_s,U_c\)。理想刚性法向约束、粘着约束、刚性安装锁定和硬限位在其相对约束方向零位移，因此不产生独立物理功。数值残差 \(\varepsilon_{\rm work}\) 必须单列，不能解释为耗散。

trial 和 rollback 不增加任何累计耗散；只有 commit 后 \(\Delta D_f,\Delta D_m\) 才进入历史。

---

## 4. 规范数据对象、状态所有权与历史变量

### 4.1 规范对象表

| 对象 | 物理/程序所有者 | 坐标与单位 | 可变性 | 读取/试探/提交 | B 可见性 |
|---|---|---|---|---|---|
| `SurfaceRealization` | A1 表面层 | 全局或可映射表面坐标；mm | 不可变 | 构造后只读；新试验创建新对象 | ID、质量、域、版本可见；原始数据不可改 |
| `A1QueryHandle` | A1 | 返回全局几何量 | 逻辑只读；内部缓存可变 | 每次残量评估读取；缓存不提交 | 句柄可传递，不可解析/改写 |
| `CompositeNeedleGeometry` | A 参数层 | 针/基座坐标；mm、rad | 不可变版本 | 所有 trial 读取 | ID、关键尺寸、版本可见 |
| `SpineParameterBundle` | A 参数层 | N、mm、MPa 等 | 不可变版本 | 所有 trial 读取 | 参数 ID、证据状态可见 |
| `AcceptedSingleSpineState` | A | 声明参考点/坐标 | 仅原子提交后变化 | evaluate 只读；commit 生成新版本 | opaque 快照和摘要可见 |
| `ReversibleMechanicalState` | A 内部力学层 | 全局/针/接触坐标 | trial 可变、可回滚 | Newton 中修改；接受后写入 | 结果摘要可见 |
| `IrreversibleSpineHistory` | A 历史层 | 路径 mm、时间 s、耗散 N·mm | 只可单调/按规则更新 | trial 仅预览；commit 才增加 | 版本、摘要、增量可见 |
| `DamageStore` | A 材料层，B 调度共享事务 | 固定表面材料坐标 | accepted 版本不可变；新版本原子生成 | trial 读快照/写意图；B 冲突重求；批量提交 | 快照 ID、读写集合、冲突签名可见 |
| `TrialSnapshot` | A 事务层 | 与 accepted 状态一致 | 不可变 | 调用开始冻结 | opaque |
| `TrialStateHandle` | A 事务层 | 无物理单位 | 临时 | 绑定请求和快照；不可提交两次 | opaque |
| `RollbackToken` | A 事务层 | 无 | 一次试探有效 | 放弃/失败时使试探失效 | opaque |
| `CommitIntent/CommitToken` | A 事务层，B 决定时机 | 无 | intent 可升级；token 一次性 | 全局接受后批量准备与原子提交 | opaque + 状态 |
| `StandaloneDriverState` | A standalone driver | \(u_x,u_z\)、s、N | accepted 步更新 | 管理搜索、同伦、行程和循环 | 不属于 B 公共接口 |
| `NumericalCache` | A 内部 | 任意数值表示 | 可丢弃 | 可在 trial 中更新，不纳入 commit | 不可见 |

### 4.2 复合针几何与参数包

最低几何字段：

```text
TipGeometry:
  Rt
  cap_blend_coordinate_zeta_b
  axis_definition(alpha, beta)
  geometry_version

NeedleBodyGeometry:
  diameter_d
  exposed_length_L_or_topology
  cone_length_or_CAD
  cone_half_angle_or_derived_value
  shaft_geometry
  mount_geometry
  clearances_by_part
  root_reference_and_offsets
```

最低物理参数分组：

```text
ContactParameters:
  friction_model_id / mu
  local_normal_compliance_model_id
StructureParameters:
  mount_mode
  spring_stiffness / spring_limit
  needle_bending
  beam_model_id / E / nu / root_compliance_model_id
MaterialParameters:
  material_adapter_id
  patch_area / control_depth / damage_kernel
  initiation_domain / softening / fracture_energy / residual_capacity
NeedleStrengthParameters:
  grade_or_batch_id / yield / fracture / stress_concentration_model
NumericalParameters:
  residual_scaling / event / support / convergence / loop limits
```

任何缺失字段必须显式标记，不得由代码私有默认值补齐。

### 4.3 已接受单刺状态

\[
\mathsf Z_A
=
(\mathsf Z_{\rm mech},
\mathsf H_{\rm irr},
\mathsf Q_{\rm solve},
v_{\rm state}).
\]

`ReversibleMechanicalState` 至少包括：

```text
base_pose
tip_pose
active_supports / feature_charts
contact_forces / gaps / tangent_frames
beam_translation / rotation / current beam model
spring_compression / state / reactions
optional_contact_compressions
current material utilization (not accumulated history)
current needle section resultants and margins
branch_id / tangent_status / local Jacobian diagnostics
```

`IrreversibleSpineHistory` 至少包括：

```text
total_path_x / physical_time / remaining_travel
contact_cycle_id / event_sequence_number
cycle_start / search / preload / stick / slide distances
accumulated_slip_length_by_support_or_material_region
DamageStore accepted version reference
material_dissipation / friction_dissipation
completed PeakRecords
last accepted events and simultaneous event set
```

路径、时间、累计滑移、损伤、耗散、循环和事件序号只在 commit 时增加。释放可使梁/弹簧可逆变量回零，但不可逆历史不回退。

### 4.4 DamageStore

每个损伤面片采用固定表面材料坐标键：

```text
DamagePatchKey:
  surface_realization_id
  material_frame_id
  anchor_position
  kernel_radius_and_version
  creation_cycle_and_event_id
  source_feature_ids_for_traceability
```

面片历史至少含 \(D,\delta_d,\delta_f,\rho,q\)、起始牵引/应力代理、模式、耗散、参数版本和不确定性。A1 表面几何不包含这些字段，也不因其变化而重建。

---

## 5. 统一几何—接触—结构—滑移—材料—损伤方程链

### 5.1 SurfaceRealization 与 A1 查询

A1 接受高度场、完整三角网格或共享接口的混合后端。表面配置必须保存材料标签、坐标、有效域、质量掩膜、可信波数带、测量/生成元数据、随机种子和不确定性。

二维高度 PSD 约定为

\[
C_h(\mathbf q)
=\int R_h(\mathbf r)e^{-i\mathbf q\cdot\mathbf r}\,d^2\mathbf r,
\qquad
\langle h^2\rangle
=\frac{1}{(2\pi)^2}\int C_h(\mathbf q)\,d^2\mathbf q.
\]

只在显式可信带 \(\mathcal B_{\rm trust}\) 内解释表面尺度。红砖、混凝土和砂纸可使用不同参数化后端，但必须通过同一查询接口进入 A；上层不得按材料类别复制接触几何。

对高度场实体 \(\Omega_h=\{z\le h(x,y)\}\)，完整球的最低球心高度为

\[
\boxed{
H_R(x_c,y_c)
=
\sup_{\rho\le R}
\left[
h(u,v)+\sqrt{R^2-\rho^2}
\right].
}
\]

跨后端统一使用欧氏有符号间隙。对实体 \(\Omega\)：

\[
g_R^{(d)}(\mathbf c)=\phi_\Omega(\mathbf c)-R.
\]

真实承载部位是暴露球冠。合法支持点必须满足

\[
(\mathbf p_j-\mathbf c_t)\cdot\mathbf a_t
\ge \zeta_b-\epsilon_{\rm cap}.
\]

A1 返回合法球冠间隙 \(g_t\)、支持点 \(\mathbf p_j\)、径向法向

\[
\boxed{
\mathbf n_j
=\frac{\mathbf c_t-\mathbf p_j}
{\|\mathbf c_t-\mathbf p_j\|}
}
\]

和所有多支持/非光滑信息。若支持唯一且光滑，径向法向与原表面外法向一致；多支持时保留全部法向，不平均成伪法向。对局部 \(+x\) 拖拽的几何方向裕度为

\[
\boxed{
\eta_{x,j}=-\mathbf n_j\cdot\mathbf e_x,
\qquad
\eta_{\max}=\max_j\eta_{x,j},
\quad
\eta_{\min}=\min_j\eta_{x,j}.
}
\]

`candidate_any` 只要求 \(\eta_{\max}\) 超过数值裕度，`candidate_robust` 要求 \(\eta_{\min}\) 超过数值裕度；二者都只是几何必要标签，不是摩擦稳定、材料安全或抓附成功。

接触切向基优先取

\[
\mathbf t_{1j}
=
\frac{(\mathbf I-\mathbf n_j\mathbf n_j^{\mathsf T})\mathbf e_x}
{\|(\mathbf I-\mathbf n_j\mathbf n_j^{\mathsf T})\mathbf e_x\|},
\qquad
\mathbf t_{2j}=\mathbf n_j\times\mathbf t_{1j}.
\]

若投影退化，使用与 \(\mathbf n_j\) 最不平行的固定全局轴构造确定性基，并记录退化处理。

锥段、针杆和安装座部件 \(K_k\) 的净安全间隙为

\[
\boxed{
g_k(T)
=
\min_{\mathbf x\in K_k(T)}\phi_\Omega(\mathbf x)
-\delta_{{\rm clr},k},
\quad
k\in\{\rm cone,shaft,mount\}.
}
\]

这些间隙是硬不等式，不产生承载乘子。

A1 每次查询必须返回 `status`、数值、容差、质量、不确定性和表面 ID。`OUT_OF_DOMAIN` 或 `GEOMETRY_UNCERTAIN` 不得被后续力学覆盖。

### 5.2 基座、弹簧、梁和针尖运动学

设声明背板参考位姿为 \(T_B\)，刚性几何给出的梁根基准位置为 \(\mathbf r_{0,\rm rigid}(T_B)\)。主线轴向弹簧位于梁根上游：

\[
\boxed{
\mathbf r_0
=\mathbf r_{0,\rm rigid}(T_B)-\delta_s\mathbf a_0.
}
\]

未弯曲针尖球心为

\[
\mathbf c_0=\mathbf r_0+L\mathbf a_0.
\]

当 `needle_bending=on`：

\[
\boxed{
\mathbf c_t=\mathbf c_0+\mathbf u_b,
\qquad
\mathbf R_t=\mathbf R_0\exp([\boldsymbol\theta_b]_\times),
\qquad
\mathbf a_t=\mathbf R_t\mathbf a_0.
}
\]

`needle_bending=off` 时 \(\mathbf u_b=\boldsymbol\theta_b=\mathbf0\)，但接触 resultant 仍传到根部并进入针体强度检查。

A1 的合法球冠和体碰撞查询必须使用变形后的球尖姿态以及梁中心线/复合针体的当前几何；不能只旋转一个刚性针尖而忽略弯曲针杆。

### 5.3 单边接触、局部接触柔顺和三维 Coulomb 摩擦

刚性局部接触主线：

\[
g_j^{\rm geom}\ge0,
\qquad
\lambda_{n,j}\ge0,
\qquad
g_j^{\rm geom}\lambda_{n,j}=0.
\]

若启用独立标定的局部法向压缩 \(c_{n,j}(\lambda_{n,j})\ge0\)：

\[
\boxed{
g_j^{\rm eff}
=g_j^{\rm geom}+c_{n,j}(\lambda_{n,j}),
\qquad
c_{n,j}(0)=0,
\quad
\frac{dc_n}{d\lambda_n}\ge0.
}
\]

局部接触储能为

\[
U_{c,j}
=\int_0^{c_{n,j}}\lambda_{n,j}(\zeta)\,d\zeta.
\]

摩擦锥为

\[
\mathcal K_{\mu_j}
=
\{(\lambda_n,\boldsymbol\lambda_t):
\lambda_n\ge0,\ 
\|\boldsymbol\lambda_t\|\le\mu_j\lambda_n\}.
\]

定义

\[
\boldsymbol\chi_j=
\begin{bmatrix}
\mu_j\lambda_{n,j}\\
\boldsymbol\lambda_{t,j}
\end{bmatrix},
\qquad
\boldsymbol\psi_j=
\begin{bmatrix}
g_j^{\rm eff}/\mu_j+\|\Delta\mathbf s_j\|\\
\Delta\mathbf s_j
\end{bmatrix}.
\]

对 \(\mu_j>0\)：

\[
\boxed{
\boldsymbol\chi_j\in\mathcal L_3,
\qquad
\boldsymbol\psi_j\in\mathcal L_3,
\qquad
\boldsymbol\chi_j^{\mathsf T}\boldsymbol\psi_j=0.
}
\]

半光滑投影残量：

\[
\boxed{
\mathbf r_{c,j}
=
\boldsymbol\chi_j-
\Pi_{\mathcal L_3}
(\boldsymbol\chi_j-\rho_j\boldsymbol\psi_j)
=\mathbf0.
}
\]

\(\rho_j\) 只用于数值尺度，不是物理刚度。若 \(\mu_j=0\)，显式退化为 \(\boldsymbol\lambda_t=\mathbf0\) 和标量 Signorini 互补。

真实滑移时

\[
\boxed{
\boldsymbol\lambda_{t,j}
=
-\mu_j\lambda_{n,j}
\frac{\Delta\mathbf s_j}{\|\Delta\mathbf s_j\|},
}
\]

并满足最大耗散。锥边界

\[
m_j=\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|=0
\]

本身不等于滑移；必须先求规定增量方向的一侧全粘着问题。

### 5.4 梁柔顺

圆截面：

\[
A=\frac{\pi d^2}{4},
\quad
I=\frac{\pi d^4}{64},
\quad
J=\frac{\pi d^4}{32},
\quad
G=\frac{E}{2(1+\nu)}.
\]

令 \(\mathbf P_\parallel=\mathbf a_0\mathbf a_0^{\mathsf T}\)、\(\mathbf P_\perp=\mathbf I-\mathbf P_\parallel\)、\(\mathbf S=[\mathbf a_0]_\times\)。针尖截面 wrench 为 \(\mathbf W_c=[\mathbf F_c;\mathbf M_c^{c_t}]\)。线性 Euler–Bernoulli 柔顺为

\[
\boxed{
\begin{aligned}
\mathbf u_b={}&
\frac{L}{EA}\mathbf P_\parallel\mathbf F_c
+\frac{L^3}{3EI}\mathbf P_\perp\mathbf F_c
-\frac{L^2}{2EI}\mathbf S\mathbf M_c^{c_t},\\
\boldsymbol\theta_b={}&
\frac{L^2}{2EI}\mathbf S\mathbf F_c
+\frac{L}{EI}\mathbf P_\perp\mathbf M_c^{c_t}
+\frac{L}{GJ}\mathbf P_\parallel\mathbf M_c^{c_t}.
\end{aligned}
}
\]

写为

\[
\boxed{
\mathbf r_b
=
\boldsymbol\eta_b-\mathbf C_b\mathbf W_c
=\mathbf0,
\qquad
U_b=\frac12\mathbf W_c^{\mathsf T}\mathbf C_b\mathbf W_c.
}
\]

若 \(L/d\)、剪切挠度、转角、轴向压缩或几何刚度指标超过已验证范围，返回 `STRUCTURAL_MODEL_OUT_OF_RANGE` 或切换显式版本化 Timoshenko/共回转分支；不得继续使用失效切线。

### 5.5 轴向弹簧与硬限位

压缩广义力：

\[
\boxed{
Q_s=-\mathbf a_0\cdot\mathbf F_c.
}
\]

弹簧输入刚度转为 N/mm 后：

\[
F_s=k_s\delta_s,
\qquad
U_s=\frac12 k_s\delta_s^2.
\]

规范分支：

- `RIGID_LOCKED`：\(\delta_s=0\)，锁定反力可为任意符号；
- `AT_ORIGINAL_LENGTH`：\(\delta_s=0,F_s=0\)，承载平衡需 \(Q_s=0\)；若下一侧需 \(Q_s<0\)，释放接触，不允许拉力；
- `COMPRESSING`：

\[
\boxed{
0<\delta_s<\delta_{\max},
\qquad
r_s=Q_s-k_s\delta_s=0;
}
\]

- `HARD_STOP`：

\[
\boxed{
\delta_s=\delta_{\max}=4\ {\rm mm},
\quad
r_s=Q_s-k_s\delta_{\max}-r_H=0,
\quad
r_H\ge0.
}
\]

硬限位后的切线轴向柔顺为零；达到硬限位不自动等于失败，只有后续平衡不可行或体碰撞才失败。

### 5.6 接触迁移、滚动和滑移

A1 是支持几何所有者。每个支持可采用两种等价内部表示：

1. **查询表示**：A1 直接返回 \(g_j,\mathbf p_j,\mathbf n_j\)，不把支持坐标作为未知量；
2. **图表表示**：在光滑表面引入 \(\boldsymbol\xi_j=(\xi^1,\xi^2)\)，以最近点/支持驻定条件

\[
\boxed{
\mathbf r_{{\rm geo},j}
=
\begin{bmatrix}
\mathbf p_{,1}^{\mathsf T}(\mathbf c_t-\mathbf p)\\
\mathbf p_{,2}^{\mathsf T}(\mathbf c_t-\mathbf p)
\end{bmatrix}
=\mathbf0
}
\]

确定支持坐标，并计算

\[
\boxed{
g_j^{\rm geom}
=
\mathbf n(\boldsymbol\xi_j)^{\mathsf T}
[\mathbf c_t-\mathbf p(\boldsymbol\xi_j)]
-R_t.
}
\]

\(g_j^{\rm eff}=g_j^{\rm geom}+c_{n,j}(\lambda_{n,j})\) 只在 SOC/Signorini 块中出现一次。活动接触时等价的三维闭合

\[
\mathbf c_t-\mathbf p-(R_t-c_n)\mathbf n=\mathbf0
\]

只作为几何一致性诊断，或在另一实现中整体替换“两个驻定方程 + 一个法向间隙条件”；不得与 SOC 法向互补同时重复装配。开放候选仍由 A1 间隙互补处理。

配置空间切向 Jacobian

\[
\mathbf A_r
=
[\mathbf p_{,1}+r\mathbf n_{,1}\ \ 
 \mathbf p_{,2}+r\mathbf n_{,2}],
\quad r=R_t-c_n
\]

的最小奇异值用于监控迁移退化。三角网格使用面—边—顶点图表及 A1 精确最近特征，不使用平均顶点法向。面、边、顶点图表分别增加与其自由参数维数相同的驻定/边界方程。

客观滑移增量：

\[
\boxed{
\Delta\mathbf s_j^G
\approx
\mathbf P_{t,j}^{n+1/2}
\left[
\Delta\mathbf c_t+
\Delta\boldsymbol\theta_t\times
(\mathbf p_j-\mathbf c_t)^{n+1/2}
\right],
}
\]

\[
\Delta\mathbf s_j
=\mathbf T_{j,n+1/2}^{\mathsf T}\Delta\mathbf s_j^G.
\]

支持坐标改变但 \(\Delta\mathbf s_j=\mathbf0\) 为 `ROLLING_NO_SLIP`；只有非零客观相对切向增量才提交滑移和摩擦耗散。切向基变化时历史向量做最小旋转/平行传输；长期累计只使用无歧义弧长。

### 5.7 局部材料容量与损伤

一个物理损伤面片 \(k\) 具有面积 \(A_k=\pi a_k^2\)、控制深度 \(\ell_k\)、核半径 \(r_{D,k}\)、材料方向和参数 \(\Theta_k\)。支持力先按归一化核权重汇聚，保证每个接触结果量只分配一次：

\[
\sum_{k\in\mathcal P(j)}w_{kj}=1,
\]

\[
\mathbf F_k^w=-\sum_jw_{kj}\mathbf f_j,
\qquad
\mathbf M_k^w=-\sum_jw_{kj}
(\mathbf p_j-\mathbf x_k)\times\mathbf f_j.
\]

相对面片法向 \(\mathbf n_k\)，取

\[
N_k=-\mathbf n_k\cdot\mathbf F_k^w\ge0,
\qquad
\mathbf T_k=-(\mathbf I-\mathbf n_k\mathbf n_k^{\mathsf T})\mathbf F_k^w,
\]

从而 \(\mathbf F_k^w=-(N_k\mathbf n_k+\mathbf T_k)\)。

接触合矩保持为独立广义应力量：

\[
\mathbf q_{M,k}=\frac{\mathbf M_k^w}{A_k\ell_k}.
\]

只有存在独立力矩容量标定时才启用

\[
r_{M,k}=\mathcal G_M(\mathbf q_{M,k};\Theta_{M,k}),
\qquad
\Phi_{M,k}=r_{M,k}-1,
\]

其中 \(\mathcal G_M\ge0\) 为无量纲利用率。没有相应标定时，`moment_augmented` 分支关闭，\(\Phi_{M,k}\) 不进入首次失效面的最大值。

压缩 \(N_k\) 和切向量 \(\mathbf T_k\) 形成有限控制体应力代理：

\[
\boxed{
\bar{\boldsymbol\sigma}_k^F
=
-\frac{N_k}{A_k}\mathbf n_k\otimes\mathbf n_k
-\frac{1}{A_k}
(\mathbf T_k\otimes\mathbf n_k+
 \mathbf n_k\otimes\mathbf T_k).
}
\]

材料方向变换为

\[
\boldsymbol\sigma_k^m
=\mathbf R_{m,k}^{\mathsf T}\bar{\boldsymbol\sigma}_k^F\mathbf R_{m,k},
\qquad
\widehat{\boldsymbol\sigma}_k=\mathbb H_k:\boldsymbol\sigma_k^m,
\]

其中 \(\mathbb H_k\) 是经目标材料标定的正定方向变换；各向同性退化分支取 \(\mathbb H_k=\mathbb I\)。令 \(\widehat\sigma_{I,k}\ge\widehat\sigma_{II,k}\ge\widehat\sigma_{III,k}\)，拉为正、压为负。方向性/压力敏感 Mohr–Coulomb 和拉伸截断定义为

\[
\Phi_{MC,k}=\widehat\sigma_{I,k}\frac{1+\sin\phi_k}{2c_k\cos\phi_k}-\widehat\sigma_{III,k}\frac{1-\sin\phi_k}{2c_k\cos\phi_k}-1,
\qquad
\Phi_{t,k}=\frac{\langle\widehat\sigma_{I,k}\rangle}{f_{t,k}}-1.
\]

若目标材料数据证明需要高压压帽，则令

\[
p_k^{\rm cap}=-\frac13\operatorname{tr}\widehat{\boldsymbol\sigma}_k,
\qquad
\widehat{\mathbf s}_k=\widehat{\boldsymbol\sigma}_k+p_k^{\rm cap}\mathbf I,
\qquad
q_k^{\rm cap}=\sqrt{\frac32\widehat{\mathbf s}_k:\widehat{\mathbf s}_k},
\]

\[
\Phi_{c,k}=\left(\frac{p_k^{\rm cap}-p_{c,k}}{X_{c,k}}\right)^2+\left(\frac{q_k^{\rm cap}}{Y_{c,k}}\right)^2-1,
\qquad p_k^{\rm cap}\ge p_{c,k}.
\]

没有压帽标定时该分支关闭。主线首次失效域因此为

\[
\Phi_{{\rm init},k}
=\max(\Phi_{MC,k},\Phi_{t,k},\Phi_{c,k}\ {\rm if\ enabled},
\Phi_{M,k}\ {\rm if\ calibrated})\le0.
\]

令 \(\mathbf z_k=\boldsymbol\sigma_k^m\)；启用力矩容量时令 \(\mathbf z_k=(\boldsymbol\sigma_k^m,\mathbf q_{M,k})\)。将无损容量集合写为 \(\mathcal C_{0,k}=\{\mathbf z:\Phi_{{\rm init},k}(\mathbf z)\le0\}\)。若该集合关于原点星形，定义射线利用率

\[
\boxed{
r_k^0(\mathbf z_k)
=\inf\{\gamma>0:
\mathbf z_k/\gamma\in\mathcal C_{0,k}\}.
}
\]

材料模型选择必须显式为 `continuum_patch`、`resultant_capacity`、`no_damage` 或 `unavailable`；两个实质不同容量模型不能同时启用后简单取最小值。

不可逆软化坐标 \(\delta_{d,k}\) 满足

\[
\delta_{d,k}^{n+1}\ge\delta_{d,k}^{n}.
\]

容量系数中 \(0\le\rho_k<1\) 是待标定残余容量比：

\[
\boxed{
q_k(\delta_d)
=
\rho_k+(1-\rho_k)
\max\left(1-\frac{\delta_d}{\delta_{f,k}},0\right),
}
\]

\[
D_k=\min(\delta_{d,k}/\delta_{f,k},1),
\qquad
r_k^0\le q_k.
\]

一致性条件：

\[
\boxed{
\dot\delta_{d,k}\ge0,
\quad
q_k-r_k^0\ge0,
\quad
\dot\delta_{d,k}(q_k-r_k^0)=0.
}
\]

半光滑投影残量可写为

\[
\boxed{
r_{{\rm mat},k}
=
\Delta\delta_{d,k}
-\Pi_{\mathbb R_+}
\left[
\Delta\delta_{d,k}
+\rho_{d,k}(r_k^0-q_k)
\right]
=0.
}
\]

材料起始时冻结等效峰值牵引 \(T_{0,k}=\|\mathbf F_k^w\|/A_k\)、失效模式和经标定的混合模态断裂能 \(G_{c,k}^{\rm mix}\)；\(\delta_{d,k}\) 是与等效软化牵引功共轭的局部化位移，不是地形退缩。线性软化的断裂能正则化为：

\[
\boxed{
\delta_{f,k}
=
\frac{2G_{c,k}^{\rm mix}}
{(1-\rho_k)T_{0,k}},
}
\]

\[
\boxed{
\mathcal D_{m,k}(\delta_d)
=
A_k(1-\rho_k)T_{0,k}
\left(
\delta_d-\frac{\delta_d^2}{2\delta_{f,k}}
\right).
}
\]

完全软化时 \(\mathcal D_{m,k}=A_kG_{c,k}^{\rm mix}\)。面片物理尺寸不随几何网格自动缩小。损伤只缩减材料容量；不改 \(\mu\)、\(E\)、\(k_s\) 或原始地形。

### 5.8 针体强度

在针局部基中，令截面半径 \(R=d/2\)，根截面结果量为

\[
\mathbf s_N=[N,V_b,V_c,T,M_b,M_c]^{\mathsf T}.
\]

圆截面保守应力上界：

\[
\boxed{
\sigma_{ab,\max}
=\frac{|N|}{A}
+\frac{R}{I}\sqrt{M_b^2+M_c^2},
}
\]

\[
\tau_T=\frac{|T|R}{J},
\qquad
\tau_V=\frac{4}{3A}\sqrt{V_b^2+V_c^2},
\qquad
\tau_{\rm ub}=\tau_T+\tau_V,
\]

\[
\boxed{
\sigma_{\rm vm}^{\rm ub}
=\sqrt{\sigma_{ab,\max}^2+3\tau_{\rm ub}^2}.
}
\]

最大主拉应力上界为

\[
\boxed{
\sigma_1^{\rm ub}
=\frac12\left(
\sigma_{ab,\max}
+\sqrt{\sigma_{ab,\max}^2+4\tau_{\rm ub}^2}
\right).
}
\]

事件裕度：

\[
E_{N,y}=1-\frac{\sigma_{\rm vm}^{\rm ub}}{\sigma_y},
\qquad
E_{N,u}=1-\frac{\sigma_1^{\rm ub}}{\sigma_u}.
\]

达到屈服或断裂上限分别终止当前线弹性/单刺承载分支。强度参数缺失时返回未认证状态，不假定无限强。

### 5.9 本征核的唯一残量装配

固定支持图表、接触开闭、摩擦、弹簧和材料活动分支后，本征核未知量按启用分支组成：

\[
\mathbf y_{\rm intr}
=
[
\boldsymbol\eta_b,\ 
\delta_s\ {\rm or}\ r_H,\ 
\{\boldsymbol\lambda_j\},\
\{\boldsymbol\xi_j\}_{\rm chart},\
\{\Delta\delta_{d,k}\}_{\rm active}
].
\]

`needle_bending=off` 删除 \(\boldsymbol\eta_b\) 和梁残量；刚性安装删除弹簧未知量；开放支持不含图表坐标；硬限位用 \(r_H\) 替代可变 \(\delta_s\)。

规范残量为

\[
\boxed{
\mathbf R_{\rm intr}
=
\begin{bmatrix}
\mathbf r_b\\
\mathbf r_s\\
\{\mathbf r_{c,j}\}\\
\{\mathbf r_{{\rm geo},j}\}_{\rm chart}\\
\{r_{{\rm mat},k}\}_{\rm active}
\end{bmatrix}
=\mathbf0.
}
\]

其中：

- \(\mathbf r_b\) 仅为梁本构兼容；
- \(\mathbf r_s\) 仅为弹簧/硬限位平衡；
- \(\mathbf r_{c,j}\) 仅为单边接触和 Coulomb 最大耗散；
- \(\mathbf r_{\rm geo}\) 仅在显式图表表示中替代 A1 对该支持的间隙闭合；
- \(r_{\rm mat}\) 仅为材料不可逆容量更新。

**本征核不含**

\[
\mathbf E_Z\cdot\mathbf F_c-0.5\ \mathrm N=0.
\]

基座位姿和增量是规定边界，公共 wrench 为后处理接口反力。

硬不等式和终止检查：

\[
g_{\rm cone}>0,\quad
g_{\rm shaft}>0,\quad
g_{\rm mount}>0,
\]

\[
0\le\delta_s\le4\ {\rm mm},
\quad
E_{N,y}\ge0,\quad E_{N,u}\ge0
\]

（达到零即事件），以及 A1 质量、材料/结构模型适用性和所有不可逆变量单调性。

### 5.10 standalone 外包装残量

standalone 在本征核外增加法向位置 \(u_z\) 为外层未知量，并施加

\[
\boxed{
r_P
=\mathbf E_Z\cdot\mathbf F_{A\to B}-P_z=0,
\qquad P_z=0.5\ \mathrm N.
}
\]

切向 \(u_x\) 规定，反力

\[
R_x=-\mathbf e_x\cdot\mathbf F_{A\to B}.
\]

因此 attached/preload 状态的完整 standalone 问题为

\[
\boxed{
\mathbf R_{\rm stand}
=
[\mathbf R_{\rm intr};r_P]
=\mathbf0.
}
\]

在 `OPEN` 状态 \(\mathbf F=0\) 且 \(P_z>0\)，上述静态残量无解；driver 必须切换到第 6.3 节受控几何搜索，而不是把 \(P_z\) 赋给某个 \(\lambda_n\)。

### 5.11 分支未知量、方程数、硬约束和后处理反力

令：

- \(b=6\)（`needle_bending=on`）或 \(0\)；
- \(s=1\)（`COMPRESSING` 或 `HARD_STOP`）或 \(0\)；
- \(m\) 为进入本步 SOC/Signorini 块的支持数；
- \(c=\sum_j d_j\) 为显式支持图表参数总维数；查询表示时 \(c=0\)；
- \(a\) 为本步活动软化面片数。

局部接触压缩按 \(c_n(\lambda_n)\) 计算，不另设未知量；若未来采用显式牵引—分离坐标，必须成对增加同数目的兼容方程并升级模型 ID。

| 模式/分支 | 未知量数 | 等式/互补残量数 | 说明 |
|---|---:|---:|---|
| embedded attached，常规查询表示 | \(b+s+3m+a\) | \(b+s+3m+a\) | 梁、弹簧、每支持 3 维 SOC、每活动面片 1 个损伤残量 |
| embedded attached，显式图表表示 | \(b+s+3m+c+a\) | \(b+s+3m+c+a\) | 每个图表增加 \(d_j\) 个坐标及同数驻定/边界方程 |
| standalone attached/preload | 上述 \(+1\) | 上述 \(+1\) | 增加外层未知 \(u_z\) 和 \(r_P=0\) |
| 事件定位 | 对当前模式 \(+1\) | 对当前模式 \(+1\) | 增加事件分数 \(\alpha\) 和被定位事件方程；并发事件以共同 \(\alpha\) 评价，不为每个事件各加一个路径未知量 |
| embedded open | \(0\) 个承载未知量 | 无静态恒力方程 | A1 几何查询后返回零 wrench 和事件信息 |
| standalone open search | 搜索策略规定 | 几何事件括区 | 不组装 \(r_P\)，直到 `TIP_ZERO_LOAD` 后开始预载 |
| `AT_ORIGINAL_LENGTH` 瞬时边界 | 常规加载中作为事件定位分支 | \(\delta_s=0,Q_s=0\) 与事件路径共同闭合 | 不把原长端当作可承拉挡块 |
| 全刚性退化 | 形式上仍为 \(3m(+c+a)\) 方程/未知量 | Jacobian 可奇异 | 返回集合值/非唯一，而非加入隐藏惩罚 |

所有模式共同的硬不等式包括：合法球冠、体部正间隙、\(\lambda_n\ge0\)、摩擦锥、弹簧范围、损伤单调、针体裕度和模型适用性。它们不能通过删除方程或静默投影到伪可行值来满足。

后处理量不再作为局部未知量重复求解：

- 公共接口 wrench \(\mathbf W_{A\to B}^{O}\)；
- standalone 切向驱动力 \(R_x=-\mathbf e_x\cdot\mathbf F_{A\to B}\)；
- 刚性安装轴向锁定反力；
- 背板锁定 \(y\) 与转动方向的约束反力/力矩；
- 各参考点运输后的 resultant；
- 针体截面内力和强度裕度；
- 能量、耗散、事件分数和切线状态。

这些量由同一收敛解后处理，不能作为第二套平衡方程再次施加。

### 5.12 残量和质量必须分块报告

至少报告：

\[
\epsilon_{\rm beam}=\|\mathbf r_b\|,
\quad
\epsilon_{\rm spring}=|r_s|,
\quad
\epsilon_{\rm cone}=\max_j\|\mathbf r_{c,j}\|,
\]

\[
\epsilon_{\rm geo}
=\max_j\|\mathbf r_{{\rm geo},j}\|,
\quad
\epsilon_{\rm mat}=\max_k|r_{{\rm mat},k}|,
\]

\[
\epsilon_{\rm gap}=\max_j[-g_j^{\rm eff}]_+,
\quad
\epsilon_{\rm friction}
=\max_j[\|\boldsymbol\lambda_{t,j}\|-\mu_j\lambda_{n,j}]_+,
\]

以及功误差、体部最小间隙、Jacobian 秩/条件数和活动集一致性。standalone 另报 \(|r_P|\)。这些量按显式尺度无量纲化，但原始有量纲值必须保留。

### 5.13 固定支持线性特例与反力增长

在单一光滑支持、粘着、小变形、活动分支固定且总接触点柔顺近似常数时，梁、压缩区轴向弹簧和局部接触柔顺的点柔顺为

\[
\boxed{
\mathbf C_p^{\rm total}
=
\mathbf J_r\mathbf C_b\mathbf J_r^{\mathsf T}
+\chi_s\frac{\mathbf a_0\mathbf a_0^{\mathsf T}}{k_s}
+\mathbf C_p^c,
}
\]

对本节单一固定支持，\(\mathbf J_r=[\mathbf I\ -[\mathbf p-\mathbf c_t]_\times]\) 把针尖截面广义位移映射为接触点平移，\(\mathbf C_p^c\) 是显式启用的局部接触点柔顺；\(\chi_s=1\) 仅在 `COMPRESSING`。定义

\[
C_{xx}
=\mathbf e_x^{\mathsf T}\mathbf C_p^{\rm total}\mathbf e_x.
\]

standalone 恒 \(P_z\) 特例满足

\[
\boxed{
\frac{dR_x}{du_x}=\frac{1}{C_{xx}},
\qquad
\frac{du_z}{du_x}
=
\frac{\mathbf E_Z^{\mathsf T}\mathbf C_p^{\rm total}\mathbf e_x}
{C_{xx}}.
}
\]

弹簧到硬限位后，其 \(\mathbf a_0\mathbf a_0^{\mathsf T}/k_s\) 项消失，切向斜率相应增大。若梁、弹簧和局部接触柔顺全部关闭，则 \(C_{xx}=0\)：理想固定支持不应出现任意平滑有限斜率；响应属于刚性约束/几何事件或集合值分支。任何有限斜率都必须来自显式启用且可追溯的物理柔顺。

二维单支持解析核验可取

\[
\mathbf n=-\sin\phi\,\mathbf e_x+\cos\phi\,\mathbf E_Z.
\]

在规定 \(+x\) 滑移边界且分母 \(1-\mu\tan\phi>0\) 时：

\[
\boxed{
\frac{R_{x,\rm crit}}{P_z}
=
\frac{\tan\phi+\mu}{1-\mu\tan\phi}.
}
\]

分母非正、另一侧摩擦锥、法向反力正性和拉离分支必须按完整 SOC 处理，不能把该标量式当作一般三维判据。

---

## 6. standalone driver 与 embedded kernel 的边界分层

| 项目 | `intrinsic_single_spine_kernel` | `standalone_single_spine_driver` |
|---|---|---|
| 公共使用者 | B | A 层验证/单刺实验 |
| 基座边界 | B 规定当前位姿和共同增量 | driver 规定 \(u_x\)，外层求 \(u_z\) |
| 法向主动推力 | 不存在针级 \(P_z\) 残量 | 固定 \(P_z=0.5\ \mathrm N\) |
| 分离态 | 返回 `OPEN_RESPONSE`、零接触 wrench、接近事件信息 | 运行受控几何搜索 |
| 首次接触 | 返回 `TIP_ZERO_LOAD` 或接触事件 | 定位后做 \(P_z(\eta)=\eta P_z\) 同伦 |
| 切向推进 | 对规定增量求本征响应 | 沿 \(+x\) 以可变数值步推进 |
| 时间 | 只返回由调用方认可的路径增量预览 | \(t=x_{\rm total}/(1\ \mathrm{mm/s})\) |
| 行程 | 不自行终止 B 全局路径，但返回历史预览/事件 | 连续总路径到 \(100\ \mathrm{mm}\) |
| 提交 | 仅返回试探句柄 | driver 接受子步后调用同一事务提交 |
| 损伤 | 读快照、写试探意图 | 单刺无冲突时原子提交 |
| 切线 | 位姿—wrench 切线/割线/集合值 | 可由 kernel 切线与外层法向平衡凝聚得到 |

### 6.1 embedded 开放响应

完全分离时，本征核不满足也不尝试满足任何恒法向力。它返回：

- \(\mathbf W_{A\to B}=\mathbf0\)；
- 主机械状态 `OPEN`；
- 质量状态；
- 最近合法球尖/体碰撞事件的分数或安全增量上限；
- 可能的几何候选；
- `error_class=OPEN_RESPONSE`。

B 通过改变共同背板位姿建立接触；A 不替 B 独立移动每根针。

### 6.2 standalone 预载与加载

首次合法球尖接触是 \(P_z\to0^+\) 的几何初态。driver 使用

\[
P_z(\eta)=\eta(0.5\ \mathrm N),
\qquad \eta:0\rightarrow1
\]

调用本征核并外层求 \(u_z\)。若体部碰撞、硬限位、最近允许位置、材料容量或所有接触分支耗尽前不能达到 \(\eta=1\)，返回 `PRELOAD_INFEASIBLE` 及最后可行状态。

达到目标推力后，driver 按 \(+\Delta u_x\) 推进；每个子步重新求 \(u_z\)，局部法向反力并不固定。释放后执行可逆回位预算，然后继续同一总 \(u_x\) 路径搜索。

### 6.3 搜索策略

standalone 允许两个显式策略：

- `NESTED_Z_SEARCH`：在给定 \(u_x\) 处沿 \(-Z\) 定位最早合法球尖接触；
- `PRESCRIBED_XZ_PATH`：沿声明连续 \((u_x,u_z)\) 路径搜索。

策略 ID、法向行程和容差必须记录。二者是控制输入差异，不得静默混用。embedded 不执行这两种搜索策略。

### 6.4 等价边界测试

把 embedded 核放入一个外部标量法向平衡器，外层解

\[
\mathbf E_Z\cdot\mathbf F_{A\to B}=0.5\ \mathrm N
\]

并使用与 standalone 相同搜索/同伦/路径时，两者的接触状态、\(u_z\)、wrench、事件、损伤和功必须在容差内一致。该测试同时证明 \(0.5\ \mathrm N\) 未在核内重复施加。

---

## 7. 柔顺、储能、耗散和失效去重审计

### 7.1 柔顺/能量矩阵

| 物理位置 | 状态量 | 共轭力 | 位移/变形 | 储能/耗散 | 开关/分支 | 不得重复项 |
|---|---|---|---|---|---|---|
| 球尖—表面局部接触斑 | \(c_{n,j}\) | \(\lambda_{n,j}\) | 局部法向压缩 | \(U_{c,j}=\int\lambda_n dc_n\)；首版不含切向微弹性 | `rigid_contact` 或经标定 `normal_compliance` | 不得用总系统斜率反演后再与梁/弹簧相加 |
| 露出针梁 | \(\boldsymbol\eta_b\) | \(\mathbf W_c\) | 轴向、双向弯曲、扭转 | \(U_b=\tfrac12\mathbf W_c^T\mathbf C_b\mathbf W_c\) | `needle_bending=off/on`；梁模型 ID | off 不等于强度关闭；根部柔顺不得静默并入 \(E\) |
| 独立轴向弹簧 | \(\delta_s\) | \(Q_s\) | 整根针组件沿轴回缩 | \(U_s=\tfrac12k_s\delta_s^2\) | rigid lock / original / compressing / hard stop | 不得允许拉伸；不与梁轴向变形合并成一个坐标 |
| 刚性背板与安装约束 | 规定基座增量、锁定反力 | 公共 wrench | 只有允许运动子空间 | 理想约束自身无内部储能；对外做功由接口计算 | 工程固定刚体 | 不引入隐藏背板/框架柔性 |
| 4 mm 硬限位 | \(r_H\) | 限位反力 | 限位后增量压缩为零 | 理想限位零增量功 | `HARD_STOP` | 不在 4 mm 后继续压缩或增加弹簧能 |
| 夹具/根部柔顺（未来） | 独立 \(\boldsymbol\eta_{\rm root}\) | 根部 wrench | 根部相对位移/转角 | 独立 \(U_{\rm root}\) | 当前关闭；启用需新模型 ID | 不得静默吸收到梁 \(E\) 或轴向弹簧 |
| Coulomb 摩擦 | 累计滑移 \(\ell_s\) | \(\boldsymbol\lambda_t\) | 客观切向相对滑移 | \(\Delta D_f=-\lambda_t\cdot\Delta s\ge0\) | \(\mu\) 参数 | 不作为弹性储能，不与划伤损伤功重复 |
| 表面材料损伤 | \(\delta_d,D,q\) | 等效牵引/容量利用率 | 局部化位移内部变量 | \(\Delta D_m\ge0\) | MaterialAdapter | 只缩减材料容量，不改 \(\mu,E,k_s\) 或地形 |
| 释放可恢复能 | `released_recoverable_energy` | — | 梁/弹簧/接触回零 | 能量返回项，不是耗散 | 释放事件 | 不并入 \(\Delta D_f\) 或 \(\Delta D_m\) |

轴向弹簧压缩与梁轴向/弯曲变形是串联的不同部件；其位移、力和能量分别输出。局部接触压缩必须在扣除仪器、夹具、梁和弹簧柔顺后标定。

### 7.2 失效与无效状态去重

| 机制 | 物理所有者 | 判据/结果 | 是否可恢复/继续 | 禁止混用 |
|---|---|---|---|---|
| 几何域外/质量不足 | A1 | `OUT_OF_DOMAIN` / `GEOMETRY_UNCERTAIN` | 停止物理排序，可更换数据/分支 | 不得写成零承载或材料失效 |
| 非承载体碰撞 | A1 几何 | \(g_{\rm cone/shaft/mount}\le0\) | 首版纯球尖分支终止 | 不是材料失效，也不是承载接触 |
| 接触释放 | A 接触/几何/平衡 | \(\lambda_n\to0\) 且打开侧，或合法分支/平衡消失 | standalone 可继续搜索；embedded 返回开放状态 | 不等于摩擦锥边界 |
| 摩擦滑移 | A2/A3 | 全粘着不可行 + 最大耗散分支 | 可继续滑移/迁移 | 不自动等于材料失效或释放 |
| 墙面材料启动/软化/完全失效 | A3 MaterialAdapter | \(r^0=q\)、\(\delta_d\) 演化 | 更新后完整重求平衡；可能继续或释放 | 不与针体强度合并 |
| 针体屈服/断裂 | A3 StrengthAdapter | \(E_{N,y/u}=0\) | 首版分支终止 | bending off 仍检查 |
| 梁模型越界/失稳 | A2 结构模型 | 剪切、转角、几何刚度等超适用范围 | 切换模型或返回不可用 | 不写成针体材料屈服 |
| 材料/参数不可用 | 参数/证据层 | adapter unavailable | 可保留未认证力学结果 | 不假定无限能力 |
| 物理无解 | 本征分支枚举 | 所有相容分支均不可行 | 调整共同运动/终止 | 不写成数值失败 |
| 数值未收敛 | 数值层 | 无法证明可行/不可行 | 减步/换配置/终止 | 不写成物理失效 |

---

## 8. 规范状态机、事件表与并发规则

### 8.1 互斥主机械状态

| 主状态 | 进入条件 | 保持不变量 | 允许退出 |
|---|---|---|---|
| `OPEN` | 无正压合法球尖接触 | 所有接触力为零；embedded 不施加恒力；不可逆历史不变 | `TIP_ZERO_LOAD`、致命几何/质量、`TRAVEL_COMPLETE` |
| `TIP_ZERO_LOAD` | 合法球冠零间隙、\(\lambda_n=0\) | 无储能/耗散提交 | standalone 到 `PRELOAD_BUILD`；embedded 可随规定增量进入 attached 或重新 open |
| `PRELOAD_BUILD` | standalone 接触后同伦 \(0<\eta<1\) | \(u_x\) 固定，外层法向平衡逐步建立 | `ATTACHED_STICK`、`PRELOAD_INFEASIBLE`、致命事件 |
| `ATTACHED_STICK` | 至少一个正压接触，所有已提交切向滑移为零 | 摩擦锥可行；可滚动/支持迁移 | `ATTACHED_SLIDE`、`RELEASE_TRANSITION`、并发材料/针体/限位事件 |
| `ATTACHED_SLIDE` | 至少一个支持有已提交非零客观滑移 | 滑移点最大耗散、耗散非负 | `ATTACHED_STICK`、`RELEASE_TRANSITION`、支持/材料/针体/限位事件 |
| `REATTACHED_ENTRY` | 第 \(k\ge2\) 次接触循环完成预载后的首个承载状态 | 旧损伤有效，路径/时间不重置 | 下一接受增量转 stick 或 slide |
| `RELEASE_TRANSITION` | 全部承载支持在共同事件位置失去正压力/合法分支/平衡 | 先记录事件前能量和状态 | `REVERSIBLE_RETURN` |
| `REVERSIBLE_RETURN` | 释放后梁/弹簧/接触压缩投影到零载 | 损伤、路径、时间、循环历史不回退 | `OPEN` |
| `TRAVEL_COMPLETE` | standalone \(x_{\rm total}=100\ \mathrm{mm}\) 或显式终止 | 状态冻结 | 无 |

`CRITICAL_SLIP`、`CONTACT_RELEASE_EVENT`、`MATERIAL_INITIATION` 等不作为长期主状态，而是瞬时事件；避免事件与驻留状态重复。

### 8.2 正交子状态

**每支持接触运动：**

`OPEN`、`TOUCH_ZERO_LOAD`、`STICKING_INTERIOR`、`STICKING_AT_CONE_BOUNDARY`、`ROLLING_NO_SLIP`、`SLIDING_COMMITTED`、`SUPPORT_SWITCH_PENDING`、`RELEASE_PENDING`。

**弹簧：**

`RIGID_LOCKED`、`AT_ORIGINAL_LENGTH`、`COMPRESSING`、`HARD_STOP`。

**材料面片：**

`MATERIAL_INTACT`、`MATERIAL_INITIATED`、`MATERIAL_SOFTENING`、`MATERIAL_RESIDUAL`、`MATERIAL_FULLY_FAILED`、`NO_DAMAGE_MODEL`、`MATERIAL_MODEL_UNAVAILABLE`。

**针体：**

`NEEDLE_ELASTIC`、`NEEDLE_YIELD_LIMIT`、`NEEDLE_FRACTURE_LIMIT`、`NEEDLE_STRENGTH_UNAVAILABLE`、`STRUCTURAL_MODEL_OUT_OF_RANGE`。

**质量/求解：**

`OK`、`OPEN_RESPONSE`、`EVENT_REDUCTION_REQUIRED`、`OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN`、`BODY_COLLISION_INVALID`、`MODEL_UNAVAILABLE`、`PARAMETER_UNAVAILABLE`、`EQUILIBRIUM_INFEASIBLE`、`EQUILIBRIUM_DEGENERATE`、`NUMERICAL_NONCONVERGENCE`、`STALE_SNAPSHOT`、`TRANSACTION_CONFLICT`。

### 8.3 关键转移规则

1. `TIP_ZERO_LOAD` 不直接成为 \(0.5\ \mathrm N\) 接触；standalone 必须通过预载同伦。
2. `STICKING_AT_CONE_BOUNDARY` 不自动转滑移；先求一侧全粘着重分配。
3. 支持点位置变化但客观滑移为零时保持无耗散滚动。
4. `MATERIAL_INITIATED` 或 `MATERIAL_SOFTENING` 只更新容量；必须完整重求力学后才能判释放。
5. 接触释放后梁、弹簧和接触压缩可逆回零；损伤、累计滑移、路径、时间和事件历史不回退。
6. 再挂接读取旧 DamageStore，不能恢复完整容量。
7. embedded 在 `OPEN` 只返回本征开放响应；standalone 才控制法向搜索。
8. 针体屈服/断裂和梁模型越界可终止首版分支，但同位置其他事件仍完整记录。

### 8.4 统一事件表

事件原始函数保留量纲，数值排序另使用显式参考尺度归一化。`event_fraction` 始终沿本次规定增量定义。

| 事件名 | 原始监控量 | 单位 | 事件性质 | 首版处理 |
|---|---|---|---|---|
| `OUT_OF_DOMAIN` | 域标志/边界距离 | 状态、mm | 致命优先 1 | 停止物理排序 |
| `GEOMETRY_UNCERTAIN` | 质量标志/不确定性 | 状态 | 致命优先 1 | 停止物理排序 |
| `CONE_COLLISION` | \(g_{\rm cone}\) | mm | 致命优先 2 | 纯球尖模型无效 |
| `SHAFT_COLLISION` | \(g_{\rm shaft}\) | mm | 致命优先 2 | 同上 |
| `MOUNT_COLLISION` | \(g_{\rm mount}\) | mm | 致命优先 2 | 同上 |
| `TIP_CONTACT_ESTABLISH` | \(g_t\) | mm | 可继续 | 建立 `TIP_ZERO_LOAD` |
| `CONTACT_LOAD_ONSET` | \(\lambda_n\) 从 0 正向进入 | N | 可继续 | 建立承载支持 |
| `FRICTION_CONE_REACHED` | \(m_j\) | N | 候选 | 一侧全粘着试探 |
| `SLIP_ONSET_CONFIRMED` | 全粘着不可行 + \(\|\Delta s\|>0\) | N、mm | 可继续 | 提交滑移分支 |
| `CONTACT_RELEASE` | \(\lambda_n=0\) 且打开侧/合法分支消失 | N、mm | 可继续 | 释放、回位、搜索/开放 |
| `SUPPORT_CHART_SWITCH` | 面重心/边参数/支持活跃约束 | 1 或 mm | 可继续 | 共同位置枚举图表 |
| `MIGRATION_DEGENERACY` | \(\sigma_{\min}(\mathbf A_r)\) | 依缩放 | 候选/退化 | 枚举相邻图表或报退化 |
| `CAP_LEGALITY_LOSS` | \((p-c_t)\cdot a_t-\zeta_b\) | mm | 可继续或释放 | 切换支持/释放 |
| `SPRING_ORIGINAL_LENGTH` | \(\delta_s\) | mm | 可继续 | 原长一侧规则 |
| `SPRING_HARD_STOP` | \(4-\delta_s\) | mm | 可继续 | 激活刚性限位 |
| `MATERIAL_INITIATION` | \(1-r_k^0\) | 1 | 可继续 | 建立面片/损伤活动候选 |
| `MATERIAL_SOFTENING_ENTRY` | \(q_k-r_k^0\) | 1 | 可继续 | 联立损伤残量 |
| `MATERIAL_FULL_FAILURE` | \(\delta_f-\delta_d\) | mm | 可继续/可能释放 | 以残余容量重求 |
| `NEEDLE_YIELD_LIMIT` | \(E_{N,y}\) | 1 | 首版终止 | 记录全部并发事件 |
| `NEEDLE_FRACTURE_LIMIT` | \(E_{N,u}\) | 1 | 首版终止 | 同上 |
| `STRUCTURAL_MODEL_LIMIT` | 梁适用指标 | 1 | 模型边界 | 切换模型或不可用 |
| `EQUILIBRIUM_DEGENERACY` | Jacobian 奇异值/秩 | 1 | 退化 | 集合值/分支报告 |
| `PHYSICAL_INFEASIBILITY` | 分支枚举结果 | 状态 | 失败 | 与数值失败分开 |
| `NUMERICAL_NONCONVERGENCE` | 迭代/残量失败 | 状态 | 数值失败 | 不解释为物理事件 |
| `PRELOAD_TARGET_REACHED` | \(\eta-1\) | 1 | standalone | 进入 attached |
| `PRELOAD_INFEASIBLE` | 同伦终止且 \(\eta<1\) | 状态 | standalone 失败 | 返回限制事件 |
| `REATTACHMENT` | 新循环预载成功 | 状态 | 可继续 | 循环 ID 加一 |
| `TRAVEL_COMPLETE` | \(100-x_{\rm total}\) | mm | 正常终止 | 冻结输出 |

### 8.5 事件缩放、括区和并发

每个事件 \(E_i\) 使用显式参考尺度 \(s_i\) 形成 \(\widehat E_i=E_i/s_i\) 仅供数值排序；最终判断使用未缩放物理量。事件一侧必须与接受分支一致，例如释放后 \(g^+>0\)、滑移后耗散非负、硬限位后不得继续增加 \(\delta_s\)。

固定致命优先级只有：

1. `OUT_OF_DOMAIN` 或 `GEOMETRY_UNCERTAIN`；
2. 锥段、针杆或安装座碰撞。

其他事件先定位到同一最早位置，再形成 `simultaneous_event_set`。不允许简单 if/else 让摩擦覆盖材料、材料覆盖释放或限位覆盖支持切换。

共同事件位置的候选后分支必须依次通过：

1. 硬不等式和模型适用性；
2. 完整耦合残量；
3. 不可逆时间方向；
4. 摩擦和材料非负耗散；
5. 未跳变量的连续性；
6. 事件一侧一致性；
7. 确定性词典序或显式非唯一报告。

针体屈服/断裂可终止，但不删除同位置其他事件记录。

---

## 9. 可执行单步算法、事务与失败分类

### 9.1 统一调用入口

一个外部请求从 accepted 状态 \(n\) 到候选状态 \(n+1\) 的流程如下。伪代码描述强制顺序，不规定编程语言。

```text
INPUT:
  mode = embedded_constitutive_trial | standalone_internal_trial
  accepted single-spine state Z_n
  immutable SurfaceRealization/A1QueryHandle
  immutable parameter bundle
  immutable shared DamageStore snapshot
  requested base increment or standalone Delta_u_x
  trial/iteration IDs and numerical configuration

0. Freeze and validate
   0.1 Validate contract/model/parameter versions, units, IDs and kinematic subspace.
   0.2 Freeze Z_n and DamageStore snapshot; create rollback snapshot and idempotency hash.
   0.3 Reject duplicate per-spine normal-force input in embedded mode.
   0.4 Clear/rebuild nonphysical caches as needed; never copy them into history.

1. Assemble boundary
   1.1 embedded: base pose and increment are prescribed; do not add P_z residual.
   1.2 standalone attached: prescribe Delta_u_x, add outer unknown u_z and
       r_P = E_Z · F_AtoB - 0.5 N.
   1.3 standalone open: select explicit SearchControllerPolicy; do not solve r_P yet.

2. Predict a certified subincrement
   2.1 Use last tangent/secant, body gaps, legal-cap gap, spring travel,
       friction margin, material margin, needle margin and Jacobian condition.
   2.2 Build candidate supports from previous active set, current A1 supports
       and near-contact features inside a conservative event band.
   2.3 Bound the step by A1 swept-distance certification so a narrow body collision
       or contact event cannot be crossed and missed.

3. Trial the least irreversible branch first
   3.1 If open, evaluate geometric contact/invalid events only.
   3.2 If attached, solve the all-sticking branch first, allowing support migration
       and load redistribution.
   3.3 Enumerate spring state consistent with the predicted side.
   3.4 Keep damage fixed at the accepted snapshot for the elastic predictor.

4. Solve each fixed branch
   4.1 Assemble R_intr and, only for standalone attached, r_P.
   4.2 In each semismooth Newton/active-set evaluation:
       - update base/root/tip kinematics;
       - re-query A1 legal cap and complete-body clearances;
       - update support charts/normals/tangent frames;
       - assemble beam and spring residuals;
       - assemble SOC contact/friction residuals;
       - assemble material residuals only for active trial damage;
       - assemble a consistent/generalized Jacobian.
   4.3 Use damping/line search. An iterate may not cross body collision,
       spring bounds, cap legality, chart boundaries or damage bounds.
   4.4 If a nonsmooth boundary is approached, stop the local Newton and return
       an event bracket instead of differentiating through the jump.

5. Enumerate irreversible/alternative activity
   5.1 If all-stick is infeasible, enumerate sliding sets from cone-boundary contacts.
   5.2 Enumerate adjacent support charts and contact open/closed states.
   5.3 Evaluate material initiation/softening sets and needle limits.
   5.4 For every irreversible candidate, update only a trial copy, then re-solve
       the complete mechanical equilibrium. Damage is never applied after-the-fact
       without re-equilibration.

6. Monitor all events simultaneously
   6.1 Evaluate every event function and quality flag on every converged trial.
   6.2 If any event lies inside the subincrement, rollback to the last accepted state.
   6.3 Form a common bracket [alpha_L, alpha_R] in the prescribed increment.
   6.4 At every bracket point, re-solve the full coupled problem; do not interpolate
       old forces, normals or damage.
   6.5 Locate the earliest common event by a bracket-preserving method.
   6.6 Apply fatal priority; otherwise construct the simultaneous event set.

7. Compete post-event branches
   7.1 Generate all physically compatible one-sided branches.
   7.2 Apply trial slip/damage updates on private copies.
   7.3 Re-solve full equilibrium and check residuals, inequalities, energy,
       nonnegative dissipation and one-sided event consistency.
   7.4 Select a unique continuation by continuity/work/state-change rules,
       or return branch nonuniqueness if observables differ.

8. Handle release/open
   8.1 If all positive-load supports open or all legal branches disappear,
       accept CONTACT_RELEASE at the located position.
   8.2 Record U_b-, U_s-, U_c- and released recoverable energy.
   8.3 Project reversible beam/spring/contact compression to zero load.
   8.4 Retain DamageStore, accumulated slip, total path/time and event history.
   8.5 embedded: return OPEN response for the remaining prescribed interval or
       an event-reduction recommendation; never start a private normal search.
   8.6 standalone: enter controlled search and continue the remaining x increment.

9. Acceptance checks
   9.1 Check every residual block separately.
   9.2 Check all hard inequalities and model/parameter evidence.
   9.3 Check work balance; numerical residual remains separate.
   9.4 Check deterministic state labels, event order and history monotonicity.
   9.5 Compute wrench, event fraction, tangent/secant and all diagnostics.

10. Trial return or commit
   10.1 embedded evaluate_trial returns an opaque trial handle and damage intents only.
        Repeated B Newton calls cannot mutate accepted state.
   10.2 standalone driver may request commit only after its outer step accepts.
   10.3 Atomic commit increases slip, damage, dissipation, path, cycle and event history
        exactly once; otherwise perform complete rollback.

11. Remaining increment loop
   11.1 Subtract only the accepted fraction and continue with the remainder.
   11.2 Detect zero-length repeated events by state hash and event ID.
   11.3 Enforce maximum event-loop count and minimum step.
   11.4 At minimum step, distinguish EQUILIBRIUM_INFEASIBLE from
        NUMERICAL_NONCONVERGENCE; never skip a feature.
   11.5 standalone stops at 100 mm; embedded returns control to B.
```

### 9.2 预测、活动集和求解顺序

强制优先尝试“最少不可逆”的分支：

1. 当前支持与全粘着；
2. 支持重分配/滚动但无滑移；
3. 部分滑移；
4. 材料启动/软化；
5. 接触打开；
6. 并发组合。

这不是物理事件的优先级，而是搜索可行分支的顺序；任何更早事件仍由统一事件定位决定。

### 9.3 切线与割线

在固定光滑分支，形成

\[
\mathbf J_{\mathcal A}
=\frac{\partial\mathbf R}{\partial\mathbf y},
\]

并通过隐函数线性化得到

\[
\mathbf K_{A\to B}
=\frac{\partial\mathbf W_{A\to B}}{\partial\mathbf q_B}.
\]

稳定准静态状态除残量和锥可行外，还要求：去除纯内力规范后的分支 Jacobian 对规定一侧增量局部可解；粘着分支的结构切线在活动接触兼容零空间上满足

\[
\boxed{
\mathbf N^{\mathsf T}\mathbf K_{\rm str}\mathbf N\succ0;
}
\]

其中 \(\mathbf K_{\rm str}\) 是当前启用可逆结构块的切线，\(\mathbf N\) 的列张成活动接触兼容约束的零空间。摩擦/损伤分支还必须无负耗散方向。该条件只声明局部增量稳定，不声明全局 Lyapunov 稳定。

必须报告秩、条件数、分支和一侧方向。若 \(\mathbf J_{\mathcal A}\) 奇异但存在解族，返回 `EQUILIBRIUM_DEGENERATE`/`constraint_set_valued`；若不存在相容分支，返回物理无解；若无法判定，返回数值未收敛。

### 9.4 事务语义

```text
snapshot() -> immutable accepted_state_n
evaluate_trial(...) -> response + opaque handle + rollback token
prepare_atomic_commit(batch) -> armed commit token or conflict/stale error
commit_atomic(token) -> new versions + receipt
rollback(handle/token) -> no physical history change
```

trial 中只允许改变私有可逆变量和试探历史副本。B 多针全局 Newton 可任意重复调用；只要未执行原子 commit，累计滑移、DamageStore、耗散、路径、时间、循环和事件序号必须保持不变。

### 9.5 共享 DamageStore

A 返回面片读写集合、旧版本和 opaque 损伤意图。B 对重叠写集合进行冲突分组，调用 A 的局部损伤事务协调器生成共同试探快照，然后重新求所有受影响针和 B 全局平衡。不得按调用顺序覆盖。最终所有针和共享 DamageStore 一起提交或一起回滚。

### 9.6 失败分类

| 类别 | 定义 | 是否物理结论 |
|---|---|---|
| `OUT_OF_DOMAIN` / `GEOMETRY_UNCERTAIN` | 输入几何不足 | 否，停止排序 |
| `BODY_COLLISION_INVALID` | 纯球尖模型无效 | 是几何无效，不是承载失效 |
| `MODEL_UNAVAILABLE` / `PARAMETER_UNAVAILABLE` | 模型或证据缺失 | 否，结果未认证 |
| `EQUILIBRIUM_INFEASIBLE` | 全部分支已证明无解 | 是，针对给定边界 |
| `EQUILIBRIUM_DEGENERATE` | 有解但集合值/不稳定/非唯一 | 是退化结论 |
| `NUMERICAL_NONCONVERGENCE` | 尚未证明可行或无解 | 否 |
| `NEEDLE_YIELD_LIMIT` / `FRACTURE_LIMIT` | 达到针体上限 | 是首版终止边界 |
| `MATERIAL_FULL_FAILURE` | 面片容量到残余/零 | 是材料事件，但是否释放需重求 |
| `PRELOAD_INFEASIBLE` | standalone 无法达到 \(0.5\ \mathrm N\) | 是独立试验边界 |
| `TRAVEL_COMPLETE` | \(100\ \mathrm{mm}\) 完成 | 正常终止 |

---

## 10. 原始输出、多峰记录与验证计划

### 10.1 每个接受子步的原始输出

```text
identity_and_versions:
  model / contract / engineering / parameter / surface versions
trajectory:
  total_path_x / physical_time / accepted_subincrement
  contact_cycle_id / event_sequence_number
  search / preload / stick / slide / attached distances
geometry:
  tip_pose / legal-cap gaps / support points / feature charts
  normals / tangent frames / cap margin / body clearances
  quality / trusted scale / uncertainty
mechanics:
  force and moment by support
  A_on_B wrench at declared reference
  grip resistance R_x
  beam / spring / contact-compression states and energies
  residual blocks / Jacobian / tangent status / nonuniqueness
motion:
  migration increment / objective slip increment / accumulated slip
material:
  patch IDs / area / depth / kernel / material frame
  initiation utilization / capacity / damage / softening / modes
  friction and material dissipation / damage evidence status
needle:
  section resultants / stress bounds / yield and fracture margins
state_and_events:
  primary state / all substates
  all event candidates / simultaneous set / accepted event
  event fraction / bracket / one-sided consistency
energy:
  base or actuator work
  U_b / U_s / U_c
  D_f / D_m / returned recoverable energy
  work balance error
transaction:
  snapshot versions / trial handle / commit receipt
```

没有二元“抓附成功”阈值。任何后处理评分都不能删除原始连续曲线、逐针/逐支持状态和事件。

### 10.2 连续路径与多峰

standalone 使用唯一总路径：

\[
0\le x_{\rm total}=u_x-u_x^{\rm start}\le100\ \mathrm{mm},
\qquad
t=\frac{x_{\rm total}}{1\ \mathrm{mm/s}}.
\]

一个接触循环从 `TIP_ZERO_LOAD` 到全部承载支持释放。支持切换、多点增减、滑移和材料软化不自动结束循环。

每个循环保存：

```text
PeakRecord:
  peak_id / contact_cycle_id
  start_x / peak_x / end_x
  start_time / peak_time / end_time
  peak_grip_resistance / complete wrench
  integrated_positive_resistance
  search / preload / sticking / sliding distances
  support IDs / damage patch IDs
  dominant or mixed failure events
  event-location / numerical / evidence quality
```

并发摩擦、材料、释放或针体事件记为 `MIXED/UNRESOLVED_ORDER`，不得任意指定单一主导机制。

### 10.3 解析与单元验证

| 类别 | 必测内容 |
|---|---|
| A1 几何 | 平面、斜面、正弦面、窄槽、多支持、球冠连接、锥/杆/座先碰撞；高度场—网格加密一致 |
| 接触摩擦 | 分离零力、\(\mu=0\)、二维单支持载荷比、锥边界但可重分配、最大耗散滑移 |
| 梁 | 矩阵对称/正定、轴向/双向弯曲/扭转解析、坐标旋转、bending off 极限、EB/Timoshenko 对比 |
| 弹簧 | 原长无拉力、压缩线性、4 mm 硬限位、卸载回原长、刚性安装与大刚度弹簧不混同 |
| 材料 | 无损极限、起始/软化 KKT、断裂能面积、无愈合、核/网格/步长客观性 |
| 针体 | 纯轴/弯/扭/剪、bending off/on 内力一致、屈服/断裂并发 |
| 事件 | 大步不漏检、共同事件、事件分数减步重现、一侧一致性、零长度循环保护 |
| 功 | 坐标/参考点不变、粘着零耗散、滑移/损伤非负、释放能单列、rollback 不累积 |

### 10.4 端到端验证

1. standalone 与 embedded 外包法向平衡在等价边界下逐步一致；
2. 一条构造多凸起路径产生至少两个完整接触循环和两个峰；
3. 释放后路径、时间和 DamageStore 不重置；
4. 同一损伤区再挂接读取折减容量；
5. trial 重复调用和 rollback 不改变 accepted 状态；
6. 共享损伤多针调用顺序不变；
7. 全刚性构造返回集合值/退化而不是隐藏惩罚斜率；
8. 域外、几何不足、体碰撞、材料缺失、物理无解和数值未收敛可分别触发；
9. 随机表面参数变化的方向和设计排序可与独立单刺试验对比；
10. \(100\ \mathrm{mm}\) 行程中事件位置、峰前反力、耗散和状态序列随步长/网格/核加密进入稳定平台。

### 10.5 当前完成状态

本文件完成并接受的是模型、方程、状态、事件、算法和合同规范。尚未完成求解器代码、材料/针体参数标定、CAD 补齐、容差收敛、随机样本研究或实验验证。解析“通过”仅指公式/结构闭合，不得表述为已运行的软件或已验证实验。

### 10.6 A 大模块完成判据核对

| 判据 | 规范层结论 | 尚需关闭 |
|---|---|---|
| 定位首次合法球尖接触和禁止体碰撞 | A1 间隙、球冠、体部硬间隙和共同事件已闭合 | 几何代码、CAD 和加密回归 |
| 区分几何候选、摩擦可行、稳定平衡、材料/针体安全 | 状态、残量和适配器分层明确 | 参数标定和稳定性回归 |
| 反力随背板位移按显式柔顺增长 | 第 5.13 节给出分支切线和刚性极限 | 实现切线与实验斜率核验 |
| 梁、弹簧、局部接触柔顺不重复 | 第 7.1 节矩阵冻结物理位置、力、位移和能量 | 独立柔顺标定 |
| 定位滑移、材料起始/软化/完全失效、针体上限和释放 | 统一事件表、共同括区和分支竞争已定义 | 数值回归和材料数据 |
| 脱离后继续搜索、再预载和再挂接 | standalone 状态机保持路径/损伤，embedded 返回开放响应 | 搜索策略与设备验证 |
| 100 mm 轨迹可产生多个闭合循环和峰 | 路径、循环、PeakRecord 和循环算法闭合 | 多凸起端到端运行 |
| 状态、方程、符号、单位、功、事件和事务全局唯一 | 本文件已完成正式冻结 | 代码数据模型审查 |
| 单步算法可执行且失败可分类 | 第 9 节给出完整顺序和失败分类 | 求解器实现与最小步研究 |
| A→B 合同可装配共同平衡且不重复 0.5 N | 第 12 节合同冻结；embedded 无 \(r_P\) | 合同测试和 B 原型调用 |
| 未决问题与关闭条件完整保留 | 第 11 节逐项登记 | 后续工程/实验任务 |
| 未开始 B/C 或排除项 | 本模型只定义单刺和 A→B 边界 | 后续任务须维持依赖方向 |

因此当前状态为 `accepted`：规范层已通过一致性审查并冻结；这不等于软件、参数或实验层完成。

---

## 11. 参数/模型状态、风险、未决问题与关闭条件

### 11.1 工程输入尚未固定

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 红砖/混凝土/砂纸 PSD、边际、相关长度、各向异性、非高斯和粒度统计 | A1 几何候选与事件分布 | 参数化 SurfaceConfig；无数据则不宣称材料专属预测 | 目标表面多位置三维测量、可信带质控和统计验收 |
| 具体砂纸目数与批次 | 砂纸表面族 | `grit_designation` 只作标签 | 工程确定目数并测量实际成品表面 |
| 表面分辨率、可信最短波长 | \(50/100\ \mu m\) 针尖支持法向可靠性 | 不足时 `GEOMETRY_UNCERTAIN` | 仪器 MTF/SNR、重复扫描和多分辨率收敛 |
| 随机样本数量与种子停止规则 | 排名置信度 | 支持顺序增加样本，不硬编码 N | 输出置信区间/方案排序进入稳定平台 |
| 球冠连接 \(\zeta_b\)、锥长/角、安装座外形 | 合法球冠与体碰撞 | 必需输入；缺失则几何模型不可用 | CAD/显微测量和制造公差审查 |
| 各部件安全间隙 | 体碰撞事件 | 版本化参数，不给默认 | 制造/装配公差和碰撞回归确定 |
| 弹簧回缩—露出梁长拓扑 | 梁刚度和碰撞几何 | 主线固定 \(L\)；另一分支关闭 | CAD/位移测量确认 \(L(\delta_s)\) |
| standalone 搜索控制路径 | 再接触位置 | 两个显式策略分别标记 | 与实际执行器控制、行程和高速观测比对 |

### 11.2 材料与针体参数待标定

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 各表面 \(\mu\) 及方向/位置分布 | 锥、滑移和峰值 | 参数或 `unavailable` | 相同针尖/载荷/环境的起滑试验，排除损伤样本 |
| 局部接触柔顺 \(c_n\) | 峰前斜率和储能 | 刚性主线；可选分支关闭 | 微加载试验扣除仪器、梁、弹簧和夹具后可辨识 |
| 高碳钢牌号、\(E,\nu\) | 梁柔顺 | 参数缺失则模型不可认证 | 采购/材质证明和成品针多方向弹性试验 |
| \(\sigma_y,\sigma_u\)、根部应力集中 | 针体上限 | 强度状态 unavailable；不宣称安全 | 成品针破坏试验、CAD/局部 FE 或经验证系数 |
| 面片面积、控制深度、损伤核 | 应力代理和耗散 | 物理参数扫描，不随网格缩小 | 局部试验 + 网格/核/步长客观性 |
| 材料方向映射、\(c,\phi,f_t\)、压帽 | 起始模式 | 参数化容量域 | 微压入/剪切/混合加载和方向试验 |
| \(G_I,G_S,G_C,\eta_G,\rho\)、软化形状 | 峰后和再挂接 | 未标定分支 unavailable 或明确 no-damage 对照 | 局部峰后力—相对位移、纯摩擦扣除和留出验证 |
| 砂纸损伤模型 | 是否划伤/颗粒脱落 | `no_damage`、结果量容量或 unavailable 显式选择 | 实际砂纸批次重复通过/显微损伤试验 |

### 11.3 模型选择待数据决定

| 选择 | 风险 | 当前选择 | 关闭条件 |
|---|---|---|---|
| Euler–Bernoulli / Timoshenko / 共回转 | \(L/d=5\)–\(6.67\) 可能有剪切/几何非线性 | EB 主线 + 强制适用性检查 | 给定材料后与高阶梁/实验误差对比 |
| 刚性/柔性局部接触 | 隐藏惩罚或重复柔顺 | 刚性主线 | 独立接触压缩可辨识和刚性极限收敛 |
| continuum_patch / resultant_capacity | 参数可辨识性与跨尺度迁移 | continuum 主线，resultant 显式候选 | 独立局部数据或稳定几何分割与留出验证 |
| 固定/可变混合模态断裂能 | 非比例加载 | 起始时冻结模式 | 非比例试验显示需升级 |
| 零/非零残余容量 | 完全失载与摩擦残余混淆 | \(\rho\) 参数，不设默认 | 峰后和重复通过试验 |
| 高度场/完整网格 | 非单值结构 | 高度场主线，网格能力分支 | 同源几何一致性和目标表面需求 |
| 根部/夹具柔顺 | 将试验系统斜率误归针体 | 当前关闭并单列风险 | 独立根部/夹具标定 |

### 11.4 数值容差和收敛缺口

| 未决项 | 当前安全处理 | 关闭条件 |
|---|---|---|
| 初始/最大/最小步长、增长率 | 配置 ID；事件时括区 | 事件、峰值、耗散、状态序列的步长平台 |
| 间隙、支持聚类、法向、球冠容差 | A1 质量/不确定性传播 | 几何网格和解析案例收敛 |
| 事件位置和并发容差 | 全事件同时监控 | 减步后事件集合和一侧状态稳定 |
| SOC/损伤投影尺度 | 只作数值尺度 | 精确解和事件对尺度不敏感 |
| 残量缩放和接受门槛 | 分块原始值与归一化值均输出 | 解析误差、有限差分和精度扫描 |
| Jacobian 条件/退化阈值 | 报告而不硬判唯一 | 构造退化案例和不同精度一致 |
| 最大事件循环/零长度检测 | 状态哈希与最小步失败分类 | 多事件回归无死循环且不跳事件 |
| 数值导数步长 | 不光滑点禁止伪光滑 | 自动微分/解析/有限差分交叉验证 |

### 11.5 实现回归与实验验证缺口

| 缺口 | 影响 | 关闭条件 |
|---|---|---|
| A1 高度场/网格、球冠和全针体碰撞代码 | 几何入口尚未运行 | 解析、构造、加密和不漏检回归 |
| SOC 半光滑 Newton/活动集 | 摩擦分支可执行性 | 分块残量、2D 特例、滑移最大耗散 |
| 梁/弹簧统一实现 | 反力斜率和限位 | 矩阵、极限、硬限位、中心线碰撞测试 |
| 材料损伤和 DamageStore | 不可逆/顺序客观性 | 无愈合、能量、键稳定、并发冲突测试 |
| 针体强度适配器 | 安全上限 | 成品针数据和解析载荷回归 |
| 100 mm 多峰端到端 | 状态机闭环 | 至少两个完整循环、路径/能量/事件闭合 |
| standalone/embedded 一致 | 0.5 N 分层正确性 | 等价边界逐步一致测试 |
| 随机表面统计与方案排序 | 工程验证目标 | 多样本置信区间及实验趋势/排序对比 |
| 允许误差范围 | 无法宣布定量验证 | 工程批准的验证指标与容差 |

### 11.6 仅 B 层允许解决的问题

以下问题不得在 A 中预先决定：

- 每单元 \(0.5\)–\(2\ \mathrm N\) 主动推力的离散扫描点；
- 弹簧刚度范围内的具体阵列扫描点；
- 多针共同 \(u_z\)、共同背板平衡和活动针集合；
- 针间载荷共享、重分配、级联失效和阵列峰值；
- 同一损伤区域被多针同时加载时的全局耦合迭代和提交时机；
- 阵列几何拓扑、针距、转置阵列和角度梯度的共同响应；
- B→C 的单元 resultant 和整爪同步搜索。

A 只返回单针本征响应、局部损伤律和事务意图，不替 B 选择全局平衡。

### 11.7 工程未决登记逐项保留

以下逐项展开正式 `UNRESOLVED.REGISTRY.GLOBAL`；集成只规范其接口和关闭责任，不把任何未决项静默视为已解决。

| 原登记 ID | 本模型中的状态 | 当前安全处理 | 关闭条件/允许关闭层 |
|---|---|---|---|
| `UNRESOLVED.A1.ENGAGEMENT_CRITERIA` | 几何候选、摩擦可行、稳定平衡和材料安全已分层；最终实验判据仍未关闭 | 输出连续裕度与状态，不设成功阈值 | 单刺实验、几何/摩擦/材料联合验证；A/validation |
| `UNRESOLVED.A2.FRICTION_STABILITY` | SOC 最大耗散和局部增量可解性已规范；参数与实现未验证 | 返回锥裕度、广义 Jacobian和分支状态 | \(\mu\) 标定、构造回归和步长收敛；A |
| `UNRESOLVED.A3.CONTACT_MIGRATION` | query/chart 统一表示已规范；实现未运行 | 非光滑处括区、图表枚举，不平均法向 | 高度场—网格迁移和面—边—顶点回归；A |
| `UNRESOLVED.A2.CONTACT_STIFFNESS` | 未决 | 刚性主线；柔性分支需独立参数 | 局部微加载扣除其他柔顺；A |
| `UNRESOLVED.MATERIAL.NEEDLE` | 未决 | 参数 unavailable 时不认证强度/梁数值 | 牌号、材质证明和成品针试验；A |
| `UNRESOLVED.SURFACE.STATISTICS` | 未决 | 版本化 SurfaceConfig，无隐藏默认 | 目标材料三维测量与统计质控；A1 |
| `UNRESOLVED.SURFACE.FRICTION` | 未决 | 局部/分层 \(\mu\) 参数接口 | 目标表面起滑试验；A |
| `UNRESOLVED.SURFACE.STRENGTH` | 未决 | MaterialAdapter unavailable/no-damage 明示 | 局部混合加载和留出验证；A |
| `UNRESOLVED.DAMAGE.EVOLUTION` | 模型结构已规范，参数和模型选择未决 | 版本化软化/残余/核，不愈合 | 峰后能量、重复通过和客观性验证；A，未来 B/C 复用 |
| `UNRESOLVED.SURFACE.RESOLUTION` | 未决 | 可信带不足返回 `GEOMETRY_UNCERTAIN` | 仪器/网格/针尖输出收敛；A1 |
| `UNRESOLVED.STOCHASTIC.SAMPLE_COUNT` | 未决 | 顺序增加样本 | 置信区间和排序稳定；A/B/C study |
| `UNRESOLVED.NUMERICS.EVENT_STEPS` | 未决 | 配置化可变步长、括区和最小步失败分类 | 事件/峰值/耗散平台；A/B/C |
| `UNRESOLVED.SPRING.SAMPLING` | 不由 A 关闭 | A 只接受任一合法 \(k_s\) | B 参数扫描计划确定离散点；B |
| `UNRESOLVED.NORMAL_LOAD.SAMPLING` | 不由 A 关闭 | embedded 无每针载荷；standalone 固定 0.5 N | B/C 确定每单元 0.5–2 N 离散点；B/C |
| `UNRESOLVED.SANDPAPER.GRITS` | 未决 | 目数仅作标签 | 工程确定集合并测量批次；A1/experiment |
| `UNRESOLVED.METRIC.BINARY_SUCCESS` | 按工程事实保持未定义 | 保存原始连续量和事件 | validation 层经实验批准 |
| `UNRESOLVED.METRIC.COMPOSITE_SCORE` | 保持未定义 | 不在 A 内评分 | validation/设计决策层批准 |
| `UNRESOLVED.C1.STOP_THRESHOLD` | A 不处理 | 只提供单刺/单元后续所需原始量 | C1 依据 B 仿真和实验确定 |
| `UNRESOLVED.C1.MAX_SEARCH_DISTANCE` | A 不处理 | 不把 100 mm 单刺行程复制到整爪 | C1 依据单元有效搜索距离确定 |
| `UNRESOLVED.VALIDATION.ERROR_TOLERANCE` | 未决 | 只报告误差和置信度 | 工程验证方案批准；validation |

“规范结构已定义”只关闭符号冲突和接口缺口，不代表上述登记项已完成代码、标定或实验验证。

### 11.8 主要风险

1. 粗糙尖点和多支持使几何/摩擦/材料事件高度非光滑；
2. 全刚性分支反力可能集合值，阵列载荷共享无唯一解；
3. 材料面片尺度和摩擦功/损伤功可能不可辨识；
4. 准静态搜索不再现跳跃、冲击和弹道再接触；
5. 针根几何与热处理可能使名义圆截面上界不保守；
6. 多事件共同位置可能存在实质不同的物理分支；
7. 未完成容差、网格、核和随机样本收敛前，不应把峰值数值当作最终预测。

---

## 12. 公共 A→B 接口

下列公共合同正文与独立文件 `A_TO_B_CONTRACT.md` 中标记范围逐字一致。

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

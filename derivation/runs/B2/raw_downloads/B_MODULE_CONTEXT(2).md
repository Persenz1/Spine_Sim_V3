# B_MODULE_CONTEXT — 刚性/独立弹簧阵列爪单元算子

> 大模块：`B`  
> 当前完成阶段：`B2`  
> 上下文候选版本：`0.2.0`  
> 工程事实版本：`1.0.0`  
> 上游合同：`A_TO_B 1.0.0 accepted`  
> B1 基线：`B_MODULE_CONTEXT 0.1.0 accepted`  
> 提示词版本：`B2 1.0.0`  
> 运行：`B2-r01`  
> 当前状态：`candidate`

本文是大模块 B 完成 B2 后的最新完整候选上下文。第 2–17 节无损继承 B1 的几何、运动、身份、拓扑、A 请求与审计语义；第 18–33 节新增 B2 的恒定法向主动推力外层平衡、正交活动状态、载荷共享、非光滑求解、失败分类、输出、验证与 B3 交接。本文中的“必须”“不得”“可”分别表示强制要求、禁止事项和在不改变强制语义前提下允许的实现选择。

---

## 1. 范围、目标与层级边界

### 1.1 当前完整上下文覆盖范围

本候选上下文同时覆盖：

1. **B1：阵列几何、共同运动与柔顺拓扑**——规则球心格点、针级身份与哈希、固定角和线性梯度、实际露出长度、安装座出口反算、刚性背板局部 x/全局 Z 平移、刚性/独立轴向弹簧安装记录、方向邻接与表面相关性绑定，以及逐针 `embedded_constitutive_trial` 请求骨架；
2. **B2：恒定法向主动推力下的活动接触集与载荷共享**——给定共同切向位置或增量与每单元主动推力后求解背板法向位置，装配全部 A_on_B wrench，维护针级正交状态和承载集合，处理刚性集合值响应、弹簧无拉力与 4 mm 硬限位，形成事件驱动的准静态共同平衡、单元切线/图和 B3 试探交接。

当前 B2 算子写为

\[
\boxed{
\mathcal E_{B2}:
\left(
\mathcal C_{B1},
 u_x,
 P_z,
 \{\mathsf S_i^n\},
 \mathsf D^n
\right)
\mapsto
\left(
 u_z,
 \{\mathsf R_i^{\rm trial}\},
 \mathcal A,
 \mathbf W_U,
 \mathbf K_U,
 \mathsf{status},
 \mathsf{events}
\right).
}
\]

这里 `C_B1`、逐针状态快照、共享损伤快照和 A 调用语义均不可由 B2 改写。

### 1.2 B1 内容的继承方式

第 2–17 节保留 B1 0.1.0 accepted 的全部技术内容、公式、接口、验证和未决项。B1 中“B1 不求力/不求活动集”的表述继续限定 **B1 几何算子本身**；不与第 18 节以后由 B2 新增的共同平衡职责冲突。任何实现必须先通过 B1 配置和合同检查，才可进入 B2。

B1 冻结算子仍为

\[
\mathcal G_{B1}:
(n_x,n_y,s,\text{角度模式},\text{针级参数},\text{安装拓扑},\mathbf q_U)
\mapsto
(\text{针级身份/几何},\text{基座位姿/共同增量},\text{A 请求骨架},\text{拓扑/相关性元数据}).
\]

其已接受内容包括：

1. `2×2` 至 `6×6` 规则矩形阵列的唯一索引、针尖球心格点、针级身份和边界标签；
2. 固定角、`80°→50°` 和 `80°→60°` 两种线性梯度的统一参数化；
3. 梯度阵列实际露出长度、球心初始共面和安装座出口反算；
4. 刚性背板局部 x/全局 Z 共同平移到全部针基座位姿和 A 规定增量的映射；
5. `RIGID_MOUNT` 与 `AXIAL_SPRING_MOUNT` 的统一外部记录、不同内部状态所有权和限位语义；
6. 实际露出长度对几何、力臂、碰撞包络、梁参数及配置哈希的一致绑定；
7. 边缘、行列、邻接、有向分离向量、阵列包络和表面空间相关性查询接口；
8. 标量、按 x 排和完整针级数组的规范化扩展接口；
9. 严格继承 `A_TO_B 1.0.0` 的逐针 `embedded_constitutive_trial` 请求/响应交接。

### 1.3 B2 的唯一职责

B2 只负责当前给定共同切向位置或切向试探增量下的阵列外层共同平衡：

- 将每单元主动法向推力只施加一次；
- 把所有逐针 A_on_B wrench 运输到共同参考点并装配；
- 求取与主动推力相容的共同背板法向位置；
- 区分几何接触、实际承载、粘滑、弹簧、材料事件、质量和非唯一性；
- 生成单元合力、约束反力诊断、原始/凝聚线性化、事件集合及 B3 所需的无副作用试探状态。

B2 不使用“有效刺数 × 平均单刺峰值”近似阵列力，也不把总主动推力平均分配给各针。

### 1.4 本轮明确不处理的内容

- **B3**：失效事件后的针级重分配、级联、共享损伤冲突联合重求解、连续再挂接、完整 100 mm 历史和原子提交；
- **C**：四单元同步收紧、内部预紧、偏心 wrench、整体摇摆与整爪渐进失效；
- **A**：球尖可达性、接触/摩擦、梁/弹簧本构、滑移迁移、材料容量、损伤、释放与再挂接的低层规律；
- 首版工程事实明确排除的裂纹扩展、碎屑动力学、针尖磨损、框架柔性和惯性动力学。

B2 可以定位局部材料或针体失效事件并返回 `B3_REBALANCE_REQUIRED`，但不得跨越该事件接受新的损伤历史或执行失效后级联。当前连续拖拽物理速度仍为 `1 mm/s`、最大行程仍为 `100 mm`；B2 只形成单步/单位置共同平衡，完整长行程历史属于 B3。

### 1.5 权威顺序、冲突结论与证据边界

权威顺序为：工程事实 1.0.0 > `A_TO_B 1.0.0 accepted` > `B_MODULE_CONTEXT 0.1.0 accepted` 的 B1 内容 > 模块规划和 B2 提示词 > 模板 > 本地文献、外部公开资料和 GPT 通用数值知识。

本轮未发现需要修改工程固定事实的语义冲突。文献06、文献07、文献10支持“名义刺数不等于真实接触数”“共同位移与回差造成收益饱和”“柔顺存在过硬/过软窗口、实际分载介于理想均载和不分载之间”等趋势，但其样机数值、材料、机构和经验系数不迁移为本项目固定参数。半光滑 Newton、主动集、广义方程和变分不等式资料只支持数值组织方式，不替代 A 的物理本构或工程事实。

### 1.6 必须遵守的工程事实

B1+B2 直接依赖并不得改写的工程事实至少包括：

- `COORDINATE.GLOBAL.FRAME`、`COORDINATE.UNIT.FRAME`、`COORDINATE.NEEDLE.AXIS`；
- `KINEMATICS.UNIT.RIGID_BOARD`；
- `NEEDLE.TIP.GEOMETRY`、`NEEDLE.CONTACT.COLLISION_BOUNDARY`、`NEEDLE.LENGTH.EXPOSED`、`NEEDLE.DIAMETER.SET`、`NEEDLE.MATERIAL.BASE`、`NEEDLE.BENDING.SWITCH`、`NEEDLE.EMBEDMENT.MODEL_BOUNDARY`；
- `ARRAY.TOPOLOGY.RECTANGULAR`、`ARRAY.SPACING.SET`、`ARRAY.ANGLE.FIXED_SET`、`ARRAY.ANGLE.LINEAR_GRADIENTS`、`ARRAY.ANGLE.GRADIENT_LENGTH_COMPENSATION`、`ARRAY.NEEDLE.DATA_EXTENSIBILITY`；
- `ARRAY.MOUNT.RIGID_MODE`、`ARRAY.MOUNT.AXIAL_SPRING_MODE`；
- `SURFACE.INTERFACE.UNIFIED`、`SURFACE.HEIGHT_FIELD.PRIMARY`、`SURFACE.TRIANGLE_MESH.SECONDARY`、`SURFACE.PARAMETERS.UNRESOLVED`；
- `LOAD.NORMAL.ACTUATOR_OUTPUT`、`LOAD.NORMAL.ARRAY_UNIT`、`LOAD.NORMAL.INFEASIBLE_TERMINATION`；
- `LOAD.DRAG.SPEED`、`LOAD.DRAG.QUASI_STATIC`、`NUMERICS.DRAG.VARIABLE_STEP`、`LOAD.DRAG.TRAVEL`；
- `PROJECT.OUTPUTS.NO_BINARY_SUCCESS`；
- `DAMAGE.MEMORY.LIGHTWEIGHT`、`SCOPE.FIRST_RELEASE.EXCLUSIONS` 和 `UNRESOLVED.REGISTRY.GLOBAL`；
- `UNRESOLVED.SPRING.SAMPLING`、`UNRESOLVED.NORMAL_LOAD.SAMPLING`、`UNRESOLVED.NUMERICS.EVENT_STEPS` 以及全部相关材料、表面、制造和评价未决登记项。

---

## 2. 坐标、符号与公共单位

### 2.1 坐标系

全局右手系为

\[
\mathcal F_G=\{\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
\]

墙面名义平面为全局 X–Y 平面，`+Z` 从墙面指向背板和自由空间。

单元方向基为

\[
\mathcal F_U=\{\mathbf e_x,\mathbf e_y,\mathbf E_Z\},
\qquad
\mathbf e_y=\mathbf E_Z\times\mathbf e_x,
\]

其中局部 `+x` 从头部指向根部，也是搜索和拖拽方向。

B1 另定义与背板刚性固连的**阵列格点框架**

\[
\mathcal F_A=\{O_A,\mathbf e_x,\mathbf e_y,\mathbf E_Z\},
\]

其原点 `O_A` 是未加载针尖球心格点的几何中心，初始格点平面取 `z_A=0`。`O_A` 是合法的刚体参考点，不要求位于实体材料上。若整爪层使用其他单元参考点 `O_i`，必须以版本化静态变换 `T_{U A}` 连接，不能改写 B1 格点坐标。

单位方向矩阵为

\[
\mathbf R_{GA}=\begin{bmatrix}\mathbf e_x&\mathbf e_y&\mathbf E_Z\end{bmatrix}\in SO(3).
\]

### 2.2 针级索引与基础符号

- `r=0,…,n_x−1`：局部 x 排索引；`r=0` 为根部排，`r=n_x−1` 为头部排；
- `c=0,…,n_y−1`：局部 y 列索引；c 随局部 `+y` 增大；
- `i=(r,c)`：针级二维索引；
- `N=n_x n_y`：安装针总数；
- `s`：未加载球心在局部 x/y 投影上的等中心距；
- `α_{rc}`：针轴相对背板平面的俯仰角；
- `β_{rc}`：针轴平面投影相对 `+x` 的偏航角；
- `L_{rc}`：安装座出口到未加载针尖球心的轴向露出长度；
- `d_{rc}`：针杆直径；
- `R_{t,rc}`：局部球形针尖半径；
- `b^0_{rc}`、`c^0_{rc}`：阵列框架中的未加载安装座出口与球心位置；
- `a_{rc}`：从安装座出口指向针尖球心的单位针轴；
- `q_U=[u_x,u_z]^T`：共同背板平移坐标。

### 2.3 公共计算单位与唯一换算位置

公共计算单位严格继承 A→B 合同：mm、N、s、rad、N·mm、MPa 和 N/mm。

| 工程输入 | 进入 B1 规范化后的值 | 规则 |
|---|---|---|
| `R_t`：50/100 μm | 0.05/0.10 mm | 除以 1000，一次且仅一次 |
| `k_s`：100–2000 N/m | 0.1–2.0 N/mm | 除以 1000，一次且仅一次 |
| 角度：degree | rad | 乘以 `π/180`，一次且仅一次 |
| 其余长度 | mm | 不重复换算 |

规范化记录同时保存 `source_value/source_unit` 供审计，但 A 请求只使用规范值。任何 downstream 再换算均为合同错误。

---

## 3. 输入、输出、不可变配置与状态所有权

### 3.1 B1 逻辑输入

B1 输入分为五组：

1. **阵列设计输入**：`n_x,n_y,s`、角度模式、针级 `α/β/L/d/R_t` 或其生成规则、安装模式、弯曲开关、参数包 ID；
2. **静态装配输入**：单元/阵列框架的初始全局位姿、复合针体几何 ID、安装座几何 ID、与其他单元参考点的静态变换；
3. **表面绑定输入**：`surface_realization_id`、不可变 `A1QueryHandle` 工厂或句柄、坐标/单位/域/质量版本；
4. **A 状态绑定输入**：逐针不可变单刺快照和同一轮共享损伤快照；
5. **试探骨架输入**：`q_U^n`、共同 `Δq_U`、全局试探身份、事件定位、切线和质量请求。

### 3.2 B1 输出

B1 输出以下不可变或只读对象：

- `B1UnitConfiguration`：规范化设计、版本、哈希和格点框架；
- `NeedleStaticRecord[N]`：针级身份、几何、参数和边界标签；
- `UnitKinematicMap`：`q_U/Δq_U` 到逐针基座位姿/增量的映射；
- `MountTopologyRecord[N]`：刚性或独立轴向移动副的配置；
- `ArrayTopologyMetadata`：邻接图、有向分离向量、方向分组和包络；
- `SurfaceCorrelationBinding`：方向协方差/PSD/联合查询接口；
- `EmbeddedTrialRequestSkeleton[N]`：逐针 A 请求骨架；
- `B2HandoffSchema`：完整保存 A 响应字段的 B2 数据结构。

B1 不输出针力、单元合力、活动针数、弹簧平衡压缩量或承载能力。

### 3.3 状态所有权

| 对象 | 所有者 | B1 权限 |
|---|---|---|
| 规则格点、针级静态参数、配置哈希 | B1/B | 生成并冻结 |
| 共同背板 `q_U`、主动推力、全局试探 ID | B/B2 | B1 定义字段与映射，不求平衡 |
| 单刺接触、梁、弹簧、材料、损伤历史 | A | 仅持有 opaque 快照/句柄，不解析、不修改 |
| `SurfaceRealization` 原始几何 | A1 | 只读句柄 |
| 共享 `DamageStore` 内容 | A 材料层定义；B 调度 | B1 只绑定同一声明版本 |
| 活动接触集和载荷共享 | B2 | B1 不定义 |
| 失效重分配和提交循环 | B3/B 事务协调 | B1 不提交 |

静态字段 `needle_exists=true` 仅表示配置中存在该针。不得在静态记录中使用 `active=true/false` 表示当前承载；活动状态必须来自 A 响应并由 B2 管理。

---

## 4. 规则矩形阵列的索引、格点、身份和数据模型

### 4.1 唯一格点表达

未加载球心格点在阵列框架中的位置为

\[
\boxed{
\mathbf c^0_{rc}=
\begin{bmatrix}
 x_r\\y_c\\0
\end{bmatrix},\quad
x_r=\left(\frac{n_x-1}{2}-r\right)s,\quad
y_c=\left(c-\frac{n_y-1}{2}\right)s.
}
\]

该定义具有以下结果：

- `r=0` 的根部排具有最大正 x；头部排具有最小负 x；
- 第一个阵列维数始终对应局部 x，第二个对应局部 y；
- 偶数维数产生半格坐标，例如 `n_x=2` 时 `x=±s/2`；
- 奇数维数存在 `x=0` 中心排或 `y=0` 中心列；
- 所有格点均值严格为零；
- 球心投影包络尺寸为
  \[
  \ell_x=(n_x-1)s,\qquad \ell_y=(n_y-1)s.
  \]

`s` 只表示未加载球心投影等中心距，不表示安装孔、针轴交点或变形后接触点距离。

### 4.2 行优先枚举和唯一性

规范枚举顺序为 `r` 外层、`c` 内层：

```text
for r in 0..n_x-1:
    for c in 0..n_y-1:
        emit needle(r,c)
```

行优先顺序只用于确定序列化和审计，不赋予载荷优先级。并行调用顺序不得改变物理解。

### 4.3 边缘与方向标签

每根针保存四个方向边界位：

```text
is_root_edge   := (r == 0)
is_head_edge   := (r == n_x-1)
is_y_minus_edge:= (c == 0)
is_y_plus_edge := (c == n_y-1)
```

聚合标签：

- `corner`：同时位于一个 x 边和一个 y 边；
- `edge`：仅位于一个边界；
- `interior`：不在边界；
- `center_row/center_column`：奇数维数时相应坐标为零。

对所有允许阵列，角点数为 4，非角边缘数为 `2(n_x−2)+2(n_y−2)`，内部数为 `(n_x−2)(n_y−2)`。

### 4.4 配置 ID、针 ID 与哈希边界

为避免“同一槽位”和“同一参数化针实例”混淆，定义两类身份：

```text
needle_slot_id = "B1S/<unit_instance_id>/r=<r>/c=<c>"
needle_id      = "B1N/<unit_instance_id>/<unit_config_hash>/r=<r>/c=<c>"
```

- `needle_slot_id` 表示物理或逻辑槽位，可跨配置版本保持稳定；
- `needle_id` 绑定精确配置，任何几何、材料、刚度、开关或版本变化都会改变；
- `unit_config_id = "B1U/0.1.0/<unit_config_hash>"`。

规范哈希流程：

1. 所有单位先规范化；
2. 所有针级数组按 `(r,c)` 行优先展开；
3. 载入角度、长度、轴、基座位置、复合几何 ID、安装模式、开关、参数包字节哈希和公式版本；
4. 不载入运行时 `q_U`、试探 ID、活动集或 A 历史；
5. 采用 RFC 8785 的确定性 JSON 规范化；
6. 采用 SHA-256 生成 `unit_config_hash`。

为避免单一哈希过载，另定义：

- `geometry_hash`：针级几何和静态变换；
- `parameter_bundle_hash`：A 参数包字节；
- `run_binding_hash`：`unit_config_hash + surface_realization/version + A contract/model version`；
- `state_compatibility_hash`：再加入逐针历史版本和共享损伤版本；
- `request_hash/response_hash`：由 A 合同事务层生成。

下游不得用旧 `needle_id` 或旧 `state_compatibility_hash` 绑定新配置。

### 4.5 针级静态记录最低字段

```text
identity:
  unit_instance_id / unit_config_id / needle_slot_id / needle_id
  r / c / row_major_ordinal / config_schema_version
geometry:
  tip_center_lattice_point_A_mm
  mount_exit_point_A_mm
  alpha_rad / beta_rad / axis_A / axis_G_at_reference
  exposed_length_mm / diameter_mm / tip_radius_mm
  composite_body_geometry_id / geometry_hash
  beam_length_binding_id / collision_length_binding_id
mount:
  mount_mode
  spring_parameter_id / spring_parameter_hash / travel_limit_mm
  needle_bending_switch / beam_model_id
parameters:
  material_parameter_id / strength_parameter_id
  contact_parameter_id / damage_parameter_id / numerical_config_id
surface:
  surface_realization_id / A1QueryHandle / query_envelope_spec
state_binding:
  immutable_A_state_snapshot_ref / shared_damage_snapshot_version
metadata:
  edge_flags / corner_edge_interior
  nearest_neighbors / optional_neighbors
  directed_separation_records
```

配置、A 动态历史和 B2 活动集是三个不同对象，任何实现不得合并为一个可变针记录。

---

## 5. 安装角、露出长度、球心共面与安装座出口反算

### 5.1 统一角度参数化

令

\[
\lambda_r=\frac{r}{n_x-1},\qquad 0\le\lambda_r\le1.
\]

所有模式均使用

\[
\boxed{
\alpha_r=(1-\lambda_r)\alpha_{\rm root}+\lambda_r\alpha_{\rm head}.
}
\]

模式定义：

- 固定角：`α_root=α_head=α_fixed`，`α_fixed∈{50°,60°,70°,80°}`；
- 梯度 1：`α_root=80°`、`α_head=50°`；
- 梯度 2：`α_root=80°`、`α_head=60°`。

同一 r 排共享角度。`n_x=2` 时只有两个端点；`n_x>2` 时按实数线性插值，不强迫 10° 整数。

正式输入以 degree 提供时，规范化器先完成一次 `degree→rad` 转换，随后公式、三角函数和 A 请求只使用 rad。

### 5.2 通用针轴

阵列框架中的针轴为

\[
\boxed{
\mathbf a_{rc}=
\cos\alpha_{rc}\cos\beta_{rc}\,\mathbf e_x+
\cos\alpha_{rc}\sin\beta_{rc}\,\mathbf e_y-
\sin\alpha_{rc}\,\mathbf E_Z.
}
\]

当前正式扫描 `β_{rc}=0`，但底层始终存储完整针级 β 数组和三维单位轴。生成器必须检查 `\|a_{rc}\|=1`；不得仅保存角度而在不同模块重复解释方向。

### 5.3 露出长度策略

固定角模式：

\[
\boxed{L_{rc}=4\ \mathrm{mm}.}
\]

梯度模式：

\[
\boxed{
L_{rc}=L_r=\frac{4\sin80^\circ}{\sin\alpha_r}\ \mathrm{mm}.
}
\]

`L_r` 是轴向距离，不是 Z 投影。当前两种梯度中 `L_r≥4 mm`，头部角度越小，轴向露出越长。

### 5.4 基座反算和共面证明

以规则球心格点为主约束，安装座出口由

\[
\boxed{
\mathbf b^0_{rc}=\mathbf c^0_{rc}-L_{rc}\mathbf a_{rc}
}
\]

唯一反算。分量为

\[
\begin{aligned}
b^0_{x,rc}&=x_r-L_{rc}\cos\alpha_{rc}\cos\beta_{rc},\\
b^0_{y,rc}&=y_c-L_{rc}\cos\alpha_{rc}\sin\beta_{rc},\\
b^0_{z,rc}&=L_{rc}\sin\alpha_{rc}.
\end{aligned}
\]

由于 `c^0_z=0` 且轴 z 分量为 `−sinα`，正向恢复为

\[
\mathbf c^0_{rc}=\mathbf b^0_{rc}+L_{rc}\mathbf a_{rc}.
\]

对梯度模式，

\[
b^0_{z,rc}=L_r\sin\alpha_r=4\sin80^\circ\ \mathrm{mm},
\]

故全部安装座出口位于同一背板基准 z 平面；反过来，若安装座出口 z 相同，则

\[
c^0_{z,rc}=b^0_z-L_r\sin\alpha_r=0
\]

（阵列框架已把共同球心平面选为 `z=0`），从而逐针证明球心初始共面。固定角模式中所有 α 和 L 相同，因此同样共面。

### 5.5 梯度导致的基座平面偏置

正式主线 `β=0` 时

\[
b^0_{x,r}=x_r-L_r\cos\alpha_r,
\qquad
b^0_{y,c}=y_c.
\]

梯度中 `L_r cosα_r=4 sin80° cotα_r` 随 r 变化，因此安装座出口的 x 间距一般不等于 s。未来 `β≠0` 时，x/y 两方向均可能发生偏置。B1 必须保存这些反算位置，并把真实复合体提交可装配/碰撞检查；不得同时要求规则安装孔和规则球心格点而忽略几何矛盾。

### 5.6 梯度测试向量

以下数值仅是固定公式的计算结果，单位为 degree/mm：

| `n_x` | `80°→50°` 的 `α_r` | 对应 `L_r` | `80°→60°` 的 `α_r` | 对应 `L_r` |
|---:|---|---|---|---|
| 2 | 80, 50 | 4.000, 5.142 | 80, 60 | 4.000, 4.549 |
| 3 | 80, 65, 50 | 4.000, 4.346, 5.142 | 80, 70, 60 | 4.000, 4.192, 4.549 |
| 4 | 80, 70, 60, 50 | 4.000, 4.192, 4.549, 5.142 | 80, 73.333, 66.667, 60 | 4.000, 4.112, 4.290, 4.549 |
| 5 | 80, 72.5, 65, 57.5, 50 | 4.000, 4.130, 4.346, 4.671, 5.142 | 80, 75, 70, 65, 60 | 4.000, 4.078, 4.192, 4.346, 4.549 |
| 6 | 80, 74, 68, 62, 56, 50 | 4.000, 4.098, 4.249, 4.461, 4.752, 5.142 | 80, 76, 72, 68, 64, 60 | 4.000, 4.060, 4.142, 4.249, 4.383, 4.549 |

所有表项满足 `L_r sinα_r=4 sin80° mm`；表中小数只用于审查，生成器保留规范化数值而不使用显示值回算。

### 5.7 复合针体与查询包络

每针几何不是一个点，而是版本化复合体：安装座、圆柱针杆、锥形过渡段和局部球形针尖。只有球形针尖允许承载；其余部分仅参与禁止碰撞和可装配检查。

B1 为 A1/A 生成查询包络规范：

\[
\mathcal E^{\rm trial}_{rc}
=\bigcup_{\eta\in[0,1]}
\mathcal B_{rc}\!\left(\mathbf q_U^n+\eta\Delta\mathbf q_U,\;\mathcal S_A^{\rm admissible}\right)
\oplus\mathcal U_{\rm geom},
\]

其中 `B_rc` 是完整针体在共同平移和 A 所有的允许弹簧/梁状态域中的占据集合，`U_geom` 是由 A1 质量配置给出的几何不确定性膨胀。B1 不自行假定梁最大挠度或安全裕量；若构造完整包络所需参数不可用，必须返回 `MODEL_UNAVAILABLE/PARAMETER_UNAVAILABLE`，不能以零裕量继续。

---

## 6. 共同刚性背板运动、针级基座位姿与 wrench 变换

### 6.1 共同平移

共同坐标为

\[
\mathbf q_U=\begin{bmatrix}u_x\\u_z\end{bmatrix},
\qquad
\mathbf d_U(\mathbf q_U)=u_x\mathbf e_x+u_z\mathbf E_Z.
\]

阵列框架全局位姿为

\[
{}^G\mathbf T_A(\mathbf q_U)=
\begin{bmatrix}
\mathbf R_{GA} & \mathbf p_A^0+\mathbf d_U(\mathbf q_U)\\
\mathbf 0^T&1
\end{bmatrix}.
\]

每针名义位置为

\[
\begin{aligned}
\mathbf b^G_{rc}(\mathbf q_U)&=\mathbf p_A^0+\mathbf d_U+\mathbf R_{GA}\mathbf b^0_{rc},\\
\mathbf c^{G,\mathrm{nom}}_{rc}(\mathbf q_U)&=\mathbf p_A^0+\mathbf d_U+\mathbf R_{GA}\mathbf c^0_{rc},\\
\mathbf a^G_{rc}&=\mathbf R_{GA}\mathbf a^A_{rc}.
\end{aligned}
\]

背板无转动，所以针轴、安装角和相对基座偏置不随 `q_U` 改变。

### 6.2 针级基座姿态

为避免绕针轴姿态不唯一，定义针局部正交框架：

\[
\mathbf t_{rc}=
\frac{\mathbf E_Z\times\mathbf a^G_{rc}}
{\|\mathbf E_Z\times\mathbf a^G_{rc}\|},
\qquad
\mathbf n_{rc}=\mathbf a^G_{rc}\times\mathbf t_{rc},
\]

\[
\mathbf R_{GN,rc}=
\begin{bmatrix}
\mathbf a^G_{rc}&\mathbf t_{rc}&\mathbf n_{rc}
\end{bmatrix}.
\]

当前 `α∈[50°,80°]`，故分母非零。每针安装座出口位姿为

\[
{}^G\mathbf T_{N,rc}(\mathbf q_U)=
\begin{bmatrix}
\mathbf R_{GN,rc}&\mathbf b^G_{rc}(\mathbf q_U)\\
\mathbf0^T&1
\end{bmatrix}.
\]

A 请求同时携带共同阵列/背板参考位姿和该静态针级安装变换；两者哈希必须一致。

### 6.3 共同增量

所有针收到同一声明增量

\[
\boxed{
\Delta\boldsymbol\xi_U^{G,O_A}=
\begin{bmatrix}
\Delta u_x\mathbf e_x+\Delta u_z\mathbf E_Z\\
\mathbf0
\end{bmatrix}.
}
\]

因为没有转动，该平移对任意针基座参考点相同。共同的是背板增量，不是球尖实际位移、弹簧压缩或接触力。实际球尖位移还取决于 A 所有的梁、弹簧、接触和滑移状态。

若输入含非零局部 y 平移或任何俯仰/滚转/偏航增量，B1 预检查必须拒绝，并按合同生成/传播 `KINEMATIC_MODE_UNSUPPORTED`；不得把 6 自由度增量投影到 x/z 后静默继续。

### 6.4 相对位置不变量

对任意两针 i、j，

\[
\mathbf b_j^G(\mathbf q_U)-\mathbf b_i^G(\mathbf q_U)
=\mathbf R_{GA}(\mathbf b_j^0-\mathbf b_i^0),
\]

与 `q_U` 无关。因此共同平移保持全部针间相对基座向量和静态装配关系。

### 6.5 wrench 参考点、方向和功

A 返回的规范量是 `A_on_B`：单刺 A 子系统对刚性背板 B 的作用 wrench。B1/B2 不再添加内部梁力、弹簧力或根部反力，也不再次换号。

优先请求 A 将全部针响应表达在全局框架、同一阵列参考点 `O_A`。若 A 返回针级参考点 `O_i`，运输到 `O_A` 必须使用

\[
\mathbf F^{O_A}=\mathbf F^{O_i},
\qquad
\boxed{
\mathbf M^{O_A}=\mathbf M^{O_i}+
(\mathbf r_{O_i}-\mathbf r_{O_A})\times\mathbf F.
}
\]

若还需旋转坐标，力和力矩必须同时旋转。离散功检查为

\[
\Delta W_{A\rightarrow B}
=(\mathbf W_{A\rightarrow B}^{G,O_A})^T
\Delta\boldsymbol\xi_U^{G,O_A}.
\]

参考点运输与增量运输必须保持该标量不变。切线不能仅用静态 wrench 变换矩阵自行变换；参考点运动可能产生几何项，除非 A 明确确认，否则应请求 A 在目标参考点返回切线。

### 6.6 `2×5` 与 `5×2` 的比较约束

比较转置阵列时必须保持：

- 同一 `F_G/F_A`、相同 `+x` 搜索方向和 `+y` 定义；
- 同一表面实现、同一表面样本坐标和随机种子；
- 相同 `s`、针级参数、主动推力方案和统计方法；
- 只交换 `n_x` 与 `n_y`。

不得旋转或重采样表面使两者人为等价。即使是 `n×n` 方阵，也只有表面统计、载荷和边界均对称时才可能统计等价。

---

## 7. 刚性安装与独立轴向弹簧安装的统一拓扑

### 7.1 统一外部记录

两种模式共享同一 `NeedleStaticRecord` 和同一 A 调用入口，只通过 `mount_mode`、参数包和 A 状态分支区分：

| 项目 | `RIGID_MOUNT` | `AXIAL_SPRING_MOUNT` |
|---|---|---|
| 背板共同运动 | 同一 `q_U/Δq_U` | 同一 `q_U/Δq_U` |
| 安装座内轴向相对运动 | 锁定为零 | 仅沿针轴回缩 |
| 安装座内转动 | 禁止 | 禁止 |
| 弹簧参数 | 不存在，不用大刚度伪装 | `k_s`、零预压、单边压缩、4 mm 行程 |
| 内部状态所有者 | A，固定 mount 子状态 | A，`δ_s`、弹簧力、余量、硬限位 |
| 针体弯曲 | 独立开关 | 独立开关 |
| 每针载荷 | B1 不规定 | B1 不规定 |

正式扫描的单元级模式要求全阵列统一为刚性或全阵列独立弹簧；底层记录保留针级字段，但混合模式不属于当前批准扫描，必须另行审批。

### 7.2 轴向回缩的几何语义

仅用于解释方向，不用于 B 自行更新历史：正压缩 `δ_s>0` 时，未弯曲针的球心相对名义伸出位置沿 `−a_{rc}` 退回安装座，

\[
\mathbf c_{rc}^{\rm illustrative}
=\mathbf c_{rc}^{\rm nom}-\delta_{s,rc}\mathbf a_{rc}.
\]

合法状态域为

\[
0\le\delta_s\le4\ \mathrm{mm}.
\]

- `δ_s=0`：弹簧处于原长，无预压，不得产生拉力；
- `0<δ_s<4 mm`：A 的线性压缩分支；
- `δ_s=4 mm`：进入刚性硬限位，A 返回额外 `hard_stop_reaction`；
- 若维持约束要求 `δ_s<0`，必须解除轴向约束或由 A 判定接触脱开。

B1 不求 `δ_s`，不共享 `δ_s`，也不把单元推力分摊为弹簧载荷。

### 7.3 初始几何一致性

在相同静态配置、`δ_s=0` 且 `needle_bending=off` 时，两种安装模式使用同一 `b^0,c^0,a,L`，初始几何必须逐针一致。之后的差异只由 A 的 mount 参数和状态产生。

### 7.4 柔顺去重

- 刚性安装不能表示为任意巨大有限 `k_s`；
- 弹簧 `k_s` 只表示安装座内轴向弹簧，不能吸收针梁柔顺或接触柔顺；
- `needle_bending=on/off` 与 `mount_mode` 正交；
- 参数包必须声明 `compliance_components`，若同一物理部件被重复计入，B1 前置检查失败。

### 7.5 制造回差字段

文献07证明通道间隙投影回差会影响阵列扩展，但本项目未固定制造间隙或回差分布。B1 可预留：

```text
manufacturing_error_model_id
axial_zero_offset_mm
lateral_backlash_model_id
orientation_error_model_id
```

默认状态必须是 `unavailable/not_enabled`，不能采用文献07的 0.1/0.5 mm 或任何唯一分布作为正式默认值。

---

## 8. 实际针长、针体弯曲、力臂和参数一致性

### 8.1 单一长度源

每根针只允许一个规范化 `exposed_length_mm`。以下对象必须引用同一 `length_binding_id`：

- 球心—基座几何；
- 复合针体碰撞/可装配几何；
- 接触点到背板参考点的静态力臂基础；
- 梁模型输入；
- 针体强度/截面结果适配器；
- 查询包络。

任何组件私自复制 `4 mm` 都会造成哈希不一致并被拒绝。

### 8.2 梁参数传递

`needle_bending=on` 时，A 必须收到逐针：

```text
exposed_length_mm = L_rc
diameter_mm = d_rc
material_parameter_id
beam_model_id / section_model_id
geometry_hash / parameter_bundle_hash
```

`needle_bending=off` 时梁位移和梁储能为零，但截面内力、屈服/断裂裕度和模型可用性字段仍保留。

### 8.3 尺度检查而非替代本构

圆实心截面的二次矩为

\[
I=\frac{\pi d^4}{64},
\]

Euler–Bernoulli 小变形横向柔顺具有

\[
\mathcal C_\perp\propto\frac{L^3}{EI}
\]

的尺度关系。该关系只用于检查“长度增大应显著降低横向刚度”的量纲趋势，不是 B1 的三维接触刚度，也不复制 A 梁状态。

### 8.4 参数不可用处理

高碳钢牌号、弹性模量、屈服和断裂参数尚未固定。B1 只接受版本化参数 ID、候选模型 ID 或 `unavailable`。若当前请求需要梁或强度模型而参数缺失，必须传播 `MODEL_UNAVAILABLE/PARAMETER_UNAVAILABLE`；不得填入隐藏钢材默认值或无限强度。

---

## 9. 阵列方向性、边缘、邻接、有向分离向量与空间相关性

### 9.1 有向分离向量

对针 i=`(r,c)` 和 j=`(r',c')`，定义

\[
\boxed{
\Delta\mathbf r_{ij}^A
=\mathbf c_j^0-\mathbf c_i^0
=\begin{bmatrix}
(r-r')s\\(c'-c)s\\0
\end{bmatrix}.
}
\]

主数据必须保存有向向量，不能只保存欧氏距离。令

\[
m_x=\frac{\Delta x}{s}=r-r',\qquad m_y=\frac{\Delta y}{s}=c'-c,
\]

则非零有向偏移 `(m_x,m_y)` 的有序针对数量为

\[
\boxed{
N(m_x,m_y)=(n_x-|m_x|)(n_y-|m_y|),
}
\]

其中 `|m_x|<n_x`、`|m_y|<n_y` 且不同时为零。该式提供可复现的方向直方图基准。

### 9.2 `2×5` 与 `5×2` 的直接差异

两者针数都为 10，但：

| 指标 | `2×5` | `5×2` |
|---|---:|---:|
| 球心 x 包络 | `s` | `4s` |
| 球心 y 包络 | `4s` | `s` |
| 无向 x 最近邻对 | 5 | 8 |
| 无向 y 最近邻对 | 8 | 5 |
| 有向偏移 `(±2s,0)` | 0 | 每方向 6 |
| 有向偏移 `(0,±2s)` | 每方向 6 | 0 |

因此沿搜索方向的采样基线、横向覆盖、同时遇到同一脊/沟的概率和边缘方向均不同。只有在旋转对称表面和对称加载下才可能出现统计巧合，不能作为数据模型等价关系。

### 9.3 邻接图

B1 至少输出：

- `G4`：局部 x/y 最近邻，距离 s；
- `G8`：可选地加入对角邻居，距离 `√2 s`；
- `G_radius`：由版本化半径或 A1 相关性查询建议生成的可选图；
- 每条边的 `Δr_ij`、方向组、距离和边界标签。

邻接图只表示几何/潜在耦合，不包含载荷转移权重。B2/B3 不得把 `G4` 自动解释为局部载荷共享定律。

### 9.4 表面空间相关性接口

一般非平稳接口为

\[
C_q(\mathbf p_i,\mathbf p_j)
=\operatorname{Cov}[q(\mathbf p_i),q(\mathbf p_j)],
\]

其中 `q` 可以是有限球尖可达高度、方向坡度、法向分量、材料容量或 A1 定义的候选特征。若表面在所考察区域可视为平稳，可缩写为

\[
C_q(\Delta\mathbf r_{ij}),
\qquad
\rho_{ij}^{(q)}=
\frac{C_q(\mathbf p_i,\mathbf p_j)}
{\sqrt{C_q(\mathbf p_i,\mathbf p_i)C_q(\mathbf p_j,\mathbf p_j)}}.
\]

B1 的 `SurfaceCorrelationBinding` 至少支持一种：

```text
directional_covariance(channel_id, p_i, p_j)
PSD_2D(channel_id, k_x, k_y, convention_id)
correlation_length_tensor(channel_id)
joint_A1_feature_query(query_envelopes, realization_id)
```

由二维 PSD 反算协方差时，傅里叶归一化、坐标方向和离散采样约定必须由表面后端显式声明；B1 不固定唯一归一化常数。

### 9.5 相关性矩阵输出

对每个阵列和相关通道，B1 输出或绑定

```text
correlation_channel_id
surface_realization/version
sample_locations_G
pairwise_directed_separations_G
covariance_or_correlation_matrix_handle
quality / uncertainty / stationarity_assumption
```

若相关长度远小于 s，非重叠针位的几何通道矩阵应趋向对角结构；若相关长度远大于阵列包络，单一平稳通道应趋近高相关、近秩一结构。这两个极限仅是候选相关结构检查，不能升级为 B2 的独立承载或完全均载结论。

### 9.6 禁止的概率外推

B1 不得：

- 把文献04的单点命中率乘成阵列成功率；
- 假设各针 IID；
- 从文献07的刺数曲线反推本项目唯一有效刺数公式；
- 用相关矩阵直接生成活动针数、接触力或失效概率。

几何覆盖和候选相关性属于 B1；实际活动接触、承载数和相关失效属于 B2/B3。

---

## 10. 任意针级扩展、广播规范与配置校验

### 10.1 三种输入形态

每个针级字段 `α,β,L,d,R_t` 以及材料、梁、弹簧参数 ID 允许三种互斥形态：

1. `scalar`：广播到全部 `(r,c)`；
2. `by_x_row[n_x]`：第 r 个值广播到该排所有 c；
3. `matrix[n_x][n_y]`：完整针级值。

一维数组始终解释为 x 排数组，不按长度猜测 y 列。字段必须显式标记形态，禁止同时提供标量和覆盖数组形成隐式优先级。

### 10.2 当前正式扫描与扩展边界

- 正式角度模式仅为四个固定角和两种规定梯度；
- 正式 `β=0`；
- 正式 `n_x,n_y∈{2,…,6}`、`s∈{4,5,6} mm`；
- 正式 `d∈{0.6,0.8} mm`、`R_t∈{0.05,0.10} mm`；
- 正式安装模式为全刚性或全独立轴向弹簧。

扩展接口存在不代表本轮允许新增偏航扫描、混合安装、任意材料或制造误差分布。正式运行必须设置 `scan_policy_id=B1_FORMAL_SCAN_1.0.0` 并执行集合校验；研究性扩展必须使用不同 policy/version，不能混入正式结果。

### 10.3 验证顺序

配置生成器按以下顺序失败即停：

1. schema、版本、必需字段和枚举；
2. `n_x/n_y`、数组秩和形状；
3. 单位可识别性和唯一换算；
4. 有限值检查，拒绝 NaN/Inf；
5. ID 格式、槽位唯一性和广播规范；
6. 正式扫描集合/范围；
7. 角度域、轴单位长度和偏航主值规范；
8. 长度策略、`L sinα` 共面和球心—基座闭合；
9. 格点唯一性、相邻球心投影间距和阵列中心；
10. 复合针体可装配、针间/背板/表面禁止碰撞包络；
11. 梁/弹簧/接触柔顺去重及参数可用性；
12. 规范序列化、哈希和针 ID；
13. A 状态、表面和损伤快照兼容性；
14. 共同增量运动子空间；
15. A 请求中禁止字段扫描。

任何针级异常都产生明确错误，不得用阵列均值替换。

### 10.4 B1 配置错误类

```text
B1_CONFIG_SCHEMA_INVALID
B1_ARRAY_SHAPE_MISMATCH
B1_UNIT_OR_CONVERSION_INVALID
B1_NONFINITE_VALUE
B1_FORMAL_SCAN_VIOLATION
B1_ID_COLLISION
B1_GEOMETRY_CLOSURE_FAILED
B1_COPLANARITY_FAILED
B1_ASSEMBLY_CHECK_FAILED
B1_PARAMETER_OR_MODEL_UNAVAILABLE
B1_DUPLICATE_COMPLIANCE
B1_STATE_BINDING_MISMATCH
KINEMATIC_MODE_UNSUPPORTED
CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD
```

能映射到 A 合同错误类的必须保留 A 的原始分类；B1 自身错误不得伪装成材料失效或零承载。

---

## 11. A 单刺调用请求骨架与 B2/B3 交接

### 11.1 唯一调用模式

B 对每根针只能调用

```text
embedded_constitutive_trial
```

不得调用或间接包装 `standalone_single_spine_driver`。B1 只实例化请求骨架，不执行载荷共享或提交。

### 11.2 逐针请求骨架

```text
contract_id: A_TO_B
contract_version: 1.0.0
call_mode: embedded_constitutive_trial

needle_identity:
  unit_instance_id
  unit_config_id / unit_config_hash
  needle_id / needle_slot_id / r / c
  geometry_id / geometry_hash
  structural_parameter_id / material_parameter_id
  strength_parameter_id / parameter_bundle_hash

surface_query_handle:
  surface_realization_id / surface_version
  A1QueryHandle
  query_envelope_spec / domain / frame / unit / quality IDs

base_pose_n:
  array_or_board_reference_pose_G
  reference_point_id / expressed_frame_id
  mount_exit_pose_G
  static_mount_transform_hash
  orientation_version

prescribed_base_increment:
  common_increment_G = [Δu_x e_x + Δu_z E_Z; 0]
  increment_coordinates = [u_x,u_z]
  interpolation = affine_translation
  kinematic_mode = UNIT_X_GLOBAL_Z_TRANSLATION

immutable_single_spine_state_n:
  opaque_snapshot_ref / accepted_history_version
  state_compatibility_hash

shared_damage_store_snapshot:
  common_snapshot_ref / version / content_hash

parameter_bundle:
  composite_body_geometry
  alpha / beta / axis / L / d / R_t
  mount_mode / needle_bending
  beam / spring / contact / friction / material / damage / strength IDs
  normalized_units / bundle_hash / evidence status

trial_identity:
  global_step_id / global_trial_id / newton_iteration_id
  caller_sequence_id = deterministic row-major audit ordinal

requested_tangent_mode
event_location_config
quality_request
continuation_hint   # optional A-generated opaque handle
```

请求中不得出现 `per_spine_normal_force`、`single_spine_Pz`、每针 `0.5 N` 或任何等价残量。每单元 `0.5–2 N` 主动推力只在 B2 外层平衡中出现。

### 11.3 同一轮一致性

同一 B 全局试探轮：

- 所有针使用同一 `global_trial_id`、`newton_iteration_id` 和共同增量；
- 每针 A 历史快照可以不同；
- 所有针首先读取同一共享损伤快照版本；
- `caller_sequence_id` 只用于审计，不得改变物理解；
- A 试探无永久副作用，B1/B2 不提交历史。

### 11.4 A 响应的无损保存

B2 的逐针试探记录必须原样保存以下字段组：

```text
wrench:
  A_on_B force/moment / opposite-wrench check
  frame / reference point / units / grip resistance
  uniqueness / admissible wrench graph

geometry_contact:
  active and near-contact support sets
  support points/features/charts / gaps / normals / tangent bases
  support forces / multipliers / slip increments / cap legality
  cone/shaft/mount gaps / A1 quality / uncertainty / nonsmooth flag

structure:
  bending switch / beam model and state
  beam translations/rotations/forces/moments/energy
  mount mode / spring state/compression/force/remaining travel
  hard-stop reaction / strength resultants and status

material_damage:
  model/evidence / queried patches
  damage read/write sets / trial intents / capacity / dissipation
  conflict signature

state_events:
  primary and orthogonal substates
  all event candidates / simultaneous set
  earliest event fraction / bracket
  suggested common increment fraction
  terminal/continuable and one-sided consistency

linearization:
  tangent or secant / status / branch / basis / reference
  finite-difference metadata

diagnostics:
  all residuals / work balance / rank/condition
  nonuniqueness / evidence / surface quality / uncertainty
  error class / detail

transaction:
  opaque trial handle / rollback token / provisional intent
  versions read / request-response hashes / idempotency key
```

不得丢弃模型不可用、参数不可用、非唯一、质量、事件或事务字段。

### 11.5 B2 归约规则（仅冻结接口）

B2 必须计算

\[
\gamma_{\rm common}
=\min_i\left(\texttt{suggested_common_increment_fraction}_i\right)
\in(0,1],
\]

缩短共同增量并重新求全部针的共同平衡。B1 只定义字段和归约规则，不执行该循环。

### 11.6 B3 与事务边界

共享损伤写集合冲突、失效后重分配、级联和再挂接属于 B3。B1 只确保 `damage_read/write sets`、`trial_damage_intents`、冲突签名和 opaque 句柄进入下游。只有 B 接受全局步并完成冲突检查后才能请求原子提交；B1 不生成 `armed_commit_token`。

---

## 12. B1 配置生成与请求实例化流程

### 12.1 生成伪代码

```text
INPUT: raw_design, static_unit_pose, surface_binding,
       A_state_bindings, q_n, Δq, trial_scaffold

1. validate schema/version/enums
2. validate n_x,n_y and formal scan policy
3. normalize units exactly once
4. normalize scalar/by-row/matrix fields to [n_x,n_y]
5. generate α_rc in radians from angle mode
6. generate/validate β_rc; formal policy requires β_rc = 0
7. generate L_rc from fixed or coplanar-gradient policy
8. generate c0_rc = [x_r,y_c,0]
9. generate unit axis a_rc
10. reverse mount exit b0_rc = c0_rc - L_rc a_rc
11. validate counts, uniqueness, spacing, centroid, endpoints,
    L sinα, forward/inverse closure and common mount z
12. bind d_rc, R_t_rc, composite geometry and parameter IDs
13. build edge labels, G4/G8 and directed separation histogram
14. build surface-correlation/query-envelope bindings
15. validate assembly/collision inputs and compliance de-duplication
16. canonicalize immutable payload and compute hashes
17. create unit_config_id, needle_slot_id and needle_id
18. validate A snapshots and surface versions against hashes
19. validate q_n/Δq lie in x-z translation subspace
20. compute T_GA(q_n), T_GN_rc(q_n), common Δξ
21. instantiate per-needle EmbeddedSingleSpineTrialRequest skeleton
22. scan request for prohibited per-spine normal-load fields
23. emit immutable configuration, request skeletons and B2 handoff
```

### 12.2 前置条件

- 工程输入单位明确；
- 所有必需参数 ID 存在或显式为 `unavailable`；
- 表面句柄不可变且域信息可查询；
- A 快照未被 B 修改；
- 复合针体几何可由 A/A1 识别；
- 共同运动只含 x/z 平移。

### 12.3 后置条件

- 恰有 `n_x n_y` 个唯一针实例；
- 每针球心、轴、长度和基座正反闭合；
- 同一共同增量被逐字节复用于全部请求；
- 请求不含每针法向载荷；
- 所有配置、参数、表面和状态版本均可审计；
- B2 可不重建低层几何地直接调用 A。

---

## 13. 事件、失败传播和回退语义

B1 本身不推进接触状态，因此不产生滑移、材料失效或再挂接事件。B1 负责：

1. 在 A 调用前拦截配置、单位、运动和状态绑定错误；
2. 把 A 返回的 `all_event_candidates`、`earliest_event_fraction`、`suggested_common_increment_fraction` 等完整交给 B2；
3. 对 `OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN`、`BODY_COLLISION_INVALID`、`MODEL_UNAVAILABLE`、`PARAMETER_UNAVAILABLE`、`EQUILIBRIUM_*`、`NUMERICAL_NONCONVERGENCE`、`STALE_SNAPSHOT`、`DAMAGE_CONFLICT_REQUIRES_RESOLVE` 和 `CONTRACT_VIOLATION` 保留原分类；
4. 禁止把任何错误改写为零承载或材料失效；
5. 禁止试探期间提交累计滑移、损伤、耗散、路径、循环或事件历史。

若几何生成失败，B1 不创建部分有效阵列；整份配置原子失败。若只有某一参数模型不可用，可生成带 `unavailable` 的候选配置用于审计，但不得进入已认证物理排序。

---

## 14. 参数、证据与迁移边界

| 内容 | 来源类别 | B1 用法 | 迁移边界 |
|---|---|---|---|
| 坐标、扫描集合、长度补偿、安装模式、运动自由度 | 工程事实 1.0.0 | 强制值与边界 | 不可由文献改写 |
| A 调用、wrench、单位、事件、状态所有权、事务 | `A_TO_B 1.0.0 accepted` | 冻结公共语义 | B 不重建 A 机理 |
| 俯仰/偏航的方向性命中与刚度权衡 | 文献04 | 支持针级 α/β 接口和方向性解释 | 57.9°、10°–20°、命中率不作为本项目固定值 |
| 共同刚性背板、线性移动副、回差与刺数饱和 | 文献07 | 支持统一拓扑、制造误差字段和非线性扩展风险 | 5 mm 行程、论文刚度/回差/载荷公式不迁移 |
| 规则格点、齐次变换、数组广播、协方差矩阵、梁尺度 | GPT 通用知识 | 形成可实现数据/数学合同 | 数值参数和材料律仍需验证 |
| JSON 规范化与 SHA-256 | 外部公开规范 | 配置/参数字节的确定性哈希 | 属实现约定，不是工程物理事实 |
| 高碳钢参数、真实 CAD、制造误差、表面相关长度 | 未决/待标定 | 版本化 ID 或 unavailable | 禁止隐藏默认值 |

外部实现参考：

- RFC 8785：`https://www.rfc-editor.org/rfc/rfc8785.html`；
- NIST FIPS 180-4：`https://csrc.nist.gov/pubs/fips/180-4/upd1/final`。

---

## 15. 验证结果、解析极限与剩余缺口

### 15.1 本轮纯几何自动检查

采用公式级双精度测试覆盖全部 `n_x,n_y∈{2,…,6}` 和 `s∈{4,5,6} mm`，共 75 个格点组合：

- 针数全部为 `n_x n_y`，格点无重复；
- x/y 最近邻球心投影距离误差为 0；
- 格点质心误差为 0；
- 两种梯度、全部 `n_x=2…6` 的 `L sinα` 最大计算残差约 `4.44×10⁻¹⁶ mm`；
- 基座反算再正向恢复球心的最大计算残差约 `1.78×10⁻¹⁵ mm`；
- 安装座出口 z 平面最大离散约 `8.88×10⁻¹⁶ mm`。

上述数值是本轮计算残差，不是正式数值容差；正式容差仍属于 `UNRESOLVED.NUMERICS.EVENT_STEPS`/实现配置。

### 15.2 验证矩阵

| 检查项 | 状态 | 结论或关闭条件 |
|---|---|---|
| 全部允许阵列的计数、唯一性、中心和间距 | 通过 | 解析式与 75 组合自动检查一致 |
| 根部/头部、x/y 方向和 `n_x×n_y` 语义 | 通过 | `r=0` 最大 x，c 随 +y |
| 固定角和两种梯度端点/插值 | 通过 | `n_x=2…6` 均闭合 |
| 梯度共面与基座反算 | 通过 | 解析证明及数值闭合 |
| `2×5`/`5×2` 有向向量和包络差异 | 通过 | 最近邻和二阶偏移计数不同 |
| 共同 x/z 平移及相对位置不变量 | 通过 | 解析恒等式成立 |
| 非零 y/转动拒绝 | 通过（合同级） | 运行时需实现单元测试 |
| wrench 参考点运输和功不变 | 通过（合同级） | 需与 A 实现做数值验收 |
| 刚性/弹簧零压缩初始几何一致 | 通过（配置级） | A 状态实现仍需合同测试 |
| 单边弹簧、4 mm 硬限位和无拉力字段 | 通过（接口级） | 平衡值属于 B2/A |
| 实际 L 同时绑定几何、梁、碰撞和力臂 | 通过（数据合同） | 实现需哈希故障注入测试 |
| 主线 β=0 且完整 β 数组可规范化 | 通过 | 新偏航扫描需审批 |
| A 请求仅用 embedded、无每针法向载荷 | 通过（骨架级） | 需请求 schema 自动扫描测试 |
| A 响应事件/质量/非唯一/事务字段无损交接 | 通过（schema 级） | B2 实现需序列化往返测试 |
| 配置规范化与哈希规则 | 通过（规范级） | 实现需 RFC8785/SHA-256 测试向量 |
| 复合针体真实 CAD 可装配 | 仍缺数据 | 需要安装孔、锥段、安装座和公差 CAD |
| 制造回差/安装误差分布 | 仍缺数据 | 需要实物测量或批准的误差模型 |
| 表面方向协方差/PSD/相关长度 | 仍缺数据 | 需要 A1 测量/生成参数和质量版本 |
| 高碳钢 E、屈服/断裂参数 | 仍缺数据 | 需要材料牌号/试验或参数包 |
| 完整查询包络中的梁挠度上界 | 部分通过 | 由 A 模型有效域/参数提供；缺失则不可用 |
| B2 活动集和载荷共享 | 后续 | B2 唯一职责 |
| B3 重分配、冲突和再挂接 | 后续 | B3 唯一职责 |

### 15.3 相关性极限检查

- `ℓ_corr≪s`：候选几何通道的非对角相关应衰减，但不得据此宣称接触/失效独立；
- `ℓ_corr≫max(ℓ_x,ℓ_y)`：候选通道相关矩阵趋近高相关；
- 各向异性时 `C(Δx,Δy)≠C(Δy,Δx)`，因此转置阵列不可互换；
- 非平稳表面必须使用 `C(p_i,p_j)` 或联合 A1 查询，不能强制平稳模型。

### 15.4 B1 完成判据核对

B1 已在规范层满足：统一阵列生成、角度/长度闭合、球心—基座反算、共同运动、统一安装接口、实际长度一致传递、方向性/相关性表示、针级扩展、A 合同适配和 B2/B3 交接。当前归档状态为 `accepted`，表示 B1 数据与运动学合同已通过本轮审查；这不表示代码、真实 CAD、表面测量或实验已经完成。

---

## 16. B1 冻结交接记录：对 B2、B3 和 C 的要求

> 本节保留 B1 0.1.0 accepted 的交接语义。B2 已在本文第 18 节以后实现其中属于本轮的要求；其余 B3/C 边界继续有效。


### 16.1 B2 可直接调用的对象

B2 必须直接继承：

- `B1UnitConfiguration`、全部针级静态记录和哈希；
- `q_U/Δq_U` 运动映射和 `KINEMATIC_MODE_UNSUPPORTED` 规则；
- `EmbeddedTrialRequestSkeleton`；
- A_on_B wrench 方向、公共参考点和功共轭；
- 邻接/分离向量/相关性元数据；
- A 响应无损保存结构和最小事件分数归约规则。

B2 新增的是每单元主动推力、共同法向平衡、活动接触集、载荷共享和求解残量。B2 不得改变针尖格点、长度补偿、安装拓扑或 A 状态所有权。

### 16.2 B3 可直接调用的对象

B3 在 B2 平衡基础上使用：

- 逐针 A 事件、试探损伤意图和冲突签名；
- 邻接与空间核重叠信息；
- 剩余弹簧行程、硬限位和针强度状态；
- opaque 试探/回滚句柄和状态版本。

B3 才定义失效重分配、级联、联合损伤重求解、再挂接和原子提交循环。

### 16.3 C 层边界

C 只能在 B 集成后调用单元响应、变换坐标并装配单元 wrench。C 不得访问 B1 以重建单刺接触，不得重新定义针级柔顺或阵列载荷共享。阵列格点框架 `F_A` 到 C 单元参考框架的静态变换必须显式版本化。

### 16.4 未决问题清单

1. 梯度基座偏置与真实安装孔/滑块 CAD 的可装配闭合；
2. 锥段、针杆和安装座的完整参数化几何及公差；
3. 制造回差、安装位置和角度误差分布；
4. 红砖、混凝土和砂纸的方向协方差、二维 PSD、相关长度和非平稳性；
5. 高碳钢具体牌号、E、屈服和断裂参数；
6. 弹簧刚度与法向主动推力的正式离散扫描点；
7. A 查询包络中的梁变形有效域；
8. B2 的共同平衡、活动集和载荷共享；
9. B3 的失效重分配、共享损伤冲突和连续再挂接；
10. B/C 级数值容差、步长和验收代码。

---

## 17. B1 冻结自检记录

> 本节保留 B1 0.1.0 accepted 当时的自检结论，作为本轮继承审计记录；本文当前的 B2 总体自检见第 33 节。


- 本文是 B 截至 B1 的首版完整上下文，不是增量摘要；
- 工程事实、A 合同、B1 机理和待标定参数已分离；
- 索引、坐标、单位、角度、长度、基座和共同增量闭合；
- `2×5` 与 `5×2` 保持方向差异；
- 共同的是背板增量，不是球尖位移、弹簧压缩、接触力或每针法向载荷；
- 刚性/弹簧安装接口统一且状态所有权清楚；
- 梁与弹簧柔顺未重复；
- 空间相关性未采用 IID 假设；
- A 仅通过 `embedded_constitutive_trial` 调用；
- B2/B3/C 的问题未被提前求解；
- 未固定参数均保留为版本化 ID、候选模型或 `unavailable`。

---

## 18. B2 输入、输出、试探状态与所有权

### 18.1 逻辑输入

B2 的一次外层评估至少包含：

```text
B2EquilibriumRequest:
  B1_unit_configuration / hashes / frames / topology
  accepted_unit_position_q_n = [u_x^n, u_z^n]
  target_u_x or requested_common_delta_u_x
  unit_normal_active_thrust_Pz
  immutable_A_state_snapshot_by_needle
  common_shared_damage_snapshot
  requested_tangent_mode
  event_location_config
  numerical_equilibrium_config
  global_step_id / global_trial_id
  optional_u_z_predictor / continuation_hints
```

前置条件：

1. B1 配置、表面、参数和状态兼容性检查通过；
2. `P_z` 满足工程事实固定范围
   \[
   0.5\ \mathrm N\le P_z\le2\ \mathrm N,
   \]
   但其具体离散扫描点由外部参数计划给出；
3. 全部针读取同一共享损伤快照；
4. `u_x` 是位移控制量，`u_z` 是本轮外层未知量；
5. 所有 A 调用都从同一接受状态 `n` 出发，Newton 迭代只改变无副作用试探目标，不累加 A 历史。

### 18.2 逻辑输出

```text
B2EquilibriumTrial:
  q_trial = [u_x, u_z]
  per_needle_A_trial_responses
  orthogonal_state_labels_and_sets
  unit_contact_wrench_W_U_at_O_A
  active_normal_generalized_force_and_residual
  displacement_control_reaction_Rx
  constrained_reaction_diagnostics
  raw_and_condensed_linearization_or_graph
  event_reduction / simultaneous_event_set
  quality / uniqueness / status / failure_classification
  opaque_trial_handles / rollback_tokens
  damage_read_write_sets / conflict_signatures
  B3_handoff_metadata
```

`W_U` 只表示全部单刺 A 子系统对背板的接触/结构净作用，不包含主动执行器力、x 位移控制反力或被禁止自由度的约束反力。上述量必须分开记录。

### 18.3 B2 不拥有永久物理历史

B2 可在一次调用内保存 Newton 迭代、活动集合、分支提示、括区间和事件定位缓存，但这些均为试探数据。累计滑移、弹簧/梁历史、材料损伤、耗散、路径、循环和再挂接历史仍由 A 拥有；接受和原子提交属于 B3/B 集成事务。B2 输出成功只表示“已形成可供后续处理的共同平衡试探”，不等于历史已推进。

---

## 19. 允许运动、广义力、主动推力和完整静力记账

### 19.1 允许刚体增量基

定义 6 维 twist 到两个允许坐标的映射

\[
\boxed{
\mathbf H_U=
\begin{bmatrix}
\mathbf e_x & \mathbf E_Z\\
\mathbf 0 & \mathbf 0
\end{bmatrix}
\in\mathbb R^{6\times2},
\qquad
\Delta\boldsymbol\xi_U^{G,O_A}=\mathbf H_U\Delta\mathbf q_U.
}
\]

其中

\[
\Delta\mathbf q_U=
\begin{bmatrix}
\Delta u_x\\
\Delta u_z
\end{bmatrix}.
\]

所有针收到同一个 `Δq_U`；针尖、弹簧和接触点实际位移由 A 内部状态决定。

### 19.2 单元接触 wrench 与广义接触力

把第 i 根针的 A_on_B wrench 运输到全局坐标和共同参考点 `O_A` 后，定义

\[
\boxed{
\mathbf W_U^{G,O_A}=
\sum_{i=1}^{N}\mathbf W_i^{G,O_A}
=
\begin{bmatrix}
\mathbf F_U\\
\mathbf M_U^{O_A}
\end{bmatrix}.
}
\]

与允许坐标功共轭的广义接触力为

\[
\boxed{
\mathbf Q_U^{A}=\mathbf H_U^{\mathsf T}\mathbf W_U
=
\begin{bmatrix}
\mathbf e_x^{\mathsf T}\mathbf F_U\\
\mathbf E_Z^{\mathsf T}\mathbf F_U
\end{bmatrix}.
}
\]

因为当前背板无转动，接触合矩不进入 x/z 广义残量，但必须完整输出，用于约束反力诊断和未来 C 层装配。

### 19.3 主动法向推力的唯一施加位置

正 Z 指向背板/自由空间，向墙面主动推力采用

\[
\boxed{
\mathbf F_{\rm act}=-P_z\mathbf E_Z,
\qquad P_z>0.
}
\]

当前理想执行器被建模为只对 `u_z` 做功的广义力；在 `O_A` 的规范 wrench 表达为

\[
\mathbf W_{\rm act}^{G,O_A}
=
\begin{bmatrix}
-P_z\mathbf E_Z\\
\mathbf0
\end{bmatrix},
\qquad
\mathbf Q_{\rm act}=\mathbf H_U^{\mathsf T}\mathbf W_{\rm act}
=
\begin{bmatrix}
0\\-P_z
\end{bmatrix}.
\]

该表示是 B2 的理想广义载荷模型，不意味着实物执行器线作用点已经固定。若未来需要输出真实执行器偏心力矩，必须另给版本化作用线；不得在本轮隐藏假设一个 CAD 位置。

### 19.4 位移控制反力和被禁止自由度的约束反力

切向 `u_x` 为位移控制，不要求其广义残量为零。定义正抓附阻力

\[
\boxed{
R_x=-\mathbf e_x^{\mathsf T}\mathbf F_U.
}
\]

维持规定 `u_x` 的外部控制力为 `+R_x e_x`。在理想主动推力无力矩时，被禁止的 y 平移和三转动约束反力分量为

\[
\begin{aligned}
R_y^{c}&=-\mathbf e_y^{\mathsf T}\mathbf F_U,\\
M_x^{c}&=-\mathbf e_x^{\mathsf T}\mathbf M_U,\\
M_y^{c}&=-\mathbf e_y^{\mathsf T}\mathbf M_U,\\
M_z^{c}&=-\mathbf E_Z^{\mathsf T}\mathbf M_U.
\end{aligned}
\]

这些量是“为保持工程事实规定运动子空间所需的反力诊断”，不是 B2 新增的运动自由度，也不得被误算成爪刺额外承载来源。

### 19.5 功方向检查

任意允许试探增量满足

\[
\Delta W_U=\mathbf W_U^{\mathsf T}\mathbf H_U\Delta\mathbf q_U
=(\mathbf Q_U^A)^{\mathsf T}\Delta\mathbf q_U.
\]

法向自由虚位移下，接触与主动推力的虚功系数必须闭合；x 向控制器提供与 `R_x` 相容的反力功。y/转动约束因对应增量为零而不做功。参考点变换仍必须保持 A→B 合同规定的离散功不变。

---

## 20. 恒定主动推力下的外层平衡与广义方程

### 20.1 唯一响应分支上的标量平衡

给定 `u_x` 和 `P_z`，B2 主线只求一个外层未知量 `u_z`。若所有逐针响应在当前分支唯一，则法向残量为

\[
\boxed{
r_z(u_z;u_x,P_z)
=\mathbf E_Z^{\mathsf T}\mathbf F_U(u_x,u_z)-P_z=0.
}
\]

因此平衡后

\[
\boxed{
\mathbf E_Z^{\mathsf T}\mathbf F_U=P_z.
}
\]

该等式只约束全部 A_on_B 力的全局 Z 分量之和。由于局部法向和摩擦力可能均含 Z 分量，通常

\[
\sum_j\lambda_{n,j}\ne P_z.
\]

更不允许推出每针 `P_z/N`。

### 20.2 刚性/退化响应的集合值平衡

对第 i 根针，在给定共同位姿和只读历史下，令

\[
\mathcal W_i(\mathbf q_U)
\]

表示 A 返回的唯一 wrench 或 admissible wrench graph。运输和相容分支装配后

\[
\mathcal W_U(\mathbf q_U)
=\bigoplus_{i=1}^{N}\mathcal T_{i\rightarrow O_A}\mathcal W_i(\mathbf q_U),
\]

其中 `⊕` 表示在共同位姿、共同损伤快照和相容低层分支下的 wrench 和，不允许任意混合彼此不相容的代表值。法向 resultant 集为

\[
\mathcal N_U(u_x,u_z)
=
\left\{
\mathbf E_Z^{\mathsf T}\mathbf F
\;\middle|\;
\begin{bmatrix}\mathbf F\\\mathbf M\end{bmatrix}
\in\mathcal W_U(u_x,u_z)
\right\}.
\]

正式外层问题是广义方程

\[
\boxed{
P_z\in\mathcal N_U(u_x,u_z)
\quad\Longleftrightarrow\quad
0\in\mathcal N_U(u_x,u_z)-P_z.
}
\]

当 `N_U` 为单点时退化为第 20.1 节。若 `P_z` 属于集合但反力分配不唯一，应返回 `BALANCED_DEGENERATE`、秩/零空间和图句柄；不得用任意大罚刚度制造唯一解。

### 20.3 集合值残量的可计算定义

若 A 图查询能给出 `N_U` 的合法表示，B2 采用

\[
d_z(u_z)=\operatorname{dist}\!\left(P_z,\mathcal N_U(u_x,u_z)\right)
\]

作为平衡可行性度量。为确定搜索方向，可选择与延续分支一致的最近 normal resultant

\[
n_z^*\in\arg\min_{n\in\mathcal N_U}|n-P_z|,
\qquad
\widehat r_z=n_z^*-P_z.
\]

若最近点或分支不唯一，必须保留非唯一状态；`d_z=0` 只能证明总法向平衡可行，不能证明针间力唯一。若实现不能查询 A 返回的图而只有代表值，则不能认证刚性退化平衡，必须降级为 `MODEL_UNAVAILABLE/CONSTRAINT_GRAPH_UNAVAILABLE`。

### 20.4 法向搜索域与“开放但可继续”

定义由表面域、完整针体碰撞、安装座边界、几何最近位置和数值搜索策略共同给出的 admissible 法向区间

\[
\mathcal I_z=[u_z^{\min},u_z^{\max}],
\]

其中向墙面运动对应 `u_z` 减小。若当前全部针为 `OPEN_RESPONSE`，则

\[
\mathbf F_U=\mathbf0,
\qquad r_z=-P_z,
\]

这不是已经证明的物理无解。只要仍可在 `I_z` 内向墙面推进且无致命质量错误，状态应为 `PRELOAD_SEARCH_CONTINUE`，并通过共同减步定位首次接触。只有到达几何/结构/域边界或穷尽所有相容分支后仍不能满足广义方程，才可进入预载不可行或物理无解分类。

### 20.5 物理无解的严格证明边界

`EQUILIBRIUM_INFEASIBLE` 只能在以下条件同时满足时使用：

1. 当前所需模型和参数可用，几何质量足以认证；
2. admissible `u_z` 区间及其事件分支已被确定性地搜索/包围；
3. 所有相容 A 本征分支或图包络均不包含 `P_z`；
4. 结论不依赖迭代次数、初猜、针调用顺序或某个未检查代表 wrench；
5. 没有未处理的事件、陈旧快照或损伤冲突。

达不到该证明标准时应返回 `NUMERICAL_NONCONVERGENCE`、`MODEL_UNAVAILABLE`、`GEOMETRY_UNCERTAIN` 或更具体诊断，不能把算法失败伪装成物理失效。

---

## 21. 针级正交状态与外层集合

### 21.1 禁止单一 `active` 布尔量

每根针的 B2 分类由相互正交的至少六个维度组成：

| 维度 | 规范子状态 | 判定来源 |
|---|---|---|
| 几何/支持 | `OPEN`、`NEAR_CONTACT`、`CLOSED_ZERO_LOAD`、`LOAD_BEARING` | A 的 active/near support、gap、支持力和 wrench |
| 接触运动 | `NO_CONTACT_MOTION`、`STICK`、`SLIP_ONSET_CONFIRMED`、`SLIDING`、`MIXED_SUPPORT_MOTION` | A 的逐支持 motion state |
| 安装结构 | `RIGID_MOUNT`、`SPRING_ZERO`、`SPRING_INTERIOR`、`SPRING_HARD_STOP` | A 的 mount/spring state、压缩量和硬限位反力 |
| 材料/针体 | `SUBCRITICAL`、`FAILURE_EVENT_PENDING_B3`、`TERMINAL_STRENGTH_EVENT_PENDING_B3` | A 的材料/针体裕度和事件 |
| 求解质量 | `VALID`、`OPEN_RESPONSE`、`EVENT_REDUCTION_REQUIRED`、各致命/不可用/失败类 | A diagnostics 与 B2 外层诊断 |
| 唯一性/线性化 | `UNIQUE`、`REPRESENTATIVE_NONUNIQUE`、`SET_VALUED`；切线状态枚举 | A wrench uniqueness、图句柄和 tangent status |

多支持单刺内部可同时有粘着和滑移支持点；B2 保留全部支持点状态，只在针级输出一个不丢信息的聚合标签 `MIXED_SUPPORT_MOTION`。

### 21.2 外层集合定义

令针全集为 `I={1,…,N}`。B2 至少维护：

\[
\begin{aligned}
\mathcal O&=\{i:\text{无 active support}\},\\
\mathcal N&=\{i:\text{有 near-contact support 且无承载}\},\\
\mathcal G&=\{i:\text{active support 非空}\},\\
\mathcal L&=\{i\in\mathcal G:\text{存在正承载支持或非零合法 wrench}\},\\
\mathcal S_{\rm stick}&=\{i:\text{至少一个承载支持粘着且无滑移支持}\},\\
\mathcal S_{\rm slip}&=\{i:\text{滑移起始确认或存在滑移支持}\},\\
\mathcal H&=\{i:\delta_{s,i}=4\ \text{mm 且为硬限位分支}\},\\
\mathcal E&=\{i:\text{存在待定位/待处理事件}\},\\
\mathcal D&=\{i:\text{反力或分支退化/集合值}\},\\
\mathcal X&=\{i:\text{域外、体碰撞、模型/参数不可用、陈旧或合同错误等不可装配响应}\}.
\end{aligned}
\]

实际实现使用版本化数值阈值判断“近零力/近零间隙”，阈值不是工程事实。所有原始连续量必须同时保存，集合标签不得替代数据。

### 21.3 接触但零载荷的处理

`CLOSED_ZERO_LOAD` 针保留在 `G`，不进入 `L`。若其 gap、乘子和一侧状态位于数值候选带内，可同时标记为外层“边界候选”，用于稳定主动集更新；候选带只是一种数值策略，不能创造物理力。离开候选带后仍按 A 响应分类。

### 21.4 开放针不得永久跳过

每次 `u_z`、`u_x`、事件分支或共享损伤试探快照改变后，必须重新调用全部针。开放针可能在新共同位置建立接触；上轮不承载不是缓存删除依据。只允许复用 A 生成的 opaque continuation hint，不能复用旧 wrench 代替新评估。

### 21.5 活动集改变后的重算边界

任何针的支持、粘滑、弹簧内部/硬限位、材料事件、质量或唯一性状态改变，均要求在同一共同 `q_U` 上重新装配全部针的 wrench、normal graph、残量和线性化。已接受 A 历史和共享损伤快照保持只读；B2 不能因活动集更新局部写入历史。

---

## 22. 刚性阵列与独立轴向弹簧阵列的统一外层框架

### 22.1 统一调用而非两套求解器

两种安装模式都使用 B1 的同一共同背板位姿、同一逐针 A 请求骨架和第 20 节外层广义方程。区别仅存在于 A 参数包和 A 拥有的内部结构状态：

- `RIGID_MOUNT`：轴向相对运动严格为零；响应可唯一、退化或集合值；
- `AXIAL_SPRING_MOUNT`：A 返回 `0≤delta_s≤4 mm`、弹簧力、剩余行程和硬限位反力；弹簧无预压、不得受拉。

B2 始终只装配 A_on_B 净 wrench。不得再加一次 `k_s delta_s`、梁根部反力、接触 resultant 或硬限位反力。

### 22.2 柔顺组件的正交组合

针体弯曲开关、轴向弹簧、局部接触柔顺和材料软化均由 A 的版本化参数包与状态定义。B2 只观察其对 wrench、图和线性化的结果。合法组合包括：

```text
rigid mount + rigid needle + optional contact compliance
rigid mount + bending needle + optional contact compliance
axial spring mount + rigid needle + optional contact compliance
axial spring mount + bending needle + optional contact compliance
```

每个物理柔顺只出现一次。参数包去重失败时直接传播合同错误。

### 22.3 弹簧无拉力与硬限位

A 必须保证

\[
0\le\delta_{s,i}\le\delta_{\max}=4\ \mathrm{mm},
\qquad
F_{s,i}=k_{s,i}\delta_{s,i}\ge0
\]

在线性压缩分支成立。`delta_s=0` 且维持接触需要负压缩时，轴向弹簧约束释放或接触脱开；不得返回拉簧力。`delta_s=4 mm` 后，进一步相容位移由硬限位反力承担，响应不再是同一线性弹簧斜率。

达到硬限位本身不等于预载不可行：若硬限位分支的合法反力图可满足 `P_z`，平衡仍可存在；只有在已耗尽相容行程/图后仍无法平衡时，才返回 `PRELOAD_INFEASIBLE_HARD_STOP`。

### 22.4 刚性极限不能由大有限刚度替代

有限 `k_s` 增大可作为数值趋势检查，但

\[
\lim_{k_s\to\infty}\text{finite-spring representative}
\]

不必给出唯一的刚性反力分配。精确刚性约束可能具有零空间和集合值反力；因此正式刚性模式必须调用 A 的刚性分支和 graph 语义，不能选一个“大数”作为工程刚度。

### 22.5 用于解释与单元测试的局部线性代理

正式求解始终调用 A。仅为解释活动集和构造解析测试，可令向墙面压入坐标 `p=-u_z`，用一侧局部代理

\[
\boxed{
F_{z,i}^{\rm surrogate}
\approx k_{z,i}^{\rm alg}\,[p-p_i^{\rm on}]_+,
\qquad
\sum_iF_{z,i}^{\rm surrogate}=P_z.
}
\]

`p_i^{on}` 表示第 i 根针在当前 `u_x` 和历史下的起载位置，`k_{z,i}^{alg}` 是当前分支的投影算法刚度。该式说明共同位移只约束同一个 p，而不同起载位置和刚度会产生部分接触与不均载；它不是替代 A 的正式材料律，也不包含滑移、损伤或集合值刚性。

---

## 23. wrench、线性化、集合值图与混合控制凝聚

### 23.1 wrench 装配

若 A 未直接在 `G,O_A` 返回 wrench，先按 A→B 合同完成坐标旋转和参考点运输，再求和。每根针输出必须保留原参考点、运输矩阵、响应哈希和功检查。正式单元量为

\[
\mathbf W_U=\sum_i\mathbf W_i,
\qquad
\mathbf F_U=\sum_i\mathbf F_i,
\qquad
\mathbf M_U=\sum_i\left[\mathbf M_i^{O_i}+(\mathbf r_{O_i}-\mathbf r_{O_A})\times\mathbf F_i\right].
\]

不得把只有力没有力矩的逐针输出直接视作共同参考点 wrench。

### 23.2 原始逐针和单元线性化

在相容且可线性化的固定分支上，A 返回

\[
\mathbf K_i
=\frac{\partial\mathbf W_i^{G,O_A}}{\partial\mathbf q_U}
\in\mathbb R^{6\times2}.
\]

原始单元线性化为

\[
\boxed{
\mathbf K_{Wq}^{\rm raw}=\sum_i\mathbf K_i
=\begin{bmatrix}\mathbf K_{W,x}&\mathbf K_{W,z}\end{bmatrix}.
}
\]

其行单位为力/力矩，列单位为 mm，因此力行是 N/mm、力矩行是 N·mm/mm。广义 2×2 线性化为

\[
\mathbf K_{Qq}^{\rm raw}
=\mathbf H_U^{\mathsf T}\mathbf K_{Wq}^{\rm raw}.
\]

A 返回的 tangent status 必须逐针保存并按最弱质量聚合；不能无说明地对称化、正定化或把割线标成一致切线。

### 23.3 法向残量斜率

定义

\[
k_{zx}=\frac{\partial r_z}{\partial u_x}
=\mathbf E_Z^{\mathsf T}\mathbf K_{F,x},
\qquad
k_{zz}=\frac{\partial r_z}{\partial u_z}
=\mathbf E_Z^{\mathsf T}\mathbf K_{F,z}.
\]

由于 `u_z` 正向远离墙面，常见压缩分支可能有 `k_zz<0`；算法不得硬编码正刚度符号。事件、摩擦、硬限位或几何迁移处应使用 A 返回的一侧广义导数/割线/图，而不是跨分支中心差分。

### 23.4 恒 Pz 平衡路径上的凝聚切线

仅当当前分支唯一、`k_zz` 可逆且线性化状态允许时，隐函数关系给出

\[
\boxed{
\frac{du_z}{du_x}\bigg|_{P_z}
=-\frac{k_{zx}}{k_{zz}}.
}
\]

因此单元接触 wrench 沿恒主动推力平衡路径的凝聚切线为

\[
\boxed{
\mathbf K_{W,x\mid P_z}
=\mathbf K_{W,x}
-\mathbf K_{W,z}\frac{k_{zx}}{k_{zz}}.
}
\]

若同时允许主动推力微增量，

\[
du_z
=-\frac{k_{zx}}{k_{zz}}du_x
+\frac{1}{k_{zz}}dP_z,
\]

\[
d\mathbf W_U
=\mathbf K_{W,x\mid P_z}du_x
+\mathbf K_{W,z}\frac{1}{k_{zz}}dP_z.
\]

上述凝聚量的参考点、坐标、分支和 tangent status 必须随输出记录。`k_zz` 近奇异、响应集合值或只有割线时，不得输出普通唯一凝聚切线；应返回一侧候选、区间斜率或 admissible graph。

### 23.5 参考点变换的切线风险

若 A 没有直接在移动的 `O_A` 返回切线，静态 wrench 运输不足以保证切线正确，因为参考点随共同位姿变化可能产生几何项。B2 优先要求 A 返回目标参考点线性化；无法确认几何项时，单元切线标为 `unavailable`，但可保留经合同验证的 wrench。

### 23.6 集合值图的装配和输出

当任一针为 `set_valued_constraint`，B2 输出：

- 逐针 graph handle 和秩/零空间；
- 共同 normal resultant 可行集或查询句柄；
- 延续规则选取的代表 wrench（若 A 提供）；
- 代表值非唯一警告；
- 单元 `constraint_set_valued` 状态；
- 禁止用于普通有限差分和唯一材料曲线拟合的标志。

若多个图的相容和无法由独立 Minkowski 和保证，必须调用 A/合同提供的联合图查询或报告不可认证；不得自行拼接不相容支持力。

---

## 24. 外层活动集、半光滑/广义 Newton 与共同重调算法

### 24.1 试探路径原则

每个 Newton 迭代都从同一接受状态 `q_U^n` 构造完整试探目标

\[
\Delta\mathbf q_U^{(k)}
=
\begin{bmatrix}
 u_x^{\rm target}-u_x^n\\
 u_z^{(k)}-u_z^n
\end{bmatrix}.
\]

A 不接收“上一 Newton 迭代到下一迭代”的累积历史增量；否则会在未接受步骤中重复累计滑移、损伤或弹簧历史。`newton_iteration_id` 改变，但 `global_trial_id`、已接受历史和共享损伤快照保持一致。

### 24.2 主循环

```text
INPUT: accepted q_n, requested target u_x, Pz,
       immutable A states, one shared damage snapshot,
       B1 configuration, numerical/event configuration

0. Validate B1/A contract, units, hashes, models and motion subspace.
1. Set u_z predictor from the previous balanced state, a continuation
   predictor, or a geometry-safe search point. Initialize a legal bracket
   or trust interval inside I_z when available.
2. For k = 0 ... max_outer_iterations:
   a. Form the full common trial Δq^(k) from accepted state n.
   b. Call every needle with the same global_trial_id, common Δq^(k),
      same damage snapshot and read-only per-needle history.
   c. Preserve all A fields; reject/propagate fatal contract, domain,
      geometry, collision, model, parameter or stale-snapshot states.
   d. Reduce all suggested_common_increment_fraction values. If an
      unhandled event lies before the target, leave the current Newton
      solve and enter the common event-location loop of Section 25.
   e. Transport and assemble wrench, normal graph, raw linearization,
      diagnostics and all orthogonal state sets.
   f. Evaluate r_z for a unique branch or d_z/selected residual for a graph.
   g. Test force residual, A constraint violations, active/branch stability,
      event one-sided consistency and quality conditions.
   h. If converged, form a B2EquilibriumTrial; do not commit A history.
   i. Otherwise update u_z with a safeguarded branch-compatible step:
      semismooth/generalized Newton when valid, else a bounded secant,
      bisection/graph projection or continuation step.
   j. Re-call all needles at the new common target. No open or inactive
      needle may be skipped.
3. If iteration/backtracking limits are reached without a proof of physical
   infeasibility, return NUMERICAL_NONCONVERGENCE with the best trial and
   complete diagnostics.
```

### 24.3 Newton 更新与保护

在唯一光滑或可用一侧广义分支上，可使用

\[
\Delta u_z^{N}=-\frac{r_z}{k_{zz}},
\qquad
u_z^{k+1}=u_z^k+\eta\Delta u_z^{N},
\quad 0<\eta\le1.
\]

`eta` 由线搜索、信赖区、法向 admissible 区间和事件边界共同限制。若 `k_zz` 近奇异、方向不能降低残量/距离、跨越未知事件或超出 `I_z`，必须拒绝全 Newton 步。具体阈值、最大迭代和缩减系数属于版本化数值配置。

### 24.4 主动集更新

主动集不是独立猜测的物理模型，而是 A 响应的外层归约。每次评估后：

1. 从 A 的 active/near support、乘子和 force 更新 `O/N/G/L`；
2. 从逐支持 motion 更新粘滑集合；
3. 从 spring state 更新 `H`；
4. 从材料/针体事件更新 `E`，但不执行 B3 重分配；
5. 从 uniqueness/tangent/diagnostics 更新 `D/X`；
6. 若任何集合或 branch ID 改变，重新装配并继续迭代；
7. 只有残量和集合/一侧状态同时稳定，才可宣称收敛。

### 24.5 收敛判据结构

候选平衡至少满足：

\[
|r_z|
\le \varepsilon_F^{\rm abs}
+\varepsilon_F^{\rm rel}\max(P_z,|F_{U,z}|)
\]

或集合值分支的 `d_z` 对应容差；并且：

- 最后一次 `u_z` 更新在位置容差内，或残量已充分收敛且步长因退化被正确标记；
- 活动支持、粘滑、硬限位和 branch ID 在要求的一侧意义下稳定；
- A 的 gap、摩擦锥、梁、弹簧、材料和功残量满足各自合同配置；
- 没有未处理事件，或目标正是已定位事件并通过一侧一致性检查；
- `W_U`、`P_z`、控制/约束反力的符号和功闭合；
- 输出切线质量与其声明状态一致。

位置步长小但力残量大不能视为收敛；活动集稳定但 A 约束残量超限也不能接受。

### 24.6 数值方法证据边界

半光滑 Newton、primal-dual active set 和变分不等式求解可用于组织非光滑残量/约束，但本项目的低层摩擦、接触、硬限位和材料分支由 A 定义。外部算法资料不授权 B2 重写 A 本构，也不保证当前非凸、历史相关问题全局唯一；因此必须保留阻尼、括区间、分支延续、失败分类和图语义。

---

## 25. 共同事件分数、同时事件和一侧定位

### 25.1 最小共同事件分数

对当前完整共同增量，定义

\[
\boxed{
\gamma_{\rm common}
=\min_{i=1,\ldots,N}
\gamma_i,
\qquad
\gamma_i=\texttt{suggested\_common\_increment\_fraction}_i
\in(0,1].
}
\]

若 `gamma_common<1`，所有逐针试探回滚；不得只缩短触发事件的单根针。行优先序号只用于审计，不参与最小值相等时的物理决策。

### 25.2 重新求平衡而非直接缩放旧 u_z

事件分数最初相对于当前 accepted-to-target 路径给出。缩短共同步后，B2 必须在新的

\[
u_x^{\rm event}=u_x^n+\gamma_{\rm common}(u_x^{\rm target}-u_x^n)
\]

处重新求法向平衡 `u_z`，而不能把旧 Newton 解的 `u_z` 简单乘以 `gamma_common` 后直接接受。重新平衡可能改变事件位置，因此事件定位是“共同步长缩减—全阵列重调—事件括区间更新”的循环。

### 25.3 同时事件集合

令最早事件括区间为 `[gamma_i^-,gamma_i^+]`。所有与全局最早括区间在事件配置容差内相交的事件，以及 A 已明确返回的 simultaneous events，组成

\[
\mathcal E_{\rm sim}.
\]

该集合按事件物理 ID 和针 ID 的规范排序序列化，但求解结果不得依赖排序。若多个事件导致不同且等价的合法分支，返回 `EQUILIBRIUM_DEGENERATE`/分支集合，而不是按线程先后选择。

### 25.4 事件类型和 B2 处理边界

- **接触建立/释放、粘滑切换、支持迁移、弹簧硬限位**：B2 可定位并在 A 提供合法一侧 trial branch 时继续重新平衡；仍不提交历史。
- **局部材料起始、针体屈服/断裂或任何需要载荷重分配的不可逆事件**：B2 定位到事件侧，输出 `B3_REBALANCE_REQUIRED` 和完整试探集合；不得越过事件执行级联或损伤联合提交。
- **体部碰撞、域边界、几何质量失效**：不是普通可穿越事件，按对应终止/不可用状态处理。

### 25.5 事件一侧一致性

定位完成后至少验证：

1. 事件前一侧仍满足旧分支；
2. 事件点残量/事件函数在配置容差内；
3. 事件后一侧若被请求，A 返回的分支与事件类型一致；
4. 全阵列最早事件没有被其他针的新事件抢先；
5. 交换调用顺序不改变 `gamma_common`、`E_sim` 和诊断。

---

## 26. 搜索、硬限位、不可行、退化和失败传播

### 26.1 状态分类

B2 单元级 `status.all_codes` 保存全部诊断；`primary_status` 按确定性语义类别选取，不覆盖其他代码。至少区分：

| 单元状态 | 含义 | 后续处理 |
|---|---|---|
| `PRELOAD_SEARCH_CONTINUE` | 当前承载不足/全开放，但仍可合法向墙面搜索 | 继续共同减步和事件定位 |
| `BALANCED_UNIQUE` | 法向平衡存在，当前分支和所需 wrench 唯一 | 可交 B3/上层继续试探 |
| `BALANCED_DEGENERATE` | 平衡存在，但反力或分支集合值/非唯一 | 保留图、秩、代表值边界；不得普通排序拟合 |
| `EVENT_REDUCTION_REQUIRED` | 当前共同步跨越最早事件 | 缩短共同步并全阵列重调 |
| `B3_REBALANCE_REQUIRED` | 已定位不可逆失效事件 | 交 B3；B2 不越过事件 |
| `PRELOAD_INFEASIBLE_GEOMETRIC_LIMIT` | 达到几何最近位置仍无平衡 | 终止本构型预载 |
| `PRELOAD_INFEASIBLE_BODY_COLLISION` | 锥段/针杆/安装座碰撞先发生 | 纯球尖模型终止 |
| `PRELOAD_INFEASIBLE_DOMAIN_LIMIT` | 表面查询域边界先发生 | 结果不可用于物理排序 |
| `PRELOAD_INFEASIBLE_HARD_STOP` | 合法硬限位分支耗尽后仍不能平衡 | 终止本构型预载 |
| `EQUILIBRIUM_INFEASIBLE` | 已证明全部相容分支物理无解 | 可改变外部位置/设计，不得称数值失败 |
| `NUMERICAL_NONCONVERGENCE` | 尚不能证明无解，算法未收敛 | 减步、换配置或停止；不得称材料失效 |
| `MODEL_UNAVAILABLE` / `PARAMETER_UNAVAILABLE` | 必需模型或参数缺失 | 未认证，不进入设计排序 |
| `GEOMETRY_UNCERTAIN` / `OUT_OF_DOMAIN` | 几何质量/域不支持结论 | 停止或提高表面质量 |
| `STALE_SNAPSHOT` / `CONTRACT_VIOLATION` | 事务或调用错误 | 丢弃全部 trial 并修正调用 |

### 26.2 硬限位不可行的判定

某根针到硬限位不自动触发单元失败。只有当：

- 所需继续压入的全部相容针已达到硬限位或被其他边界阻止；
- 当前刚性硬限位 graph 仍不能包含 `P_z`；
- 没有可通过新接触进入的开放针；
- 结论通过事件和图查询认证；

才可使用 `PRELOAD_INFEASIBLE_HARD_STOP`。

### 26.3 错误不得伪装为零承载

`OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN`、`BODY_COLLISION_INVALID`、`MODEL_UNAVAILABLE`、`PARAMETER_UNAVAILABLE`、`STALE_SNAPSHOT` 和 `NUMERICAL_NONCONVERGENCE` 均不能把该针 wrench 置零后继续装配。它们使当前单元结果不可认证；输出可保留此前的 best trial 供诊断，但必须从正式物理排序中排除。

### 26.4 单元状态的确定性聚合

建议的 primary 状态优先级为：合同/陈旧错误 → 域/几何/碰撞/模型/参数致命错误 → 事件缩减或 B3 交接 → 已证明预载/平衡不可行 → 数值未收敛 → 平衡退化 → 平衡唯一 → 可继续搜索。该优先级只决定摘要代码；所有逐针和单元 `all_codes` 必须无损保存。

---

## 27. 单元、针级和载荷共享输出

### 27.1 单元级力学量

必须分别输出：

```text
contact_only:
  W_U = [F_U, M_U] at G,O_A
  F_U_x / F_U_y / F_U_z
  M_U_x / M_U_y / M_U_z
  grip_resistance_Rx
active_actuator:
  Pz / F_act / generalized_force_Q_act
control_and_constraints:
  x_displacement_control_reaction
  y_constraint_reaction
  rotational_constraint_reactions
balance:
  r_z or set_distance_d_z
  normal_graph / uniqueness / rank / condition
linearization:
  raw K_Wq / generalized K_Qq
  k_zx / k_zz
  condensed K_W,x|Pz when valid
  tangent status / branch / reference / units
```

实际接触 Z resultant、主动推力和支持点法向乘子必须分栏，避免把三个概念混为一体。

### 27.2 针级原始量

每根针至少保留：

- 总 A_on_B force/moment 及参考点；
- 全部支持点接触力、法向/切向乘子、gap、法向和切基；
- 几何/承载/粘滑正交状态；
- 弹簧压缩、弹簧力、剩余行程、硬限位反力；
- 梁位移、转角、根部力/矩、能量和模型有效性；
- 材料起始利用率、容量尺度、针体屈服/断裂裕度；
- 所有事件、括区间、共同步长建议；
- tangent/graph 状态、残量、质量、不确定性和错误；
- opaque trial/rollback 句柄、损伤 read/write set 和冲突签名。

### 27.3 针数统计

必须同时输出：

\[
N_{\rm nominal}=N,
\quad
N_{\rm geom}=|\mathcal G|,
\quad
N_{\rm load}=|\mathcal L|,
\quad
N_{\rm hardstop}=|\mathcal H|,
\quad
N_{\rm invalid}=|\mathcal X|.
\]

可再输出 `near_contact`、`stick`、`slip`、`event_pending` 和 `degenerate` 数量，但不能用任一数量乘平均单刺峰值代替实际 wrench 装配。

### 27.4 参数化载荷不均指标

指标必须绑定明确的非负载荷通道，不把法向、切向和容量混成一个分数。例如：

\[
\ell_i^{(z)}=\max(0,\mathbf E_Z^{\mathsf T}\mathbf F_i),
\qquad
\ell_i^{(x)}=\max(0,-\mathbf e_x^{\mathsf T}\mathbf F_i).
\]

对任选通道 `ell_i`，若 `sum ell_i>0`，定义

\[
w_i=\frac{\ell_i}{\sum_j\ell_j},
\qquad
\boxed{N_{\rm eff}=\frac{1}{\sum_iw_i^2}
=\frac{(\sum_i\ell_i)^2}{\sum_i\ell_i^2}}.
\]

还可输出：

\[
\mathrm{CV}=\frac{\operatorname{std}(\ell_i)}{\operatorname{mean}(\ell_i)},
\qquad
\rho_{\max/\rm mean}=\frac{\max_i\ell_i}{\operatorname{mean}(\ell_i)},
\]

以及 Gini 系数和逐针材料/针体/摩擦利用率分布。必须声明统计是否包含零载荷针，并分别报告法向与切向通道。B2 不固定最终论文综合评分。

### 27.5 供 B3 使用的完整试探包

`B2EquilibriumTrial` 必须使 B3 无需重建共同平衡即可继续：

```text
balanced q_trial / Pz / u_x target
all per-needle A responses and branch IDs
O/N/G/L/stick/slip/hardstop/event/invalid/degenerate sets
W_U / raw and condensed linearization or graph
simultaneous event set / event brackets / one-sided consistency
all opaque trial handles / rollback tokens
all damage read/write sets / conflict signatures
snapshot versions / request-response hashes
status codes / certification level
```

B3 可以要求在事件后一侧重新调用 A 并重新求共同平衡，但不得更改本文件定义的 wrench 方向、运动坐标或主动推力边界。

---

## 28. 四个核心现象的可计算机理解释

### 28.1 刚性阵列刺数增加不一定提高承载

机理链为：

\[
\text{共同刚性位移}
\rightarrow
\text{不同起载间隙/方向}
\rightarrow
\text{部分接触集合 }\mathcal L
\rightarrow
\sum_iF_{z,i}=P_z
\rightarrow
\text{少数针载荷集中或总载荷被分摊}
\rightarrow
\text{局部阈值/容量的不同触发次序}.
\]

增加名义针数只增大候选集合 `I`，不保证 `|L|` 同比例增加。固定总 `P_z` 下，新接触可能降低既有针的单针载荷，使某些阈值型挂接/微损伤不再触发；也可能因高度差继续架空。B2 通过 `N_nominal/N_geom/N_load`、逐针 force、利用率和 `N_eff` 直接检查，而不是使用文献06的特定“约 2–3 根”作为常数。文献06提供固定总载荷、硬面部分接触的趋势证据；文献07提供共同位移和起载差异导致扩展饱和的证据。

### 28.2 `2×5` 与 `5×2` 不等价

两者虽有相同 N，但 B1 已证明沿 x/y 的包络、有向分离向量、边缘和邻接计数不同。B2 进一步通过

\[
\{p_i^{\rm on},\mathbf n_i,\mathbf K_i,\text{capacity}_i\}
\]

把这些方向差异映射为不同活动集和载荷分配。沿 `+x` 搜索时，x 向长阵列具有更长的顺序遇障基线；y 向长阵列具有不同横向并发覆盖。若表面协方差各向异性或非平稳，转置后联合 gap/法向/容量分布不保持不变。只有在人为构造的各向同性、边界和加载完全对称的统计极限中，两个设计的集合统计才可能趋近；数据模型仍不得合并或旋转表面来强制等价。

### 28.3 存在依赖工况的弹簧刚度窗口

- **过硬**：很小压缩就建立大力，难以吸收针尖起载位置差，`N_load` 和 `N_eff` 接近刚性部分接触，少数针提前达到局部容量；
- **过软**：为建立给定力需要较大压缩，快速消耗 4 mm 行程，可能在其他针充分调动前进入硬限位；切向加载中力增长慢，局部接触可能先滑移/迁移；
- **中间区域**：能在不耗尽行程的情况下补偿一部分高度差，并使更多针在其局部容量内共同承载。

建议扫描时同时观察

\[
\rho_{\delta}=\max_i\frac{\delta_{s,i}}{4\ \mathrm{mm}},
\qquad
N_{\rm eff},
\qquad
\max_i\text{capacity utilization},
\qquad
\frac{dR_x}{du_x}\bigg|_{P_z},
\]

而不是寻找由文献10直接给出的唯一刚度。最优区间依赖表面、角度、针梁、`P_z`、局部材料容量和剩余行程；文献10只支持过硬/过软竞争和非理想分载趋势。

### 28.4 相同总主动推力仍会高度不均

外层仅施加一个标量约束

\[
\sum_i\mathbf E_Z^{\mathsf T}\mathbf F_i=P_z,
\]

没有 `F_i=F_j` 约束。逐针力由不同的 gap、局部法向/摩擦域、接触深度、梁/弹簧刚度、剩余行程、硬限位、历史损伤和材料容量决定。第 22.5 节代理式已表明，只要 `p_i^{on}` 或 `k_i` 不同，共同 p 下即不等载。文献10的区域实验显示实际分载位于完全均载和不分载之间，但其斜率不能用作本项目逐针分配系数。

---

## 29. 参数、证据、外部数值知识与迁移边界

| 内容 | 来源类别 | B2 使用方式 | 迁移边界 |
|---|---|---|---|
| 坐标、Pz 范围、刚性背板、弹簧 0–4 mm、无拉力、硬限位、输出和失败边界 | 工程事实 1.0.0 | 强制边界 | 不由文献或数值方法改写 |
| A_on_B wrench、状态所有权、切线/图、错误、事件和事务 | A_TO_B 1.0.0 accepted | 冻结公共语义 | B2 不重建 A 物理 |
| 格点、角度/长度、安装拓扑、哈希、共同增量和相关性 | B1 0.1.0 accepted | 完整继承 | 不在 B2 改写 |
| 固定总载荷下硬面部分接触、名义数与真实接触数分离 | 文献06 | 核心趋势和验证 | 特定接触数、材料、角度和载荷不迁移 |
| 共同位移、随机起载差异、硬限位和刺数收益饱和 | 文献07 | 主动集/共同位移验证基线 | 回差、刚度、5 mm 行程和“最弱停止”不作默认 |
| 过硬/过软柔顺窗口、实际分载介于两极之间 | 文献10 | 刚度扫描解释和不均载验证 | 软掌面、腱索、区域斜率和外推载荷不迁移 |
| 广义 Jacobian 与半光滑 Newton | 外部论文 `https://doi.org/10.1007/BF01581275` | 支持非光滑方程的一侧 Newton 组织 | 不保证本问题全局唯一，必须阻尼/延续 |
| primal-dual active set 与半光滑 Newton 等价思想 | 外部论文 `https://doi.org/10.1137/S1052623401383558` | 支持活动集作为非光滑 Newton 的实现视角 | 论文问题类别不同，不替代 A 接触状态 |
| 变分不等式求解器接口参考 | PETSc 官方文档 `https://petsc.org/release/manual/snes/#variational-inequalities` | 实现选型参考 | 当前模型含历史、事件和集合值图，不能直接视为普通 box VI |
| wrench 装配、混合控制凝聚、图距离、事件括区间、顺序不变归约 | GPT 通用力学/数值知识 | 形成可审查方程和算法合同 | 参数、材料律和收敛容差仍待实现验证 |

### 29.1 仍未固定的关键量

- 弹簧刚度和 `P_z` 的具体离散扫描点；
- 表面统计、摩擦、局部强度、接触柔顺和相关性；
- 高碳钢 E、屈服和断裂参数；
- A/B 数值绝对/相对残量、near-contact 带、事件括区间、最大迭代、阻尼和信赖区；
- 刚性 graph 的具体查询实现和分支延续规则；
- 载荷不均指标中用于论文排序的最终通道/组合；
- 制造回差和安装误差模型。

所有量必须通过版本化参数/配置表达，缺失时返回不可用或保留候选，不得隐藏默认值。

---

## 30. 验证矩阵、解析极限和失败含义

下表定义实现后的最小可复现测试。数值容差均来自版本化配置，不是本文件固定值。

| 编号 | 测试构造 | 期望结果 | 检验对象 | 失败含义 |
|---:|---|---|---|---|
| 1 | 全部针开放、`P_z>0`、仍有合法向墙行程 | `F_U=0`，状态 `PRELOAD_SEARCH_CONTINUE`，继续定位首次接触 | 第 20.4 节、OPEN_RESPONSE | 伪造接触力或过早宣称无解 |
| 2 | 全部开放且先到几何最近边界/体碰撞/域边界 | 分别返回对应预载不可行/碰撞/域状态 | 工程终止边界 | 错误类被改写为零承载 |
| 3 | 合成单针、外部 B2 标量平衡包围 embedded A 核 | 与 A 合同 standalone/embedded 等价测试一致；embedded 请求无 0.5 N | Pz 只施加一次 | 重复法向载荷或符号错误 |
| 4 | N 根同高、同参数、同状态的有限弹簧针，对称表面 | 唯一对称分支上置换后响应不变，载荷相等；总 Z 力为 Pz | 装配、对称性、共同平衡 | 调用顺序或 ID 影响物理结果 |
| 5 | 多个完全刚性同高接触，只有总法向约束 | 返回可行但反力集合值/退化，不强迫唯一等载 | graph、秩/零空间 | 用罚刚度伪造唯一材料曲线 |
| 6 | 两组已知起载高度差的刚性阵列 | 高点先进入 `G/L`，出现部分接触与集中；增加未接触名义针不自动增力 | 活动集和第 22.5 节代理 | 永久全接触或线性刺数相加 |
| 7 | 与测试6相同高度差、独立弹簧且所需压缩 <4 mm | 合法弹簧压缩补偿高度差，`N_load/N_eff` 可增加，无拉力 | 弹簧分支、载荷共享 | 压缩方向/单位/状态错误 |
| 8 | 逐步把一根弹簧推到 4 mm | 事件被定位，随后切换硬限位；压缩不超过 4 mm，额外反力单列 | 共同事件、硬限位 | 穿越行程或重复计力 |
| 9 | `k_s` 极小并保留有限行程 | 压缩/行程消耗主导，可能较早硬限位；不得产生拉力 | 过软极限 | 将软弹簧等同理想均载 |
| 10 | 有限 `k_s` 逐渐增大并与正式 RIGID_MOUNT 比较 | 几何/位移趋势可接近刚性，但刚性非唯一时不要求力分配极限唯一 | 刚性极限语义 | 用任意大 k 替代刚性图 |
| 11 | 光滑唯一分支对 `u_x/u_z` 做一侧或中心有限差分 | `K_Wq` 与差分一致，凝聚切线满足隐函数式 | 切线装配/凝聚 | 参考点、符号或重复柔顺错误 |
| 12 | 摩擦、接触建立、硬限位附近差分 | 不宣称 smooth tangent；状态为一侧/分支/割线/图 | tangent status | 跨事件差分冒充一致切线 |
| 13 | 两针同一共同步同时临界，交换串行/并行调用顺序 | `gamma_common`、`E_sim`、平衡和诊断不变，或明确非唯一 | 同时事件与顺序不变性 | 行优先序号污染物理结果 |
| 14 | `2×5` 与 `5×2` 使用同一各向异性表面坐标和 +x 搜索 | 允许不同活动集、力和统计；不得旋转表面 | B1 方向性到 B2 映射 | 转置阵列被错误合并 |
| 15 | 人工构造各向同性、周期边界和对称统计样本 | 两转置设计在足够样本下可趋向统计一致，但 ID/数据仍独立 | 统计极限 | 把单样本差异误判为代码错误 |
| 16 | 对完整平衡结果做作用—反作用、参考点和功检查 | `F_U,z=Pz`；x 控制反力和 y/矩约束反力闭合；功符号一致 | 第 19 节 | wrench 方向/力矩运输错误 |
| 17 | 分别注入域外、几何不确定、体碰撞、模型/参数缺失、物理无解、退化和数值未收敛 | 每类独立触发且保留原始针级代码 | 第 26 节 | 失败分类相互替换 |
| 18 | 文献趋势对照：硬面刚性部分接触、起载差异收益饱和、过硬/过软窗口 | 只要求方向和机制一致，不拟合文献具体接触数/载荷 | 证据迁移边界 | 过拟合外部样机数值 |

### 30.1 可直接解析检查的最小代理

对 N 根同高同刚度有限弹簧代理

\[
F_{z,i}=k[p-p_0]_+,
\]

在全部承载且未到限位时应有

\[
F_{z,i}=\frac{P_z}{N},
\qquad
p=p_0+\frac{P_z}{Nk}.
\]

该结果仅用于唯一对称分支单元测试。精确刚性同高接触中只固定 `sum F_i=P_z` 和非负/局部可行性，单针分配可非唯一。

### 30.2 验证状态说明

本轮已完成方程、状态、接口和测试构造审查；尚未运行真实 A 实现或实验数据。实现关闭条件是按表中输入构造自动测试，记录全部版本、容差、结果哈希和失败分类。规范完成不等于代码或实验已验证。

---

## 31. B2 对 B3 的正式交接与禁止反向改写

### 31.1 B3 可直接使用

B3 接收第 27.5 节完整 `B2EquilibriumTrial`，并可：

- 对已定位材料/针体失效事件调用事件后一侧 A trial；
- 重新求第 20 节同一个共同法向平衡；
- 处理载荷重分配和级联；
- 发现并联合解决共享损伤 write-set 冲突；
- 在全局步接受后准备和执行原子提交；
- 推进连续 100 mm 历史和再挂接。

### 31.2 B3 必须原样继承

- `q_U=[u_x,u_z]` 和正方向；
- 每单元 `P_z` 只在外层施加一次；
- A_on_B wrench、共同 `O_A`、力矩运输和功方向；
- 全阵列重新调用、同一损伤快照和共同最小事件分数；
- 正交针级状态和错误分类；
- 刚性 graph、弹簧无拉力、4 mm 硬限位和柔顺去重；
- 原始/凝聚线性化的状态标签。

### 31.3 B3 不得做

B3 不得把 G4 邻接变成固定转移权重，不得用失效针峰值直接分给邻针，不得修改 A 的损伤律、摩擦、梁/弹簧本构或 B1 几何，也不得只提交部分“成功针”。

### 31.4 C 层边界继续有效

C 只能调用完成 B3/B 集成后的单元响应。当前 B2 的 `W_U` 和切线/图可作为接口设计输入，但尚不构成已接受的 B_TO_C 合同；C 不得直接操作针级 A 状态来绕过 B 的共同平衡和事务。

---

## 32. B2 完成判据核对与未决问题

### 32.1 完成判据核对

本候选已形成：

1. B1+B2 最新完整上下文；
2. 给定 `u_x/P_z` 求 `u_z` 的唯一/集合值外层问题；
3. 主动推力、接触 resultant、控制反力、约束反力和功方向的分离；
4. 针级正交状态与全部外层集合；
5. 刚性/独立弹簧统一 graph/残量框架；
6. 逐针 wrench 和线性化到单元量的装配与混合控制凝聚；
7. 可转程序的全阵列重调、半光滑/广义 Newton、保护和收敛结构；
8. 共同最小事件分数、同时事件和事件后一侧边界；
9. 搜索、预载不可行、物理无解、退化、数值失败和不可用分类；
10. 单元/针级输出和载荷不均候选指标；
11. 四个核心现象的方程/状态/验证链；
12. 不越过 B3 的完整试探交接。

### 32.2 仍未决的问题

1. A 刚性 admissible graph 的具体数据结构、查询算子和联合相容装配实现；
2. 非单调 normal graph 下的全局括区间/分支延续策略；
3. B2 数值容差、最大迭代、阻尼、信赖区和事件括区间；
4. 弹簧刚度与 Pz 的正式离散点；
5. 真实 CAD、制造回差、安装误差和表面方向统计；
6. 高碳钢、接触、摩擦、表面局部强度和损伤参数；
7. 载荷不均/能力利用指标用于论文排序的最终选择；
8. B3 失效重分配、共享损伤冲突、再挂接和原子提交；
9. 实现级自动测试、结果哈希和实验趋势验收。

所有未决项保留为参数、接口或明确失败状态；没有因推导方便而静默关闭。

---

## 33. 输出前最终自检结论

- 已完整阅读工程事实、模块规划、B2 提示词、四个模板、A→B 合同、B1 完整上下文以及文献06/07/10 压缩包中的全部证据卡和关键图片；
- 本文是 B1+B2 最新完整候选，不是 B2 增量；
- B1 几何、索引、角度、实际长度、安装拓扑、身份/哈希、共同运动、相关性和 A 请求语义已保留；
- 每单元 `P_z` 只在 B2 外层施加一次，未出现每针 0.5 N 或平均分载；
- `u_z` 外层未知量、唯一/集合值残量、活动状态、切线/图和收敛条件闭合；
- A_on_B wrench、共同参考点、作用—反作用、力矩运输和功方向一致；
- 刚性非唯一、弹簧无拉力、4 mm 硬限位、针梁开关和柔顺去重均保留；
- 接触、承载、粘滑、弹簧、材料、质量和唯一性未压扁为单一布尔量；
- 开放针在共同位置变化后仍重新调用；
- 全部针使用同一共同增量和共享损伤快照，事件采用共同最小分数并全阵列重调；
- 同时事件、物理无解、退化和数值未收敛分别处理；
- 域外、体碰撞、模型/参数不可用未伪装为零承载或材料失效；
- 输出足以支持 B3，但未执行失效后级联、共享损伤提交、连续再挂接或完整历史；
- 四个核心现象均有状态、方程和验证量支撑；
- 文献06/07/10 的特定数值和机构未被外推为工程事实；
- 本轮未发现工程事实变化，所有未决参数和实现风险继续显式保留。


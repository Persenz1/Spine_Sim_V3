# B_MODULE_CONTEXT — 刚性/独立弹簧阵列爪单元算子

> 大模块：`B`  
> 当前完成阶段：`B1`  
> 上下文候选版本：`0.1.0`  
> 工程事实版本：`1.0.0`  
> 上游合同：`A_TO_B 1.0.0 accepted`  
> 提示词版本：`B1 1.0.0`  
> 运行：`B1-r01`  
> 当前状态：`candidate`

本文是大模块 B 在完成 B1 后的首版完整上下文。本文中的“必须”“不得”“可”分别表示强制要求、禁止事项和在不改变强制语义前提下允许的实现选择。

---

## 1. 范围、目标与层级边界

### 1.1 B1 已覆盖的物理与数据问题

B1 建立不可变的阵列配置与运动学算子

\[
\mathcal G_{B1}:
(n_x,n_y,s,\text{角度模式},\text{针级参数},\text{安装拓扑},\mathbf q_U)
\mapsto
(\text{针级身份/几何},\text{基座位姿/共同增量},\text{A 请求骨架},\text{拓扑/相关性元数据}).
\]

B1 已定义：

1. `2×2` 至 `6×6` 规则矩形阵列的唯一索引、针尖球心格点、针级身份和边界标签；
2. 固定角、`80°→50°` 和 `80°→60°` 两种线性梯度的统一参数化；
3. 梯度阵列实际露出长度、球心初始共面和安装座出口反算；
4. 刚性背板局部 x/全局 Z 共同平移到全部针基座位姿和 A 规定增量的映射；
5. `RIGID_MOUNT` 与 `AXIAL_SPRING_MOUNT` 的统一外部记录、不同内部状态所有权和限位语义；
6. 实际露出长度对几何、力臂、碰撞包络、梁参数及配置哈希的一致绑定；
7. 边缘、行列、邻接、有向分离向量、阵列包络和表面空间相关性查询接口；
8. 标量、按 x 排和完整针级数组的规范化扩展接口；
9. 严格继承 `A_TO_B 1.0.0` 的逐针 `embedded_constitutive_trial` 请求/响应交接。

### 1.2 B1 明确不处理的内容

B1 不求解任何接触力、弹簧平衡值或活动接触集。以下内容属于后续阶段：

- **B2**：给定切向位移时的背板法向位置、每单元恒定主动推力、活动接触集、针间载荷共享、共同残量和 Newton/互补求解；
- **B3**：针失效后的重分配、共享损伤冲突联合重求解、级联、连续再挂接和单元力—位移历史；
- **C**：四单元同步收紧、内部预紧、偏心 wrench、整体摇摆和整爪渐进失效；
- **A**：球尖可达性、复合针体碰撞、接触、摩擦、梁/弹簧本构、滑移、材料容量、损伤、释放和再挂接。

B1 不允许用单刺峰值乘刺数，不允许把每单元 `0.5–2 N` 主动推力平均分到各针，也不生成整爪 wrench 或成功/停止阈值。

### 1.3 权威顺序与冲突结论

权威顺序为：工程事实 `1.0.0` > `A_TO_B 1.0.0 accepted` 的 A 调用语义 > 模块规划与 B1 提示词 > 模板 > 文献与外部通用知识。

本轮未发现工程事实与 A→B 合同之间的语义冲突。存在一个实现闭合问题而非事实冲突：梯度阵列规定规则的是**未加载球心投影格点**，反算后的安装座出口在局部 x（未来非零偏航时还在 y）方向发生非等距偏置；真实 CAD 是否能容纳该安装孔/导向布局必须另行检查，不能把针尖中心距静默改成安装孔中心距。

### 1.4 必须继承的工程事实

B1 直接依赖并不得改写的事实至少包括：

- `COORDINATE.GLOBAL.FRAME`、`COORDINATE.UNIT.FRAME`、`COORDINATE.NEEDLE.AXIS`；
- `KINEMATICS.UNIT.RIGID_BOARD`；
- `NEEDLE.TIP.GEOMETRY`、`NEEDLE.CONTACT.COLLISION_BOUNDARY`、`NEEDLE.LENGTH.EXPOSED`、`NEEDLE.DIAMETER.SET`、`NEEDLE.MATERIAL.BASE`、`NEEDLE.BENDING.SWITCH`、`NEEDLE.EMBEDMENT.MODEL_BOUNDARY`；
- `ARRAY.TOPOLOGY.RECTANGULAR`、`ARRAY.SPACING.SET`、`ARRAY.ANGLE.FIXED_SET`、`ARRAY.ANGLE.LINEAR_GRADIENTS`、`ARRAY.ANGLE.GRADIENT_LENGTH_COMPENSATION`、`ARRAY.NEEDLE.DATA_EXTENSIBILITY`；
- `ARRAY.MOUNT.RIGID_MODE`、`ARRAY.MOUNT.AXIAL_SPRING_MODE`；
- `SURFACE.INTERFACE.UNIFIED`、`SURFACE.HEIGHT_FIELD.PRIMARY`、`SURFACE.TRIANGLE_MESH.SECONDARY`、`SURFACE.PARAMETERS.UNRESOLVED`；
- `LOAD.NORMAL.ACTUATOR_OUTPUT`、`LOAD.NORMAL.ARRAY_UNIT`、`LOAD.DRAG.SPEED`、`LOAD.DRAG.QUASI_STATIC`、`NUMERICS.DRAG.VARIABLE_STEP`、`LOAD.DRAG.TRAVEL`；
- `DAMAGE.MEMORY.LIGHTWEIGHT`、`SCOPE.FIRST_RELEASE.EXCLUSIONS` 和 `UNRESOLVED.REGISTRY.GLOBAL`。

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

B1 已在规范层满足：统一阵列生成、角度/长度闭合、球心—基座反算、共同运动、统一安装接口、实际长度一致传递、方向性/相关性表示、针级扩展、A 合同适配和 B2/B3 交接。当前状态仍为 `candidate`，表示代码、真实 CAD、表面测量和实验尚未完成；这不改变 B1 数据与运动学合同的闭合性。

---

## 16. 对 B2、B3 和 C 的交接

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

## 17. 输出前自检结论

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

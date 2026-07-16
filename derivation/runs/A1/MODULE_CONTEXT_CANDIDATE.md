# A_MODULE_CONTEXT

> 大模块：`A`——从随机表面到单刺连续啮合算子  
> 当前完成阶段：`A1`——地形生成、有限针尖可达性与几何候选  
> 上下文版本：`0.1.0`  
> 工程事实版本：`engineering_fixed_context 1.0.0`  
> 执行提示词版本：`A1 1.2.0`  
> 当前状态：`candidate`

本文档是大模块 A 在 A1 完成后的首版完整滚动上下文。它给出可直接实现和审查的几何规范，但不包含求解器代码。固定工程事实以事实 ID 标注；本地证据分别记为 `[L01]`、`[L11]`、`[L12]`、`[L16]`；外部原始或官方来源记为 `[E-*]`；通用数学、随机场、计算几何和数值分析知识记为 `[GPT]`。这些标记只说明证据层级，不把文献示例数值升级为工程固定值。

---

## 1. 范围、目标与不可越界边界

### 1.1 A1 的算子位置

完整物理链为

$$
\text{表面几何}
\rightarrow
\text{单刺状态演化}
\rightarrow
\text{阵列活动接触集与载荷共享}
\rightarrow
\text{十字对爪整体平衡}.
$$

A1 只构造最底层几何算子

$$
\boxed{
\mathcal G_{A1}:
(\text{表面数据/参数},\ \text{针体几何},\ \text{针姿态},\ \text{运动路径})
\mapsto
(\text{可达几何},\ \text{间隙},\ \text{首次接触},\ \text{方向候选},\ \text{禁止碰撞})
}
$$

它回答四类问题：

1. 表面如何生成、导入、预处理并证明在目标尺度上可信；
2. 有限半径球形针尖的球心能到达哪里、对应原表面接触点在哪里；
3. 首次合法球尖接触何时发生，局部几何是否具有抵抗局部 $+x$ 拖拽的必要方向分量；
4. 锥段、圆柱针杆或安装座是否先发生禁止碰撞。

A1 的输出是 A2/A3 以及后续阵列、整爪层唯一共享的表面几何入口。上层不得按红砖、混凝土或砂纸复制一套接触几何，也不得重新定义球尖可达性。[EF:PROJECT.ARCHITECTURE.DEPENDENCY] [EF:SURFACE.INTERFACE.UNIFIED]

### 1.2 本阶段明确不处理

以下问题不属于 A1，任何相关字段只能保留为空值、占位符或下游接口：

- 库仑摩擦锥、粘着/滑移和摩擦稳定；
- 接触力、法向主动推力平衡、抓附力或承载概率；
- 针体弯曲、独立轴向弹簧压缩和结构柔顺；
- 红砖/混凝土压碎、剪裂、断裂、损伤和强度域；
- 已接触后的连续接触点迁移、脱离和再挂接；
- 多刺活动集、阵列载荷共享和统计独立性；
- 十字对爪同步预紧、整体 wrench 和偏心承载；
- 显式裂纹、碎屑、磨损与地形重网格化。

因此，A1 中的“方向候选”只是进入 A2 的必要几何筛选，不等价于稳定挂接、可承载接触或成功抓附。[L01][L16]

### 1.3 必须遵守的工程事实

A1 直接受以下事实约束：

| 领域 | 事实 ID | A1 中的约束 |
|---|---|---|
| 物理架构 | `PROJECT.ARCHITECTURE.DEPENDENCY` | 高层只能复用 A1 几何入口。 |
| 全局坐标 | `COORDINATE.GLOBAL.FRAME` | 墙面名义平面为全局 $X$-$Y$，$+Z$ 指向背板/自由空间。 |
| 单元坐标 | `COORDINATE.UNIT.FRAME` | 局部 $+x$ 从头部指向根部，也是搜索和拖拽方向。 |
| 针轴 | `COORDINATE.NEEDLE.AXIS` | 采用已固定的 $\alpha,\beta$ 方向定义，当前 $\beta=0$。 |
| 背板运动 | `KINEMATICS.UNIT.RIGID_BOARD` | A1 接收沿局部 $x$ 与全局 $Z$ 的刚体平移路径。 |
| 针尖 | `NEEDLE.TIP.GEOMETRY` | $R_t\in\{50,100\}\ \mu\mathrm m$；只表示局部球面曲率。 |
| 承载边界 | `NEEDLE.CONTACT.COLLISION_BOUNDARY` | 仅局部球形针尖可作为承载接触；其余部位只做禁止碰撞。 |
| 露出长度 | `NEEDLE.LENGTH.EXPOSED` | 固定角阵列安装座出口至针尖球心 $L_e=4\ \mathrm{mm}$。 |
| 针径 | `NEEDLE.DIAMETER.SET` | $d\in\{0.6,0.8\}\ \mathrm{mm}$。 |
| 表面类别 | `SURFACE.CATEGORIES.FIRST_RELEASE` | 红砖、混凝土和不同目数砂纸；具体砂纸目数未固定。 |
| 统一接口 | `SURFACE.INTERFACE.UNIFIED` | 高度场与三角网格共享同一查询合同。 |
| 主表示 | `SURFACE.HEIGHT_FIELD.PRIMARY` | 主区域 $150\times150\ \mathrm{mm}$，$z=h(x,y)$。 |
| 网格分支 | `SURFACE.TRIANGLE_MESH.SECONDARY` | 完整网格用于非单值结构和三维碰撞，不另建接触机理。 |
| 未决表面参数 | `SURFACE.PARAMETERS.UNRESOLVED` | PSD、分布、相关长度、各向异性、非高斯、粒度/密度、分辨率、种子数均不得硬编码。 |
| 数值推进 | `NUMERICS.DRAG.VARIABLE_STEP` | 采用可变位移步长和事件定位，不能改物理速度替代减步。 |
| 拖拽工况 | `LOAD.DRAG.SPEED`, `LOAD.DRAG.TRAVEL` | 物理速度 $1\ \mathrm{mm/s}$，单刺/阵列行程 $100\ \mathrm{mm}$。 |
| 未决登记 | `UNRESOLVED.REGISTRY.GLOBAL` | A1 判据、统计、分辨率、样本数和事件容差保留显式未决项。 |

---

## 2. 坐标、几何对象、符号与单位

### 2.1 坐标与实体侧定义

全局正交基为 $\{\mathbf E_X,\mathbf E_Y,\mathbf E_Z\}$，墙面名义平面为 $Z=0$，$+Z$ 从墙面指向针体和背板。每个爪单元局部基为 $\{\mathbf e_x,\mathbf e_y,\mathbf E_Z\}$，其中 $\mathbf e_x$ 是搜索/拖拽方向，$\mathbf e_y=\mathbf E_Z\times\mathbf e_x$。[EF:COORDINATE.GLOBAL.FRAME] [EF:COORDINATE.UNIT.FRAME]

对单值高度场，墙体实体定义为

$$
\Omega_h=\{(x,y,z)\in\mathbb R^3:\ z\le h(x,y)\},
$$

自由空间为 $\mathbb R^3\setminus\Omega_h$。原表面外法向始终指向自由空间；若 $h$ 可微，

$$
\boxed{
\mathbf n_h(x,y)=
\frac{(-h_x,-h_y,1)}{\sqrt{1+h_x^2+h_y^2}}
}
$$

为无量纲单位向量。该符号约定保证：沿 $+x$ 的上坡面 $h_x>0$ 有 $\mathbf n_h\cdot\mathbf e_x<0$，墙面对针尖的法向方向具有抵抗 $+x$ 运动的分量。

对完整网格，$\Omega_m$ 必须是定向、闭合或经明确“向下封闭”的墙体实体；开放薄片若没有实体侧定义，不能给出可靠非穿透符号，只能返回 `orientation_undefined`，不得用最近三角形法向猜测内外侧。[GPT]

### 2.2 针轴和刚体姿态

安装座出口指向针尖球心的单位针轴为

$$
\boxed{
\mathbf a=
\cos\alpha\cos\beta\,\mathbf e_x+
\cos\alpha\sin\beta\,\mathbf e_y-
\sin\alpha\,\mathbf E_Z
}
$$

当前正式工况 $\beta=0$，故

$$
\mathbf a=\cos\alpha\,\mathbf e_x-\sin\alpha\,\mathbf E_Z.
$$

设针尖球心为 $\mathbf c_t$，安装座出口为 $\mathbf m$，则固定角单针有

$$
\mathbf c_t=\mathbf m+L_e\mathbf a,
\qquad L_e=4\ \mathrm{mm}.
$$

A1 接收一般刚体位姿 $\mathbf q=(\mathbf r,\mathbf R)$ 或等价齐次变换 $\mathbf T\in SE(3)$；当前单刺/阵列背板主线只有 $u_x,u_z$ 平移，但底层查询不把零转动硬编码为永久限制。

### 2.3 核心符号表

| 符号 | 含义 | 单位 |
|---|---|---|
| $h(x,y)$ | 相对名义平面的原始/处理后高度 | mm |
| $L_x,L_y$ | 正式查询区域尺寸，当前均为 $150$ | mm |
| $\Delta x,\Delta y$ | 数值采样/网格间距 | mm |
| $\mathbf q=(q_x,q_y)$ | 二维角波数向量 | rad/mm |
| $C_h(\mathbf q)$ | 二维高度 PSD（本文约定） | mm$^4$ |
| $R_t$ | 局部球形针尖半径 | mm（输入可用 $\mu$m，入算子前换算） |
| $\mathbf c_t$ | 针尖球心 | mm |
| $\mathbf p_j$ | 第 $j$ 个原表面接触/支持点 | mm |
| $\mathbf n_j$ | 从墙体指向针尖的接触法向 | 1 |
| $H_R(x_c,y_c)$ | 完全球尖的最低球心高度包络 | mm |
| $g_t$ | 合法球冠针尖有符号几何间隙 | mm |
| $g_k$ | 非承载部件 $k$ 的有符号净间隙 | mm |
| $\delta_{\rm clr,k}$ | 部件 $k$ 的安全间隙 | mm，未决 |
| $\mathbf d$ | 单位搜索/拖拽方向，主线 $\mathbf d=\mathbf e_x$ | 1 |
| $\eta_x=-\mathbf n\cdot\mathbf d$ | 抵抗 $+x$ 的方向几何裕度 | 1 |
| $\phi_g=\arcsin\eta_x$ | 有符号几何坡向角 | rad 或 °，接口必须标明 |
| $\xi$ | 沿给定运动路径的标量参数 | mm（若采用弧长参数化） |
| $\epsilon_g,\epsilon_x,\epsilon_n$ | 间隙、事件位置和法向数值容差 | mm、mm、rad，未决 |

除工程输入显示外，内部统一使用 mm、N、s、rad；所有角度字段必须携带单位标签，禁止在同一公式链静默混用度和弧度。

---

## 3. 输入、输出、状态与统一数据合同

### 3.1 `SurfaceConfig`：统一表面配置

每个表面实现必须由不可变配置和可追溯实现标识。最低字段如下：

| 字段组 | 必需字段 | 说明 |
|---|---|---|
| 身份与版本 | `surface_id`, `realization_id`, `config_version`, `parameter_set_id`, `created_by` | 区分材料类别、模型参数和随机实现。 |
| 材料标签 | `material_class`, `material_subtype`, `finish_or_treatment`, `grit_designation` | `material_class` 为红砖/混凝土/砂纸；砂纸目数可为空，且不等同地形参数。 |
| 表示后端 | `backend={height_field, triangle_mesh, hybrid}`, `generator_or_importer` | 不同后端通过同一查询接口进入上层。 |
| 坐标与单位 | `frame_id`, `origin`, `basis`, `length_unit`, `height_sign` | 必须能映射到全局 $X$-$Y$-$Z$ 和单元局部方向。 |
| 区域 | `nominal_domain`, `generated_domain`, `crop_window`, `halo_width`, `boundary_policy` | 正式输出为 $150\times150$ mm；生成域/测量域可更大。 |
| 有效性 | `valid_mask`, `domain_mask`, `quality_mask`, `excluded_regions` | 缺失区、遮挡、边界和仪器异常不得被静默填平。 |
| 测量元数据 | 仪器、探头/光学方式、横纵采样、竖向噪声、标定、拼接误差、滤波、日期 | 区分物理分辨率、采样间距和数值网格。[L12][L16] |
| 可信尺度 | `trusted_q_region`, `trusted_lambda_min/max`, `directional_band`, `transfer_function`, `snr_rule` | 允许方向相关可信波段，不能只保存一个“分辨率”数字。 |
| 合成统计 | `psd_model`, `marginal_model`, `anisotropy_model`, `feature_process`, `seed` | 未启用项为显式 `null`，不得用隐藏默认值。 |
| 可复现性 | `master_seed`, `stream_id`, `sample_index`, `algorithm_version`, `parameter_hash` | 相同配置与算法版本必须重现同一地形。 |
| 不确定性 | `height_uncertainty`, `lateral_uncertainty`, `normal_uncertainty`, `model_form_uncertainty` | 供候选边界和后续敏感性分析使用。 |
| 下游占位 | `friction_parameters`, `local_strength_parameters` | A1 保留字段但不填未经批准的唯一值。 |

随机数采用可分流的伪随机流：主种子只定义试验族，`surface_id/parameter_set_id/sample_index` 经确定性哈希派生子流。这样改变并行顺序不会改变样本内容。种子数量和样本数仍属于未决项。[EF:SURFACE.PARAMETERS.UNRESOLVED]

### 3.2 高度场与三角网格数据

#### 3.2.1 `HeightFieldData`

至少包含：

- 规则或非规则二维节点坐标；
- 原始高度、处理后高度和被移除的宏观形状；
- 有效掩膜、质量掩膜和每点/每单元不确定度；
- 插值器类型、插值阶次、边界策略及其误差记录；
- 原始二维 PSD、窗口化 PSD、方向谱、相关函数和谱矩；
- 处理历史的有序记录，不覆盖原始数据；
- 用于局部碰撞的图面三角化及 BVH/AABB 索引。

#### 3.2.2 `TriangleMeshData`

至少包含：

- 顶点、三角形、连通关系、面朝向和单位；
- 闭合性、流形性、自交、退化三角形和法向一致性检查结果；
- 若由高度场生成，保存源高度场 ID、三角化规则和封闭底面位置；
- 若由点云重建，保存配准、去噪、重建、孔洞处理和误差元数据；
- 面/边/顶点特征索引、BVH/AABB 树、可选有符号距离加速结构；
- 原始点云与重建网格的偏差分布，避免把插值网格精度误当测量精度。[L16]

### 3.3 统一几何查询接口

高度场和网格必须实现同一逻辑合同；具体算法可以不同。

| 查询 | 输入 | 最低输出 |
|---|---|---|
| `query_domain(x)` | 点或 AABB | 域内/域外、掩膜、距有效边界距离、质量等级 |
| `query_raw_surface(x,y,scale)` | 平面坐标、显式尺度 | 高度/最近点、原表面法向、局部拟合、残差、可信性 |
| `query_signed_distance(p)` | 三维点 | 到墙体实体的有符号距离、最近点集合、特征类型、符号可靠性 |
| `query_tip_center(c,R,a,cap)` | 球心、半径、轴向、球冠参数 | 竖向包络残差、统一欧氏间隙、合法球冠间隙、支持点集合、径向法向、质量 |
| `query_rigid_part(T,K,clearance)` | 位姿、部件几何、安全间隙 | 净间隙、最近点对、碰撞部件、法向、保守/精确标记 |
| `query_neighborhood(region)` | 圆/球/AABB | 局部节点/三角形及其索引，用于拟合与缓存 |

所有查询都返回：`status`、`value`、`tolerance_used`、`data_quality`、`uncertainty_bound`、`source_surface_id`。若数据不足，不得返回伪精确法向或间隙，而应返回 `GEOMETRY_UNCERTAIN` 或 `OUT_OF_DOMAIN`。

### 3.4 A1 主状态与附加标签

A1 的互斥主状态集合为

$$
\mathcal Z_{A1}^{\rm primary}=\{
\texttt{SEPARATED},
\texttt{TIP\_TOUCH},
\texttt{BODY\_COLLISION\_INVALID},
\texttt{GEOMETRY\_UNCERTAIN},
\texttt{OUT\_OF\_DOMAIN}
\}.
$$

主状态含义：

- `SEPARATED`：合法球冠和所有非承载部件均有正净间隙；
- `TIP_TOUCH`：合法球冠首次达到零间隙，且其他部件仍满足安全间隙；
- `BODY_COLLISION_INVALID`：锥段、针杆或安装座越过安全间隙，不能继续按纯球尖接触处理；
- `GEOMETRY_UNCERTAIN`：测量带宽、缺失区、法向退化或数值误差使结论无法可靠分类；
- `OUT_OF_DOMAIN`：针体查询包络超出有效表面域。

`DIRECTION_CANDIDATE` 不是与 `TIP_TOUCH` 互斥的主状态，而是只附着在合法 `TIP_TOUCH` 记录上的几何标签。它至少包括 `candidate_any`、`candidate_robust` 和 `uncertain` 三种结果；这样不会把“已接触”和“方向上可能阻挡”混成一个状态。

主状态转换如下：

| 当前主状态 | 最早事件 | 新主状态 | 附加处理 |
|---|---|---|---|
| `SEPARATED` | 合法球冠间隙到零，所有体碰撞间隙仍为正 | `TIP_TOUCH` | 恢复支持集并计算方向标签 |
| `SEPARATED` | 任一锥段/针杆/安装座净间隙到零或以下 | `BODY_COLLISION_INVALID` | 即使球尖同时接触，也保留无效优先级 |
| 任意 | 查询越过有效域 | `OUT_OF_DOMAIN` | 终止当前路径区间 |
| 任意 | 数据/法向/带宽不足以分类 | `GEOMETRY_UNCERTAIN` | 可局部加密或切换高保真分支后重试 |

A1 对固定表面和姿态是无物理历史的确定性几何算子。只允许保存数值缓存、前一安全步、事件括区和表面查询缓存；这些不构成材料或接触历史。滑移、损伤和再挂接历史由 A3 定义。

---

## 4. 地形生成与导入机理

### 4.1 二维 PSD 约定与有限波数窗

#### 4.1.1 连续定义

对零均值、二阶平稳高度场 $h(\mathbf x)$，本文采用

$$
R_h(\mathbf r)=\langle h(\mathbf x+\mathbf r)h(\mathbf x)\rangle,
$$

$$
\boxed{
C_h(\mathbf q)=\int_{\mathbb R^2}R_h(\mathbf r)e^{-i\mathbf q\cdot\mathbf r}\,d^2\mathbf r
}
$$

及逆变换

$$
R_h(\mathbf r)=\frac{1}{(2\pi)^2}
\int_{\mathbb R^2}C_h(\mathbf q)e^{i\mathbf q\cdot\mathbf r}\,d^2\mathbf q.
$$

因此

$$
\boxed{
S_q^2=\langle h^2\rangle=\frac{1}{(2\pi)^2}\int C_h(\mathbf q)\,d^2\mathbf q
}
$$

且 $C_h$ 的量纲为长度四次方。不同论文或 FFT 库可能把 $(2\pi)^2$ 放在不同位置；实现必须在元数据中记录约定，并以生成后回算为最终校验，不可只照搬振幅公式。[L11][E-PSD][GPT]

真实接触几何只相信有限二维波数区域

$$
\mathcal B_{\rm trust}
=\{\mathbf q:\ q_{\min}(\theta)\le |\mathbf q|\le q_{\max}(\theta),\ \mathrm{SNR}(\mathbf q)\ge\mathrm{SNR}_{\min}\}.
$$

主模型保留完整 $C_h(q_x,q_y)$；径向平均谱只能作为各向同性摘要，不能替代方向谱。[L11][L12][E-PSD]

#### 4.1.2 离散谱合成和归一化

在生成域 $L_x^{\rm gen}\times L_y^{\rm gen}$ 上取

$$
q_{x,k}=\frac{2\pi k}{L_x^{\rm gen}},
\qquad
q_{y,l}=\frac{2\pi l}{L_y^{\rm gen}},
$$

$$
\Delta q_x=\frac{2\pi}{L_x^{\rm gen}},
\qquad
\Delta q_y=\frac{2\pi}{L_y^{\rm gen}}.
$$

若采用随机相位、固定模值的离散傅里叶级数

$$
h(\mathbf x)=\sum_{\mathbf q\in\mathcal Q}
H_{\mathbf q}e^{i\mathbf q\cdot\mathbf x},
$$

则在本文连续约定下可取

$$
\boxed{
|H_{\mathbf q}|=
\sqrt{\frac{C_h(\mathbf q)\Delta q_x\Delta q_y}{(2\pi)^2}}
}
$$

并强制

$$
H_{-\mathbf q}=H_{\mathbf q}^{*},
\qquad H_{\mathbf 0}=0,
$$

使 $h$ 为实值零均值场。Nyquist 轴和其他自共轭模态必须使用实系数。若希望每个模态具有高斯振幅而非固定振幅，可在独立半平面用

$$
H_{\mathbf q}=
\sqrt{\frac{C_h(\mathbf q)\Delta q_x\Delta q_y}{2(2\pi)^2}}
(\xi_1+i\xi_2),
\qquad \xi_1,\xi_2\sim\mathcal N(0,1),
$$

再补共轭模态。具体数组缩放需按 FFT/IFFT 库是否含 $1/(N_xN_y)$ 修正。[L11][GPT]

每次生成必须回算窗口修正后的二维周期图。令

$$
\widetilde h(\mathbf q)=
\Delta x\Delta y
\sum_{m,n}w_{mn}\bigl(h_{mn}-\bar h_w\bigr)
e^{-i\mathbf q\cdot\mathbf x_{mn}},
$$

$$
U_w=\frac{1}{N_xN_y}\sum_{m,n}w_{mn}^2,
$$

则一种与上述量纲一致的估计为

$$
\boxed{
\widehat C_h(\mathbf q)=
\frac{|\widetilde h(\mathbf q)|^2}{A\,U_w},
\qquad A=L_xL_y.
}
$$

窗口只用于统计估计；几何查询域不得被窗函数压低。应报告二维谱误差、径向谱误差、方向扇区误差和谱矩误差，而不是只比较 $S_q$。[E-PSD][GPT]

#### 4.1.3 谱矩与参数非独立性

定义

$$
S_{\nabla}^2
=\left\langle h_x^2+h_y^2\right\rangle
=\frac{1}{(2\pi)^2}\int |\mathbf q|^2C_h(\mathbf q)\,d^2\mathbf q,
$$

$$
S_{\Delta}^2
=\left\langle (\nabla^2h)^2\right\rangle
=\frac{1}{(2\pi)^2}\int |\mathbf q|^4C_h(\mathbf q)\,d^2\mathbf q.
$$

其中 $S_q$ 为 RMS 高度，$S_{\nabla}$ 为无量纲 RMS 坡度，$S_{\Delta}$ 是量纲为 $\mathrm{mm}^{-1}$ 的谱拉普拉斯曲率代理，不等同于大坡度下的真实主曲率。短波截止对 $S_{\nabla}$ 和 $S_{\Delta}$ 极敏感，因此必须与可信波段一起报告。[L11][E-PSD]

相关长度必须写明定义，例如方向自相关 $R_h(r\mathbf e)/R_h(0)$ 首次降至 $e^{-1}$ 的距离、积分尺度或拟合模型参数。$S_q$、相关长度、roll-off、Hurst 指数 $H$、长短波截止和坡度/曲率并非任意独立：给定谱族后，它们由同一个 $C_h$ 的不同积分或形状参数共同决定。接口允许两种输入模式：

1. **谱参数模式**：直接给定 $C_0,H,q_r,q_{\min},q_{\max}$、各向异性等，输出派生矩；
2. **目标统计模式**：给定可测目标和权重，通过受约束拟合反求谱参数，并报告残差和不可同时满足的指标。

不得同时硬设一组互相矛盾的 RMS 高度、坡度、曲率和相关长度。

### 4.2 首版主线 PSD 模型及各向异性

首版通用合成后端采用**有限波数窗二维方向谱**。令旋转后的波数为

$$
\mathbf q'=\mathbf R(-\theta_0)\mathbf q,
$$

用无量纲正定矩阵 $\mathbf A$ 定义椭圆等效波数

$$
q_e(\mathbf q)=\sqrt{\mathbf q^\mathsf T\mathbf A\mathbf q}.
$$

一个可执行的分段谱族为

$$
\boxed{
C_h(\mathbf q)=C_0D(\theta_{\mathbf q})
\begin{cases}
0, & q_e<q_{\min},\\
1, & q_{\min}\le q_e<q_r,\\
\left(q_e/q_r\right)^{-2(1+H)}, & q_r\le q_e\le q_{\max},\\
0, & q_e>q_{\max},
\end{cases}
}
$$

其中：

- $C_0$ 控制谱幅值；
- $q_r$ 是 roll-off 转折；
- $H$ 是有限自仿射区斜率参数，不宣称表面在无限尺度上分形；
- $\mathbf A$ 控制椭圆各向异性；
- $D(\theta+\pi)=D(\theta)>0$ 是归一化方向调制，平均值设为 1；
- $q_{\min},q_{\max}$ 必须位于目标数据可信波段内。

若实测方向谱不能由椭圆模型描述，可直接使用平滑、非负、中心对称的二维经验谱表；若存在窄带纹理，可在背景谱上叠加成对方向峰。所有分支均要求 $C_h(-\mathbf q)=C_h(\mathbf q)$ 和非负性。[L11][L12][GPT]

### 4.3 非高斯与稀疏特征分支

PSD 只约束二阶统计，不能唯一决定峰度、尖峰、孔洞、凸粒或连通形态。A1 保留三类显式分支：

#### 4.3.1 二维 IAAFT/交替投影分支

输入为目标 Fourier 模值和目标高度经验分布。算法交替执行：

1. 把当前场 Fourier 模值替换为目标模值，保留相位；
2. 通过秩排序把高度替换为目标分位数；
3. 迭代至 PSD 误差和分布误差均收敛。

该分支适合在不改变目标边际分布的前提下近似保持 PSD，但不能保证孔洞拓扑、峰间依赖或任意三阶/四阶空间统计。必须输出迭代次数、PSD 残差、CDF 残差和不同初值的稳定性。[GPT]

#### 4.3.2 高斯 copula 变换分支

先生成高斯场 $g$，再取

$$
h=F_h^{-1}\!\left[\Phi\!\left(g/\sigma_g\right)\right].
$$

该式精确控制边际分布但会改变 PSD，故只能作为初始化或需迭代校正，不能在变换后仍声称保持原谱。[GPT]

#### 4.3.3 标记特征过程分支

用背景随机场与显式特征叠加：

$$
\boxed{
h(\mathbf x)=h_{\rm bg}(\mathbf x)+
\sum_{j=1}^{N_f}A_j\,
\psi_j\!\left(\mathbf R_j^{-1}(\mathbf x-\mathbf X_j);\boldsymbol\mu_j\right)}.
$$

$\mathbf X_j$ 可来自 Poisson、硬核或聚簇点过程；$A_j,\mathbf R_j,\boldsymbol\mu_j$ 描述高度、尺寸、方向和形状。该分支可表示稀疏孔洞、烧成裂纹、骨料/砂粒凸起或制造条纹，但只有在有三维测量支持其密度、尺寸和标记分布时才能启用。叠加后必须重新回算 PSD、边际分布、坡度、曲率和可达性；不能把“背景谱”和“特征统计”当作互不影响的参数。[L12][GPT]

### 4.4 红砖、混凝土和砂纸的模型族选择

A1 不把三类表面强制成同一唯一随机场，也不在证据不足时任意指定材料参数。首版采用“统一查询接口 + 不同可标定后端”的策略。

| 表面 | 首选数据路径 | 首版合成主线 | 保留分支 | 不允许的简化 |
|---|---|---|---|---|
| 红砖 | 多位置、多方向三维面测量；保存烧制/表面位置元数据 | 二维方向 PSD + 实测边际分布；必要时 IAAFT | 经测量标定的挤出条纹、孔洞/裂纹标记过程；分区或非平稳拼接 | 单条二维轮廓、单一 $R_a$，或把文献 2D/3D 比值当固定换算。[L12] |
| 混凝土 | 针对具体墙面、表面处理和测量尺度的三维测量 | 二维方向 PSD + 非高斯边际；允许局部参数场 | 骨料/孔洞显式特征、多个尺度成分、处理状态条件模型 | 把“混凝土”视为单一统计族，或跨处理/分辨率迁移唯一数值。[E-CONCRETE] |
| 砂纸 | 对实际批次和目数做三维面测量 | 二维方向 PSD + 非高斯边际 | 具有粒径、突出高度、面密度和粘结层参数的标记颗粒模型 | 把 P 目数直接等同唯一粒径、峰高、密度或 PSD。[E-FEPA][E-GRIT2][E-GRIT3] |

FEPA/ISO 的 P 目数规定磨粒粒度分布与检验框架，不提供涂附磨具成品表面的唯一三维高度统计；粘结层、撒砂工艺、磨粒形状、取向、突出高度和磨损状态仍需测量。因此 `grit_designation` 只作为模型条件标签和候选粒度先验，不直接生成地形。[E-FEPA][E-GRIT2][E-GRIT3]

### 4.5 150 mm × 150 mm 区域的生成、裁剪与拼接

#### 4.5.1 合成表面

FFT 合成天然周期。为避免正式区域内出现周期接缝或针体查询越界，应先生成带缓冲的域

$$
L_x^{\rm gen}\ge150+2b_x,
\qquad
L_y^{\rm gen}\ge150+2b_y,
$$

其中缓冲宽度至少覆盖球尖邻域、完整针体投影、安装座包络、局部拟合半径和事件步长安全裕度。具体 $b_x,b_y$ 由仍未固定的完整结构几何决定，不给唯一值。随后裁取中心 $150\times150$ mm 作为正式几何域，保留外圈 halo 仅供查询。

若需要比生成域更长的可信波长，不能靠重复平铺补回；必须增大生成域或把长波形状作为独立、可追溯的低频分量。正式查询域内不得跨周期边界环绕。

#### 4.5.2 实测表面

若测量区域大于 $150\times150$ mm，从有效区域内按预先定义的随机或分层抽样规则裁取窗口，记录原始坐标、方向、边界距离和排除原因。不同窗口不得只挑选“看起来粗糙”的区域。

若实测区域小于正式域，不允许把同一块数据无缝平铺并称为真实表面。可选择：

- 继续测量；
- 用实测统计标定合成扩展，并把结果标为 `hybrid/synthetic_extension`；
- 用多个真实测区拼接，但必须做重叠配准、误差传播和接缝统计检查。

任何混合/拼接都要重新验证二维 PSD、边际分布、方向性、局部统计和球尖可达性。

#### 4.5.3 样本数、参数扫描与统计代表性

随机样本数量未固定。首版接口支持顺序增加样本，并依据目标输出（如首次接触距离分位数、方向候选密度、可达表面谱矩）的置信区间或排名稳定性停止，而不是预设一个无依据的固定 $N$。同一参数组至少需要多个独立种子，且种子间统计一致性属于验证项。[EF:UNRESOLVED.STOCHASTIC.SAMPLE_COUNT]

参数扫描对象至少含 `study_id`、模型族、独立参数向量、约束/相关关系、参数来源、采样设计、重复种子、公共随机数配对标志和停止规则。只扫描真正独立的谱/分布参数；$S_q$、RMS 坡度、曲率代理等派生量不与其母谱参数同时无约束扫描。可采用规则网格、Latin hypercube 或其他空间填充设计，但具体方法和样本量由研究目标决定。比较两个针尖/结构方案时可对同一表面种子做配对，以降低地形随机性，但必须同时保留独立种子检验，避免把公共随机数误当统计独立样本。[GPT]

---

## 5. 实测表面预处理与质量门槛

### 5.1 四种尺度必须分开记录

1. **仪器物理分辨率**：由探头半径、光学数值孔径、点扩散函数/调制传递函数、轴向噪声和算法决定；
2. **采样间距**：数据点在 $x,y$ 的名义间隔；
3. **数值网格间距**：重采样或三角化后的计算间隔，可小于采样间距，但不能创造新信息；
4. **可信空间波长范围**：综合有限测区、去趋势、仪器传递、噪声和采样后的可相信波段。

针尖敏感尺度不是上述任意一个数字。有限球尖会删除一部分窄凹部，但与 $R_t$ 同量级的峰、坡度和支撑组合仍可改变首次接触与法向；因此必须通过球尖包络结果的网格/带宽收敛确定实际敏感范围。[L01][L12][L16][E-NIST]

### 5.2 不可破坏的处理流程

#### 步骤 1：冻结原始数据

原始点云/高度图只读保存，记录单位、坐标、采集顺序、仪器、标定、探头/光学参数、环境、重复扫描和文件哈希。任何处理生成新版本，不覆盖原始数据。

#### 步骤 2：单位和坐标统一

统一到 mm；校验轴方向、左右手性和高度正号。通过标志点、扫描姿态或已知基准把墙面外侧对齐到 $+Z$。拼接变换及其残差必须保存。[L16]

#### 步骤 3：有效掩膜、缺失区和离群点

缺失、饱和、遮挡、边缘、反射异常和配准失败必须写入掩膜。离群点不能只按高度阈值删除，因为真实砂粒或砖面尖峰也可能是极值；优先使用重复扫描、仪器质量标志、局部残差与物理可实现性联合判定。未经验证的空洞填补区不得参与首次接触判定；若为谱估计进行条件填补，应生成多个条件实现并传播不确定性。[GPT]

#### 步骤 4：去趋势与名义平面对齐

在确认测区宏观形状可由平面表示时，使用鲁棒或加权平面拟合

$$
z_{\rm form}(x,y)=a_0+a_xx+a_yy,
\qquad
h=z-z_{\rm form}.
$$

拟合面、残差、权重和被排除区域分别保存。局部分区统计共用同一经批准的名义平面，以免每个小窗口各自去倾斜而删除真实长波变化；这一点与红砖三维分区证据一致。[L12] 若墙面存在已知曲率、台阶或制造形状，应使用物理上有意义的形状模型，而不是任意高阶多项式。

#### 步骤 5：噪声与仪器传递评估

通过重复扫描、校准样件、空白区或厂家/实验标定估计噪声谱 $C_n(\mathbf q)$ 和传递函数 $M(\mathbf q)$。可信波数上限可写成

$$
q_{\max}^{\rm trust}(\theta)=
\min\left[
q_{\rm MTF}(\theta),
q_{\rm SNR}(\theta),
\gamma_N\frac{\pi}{\Delta s(\theta)}
\right],
$$

下限可写成

$$
q_{\min}^{\rm trust}(\theta)=
\max\left[
\frac{2\pi}{L_{\rm eff}(\theta)},
q_{\rm detrend}(\theta)
\right].
$$

$\gamma_N<1$、SNR 门槛和 MTF 门槛均为待验证数值参数，不能在理论阶段固定。空间带宽会系统影响 RMS 高度、相关长度和短波导数量，因此所有形貌指标必须带波段。[E-NIST][E-PSD]

#### 步骤 6：滤波和重采样

不采用“看起来更平滑”的任意滤波。允许的滤波必须有明确目的：去除已识别噪声、反混叠、分离名义形状或匹配两个仪器的共同带宽。滤波器、截止、相位、边界和传递函数全部记录。重采样前先在可信带宽内反混叠；更细计算网格只改善插值和碰撞离散，不提高物理分辨率。

#### 步骤 7：谱估计和局部异质性

谱估计使用去均值、窗函数能量修正和必要的分块平均；保留二维谱与方向扇区，不只保存径向平均。对红砖/混凝土按多个尺度和位置计算局部 PSD、边际、坡度与可达性，评估平稳性。单个全域均值不得掩盖局部高粗糙带或方向纹理。[L12]

#### 步骤 8：几何查询质量门槛

每个候选位置必须能回答：

- 球尖查询邻域是否完全处于有效域；
- 与 $R_t$ 和局部包络相关的波段是否可信；
- 插值/三角化误差是否低于当前几何容差；
- 法向和支持点是否在加密时收敛；
- 完整针体邻域是否有足够测量覆盖。

若任一项失败，返回 `GEOMETRY_UNCERTAIN`，而不是把缺失区当平面或把插值结果当真实微形貌。

### 5.3 采样间距、球尖半径和误差条件

令规则单元的平面半对角为

$$
r_{\rm cell}=\frac12\sqrt{\Delta x^2+\Delta y^2}.
$$

对球核在一个单元内的竖向变化，可用

$$
e_{\rm kernel}=R_t-\sqrt{R_t^2-r_{\rm cell}^2},
\qquad r_{\rm cell}<R_t,
$$

作为离散搜索敏感度的保守诊断之一；当 $r_{\rm cell}\ll R_t$ 时，$e_{\rm kernel}\approx r_{\rm cell}^2/(2R_t)$。它不是通用误差证明，必须与表面插值误差 $e_h$、测量误差 $e_m$ 和最大值搜索误差 $e_{\max}$ 一起满足

$$
 e_m+e_h+e_{\max}+e_{\rm kernel}\le\epsilon_{\rm geom}.
$$

$\epsilon_{\rm geom}$ 未固定，应通过输出量收敛和 A2 所需精度反推。对二阶光滑表面，线性三角化误差通常为 $O(\|\nabla^2h\|\Delta^2)$；在尖点或仅 Lipschitz 表面上不能使用二阶收敛假设。[GPT]

---

## 6. 有限球形针尖可达性

### 6.1 配置空间定义

设墙体实体为闭集 $\Omega$，半径 $R$ 的完整球为 $B_R$。球心的配置空间障碍为 Minkowski 和

$$
\boxed{
\mathcal O_R=\Omega\oplus B_R
=\{\mathbf y+\mathbf b:\mathbf y\in\Omega,\ \|\mathbf b\|\le R\}.
}
$$

球心可行域为 $\mathbb R^3\setminus\operatorname{int}\mathcal O_R$，接触边界为 $\partial\mathcal O_R$。这一定义表示有限球尖无法进入比自身几何允许范围更窄的凹部，是 A1 的尺度过滤核心。[L01][L16][GPT]

工程针尖只是局部球形球冠，不是独立完整球体。[EF:NEEDLE.TIP.GEOMETRY] 因此 A1 同时保存：

1. **完整球包络**：用于统一可达地形、尺度分析和快速候选；
2. **球冠合法性/精确复合针体查询**：用于判定接触点是否位于真实暴露球冠，并排除后方虚拟球体造成的假拒绝或假接触。

完整球结果不能跳过球冠和其余针体检查。

### 6.2 高度场上的最低球心包络

对球心 $\mathbf c=(x_c,y_c,z_c)$，令

$$
\rho^2=(u-x_c)^2+(v-y_c)^2.
$$

完整球不穿透 $\Omega_h$ 等价于

$$
z_c\ge h(u,v)+\sqrt{R^2-\rho^2}
\quad\forall (u,v):\rho\le R.
$$

因此最低可达球心高度为

$$
\boxed{
H_R(x_c,y_c)=
\sup_{\rho\le R}
\left[h(u,v)+\sqrt{R^2-\rho^2}\right].
}
$$

高度场包络直接给出**竖向残差**

$$
\boxed{g_R^{(z)}(\mathbf c)=z_c-H_R(x_c,y_c).}
$$

其符号解释为：$g_R^{(z)}>0$ 分离，$g_R^{(z)}=0$ 接触，$g_R^{(z)}<0$ 穿透。该运算是以球下半部为结构元的上形态包络（max-plus 膨胀）。[L01][GPT]

为使高度场和网格返回同一量纲、同一度量的间隙，统一查询还必须返回欧氏有符号球间隙

$$
\boxed{
 g_R^{(d)}(\mathbf c)=\phi_{\Omega_h}(\mathbf c)-R.
}
$$

对合法外侧构型，$g_R^{(z)}$ 与 $g_R^{(d)}$ 的符号和零点一致，但在斜面上数值大小一般不同。$g_R^{(z)}$ 适合直接构造最低球心高度和固定横向位置的竖向接近事件；跨后端比较、碰撞净距和保守推进采用 $g_R^{(d)}$。接口必须携带 `gap_metric`，不得把两者静默混用。

#### 6.2.1 支持点恢复

支持点平面坐标集合为

$$
\mathcal U_R(x_c,y_c)=
\operatorname*{arg\,max}_{\rho\le R}
\left[h(u,v)+\sqrt{R^2-\rho^2}\right].
$$

数值上返回容差支持集

$$
\mathcal U_R^{\epsilon}=
\left\{(u,v):
H_R-f_R(u,v)\le\epsilon_{\rm supp}
\right\},
$$

并按连通分量聚类，避免把一个宽平台的许多采样点误报成许多独立接触。对每个代表支持点

$$
\mathbf p_j=(u_j,v_j,h(u_j,v_j)),
$$

在接触时有

$$
\|\mathbf c-\mathbf p_j\|=R,
\qquad
\boxed{
\mathbf n_j=\frac{\mathbf c-\mathbf p_j}{R}
}.
$$

$\mathbf n_j$ 是球—表面接触对的径向法向，指向自由空间/球心。若原表面在 $\mathbf p_j$ 光滑且支持唯一，则 $\mathbf n_j=\mathbf n_h(\mathbf p_j)$；若存在多个支持、棱边、尖峰或平台，包络非光滑，必须返回全部支持法向和法向锥，不得平均成一个伪法向。

#### 6.2.2 局部球冠限制

设真实暴露球冠由球面轴向坐标

$$
\zeta=(\mathbf p-\mathbf c_t)\cdot\mathbf a
$$

满足

$$
\zeta\in[\zeta_b,R_t]
$$

定义，其中 $\zeta_b$ 是球冠—锥段连接位置，尚未固定。对高度场，在球面下半支接触处 $z_c=h+\sqrt{R_t^2-\rho^2}$，因此球冠条件可写成不含未知 $z_c$ 的形式

$$
\chi_{\rm cap}(u,v)=
(u-x_c)a_x+(v-y_c)a_y
-\sqrt{R_t^2-\rho^2}\,a_z
\ge\zeta_b.
$$

球冠限制包络为

$$
\boxed{
H_{\rm cap}(x_c,y_c;\mathbf a)=
\sup_{\substack{\rho\le R_t\\\chi_{\rm cap}\ge\zeta_b}}
\left[h(u,v)+\sqrt{R_t^2-\rho^2}\right].
}
$$

若可行集合为空，球冠在该横向位置没有可接触方向。球冠限制包络给出竖向残差

$$
g_t^{(z)}=z_c-H_{\rm cap}.
$$

统一欧氏球冠间隙记为 $g_t^{(d)}$，由暴露球冠/复合针体与墙体的精确有符号最近距离查询获得。实现可把完整球包络和 $g_t^{(z)}$ 作为广相候选，再用球冠条件及复合针体窄相精确检查；首次合法接触事件以 $g_t\equiv g_t^{(d)}$ 为主判据。只有在固定横向位置的纯竖向接近中，才可用与其零点一致的 $g_t^{(z)}$ 定位。不得只依据完整球的 $g_R^{(z)}$ 或 $g_R^{(d)}$ 宣告真实球冠接触。

### 6.3 多点支撑、退化法向与非光滑包络

在沟槽两侧、尖峰周围或网格边/顶点上，一个球可有多个等距支持。A1 采用以下规则：

- 支持点间距小于空间容差且属于同一平滑片时合并；
- 相互分离的支持分量全部保留；
- 每个支持返回径向法向、原表面相邻面法向集合、接触特征类型和不确定度；
- 包络法向集合可记为支持法向凸包/法向锥，但 A1 不求接触力组合；
- 方向候选同时输出“存在型”和“稳健型”结果，见第 8 节；
- 若三角形退化、法向条件数差或小扰动导致支持集合剧变，标记 `GEOMETRY_UNCERTAIN` 并触发局部加密。

### 6.4 完整三角网格上的球尖查询

#### 6.4.1 有符号距离定义

对闭合、定向墙体实体 $\Omega_m$，定义

$$
\phi_{\Omega_m}(\mathbf x)=
\begin{cases}
+\operatorname{dist}(\mathbf x,\partial\Omega_m), & \mathbf x\notin\Omega_m,\\
-\operatorname{dist}(\mathbf x,\partial\Omega_m), & \mathbf x\in\operatorname{int}\Omega_m.
\end{cases}
$$

统一欧氏完整球间隙为

$$
\boxed{g_R^{(d)}(\mathbf c)=\phi_{\Omega_m}(\mathbf c)-R.}
$$

当 $g_R^{(d)}=0$ 时，最近点集合

$$
\mathcal P_R(\mathbf c)=
\operatorname*{arg\,min}_{\mathbf p\in\Omega_m}
\|\mathbf c-\mathbf p\|
$$

给出接触点，径向法向仍为 $(\mathbf c-\mathbf p)/R$。最近特征可能位于三角形面、边或顶点；法向不能用插值顶点法向替代精确最近点方向。[GPT]

#### 6.4.2 球—三角形最近距离和空间加速

每次查询先用球心附近半径 $R+$ 安全裕度的 AABB 对 BVH 做局部遍历，再对候选三角形计算点—三角形精确最近点。对开放测量网格，主线处理是沿 $-Z$ 向下延伸并封闭侧面/底面，且封闭深度远离针体查询范围；若不能可靠封闭，则只返回无符号距离和 `orientation_undefined`，不能进行非穿透事件判定。

不得采用全点云三点组合穷举。文献 16 的空球三角形思想可用于理解有限半径可达性和构造局部候选，但工程实现采用网格邻接、BVH、最近距离和支持集；候选三角形数量也不解释为接触概率或承载能力。[L16]

#### 6.4.3 球冠查询

对完整网格，合法球冠接触要求最近/支持点满足

$$
(\mathbf p_j-\mathbf c_t)\cdot\mathbf a\ge\zeta_b-\epsilon_{\rm cap}.
$$

若全局最近点落在虚拟球后部，不可直接判定针尖接触。应在局部候选三角形上求球冠实体与墙面的最近距离，或调用统一复合针体窄相查询。若最先接触的是锥段/针杆，则状态为 `BODY_COLLISION_INVALID`。

### 6.5 高度场—网格一致性

对同一单值 $h(x,y)$：

1. 按相同节点和对角规则生成图面三角网格；
2. 向下封闭为实体；
3. 用高度场形态包络获得 $H_R$ 和竖向零点，同时用两分支的欧氏有符号距离查询同一球心路径；
4. 随 $\Delta x,\Delta y\to0$，要求 $H_R$、统一欧氏间隙、首次接触位置、支持点、法向、方向裕度和最小体碰撞间隙收敛到同一极限。

允许有限网格下存在离散差异，但差异必须随加密下降；若不下降，应检查对角划分、边界、符号、插值或支持点退化。

### 6.6 极限与量纲检查

- 平面 $h=h_0$：$H_R=h_0+R$，支持点为 $(x_c,y_c,h_0)$，法向 $\mathbf E_Z$；
- 斜面 $h=ax+by+c$，令 $s=\sqrt{1+a^2+b^2}$：

  $$
  \boxed{H_R=ax_c+by_c+c+Rs}
  $$

  支持点为

  $$
  u=x_c+\frac{Ra}{s},
  \qquad
  v=y_c+\frac{Rb}{s},
  $$

  且 $\mathbf n=(-a,-b,1)/s$；
- $R\to0^+$：在连续点恢复 $H_R\to h$；
- 所有 $H_R,g_R^{(z)},g_R^{(d)},g_t^{(z)},g_t^{(d)}$ 为长度；法向和方向裕度无量纲；
- 球尖变大时配置障碍 $\Omega\oplus B_R$ 单调扩大，但方向候选数不必严格单调，因为支持点和法向可切换；
- 窄于球尖可进入尺度的凹槽应从球心可达包络中消失。[L01]

---

## 7. 完整针体与安装结构的禁止碰撞

### 7.1 参数化复合几何

针体沿 $\mathbf a$ 从安装座出口指向针尖。令 $\zeta=(\mathbf x-\mathbf c_t)\cdot\mathbf a$，到轴线的径向距离为

$$
r_\perp=\left\|\mathbf x-\mathbf c_t-\zeta\mathbf a\right\|.
$$

#### 7.1.1 局部球形球冠（唯一允许的承载接触部位）

$$
K_{\rm cap}=
\left\{\mathbf x:
\|\mathbf x-\mathbf c_t\|\le R_t,
\ \zeta\ge\zeta_b
\right\}.
$$

球冠连接半径

$$
r_b=\sqrt{R_t^2-\zeta_b^2}.
$$

$\zeta_b$ 未固定，必须作为几何输入或由 CAD/显微测量获得。

#### 7.1.2 锥形过渡段（禁止承载）

从球冠连接处沿 $-\mathbf a$ 定义 $\ell\in[0,L_c]$：

$$
\mathbf x_{\rm axis}(\ell)=
\mathbf c_t+(\zeta_b-\ell)\mathbf a,
$$

$$
r_c(\ell)=r_b+\ell\tan\gamma_c.
$$

与针杆半径 $d/2$ 连续连接要求

$$
\boxed{
\tan\gamma_c=\frac{d/2-r_b}{L_c}
}
$$

或等价地由 $L_c,\gamma_c$ 中一个和实际 CAD 确定另一个。$L_c,\gamma_c$ 均未固定，不能自行指定唯一值。

#### 7.1.3 圆柱针杆（禁止承载）

圆柱半径 $d/2$，轴向区间为

$$
-L_e\le\zeta\le\zeta_b-L_c,
$$

要求几何可实现性

$$
L_{\rm sh}=L_e+\zeta_b-L_c\ge0.
$$

若实际针杆/锥段 CAD 与该简化不同，应导入精确部件网格，但仍使用同一碰撞查询合同。

#### 7.1.4 安装座（禁止承载）

安装座外形记为参数化实体 $K_{\rm mount}(\boldsymbol\theta_m)$ 或三角网格；其外形、相对安装座出口位置和局部安全间隙尚未固定。内部预埋段不做实体力学，但任何靠近墙面的外部安装结构必须参与非穿透检查。[EF:NEEDLE.EMBEDMENT.MODEL_BOUNDARY]

### 7.2 统一非穿透间隙

对任一刚体部件 $K_k(\mathbf q)$，定义其对墙体实体的几何间隙

$$
\widetilde g_k(\mathbf q)=
\min_{\mathbf x\in K_k(\mathbf q)}
\phi_\Omega(\mathbf x),
$$

净安全间隙为

$$
\boxed{
g_k(\mathbf q)=\widetilde g_k(\mathbf q)-\delta_{\rm clr,k}.}
$$

判定为：

- $g_k>\epsilon_g$：安全分离；
- $|g_k|\le\epsilon_g$：进入碰撞事件容差带；
- $g_k<-\epsilon_g$：违反安全间隙/发生穿透，并输出 `BODY_COLLISION_INVALID`。

高度场分支也将局部图面三角化并使用同一部件—三角形窄相算法，使锥段、圆柱和安装座碰撞不依赖“只比较某个轴线高度”的近似。允许使用解析球/圆锥/圆柱—三角形距离、经误差认证的凸分解，或足够细的部件网格；必须标明查询是精确还是保守近似。

### 7.3 合法球尖接触与禁止碰撞的分离

一个构型只有同时满足以下条件才是 A1 合法球尖接触：

$$
|g_t|\le\epsilon_g,
$$

$$
\zeta_j=(\mathbf p_j-\mathbf c_t)\cdot\mathbf a
\ge\zeta_b-\epsilon_{\rm cap},
$$

$$
 g_{\rm cone}>\epsilon_g,
\quad
 g_{\rm shaft}>\epsilon_g,
\quad
 g_{\rm mount}>\epsilon_g.
$$

若球尖与非承载部位在同一事件容差内同时接触，记录两类事件，但按纯球尖模型视为不可行，优先输出 `BODY_COLLISION_INVALID`。A1 不把锥段/针杆接触转化为分布承载。[EF:NEEDLE.CONTACT.COLLISION_BOUNDARY]

---

## 8. 首次接触与方向性几何候选

### 8.1 运动路径与四类几何情形

给定连续刚体路径 $\mathbf q(\xi)$，$\xi$ 可取弧长或规定的接近/拖拽位移。定义：

1. **单纯接近**：$g_t>\epsilon_g$ 且所有非承载部件 $g_k>\epsilon_g$；
2. **首次球尖接触**：最早的 $\xi_t^*$ 使合法球冠间隙进入零容差带；
3. **方向候选**：首次接触支持法向具有抵抗 $+x$ 的必要分量；
4. **不可行构型**：某非承载部件的碰撞事件不晚于合法球尖事件。

以下将统一欧氏合法球冠间隙 $g_t^{(d)}$ 简记为 $g_t$。先分别定义无约束的最早球冠与非承载体事件

$$
\xi_{t,0}=\inf\{\xi\ge\xi_0:g_t(\mathbf q(\xi))\le0\},
$$

$$
\xi_{b,0}=\inf\left\{\xi\ge\xi_0:
\min_{k\in\{\rm cone,shaft,mount\}}g_k(\mathbf q(\xi))\le0
\right\}.
$$

严格的首次合法球尖接触为

$$
\boxed{
\xi_t^*=\xi_{t,0}
\quad\text{且}\quad
\xi_{t,0}<\xi_{b,0}
}
$$

并要求从 $\xi_0$ 到 $\xi_t^*$ 的整个前缀路径均处于有效域和可信数据区。若两事件在并发容差内相同，则按非承载体碰撞优先，构型无效。这样可防止“体部先碰撞、后来又分离”后把更晚的球尖接触误称为首次合法接触。数值实现使用容差和事件括区，不要求恰好得到浮点零。

### 8.2 间隙、接触基与方向指标

主拖拽方向为

$$
\mathbf d=\mathbf e_x.
$$

对每个可信支持法向 $\mathbf n_j$，定义

$$
\boxed{
\eta_{x,j}=-\mathbf n_j\cdot\mathbf d
}
$$

和等价有符号几何角

$$
\boxed{
\phi_{g,j}=\arcsin\!\left[\operatorname{clip}(\eta_{x,j},-1,1)\right].
}
$$

- $\eta_{x,j}>0$：法向方向含有抵抗 $+x$ 的分量；
- $\eta_{x,j}=0$：法向对 $+x$ 无分量，例如理想水平面；
- $\eta_{x,j}<0$：法向分量顺着 $+x$，几何上不具备所需阻挡方向。

数值候选条件为

$$
\eta_{x,j}>\eta_{\rm tol},
$$

其中 $\eta_{\rm tol}$ 只覆盖法向误差和数值噪声，不是摩擦角或经验啮合阈值。若法向不确定度给出角误差 $\delta\theta_n$，应输出 $\eta$ 的上下界并在区间跨越零时标记不确定。

切向基定义为

$$
\mathbf t_1=
\frac{\mathbf d-(\mathbf d\cdot\mathbf n)\mathbf n}
{\|\mathbf d-(\mathbf d\cdot\mathbf n)\mathbf n\|},
\qquad
\mathbf t_2=\mathbf n\times\mathbf t_1.
$$

若投影范数低于容差，即 $\mathbf d$ 近似平行法向，则从固定参考轴中选择与 $\mathbf n$ 最不平行者构造确定性正交基，并记录退化处理。A1 不在该基上施加摩擦锥。

### 8.3 多点接触的方向标签

对支持集合 $\{\mathbf n_j\}_{j=1}^{m}$，定义

$$
\eta_{\max}=\max_j(-\mathbf n_j\cdot\mathbf d),
\qquad
\eta_{\min}=\min_j(-\mathbf n_j\cdot\mathbf d).
$$

输出两个不同标签：

$$
\texttt{candidate\_any}
\iff \eta_{\max}>\eta_{\rm tol},
$$

$$
\texttt{candidate\_robust}
\iff \eta_{\min}>\eta_{\rm tol}.
$$

`candidate_any` 表示至少一个支持方向可能抵抗拖拽；`candidate_robust` 表示当前所有分辨出的支持方向均满足。A2 必须接收完整法向集合/法向锥后再判断接触力分配和稳定性，不能只读取一个布尔值。

### 8.4 尖峰、法向退化和尺度依赖

- 对光滑高度场，原表面法向可由显式插值导数或局部拟合求得；
- 对三角形面内接触，接触法向采用径向最近点法向；
- 对网格边/顶点或多支持，保留相邻面法向集合，不做任意顶点法向平滑；
- 对局部曲率/坡度，使用显式拟合半径 $r_{\rm fit}$ 的二次曲面，并输出拟合半径、残差、条件数和可信带宽；
- 至少在多个 $r_{\rm fit}$ 上检查法向和曲率稳定性，不能选择一个隐藏平滑尺度；
- 包络导数/曲率只在唯一、光滑支持分支上报告；在支持切换处返回非光滑标志。

A2 所需接触运动学法向优先使用接触对径向法向；原表面法向、局部主曲率和纹理尺度作为材料/几何上下文同时保留。可达包络是球心配置空间边界，不替代原材料表面。

### 8.5 交给 A2 的候选记录

每个候选至少包含：

```text
candidate_id
surface_id / realization_id / parameter_set_id
pose_id / path_coordinate / physical_time
needle_geometry_id / Rt / alpha / beta / Le / diameter
center_ct
raw_contact_points[]
support_feature_types[]
contact_normals_radial[]
raw_surface_normals_or_face_sets[]
tangent_bases[]
full_sphere_vertical_residual / full_sphere_euclidean_gap / legal_cap_vertical_residual / legal_cap_euclidean_gap / gap_metric
support_multiplicity / nonsmooth_flag
eta_x_each[] / eta_min / eta_max
candidate_any / candidate_robust / geometric_margin
local_height / slope / curvature_proxy / fit_scale / fit_residual
trusted_wavelength_band / data_quality / uncertainty_bounds
cone_gap / shaft_gap / mount_gap / closest_pairs
body_collision_flag / cap_legality_flag
boundary_distance / out_of_domain_flag
event_bracket / event_location_tolerance
friction_parameters: null
local_strength_parameters: null
```

`physical_time=path_distance/(1\ \mathrm{mm/s})` 只做输出映射；几何平衡不依赖速度。[EF:LOAD.DRAG.QUASI_STATIC]

---

## 9. 事件函数、可变步长与数值算法

### 9.1 事件函数

对路径 $\mathbf q(\xi)$ 定义：

$$
E_t(\xi)=g_t(\mathbf q(\xi)),
$$

$$
E_k(\xi)=g_k(\mathbf q(\xi)),
\quad k\in\{\text{cone, shaft, mount}\},
$$

$$
E_{\rm cap,j}(\xi)=
(\mathbf p_j-\mathbf c_t)\cdot\mathbf a-\zeta_b,
$$

$$
E_{\rm dir,j}(\xi)=\eta_{x,j}-\eta_{\rm tol},
$$

并设置离开有效域和质量门槛事件 $E_{\rm domain},E_{\rm quality}$。球尖/体间隙通常连续但在最近特征或支持点切换处不可微；方向指标在支持切换处也可能跳到另一分支。因此根定位不得只依赖 Newton 导数。

### 9.2 防止跨越事件的保守推进

只检查步长两端的符号会漏掉“中间碰撞、末端又分离”的窄特征。对刚体部件到静态表面的欧氏距离，若路径参数为 $\xi$，可用部件最大点速度界

$$
V_k(\xi)\le
\left\|\frac{d\mathbf r}{d\xi}\right\|+
\left\|\boldsymbol\omega_\xi\right\|r_{\max,k}
$$

构造保守步长。设当前安全间隙为 $g_k>\epsilon_g$，取

$$
\boxed{
\Delta\xi_k\le
\gamma_{\rm safe}
\frac{g_k-\epsilon_g}{V_k+\epsilon_V},
\qquad 0<\gamma_{\rm safe}<1.
}
$$

对所有球尖与非承载部件取最小值，并受用户最大步长限制。若高度场使用竖向包络差而非欧氏距离，必须给出包络斜率的可靠 Lipschitz 上界；不能无条件把 $V=1$ 当安全界。[GPT]

### 9.3 事件括区与定位

当保守推进预测接近事件，或一次试探步发现任一事件函数进入容差带时：

1. 回退到最后一个全部安全的状态；
2. 保存 $[\xi_L,\xi_R]$，其中左端安全，右端为接触/碰撞或无法证明安全；
3. 对所有可能事件同时评估，使用二分、Brent 或其他保持括区的方法缩小区间；
4. 终止条件同时检查 $|\xi_R-\xi_L|\le\epsilon_x$ 和间隙容差；
5. 在定位点重新做最高精度局部几何查询和支持点恢复；
6. 若多个事件位置差小于事件并发容差，视为同时事件并全部记录。

不使用仅凭局部导数、可能跳出括区的纯 Newton 法作为唯一定位器。支持点切换时，以左右极限和全部支持集判定方向候选。

### 9.4 事件优先级

同一容差窗口内的处理顺序为：

1. `OUT_OF_DOMAIN` / `GEOMETRY_UNCERTAIN`：停止并报告数据不足；
2. 非承载部件禁止碰撞：构型标记无效；
3. 合法球冠首次接触：建立 `TIP_TOUCH`；
4. 方向候选标签：作为接触记录的附加字段，不改变接触事实。

若球尖和体碰撞同时发生，记录球尖接触但最终状态为 `BODY_COLLISION_INVALID`。该优先级防止把安装座撞墙误报为针尖挂接。

### 9.5 步长恢复与缓存

在所有归一化间隙连续若干步大于恢复阈值、局部曲率/支持特征稳定且没有质量风险时，可几何增长步长至最大值。具体增长率、连续安全步数、初始/最小步长和事件容差均为未决数值参数。[EF:NUMERICS.DRAG.VARIABLE_STEP]

空间加速和缓存策略：

- 高度场：以球心/部件投影 AABB 查询局部栅格块和图面 BVH；缓存相邻路径步重叠块；
- 网格：BVH/AABB 广相，三角形面/边/顶点窄相；
- 支持点：以前一步支持邻域作为优先候选，但必须有全局局部-AABB 回退，防止错过新特征；
- 多半径：可缓存原始局部邻域，但 $R_t=50,100\ \mu$m 的包络和支持集分别计算，不能线性缩放；
- 缓存键必须包含表面版本、几何版本、容差和查询尺度。

### 9.6 预处理伪代码

```text
INPUT: SurfaceConfig, raw measurement or synthesis parameters
1. Validate units, frame, material labels, parameter version and seed metadata.
2. If measured:
   a. Freeze raw data and build valid/quality masks.
   b. Register to nominal wall frame; estimate registration uncertainty.
   c. Fit approved nominal plane/form; retain both form and residual.
   d. Estimate instrument/noise transfer and trusted 2-D wave-number region.
   e. Resample only after anti-aliasing; retain physical and numerical resolutions separately.
3. If synthetic:
   a. Build finite-band 2-D PSD, including anisotropy.
   b. Generate a padded Hermitian spectrum and real height field.
   c. Apply optional non-Gaussian/feature branch with explicit version and seed.
   d. Crop central 150 mm × 150 mm query region; retain halo.
4. Compute QC: marginal, 2-D PSD, directional spectra, ACF, spectral moments,
   local heterogeneity and boundary/seam diagnostics.
5. Build height-field triangulation or validate/import full mesh.
6. Build BVH/AABB and signed-side representation.
7. Run analytic and representation-consistency tests.
8. Publish immutable SurfaceRealization only if quality gates pass;
   otherwise publish with GEOMETRY_UNCERTAIN status and reasons.
```

### 9.7 单路径步进伪代码

```text
INPUT: accepted SurfaceRealization, composite needle geometry, continuous pose path q(xi)
STATE: last_safe_xi, current_step, event brackets, local spatial cache

1. Validate that the complete swept AABB lies inside the surface domain/halo.
2. Query full-sphere envelope as a broad-phase scale/reachability result.
3. Query the legal spherical cap and recover all support points/normals.
4. Query cone, shaft and mount clearances through the shared collision interface.
5. If geometry quality or domain coverage is insufficient, return GEOMETRY_UNCERTAIN/OUT_OF_DOMAIN.
6. Compute a certified/conservative next-step bound from all positive gaps.
7. Trial advance by the minimum of safe bound and requested maximum step.
8. Re-evaluate all event functions; never accept a step merely because endpoint gaps are positive
   unless the conservative bound certifies the entire interval.
9. If an event is possible, roll back, form a bracket and locate the earliest event with a
   bracketing root method.
10. At the located pose, refine local surface/mesh as needed and recompute exact support sets.
11. Apply event priority: body collision invalidates pure-tip contact; otherwise record TIP_TOUCH.
12. For each contact normal compute tangent basis, eta_x and uncertainty bounds.
13. Set candidate_any/candidate_robust without invoking friction or force balance.
14. Emit the complete A2 candidate record, event diagnostics and query provenance.
15. For a continuing search path with no legal contact, update last_safe_xi and adapt step.
```

A1 在首次接触后不推进粘着/滑移接触点；连续迁移属于 A3。若调用者只需要扫描多次“重新搜索”区段，应由 A3 提供新的分离初态再调用 A1。

---

## 10. 模型选择、参数证据与标定状态

### 10.1 候选地形生成方法比较

| 方法 | 输入 | 输出 | 主要假设 | 优点 | 局限 | 需要标定的数据 | 验证 |
|---|---|---|---|---|---|---|---|
| 有限带二维 PSD + 高斯谱系数 | $C_h(q_x,q_y)$、波段、域、种子 | 平稳高斯高度场 | 二阶统计足够、周期生成域 | 归一化清楚，方向谱和多尺度可控 | 不保峰度/孔洞/颗粒拓扑 | 三维测量二维 PSD、可信波段 | 回算 PSD、ACF、谱矩、种子统计 |
| 随机相位固定模值 | 同上 | 近高斯随机场 | 足够多模态 | 每个实现谱模值接近目标 | 有限模态下分布并非严格高斯 | 同上 | PSD 精确度、边际分布 |
| 2D IAAFT | 目标谱模值、目标边际 | 非高斯场 | 交替约束存在可接受解 | 同时控制谱和边际 | 不保证高阶空间拓扑，可能不收敛到唯一解 | 实测高度 CDF + PSD | PSD/CDF 双残差、多初值 |
| 标记特征过程 + 背景场 | 特征密度、尺寸、形状、方向、背景谱 | 含孔/粒/纹理的场 | 特征族和点过程可代表结构 | 物理解释较强，可表达稀疏异常 | 参数多，叠加改变 PSD | 三维分割、粒/孔尺寸和密度 | 特征统计、PSD、可达性联合 |
| 实测高度场 | 原始面测量、仪器元数据 | 处理后高度场 | 测量带宽覆盖目标 | 最少模型形式假设 | 受仪器滤波、测区和缺失限制 | 重复扫描、标定和多位置样本 | 带宽、重复性、局部异质性 |
| 完整三角网格 | 点云/网格、实体侧 | 非单值三维几何 | 重建误差可量化 | 可表示倒扣并做完整碰撞 | 数据量大，符号/闭合性敏感 | 高质量点云、配准和重建误差 | 网格质量、点云偏差、HF 一致性 |

**首版主线选择**：实测数据可用且尺度合格时优先实测；合成基线使用有限带二维方向 PSD；非高斯边际用 IAAFT 作为首个可选分支；显式孔洞/颗粒特征和非平稳局部参数场保留为需要材料专属数据的分支。该选择不宣称三类材料共享同一参数族，只共享算法合同。

### 10.2 正式工程事实与未决参数

#### 已固定

- 正式高度场区域 $150\times150$ mm；
- 完整网格能力分支；
- 表面类别；
- 针尖半径 $50/100\ \mu$m；
- 针径 $0.6/0.8$ mm；
- 露出长度、针轴方向和只允许球尖承载；
- 物理拖拽速度、行程和可变步长接口。

#### 仍未固定，必须保留为参数/登记项

- 红砖、混凝土、各砂纸的 PSD、边际分布、相关长度、各向异性和非高斯参数；
- 砂纸目数集合、磨粒突出高度、面密度、形状和粘结层统计；
- 测量方法、可信最短/最长波长和数值网格间距；
- 随机样本数量和统计停止准则阈值；
- 球冠连接坐标 $\zeta_b$、锥长/锥角、针杆端部细节、安装座外形；
- 各部件安全间隙；
- PSD/分布验收容差、法向不确定度阈值、方向数值容差；
- 初始/最大/最小位移步长、事件位置和并发容差；
- 局部拟合半径集合及残差门槛；
- 材料专属模型族选择和参数先验。

### 10.3 证据来源与迁移边界

#### 本地文献

本轮四个压缩包中可访问的归档内容为完整证据卡及配套关键图，未包含可直接打开的论文 PDF；以下本地结论严格限定在这些可访问内容，不补写未提供原文中的细节。

- `[L01] 文献01`：支持三维方向几何、有限球尖偏置可达性和首次啮合距离概念。其摩擦稳定留给 A2；原文 MI 符号矛盾、半径/峰宽阈值和候选折减率不迁移为通用常数。
- `[L11] 文献11`：支持有限波数窗二维 PSD、随机相位合成、多尺度谱和网格收敛思想。其各向同性、弹性半空间与法向接触理论不作为 A1 针尖承载模型。
- `[L12] 文献12`：支持红砖位置/方向异质性、三维面测量、统一拟合平面和局部分区。文中的二维/三维比值及互相冲突的采样元数据不硬编码。
- `[L16] 文献16`：支持点云/三角形、有限空球和完整三维可达性。扫描误差可能接近或大于针尖尺度；三点穷举和候选计数不进入主实现。

#### 外部原始/官方来源

外部资料访问日期均为 `2026-07-15`。本轮没有把其数值升级为工程固定事实；记录如下：

| 标识 | 对象、版本与测量/规定方法 | 空间尺度、单位或适用范围 | 访问条件 | 对本项目的可迁移边界 | 直接网址 |
|---|---|---|---|---|---|
| `[E-ISO25178]` | ISO 25178-2:2021，Edition 2，面形表面纹理术语、定义和参数；属于 areal 方法标准，不是材料数据集 | 标准本身不规定本项目测区或材料数值；参数单位按各定义 | ISO 官方摘要/预览公开，完整标准需按 ISO 条件获取 | 只迁移术语、参数类别和“面测量”边界；不迁移红砖/混凝土/砂纸数值 | https://www.iso.org/standard/74591.html |
| `[E-FEPA]` | FEPA 官方磨料标准页面；说明涂附磨具使用 P-grit，宏粒平均直径为范围而非单值，宏粒用筛分、微粒用沉降类方法 | 粒度分级，不是成品表面空间高度；网页未给统一表面测区 | 官方网页公开，无固定出版版本 | 只迁移“P 目数是粒度分布标签”的边界；不能推出峰高、面密度、粘结层或 PSD | https://fepa-abrasives.org/abrasives/standards/ |
| `[E-GRIT2]` | ISO 6344-2:2021，Edition 2；涂附磨具用电熔氧化铝/碳化硅宏粒粒度分布的测定与检验 | P12–P220；粒度单位和完整试验细节以标准正文为准 | ISO 官方摘要/预览公开，完整标准受访问/购买条件限制 | 可作为候选目数与粒度分布的标准标签；不能直接变成砂纸表面峰高或颗粒突出量 | https://www.iso.org/standard/78220.html |
| `[E-GRIT3]` | ISO 6344-3:2021，Edition 3；涂附磨具用电熔氧化铝/碳化硅微粒粒度分布的测定与检验 | P240–P5000；粒度单位和完整试验细节以标准正文为准 | ISO 官方摘要/预览公开，完整标准受访问/购买条件限制 | 同上，只约束粒度分布/目数，不给成品三维地形 | https://www.iso.org/standard/78219.html |
| `[E-NIST]` | Grossman 等，2016；聚焦变化显微测量的空间带宽偏差分析，以经滤波的 Monte Carlo 各向同性、指数自协方差模拟面验证，并分析 11 种室外建筑材料 | 论文比较不同放大倍数/空间带通；具体仪器尺度不作为本项目输入，粗糙度为长度、相关长度为长度 | NIST 页面和论文下载公开 | 只迁移“有限视场和横向分辨率会偏置 RMS/相关长度”的警告；其各向同性、单一相关长度假设不作为材料模型 | https://www.nist.gov/publications/robust-evaluation-statistical-surface-topography-parameters-using-focus-variation |
| `[E-PSD]` | Jacobs、Junge、Pastewka，arXiv:1607.03040；一维/二维 PSD 定义、跨尺度测量重建、虚拟测量和小尺度伪影分析 | 波数为长度倒数；在本文采用的二维约定下 PSD 为长度四次方；不绑定单一材料/测区 | arXiv PDF 公开 | 迁移 PSD 规范化、谱矩、各向异性和带宽/伪影检查；不迁移接触力学或材料参数 | https://arxiv.org/pdf/1607.03040 |
| `[E-CONCRETE]` | Czarnecki，2025，开放论文；对抹平、磨削和抛丸三种混凝土表面做三维激光三角测量并比较五档重采样分辨率 | 分析间距 0.1、0.2、0.25、0.5、1.0 mm；原始扫描说明含 10 μm 轮廓间隔和 15 μm 精度 | 开放访问论文 | 只迁移“表面处理与测量尺度共同影响参数”的证据；其混凝土配比、处理工艺和具体百分比不作为本项目唯一先验 | https://www.mdpi.com/1996-1944/18/23/5320 |

#### GPT 自带知识

`[GPT]` 覆盖：Hermitian 谱合成、2D IAAFT、Minkowski 和/形态学包络、有符号距离、点—三角形最近距离、BVH/AABB、刚体 swept-distance 保守推进、括区根定位和误差收敛。适用边界是刚性几何和确定性数值算法；材料统计、仪器性能和工程容差仍需测量或审批，不能由通用知识给出唯一值。

---

## 11. 验证、收敛、完成判据与当前状态

### 11.1 解析与构造几何验证

| 验证项 | 预期结果/判据 | 当前状态 |
|---|---|---|
| 平面 | $H_R=h_0+R$，支持点同 $(x_c,y_c)$，$\mathbf n=\mathbf E_Z$，$\eta_x=0$ | **通过（解析推导）** |
| 斜面 | $H_R=ax_c+by_c+c+R\sqrt{1+a^2+b^2}$，支持点和法向与第 6.6 节一致 | **通过（解析推导）** |
| $R_t\to0$ | 完全球包络趋于原高度场；接触点趋于原表面 | **通过（极限定义）** |
| 各向同性关闭/开启 | $\mathbf A=\mathbf I,D=1$ 时方向谱退化为各向同性；旋转应随 $\theta_0$ 转动 | **通过（模型构造）** |
| 单一正弦面 | 与高精度连续最大化/细网格基准比较包络、支持点和首次接触 | **部分通过：测试规范已定义，待实现运行** |
| 已知沟槽/凹腔 | 宽度减小时出现球尖不可达；多侧支撑被完整返回 | **部分通过：测试规范已定义，待实现运行** |
| 球冠/球冠连接 | 接触点越过 $\zeta_b$ 时从合法球尖切换为禁止体接触/精确复合查询 | **部分通过：待结构几何数据与实现** |

### 11.2 随机场验证

每个参数组和种子至少检查：

- 均值、方差、偏度、峰度和目标 CDF；
- 完整二维 PSD、径向 PSD 和方向扇区 PSD；
- 自相关函数与定义明确的方向相关长度；
- $S_q,S_{\nabla},S_{\Delta}$；
- 非高斯分支的 PSD/CDF 双残差；
- 标记特征的数量、尺寸、方向、覆盖率和空间统计；
- 不同种子下估计量的分布与置信区间；
- 中央裁剪前后、拼接前后和边界附近的统计一致性。

当前状态：**部分通过——生成公式、归一化和验收量已定义，尚无本轮实际生成数据可执行统计检验。**

### 11.3 表示和数值收敛

对每次网格加密、插值阶次或事件容差扫描，至少要求以下量收敛：

$$
H_R,
\quad \xi_t^*,
\quad \mathbf p_j,
\quad \angle(\mathbf n_j^{(k)},\mathbf n_j^{(k+1)}),
\quad \eta_{\min/\max},
\quad \min_k g_k,
$$

以及事件顺序、支持点分量数和 `candidate_any/robust` 分类。分类在数值裕度接近零时允许标为不确定，而不强迫二元稳定。

| 验证项 | 判据 | 当前状态 |
|---|---|---|
| 高度场—网格一致性 | 同一图面随加密，包络、事件和法向差异下降到容差内 | **部分通过：合同已定义，待实现** |
| 网格间距收敛 | 关键输出相对/绝对差满足预定容差，不依赖单一固定网格 | **部分通过：容差未定，待实现** |
| 插值阶次 | 更高阶不应在可信带外制造振荡；关键输出稳定 | **部分通过：待数据与实现** |
| 事件不漏检 | 解析/人工窄障碍案例中，大外部步长仍由保守推进和括区定位捕获最早事件 | **部分通过：算法已定义，待实现** |
| 球尖与体碰撞区分 | 球尖合法、锥段先撞、针杆先撞、安装座先撞和同时事件均正确分类 | **部分通过：安装座/锥段几何未定** |

### 11.4 测量与材料数据状态

| 数据问题 | 状态 | 关闭条件 |
|---|---|---|
| 红砖材料专属 2D PSD、边际和方向异质性 | **仍缺数据** | 对目标砖多位置、多方向三维面测量并完成带宽质控 |
| 混凝土处理状态的统计族 | **仍缺数据** | 对目标墙面/处理状态测量，不跨论文样品硬迁移 |
| 砂纸实际目数集合和成品地形 | **仍缺数据** | 工程确定目数并测量具体批次的三维面形 |
| 测量可信最短波长是否覆盖 $50\ \mu$m 针尖敏感尺度 | **仍缺数据** | 仪器 MTF/SNR/重复扫描或多仪器共同带宽验证 |
| 球冠、锥段和安装座完整几何 | **仍缺数据** | CAD/显微测量确定 $\zeta_b,L_c,\gamma_c,K_{\rm mount}$ |
| 安全间隙与数值容差 | **仍缺数据/未决** | 由制造公差、实验和实现收敛联合确定 |

### 11.5 A1 完成判据逐项核对

| 判据 | 结论 |
|---|---|
| 给定参数能生成/导入可复现且可质控的表面 | **满足规范层要求**：数据模型、谱合成、非高斯分支、种子和 QC 已闭合；材料参数待标定。 |
| 三类表面差异不是任意硬编码 | **满足**：实测优先、共同后端与材料专属分支明确，未给唯一统计值。 |
| 给定针尖半径、姿态和运动增量可查询间隙并定位首次接触 | **满足规范层要求**：高度场/网格间隙、球冠合法性、事件函数和括区算法已定义。 |
| 能恢复接触点、法向、局部几何和方向字段 | **满足**：支持集、径向法向、原表面描述和多点方向裕度已定义。 |
| 能排除锥段、针杆和安装座碰撞 | **满足接口和方程要求**；完整几何参数仍待输入。 |
| 高度场和完整网格共享统一抽象并可一致性验证 | **满足**。 |
| 几何结果具有网格、插值和步长收敛要求 | **满足**；具体容差未固定。 |
| 输出足以让 A2 不重建地形机理 | **满足**，候选记录和查询合同完整。 |
| 所有未固定参数均显式保留 | **满足**。 |

结论：**A1 的机理与算法规范达到本轮完成标准；求解器实现、材料实测参数和数值验证运行不属于本轮已完成事实，均保留为后续任务。**

### 11.6 提示词覆盖矩阵

八类必答问题的落点：

| 必答问题 | 对应章节 | 覆盖状态 |
|---|---|---|
| 地形数据模型与统一参数接口 | 3.1–3.3、4.5 | 完整覆盖 |
| 合成地形生成机理 | 4.1–4.5、10.1 | 完整覆盖 |
| 实测表面预处理与质量门槛 | 第 5 节 | 完整覆盖 |
| 有限球形针尖可达表面 | 第 6 节 | 完整覆盖 |
| 完整针体与安装结构禁止碰撞 | 第 7 节 | 完整覆盖，结构数值保持未决 |
| 首次接触与方向性几何候选 | 第 8 节 | 完整覆盖，不越界到摩擦/力学 |
| 分辨率独立性、事件定位与数值算法 | 5.3、第 9 节、11.3 | 完整覆盖，容差保持未决 |
| 对 A2/A3 的参数与接口交接 | 8.5、第 12 节 | 完整覆盖 |

十二项理论和算法结果的落点：

| 结果 | 对应章节 |
|---|---|
| 1. 表面配置、数据和元数据模型 | 3.1–3.2 |
| 2. 三类表面的合成主线与可选分支 | 4.2–4.4、10.1 |
| 3. 实测表面预处理和质控流程 | 第 5 节 |
| 4. 高度场和三角网格统一查询合同 | 3.3、6.5 |
| 5. 有限球尖可达性与接触点恢复公式 | 6.1–6.4 |
| 6. 球冠、锥段、针杆和安装座碰撞边界 | 第 7 节 |
| 7. 首次接触事件函数 | 8.1、9.1–9.4 |
| 8. 方向性几何候选条件 | 8.2–8.3 |
| 9. 局部法向、坡度、曲率和方向量计算尺度 | 5.3、8.4 |
| 10. 分辨率、收敛、事件定位和失败回退 | 5.3、第 9 节、11.3 |
| 11. 面向实现的单步算法/伪代码 | 9.6–9.7 |
| 12. A1 向 A2/A3 交付字段和未决参数 | 8.5、10.2、第 12 节 |

---

## 12. 对 A2/A3 的交接合同

### 12.1 A2 可直接调用的内容

A2 接收并原样继承：

- 统一表面坐标、实体侧、单位和法向正方向；
- 原始表面与球心可达包络的区别；
- 合法球冠间隙 $g_t$ 和非承载部件间隙 $g_k$；
- 接触点支持集、径向接触法向、切向基和多点法向集合；
- $\eta_x$、`candidate_any/robust` 及其不确定度；
- 局部原表面统计、拟合尺度、曲率代理、可信波段和数据质量；
- 材料类别、表面实现 ID、随机种子和全部处理元数据；
- `friction_parameters` 和 `local_strength_parameters` 的空占位字段。

A2 在这些候选上建立单边接触、摩擦稳定、接触力与结构柔顺，不得重建 PSD、重新平滑表面、改变法向符号或用自己的尖端半径过滤。

### 12.2 A3 可直接调用的内容

A3 在滑移/脱离后可调用同一 A1 表面与复合针体查询来获得新姿态下的几何，但接触点迁移、材料失效、损伤记忆、脱离和再搜索状态机由 A3 定义。A1 不修改表面几何以表示破坏；若 A3 使用轻量损伤图，应作为独立材料状态层叠加，而不是静默重写 A1 原始表面。

### 12.3 下游禁止重新定义的低层机理

下游不得：

- 把单条轮廓或单一粗糙度值替换 A1 三维表面；
- 把原表面上不可达凹点直接作为球尖接触点；
- 把候选三角形数量、候选面积或 `candidate_any` 当作成功概率/承载力；
- 把完整球后部的虚拟接触当作真实球冠接触；
- 忽略锥段、针杆和安装座禁止碰撞；
- 在没有显式版本变化时改变 PSD 约定、坐标、单位、法向、插值或质量掩膜；
- 用改变物理拖拽速度代替事件附近的数值减步。

### 12.4 下一阶段仍需补齐

A2 需要补齐：单边接触互补、摩擦锥、接触力、恒法向主动推力平衡、刚性/梁针/轴向弹簧柔顺以及接触状态可行性。A3 需要补齐：滑移迁移、局部强度、失效、损伤、脱离和再挂接。两阶段都必须保留 A1 的数据质量和不确定度，不得把 `GEOMETRY_UNCERTAIN` 强行转成稳定接触。

---

## 附录 A：实现前最小参数对象

```text
TipGeometry:
  Rt
  cap_blend_coordinate_zeta_b            # unresolved
  axis_a
  center_ct

NeedleBodyGeometry:
  diameter_d
  exposed_length_Le
  cone_length_Lc                         # unresolved
  cone_half_angle_gamma_c                # unresolved or derived
  mount_geometry                         # unresolved parametric/CAD mesh
  clearances_by_part                     # unresolved
  geometry_version

GeometryTolerances:
  gap_tolerance                          # unresolved
  support_tolerance                      # unresolved
  cap_tolerance                          # unresolved
  normal_angle_tolerance                 # unresolved
  direction_margin_tolerance             # numerical only; unresolved
  event_position_tolerance               # unresolved
  simultaneous_event_tolerance           # unresolved

SurfaceQuality:
  physical_resolution
  sampling_spacing
  numerical_spacing
  trusted_2d_wave_number_region
  transfer_function_and_noise
  valid_mask
  uncertainty_fields
  qc_status_and_reasons
```

## 附录 B：A1 不确定性传播最低要求

A1 不要求建立完整概率接触力学，但必须把几何不确定性显式传递：

- 对高度误差/配准误差，给出间隙上下界或通过扰动实现求区间；
- 对法向误差，给出 $\eta_x$ 区间；
- 对缺失区，返回无结论而不是插值后的单值结论；
- 对模型族不确定性，保持多模型实现 ID，比较候选和首次接触的敏感性；
- 对随机表面，报告参数内变异（种子）和参数/模型间变异，二者不混为一项；
- A2/A3 必须能识别候选是 `certain`, `borderline` 还是 `uncertain`。

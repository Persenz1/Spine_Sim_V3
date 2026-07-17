# A_MODULE_CONTEXT

> 大模块：`A`——从随机表面到单刺连续啮合算子  
> 当前完成阶段：`A3`——滑移、局部材料失效、脱离与再挂接  
> 上下文版本：`0.3.0`  
> 工程事实版本：`engineering_fixed_context 1.0.0`  
> 执行提示词版本：`A3 1.0.0`  
> 当前状态：`candidate`

本文档是大模块 A 截至 A3 完成后的最新完整滚动上下文，不是 A3 增量。第 1–12 节及附录 A–B 完整保留已接受的 A1 几何、数据质量、事件、验证和交接合同；第 13–25 节完整保留已接受的 A2 单边接触、三维库仑摩擦、刚性/梁针/轴向弹簧统一柔顺、恒法向主动推力混合边界、非光滑单步求解及 A3/B 接口；第 26 节起新增 A3 的真实滑移提交、三维接触迁移、局部材料容量与尺度桥接、针体强度、不可逆损伤、释放、继续搜索、再挂接、并发事件和完整 A→B 单刺接口。固定工程事实以事实 ID 标注；本地证据沿用 A1/A2 的 `[L01]`、`[L07]`、`[L11]`、`[L12]`、`[L16]`，并新增 `[L03]`、`[L05]`、`[L14]`、`[L15]`；外部原始或官方来源记为 `[E-*]`；通用接触几何、材料/损伤、梁强度和非光滑数值方法记为 `[GPT]`。这些标记只说明证据层级，不把论文示例数值、外部材料参数或数值算法参数升级为工程固定值。

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

用主轴坐标系下的无量纲正定矩阵 $\mathbf A$ 定义椭圆等效波数

$$
q_e(\mathbf q)=\sqrt{{\mathbf q'}^\mathsf T\mathbf A\mathbf q'}.
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

---

# A2：单边接触、摩擦稳定与结构柔顺加载

## 13. A2 范围、算子目标与工程边界

### 13.1 A2 在物理链中的位置

A2 以 A1 已接受的合法球冠接触、支持点、径向法向、切向基、多支持法向集合、复合针体禁止碰撞间隙和数据质量为唯一几何入口，建立单刺准静态加载算子

$$
\boxed{
\mathcal S_{A2}:
(\mathcal C_{A1},\ \mathcal M_{\rm structure},\ P_z,\ \Delta u_x,\ \mathsf z_{A2}^{n})
\mapsto
(\mathsf z_{A2}^{n+1},\ \mathbf f_c,\ u_z,\ \boldsymbol\eta_b,\ \delta_s,\ R_x,\ \mathcal E)
}
$$

其中 $\mathcal C_{A1}$ 是 A1 候选及其查询句柄，$\mathcal M_{\rm structure}$ 是安装与针体柔顺配置，$P_z=0.5\ \mathrm N$ 是法向执行器主动推力，$\Delta u_x$ 是沿局部 $+x$ 的规定增量，$\mathsf z_{A2}^{n}$ 是上一步 A2 状态，$\mathcal E$ 是事件、可行性和诊断集合。[EF:LOAD.NORMAL.SINGLE_SPINE] [EF:LOAD.NORMAL.ACTUATOR_OUTPUT]

A2 只推进至以下任一边界：稳定粘着平衡、摩擦临界、接触释放、轴向弹簧原长端或硬限位、禁止体碰撞、预载不可行、平衡无解或数值未收敛。达到摩擦边界后的实际滑移路径、局部材料失效、损伤、脱离后的再搜索由 A3 处理；多个针共享背板和载荷重分配由 B 层处理；十字对爪整体平衡由 C 层处理。

### 13.2 A2 继承且不得改写的 A1 合同

A2 必须原样继承：

- 全局/单元坐标、$+Z$ 实体侧和局部 $+x$ 拖拽方向；
- 合法球冠欧氏间隙 $g_t$、完整球包络和原始表面的区别；
- 球冠支持点 $\mathbf p_j$、径向法向 $\mathbf n_j$、切向基 $\mathbf T_j=[\mathbf t_{1j}\ \mathbf t_{2j}]$；
- 多支持点集合、法向锥、非光滑标志、质量和不确定度；
- 锥段、针杆、安装座的禁止碰撞间隙与无效优先级；
- A1 的事件括区、首次合法球尖接触位置和 `candidate_any/robust` 仅为几何必要条件。

A2 不重建 PSD、不重新平滑表面、不改变法向符号、不把完整球后部当作球冠，也不把方向候选直接当作承载状态。

### 13.3 本阶段明确不处理

A2 不定义或执行：

- 摩擦边界后的接触点滑移迁移；
- 红砖/混凝土压碎、剪裂、划伤、断裂、损伤变量或地形更新；
- 针尖磨损、显式裂纹、碎屑、切削有限元和重网格化；
- 多针共同背板平衡、阵列载荷共享和失效重分配；
- 四单元同步收紧、偏心 wrench 和整爪摇摆；
- 导轨/框架柔性、真实安装座有限元、惯性和复杂控制器。

A2 可以输出针根内力、弯矩、能量和材料失效检查钩子，但不得代替 A3 给出强度域或失效结论。

### 13.4 A2 直接约束的工程事实

| 事实 ID | A2 中的强制含义 |
|---|---|
| `COORDINATE.GLOBAL.FRAME` | 墙面名义平面为全局 $X$-$Y$；$+Z$ 指向背板/自由空间。 |
| `COORDINATE.UNIT.FRAME` | 局部 $+x$ 是搜索和拖拽方向；局部 $y$ 与 $+Z$ 构成右手系。 |
| `COORDINATE.NEEDLE.AXIS` | 针轴 $\mathbf a$ 从安装座出口指向针尖球心，当前 $\beta=0$。 |
| `KINEMATICS.UNIT.RIGID_BOARD` | 背板只允许 $u_x,u_z$ 平移；$u_x$ 位移控制，$u_z$ 由力平衡求得。 |
| `NEEDLE.CONTACT.COLLISION_BOUNDARY` | 仅球尖承载；锥段、针杆、安装座碰撞立即使纯球尖模型无效。 |
| `NEEDLE.LENGTH.EXPOSED` | 固定角单针基准露出长度 $L_e=4\ \mathrm{mm}$。 |
| `NEEDLE.DIAMETER.SET` | $d\in\{0.6,0.8\}\ \mathrm{mm}$。 |
| `NEEDLE.MATERIAL.BASE` | 材料类别为高碳钢；具体 $E,\nu$ 和强度未固定。 |
| `NEEDLE.BENDING.SWITCH` | `off` 为刚体针，`on` 才启用梁柔顺；不得与弹簧柔顺重复。 |
| `ARRAY.MOUNT.RIGID_MODE` | 刚性安装锁定轴向移动副，允许传递任意符号的轴向约束反力。 |
| `ARRAY.MOUNT.AXIAL_SPRING_MODE` | $k_s\in[100,2000]\ \mathrm{N/m}$，无预压、只压缩、$0\le\delta_s\le4\ \mathrm{mm}$，上端硬限位。 |
| `LOAD.NORMAL.ACTUATOR_OUTPUT` | 恒定的是主动推力，不是局部法向反力或墙面实际合力。 |
| `LOAD.NORMAL.SINGLE_SPINE` | 单刺层 $P_z=0.5\ \mathrm N$。 |
| `LOAD.NORMAL.INFEASIBLE_TERMINATION` | 到体碰撞、硬限位、最近位置或无平衡仍无法建立目标推力时终止。 |
| `LOAD.DRAG.SPEED`, `LOAD.DRAG.QUASI_STATIC`, `LOAD.DRAG.TRAVEL` | $1\ \mathrm{mm/s}$ 只映射时间；忽略惯性；连续行程上限 $100\ \mathrm{mm}$。 |
| `NUMERICS.DRAG.VARIABLE_STEP` | 非光滑事件附近必须减步、括区和定位；步长与容差仍未固定。 |
| `UNRESOLVED.REGISTRY.GLOBAL` | $\mu$、接触刚度、钢材参数、容差和弹簧采样点不得硬编码。 |

本轮没有发现需要修改正式工程事实的证据；A2 的方程、状态和算法全部属于模块上下文。

## 14. 自由度、坐标、功共轭符号与单位

### 14.1 坐标和针局部基

沿用 A1 的单元基 $\{\mathbf e_x,\mathbf e_y,\mathbf E_Z\}$。针轴为

$$
\mathbf a=
\cos\alpha\cos\beta\,\mathbf e_x+
\cos\alpha\sin\beta\,\mathbf e_y-
\sin\alpha\,\mathbf E_Z,
\qquad \|\mathbf a\|=1,
$$

当前 $\beta=0$。为梁计算构造右手正交基 $\mathcal F_N=\{\mathbf a,\mathbf b,\mathbf c\}$。$\mathbf b$ 由固定参考轴在 $\mathbf a$ 的正交平面内投影并确定符号，$\mathbf c=\mathbf a\times\mathbf b$；若参考轴近似平行 $\mathbf a$，改用与 $\mathbf a$ 最不平行的全局轴。该规则必须确定性，避免同一姿态下梁矩阵跳变。

### 14.2 位移、力和正方向

- $u_x$：背板沿局部 $+x$ 的规定位移，单位 mm；$\dot u_x>0$ 为拖拽。
- $u_z$：背板沿全局 $+Z$ 的位置/位移，单位 mm；向墙接近对应 $\Delta u_z<0$。
- 法向执行器对“背板—安装—针”系统施加

  $$
  \boxed{\mathbf f_{\rm act}=-P_z\mathbf E_Z},
  \qquad P_z=0.5\ \mathrm N.
  $$

- 切向执行器对系统施加 $+R_x\mathbf e_x$；$R_x>0$ 表示维持 $+x$ 运动所需的驱动力。
- 第 $j$ 个墙面对针的接触力定义为

  $$
  \boxed{
  \mathbf f_j=\lambda_{n,j}\mathbf n_j+\mathbf T_j\boldsymbol\lambda_{t,j}
  },
  \qquad
  \lambda_{n,j}\ge0,
  \quad
  \boldsymbol\lambda_{t,j}\in\mathbb R^2.
  $$

  $\mathbf n_j$ 从墙体指向针尖/自由空间。针作用于墙的力为 $-\mathbf f_j$。

- 接触合力和以针尖球心 $\mathbf c_t$ 为参考的合矩为

  $$
  \mathbf F_c=\sum_j\mathbf f_j,
  \qquad
  \mathbf M_c=\sum_j(\mathbf p_j-\mathbf c_t)\times\mathbf f_j.
  $$

定义从单元局部、针局部和第 $j$ 个接触局部坐标到全局坐标的旋转矩阵

$$
\mathbf R_{GU}=
\begin{bmatrix}\mathbf e_x&\mathbf e_y&\mathbf E_Z\end{bmatrix},
\qquad
\mathbf R_{GN}=
\begin{bmatrix}\mathbf a&\mathbf b&\mathbf c\end{bmatrix},
$$

$$
\mathbf R_{GC,j}=
\begin{bmatrix}\mathbf n_j&\mathbf t_{1j}&\mathbf t_{2j}\end{bmatrix}.
$$

于是

$$
\boxed{
\mathbf f_j^G
=\mathbf R_{GC,j}
\begin{bmatrix}\lambda_{n,j}\\\boldsymbol\lambda_{t,j}\end{bmatrix},
\qquad
\mathbf f_j^U=\mathbf R_{GU}^{\mathsf T}\mathbf f_j^G,
\qquad
\mathbf f_j^N=\mathbf R_{GN}^{\mathsf T}\mathbf f_j^G.
}
$$

力矩使用同一旋转规则；对 $F\in\{U,N,C_j\}$，六维 wrench 使用

$$
\mathbf Q_{GF}=\operatorname{diag}(\mathbf R_{GF},\mathbf R_{GF}).
$$

所有抓附输出最终以 $R_x=-\mathbf e_x^{\mathsf T}\mathbf F_c$ 映射到抵抗局部 $+x$ 的标量，同时保留完整全局合力/合矩，不能只存一个载荷比。

### 14.3 最小未知量向量

给定 $u_x^{n+1}=u_x^n+\Delta u_x$ 后，A2 不把 $u_x$ 作为未知量。对一个包含 $m$ 个候选支持的常规加载步，最小未知量按活动分支组成：

$$
\boxed{
\mathbf y=
\left[
 u_z,
 \ \boldsymbol\eta_b\ (\text{仅 bending=on}),
 \ \delta_s\ (\text{仅弹簧 COMPRESSING}),
 \ r_H\ (\text{仅 HARD\_STOP}),
 \ \boldsymbol\lambda_1,\ldots,\boldsymbol\lambda_m
\right]
}
$$

其中 $\boldsymbol\eta_b=[\mathbf u_b;\boldsymbol\theta_b]\in\mathbb R^6$ 是针尖参考截面的梁平移和小转角，$\boldsymbol\lambda_j=[\lambda_{n,j};\boldsymbol\lambda_{t,j}]\in\mathbb R^3$。刚性安装没有 $\delta_s$；`needle_bending=off` 没有 $\boldsymbol\eta_b$。事件定位时可把事件位置 $u_x^*$ 或路径参数 $\xi^*$ 加为未知量。

切向驱动反力 $R_x$、锁定横向反力、背板约束力矩和刚性安装轴向反力均由求解结果后处理，不是自由度。

### 14.4 单位

内部统一使用：长度 mm、力 N、时间 s、角度 rad、力矩 N·mm、应力/弹性模量 N/mm$^2$（MPa）、平移刚度 N/mm、转动刚度 N·mm/rad、柔顺 mm/N 或 rad/(N·mm)。工程弹簧刚度输入为 N/m，进入方程前必须除以 $1000$ 转成 N/mm。任何角度输入若以度给出，进入三角函数前转换为 rad。

### 14.5 功、储能和耗散符号

外力对系统做正功定义为正。一个增量的执行器功近似为

$$
\boxed{
\Delta W_{\rm ext}
=R_x^{\rm mid}\Delta u_x-P_z\Delta u_z
}
$$

其中向墙接近时 $\Delta u_z<0$，故法向执行器做正功。梁和弹簧储能非负；库仑摩擦耗散定义为

$$
\boxed{
\Delta D_f=-\sum_j
\boldsymbol\lambda_{t,j}^{\rm mid}\cdot\Delta\mathbf s_j\ge0
}.
$$

刚性法向接触、锁定自由度反力和理想硬限位在其约束方向位移为零，因此不做功。接受步应满足

$$
\Delta W_{\rm ext}
=\Delta U_b+\Delta U_s+\Delta U_c+\Delta D_f+\mathcal E_{\rm work},
$$

$\mathcal E_{\rm work}$ 是可检查的离散/迭代残差，不得被当作物理耗散。

## 15. 变形后运动学、A1 几何更新与接触增量

### 15.1 背板、轴向移动副和未变形针尖位置

设背板参考点为

$$
\mathbf r_B=\mathbf r_B^0+u_x\mathbf e_x+u_z\mathbf E_Z.
$$

刚性安装时梁根位置为 $\mathbf r_0=\mathbf r_B+\mathbf r_{\rm off}$。弹簧安装的首版串联拓扑定义为

$$
\boxed{
\mathbf r_0=\mathbf r_B+\mathbf r_{\rm off}-\delta_s\mathbf a
}
$$

即 $\delta_s>0$ 表示针组件相对背板沿 $-\mathbf a$ 回缩。梁根不允许相对安装座转动。未弯曲针尖球心为

$$
\mathbf c_0=\mathbf r_0+L\mathbf a.
$$

$L$ 是当前结构配置提供的实际露出梁长：固定角单针主线取 $L=L_e=4\ \mathrm{mm}$；梯度阵列将来由 B1 传入各针实际 $L_j$。A2 主线把轴向移动副置于梁根上游，并在一个活动分支内保持 $L$ 不变，从而严格区分“整根梁平移”和“梁弯曲”。若 CAD 证明针通过固定出口回缩、使 $L=L(\delta_s)$，必须启用显式几何分支并在刚度、能量和碰撞中一致包含 $dL/d\delta_s$；不得静默用 $L_e-\delta_s$ 替换主线。

### 15.2 梁变形后的针尖位姿

当 `needle_bending=on`，针尖参考截面位姿采用小变形/小转角更新

$$
\mathbf c_t=\mathbf c_0+\mathbf u_b,
\qquad
\mathbf R_t=\mathbf R_0\exp([\boldsymbol\theta_b]_\times),
\qquad
\mathbf a_t=\mathbf R_t\mathbf a_0.
$$

首版牛顿迭代可用指数映射或一阶 $\mathbf R_t\approx\mathbf R_0(\mathbf I+[\boldsymbol\theta_b]_\times)$，但最终几何查询必须重新正交化。`needle_bending=off` 时 $\mathbf u_b=\boldsymbol\theta_b=\mathbf0$。

### 15.3 A1 查询在变形构型上的调用

每次残量评估均调用 A1 的同一几何后端：

1. 用 $\mathbf c_t,R_t,\mathbf a_t,\mathbf R_t$ 查询合法球冠欧氏间隙、支持点、径向法向、切向基和球冠合法性；
2. 用变形后的针体几何查询锥段、针杆和安装座净间隙；
3. 检查可信波段、质量、不确定度和有效域；
4. 以 `support_id` 跟踪同一支持分支；最近特征/支持集合切换被视为非光滑事件。

球面几何的法向间隙主要由球心决定，但球冠合法区和锥段方向随 $\mathbf R_t$ 变化。A2 不把上一步法向永久冻结；在一个平滑支持分支内更新法向，在支持切换处回退并定位事件。

### 15.4 梁中心线和禁止体碰撞

`needle_bending=on` 时不得把整个针体只按针尖刚体位姿旋转。对圆截面 Euler–Bernoulli 梁，在梁根基 $\{\mathbf a,\mathbf b,\mathbf c\}$ 中，设针尖合力分量为 $F_a,F_b,F_c$，合矩分量为 $M_a,M_b,M_c$。沿轴坐标 $s\in[0,L]$ 的首版中心线位移为

$$
 u_a(s)=\frac{F_a s}{EA},
$$

$$
 w_b(s)=\frac{F_b s^2(3L-s)}{6EI}+\frac{M_c s^2}{2EI},
$$

$$
 w_c(s)=\frac{F_c s^2(3L-s)}{6EI}-\frac{M_b s^2}{2EI},
$$

对应转角为

$$
 \theta_a(s)=\frac{M_a s}{GJ},
$$

$$
 \theta_c(s)=\frac{F_b s(2L-s)}{2EI}+\frac{M_c s}{EI},
$$

$$
 \theta_b(s)=-\frac{F_c s(2L-s)}{2EI}+\frac{M_b s}{EI}.
$$

由此重建变形中心线和截面姿态，将针杆/锥段离散为有误差控制的胶囊、圆台或临时三角网格，再调用 A1 的部件—表面距离内核。安装座保持背板刚体。若任一非承载部件净间隙进入零容差带，A2 立即产生 `BODY_COLLISION_INVALID`，即使球尖同时接触也不允许把该部位加入承载集。[EF:NEEDLE.CONTACT.COLLISION_BOUNDARY]

### 15.5 接触点速度雅可比和切向相对增量

在当前支持点 $\mathbf p_j$，令

$$
\mathbf r_j=\mathbf p_j-\mathbf c_t.
$$

针尖刚体在该点的速度为

$$
\mathbf v_j=\dot{\mathbf c}_t+\boldsymbol\omega_t\times\mathbf r_j.
$$

若 $\mathbf q$ 收集 $u_x,u_z,\delta_s,\boldsymbol\eta_b$，定义针尖扭量雅可比 $\mathbf J_t$，则

$$
\mathbf v_j=
\underbrace{\begin{bmatrix}\mathbf I&-[\mathbf r_j]_\times\end{bmatrix}}_{\mathbf J_{p,j}}
\mathbf J_t\dot{\mathbf q}.
$$

墙体固定，故第 $j$ 个接触的二维切向相对增量采用客观中点/梯形离散

$$
\boxed{
\Delta\mathbf s_j
\approx
\mathbf T_{j,\,n+1/2}^{\mathsf T}
\mathbf J_{p,j,\,n+1/2}
\mathbf J_{t,\,n+1/2}
(\mathbf q_{n+1}-\mathbf q_n)
}
$$

单位为 mm。步长加密时该离散必须收敛。$\Delta\mathbf s_j=\mathbf0$ 表示当前接触材料点无切向相对运动；球面可因针尖转动发生无滑滚动并由 A1 重新查询几何支持。A3 只在达到摩擦边界后推进有耗散滑移和跨特征迁移。

### 15.6 法向间隙

对每个平滑支持分支，$g_j^{\rm geom}(\mathbf q)$ 是 A1 合法球冠的欧氏有符号间隙，正为分离、零为接触、负为刚性几何穿透。全局球尖间隙是所有合法分支的最小值；数值实现不得只检查上一步支持。非承载体间隙 $g_k$ 始终是硬不等式

$$
 g_k(\mathbf q)>0,
 \qquad k\in\{\text{cone, shaft, mount}\},
$$

不为其引入承载乘子。

## 16. 单边接触、三维库仑摩擦与多支持处理

### 16.1 刚性单边接触主线

无局部接触柔顺时，Signorini 条件为

$$
\boxed{
 g_j^{\rm geom}\ge0,
 \qquad \lambda_{n,j}\ge0,
 \qquad g_j^{\rm geom}\lambda_{n,j}=0.
}
$$

严格区分：

- `OPEN`：$g_j>0,\lambda_{n,j}=0$；
- `TOUCH_ZERO_LOAD`：$g_j=0,\lambda_{n,j}=0$；
- `LOADED_CONTACT`：$g_j=0,\lambda_{n,j}>0$；
- `PENETRATION_INFEASIBLE`：$g_j<0$ 且未启用经标定的局部接触柔顺。

### 16.2 可选局部法向柔顺

局部接触刚度尚未固定，A2 主线为刚性互补。可选物理分支在接触界面单独引入法向压缩

$$
 c_{n,j}=c_{n,j}(\lambda_{n,j};\boldsymbol\theta_c),
 \qquad c_{n,j}(0)=0,
 \qquad \frac{dc_{n,j}}{d\lambda_n}\ge0,
$$

并使用有效间隙

$$
\boxed{g_j^{\rm eff}=g_j^{\rm geom}+c_{n,j}.}
$$

线性示例为 $c_{n,j}=\lambda_{n,j}/k_{n,j}$，但 $k_{n,j}$ 不得预设。该柔顺位于“球尖—墙体局部接触斑”，与针梁、轴向弹簧的位移和能量分别记录。其物理储能按接触压缩路径计算：

$$
U_{c,j}=\int_{0}^{c_{n,j}}\lambda_{n,j}(\zeta)\,d\zeta,
$$

若使用力为自变量，则同时可记录互补能

$$
U_{c,j}^{*}=\int_{0}^{\lambda_{n,j}}c_{n,j}(q)\,dq.
$$

线性分支两者均为 $\lambda_{n,j}c_{n,j}/2=\lambda_{n,j}^{2}/(2k_{n,j})$。令 $k_{n,j}\to\infty$ 或 $c_{n,j}\to0$ 时，事件位置、接触力和反力必须收敛到刚性互补解。未有独立证据时，切向接触微柔顺保持关闭，不能用它伪造静摩擦储能。

### 16.3 摩擦锥和最大耗散

第 $j$ 个接触的三维库仑锥为

$$
\boxed{
\mathcal K_{\mu_j}
=\left\{(\lambda_n,\boldsymbol\lambda_t):
\lambda_n\ge0,
\ \|\boldsymbol\lambda_t\|\le\mu_j\lambda_n
\right\}.
}
$$

$\mu_j\ge0$ 是待标定的局部静摩擦系数。对 $\mu_j>0$，定义标准三维二阶锥 $\mathcal L_3=\{(x_0,\mathbf x):x_0\ge\|\mathbf x\|\}$ 及

$$
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
$$

A2 的单边接触—库仑摩擦增量律写成

$$
\boxed{
\boldsymbol\chi_j\in\mathcal L_3,
\qquad
\boldsymbol\psi_j\in\mathcal L_3,
\qquad
\boldsymbol\chi_j^{\mathsf T}\boldsymbol\psi_j=0.
}
\tag{A2-CC}
$$

该式等价于

$$
\lambda_{n,j}g_j^{\rm eff}
+\mu_j\lambda_{n,j}\|\Delta\mathbf s_j\|
+\boldsymbol\lambda_{t,j}\cdot\Delta\mathbf s_j=0.
$$

由于各项均非负或受 Cauchy 不等式下界，得到：

- 若 $\Delta\mathbf s_j=\mathbf0$，则为粘着，$\boldsymbol\lambda_t$ 可在锥内；
- 若 $\Delta\mathbf s_j\ne\mathbf0$，则

  $$
  \boxed{
  \|\boldsymbol\lambda_{t,j}\|=\mu_j\lambda_{n,j},
  \qquad
  \boldsymbol\lambda_{t,j}
  =-\mu_j\lambda_{n,j}
  \frac{\Delta\mathbf s_j}{\|\Delta\mathbf s_j\|}
  }
  $$

  并满足最大耗散；
- 若 $g_j^{\rm eff}>0$，则 $\lambda_{n,j}=\boldsymbol\lambda_{t,j}=0$。

这是 Kanno 等三维准静态库仑接触二阶锥互补形式在本项目正法向符号下的重写。[E-KANNO] 它是非线性锥互补问题；不能把摩擦锥线性化成少量固定方向而不报告各向异性误差。

当 $\mu_j=0$ 时不使用除以 $\mu_j$ 的式子，而明确退化为

$$
\boldsymbol\lambda_{t,j}=\mathbf0,
\qquad
0\le\lambda_{n,j}\perp g_j^{\rm eff}\ge0.
$$

### 16.4 粘着、锥边界和临界滑移

定义力裕度

$$
 m_j=\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|.
$$

- `STICKING_INTERIOR`：$\lambda_n>0$、$\|\Delta\mathbf s\|$ 在容差内、$m_j>0$；
- `STICKING_AT_CONE_BOUNDARY`：$\Delta\mathbf s=0$、$m_j=0$，但下一个 $+u_x$ 单边试探仍可通过其他接触重分配保持粘着；
- `CRITICAL_SLIP`：$\Delta\mathbf s=0$、$m_j=0$，且无穷小 $+u_x$ 试探产生 $\Delta\mathbf s_j\ne0$，其方向与上式最大耗散关系一致；
- `SLIDING_TRIAL`：事件试探步中 $\Delta\mathbf s_j\ne0$。A2 用其方向定位临界点，但不提交该滑移位移；提交和接触点迁移由 A3 完成。

因此“摩擦锥边界”本身不自动等于即将滑移，必须结合规定加载方向的单边增量解。

### 16.5 二阶锥投影残量

对任意 $\rho_j>0$（单位 N/mm，仅为互补函数尺度，不是接触惩罚），式 (A2-CC) 等价于

$$
\boxed{
\mathbf r_{c,j}
=\boldsymbol\chi_j-
\Pi_{\mathcal L_3}
\left(\boldsymbol\chi_j-\rho_j\boldsymbol\psi_j\right)
=\mathbf0.
}
$$

标准二阶锥投影为

$$
\Pi_{\mathcal L_3}(z_0,\mathbf z)=
\begin{cases}
(z_0,\mathbf z),&\|\mathbf z\|\le z_0,\\
\mathbf0,&\|\mathbf z\|\le-z_0,\\
\dfrac{z_0+\|\mathbf z\|}{2}
\left(1,\dfrac{\mathbf z}{\|\mathbf z\|}\right),&\text{其他}.
\end{cases}
$$

投影残量半光滑，可用于广义 Newton/原始—对偶活动集。精确零点不依赖 $\rho_j$；实现必须通过尺度扫描验证结果不随 $\rho_j$ 改变，不能把它当作物理刚度。[E-KANNO][E-PDAS]

### 16.6 多支持点主线与非唯一性

A2 主线保留 A1 返回的每个空间分离支持点为独立接触约束和独立摩擦锥，因为不同作用点会产生不同力矩。法向凸包只用于几何诊断，不替代逐点力学。处理规则为：

1. 同一平滑片内、距离和法向均在聚类容差内的重复采样先合并；
2. 分离支持分量全部保留；
3. 零载支持允许 $g=0,\lambda=0$；
4. 若多个力分配产生同一合力/合矩和结构变形，报告 `contact_force_nonunique=true`、活动约束秩和可行内力零空间维数；
5. 数值分支选择采用严格的词典序规则：先最小化相对上一步接触力/结构状态的变化；若仍不唯一，新接触采用最小加权力范数。该二级问题只在完全满足原始平衡和锥约束的可行集合内求解，不改变物理方程；
6. 输出每点力和合力时同时标明哪些量对非唯一内力不敏感，禁止把任意代表解称为唯一物理分配。


## 17. 几何卡合、摩擦自锁、稳定平衡及文献 01 特例

### 17.1 三个概念的严格区分

1. **几何卡合/方向候选**：A1 的某个合法支持法向满足 $-\mathbf n\cdot\mathbf e_x>0$。它只说明法向方向可能阻挡 $+x$，不包含力大小、摩擦、结构兼容或执行器平衡。
2. **摩擦自锁**：在明确的外载符号、扰动方向和接触锥下，增加该扰动不要求切向滑移。它是局部载荷路径性质；改变法向载荷符号、接触象限或扰动方向后必须重算。
3. **稳定准静态平衡**：所有单边接触、摩擦锥、梁/弹簧兼容、$P_z$ 混合边界、力/力矩残量、体碰撞和数据质量同时可行，并通过第 21.6 节的局部增量可解性检查。

几何候选是必要筛选而非充分条件；摩擦自锁仍可能因体碰撞、弹簧无拉力、预载不平衡或结构失稳而不可行；一个可行平衡也可能位于锥边界而不是严格自锁。

### 17.2 本项目符号下的二维单支持特例

考虑 $\mathbf e_x$-$\mathbf E_Z$ 平面内单支持，定义 A1 有符号几何角 $\phi$：

$$
\mathbf n=-\sin\phi\,\mathbf e_x+\cos\phi\,\mathbf E_Z,
\qquad
\boldsymbol\tau=\cos\phi\,\mathbf e_x+\sin\phi\,\mathbf E_Z.
$$

$\phi>0$ 对应法向含抵抗 $+x$ 的分量。令外部切向驱动力为 $+F\mathbf e_x$，令 $W>0$ 表示外部法向力朝墙，即 $-W\mathbf E_Z$。平衡要求墙面对针的接触力为

$$
\mathbf f_c=-F\mathbf e_x+W\mathbf E_Z.
$$

投影到 $\{\mathbf n,\boldsymbol\tau\}$：

$$
\boxed{
\lambda_n=F\sin\phi+W\cos\phi,
\qquad
\lambda_t=-F\cos\phi+W\sin\phi.
}
$$

对即将沿 $+\boldsymbol\tau$ 滑动的分支，$\lambda_t=-\mu\lambda_n$，得到

$$
\boxed{
\frac{F}{W}
=\frac{\sin\phi+\mu\cos\phi}
{\cos\phi-\mu\sin\phi}
=\frac{\tan\phi+\mu}{1-\mu\tan\phi}
}
\tag{A2-2D}
$$

这正是文献 01 标量载荷比在本项目坐标、正法向和载荷符号下的恢复。[L01] 其适用条件仅为：单支持、二维、刚性局部几何、准静态库仑摩擦、给定滑移方向且无结构/材料上限。

### 17.3 分母奇异、法向反力和拉离分支

令

$$
D=\cos\phi-\mu\sin\phi,
\qquad
N=\sin\phi+\mu\cos\phi.
$$

在沿 $+\boldsymbol\tau$ 的滑移边界有 $W=\lambda_nD$、$F=\lambda_nN$。但完整摩擦锥还要求另一侧锥面

$$
\lambda_t\le\mu\lambda_n.
$$

对 $W>0$、$F\ge0$ 和 $0\le\phi<\pi/2$，该侧等价于

$$
\boxed{
\frac{F}{W}\ge
\max\!\left(0,
\frac{\tan\phi-\mu}{1+\mu\tan\phi}
\right)
}.
$$

所以以下“水平自锁”只表示沿规定 $+x$ 扰动没有有限的上侧滑移界；它不表示任意较小 $F$ 都满足完整摩擦锥。所有分支仍须同时检查上述下界和 $\lambda_n>0$。[GPT]

因此必须分支处理：

- $W>0,D>0$：沿 $+\boldsymbol\tau$ 存在有限上界 $F/W=N/D$，且 $\lambda_n=W/D>0$；完整粘着可行区还必须位于上述另一侧锥面给出的下界之上；
- $W>0,D=0$：有限 $\lambda_n$ 的 $+\boldsymbol\tau$ 滑移边界不能平衡正 $W$，上界发散；满足另一侧锥面下界后，进入理想水平自锁临界；
- $W>0,D<0$：对规定 $+x$ 扰动，$+\boldsymbol\tau$ 侧不再给出有限水平滑移上限；只有同时满足另一侧锥面下界、$\lambda_n>0$ 以及结构、体碰撞和材料接口时，才属于该方向的理想水平自锁区；
- $W<0$（外部拉离）：只有 $D<0$ 才可能有 $\lambda_n=W/D>0$ 的摩擦拉附分支；$D\ge0$ 时该方向需要非正法向反力，违反单边接触；
- 任意分支若 $\lambda_n\le0$，必须释放接触，不能继续使用载荷比式；
- 一般三维、多支持、柔顺和混合边界问题不得用式 (A2-2D) 替代锥互补求解。

水平自锁阈值 $D\le0$ 可写为 $\phi\ge\pi/2-\arctan\mu$，但该角度只对上述载荷象限和滑移方向成立，不是普适“挂住角”。

### 17.4 局部稳定/增量可解判据

A2 不把“存在一个静力解”自动称为稳定。接受为 `STABLE_QUASISTATIC` 需满足：

1. 第 21 节全部残量、锥条件、边界和碰撞检查通过；
2. 固定当前光滑几何分支和活动集后，广义 Jacobian 去除非唯一内力规范后满秩，给定 $\Delta u_x$ 的一侧增量解局部有界；
3. 对粘着分支，结构切线刚度在活动接触兼容约束的零空间上正定：若 $\mathbf N$ 张成允许的内部扰动，要求

   $$
   \mathbf N^{\mathsf T}\mathbf K_{\rm str}\mathbf N\succ0;
   $$

4. 对锥边界，枚举所有相容的一侧摩擦模式，至少一个模式可解，且 $\boldsymbol\lambda_t\cdot\Delta\mathbf s\le0$；
5. 对零控制增量不存在既满足约束又导致负结构二次功、正摩擦产能的方向；
6. 小幅正/负扰动和减步求解收敛到同一局部分支，或明确报告方向性分叉。

这是“强正则性 + 正结构切线 + 非负耗散”的操作性局部判据，不宣称全局 Lyapunov 稳定。摩擦系统可能存在方向不稳定和多解；若 Jacobian 奇异或分支对步长不收敛，标记 `EQUILIBRIUM_DEGENERATE`，不得强行选一个解。[E-KANNO][GPT]

## 18. 刚性针、梁针和弹簧加梁针的统一柔顺

### 18.1 结构拓扑和统一接口

A2 将柔顺分成物理位置不同的部件：

$$
\text{刚性背板}
\rightarrow
\text{可选轴向移动副/弹簧}
\rightarrow
\text{可选露出针梁}
\rightarrow
\text{可选局部接触压缩}
\rightarrow
\text{刚性墙面}.
$$

三种正式结构模式为：

| 模式 | 轴向移动副 | 针梁 | 局部接触柔顺 |
|---|---|---|---|
| `RIGID_MOUNT_RIGID_NEEDLE` | 锁定 | `needle_bending=off` | 主线关闭 |
| `RIGID_MOUNT_BEAM_NEEDLE` | 锁定 | `needle_bending=on` | 主线关闭/可选参数化 |
| `AXIAL_SPRING_NEEDLE` | 单边弹簧 + 硬限位 | 由开关选择 off/on | 主线关闭/可选参数化 |

轴向弹簧、梁弯曲和接触压缩分别输出位移、力和能量；任何一个参数不得同时代表两个部件。

### 18.2 圆截面梁截面量

对直针圆截面：

$$
A=\frac{\pi d^2}{4},
\qquad
I=\frac{\pi d^4}{64},
\qquad
J=\frac{\pi d^4}{32},
\qquad
G=\frac{E}{2(1+\nu)}.
$$

$E,\nu$ 是待定高碳钢材料参数；$d$ 和 $L$ 使用每根针的实际工程输入。文献 07 的可疑圆截面系数不迁移，以上量由截面几何重新推导。[L07]

### 18.3 三维 Euler–Bernoulli 针尖柔顺

令 $\mathbf P_\parallel=\mathbf a\mathbf a^{\mathsf T}$，$\mathbf P_\perp=\mathbf I-\mathbf P_\parallel$，$\mathbf S=[\mathbf a]_\times$。针尖参考截面承受 $\mathbf W_c=[\mathbf F_c;\mathbf M_c]$。小变形圆截面悬臂梁的坐标无关柔顺为

$$
\boxed{
\begin{aligned}
\mathbf u_b={}&
\frac{L}{EA}\mathbf P_\parallel\mathbf F_c
+\frac{L^3}{3EI}\mathbf P_\perp\mathbf F_c
-\frac{L^2}{2EI}\mathbf S\mathbf M_c,\\
\boldsymbol\theta_b={}&
\frac{L^2}{2EI}\mathbf S\mathbf F_c
+\frac{L}{EI}\mathbf P_\perp\mathbf M_c
+\frac{L}{GJ}\mathbf P_\parallel\mathbf M_c.
\end{aligned}
}
\tag{A2-BEAM}
$$

即

$$
\boldsymbol\eta_b=\mathbf C_b\mathbf W_c,
$$

$$
\boxed{
\mathbf C_b=
\begin{bmatrix}
\dfrac{L}{EA}\mathbf P_\parallel+\dfrac{L^3}{3EI}\mathbf P_\perp
&-\dfrac{L^2}{2EI}\mathbf S\\[1ex]
\dfrac{L^2}{2EI}\mathbf S
&\dfrac{L}{EI}\mathbf P_\perp+\dfrac{L}{GJ}\mathbf P_\parallel
\end{bmatrix}.
}
$$

因 $\mathbf S^{\mathsf T}=-\mathbf S$，$\mathbf C_b$ 对称；当 $E>0,G>0,A>0,I>0,J>0,L>0$ 时正定。梁储能和切线刚度为

$$
U_b=\frac12\mathbf W_c^{\mathsf T}\mathbf C_b\mathbf W_c
=\frac12\boldsymbol\eta_b^{\mathsf T}\mathbf K_b\boldsymbol\eta_b,
\qquad
\mathbf K_b=\mathbf C_b^{-1}.
$$

针尖接触力通过 $\mathbf r_j=\mathbf p_j-\mathbf c_t$ 产生 $\mathbf r_j\times\mathbf f_j$，因此式 (A2-BEAM) 自动包含接触力臂、两个弯曲平面和扭转，不能用与方向无关的单一标量刚度替代。

在针局部基中，每个弯曲平面的自由端凝聚刚度为

$$
\begin{bmatrix}F_t\\M_r\end{bmatrix}
=EI
\begin{bmatrix}
12/L^3&-6/L^2\\
-6/L^2&4/L
\end{bmatrix}
\begin{bmatrix}u_t\\\theta_r\end{bmatrix},
$$

轴向和扭转刚度分别为 $EA/L$、$GJ/L$，可作为矩阵单元测试。

### 18.4 坐标变换和接触点柔顺

若 $\mathbf R_{GN}$ 从针局部基转到全局，定义 $\mathbf Q=\operatorname{diag}(\mathbf R_{GN},\mathbf R_{GN})$，则

$$
\mathbf C_b^G=\mathbf Q\mathbf C_b^N\mathbf Q^{\mathsf T}.
$$

对位于 $\mathbf r$ 的接触点，点位移雅可比为

$$
\mathbf J_r=\begin{bmatrix}\mathbf I&-[\mathbf r]_\times\end{bmatrix},
$$

接触点由梁产生的平移柔顺为

$$
\boxed{
\mathbf C_{p}^{b}=\mathbf J_r\mathbf C_b^G\mathbf J_r^{\mathsf T}
}
$$

它对称半正定，并显式包含切向力在球尖半径处产生的弯矩。变换坐标而保持同一物理姿态时，$\mathbf f^{\mathsf T}\Delta\mathbf x$ 和 $U_b$ 不变。

### 18.5 弹簧切线柔顺和总柔顺

在 `COMPRESSING` 内部，轴向移动副的增量柔顺为

$$
\boxed{
\mathbf C_p^s=\frac1{k_s}\mathbf a\mathbf a^{\mathsf T}
}
$$

因为接触合力的压缩广义力为 $Q_s=-\mathbf a\cdot\mathbf F_c$，针组件位移为 $-\delta_s\mathbf a$。在 `HARD_STOP`，该方向切线柔顺为零；在原长端只存在一侧进入压缩的切线，不能用双向线性弹簧矩阵。

固定活动分支、单支持的小扰动点柔顺可写为

$$
\boxed{
\mathbf C_p^{\rm total}
=\mathbf C_p^b
+\chi_s\frac{\mathbf a\mathbf a^{\mathsf T}}{k_s}
+\mathbf C_p^c,
}
$$

$\chi_s=1$ 仅在 `COMPRESSING`，否则为 0；$\mathbf C_p^c$ 是可选已标定局部接触柔顺。刚性针/刚性安装时前两项均为零，而不是把 $E$ 或 $k_s$ 取一个任意巨大有限数。

### 18.6 梁理论适用范围和升级判据

首版主线采用线性 Euler–Bernoulli 梁，假设：直、均匀圆截面；根部固支；小应变、小转角；截面保持平面且忽略剪切变形；材料在线弹性范围。工程基准 $L/d=5$（$d=0.8$ mm）至约 $6.67$（$d=0.6$ mm），并不属于非常细长的梁，故必须把 Euler–Bernoulli 与 Timoshenko 对比列为强制验证，而不能默认剪切永远可忽略。

对自由端横向力，剪切/弯曲挠度比为

$$
\boxed{
\eta_{\rm shear}
=\frac{L/(\kappa GA)}{L^3/(3EI)}
=\frac{3EI}{\kappa GA L^2},
}
$$

$\kappa$ 为圆截面剪切修正系数。若该比值超过尚未批准的误差门槛，Timoshenko 分支在 $\mathbf C_{uu}$ 的横向块加入 $L/(\kappa GA)\mathbf P_\perp$。$\kappa$ 和门槛必须显式记录。

若 $\|\mathbf u_{b,\perp}\|/L$、$\|\boldsymbol\theta_b\|$ 或轴向压缩参数 $|N|L^2/(EI)$ 不再小，切换到共回转/几何精确梁；对固支—自由梁，接近 Euler 失稳量级 $\pi^2EI/(4L^2)$ 时线性切线不得继续使用。材料屈服/断裂仍交给 A3，但几何失稳属于 A2 的结构可解性风险。[E-BEAM][GPT]

### 18.7 开关和刚性极限

- `needle_bending=off`：强制 $\boldsymbol\eta_b=\mathbf0,U_b=0$，不组装 $\mathbf C_b$；
- `needle_bending=on`：使用实际 $d,L,E,\nu$；
- $E\to\infty$ 或 $\mathbf C_b\to0$：梁解收敛到刚性针，但正式刚性分支仍用开关；
- 刚性安装：轴向移动副被锁定并可产生锁定反力；不得用 $k_s\to\infty$ 代替，因为单边原长端和锁定轴向反力的物理集合不同。

## 19. 无拉力轴向弹簧、原长端和 4 mm 硬限位

### 19.1 压缩广义力和弹簧力

轴向移动副坐标 $\delta_s>0$ 的虚位移使针组件沿 $-\mathbf a$ 运动。接触合力对该坐标的压缩广义力为

$$
\boxed{Q_s=-\mathbf a\cdot\mathbf F_c.}
$$

$Q_s>0$ 倾向压缩弹簧。线性压缩力和储能为

$$
F_s=k_s\delta_s,
\qquad
U_s=\frac12k_s\delta_s^2,
\qquad
k_s\in[100,2000]\ \mathrm{N/m}.
$$

### 19.2 互斥活动状态

#### `RIGID_LOCKED`

刚性安装，$\delta_s=0$。轴向锁定反力

$$
r_{\rm lock}=Q_s
$$

可为任意符号，因为它来自刚性安装约束，不是弹簧力。

#### `AT_ORIGINAL_LENGTH`

$$
\delta_s=0,
\qquad F_s=0,
\qquad r_H=0.
$$

无拉力意味着一个承载平衡在该瞬间还必须满足 $Q_s=0$。单边试探规则：

- $Q_s^{\rm trial}>0$：进入 `COMPRESSING`；
- $Q_s^{\rm trial}<0$：维持当前接触需要弹簧拉力，当前接触必须释放或改变活动集；
- $Q_s^{\rm trial}=0$：可停留在原长端，但通常是事件点或退化分支。

因此原长端不是能提供任意“下限反力”的硬挡块；不得引入一个伪拉力乘子把接触强行留住。

#### `COMPRESSING`

$$
0<\delta_s<\delta_{\max},
\qquad
\delta_{\max}=4\ \mathrm{mm},
$$

$$
\boxed{Q_s-k_s\delta_s=0,\qquad r_H=0.}
$$

#### `HARD_STOP`

$$
\delta_s=\delta_{\max},
\qquad
\boxed{Q_s-k_s\delta_{\max}-r_H=0},
\qquad r_H\ge0.
$$

硬限位反力 $r_H$ 只抵抗进一步压缩；若求得 $r_H<0$，硬限位活动集错误，应退回 `COMPRESSING`。等价上端互补为

$$
0\le r_H\perp \delta_{\max}-\delta_s\ge0,
$$

但下端不设置可承拉的反力。

### 19.3 卸载和事件

从 `COMPRESSING` 卸载时 $Q_s$ 和 $\delta_s$ 同步减小；到 $\delta_s=0$ 定位 `SPRING_ORIGINAL_LENGTH` 事件。继续卸载若试探要求 $Q_s<0$，A2 释放相应接触，绝不令 $\delta_s<0$。到 $\delta_s=4$ mm 定位 `SPRING_HARD_STOP`；之后位置固定，附加压缩由 $r_H$ 承担，弹簧储能不再因 $\delta_s$ 增加。

若原长、硬限位、摩擦边界和接触切换在同一容差内发生，先定位共同事件位置，再同时枚举相容的后事件活动集；除体碰撞/数据无效这类致命事件外，不用人为顺序掩盖并发性。

### 19.4 软硬极限和预载可行性

- 很软的 $k_s$：建立给定 $Q_s$ 所需 $\delta_s=Q_s/k_s$ 较大，可能在建立 $P_z$ 前到硬限位；到限后可转为硬止挡分支，但若几何/体碰撞仍不能平衡则 `PRELOAD_INFEASIBLE`；
- 很硬的有限 $k_s$：压缩很小且数值条件数增大，趋近“压缩分支上的近刚性”，但不等同刚性安装；
- 原长端若接触载荷需要 $Q_s<0$，不存在无拉力弹簧平衡；
- 达到硬限位不自动等于失败，只有到限后仍无目标法向平衡或发生禁止体碰撞才判预载不可行。

## 20. 恒法向主动推力/切向位移混合边界与反力增长

### 20.1 整体外力平衡

把背板、安装结构、弹簧和针视为一个系统，内部梁/弹簧力相消。法向自由度的平衡为

$$
\boxed{
\mathbf E_Z\cdot\mathbf F_c-P_z=0.
}
\tag{A2-Z}
$$

因此 $0.5$ N 约束的是所有接触力的全局 $Z$ 合分量，不是任一 $\lambda_{n,j}$。切向 $u_x$ 受控，驱动反力为

$$
\boxed{
R_x=-\mathbf e_x\cdot\mathbf F_c.
}
\tag{A2-X}
$$

$R_x>0$ 即抵抗 $+x$ 拖拽的抓附反力。锁定的局部 $y$ 和背板转动自由度可产生零功约束反力：

$$
R_y=-\mathbf e_y\cdot\mathbf F_c,
$$

$$
\mathbf M_B^{\rm react}
=-\sum_j(\mathbf p_j-\mathbf r_B)\times\mathbf f_j
-\mathbf M_{\rm actuator},
$$

其中法向执行器若不通过背板参考点，其已知力矩为

$$
\mathbf M_{\rm actuator}
=(\mathbf r_{\rm act}-\mathbf r_B)\times(-P_z\mathbf E_Z);
$$

若作用线通过 $\mathbf r_B$，该项为零。构造这些零功约束反力后，完整刚体平衡残量为

$$
\boxed{
\mathbf r_F
=\mathbf F_c-P_z\mathbf E_Z
+R_x\mathbf e_x+R_y\mathbf e_y
=\mathbf0,
}
$$

$$
\boxed{
\mathbf r_M
=\sum_j(\mathbf p_j-\mathbf r_B)\times\mathbf f_j
+\mathbf M_{\rm actuator}+\mathbf M_B^{\rm react}
=\mathbf0.
}
$$

只有 $\mathbf E_Z$ 方向是自由且需在主求解中用式 (A2-Z) 闭合；$x/y$ 和转动分量由位移控制或锁定约束反力闭合，并分别输出残量。切向受控自由度绝不能误写成 $\mathbf e_x\cdot\mathbf F_c=0$。

### 20.2 分离、首次接触和预载建立

理想质量为零的系统在完全分离且受非零恒力时没有静态平衡。A2 因此对三个阶段使用同一边界合同但不同可接受状态：

1. `SEPARATED_SEARCH`：$\mathbf F_c=0$，式 (A2-Z) 未闭合；法向力控制器单调向墙移动，调用 A1 做几何搜索。该状态明确标记为“搜索中、非承载”，不伪称静力平衡；
2. `TIP_ZERO_LOAD`：A1 首次合法球尖接触位置作为 $P_z\to0^+$ 的初始几何；
3. `PRELOAD_EQUILIBRATION`：固定当前 $u_x$，以数值同伦 $P_z(\eta)=\eta(0.5\ \mathrm N)$、$\eta:0\to1$ 求最终恒推力平衡。该同伦仅用于求解，不改变最终工程边界；
4. `CONTACT_LOADING`：达到 $P_z=0.5$ N 后按 $u_x$ 增量推进，$u_z$ 每步由式 (A2-Z) 求得。

若在体碰撞、轴向硬限位、A1 最近允许位置或可行接触分支耗尽前无法达到 $\eta=1$，返回 `PRELOAD_INFEASIBLE`，不得无限推进 $u_z$。[EF:LOAD.NORMAL.INFEASIBLE_TERMINATION]

### 20.3 为什么恒 $P_z$ 下局部法向力仍变化

即使单支持时全局接触 $Z$ 分量固定为 $P_z$，局部法向反力为

$$
\lambda_n=\mathbf n\cdot\mathbf f_c.
$$

在二维特例中

$$
\lambda_n=F\sin\phi+P_z\cos\phi.
$$

因此随抓附反力 $F$、法向方向、支持切换和摩擦分量变化，$\lambda_n$ 可显著变化。多支持时只有 $\sum_j\mathbf E_Z\cdot\mathbf f_j=P_z$ 固定，各点 $\lambda_{n,j}$ 还会因结构兼容和内力非唯一而重分配。

### 20.4 单支持线性柔顺的解析力—位移基准

考虑一个固定平滑支持、二维粘着、小变形且总接触点柔顺 $\mathbf C_p^{\rm total}$ 常数。单支持整体平衡给出

$$
\mathbf f_c=-F\mathbf e_x+P_z\mathbf E_Z.
$$

在恒 $P_z$ 下，增量接触力为 $d\mathbf f_c=-dF\mathbf e_x$。粘着兼容为

$$
\mathbf0
=du_x\mathbf e_x+du_z\mathbf E_Z
+\mathbf C_p^{\rm total}(-dF\mathbf e_x).
$$

投影得到

$$
\boxed{
\frac{dF}{du_x}
=\frac{1}{C_{xx}},
\qquad
C_{xx}=\mathbf e_x^{\mathsf T}\mathbf C_p^{\rm total}\mathbf e_x,
}
\tag{A2-KT}
$$

$$
\boxed{
\frac{du_z}{du_x}
=\frac{\mathbf E_Z^{\mathsf T}\mathbf C_p^{\rm total}\mathbf e_x}{C_{xx}}.
}
$$

若 $C_{xx}$ 和几何近似常数，

$$
F(u_x)=F_0+\frac{u_x-u_{x,0}}{C_{xx}}.
$$

在 `COMPRESSING` 状态，弹簧对 $C_{xx}$ 的贡献为

$$
C_{xx}^{s}=\frac{(\mathbf e_x\cdot\mathbf a)^2}{k_s};
$$

到硬限位后该项消失，反力—位移斜率增大。梁项由 $\mathbf e_x^{\mathsf}\mathbf J_r\mathbf C_b\mathbf J_r^{\mathsf T}\mathbf e_x$ 给出，包含接触点力臂。三个正式结构模式在固定支持线性特例中的初始切线对比如下：

| 结构模式 | $C_{xx}$ | 初始 $dF/du_x$ |
|---|---:|---:|
| 刚性安装 + 刚性针 + 刚性接触 | $0$ | 理想无穷大；真实分支由几何事件而非隐藏弹簧决定 |
| 刚性安装 + 梁针 | $C_{xx}^{b}$ | $1/C_{xx}^{b}$ |
| 压缩区轴向弹簧 + 可选梁针 | $C_{xx}^{b}+(\mathbf e_x\cdot\mathbf a)^2/k_s$ | 上式倒数；通常比梁针分支更软 |
| 弹簧硬限位 + 可选梁针 | $C_{xx}^{b}$ | 从压缩区切换后增大；若梁也关闭则回到刚性事件分支 |

若启用局部接触柔顺，再向各行加入 $C_{xx}^{c}$。式 (A2-KT) 是一般求解器的解析/半解析验证，不使用文献 01 的实验系统斜率。

对完全刚性针、刚性安装和刚性接触，$C_{xx}=0$，固定支持上的理想粘着切线为无穷大；有限位移不能产生人为有限斜率。该模式的有限反力变化只能来自接触几何滚动/支持切换、未建模驱动柔顺或显式启用的局部接触柔顺。若数值结果在全刚性固定几何基准上给出任意平滑有限斜率，说明使用了隐藏惩罚。

### 20.5 到摩擦临界的半解析距离

在第 17.2 节二维条件且 $D>0$ 时，

$$
F_{\rm crit}
=P_z\frac{\tan\phi+\mu}{1-\mu\tan\phi}.
$$

若 $F_0<F_{\rm crit}$ 且 $C_{xx}$ 常数，则

$$
\boxed{
\Delta u_{x,\rm crit}
=C_{xx}(F_{\rm crit}-F_0).
}
$$

若期间弹簧到限、接触法向变化或梁几何非线性显著，必须分段积分而不能继续用常数斜率。

### 20.6 搜索位移与啮合后加载位移

A2/A3 必须分别记录：

$$
x_{\rm search}=u_x^{\rm touch}-u_x^{\rm last\ separation},
$$

$$
x_{\rm elastic}=u_x-u_x^{\rm touch}
$$

以及每次再挂接后的新起点。搜索位移只定位候选，不储存梁/弹簧能；啮合后的兼容位移才通过式 (A2-KT) 形成反力。文献 01 的试验显示峰值力与啮合后弹性位移相关、与搜索位移无显著相关，但其斜率含试验系统柔顺，不能作为本项目刚度。[L01]

### 20.7 增长分支的终止

反力增长持续到最早事件：

- 某接触达到 `CRITICAL_SLIP`，交给 A3；
- 接触法向反力降为零并释放；
- 弹簧卸载至原长或压缩至硬限位；
- 锥段/针杆/安装座禁止碰撞；
- 支持点/法向非光滑切换；
- 梁小变形失效或局部平衡 Jacobian 退化；
- 预载/平衡无解；
- 到达 A3 材料强度检查接口。


## 21. 非光滑单步平衡、残量系统与主求解算法

### 21.1 固定活动分支下的残量

给定 $u_x^{n+1}$、候选支持集和一个试探弹簧状态，定义接触合力/合矩 $\mathbf F_c,\mathbf M_c$。A2 主残量由以下块组成。

#### 法向混合边界

$$
\boxed{r_z=\mathbf E_Z\cdot\mathbf F_c-P_z=0.}
$$

#### 梁兼容

当 `needle_bending=on`：

$$
\boxed{
\mathbf r_b=\boldsymbol\eta_b-
\mathbf C_b
\begin{bmatrix}\mathbf F_c\\\mathbf M_c\end{bmatrix}
=\mathbf0.
}
$$

当开关为 `off` 时不组装该未知量和残量，并强制 $\boldsymbol\eta_b=\mathbf0$。

#### 轴向安装

- 刚性安装：不组装轴向方程；后处理 $r_{\rm lock}=Q_s$；
- `COMPRESSING`：

  $$
  \boxed{r_s=Q_s-k_s\delta_s=0},
  \qquad 0<\delta_s<\delta_{\max};
  $$

- `HARD_STOP`：

  $$
  \boxed{r_s=Q_s-k_s\delta_{\max}-r_H=0},
  \qquad r_H\ge0;
  $$

- `AT_ORIGINAL_LENGTH` 是事件分支：$\delta_s=0,Q_s=0$。在常规固定 $u_x$ 加载步中它通常不构成有限区间；事件定位时把 $u_x^*$ 或其他加载参数作为附加未知量以闭合方程。

#### 接触—摩擦锥

对每个候选支持：

$$
\boxed{
\mathbf r_{c,j}
=\boldsymbol\chi_j-
\Pi_{\mathcal L_3}(\boldsymbol\chi_j-\rho_j\boldsymbol\psi_j)
=\mathbf0
}
$$

或在 $\mu_j=0$ 时使用标量 Signorini 互补残量和 $\boldsymbol\lambda_t=0$。

因此常规 `COMPRESSING + bending=on` 步的方程数与未知量数均为 $8+3m$：$u_z$ 一项、梁六项、弹簧一项和每个支持三项。`HARD_STOP` 用 $r_H$ 替换 $\delta_s$；刚性安装和/或刚性针相应删除成对未知量/残量。

### 21.2 硬不等式和致命检查

以下条件不通过乘子承载，而作为步接受硬条件：

$$
 g_{\rm cone}>0,
 \quad g_{\rm shaft}>0,
 \quad g_{\rm mount}>0,
$$

$$
\texttt{data\_quality}\notin
\{\texttt{GEOMETRY\_UNCERTAIN},\texttt{OUT\_OF\_DOMAIN}\},
$$

$$
0\le\delta_s\le\delta_{\max}.
$$

体碰撞或数据无效优先于任何球尖承载解。局部法向柔顺启用时只允许球尖几何间隙出现与 $c_n$ 一致的受控负值，体部间隙仍不允许负值。

### 21.3 平衡、兼容和互补残量分开报告

不得只报告一个总残量。至少输出：

$$
\epsilon_{\rm force}=|r_z|,
$$

$$
\epsilon_{\rm beam}=\|\mathbf r_b\|,
\qquad
\epsilon_{\rm spring}=|r_s|,
$$

$$
\epsilon_{\rm cone}=\max_j\|\mathbf r_{c,j}\|,
$$

$$
\epsilon_{\rm gap}=\max_j[-g_j^{\rm eff}]_+,
$$

$$
\epsilon_{\rm friction}=\max_j[\|\boldsymbol\lambda_{t,j}\|-\mu_j\lambda_{n,j}]_+,
$$

以及体碰撞最小间隙、功平衡误差和活动集一致性。各量用显式力/长度尺度无量纲化后与尚未固定的容差比较；容差必须由收敛研究确定。

### 21.4 主算法：活动分支 + 半光滑 Newton

A2 首版选择“有限弹簧活动集 + 二阶锥投影半光滑 Newton”的小规模非线性互补求解。三维接触条件不做摩擦棱锥离散，不用任意法向惩罚替代互补。原始—对偶活动集和半光滑 Newton 对三维 Coulomb 接触可在不加罚的条件下同时识别接触/摩擦状态；本项目将该思想用于有限维单刺残量。[E-PDAS]

每个加载步的主流程：

```text
INPUT:
  accepted A1 surface/query handle and candidate neighborhood
  previous accepted A2 state z_n
  prescribed delta_u_x and target P_z
  mount mode, bending switch, material/stiffness parameter IDs

1. Set u_x_target = u_x_n + delta_u_x; retain the last accepted state for rollback.
2. Propagate A1 quality and domain checks. If uncertain/out of domain, stop without force solve.
3. Build candidate support set from:
     previous active supports,
     current A1 legal-cap supports,
     near-contact supports whose gap is within a conservative event band.
4. Predict u_z, beam deformation, spring state and contact forces from the previous tangent.
5. Select trial spring branch:
     rigid locked; compressing; or hard stop.
   Original-length is handled as an event boundary, not as a tensile stop.
6. Assemble residual blocks r_z, r_b, r_s and all SOC projection residuals.
7. Within each Newton evaluation:
     a. update tip pose and deformed beam centerline;
     b. re-query A1 legal-cap geometry and body clearances;
     c. keep the current smooth support feature fixed for the local derivative;
     d. update normals/tangent bases and objective tangential increments;
     e. assemble a consistent/generalized Jacobian.
8. Solve the generalized Newton system. Use damping/line search so that:
     body gaps remain positive,
     spring bounds are not crossed without event localization,
     the scaled merit function decreases.
9. If the support feature changes, a body gap approaches zero, or a spring bound is crossed,
   reject the trial iterate and return an event bracket rather than differentiating through the jump.
10. On convergence, infer each contact state from gap, load, slip increment and cone margin.
11. If a contact is on the cone boundary, perform a one-sided +u_x directional trial:
      - if stick can be maintained by redistribution, label STICKING_AT_CONE_BOUNDARY;
      - if nonzero slip obeying maximum dissipation appears, bracket CRITICAL_SLIP.
12. Check local incremental stability/strong regularity and the energy-work residual.
13. If multiple exact force distributions remain, apply the lexicographic continuation tie-breaker
    and report nonuniqueness diagnostics.
14. Accept only if all residual blocks, inequalities, quality checks and event ordering pass.
15. Otherwise roll back, reduce delta_u_x and retry. Never commit a sliding trial in A2.
OUTPUT:
  accepted state or a located event/infeasibility/nonconvergence diagnostic.
```

### 21.5 热启动、线性化和确定性分支

- **热启动**：优先使用上一步 $u_z,\boldsymbol\eta_b,\delta_s,r_H,\boldsymbol\lambda$；新接触力从零开始；
- **几何线性化**：平滑支持上使用 A1 返回的间隙梯度/法向及接触点 Jacobian；支持切换使用左右广义导数并减步；
- **梁一致切线**：线性梁时 $\mathbf C_b$ 常数，但 $\mathbf M_c$ 的力臂和接触几何随状态更新；几何非线性分支需含其一致切线；
- **SOC 广义导数**：使用投影的分段广义 Jacobian；锥顶和边界退化时允许多个候选导数，需用线搜索和活动集枚举；
- **确定性**：相同输入、容差、缩放和上一步状态必须得到相同分支；任何随机扰动只可用于离线诊断，不进入正式求解。

### 21.6 局部稳定性和一致切线检查

收敛后固定一个相容活动模式，形成分支 Jacobian $\mathbf J_{\mathcal A}=\partial\mathbf R/\partial\mathbf y$。A2 输出：

- 最小奇异值或条件数；
- 去除内力规范后的秩；
- $dR_x/du_x$、$du_z/du_x$、$d\delta_s/du_x$；
- 每个边界接触的一侧滑移方向；
- reduced stiffness 的最小特征值。

若 $\mathbf J_{\mathcal A}$ 不可逆但存在连续解族，只能标记 `DEGENERATE_NONUNIQUE`；若无相容一侧解，标记 `EQUILIBRIUM_INFEASIBLE`。条件数阈值不固定，必须通过步长/精度研究建立。

### 21.7 失败回退和保守替代

按以下顺序处理失败：

1. 更换 SOC 广义导数并阻尼 Newton；
2. 重新缩放残量和变量，但保持物理解不变；
3. 回退至最后接受状态并减小 $\Delta u_x$；
4. 对最早可能事件做括区定位；
5. 对单刺小规模问题枚举相邻离散分支：支持开/闭、粘着/锥边界、弹簧压缩/硬限位；
6. 在所有精确可行分支中按连续性和词典序规则选择；
7. 若所有分支均不可行，返回物理 `EQUILIBRIUM_INFEASIBLE`；
8. 若无法证明不可行但数值过程未收敛，返回 `NUMERICAL_NONCONVERGENCE`，不得伪装成物理失效。

所谓“保守替代”只允许返回：零承载、停止推进并报告未知，或缩小步长；不允许用任意高惩罚刚度制造一个看似收敛的穿透解。

## 22. 状态、事件、预载不可行和可变步长

### 22.1 层次化状态而非互相混用

A2 使用一个主机械状态和若干正交子标签。

#### 主机械状态

| 状态 | 定义 |
|---|---|
| `SEPARATED_SEARCH` | 无承载接触，继续 A1 几何搜索；恒力尚无静态平衡。 |
| `TIP_ZERO_LOAD` | 合法球尖间隙为零但所有接触力为零。 |
| `STICKING_LOAD` | 至少一个正压接触，所有接受的切向增量为零且锥可行。 |
| `CRITICAL_SLIP` | 至少一个接触在规定 $+x$ 方向的一侧试探中达到最大耗散滑移边界。 |
| `BODY_COLLISION_INVALID` | 锥段、针杆或安装座触碰/越过禁止边界。 |
| `PRELOAD_INFEASIBLE` | 在允许法向推进范围内不能建立 $0.5$ N 主动推力平衡。 |
| `EQUILIBRIUM_INFEASIBLE` | 给定加载增量不存在满足接触、摩擦、结构和边界的平衡。 |
| `EQUILIBRIUM_DEGENERATE` | 有解但局部 Jacobian/活动约束退化，稳定性或力分配不唯一。 |
| `NUMERICAL_NONCONVERGENCE` | 尚不能区分物理无解与算法失败。 |
| `GEOMETRY_UNCERTAIN` | A1 数据质量/法向/支持退化不足以做力学结论。 |
| `OUT_OF_DOMAIN` | 查询包络离开有效表面域。 |

#### 弹簧子状态

`RIGID_LOCKED`、`AT_ORIGINAL_LENGTH`、`COMPRESSING`、`HARD_STOP`。

#### 接触点子状态

`OPEN`、`TOUCH_ZERO_LOAD`、`STICKING_INTERIOR`、`STICKING_AT_CONE_BOUNDARY`、`CRITICAL_SLIP`、`SLIDING_TRIAL_NOT_COMMITTED`。

该层次允许例如“主状态 `STICKING_LOAD` + 弹簧 `HARD_STOP` + 一个零载支持”而不创建含糊组合名称。

### 22.2 事件函数

至少监控：

$$
E_{{\rm contact},j}=g_j^{\rm eff},
$$

$$
E_{{\rm release},j}=\lambda_{n,j},
$$

$$
E_{{\rm friction},j}=m_j
=\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|,
$$

$$
E_{s0}=\delta_s,
\qquad
E_{sH}=\delta_{\max}-\delta_s,
$$

$$
E_{{\rm body},k}=g_k,
$$

以及 A1 支持切换、球冠合法性、数据质量、域边界和梁升级指标。摩擦事件还必须通过一侧试探确认，不以 $m_j=0$ 单独触发实际滑移。

### 22.3 步长、括区和定位

外部物理速度始终 $1\ \mathrm{mm/s}$；仅调整数值 $\Delta u_x$。一个试探步若出现任一事件函数跨越、活动集改变、Jacobian 条件恶化或 Newton 迭代超限：

1. 回退至最后接受状态；
2. 保存 $[u_{x,L},u_{x,R}]$，左端为已接受状态，右端为事件/无法证明安全状态；
3. 用二分、Brent 或保持括区的分支求解定位最早事件；
4. 每个括区点都完整求解 $u_z$、结构和接触，而不是只对旧状态事件函数做插值；
5. 事件位置和残量同时达到未决容差后才提交；
6. 离开事件区后按连续安全步逐渐恢复步长。

### 22.4 同时事件处理

同一并发容差内：

1. `OUT_OF_DOMAIN` / `GEOMETRY_UNCERTAIN`：停止并报告数据不足；
2. `BODY_COLLISION_INVALID`：纯球尖承载模型立即失效；
3. 对其余接触建立/释放、摩擦边界、弹簧原长/硬限位和支持切换，在共同事件位置枚举所有相容后事件活动集；
4. 若同时达到 `CRITICAL_SLIP` 和 `HARD_STOP`，向 A3 传递“硬限位已活动”的临界状态；
5. 若接触释放与弹簧原长同时发生，先提交共同事件，再进入分离/搜索；
6. 不在 A2 执行材料失效；若 A3 强度钩子也在同一位置达到阈值，只记录候选并交由 A3 决策。

### 22.5 预载不可行的稳定返回

预载同伦每个阶段都使用第 21 节同一残量，只把目标 $P_z$ 改为 $\eta P_z$。以下任一条件使当前接触路径终止：

- 非承载体间隙到零；
- 达到几何允许的最近位置；
- 弹簧到硬限位后仍无 $r_H\ge0$ 的平衡；
- 原长端需要轴向拉力；
- 所有支持/摩擦活动集均不可行；
- A1 质量不足或越界。

若在终止前 $\eta<1$，返回

```text
PRELOAD_INFEASIBLE
achieved_normal_actuator_fraction = eta_max
limiting_event = body_collision | hard_stop | closest_pose | no_equilibrium | data_boundary
last_feasible_state
failed_active_sets[]
residual_and_event_bracket
```

不得继续向墙推进，也不得把 $P_z$ 直接赋给某个 $\lambda_n$ 来“完成”预载。

## 23. A2 输出数据合同及 A3/B 交接

### 23.1 每个增量的最低输出

```text
identity:
  surface_id / realization_id / parameter_set_id
  candidate_id / pose_id / path_coordinate
  needle_geometry_id / structure_parameter_set_id

A1_geometry:
  accepted_geometry_status / data_quality / uncertainty_bounds
  legal_cap_gap / support_ids / support_points
  contact_normals / tangent_bases / nonsmooth_flag
  cone_gap / shaft_gap / mount_gap / cap_legality

loading_and_time:
  u_x / delta_u_x / u_z
  search_displacement / elastic_loading_displacement
  physical_time = total_path_distance / (1 mm/s)
  normal_actuator_force_vector = -P_z E_Z

structure:
  mount_mode / spring_stiffness_id
  needle_bending switch / material_parameter_id / E / nu / L / d
  beam_tip_translation / beam_tip_rotation
  beam_root_force / beam_root_moment / deformed_centerline_summary
  spring_compression / spring_state / spring_force
  hard_stop_reaction / rigid_mount_lock_reaction

contact_forces:
  active_support_set
  gaps_by_support / effective_gaps / normal_compressions
  lambda_n_by_support / lambda_t_by_support
  contact_force_by_support in contact, needle, unit-local and global frames
  contact_resultant_force and moment about tip center, beam root and board reference
  force_nonuniqueness flag / rank / nullspace dimension / selection rule

reactions_and_balance:
  drag_drive_force +R_x e_x / measured opposite reaction
  grip_resistance R_x
  locked_y_reaction / board_constraint_moment
  force_residual / moment_diagnostic / beam_residual / spring_residual
  cone_complementarity_residual / gap_violation / friction_violation

state_and_events:
  primary_A2_state / spring_substate / per_contact_states
  friction_margin / potential_slip_direction
  local_stability_status / generalized_Jacobian_condition
  event_candidates / event_brackets / simultaneous_events
  step_accepted / rollback_count / convergence_diagnostics

energy:
  beam_energy / spring_energy / optional_contact_energy
  external_work_increment / friction_dissipation_increment / work_balance_error

A3_hook:
  beam_section_resultants / root_stress_inputs
  local_contact_force_and_geometry
  unresolved_material_strength_parameter_id
  material_failure_candidate_only = true
```

### 23.2 A3 可直接调用

A3 原样接收：

- A2 的接触力符号、逐点摩擦锥和最大耗散方向；
- 当前支持点、法向、切向基、梁/弹簧状态和硬限位；
- `CRITICAL_SLIP` 的一侧潜在滑移方向和事件位置；
- 力、力矩、能量、材料检查钩子和 A1 质量；
- 接触释放后调用 A1 继续搜索所需的完整姿态。

A3 可以推进非零滑移、接触点迁移、材料失效、脱离和再挂接，但不得重新定义 A2 摩擦锥、梁柔顺、弹簧原长/硬限位或 $P_z$ 混合边界。

### 23.3 B 层可直接调用

B 层将来对每根针传入共同背板 $u_x,u_z$ 和针级配置，调用同一 A2 单刺残量/响应，装配多针平衡。B 层不得把单刺峰值相乘，不得修改单刺接触力符号或柔顺；多针活动集、共同 $u_z$、载荷共享和重分配由 B2/B3 新增。

### 23.4 下游禁止重新定义

下游不得：

- 把 $0.5$ N 当作每个接触的 $\lambda_n$；
- 用一个摩擦角阈值替换三维逐点锥；
- 把弹簧和梁合成一个不注明位置的标量刚度；
- 在弹簧原长端允许拉力或在 4 mm 后继续压缩；
- 把锥段/针杆侧触转成承载接触；
- 在 A3/B/C 层偷偷加入惩罚穿透以改变 A2 解；
- 删除 A1 的几何不确定性和域外状态。

## 24. 参数、证据、适用边界与标定状态

### 24.1 本地文献 01

`[L01] 文献01` 直接支持：三维局部法向与加载方向的摩擦稳定域、二维载荷比特例、水平滑脱/竖向拉脱分支，以及“啮合后弹性位移而非搜索位移控制峰值力”的试验趋势。迁移边界：原文为刚性球形单刺、准静态库仑摩擦、无显著材料损伤；其 $\mu=0.8$、系统斜率、临界角、砂纸统计和半径尺度阈值均不硬编码；原文符号按第 17 节重推。

### 24.2 本地文献 07

`[L07] 文献07` 直接支持：线性移动副、轻推弹簧、单刺滑移/稳定尖端接触/通道内滑/结构限位、共同位移、回差和硬限位进入力学模型。迁移边界：论文的通道角、5 mm 行程、针径、刚度、预载和混凝土参数不是本项目值；针杆/锥段接触在本项目仅为禁止碰撞；文献梁系数有疑点，A2 已按圆截面和梁理论重推；阵列与对置模型不进入 A2。

本轮两个压缩包的可访问内容为证据卡及六幅关键图，没有可直接打开的论文 PDF。A2 只使用这些可访问内容和公开论文页面，不伪造未提供原文细节。

### 24.3 外部原始/官方来源

访问日期：`2026-07-16`。

| 标识 | 来源与用途 | 迁移边界 | 直接网址 |
|---|---|---|---|
| `[E-KANNO]` | Kanno，三维准静态 Coulomb 接触的非线性/二阶锥互补与投影算法；支持式 (A2-CC)、SOC 残量和“无通用求解器”的数值风险。 | 原文是小变形线弹性有限元接触；本项目是低维梁/弹簧和 A1 几何，需重建 Jacobian，不能照搬容差或迭代参数。 | https://arxiv.org/pdf/2101.11763 |
| `[E-PDAS]` | Hüeber、Stadler、Wohlmuth，三维 Coulomb 接触的原始—对偶活动集/半光滑 Newton；支持无罚识别接触和摩擦活动状态。 | 原文基于 mortar 有限元；本项目只迁移非光滑活动集方法，不迁移网格离散或求解参数。 | https://epubs.siam.org/doi/10.1137/060671061 |
| `[E-BEAM]` | MIT 官方 Euler–Bernoulli 梁讲义；支持悬臂梁小变形假设和自由端力/弯矩关系的公开核对。 | 讲义不是本项目材料数据；A2 的三维矩阵、圆截面量和接触力臂由本轮重推，$E,\nu$ 仍待标定。 | https://ocw.mit.edu/courses/2-002-mechanics-and-materials-ii-spring-2004/bc25a56b5a91ad29ca5c7419616686f7_lec2.pdf |

### 24.4 GPT 通用知识

`[GPT]` 实际使用：刚体扭量和功共轭变换、Signorini 互补、二阶锥对偶/投影、Coulomb 最大耗散、KKT/变分不等式、半光滑 Newton、强正则性、Euler–Bernoulli/Timoshenko 梁、共回转升级、能量和量纲检查。适用边界：这些是通用数学和连续体/数值方法；不能给出目标表面的 $\mu$、局部接触刚度、高碳钢牌号/强度或数值容差。

### 24.5 参数状态表

| 参数/选择 | 状态 | A2 处理 |
|---|---|---|
| $P_z=0.5$ N | 工程固定 | 作为全局 $Z$ 主动推力，不作为局部 $\lambda_n$。 |
| $k_s\in[100,2000]$ N/m、$\delta_{\max}=4$ mm | 工程范围/边界固定 | 具体采样点未定；逐次输入参数 ID。 |
| $d=0.6/0.8$ mm、基准 $L=4$ mm | 工程集合/固定 | 梁用实际针级 $d,L$。 |
| `needle_bending` | 工程开关固定 | off/on 两个正式分支。 |
| $E,\nu,G$ | 未决 | 参数接口；不得指定唯一高碳钢牌号。 |
| 屈服、断裂、疲劳强度 | 未决/A3 | 只输出内力和应力输入钩子。 |
| $\mu_j$ | 未决 | 表面/工况参数或分布；逐点锥使用。 |
| 局部接触柔顺 $c_n$ 或 $k_n$ | 未决 | 刚性主线；可选分支需标定并做刚性收敛。 |
| Timoshenko $\kappa$、升级阈值 | 未决 | 作为模型验证参数，不硬编码。 |
| 支持聚类、事件、残量、稳定性容差 | 未决 | 必须由网格/步长/精度收敛确定。 |
| SOC 尺度 $\rho_j$、变量缩放 | 数值参数 | 精确解应尺度不变；做灵敏度检查。 |
| 弹簧移动副是否改变露出梁长 | 几何实现未决 | 主线为上游平移、固定 $L$；若 CAD 证实固定出口回缩，启用显式 $L(\delta)$ 分支。 |

### 24.6 候选范围来源、标定方案和可辨识性

#### 针体材料与有效根部柔顺

在具体高碳钢牌号和热处理状态确定前，不给出一个虚假的通用数值范围。候选集合定义为

$$
\Theta_{\rm mat}^{\rm candidate}
=\bigcup_{g\in\mathcal G_{\rm approved}}
\operatorname{bounds}
\{E_g,\nu_g,\text{strength-data hooks}_g\},
$$

其中 $\mathcal G_{\rm approved}$ 只包含由采购牌号、炉批/材质证明、制造商正式数据表或相应牌号标准确认的材料状态；来源、温度、热处理和不确定度必须随 `material_parameter_id` 保存。普通“高碳钢”网页汇总不能成为正式范围。

A2 的弹性标定按以下层级进行：

1. 测量每根成品针的实际 $d,L$ 和根部边界；几何误差不得吸收到 $E$；
2. 对成品针做多个方向的已知端力/端矩静态试验，联合拟合 $EA$、两个 $EI$ 和必要的 $GJ$；
3. 用

   $$
   \mathbf C_{\rm measured}
   =\mathbf C_b(E,\nu,d,L)+\mathbf C_{\rm root}
   $$

   区分针体柔顺和夹持/出口根部柔顺；若 $\mathbf C_{\rm root}$ 显著，不得把它静默并入轴向弹簧或伪造一个材料 $E$；
4. 仅靠弯曲试验通常不能可靠识别 $\nu$；需要扭转/轴向联合试验或牌号专属数据约束；
5. 使用独立载荷方向和不同力臂做留出验证，报告参数协方差、重复件离散和残差；
6. 屈服/断裂标定进入 A3，A2 只限制标定载荷处于可逆线弹性范围。

#### 摩擦系数

$\mu_j$ 的候选范围来自相同针尖半径、相同目标表面批次、相同清洁/湿度状态和代表性法向载荷下的静摩擦起滑试验，而不是文献 01 的示例值。优先用可独立测得法向/切向力的平面或局部斜面试验；估计量为起滑前极限

$$
\widehat\mu_s=\frac{\|\boldsymbol\lambda_t\|}{\lambda_n},
\qquad \lambda_n>0.
$$

粗糙表面应保存位置/方向/重复件分布或分层参数，而不是只保存单一均值。若试验中出现压碎或划伤，该数据属于 A3 耦合失效，不能当作纯 Coulomb 摩擦标定。

#### 局部接触柔顺

使用与正式针尖半径和目标材料一致的低损伤法向微加载试验，测量总接近量 $\delta_{\rm meas}(F_n)$。先独立扣除仪器、夹具、梁针和轴向弹簧柔顺：

$$
\boxed{
 c_n(F_n)
 =\delta_{\rm meas}(F_n)
 -c_{\rm fixture}(F_n)
 -c_b(F_n)
 -c_s(F_n).
}
$$

只有残差为非负、单调并在重复试验中可辨识时才启用接触柔顺分支。用整套拖拽系统的峰前斜率直接拟合 $k_n$ 会把梁、弹簧、夹具和几何耦合重复计入，禁止采用。标定载荷必须低于可检测材料失效起点；否则交由 A3 的接触—损伤模型。

#### 数值参数

支持聚类、SOC 缩放、残量容差、事件容差和最小步长不从文献示例复制。它们分别通过：A1 几何加密、$\rho_j$ 尺度不变性、解析特例残量、事件括区加密、力—位移有限差分切线和状态序列收敛确定。候选值只有在关键事件位置、峰前反力和能量误差进入稳定平台后才能固定。

以上标定流程属于参数识别方案，不构成工程事实变更；实际牌号、数据范围和验收阈值仍待实验/采购输入。[GPT]

## 25. 验证、完成判据、风险与下一阶段交接

### 25.1 解析与物理极限检查

| 检查 | 本轮结论 | 状态 |
|---|---|---|
| 分离时接触力为零 | SOC/Signorini 条件令 $g>0\Rightarrow\lambda=0$。 | **通过（解析）** |
| $\mu=0$ | 显式退化为无摩擦单边接触，$\boldsymbol\lambda_t=0$；切向承载只能来自法向几何投影和整体平衡。 | **通过（解析）** |
| 单支持二维刚性特例 | 第 17.2 节恢复文献 01 的载荷比，并给出分母、法向力和拉离分支。 | **通过（重推）** |
| 梁柔顺趋零 | $\mathbf C_b\to0$、$\boldsymbol\eta_b\to0$，与 bending=off 接口一致。 | **通过（解析）** |
| 刚性安装 | 由锁定移动副和独立 $r_{\rm lock}$ 得到，不用巨大有限弹簧。 | **通过（模型构造）** |
| 弹簧原长/硬限位 | 原长无拉力、硬限位无继续压缩；力、位移和能量量纲闭合。 | **通过（解析）** |
| 梁矩阵对称/正定 | 式 (A2-BEAM) 对称，正材料参数下正定；点柔顺半正定。 | **通过（解析）** |
| 坐标旋转与功不变 | 采用扭量/旋转合同，$\mathbf f^T\Delta\mathbf x$ 和储能不变。 | **通过（解析）** |
| 功和耗散符号 | 粘着耗散为零；滑移试探满足 $-\lambda_t\cdot\Delta s\ge0$；硬限位零功。 | **通过（解析），待实现数值核验** |
| 平面/斜面作用—反作用 | 平面 $\mathbf n=\mathbf E_Z$ 时 $\mu=0$ 无切向承载；斜面按第 17 节分解。 | **通过（解析）** |
| 单支持线性力—位移 | 第 20.4 节给出 $dF/du_x=1/C_{xx}$ 和硬限位斜率跳变。 | **通过（解析）** |

### 25.2 数值与事件验证计划的当前状态

| 检查 | 接受判据 | 当前状态 |
|---|---|---|
| 分块残量 | 力、梁、弹簧、锥、间隙、摩擦和功分别收敛 | **部分通过：残量已定义，待代码运行** |
| 刚性互补—接触柔顺收敛 | $c_n\to0$ 时力、事件和位移收敛到刚性解 | **部分通过：协议已定义，缺实现/标定** |
| 接触/释放/摩擦/弹簧事件 | 大步试探仍经回退括区定位同一最早事件 | **部分通过：算法已定义，待测试** |
| 多支持退化 | 重复法向聚类；内力非唯一被报告而非伪唯一 | **部分通过：规则已定义，待构造案例** |
| 球尖与体碰撞同时发生 | 体碰撞无效优先，球尖事件同时记录 | **通过（规则），待实现回归** |
| 预载不可行 | 在规定边界稳定返回原因和最后可行状态 | **部分通过：状态机已定义，待实现** |
| 热启动失败回退 | 减步、活动集枚举和非收敛/无解分离可复现 | **部分通过：流程已定义，待实现** |
| 一致切线 | 与有限差分和第 20.4 节解析斜率一致 | **部分通过：解析基准已给，待代码** |
| 步长/容差收敛 | 事件位置、峰前反力和状态序列随加密稳定 | **仍缺实现与容差研究** |
| EB/Timoshenko 对比 | 给定 $E,\nu,\kappa$ 后评估剪切误差，必要时升级 | **仍缺材料参数/实现** |

### 25.3 A2 九类理论与算法结果落点

| 必须结果 | 章节 | 覆盖 |
|---|---|---|
| 1. 自由度、广义坐标、功共轭和单位 | 第 14 节 | 完整 |
| 2. 变形后运动学、间隙和单边互补 | 第 15、16 节 | 完整 |
| 3. 三维摩擦锥、状态和全局抓附映射 | 第 16、20 节 | 完整 |
| 4. 几何卡合、自锁、稳定平衡区别 | 第 17 节 | 完整 |
| 5. 三种结构模型的统一柔顺/刚度/储能 | 第 18 节 | 完整 |
| 6. 无拉力弹簧、原长端和硬限位 | 第 19 节 | 完整 |
| 7. 恒推力/位移混合边界单步问题 | 第 20、21 节 | 完整 |
| 8. 状态、非光滑事件、算法和回退 | 第 21、22 节 | 完整 |
| 9. 反力增长机制、验证特例和接口 | 第 20、23、25 节 | 完整 |

### 25.4 A2 完成判据逐项核对

| 判据 | 结论 |
|---|---|
| A1 候选进入闭合变形接触模型 | **满足**：位姿、梁中心线、A1 重查询、接触 Jacobian 已定义。 |
| 接触、三维摩擦、弹簧和硬限位进入同一问题 | **满足**：SOC 互补 + 梁/弹簧残量 + 活动分支。 |
| 三个概念严格区分 | **满足**：第 17.1 节。 |
| 三种结构接口统一且不重复柔顺 | **满足**：第 18.1、18.5 节。 |
| 混合边界正确 | **满足**：式 (A2-Z)/(A2-X)，$0.5$ N 未等同局部法向。 |
| 能判定主要状态和无解 | **满足规范层要求**：第 16、19、22 节。 |
| 未知量、残量、算法和伪代码可执行 | **满足**：第 21 节。 |
| 能解释/计算接触后反力增长 | **满足**：式 (A2-KT) 和临界距离。 |
| 未越界到 A3/B/C | **满足**。 |
| 未固定参数保持参数化 | **满足**。 |

结论：**A2 的机理和算法规范达到本轮完成标准；求解器代码、材料/摩擦/接触标定、容差确定和数值回归不属于本轮已完成事实。**

### 25.5 关键风险和未决问题

1. $L/d=5$–$6.67$ 使 Euler–Bernoulli 不是无条件安全近似，必须完成 Timoshenko 对比；
2. 高碳钢 $E,\nu$、强度和具体牌号未定，梁数值和 A3 强度判断不能最终化；
3. 各表面 $\mu$ 和局部接触刚度未定；
4. 弹簧移动副的真实“固定露出梁长/固定出口回缩”拓扑需 CAD 确认；
5. 多支持刚性接触可能存在内力非唯一和方向不稳定，必须报告而非隐藏；
6. 摩擦接触非线性互补没有普适全局收敛保证，需活动集枚举、减步和独立残量诊断；
7. A1 法向/支持在粗糙尖点可能非光滑，事件位置必须随几何加密收敛；
8. 全刚性固定支持模型没有有限弹性加载斜率，实验有限斜率不得被无证据地归因于接触刚度。

### 25.6 对 A3 的正式交接

A3 必须原样继承 A1+A2 的坐标、合法球冠/体碰撞、接触力符号、SOC 摩擦律、梁/弹簧状态、混合边界和能量方向。A3 首要补齐：

- `CRITICAL_SLIP` 后的接触点迁移和支持切换；
- 局部材料承载域、针体强度域和失效竞争；
- 损伤记忆、脱离、再搜索和再挂接；
- 同时摩擦/材料/几何事件的优先级；
- 100 mm 连续轨迹的多峰状态机。

A3 不得通过改变 $\mu$ 符号、弹簧限位或梁柔顺来“修复”滑移算法。

### 25.7 对 B 层的正式交接

B 层只装配多个 A2 单刺响应和共同背板平衡。必须保留每根针的：活动支持、力/矩、切线、梁/弹簧状态、剩余行程、事件和不确定性。B 层新定义多针共同 $u_z$、活动集、载荷共享和失效重分配；不得把 A2 单刺响应替换为平均力乘有效刺数。

---

# A3：滑移、局部材料失效、脱离与再挂接

## 26. A3 范围、算子、继承关系与禁止越界

### 26.1 A3 在大模块 A 中的位置

A3 从第 22 节已定位的 `CRITICAL_SLIP`、接触释放或材料检查钩子继续推进，闭合单刺连续轨迹：

$$
\text{搜索}
\rightarrow
\text{首次接触}
\rightarrow
\text{预载建立}
\rightarrow
\text{粘着加载}
\rightarrow
\text{滑移/局部失效}
\rightarrow
\text{脱离}
\rightarrow
\text{继续搜索与再挂接}.
$$

本阶段定义的完整单刺更新算子为

$$
\boxed{
\mathcal S_{A3}:
(\mathsf z_A^n,\ \mathcal Q_{A1},\ \mathcal R_{A2},\ \mathcal M_{\rm material},\ \Delta u_x)
\mapsto
(\mathsf z_A^{n+1},\ \mathbf f_c,\ \mathcal D^{n+1},\ \mathcal E,\ \mathcal O)
}
$$

其中：

- $\mathsf z_A^n$ 包含 A1 几何状态、A2 接触/结构状态以及 A3 的滑移、材料和事件历史；
- $\mathcal Q_{A1}$ 是合法球冠、支持特征、法向、曲率、复合针体碰撞、质量和域查询；
- $\mathcal R_{A2}$ 是第 21 节定义的接触—摩擦—梁/弹簧—混合边界残量及其切线；
- $\mathcal M_{\rm material}$ 是本节定义的表面局部承载、软化和损伤接口；
- $\mathcal D$ 是不改写 A1 原始表面的稀疏轻量损伤层；
- $\mathcal E$ 是滑移、支持切换、材料起始/软化/完全失效、针体上限、释放、再接触、限位和不可行事件；
- $\mathcal O$ 是沿连续 $100\ \mathrm{mm}$ 路径保存的原始响应。

A3 的输出是后续大模块 A 集成及 B 层唯一允许调用的完整单刺物理入口。[EF:PROJECT.ARCHITECTURE.DEPENDENCY]

### 26.2 必须原样继承的 A1+A2 合同

A3 不重写以下内容：

1. A1 的表面数据、可信尺度、有限球尖配置空间、合法球冠、支持集合、法向、复合针体禁止碰撞和几何质量状态；
2. A2 的接触力正方向、逐点 Signorini–Coulomb 二阶锥、最大耗散、梁/弹簧柔顺、无拉力原长端、$4\ \mathrm{mm}$ 硬限位、恒主动推力/切向位移混合边界和功符号；
3. A2 对 `SEPARATED_SEARCH` 的结论：完全分离且受非零恒力时没有静态平衡，搜索阶段是受控几何续接过程，不是伪静力平衡；
4. A1/A2 的优先级：`OUT_OF_DOMAIN`、`GEOMETRY_UNCERTAIN` 和非承载体碰撞优先于纯球尖承载。

第 25.6 节是 A2 阶段对 A3 的交接记录；本节完成其列出的任务，不删除该历史交接。

### 26.3 A3 明确不处理

A3 不建立：

- 显式三维裂纹网格、相场/XFEM、碎屑或颗粒动力学；
- 连续切削有限元、地形重网格化和针尖磨损演化；
- 多根针的共同背板平衡、载荷共享、级联重分配或独立概率乘法；
- 四单元同步收紧、偏心 wrench、整爪摇摆和整体承载；
- 导轨/框架柔性、惯性、冲击弹跳、真实传动链和复杂控制器；
- 未经批准的材料数值、事件容差、成功阈值或综合评分。

文献 05 观察到的失接跳跃只作为准静态模型风险和搜索路径参数化缺口，不引入无依据的弹道轨迹。[L05]

### 26.4 A3 直接约束的工程事实

| 事实 ID | A3 中的强制含义 |
|---|---|
| `PROJECT.OUTPUTS.NO_BINARY_SUCCESS` | 保存完整连续量、状态和事件，不设二元成功阈值。 |
| `COORDINATE.GLOBAL.FRAME`, `COORDINATE.UNIT.FRAME` | 坐标、方向、法向和局部 $+x$ 拖拽方向保持不变。 |
| `NEEDLE.CONTACT.COLLISION_BOUNDARY` | 只有球尖承载；锥段、针杆、安装座碰撞仍是致命无效事件。 |
| `NEEDLE.MATERIAL.BASE` | 针体为高碳钢，但牌号、弹性和强度参数未固定。 |
| `NEEDLE.BENDING.SWITCH` | `off` 只关闭变形，不能关闭强度检查。 |
| `ARRAY.MOUNT.AXIAL_SPRING_MODE` | 弹簧只压缩、不可拉伸、$0$–$4\ \mathrm{mm}$、到限后刚性。 |
| `SURFACE.INTERFACE.UNIFIED` | 红砖、混凝土、砂纸共享材料能力接口，不复制上层接触状态机。 |
| `LOAD.NORMAL.ACTUATOR_OUTPUT`, `LOAD.NORMAL.SINGLE_SPINE` | 恒定的是 $0.5\ \mathrm N$ 主动推力，不是局部法向反力。 |
| `LOAD.DRAG.SPEED`, `LOAD.DRAG.QUASI_STATIC`, `LOAD.DRAG.TRAVEL` | $1\ \mathrm{mm/s}$ 只映射时间；忽略惯性；总路径不超过 $100\ \mathrm{mm}$ 且脱离后不重置。 |
| `NUMERICS.DRAG.VARIABLE_STEP` | 滑移、材料、脱离、再挂接和限位附近必须减步和定位。 |
| `DAMAGE.MEMORY.LIGHTWEIGHT` | 连续过程保留不可逆轻量损伤；新试验/新表面重置；不改写地形。 |
| `SCOPE.FIRST_RELEASE.EXCLUSIONS` | 显式裂纹、碎屑、磨损和重网格化仍被排除。 |
| `UNRESOLVED.REGISTRY.GLOBAL` | 迁移、强度、损伤、钢材参数和事件容差保持参数化。 |

本轮没有发现需要修改正式工程事实的证据；A3 的全部新增内容属于机理、状态、接口和待标定参数。

## 27. A3 状态、历史变量、输入输出与数据模型

### 27.1 层次化状态

A3 延续 A2 的“主机械状态 + 正交子状态”结构，避免把摩擦、材料、弹簧和失败原因拼成不可维护的组合枚举。

#### 主机械状态

| 状态 | 定义 |
|---|---|
| `SEPARATED_SEARCH` | 无承载接触；背板路径继续，法向执行器调用受控接近过程寻找下一合法球尖候选。 |
| `TIP_ZERO_LOAD` | 合法球冠零间隙、零接触力。 |
| `PRELOAD_EQUILIBRATION` | 以 A2 同伦建立目标 $P_z=0.5\ \mathrm N$。 |
| `STICKING_LOAD` | 至少一个正压接触，所有已提交相对切向位移为零。 |
| `CRITICAL_SLIP` | A2 一侧试探证明无法继续全粘着，等待 A3 提交滑移分支。 |
| `SLIDING_CONTACT` | 至少一个支持有非零已提交切向相对位移并满足 A2 最大耗散。 |
| `REATTACHED_LOAD` | 第 $k\ge2$ 次接触循环中，重新完成预载后的第一个接受承载状态；随后转入粘着或滑移。 |
| `CONTACT_RELEASE_EVENT` | 所有可承载支持在共同事件位置失去正法向反力、合法分支或可行平衡；只作为瞬时事件状态。 |
| `REVERSIBLE_UNLOAD_RETURN` | 接触力清零后，梁/弹簧投影到零载可逆状态并记录释放能；随后进入搜索。 |
| `BODY_COLLISION_INVALID` | 非承载部件碰撞，纯球尖模型终止。 |
| `PRELOAD_INFEASIBLE` | 无法建立目标主动推力。 |
| `EQUILIBRIUM_INFEASIBLE` | 所有相容接触/滑移/材料活动分支均无物理解。 |
| `NUMERICAL_NONCONVERGENCE` | 尚不能证明物理无解，只能确认算法未收敛。 |
| `GEOMETRY_UNCERTAIN` / `OUT_OF_DOMAIN` | A1 数据质量或域不足。 |
| `TRAVEL_COMPLETE` | 连续路径达到 $100\ \mathrm{mm}$ 或外部显式终止。 |

#### 接触运动子状态

每个支持点取：

- `OPEN`；
- `TOUCH_ZERO_LOAD`；
- `STICKING_INTERIOR`；
- `STICKING_AT_CONE_BOUNDARY`；
- `SLIDING_COMMITTED`；
- `ROLLING_NO_SLIP`；
- `SUPPORT_SWITCH_PENDING`；
- `RELEASE_PENDING`。

`ROLLING_NO_SLIP` 表示接触位置在表面迁移而材料相对切向速度为零；它不是滑移，也不产生库仑耗散。

#### 材料子状态

每个损伤面片取：

- `MATERIAL_INTACT`；
- `MATERIAL_INITIATED`；
- `MATERIAL_SOFTENING`；
- `MATERIAL_RESIDUAL`；
- `MATERIAL_FULLY_FAILED`；
- `MATERIAL_MODEL_UNAVAILABLE`。

模式标签不单独决定状态，可取 `TENSILE_CHIP`、`SHEAR_BREAKOUT`、`COMPRESSIVE_CRUSH`、`ABRASIVE_SCRATCH`、`MIXED`。`ABRASIVE_SCRATCH` 是“滑移 + 剪切主导面片损伤”的标签，不另建与主容量域冲突的硬阈值。

#### 针体子状态

- `NEEDLE_ELASTIC`；
- `NEEDLE_YIELD_LIMIT`；
- `NEEDLE_FRACTURE_LIMIT`；
- `NEEDLE_STRENGTH_UNAVAILABLE`。

首版不推进针体塑性历史；达到屈服或断裂上限即终止该分支并输出上限事件。

### 27.2 完整历史状态

A3 的最低持久状态为

```text
SingleSpineHistory:
  identity:
    trial_id / surface_realization_id / needle_id / parameter_set_ids
  path:
    u_x_total / physical_time / remaining_travel
    contact_cycle_id / current_cycle_start_x
    search_distance_current / loaded_distance_current
  mechanics:
    A1_geometry_state
    A2_state_snapshot
    active_support_ids / support_feature_charts
    committed_slip_increment_by_support
    accumulated_slip_length_by_support
    previous_contact_points / normals / tangent_frames
  material:
    damage_store_handle
    active_damage_patch_ids
    capacity_utilization / active_failure_modes
    softening_coordinate / damage / residual_capacity_ratio
    dissipated_material_energy / last_material_event
  needle:
    section_resultants / stress_measures / strength_margins
  events:
    last_accepted_event / pending_brackets / rollback_snapshot
    event_sequence_number / simultaneous_event_set
  outputs:
    current_peak_record / completed_peak_records
```

历史变量只在全局步骤接受后提交。试探 Newton、B 层未来的全局迭代和事件枚举必须使用快照/回滚，禁止在未接受试探中永久增加损伤或累计滑移。

### 27.3 必需输入

| 输入 | 类型/单位 | 前置条件 |
|---|---|---|
| `A1QueryHandle` | 几何查询对象 | 表面版本、单位、法向和质量合同已验证。 |
| `A2ResidualHandle` | 残量、广义 Jacobian、事件输出 | 采用第 21 节符号和 SOC 摩擦，不得替换。 |
| $\Delta u_x$ | mm | 规定方向为局部 $+x$；可被内部事件循环细分。 |
| `MaterialAdapter` | 参数化接口 | 明确 `continuum_patch`、`resultant_capacity`、`no_damage` 或 `unavailable`。 |
| `NeedleStrengthAdapter` | 参数化接口 | 至少提供牌号/批次 ID 或明确 `unavailable`。 |
| `DamageStore` | 稀疏空间状态 | 属于当前表面实现；新试验初值为空。 |
| `SearchControllerPolicy` | 受控几何续接策略 | 只规定分离态如何在 $(u_x,u_z)$ 中向墙接近，不引入惯性。 |
| 数值配置 | 无量纲/力/长度容差 | 所有值均为待收敛验证的配置，不是工程事实。 |

### 27.4 最低输出

A3 每个接受子步输出：

- 完整全局/局部接触力与力矩、A2 反力和结构状态；
- 接触点、支持特征、法向/切向基、迁移增量、滑移增量和累计滑移；
- 材料面片、尺度桥接参数、容量裕度、损伤、模式和耗散；
- 针体截面内力、应力上界、屈服/断裂裕度；
- 主状态、所有正交子状态、事件括区、位置误差和残量；
- 搜索/加载/滑移距离、总路径和物理时间；
- 当前抓附循环和多峰记录；
- 可供 B 层调用的单刺 wrench、分支切线/割线和试探状态。

## 28. 从 `CRITICAL_SLIP` 到真实滑移提交

### 28.1 先检查多支持重分配，不能把锥边界等同脱离

设当前正压支持集合为 $\mathcal A$，锥边界集合为

$$
\mathcal B_f=
\left\{j\in\mathcal A:
\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|
\le\epsilon_f
\right\}.
$$

对规定的正向增量 $\Delta u_x>0$，A3 先求**全粘着一侧问题**：

$$
\Delta\mathbf s_j=\mathbf0,
\qquad j\in\mathcal A,
$$

并保留 A2 的全部平衡、梁/弹簧、SOC 锥和混合边界。若存在满足

$$
\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|\ge0
$$

的局部有界增量解，则通过接触间重分配继续 `STICKING_LOAD`；即使某点已在锥边界，也不提交滑移。

只有当全粘着一侧问题不可行，且至少一个相容滑移活动集存在时，才从 `CRITICAL_SLIP` 进入 `SLIDING_CONTACT`。

### 28.2 滑移活动集和未知量

令 $\mathcal S\subseteq\mathcal A$ 为试探滑移集合，$\mathcal K=\mathcal A\setminus\mathcal S$ 为粘着集合。常规平滑支持分支的 A3 未知量为

$$
\boxed{
\mathbf y_{A3}=
\left[
\mathbf y_{A2},
\{\boldsymbol\xi_j\}_{j\in\mathcal A},
\{\delta_{d,k}\}_{k\in\mathcal P_{\rm soft}}
\right]
}
$$

其中 $\boldsymbol\xi_j$ 是表面或配置空间支持特征坐标，$\delta_{d,k}$ 是正在软化的材料面片内部坐标。切向滑移增量由位姿和支持坐标计算，不作为独立任意步长。

活动条件为：

- $j\in\mathcal K$：$\Delta\mathbf s_j=\mathbf0$，摩擦力在锥内；
- $j\in\mathcal S$：$\Delta\mathbf s_j\ne\mathbf0$，并使用 A2 原式

  $$
  \boxed{
  \boldsymbol\lambda_{t,j}
  =-\mu_j\lambda_{n,j}
  \frac{\Delta\mathbf s_j}{\|\Delta\mathbf s_j\|}
  }
  $$

  或等价 SOC 投影残量；
- 任一接触仍满足 $g_j^{\rm eff}=0$、$\lambda_{n,j}>0$；否则进入释放候选。

### 28.3 滑移分支接受条件

一个滑移候选只有同时满足以下条件才可提交：

1. A2 全部残量与硬不等式通过；
2. 滑移点均在摩擦锥边界，粘着点在锥内；
3. 每点摩擦耗散

   $$
   \Delta D_{f,j}=-\boldsymbol\lambda_{t,j}\cdot\Delta\mathbf s_j\ge0;
   $$

4. 接触几何在合法球冠和有效支持特征内连续；
5. 材料和针体容量约束通过，或相应不可逆分支已在同一问题中激活；
6. 下一侧试探不要求负法向反力、弹簧拉伸或体部穿透；
7. 事件位置、状态和响应随减步收敛。

若多个滑移活动集都精确可行，按以下顺序选择代表分支：

1. 与上一接受状态及潜在滑移方向连续；
2. 总离散功误差最小；
3. 接触状态跳变和支持 ID 变化最少；
4. 最后使用确定性词典序。

若两个分支代表实质不同且证据不足的机理，不强制伪唯一；输出 `branch_nonunique=true`、候选分支及关闭条件。

### 28.4 滚动与滑移的区分

球尖是局部球面，几何接触位置可移动而不发生材料滑移。对当前接触点 $\mathbf p_j$，球面材料点速度为

$$
\mathbf v_{b,j}
=\dot{\mathbf c}_t+\boldsymbol\omega_t\times(\mathbf p_j-\mathbf c_t).
$$

墙面固定，切向相对速度为

$$
\boxed{
\mathbf v_{\rm slip,j}
=\mathbf P_{t,j}\mathbf v_{b,j},
\qquad
\mathbf P_{t,j}=\mathbf I-\mathbf n_j\mathbf n_j^{\mathsf T}.
}
$$

- 支持坐标变化且 $\mathbf v_{\rm slip}=\mathbf0$：`ROLLING_NO_SLIP`；
- $\|\mathbf v_{\rm slip}\|>0$：`SLIDING_COMMITTED`；
- 支持坐标不变且切向速度为零：普通粘着。

球形几何迁移由球心和表面决定，针尖转动只影响球面材料点速度、球冠合法性和其余针体姿态；不得用“接触点移动”直接等同摩擦滑移。

## 29. 三维球尖接触迁移、支持切换和非光滑峰顶

### 29.1 光滑表面分支的几何闭合

在一个光滑支持分支上，用二维参数 $\boldsymbol\xi=(\xi^1,\xi^2)$ 表示原表面：

$$
\mathbf p=\mathbf p(\boldsymbol\xi),
\qquad
\mathbf n=\mathbf n(\boldsymbol\xi).
$$

若 A2 可选局部法向压缩为 $c_n\ge0$，有效球心偏置半径为

$$
r=R_t-c_n.
$$

合法球尖接触的矢量闭合为

$$
\boxed{
\mathbf r_g
=\mathbf c_t-\mathbf p(\boldsymbol\xi)-r\mathbf n(\boldsymbol\xi)
=\mathbf0.
}
\tag{A3-GEO}
$$

刚性接触主线取 $c_n=0$。式 (A3-GEO) 同时包含零间隙和最近点法向条件，不能用“沿表面移动固定距离”替代。

定义配置空间切向 Jacobian

$$
\mathbf A_r(\boldsymbol\xi)=
\begin{bmatrix}
\mathbf p_{,1}+r\mathbf n_{,1} &
\mathbf p_{,2}+r\mathbf n_{,2}
\end{bmatrix}.
$$

微分后得到

$$
\boxed{
\dot{\mathbf c}_t
=\mathbf A_r\dot{\boldsymbol\xi}
-\dot c_n\mathbf n.
}
\tag{A3-MIG}
$$

在刚性接触下 $\dot c_n=0$；$\mathbf A_r$ 满列秩时，支持坐标速度可由最小二乘/QR 稳定求解。$\sigma_{\min}(\mathbf A_r)$ 逼近零表示偏置表面焦点、峰顶或支持切换风险，不允许继续用单一光滑导数外推。

若使用形状算子 $\mathcal S$ 且采用 $d\mathbf n=-\mathcal S\,d\mathbf p$ 的约定，则

$$
\mathbf P_t\,d\mathbf c_t
=(\mathbf I-r\mathcal S)\,d\mathbf p,
$$

但实现以直接 Jacobian $\mathbf A_r$ 为准，避免曲率符号约定差异。

### 29.2 客观切向滑移增量

球面接触向量为

$$
\mathbf p_j-\mathbf c_t=-r_j\mathbf n_j.
$$

在子步 $[n,n+1]$ 内，三维切向滑移增量采用中点或高阶求积：

$$
\boxed{
\Delta\mathbf s_j^G
\approx
\mathbf P_{t,j}^{n+1/2}
\left[
\Delta\mathbf c_t
+\Delta\boldsymbol\theta_t\times
(\mathbf p_j-\mathbf c_t)^{n+1/2}
\right].
}
\tag{A3-SLIP}
$$

接触局部分量为

$$
\Delta\mathbf s_j=
\mathbf T_{j,n+1/2}^{\mathsf T}\Delta\mathbf s_j^G.
$$

切向基变化时，对历史向量做最小旋转/平行传输；长期统计只累计无歧义的标量弧长

$$
\ell_{s,j}^{n+1}=\ell_{s,j}^{n}+\|\Delta\mathbf s_j\|.
$$

基于不同切向基直接相加二维分量会产生伪滑移，禁止采用。

### 29.3 高度场分支

高度场使用第 6 节同一 A1 查询：

- 光滑唯一支持时，$\boldsymbol\xi=(x,y)$，由式 (A3-GEO) 求接触点；
- 支持最大值切换、多个等高支持或曲率/拟合退化时，触发 `SUPPORT_SWITCH_PENDING`；
- A3 不重新滤波、拟合或平滑高度场；局部曲率只使用 A1 明确尺度和质量输出；
- 若直接高度场和其加密三角网格表示同一几何，迁移轨迹、支持切换、释放位置和法向必须收敛到同一极限。

### 29.4 三角网格的面—边—顶点配置空间图表

A3 对网格使用 A1 精确最近特征，不使用插值顶点法向伪造光滑表面。

#### 面分支

对三角面 $f$，法向 $\mathbf n_f$ 常数，重心坐标 $\boldsymbol\lambda$ 满足 $\lambda_i\ge0$、$\sum\lambda_i=1$：

$$
\mathbf c_t=\sum_i\lambda_i\mathbf v_i+r\mathbf n_f.
$$

任一 $\lambda_i=0$ 是到边的事件。

#### 边分支

对边 $\mathbf e(s)=\mathbf v_0+s(\mathbf v_1-\mathbf v_0)$，$s\in[0,1]$，配置空间分支为边周围圆柱片：

$$
\mathbf c_t=\mathbf e(s)+r\mathbf u(\vartheta),
$$

其中 $\mathbf u$ 位于边法平面，角度 $\vartheta$ 被相邻面的 Voronoi 法向楔限制。$s=0/1$ 或 $\vartheta$ 到楔边界分别触发顶点或面切换。

#### 顶点分支

对顶点 $\mathbf v$，配置空间分支是受顶点法向锥裁剪的球面片：

$$
\mathbf c_t=\mathbf v+r\mathbf u(\vartheta,\varphi),
\qquad \|\mathbf u\|=1.
$$

离开法向锥或出现更近面/边时触发切换。

这些图表只是 A1 有符号距离/最近特征的局部参数化，不能把网格棱角当作真实材料新增几何。加密收敛是正式接受条件。

### 29.5 多支持、非光滑峰顶与确定性选择

在多个等距支持处，A3 保留全部支持分支 $\mathcal A_g$，不平均法向。事件位置采用共同括区，随后：

1. 枚举接触开/闭、粘着/滑移和可行相邻特征；
2. 对每个分支完整重求 A2 平衡和材料/针体容量；
3. 丢弃负法向、球冠非法、体碰撞、负耗散或材料愈合分支；
4. 优先保留从左侧状态连续、功误差最小且事件序列随减步稳定的分支；
5. 若多个分支在物理可观测量上等价，只报告内力/支持非唯一；若响应不同，保留候选分支并标记证据不足。

A3 不允许在峰顶用平均法向构造一个不存在的唯一滑移方向。

## 30. 几何释放、卸载回位、继续搜索与再挂接

### 30.1 接触释放不是摩擦边界的同义词

对任一接触 $j$，到达摩擦锥边界只触发滑移活动集检查。物理释放至少需要以下一种条件成立：

1. **法向力释放**：

   $$
   \lambda_{n,j}=0
   $$

   且规定后事件方向的一侧试探满足 $\dot g_j^{\rm eff}>0$；仅有 $\lambda_n=0$ 的零载接触可继续保留为 `TOUCH_ZERO_LOAD`；
2. **合法几何分支终止**：式 (A3-GEO) 在当前及相邻支持特征上均无解，或球冠合法裕度由零转负；
3. **配置空间运动学不可行**：$\mathbf A_r$ 失秩后没有相邻面/边/顶点分支能提供与规定背板增量相容的接触中心速度；
4. **全部支持消失**：多支持集合逐点减少后没有正压合法支持；
5. **平衡不可行**：所有接触/摩擦/材料活动集都不能满足 A2 混合边界；
6. **材料完全失效后的重求解释放**：局部容量降至残余/零后，重求 A2 得到接触打开；
7. **致命几何事件**：体部碰撞、域外或几何不确定；这些不是正常脱离，而是终止/未知。

### 30.2 释放事件函数

除第 35 节统一事件表外，释放判定至少使用：

$$
E_{\lambda,j}=\frac{\lambda_{n,j}}{F_{\rm ref}},
$$

$$
E_{g,j}=\frac{g_j^{\rm eff}}{L_{\rm ref}},
$$

$$
E_{{\rm kin},j}=\frac{\sigma_{\min}(\mathbf A_{r,j})}{A_{\rm ref}},
$$

$$
E_{{\rm cap},j}=\frac{(\mathbf p_j-\mathbf c_t)\cdot\mathbf a_t-\zeta_b}{L_{\rm ref}}.
$$

$F_{\rm ref}$、$L_{\rm ref}$、$A_{\rm ref}$ 仅用于数值缩放，不是物理阈值。根被定位后必须用未缩放的法向力、间隙、合法性和分支可行性做最终判定。

### 30.3 释放后的可逆状态投影

在 `CONTACT_RELEASE_EVENT` 处先保存事件前状态：

$$
U_b^{-},\quad U_s^{-},\quad \mathbf f_c^{-},\quad
\mathcal D^{-},\quad u_x^{-},\quad t^{-}.
$$

随后接触力置零，梁和弹簧投影到零载可逆流形：

$$
\mathbf F_c=\mathbf0,
\qquad
\boldsymbol\eta_b\rightarrow\mathbf0,
\qquad
\delta_s\rightarrow0,
\qquad
r_H\rightarrow0.
$$

弹簧不允许越过原长，损伤状态不回退。该投影表示首版不解析的快速回弹/控制器卸载，不声称是分离态静力轨迹。释放的可恢复能

$$
\boxed{
E_{\rm returned}=U_b^{-}+U_s^{-}+U_c^{-}
}
$$

单独记录为返回执行器、结构阻尼或未建模动态的能量预算，不得计入摩擦或材料耗散。若该能量对再接触位置敏感，必须升级到动力学分支；首版只报告风险。

### 30.4 `SEPARATED_SEARCH` 的准静态控制过程

完全分离且 $P_z>0$ 时不存在静态平衡。A3 沿用 A2 的受控几何续接：

1. 总路径坐标 $u_x$ 继续单调增加，不重置；
2. 对当前或下一 $u_x$ 目标，`SearchControllerPolicy` 规定法向位置的单调向墙搜索序列；
3. 每个试探位置调用 A1 合法球冠和全针体查询；
4. 使用保守扫掠/括区定位最早合法球尖接触或最早致命体碰撞；
5. 在球尖接触前不构造接触力，也不把 $P_z$ 赋给任一局部法向力；
6. 搜索法向路径、最大单次法向调整和容差均为数值/控制输入，必须记录，不被包装成材料参数。

首版允许两种明确的搜索策略：

- `NESTED_Z_SEARCH`：在给定 $u_x$ 处沿 $-Z$ 内搜索首个合法接触；
- `PRESCRIBED_XZ_PATH`：沿显式连续路径 $\Gamma_{\rm search}(\xi)=(u_x(\xi),u_z(\xi))$ 搜索。

两种策略必须产生独立结果标签。没有实验控制器证据时不得静默选择一个并声称预测了真实跳跃距离。

### 30.5 再接触、再预载和再承载

定位下一合法球尖接触后：

1. 状态进入 `TIP_ZERO_LOAD`；
2. 查询损伤层，读取接触区域已有 $D$、残余容量和模式历史；
3. 以 A2 的 $P_z(\eta)=\eta P_z$ 同伦重建预载；
4. 若 $\eta=1$ 前出现体碰撞、硬限位、材料容量不足或无平衡，返回 `PRELOAD_INFEASIBLE`；
5. 若成功，接触循环编号加一，进入 `REATTACHED_LOAD`；
6. 下一接受增量按全粘着试探，再决定粘着、滑移或立即释放。

再挂接不恢复材料完整强度，不恢复总行程，也不清零物理时间。文献 03 直接支持“失接—回墙—再挂接—继续承载”的状态结构，但其二维机构刚度和阵列载荷转移不迁移到本单刺模型。[L03]

### 30.6 连续路径和循环定义

定义总路径与时间：

$$
0\le x_{\rm path}=u_x-u_x^0\le100\ \mathrm{mm},
\qquad
 t=\frac{x_{\rm path}}{1\ \mathrm{mm/s}}.
$$

第 $k$ 个接触循环是从第 $k$ 次 `TIP_ZERO_LOAD` 到随后所有正压支持完全释放的最大连续区间。支持切换、多点增减和滑移不自动结束循环；只有全部承载支持消失才结束。

每个循环至少记录：

$$
\{x_{\rm start},x_{\rm peak},x_{\rm end},
R_{x,\max},\Delta x_{\rm load},\Delta x_{\rm slide},
\text{dominant mode},\epsilon_{\rm event}\}.
$$

“峰”首先按接触循环定义，不依赖未固定的二元成功阈值。循环内部的次级局部极值可从原始曲线后处理，但不能在 A3 固定无依据的幅值阈值。

## 31. 局部材料容量、尺度桥接与模型选择

### 31.1 为什么不能使用无限承载或单点强度越限

A2 的接触力若没有材料上限，可随结构兼容继续增长。文献 05 明确反证“赫兹局部应力第一次超过宏观强度即整体脱附”；局部损伤会改变凸体承载和几何，整体失效由表面容量、针体容量、摩擦和几何共同决定。[L05]

文献 15 支持压力敏感、方向相关的多轴首次失效结构，但其判据作用于 RVE 空间平均相应力，不能直接作用于点力。[L15] 文献 14 支持起裂后软化传力、断裂能约束和完全分离结构，但其参数来自厘米级 Mode-I 三点弯曲，不能直接成为微米球尖混合模态参数。[L14]

因此 A3 必须显式定义“接触结果量 → 有限局部控制体 → 失效起始 → 能量正则化软化”的桥接。

### 31.2 候选模型比较

#### 候选 A：有限控制体应力域 + 不可逆软化（首版主线）

- 把一个或多个相邻支持的接触合力汇聚到物理尺寸固定的局部面片；
- 由有效面积构造有限牵引/应力代理；
- 在材料坐标中使用方向性、压力敏感的起始域；
- 容量按一个不可逆软化坐标缩减，耗散面积由断裂能/特征长度约束；
- 同一接口可用于红砖、混凝土，砂纸可选择经验或无损分支。

优点：变量和量纲闭合；能表达方向、围压、软化和空间记忆；可做网格/步长客观性检查。缺点：有效接触面积、控制深度和混合模态参数需标定；它仍是降阶应力代理，不是完整接触应力场。

#### 候选 B：几何特征结果量容量域 + 断裂能正则化

对经稳定分割的凸体/面片，以接触合力和力矩定义容量，例如

$$
\boxed{
\Psi_F=
\left(\frac{\langle N\rangle}{N_c}\right)^{p_N}
+\left(\frac{\|\mathbf T\|}{T_c}\right)^{p_T}
+\left(\frac{\|\mathbf M\|}{M_c}\right)^{p_M}
\le1.
}
$$

$N_c,T_c,M_c,p_N,p_T,p_M$ 均为面片几何和材料状态的标定参数，峰后同样用能量正则化软化。

优点：不需要把点力解释为唯一应力场；可直接由单刺实验辨识。缺点：稳定凸体分割在随机三维表面上困难；参数随分割尺度变化；方向性和压力敏感性缺少材料层解释；跨高度场/网格迁移较弱。

#### 选择

首版选择候选 A。候选 B 作为以下情况下的显式分支：

- 无法获得材料局部弹性/强度输入，但有充分的成品单刺结果量标定；
- 砂纸等表面不适合砖材连续体软化；
- 几何特征分割可重复且对网格加密稳定。

不得在同一面片同时启用两个容量模型后简单取标量最小值；模型选择由 `material_model_id` 明确控制。

### 31.3 损伤面片、空间核和接触汇聚

面片 $k$ 具有：

$$
\mathcal P_k=
(\mathbf x_k,\mathbf R_{m,k},a_k,\ell_k,r_{D,k},\Theta_k),
$$

其中 $\mathbf x_k$ 为材料坐标锚点，$\mathbf R_{m,k}$ 为材料方向，$a_k$ 是有效接触半径，$\ell_k$ 是控制深度，$r_{D,k}$ 是损伤核半径，$\Theta_k$ 是参数集合。

定义

$$
A_k=\pi a_k^2,
\qquad
V_k=A_k\ell_k.
$$

$a_k$、$\ell_k$、$r_{D,k}$ 都是物理/标定参数，不等同网格间距。它们不得小于当前表面查询的可信尺度而仍宣称物理有效。

对支持 $j$ 和当前可查询面片 $k$，先定义原始核权重

$$
\widetilde w_{kj}=K(\|\mathbf p_j-\mathbf x_k\|/r_{D,k}),
$$

其中 $K$ 为非负、紧支撑、版本化核。若一个支持落入多个重叠面片，按面片方向归一化

$$
\boxed{
w_{kj}=\frac{\widetilde w_{kj}}
{\sum_{m\in\mathcal P(j)}\widetilde w_{mj}},
\qquad
\sum_{k\in\mathcal P(j)}w_{kj}=1.
}
$$

若 $\mathcal P(j)$ 为空，则先按第 32.6 节确定性规则创建或匹配一个面片。这样每个接触结果量只分配一次，不因损伤核重叠被重复计入。汇聚墙面对针的接触力对应的针作用于墙的结果量：

$$
\mathbf F_k^{w}=-\sum_jw_{kj}\mathbf f_j,
$$

$$
\mathbf M_k^{w}=-\sum_jw_{kj}
(\mathbf p_j-\mathbf x_k)\times\mathbf f_j.
$$

同一物理核内的多支持先汇聚再做一次材料检查，避免把同一局部体积重复计为多个独立材料点。面片平均法向和材料方向若需由多个支持估计，使用另一个在面片内部归一化的几何权重，并保留 A1 多支持非唯一标志；不得用力分配权重平均出伪唯一法向。

### 31.4 有限牵引和应力代理

令面片平均外法向为 $\mathbf n_k$，把接触合力分解为

$$
N_k=-\mathbf n_k\cdot\mathbf F_k^{w}\ge0,
$$

$$
\mathbf T_k=
-\mathbf P_{t,k}\mathbf F_k^{w}.
$$

这里 $N_k$ 取压缩为正，$\mathbf T_k$ 与 A2 墙面对针的切向力方向一致。采用拉应力为正的 Cauchy 符号，首版力结果量应力代理为

$$
\boxed{
\bar{\boldsymbol\sigma}_k^{F}
=-\frac{N_k}{A_k}\mathbf n_k\otimes\mathbf n_k
-\frac{1}{A_k}
\left(
\mathbf T_k\otimes\mathbf n_k+
\mathbf n_k\otimes\mathbf T_k
\right).
}
\tag{A3-STRESS}
$$

该式满足

$$
\bar{\boldsymbol\sigma}_k^{F}\mathbf n_k
=-\frac{N_k\mathbf n_k+\mathbf T_k}{A_k},
$$

即给出与汇聚接触合力一致的平均表面牵引。它不是赫兹峰值或完整半空间应力解，只是显式、有限、可标定的控制体代理。

接触合矩作为独立广义应力量保存：

$$
\mathbf q_{M,k}=\frac{\mathbf M_k^{w}}{A_k\ell_k}.
$$

若有相应容量数据，可在 `moment_augmented` 分支中加入；否则只报告其数值和未覆盖风险，不用任意系数静默并入式 (A3-STRESS)。

材料坐标中的应力为

$$
\boldsymbol\sigma_k^{m}
=\mathbf R_{m,k}^{\mathsf T}
\bar{\boldsymbol\sigma}_k^{F}
\mathbf R_{m,k}.
$$

红砖挤出方向未知时，$\mathbf R_m$ 必须作为试样元数据或不确定参数；不得默认各向同性。[L15]

### 31.5 方向性、压力敏感的首次失效域

主线使用“方向变换 + Mohr–Coulomb + 拉伸截断 + 可选压缩帽”的组合。先定义由目标材料标定的正定方向变换

$$
\widehat{\boldsymbol\sigma}_k
=\mathbb H_k:\boldsymbol\sigma_k^{m},
$$

其中 $\mathbb H=\mathbb I$ 是各向同性退化分支。令 $\widehat\sigma_I\ge\widehat\sigma_{II}\ge\widehat\sigma_{III}$，拉为正、压为负。

Mohr–Coulomb 候选为

$$
\boxed{
\Phi_{MC}=
\widehat\sigma_I
\frac{1+\sin\phi}{2c\cos\phi}
-
\widehat\sigma_{III}
\frac{1-\sin\phi}{2c\cos\phi}
-1.
}
\tag{A3-MC}
$$

该结构来自文献 15，但 $c,\phi,\mathbb H$ 必须由目标材料和本项目局部尺度标定，不能复制其特定 $880^\circ\mathrm C$ 砖参数。[L15]

拉伸截断为

$$
\Phi_t=\frac{\langle\widehat\sigma_I\rangle}{f_t}-1.
$$

若目标材料数据证明需要描述高压压碎，可启用压缩帽：

$$
p=-\frac13\operatorname{tr}\widehat{\boldsymbol\sigma},
\qquad
q=\sqrt{\frac32\widehat{\mathbf s}:\widehat{\mathbf s}},
$$

$$
\Phi_c=
\left(\frac{p-p_c}{X_c}\right)^2+
\left(\frac{q}{Y_c}\right)^2-1,
\qquad p\ge p_c.
$$

没有压缩帽标定时该分支关闭，而不是填入通用混凝土值。

完整首次失效条件为

$$
\boxed{
\Phi_{\rm init}
=\max(\Phi_{MC},\Phi_t,\Phi_c\ \text{if enabled},\Phi_M\ \text{if calibrated})
\le0.
}
\tag{A3-INIT}
$$

模式判定：

- $\Phi_t$ 唯一控制：`TENSILE_CHIP`；
- $\Phi_{MC}$ 唯一控制：`SHEAR_BREAKOUT`；
- $\Phi_c$ 唯一控制：`COMPRESSIVE_CRUSH`；
- 滑移且剪切模式控制：附加 `ABRASIVE_SCRATCH`；
- 多个面在并发容差内：`MIXED`。

### 31.6 容量集合和射线利用率

为统一不同起始面，定义无损容量集合

$$
\mathcal C_{0,k}
=\{\boldsymbol\sigma:\Phi_{\rm init}(\boldsymbol\sigma;\Theta_k)\le0\}.
$$

若该集合关于原点星形，定义射线利用率（Minkowski 泛函）

$$
\boxed{
r_k^0(\boldsymbol\sigma)
=\inf\{\gamma>0:\boldsymbol\sigma/\gamma\in\mathcal C_{0,k}\}.
}
\tag{A3-UTIL}
$$

$r_k^0<1$ 为无损域内，$r_k^0=1$ 为首次失效。对于式 (A3-MC) 和拉伸截断，利用率可解析或一维求根；对带帽面用可靠的一维射线求交。这样避免把不同物理面任意相加成一个无量纲分数。

### 31.7 不同表面类别的同一接口

`MaterialAdapter` 至少支持：

| 分支 | 适用对象 | 处理 |
|---|---|---|
| `continuum_patch` | 有目标参数的红砖/混凝土 | 使用式 (A3-STRESS)–(A3-UTIL) 和第 32 节软化。 |
| `resultant_capacity` | 有直接单刺结果量标定的表面或砂纸 | 使用候选 B，不改变接触/状态机。 |
| `no_damage` | 只研究几何+摩擦的对照 | 材料容量视为无穷，但明确输出模型开关和适用边界。 |
| `unavailable` | 参数不足且不允许无损假设 | 返回 `MATERIAL_MODEL_UNAVAILABLE`，不产生伪强度。 |

上层状态机、A1 几何和 A2 摩擦不按材料类别复制。

## 32. 不可逆软化、断裂能正则化与轻量损伤记忆

### 32.1 软化变量和容量缩减

每个损伤面片保存位移量纲的内部软化坐标

$$
\delta_{d,k}\ge0,
\qquad
\delta_{d,k}^{n+1}\ge\delta_{d,k}^{n}.
$$

在首次失效事件创建面片时 $\delta_d=0$。定义残余容量比 $0\le\rho_k<1$ 和线性软化容量系数

$$
\boxed{
q_k(\delta_d)=
\rho_k+(1-\rho_k)
\max\left(1-\frac{\delta_d}{\delta_{f,k}},0\right).
}
\tag{A3-SOFT}
$$

损伤变量为

$$
\boxed{
D_k=
\min\left(\frac{\delta_{d,k}}{\delta_{f,k}},1\right).
}
$$

损伤容量集合采用首版同心缩放：

$$
\mathcal C_k(D_k)=q_k\mathcal C_{0,k}.
$$

因此材料可行条件为

$$
\boxed{
r_k^0(\boldsymbol\sigma_k)\le q_k(\delta_{d,k}).}
\tag{A3-CAP}
$$

这是降阶软化容量，不声称给出真实裂纹路径。$\rho$ 保持待标定参数；只有显式选择并记录 `zero_residual_candidate` 时才可令 $\rho=0$ 作为完全失载候选，不能把零残余静默设为所有材料的默认值。非零残余也必须单独标定，且不被解释为碎屑动力学。

### 32.2 损伤一致性条件

加载/卸载使用

$$
\dot\delta_{d,k}\ge0,
\qquad
\psi_k=q_k-r_k^0\ge0,
\qquad
\boxed{
\dot\delta_{d,k}\,\psi_k=0.
}
\tag{A3-DKKT}
$$

- $r^0<q$：弹性/几何卸载，$\dot\delta_d=0$；
- $r^0=q$ 且后续加载需要降低容量：`MATERIAL_SOFTENING`；
- $\delta_d=\delta_f$：`MATERIAL_FULLY_FAILED` 或有证据时 `MATERIAL_RESIDUAL`。

式 (A3-DKKT) 与 A2 平衡、滑移和结构残量共同求解。局部失效后必须重求平衡；损伤标记本身不等于立即脱离。

### 32.3 断裂能和特征长度

在材料起始时保存当前等效峰值牵引

$$
T_{0,k}=\frac{\|\mathbf F_k^{w}\|}{A_k}
$$

及主导模式/模式混合。$\delta_{d,k}$ 被解释为面片过程区的**等效局部化位移**，与等效软化牵引功共轭；它不是 A1 表面高度的几何退缩，也不用于移动网格节点。首版 `capacity_softening` 分支通过“旧容量的弹性试探 → 超出容量时返回到 $r=q$ → 全局功平衡检查”确定其增量。若该降阶分支无法同时满足平衡和功误差门槛，必须切换到带显式局部化位移/牵引—分离兼容残量的 `cohesive_displacement` 升级分支，不能仅为收敛任意增加损伤。

令标定的有效断裂能为 $G_{c,k}^{\rm mix}$，单位在内部使用 $\mathrm{N/mm}$。线性软化的耗散面积满足

$$
G_{c,k}^{\rm mix}
=\int_0^{\delta_{f,k}}
(1-\rho_k)T_{0,k}
\left(1-\frac{\delta_d}{\delta_{f,k}}\right)d\delta_d,
$$

故

$$
\boxed{
\delta_{f,k}
=\frac{2G_{c,k}^{\rm mix}}
{(1-\rho_k)T_{0,k}}.
}
\tag{A3-DF}
$$

累计材料耗散为

$$
\boxed{
\mathcal D_{m,k}(\delta_d)
=A_k(1-\rho_k)T_{0,k}
\left(
\delta_d-\frac{\delta_d^2}{2\delta_{f,k}}
\right),
\quad 0\le\delta_d\le\delta_f.
}
\tag{A3-ENERGY}
$$

完全软化时 $\mathcal D_{m,k}=A_kG_{c,k}^{\rm mix}$。该面积约束继承文献 14 “软化曲线面积为断裂能、达到临界张开后完全分离”的结构，但 $G_c$、$T_0$ 和软化形状必须在本项目局部尺度标定。[L14]

若采用应变型局部损伤实现，则用控制体特征长度 $\ell_k$ 将等效非弹性应变转为位移：

$$
\delta_d=\ell_k\varepsilon_d,
$$

并保持每单位失效面积耗散 $G_c$ 不随网格改变。这与裂带理论的能量正则化原则一致，但本项目不把混凝土参数或网格带宽直接迁移为红砖微接触值。[E-CRACKBAND]

### 32.4 混合模态能量分支

Mode-I 证据不能直接覆盖剪切/压碎。首版允许经目标试验标定的模式插值：

$$
\chi_s=\frac{Y_s}{Y_n+Y_s+\epsilon_Y},
$$

$$
\boxed{
G_c^{\rm mix}=G_I+(G_S-G_I)\chi_s^{\eta_G}.
}
\tag{A3-MIXG}
$$

$Y_n,Y_s$ 是起始时由拉伸/剪切驱动量构造的非负权重；$G_I,G_S,\eta_G$ 全部未固定。压缩破碎使用独立 $G_C$ 分支或保持不可用，禁止用 Mode-I $G_F$ 直接代替。

首版在面片起始时冻结 $T_0$、模式标签和 $G_c^{\rm mix}$，适用于近比例软化路径。若非比例加载导致模式显著旋转，启用 `variable_mode` 分支或终止为模型不足。NASA 的混合模态黏聚模型证明“单一不可逆历史变量 + 模式相关断裂能”是可执行结构，但其复合材料参数和具体 B-K 指数不能迁移到砖材。[E-COHESIVE]

### 32.5 避免与摩擦、梁和弹簧重复耗散

材料损伤只缩减面片容量并记录式 (A3-ENERGY) 的材料耗散；它不修改：

- A2 的摩擦系数或 SOC 最大耗散；
- 梁弹性模量、梁储能或几何柔顺；
- 弹簧刚度、原长或硬限位；
- A1 原始高度场/网格。

总耗散分开记录：

$$
\boxed{
\Delta D_{\rm total}
=\Delta D_f+\Delta D_m
\ge0.
}
$$

若实现额外局部接触柔顺，其储能/耗散仍按 A2 独立字段记录。禁止用同一个经验折减系数同时降低摩擦、材料强度和弹簧/梁刚度。

### 32.6 空间键和损伤查询

损伤记录不以瞬时网格元素编号作为唯一身份。最低键为

```text
DamagePatchKey:
  surface_realization_id
  material_frame_id
  anchor_position_in_surface_frame
  kernel_radius_and_version
  creation_cycle_and_event_id
  source_feature_ids_for_traceability
```

锚点位于固定表面材料坐标。查询位置 $\mathbf x$ 的有效损伤采用明确核聚合，例如

$$
D_{\rm eff}(\mathbf x)
=\max_k\left[D_k K(\|\mathbf x-\mathbf x_k\|/r_{D,k})\right].
$$

使用 `max` 可避免重叠核反复乘折减；若采用其他聚合必须做能量和网格客观性验证。相邻接触落入已有兼容核时更新同一面片；否则创建新面片。核尺寸不随网格自动缩小。

### 32.7 每个面片的最低历史字段

```text
DamagePatchState:
  patch_id / key / parameter_set_id
  anchor / material_frame / area / control_depth / kernel_radius
  D / softening_coordinate / final_softening_coordinate
  residual_capacity_ratio / capacity_scale
  initiation_stress_proxy / T0 / frozen_mode_mix
  active_failure_mode_weights
  max_undamaged_utilization
  material_dissipation
  last_contact_position / last_event_x / last_event_time
  update_count / provenance / uncertainty_flags
```

初值为 $D=0$、$\delta_d=0$、耗散为零。所有历史量单调或有明确可逆属性；不得在卸载、脱离或再接触时愈合。

### 32.8 生命周期

- 同一次连续 $100\ \mathrm{mm}$ 拖拽内保留；
- 未来 B 层多针可通过同一 `DamageStore` 查询，但 A3 本身不定义多针载荷重分配；
- 新的独立试验、不同随机表面实现或显式重置命令从空损伤层开始；
- A1 原始表面 ID 和数据保持不可变；
- 不生成碎屑、不改变高度、不重网格。

### 32.9 网格、核和步长客观性

至少执行三类收敛检查：

1. **几何网格加密**：保持 $a_k,\ell_k,r_D$ 的物理尺寸不变，比较面片位置、利用率和耗散；
2. **损伤核扫描**：在有单刺试验约束下扫描物理核尺寸，避免由任意核产生无限强或无限软结果；
3. **位移步长加密**：材料起始、完全失效、峰值和总耗散应收敛，且 $\sum_k\mathcal D_{m,k}$ 不随步数无界增长。

若结果只能通过把核尺寸等于网格尺寸才能匹配，模型不可接受。

## 33. 针体自身强度上限接口

### 33.1 截面内力和坐标

A2 已在针局部右手基 $\{\mathbf a,\mathbf b,\mathbf c\}$ 中输出任意截面，特别是梁根截面的六个结果量：

$$
\boxed{
\mathbf s_N=
[N,\ V_b,\ V_c,\ T,\ M_b,\ M_c]^{\mathsf T}
}
$$

其中 $N$ 沿 $+\mathbf a$ 为拉力，$V_b,V_c$ 为横向剪力，$T$ 为绕 $\mathbf a$ 的扭矩，$M_b,M_c$ 为双轴弯矩。若 `needle_bending=off`，这些结果量仍由刚体针的接触 wrench 和安装约束平衡计算；关闭变形不能把截面强度设为无穷。

对直径 $d$ 的实心圆截面，令 $R=d/2$，有

$$
A=\frac{\pi d^2}{4},
\qquad
I=\frac{\pi d^4}{64},
\qquad
J=\frac{\pi d^4}{32}.
$$

### 33.2 弹性截面应力映射

在截面坐标 $(y,z)$ 中，一阶轴向—弯曲正应力为

$$
\boxed{
\sigma_{aa}(y,z)
=\frac{N}{A}-\frac{M_b}{I}z+\frac{M_c}{I}y.
}
$$

圆周上的最大正应力绝对值为

$$
\boxed{
\sigma_{ab,\max}
=\frac{|N|}{A}
+\frac{R}{I}\sqrt{M_b^2+M_c^2}.
}
\tag{A3-NEEDLE-N}
$$

扭转载荷的外表面最大剪应力为

$$
\boxed{
\tau_T=\frac{|T|R}{J}
=\frac{16|T|}{\pi d^3}.
}
$$

圆截面横向剪力的经典最大值为

$$
\tau_V
=\frac{4}{3A}\sqrt{V_b^2+V_c^2}.
$$

在不求解完整截面剪应力矢量叠加时，首版使用明确标记为保守的上界

$$
\tau_{\rm ub}=\tau_T+\tau_V,
$$

并定义

$$
\boxed{
\sigma_{\rm vm}^{\rm ub}
=\sqrt{\sigma_{ab,\max}^2+3\tau_{\rm ub}^2}
}
\tag{A3-NEEDLE-VM}
$$

以及最大主拉应力上界

$$
\boxed{
\sigma_1^{\rm ub}
=\frac12\left(
\sigma_{ab,\max}
+\sqrt{\sigma_{ab,\max}^2+4\tau_{\rm ub}^2}
\right).
}
$$

若需要减少保守性，升级分支必须在圆截面上解析或数值搜索完整三维应力场，而不是任意降低上界系数。所有应力使用 N/mm$^2$（MPa）。

### 33.3 屈服、塑性弯曲和断裂候选事件

`NeedleStrengthAdapter` 最低提供：材料/批次 ID、温度与热处理状态、$E,\nu$、屈服强度或证明应力 $\sigma_y$、极限/断裂强度 $\sigma_u$，以及数据来源和不确定度。事件函数定义为

$$
E_{N,y}=1-\frac{\sigma_{\rm vm}^{\rm ub}}{\sigma_y},
$$

$$
E_{N,u}=1-\frac{\sigma_1^{\rm ub}}{\sigma_u}.
$$

若材料适合其他失效准则，例如脆性最大主应力、断裂力学或扭剪主导准则，可由适配器增加独立裕度，但必须保留所需缺口/裂纹尺度和试验适用边界，不能把通用高碳钢网页值设为成品针唯一参数。

首版事件处理为：

1. $E_{N,y}=0$：输出 `NEEDLE_YIELD_LIMIT`，终止当前线弹性分支；不在 A3 内推进塑性铰或残余变形；
2. $E_{N,u}=0$：输出 `NEEDLE_FRACTURE_LIMIT`，终止当前单刺承载分支；
3. 强度参数缺失：输出 `NEEDLE_STRENGTH_UNAVAILABLE`；力学可继续作为“未检查上限”的候选结果，但不得宣称安全；
4. 若几何非线性/弹性失稳先使 A2 梁模型失效，先返回结构模型越界，而不是继续比较材料强度。

### 33.4 墙面失效与针体失效的竞争

墙面容量和针体容量是同一平衡状态上的两个不同约束：

$$
\Phi_{m,k}\le0,
\qquad
E_{N,y}\ge0,
\qquad
E_{N,u}\ge0.
$$

A3 不把它们压缩为一个未经解释的标量
$\min(F_{\rm wall},F_{\rm needle})$。增量步骤中分别监控各自事件函数，在共同事件位置求同一接触/结构平衡，并记录：

- 哪个约束先到零；
- 两个事件是否在并发容差内；
- 墙面损伤更新后重求平衡是否使针体裕度恢复或继续恶化；
- 针体达到上限时墙面是否仍未启动、已软化或已完全失效。

文献 05 支持“表面凸体能力与刺体上限竞争”的结构，但其经验力式和具体数值不迁移。[L05]

## 34. A3 耦合残量、活动分支和可执行单步算法

### 34.1 固定平滑分支上的残量结构

在给定支持图表、接触开闭状态、摩擦模式、材料模式和弹簧状态后，A3 将未知量写为

$$
\mathbf y_{A3}
=
\left[
\mathbf y_{A2},
\{\boldsymbol\xi_j\}_{j\in\mathcal A},
\{\delta_{d,k}\}_{k\in\mathcal P_a}
\right],
$$

其中 $\boldsymbol\xi_j$ 是第 29 节的表面/配置空间特征坐标，$\mathcal P_a$ 是本步可能更新的损伤面片集合。耦合残量按物理块分开：

$$
\boxed{
\mathbf R_{A3}=
\begin{bmatrix}
\mathbf R_{A2}\\
\{\mathbf r_{{\rm mig},j}\}_{j\in\mathcal A}\\
\{\mathbf r_{{\rm mat},k}\}_{k\in\mathcal P_a}
\end{bmatrix}
=\mathbf0.
}
\tag{A3-RES}
$$

- $\mathbf R_{A2}$ 是第 21 节原样复用的法向平衡、梁、弹簧和 SOC 接触—摩擦残量；
- $\mathbf r_{{\rm mig},j}$ 是式 (A3-GEO) 及接触图表内部约束；
- $\mathbf r_{{\rm mat},k}$ 实现第 32 节不可逆软化互补。

一种适合半光滑 Newton 的材料投影残量为

$$
\boxed{
 r_{{\rm mat},k}
=
\Delta\delta_{d,k}
-
\Pi_{\mathbb R_+}
\left(
\Delta\delta_{d,k}
+\rho_{d,k}[r_k-q_k]
\right)
=0,
}
\tag{A3-DPROJ}
$$

其中 $\Delta\delta_{d,k}=\delta_{d,k}^{n+1}-\delta_{d,k}^{n}$，$\rho_{d,k}>0$ 只用于数值尺度化。精确零点必须对 $\rho_{d,k}$ 不敏感。若材料模式为未启动/卸载，则 $\Delta\delta_{d,k}=0$；若活动软化，则 $r_k=q_k$。

### 34.2 试探、提交和回滚语义

所有 A3 历史量必须提供三态事务接口：

```text
snapshot()  -> immutable state_n
trial(...)  -> state_trial, residuals, events    # 不改写永久状态
commit(state_trial)                              # 只在接受子步后调用
rollback(state_n)                                # 事件括区/全局迭代失败时恢复
```

以下量只能在 `commit` 时增加：累计滑移、损伤、材料耗散、事件序号、路径坐标和峰记录。B 层未来对多针共同平衡做 Newton 时，可反复调用 A3 `trial`，但不能在全局残量尚未接受时永久损伤表面。

### 34.3 首版非光滑求解策略

首版采用“事件驱动外循环 + 有限活动分支枚举 + 半光滑 Newton/括区定位”。理由是：单刺候选支持和并发机制数目通常有限，而直接把所有支持、摩擦、损伤、释放和图表切换放入一个无约束黑箱会掩盖物理竞争。

每个固定分支内：

1. 用 A2 热启动预测 $u_z$、梁/弹簧状态和接触力；
2. 用 A1 上一步支持特征和邻域构建迁移图表；
3. 组装式 (A3-RES) 的一致/广义 Jacobian；
4. 用阻尼半光滑 Newton 求解；
5. 线搜索不得跨越体碰撞、球冠非法、损伤下界/上界或特征图表边界；
6. 任何不光滑切换先返回事件括区，再在事件点枚举后事件分支；
7. 只有全部块残量、硬不等式、能量和状态一致性通过后接受。

A1 后端若不能提供解析导数，可使用局部自动微分、复步/中心差分或几何图表解析导数，但必须做步长收敛；不能对支持切换点使用单侧导数伪装光滑。

### 34.4 完整单步伪代码

```text
INPUT:
  accepted full state z_n
  requested board increment Delta_u_x > 0
  A1QueryHandle, A2ResidualHandle
  MaterialAdapter, NeedleStrengthAdapter, DamageStore

STATE:
  remaining_increment = Delta_u_x
  rollback_snapshot = snapshot(z_n)
  event_loop_count = 0

WHILE remaining_increment > numerical_zero:
  1. Check domain, geometry quality and complete-body clearances at the current state.
     Fatal A1 status or body collision terminates before any material/contact update.

  2. If primary state is SEPARATED_SEARCH:
       a. advance the prescribed x coordinate only within a certified geometric step;
       b. call the selected quasi-static SearchControllerPolicy for normal approach;
       c. use A1 to locate the earliest legal cap contact or fatal geometry event;
       d. on legal contact, create TIP_ZERO_LOAD and run the unchanged A2 preload homotopy;
       e. query existing damage patches before accepting the first loaded state;
       f. mark REATTACHED_LOAD when contact_cycle_id >= 2.
     Continue the loop with any unused x increment.

  3. For an attached state, first solve the one-sided all-sticking A2 problem.
     If it is feasible, update geometry/support charts and continue STICKING_LOAD.

  4. If all-stick is infeasible, enumerate candidate sliding sets drawn from cone-boundary contacts.
     For each set:
       a. solve A2 SOC maximum-dissipation equations together with A3 migration charts;
       b. require nonzero committed slip only on the sliding set;
       c. reject branches with negative normal force, illegal cap, body collision,
          incompatible feature velocity or negative frictional dissipation.

  5. At every converged mechanical trial:
       a. aggregate contact resultants into physical damage patches;
       b. evaluate undamaged material initiation, current softened capacity and mode mix;
       c. evaluate needle section stresses and strength margins;
       d. form all event functions and detect whether the trial crosses an event.

  6. If an event is crossed:
       a. rollback to the last accepted state;
       b. bracket the earliest event in path coordinate;
       c. at every bracket point re-solve the complete coupled equilibrium;
       d. locate the common event position and construct the simultaneous event set;
       e. enumerate all physically compatible post-event branches;
       f. apply irreversible damage only to trial copies, re-solve equilibrium,
          and accept according to Section 35.4.

  7. If material softening is active, solve the damage projection residual jointly.
     After any irreversible update, re-solve A2 balance; do not equate damage with release.

  8. If all positive-load supports open or all legal branches disappear:
       a. commit CONTACT_RELEASE_EVENT at the located position;
       b. project beam and spring to the reversible zero-load state;
       c. retain DamageStore and total path/time;
       d. enter SEPARATED_SEARCH without resetting u_x_total.

  9. If a trial is converged and contains no earlier event:
       a. verify residual blocks, complementarity, energy, dissipation and hard inequalities;
       b. commit slip, damage, path and outputs atomically;
       c. update peak/cycle records;
       d. reduce remaining_increment by the accepted subincrement.

 10. If no branch is physically feasible, return EQUILIBRIUM_INFEASIBLE.
     If feasibility cannot be decided because iterations fail, return NUMERICAL_NONCONVERGENCE.
     If the material/needle adapter is unavailable, keep the mechanical result explicitly
     uncertified rather than silently assuming infinite capacity.

 11. Stop at 100 mm total travel, fatal geometry/body event, needle terminal limit,
     user-specified termination or persistent numerical failure.
```

### 34.5 物理无解、证据不足和数值失败必须分开

- `EQUILIBRIUM_INFEASIBLE`：已枚举的全部相容接触/滑移/材料活动分支均违反物理约束；
- `MATERIAL_MODEL_UNAVAILABLE` / `NEEDLE_STRENGTH_UNAVAILABLE`：力学解存在，但缺少证据支持容量结论；
- `NUMERICAL_NONCONVERGENCE`：尚不能证明无解，算法未通过残量/收敛门槛；
- `GEOMETRY_UNCERTAIN`：A1 输入不足，不能继续作力学解释。

禁止把数值失败记录为“材料失效”，也禁止把材料参数缺失等价为无限强度。

## 35. 事件函数、同时事件、优先级和自适应减步

### 35.1 事件清单和量纲

| 事件 | 事件函数/监控量 | 单位或尺度 | 事件含义 |
|---|---|---|---|
| 摩擦边界 | $E_{f,j}=\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|$ + 正向试探 | N | 锥边界；只有试探不可全粘着才提交滑移。 |
| 接触释放 | $E_{\lambda,j}=\lambda_{n,j}$ 与打开侧 $g_j^{+}$ | N、mm | 正压力到零且下一侧间隙打开。 |
| 支持图表边界 | 面重心坐标、边参数端点或特征活跃约束 | 1 或 mm | 面—边—顶点/支持特征切换。 |
| 迁移退化 | 最小奇异值 $\sigma_{\min}(\mathbf A_{r,j})$ | 1 或 mm | 规定运动无相容接触速度或图表病态。 |
| 球冠合法性 | $E_{{\rm cap},j}=\zeta_j-\zeta_b$ | mm | 接触越出真实暴露球冠。 |
| 材料起始 | $E_{m0,k}=1-r_k^0$ | 1 | 完整材料域首次到达。 |
| 软化活动 | $E_{mq,k}=q_k-r_k$ | 1 | 当前软化容量是否饱和。 |
| 完全失效 | $E_{mf,k}=\delta_{f,k}-\delta_{d,k}$ | mm | 面片达到残余/完全失效端。 |
| 针体屈服/断裂 | $E_{N,y},E_{N,u}$ | 1 | 线弹性上限或断裂上限。 |
| 弹簧原长/硬限位 | $\delta_s$, $\delta_{\max}-\delta_s$ | mm | A2 既定单边限位。 |
| 非承载体碰撞 | $g_{\rm cone},g_{\rm shaft},g_{\rm mount}$ | mm | 致命无效。 |
| 几何质量/域 | A1 质量标志、边界距离 | 状态、mm | 数据不足或域外。 |
| 平衡退化 | 分支 Jacobian 最小奇异值/条件数 | 缩放后无量纲 | 平衡折点、非唯一或数值风险。 |

材料软化坐标若不是物理位移，必须给出明确单位和与 $G_c$ 的功共轭关系；表中不得把无量纲损伤 $D$ 与长度 $\delta_d$ 混用。

### 35.2 事件括区和定位

试探子步若出现符号跨越、活动特征变化、Jacobian 条件突变或残量无法连续下降，则：

1. 回滚到最后接受状态；
2. 建立路径区间 $[u_{x,L},u_{x,R}]$；
3. 对所有可能事件同时保留候选，不先按 if/else 删除；
4. 用二分、Brent 或保持括区的分支连续法定位最早共同事件；
5. 每个括区点重新求完整 A2+A3 平衡、材料利用率和针体裕度；
6. 同时满足位置误差、分块残量、事件函数和活动集一致性后才提交。

不得只对上一步事件函数线性插值，因为法向、接触力、损伤和支持特征均随 $u_z$ 与结构平衡改变。

### 35.3 固定致命优先级

同一事件容差窗口内，只有以下两类保持 A1/A2 已固定的优先级：

1. `OUT_OF_DOMAIN` / `GEOMETRY_UNCERTAIN`：输入不足，停止作物理排序；
2. 锥段、针杆或安装座碰撞：纯球尖承载模型无效。

除这两类外，摩擦、材料、针体、释放、支持切换和弹簧限位均先进入共同事件集合，不得预先用 if/else 抹去竞争。若共同集合含 `NEEDLE_FRACTURE_LIMIT`，记录同位置的全部其他事件和最后一个弹性平衡后终止，因为首版没有断针后的承载分支；若含 `NEEDLE_YIELD_LIMIT`，将其标为线弹性模型边界并终止或转交未来显式塑性分支。该终止规则不把同时发生的墙面失效或释放从事件记录中删除。

### 35.4 非致命并发事件的分支竞争

对共同事件位置的集合

$$
\mathcal E^*=
\{
\text{friction},\text{material},\text{needle yield},
\text{release},\text{support switch},\text{spring limit}
\},
$$

A3 枚举由这些事件生成的相容后状态，例如：

- 继续粘着并重新分配；
- 某些支持滑移、其余粘着；
- 支持切换后粘着或滑移；
- 材料启动后继续承载、软化滑移或完全释放；
- 某接触打开而其余接触重平衡；
- 弹簧到限同时进入滑移/材料软化。

每个候选分支均执行：不可逆变量试探更新 → 完整平衡重求解 → 事件一侧一致性检查。确定性接受顺序为：

1. 满足全部硬约束和残量；
2. 不违反时间方向：滑移、损伤和路径历史不回退；
3. 摩擦和材料耗散均非负；
4. 与事件前状态在未发生跳变的可逆变量上最连续；
5. 若仍有多个物理等价解，保留非唯一报告并按固定词典序选择代表解。

若两个候选代表实质不同、证据无法区分的材料机理，则作为有显式配置 ID 的候选分支保留，不静默选定为唯一物理真相。

### 35.5 自适应步长和循环保护

步长上限同时受以下预测约束：最近几何/体碰撞距离、摩擦裕度、材料容量裕度、软化剩余坐标、针体裕度、弹簧剩余行程和 Jacobian 条件。事件附近按括区减步；离开事件后只有在连续若干接受步中活动集和残量稳定，才几何增长步长。

具体初始步长、最小步长、增长率和事件容差均未固定。实现必须设置：

- 单一外部增量内的最大事件循环次数；
- 零长度事件的重复检测和状态哈希；
- 同一位置往返图表/活动集的循环诊断；
- 达到最小步长仍无法区分物理分支时返回 `NUMERICAL_NONCONVERGENCE`。

不得通过任意“跳过当前凸起”来摆脱循环；跳过只能是受控搜索路径、明确的几何释放，或未来动力学扩展。

## 36. 连续 $100\ \mathrm{mm}$ 输出、多峰记录和 A→B 接口

### 36.1 连续路径坐标和时间

全过程只使用一个不重置的总路径坐标

$$
0\le x_{\rm total}=u_x-u_x^{\rm start}\le100\ \mathrm{mm},
$$

$$
t=\frac{x_{\rm total}}{1\ \mathrm{mm/s}}.
$$

每次脱离只结束当前接触循环，不重置 $x_{\rm total}$、物理时间或损伤层。每个循环另存：

$$
x_{\rm search}^{(k)},\quad
x_{\rm preload}^{(k)},\quad
x_{\rm stick}^{(k)},\quad
x_{\rm slide}^{(k)},\quad
x_{\rm attached}^{(k)}.
$$

这些局部距离之和与总路径增量必须闭合。

### 36.2 每个接受子步的原始输出

```text
trajectory:
  total_path_x / physical_time / accepted_step / event_location_error
  contact_cycle_id / state_dwell_distance
  current_search_distance / loaded_distance / sliding_distance

geometry_and_motion:
  tip_pose / support_ids / feature_types / feature_coordinates
  contact_points / normals / tangent_frames / local_curvatures
  migration_increment / objective_slip_increment / accumulated_slip
  cap_legality / body_clearances / A1_quality

mechanics:
  force_and_moment_by_support in all required frames
  resultant_wrench / grip_resistance / board_normal_position
  beam_state / spring_state / hard_stop_reaction
  A2_and_A3_residual_blocks / branch_Jacobian_diagnostics

material:
  queried_damage_patch_ids / effective_damage
  control_area / depth / material_frame / bridge_version
  initiation_utilization / softened_capacity / failure_mode_weights
  damage / softening_coordinate / residual_capacity
  material_dissipation / uncertainty_and_parameter_ids

needle:
  N / V_b / V_c / T / M_b / M_c
  stress_bounds / yield_margin / fracture_margin / strength_parameter_id

state_and_events:
  primary_state / contact_substates / material_substates / needle_substate
  event_candidates / simultaneous_event_set / accepted_event
  rollback_count / convergence_status / physical_or_numerical_failure_class

energy:
  external_work / beam_energy / spring_energy / optional_contact_energy
  friction_dissipation / material_dissipation / released_recoverable_energy
  work_balance_error
```

在没有二元成功阈值时，这些连续量和事件是正式输出；任何后处理评分都不得替代原始记录。[EF:PROJECT.OUTPUTS.NO_BINARY_SUCCESS]

### 36.3 抓附峰定义和记录

一个峰候选记录从某次 `TIP_ZERO_LOAD`/`REATTACHED_LOAD` 后首次出现正抓附反力开始，到对应接触循环释放、终止或反力回到零附近结束。对第 $k$ 个循环保存：

```text
PeakRecord:
  peak_id / contact_cycle_id
  start_x / peak_x / end_x
  start_time / peak_time / end_time
  peak_grip_resistance and complete_wrench
  integrated_positive_resistance
  search_distance_before_peak
  sticking_and_sliding_distance
  dominant_failure_mode and simultaneous_events
  support_and_damage_patch_ids
  event_location_error / numerical_quality / evidence_status
```

“主导失效模式”由事件位置的活动约束、耗散增量和裕度共同判定；若摩擦、材料和释放并发，记录 `MIXED/UNRESOLVED_ORDER`，不得任意选一个标签。至少两个独立接触循环的构造轨迹是未来实现回归测试，不是本轮已经运行的实验结果。

### 36.4 A→B 单刺调用合同

完整 A 算子向 B 层暴露事务式接口：

```text
SingleSpineTrialResponse evaluate_trial(
    base_pose_n,
    prescribed_base_increment,
    immutable_single_spine_state_n,
    shared_damage_store_snapshot,
    parameter_bundle,
    requested_tangent_mode
)

commit(trial_response)
rollback(trial_response)
```

最低返回：

```text
SingleSpineTrialResponse:
  resultant_force_and_moment_at_declared_reference
  algorithmic_tangent_or_secant
  tangent_status: smooth | generalized | branch_dependent | unavailable
  active_supports / contact_forces / feature_charts
  beam_and_spring_state / remaining_spring_travel
  material_damage_queries_and_trial_updates
  needle_strength_margins
  primary_state / events / event_fraction_within_increment
  A1_query_callbacks / A2_residual_callbacks
  residuals / quality / uncertainty
  trial_state_handle
```

由于库仑摩擦、活动集和损伤可使算法切线非对称、分支相关，B 层必须读取 `tangent_status`，不能假定一个全局对称刚度。B 层可缩小共同增量并重调 A3 `trial`；只有阵列共同平衡接受后才能提交每根针的状态和共享损伤更新。

### 36.5 B 层禁止重定义

B 层不得重新定义：A1 几何、A2 SOC 摩擦、A3 接触迁移、材料容量/损伤、针体强度、脱离或再挂接。B 层只新增共同背板平衡、多针活动集、载荷共享和重分配。共享 `DamageStore` 使后续针经过同一空间区域时读取相同历史，但何时由哪根针加载该区域属于 B 的全局求解，不由 A3 预设。

## 37. 参数、证据、标定状态与迁移边界

### 37.1 本地文献证据

- `[L03] 文献03`：支持未挂接、承载、脱附、回位和再挂接的状态结构，以及长滑移中反复再挂接的可行性。其二维轮廓、专用方向悬架、阵列载荷转移和动态参数不直接迁移到本项目 A3；阵列重分配留给 B。[L03]
- `[L05] 文献05`：提供“局部赫兹强度首次越限不等于整体脱附”的关键负证据，支持局部凸体破坏、有效搜索行程和墙面—针体上限竞争。其量纲错误断裂式、特定经验拟合和材料数值均不实现。[L05]
- `[L14] 文献14`：支持烧结黏土砖起裂后继续传力、牵引软化、耗散面积为断裂能以及达到临界张开后完全分离的状态结构。厘米级 Mode-I 三点弯曲参数、Petersson 曲线和混凝土系数不能直接下推到微米级混合模态接触。[L14]
- `[L15] 文献15`：支持烧结砖方向性、压力敏感多轴首次失效以及“宏观应力—有限 RVE 平均应力—材料判据”的尺度桥接思路。特定 $880\ ^\circ\mathrm C$ 砖参数和 Eq. (5.2) 的 RVE 平均应力不能直接用于点合力；该文不提供峰后软化和损伤历史。[L15]

四者在 A3 中互补：`[L15]` 约束首次失效域，`[L14]` 约束峰后耗能/完全分离，`[L05]` 约束局部破坏结构和负证据，`[L03]` 约束释放后的搜索/再挂接状态。

### 37.2 外部原始来源

访问日期均为 `2026-07-16`。外部来源只支持通用数值/本构结构，不提供目标红砖、混凝土或针体的已批准数值。

| 标识 | 来源与实际用途 | 适用边界 | 直接网址 |
|---|---|---|---|
| `[E-CRACKBAND]` | Bažant 与 Oh 的 crack-band 理论原始论文；支持用物理特征宽度/单元带宽把软化功与断裂能关联，避免网格加密导致耗散任意变化。 | 原文针对连续体有限元中的分布裂纹带；本项目只迁移能量正则化原则，不把其混凝土参数或裂纹带几何直接用于针尖损伤核。 | https://www.civil.northwestern.edu/people/bazant/PDFs/Papers/157.pdf |
| `[E-COHESIVE]` | NASA 技术报告中的混合模态界面退化模型；支持单一不可逆损伤变量、卸载不愈合、模式相关断裂能和牵引—分离状态结构。 | 原对象为复合材料分层界面；本项目只迁移数学结构和验证要求，不迁移界面强度、断裂能、模式指数或网格参数。 | https://ntrs.nasa.gov/api/citations/20020053651/downloads/20020053651.pdf |

### 37.3 GPT 通用知识

`[GPT]` 实际使用：微分几何接触图表、球面接触点客观速度、面—边—顶点配置空间特征、摩擦/损伤互补、能量正则化、圆截面组合应力、非光滑事件括区和事务式状态更新。适用边界是准静态、有限维状态和首版轻量损伤；任何材料参数、核尺度、搜索控制路径和容差仍需试验/实现标定。

### 37.4 参数状态表

| 参数/模型选择 | 状态 | A3 处理 |
|---|---|---|
| 总行程、速度、$P_z$、针尖半径、针径、弹簧范围/限位 | 工程事实 | 原样使用，不在 A3 修改。 |
| 摩擦系数、局部接触柔顺 | 未决/A2 | 原样由 A2 参数接口传入。 |
| 面片面积 $A_k$、控制深度 $\ell_k$、核半径 $r_{D,k}$ | 未决 | 物理参数；通过局部试验和网格/核收敛联合确定。 |
| 材料方向和映射 $\mathbf Q_m,\mathbb H_m$ | 未决 | 红砖保留方向性；混凝土/砂纸按适配器显式选择。 |
| $c,\phi,f_t$、压缩帽和力矩容量 | 未决 | 只作为候选首次失效域参数，不复制文献 15 数值。 |
| $G_I,G_S,G_C,\eta_G$、软化形状、$\rho$ | 未决 | 目标材料/尺度标定；宏观 Mode-I 只作先验和状态证据。 |
| 损伤模式标签权重 | 本轮推导接口 | 不作为独立硬阈值；由利用率/模式混合派生并验证。 |
| 高碳钢 $\sigma_y,\sigma_u$ 和牌号 | 未决 | 采购/材质证明、标准或成品针试验输入。 |
| 搜索控制器法向路径 | 未决 | `NESTED_Z_SEARCH` 或 `PRESCRIBED_XZ_PATH` 显式配置并与设备行程对应。 |
| 事件步长、容差、SOC/损伤投影尺度 | 未决数值参数 | 通过解析基准、步长/网格/尺度扫描确定。 |
| 砂纸材料损伤 | 模型选择未决 | 可用 `no_damage`、经验结果量容量或待标定分支；不得套砖材 MC+软化参数。 |

### 37.5 材料尺度桥接和损伤参数标定

建议的最小辨识链为：

1. **几何尺度**：用目标针尖、目标表面三维测量及低损伤压入/拖曳确定有效接触范围；比较不同 $A_k,\ell_k,r_D$ 对局部平均量和总响应的敏感性；
2. **首次失效域**：在相同材料方向和环境下进行微压入、局部剪切/划擦或可控混合加载；同步测量力、位移和损伤起始位置，辨识压力敏感/方向性参数；
3. **峰后能量**：从局部力—相对位移曲线扣除仪器、梁、弹簧和纯摩擦功，辨识 $G_c$、残余比例和软化形状；宏观 Mode-I 结果只能作为宽先验和一致性检查；
4. **空间记忆**：在同一位置重复通过，检验再加载容量折减和无愈合；改变网格、路径步长和查询顺序验证同一损伤键；
5. **留出验证**：用未参与拟合的针尖半径、法向推力、加载方向或表面区域测试事件顺序、峰值和耗散。

若只能用总拖拽峰值拟合多个参数，则 $A_k,\ell_k,G_c,c,\phi$ 通常不可辨识，必须减少参数、增加独立实验或保留多个候选模型，不能报告唯一解。

### 37.6 针体强度标定

强度输入优先级：实际采购牌号和热处理/材质证明 → 对应正式标准/制造商数据 → 成品针静态试验。成品针至少做：

- 多方向弯曲，校核根部边界与双轴弯矩；
- 必要的轴向和扭转载荷，分离 $N,T,V$ 贡献；
- 逐步加载至永久变形起点和破坏，记录制造缺口/根部应力集中；
- 多件重复，保存批次离散。

若成品针根部几何导致显著应力集中，应由实测/CAD 的应力集中系数或局部有限元修正式 (A3-NEEDLE-N)，并把模型版本显式写入适配器。不得用名义圆杆强度掩盖安装出口缺口。

## 38. 验证、完成判据、风险和正式交接

### 38.1 解析与物理极限

| 检查 | 预期结论 | 当前状态 |
|---|---|---|
| 材料和针体容量趋无穷 | A3 退化为 A1+A2 的粘着/滑移/几何释放问题。 | **通过（方程极限）** |
| 损伤关闭/未启动 | $D,\delta_d,\mathcal D_m$ 不变；新试验初始化为零。 | **通过（状态构造）** |
| 平面单支持、恒法向、无几何变化 | 提交滑移满足 A2 Coulomb 最大耗散，$\Delta D_f\ge0$。 | **通过（解析结构），待代码回归** |
| $\mu=0$ | $\boldsymbol\lambda_t=0$；斜面法向投影、材料容量和释放仍按一般平衡判断。 | **通过（继承 A2）** |
| 光滑解析凸面 | 式 (A3-GEO) 给出连续接触迁移；法向变化和顶部释放可与解析圆/球面比较。 | **部分通过：基准已定义，待实现** |
| 无损支持切换 | 不凭空增加储能或耗散；多支持非唯一被报告。 | **部分通过：规则已定义，待实现** |
| 软化能量 | 式 (A3-ENERGY) 量纲闭合；保持物理核/控制体尺度时加密不应使总耗散无界变化。 | **通过（构造），待数值收敛** |
| 针体/墙面各自趋无限强 | 分别只剩另一容量分支及摩擦/几何限制。 | **通过（约束分离）** |
| 脱离后路径连续 | $x_{\rm total}$、时间和 DamageStore 不重置。 | **通过（状态合同）** |
| 力—位移—功单位 | N、mm、N·mm、N/mm$^2$、N/mm、无量纲损伤分离。 | **通过（量纲检查）** |

### 38.2 数值、状态和事件验证计划

| 检查 | 接受判据 | 当前状态 |
|---|---|---|
| `CRITICAL_SLIP` 到已提交滑移 | A2 残量、SOC、最大耗散和 A3 迁移同时满足，事件前后力/状态收敛。 | **部分通过：闭合方程已给，待实现** |
| 高度场—同源网格迁移 | 随加密，接触轨迹、支持切换和释放位置收敛。 | **待实现** |
| 面—边—顶点/多支持 | 不平均法向伪造唯一解；左右分支和非唯一报告可复现。 | **待构造回归案例** |
| 并发事件 | 摩擦、材料、针体、释放、限位和体碰撞在减步后得到稳定事件集合和分支。 | **待实现** |
| 损伤键复现 | 网格编号、并行顺序和查询顺序改变后，同一材料区域读取同一历史。 | **待实现** |
| 无愈合/非负耗散 | 卸载、脱离、再接触后 $D$ 不减，$\Delta D_m\ge0$。 | **通过（约束），待回归** |
| 失败分类 | 构造案例能区分物理无解、适配器缺失、几何不足和数值未收敛。 | **待实现** |
| 步长/容差收敛 | 滑移起点、材料起始、释放、再挂接、峰值和耗散进入稳定平台。 | **待实现** |
| 多峰轨迹 | 构造多凸起路径出现至少两个完整循环，且所有峰记录闭合。 | **待实现** |
| 针体应力接口 | 梁根解析载荷、纯弯/扭/轴和 bending off/on 给出一致截面结果量与裕度。 | **部分通过：公式已定义，待代码** |

本轮没有运行求解器、材料试验或数值收敛测试；“通过”仅指解析关系或状态构造闭合，不能解释为已完成实验验证。

### 38.3 A3 十类理论与算法结果落点

| 必须结果 | 章节 | 覆盖 |
|---|---|---|
| 1. 粘着到真实滑移提交 | 第 28 节 | 完整 |
| 2. 三维接触点/支持特征迁移 | 第 29 节 | 完整 |
| 3. 接触释放和几何脱离 | 第 30 节 | 完整 |
| 4. 局部材料承载域与尺度桥接 | 第 31 节 | 完整，参数待标定 |
| 5. 针体强度上限 | 第 33 节 | 完整，材料数据待输入 |
| 6. 损伤、软化、耗能和空间记忆 | 第 32 节 | 完整，参数待标定 |
| 7. 完整单刺状态机和再挂接 | 第 27、30 节 | 完整 |
| 8. 同时事件、优先级和自适应步长 | 第 35 节 | 完整 |
| 9. 未知量、残量、活动集、回退和伪代码 | 第 34 节 | 完整 |
| 10. $100\ \mathrm{mm}$ 多峰输出和 A→B 接口 | 第 36 节 | 完整 |

### 38.4 A3 完成判据逐项核对

| 判据 | 结论 |
|---|---|
| 摩擦边界后区分重分配、滑移、材料/针体上限和释放 | **满足规范层要求**：第 28、31、33、35 节。 |
| 三维球尖迁移和非光滑支持切换闭合 | **满足规范层要求**：第 29 节；实现验证待完成。 |
| 材料域含尺度桥接、压力/方向敏感起始和峰后耗能 | **满足**：第 31–32 节；目标参数未硬编码。 |
| 压碎、剪断、划伤、脆性脱落统一 | **满足**：共享利用率、软化坐标和模式权重，而非互斥硬阈值。 |
| 针体与墙面容量显式竞争 | **满足**：第 33.4、35.4 节。 |
| 损伤不可逆、空间可查询且不改地形 | **满足**：第 32.6–32.9 节。 |
| 脱离后继续搜索、再预载和再承载 | **满足**：第 30 节。 |
| 状态、事件、残量和算法可转化为程序 | **满足**：第 27、34、35 节。 |
| 同一轨迹可形成多峰且不重置 | **满足数据/状态合同**：第 36 节；实际多峰回归待运行。 |
| A1/A2 未被静默改写，B/C 未越权 | **满足**。 |
| 未固定参数全部参数化/待标定 | **满足**。 |

结论：**A3 的机理、状态、算法和交接规范达到本轮完成标准；这不代表求解器代码、目标材料参数、数值收敛或实验验证已经完成。**

### 38.5 关键风险和未决问题

1. 面片面积、控制深度和损伤核尺度会显著影响应力代理与耗散，必须用独立局部试验和收敛共同约束；
2. 红砖宏观 Mode-I 数据不能关闭局部压碎/剪切混合模态参数缺口；
3. 文献 15 的 RVE 平均判据在球尖高梯度区可能失效，需要有限控制体敏感性和局部实验；
4. 摩擦功与划伤/剪切损伤功可能在试验反演中相关，必须分离纯摩擦基准；
5. 材料软化、支持切换和接触释放并发时可能存在多个物理可行分支；
6. 准静态搜索不能再现动态跳跃和冲击，需把与实验的系统性漏接作为模型风险；
7. 针根实际几何、热处理和成品缺陷可能使名义圆截面上界不保守；
8. 砂纸是否需要损伤模型以及其经验容量形式尚未确定；
9. 搜索控制器的法向路径必须与真实执行器和行程边界对应；
10. 所有事件容差、最小步长和分支 Jacobian 门槛仍需代码收敛研究。

每项未决问题均保留参数 ID、证据状态和关闭条件，不因缺数据而从接口消失。

### 38.6 对大模块 A 集成的交接

A1、A2、A3 现已形成完整低层合同，但仍需独立的大模块 A 集成工作：

- 把 A1/A2/A3 接口实现成同一事务式单刺对象；
- 建立解析几何、摩擦、梁/弹簧、材料和多峰端到端回归套件；
- 确认所有符号、参考点、状态枚举、单位和事件编码在代码数据模型中唯一；
- 用目标材料/针体参数完成标定后，冻结可供 B 调用的版本化参数包；
- 对完整 $100\ \mathrm{mm}$ 随机表面轨迹执行步长、网格、损伤核和随机样本收敛。

本轮不输出 `A_INTEGRATED_MODEL.md` 或 `A_TO_B_CONTRACT.md`；第 36.4 节只定义 A3 必须暴露的单刺接口。

### 38.7 对 B 层的正式物理边界

B 层可直接调用的量包括：任意针基座位姿/增量下的单刺试探 wrench、分支切线/割线、活动支持、梁/弹簧状态、材料损伤查询与试探更新、针体裕度、释放/再挂接事件、事件分数和 A1/A2 回调。B 层必须原样继承这些定义。

B 层可以新增：共同刚性背板运动、多个单刺残量装配、阵列法向平衡、活动针集合、载荷共享、失效重分配和共享损伤提交顺序。B 层不得重新定义任何单刺接触、摩擦、滑移、材料、损伤、针强度、释放或再挂接机理。

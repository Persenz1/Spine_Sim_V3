# 钩爪式爬壁机器人爪刺啮合求解器：工程固定上下文

> 版本：`1.0.0`
> 状态：`current`
> 本文件由 `engineering_fixed_context/internal/facts/*.yaml` 单向生成，是供人工审阅和网页端上传的完整工程事实视图。
> 它只定义工程事实、边界、工况、接口要求和未决参数；具体机理实现属于 `RESULT` 与 `MODULE_CONTEXT`。

## 阅读与修改规则

供机理推导、求解器实现、参数扫描和实验对比共同依赖的工程事实库。 本库只记录工程事实、边界、工况、接口要求和未决参数，不记录具体机理实现。

- “已固定”表示当前正式基线，后续理论或代码不得静默改写；允许经显式说明、差异审查和人工确认后升级版本。
- “范围/集合已固定”不代表其内部离散点或标定值已经全部确定。
- “接口能力已固定”只约束程序必须提供的能力，不预先指定机理算法。
- “尚未固定”表示必须保留为参数或待标定项，禁止擅自硬编码唯一值。
- 修改结构化事实后运行 `conda run --no-capture-output -n codex-py312 python -X utf8 engineering_fixed_context/internal/build_context.py --write` 重新生成本文件。

## 状态图例

| 状态 | 含义 |
|---|---|
| `fixed` | 已固定 |
| `fixed_set` | 扫描集合已固定 |
| `fixed_range` | 范围已固定 |
| `model_switch` | 模型开关已固定 |
| `interface_required` | 接口能力已固定 |
| `unresolved` | 尚未固定 |
| `excluded` | 首版明确排除 |

## 领域导航

- [1. 工程目标、验证边界与仿真层级](#domain-1)
- [2. 坐标系、方向约定与刚体运动学](#domain-2)
- [3. 十字对爪固定几何](#domain-3)
- [4. 单根针刺几何、材料和结构开关](#domain-4)
- [5. 阵列拓扑、设计空间与安装柔顺](#domain-5)
- [6. 表面类别、表示和统一查询能力](#domain-6)
- [7. 法向预载、直线拖拽、同步搜索与偏心承载](#domain-7)
- [8. 损伤记忆边界与首版范围排除](#domain-8)
- [9. 尚未固定且禁止擅自硬编码的登记项](#domain-9)

<a id="domain-1"></a>

## 1. 工程目标、验证边界与仿真层级

本领域定义求解器为什么存在、怎样判断阶段成果有效，以及各物理层级之间不可破坏的依赖关系。

### PROJECT.GOALS.CORE — 核心工程目标

- 状态：已固定
- 适用范围：全局、求解器全层级、实验对比

建立自研三维准静态求解器，服务爪单元设计筛选、参数研究、实验趋势对比和十字主动对爪扩展。

必须满足：

- 比较并筛选爪单元设计。
- 研究针刺安装角、角度梯度、阵列尺寸、阵列方向、针距、针径和针尖半径的影响。
- 比较刚性阵列与独立轴向弹簧柔顺阵列。
- 选择独立弹簧刚度。
- 预测不同设计的相对抓附能力。
- 与直线模组拖拽实验比较趋势和方案排序。
- 将经验证的爪单元模型扩展到十字主动啮合对爪，预测偏心面内载荷下的整体承载能力。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 1.1 节；来源类型：engineering_decision。

### PROJECT.GOALS.VALIDATION — 当前验证目标

- 状态：已固定
- 适用范围：全局、求解器全层级、实验对比

当前不要求求解器与实验在绝对数值上完全等价，也不以拟合单次偶然峰值为首要目标。

必须满足：

- 参数变化方向一致。
- 不同设计方案的排序大体一致。
- 能解释刚性阵列与柔顺阵列、不同阵列方向和不同安装角产生差异的原因。

约束：

- 不把单次偶然峰值拟合作为首要目标。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 1.2 节；来源类型：engineering_decision。

### PROJECT.OUTPUTS.NO_BINARY_SUCCESS — 暂不定义二元抓附成功

- 状态：已固定
- 适用范围：求解器全层级、实验对比

当前不固定“抓附成功/失败”的实验阈值，也不固定综合评分；求解器必须保存可供后续定义判据的原始连续量和事件记录。

必须满足：

- 输出力—位移曲线。
- 输出力—时间曲线。
- 输出法向位置或法向位移。
- 输出各针接触状态。
- 输出各针载荷。
- 记录接触、滑移、脱离、局部失效、再挂接和限位事件。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 1.3 节；来源类型：engineering_decision。

### PROJECT.ARCHITECTURE.PHYSICAL_LEVELS — 三个物理层级

- 状态：已固定
- 适用范围：全局、求解器全层级

工程按能够独立形成和验证的物理算子划分为单刺、阵列爪单元和整十字对爪三个层级。

定义：

| 名称 | 含义 |
|---|---|
| 单爪刺层 | 一根针刺与粗糙表面的连续搜索、接触、加载、滑移、失效、脱离和再搜索。 |
| 阵列爪单元层 | 规则多刺阵列在刚性背板共同运动下的部分接触、载荷共享和重分配。 |
| 整十字对爪层 | 四个相同爪单元同步向中心收紧，并在偏心面内载荷下共同承载。 |

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 2 节；来源类型：engineering_decision。

### PROJECT.ARCHITECTURE.DEPENDENCY — 物理算子单向依赖

- 状态：已固定
- 适用范围：全局、求解器全层级

高层只能复用低层物理入口，不得重复实现或暗中改写低层机理。

工程表达：

- 推荐实现依赖关系

$$
\text{表面查询}
\rightarrow
\text{单刺算子}
\rightarrow
\text{阵列单元算子}
\rightarrow
\text{十字对爪算子}
$$

约束：

- 高层不得重复实现低层机理。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 2 节；来源类型：engineering_decision。

<a id="domain-2"></a>

## 2. 坐标系、方向约定与刚体运动学

本领域固定全局与局部坐标、针轴方向、允许自由度和整爪小角度摇摆边界。

### COORDINATE.GLOBAL.FRAME — 全局坐标系

- 状态：已固定
- 适用范围：全局、单刺层、阵列爪单元层、十字对爪层

墙面名义平面为全局 X-Y 平面，正 Z 从墙面指向爪单元背板。

定义：

| 名称 | 含义 |
|---|---|
| $\mathbf E_X,\mathbf E_Y$ | 墙面名义平面内的全局基向量。 |
| $\mathbf E_Z$ | 墙面法向，从墙面指向爪单元背板。 |
| $C=(0,0,z_C)$ | 四条单元中线延长后的公共交点。 |

工程表达：

$$
\mathcal F_G=\{C,\mathbf E_X,\mathbf E_Y,\mathbf E_Z\}
$$

约束：

- 十字对爪四条单元中线分别与全局 $\pm X,\pm Y$ 方向重合。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 3.1 节；来源类型：engineering_decision。

### COORDINATE.UNIT.FRAME — 单爪单元局部坐标系

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层

每个爪单元使用局部 x/y 与全局 Z 组成的右手坐标系；局部正 x 同时是从头部到根部的方向以及主动搜索和拖拽方向。

定义：

| 名称 | 含义 |
|---|---|
| 局部 $+x_i$ | 从单元头部指向根部，也是主动搜索和拖拽方向；头部位于局部负 x，根部位于局部正 x。 |
| 局部 $y_i$ | 背板平面内、垂直于单元中线的横向。 |
| 局部 $z$ | 与全局 Z 共用。 |

工程表达：

$$
\mathcal F_i=\{O_i,\mathbf e_{x_i},\mathbf e_{y_i},\mathbf E_Z\}
$$

- 右手系横向基向量

$$
\mathbf e_{y_i}=\mathbf E_Z\times\mathbf e_{x_i}
$$

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 3.2 节；来源类型：engineering_decision。

### COORDINATE.NEEDLE.AXIS — 针轴方向和安装角

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层

安装角是针轴与安装背板平面的夹角；从安装座出口指向针尖球心的轴向量具有局部正 x 分量和负 Z 分量，并为未来偏航角保留接口。

定义：

| 名称 | 含义 |
|---|---|
| $\alpha$ | 针轴与安装背板平面的夹角。 |
| $\beta$ | 针轴在背板平面内向正或负 y 偏转的偏航角。 |

工程表达：

- 预留偏航角的通用针轴

$$
\boxed{
\mathbf a=
\cos\alpha\cos\beta\,\mathbf e_x+
\cos\alpha\sin\beta\,\mathbf e_y-
\sin\alpha\,\mathbf E_Z
}
$$

- 当前正式工况

$$
\beta=0,
\qquad
\mathbf a=
\cos\alpha\,\mathbf e_x-
\sin\alpha\,\mathbf E_Z
$$

约束：

- 首版不扫描偏航角，但底层数据和坐标接口必须保留 $\beta$。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 3.3 节；来源类型：engineering_decision。

### KINEMATICS.UNIT.RIGID_BOARD — 单刺和阵列单元背板运动

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层

安装背板视为绝对刚性，只允许沿局部 x 和全局 Z 平移。

定义：

| 名称 | 含义 |
|---|---|
| $u_{x_i}$ | 沿局部 $x_i$ 的搜索和拖拽位移。 |
| $u_{z_i}$ | 法向接近、压紧和卸载位移。 |

工程表达：

$$
\mathbf q_i=
\begin{bmatrix}
u_{x_i}\\
u_{z_i}
\end{bmatrix}
$$

约束：

- 背板不发生俯仰、滚转、偏航、翘曲或局部弯曲。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 4.1 节；来源类型：engineering_decision。

### KINEMATICS.CROSS.RIGID_REFERENCE — 整十字对爪刚体关系与摇摆开关

- 状态：模型开关已固定
- 适用范围：十字对爪层
- 取值：
  - rocking：off, on
  - optional_rotations：theta_X, theta_Y

四个单元相对无质量、无限刚性的虚拟参考体保持固定安装关系；偏心承载阶段可选择是否允许整爪绕全局 X、Y 小角度摇摆。

约束：

- 不建模实际框架、导轨、驱动杆或连接件的柔性。
- 外部框架、导轨和连接件不得替爪刺接触承担外部载荷。
- 首版不考虑绕 Z 轴整体偏航、大角度翻转、动态倾覆、框架有限元或单个爪单元相对整爪独立转动。
- 失去准静态稳定平衡后即可终止，不模拟脱落后的大角度运动。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 4.2 节；来源类型：engineering_decision。

<a id="domain-3"></a>

## 3. 十字对爪固定几何

本领域固定四个爪单元相对于参考中心的安装关系和中央空区尺寸。

### GEOMETRY.CROSS.LAYOUT — 四单元十字布局

- 状态：已固定
- 适用范围：十字对爪层
- 取值：
  - opposite_root_midpoint_distance：80 mm
  - central_clear_square_side：80 mm

四个单元中线延长后交于 C；两个相对单元的根部背板中点距离为 80 mm，四个根部背板中点围成 80 mm × 80 mm 的中央正方形空区。

工程表达：

- 单元参考点通式

$$
\mathbf O_i=\mathbf C-40\,\mathbf e_{x_i}\ \text{mm}
$$

- 一组正式编号

$$
\begin{aligned}
\mathbf e_{x_1}&=+\mathbf E_X, & \mathbf O_1&=(-40,0,z_C)\ \text{mm},\\
\mathbf e_{x_2}&=-\mathbf E_X, & \mathbf O_2&=(+40,0,z_C)\ \text{mm},\\
\mathbf e_{x_3}&=+\mathbf E_Y, & \mathbf O_3&=(0,-40,z_C)\ \text{mm},\\
\mathbf e_{x_4}&=-\mathbf E_Y, & \mathbf O_4&=(0,+40,z_C)\ \text{mm}.
\end{aligned}
$$

说明：

- 编号本身可以改变，但几何和方向关系不得改变。
- 本编号中各单元局部正 x 指向十字中心。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 5 节；来源类型：engineering_decision。

<a id="domain-4"></a>

## 4. 单根针刺几何、材料和结构开关

本领域定义针尖、针杆、露出长度、针径、材料边界、弯曲开关和安装座内埋段的工程处理。

### NEEDLE.TIP.GEOMETRY — 球形针尖局部曲率

- 状态：扫描集合已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层
- 符号：$R_t$
- 取值：50, 100 μm

针尖局部退化为球面接触头；球形针尖只表示最尖端局部曲率，不表示针杆末端连接一个完整独立球体。

必须满足：

- 实际几何由圆柱针杆、锥形过渡段和局部球形针尖依次组成。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.1 节；来源类型：engineering_decision。

### NEEDLE.CONTACT.COLLISION_BOUNDARY — 承载接触和禁止碰撞边界

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层、求解器全层级

只有球形针尖参与接触承载；其他针体和安装结构只参与非穿透与可装配检查。

约束：

- 锥形过渡段、圆柱针杆和安装座不参与承载，只参与非穿透与可装配检查。
- 非承载部位与表面发生禁止碰撞时，该构型不能继续按纯针尖接触处理。
- 首版不建立锥段或针杆的分布接触承载模型。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.2 节；来源类型：engineering_decision。

### NEEDLE.LENGTH.EXPOSED — 固定角阵列针尖球心露出长度

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层
- 符号：$L_e$
- 取值：4 mm

安装座出口到针尖球心的轴向距离为 4 mm；固定安装角阵列中的所有针默认使用该值。

说明：

- 线性角度梯度阵列采用单独的露出长度补偿规则。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.3 节；来源类型：engineering_decision。

### NEEDLE.DIAMETER.SET — 针径扫描集合

- 状态：扫描集合已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层
- 符号：$d$
- 取值：0.6, 0.8 mm

针杆直径在两个固定候选值之间扫描。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.4 节；来源类型：engineering_decision。

### NEEDLE.MATERIAL.BASE — 针体材料类别

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层
- 取值：高碳钢

针体材料类别固定为高碳钢，但当前不固定具体牌号和材料参数。

约束：

- 具体牌号、弹性模量、屈服强度和断裂强度属于后续材料参数表，不得在理论阶段擅自指定。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.5 节；来源类型：engineering_decision。

### NEEDLE.BENDING.SWITCH — 露出针体弯曲开关

- 状态：模型开关已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层、求解器全层级
- 取值：
  - needle_bending：off, on

露出针体是否发生弹性弯曲由统一模型开关控制。

定义：

| 名称 | 含义 |
|---|---|
| off | 露出针体视为刚体。 |
| on | 根据针径、露出长度和后续给定材料参数建立梁柔顺。 |

约束：

- 针体弯曲与独立弹簧压缩必须分开建模，避免重复计入柔顺。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.6 节；来源类型：engineering_decision。

### NEEDLE.EMBEDMENT.MODEL_BOUNDARY — 安装座内埋段工程处理

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、求解器全层级
- 取值：
  - rigid_array_nominal_embedment：8 mm
  - compliant_array_nominal_embedment：4 mm

实物内埋深只作为结构背景记录；求解器不显式模拟内埋针体和安装座细节。

约束：

- 安装座内部机构统一退化为理想刚性约束或理想轴向移动副。

说明：

- 实物刚性阵列约有 8 mm 预埋，柔顺阵列约有 4 mm 预埋。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 6.7 节；来源类型：engineering_decision。

<a id="domain-5"></a>

## 5. 阵列拓扑、设计空间与安装柔顺

本领域固定规则阵列的索引、尺寸、针距、角度模式、露出长度补偿，以及刚性和独立轴向弹簧两种安装模式。

### ARRAY.TOPOLOGY.RECTANGULAR — 规则矩形田字格阵列

- 状态：扫描集合已固定
- 适用范围：阵列爪单元层、十字对爪层
- 符号：$n_x\times n_y$
- 取值：
  - n_x：2, 3, 4, 5, 6
  - n_y：2, 3, 4, 5, 6

阵列采用规则矩形田字格排布；局部 x 和 y 方向的针数分别独立扫描。

定义：

| 名称 | 含义 |
|---|---|
| $n_x$ | 沿单元局部 x 方向的针数。 |
| $n_y$ | 沿单元局部 y 方向的针数。 |

约束：

- 不采用交错排列。
- 针朝向在同一模式内按规定保持一致。
- x、y 两方向针距相同。
- 必须保留 $2\times5$ 与 $5\times2$ 等转置阵列的独立结果，不得视为等价。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 7.1 节；来源类型：engineering_decision。

### ARRAY.SPACING.SET — 等中心距扫描集合

- 状态：扫描集合已固定
- 适用范围：阵列爪单元层、十字对爪层
- 符号：$s_x=s_y=s$
- 取值：4, 5, 6 mm

阵列局部 x、y 两方向采用相同的针尖中心距。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 7.2 节；来源类型：engineering_decision。

### ARRAY.ANGLE.FIXED_SET — 固定安装角模式

- 状态：扫描集合已固定
- 适用范围：阵列爪单元层、十字对爪层
- 符号：$\alpha$
- 取值：50, 60, 70, 80 °

固定角模式中同一阵列的所有针采用相同安装角。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 7.3 节；来源类型：engineering_decision。

### ARRAY.ANGLE.LINEAR_GRADIENTS — 线性角度梯度模式

- 状态：扫描集合已固定
- 适用范围：阵列爪单元层、十字对爪层
- 取值：
  - gradient_1_root_to_head：80, 50 °
  - gradient_2_root_to_head：80, 60 °

安装角只沿局部 x 方向变化；同一 x 坐标排内的所有针共享相同安装角。

约束：

- 对任意 $n_x$，各排角度按根部到头部线性插值。
- 不要求每排角度必须为 10° 整数。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 7.4 节；来源类型：engineering_decision。

### ARRAY.ANGLE.GRADIENT_LENGTH_COMPENSATION — 梯度阵列露出长度补偿

- 状态：已固定
- 适用范围：阵列爪单元层、十字对爪层

根部排球心露出长度固定为 4 mm、安装角为 80°；其他排调整轴向露出长度，使未加载针尖球心处于同一全局 z 高度。

工程表达：

- 球心共面条件

$$
L_j\sin\alpha_j=4\sin80^\circ
$$

- 第 j 排露出长度

$$
\boxed{
L_j=\frac{4\sin80^\circ}{\sin\alpha_j}\ \text{mm}
}
$$

约束：

- 开启针体弯曲时必须使用各排实际 $L_j$ 计算柔顺，不得继续使用统一 4 mm。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 7.5 节；来源类型：engineering_decision。

### ARRAY.NEEDLE.DATA_EXTENSIBILITY — 针级任意分布扩展接口

- 状态：接口能力已固定
- 适用范围：阵列爪单元层、求解器全层级

首版不扫描任意针级分布，但底层数组不能把全阵列同角度、同长度或同材料硬编码为唯一结构。

必须满足：

- 允许每根针独立安装角。
- 允许每根针独立偏航角。
- 允许每根针独立露出长度。
- 允许每根针独立材料或刚度参数。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 7.6 节；来源类型：engineering_decision。

### ARRAY.MOUNT.RIGID_MODE — 刚性阵列安装模式

- 状态：已固定
- 适用范围：阵列爪单元层、十字对爪层

刚性阵列中的所有针在安装座内无相对轴向运动，全部针基座运动由共同刚性背板位移决定。

约束：

- 针体是否弯曲仍由独立的 `needle_bending` 开关控制。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 8.1 节；来源类型：engineering_decision。

### ARRAY.MOUNT.AXIAL_SPRING_MODE — 独立轴向弹簧阵列

- 状态：范围已固定
- 适用范围：阵列爪单元层、十字对爪层
- 取值：
  - stiffness_min：100 N/m
  - stiffness_max：2000 N/m

每根针具有与针轴共线、彼此独立的线性压缩弹簧；刚度范围固定，具体采样点后续确定。

工程表达：

- 弹簧压缩行程

$$
0\le\delta_s\le4\ \text{mm}
$$

约束：

- 弹簧只能压缩，可以回弹到原长，但不能伸长超过原长。
- 弹簧无初始预压，不得承受拉力。
- 不允许针在安装座内转动。
- 忽略导向摩擦，各针弹簧彼此独立。
- 达到 4 mm 压缩行程后切换到刚性硬限位。
- 若维持接触需要 $\delta_s<0$，应解除轴向约束或判定接触脱开，不得允许弹簧拉伸。

说明：

- 具体刚度离散采样点由参数扫描计划确定。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 8.2 节；来源类型：engineering_decision。

<a id="domain-6"></a>

## 6. 表面类别、表示和统一查询能力

本领域固定首版表面类别、主几何表示、完整网格分支及所有表面进入接触求解器时必须共享的接口能力。

### SURFACE.CATEGORIES.FIRST_RELEASE — 首版表面类别

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层、实验对比
- 取值：红砖, 混凝土, 不同目数砂纸

首版研究红砖、混凝土和不同目数砂纸；具体砂纸目数集合尚未固定。

约束：

- 不得擅自硬编码唯一的砂纸目数集合。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 9.1 节；来源类型：engineering_decision。

### SURFACE.INTERFACE.UNIFIED — 统一可扩展表面接口

- 状态：接口能力已固定
- 适用范围：求解器全层级、单刺层、阵列爪单元层、十字对爪层

不同表面可以采用不同参数和随机生成后端，但必须通过同一表面接口进入接触求解器；上层不得按材料类别复制接触逻辑。

必须满足：

- 提供表面高度或三维几何。
- 提供局部法向。
- 提供局部坡度和必要的曲率信息。
- 提供摩擦参数。
- 提供局部材料承载或损伤参数。
- 提供空间查询和邻域查询能力。

约束：

- 求解器上层不得针对红砖、混凝土或砂纸分别编写接触逻辑。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 9.2 节；来源类型：engineering_decision。

### SURFACE.HEIGHT_FIELD.PRIMARY — 主表面表示与区域

- 状态：已固定
- 适用范围：求解器全层级、单刺层、阵列爪单元层、十字对爪层
- 取值：
  - size_x：150 mm
  - size_y：150 mm

正式研究主线采用单值高度场，主仿真区域为 150 mm × 150 mm。

工程表达：

$$
z=h(x,y)
$$

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 9.3 节；来源类型：engineering_decision。

### SURFACE.TRIANGLE_MESH.SECONDARY — 完整三角网格能力分支

- 状态：接口能力已固定
- 适用范围：求解器全层级、单刺层、阵列爪单元层、十字对爪层

保留完整三角网格分支，用于检验高度场无法表达的非单值三维结构；该分支不建立另一套接触机理。

必须满足：

- 能检验倒扣和非单值几何。
- 能进行完整三维碰撞检查。
- 能表达高度场无法表示的局部结构。

约束：

- 三角网格分支与高度场分支共享接触、摩擦、柔顺和失效机理。
- 高度场是正式研究主线，完整网格是次级工程能力验证分支。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 9.4 节；来源类型：engineering_decision。

### SURFACE.PARAMETERS.UNRESOLVED — 尚未固定的表面参数

- 状态：尚未固定
- 适用范围：求解器全层级、实验对比

表面统计、摩擦、强度和采样参数由后续文献、合成试验或真实测量确定，当前不得设为唯一默认值。

登记项：

| 编号 | 项目 | 作用域 | 说明 |
|---|---|---|---|
| SURFACE.PSD | PSD 或其他谱参数 | — | — |
| SURFACE.HEIGHT_DISTRIBUTION | 高度分布 | — | — |
| SURFACE.CORRELATION_LENGTH | 相关长度 | — | — |
| SURFACE.ANISOTROPY | 各向异性 | — | — |
| SURFACE.NON_GAUSSIAN | 非高斯参数 | — | — |
| SURFACE.GRIT_SCALE_DENSITY | 砂粒尺度和密度 | — | — |
| SURFACE.FRICTION | 摩擦系数 | — | — |
| SURFACE.LOCAL_STRENGTH | 局部强度 | — | — |
| SURFACE.RESOLUTION | 网格或采样分辨率 | — | — |
| SURFACE.RANDOM_SEEDS | 随机种子数量 | — | — |

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 9.5 节；来源类型：engineering_decision。

<a id="domain-7"></a>

## 7. 法向预载、直线拖拽、同步搜索与偏心承载

本领域固定执行器推力含义、各层级载荷范围、拖拽速度与行程、十字对爪共同搜索约束，以及偏心面内加载工况。

### LOAD.NORMAL.ACTUATOR_OUTPUT — 恒定法向主动推力的含义

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层、求解器全层级
- 符号：$P_i$

法向预载采用恒定推力执行器输出模式；恒定的是主动推力，不是墙面对单元的实际法向接触合力。

约束：

- 实际法向接触力由接触状态、表面几何、整体平衡、单元法向位置和整爪小角度摇摆共同决定。
- 不得将恒主动推力误写为恒实际接触合力边界。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 10.1 节；来源类型：engineering_decision。

### LOAD.NORMAL.SINGLE_SPINE — 单刺层法向主动预载

- 状态：已固定
- 适用范围：单刺层
- 符号：$P_z$
- 取值：0.5 N

单根针的法向主动预载固定为 0.5 N，单刺层不扫描该参数。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 10.2 节；来源类型：engineering_decision。

### LOAD.NORMAL.ARRAY_UNIT — 阵列单元法向主动预载范围

- 状态：范围已固定
- 适用范围：阵列爪单元层
- 符号：$P_z$
- 取值：
  - min：0.5 N
  - max：2 N

每个阵列单元的法向主动推力范围固定为 0.5–2 N，具体离散扫描点后续确定。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 10.3 节；来源类型：engineering_decision。

### LOAD.NORMAL.CROSS_GRIPPER — 十字对爪各单元法向主动推力

- 状态：范围已固定
- 适用范围：十字对爪层
- 符号：$P_i$
- 取值：
  - per_unit_min：0.5 N
  - per_unit_max：2 N

四个单元分别施加法向主动推力，每个单元的范围均为 0.5–2 N。

约束：

- 不得将该范围误写为整爪总推力 0.5–2 N。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 10.4 节；来源类型：engineering_decision。

### LOAD.NORMAL.INFEASIBLE_TERMINATION — 法向预载不可行终止

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层、求解器全层级

法向恒推力求解不得无限向墙面推进；到达几何或结构边界前仍不能建立目标推力时，必须标记预载不可行。

约束：

- 非承载针体或安装座发生禁止碰撞时终止推进。
- 柔顺针达到轴向硬限位且仍不可平衡时终止推进。
- 达到几何允许的最近位置时终止推进。
- 接触状态不存在可行平衡时终止推进。

说明：

- 具体安全间隙和数值容差由实现阶段确定。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 10.5 节；来源类型：engineering_decision。

### LOAD.DRAG.SPEED — 直线拖拽物理速度

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、实验对比
- 符号：$v_x$
- 取值：1 mm/s

单刺和阵列单元沿局部正 x 方向以 1 mm/s 的物理速度拖拽。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 11.1 节；来源类型：engineering_decision。

### LOAD.DRAG.QUASI_STATIC — 直线拖拽准静态边界

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层、求解器全层级

拖拽求解忽略惯性和冲击动力学；速度主要用于将位移映射为时间。

工程表达：

- 位移到时间的换算

$$
t=\frac{x}{1\ \text{mm/s}}
$$

约束：

- 若无速率相关材料模型，平衡方程不显式依赖 $v_x$。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 11.2 节；来源类型：engineering_decision。

### NUMERICS.DRAG.VARIABLE_STEP — 可变位移步长和事件定位

- 状态：接口能力已固定
- 适用范围：单刺层、阵列爪单元层、求解器全层级
- 符号：$\Delta x$

物理拖拽速度保持不变，数值求解使用可变位移步长，并在非光滑事件附近减步和定位事件。

必须满足：

- 接触建立、滑移、局部失效、脱离、再挂接和硬限位附近允许减小步长。
- 上述事件允许进行事件定位。

约束：

- 不得通过改变实际拖拽速度代替可变数值步长。
- 初始步长、最小步长和事件容差尚未固定。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 11.3 节；来源类型：engineering_decision。

### LOAD.DRAG.TRAVEL — 单刺和阵列直线拖拽行程

- 状态：已固定
- 适用范围：单刺层、阵列爪单元层
- 取值：100 mm

单刺和阵列单元直线拖拽层的当前最大行程统一为 100 mm；全过程连续推进，不在每次脱离后重置。

必须满足：

- 行程内允许连续经历搜索、接触、加载、滑移或局部失效、脱离和继续搜索。

约束：

- 每次脱离后不得重置到初始位置。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 11.4 节；来源类型：engineering_decision。

### LOAD.CROSS.SEARCH_SYNCHRONIZATION — 十字对爪共同搜索坐标

- 状态：已固定
- 适用范围：十字对爪层
- 符号：$s$

四个单元由同一驱动器同步向中心收紧，只有一个共同径向搜索坐标；地形和接触状态可以不同，但单元不得独立采用不同搜索位移。

工程表达：

$$
u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s
$$

约束：

- 搜索距离只有上限，不要求每次达到上限。
- 若上限前已形成足够好的预紧或潜在承载状态，应停止收紧、保持共同位置、锁定径向搜索位移并进入偏心承载阶段。
- “足够好”的停止准则必须由单元仿真和单元实验反推，当前不预设数值。
- 整爪最大搜索距离应取单元层中能够基本发挥最大抓附能力的最小搜索距离。
- 不得直接沿用单元层 100 mm 作为整爪必然搜索距离。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 12 节；来源类型：engineering_decision。

### LOAD.CROSS.ECCENTRIC_POINT — 偏心外载加载点

- 状态：已固定
- 适用范围：十字对爪层、实验对比

外载作用点位于十字参考中心沿正 Z 方向 50 mm 处。

工程表达：

$$
\mathbf r_P=
\begin{bmatrix}
0\\0\\50
\end{bmatrix}\ \text{mm}
$$

$$
P=(0,0,z_C+50\ \text{mm})
$$

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 13.1 节；来源类型：engineering_decision。

### LOAD.CROSS.DIRECTIONS — 偏心面内加载方向

- 状态：扫描集合已固定
- 适用范围：十字对爪层、实验对比

正式比较外载与一组爪单元轴线对齐，以及外载位于两组爪单元轴线之间的两个墙面内方向。

工程表达：

- 工况 A：全局正 X

$$
\hat{\mathbf d}_A=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}
$$

- 工况 B：从正 X 向正 Y 偏 45°

$$
\hat{\mathbf d}_B=
\frac{1}{\sqrt2}
\begin{bmatrix}
1\\1\\0
\end{bmatrix}
$$

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 13.2 节；来源类型：engineering_decision。

### LOAD.CROSS.ECCENTRIC_MOMENT — 偏心外力矩定义

- 状态：已固定
- 适用范围：十字对爪层、求解器全层级

加载点偏置使墙面内外力相对于 C 产生主要绕全局 X/Y 轴的倾覆力矩，而不是绕 Z 的纯扭转。

工程表达：

$$
\mathbf F_{\mathrm{ext}}=F\hat{\mathbf d}
$$

$$
\mathbf M_{\mathrm{ext}}=
\mathbf r_P\times\mathbf F_{\mathrm{ext}}
$$

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 13.3 节；来源类型：engineering_decision。

### LOAD.CROSS.DISPLACEMENT_CONTROL — 偏心承载加载方式和输出

- 状态：已固定
- 适用范围：十字对爪层、求解器全层级、实验对比

正式求解采用准静态位移推进获取整体反力曲线；失稳后不继续强制纯力控制。

必须满足：

- 输出整体反力—加载点位移曲线。
- 输出峰值可承受外力。
- 输出四个单元的载荷分配。
- 输出一侧压紧与对侧剥离过程。
- 输出单元级和针级渐进失效。
- 输出失去稳定平衡的临界状态。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 13.4 节；来源类型：engineering_decision。

<a id="domain-8"></a>

## 8. 损伤记忆边界与首版范围排除

本领域固定连续试验内部允许保留的轻量损伤记忆，以及首版机理和求解器明确不包含的内容。

### DAMAGE.MEMORY.LIGHTWEIGHT — 连续过程内的轻量损伤记忆

- 状态：接口能力已固定
- 适用范围：单刺层、阵列爪单元层、十字对爪层、求解器全层级

一次连续拖拽或一次整爪承载仿真中允许保留轻量级局部损伤记忆；新的独立试验或随机表面样本从无损状态开始。

必须满足：

- 局部承载点发生材料失效后，不应立即恢复为原始完整强度。
- 可以采用局部损伤变量、强度折减或失效标记。
- 新的独立试验或新的随机表面样本从无损状态开始。

约束：

- 不显式模拟裂纹路径、碎屑、断口重建和地形重网格化。
- 具体损伤演化律由后续机理推导决定，本事实库不预设公式。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 14 节；来源类型：engineering_decision。

### SCOPE.FIRST_RELEASE.EXCLUSIONS — 首版明确不做的内容

- 状态：首版明确排除
- 适用范围：全局、求解器全层级

下列能力不属于首版机理和求解器范围，不得在未显式扩展工程边界前加入正式主线。

必须满足：

- 不做显式裂纹扩展有限元。
- 不做碎屑和颗粒动力学。
- 不做针尖磨损演化。
- 不做针杆或锥段的分布承载接触。
- 不做安装座内部真实结构有限元。
- 不做导轨和框架柔性。
- 不做整机质量和惯性动力学。
- 不做大角度倾覆后的运动。
- 不做任意复杂控制器。
- 不强行拟合某一次实验的绝对曲线。

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 15 节；来源类型：engineering_decision。

<a id="domain-9"></a>

## 9. 尚未固定且禁止擅自硬编码的登记项

本领域汇总后续由文献、临时计算或实验标定确定的事项。未固定不代表可以忽略，而是必须保留参数、接口或决策位置。

### UNRESOLVED.REGISTRY.GLOBAL — 全局未决登记表

- 状态：尚未固定
- 适用范围：全局、求解器全层级、实验对比

以下事项在正式机理推导或实验标定完成前不得被假设为唯一值；相关实现必须能显式表达“尚未确定”。

约束：

- 未固定项不得在正式机理推导完成前随意假设为唯一值。
- 未固定项不得因暂时缺少数值而从程序接口或结果记录中消失。

登记项：

| 编号 | 项目 | 作用域 | 说明 |
|---|---|---|---|
| UNRESOLVED.A1.ENGAGEMENT_CRITERIA | 单刺几何候选和稳定挂接的最终判据 | A1/A2 | — |
| UNRESOLVED.A2.FRICTION_STABILITY | 摩擦稳定条件的具体实现 | A2 | — |
| UNRESOLVED.A3.CONTACT_MIGRATION | 接触点滑移和迁移算法 | A3 | — |
| UNRESOLVED.A2.CONTACT_STIFFNESS | 局部接触刚度 | A2 | — |
| UNRESOLVED.MATERIAL.NEEDLE | 高碳钢具体材料参数 | A2/A3 | — |
| UNRESOLVED.SURFACE.STATISTICS | 红砖、混凝土和砂纸的表面统计参数 | A1 | — |
| UNRESOLVED.SURFACE.FRICTION | 各表面的摩擦系数 | A2 | — |
| UNRESOLVED.SURFACE.STRENGTH | 局部材料强度与失效域 | A3 | — |
| UNRESOLVED.DAMAGE.EVOLUTION | 损伤变量演化规律 | A3/B3/C3 | — |
| UNRESOLVED.SURFACE.RESOLUTION | 表面网格分辨率 | A1 | — |
| UNRESOLVED.STOCHASTIC.SAMPLE_COUNT | 随机样本数量 | A/B/C | — |
| UNRESOLVED.NUMERICS.EVENT_STEPS | 数值初始步长、最小步长和事件容差 | A/B/C | — |
| UNRESOLVED.SPRING.SAMPLING | 弹簧刚度的具体离散采样点 | B | — |
| UNRESOLVED.NORMAL_LOAD.SAMPLING | 法向预载 0.5–2 N 的具体离散点 | B/C | — |
| UNRESOLVED.SANDPAPER.GRITS | 具体砂纸目数集合 | A1/experiment | — |
| UNRESOLVED.METRIC.BINARY_SUCCESS | “成功抓附”的二元阈值 | validation | — |
| UNRESOLVED.METRIC.COMPOSITE_SCORE | 综合性能评分 | validation | — |
| UNRESOLVED.C1.STOP_THRESHOLD | 整爪搜索停止阈值 | C1 | — |
| UNRESOLVED.C1.MAX_SEARCH_DISTANCE | 整爪最大搜索距离 | C1 | — |
| UNRESOLVED.VALIDATION.ERROR_TOLERANCE | 实验与仿真的允许误差范围 | validation | — |

> 来源：docs/extract/ENGINEERING_FIXED_CONTEXT.md，第 16 节；来源类型：engineering_decision。

## 结构化源与生成信息

- 事实库标识：`spine-sim-v3-engineering-context`
- 结构化源目录：`engineering_fixed_context/internal/facts/`
- 原始基线：`docs/extract/ENGINEERING_FIXED_CONTEXT.md`
- 正式修改流程：提出语义变更说明 → 审查差异 → 人工确认 → 更新 YAML → 校验并重新生成。

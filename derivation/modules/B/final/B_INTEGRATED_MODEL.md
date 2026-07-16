# B_INTEGRATED_MODEL — 刚性/独立弹簧阵列爪单元正式集成模型

| 元数据 | 值 |
|---|---|
| 大模块 | `B` |
| 模型版本 | `1.0.0` |
| 工程事实版本 | `engineering_fixed_context 1.0.0` |
| 上游公共合同 | `A_TO_B 1.0.0 accepted` |
| 输入上下文 | `B_MODULE_CONTEXT 0.3.0 accepted` |
| 集成提示词版本 | `B_INTEGRATION_PROMPT 1.0.0` |
| 运行 | `B_INTEGRATION-r01` |
| 状态 | `accepted` |

> 本文件是 B1 几何/拓扑、B2 共同平衡和 B3 事件/事务的唯一集成定义。它不是求解器源代码，不修改工程事实，不固定未决材料、表面、损伤、数值或评价参数。  
> 规范词“必须/不得/可”的含义与文件中的接口合同一致。  
> 来源完整性：三份输入文件已按“工程事实 > accepted B 上下文 > 集成提示词”读取和消解；本轮未发现需要升级工程事实的冲突。

---

## 1. 范围、对象、权威输入与禁止越界

### 1.1 集成目标

正式 B 算子把一套不可变阵列配置、逐针接受状态和共享损伤快照映射为历史相关的阵列单元响应：

\[
\boxed{
\mathcal B:
\left(
\mathcal C_U,\,
\mathsf X_U^n,\,
\mathsf D^n,\,
\mathsf I_U^{\rm trial}
\right)
\longmapsto
\left(
\mathsf Y_U^{\rm trial},\,
\mathsf J_U^{\rm provisional}
\right).
}
\]

其中：

- \(\mathcal C_U\)：B1 生成并冻结的阵列配置；
- \(\mathsf X_U^n\)：最后接受的单元物理快照，内部包含逐针 opaque A 状态；
- \(\mathsf D^n\)：共享 DamageStore 接受快照；
- \(\mathsf I_U^{\rm trial}\)：允许运动、控制、事件和质量请求；
- \(\mathsf Y_U^{\rm trial}\)：contact-only wrench、状态、事件、graph/切线、能力、行程、质量和失败；
- \(\mathsf J_U^{\rm provisional}\)：无副作用的 provisional commit intent。

同一内在 B kernel 服务两个外层：

1. **standalone continuous unit driver**：组织单元级预载/拖拽路径、1 mm/s 时间映射、最大 100 mm 行程、事件循环和本层原子提交；
2. **C embedded unit trial**：从不可变接受快照试探，返回可供 C 装配的结果和 provisional intent，在 C 四单元全局接受前绝不提交。

### 1.2 物理依赖与唯一所有者

\[
\boxed{
\text{B1 immutable configuration}
\rightarrow
\left\{
\text{Surface/A1 query}
\rightarrow
\text{A single-spine embedded trials}
\right\}_{i=1}^{N}
\rightarrow
\text{B2 equilibrium/graph}
\rightarrow
\text{B3 event/transaction}
\rightarrow
\text{standalone driver or C}.
}
\]

高层只复用低层入口：

- A 拥有单刺接触、摩擦、局部接触柔顺、针梁、轴向弹簧、硬限位、材料容量、针体强度、损伤、释放和再挂接；
- B1 拥有阵列静态几何、身份、拓扑、单位规范化和共同运动映射；
- B2 拥有给定共同试探姿态下的全阵列装配、恒主动推力法向平衡、活动集合、graph 和切线；
- B3 拥有事件定位后的全阵列重求、共享损伤调度、级联、历史与事务；
- standalone driver 拥有单元路径推进与单元级接受；
- C 拥有四单元共同运动、整爪力/力矩平衡、跨单元事件/损伤归约和全局提交时机。

### 1.3 权威输入

| 优先级 | 输入 | 本模型用法 |
|---:|---|---|
| 1 | `engineering_fixed_context 1.0.0` | 固定事实、范围、扫描集合、模型开关、接口能力、排除项和未决登记 |
| 2 | `B_MODULE_CONTEXT 0.3.0 accepted` | A→B 继承语义及 B1/B2/B3 已接受机理、状态、证据边界、验证和未决项 |
| 3 | `B_INTEGRATION_PROMPT 1.0.0` | 集成分层、输出合同、必须关闭的一致性问题 |

本模型中的坐标变换、残量重组、事务层级和公共 schema 属于**集成推导**，不是新增材料事实或工程事实。

### 1.4 明确范围

本模型必须支持并比较：

- \(n_x,n_y\in\{2,3,4,5,6\}\)，且 `2×5` 与 `5×2` 独立；
- 等中心距 \(s\in\{4,5,6\}\) mm；
- 固定角 \(50^\circ,60^\circ,70^\circ,80^\circ\)；
- 根部到头部 \(80^\circ\to50^\circ\) 和 \(80^\circ\to60^\circ\) 线性梯度；
- 针径 0.6/0.8 mm、针尖半径 0.05/0.10 mm；
- `needle_bending=off/on`；
- `RIGID_MOUNT` 与 `AXIAL_SPRING_MOUNT`；
- 弹簧刚度 0.1–2.0 N/mm 的参数范围；
- 每单元主动法向推力 0.5–2 N 的参数范围；
- 红砖、混凝土和未固定目数集合的砂纸，通过统一表面接口；
- 单元最大 100 mm 连续拖拽和 1 mm/s 位移—时间映射；
- 轻量不可逆 DamageStore 和记忆内再挂接。

### 1.5 明确排除

本模型不开始或不包含：

- C1/C2/C3 的同步搜索停止阈值、最大整爪搜索距离、偏心整体平衡、渐进剥离或整爪峰值；
- 全局 A/B/C 集成；
- A 本构重建或参数覆盖；
- 显式裂纹扩展、碎屑/颗粒动力学、连续切削、地形重网格、针尖磨损；
- 安装座、框架、导轨或连接件有限元；
- 惯性动力学、大角度倾覆或任意控制器；
- 通过拟合单次偶然峰值固定模型；
- 未认证的局部 y 平移或单元转动；
- 将 `rocking=on` 静默投影到 x/z 平移。

### 1.6 当前认证等级

- 理论/数据合同：`accepted`；
- B1/B2/B3 输入：`accepted`；
- 源代码实现：未在本轮提供或验证；
- CAD、材料、表面和实验：仍有显式缺口；
- `rocking=off` 的 x/z 单元语义：合同可用；
- `rocking=on` 的真实姿态变化：`KINEMATIC_MODE_UNSUPPORTED`。

---

## 2. B1/B2/B3 集成决策、重复定义与冲突消解

### 2.1 集成决策表

| 议题 | 历史表述或潜在冲突 | 唯一规范定义 | 影响 |
|---|---|---|---|
| B1/B2 中“B3 后续” | 历史章节仍使用未来时 | 仅作为审计记录；当前 B3 已完整继承并集成 | 删除时态冲突，不删除历史语义 |
| B3 单元提交与 C Newton | B3 可在单元层原子提交；C 会反复试探四单元 | 分离 standalone driver 与 embedded trial；C 模式只返回 provisional intent | 防止 C 未接受时污染历史 |
| B 的公共入口 | B1/B2/B3 各有内部入口 | C 只调用 `embedded_array_unit_trial`；B 内部再调 A | C 无法绕过载荷共享 |
| 单元状态 | 多章节存在重叠状态枚举 | 一个互斥 `UnitMainState`，针级使用正交子状态，事务使用独立 phase | 状态唯一且不压扁原始量 |
| `active` | B1 静态存在、B2 承载活动容易混淆 | `needle_exists` 只表示配置存在；活动由 A 响应和 B 集合定义 | 禁止静态布尔量替代物理状态 |
| A wrench 与内部力 | A 同时返回净 wrench 和组件诊断 | 只把净 `A_on_B` wrench 装配一次；组件只审计 | 消除梁/弹簧/接触重复反力 |
| 主动推力 | 可能被理解为每针载荷或实际接触合力 | \(P_z\) 只在 B 外层施加一次；A 请求无逐针法向力 | 防止重复或平均载荷 |
| B2/B3 载荷共享 | B2 形成共同平衡，B3 描述重分配 | 共享和重分配都是同一兼容—A 响应—恒 \(P_z\) 方程的不同事件侧解 | 不新增转移矩阵 |
| 邻接图 | 可用于几何/相关性，也易误作转移权重 | `G4/G8/G_radius` 不参与主线载荷分配 | 防止经验均分 |
| 刚性安装 | 可用弹簧刚度极限作趋势 | 正式刚性为 exact constraint/admissible graph | 不用大有限刚度伪装 |
| 弹簧硬限位 | 4 mm 后可能被当作失败 | 进入刚性硬限位分支；只有合法图仍无平衡才不可行 | 保留可承载硬限位 |
| 损伤写入 | A 拥有材料律，B3 调度，C 有跨单元冲突 | A 生成/协调 opaque intents；B 调度单元内；C 组织跨单元联合；全局一次提交 | 禁止 B/C 直接改损伤 |
| 参考点 | `O_A`、针级 `O_i`、C 整爪参考点并存 | B 公共参考点固定 `O_A`；逐针先运输；C 再版本化运输 | 力矩和功方向唯一 |
| 主动/控制/约束量 | 可能混入 contact wrench | 四类量严格分栏；整爪墙面外部装配只用 contact-only | 防止漏算/重复 |
| 作用点 | 一般三维 wrench 未必有唯一点 | 返回中心轴；只有纯力线与声明平面唯一相交时才给点 | 不伪造压力中心 |
| 数值缓存 | B2 活动集/牛顿缓存可能混入历史 | 所有数值缓存属于 ephemeral trial cache | 回滚后物理状态不变 |
| 低维能力 | B3 仅为候选接口 | 集成为正式公共 schema，但明确历史相关、局部有效和完整回调 | 不伪装无记忆极限面 |
| C rocking | C 未来需要摇摆，B 只认证 x/z | 返回 `KINEMATIC_MODE_UNSUPPORTED`；不旋转旧 wrench | 保留能力缺口 |
| 物理无解与数值失败 | 多种失败可能被压成 `failed` | 分离无解、失稳、可/不可恢复脱附、不可用、事务和数值失败 | 结果可审计 |
| 事件优先级 | 总 if/else 会删除并发事件 | 致命认证先行；其余采用依赖偏序并保留同时组 | 并发不丢失 |
| 时间/路径 | 试探和事件定位可能误累计 | 只在 commit receipt 后推进；C embedded 不推进 | 100 mm/1 mm/s 历史一致 |

### 2.2 无工程事实冲突结论

未发现需要修改固定坐标、几何、扫描范围、加载、损伤边界或首版排除项的冲突。以下内容仍不得固定：

- 表面 PSD、高度分布、相关长度、摩擦和局部强度；
- 高碳钢具体牌号、弹性模量、屈服/断裂参数；
- 接触刚度、损伤演化、材料容量模型；
- 弹簧刚度与法向推力的离散扫描点；
- 数值步长、容差、最大迭代和事件带；
- 砂纸目数、随机样本数；
- 成功阈值、综合评分、能力特征阈值；
- C 搜索停止阈值、最大搜索距离和验证误差容限。

---

## 3. 唯一坐标、符号、单位、参考点、wrench 和功方向

### 3.1 框架

\[
\mathcal F_G=\{C,\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
\qquad
\mathcal F_U=\{O_U,\mathbf e_x,\mathbf e_y,\mathbf E_Z\},
\]

\[
\mathbf e_y=\mathbf E_Z\times\mathbf e_x,
\qquad
\mathcal F_A=\{O_A,\mathbf e_x,\mathbf e_y,\mathbf E_Z\}.
\]

- `O_U`：外部单元安装/装配参考点，可与 `O_A` 不同；
- `O_A`：B 的唯一公共 wrench 参考点和规则球心格点中心；
- \(\mathcal F_{N_i}\)：针 i 的轴向框架；
- \(\mathcal F_{C_{ij}}\)：针 i 第 j 个接触支持的局部框架；
- `T_UA`：`O_A` 到外部单元参考点的版本化静态变换；
- `T_CU`：C 整爪参考点到单元参考点的版本化安装变换。

当前 B 的单位方向矩阵为

\[
\mathbf R_{GA}=
\begin{bmatrix}
\mathbf e_x&\mathbf e_y&\mathbf E_Z
\end{bmatrix}\in SO(3).
\]

### 3.2 允许运动与实际针尖运动的区别

\[
\boxed{
\mathbf q_U=
\begin{bmatrix}
u_x\\u_z
\end{bmatrix},
\qquad
\mathbf d_U=u_x\mathbf e_x+u_z\mathbf E_Z.
}
\]

- 背板共同位移对全部针相同；
- 实际针尖、接触点、梁端和弹簧滑块位移由 A 的内部状态决定；
- `+u_z` 远离墙面，主动压入是负增量；
- 当前没有局部 y 或转动自由度。

B 的允许 twist 基为

\[
\mathbf H_U=
\begin{bmatrix}
\mathbf e_x&\mathbf E_Z\\
\mathbf0&\mathbf0
\end{bmatrix},
\qquad
\Delta\boldsymbol\xi_U^{G,O_A}=\mathbf H_U\Delta\mathbf q_U.
\]

### 3.3 单位与唯一换算

| 量 | 规范单位 |
|---|---|
| \(u_x,u_z,L,s,d,R_t,\delta_s\) | mm |
| 力、\(P_z,R_x\) | N |
| 时间 | s |
| 角度 | rad |
| 力矩 | N·mm |
| 应力/强度 | MPa |
| 刚度 | N/mm |

\[
50/100\ \mu{\rm m}=0.05/0.10\ {\rm mm},
\qquad
100\text{--}2000\ {\rm N/m}=0.1\text{--}2.0\ {\rm N/mm}.
\]

规范化器保存 source value/unit，但 B 内部和公共合同只传规范值。重复换算是 `B1_UNIT_OR_CONVERSION_INVALID` 或 `CONTRACT_VIOLATION`。

### 3.4 wrench 方向与参考点

A 返回 `A_on_B`，即单刺子系统对背板的净作用：

\[
\mathbf W_i^{G,O_A}
=
\begin{bmatrix}
\mathbf F_i\\\mathbf M_i^{O_A}
\end{bmatrix}.
\]

若原始参考点为 \(O_i\)：

\[
\mathbf M_i^{O_A}
=
\mathbf M_i^{O_i}
+
(\mathbf r_{O_i}-\mathbf r_{O_A})\times\mathbf F_i.
\]

单元 contact-only wrench 为

\[
\boxed{
\mathbf W_U^{G,O_A}=\sum_i\mathbf W_i^{G,O_A}.
}
\]

B 不再添加梁根力、弹簧力、接触合力或硬限位反力，因为它们已经在净 wrench 中。

### 3.5 主动推力、控制反力和约束反力

\[
\mathbf F_{\rm act}=-P_z\mathbf E_Z,
\qquad
P_z>0,
\]

\[
r_z=\mathbf E_Z^{\mathsf T}\mathbf F_U-P_z,
\qquad
R_x=-\mathbf e_x^{\mathsf T}\mathbf F_U.
\]

被禁止自由度的反力诊断为

\[
R_y^c=-\mathbf e_y^{\mathsf T}\mathbf F_U,
\qquad
\mathbf M^c=-\mathbf M_U
\]

（在单元基展开）。四类量为：

1. `contact_only_wrench`；
2. `active_normal_actuator`；
3. `x_displacement_control_reaction`；
4. `y/rotational_constraint_reactions`。

它们不得互相包含。

### 3.6 功和作用—反作用

单元控制功增量：

\[
\boxed{
dW_{\rm ext}=R_x\,du_x-P_z\,du_z.
}
\]

A 子系统基座输入功：

\[
dW_{\rm in,A}
=
-\sum_i
(\mathbf W_i^{G,O_A})^{\mathsf T}
\mathbf H_U\,d\mathbf q_U.
\]

平衡、坐标和参考点正确时，两者与 A 返回的可恢复储能、摩擦/材料耗散及释放能在声明残量内闭合。试探、回滚和重复调用不累计任何能量。

### 3.7 一般 wrench 的作用点语义

若 \(\|\mathbf F_U\|>0\)，中心轴最近点为

\[
\mathbf r_\perp=
\frac{\mathbf F_U\times\mathbf M_U^{O_A}}
{\|\mathbf F_U\|^2},
\]

自由力偶为

\[
\mathbf M_\parallel
=
\frac{\mathbf F_U^{\mathsf T}\mathbf M_U^{O_A}}
{\|\mathbf F_U\|^2}\mathbf F_U.
\]

只有自由力偶可忽略且中心轴与声明平面唯一相交时，才返回单一作用点/压力中心；否则返回中心轴或 `not_available`。

### 3.8 C 的当前装配规则

C 将各 `contact_only_wrench` 运输到整爪参考点并只装配一次。主动推力已经作为 B 的控制参数参与单元法向平衡，不再加入整爪墙面外部 wrench；控制/约束反力同样不作为额外墙面力。真实执行器作用线未固定，未来需要新的版本化合同。

## 4. 规范配置、状态、历史、graph 与事务对象

### 4.1 对象所有权表

| 规范对象 | 物理/软件所有者 | 坐标与单位 | 可变性 | 读取时机 | 试探修改 | 提交时机 | A/B/C 可见性 |
|---|---|---|---|---|---|---|---|
| `B1UnitConfiguration` | B1/B | \(\mathcal F_A\)，规范单位 | 不可变 | 每次 B trial | 不允许 | 配置生成时一次冻结 | A 收到派生字段；B 完整；C 句柄+公共字段 |
| `NeedleStaticRecord[N]` | B1/B | \(\mathcal F_A,\mathcal F_{N_i}\) | 不可变 | 逐针请求实例化 | 不允许 | 配置冻结 | A 按针读取；C 不直接改 |
| `geometry_hash/parameter_bundle_hash/run_binding_hash` | B | 无量纲标识 | 不可变 | 请求校验 | 不允许 | 配置/运行绑定 | A/B/C 可审计 |
| `SurfaceRealization/A1QueryHandle` | A1/表面后端 | \(\mathcal F_G\)，mm | 原始几何只读 | A 查询前 | 不允许 B/C 修改 | 新 realization 时 | C 仅句柄/版本 |
| `AcceptedAStateBundle` | A | 各针 opaque | 接受时可演化 | 每次 trial 从接受版本读 | 仅 A trial 内部 | standalone 或 C 全局原子提交 | B/C 仅句柄/版本 |
| `DamageStoreSnapshot` | A 材料层；B/C 调度 | 表面面片/核坐标 | 接受时不可逆演化 | 同一 trial 统一读取 | A 协调器生成 trial snapshot | 原子提交一次 | B/C 不解析内部变量 |
| `B2EquilibriumTrial` | B2 | \(\mathcal F_A\)，N、N·mm | ephemeral | B 内层迭代 | 可重建，不是历史 | 从不独立提交 | C 只见集成后的公开输出 |
| `ActiveSet/BranchGraph` | A+B2 | 支持/针 ID | ephemeral + 可序列化 graph | Newton/事件 | 可预测/更新 | graph 摘要随接受状态记录 | C 读摘要/handle，不改 |
| `NumericalTrialCache` | B | 无物理所有权 | ephemeral | 同一次 trial | 任意数值更新 | 永不提交为物理历史 | C 不可见或诊断可见 |
| `UnitAcceptedSnapshot` | B（含 A opaque 状态） | \(\mathbf q_U\)、版本 | 接受后不可变 | 下一步 trial | 不允许直接改 | 原子提交生成新版本 | C 持 opaque handle |
| `PerNeedleAcceptedHistory` | A；B 索引 | 逐针状态 | 接受时追加 | 试探前只读 | A trial 副本 | 原子提交 | C 只见摘要/handle |
| `UnitHistoryLedger` | B | mm、N、s、N·mm | 仅追加 | standalone/诊断 | trial 日志与接受日志分离 | receipt 后追加 | C 可读取接受摘要 |
| `EventLedger` | B | 事件坐标/版本 | 仅追加 | 事件去重 | trial event 可回滚 | receipt 后写 committed event | C 见原始事件组 |
| `EnergyLedger` | B 装配、A 提供通道 | N·mm | 接受差量 | 质量检查 | trial 计算 | receipt 后累计 | C 见摘要和残量 |
| `UnitCapabilityState` | B | \(\mathcal F_A\)，规范单位 | 接受状态的派生快照 | C/standalone 查询 | 可生成 trial 候选 | 与接受状态版本绑定 | C 公共 |
| `EmbeddedUnitTrialHandle` | B 事务层 | opaque | 单次 trial | C 回滚/prepare | 不允许 C 解析 | 提交或回滚后失效 | C 持有 |
| `RollbackToken` | B 事务层 | opaque | 单次使用/幂等 | 拒绝 trial | 无物理修改 | rollback receipt | C 持有 |
| `ProvisionalCommitIntent` | B/A | opaque + read/write sets | 不可提交状态 | prepare 前 | 只由 B/A 构造 | 需升级为 armed token | C 仅传递 |
| `ArmedCommitToken` | B 事务层 | opaque | 短生命周期、一次性 | 全局 commit | 不允许修改 | C 全局条件通过后使用 | C 持有 |
| `CommitReceipt` | B/A 持久层 | 版本/哈希 | 不可变 | 后续状态链 | 不允许修改 | 原子 commit 成功生成 | C/B 可审计 |
| `StandaloneDriverState` | standalone B driver | \(\chi,t\) | 接受时推进 | 单元路径循环 | 试探副本 | 单元级 commit | C 不使用 |
| `COpaqueUnitStateHandle` | B 提供，C 持有 | opaque | 指向接受快照 | C trial | C 不得改 | 全局 commit 后更新 | C 公共 |

### 4.2 配置、参数、运行和状态哈希

身份分层：

```text
needle_slot_id
needle_id
unit_config_id / unit_config_hash
geometry_hash
parameter_bundle_hash
run_binding_hash
state_compatibility_hash
request_hash / response_hash
trial_idempotency_key / commit_idempotency_key
```

- `unit_config_hash` 不含运行时 `q_U` 或历史；
- `run_binding_hash` 加入表面 realization、A 合同/模型版本；
- `state_compatibility_hash` 再加入逐针接受状态和 DamageStore 版本；
- 哈希前先完成一次单位规范化和确定性序列化；
- 任何几何、参数、表面或状态不相容均不得复用旧句柄。

### 4.3 不可变配置结构

```text
B1UnitConfiguration:
  schema/version/status
  unit identity and hashes
  F_G / F_U / F_A definitions
  n_x / n_y / spacing
  angle mode and per-needle alpha/beta
  per-needle L/d/R_t
  mount mode / bending switch
  static needle records
  composite body and collision geometry IDs
  surface/A1 bindings
  topology and directed separations
  parameter/model IDs and availability
  formal scan policy
```

配置静态记录不包含当前承载状态、活动集、弹簧压缩或材料损伤。


#### 4.3.1 针级广播与扩展规范

针级 `alpha/beta/L/d/R_t` 及材料、梁、弹簧参数 ID 只允许三种显式形态：

1. `scalar`：广播到全部针；
2. `by_x_row[n_x]`：按局部 x 排广播；
3. `matrix[n_x][n_y]`：完整针级值。

一维数组只能解释为 x 排，不按数组长度猜测 y 列；同一字段不得同时给标量和覆盖数组。正式扫描策略仍限制在固定角、两种规定梯度、`beta=0` 和全刚性/全独立弹簧，但底层规范对象必须保存逐针数组，不能把全阵列同角、同长、同材料硬编码为唯一数据结构。

#### 4.3.2 配置闭合与失败即停

配置按以下顺序原子校验：

```text
schema/version/enums
-> n_x/n_y and array shapes
-> units and one-time conversion
-> finite values and ID uniqueness
-> formal scan range/set
-> alpha/beta/axis normalization
-> L policy and L sin(alpha) coplanarity
-> grid uniqueness/centroid/spacing
-> base-tip forward/inverse closure
-> composite body assembly and collision envelope
-> compliance de-duplication and parameter availability
-> deterministic serialization and hashes
-> A state/surface/DamageStore compatibility
-> certified motion subspace
-> prohibited per-spine load scan
```

任一针级异常使整个配置或 trial 原子失败，不得用阵列均值替换。典型错误保留为 `B1_CONFIG_SCHEMA_INVALID`、`B1_ARRAY_SHAPE_MISMATCH`、`B1_COPLANARITY_FAILED`、`B1_ASSEMBLY_CHECK_FAILED`、`B1_DUPLICATE_COMPLIANCE`、`B1_STATE_BINDING_MISMATCH` 和 `KINEMATIC_MODE_UNSUPPORTED`。

### 4.4 接受快照

\[
\boxed{
\mathsf X_U^n=
\left(
\mathbf q_U^n,\,
\{\mathsf S_i^n\},\,
\mathsf D^n,\,
\mathsf L_E^n,\,
\mathsf L_W^n,\,
\mathsf V^n,\,
\mathsf U_{\rm main}^n
\right).
}
\]

- \(\mathsf S_i^n\)：逐针 A opaque 接受状态；
- \(\mathsf D^n\)：共享 DamageStore；
- \(\mathsf V^n\)：版本、哈希和最后收据；
- \(\mathsf U_{\rm main}^n\)：互斥单元主状态；
- trial 不能直接在该对象上写入。

### 4.5 trial 对象

```text
EmbeddedArrayUnitTrial:
  frozen_input_manifest
  control_mode / path semantics
  target q or target ux/Pz
  all per-needle A responses
  B2 residual/graph/active sets
  event phases and simultaneous group
  coordinated trial damage snapshot
  cascade rounds
  wrench/tangent/capability/quality
  rollback tokens
  provisional commit intent
```

Newton 活动集预测、线搜索、括区间和 continuation hints 存在于 `NumericalTrialCache`，不是接受物理状态。

### 4.6 三层事务边界

1. **A trial**：对单刺历史和 DamageStore 无副作用；
2. **B embedded trial**：对整个单元、全部 A 历史、DamageStore、路径、时间、事件和能量无副作用；
3. **standalone B driver**：本层平衡/事件/质量通过后，可 prepare 并提交一个单元事务；
4. **C embedded**：只有 C 四单元全局残量、跨单元事件、损伤、版本和质量全部通过，才能把全部 provisional intents 一起 prepare 并原子提交。

### 4.7 数据可见性原则

- C 可见：contact-only wrench、分栏反力、状态摘要、事件、行程、graph/切线、能力、质量、版本、opaque handles；
- C 不可见/不可改：A 状态内部变量、DamageStore 内容、低层摩擦/材料/弹簧/梁状态实现；
- B 可见低层诊断但不得改写 A 本构；
- A 不接收 C 全局平衡或每针载荷分配。

---


### 4.8 表面表示、统一接口与非承载体边界

正式主线表面为 150 mm × 150 mm 单值高度场 \(z=h(x,y)\)；完整三角网格作为非单值/倒扣和三维碰撞的次级能力分支。两者必须共享同一接触、摩擦、柔顺、材料和损伤机理，上层不得按红砖、混凝土或砂纸复制接触逻辑。

统一表面接口至少提供：

```text
height or 3D geometry
local normal / slope / required curvature
friction parameters
local material capacity/damage parameters
spatial and neighborhood queries
domain / quality / uncertainty
```

只有局部球形针尖参与承载。锥段、圆柱针杆和安装座只参与非穿透/可装配检查；任一非承载体碰撞使当前纯针尖构型不可继续。

每针查询包络覆盖共同试探路径、A 允许的梁/弹簧状态域和几何不确定性膨胀。若缺少构造包络所需的模型有效域或参数，返回 `MODEL_UNAVAILABLE/PARAMETER_UNAVAILABLE`，不能假定零挠度安全裕量。

## 5. 统一几何—逐针 A 调用—共同平衡—事件重分配方程链

### 5.1 规则格点、索引和方向

针索引 \(i=(r,c)\)，其中

\[
r=0,\ldots,n_x-1,
\qquad
c=0,\ldots,n_y-1.
\]

唯一球心格点：

\[
\boxed{
\mathbf c^0_{rc}
=
\begin{bmatrix}
x_r\\y_c\\0
\end{bmatrix},
\quad
x_r=\left(\frac{n_x-1}{2}-r\right)s,
\quad
y_c=\left(c-\frac{n_y-1}{2}\right)s.
}
\]

`r=0` 为根部排，具有最大正 x；c 随局部 `+y` 增大。行优先枚举只用于确定性序列化，不赋予物理优先级。

### 5.2 安装角、轴、实际长度和基座反算

\[
\lambda_r=\frac{r}{n_x-1},
\qquad
\alpha_r=(1-\lambda_r)\alpha_{\rm root}+\lambda_r\alpha_{\rm head}.
\]

\[
\boxed{
\mathbf a_{rc}
=
\cos\alpha_{rc}\cos\beta_{rc}\,\mathbf e_x
+
\cos\alpha_{rc}\sin\beta_{rc}\,\mathbf e_y
-
\sin\alpha_{rc}\,\mathbf E_Z.
}
\]

当前正式扫描 \(\beta=0\)，接口保留逐针 \(\beta\)。

\[
L_{rc}=
\begin{cases}
4\ {\rm mm}, & \text{固定角},\\[2mm]
\dfrac{4\sin80^\circ}{\sin\alpha_r}\ {\rm mm}, & \text{线性梯度}.
\end{cases}
\]

\[
\boxed{
\mathbf b^0_{rc}=\mathbf c^0_{rc}-L_{rc}\mathbf a_{rc}.
}
\]

梯度模式满足

\[
L_r\sin\alpha_r=4\sin80^\circ\ {\rm mm},
\]

故安装座出口共面且未加载球心共面。真实梯度基座 x 偏置必须进入 CAD/碰撞检查，不能同时假定规则球心和规则安装孔。

### 5.3 共同背板运动与针级位姿

\[
{}^G\mathbf T_A(\mathbf q_U)=
\begin{bmatrix}
\mathbf R_{GA}&\mathbf p_A^0+u_x\mathbf e_x+u_z\mathbf E_Z\\
\mathbf0^{\mathsf T}&1
\end{bmatrix}.
\]

\[
\mathbf b^G_i(\mathbf q_U)
=
\mathbf p_A^0+u_x\mathbf e_x+u_z\mathbf E_Z
+\mathbf R_{GA}\mathbf b_i^0.
\]

针轴在当前 B 认证运动中不转动。对任意 i、j：

\[
\mathbf b_j^G-\mathbf b_i^G
=
\mathbf R_{GA}(\mathbf b_j^0-\mathbf b_i^0),
\]

共同平移保持静态装配关系。


### 5.3.1 有向拓扑、转置阵列和表面相关性

对针 i、j：

\[
\boxed{
\Delta\mathbf r_{ij}^{A}
=
\mathbf c_j^0-\mathbf c_i^0.
}
\]

若 \(\Delta x=m_xs,\Delta y=m_ys\)，相应有向偏移的有序针对数为

\[
\boxed{
N(m_x,m_y)=(n_x-|m_x|)(n_y-|m_y|),
}
\]

其中偏移合法且不同时为零。B 保存 `G4`、可选 `G8`、版本化 `G_radius`、方向分组和有向分离向量。

`2×5` 与 `5×2` 的 x/y 包络、方向邻接、顺序遇障基线和表面联合采样不同；比较时必须使用相同全局坐标、同一 `+x`、同一表面 realization/坐标/种子，只交换 `n_x,n_y`，不得旋转或重采样表面使其人为等价。

表面相关性可由

\[
C_q(\mathbf p_i,\mathbf p_j)
\]

或平稳近似 \(C_q(\Delta\mathbf r_{ij})\) 表达，后端可提供方向协方差、二维 PSD、相关长度张量或联合 A1 特征查询。B1 的相关性和邻接只用于几何、查询、损伤冲突候选和诊断，不产生 IID 成功率、活动针数或载荷转移权重。

### 5.4 A embedded 试探

对每根针：

\[
\boxed{
\mathcal R_i^{\rm A}
=
\mathcal A_i^{\rm embedded}
\left(
{}^G\mathbf T_{N_i}(\mathbf q_U^n),\,
\Delta\boldsymbol\xi_U,\,
\mathsf S_i^n,\,
\mathsf D^{\rm read},\,
\mathcal P_i
\right).
}
\]

\(\mathcal R_i^{\rm A}\) 至少包含：

- `A_on_B` wrench；
- 支持/gap/法向/粘滑与迁移；
- 梁、弹簧、硬限位和强度状态；
- 材料容量、损伤 read/write set 和 trial intents；
- 事件候选、最早分数和一侧分支；
- tangent/secant/graph；
- 质量、错误、trial handle、rollback token、provisional intent。

同一试探轮全部针从相同接受快照链和相同 DamageStore snapshot 出发。`P_z` 不进入逐针请求。

### 5.5 wrench 装配

\[
\boxed{
\mathbf W_U^{G,O_A}(\mathbf q_U)
=
\sum_{i=1}^{N}
\mathcal T_{O_i\rightarrow O_A}
\mathbf W_i^{A\rightarrow B}.
}
\]

只有通过致命认证检查的响应才能装配。域外、几何不确定、体部碰撞、模型/参数缺失或陈旧响应不能置零后继续。

### 5.6 两种嵌入控制模式

#### 模式 A：`UX_PZ_BALANCED`

规定 \(u_x,P_z\)，未知 \(u_z\)。

唯一分支：

\[
\boxed{
r_z(u_z)=\mathbf E_Z^{\mathsf T}\mathbf F_U(u_x,u_z)-P_z=0.
}
\]

集合值分支：

\[
\boxed{
0\in\mathcal N_U(u_x,u_z)-P_z,
\qquad
d_z=\operatorname{dist}(P_z,\mathcal N_U).
}
\]

该模式形成 standalone 主线和 C 可选的单元法向力控制响应。

#### 模式 B：`PRESCRIBED_XZ_RESIDUAL`

规定 \(u_x,u_z,P_z\)，B 完整评估

\[
r_z=\mathbf E_Z^{\mathsf T}\mathbf F_U-P_z
\]

或 `d_z`，但不通过改变 \(u_z\) 强制平衡。C 可将该残量纳入更大的平移耦合系统。若残量未通过，响应不能标为平衡或准备提交。

### 5.7 搜索域和预载不可行

法向 admissible 区间 \(\mathcal I_z\) 由表面域、非承载体碰撞、几何最近位置、弹簧硬限位和模型有效域共同限定。全开放且 \(P_z>0\) 时：

\[
\mathbf F_U=\mathbf0,\qquad r_z=-P_z.
\]

只要仍可向墙推进，状态为 `PRELOAD_SEARCH_CONTINUE`，不是物理无解。只有穷尽合法区间和相容 graph 后仍不能平衡，才可返回对应预载不可行或 `EQUILIBRIUM_INFEASIBLE`。

### 5.8 raw 与凝聚切线

\[
\mathbf K_{Wq}^{\rm raw}
=
\sum_i
\frac{\partial\mathbf W_i}{\partial\mathbf q_U}
=
\begin{bmatrix}
\mathbf K_{W,x}&\mathbf K_{W,z}
\end{bmatrix}.
\]

\[
k_{zx}=\mathbf E_Z^{\mathsf T}\mathbf K_{F,x},
\qquad
k_{zz}=\mathbf E_Z^{\mathsf T}\mathbf K_{F,z}.
\]

唯一光滑分支且 `k_zz` 合格时：

\[
\boxed{
\frac{du_z}{du_x}\bigg|_{P_z}
=-\frac{k_{zx}}{k_{zz}},
\qquad
\mathbf K_{W,x\mid P_z}
=
\mathbf K_{W,x}
-\mathbf K_{W,z}\frac{k_{zx}}{k_{zz}}.
}
\]

否则输出一侧切线、割线、graph 或 unavailable；不得跨事件中心差分冒充一致切线。

### 5.9 事件分数和事件路径

每针返回 \(\gamma_i\)，单元归约：

\[
\boxed{\gamma_U=\min_i\gamma_i.}
\]

- `UX_PZ_BALANCED`：分数沿 \(u_x\) 路径定义；每个候选分数都重新求 \(u_z\)；
- `PRESCRIBED_XZ_RESIDUAL`：分数沿声明的 x/z 仿射路径定义；
- \(\gamma_U<1\) 时回滚目标 trial，缩短共同步并重求全阵列；
- 同时事件按括区间重叠和 A 明确分组形成规范集合；
- 行优先/线程顺序不决定物理先后。

### 5.10 事件后一侧、共享损伤和级联

设事件坐标为 \(\chi_e\) 或全局 trial fraction 对应位置。B 依次构造：

1. `PRE_EVENT_LIMIT_TRIAL`；
2. `EVENT_POINT_TRIAL`；
3. `POST_EVENT_SIDE_TRIAL`；
4. `FINAL_COMMIT_CANDIDATE`。

每一相位仍从 \(\mathsf X_U^n\) 构造，不串接未接受 A 历史。事件后一侧、损伤协调和每一级联轮都重新调用全阵列并重新解 `u_z` 或残量。

损伤冲突图：

\[
i\sim_D j
\iff
(W_i\cap W_j\neq\varnothing)
\lor(K_i\cap K_j\neq\varnothing)
\lor(W_i\cap R_j\neq\varnothing)
\lor(W_j\cap R_i\neq\varnothing).
\]

B 只组织并把 opaque intents 交给 A 损伤协调器。协调后的 trial DamageStore 变化时，所有针和共同平衡重新求解。

### 5.11 载荷重分配

事件前后：

\[
\mathbf W_i^-\in\mathcal W_i(\mathbf q_U^-;\mathsf S_i^n,\mathsf D^n),
\]

\[
\mathbf W_i^+\in\mathcal W_i(\mathbf q_U^+;\mathsf S_i^{\rm post},\mathsf D^{\rm trial}).
\]

重分配审计量：

\[
\boxed{
\Delta\mathbf W_i=\mathbf W_i^+-\mathbf W_i^-.
}
\]

恒 \(P_z\) 下：

\[
\mathbf E_Z^{\mathsf T}\sum_i\Delta\mathbf F_i\approx0
\]

至数值残量；切向反力和力矩可变化。失效针旧载荷不是需要按权重守恒分配的独立包。

### 5.12 离散功与能量

接受步外功：

\[
\boxed{
\Delta W_{\rm ext}
=
\int R_x\,du_x-\int P_z\,du_z.
}
\]

A 能量通道：

\[
\Delta\Psi_{\rm beam}
+
\Delta\Psi_{\rm spring}
+
\Delta\Psi_{\rm contact}
+
D_{\rm friction}
+
D_{\rm material}
+
E_{\rm released}.
\]

能量残量必须与数值误差、积分误差和浮点归约误差分开。只有 A 返回的材料/摩擦通道可计为相应耗散。

---

## 6. 刚性/独立弹簧统一框架与去重审计

### 6.1 统一拓扑

| 项目 | `RIGID_MOUNT` | `AXIAL_SPRING_MOUNT` |
|---|---|---|
| 共同背板运动 | 同一 `q_U` | 同一 `q_U` |
| 安装座内轴向相对运动 | 精确锁定为零 | 沿针轴单边压缩 |
| 安装座内转动 | 禁止 | 禁止 |
| 弹簧状态 | 不适用 | \(0\le\delta_s\le4\) mm |
| 弹簧力 | 不适用 | \(f_s=k_s\delta_s\) 内部分支，硬限位另有反力 |
| 拉力 | 不适用 | 禁止 |
| 硬限位 | 刚性约束本身 | \(\delta_s=4\) mm 后切换 |
| 针体弯曲 | 独立开关 | 独立开关 |
| 正式实现 | exact graph/constraint | A 的单边弹簧/硬限位分支 |

### 6.2 弹簧约束语义

\[
0\le\delta_{s,i}\le\delta_{\max}=4\ {\rm mm},
\]

\[
f_{s,i}=k_{s,i}\delta_{s,i}+\lambda_{h,i},
\qquad
\lambda_{h,i}\ge0,
\qquad
\lambda_{h,i}(\delta_{\max}-\delta_{s,i})=0.
\]

当维持接触需要 \(\delta_s<0\) 或拉力时，A 必须释放轴向约束/接触。达到 4 mm 不自动失败；合法硬限位 graph 可继续平衡。

### 6.3 物理位置—所有者—能量—不得重复矩阵

| 物理位置/机制 | 唯一所有者 | 状态量 | 力/位移输出 | 能量通道 | 开关/分支 | B/C 不得重复 |
|---|---|---|---|---|---|---|
| 球尖—表面局部接触 | A 接触层 | 支持、gap、法向、接触柔顺状态 | 支持力、净 wrench 组成 | 可选接触储能 | 接触模型 ID | 不再加 Hertz/罚力或局部刚度 |
| 三维摩擦与粘滑/迁移 | A 摩擦层 | stick/slip/support motion | 切向支持力 | 摩擦耗散 | 摩擦模型/参数 | 不用 C/B 摩擦锥重判 |
| 露出针梁 | A 结构层 | 梁位移、转角、根力/矩 | 已含于净 wrench | 梁储能 | `needle_bending` | 不在 B 再加 \(EI/L^3\) 力 |
| 轴向独立弹簧 | A mount 层 | \(\delta_s,f_s\) | 已含于净 wrench | 弹簧储能 | `AXIAL_SPRING_MOUNT` | 不再加 \(k_s\delta_s\) |
| 刚性 mount | A 约束 graph | 约束反力/秩/零空间 | 已含于净 wrench/graph | 理想约束功边界 | `RIGID_MOUNT` | 不用大有限刚度 |
| 弹簧硬限位 | A mount 层 | hard-stop active/reaction | 已含于净 wrench | 理想/接触功边界 | \(\delta_s=4\) mm | 不把硬限位反力再加一次 |
| 表面材料容量/损伤 | A 材料层 + DamageStore | 容量、damage intents、版本 | 通过 A 响应改变 wrench/事件 | 材料耗散 | damage model ID | B/C 不直接减强或改摩擦 |
| 针体屈服/断裂 | A 强度层 | 截面内力、裕度、terminal | A 事件/后侧响应 | 由 A 声明 | strength model ID | 不把释放等同断裂 |
| 共同刚性背板兼容 | B1/B2 | `q_U` | 所有针共同输入 | 外部控制功 | x/z 运动 | 不给每针独立板位移 |
| 恒 \(P_z\) 共同平衡 | B2 | `u_z`/graph | 单元 resultant | \(-P_zdu_z\) | 控制模式 | 不平均分配 \(P_z\) |
| 活动集载荷共享 | B2 | O/N/G/L 等集合 | 逐针净 wrench 求和 | 无独立能量项 | 响应分支 | 不引入均载公式 |
| 事件后重分配/级联 | B3 调度 | 事件组、后侧状态 | 全阵列重求的 \(\Delta W_i\) | 最终事件差量 | event/cascade | 不使用邻接权重/旧峰值包 |
| 损伤写入协调 | A 物理，B/C 调度 | read/write sets、trial snapshot | 间接改变后续响应 | 材料耗散由 A 给出 | transaction | 不按顺序覆盖或相加 |
| 主动法向推力 | B 外层 | \(P_z\) | `active_actuator` 分栏 | \(-P_zdu_z\) | 0.5–2 N 参数 | 不进入 A，不在 C 外部接触重复加 |
| x 控制反力 | B 后处理 | \(R_x\) | control 分栏 | \(R_xdu_x\) | 位移控制 | 不加到 contact-only |
| y/转动约束反力 | B 后处理 | \(R_y^c,\mathbf M^c\) | constraint 分栏 | 允许位移为零 | 运动约束 | 不视作额外爪刺力 |

### 6.4 损伤的有限作用边界

材料损伤只能按 A 的版本化材料律改变对应容量/历史。没有证据时，不得同步降低：

- 摩擦系数；
- 针梁刚度；
- 轴向弹簧刚度；
- 针体材料参数；
- 原始表面几何。

新的独立试验/新 surface realization 从无损状态开始。

### 6.5 失败语义去重

下列状态必须独立：

- 接触释放；
- `FRICTION_CONE_REACHED`；
- `SLIP_ONSET_CONFIRMED`；
- 支持迁移；
- 材料起始/软化；
- 针体屈服/断裂；
- 弹簧硬限位进入/离开；
- 非承载体碰撞；
- 物理无解；
- 物理失稳；
- 模型/参数不可用；
- 数值未收敛；
- 事务/版本错误。

不得统一压缩为 `failed`。

## 7. 规范状态机、事件依赖、同时事件和级联

### 7.1 互斥单元主状态

`UnitMainState` 只描述**最后接受的物理状态**，互斥枚举为：

| 主状态 | 进入条件 | 保持不变量 | 允许退出 |
|---|---|---|---|
| `READY_SEARCH` | 配置/快照有效，当前尚未形成承载平衡但可继续搜索 | 状态版本有效；路径未越界 | 首次平衡、可恢复脱附、终止 |
| `BALANCED_ATTACHED` | 当前接受状态有合法法向平衡且至少一个承载针 | \(P_z\) 平衡或 graph 可行；历史已提交 | 平滑推进、事件、可恢复/不可恢复脱附、终止 |
| `DETACHED_RECOVERABLE` | 当前无承载，但存在 continuable 针、合法搜索域和余程 | 路径/时间不重置；损伤不恢复 | 再挂接、不可恢复、域/碰撞/数值终止 |
| `COMPLETED_PATH` | standalone 达到规定端点，最大 100 mm | 最后收据有效 | 终态 |
| `TERMINATED_PHYSICAL` | 无解、失稳、不可恢复脱附或体碰撞等物理/几何终止 | 保留最后有效接受状态 | 终态，除非外部创建新试验 |
| `TERMINATED_UNCERTIFIED` | 模型/参数/几何/域/运动子空间不支持 | 不得用于物理排序 | 补全输入后从接受快照新试验 |
| `TERMINATED_TRANSACTION` | 陈旧、合同、损伤协调或持久化失败 | 未接受 trial 全回滚 | 修复事务后重试 |
| `TERMINATED_NUMERICAL` | 未证明无解但算法不能收敛 | 最后有效接受状态不变 | 更换数值配置后重试 |

配置错误发生在创建接受状态前，不形成一个可承载的主状态。

### 7.2 独立的 trial/事务 phase

`TransactionPhase` 与主状态正交：

```text
FROZEN_INPUT
-> FULL_ARRAY_EVALUATION
-> EQUILIBRIUM_SOLVE
-> EVENT_LOCATION
-> EVENT_POINT_VALIDATION
-> POST_EVENT_REBALANCE
-> DAMAGE_COORDINATION
-> CASCADE_RESOLUTION
-> FINAL_CANDIDATE
-> PREPARED
-> COMMITTED | ROLLED_BACK
```

phase 不是物理时间推进。C embedded trial 最多到 `FINAL_CANDIDATE`，只有全局 prepare/commit 后进入新的接受主状态。

### 7.3 逐针正交子状态

每针同时保存以下维度和原始连续量：

1. **几何/支持**：`OPEN`、`NEAR_CONTACT`、`CLOSED_ZERO_LOAD`、`LOAD_BEARING`；
2. **接触运动**：`NO_CONTACT_MOTION`、`STICK`、`SLIP_ONSET_CONFIRMED`、`SLIDING`、`MIXED_SUPPORT_MOTION`；
3. **安装结构**：`RIGID_MOUNT`、`SPRING_ZERO`、`SPRING_INTERIOR`、`SPRING_HARD_STOP`；
4. **梁结构**：`BENDING_OFF`、`ELASTIC_VALID`、`MODEL_LIMIT`、`STRENGTH_EVENT`；
5. **材料/针体**：`SUBCRITICAL`、`MATERIAL_EVENT`、`SOFTENED`、`TERMINAL_STRENGTH`；
6. **质量/认证**：`VALID`、`SET_VALUED`、`EVENT_REDUCTION_REQUIRED`、致命错误类；
7. **唯一性/线性化**：`UNIQUE`、`REPRESENTATIVE_NONUNIQUE`、`SET_VALUED` 及 tangent status；
8. **恢复性**：`CONTINUABLE`、`TERMINAL`。

任何标签必须与 gap、支持力、摩擦裕度、\(\delta_s\)、剩余行程、材料/强度裕度、graph 和质量数据一起保存。


#### 7.3.1 针级子状态转移、恢复与提交语义

| 子状态 | 进入条件 | 保持不变量 | 允许转移/退出事件 | 可恢复性 | 历史提交 |
|---|---|---|---|---|---|
| `OPEN` | A 无 active support，合法 gap 为开 | wrench 可为零；针仍存在并继续被调用 | `CONTACT_ESTABLISH`→`NEAR_CONTACT/CLOSED_ZERO_LOAD/LOAD_BEARING`；终止质量错误 | 可恢复 | 仅最终接受状态写入 |
| `NEAR_CONTACT` | A 给 near support，无合法承载 | 不创造接触力 | 接触建立、远离、域/碰撞边界 | 可恢复 | 接受后记录 raw gap |
| `CLOSED_ZERO_LOAD` | active support 存在但承载近零 | 单边约束合法，不能按承载计数 | 加载→`LOAD_BEARING`；释放→`OPEN`；迁移 | 可恢复 | 与零力带 ID 一起提交 |
| `LOAD_BEARING` | 存在正承载支持或合法非零 wrench | 力来自 A 净响应 | 滑移、迁移、材料/强度事件、释放 | 通常可恢复，取决于 A | 提交逐支持力和 wrench |
| `NO_CONTACT_MOTION` | 无接触或无切向支持运动 | 不宣称 stick/slip | 接触建立后进入其他运动状态 | 可恢复 | 接受时记录 |
| `STICK` | A 证明粘着分支可行 | 摩擦裕度和支持 ID 有效 | 锥边界、滑移起始、迁移、释放 | 可恢复 | 只提交最终分支 |
| `SLIP_ONSET_CONFIRMED` | A 证明全粘着一侧不可行并给滑移后侧 | 不与 `FRICTION_CONE_REACHED` 混同 | `SLIDING`、重新粘着、迁移、释放 | 可恢复但可耗散 | 提交事件和 A 耗散 |
| `SLIDING` | A 返回滑动支持/增量 | 摩擦耗散非负按 A convention | stick、迁移、释放、材料事件 | 可恢复但历史相关 | 提交累计滑移仅一次 |
| `MIXED_SUPPORT_MOTION` | 同针多支持含不同运动分支 | 保存全部支持，不用单一代表替代 | 支持集合变化或统一分支 | 可恢复 | 提交支持级状态 |
| `RIGID_MOUNT` | 配置为刚性安装 | 轴向相对位移严格为零 | 仅随接触/graph 分支变化 | 不适用“回弹” | graph/反力随接受状态记录 |
| `SPRING_ZERO` | \(\delta_s=0\)，无预压/拉力 | \(f_s\ge0\)，不得负压缩 | 压缩→`SPRING_INTERIOR`；释放保持零 | 可恢复 | 提交 \(\delta_s=0\) |
| `SPRING_INTERIOR` | \(0<\delta_s<4\) mm | 线性压缩分支、无拉力 | 回弹→zero；硬限位进入；接触释放 | 可恢复 | 提交最终压缩与储能 |
| `SPRING_HARD_STOP` | \(\delta_s=4\) mm 且硬限位反力合法 | 不得超过 4 mm；额外反力属硬限位 | `HARD_STOP_LEAVE`、释放、无解 | 可恢复/可离开 | 提交硬限位事件和反力 |
| `BENDING_OFF` | `needle_bending=off` | 梁位移/储能为零；强度接口可保留 | 配置不在运行中切换 | 不适用 | 配置级记录 |
| `ELASTIC_VALID` | 梁模型有效且未越界 | 使用实际 \(L_i,d_i\)；能量按 A | 强度事件、模型有效域边界、卸载 | 通常可恢复 | 提交 A 梁状态 |
| `MODEL_LIMIT` | 梁/结构模型超有效域 | 当前响应未认证 | 补充模型/减步/终止 | 未认证，不是物理断裂 | 不提交为物理失效 |
| `SUBCRITICAL` | 材料与针体裕度为正 | DamageStore 版本一致 | 材料起始、强度事件 | 可继续 | 提交原始裕度 |
| `MATERIAL_EVENT` | A 容量事件临界 | 不由 B 直接改损伤 | A damage intent→协调→`SOFTENED`/其他后侧 | 不可逆记忆可能开始 | 仅协调后最终状态提交 |
| `SOFTENED` | DamageStore 已提交损伤影响 | 强度不自动恢复；不隐式改摩擦/梁/弹簧 | 继续承载、释放、再挂接、终止 | 可继续但历史不可逆 | 提交 DamageStore 新版本 |
| `TERMINAL_STRENGTH` | A 明确终止断裂/强度状态 | 首版不模拟断针后承载 | 保持 terminal fast path | 不可恢复 | 原子提交 terminal 版本 |
| `UNIQUE` | 当前 wrench/分支唯一 | 可按状态声明切线质量 | 事件/退化→非唯一或 set-valued | 状态可变 | 随接受状态提交 |
| `REPRESENTATIVE_NONUNIQUE` | A 给连续性代表值但非唯一 | 必须保留非唯一警告/集合 | 分支消除或 graph 扩展 | 不适用 | 代表值和边界一起提交 |
| `SET_VALUED` | admissible graph 非单点 | 不以罚刚度或 ID 选唯一 | graph 变单点、分支变化、无解 | 不适用 | 提交 graph handle/秩/零空间 |
| `VALID` | 合同、域、几何、模型和残量满足 | 可进入装配 | 任一致命诊断 | 不适用 | 质量随接受状态提交 |
| `CONTINUABLE` | A 声明释放后仍可搜索/再挂接 | 路径和损伤不重置 | 再挂接或 terminal | 可恢复 | 接受时保存恢复性 |
| `TERMINAL` | A 声明不再参与未来物理分支 | 仍出现在请求/响应和审计中 | 无物理恢复 | 不可恢复 | 原子提交 terminal 句柄 |

所有子状态转换先形成 trial；只有所属单元最终候选被 standalone 或 C 全局事务接受后，才一次性写入逐针历史。被回滚的转换只能进入诊断日志。

### 7.4 单元集合

\[
\begin{aligned}
\mathcal O&=\{i:\text{无 active support}\},\\
\mathcal N&=\{i:\text{near-contact 且不承载}\},\\
\mathcal G&=\{i:\text{有 active support}\},\\
\mathcal L&=\{i:\text{存在正承载或合法非零 wrench}\},\\
\mathcal S_{\rm stick}&=\{i:\text{粘着承载}\},\\
\mathcal S_{\rm slip}&=\{i:\text{真实滑移起始或滑动}\},\\
\mathcal H&=\{i:\text{硬限位分支}\},\\
\mathcal E&=\{i:\text{事件候选}\},\\
\mathcal D&=\{i:\text{集合值/退化}\},\\
\mathcal X&=\{i:\text{不可装配致命响应}\}.
\end{aligned}
\]

开放针不得永久跳过；`q_U`、分支或 DamageStore 变化后全部针重新调用。

### 7.5 致命认证优先级

在装配任何 wrench 前按以下顺序处理：

1. 合同、单位、版本、哈希、陈旧和幂等性错误；
2. 未认证运动子空间；
3. 表面域外；
4. 几何质量不足；
5. 锥段、针杆或安装座禁止碰撞；
6. 模型/参数/graph/能量适配器不可用。

这些响应不能作为零承载针进入装配。

### 7.6 物理事件规范表

| 事件 | 进入条件来源 | 保持/后侧要求 | 可恢复性 |
|---|---|---|---|
| `CONTACT_ESTABLISH` | A gap/支持事件 | 重求全阵列和共同平衡 | 通常可逆 |
| `CONTACT_RELEASE` | A 单边接触后侧 | 释放针仍继续被调用 | 可恢复，除非 A terminal |
| `FRICTION_CONE_REACHED` | A 摩擦边界诊断 | 不等同真实滑移 | 诊断 |
| `SLIP_ONSET_CONFIRMED` | A 证明粘着不可行并给滑移分支 | 重算支持/摩擦/材料 | 可逆或伴随耗散 |
| `SUPPORT_MIGRATION` | A 支持点/特征切换 | 保留旧/新支持 ID | 可逆 |
| `MATERIAL_INITIATION` | A 材料容量 | 生成 trial damage intent | 不可逆记忆 |
| `MATERIAL_SOFTENING_UPDATE` | A 损伤演化 | DamageStore 协调后重求 | 不可逆 |
| `NEEDLE_STRENGTH_EVENT` | A 截面强度 | 根据 A 返回继续/终止 | 模型决定 |
| `NEEDLE_TERMINAL_FRACTURE` | A terminal 强度事件 | 首版不模拟断针后承载 | 不可恢复 |
| `SPRING_HARD_STOP_ENTER` | \(\delta_s=4\) mm 一侧切换 | 进入刚性硬限位 graph | 可离开 |
| `SPRING_HARD_STOP_LEAVE` | 硬限位反力消失/回弹 | 回到内部或释放分支 | 可逆 |
| `REENGAGED` | 先前开放/搜索针新支持并经平衡接受 | 记录面片、损伤版本 | 可恢复链 |
| `BODY_COLLISION` | 非承载体 gap 违规 | 终止纯针尖模型 | 非普通事件 |
| `DOMAIN_BOUNDARY` | 查询包络越界 | 未认证终止 | 非普通事件 |
| `GEOMETRY_QUALITY_FAILURE` | 法向/曲率/网格质量不足 | 未认证终止 | 非普通事件 |

### 7.7 依赖偏序

非致命事件不使用武断总 if/else。重算偏序为：

```text
接触支持/几何可行分支
  -> 粘滑/支持迁移与弹簧内部/硬限位
  -> 当前力状态下的材料容量与针体强度
  -> 共享损伤协调
  -> 全阵列共同平衡、容量和稳定性复核
```

同时发生的事件全部写入同一事件组；偏序只规定后侧响应依赖，不删除事件。

### 7.8 同时事件组

事件括区间 \([a_e^-,a_e^+]\) 在声明同时容差内相交，或 A 给出同一 simultaneous ID 时，形成

\[
\mathcal G_e=
\operatorname{CanonicalSet}
\{(needle,event,support,patch,bracket,raw\ value,prestate)\}.
\]

规范排序只用于序列化和哈希。若后侧有多个真实可行分支，返回 branch set/graph，不按针 ID 选取。

### 7.9 同位置级联

级联满足：

- 物理位置与 \(P_z\) 不变；
- 新事件由上一后侧重平衡、损伤协调或容量复核直接触发；
- 中间无已提交平滑状态。

每轮重新求 `u_z`、全部针、活动集、损伤和能量。终止条件：

- `CASCADE_STABILIZED`；
- `EQUILIBRIUM_INFEASIBLE`；
- `PHYSICAL_INSTABILITY`；
- `UNIT_DETACHED_RECOVERABLE/IRRECOVERABLE`；
- 未认证状态；
- `NUMERICAL_NONCONVERGENCE`。

### 7.10 Zeno 与顺序依赖防护

- 保存原始事件量和括区间，不用数值带替代物理阈值；
- enter/leave 数值带可不同，但必须版本化；
- 事件转换键包含位置、对象、事件、前后状态和级联 ID；
- 相同转换幂等去重，反向转换作为新事件记录；
- 相同 `q/branch/event/damage` 哈希重复且残量无改善时停止；
- 采用确定性归约和规范求和；
- 最大定位/冲突/级联轮数是数值安全阈值，不是物理上限。

---

## 8. standalone unit driver 与 C embedded unit trial 分层

### 8.1 共用内在 kernel

两种外层共用：

- 同一 `B1UnitConfiguration`；
- 同一逐针 A embedded 请求；
- 同一 B2 residual/graph；
- 同一事件分数和全阵列重求；
- 同一共享 DamageStore 协调；
- 同一状态、能量、质量和失败分类；
- 同一 provisional intent 格式。

不得维护两套物理实现。

### 8.2 standalone continuous unit driver

职责：

1. 从单元接受快照开始；
2. 选择合法数值 `Δχ`；
3. 以 \(u_x=u_x^0+\chi\) 推进；
4. 给定 \(P_z\) 求 `u_z`；
5. 处理最早事件、后侧、损伤和级联；
6. 单元层 prepare/commit/rollback；
7. 仅在 receipt 后推进
   \[
   t=\chi/(1\ {\rm mm/s});
   \]
8. 精确终止在用户端点或 100 mm；
9. 输出完整单元、逐针、事件和能量历史。

standalone 可提交，因为其本层就是接受边界。

### 8.3 C embedded unit trial

职责：

1. 只读 C 提供的 accepted unit snapshot 和共同 DamageStore snapshot；
2. 在认证 x/z 子空间执行完整试探；
3. 返回 contact-only wrench、分栏反力、残量/graph、事件、能力、质量、trial damage 和 provisional intent；
4. 若发现更早事件，返回建议全局增量上限，当前目标不可提交；
5. C 缩短后，B 从同一接受快照重求；
6. 单元内部同时事件和级联由 B 处理；
7. 跨单元事件、共享损伤和全局残量由 C 组织；
8. C 全局接受前不推进路径、时间、损伤、耗散或事件号。

### 8.4 公开控制模式

- `UX_PZ_BALANCED`：C 给 `u_x/P_i`，B 求 `u_z`；
- `PRESCRIBED_XZ_RESIDUAL`：C 给 `q_U/P_i`，B 返回残量/graph；
- 两者都只认证平移；
- 后者是耦合方程入口，不允许忽略残量后准备提交。

### 8.5 C 的全局缩步义务

四单元建议分数：

\[
\gamma_C=\min_{j=1,\ldots,4}\gamma_{U_j}.
\]

缩短后 C 重新生成各单元试探输入并重新调用所有受全局平衡影响的单元。当前四单元刚体耦合主线默认四个全部重调。不得只重算触发单元。

### 8.6 C 全局原子接受

只有以下全部通过：

- 四单元 B residual/graph；
- C 全局力/力矩/运动残量；
- 全局事件组；
- 跨单元 DamageStore fixed point；
- 版本、哈希、质量、能量和认证；

才能把四单元 provisional intents 一起 prepare 并原子提交。任一失败全部 rollback。

---

## 9. 可执行单步残量、算法、嵌套事务和失败分类

### 9.1 调用前不变量

```text
assert configuration/status/version compatible
assert units normalized once
assert q and increment in certified x-z subspace
assert Pz is unit-level control parameter
assert no per-spine normal load exists
assert accepted A states and DamageStore are immutable
assert surface/domain/collision query envelope is available
freeze one input manifest and one state_compatibility_hash
```

### 9.2 全阵列评估函数

```text
FUNCTION FULL_ARRAY_EVALUATE(frozen_snapshot, trial_q, phase, trial_damage):
    responses = []
    FOR every configured needle in deterministic audit order:
        build A embedded request from the same accepted A state,
        same trial_damage snapshot, same common board increment,
        needle-specific static geometry/parameters
        call A embedded_constitutive_trial
        preserve the full response without state edits
        if fatal certification error:
            return uncertified response; do not zero this needle
        responses.append(response)
    transport every valid A_on_B wrench to G,O_A
    assemble contact-only W_U, raw tangent/graph, active sets,
    event candidates, damage sets, quality and energy channels
    return full assembly
```

并行实现可改变执行顺序，但归约和输出必须确定性。

### 9.3 B2 法向平衡函数

```text
FUNCTION SOLVE_UNIT_NORMAL_BALANCE(frozen_snapshot, target_ux, Pz, phase, damage):
    choose legal uz predictor/bracket in admissible interval I_z
    FOR k = 0..max_outer_iterations:
        trial_q = [target_ux, uz_k]
        assembly = FULL_ARRAY_EVALUATE(...)
        if fatal/unavailable:
            return classified failure
        if assembly reports an earlier unhandled event:
            return EVENT_REDUCTION_REQUIRED with raw event data
        evaluate rz or normal graph distance
        test A constraints, branch stability, quality and one-sided status
        if converged:
            return B2 balanced trial, no commit
        choose safeguarded semismooth/generalized Newton step when valid
        otherwise use bounded secant, bracket, graph projection or continuation
        update uz inside I_z
        every iteration re-calls all needles from the same accepted state
    return NUMERICAL_NONCONVERGENCE unless physical infeasibility is proven
```

Newton 迭代之间不得串接 A 历史。

### 9.4 事件定位函数

```text
FUNCTION LOCATE_EARLIEST_UNIT_EVENT(accepted_snapshot, proposed_target):
    probe the proposed target
    reduce all needle suggested fractions to gamma_U
    if gamma_U == 1 and no earlier event:
        return smooth target candidate
    rollback all target trials
    shorten the common path according to its declared fraction basis
    re-solve the complete unit at the shortened target
    refine brackets with repeated full-array solves
    rebuild the simultaneous event group after each re-equilibration
    verify no other needle event is earlier
    return pre-event, event-point and raw simultaneous group
```

`UX_PZ_BALANCED` 中不能缩放旧 `u_z`；每个事件候选 `u_x` 都重新解 `u_z`。

### 9.5 事件后一侧与损伤协调

```text
FUNCTION RESOLVE_POST_EVENT_SIDE(event_point, canonical_group):
    create distinct post-side trial identity
    request A-defined post-event branches without direct B state edits
    re-call every configured needle
    re-solve the complete unit balance/residual
    build damage conflict graph from opaque read/write/kernel signatures
    call A damage coordinator
    if trial DamageStore changes:
        re-call all needles and re-solve balance
        rebuild conflict graph
    repeat until one common trial DamageStore and all responses are consistent
    return post-side candidate or explicit nonunique/unresolved state
```

### 9.6 级联 fixed-point

```text
FUNCTION RESOLVE_CASCADE(event_coordinate, post_side_candidate):
    seen_state_hashes = {}
    FOR c = 0..max_cascade_rounds:
        evaluate all current event/capacity channels
        build new simultaneous event group at the same physical coordinate
        if no new event and balance/damage/quality/energy pass:
            return CASCADE_STABILIZED final candidate
        if physical no-equilibrium/stability/recoverability proof passes:
            return classified physical termination
        if unavailable/stale/transaction failure:
            return classified uncertified/transaction termination
        if state hash repeats without residual improvement:
            return NUMERICAL_NONCONVERGENCE
        resolve new group, coordinate damage, and fully re-solve
    return NUMERICAL_NONCONVERGENCE
```

### 9.7 从接受状态 n 到候选 n+1 的总算法

```text
INPUT:
  B1 configuration C_U
  accepted unit snapshot X_U^n
  shared DamageStore snapshot D^n
  trial target/control from standalone driver or C
  numerical/event/quality configuration

1. Freeze configuration, units, hashes, accepted states, damage snapshot,
   frame transform, control mode and trial identities.
2. Validate motion subspace; reject y/rotation/rocking requests.
3. Assemble the requested target:
     a. standalone: target chi/u_x and Pz;
     b. C embedded UX_PZ_BALANCED: target u_x and P_i;
     c. C embedded PRESCRIBED_XZ_RESIDUAL: target q_U and P_i.
4. Build a predictor, but never mutate accepted history.
5. Evaluate the full array:
     a. for balanced mode solve common u_z;
     b. for prescribed mode evaluate residual/graph.
6. Reduce earliest needle event fractions.
7. If an event precedes target:
     a. rollback every target trial;
     b. locate the common event by repeated full-array re-solves;
     c. return EVENT_REDUCTION_REQUIRED to C if the C global step must shrink;
     d. standalone shrinks its own step and continues.
8. At the globally accepted event coordinate, build PRE_EVENT_LIMIT_TRIAL
   and EVENT_POINT_TRIAL.
9. Construct the canonical unit simultaneous event group.
10. Request POST_EVENT_SIDE_TRIAL from A for all needles.
11. Re-solve the complete B2 problem; do not edit A state to force balance.
12. Coordinate unit-internal DamageStore conflicts using A's coordinator.
13. Whenever the trial DamageStore changes, re-call all needles and re-solve.
14. Execute same-position cascade rounds to a fixed point or classified end.
15. Assemble final contact-only wrench, separate active/control/constraint
   fields, raw/condensed tangent or graph, state, events, capability,
   remaining travel, damage sets, energy and quality.
16. Check:
     - action/reaction and reference-point transport;
     - normal balance or graph distance;
     - active/branch one-sided consistency;
     - no unhandled earlier event;
     - damage fixed point and version consistency;
     - energy/numerical residual separation;
     - deterministic hashes and idempotency.
17. Create FINAL_COMMIT_CANDIDATE, rollback token and provisional intent.
18. If standalone:
     a. prepare the complete unit/A/DamageStore bundle;
     b. on any failure rollback;
     c. commit once;
     d. append physical path/time/history only from receipt;
     e. continue until endpoint, 100 mm or classified termination.
19. If C embedded:
     a. return without permanent commit;
     b. C may shrink/reject and must rollback;
     c. after C global acceptance, all four intents prepare together;
     d. commit one global bundle or rollback all.
```

### 9.8 C 缩步后的重调

当任一单元给出更小分数、C 全局 Newton 改变姿态/位移、或跨单元 DamageStore 变化时：

- 原四单元响应全部视为陈旧；
- C 重新计算每个单元合法输入；
- 所有受全局平衡影响的单元重新调用；
- 不允许只旋转/缩放旧 wrench；
- 不允许只更新触发事件的针或单元。

### 9.9 prepare/commit/rollback

```text
trial -> provisional intent
global checks -> prepare all intents
all prepared -> one atomic global commit
any failure -> rollback all
```

prepare 只验证版本、哈希、read/write set 和持久化可用性，不推进物理状态。armed token 一次性并绑定最终候选哈希。重复 commit key 只能返回同一收据或安全拒绝。

### 9.10 失败分类和证明边界

| 类别 | 使用条件 | 不得混用 |
|---|---|---|
| `EQUILIBRIUM_INFEASIBLE` | 模型/参数/几何可用，已搜索全部相容分支且 graph 不含目标 | 不由 Newton 失败推断 |
| `PHYSICAL_INSTABILITY` | 一侧稳定性/admissible graph 明确否定稳定准静态分支 | 不由负切线单独推断 |
| `UNIT_DETACHED_RECOVERABLE` | 当前无承载但仍有 continuable 针、合法域和余程 | 不终止/不重置路径 |
| `UNIT_DETACHED_IRRECOVERABLE` | 全部针终止或已证明剩余合法路径无法恢复 | 强于单点无解 |
| `MODEL/PARAMETER_UNAVAILABLE` | 所需物理模型/参数缺失 | 不视为零承载 |
| `OUT_OF_DOMAIN/GEOMETRY_UNCERTAIN/BODY_COLLISION_INVALID` | 查询或纯针尖模型认证边界 | 不视为材料失效 |
| `DAMAGE_CONFLICT_UNRESOLVED/STALE/CONTRACT` | 事务无法形成一致候选 | 全部回滚 |
| `NUMERICAL_NONCONVERGENCE` | 尚不能证明物理无解，算法未收敛 | 不视为物理失效 |
| `EQUILIBRIUM_DEGENERATE` | 平衡存在但反力/分支集合值 | 保留 graph/零空间 |

### 9.11 standalone 路径和时间

\[
\chi=u_x-u_x^0,
\qquad
0\le\chi\le100\ {\rm mm},
\qquad
t=\chi/(1\ {\rm mm/s}).
\]

只有 commit receipt 后推进 \(\chi,t\)。事件定位、Newton、回溯、损伤协调和级联不增加物理时间。释放后不重置路径。


## 10. 原始输出、能力特征、历史相关接口和完整回调

### 10.1 单元接受历史 `H_U`

每个接受状态至少保存：

```text
identity:
  accepted_state_id / commit_receipt_id
  unit_config / parameter / surface / damage versions
path:
  chi_mm / u_x_mm / u_z_mm / time_s / Pz_N
contact_only:
  F_U_N[3] / M_U_Nmm[3] at G,O_A
  Rx_N
active_control_constraints:
  active Pz / x control / y and rotational reactions
balance:
  rz or graph distance / uniqueness / rank / nullspace / certification
linearization:
  raw K_Wq / K_Qq
  condensed K_W,x|Pz when valid
  secant or graph / branch / reference / validity
state:
  O/N/G/L/stick/slip/hardstop/event/invalid/degenerate sets
  N_nominal / N_geom / N_load / N_eff
damage_events:
  DamageStore version / recent event group / cascade / reengagement
energy_quality:
  work/storage/dissipation/residual ledger
  quality / uncertainty / all status codes
```

必须保存力—位移；力—时间由同一接受历史派生，不建立动力学。

### 10.2 逐针接受历史 `H_i`

每针至少保存：

- `A_on_B` force/moment、参考点和运输记录；
- 支持点、gap、法向、切基、支持力和乘子；
- 几何/承载/粘滑/弹簧/梁/材料/强度/质量/唯一性子状态；
- \(\delta_s\)、弹簧力、剩余行程、硬限位反力；
- 梁位移、转角、根部力/矩、储能和有效域；
- 摩擦、材料和针体裕度原始向量；
- queried patches、damage read/write 摘要和 DamageStore 版本；
- 累计 \(\chi,t\)、释放后局部搜索距离、首次/再次挂接位置；
- opaque A 接受状态句柄和版本；
- 相关事件和提交收据。

### 10.3 事件历史 `H_E`

```text
EventRecord:
  event_id / event_group_id / cascade_id
  path coordinate / time / bracket / fraction basis
  event type / raw event values / numerical band ID
  needle / support / patch participants
  pre-event / event-point / post-event states
  q_U and Pz pre/post
  W_i and W_U pre/post / delta_W_i
  damage conflict and coordinated versions
  energy and residuals
  branch / graph / nonuniqueness
  response hashes / commit receipt
```

未提交事件只进入 rejected trial diagnostics，并明确标记，不得混入 committed history。

### 10.4 针数和不均载指标

\[
N_{\rm nominal}=N,
\qquad
N_{\rm geom}=|\mathcal G|,
\qquad
N_{\rm load}=|\mathcal L|.
\]

对明确命名的非负通道 \(\ell_i\)：

\[
w_i=\frac{\ell_i}{\sum_j\ell_j},
\qquad
\boxed{
N_{\rm eff}=\frac{1}{\sum_iw_i^2}
=\frac{(\sum_i\ell_i)^2}{\sum_i\ell_i^2}.
}
\]

法向与切向通道分别计算并声明是否包含零载荷针。可同时保存 CV、Gini、最大/平均和容量利用率，但不固定综合评分。

### 10.5 事件前后重分配输出

\[
\Delta\mathbf W_i=\mathbf W_i^+-\mathbf W_i^-,
\qquad
\Delta R_{x,i}=-\mathbf e_x^{\mathsf T}\Delta\mathbf F_i.
\]

必须同时输出：

- pre/post 支持与分支；
- pre/post 弹簧压缩/余程；
- 材料/摩擦/强度利用率；
- 单元 `W_U/R_x/u_z` 变化；
- 同时事件、级联和损伤冲突；
- 法向差量闭合残量；
- commit receipt。

### 10.6 原始能力曲线和候选特征

保留完整 \(R_x(\chi),\mathbf W_U(\chi),u_z(\chi)\) 后，才可派生：

- 首次几何接触；
- 首次承载；
- 首次正 \(R_x\)；
- 全程峰值和事件间局部峰值；
- 峰值持续距离；
- 再挂接次数、间隔与恢复能力；
- 搜索距离边际增益；
- 平台候选；
- 峰值/平台期间的逐针状态、行程和损伤分布。

候选持续距离：

\[
L_{\rm persist}(\rho)
=
\max_I
\{|I|:R_x(\chi)\ge\rho R_{x,\max},\ \forall\chi\in I\}.
\]

候选边际增益：

\[
\Delta_wR_x(\chi)
=
\max_{\xi\in[\chi,\min(\chi+w,L_x)]}R_x(\xi)-R_x(\chi).
\]

\(\rho,w\)、平台阈值、窗口数和统计方法均由 `feature_config_id` 给出，当前不固定。

### 10.7 `UnitCapabilityState`

```text
UnitCapabilityState:
  schema / source versions
  configuration / parameter / surface IDs
  accepted_state / receipt / opaque history handle
  q_U / Pz / W_U / Rx
  active/control/constraint summaries
  balance residual or graph
  raw/local tangent, secant or graph
  branch / trust region / predicted event distance
  per-needle opaque state bundle handle
  active needle and N_* summaries
  spring compression / remaining travel / hardstop summaries
  remaining standalone path if applicable
  DamageStore version / handle
  recent events / cascade / reengagement
  energy / quality / uncertainty / certification
  full_unit_resolve_callback_requirement
  callback_reason_codes
```

它是历史相关局部算子状态，不是无记忆能力面。

### 10.8 低维有效条件

局部响应只在以下条件同时成立时使用：

- 分支、活动集和 DamageStore 版本不变；
- 不跨事件括区间；
- 切线/graph 质量合格；
- `k_zz` 和凝聚有效；
- 参考点、坐标、控制模式和 \(P_z\) 参数化一致；
- 增量位于 trust region；
- 表面/参数/状态未陈旧；
- 请求仍在 x/z 子空间。

### 10.9 强制完整回调

任一条件触发完整 B 重求：

- 接触、滑移、迁移、材料、强度、释放、再挂接或硬限位事件；
- 活动集、分支或 DamageStore 变化；
- graph 非唯一、切线不可用/奇异；
- 超出 trust region；
- 快照陈旧；
- 接近域/碰撞/几何质量边界；
- 需要逐针裕度、损伤冲突、级联或准确作用点；
- C 请求 y/转动/rocking；
- 控制模式或路径方向变化；
- callback flag 为真。

### 10.10 剩余行程语义

- 独立弹簧：
  \[
  r_{s,i}^{\rm remain}=4-\delta_{s,i}\ {\rm mm}.
  \]
- 刚性 mount：`not_applicable`，不是无穷大；
- standalone 拖拽余程：只对同一 100 mm 路径定义；
- C 整爪搜索余程/上限尚未固定，不能用 standalone 余程替代；
- 当前无承载但可继续搜索时保留 `DETACHED_RECOVERABLE` 和原始路径。

---

## 11. 参数/模型状态、验证矩阵、风险、未决问题与关闭条件

### 11.1 参数和模型状态分类

| 类别 | 当前状态 | 安全处理 |
|---|---|---|
| 工程固定几何/工况 | fixed/fixed_set/fixed_range | 严格校验，不静默改写 |
| A/B accepted 机理语义 | accepted input | 原样继承所有权、方向、事件和事务 |
| 集成坐标/事务/schema | accepted | 由本文件和公共合同正式冻结 |
| 材料/表面/损伤参数 | unresolved | 版本化 ID 或 unavailable |
| 数值配置 | unresolved | `numerical_config_id`，通过收敛研究关闭 |
| 能力特征阈值 | unresolved | 原始曲线优先，`feature_config_id` |
| C rocking/6D | unsupported | 显式拒绝，未来版本扩展 |
| 源代码和实验 | not validated in this run | 不把理论接受写成实现/实验通过 |


### 11.1.1 证据和知识迁移边界

| 来源层 | 可用于本模型的内容 | 不得迁移的内容 |
|---|---|---|
| 工程事实 1.0.0 | 坐标、扫描集合/范围、加载、运动、损伤边界、输出和排除项 | 未决量的唯一数值 |
| `A_TO_B 1.0.0 accepted` | A embedded 入口、`A_on_B`、状态所有权、事件、graph、损伤和事务语义 | C/B 重建 A 本构 |
| `B_MODULE_CONTEXT 0.3.0 accepted` | B1/B2/B3 已接受方程、趋势证据边界、验证矩阵和未决项 | 历史章节中的“B3 后续”时态 |
| B 上下文已审查文献 | 部分接触、收益饱和、过硬/过软竞争、失效后再挂接和渐进脱附的趋势解释 | 论文样机的具体力、刚度、概率、固定行程或搜索阈值 |
| 通用数学/力学/事务知识 | 坐标运输、功不变、残量分块、冲突图和原子事务的集成表达 | 升级为材料证据或工程固定事实 |

本轮不重新检索论文，不新增材料分支，也不把理论合同接受写成代码或实验验证。

### 11.2 集成验证矩阵

下列为实现必须执行的测试；状态均为“规范已定义，待实现验证”，除非注明继承的解析检查。

| ID | 测试构造 | 关键检查 | 预期 |
|---:|---|---|---|
| V01 | 全部允许阵列尺寸/针距 | 数量、质心、间距、ID 唯一 | 规则格点闭合 |
| V02 | 两种梯度、全部 \(n_x\) | \(L\sin\alpha\)、基座正反算 | 球心/基座共面闭合 |
| V03 | `2×5` 与 `5×2` 同表面 | 有向分离、活动集、wrench | 独立结果，不旋转表面 |
| V04 | 相同 trial 重复调用 | 状态/损伤/能量/事件版本 | 完全无副作用 |
| V05 | 逐针调用顺序/并行置换 | wrench 多重集、事件组、hash | 置换不改变物理解 |
| V06 | 单针外部 B driver 包围 embedded A | \(P_z\) 所有权、wrench 符号 | A 请求无重复预载 |
| V07 | 对称有限弹簧阵列 | 总法向力、对称载荷、\(\delta_s\) | 唯一分支对称 |
| V08 | 完全刚性同高阵列 | graph、秩、零空间 | 不伪造唯一等载 |
| V09 | 一针先接触/多针后接触 | O/N/G/L、载荷集中 | 真实部分接触 |
| V10 | 弹簧 0/内部/4 mm/离开 | 无拉力、硬限位事件、余程 | 分支合法且不穿越 |
| V11 | 光滑分支有限差分 | raw/凝聚切线、参考点 | 有效域内一致 |
| V12 | 接触/滑移/硬限位事件差分 | tangent status | 不跨事件冒充光滑切线 |
| V13 | 同时事件与调用顺序交换 | fraction/group/后侧状态 | 同一事件组或明确非唯一 |
| V14 | 一针失效但余针可承载 | \(\Delta W_i\)、共同平衡 | 首刺不等于单元失败 |
| V15 | 连续级联三针 | 同位置多轮、状态哈希 | 稳定或明确终止 |
| V16 | DamageStore 非冲突/冲突/写读依赖 | 协调、全阵列重求 | 无最后写者覆盖 |
| V17 | prepare/commit 各阶段故障 | 全部版本、路径、损伤 | 原子回滚 |
| V18 | 释放—回弹—再挂接 | 路径/时间、面片/损伤、\(\delta_s\) | 不重置、不恢复损伤 |
| V19 | 长程 100 mm | 最终坐标、时间、历史收据 | 精确 100 mm/100 s |
| V20 | 作用—反作用和参考点运输 | 力矩、功不变 | 坐标/wrench 正确 |
| V21 | contact/actuator/control/constraint 分栏 | 整爪装配 | 不漏算/不重复 |
| V22 | 作用点边界 | 零力、自由力偶、平面平行 | 不伪造压力中心 |
| V23 | C 四单元 event fraction | 全局最小、四单元重调 | 不缩放旧响应 |
| V24 | 跨单元 DamageStore 冲突 | 联合协调和全局提交 | 调用顺序无覆盖 |
| V25 | rocking 请求 | 真实转动输入 | 明确 `KINEMATIC_MODE_UNSUPPORTED` |
| V26 | 错误注入 | 各失败代码 | 物理/未认证/数值/事务分离 |
| V27 | 能量审计 | 外功、储能、耗散、残量 | 数值误差不作材料耗散 |
| V28 | 低维能力 trust region | 小增量/跨事件对照 | 分支内可用，跨事件强制回调 |

B1 accepted 上下文曾给出公式级几何闭合残差；本集成不把该结果升级为求解器实现验证。

### 11.3 风险登记

| 风险 | 后果 | 当前控制 |
|---|---|---|
| A 刚性 graph 未实现或仅给代表值 | 刚性阵列非唯一响应被伪装 | graph unavailable 时禁止认证 |
| 真实 CAD 不闭合梯度基座偏置 | 纯针尖承载构型不可装配 | 进入 CAD/碰撞关闭条件 |
| 材料/表面参数缺失 | 排序和绝对值不可信 | 明确 unavailable，不隐藏默认 |
| 数值事件带不当 | 抖振、错序或漏事件 | 原始量+括区间+Zeno 测试 |
| DamageStore 跨单元并发 | 顺序依赖和部分损伤提交 | opaque 联合协调+全局原子提交 |
| 能量 convention 不统一 | 误把残量当耗散 | convention ID 和分栏账本 |
| 低维能力被当全局极限面 | C 跨事件错误外推 | trust region+强制 callback |
| `rocking=on` 被坐标旋转伪装 | 针级接触和碰撞错误 | 明确 unsupported 和防伪测试 |
| 主动推力在 C 重复装配 | 法向载荷双算 | `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1` |
| 长程历史存储/重放不足 | 事件和损伤不可审计 | opaque 完整历史+receipt 链 |
| 集合值代表值选择依赖针 ID | 物理结果顺序依赖 | 返回 graph/分支集合，ID 仅审计 |
| 实验只看偶然峰值 | 过拟合 | 保留原始曲线、持续和事件统计 |

### 11.4 未决问题与关闭条件

#### A. 工程输入与扫描

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 弹簧刚度离散点 | 扫描成本和最优窗口 | 接受 0.1–2.0 N/mm 范围参数 | 参数扫描计划审查 |
| 单元 \(P_z\) 离散点 | 平衡/载荷共享 | 接受 0.5–2 N 范围参数 | 实验/扫描计划 |
| 砂纸目数集合 | 表面类别对比 | surface ID 可扩展，不固定集合 | 实验材料清单 |
| 随机样本数 | 统计置信 | realization 独立保存 | 统计功效/收敛分析 |
| 二元成功阈值/综合评分 | 方案筛选 | 不输出固定判据 | 验证方案正式批准 |

#### B. 材料、表面与损伤

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 高碳钢 E、屈服、断裂 | 梁/强度响应 | 参数 ID 或 unavailable | 牌号/试验 |
| 摩擦系数 | 粘滑和能力 | surface/contact 参数包 | 实验/文献标定 |
| 局部接触刚度 | 载荷共享和切线 | A 模型版本 | 接触标定 |
| 表面 PSD/分布/相关长度 | 阵列方向和随机性 | A1 realization 接口 | 测量/合成验证 |
| 局部强度和损伤演化 | 失效/再挂接 | A damage model ID | 材料试验 |
| DamageStore 核/协调规则 | 并发损伤 | A opaque coordinator | 冲突测试和物理审查 |

#### C. CAD 与制造

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 锥段、针杆、安装座真实几何 | 禁止碰撞 | geometry ID；缺失不可认证 | CAD 导入和包络测试 |
| 梯度阵列安装孔/滑块布局 | 可装配性 | 基座反算保留真实偏置 | 机械设计闭合 |
| 回差、位置/角度误差 | 实际载荷共享 | error model disabled/unavailable | 测量分布与版本模型 |
| 执行器真实作用线 | C 力矩记账 | 理想广义力，无 CAD 力矩 | 机构定义和合同升级 |

#### D. 模型、graph 和事务实现

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 刚性 graph 数据结构 | 非唯一/退化 | handle 或 unavailable | 联合查询和序列化测试 |
| 非单调 normal graph 延续 | 分支选择 | 明确 nonunique/continuation config | 全局括区间与验证 |
| A 能量 convention | 能量审计 | convention ID | 端到端功测试 |
| 原子持久层 | 部分提交风险 | prepare/commit/rollback 合同 | 故障注入与恢复测试 |
| 跨四单元损伤协调服务 | C 事务 | C 组织，A/B 决定物理 | 并行置换与固定点测试 |

#### E. 数值配置

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 初始/最小/最大位移步长 | 事件定位/成本 | numerical config | 步长收敛 |
| 力/位置/graph 容差 | 平衡认证 | 显式版本 | 解析/网格/实验验证 |
| 同时事件/级联容差 | 事件分组 | 保留原始括区间 | 敏感性研究 |
| Newton/线搜索/信赖区 | 收敛 | 配置化 | 回归矩阵 |
| 最大损伤/级联轮 | Zeno 防护 | 数值安全阈值 | 压力测试 |
| 浮点确定性策略 | 重放 | manifest | 跨平台测试 |
| 能量积分容差 | 认证 | 分栏残量 | 数值收敛 |

#### F. 能力特征

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| 峰值持续比例 \(\rho\) | 持续能力 | feature config | 实验目标 |
| 窗口 \(w\)/平台阈值 | 搜索停止候选 | 原始曲线优先 | 单元实验回推 |
| trust region | C 局部预测 | 保守 callback | 有限差分/回调测试 |
| 统计汇总方法 | 方案排序 | realization 可追溯 | 统计方案批准 |

#### G. C 接口能力

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| `rocking=on` 真实转动 | 偏心承载 | unsupported | B 六维扩展 |
| 局部 y/完整 6D | C 全局运动 | unsupported | 运动/切线/碰撞扩展 |
| C 搜索停止阈值 | C1 | B 只返回候选能力 | 单元仿真/实验反推 |
| C 最大搜索距离 | C1 | 不沿用 100 mm | C1 正式确定 |
| C 全局作用点/执行器模型 | 力矩装配 | contact-only 规则 | 机构/合同升级 |

#### H. 实现与实验验证

| 未决项 | 影响 | 当前安全处理 | 关闭条件 |
|---|---|---|---|
| A/B 实现级自动测试 | 理论无法执行 | 不宣称实现通过 | V01–V28 自动化 |
| 真实表面测量 | 参数真实性 | realization version | 测量质量审查 |
| 直线模组实验趋势 | 方案排序验证 | 输出原始曲线 | 趋势/排序比较 |
| 允许误差范围 | 验证判定 | 不固定 | validation plan |
| 长程重放/存储 | 审计 | receipt/hash schema | 100 mm 压力测试 |

### 11.5 关闭结论

本正式集成已关闭 B1/B2/B3 的语义重复、状态所有权、参考点、功方向、主动推力、事件事务和 C 嵌入提交污染问题；未关闭项均保持参数化、不可用或显式能力缺口。没有开始 C 子模块，也没有生成新的工程事实。

---

## 12. 公共 B→C 接口

以下 `BEGIN/END B_TO_C_PUBLIC_CONTRACT` 标记之间的正文是 C 可独立使用的稳定公共合同，并与 `B_TO_C_CONTRACT.md` 中同名标记块逐字一致。

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

# 从粗糙形貌到整机承载：爪刺啮合机理的因果链形式化推导

**文档性质：** 因果链重写版、闭合修正提案

**版本：** 0.2.0-proposed

**日期：** 2026-07-17

**主要用途：** 论文方法章节、方程审查、求解器实现交接

**配套讲解稿：** [一根爪刺如何把“划过墙面”变成“整机承载”](MECHANISM_DERIVATION_TUTORIAL.md)

> **规范身份。** 本稿不是 accepted 理论。现行正式权威仍是
> [SYSTEM_INTEGRATED_MODEL 1.0.0](../system/SYSTEM_INTEGRATED_MODEL.md)、
> [A_INTEGRATED_MODEL 1.0.0](../modules/A_INTEGRATED_MODEL.md)、
> [B_INTEGRATED_MODEL 1.0.0](../modules/B_INTEGRATED_MODEL.md)、
> [C_INTEGRATED_MODEL 1.0.0](../modules/C_INTEGRATED_MODEL.md) 以及
> [A_TO_B 1.0.0](../interfaces/A_TO_B_CONTRACT.md)、
> [B_TO_C 1.0.0](../interfaces/B_TO_C_CONTRACT.md)。
> 本稿把独立复核已经指出的闭合修正和证据反审计提出的结构性补充组织成一份下一版候选推导；任何内容若要进入 accepted，仍需版本化 amendment、实现验证和正式接受。

> **证据边界。** 2026-07-17 反审计以 29 张证据卡、提取审计和关键图为输入，没有重新核验全部源 PDF 或 ZIP。审计未发现本 proposed 主链中尚未处理的明确文献冲突，但这不等于参数、代码或实验已经闭合。文献在本稿中只提供定性支持、结构性补充和验证建议；具体数值、拟合式、阈值与硬件模型不得直接迁移。
> 反审计的主审快照是提交 36c3c53 中的 0.1.0-proposed；报告内引用的 FORMAL 行号属于该历史快照，不对应本 0.2.0 文件的现行行号。

## 摘要

爪刺在粗糙墙面上的承载不是“针尖碰到凸起”这一个瞬间，而是一条连续的因果链：表面数据先限定哪些微结构可信；有限尺寸针尖从可信形貌中筛出可达支持；单边接触和摩擦判断支持是否真正受力；针梁与安装柔顺把运动转成逐渐增长的反力；释放、滑移、损伤和再接触把光滑力曲线切成历史相关分支；多刺阵列通过共同位姿与总平衡自然形成不等载和事件后重分配；四个阵列的力与力矩经参考点运输后，才组成整机预紧和偏心承载问题。

本文按这条物理发生顺序推导模型，而不是把几何、摩擦、梁、阵列和系统公式并列罗列。完全闭合的开发基线为 \(\mathsf M_0=\) finite-tip geometry + Signorini–Coulomb + beam/mount + no_damage。材料扩展 \(\mathsf M_1\) 只有在局部化运动学、接触量到材料量的尺度桥、模式身份、功共轭、参数来源和卸载/重载规则全部给出后才可启用。系统层提出刚性共体边界 C-R 作为论文主线，并把四独立法向执行器边界 C-I 保留为互斥备选；二者目前都不能静默覆盖 accepted C。由于 B_TO_C 1.0.0 只认证单元局部 x 与全局 Z 平移，非零 \(+X\)、\(45^\circ\) 和 rocking 的正式在线求解仍必须在物理推进前安全拒绝，\(F_{\rm crit}\) 保持 unavailable，而不是置零。

**关键词：** microspine；粗糙表面；有限球尖；单边接触；Coulomb 摩擦；载荷共享；非光滑事件；历史变量；wrench；准静态稳定性

---

## 0. 先给结论：模型保留什么，补什么

### 0.1 中央研究问题

本文只回答一个问题：

> 给定一块有证据边界的粗糙表面、一根有限尺寸爪刺及其结构安装、一个多刺阵列和一个四单元十字机构，外部规定运动怎样沿一条可审计路径变成承载力、力矩、释放、重分配和最终能力？

这个问题不能由单一“抓附系数”回答，因为同一个瞬时位置可能对应开放、刚接触、粘着、滑移、释放、再挂接或损伤后的不同历史分支。

### 0.2 贯穿全文的因果链

\[
\boxed{
\begin{aligned}
\text{表面证据}
&\rightarrow \text{有限尖端可达支持}\\
&\rightarrow \text{受载单边接触}\\
&\rightarrow \text{摩擦稳定与结构变形}\\
&\rightarrow \text{单刺反力和事件}\\
&\rightarrow \text{阵列共同平衡与重分配}\\
&\rightarrow \text{四单元 wrench 装配}\\
&\rightarrow \text{稳定可达的整机能力}.
\end{aligned}
}
\]

每个箭头都对应一个必须闭合的桥：

| 从哪里到哪里 | 所遇问题 | 采用机理 | 机理来源 | 必须输出 |
|---|---|---|---|---|
| 表面到支持 | 粗糙度指标不能说明针尖能否到达 | 有限球包络、球冠合法性、体部净空 | 几何非穿透 | 候选支持、法向、质量与域 |
| 支持到受力 | “碰到”不等于“承载” | Signorini 单边接触 | 不可穿透与无拉力接触 | gap、法向乘子、开闭状态 |
| 受力到稳定 | 法向力不能自动阻止切向运动 | 三维 Coulomb 锥与最大耗散 | 摩擦功和锥约束 | 粘着/滑移、切向力、耗散 |
| 运动到力增长 | 刚体接触不能解释渐进加载 | 梁、单边安装弹簧与共同平衡 | 结构力学和兼容条件 | 位移、wrench、储能、行程 |
| 单刺到阵列 | 逐针峰值相加忽略共同运动 | B 层全阵列平衡 | 牛顿平衡与虚功 | 非等载分配、事件后重求 |
| 阵列到整机 | 合力相消不代表力矩闭合 | wrench 运输与六维平衡 | 刚体力学和功不变 | 整机力、力矩、姿态、反力 |
| 一步到整条路径 | 接触切换和损伤使响应不光滑 | 事件定位、回滚、原子提交 | 非光滑延拓与事务语义 | 可重放历史、事件和能力 |

### 0.3 本轮判断

证据反审计支持保留以下核心主链：

1. 有限针尖与三维形貌，而非点尖和单一粗糙度；
2. Signorini–Coulomb 接触，而非经验挂接力；
3. 梁/安装柔顺与共同兼容，而非逐针指定力；
4. 事件后全量重平衡，而非固定换载权重；
5. 历史、释放和再挂接，而非无记忆能力面；
6. 对置预紧与完整 wrench，而非只看面内合力。

需要补强的不是另一套核心方程，而是六类桥接合同：表面生成/采集、挂接阶段术语、释放—再接触路径、\(\mathsf M_1\) 材料桥、阵列诊断、执行器到 \(s\)/主动 wrench/功的映射，以及与之对应的负例和事件级验证。

### 0.4 三条模型线

| 模型线 | 当前身份 | 可做什么 | 不能声称什么 |
|---|---|---|---|
| \(\mathsf M_0\) | 本稿闭合开发基线 | 几何、接触、摩擦、梁/安装、事件、阵列平衡 | 材料破坏定量预测 |
| \(\mathsf M_1\) | 条件扩展 | 在全部材料桥门控闭合后描述指定模式 | 缺桥时不得以容量折减器冒充材料本构 |
| C 偏心承载 | 理论方程已定义、在线接口被阻断 | 解析推导、接口缺口和安全拒绝测试 | B 1.0 下的非零 \(+X/45^\circ\)/rocking 或正式 \(F_{\rm crit}\) |

---

## 1. 故事的起点：一张粗糙度表还不是一面可计算的墙

### 1.1 物理域与状态

墙面、单刺、阵列和整机分别由 A、B、C 三层拥有。一次路径上的已接受状态记为

\[
\mathcal S_n=
\left(
\mathcal G,\,
\mathcal H_{A,n},\,
\mathcal H_{B,n},\,
\mathcal H_{C,n},\,
\mathcal D_n,\,
\mathcal I_n
\right),
\]

其中 \(\mathcal G\) 是不可变几何/表面 realization，\(\mathcal H_A,\mathcal H_B,\mathcal H_C\) 是各层历史，\(\mathcal D\) 是共享 DamageStore，\(\mathcal I\) 保存版本、哈希、参考点和提交收据。模型是历史相关算子

\[
\boxed{
\mathcal S_{n+1}^{trial}
\in
\mathcal G_{\rm mech}
\left(
\mathcal S_n,\Delta\chi,\Theta
\right),
}
\]

而不是只依赖当前位置的函数。只有全局接受后，trial 才能成为 \(\mathcal S_{n+1}\)。

### 1.2 为什么采用准静态路径

本模型研究的是受控慢速搜索、预紧和拖曳。相对运动的主要时间尺度若远大于结构振动衰减、接触调整和控制内环时间尺度，可在每个已定位事件之间忽略惯性，求

\[
\boxed{
\mathbf r_{\rm force}=\mathbf0,
\qquad
\mathbf r_{\rm moment}=\mathbf0.
}
\]

“准静态”不表示响应光滑，也不表示事件没有瞬时跳变。它只表示每个事件前、事件点和事件后一侧都由静力平衡或 admissible graph 连接；滑移起始、释放和同位置级联仍需专门定位。若冲击、反弹、显著惯性、速率相关材料或控制器动态与接触时间尺度同阶，本模型应返回 DYNAMIC_EXTENSION_REQUIRED，而不是调大数值阻尼继续。

时间不是本征独立变量。只有外部协议提供速度或时间戳时，才建立 \(t\leftrightarrow\chi\) 映射；否则路径位置和事件顺序完整保留，时间为 unavailable。

### 1.3 SurfaceGenerationAndAcquisitionContract

表面必须先成为带证据边界的 realization，才能进入接触求解。本文提出如下非规范性输入合同。

共同字段至少包括：

- 坐标、单位、区域尺寸、材料方向和原始身份哈希；
- PSD 定义、可信波数带、方向谱、roll-off 和非高斯高度边际；
- 宏观孔洞、边缘、裂隙或污染等缺陷标签；
- 去趋势、插值、滤波、窗函数、缺失掩膜和可回放处理链；
- 扫描尺度与 \(h_{\rm rms}(L)\) 或等价尺度曲线；
- 多位置、方向、批次、留出区及技术内/技术间不确定带；
- 50/100 \(\mu{\rm m}\) 针尖相对可信最短波长的覆盖裕度。

合成表面分支还需保存 FFT 归一化、Hermitian 配对、零模、随机种子、周期域、目标/回算 PSD、方差与实值误差。实测分支还需保存仪器原理、探针形状或 MTF/SNR、原生点距、配准误差、陡坡漏检、窄谷不可达和各方向可信截止。原生点距不自动等于物理分辨率；插补值不自动成为真实形貌；多数技术的一致也不自动成为“真值”。

这些字段只证明“输入在哪些尺度上可用”，不证明“这里能挂住”。

### 1.4 表面 realization

对高度场

\[
\Omega_h=\{(x,y,z):z\le h(x,y)\},
\]

采用约定

\[
C_h(\mathbf q)
=
\int R_h(\mathbf r)e^{-i\mathbf q\cdot\mathbf r}\,d^2\mathbf r,
\qquad
\langle h^2\rangle
=
\frac1{(2\pi)^2}\int C_h(\mathbf q)\,d^2\mathbf q.
\]

PSD 只在合同声明的可信波数带内解释。高度场、点云或三角网格最终都应提供外正内负的欧氏有符号距离查询 \(\phi_\Omega(\mathbf x)\)、域状态和质量状态。

### 1.5 有限球尖先筛掉“看得见但够不着”的纹理

针尖不是数学点。半径 \(R_t\) 的完整球在平面位置 \((x_c,y_c)\) 上不穿透表面的最低合法球心高度为

\[
\boxed{
H_{R_t}(x_c,y_c)
=
\sup_{\rho\le R_t}
\left[
h(u,v)+\sqrt{R_t^2-\rho^2}
\right],
}
\]

\[
\rho^2=(u-x_c)^2+(v-y_c)^2.
\]

竖直可行裕量为

\[
g_{R_t}^{env}=c_z-H_{R_t}(x_c,y_c).
\]

跨几何后端用于互补求解的规范间隙写成

\[
\boxed{
g_{R_t}^{(d)}(\mathbf c)=\phi_\Omega(\mathbf c)-R_t.
}
\]

两者应给出一致的可行域和零接触集，但不要求数值相同。这个球包络就是“有限针尖对粗糙度的几何滤波器”：比针尖更窄、更深且不可达的谷，不应被当作支持。

### 1.6 球冠、支持和体部净空

针尖只有有限球冠可承载。对当前针轴 \(\mathbf a_t\)、球冠边界 \(\zeta_b\)，候选支持 \(\mathbf p_j\) 必须满足

\[
(\mathbf p_j-\mathbf c_t)\cdot\mathbf a_t
\ge \zeta_b-\epsilon_{\rm cap}.
\]

接触法向为

\[
\boxed{
\mathbf n_j=
\frac{\mathbf c_t-\mathbf p_j}
{\|\mathbf c_t-\mathbf p_j\|}.
}
\]

支持驻定条件不是充分条件。光滑图表上还要检查局部最小二阶条件，并与邻域内所有合法候选比较；三角网格要分别比较面、边和顶点。并列最小值保留为多支持 graph，不能平均成一个伪法向。

锥段、针杆和安装座的净空为

\[
g_k(T)
=
\min_{\mathbf x\in K_k(T)}
\phi_\Omega(\mathbf x)-\delta_{{\rm clr},k}>0.
\]

这些是硬可行性条件，不产生新的承载力。若体部先碰撞，纯球尖啮合模型应返回 BODY_COLLISION_INVALID，而不是把碰撞偷换成额外抓附。

### 1.7 第一处术语分栏

本稿不再用“挂接”包办所有阶段：

\[
\boxed{
\text{geometric candidate}
\rightarrow
\text{loaded contact}
\rightarrow
\text{frictionally stable}
\rightarrow
\text{load-bearing}
\rightarrow
\text{released/reengaged}.
}
\]

- geometric candidate：几何上可达，但可为零力；
- loaded contact：单边接触乘子为正；
- frictionally stable：当前切向需求在摩擦允许集内；
- load-bearing：对声明任务方向产生有效阻力或 wrench；
- released/reengaged：历史路径上的释放和再次受载。

这组分栏把“发现一个凸起”和“形成任务承载”之间缺失的故事补上。

---

## 2. 候选怎样变成受力：A 层单刺接触

### 2.1 针尖姿态必须先闭合

给定背板位姿 \(T_B\)，刚性根部位置为 \(\mathbf r_{0,\rm rigid}(T_B)\)。若存在轴向压缩量 \(\delta_s\)，

\[
\mathbf r_0
=
\mathbf r_{0,\rm rigid}(T_B)-\delta_s\mathbf a_0,
\qquad
\mathbf c_0=\mathbf r_0+L\mathbf a_0.
\]

令 \(\mathbf R_0\mathbf e_1=\mathbf a_0\)，并把梁转角明确为全局旋转向量 \({}^G\boldsymbol\theta_b\)。闭合姿态采用全局左乘：

\[
\boxed{
\mathbf R_t
=
\exp([{}^G\boldsymbol\theta_b]_\times)\mathbf R_0,
}
\]

\[
\boxed{
\mathbf c_t=\mathbf c_0+\mathbf u_b,
\qquad
\mathbf a_t
=
\exp([{}^G\boldsymbol\theta_b]_\times)\mathbf a_0.
}
\]

小转角下

\[
\mathbf a_t
\approx
\mathbf a_0+{}^G\boldsymbol\theta_b\times\mathbf a_0.
\]

这是几何 P0 的 proposed 闭合：不能把已经用全局分量表示的轴再当成局部向量重复旋转。

### 2.2 单边接触回答“能推，不能拉”

第 \(j\) 个支持上，墙面对针的力定义为

\[
\boxed{
\mathbf f_j
=
\lambda_{n,j}\mathbf n_j
+\mathbf T_j\boldsymbol\lambda_{t,j},
}
\]

其中 \(\mathbf T_j=[\mathbf t_{1j}\ \mathbf t_{2j}]\)。刚性局部接触满足

\[
\boxed{
g_j\ge0,\qquad
\lambda_{n,j}\ge0,\qquad
g_j\lambda_{n,j}=0.
}
\]

这三个条件同时覆盖开放、刚接触和受压接触：

- \(g_j>0\Rightarrow\lambda_{n,j}=0\)；
- \(\lambda_{n,j}>0\Rightarrow g_j=0\)；
- \(g_j=\lambda_{n,j}=0\) 是事件边界，不应被强行判成某一侧。

若未来有独立标定的接触压缩 \(c_n(\lambda_n)\)，可写

\[
g_j^{eff}=g_j^{geom}+c_{n,j}(\lambda_{n,j}),
\quad
c_n(0)=0,\quad
\frac{dc_n}{d\lambda_n}\ge0.
\]

\(\mathsf M_0\) 取 \(c_n=0\)。非穿透接触、允许穿透的软接触和材料黏附必须使用互斥 model ID，不得把三种语义混入同一 gap。

### 2.3 摩擦回答“受压以后能否留住”

三维 Coulomb 条件为

\[
\|\boldsymbol\lambda_{t,j}\|
\le
\mu_j\lambda_{n,j}.
\]

令二阶锥

\[
\mathcal L_3
=
\{(x_0,\mathbf x):x_0\ge\|\mathbf x\|\},
\]

\[
\boldsymbol\chi_j
=
\begin{bmatrix}
\mu_j\lambda_{n,j}\\
\boldsymbol\lambda_{t,j}
\end{bmatrix},
\qquad
\boldsymbol\psi_j
=
\begin{bmatrix}
g_j^{eff}/\mu_j+\|\Delta\mathbf s_j\|\\
\Delta\mathbf s_j
\end{bmatrix}.
\]

接触、摩擦锥和最大耗散可统一写为

\[
\boxed{
\boldsymbol\chi_j\in\mathcal L_3,\qquad
\boldsymbol\psi_j\in\mathcal L_3,\qquad
\boldsymbol\chi_j^\mathsf T\boldsymbol\psi_j=0.
}
\]

真实滑移时

\[
\boxed{
\boldsymbol\lambda_{t,j}
=
-\mu_j\lambda_{n,j}
\frac{\Delta\mathbf s_j}{\|\Delta\mathbf s_j\|}.
}
\]

因此 \(\mu\) 是局部本构参数，不是实验中任意切/法向力比；表面坡度、支持法向、梁姿态和载荷路径都会改变表观力比。

### 2.4 滑移必须相对局部接触面客观计算

\[
\mathbf P_{t,j}
=
\mathbf I-\mathbf n_j\mathbf n_j^\mathsf T,
\]

\[
\Delta\mathbf s_j^G
=
\mathbf P_{t,j}^{n+1/2}
\left[
\Delta\mathbf c_t
+\Delta{}^G\boldsymbol\theta_b
\times(\mathbf p_j-\mathbf c_t)^{n+1/2}
\right],
\]

\[
\boxed{
\Delta\mathbf s_j
=
\mathbf T_{j,n+1/2}^\mathsf T\Delta\mathbf s_j^G.
}
\]

支持点在表面上迁移但 \(\Delta\mathbf s_j=0\) 可以是滚动；摩擦锥达到边界也不自动等于滑移已经发生。只有真实非零客观滑移才提交摩擦耗散。

### 2.5 单刺接触输出是完整 wrench

\[
\mathbf F_c=\sum_j\mathbf f_j,
\]

\[
\boxed{
\mathbf M_c^{c_t}
=
\sum_j(\mathbf p_j-\mathbf c_t)\times\mathbf f_j
+\sum_j\mathbf m_j^{local}.
}
\]

首版点接触取 \(\mathbf m_j^{local}=\mathbf0\)。接触端口输出为

\[
\mathbf W_c=
\begin{bmatrix}
\mathbf F_c\\
\mathbf M_c^{c_t}
\end{bmatrix}.
\]

到这里，模型只回答了“当前构型若受力，力在哪里、朝哪里”。下一步还要解释：为什么拖动一点以后力会增长，而不是瞬间得到一个任意反力。

---

## 3. 力为什么会长出来：结构柔顺与 \(\mathsf M_0\) 单刺闭合

### 3.1 梁把接触力变成可测位移

圆截面参数为

\[
A=\frac{\pi d^2}{4},\quad
I=\frac{\pi d^4}{64},\quad
J=\frac{\pi d^4}{32},\quad
G=\frac{E}{2(1+\nu)}.
\]

定义

\[
\mathbf P_\parallel=\mathbf a_0\mathbf a_0^\mathsf T,
\quad
\mathbf P_\perp=\mathbf I-\mathbf P_\parallel,
\quad
\mathbf S=[\mathbf a_0]_\times.
\]

Euler–Bernoulli 柔顺关系为

\[
\boxed{
\begin{aligned}
\mathbf u_b={}&
\frac{L}{EA}\mathbf P_\parallel\mathbf F_c
+\frac{L^3}{3EI}\mathbf P_\perp\mathbf F_c
-\frac{L^2}{2EI}\mathbf S\mathbf M_c^{c_t},\\
{}^G\boldsymbol\theta_b={}&
\frac{L^2}{2EI}\mathbf S\mathbf F_c
+\frac{L}{EI}\mathbf P_\perp\mathbf M_c^{c_t}
+\frac{L}{GJ}\mathbf P_\parallel\mathbf M_c^{c_t}.
\end{aligned}
}
\]

记 \(\boldsymbol\eta_b=[\mathbf u_b,{}^G\boldsymbol\theta_b]\)，则

\[
\boxed{
\mathbf r_b
=
\boldsymbol\eta_b-\mathbf C_b\mathbf W_c=\mathbf0,
\qquad
U_b=\frac12\mathbf W_c^\mathsf T\mathbf C_b\mathbf W_c.
}
\]

如果细长比、剪切效应、转角或几何刚度超出模型有效域，应切换经验证的 Timoshenko/共回转分支或返回 STRUCTURAL_MODEL_OUT_OF_RANGE，不能让小变形公式无限延伸。

### 3.2 安装弹簧只压不拉

令轴向压缩需求

\[
Q_s=-\mathbf a_0\cdot\mathbf F_c.
\]

权威分支图为

\[
\boxed{
\begin{array}{lll}
\text{RIGID\_LOCKED:}
&\delta_s=0,
&Q_s\text{ 由约束反力承担};\\[1mm]
\text{AT\_ORIGINAL\_LENGTH:}
&\delta_s=0,
&F_s=0,\ Q_s=0;\\[1mm]
\text{COMPRESSING:}
&0<\delta_s<\delta_{\max},
&Q_s-k_s\delta_s=0;\\[1mm]
\text{HARD\_STOP:}
&\delta_s=\delta_{\max},
&Q_s-k_s\delta_{\max}-r_H=0,\ r_H\ge0.
\end{array}
}
\]

\[
\delta_{\max}=4\ {\rm mm}.
\]

维持接触若要求 \(\delta_s<0\) 或拉簧力，系统必须释放该约束或接触。零位分支不能同时保留正弹簧力；刚性安装也不能用“很大有限刚度”伪装。

### 3.3 接触 resultant 到根截面必须有明确桥

针自由体平衡给出

\[
\mathbf F_r+\mathbf F_c=\mathbf0,
\]

\[
\mathbf M_r^{r_0}
+\mathbf M_c^{c_t}
+(\mathbf c_t-\mathbf r_0)\times\mathbf F_c
=\mathbf0.
\]

内部根截面结果量为

\[
\boxed{
\mathbf F_{\rm sec}=\mathbf F_c,
\qquad
\mathbf M_{\rm sec}
=
\mathbf M_c^{c_t}
+(\mathbf c_t-\mathbf r_0)\times\mathbf F_c.
}
\]

在针局部基 \(\mathbf R_N=[\mathbf a_0\ \mathbf e_b\ \mathbf e_c]\) 中，

\[
{}^N\mathbf F=\mathbf R_N^\mathsf T\mathbf F_{\rm sec},
\qquad
{}^N\mathbf M=\mathbf R_N^\mathsf T\mathbf M_{\rm sec},
\]

\[
\boxed{
\mathbf s_N=[N,V_b,V_c,T,M_b,M_c]^\mathsf T.
}
\]

名义应力监控可写为

\[
\sigma_{ab,\max}
=
\frac{|N|}{A}
+\frac{d/2}{I}\sqrt{M_b^2+M_c^2},
\]

\[
\tau_{ub}
=
\frac{|T|(d/2)}{J}
+\frac{4}{3A}\sqrt{V_b^2+V_c^2},
\qquad
\sigma_{vm}^{ub}
=
\sqrt{\sigma_{ab,\max}^2+3\tau_{ub}^2}.
\]

没有材料牌号、根部几何和强度证据时，只能输出监控量，不能输出认证断针。

### 3.4 \(\mathsf M_0\) 本征问题

固定支持图表、开闭、摩擦和安装分支后，未知量记为

\[
\mathbf y_A
=
[
\boldsymbol\eta_b,\,
\delta_s\ {\rm or}\ r_H,\,
\{\boldsymbol\lambda_j\},\,
\{\boldsymbol\xi_j\}_{chart}
].
\]

闭合方程为

\[
\boxed{
\mathbf0\in
\mathcal R_A(\mathbf y_A)
=
\begin{bmatrix}
\mathbf r_b\\
\mathbf r_s\\
\{\mathbf r_{c,j}\}\\
\{\mathbf r_{geo,j}\}_{chart}
\end{bmatrix},
}
\]

并检查球冠、锥段、针杆、安装座、行程、域和质量条件。\(\mathsf M_0\) 不创建材料损伤；A embedded kernel 也不含主动法向推力。它接收规定背板运动，返回 contact-only wrench、状态、事件和诊断。

### 3.5 standalone 法向力控只是 A 外面的实验包装

单刺独立拖曳时，可在本征核外增加 \(u_z\)，给定 \(u_x\) 和实验推力 \(P_z\)：

\[
\boxed{
\mathbf0
\in
\begin{bmatrix}
\mathcal R_A(\mathbf y_A;u_x,u_z)\\
\mathbf E_Z^\mathsf T\mathbf F_c-P_z
\end{bmatrix}.
}
\]

正拖曳阻力和外功为

\[
\boxed{
R_x=-\mathbf e_x^\mathsf T\mathbf F_c,
\qquad
dW_A=R_x\,du_x-P_z\,du_z.
}
\]

当前工程 standalone 工况取 \(P_z=0.5\ {\rm N}\)，沿同一连续路径最多推进 100 mm；若协议采用 \(1\ {\rm mm/s}\)，时间只由 \(t=\chi/(1\ {\rm mm/s})\) 派生，不因此引入惯性动力学。释放后从当前 accepted 历史继续搜索，不重置位置或损伤。

这个外包装不能被 B 调用来给每根针分配 \(P_z/N\)。A embedded 和 A standalone 共用本征机理，但控制所有者不同；100 mm 和 1 mm/s 也不得迁移成 C 层搜索上限或加载速度。

---

## 4. 啮合怎样结束、又怎样回来：事件、释放与 \(\mathsf M_1\)

### 4.1 力曲线不是一条永远光滑的线

沿路径 \(\chi\) 监控的事件至少包括：

- gap 过零：接触建立或释放；
- 摩擦锥边界与真实滑移起始；
- 支持迁移、并列支持和图表切换；
- 安装弹簧零位、内点和硬限位切换；
- 材料起始、软化端点和针体强度事件；
- 域、碰撞、几何质量和模型有效域边界；
- 再接触与再挂接。

事件函数只定位候选；真正的事件后状态必须切换分支并重新求平衡。

### 4.2 释放是路径，不是把变形瞬间清零

接触释放时，梁和弹簧可能仍储能。把 \(\mathbf u_b,\boldsymbol\theta_b,\delta_s\) 瞬时投影为零，会跳过回弹途中可能发生的扫掠碰撞、再接触和功交换。

安全的外部操作协议应明确：

\[
\boxed{
\text{unload}
\rightarrow
\text{drive-off/unlock}
\rightarrow
\text{reverse-search or lift-off}
\rightarrow
\text{swept collision checks}
\rightarrow
\text{recontact guards}.
}
\]

C/System 编排操作路径，A 负责低层释放、碰撞和再接触事件。若回位路径尚未实现，当前承载分支必须停在释放 pose，保留历史；不能自动回零后继续。

### 4.3 \(\mathsf M_1\) 的共同启用门

材料扩展只有下列项目同时闭合时才可启用：

1. 真实局部位移跳量或局部化运动学 \(\mathbf j_k\)；
2. 与 model ID 匹配的 contact_to_material_bridge；
3. 明确模式：例如 cohesive_interface、continuum_RVE 或 resultant_capacity；
4. 目标材料、来源批次、尺度和参数 provenance；
5. 功共轭、客观性和非负耗散；
6. 软化形状、卸载/重载与残余通道身份；
7. initial_material_state 与接触诱发 DamageStore 分离；
8. 观测算子：实验基距、弹性伸长、裂纹开度、内部损伤坐标不得混名。

这些门缺一时，\(\mathsf M_0\) 仍可执行，但请求的 \(\mathsf M_1\) 分支必须返回 MATERIAL_MODEL_UNAVAILABLE。

### 4.4 软化端点与残余入口不能同名

对面片 \(k\)，若采用线性容量退化候选，

\[
0\le\delta_{d,k}\le\delta_{f,k},
\qquad
0\le\varrho_k<1,
\]

\[
q_k(\delta_{d,k})
=
\varrho_k+(1-\varrho_k)
\left(1-\frac{\delta_{d,k}}{\delta_{f,k}}\right).
\]

令 \(\mathbf z_k\) 为 contact_to_material_bridge 输出的材料驱动量，\(\mathcal C_{0,k}\) 为无损容量集，其规范化利用率为

\[
r_k^0(\mathbf z_k)
=
\inf\{\gamma>0:\mathbf z_k/\gamma\in\mathcal C_{0,k}\}.
\]

演化满足

\[
\dot\delta_{d,k}\ge0,
\quad
q_k-r_k^0\ge0,
\quad
\dot\delta_{d,k}(q_k-r_k^0)=0.
\]

到达 \(\delta_d=\delta_f\) 后坐标冻结：

\[
\boxed{
\varrho_k>0
\Rightarrow
\text{SOFTENING\_COMPLETE/RESIDUAL\_ENTRY},
}
\]

\[
\boxed{
\varrho_k=0
\Rightarrow
\text{ZERO\_CAPACITY\_FAILURE}.
}
\]

在纯 Mode-I 完全张开分离的同一法向黏聚通道中，零容量终态不能继续保留非零法向黏聚牵引。压剪接触、摩擦或其他残余机制可以存在，但必须另列状态、作用对象和功通道。

若 \(\varrho_k>0\)，

\[
\mathbf t_k=\mathbf t_{{\rm res},k}+\mathbf t_{{\rm diss},k},
\]

\[
\dot{\mathcal D}_{m,k}
=
\mathbf t_{{\rm diss},k}\cdot\dot{\mathbf j}_k\ge0,
\qquad
\mathcal P_{{\rm res},k}
=
\mathbf t_{{\rm res},k}\cdot\dot{\mathbf j}_k.
\]

残余功必须被唯一归入可恢复、摩擦/塑性耗散或其他已定义通道。没有残余功规则时，功共轭 cohesive 分支只能取 \(\varrho=0\)；非零残余只能作为未认证 fixture。

若且仅若模型身份确认为线性软化、\(\mathbf j_k\) 与 \(\delta_{d,k}\) 的桥已经闭合，并且 \(A_k,T_{0,k},G_{c,k}^{mix}\) 都属于目标材料和目标尺度，可采用候选关系。其中 \(A_k\) 是物理面片面积，\(T_{0,k}\) 是该模式下的峰值牵引尺度，\(G_{c,k}^{mix}\) 是适用混合模态和尺度下的断裂能。

\[
\delta_{f,k}
=
\frac{2G_{c,k}^{mix}}
{(1-\varrho_k)T_{0,k}},
\]

\[
\mathcal D_{m,k}
=
A_k(1-\varrho_k)T_{0,k}
\left(
\bar\delta_{d,k}
-\frac{\bar\delta_{d,k}^2}{2\delta_{f,k}}
\right),
\qquad
\bar\delta_{d,k}=\min(\delta_{d,k},\delta_{f,k}).
\]

这只是一个带明确适用门的候选分支，不是从反审计文献直接识别出的项目本构，也不能由能量面积闭合反推出完整卸载/重载律。

### 4.5 DamageStore 记录物理位置，而不是调用顺序

原始 SurfaceRealization 保持不可变。损伤存在独立版本化 DamageStore 中。创建面片前必须先在兼容空间核内查询既有物理面片；并发写入按 read/write set 和核重叠组成冲突组，由同一材料协调器生成共同 trial 快照。不得按针 ID、线程完成顺序、求和或取最大值覆盖。

如果未来损伤会改变有效支持几何，需要另行定义 DamageGeometryOverlay；在此之前 \(\mathsf M_1\) 不得声称完整覆盖脆性凸体脱落后的新地形。

---

## 5. A 怎样把结果交给 B：唯一端口与作用—反作用

### 5.1 公共方向

A 对 B 的唯一公共 wrench 是单刺 A 子系统对刚性背板 B 的作用：

\[
\boxed{
\mathbf W_{A\rightarrow B}^{G,O}
=
\begin{bmatrix}
\mathbf F_{A\rightarrow B}^{G}\\
\mathbf M_{A\rightarrow B}^{G,O}
\end{bmatrix},
}
\]

\[
\mathbf F_{A\rightarrow B}^{G}=\sum_j\mathbf f_j,
\qquad
\mathbf M_{A\rightarrow B}^{G,O}
=
\sum_j(\mathbf p_j-\mathbf r_O)\times\mathbf f_j.
\]

背板对 A 的作用严格为

\[
\mathbf W_{B\rightarrow A}^{G,O}
=
-\mathbf W_{A\rightarrow B}^{G,O}.
\]

正抓附阻力定义为

\[
\boxed{
R_x=-\mathbf e_x\cdot\mathbf F_{A\rightarrow B}.
}
\]

梁、安装弹簧和硬限位已包含在 A 的净响应中，B 不得再加一次内部反力。

### 5.2 参考点运输与功不变

从 \(O\) 运输到 \(O'\)：

\[
\boxed{
\mathbf F^{O'}=\mathbf F^O,
\qquad
\mathbf M^{O'}
=
\mathbf M^O+(\mathbf r_O-\mathbf r_{O'})\times\mathbf F.
}
\]

对同一刚体运动，

\[
\boxed{
(\mathbf W^{O})^\mathsf T\Delta\boldsymbol\xi^{O}
=
(\mathbf W^{O'})^\mathsf T\Delta\boldsymbol\xi^{O'}.
}
\]

这条功不变关系是判断符号、坐标和参考点是否搬运正确的最强局部检查。只旋转力而漏掉力矩运输，或改变参考点却不改变 twist，都会破坏它。

### 5.3 A_TO_B 仍是正式边界

本稿没有修改 [A_TO_B 1.0.0](../interfaces/A_TO_B_CONTRACT.md)。B 只能调用无副作用 embedded_constitutive_trial，不能直接修改 A opaque 历史、DamageStore 或逐针本构，也不能向 A 请求逐针法向恒力。

---

## 6. 一根针释放以后，其他针为什么会增载：B 层共同平衡

### 6.1 阵列先规定共同几何

规则格点为

\[
\mathbf c_{rc}^{0}
=
\begin{bmatrix}
\left(\frac{n_x-1}{2}-r\right)p\\
\left(c-\frac{n_y-1}{2}\right)p\\
0
\end{bmatrix}.
\]

针轴、长度和基座位置由同一配置唯一生成。实际针长必须同时绑定几何、碰撞、梁、强度和力臂；不能在不同子模型中偷偷使用不同长度。阵列转向时只旋转安装坐标，不能把同一随机表面一起旋转来制造虚假等价。

### 6.2 B 1.0 的共同运动

当前认证单元坐标为

\[
\boxed{
\mathbf q_U=
\begin{bmatrix}
u_x\\u_z
\end{bmatrix},
\qquad
\Delta\boldsymbol\xi_U
=
\mathbf H_U\Delta\mathbf q_U.
}
\]

所有针从同一 accepted 单元快照、同一 DamageStore 快照和同一共同背板增量出发调用 A。单元 contact-only wrench 为

\[
\boxed{
\mathbf W_U^{G,O_A}
=
\sum_{i=1}^{N}\mathbf W_i^{G,O_A}.
}
\]

它不包含主动推力、x 位移控制反力、y/转动约束反力或 C 外载。

### 6.3 恒推力外层的平衡

在 UX_PZ_BALANCED 模式，给定 \(u_x\) 和单元主动推力 \(P_z\)，B 求共同 \(u_z\)：

\[
\boxed{
r_z(u_z;u_x,P_z)
=
\mathbf E_Z^\mathsf T
\sum_i\mathbf F_i(u_x,u_z)-P_z=0.
}
\]

退化分支写为

\[
\boxed{
0\in\mathcal N_U(u_x,u_z)-P_z.
}
\]

在 PRESCRIBED_XZ_RESIDUAL 模式，\(u_x,u_z\) 都由外层规定，B 只返回同一残量或 graph 距离；残量未闭合时不能称为平衡。

### 6.4 载荷共享不是额外公式，而是平衡的结果

设两根针在共同位移 \(u\) 下分别有

\[
f_1=k_1[u-h_1]_+,\qquad
f_2=k_2[u-h_2]_+,
\]

且总推力满足

\[
f_1+f_2=P.
\]

只要 \(h_1\ne h_2\) 或 \(k_1\ne k_2\)，两针就自然不等载。若针 1 释放，正确做法是把 \(f_1\) 分支改为零，再解同一个总平衡；新的 \(u\) 会使针 2 和其他针重新增载。不存在一个普适的“把失效载荷平均分给剩余针”的独立物理定律。

因此：

\[
\boxed{
\text{载荷重分配}
=
\text{活动分支改变以后重新求共同平衡}.
}
\]

固定邻接权重、平均力、局部载荷分享或旧峰值包只能作为假设完全匹配时的回归 fixture，不能成为正式求解器。

### 6.5 光滑分支可凝聚，但不能跨事件外推

\[
\mathbf K_{Wq}^{raw}
=
\frac{\partial\mathbf W_U}{\partial\mathbf q_U}
=
\begin{bmatrix}
\mathbf K_{W,x}&\mathbf K_{W,z}
\end{bmatrix}.
\]

令

\[
k_{zx}
=
\mathbf E_Z^\mathsf T\mathbf K_{F,x},
\qquad
k_{zz}
=
\mathbf E_Z^\mathsf T\mathbf K_{F,z}.
\]

当分支唯一、光滑且 \(k_{zz}\ne0\) 时，

\[
\frac{du_z}{du_x}\bigg|_{P_z}
=
-\frac{k_{zx}}{k_{zz}},
\]

\[
\boxed{
\mathbf K_{W,x|P_z}
=
\mathbf K_{W,x}
-\mathbf K_{W,z}\frac{k_{zx}}{k_{zz}}.
}
\]

接触、滑移、硬限位、损伤或 graph 分支改变后，这个局部切线立即失效；应返回一侧切线、割线、集合值 graph 或 unavailable。

### 6.6 为什么有时返回 graph，而不是一个数

在活动支持、粘滑、安装和材料分支固定的光滑区间，令

\[
\mathbf R(\mathbf y,\chi)=\mathbf0.
\]

若

\[
\det\left(\frac{\partial\mathbf R}{\partial\mathbf y}\right)\ne0,
\]

隐函数定理只保证该邻域内存在唯一局部分支 \(\mathbf y(\chi)\)。它不保证跨接触切换、刚性退化、摩擦锥边界或软化转折后的全局唯一性。

当反力或状态集合值时，规范解对象应写成

\[
\boxed{
(\chi,\mathbf y,\mathbf W)
\in
\operatorname{Graph}(\mathcal G).
}
\]

返回的代表值必须同时带 branch、rank、nullspace、选择政策和 graph handle。用针 ID、最小范数或大罚刚度静默挑一个解，会把约束非唯一误写成材料刚度。

### 6.7 B 的真实事件路径不是 A 的直线猜测

在恒 \(P_z\) 路径上，\(u_z=u_z(u_x)\)。A 针级事件若只沿固定 \(u_z\) 的直线增量预测，不能保证它是 B 平衡曲线上的最早事件。B 必须在真实外层平衡路径上监控事件，或保守括区间后完整重求；不能直接采纳未经路径校正的针级事件分数。

### 6.8 阵列诊断只读，不反馈成权重

建议输出

\[
N_{\rm nominal},\quad
N_{\rm candidate},\quad
N_{\rm contact},\quad
N_{\rm load},
\]

其中 \(N_{\rm candidate}\) 是本稿建议的细化名称；只有定义完全一致时才可与 accepted B 中的 \(N_{\rm geom}\) 映射。新增名称属于 proposed 输出补充，不改变 B_TO_C 1.0.0 的现行 schema。

以及对明确非负载荷通道 \(\ell_i\)

\[
\boxed{
N_{\rm eff}
=
\frac{(\sum_i\ell_i)^2}{\sum_i\ell_i^2}.
}
\]

同时可报告 CV、Gini、最大/平均、方向离散、load_capacity_alignment、欠接合裕度、过利用裕度、最弱针、剩余行程、位姿误差敏感性、condition 和分支切换率。这些量用于理解“谁在承载、是否过度集中”，不得反向成为逐针经验分载系数。

---

## 7. 从阵列到十字爪：预紧边界必须先说清硬件

### 7.1 四单元与共同径向搜索

四个单元沿

\[
\mathbf e_{x_1}=+\mathbf E_X,\quad
\mathbf e_{x_2}=-\mathbf E_X,\quad
\mathbf e_{x_3}=+\mathbf E_Y,\quad
\mathbf e_{x_4}=-\mathbf E_Y
\]

布置。同步搜索坐标满足

\[
\boxed{
\mathbf O_i=\mathbf C-40\,\mathbf e_{x_i}\ {\rm mm}.
}
\]

四个工程安装参考点围成 80 mm \(\times\) 80 mm 的中央空区。B 的规范参考点 \(O_{A_i}\) 未必与 \(\mathbf O_i\) 重合；真实运输力臂应为

\[
\mathbf r_{A_i/C}
=
-40\,\mathbf e_{x_i}
+\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i},
\]

只有偏置 \(\boldsymbol\rho_{A/i}^{i}\) 有版本化几何证据为零时，才可令 \(O_{A_i}=O_i\)。

\[
\boxed{
u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s.
}
\]

接触对 \(s\) 的广义力及驱动反力为

\[
Q_s^{contact}
=
\sum_{i=1}^4\mathbf e_{x_i}^\mathsf T\mathbf F_i^G,
\]

\[
\boxed{
Q_s^{drive}
=
-Q_s^{contact}
=
\sum_{i=1}^4R_{x_i}.
}
\]

对称时四单元全局面内合力可能相消，但电机仍要克服四个径向阻力，因此“合力为零”绝不等于“驱动功为零”。

### 7.2 C-R 与 C-I 是互斥物理边界

固定工程事实描述了刚性十字参考体，因此本 proposed 论文选择

\[
\boxed{
\text{C-R：共同刚体 pose + 共同 }s
}
\]

为主线。四单元运动由

\[
\boldsymbol\xi_i
=
\mathbf J_i(\mathbf q_C,s)
\begin{bmatrix}
\Delta\mathbf q_C\\
\Delta s
\end{bmatrix}
\]

唯一导出，不存在四个彼此独立的 \(u_{z_i}\)。

accepted C 中逐单元

\[
\mathbf E_Z^\mathsf T\mathbf F_i-P_i=0
\]

对应另一种边界：

\[
\boxed{
\text{C-I：四个具有独立 Z 行程的法向力控执行器}.
}
\]

两者映射如下：

| 边界 | B 调用 | \(u_{z_i}\) 来源 | \(P_i\) 的位置 |
|---|---|---|---|
| C-R 刚性共体主线 | PRESCRIBED_XZ_RESIDUAL | 由 \((\mathbf q_C,s)\) 导出 | 端点和作用线绑定后成为 C 级主动广义载荷 |
| C-I 独立执行器备选 | UX_PZ_BALANCED | 每个 B 独立求解 | 每个独立法向执行器的主动推力 |

任一运行只能选择一行。不能先按 C-I 求四个 \(u_{z_i}\)，再把结果称作一个刚性 pose。

### 7.3 真正缺的是电机和执行器端口桥

硬件合同至少要给出：

\[
q_m
\xrightarrow{\ \mathcal T_s\ }
s,
\qquad
\dot q_m\tau_m
=
Q_s^{drive}\dot s+\mathcal P_{\rm loss},
\]

以及每个法向执行器的双端、源/目标体、作用线、相对行程 \(\eta_i\)、主动 wrench 和功：

\[
\mathbf W_{{\rm act},i}
=
\mathcal A_i(P_i,\text{pose, geometry}),
\qquad
dW_{{\rm act},i}=P_i\,d\eta_i.
\]

没有这些信息时，只能做 prescribed-\(s\) 接触扫描、驱动反力和保持反力诊断，不能声称真实 C 预紧已经认证。文献样机的传动公式不能替代本项目 CAD 和端口定义。

### 7.4 C-R 预紧平衡

C-R 向第 \(i\) 个 B 发出

\[
\boxed{
\operatorname{BTrial}_i
=
\operatorname{PRESCRIBED\_XZ\_RESIDUAL}
\left(
u_{x_i}=s,\,
u_{z_i}=u_{z_i}(\mathbf q_C,s)
\right).
}
\]

若参考体 pose 被台架规定，保持反力为

\[
\boxed{
\mathbf W_{\rm hold}^{preload}
=
-\left(
\mathbf W_{\rm contact}
+\mathbf W_{\rm active}
\right).
}
\]

它是边界反力，不是额外墙面承载。若参考体在授权自由度上自由，则求

\[
\boxed{
\mathbf0
\in
\sum_{i=1}^4
\mathbf J_i^\mathsf T\mathcal W_i
+\mathbf Q_{\rm active}
+\mathbf C_{\rm auth}^\mathsf T\boldsymbol\mu_{\rm auth}.
}
\]

只有真实授权的台架约束可以有非零乘子。

### 7.5 预紧何时停止

预紧不是“搜到第一个峰就锁住”。定义每单元特征 \(\mathbf A_i(s)\) 和整体质量 \(A_G(s)\)，正常停止至少要求：

\[
G_{\rm stop}
=
G_{\rm valid}
\land G_{\rm plateau}
\land G_{\rm gain}
\land G_{\rm weak}
\land G_{\rm safe}
\land G_{\rm persist}
\land G_{\rm range}
\land\neg V_{\rm decline}.
\]

\(V_{\rm decline}\) 是负斜率、能力下降或重大损伤否决。阈值、窗口、置信、滞回和 \(s_{\max}\) 均未固定，不能把 B standalone 的 100 mm 路径当作整爪搜索上限。在策略被标定以前，只允许 prescribed-\(s\) 扫描，不自动锁定。

---

## 8. 为什么整机必须算力矩：偏心载荷的完整理论

### 8.1 Wrench 是力与力矩的同一对象

四单元 contact-only wrench 必须从各自 \(O_{A_i}\) 运输到整机参考点 \(C\)：

\[
\boxed{
\mathbf F_i^C=\mathbf R_{Ci}\mathbf F_i,
\qquad
\mathbf M_i^C
=
\mathbf R_{Ci}\mathbf M_i^{O_A}
+\mathbf r_{A_i/C}\times\mathbf F_i^C.
}
\]

\[
\mathbf W_{\rm contact}^{C}
=
\sum_{i=1}^4
\begin{bmatrix}
\mathbf F_i^C\\
\mathbf M_i^C
\end{bmatrix}.
\]

主动推力、控制反力、真实台架反力和外加载荷必须分栏，contact-only 只装配一次。

### 8.2 50 mm 偏心加载天然产生力矩

加载点为

\[
\mathbf r_P=50\,\mathbf E_Z\ {\rm mm}.
\]

对单位加载方向 \(\hat{\mathbf d}\)，加载器单位 wrench 为

\[
\boxed{
\mathbf b_P(\hat{\mathbf d})
=
\begin{bmatrix}
\hat{\mathbf d}\\
\mathbf r_P\times\hat{\mathbf d}
\end{bmatrix},
\qquad
\mathbf W_{\rm load}
=
\lambda_P\mathbf b_P.
}
\]

加载路径约束为

\[
\boxed{
\mathbf b_P^\mathsf T\Delta\mathbf q_C
=
\Delta\delta_P.
}
\]

例如 \(+X\) 载荷产生 \(+50F\,\mathbf E_Y\) 的力矩；\(45^\circ\) 载荷同时产生 X、Y 力矩。只比较四个阵列的拉力和，无法判断偏心平衡。

显式地，

\[
\hat{\mathbf d}_{45}
=
\frac1{\sqrt2}(\mathbf E_X+\mathbf E_Y),
\]

\[
\boxed{
\mathbf r_P\times(F\hat{\mathbf d}_{45})
=
\frac{50F}{\sqrt2}
(-\mathbf E_X+\mathbf E_Y)\ {\rm N\,mm}.
}
\]

### 8.3 六维平衡与稳定性

完整理论方程为

\[
\boxed{
\mathbf0
\in
\sum_{i=1}^4
\mathbf J_i^\mathsf T
\mathcal W_i
+\lambda_P\mathbf b_P
+\mathbf W_{\rm other,authorized}
+\mathbf C_{\rm auth}^\mathsf T\boldsymbol\mu_{\rm auth}.
}
\]

代数根不自动等于稳定平衡。对固定加载路径和授权约束下的自由扰动基 \(\mathbf N\)，光滑唯一分支可检查

\[
\mathbf K_{\rm rest}
=
-\mathbf N^\mathsf T
\frac{\partial\mathbf r_W}{\partial\mathbf q_C}
\mathbf N,
\]

\[
\boxed{
\delta\mathbf z^\mathsf T
\operatorname{sym}(\mathbf K_{\rm rest})
\delta\mathbf z>0
}
\]

作为保守充分条件。摩擦、损伤和集合值分支应使用一侧切线、增量功或 graph 正则性。Newton 不收敛、代数无解、物理失稳和不可恢复脱附必须分开。

### 8.4 临界承载只在稳定可达历史上定义

令 \(\mathcal B_{\rm stable,reachable}\) 为从同一合法预紧态出发、合同/模型/参数/域有效、六维平衡和一侧稳定性通过、事件已定位并原子提交的状态集合，则

\[
\boxed{
F_{\rm crit}
=
\sup_{\mathsf s\in\mathcal B_{\rm stable,reachable}}
F_{\rm reaction}(\mathsf s).
}
\]

首针释放、首单元退化、第一处反力下降和第一个局部峰都不自动等于 \(F_{\rm crit}\)。只要还有合法稳定分支，就应继续追踪峰后下降、重平衡、再挂接和二次峰。

### 8.5 当前硬阻断

B_TO_C 1.0.0 对每个单元只认证局部 x 与全局 Z 平移。非零 \(+X\)：

- X 向两个单元需要局部 x；
- Y 向两个单元需要局部 y。

非零 \(45^\circ\) 使四个单元都需要局部 y；rocking 还需要动态姿态、针轴更新、表面/碰撞查询和 6D tangent/graph。因此正式请求必须返回

\[
\boxed{
\text{C\_CONTRACT\_EXTENSION\_REQUIRED}
}
\]

并保证：

\[
\Delta\delta_P^{accepted}=0,
\quad
\Delta\mathcal H_A
=\Delta\mathcal H_B
=\Delta\mathcal H_C
=\Delta\mathcal D=0,
\]

\[
F_{\rm crit}=\text{unavailable}.
\]

禁止用 x/Z 投影、冻结旧姿态后旋转旧 wrench 或经验能力域绕过。安全拒绝不等于零承载、物理失效或数值失败。

---

## 9. 求解器怎样沿这条故事线前进：事件驱动与原子事务

### 9.1 路径坐标

不同阶段使用统一路径符号 \(\chi\)：

\[
\chi=
\begin{cases}
u_x,&\text{单刺/阵列拖曳},\\
s,&\text{同步预紧},\\
\delta_P,&\text{偏心加载},\\
\chi_{\rm release},&\text{卸载—回位—再接触协议}.
\end{cases}
\]

所有层对同一 trial 增量返回最早事件分数 \(\gamma\in(0,1]\)。全局最早位置为

\[
\boxed{
\gamma_*=\min\gamma_e.
}
\]

### 9.2 一步不能“跨过去”

规范流程为：

\[
\boxed{
\begin{aligned}
\text{accepted snapshot}
&\rightarrow \text{side-effect-free trial}\\
&\rightarrow \text{find earliest event}\\
&\rightarrow \text{rollback if crossed}\\
&\rightarrow \text{re-solve at event}\\
&\rightarrow \text{switch branches}\\
&\rightarrow \text{damage fixed point}\\
&\rightarrow \text{same-position cascade}\\
&\rightarrow \text{global prepare}\\
&\rightarrow \text{atomic commit}.
\end{aligned}
}
\]

若 \(\gamma_*<1\)，当前目标 trial 全部回滚，从同一 accepted 状态在缩短后的共同路径点重求。不得按 \(\gamma_*\) 线性缩放旧 wrench、旧 \(u_z\)、旧姿态或旧损伤。

### 9.3 同时事件与同位置级联

括区间重叠、位置在同时容差内或 DamageStore 核耦合的事件组成同一组。排序只用于哈希和重放，不决定物理先后。

事件后可有 \(d\chi=0\) 但 \(du_z\ne0\)、姿态变化、储能释放和损伤更新。此时必须重复“低层重求—损伤协调—阵列/整机平衡—稳定性检查”，直到固定点、明确物理终止、未认证终止或数值终止。

### 9.4 原子提交保护历史

trial、Newton、线搜索、事件定位和回滚不得永久增加：

- 路径、时间、滑移或循环计数；
- DamageStore 或材料损伤；
- 摩擦/材料耗散；
- 事件号、峰值和再挂接计数。

只有 C/B 全局接受以后，A 状态、B 状态、C 状态、共享 DamageStore、事件、功和曲线才作为一个包提交。任一 prepare 或持久化失败，全部保持旧版本。

这不是软件附属细节，而是历史相关物理模型的一部分：如果四根针看到不同损伤版本，或者回滚 trial 已经偷偷积累滑移，求解的就不再是同一个物理问题。

---

## 10. 功和能量：检查故事有没有重复算力

### 10.1 端口功

对任一 A→B 或 B→C 端口，

\[
dW=\mathbf W^\mathsf T d\boldsymbol\xi.
\]

参考点和坐标变换必须保持该标量不变。B standalone 的外功为

\[
dW_B=R_x\,du_x-P_z\,du_z.
\]

C 预紧径向驱动功为

\[
dW_s^{drive}=Q_s^{drive}\,ds.
\]

偏心加载器功为

\[
dW_{\rm load}=\lambda_P\,d\delta_P.
\]

真实法向执行器功只有在双端和相对行程绑定后才能写成 \(P_i\,d\eta_i\)；否则 certified actuator work 必须 unavailable。

### 10.2 唯一能量闭合式

对一个 accepted 增量，

\[
\boxed{
r_E
=
\Delta W_{\rm ext}
-\Delta\Psi
-D_{\rm friction}
-D_{\rm damage}
-E_{\rm out}
=0.
}
\]

\(\Delta\Psi\) 包括接触、梁和安装弹簧的可恢复储能变化。\(E_{\rm out}\) 只记录真正离开所建模系统的释放能；若能量已作为返回执行器的负功或摩擦/材料耗散入账，不得再计一次。数值残量、积分误差和浮点误差必须另列，不能伪装成材料耗散。

同位置级联即使 \(d\chi=0\)，仍可能有 \(du_z\ne0\) 或 \(d\eta_i\ne0\)，因此外功不一定为零。

---

## 11. 模型怎样与实验相遇：可观测、统计与可辨识性

### 11.1 原始量优先

每个 accepted 点至少保存：

- 位移路径、时间映射若有、完整力和力矩；
- 表面、参数、模型、坐标、参考点和版本；
- 支持、gap、接触力、粘滑、梁、弹簧和行程；
- \(N_{\rm candidate},N_{\rm contact},N_{\rm load},N_{\rm eff}\)；
- 事件前/点/后状态、释放、再挂接和 DamageStore；
- 原始曲线、功、能量、残量和提交收据。

滤波、平台、峰值、综合质量和成功判据只能作为带版本的派生通道，不能覆盖原始历史。

在验证协议冻结以前，不自动输出二元“抓附成功”、单一综合评分或未经标定的安全系数。未来机器人层若需要支撑集、grasp-map rank、单爪丢失后可恢复性或 attachment_margin_LB，应作为 C/System 之上的新接口读取已认证 wrench 和状态，不能替换 B 的物理重平衡。

### 11.2 搜索统计

首次承载距离可能在零距离有点质量，同时对正距离有条件尾部，并在搜索上限处右删失。建议分别记录：

- nominal search distance；
- effective contact-search distance；
- 跳过区间和 re-capture distance；
- false engagement 次数、持续距离和分支；
- 未挂接质量与条件正峰值分布。

多根针看到的是相关表面，不得把单刺概率按 IID 直接相乘得到阵列成功率。

### 11.3 哪些参数不能从一条拖曳曲线单独识别

同一 \(R_x(u_x)\) 可能由不同组合产生：

- \(\mu_{\rm Coulomb}\) 与支持坡度/法向；
- 针梁柔顺、安装弹簧和接触柔顺；
- 表面统计、针尖半径和搜索路径；
- 材料容量、局部面积和损伤核；
- 执行器行程、保持反力和结构边界。

因此实验优先标定联合可观测量、趋势和设计排序，不应从单次峰值反推出唯一材料参数。外部论文的摩擦、刚度、载荷、概率或断裂参数最多作为弱先验、解析 fixture 或趋势对照，只有对象、尺度、模式、材料和硬件适用域一致并经过项目标定后，才可成为参数来源。

---

## 12. 验证不是最后一节附录，而是每个箭头的反证

### 12.1 几何与表面

必须覆盖：

1. 平面、单峰、单谷、斜面和多支持解析表面；
2. 球包络与欧氏距离零集一致；
3. 球冠边界、面/边/顶点最近特征和体部碰撞；
4. 合成表面 PSD 回算、方差、种子重放；
5. 实测预处理、缺失掩膜、可信带和针尖尺度敏感性；
6. 表面分辨率/带宽增加时的接触输出收敛，而不只是 PSD 收敛。

### 12.2 单刺

必须覆盖：

1. 开放、零载、受压、粘着、滑移和释放；
2. 支持迁移但零客观滑移；
3. 梁柔顺与有限差分；
4. 弹簧零位、内点、硬限位和禁止拉力；
5. 根截面搬运和名义应力；
6. 释放 pose 停止或完整扫掠回位；
7. \(\mathsf M_1\) 缺桥时 unavailable；
8. 纯 Mode-I 零容量终态不保留同通道法向黏聚牵引。

### 12.3 阵列

必须覆盖：

1. 同高同刚度对称载荷；
2. 高度/刚度差导致自然不等载；
3. 首针释放后全量重平衡；
4. 固定均分/邻接权重被拒绝；
5. 恒 \(P_z\) 曲线上的最早事件；
6. graph 非唯一不被大罚刚度隐藏；
7. DamageStore 调用顺序和并行顺序不变；
8. 诊断量不反馈成分载权重。

### 12.4 系统与接口负例

必须覆盖：

1. wrench 运输和功不变；
2. contact-only、主动、控制和台架反力不重复；
3. C-R/C-I 互斥；
4. 缺硬件端口时真实预紧不认证；
5. 非零 \(+X\)、\(45^\circ\)、rocking 在 B 1.0 下安全拒绝；
6. 拒绝时所有历史零推进，\(F_{\rm crit}\) 为 unavailable；
7. Newton 不收敛、物理无解、失稳和脱附分类不混用；
8. prepare/commit 故障使所有层同时回滚。

### 12.5 验证阶梯

| 等级 | 能证明什么 | 不能证明什么 |
|---|---|---|
| 方程/合同验证 | 符号、单位、边界和恒等式一致 | 求解器已经可靠 |
| 求解器验证 | 事件、分支、收敛、回滚可执行 | 参数适用于目标表面 |
| 合成 ensemble | 趋势、敏感性和统计稳定性 | 真实材料定量正确 |
| 单刺/单元实验 | 联合参数和局部趋势 | 整机偏心能力 |
| 整机配对实验 | 系统趋势、方向和事件链 | 未观测内部变量唯一可辨识 |

当前状态仍停留在“理论与合同已部分定义；代码、数值和实验未验证”。

---

## 13. 当前可执行性与阻断矩阵

| 分支 | 理论闭合 | 当前可实现性 | 认证结论 |
|---|---:|---:|---|
| 解析/合成表面 + 有限球尖 | 是 | 待实现验证 | 开发可用 |
| A \(\mathsf M_0\) no_damage | proposed 闭合 | 待实现 | 首选开发基线 |
| A \(\mathsf M_1\) | 条件性 | 桥和参数未齐 | unavailable |
| B x/Z 阵列平衡 | accepted 主链 + proposed 事件修正 | 待实现 | 可开发 |
| B 经验均载/固定换载 | 否 | 禁止 | 只能严格受限 fixture |
| C-R prescribed-\(s\) 扫描 | proposed | 缺硬件端口 | 只作诊断 |
| C-I 独立 Z 执行器 | 条件性 | 缺端点/作用线 | unavailable |
| C 非零 \(+X/45^\circ\) fixed pose | 理论已写 | B local-y 缺失 | C_CONTRACT_EXTENSION_REQUIRED |
| C rocking | 理论已写 | B SE(3) 缺失 | C_CONTRACT_EXTENSION_REQUIRED |
| 正式 \(F_{\rm crit}\) | 定义已写 | 在线路径被阻断 | unavailable |

---

## 14. 结论：完整机理是一条受边界约束的因果链

本轮不需要推翻现有机理。需要改变的是“完整”的含义。

完整不是把接触、摩擦、梁、损伤、阵列和整机公式全部放进一个文档；完整是每个物理转换都有明确输入、所有者、方程、事件、输出、证据等级和失败状态：

1. 表面合同告诉我们哪些几何可相信；
2. 有限球尖告诉我们哪些支持可到达；
3. Signorini 告诉我们候选是否真正受压；
4. Coulomb 与客观滑移告诉我们能否稳定留住；
5. 梁和安装分支把运动变成渐进反力；
6. 事件、释放路径和历史告诉我们反力为何突变以及能否再挂接；
7. B 的共同平衡让载荷自然共享和重新分配；
8. C 的完整 wrench 让力矩、预紧和偏心承载进入同一平衡；
9. 事务和能量账本保证这条路径没有被数值试探或重复计力污染；
10. 验证和阻断矩阵明确区分“理论写出来了”和“当前能认证地算出来”。

因此本稿的最终判断是：

\[
\boxed{
\text{保留核心机理}
+\text{补齐桥接合同}
+\text{重写因果叙事}
+\text{维持所有安全阻断}.
}
\]

在下一版 accepted amendment 通过前，本文仍是 0.2.0-proposed。尤其是 A 姿态、材料端点、B 平衡路径事件、C-R/C-I 边界和执行器端口映射，都不能因为本稿叙述更完整而被静默视为正式迁移。

---

## 附录 A：变量角色速查

| 符号 | 角色 |
|---|---|
| \(\phi_\Omega,h,C_h\) | 表面 realization 与谱证据 |
| \(R_t,\mathbf c_t,\mathbf a_t\) | 有限球尖半径、球心和当前针轴 |
| \(g_j,\lambda_{n,j},\boldsymbol\lambda_{t,j}\) | 接触间隙、法向和切向乘子 |
| \(\mathbf u_b,\boldsymbol\theta_b\) | 梁端平移和全局转角 |
| \(\delta_s,k_s,r_H\) | 针级安装弹簧压缩、刚度和硬限位反力 |
| \(\mathbf W_{A\rightarrow B},\mathbf W_U\) | 单刺和阵列 contact-only wrench |
| \(u_x,u_z,P_z\) | B 共同切向/法向位移与单元主动推力 |
| \(s,Q_s^{drive}\) | C 同步搜索坐标与驱动广义反力 |
| \(\mathbf q_C,\delta_P,\lambda_P\) | 整机位姿、偏心加载路径和反力 |
| \(\mathcal D,\mathcal H,\gamma\) | DamageStore、历史和事件分数 |

## 附录 B：本稿相对 0.1.0-proposed 的实质变化

1. 把全篇从“A/B/C 工具箱顺序”改为“表面—支持—受力—变形—释放—重分配—整机承载”的因果顺序。
2. 在正文开头明确给出问题—机理—来源—输出映射。
3. 新增 SurfaceGenerationAndAcquisitionContract 的 proposed 结构。
4. 统一 geometric candidate、loaded contact、frictionally stable、load-bearing、released/reengaged。
5. 把释放写成可扫掠、可再接触的外部操作路径；未实现时停在释放 pose。
6. 将 \(\mathsf M_1\) 的材料桥、模式、尺度、观测算子、初始缺陷和 provenance 统一为硬启用门。
7. 增加阵列能力—载荷对齐、双侧裕度与相关性统计，但明确只读。
8. 将 C-R/C-I 的互斥边界和电机/执行器端口桥放在预紧方程之前。
9. 将 B_TO_C 1.0.0 的 P0 阻断放入主叙事，而不是只留在末尾限制表。
10. 把验证重写为对每个因果箭头的正例、负例和事件级反证。

## 附录 C：证据与权限入口

- [理论入口与权威说明](../README.md)
- [独立推导复核](../review/DERIVATION_VERIFICATION_2026-07-17.md)
- [证据反审计总报告](../evidence_reassessment/reverse_audit_2026-07-17/MECHANISM_EVIDENCE_REASSESSMENT_REPORT.md)
- [证据反审计协议](../evidence_reassessment/reverse_audit_2026-07-17/REVIEW_PROTOCOL.md)
- [工程证据上下文](../evidence_reassessment/engineering_fixed_context.md)

本稿引用上述反审计时，含义始终是“基于证据卡、提取审计和关键图的反审计”，不是“重新核验了全部原始论文全文”。

## 附录 D：论文级证据线索

下列条目保留为本项目已经建立证据卡的代表性文献入口，不表示本轮重新完成了全文核验：

1. Xiang et al., frictional engagement of microspines, *Tribology International*, 2025, DOI 10.1016/j.triboint.2025.110533；[证据卡](../evidence_reassessment/literature/01_frictional_engagement/evidence_card.md)。
2. A. T. Asbeck, *Compliant Directional Suspensions for Climbing with Microspines*, Stanford University dissertation, 2010；[证据卡](../evidence_reassessment/literature/03_compliant_directional_suspensions/evidence_card.md)。
3. Iacoponi et al., isolated spine interlock and fracture analysis, 2020, DOI 10.1115/1.4047725；[证据卡](../evidence_reassessment/literature/05_isolated_spine_fracture_interlock/evidence_card.md)。
4. Wang, Jiang and Cutkosky, linearly constrained spines, *The International Journal of Robotics Research*, 2017, DOI 10.1177/0278364917720019；[证据卡](../evidence_reassessment/literature/07_linearly_constrained_spines/evidence_card.md)。
5. Jiang, Wang and Cutkosky, stochastic compliant arrays, *The International Journal of Robotics Research*, 2018, DOI 10.1177/0278364918778350；[证据卡](../evidence_reassessment/literature/09_stochastic_compliant_spine_arrays/evidence_card.md)。
6. Ruotolo, Roig and Cutkosky, soft-paw load sharing, *IEEE Robotics and Automation Letters*, 2019, DOI 10.1109/LRA.2019.2897002；[证据卡](../evidence_reassessment/literature/10_soft_spiny_paw_load_sharing/evidence_card.md)。
7. B. N. J. Persson, random rough contact mechanics, *Surface Science Reports*, 2006, DOI 10.1016/j.surfrep.2006.04.001；[证据卡](../evidence_reassessment/literature/11_randomly_rough_contact_mechanics/evidence_card.md)。
8. Arnold et al., roughness measurement of red ceramic surfaces, *Remote Sensing*, 2021, DOI 10.3390/rs13040789；[证据卡](../evidence_reassessment/literature/12_red_ceramic_blocks_roughness/evidence_card.md)。
9. D'Antino, Santandrea and Carloni, fracture parameters of brick and tuff, *Journal of Engineering Mechanics*, 2020, DOI 10.1061/(ASCE)EM.1943-7889.0001815；[证据卡](../evidence_reassessment/literature/14_fired_clay_tuff_fracture_properties/evidence_card.md)。

正式投稿前必须重新打开原始来源，核对书目信息、原式、图表、适用域和引用上下文，并补充 SE(3)/虚功、变分不等式、非光滑接触、准静态分支延拓、稳定性及事务式历史推进的一手基础文献。

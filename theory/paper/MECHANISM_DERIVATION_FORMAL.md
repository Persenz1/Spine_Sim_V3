# 壁面—单刺—阵列—十字对爪准静态机理的完整形式化推导

**文档性质：** 闭合修正版形式推导稿
**版本：** 0.1.0-proposed
**日期：** 2026-07-17
**主要用途：** 论文方法章节、方程逐式审查、求解器实现交接
**配套易读稿：** [从牛顿平衡到分层非光滑算子](MECHANISM_DERIVATION_TUTORIAL.md)

> **规范状态。** 本稿以当前 [系统集成模型](../system/SYSTEM_INTEGRATED_MODEL.md) 和 [A](../modules/A_INTEGRATED_MODEL.md)、[B](../modules/B_INTEGRATED_MODEL.md)、[C](../modules/C_INTEGRATED_MODEL.md) 为来源，显式修补本轮复核发现的姿态类型、损伤末端、根截面映射和 B 弹簧摘要冲突。它是“建议并入下一版正式模型”的闭合稿，在完成版本化评审前不覆盖现有 accepted 文档。现有模型与本稿的差异见 [独立复核报告](../review/DERIVATION_VERIFICATION_2026-07-17.md)。

## 摘要

本文建立一个从随机粗糙壁面到单根有限球尖爪刺、多刺阵列单元及四单元十字对爪的三维准静态、历史相关、非光滑分层模型。壁面几何由高度场或三角网格的统一有符号距离查询给出；单刺层联立有限球冠支持、Signorini 单边接触、三维 Coulomb 摩擦、针梁柔顺、单边轴向弹簧及可选材料容量；阵列层通过共同刚性背板的法向平衡而非经验均载实现载荷共享和事件后重分配；系统层通过 wrench–twist 对偶、参考点运输和六维平衡描述同步预紧与偏心加载。模型以 trial–event localization–rollback–re-solve–atomic commit 事务保证事件顺序和共享损伤历史的一致性。

为保证当前可执行性，本文定义完全闭合的开发基线 \(\mathsf M_0\)：刚性局部接触、Coulomb 摩擦、Euler–Bernoulli 梁、已定义的安装分支与 `no_damage`。材料损伤扩展 \(\mathsf M_1\) 只有在给出功共轭局部化位移、尺度桥和参数后才可启用。C 层按固定工程事实选择刚性参考体主模型；现有逐单元独立 \(u_{z_i}\) 平衡仅保留为“具有独立法向执行器行程”条件下的备选边界。当前 B→C 1.0 不覆盖 local-y 或转动，故非零 +X、45° 与 rocking 的在线调用必须安全拒绝。

## 1. 问题、状态与模型版本

### 1.1 物理域

设壁面实体为

\[
\Omega\subset\mathbb R^3,
\]

其边界 \(\Gamma=\partial\Omega\) 的平均平面为全局 XY 平面。爪刺位于壁外，+Z 指向离墙方向。

系统含：

- 每个单刺的有限球尖、锥段、针杆和安装座；
- 每个阵列单元的共同刚性背板；
- 四个阵列单元构成的刚性十字参考体；
- 外部主动推力、同步径向驱动和偏心加载器；
- 接触、滑移、弹簧、事件和可选损伤历史。

### 1.2 全局接受状态

在第 n 个接受点，将系统状态写成

\[
\mathcal S^n=
\left(
\{S_{A,i}^n\},
\{S_{B,j}^n\},
S_C^n,
D^n,
H^n
\right),
\]

其中：

- \(S_{A,i}\)：第 i 根针的机械与接触历史；
- \(S_{B,j}\)：第 j 个阵列单元的共同位姿、活动集和事务状态；
- \(S_C\)：整机阶段、位姿、预紧锁定态和加载态；
- \(D\)：唯一权威共享 DamageStore；
- \(H\)：原始曲线、事件、功和质量历史。

一个系统 trial 算子写成

\[
\mathscr T:
(\Delta\chi,\mathcal S^n,\mathbf p)
\mapsto
(\mathbf z^{trial},\mathcal E^{trial},
\mathcal I_D^{trial},\mathcal Q^{trial}),
\]

其中 \(\chi\) 是当前路径坐标，\(\mathbf p\) 是不可变参数，\(\mathcal I_D\) 是损伤写入意图，\(\mathcal Q\) 是质量/认证结果。只有全局接受谓词为真时才允许

\[
\mathcal S^{n+1}
=\operatorname{Commit}
(\mathcal S^n,\mathbf z^{trial},\mathcal I_D^{trial}).
\]

### 1.3 两个模型版本

本文区分：

\[
\boxed{
\mathsf M_0
=
\text{几何}
+\text{刚性接触}
+\text{Coulomb}
+\text{梁/安装}
+\text{无材料损伤}
}
\]

和

\[
\boxed{
\mathsf M_1
=\mathsf M_0+\text{经功共轭与参数闭合的材料扩展}.
}
\]

\(\mathsf M_0\) 是当前实现主线；\(\mathsf M_1\) 是条件性扩展，不得因提供了公式就自动视为可用。

## 2. 基本假设与适用域

### 2.1 准静态假设

完整离散动力学为

\[
\mathbf M(\mathbf q)\ddot{\mathbf q}
=
\mathbf Q_{ext}
+\mathbf Q_{contact}
+\mathbf Q_{internal}
+\mathbf Q_{constraint}.
\]

令

\[
\varepsilon_I
=\frac{M_*L_*}{T_*^2F_*}.
\]

在连续加载段假设 \(\varepsilon_I\ll1\)，得到

\[
\boxed{
\mathbf Q_{ext}
+\mathbf Q_{contact}
+\mathbf Q_{internal}
+\mathbf Q_{constraint}
=\mathbf0.
}
\]

释放后的高速回弹、冲击和大角度脱落不在模型内。

### 2.2 几何与本构假设

对 \(\mathsf M_0\)：

1. 高度场分支在局部查询带内分片 \(C^2\)，或三角网格具有确定的面–边–顶点最近特征规则；
2. 球尖半径 \(R_t>0\)，针梁 \(E>0,G>0,A>0,I>0,J>0,L>0\)；
3. 摩擦参数 \(\mu_j\ge0\)；
4. 安装为 `RIGID_MOUNT` 或已给定 \(k_s>0\) 的单边压缩弹簧；
5. 非承载体只施加硬几何可行性，不产生未授权接触反力；
6. 同一接受步内参数、表面 realization 和参考系版本不变；
7. 若光滑分支 Jacobian 奇异或集合值图没有认证选解，则返回 graph/unavailable，而非静默正则化成物理参数。

### 2.3 路径

四类路径不得混用：

\[
\chi=
\begin{cases}
u_x,&\text{A/B 直线拖曳},\\
s,&\text{C 同步预紧},\\
\delta_P,&\text{C 偏心位移加载},\\
\gamma,&\text{单步内部事件比例}.
\end{cases}
\]

拖曳物理时间仅用于输出：

\[
t=u_x/(1\ \mathrm{mm/s}).
\]

若无速率本构，平衡方程不显式依赖该速度。

## 3. 坐标、刚体变换、wrench 与虚功

### 3.1 坐标

全局正交基为 \((\mathbf E_X,\mathbf E_Y,\mathbf E_Z)\)。第 i 个单元的局部基满足

\[
\mathbf e_{y_i}=\mathbf E_Z\times\mathbf e_{x_i},
\qquad
\mathbf e_{x_i}\times\mathbf e_{y_i}=\mathbf E_Z.
\]

针初始轴在单元局部坐标中定义为

\[
{}^A\mathbf a
=
\begin{bmatrix}
\cos\alpha\cos\beta\\
\cos\alpha\sin\beta\\
-\sin\alpha
\end{bmatrix},
\]

避免将已经是全局坐标的轴向量再次旋转。当前正式扫描取 \(\beta=0\)。

### 3.2 刚体变换

令

\[
{}^G T_A=
\begin{bmatrix}
{}^G R_A&{}^G\mathbf p_A\\
\mathbf0^\mathsf T&1
\end{bmatrix}.
\]

点的变换为

\[
{}^G\mathbf x
={}^G R_A{}^A\mathbf x+{}^G\mathbf p_A.
\]

定义反对称矩阵 \([\mathbf r]_\times\mathbf x=\mathbf r\times\mathbf x\)。

### 3.3 wrench 搬运

本文使用

\[
\mathbf W_O=
\begin{bmatrix}
\mathbf F\\
\mathbf M_O
\end{bmatrix},
\qquad
\mathbf V_O=
\begin{bmatrix}
\mathbf v_O\\
\boldsymbol\omega
\end{bmatrix}.
\]

同一坐标系内从 P 搬到 O：

\[
\boxed{
\mathbf F_O=\mathbf F_P,
\qquad
\mathbf M_O
=\mathbf M_P+\mathbf r_{OP}\times\mathbf F_P.
}
\]

若同时旋转坐标：

\[
{}^G\mathbf F
={}^G R_A{}^A\mathbf F,
\]

\[
{}^G\mathbf M_O
={}^G R_A{}^A\mathbf M_P
+{}^G\mathbf r_{OP}\times{}^G\mathbf F.
\]

### 3.4 功率不变命题

刚体点速度满足

\[
\mathbf v_P
=\mathbf v_O+\boldsymbol\omega\times\mathbf r_{OP}.
\]

于是

\[
\boxed{
\mathbf W_P^\mathsf T\mathbf V_P
=\mathbf W_O^\mathsf T\mathbf V_O.
}
\]

证明为

\[
\mathbf F\cdot
(\boldsymbol\omega\times\mathbf r)
=\boldsymbol\omega\cdot
(\mathbf r\times\mathbf F).
\]

该恒等式同时固定参考点搬运、作用—反作用和 Jacobian 对偶的符号。

### 3.5 Jacobian 对偶装配

若第 i 个单元 twist 与系统速度满足

\[
\mathbf V_i=\mathbf J_i\dot{\mathbf q}_C,
\]

虚功

\[
\delta W_i
=\mathbf W_i^\mathsf T\mathbf J_i\delta\mathbf q_C
\]

给出系统广义力

\[
\boxed{
\mathbf Q_i=\mathbf J_i^\mathsf T\mathbf W_i.
}
\]

## 4. 表面 realization 与有限球尖形态学

### 4.1 高度场

高度场实体为

\[
\Omega_h=\{(x,y,z):z\le h(x,y)\}.
\]

二维 PSD 约定

\[
C_h(\mathbf q)
=\int R_h(\mathbf r)
e^{-i\mathbf q\cdot\mathbf r}\,d^2\mathbf r,
\]

\[
\langle h^2\rangle
=\frac1{(2\pi)^2}\int C_h(\mathbf q)\,d^2\mathbf q.
\]

PSD 只在声明的可信波数带内解释。

### 4.2 完整球的非穿透包络

令球心平面坐标为 \((x_c,y_c)\)，\(\rho^2=(u-x_c)^2+(v-y_c)^2\)。半径 R 的最低合法球心高度是

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

因此高度场球形包络的竖直可行裕量为

\[
\boxed{
g_R^{env}=c_z-H_R(x_c,y_c).
}
\]

它给出 \(g_R^{env}\ge0\) 的非穿透可行域及 \(g_R^{env}=0\) 的接触零集。其数值尺度一般不同于欧氏距离；跨后端用于接触互补的规范间隙统一写成

\[
g_R^{(d)}(\mathbf c)
=\phi_\Omega(\mathbf c)-R,
\]

其中 \(\phi_\Omega\) 是外正内负的欧氏有符号距离。\(g_R^{env}\) 与 \(g_R^{(d)}\) 只要求可行域和零接触条件一致，不假定二者数值相等。

### 4.3 有限球冠

令当前针轴为 \(\mathbf a_t\)，球冠边界的轴向坐标为 \(\zeta_b\)。候选支持点 \(\mathbf p_j\) 必须满足

\[
(\mathbf p_j-\mathbf c_t)\cdot\mathbf a_t
\ge\zeta_b-\epsilon_{cap}.
\]

接触径向法向为

\[
\boxed{
\mathbf n_j
=\frac{\mathbf c_t-\mathbf p_j}
{\|\mathbf c_t-\mathbf p_j\|}.
}
\]

多支持时保留

\[
\{(\mathbf p_j,\mathbf n_j)\}_{j=1}^{n_s},
\]

不得平均为单个伪法向。

### 4.4 切向基与非承载体间隙

若不退化，

\[
\mathbf t_{1j}
=\frac{(\mathbf I-\mathbf n_j\mathbf n_j^\mathsf T)
\mathbf e_x}
{\|(\mathbf I-\mathbf n_j\mathbf n_j^\mathsf T)
\mathbf e_x\|},
\qquad
\mathbf t_{2j}=\mathbf n_j\times\mathbf t_{1j}.
\]

令

\[
\mathbf T_j=
[\mathbf t_{1j}\ \mathbf t_{2j}].
\]

对锥段、针杆和安装座 \(K_k(T)\)，

\[
g_k(T)
=\min_{\mathbf x\in K_k(T)}
\phi_\Omega(\mathbf x)
-\delta_{clr,k}>0.
\]

这些是硬可行性条件，不产生承载乘子。

### 4.5 支持点认证

在光滑图表 \(\mathbf p(\boldsymbol\xi)\) 上，最近支持候选满足

\[
\mathbf r_{geo}
=
\begin{bmatrix}
\mathbf p_{,1}^\mathsf T(\mathbf c_t-\mathbf p)\\
\mathbf p_{,2}^\mathsf T(\mathbf c_t-\mathbf p)
\end{bmatrix}
=\mathbf0.
\]

但驻定不是最近点的充分条件。接受支持还必须满足：

\[
\nabla_{\boldsymbol\xi}^2
\frac12\|\mathbf c_t-\mathbf p(\boldsymbol\xi)\|^2
\succeq0,
\]

并与搜索邻域内全部合法球冠候选比较距离/包络值。退化或并列最小值作为多支持 graph 保留。三角网格必须枚举并比较面、边、顶点的精确最近特征，不用平均顶点法向代替认证。

## 5. A 层：单刺本征问题

### 5.1 修正后的针尖运动学

给定背板位姿 \(T_B\)，刚性几何的梁根位置为

\[
\mathbf r_{0,rigid}(T_B).
\]

若存在轴向压缩弹簧：

\[
\boxed{
\mathbf r_0
=\mathbf r_{0,rigid}(T_B)-\delta_s\mathbf a_0.
}
\]

未弯曲球心为

\[
\mathbf c_0=\mathbf r_0+L\mathbf a_0.
\]

令 \(\mathbf R_0\mathbf e_1=\mathbf a_0\)，并把梁转角明确表示为全局旋转向量 \({}^G\boldsymbol\theta_b\)。闭合的姿态更新选为左乘：

\[
\boxed{
\mathbf R_t
=\exp([{}^G\boldsymbol\theta_b]_\times)\mathbf R_0,
}
\]

\[
\boxed{
\mathbf c_t=\mathbf c_0+\mathbf u_b,
\qquad
\mathbf a_t=\mathbf R_t\mathbf e_1
=\exp([{}^G\boldsymbol\theta_b]_\times)\mathbf a_0.
}
\]

小转角下

\[
\mathbf a_t
\approx\mathbf a_0
+{}^G\boldsymbol\theta_b\times\mathbf a_0.
\]

这消除了“全局 \(\mathbf a_0\) 再乘局部姿态”的二次变换。

### 5.2 接触力与 Signorini 条件

第 j 个支持上的墙面对针接触力为

\[
\mathbf f_j
=\lambda_{n,j}\mathbf n_j
+\mathbf T_j\boldsymbol\lambda_{t,j}.
\]

刚性局部接触：

\[
\boxed{
g_j^{geom}\ge0,
\quad
\lambda_{n,j}\ge0,
\quad
g_j^{geom}\lambda_{n,j}=0.
}
\]

若有独立标定的法向压缩 \(c_{n,j}(\lambda_n)\ge0\)，则

\[
g_j^{eff}
=g_j^{geom}+c_{n,j}(\lambda_{n,j}),
\]

\[
c_{n,j}(0)=0,
\qquad
\frac{dc_n}{d\lambda_n}\ge0.
\]

\(\mathsf M_0\) 取 \(c_n=0\)。

### 5.3 三维 Coulomb 锥的互补形式

定义二阶锥

\[
\mathcal L_3
=\{(x_0,\mathbf x):x_0\ge\|\mathbf x\|\}.
\]

对 \(\mu_j>0\)，令

\[
\boldsymbol\chi_j
=
\begin{bmatrix}
\mu_j\lambda_{n,j}\\
\boldsymbol\lambda_{t,j}
\end{bmatrix},
\]

\[
\boldsymbol\psi_j
=
\begin{bmatrix}
g_j^{eff}/\mu_j+\|\Delta\mathbf s_j\|\\
\Delta\mathbf s_j
\end{bmatrix}.
\]

接触与最大耗散统一写成

\[
\boxed{
\boldsymbol\chi_j\in\mathcal L_3,
\quad
\boldsymbol\psi_j\in\mathcal L_3,
\quad
\boldsymbol\chi_j^\mathsf T\boldsymbol\psi_j=0.
}
\]

半光滑投影残量：

\[
\boxed{
\mathbf r_{c,j}
=
\boldsymbol\chi_j
-\Pi_{\mathcal L_3}
(\boldsymbol\chi_j-\kappa_{proj,j}\boldsymbol\psi_j)
=\mathbf0.
}
\]

\(\kappa_{proj,j}>0\) 的单位为 N/mm，只是使力型 \(\boldsymbol\chi_j\) 与位移型 \(\boldsymbol\psi_j\) 可相减的数值投影尺度，不是物理接触刚度，也不与材料残余容量共用符号。\(\mu_j=0\) 时退化为

\[
\boldsymbol\lambda_{t,j}=\mathbf0
\]

和标量 Signorini 条件。

真实滑移 \(\Delta\mathbf s_j\ne\mathbf0\) 时

\[
\boldsymbol\lambda_{t,j}
=-\mu_j\lambda_{n,j}
\frac{\Delta\mathbf s_j}
{\|\Delta\mathbf s_j\|}.
\]

### 5.4 客观滑移

以中点量计算

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

其中

\[
\mathbf P_{t,j}
=\mathbf I-\mathbf n_j\mathbf n_j^\mathsf T.
\]

局部切向分量为

\[
\boxed{
\Delta\mathbf s_j
=\mathbf T_{j,n+1/2}^\mathsf T
\Delta\mathbf s_j^G.
}
\]

支持点迁移而 \(\Delta\mathbf s_j=\mathbf0\) 是无滑移滚动；只有非零客观滑移提交摩擦耗散。

### 5.5 合接触 wrench

定义

\[
\mathbf F_c=\sum_j\mathbf f_j,
\]

\[
\boxed{
\mathbf M_c^{c_t}
=\sum_j
(\mathbf p_j-\mathbf c_t)\times\mathbf f_j
+\sum_j\mathbf m_j^{local},
}
\]

其中没有接触偶力模型时 \(\mathbf m_j^{local}=\mathbf0\)。针尖截面 wrench 为

\[
\mathbf W_c=
\begin{bmatrix}
\mathbf F_c\\
\mathbf M_c^{c_t}
\end{bmatrix}.
\]

### 5.6 梁柔顺

圆截面参数

\[
A=\frac{\pi d^2}{4},
\quad
I=\frac{\pi d^4}{64},
\quad
J=\frac{\pi d^4}{32},
\quad
G=\frac{E}{2(1+\nu)}.
\]

定义

\[
\mathbf P_\parallel
=\mathbf a_0\mathbf a_0^\mathsf T,
\quad
\mathbf P_\perp
=\mathbf I-\mathbf P_\parallel,
\quad
\mathbf S=[\mathbf a_0]_\times.
\]

Euler–Bernoulli 柔顺为

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

写成

\[
\boxed{
\mathbf r_b
=\boldsymbol\eta_b-\mathbf C_b\mathbf W_c
=\mathbf0,
\qquad
U_b=\frac12\mathbf W_c^\mathsf T
\mathbf C_b\mathbf W_c.
}
\]

若梁细长比、剪切修正、转角或几何刚度超出验证域，必须切换版本化 Timoshenko/共回转模型或返回 `STRUCTURAL_MODEL_OUT_OF_RANGE`。

### 5.7 单边轴向弹簧的权威图

压缩广义需求

\[
Q_s=-\mathbf a_0\cdot\mathbf F_c.
\]

分支定义为

\[
\boxed{
\begin{array}{lll}
\text{RIGID\_LOCKED:}
&\delta_s=0,
&Q_s\ \text{由约束反力承担};\\[1mm]
\text{AT\_ORIGINAL\_LENGTH:}
&\delta_s=0,
&F_s=0,\ Q_s=0;\\[1mm]
\text{COMPRESSING:}
&0<\delta_s<\delta_{max},
&Q_s-k_s\delta_s=0;\\[1mm]
\text{HARD\_STOP:}
&\delta_s=\delta_{max},
&Q_s-k_s\delta_{max}-r_H=0,\ r_H\ge0.
\end{array}
}
\]

其中

\[
\delta_{max}=4\ \mathrm{mm}.
\]

若维持接触需要 \(\delta_s<0\) 或弹簧拉力，则切换到释放分支。B 层任何 `SPRING_ZERO` 摘要必须服从本图，不得另行允许 \(F_s>0\)。

### 5.8 根截面结果量的闭合映射

针自由体根部反力满足

\[
\mathbf F_r+\mathbf F_c=\mathbf0,
\]

\[
\mathbf M_r^{r_0}
+\mathbf M_c^{c_t}
+(\mathbf c_t-\mathbf r_0)\times\mathbf F_c
=\mathbf0.
\]

定义针内部从根部传向针体的截面 wrench：

\[
\boxed{
\mathbf F_{sec}=\mathbf F_c,
\qquad
\mathbf M_{sec}
=\mathbf M_c^{c_t}
+(\mathbf c_t-\mathbf r_0)\times\mathbf F_c.
}
\]

取与针轴正交的两个横向单位向量 \(\mathbf e_b,\mathbf e_c\)，定义针基

\[
\mathbf R_N=[\mathbf a_0\ \mathbf e_b\ \mathbf e_c],
\]

局部结果量为

\[
{}^N\mathbf F=\mathbf R_N^\mathsf T\mathbf F_{sec},
\qquad
{}^N\mathbf M=\mathbf R_N^\mathsf T\mathbf M_{sec},
\]

\[
\boxed{
\mathbf s_N
=[N,V_b,V_c,T,M_b,M_c]^\mathsf T.
}
\]

由此

\[
\sigma_{ab,max}
=\frac{|N|}{A}
+\frac{d/2}{I}\sqrt{M_b^2+M_c^2},
\]

\[
\tau_{ub}
=\frac{|T|(d/2)}{J}
+\frac{4}{3A}\sqrt{V_b^2+V_c^2},
\]

\[
\sigma_{vm}^{ub}
=\sqrt{\sigma_{ab,max}^2+3\tau_{ub}^2}.
\]

没有 \(\sigma_y,\sigma_u\) 和根部几何证据时，只输出名义应力监控，不输出认证失效。

### 5.9 \(\mathsf M_0\) 的本征未知量与残量

固定支持图表、开闭、摩擦和安装活动分支后，

\[
\mathbf y_A
=
[
\boldsymbol\eta_b,
\delta_s\ \text{or}\ r_H,
\{\boldsymbol\lambda_j\},
\{\boldsymbol\xi_j\}_{chart}
].
\]

规范广义方程为

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
\end{bmatrix}.
}
\]

并同时检查：

\[
g_{cone}>0,
\quad
g_{shaft}>0,
\quad
g_{mount}>0,
\]

\[
0\le\delta_s\le4\ \mathrm{mm}.
\]

A embedded kernel 不含法向主动推力方程；背板运动是规定边界，contact-only wrench 是后处理反力。

### 5.10 条件材料扩展 \(\mathsf M_1\)

每个物理材料面片 k 接收归一化支持权重

\[
\sum_{k\in\mathcal P(j)}w_{kj}=1.
\]

无损容量利用率记为

\[
r_k^0(\mathbf z_k)
=\inf\{
\gamma>0:
\mathbf z_k/\gamma\in\mathcal C_{0,k}
\}.
\]

为修复软化末端，定义

\[
\boxed{
0\le\delta_{d,k}\le\delta_{f,k}
}
\]

和

\[
0\le\varrho_k<1,
\qquad
A_k>0,
\qquad
T_{0,k}>0,
\qquad
G_{c,k}^{mix}>0,
\]

\[
q_k(\delta_{d,k})
=\varrho_k+(1-\varrho_k)
\left(1-\frac{\delta_{d,k}}{\delta_{f,k}}\right),
\qquad
0\le\delta_{d,k}\le\delta_{f,k}.
\]

演化互补：

\[
\dot\delta_{d,k}\ge0,
\quad
q_k-r_k^0\ge0,
\quad
\dot\delta_{d,k}(q_k-r_k^0)=0.
\]

达到 \(\delta_d=\delta_f\) 后冻结该坐标并移出活动未知量。状态名为

\[
\texttt{SOFTENING\_COMPLETE/RESIDUAL\_ENTRY}
\]

；只有 \(\varrho_k=0\) 时才是零容量失效。这里 \(\varrho_k\) 专指材料残余容量比，与第 5.3 节的数值投影尺度无关。

令

\[
\bar\delta_d=\min(\delta_d,\delta_f),
\]

并在具有经标定混合模态断裂能时取

\[
\boxed{
\delta_{f,k}
=
\frac{2G_{c,k}^{mix}}
{(1-\varrho_k)T_{0,k}}.
}
\]

线性软化耗散候选为

\[
\mathcal D_{m,k}
=
A_k(1-\varrho_k)T_{0,k}
\left(
\bar\delta_d
-\frac{\bar\delta_d^2}{2\delta_{f,k}}
\right).
\]

该耗散式只对应超过残余牵引的软化部分。若 \(\varrho_k>0\)，必须显式拆分

\[
\mathbf t_k
=\mathbf t_{res,k}+\mathbf t_{diss,k},
\]

并冻结

\[
\boxed{
\dot{\mathcal D}_{m,k}
=\mathbf t_{diss,k}\cdot\dot{\mathbf j}_k\ge0,
}
\]

同时为

\[
\mathcal P_{res,k}
=\mathbf t_{res,k}\cdot\dot{\mathbf j}_k
\]

指定可恢复、摩擦/塑性耗散或其他唯一功通道以及卸载/重载规则。若没有这套残余功规则，功共轭的 cohesive 分支必须限制为 \(\varrho_k=0\)；\(\varrho_k>0\) 只能作为不认证能量的容量 fixture。

此外，该式只有在另行提供真实局部相对运动 \(\mathbf j_k\)、等效分离映射

\[
\delta_{d,k}
=\mathcal K_k(\mathbf j_k,\text{history})
\]

及与上述耗散牵引一致的功共轭关系后才构成材料本构。若 \(\varrho_k=0\)，它退化为

\[
\dot{\mathcal D}_{m,k}
=\mathbf t_k\cdot\dot{\mathbf j}_k\ge0.
\]

若 \(\mathcal K_k\) 未定义，或 \(\varrho_k>0\) 而残余功通道未定义，则该分支必须返回

\[
\texttt{MATERIAL\_MODEL\_UNAVAILABLE}
\]

或仅作为 `uncertified_empirical_capacity_return` 算法 fixture。

创建损伤面片前必须先在版本化兼容核内查询既有物理面片。若空间、表面 ID、材料方向和模型版本兼容，则更新同一面片；只有没有兼容面片时才创建新面片。并发 intents 先确定性匹配/合并，再由唯一外层 commit 写入，禁止同一物理位置因不同 creation event 重复建片而产生隐性愈合。

### 5.11 A standalone 法向力控外包装

A embedded kernel 把背板运动当规定边界；单刺独立拖曳时，在其外增加法向位置 \(u_z\)：

\[
\mathbf y_A^{stand}
=
[u_z,\mathbf y_A]^\mathsf T.
\]

给定 \(u_x\) 和

\[
P_z=0.5\ \mathrm N,
\]

求解

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

正拉力和外功为

\[
\boxed{
R_x=-\mathbf e_x^\mathsf T\mathbf F_c,
\qquad
dW_A=R_xdu_x-P_zdu_z.
}
\]

路径沿 100 mm 连续推进；释放后继续从当前历史搜索，不把位置或损伤重置。若到达碰撞、硬限位或最近允许位置仍无法建立 0.5 N，则返回法向预载不可行。

## 6. A→B 接口和作用—反作用

A 返回墙面对针/单元的 contact-only wrench，记为

\[
{}^A\mathbf W_{wall\to spine}^{O_i}.
\]

B 装配时只做一次旋转和移矩：

\[
{}^A\mathbf F_i
={}^A R_i{}^i\mathbf F_i,
\]

\[
{}^A\mathbf M_i^{O_A}
={}^A R_i{}^i\mathbf M_i^{O_i}
+{}^A\mathbf r_{O_AO_i}
\times{}^A\mathbf F_i.
\]

总 contact-only wrench：

\[
\boxed{
{}^A\mathbf W_B^{O_A}
=\sum_i{}^A\mathbf W_i^{O_A}.
}
\]

梁反力、安装弹簧、接触柔顺与摩擦已经包含在 A 解中，B 不再添加同机制的力或能量。

## 7. B 层：阵列几何、共同平衡与载荷共享

### 7.1 规则格点

针索引 \(i=(r,c)\)：

\[
r=0,\ldots,n_x-1,
\qquad
c=0,\ldots,n_y-1.
\]

未加载球心格点

\[
{}^A\mathbf c_{rc}^0
=
\begin{bmatrix}
x_r\\y_c\\0
\end{bmatrix},
\]

\[
x_r=\left(\frac{n_x-1}{2}-r\right)s_p,
\qquad
y_c=\left(c-\frac{n_y-1}{2}\right)s_p.
\]

使用明确的局部轴

\[
{}^A\mathbf a_{rc}
=
\begin{bmatrix}
\cos\alpha_{rc}\cos\beta_{rc}\\
\cos\alpha_{rc}\sin\beta_{rc}\\
-\sin\alpha_{rc}
\end{bmatrix}.
\]

基座

\[
\boxed{
{}^A\mathbf b_{rc}^0
={}^A\mathbf c_{rc}^0
-L_{rc}{}^A\mathbf a_{rc}.
}
\]

梯度角模式

\[
\alpha_r
=(1-\lambda_r)\alpha_{root}
+\lambda_r\alpha_{head},
\quad
\lambda_r=\frac r{n_x-1},
\]

\[
L_r=\frac{4\sin80^\circ}{\sin\alpha_r}\ \mathrm{mm}.
\]

### 7.2 B 1.0 共同运动

当前认证板坐标

\[
\mathbf q_B=[u_x,u_z]^\mathsf T.
\]

第 i 根针基座

\[
{}^G\mathbf b_i
=\mathbf p_A^0
+u_x\mathbf e_x
+u_z\mathbf E_Z
+{}^G R_A{}^A\mathbf b_i^0.
\]

所有针共享 \((u_x,u_z)\)，没有逐针背板位移。

### 7.3 逐针 trial 和总 wrench

给定 accepted 快照与共享 DamageStore，

\[
(\mathbf W_i,\mathcal E_i,S_i^{trial},
\mathcal I_{D,i})
\in
\mathcal A_i(
\mathbf q_B,S_i^n,D^n,\mathbf p_i).
\]

搬到 B 参考点并求和：

\[
\mathbf W_B
=\sum_i\operatorname{Transport}_{O_i\to O_A}
(\mathbf W_i).
\]

### 7.4 两种外层控制

**恒主动推力平衡模式**

给定 \((u_x,P_z)\)，求 \(u_z\)：

\[
\boxed{
r_z(u_z;u_x,P_z)
=\mathbf E_Z^\mathsf T\mathbf F_B
-P_z=0,
}
\]

或

\[
0\in\mathcal N_B(u_x,u_z)-P_z.
\]

**规定 x/Z 残量模式**

给定 \((u_x,u_z)\)，只返回

\[
r_z=\mathbf E_Z^\mathsf T\mathbf F_B-P_z,
\]

不得在 B 内部偷偷调整 \(u_z\)。

### 7.5 拉力、功与载荷共享

正传感器拉力

\[
\boxed{
R_x=-\mathbf e_x^\mathsf T\mathbf F_B.
}
\]

外部增量功

\[
\boxed{
dW_B=R_xdu_x-P_zdu_z.
}
\]

第 i 根针载荷由

\[
\mathbf W_i
=\mathcal A_i(u_x,u_z,S_i^n,D^n)
\]

与总平衡共同决定。一般

\[
\mathbf W_i\ne\mathbf W_j.
\]

某针事件后切换分支并重解

\[
\mathbf E_Z^\mathsf T\sum_i\mathbf F_i=P_z,
\]

即得到载荷重分配；不引入经验转移矩阵。

### 7.6 光滑分支的凝聚

若

\[
r_z(u_x,u_z)=0
\]

且

\[
k_{zz}=\frac{\partial r_z}{\partial u_z}\ne0,
\]

隐函数定理给出

\[
\boxed{
\frac{du_z}{du_x}
=-\frac{k_{zx}}{k_{zz}},
\qquad
k_{zx}=\frac{\partial r_z}{\partial u_x}.
}
\]

总 wrench 的恒推力凝聚切线为

\[
\boxed{
K_{W,x|P}
=K_{W,x}
-K_{W,z}\frac{k_{zx}}{k_{zz}}.
}
\]

若 \(k_{zz}=0\)、分支不唯一或活动集切换，则该公式不可用，必须保留 graph/割线并完整回调。

### 7.7 B 路径事件

真实力控路径

\[
\mathbf q_B(u_x)
=(u_x,u_z(u_x)).
\]

对任一事件函数 \(\phi_e\)，事件位置必须由

\[
\phi_e(u_x,u_z(u_x))=0
\]

求得。A 对仿射基座 trial 返回的 \(\gamma_e\) 只能作为 predictor。每个括区间和求根评价点都必须重新求 \(u_z\) 平衡。

## 8. B→C 运动、wrench 与合同

### 8.1 四单元局部方向

四个单元局部 +x 沿全局

\[
+\mathbf E_X,\ -\mathbf E_X,
+\mathbf E_Y,\ -\mathbf E_Y.
\]

每个 B wrench 运输到 C：

\[
{}^G\mathbf F_i={}^G R_i{}^i\mathbf F_i,
\]

\[
{}^G\mathbf M_i^C
={}^G R_i{}^i\mathbf M_i^{O_i}
+{}^G\mathbf r_{CO_i}\times{}^G\mathbf F_i.
\]

\[
\boxed{
\mathbf W_{contact}^{G,C}
=\sum_{i=1}^4\mathbf W_i^{G,C}.
}
\]

### 8.2 当前认证子空间

B→C 1.0 的第 i 单元运动子空间是

\[
\mathcal S_i^{1.0}
=\operatorname{span}
\{\mathbf e_{x_i},\mathbf E_Z\}.
\]

因此：

- 全局 +X 对 ±Y 单元需要 local-y；
- 全局 45° 对四单元都需要 local-y；
- rocking 需要角速度和动态几何。

若请求含

\[
\Delta u_{y_i}\ne0
\quad\text{or}\quad
\Delta\boldsymbol\vartheta_i\ne\mathbf0,
\]

则

\[
\boxed{
\texttt{primary\_status}
=\texttt{C\_CONTRACT\_EXTENSION\_REQUIRED}.
}
\]

accepted state、DamageStore、事件、功、曲线和峰值均零推进。

## 9. C 层边界闭合：刚性主模型与条件备选

### 9.1 固定事实引出的主模型选择

固定工程事实要求四个单元相对无质量、无限刚性参考体保持规定安装关系。因而本文将以下模型选为论文主模型：

\[
\boxed{
\text{C-R：共同刚体 pose + 共同同步搜索坐标 }s.
}
\]

这里的 s 是预紧机构唯一的对称径向内部自由度：预紧阶段四个单元相对参考体只允许由同一个 s 产生的规定径向运动；不存在四个独立 \(s_i\)。达到 \(s_{stop}\) 后该机构自由度锁定，此后四个单元与十字参考体保持固定刚体关系。

四个单元的完整运动由

\[
\boldsymbol\xi_i
=\mathbf J_i(\mathbf q_C,s)
\begin{bmatrix}
\Delta\mathbf q_C\\
\Delta s
\end{bmatrix}
\]

唯一导出，不允许四个彼此独立的 Z 位移。

现有 C 文档的

\[
\mathbf E_Z^\mathsf T\mathbf F_i-P_i=0
\quad(i=1,\ldots,4)
\]

只在另一个物理模型成立：

\[
\boxed{
\text{C-I：四个具有独立 Z 行程的法向力控执行器}.
}
\]

C-I 必须给出每个执行器的端点、作用线、源体、目标体和功；否则只能作条件 trial，不能认证真实机构。本文不再把 C-R 与 C-I 混装在同一个平衡系统中。

两种边界与 B 调用模式的互斥映射为：

| C 边界 | B 调用模式 | \(u_{z_i}\) 来源 | \(P_i\) 的位置 |
|---|---|---|---|
| C-R 刚性参考体主线 | `PRESCRIBED_XZ_RESIDUAL` | 由 \((\mathbf q_C,s)\) 的刚体/机构运动学唯一导出 | 只有端点和作用线绑定后，作为 C 级外部广义载荷；不得逐单元强制 \(F_{z_i}=P_i\) |
| C-I 独立 Z 执行器备选 | `UX_PZ_BALANCED` | 每个 B 在给定 \((s,P_i)\) 下独立求解 | 每个独立法向执行器的主动推力 |

任一运行只能选择一行；不得先用 C-I 求出四个 \(u_{z_i}\)，再把其结果伪装成 C-R 刚体 pose。

### 9.2 同步搜索坐标

共同径向搜索满足

\[
\boxed{
u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s.
}
\]

接触对 s 的广义力

\[
Q_s^{contact}
=\sum_{i=1}^4
\mathbf e_{x_i}^\mathsf T\mathbf F_i^G.
\]

驱动反力

\[
\boxed{
Q_s^{drive}
=-Q_s^{contact}
=\sum_{i=1}^4R_{x_i}.
}
\]

对称时全局面内合力可能为零，但四个搜索阻力之和一般不为零。

### 9.3 C-R 预紧阶段的平衡

C-R 对第 i 个 B 的请求必须是

\[
\boxed{
\operatorname{BTrial}_i
=
\operatorname{PRESCRIBED\_XZ\_RESIDUAL}
\left(
u_{x_i}=s,\qquad
u_{z_i}=u_{z_i}(\mathbf q_C,s)
\right).
}
\]

B 返回 contact-only wrench 和法向残量，但不得内部移动 \(u_{z_i}\) 去满足 \(P_i\)。在执行器端点尚未绑定的当前阶段，只能规定 \((\mathbf q_C,s)\) 做运动学/接触响应诊断；这类 scan 不使用逐单元 \(F_{z_i}=P_i\) 作为物理接受条件。

若十字参考体 pose 在预紧台架上被规定，保持台架的反力必须显式记录：

\[
\boxed{
\mathbf W_{hold}^{preload}
=-
\left(
\mathbf W_{contact}
+\mathbf W_{active}
\right).
}
\]

该量是边界反力诊断，不是额外壁面承载。

若参考体在允许自由度上自由，则求

\[
\boxed{
\mathbf0
\in
\sum_{i=1}^4
\mathbf J_i^\mathsf T
\mathcal W_i
+\mathbf Q_{active}
+\mathbf C_{auth}^\mathsf T\boldsymbol\mu_{auth}.
}
\]

其中只有真实授权的台架约束可有非零乘子。

在法向执行器端点未冻结前，\(\mathbf W_{active}\) 与真实执行器功保持 unavailable。因此当前开发只做规定 s 的能力扫描和反力诊断，不宣称 C 预紧已物理认证。

### 9.4 预紧停止

每单元能力特征

\[
\mathbf A_i(s)
=\Phi_A(\mathcal R_{U_i}(s)).
\]

整体能力

\[
A_G(s)
=\mathcal A_G(
\mathbf A_1,\ldots,\mathbf A_4,
\Delta_X,\Delta_Y).
\]

正常停止至少要求

\[
V_{decline}
=
(\text{负斜率})
\lor(\text{能力下降})
\lor(\text{重大损伤}),
\]

\[
G_{stop}
=
G_{valid}
\land G_{plateau}
\land G_{gain}
\land G_{weak}
\land G_{safe}
\land G_{persist}
\land G_{range}
\land\neg V_{decline}.
\]

其中 \(V_{decline}\) 是负斜率、能力下降或重大损伤否决条件，只有其为假才可正常停止。阈值、窗口、置信、滞回和 \(s_{max}\) 均需由单元模拟和留出实验确定；在此之前只允许 `prescribed-s scan`，不自动锁定。

## 10. C 偏心加载的完整理论方程

### 10.1 外载

加载点

\[
\mathbf r_P=50\mathbf E_Z\ \mathrm{mm}.
\]

单位方向

\[
\mathbf d_X=\mathbf E_X,
\qquad
\mathbf d_{45}
=\frac{\mathbf E_X+\mathbf E_Y}{\sqrt2}.
\]

外载 wrench

\[
\boxed{
\mathbf W_{load}^{G,C}
=\lambda_P
\begin{bmatrix}
\mathbf d\\
\mathbf r_P\times\mathbf d
\end{bmatrix}.
}
\]

对应力矩：

\[
\mathbf M_X=50\lambda_P\mathbf E_Y,
\]

\[
\mathbf M_{45}
=\frac{50\lambda_P}{\sqrt2}
(-\mathbf E_X+\mathbf E_Y).
\]

### 10.2 路径约束

偏心点沿 \(\mathbf d\) 的位移为 \(\delta_P\)。若

\[
\mathbf b_P
=
\begin{bmatrix}
\mathbf d\\
\mathbf r_P\times\mathbf d
\end{bmatrix},
\]

则路径约束

\[
\boxed{
\mathbf b_P^\mathsf T\Delta\mathbf q_C
=\Delta\delta_P.
}
\]

### 10.3 六维平衡

在 B 2.x 提供完整 SE(3) response 后，

\[
\mathbf W_i
\in
\mathcal W_i(
\boldsymbol\xi_i,
\mathcal H_i,D,P_i).
\]

系统广义平衡

\[
\boxed{
\mathbf0
\in
\sum_{i=1}^4
\mathbf J_i^\mathsf T\mathcal W_i
+\lambda_P\mathbf b_P
+\mathbf W_{other,authorized}
+\mathbf C_{mode}^\mathsf T\boldsymbol\mu_{mode}
+\mathbf C_{rig}^\mathsf T\boldsymbol\mu_{rig}.
}
\]

该式中的 \(\mathbf W_i\) 是与 \(\boldsymbol\xi_i\) 功共轭的单元局部 wrench，\(\mathbf J_i^\mathsf T\) 已包含对偶运输。若输入已经是搬到 C 的 \(\mathbf W_i^{G,C}\)，则等价地直接写

\[
\mathbf0
\in
\sum_i\mathbf W_i^{G,C}
+\mathbf W_{load}^{G,C}
+\mathbf W_{other,authorized}^{G,C}
+\mathbf W_{mode,authorized}^{G,C}
+\mathbf W_{rig,authorized}^{G,C},
\]

其中后两项分别是与 \(\mathbf C_{mode}^\mathsf T\boldsymbol\mu_{mode}\) 和 \(\mathbf C_{rig}^\mathsf T\boldsymbol\mu_{rig}\) 对应、且确有授权边界的约束 wrench。二者只能选一种装配形式，不能既搬运 wrench 又重复乘同一个运输 Jacobian。

未授权乘子必须为零。不能以加权最小二乘目标很小代替逐分量平衡通过。

### 10.4 姿态模式

`rocking=off`：

\[
\theta_X=\theta_Y=\theta_Z=0.
\]

但固定姿态不授权免费反力矩；接触和真实外载必须自然满足力矩平衡。

`rocking=on`：

\[
\theta_Z=0,
\qquad
\theta_X,\theta_Y\ \text{为未知}.
\]

在单元参考点距 C 为 40 mm 的解析构造中，

\[
\Delta u_{z_1}^{rock}=+40\Delta\theta_Y,
\quad
\Delta u_{z_2}^{rock}=-40\Delta\theta_Y,
\]

\[
\Delta u_{z_3}^{rock}=-40\Delta\theta_X,
\quad
\Delta u_{z_4}^{rock}=+40\Delta\theta_X.
\]

实际接触变化仍由完整 B response 决定。

### 10.5 稳定性

设 \(\mathbf N\) 张成满足路径、模式和真实约束的自由一侧扰动子空间。光滑分支残量为 \(\mathbf r_W\)，定义

\[
\mathbf K_{res,red}
=\mathbf N^\mathsf T
\frac{\partial\mathbf r_W}{\partial\mathbf q_C}
\mathbf N,
\]

\[
\mathbf K_{rest}=-\mathbf K_{res,red}.
\]

保守局部稳定充分条件：

\[
\boxed{
\delta\mathbf z^\mathsf T
\operatorname{sym}(\mathbf K_{rest})
\delta\mathbf z>0
}
\]

对所有非零 admissible 一侧扰动成立。

对摩擦、损伤或集合值分支，必须使用一侧切线/割线、增量功或 graph 的强正则性；Newton 收敛、代数根存在、局部稳定与全路径可恢复性是四个不同判断。

### 10.6 临界承载

令 \(\mathcal R_{stab}(\delta_P)\) 是从合格锁定态沿历史路径可达的稳定、合同有效状态集合。正式能力定义为

\[
\boxed{
F_{crit}
=
\sup\{
\lambda_P\ge0:
\exists\delta_P\ge0,\quad
\exists\mathcal S
\in\mathcal R_{stab}(\delta_P)
\}.
}
\]

首个局部峰不自动等于 \(F_{crit}\)；只有达到物理终止证明，且合同、参数、数值与稳定性均通过，才确认最终能力。

当前 B 1.0 下

\[
F_{crit}=\mathrm{null}.
\]

## 11. 非光滑事件、共享历史与原子事务

### 11.1 事件函数

事件不是“任何当前等于零的约束”。每个事件必须定义成四元组

\[
e=
(\mathcal S_e^{source},G_e,\operatorname{dir}_e,
\mathcal S_e^{target}),
\]

其中 \(G_e\) 是只在源活动分支启用的带符号 guard，\(\operatorname{dir}_e\) 给出允许的单侧 crossing 方向。已处于活动约束且沿整段恒为零的函数必须从候选集中排除。

例如：

| 转移 | 仅在何分支启用 | guard/一侧确认 |
|---|---|---|
| OPEN/NEAR → CLOSED | 开放或近接触 | \(G_e=g_j^{geom}\)，从正值到零 |
| STICK → 摩擦边界/SLIDE | 全粘着一侧 trial | \(G_e=m_j=\mu_j\lambda_{n,j}-\|\boldsymbol\lambda_{t,j}\|\)，从正值到零；随后解滑动一侧确认 |
| CLOSED → OPEN | 闭合接触 | 不能用持续为零的 gap；使用 \(\lambda_{n,j}\) 的一侧反力丧失或接触 graph 可行性丧失 |
| SLIDE → STICK | 滑动分支 | 使用一侧滑移速率/增量趋零和粘着可行性，不使用持续为零的摩擦余量 |
| COMPRESSING → HARD_STOP | 弹簧内点 | \(G_e=\delta_{max}-\delta_s\)，从正值到零 |
| 安全几何 → 碰撞 | 当前无碰撞 | \(G_e=g_k\)，从正值到零 |
| 弹性安全 → 强度边界 | 强度参数可用 | \(G_e=E_{N,y}\) 或 \(E_{N,u}\)，从正值到零 |

支持切换、材料起始、稳定性丧失、表面域和合同覆盖也按同一“源状态 + guard + crossing 方向”结构定义。

令 \(\operatorname{Cross}_e(\chi)\) 表示：

1. \(\mathcal S(\chi^-)\in\mathcal S_e^{source}\)；
2. \(G_e(\chi^-)>0\)、\(G_e(\chi)=0\)；
3. 规定的一侧 trial 指向目标分支；
4. \(G_e\) 不是当前活动分支上的恒零约束。

最早事件坐标为

\[
\boxed{
\chi_e
=\inf\{
\chi>\chi_n:
\exists e,\ \operatorname{Cross}_e(\chi)
\}.
}
\]

在容差内到达同一 \(\chi_e\) 的事件组成同时事件组，不按针 ID 决定物理优先级。

### 11.2 无副作用 trial

定义

\[
(\mathbf z^*,\mathcal I_D^*,\mathcal E^*)
=\operatorname{Trial}
(\mathcal S^n,\chi^*).
\]

必须满足

\[
\operatorname{Trial}
\quad\Longrightarrow\quad
\mathcal S^n\ \text{不变}.
\]

发现更早事件后，所有组件从同一 \(\mathcal S^n\) 重算至 \(\chi_e\)，不能缩放旧 wrench 或复用已经写入的历史。

### 11.3 共享损伤 fixed point

所有 A trial 读取同一 \(D^n\)，只输出 intents。对同一位置级联，迭代

\[
D^{(\ell+1)}
=
\operatorname{Merge}
\left(
D^n,
\{\mathcal I_{D,i}(D^{(\ell)})\}
\right)
\]

直到

\[
D^{(\ell+1)}=D^{(\ell)}
\]

且所有事件、平衡和活动集一致。DamageStore 只有一个内容权威版本；单元快照只保存 id/version/hash。

### 11.4 同位置级联

事件后在同一 \(\chi_e\) 重求平衡。若重分配立即触发新事件，继续同位置处理：

\[
\mathcal S^{(k+1)}
=\mathcal C(\mathcal S^{(k)};\chi_e).
\]

若状态重复、超过级联上限或出现 Zeno 行为，返回明确未收敛/模型状态，不得任意截断后提交。

### 11.5 原子提交

仅当以下全部为真：

\[
G_{accept}
=G_{contract}
\land G_{geometry}
\land G_{equilibrium}
\land G_{complementarity}
\land G_{event}
\land G_{history}
\land G_{energy}
\land G_{quality},
\]

才执行

\[
\mathcal S^{n+1}
=\operatorname{AtomicCommit}(\mathcal S^n,trial).
\]

否则

\[
\boxed{
\mathcal S^{n+1}=\mathcal S^n.
}
\]

### 11.6 释放后的回位边界

接触释放事件只在事件 pose 提交“接触已打开”和可恢复储能预算，不把梁、弹簧和接触压缩瞬间投影到零。若要计算弹性回位，必须另开一条带扫掠碰撞、接触/再接触 guard 和事件定位的准静态或过阻尼路径。若该路径尚未实现，模型在释放 pose 终止当前承载分支，把无法解析的瞬态标为 excluded，而不是跨越潜在碰撞后继续。

## 12. 功与能量闭合

对接受步定义

\[
\Delta\Psi
=\Delta\Psi_{beam}
+\Delta\Psi_{spring}
+\Delta\Psi_{contact}.
\]

系统能量残量

\[
\boxed{
r_E
=
\Delta W_{ext}
-\Delta\Psi
-D_{friction}
-D_{material}
-E_{out}.
}
\]

接受要求

\[
|r_E|\le\epsilon_E,
\qquad
D_{friction}\ge0,
\qquad
D_{material}\ge0.
\]

负 \(\Delta\Psi\) 是释放能来源；\(E_{out}>0\) 是离开建模系统的去向，二者可以同时存在。例如

\[
\Delta W_{ext}=0,
\quad
\Delta\Psi=-U,
\quad
E_{out}=U
\]

时 \(r_E=0\)。若能量已经作为负外功返回执行器或计入某一耗散通道，则不能再记入 \(E_{out}\)。

同位置级联的中间 trial 不分别计功，只对最终事件前后 accepted 状态记净差量。

## 13. 解的局部存在、唯一性与 graph

### 13.1 光滑活动分支

固定活动集后，设

\[
\mathbf R(\mathbf y;\mathbf q)=\mathbf0.
\]

若

\[
\det\left(
\frac{\partial\mathbf R}{\partial\mathbf y}
\right)\ne0,
\]

则隐函数定理保证局部存在唯一

\[
\mathbf y=\mathbf y(\mathbf q)
\]

及一致切线。

### 13.2 非光滑分支

接触、摩擦和刚性约束一般写成

\[
\mathbf0\in\mathcal G(\mathbf y;\mathbf q).
\]

若 graph 在当前点强正则，可定义局部单值延拓；若不满足，则必须：

- 保留集合值输出；
- 通过物理柔顺恢复唯一性；
- 使用认证的分支延拓/选解策略；
- 或返回 `UNRESOLVED/UNAVAILABLE`。

禁止用任意大罚刚度、最小范数或调用顺序静默制造“物理解”。

### 13.3 当前可证明边界

本稿给出方程闭合和接受条件，不声称对任意粗糙面和任意参数全局存在唯一解。多支持、摩擦锥顶点、极限点、失稳和事件级联本来就可能产生非唯一或无解。

## 14. 可观测输出与参数可辨识性

### 14.1 直线拖曳可观测

实验直接给出

\[
y=\{t,x(t),F_x(t),P_z,\text{metadata}\}.
\]

可稳定估计的联合量包括：

\[
S_X(x),\quad
k_{eff},\quad
\mathcal D(F_{peak}),\quad
\mathcal D(\Delta x_{event}),\quad
W_+,\quad r_{repeat}.
\]

其中

\[
W_+
=\int_0^{100\,mm}\max(F_x,0)\,dx.
\]

### 14.2 结构不可辨识性

挂接段组合柔顺近似

\[
\frac1{k_{eff}}
\approx
\frac1{k_{machine}}
+\frac1{k_{fixture}}
+\frac1{k_{beam}}
+\frac1{k_{spring}}
+\frac1{k_{contact}}.
\]

单个 \(k_{eff}\) 不足以唯一拆分各项。

二维坡面上

\[
F_x
=\frac{-h'\lambda_n+\lambda_t}
{\sqrt{1+h'^2}},
\]

说明摩擦、法向力和局部坡度相互混淆。因此标量拖曳不能唯一反演：

- 真实 3D PSD、法向与曲率；
- 唯一 \(\mu\)；
- 各柔顺分量；
- 局部强度、断裂能和损伤核；
- 逐针载荷；
- 完整 6D wrench 与 C 稳定性。

### 14.3 采用的标定对象

首版只拟合

\[
\boxed{
\boldsymbol\theta_{eff}
=\{
S_X,
k_{eff},
\mathcal D(F_{peak}),
\mathcal D(\Delta x_{event}),
r_{repeat}
\}.
}
\]

具体先验、扫描、实验批次和机器配置见 [开发期标定与参数政策](../implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md) 与 [DEV_BOOTSTRAP_PROFILE.yaml](../implementation/DEV_BOOTSTRAP_PROFILE.yaml)。

## 15. 当前可执行模型与阻断矩阵

| 模块/路径 | 数学状态 | 当前开发决定 |
|---|---|---|
| A 几何 + 刚性接触 + Coulomb + 梁 | 修正姿态后闭合 | 实现 |
| A 单边安装弹簧 | A 权威图已闭合 | 实现；修 B 摘要 |
| A `no_damage` | 闭合 | 主线 |
| A empirical capacity | 条件闭合 | 仅修复后做算法 fixture |
| A continuum patch damage | 缺功共轭/参数 | unavailable |
| B x/Z 共同平衡 | 闭合为残量/graph | 实现 |
| B 曲线路径事件 | 需完整延拓求根 | 实现时强制 |
| C 规定 s 扫描 | 条件可表达 | 只输出诊断，不自动锁定 |
| C-R 真实预紧 | 缺执行器端点/台架边界 | unavailable for certification |
| C +X/45° | B 1.0 不覆盖 | 安全拒绝 |
| C rocking | B 1.0 不覆盖 | 安全拒绝 |
| 正式 \(F_{crit}\) | 上游与验证未闭合 | null |

## 16. 验证义务

### 16.1 解析验证

1. 四单元 \(R^\mathsf TR=I,\det R=1\)；
2. wrench–twist 功率不变；
3. 50 mm 偏心力矩；
4. 平面、斜坡、球面和已知支持切换；
5. 梁解析柔顺；
6. A 弹簧四分支；
7. B 两针/多针共同平衡与事件后重分配；
8. C 合同拒绝零推进。

### 16.2 数值验证

- 残量和互补误差；
- 活动集一致性；
- 步长与事件位置收敛；
- 表面分辨率收敛；
- B 非单调 \(u_z(u_x)\) 事件完备性；
- 同位置级联与循环防护；
- 能量误差；
- deterministic replay；
- 随机 seed 扩增后的排名稳定。

### 16.3 实验验证

- 空载/加载链基线；
- 单刺首次挂接、峰值和组合刚度；
- B 预载、方向、刚柔和阵列趋势；
- 新轨迹与重复轨迹分开；
- 整条轨迹/壁面区域留出；
- B 2.x 与 C 边界闭合前不做正式偏心承载认证。

## 17. 结论

在修正姿态坐标类型、采用 A 已冻结的单边弹簧图并关闭未闭合损伤后，A/B 的准静态主链可以严格写成几何查询、SOC/Signorini 接触、梁/安装本构和共同平衡组成的广义方程：

\[
\boxed{
\mathbf0
\in
\mathcal R_B
\left(
\{\mathcal R_{A,i}\},
u_x,u_z,P_z,
\mathcal S^n,D^n
\right).
}
\]

这一路径已经足以支持求解器开发、合成表面敏感性和直线拖曳联合量标定，不必等待白光轮廓仪。

C 的完整理论可严格写成 wrench–twist 对偶下的六维平衡与稳定可达分支问题，但当前仍有两个独立阻断：法向执行器/台架边界未闭合，以及 B→C 1.0 不含 local-y/转动。因此本稿选择刚性参考体 C-R 作为论文主模型，同时要求当前代码对非零 +X、45°、rocking 和正式 \(F_{crit}\) 做安全拒绝。该拒绝是严格模型的一部分，不是模型失败。

最终形成两条清楚的证据链：

\[
\boxed{
\mathsf M_0:
\text{可实现、可做数值验证、可与直线拖曳联合量比较}
}
\]

和

\[
\boxed{
\mathsf M_1/C_{full}:
\text{待功共轭、边界、接口和额外证据关闭后启用}.
}
\]

## 附录 A：变量角色表

| 层 | 规定量 | 主未知量 | 后处理/输出 |
|---|---|---|---|
| A embedded | 根部运动、旧历史、表面、参数 | 接触力、支持、梁变形、弹簧状态 | contact-only wrench、事件、trial |
| A standalone | \(u_x,P_z\) | A 未知量 + \(u_z\) | \(R_x\)、曲线 |
| B balanced | \(u_x,P_z\)、各 A 快照 | \(u_z\)、所有 A 本征未知量 | 总 wrench、逐针载荷、事件 |
| B residual | \(u_x,u_z,P_z\) | 所有 A 本征未知量 | \(r_z\)、总 wrench |
| C prescribed-s | s、边界模式 | B/A 内部状态；可选 C pose | 能力、驱动反力、保持反力 |
| C full | \(\delta_P,s_{stop}\)、方向、授权边界 | C pose、\(\lambda_P\)、B/A 状态 | 六维曲线、稳定性、\(F_{crit}\) |

## 附录 B：本稿相对 accepted 1.0 的闭合修订

1. 针尖姿态改为全局旋转向量左乘 \(\mathbf R_t=\exp([{}^G\theta_b]_\times)\mathbf R_0\)。
2. 明确 \(\mathbf a_t=\mathbf R_t\mathbf e_1\)，不再二次旋转全局 \(\mathbf a_0\)。
3. 写出 contact wrench 到根截面六分量的搬运和局部投影。
4. B 弹簧摘要服从 A 的 `AT_ORIGINAL_LENGTH`、`COMPRESSING`、`HARD_STOP` 图。
5. 损伤坐标限制在 \([0,\delta_f]\)，末端冻结；残余状态不再误称完全失效。
6. 没有局部相对位移和功共轭映射时，材料软化保持 unavailable/empirical。
7. B 事件根沿 \((u_x,u_z(u_x))\) 平衡路径求取。
8. C 刚性参考体与独立 Z 执行器被拆成两个互斥边界模型；论文主线选择 C-R。
9. 预紧停止增加能力下降/重大损伤否决门。
10. 能量账本明确区分释放来源 \(-\Delta\Psi\) 与去向 \(E_{out}\)。

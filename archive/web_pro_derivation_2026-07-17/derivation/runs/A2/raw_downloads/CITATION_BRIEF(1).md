# A2 简短引用说明

> 运行：`A2-r01`  
> 提示词版本：`1.0.0`  
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

### 1.1 三维单边接触—库仑摩擦的二阶锥互补

对第 $j$ 个合法球尖支持，令

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

当 $\mu_j>0$ 时，A2 采用

$$
\boldsymbol\chi_j\in\mathcal L_3,
\qquad
\boldsymbol\psi_j\in\mathcal L_3,
\qquad
\boldsymbol\chi_j^{\mathsf T}\boldsymbol\psi_j=0.
$$

该式同时表达非穿透、非负法向反力、三维摩擦锥、粘着和最大耗散滑移；$\mu_j=0$ 时显式退化为无摩擦 Signorini 互补。它由三维准静态 Coulomb 接触的锥互补形式按本项目正法向和间隙符号重写，而不是惩罚近似 [1,2]。

### 1.2 文献 01 标量载荷比的项目坐标特例

对单支持二维特例

$$
\mathbf n=-\sin\phi\,\mathbf e_x+\cos\phi\,\mathbf E_Z,
\qquad
\boldsymbol\tau=\cos\phi\,\mathbf e_x+\sin\phi\,\mathbf E_Z,
$$

在外部切向驱动力 $+F\mathbf e_x$、向墙法向力 $-W\mathbf E_Z$ 和即将沿 $+\boldsymbol\tau$ 滑动的条件下，

$$
\boxed{
\frac{F}{W}
=\frac{\tan\phi+\mu}{1-\mu\tan\phi}
}.
$$

该式只适用于单支持、二维、刚性局部几何和指定滑移方向；分母非正、$\lambda_n\le0$ 或外载改为拉离时必须另行分支，不能把某一角度称为普适自锁阈值 [3]。

### 1.3 圆截面悬臂针的三维柔顺

令 $\mathbf P_\parallel=\mathbf a\mathbf a^{\mathsf T}$、$\mathbf P_\perp=\mathbf I-\mathbf P_\parallel$、$\mathbf S=[\mathbf a]_\times$，且

$$
A=\frac{\pi d^2}{4},
\qquad
I=\frac{\pi d^4}{64},
\qquad
J=\frac{\pi d^4}{32},
\qquad
G=\frac{E}{2(1+\nu)}.
$$

A2 重推的 Euler–Bernoulli 针尖柔顺为

$$
\begin{bmatrix}
\mathbf u_b\\
\boldsymbol\theta_b
\end{bmatrix}
=
\begin{bmatrix}
\dfrac{L}{EA}\mathbf P_\parallel+\dfrac{L^3}{3EI}\mathbf P_\perp
&-\dfrac{L^2}{2EI}\mathbf S\\[1ex]
\dfrac{L^2}{2EI}\mathbf S
&\dfrac{L}{EI}\mathbf P_\perp+\dfrac{L}{GJ}\mathbf P_\parallel
\end{bmatrix}
\begin{bmatrix}
\mathbf F_c\\
\mathbf M_c
\end{bmatrix}.
$$

该矩阵保留轴向、双向弯曲、扭转和接触力臂，且与轴向安装弹簧分开；文献 07 中有疑点的梁系数未直接迁移。由于本项目 $L/d$ 仅约为 $5$–$6.67$，Euler–Bernoulli 必须与 Timoshenko 分支比较后才能确认误差 [2,4,5]。

### 1.4 无拉力弹簧与硬限位

定义压缩广义力

$$
Q_s=-\mathbf a\cdot\mathbf F_c.
$$

活动状态为：原长端 $\delta_s=0$ 且弹簧力为零；压缩区 $0<\delta_s<4\ \mathrm{mm}$ 时 $Q_s=k_s\delta_s$；硬限位 $\delta_s=4\ \mathrm{mm}$ 时

$$
Q_s=k_s\delta_{\max}+r_H,
\qquad r_H\ge0.
$$

原长端若维持接触需要 $Q_s<0$，必须释放接触或轴向约束，不得令弹簧承受拉力。文献 07 只支持线性移动副、弹簧和限位进入模型的机理；本项目采用自己的无预压、$0$–$4\ \mathrm{mm}$ 边界。工程事实：`ARRAY.MOUNT.AXIAL_SPRING_MODE` [5]。

### 1.5 混合边界与粘着加载斜率

单刺层的混合边界为

$$
\boxed{
\mathbf E_Z\cdot\mathbf F_c=P_z,
\qquad
R_x=-\mathbf e_x\cdot\mathbf F_c
},
\qquad P_z=0.5\ \mathrm N.
$$

因此固定的是法向执行器主动推力，而不是任一局部法向接触力。工程事实：`LOAD.NORMAL.ACTUATOR_OUTPUT`、`LOAD.NORMAL.SINGLE_SPINE`。

在单支持、固定平滑几何、线性总点柔顺和粘着特例中，

$$
\boxed{
\frac{dF}{du_x}=\frac{1}{C_{xx}}
},
\qquad
C_{xx}=\mathbf e_x^{\mathsf T}\mathbf C_p^{\rm total}\mathbf e_x.
$$

该式用于验证接触后弹性位移如何转化为反力；搜索位移必须与啮合后加载位移分开记录。文献 01 只支持相关实验趋势，其试验系统斜率不能直接作为本项目刚度 [2,3]。

## 2. 关键方法选择与结论来源

- A2 主线使用精确 Signorini—Coulomb 锥互补；局部接触柔顺仅作为独立、待标定的可选物理分支，并要求在刚度加密时收敛到刚性接触 [1,2]。
- 非光滑单步求解采用有限弹簧活动分支、二阶锥投影残量和半光滑 Newton/原始—对偶活动集；失败时减步、事件括区和相邻活动集枚举，不以任意惩罚刚度掩盖穿透或无解 [1,2,6]。
- 多支持点保留逐点力和逐点摩擦锥；若存在静摩擦内力非唯一，报告秩、零空间和代表解选择规则，不把数值正则化解释为唯一物理载荷分配 [2]。
- `needle_bending=off` 直接锁定梁变形；刚性安装直接锁定轴向移动副，不用巨大有限 $E$ 或 $k_s$ 伪装刚性极限。工程事实：`NEEDLE.BENDING.SWITCH`、`ARRAY.MOUNT.RIGID_MODE`。
- 锥段、针杆和安装座只做禁止碰撞；其接触不得转化为承载分支。工程事实：`NEEDLE.CONTACT.COLLISION_BOUNDARY`。
- 达到摩擦临界后，A2 只输出潜在滑移方向和事件状态；实际滑移迁移、材料失效、脱离和再挂接由 A3 处理。工程事实：`PROJECT.ARCHITECTURE.DEPENDENCY`。

## 参考来源

[1] https://arxiv.org/pdf/2101.11763

[2] GPT 自带知识：刚体扭量与功共轭、Signorini 互补、二阶锥自对偶与投影、Coulomb 最大耗散、KKT/变分不等式、半光滑 Newton、Euler–Bernoulli/Timoshenko 梁、坐标变换、储能和量纲检查；仅作为通用数学、连续体和数值方法使用，材料参数、摩擦系数、接触刚度和数值容差仍需标定。

[3] 文献01

[4] https://ocw.mit.edu/courses/2-002-mechanics-and-materials-ii-spring-2004/bc25a56b5a91ad29ca5c7419616686f7_lec2.pdf

[5] 文献07

[6] https://epubs.siam.org/doi/10.1137/060671061

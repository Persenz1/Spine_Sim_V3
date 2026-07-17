# B1 简短引用说明

> 运行：`B1-r01`  
> 提示词版本：`1.0.0`  
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

### 1.1 阵列格点与方向约定

\[
x_r=\left(\frac{n_x-1}{2}-r\right)s,
\qquad
y_c=\left(c-\frac{n_y-1}{2}\right)s,
\]

其中 `r=0` 为根部排，`r=n_x−1` 为头部排，c 随局部 `+y` 增加。该式直接落实规则球心格点、`n_x×n_y` 方向和 `2×5/5×2` 独立比较要求。工程事实：`ARRAY.TOPOLOGY.RECTANGULAR`、`ARRAY.SPACING.SET`、`COORDINATE.UNIT.FRAME`。

### 1.2 梯度角、实际针长和基座反算

\[
\alpha_r=(1-\lambda_r)\alpha_{\rm root}+\lambda_r\alpha_{\rm head},
\qquad
\lambda_r=\frac{r}{n_x-1},
\]

\[
L_r=\frac{4\sin80^\circ}{\sin\alpha_r}\ \mathrm{mm},
\qquad
\mathbf b^0_{rc}=\mathbf c^0_{rc}-L_r\mathbf a_{rc}.
\]

因为 `b^0_{z,rc}=L_r sinα_r=4 sin80° mm`，所有梯度安装座出口共面；正向恢复 `b^0+L a=c^0`。规则间距作用于球心投影，梯度引起的安装座 x/y 偏置必须保留。工程事实：`ARRAY.ANGLE.LINEAR_GRADIENTS`、`ARRAY.ANGLE.GRADIENT_LENGTH_COMPENSATION`、`COORDINATE.NEEDLE.AXIS`。

### 1.3 共同运动和 wrench 运输

\[
\Delta\boldsymbol\xi_U^{G,O}
=
\begin{bmatrix}
\Delta u_x\mathbf e_x+\Delta u_z\mathbf E_Z\\
\mathbf0
\end{bmatrix},
\]

\[
\mathbf F^{O'}=\mathbf F^O,
\qquad
\mathbf M^{O'}=\mathbf M^O+(\mathbf r_O-\mathbf r_{O'})\times\mathbf F.
\]

所有针获得同一背板增量，但不具有相同实际球尖位移、弹簧压缩或接触力。A 返回的规范方向为 `A_on_B`，B 不重复换号或添加内部梁/弹簧反力。上游合同：`A_TO_B 1.0.0 accepted`。

### 1.4 有向分离向量与空间相关性

\[
\Delta\mathbf r_{ij}
=\mathbf c_j^0-\mathbf c_i^0,
\qquad
N(m_x,m_y)=(n_x-|m_x|)(n_y-|m_y|),
\]

\[
\rho_{ij}^{(q)}=
\frac{C_q(\mathbf p_i,\mathbf p_j)}
{\sqrt{C_q(\mathbf p_i,\mathbf p_i)C_q(\mathbf p_j,\mathbf p_j)}}.
\]

主数据保存向量而非仅保存距离，以保留搜索方向、横向覆盖和各向异性。相关性由 A1 表面实现、方向协方差、二维 PSD 或联合查询给出；B1 不采用针间 IID，也不把单点命中率乘成阵列成功率。偏航对方向命中和小扰动刚度的权衡只支撑接口和趋势解释，不新增本项目偏航扫描 [1]。共同背板、线性移动副和回差导致阵列扩展饱和的证据只支撑拓扑与风险字段，不迁移论文行程、回差或载荷定律 [2]。相关系数按“同一量在不同间隔/滞后位置的相关”建立，二维空间扩展及方向通道由本轮通用随机场知识给出 [3,4]。

### 1.5 配置规范化和哈希

\[
\texttt{unit\_config\_hash}
=\operatorname{SHA256}
\left(\operatorname{JCS}(\texttt{normalized\_config\_payload})\right).
\]

先完成唯一单位换算，再按 `(r,c)` 行优先序列化针级数组。RFC 8785 提供确定性 JSON 规范表示 [5]，SHA-256 采用 NIST Secure Hash Standard [6]。该选择用于检测配置、实际 `L_r`、参数包和状态快照误配，不构成新的工程物理事实。

### 1.6 梁尺度一致性检查

\[
I=\frac{\pi d^4}{64},
\qquad
\mathcal C_\perp\propto\frac{L^3}{EI}.
\]

该关系仅检查梯度实际长度是否同时进入梁参数，并不替代 A 的三维梁本构、接触柔顺或强度模型 [4]。

## 2. 关键方法选择与结论来源

- `2×5` 与 `5×2` 使用同一表面坐标和搜索方向比较，只交换 x/y 针数；不得旋转表面样本。工程事实：`ARRAY.TOPOLOGY.RECTANGULAR`。
- 固定角和梯度均以规则球心投影格点为主约束，安装座出口由针轴和实际长度反算；真实 CAD 冲突保留为未决检查。工程事实：`ARRAY.SPACING.SET`、`ARRAY.ANGLE.GRADIENT_LENGTH_COMPENSATION`。
- 刚性安装与独立弹簧安装使用同一针级外部接口，但弹簧压缩、余量和硬限位由 A 所有；刚性模式不以巨大有限刚度伪装 [2]。
- 文献04的细粒砖 `57.9°` 和偏航 `10°–20°` 仅是其对象和假设下的预测/折中，未升级为本项目固定参数 [1]。
- 文献07的 `5 mm` 行程、通道间隙、刚度和承载曲线未迁移；本项目坚持无预压、无拉力、`0–4 mm` 压缩和 4 mm 硬限位 [2]。
- B1 只生成 `embedded_constitutive_trial` 请求骨架，不施加每针法向载荷，不求活动集、载荷共享或重分配。上游合同：`A_TO_B 1.0.0 accepted`。
- 高碳钢参数、制造误差、表面相关长度、弹簧采样点、主动推力离散点和数值容差保持 `unavailable/待标定`。工程事实：`UNRESOLVED.REGISTRY.GLOBAL`。

## 参考来源

[1] 文献04

[2] 文献07

[3] https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm

[4] GPT 自带知识：规则矩形格点、刚体齐次变换、参考点力矩运输、数组广播、二维随机场协方差矩阵、圆截面二次矩和 Euler–Bernoulli 柔顺尺度；仅作为通用数学、力学和数据合同知识使用，真实 CAD、材料参数、相关性参数和数值容差仍需验证或标定。

[5] https://www.rfc-editor.org/rfc/rfc8785.html

[6] https://csrc.nist.gov/pubs/fips/180-4/upd1/final

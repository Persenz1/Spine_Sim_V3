# A3 简短引用说明

> 运行：`A3-r01`  
> 提示词版本：`1.0.0`  
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

在固定光滑支持分支上，球尖球心、原表面支持点和偏置法向的几何闭合为

$$
\mathbf c_t-\mathbf p(\boldsymbol\xi)-r\mathbf n(\boldsymbol\xi)=\mathbf0,
\qquad
\dot{\mathbf c}_t=
\begin{bmatrix}
\mathbf p_{,1}+r\mathbf n_{,1}&
\mathbf p_{,2}+r\mathbf n_{,2}
\end{bmatrix}
\dot{\boldsymbol\xi}-\dot c_n\mathbf n.
$$

该式用于三维接触点连续迁移；支持图表退化、面—边—顶点切换和多个等距支持必须按非光滑事件处理，不能用平均法向或“沿表面移动一步”替代闭合求解 [1]。

首版局部材料起始域采用有限控制体应力代理，并保留方向性、压力敏感的 Mohr–Coulomb 候选结构：

$$
\Phi_{MC}=
\widehat\sigma_I
\frac{1+\sin\phi}{2c\cos\phi}
-
\widehat\sigma_{III}
\frac{1-\sin\phi}{2c\cos\phi}-1.
$$

文献15只支持“材料方向—有限 RVE 平均应力—压力敏感首次失效”的结构；目标表面的控制体尺度、方向变换、$c$ 和 $\phi$ 必须重新标定，不能直接使用该文特定砖材数值 [2,1]。

不可逆线性软化以局部断裂能约束：

$$
q(\delta_d)=
\rho+(1-\rho)\max\left(1-\frac{\delta_d}{\delta_f},0\right),
$$

$$
\delta_f=
\frac{2G_c^{\rm mix}}{(1-\rho)T_0},
\qquad
\mathcal D_m(\delta_f)=A G_c^{\rm mix}.
$$

该结构保留“起始后继续传力—峰后软化—耗散面积为断裂能—完全分离”的证据，同时使用物理控制体/特征长度约束网格依赖；宏观 Mode-I 参数、复合材料界面参数和具体混合模态指数均不得直接迁移 [3,4,5]。

圆截面针体的首版保守组合应力接口为

$$
\sigma_{ab,\max}=
\frac{|N|}{A}+
\frac{R}{I}\sqrt{M_b^2+M_c^2},
$$

$$
\sigma_{\rm vm}^{\rm ub}
=
\sqrt{\sigma_{ab,\max}^2+3(\tau_T+\tau_V)^2}.
$$

`needle_bending=off` 只关闭针体变形，仍必须从刚体接触 wrench 计算截面结果量并检查强度上限；高碳钢牌号、屈服和断裂参数保持待定 [1]。

## 2. 关键方法选择与结论来源

- 达到 A2 摩擦锥边界后，先求多支持全粘着一侧问题；只有全粘着不可行且最大耗散滑移分支可行时才提交真实滑移。工程事实：`UNRESOLVED.A2.FRICTION_STABILITY`；数学闭合使用 [1]。
- “局部接触应力首次越过宏观强度”不能直接等同整个位形脱离；材料启动后必须更新容量并重求 A2 平衡，决定继续承载、滑移、支持切换或释放 [6]。
- 材料容量主线选择“有限控制体应力域 + 不可逆能量正则化软化”；“几何特征结果量容量域”只作为有直接单刺标定时的显式可选分支 [1,2,3,4]。
- 损伤记忆独立于 A1 原始高度场/网格，连续 `100 mm` 轨迹内保留，新独立试验或新随机表面重置。工程事实：`DAMAGE.MEMORY.LIGHTWEIGHT`、`LOAD.DRAG.TRAVEL`。
- 脱离后不重置总路径；梁和弹簧按可逆零载状态回位，损伤保留，再调用 A1 搜索、A2 预载同伦并进入再挂接承载。文献03支持“失接—回位—再挂接—继续承载”的状态结构，但其二维悬架和阵列重分配不迁移到 A3 [7]。
- 墙面材料上限和针体上限必须作为同一平衡状态上的独立事件竞争，不能无解释地压缩为一个标量最小值 [1,6]。

## 参考来源

[1] GPT 自带知识：三维球面接触的微分几何图表、客观滑移速度、Signorini–Coulomb 最大耗散、不可逆损伤互补、圆截面组合应力、非光滑事件括区与事务式状态更新；适用于准静态首版降阶模型，材料参数、核尺度和数值容差仍需验证。

[2] 文献15

[3] 文献14

[4] https://www.civil.northwestern.edu/people/bazant/PDFs/Papers/157.pdf

[5] https://ntrs.nasa.gov/api/citations/20020053651/downloads/20020053651.pdf

[6] 文献05

[7] 文献03

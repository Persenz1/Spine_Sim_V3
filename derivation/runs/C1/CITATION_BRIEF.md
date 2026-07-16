# `C1` 简短引用说明

> 运行：`C1-r01`
> 提示词版本：`1.0.0`
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

第 $i$ 个单元在 $O_A$ 表达的 contact-only wrench 运输到全局参考点 $C$ 时，力和力矩必须同时变换：

$$
\mathbf F_i^{C}=\mathbf R_{CS_i}\mathbf F_i^{O_A},
\qquad
\mathbf M_i^{C}=\mathbf R_{CS_i}\mathbf M_i^{O_A}
+\mathbf r_{O_A/C}^{C}\times\mathbf F_i^{C}.
$$

相应 twist 必须采用对偶变换，使

$$
\left(\mathbf W_i^{O_A}\right)^{\mathsf T}\Delta\boldsymbol\xi_i^{O_A}
=
\left(\mathbf W_i^{C}\right)^{\mathsf T}\Delta\boldsymbol\xi_i^{C}.
$$

该式用于防止只旋转力、遗漏参考点力矩或在错误参考点计算功 [1]。

四个单元共享同一径向搜索坐标 $s$。若

$$
R_{x_i}=-\mathbf e_{x_i}^{\mathsf T}\mathbf F_i,
$$

则由虚功得到

$$
Q_s^{\mathrm{contact}}=-\sum_{i=1}^{4}R_{x_i},
\qquad
Q_s^{\mathrm{drive}}=\sum_{i=1}^{4}R_{x_i}.
$$

因此，对置分支的全局面内力可以相消，而共同驱动反力和内部预紧仍非零；这不是漏算 [2]。

两组对置分支的轴向预紧和不平衡采用

$$
p_X=\frac{R_{x_1}+R_{x_2}}{2},
\quad
\Delta_X=R_{x_2}-R_{x_1},
$$

$$
p_Y=\frac{R_{x_3}+R_{x_4}}{2},
\quad
\Delta_Y=R_{x_4}-R_{x_3}.
$$

对置微刺文献支持“相反切向内力形成预紧、法向能力与剩余切向/行程裕度存在权衡”的结构，但本项目四个单元的实际数值必须来自 B 历史相关显式求解 [3]。

跨单元事件采用

$$
\gamma_C=\min_{i=1,\ldots,4}\gamma_{U_i}.
$$

若 $\gamma_C<1$，当前四单元目标均不可提交；缩短共同增量后，四个单元必须从同一接受快照重新试探。停止条件采用平台、乐观边际收益、最弱分支、安全裕度和保持窗口的合取，而不是总力单阈值 [2]。

## 2. 关键方法选择与结论来源

- 中心机构同步驱动多个径向分支、挂接后通过串联柔顺继续增载，以及分支非均匀分载的机构证据 [4]。
- 对置预紧、柔顺/硬止挡权衡和失效后再挂接的低阶结构证据 [3]。
- Wrench/twist 的 SE(3) 表达变换和功不变交叉检查 [1]。
- 最早事件归约、共享状态 fixed point、两阶段 prepare + 原子提交、最弱分支门槛、因果平台检测和留出验证 [2]。
- 工程事实：`GEOMETRY.CROSS.LAYOUT`、`LOAD.CROSS.SEARCH_SYNCHRONIZATION`、`LOAD.NORMAL.CROSS_GRIPPER`、`KINEMATICS.CROSS.RIGID_REFERENCE`、`UNRESOLVED.C1.STOP_THRESHOLD`、`UNRESOLVED.C1.MAX_SEARCH_DISTANCE`。
- 已接受上游合同：`B_TO_C 1.0.0`；contact-only wrench、事件、DamageStore 和事务语义不分配参考文献号。

## 参考来源

[1] https://modernrobotics.northwestern.edu/chapters/chapter3/

[2] GPT 自带知识：多体虚功与广义力、非光滑事件的最早事件归约、共享状态 fixed-point 迭代、两阶段准备与原子提交、稳健一侧割线/下置信界平台检测、最弱分支门槛和按独立表面实现进行留出/重采样；这些是通用数学、数值和统计方法，具体阈值、容差和实现仍需验证。

[3] 文献09

[4] 文献20

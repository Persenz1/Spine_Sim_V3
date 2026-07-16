# `C2` 简短引用说明

> 运行：`C2-r01`
> 提示词版本：`1.0.0`
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

十字参考点 C 的小增量 twist 映射到第 i 个单元规范参考点 `O_A`：

$$
\Delta\mathbf u_{A_i}^{G}
=
\Delta\mathbf u_C^{G}
+
\Delta\boldsymbol\theta^{G}\times\mathbf r_{A_i/C}^{G},
\qquad
\Delta\boldsymbol\xi_{A_i}^{i}=\mathbf J_i\Delta\boldsymbol\xi_C^{G}.
$$

其功对偶 wrench 运输为

$$
\mathbf W_i^{G,C}=\mathbf J_i^{\mathsf T}\mathbf W_i^{i,O_A},
\qquad
(\mathbf W_i^{i,O_A})^{\mathsf T}\Delta\boldsymbol\xi_{A_i}^{i}
=
(\mathbf W_i^{G,C})^{\mathsf T}\Delta\boldsymbol\xi_C^{G}.
$$

这是刚体点运动、参考点力矩运输和虚功对偶的标准结果；只旋转旧 wrench 不能更新接触状态 [3]。

外载点为工程事实 `LOAD.CROSS.ECCENTRIC_POINT`：

$$
\mathbf W_{\mathrm{load}}^{G,C}
=
\lambda_P
\begin{bmatrix}
\hat{\mathbf d}\\
\mathbf r_P\times\hat{\mathbf d}
\end{bmatrix}.
$$

因此 `+X` 工况有 `M_Y=+50F N·mm`，`45°` 工况有
`M_X=-50F/sqrt(2)`、`M_Y=+50F/sqrt(2)`；符号来自同一作用方向和右手叉乘 [3]。

四单元 contact-only wrench 的唯一装配为

$$
\mathbf W_{\mathrm{contact}}^{G,C}=\sum_{i=1}^{4}\mathbf W_i^{G,C}.
$$

多刺作用点/压力中心和对置分支 wrench 结构可用于检查装配，但实际作用点、自由力偶和历史必须由 B 返回，不能使用随机压力中心或论文峰值替代 [1]。

受约束位移加载的整体平衡写为

$$
\mathbf W_{\mathrm{phys}}
+
\lambda_P\mathbf b_P
+
\mathbf C_{\mathfrak m}^{\mathsf T}\boldsymbol\mu_{\mathfrak m}
+
\mathbf C_{\mathrm{rig}}^{\mathsf T}\boldsymbol\mu_{\mathrm{rig}}
=\mathbf0.
$$

`lambda_P` 属于加载执行器；模式乘子若无真实支承必须为零。该结构结合了整体力/力矩平衡、最小弱分支/裕度思想和虚功所有权 [2,3]。

在唯一、事件外分支上，令 `K_res,red` 为净 wrench 残量对固定加载位移下自由扰动的切线，并取恢复刚度 `K_rest=-K_res,red`。一侧增量功的保守稳定性检查为：

$$
\delta\mathbf z^{\mathsf T}
\frac{\mathbf K_{\mathrm{rest}}+\mathbf K_{\mathrm{rest}}^{\mathsf T}}{2}
\delta\mathbf z>0.
$$

负号来自“稳定接触对正扰动产生反向净 wrench”的作用方向。对摩擦、损伤或集合值 graph，该条件只是充分条件；无可靠下界时应返回未认证，而不是把 Newton 失败称为物理失稳 [3]。

## 2. 关键方法选择与结论来源

- 四分支 wrench 分量相互耦合，不能逐分量独立取最大值；作用点存在性必须与自由力偶和质量状态一起保存 [1]。
- 整体层采用“六维平衡 + 单元 admissible response/graph + 最弱裕度”的结构；文献中的常数线性爪界只作骨架，不替代 B 历史相关响应 [2]。
- 工程事实：`LOAD.CROSS.SEARCH_SYNCHRONIZATION`。`s_stop` 是 C1 内部锁定历史坐标，C2 刚体平移/摇摆不得改写为重新独立搜索。
- 上游合同：`B_TO_C 1.0.0`。四单元允许平移子空间的交集只有全局 Z；正式 `+X`、`45°` 和 rocking 需要版本化 B 2.x 扩展，扩展前必须安全拒绝。
- 工程事实：`LOAD.NORMAL.ACTUATOR_OUTPUT`。`P_i` 是主动推力，不是第二份墙面 contact wrench；其系统 wrench 和功取决于执行器端点与系统边界。
- 工程事实：`KINEMATICS.CROSS.RIGID_REFERENCE`。固定姿态不授权免费反力矩；contact-only 与授权外载无法闭合时应判无平衡。
- 事件缩步、共享 DamageStore fixed point、同位置级联和全局原子提交沿用 `B_TO_C 1.0.0` 与已接受 C1 上下文 [3]。

## 参考来源

[1] 文献17

[2] 文献28

[3] GPT 自带知识：刚体 SE(3) 小增量运动、twist/wrench 对偶与虚功；受约束平衡/KKT 乘子所有权；集合值 graph、事件驱动缩步、事务式状态提交和一侧增量稳定性。作为通用数学与数值方法使用；项目作用线、角度上限、阈值、材料参数和实验约束仍需合同或标定。

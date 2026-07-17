# `C3` 简短引用说明

> 运行：`C3-r01`
> 提示词版本：`1.0.0`
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

### 1.1 等刚度换载仅作为特殊回归基准

若一个承载分支脱离前承担 $F_{\mathrm{lost}}$，其余 $N-1$ 个分支完全等刚度、经历相同位移增量且无其他状态变化，则

$$
\Delta F_k=\frac{F_{\mathrm{lost}}}{N-1},
\qquad k=1,\ldots,N-1.
$$

该式只用于验证“活动集改变后剩余分支增载”的方向和等刚度极限；正式 C3 必须由四单元历史相关响应与六维平衡重求解，不能使用固定均分规则 [1]。

### 1.2 历史相关四单元整体平衡

$$
\mathbf0
\in
\sum_{i=1}^{4}
\mathbf J_i^{\mathsf T}
\mathcal W_i
\left(
\boldsymbol\xi_i,
\mathcal H_i,
\mathcal D,
P_i
\right)
+
\lambda_P\mathbf b_P
+
\mathbf W_{\mathrm{other,authorized}}.
$$

文献 28 支持给定活动集的整体力/力矩平衡和最弱裕度结构；本式进一步用 B 返回的非线性、集合值、历史相关单元 response/graph 替换常数单爪能力域，并绑定事件、姿态和 DamageStore [2,3]。

### 1.3 全局最早事件归约

$$
\gamma_C
=
\min\left(
\gamma_{U_1},\ldots,\gamma_{U_4},
\gamma_{\mathrm{pose}},
\gamma_{\mathrm{graph}},
\gamma_{\mathrm{stability}},
\gamma_{\mathrm{collision}},
\gamma_{\mathrm{domain}}
\right).
$$

若 $\gamma_C<1$，当前目标全部回滚并缩步；四个单元必须从同一 accepted state 和同一 DamageStore 基线重新试探，不能缩放旧 wrench、姿态或损伤意图 [1,3]。

### 1.4 稳定可达分支上的最大承载

$$
F_{\mathrm{crit}}
=
\sup_{\mathsf s\in\mathcal B_{\mathrm{stable,reachable}}}
F_{\mathrm{reaction}}(\mathsf s).
$$

集合 $\mathcal B_{\mathrm{stable,reachable}}$ 只包含经合同、平衡、事件、损伤、功和一侧稳定性认证，并通过连续 accepted 历史或合法事件跳转可达的状态。当前最大观测值或局部峰值只是候选；只有合法终止或分支覆盖证据闭合后才能确认 $F_{\mathrm{crit}}$ [3]。

### 1.5 非光滑峰值候选

$$
D^-F(\delta_P^*)\ge0,
\qquad
D^+F(\delta_P^*)\le0.
$$

该条件用事件点左右割线、一侧导数或区间斜率实现，允许尖峰、平台和多个局部峰；首个反力下降不自动终止位移控制加载 [3]。

## 2. 关键方法选择与结论来源

- 活动集或单元状态改变后，必须重新求解全部受整体平衡影响的分支；文献 23 的等刚度换载只作特殊解析基准 [1,3]。
- 最大化最小附着裕度可作为当前活动集的局部审计骨架，但能力边界必须来自 B，且事件、姿态或 DamageStore 改变后旧能力对象立即失效 [2,3]。
- 首个针材料/强度事件不等于单元失败；只有版本化单元退化事件函数经完整 B 回调、四单元重平衡和原子提交后跨越，才记录首个单元显著退化 [3]。
- 代数无平衡、代数根但物理失稳、可恢复脱附、不可恢复脱附、数值不收敛和合同未认证必须分别报告 [3]。
- 工程事实：`LOAD.CROSS.ECCENTRIC_POINT`、`LOAD.CROSS.DIRECTIONS` 固定 50 mm 偏心加载点和两个正式方向，不分配参考文献号。
- 工程事实：`LOAD.CROSS.DISPLACEMENT_CONTROL` 要求输出整体反力—位移曲线、峰值和失去稳定平衡的临界状态，不分配参考文献号。
- 工程事实：`DAMAGE.MEMORY.LIGHTWEIGHT` 要求同一次连续承载过程保留轻量损伤历史，不分配参考文献号。
- 工程事实：`PROJECT.OUTPUTS.NO_BINARY_SUCCESS` 要求保留连续量和事件，当前不定义二元成功或综合评分，不分配参考文献号。
- 上游合同：`B_TO_C 1.0.0 accepted` 当前只认证单元局部 x 与全局 Z 平移；正式 `+X/45°` 和真实 rocking 在扩展接受前必须安全拒绝，不能伪装为零承载。

## 参考来源

[1] 文献23

[2] 文献28

[3] GPT 自带知识：历史相关集合值本构/接触响应、非光滑事件括区间与一侧状态、准静态分支延拓、一侧增量稳定性、非光滑峰值定位、稳定可达集合以及多对象原子提交；这些方法仅提供通用数学和算法结构，项目阈值、材料/表面参数、姿态有效域与实验误差仍需实现验证和标定。

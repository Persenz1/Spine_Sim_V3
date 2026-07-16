# B3 简短引用说明

> 运行：`B3-r01`
> 提示词版本：`1.0.0`
> 用途：仅本地归档；不进入任何后续默认上传、交互、模块上下文、集成模型或工程事实审批。

## 1. 关键公式与来源

失效事件前后仍求同一个恒主动推力共同平衡：

$$
P_z\in\mathcal N_U(u_x^e,u_z^-),
\qquad
P_z\in\mathcal N_U(u_x^e,u_z^+).
$$

该式继承工程事实 `LOAD.NORMAL.ACTUATOR_OUTPUT`、`LOAD.NORMAL.ARRAY_UNIT`、B2 accepted 的集合值平衡和 `A_TO_B 1.0.0 accepted`；它表示失效后必须重新调用全部针并重求共同 $u_z$，而不是分发一个“失效针旧载荷包”。

对唯一或历史连续代表分支，逐针重分配审计量为

$$
\Delta\mathbf W_i=\mathbf W_i^+-\mathbf W_i^-,
\qquad
\Delta R_{x,i}=-\mathbf e_x^{\mathsf T}(\mathbf F_i^+-\mathbf F_i^-),
$$

且恒 $P_z$ 平衡给出

$$
\mathbf E_Z^{\mathsf T}\sum_i(\mathbf F_i^+-\mathbf F_i^-)\approx0.
$$

这是共同兼容、静力平衡和事件前后差量的直接结果；集合值刚性分支必须输出配对 graph/分支集合，不能按针 ID 选唯一解 [1]。

共享损伤冲突图采用读/写集合和空间核重叠：

$$
i\sim_Dj
\iff
(W_i\cap W_j\ne\varnothing)
\lor(K_i\cap K_j\ne\varnothing)
\lor(W_i\cap R_j\ne\varnothing)
\lor(W_j\cap R_i\ne\varnothing).
$$

连通分量只用于形成冲突组；最终损伤试探仍由 A 的损伤事务协调器按同一低层损伤律联合生成，不能简单相加或顺序覆盖 [1]。

连续路径和时间映射为

$$
\chi=u_x-u_x^0,
\qquad
0\le\chi\le100\ \mathrm{mm},
\qquad
t=\frac{\chi}{1\ \mathrm{mm/s}}.
$$

工程事实：`LOAD.DRAG.SPEED`、`LOAD.DRAG.QUASI_STATIC`、`LOAD.DRAG.TRAVEL`、`NUMERICS.DRAG.VARIABLE_STEP`。Newton、回溯、事件定位、损伤协调和级联试探不增加物理时间。

候选峰值持续距离和滑动窗口边际增益为

$$
L_{\rm persist}(\rho)=
\max_{I\subset[0,L_x]}
\left\{|I|:\ R_x(\chi)\ge\rho R_{x,\max}\ \forall\chi\in I\right\},
$$

$$
\Delta_wR_x(\chi)=
\max_{\xi\in[\chi,\min(\chi+w,L_x)]}R_x(\xi)-R_x(\chi).
$$

$\rho$、窗口 $w$、平台阈值和统计置信要求均为未决特征配置；文献21的约 5 mm 只能作趋势验证，不能硬编码 [1,4]。

## 2. 关键方法选择与结论来源

- 失效后正式载荷重分配由刚性背板兼容、全部 A 本征响应、恒 $P_z$ 平衡、容量/约束和当前切线或 graph 自动决定；`G4/G8/G_radius` 不作为载荷转移权重 [1]。
- 文献03直接支持“承载—滑脱/释放—回壁—再搜索—再挂接”以及交替脱落/再挂接时总附着可保持非零；其 stalk 机构、刚度、预载和单刺力不迁移为本项目参数 [2]。
- 文献09支持保持、滑脱、未挂接和滑脱后再搜索的递归状态，以及挂接位置—剩余行程—连续力曲线骨架；其独立刺、Poisson 和无动态增载假设只能作统计对照，不能替代 B2+B3 显式共同平衡 [3]。
- 文献21支持弱峰跳过后二次锚定、首批刺脱离后剩余接触继续承载和搜索距离增益趋缓；论文没有逐刺同步力，不能给出重分配系数或通用 5 mm 阈值 [4]。
- 多事件定位采用“全阵列重求平衡—更新共同括区间—定位最早事件”的结构；SUNDIALS 的多根函数括区间与改进割线方法只作数值实现参考，不把 B3 变成 ODE/DAE 时间积分 [5]。
- 半光滑 Newton、约束活动集和 VI 求解只用于 B2/B3 非光滑平衡的数值组织；PETSc 官方接口不替代 A 的接触、摩擦、硬限位或材料物理 [6]。
- `prepare_atomic_commit -> commit/rollback` 的两阶段组织与 PostgreSQL 官方两阶段事务文档相似，但本项目的状态所有权、令牌、版本和原子性以 `A_TO_B 1.0.0 accepted` 为唯一权威 [7]。
- 低维 `UnitCapabilityState` 只有在固定分支、损伤版本不变、事件未跨越和 trust region 内才可使用；当前不能证明低维摘要满足 Markov 性，因此必须保留逐针 opaque 历史和 DamageStore 句柄 [1]。

## 参考来源

[1] GPT 自带知识：共同位移静力重平衡、事件前后差量审计、图连通分量冲突分组、fixed-point 级联、确定性归约、能量账本和历史充分状态判断；作为通用力学、图论、数值与软件工程结构使用，具体物理阈值、损伤律、参数和收敛性仍需实现/实验验证。

[2] 文献03

[3] 文献09

[4] 文献21

[5] https://sundials.readthedocs.io/en/latest/ida/Mathematics_link.html

[6] https://petsc.org/release/manual/snes/

[7] https://www.postgresql.org/docs/current/sql-prepare-transaction.html

## 3. 归档边界

- 本文件只摘录 B3 的关键公式、方法选择和证据边界，不复制完整 `B_MODULE_CONTEXT`。
- 外部资料只支撑数值或事务组织，不提出工程事实变化。
- 本轮无工程事实变化；`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 与正式 1.0.0 基线逐字一致。
- 理论合同完成不等于求解器、CAD、材料参数、真实表面或实验已经验证。

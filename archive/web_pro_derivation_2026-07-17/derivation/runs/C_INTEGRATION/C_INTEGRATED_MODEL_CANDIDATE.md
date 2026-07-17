# 大模块 C：十字主动对爪同步预紧—偏心渐进承载集成模型

> 大模块：`C`  
> 模型版本：`1.0.0-candidate`  
> 工程事实版本：`engineering_fixed_context 1.0.0`  
> 上游公共合同：`B_TO_C 1.0.0 accepted`  
> 输入上下文：`C_MODULE_CONTEXT 0.3.0 accepted`  
> 集成提示词版本：`C_INTEGRATION 1.0.0`  
> 运行：`C_INTEGRATION-r01`  
> 状态：`candidate`  
> 任务性质：C 大模块一致性集成与公共整爪模型冻结；不编写求解器源代码  
> 认证摘要：**C 的理论状态、方程、事件、事务、稳定性、峰值与公共接口已经统一；但 `B_TO_C 1.0.0` 仅认证单元局部 x 与全局 Z 平移。在完整 twist/动态姿态扩展被正式接受前，任何非零正式 `+X` 或 `45°` 偏心加载必须返回 `C_CONTRACT_EXTENSION_REQUIRED`，不得推进任何物理历史，也不得把该安全拒绝解释为零承载或物理失效。**

---

## 0. 文件性质、权威输入与规范性结论

### 0.1 文件性质

本文件将已接受的 C1、C2、C3 历史模型重构为一个规范、阶段化但状态唯一的 C 算子。它不是 `C_MODULE_CONTEXT` 的章节摘要，也不是三个子模型的并列拼接。正式实现应以本文件中的规范对象、方程、状态映射、事件语义、事务边界和认证规则为 C 层唯一入口。

统一算子记为

\[
\boxed{
\mathcal G_C:
\left(
\mathcal S_{C,n},
\Delta\chi,
\{P_i\}_{i=1}^{4},
\mathcal D_n,
\Theta,
\mathcal B
\right)
\mapsto
\left(
\mathcal S_{C,n+1}^{\mathrm{trial/accepted}},
\mathbf W_C,
\mathcal E_C,
\mathcal K_C,
\Sigma_C
\right)
}
\]

其中：

- \(\mathcal S_{C,n}\)：唯一的已接受 C 状态；
- \(\chi\)：阶段无关路径坐标；预紧阶段取 \(s\)，偏心加载阶段取 \(\delta_P\)；
- \(P_i\)：第 \(i\) 单元的恒定法向主动广义推力；
- \(\mathcal D_n\)：共享 `DamageStore` 已接受快照；
- \(\Theta\)：工程、表面、材料、事件、稳定性、停止、峰值、分支和数值配置；
- \(\mathcal B\)：系统边界、真实执行器和试验架约束绑定；
- \(\mathbf W_C\)：C 点完整 wrench、加载反力及分配；
- \(\mathcal E_C\)：针级、单元级、整体事件、同时组、级联和里程碑；
- \(\mathcal K_C\)：局部切线/割线/集合值 graph、稳定性与能力对象；
- \(\Sigma_C\)：主状态、全部诊断、认证等级和事务结果。

### 0.2 权威顺序

1. `engineering_fixed_context 1.0.0`：固定工程事实、边界、集合、开关、接口能力、排除项和未决登记；
2. `C_MODULE_CONTEXT 0.3.0 accepted`：C1–C3 已接受机理、B→C 语义、状态所有权、方程、证据边界、验证风险和未决项；
3. `C_INTEGRATION_PROMPT 1.0.0`：规定本轮的集成方式、输出合同和必须消解的一致性问题；
4. 本文件中的新增内容仅属于**集成推导**：用于统一对象、符号、残量、状态映射、算法和事务，不升级为工程事实或低层材料证据。

若发生冲突，按上述顺序处理；任何冲突、采用定义和影响必须在第 1 节的集成决策表中可追溯。

### 0.3 当前规范性结论

1. C 只有两个连续物理阶段：
   - `synchronous_preload_stage`：唯一共同 \(s\) 上的四单元同步搜索、事件归约、损伤协调和联合停止；
   - `eccentric_progressive_load_stage`：从唯一预紧接受态无损继续，锁定 \(s_{\mathrm{stop}}\)，按 \(\delta_P\) 进行偏心位移加载、六维平衡、渐进事件、峰后路径和能力确认。
2. C 当前状态只能由一个 `CAcceptedState` 表示；旧 `C1PreloadState`、`C2AcceptedState`、`C3AcceptedState` 是迁移来源或只读兼容视图，不得同时充当三个“当前状态”。
3. C 不直接调用 A，不解析或修改 A/B opaque 状态，不指定逐针力、逐针活动集或经验载荷分配。
4. B 返回的 `A_on_B` contact-only wrench 只运输、装配一次；\(P_i\)、径向驱动、加载器和真实约束反力分栏，不得重复计入墙面承载。
5. C 不新增接触、针梁、针轴向弹簧、硬限位、框架或导轨柔顺；rocking 是允许刚体自由度，不是弹性元件。
6. 任一物理事件后，必须重新调用受影响 B 单元；刚性十字主线默认四单元全部重调，并重新求姿态、加载反力、共享损伤和六维平衡。
7. 首针材料/强度失效、单元显著退化、整体峰值、物理无平衡、物理失稳和可恢复/不可恢复脱附互不等价。
8. \(F_{\mathrm{crit}}\) 只能由经认证、可达、稳定且已提交的状态集合定义；未认证、数值或事务停止时保持 `null/unavailable`。
9. 当前 B 1.0 的正式偏心加载能力缺口必须原样保留，不能在 C 集成中被“修复”。

### 0.4 禁止越界

本文件不执行或批准以下事项：

- 不修改 A/B 正式模型、`A_TO_B`、`B_TO_C` 或工程事实；
- 不批准 `B_TO_C 2.x`，只定义扩展要求和关闭验证；
- 不固定 C1 停止阈值、\(s_{\max}\)、显著退化阈值、峰值容差、材料/表面/损伤参数或加载速度；
- 不引入框架/导轨/传动链柔性、惯性、大角度运动、绕 Z 扭转扫描、显式裂纹、碎屑、磨损或地形重网格化；
- 不定义二元抓附成功、综合评分或 `+X/45°` 的先验优劣；
- 不声称求解器、B 2.x、数值验证或目标实验已经完成。

---

# 第一篇：集成决策、唯一状态和规范对象

## 1. C1/C2/C3 集成决策与冲突消解

### 1.1 两阶段、单状态的规范结构

规范阶段枚举为：

```text
CStage:
  PRELOAD_SEARCH
  PRELOAD_EVENT_RESOLUTION
  PRELOAD_ACCEPTED_LOCKED
  ECCENTRIC_LOAD_TRIAL
  ECCENTRIC_EVENT_RESOLUTION
  ECCENTRIC_LOAD_ACCEPTED
  PHYSICAL_TERMINATED
  UNCERTIFIED_STOPPED
  NUMERICAL_OR_TRANSACTION_STOPPED
```

阶段描述物理路径位置和允许的状态迁移；主状态描述当前一次调用的结果。二者不得混为一列。

规范状态迁移为：

```text
PRELOAD_SEARCH
  -> PRELOAD_EVENT_RESOLUTION
  -> PRELOAD_SEARCH
  -> PRELOAD_ACCEPTED_LOCKED
  -> ECCENTRIC_LOAD_TRIAL
  -> ECCENTRIC_EVENT_RESOLUTION
  -> ECCENTRIC_LOAD_ACCEPTED
  -> ... continued eccentric loading ...
  -> PHYSICAL_TERMINATED
```

异常迁移：

```text
any trial stage
  -> UNCERTIFIED_STOPPED
  -> NUMERICAL_OR_TRANSACTION_STOPPED
```

异常状态保留最后一个有效 `CAcceptedState`；它们不创建新的物理历史节点。

### 1.2 旧对象到规范对象的映射

| 旧对象 | 规范映射 | 保留内容 | 被消除的竞争定义 |
|---|---|---|---|
| `C1SearchRequest` | `CTrialRequest`，`stage=PRELOAD_SEARCH` | 共同 \(s\)、四个 \(P_i\)、B/A 快照、DamageStore、停止策略、事件与事务字段 | 独立的 C1 顶层请求类型 |
| `C1SearchTrialResponse` | `CTrialResponse`，`stage=PRELOAD_*` | 四单元原始响应、预紧、事件、损伤、停止和事务字段 | 独立的 C1 响应生命周期 |
| `C1PreloadState` | `CAcceptedState`，`stage=PRELOAD_ACCEPTED_LOCKED` | \(s_{\mathrm{stop}}\)、四个 B/A 状态、DamageStore、wrench、事件、功和锁定规则 | 与后续 C2/C3 并存的“当前状态” |
| `C2LoadRequest`、`C3LoadRequest` | `CTrialRequest`，`stage=ECCENTRIC_LOAD_TRIAL` | \(\delta_P\)、方向、姿态、模式、边界、完整回调、稳定性、峰值策略 | C2/C3 两套加载请求 |
| `C2LoadTrialResponse`、`C3LoadTrialResponse` | `CTrialResponse`，`stage=ECCENTRIC_*` | 六维平衡、姿态、四单元载荷、事件、损伤、稳定性、峰值、事务 | 两套相互重叠的加载响应 |
| `C2AcceptedState` | `CAcceptedState` 的早期加载兼容视图 | C2 刚体、wrench、稳定性、事件和状态 | 与 C3AcceptedState 竞争 |
| `C3AcceptedState` | `CAcceptedState` 的完整加载视图 | C2 全部字段，加退化、曲线、峰值和能力账本 | C2/C3 分裂的历史 |
| `C3UnitContinuationCapsule` | `CUnitContinuationCapsule` | 原始 B 句柄、graph、trust region、事件、能力和回调条件 | 仅 C3 可用的局部对象 |
| `C3EventRecord` | `CEventRecord` | 针/单元/整体层级、括区间、前点后状态、同时组、损伤和提交状态 | C1/C2/C3 三套事件账本 |
| `C3MaximumCapacityResult` | `CMaximumCapacityResult` | 临界能力、峰值区间、临界姿态、四单元分配、事件和证据 | 仅 C3 能理解的终态对象 |

### 1.3 关键重复定义与采用结论

| 一致性问题 | 历史定义差异 | 规范采用定义 | 影响 |
|---|---|---|---|
| 当前状态 | C1、C2、C3 各有 accepted state | 单一 `CAcceptedState`，由 `stage` 和版本化字段区分 | 防止重置、分叉和重复提交 |
| 路径坐标 | C1 用 \(s\)，C2/C3 用 \(\delta_P\) | 阶段无关 \(\chi\)，由 `path_kind` 绑定到 \(s\) 或 \(\delta_P\) | 统一事件、缩步和事务 |
| 法向主动功 | C1 使用 \(-P_i\,du_{z_i}\)；C2/C3 要求完整执行器端点 | 同时保存 `ideal_generalized_force_work` 与 `certified_relative_actuator_work`；未绑定端点时后者不可用 | 消除功的过度解释和重复计入 |
| 固定姿态 | 可被误解为存在固定反力矩 | 固定坐标不自动授权反力；未授权乘子必须为零 | 消除隐藏框架承载 |
| rocking | C2/C3 作为可选姿态自由度 | 仅为刚体 X/Y 小角度自由度；不是柔顺；需 B 动态姿态支持 | 防止旋转旧 wrench 或添加弹簧 |
| 单元能力 | C1 预紧质量、C3 局部能力对象 | 两者均为历史相关、配置化诊断，不是永久极限面 | 事件后必须重建 |
| 失效 | 针事件、单元退化、整体终止容易混用 | 采用分层事件与独立里程碑 | 防止过早终止 |
| 峰值 | C2 只生成曲线，C3 定义最终能力 | 统一峰值账本；只有覆盖/物理终止证据闭合后确认 \(F_{\mathrm{crit}}\) | 保留峰后分支和多峰 |
| 扩展缺口状态 | `C2_CONTRACT_EXTENSION_REQUIRED`、`C3_CONTRACT_EXTENSION_REQUIRED` | 统一为 `C_CONTRACT_EXTENSION_REQUIRED` | 一个安全拒绝语义 |
| contact-only 装配 | C1/C2/C3 重复说明 | `CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1` 作为唯一装配策略 | 恰好装配一次 |
| DamageStore | 各阶段均协调 | 统一由 B/A 协调器拥有；C 只组织跨单元 fixed point 和原子事务 | 防止多次写入和顺序覆盖 |
| 事务 | C1/C2/C3 分别定义提交包 | 一个阶段无关 `CTransactionBundle`，按阶段携带不同物理字段 | 路径、四单元、损伤、事件、功和峰值同时可见 |

### 1.4 不再保留的历史时态

以下文字只作为历史审计，不进入规范模型的当前时态：

- “C2 尚需完成……”
- “C3 尚需完成……”
- “下一阶段应……”
- “不得自动开始 C 集成……”

本文件已经完成 C 模块理论集成；但“理论集成完成”不改变 B 1.0 的运动认证边界，也不代表代码和实验完成。

### 1.5 不可破坏的集成不变量

任一已接受 C 状态必须满足：

1. `s_stop` 在进入偏心加载后恒定；
2. 四个 B accepted snapshots、内部 A opaque bundles 与共享 DamageStore 版本成套匹配；
3. 所有 wrench 均声明作用方向、表达坐标和参考点；
4. contact-only wrench 只装配一次；
5. 任何未授权约束反力均为零，否则状态不可接受；
6. 事件、损伤、功、曲线和峰值只在全局原子提交后推进；
7. 未认证、数值失败或事务失败不创建物理 accepted 节点；
8. 所有低维 capsule 都绑定完整历史、姿态、DamageStore 和 trust region；
9. 任一事件、姿态、DamageStore、控制模式或合同版本变化使相关旧 capsule 失效；
10. `all_status_codes` 永久保留，主状态只作摘要；
11. `F_crit_confirmed=true` 时必须存在可审计的终止或分支覆盖证据；
12. 正式非零偏心加载在 B 1.0 下不能产生 accepted 加载状态。

---

## 2. 唯一坐标、参考点、符号、单位与作用方向

### 2.1 全局与四个单元局部坐标

全局右手坐标系为

\[
\mathcal F_G=\{C,\mathbf E_X,\mathbf E_Y,\mathbf E_Z\},
\]

其中墙面名义平面为 \(X-Y\)，\(+Z\) 从墙面指向背板和自由空间。

第 \(i\) 个单元局部系为

\[
\mathcal F_i=\{O_i,\mathbf e_{x_i},\mathbf e_{y_i},\mathbf E_Z\},
\qquad
\mathbf e_{y_i}=\mathbf E_Z\times\mathbf e_{x_i}.
\]

正式编号：

\[
\begin{aligned}
\mathbf e_{x_1}&=+\mathbf E_X,& \mathbf e_{y_1}&=+\mathbf E_Y,\\
\mathbf e_{x_2}&=-\mathbf E_X,& \mathbf e_{y_2}&=-\mathbf E_Y,\\
\mathbf e_{x_3}&=+\mathbf E_Y,& \mathbf e_{y_3}&=-\mathbf E_X,\\
\mathbf e_{x_4}&=-\mathbf E_Y,& \mathbf e_{y_4}&=+\mathbf E_X.
\end{aligned}
\]

局部到全局旋转矩阵为

\[
\boxed{
\mathbf R_{Gi}=
\begin{bmatrix}
\mathbf e_{x_i}&\mathbf e_{y_i}&\mathbf E_Z
\end{bmatrix}
}
\]

并必须满足

\[
\mathbf R_{Gi}^{\mathsf T}\mathbf R_{Gi}=\mathbf I,
\qquad
\det\mathbf R_{Gi}=+1.
\]

显式矩阵：

\[
\mathbf R_{G1}=
\begin{bmatrix}1&0&0\\0&1&0\\0&0&1\end{bmatrix},
\quad
\mathbf R_{G2}=
\begin{bmatrix}-1&0&0\\0&-1&0\\0&0&1\end{bmatrix},
\]

\[
\mathbf R_{G3}=
\begin{bmatrix}0&-1&0\\1&0&0\\0&0&1\end{bmatrix},
\quad
\mathbf R_{G4}=
\begin{bmatrix}0&1&0\\-1&0&0\\0&0&1\end{bmatrix}.
\]

### 2.2 工程参考点与 B 规范参考点

四个工程安装参考点为

\[
\boxed{
\mathbf O_i=\mathbf C-40\,\mathbf e_{x_i}\ {\rm mm}
}
\]

即

\[
\begin{aligned}
\mathbf O_1&=(-40,0,z_C)\ {\rm mm},&
\mathbf O_2&=(+40,0,z_C)\ {\rm mm},\\
\mathbf O_3&=(0,-40,z_C)\ {\rm mm},&
\mathbf O_4&=(0,+40,z_C)\ {\rm mm}.
\end{aligned}
\]

B 的规范参考点 \(O_{A_i}\) 是未加载针尖球心规则格点的几何中心。定义局部偏置

\[
\boldsymbol\rho_{A/i}^{i}=\overrightarrow{O_iO_{A_i}}.
\]

在 C1 接受构型中的冻结向量为

\[
\boxed{
\mathbf r_{A_i/C}^{0}
=
-40\,\mathbf e_{x_i}
+
\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i}.
}
\]

只有绑定文件显式给出 \(\boldsymbol\rho_{A/i}^{i}=\mathbf0\)，且参考点 ID、几何哈希和版本全部匹配时，才允许令 \(O_A=O_i\)。

中央 \(80\,{\rm mm}\times80\,{\rm mm}\) 空区不与墙面接触；它只通过 \(\mathbf r_{A_i/C}\times\mathbf F_i\) 提供力臂。

### 2.3 搜索、法向和刚体坐标的正方向

- \(+s\)：四个单元各自沿局部 \(+\mathbf e_{x_i}\) 向十字中心搜索；
- \(s_{\mathrm{stop}}\)：预紧接受后冻结的共同径向坐标；
- \(+u_{z_i}\)：远离墙面；向墙压入为 \(du_{z_i}<0\)；
- \(P_i>0\)：理想主动广义力对单元作用为 \(-P_i\mathbf E_Z\)；
- C 点完整刚体坐标：

\[
\boxed{
\mathbf q_C=
\begin{bmatrix}
u_X&u_Y&u_Z&\theta_X&\theta_Y&\theta_Z
\end{bmatrix}^{\mathsf T}.
}
\]

首版固定 \(\theta_Z=0\)。`rocking=on` 只允许 \(\theta_X,\theta_Y\) 的小角度运动；`rocking=off` 固定二者为零，但不自动产生授权反力矩。

### 2.4 当前姿态与四单元完整 twist

以预紧接受构型为加载阶段零增量参考。当前十字参考体旋转和平移为 \(\mathbf R_C,\mathbf p_C\)，则

\[
\mathbf r_{A_i/C}^{G}=\mathbf R_C\mathbf r_{A_i/C}^{0},
\qquad
\mathbf p_{A_i}^{G}=\mathbf p_C+\mathbf r_{A_i/C}^{G}.
\]

C 点小增量 twist 为

\[
\Delta\boldsymbol\xi_C^G=
\begin{bmatrix}
\Delta\mathbf u_C^G\\
\Delta\boldsymbol\theta^G
\end{bmatrix}.
\]

点 \(O_{A_i}\) 的刚体位移为

\[
\boxed{
\Delta\mathbf u_{A_i}^{G}
=
\Delta\mathbf u_C^G
+
\Delta\boldsymbol\theta^G\times\mathbf r_{A_i/C}^{G}.
}
\]

当前单元姿态矩阵为 \(\mathbf R_{Gi}(\mathbf q_C)\)，则送入完整 B 接口的局部 twist 为

\[
\boxed{
\Delta\boldsymbol\xi_{A_i}^{i}
=
\mathbf J_i\Delta\boldsymbol\xi_C^G,
\qquad
\mathbf J_i=
\begin{bmatrix}
\mathbf R_{iG}&-\mathbf R_{iG}[\mathbf r_{A_i/C}^{G}]_\times\\
\mathbf0&\mathbf R_{iG}
\end{bmatrix}.
}
\]

其中 \([\mathbf r]_\times\mathbf v=\mathbf r\times\mathbf v\)。

局部分量为

\[
\begin{aligned}
\Delta u_{x_i}&=\mathbf e_{x_i}^{\mathsf T}
(\Delta\mathbf u_C+\Delta\boldsymbol\theta\times\mathbf r_i),\\
\Delta u_{y_i}&=\mathbf e_{y_i}^{\mathsf T}
(\Delta\mathbf u_C+\Delta\boldsymbol\theta\times\mathbf r_i),\\
\Delta u_{z_i}^{\rm rigid}&=\mathbf E_Z^{\mathsf T}
(\Delta\mathbf u_C+\Delta\boldsymbol\theta\times\mathbf r_i),\\
\Delta\boldsymbol\vartheta_i&=\mathbf R_{iG}\Delta\boldsymbol\theta.
\end{aligned}
\]

可选 \(\eta_i\) 是机构绑定后的法向执行器相对行程，不属于刚体 twist，也不是第二根针级弹簧。

### 2.5 加载点、路径方向和作用—反作用

加载点相对 C 固定为

\[
\boxed{
\mathbf r_P^0=50\,\mathbf E_Z\ {\rm mm}.
}
\]

当前姿态下 \(\mathbf r_P^G=\mathbf R_C\mathbf r_P^0\)，其位移增量为

\[
\Delta\mathbf u_P
=
\Delta\mathbf u_C
+
\Delta\boldsymbol\theta\times\mathbf r_P^G.
\]

正式方向：

\[
\hat{\mathbf d}_X=
\begin{bmatrix}1\\0\\0\end{bmatrix},
\qquad
\hat{\mathbf d}_{45}=
\frac1{\sqrt2}
\begin{bmatrix}1\\1\\0\end{bmatrix}.
\]

加载路径约束为

\[
\boxed{
\hat{\mathbf d}^{\mathsf T}\Delta\mathbf u_P=\Delta\delta_P.
}
\]

定义加载器**作用于爪体**的功共轭反力 \(\lambda_P\)，其 C 点单位 wrench 为

\[
\boxed{
\mathbf b_P(\hat{\mathbf d})=
\begin{bmatrix}
\hat{\mathbf d}\\
\mathbf r_P^G\times\hat{\mathbf d}
\end{bmatrix},
\qquad
\mathbf W_{\rm load}^{G,C}=\lambda_P\mathbf b_P.
}
\]

规范输出取

\[
F_{\rm reaction}=\lambda_P
\]

作为正向位移控制所需的加载力幅值。爪体作用于加载器的 wrench 为 \(-\mathbf W_{\rm load}\)，力和力矩必须同时反号。

两个正式方向的外力矩检查：

\[
\mathbf r_P\times(F\mathbf E_X)=50F\,\mathbf E_Y\ {\rm N\,mm},
\]

\[
\mathbf r_P\times
\left[
\frac{F}{\sqrt2}(\mathbf E_X+\mathbf E_Y)
\right]
=
\frac{50F}{\sqrt2}
(-\mathbf E_X+\mathbf E_Y)\ {\rm N\,mm}.
\]

### 2.6 Wrench 旋转、参考点运输与功不变

B 返回 `A_on_B` contact-only wrench，必须同时声明源表达框架 \(\mathcal F_{S_i}\) 和参考点 \(O_{A_i}\)：

\[
\mathbf W_i^{S_i,O_A}
=
\begin{bmatrix}
\mathbf F_i^{S_i}\\
\mathbf M_i^{S_i,O_A}
\end{bmatrix}.
\]

运输到全局 C 点：

\[
\boxed{
\begin{aligned}
\mathbf F_i^{G,C}&=\mathbf R_{GS_i}\mathbf F_i^{S_i},\\
\mathbf M_i^{G,C}&=
\mathbf R_{GS_i}\mathbf M_i^{S_i,O_A}
+
\mathbf r_{A_i/C}^{G}\times\mathbf F_i^{G,C}.
\end{aligned}
}
\]

若使用 Jacobian 表达，则

\[
\boxed{
\mathbf W_i^{G,C}=\mathbf J_i^{\mathsf T}\mathbf W_i^{i,O_A}.
}
\]

必须验证 wrench–twist 功不变：

\[
\boxed{
\left(\mathbf W_i^{S_i,O_A}\right)^{\mathsf T}
\Delta\boldsymbol\xi_{A_i}^{S_i}
=
\left(\mathbf W_i^{G,C}\right)^{\mathsf T}
\Delta\boldsymbol\xi_C^G.
}
\]

误差必须同时用绝对和相对容差检查；容差由版本化数值配置提供。只旋转力、不运输力矩，或只旋转旧 wrench 而不在新姿态重求 B，均不合法。

### 2.7 公共单位

| 物理量 | 规范单位 |
|---|---|
| 长度、位移、行程、事件括区间 | mm |
| 力、平移广义反力 | N |
| 力矩 | N·mm |
| 角度 | rad |
| 时间 | s |
| 刚度 | N/mm |
| 功、能量 | N·mm |
| 裕度、置信度、事件分数 | 1 |

N 与 N·mm 不得未经版本化长度尺度直接拼成欧氏范数。任何 wrench 归一化矩阵 \(\mathbf S_W\) 必须绑定 `residual_scaling_id/version`。

---

## 3. 规范对象族、状态所有权与可见性

### 3.1 模型身份与不可变绑定

```text
CModelIdentity:
  C_model_version = 1.0.0-candidate
  engineering_context_version = 1.0.0
  upstream_contract = B_TO_C 1.0.0 accepted
  input_context = C_MODULE_CONTEXT 0.3.0 accepted
  integration_prompt_version = 1.0.0
  run_id = C_INTEGRATION-r01
  certification_level:
    theory_integrated = true
    formal_nonzero_eccentric_loading = contract-extension-required
    code_verified = false
    experiment_verified = false
```

```text
CGeometryBinding:
  global_frame_id
  C_reference_point_id
  unit_slots[4]:
    O_i_reference_point_id
    O_A_reference_point_id
    R_Gi
    rho_A_over_i
    transform_id / version
  load_point_reference_id
  r_P_mm = [0, 0, 50]
  geometry_hash
  unit_config_hashes[4]
```

上述对象在一个独立运行内不可变；任何变更必须创建新的运行或显式状态迁移，不得静默覆盖。

### 3.2 唯一已接受状态 `CAcceptedState`

```text
CAcceptedState:
  identity:
    c_state_id
    parent_c_state_id_optional
    commit_receipt_id
    stage
    primary_status
    all_status_codes[]
    model_identity
  path:
    path_kind: COMMON_SEARCH_S | ECCENTRIC_LOAD_DELTA_P
    s_mm
    s_stop_mm_optional
    delta_P_mm_optional
    loading_direction_optional
    load_point_position_optional
  pose_and_constraints:
    q_C[6]
    rocking_mode
    theta_Z_fixed_zero
    authorized_constraint_manifest
    normal_actuator_boundary_manifest
    eta_i_optional[4]
  immutable_bindings:
    geometry_binding
    surface_ids[4]
    parameter_bundle_ids[4]
    configuration_hashes[4]
  low_level_accepted_bundle:
    B_snapshot_handles[4]
    A_opaque_bundle_handles[4]
    B_control_modes[4]
    current_unit_poses[4]
    shared_DamageStore_handle / version / hash
  mechanics:
    raw_B_response_handles[4]
    contact_only_W_i_at_C[4]
    summed_contact_only_W_at_C
    loading_W_optional
    authorized_other_W[]
    residual_or_graph
    lambda_P_optional
    R_x_i_optional[4]
    Q_s_drive_optional
    pair_preload_and_imbalance_optional
    mode_and_rig_multipliers
  unit_continuation:
    capsule_handles[4]
    balance_branch_rank_nullspace_condition[4]
    action_line_CoP_free_couple_availability[4]
    remaining_travel_and_recoverability[4]
  history:
    event_ledger_handle
    damage_and_cascade_ledger
    milestone_ledger
    work_energy_error_ledger
    accepted_curve_handle_optional
    peak_ledger_optional
    branch_lineage_optional
  quality_and_certification:
    domain_geometry_collision_model_parameter_status
    stability_evidence
    replay_manifest
    last_valid_state_id
  continuation:
    full_B_callback_conditions
    legal_next_stages
    contract_extension_requirement_optional
```

`CAcceptedState` 对调用者是 opaque 对象；调用者只能持有并原样传回，不能解析后修改 B/A/DamageStore 或低层历史。

### 3.3 试探对象

```text
CTrialRequest:
  identity / idempotency_key
  parent_accepted_state_id / commit_receipt_id
  requested_stage_operation
  common_path_target_or_increment
  loading_direction_optional
  P_i_N[4]
  rocking_and_boundary_mode
  accepted_B_A_DamageStore_handles
  transforms / reference_points / units / hashes
  event_damage_stability_stop_peak_branch_configs
  requested_B_trial_phase
  requested_raw_outputs
  deterministic_replay_request
```

```text
CTrialResponse:
  request_hash / response_hash
  parent_state_check
  proposed_path_and_pose
  per_unit_full_input_motion
  raw_B_trial_responses[4]
  transported_contact_only_wrenches[4]
  assembled_residual_or_graph
  preload_or_loading_reaction
  events / simultaneous_groups / damage_fixed_point
  degradation / milestones / stability / peak_candidates
  work_energy_error_trial_ledger
  all_status_codes / primary_status
  rollback_tokens[4]
  provisional_intents[4]
  shared_damage_intent
  prepare_eligibility
  last_valid_accepted_state
```

试探响应无副作用；除非形成全局提交收据，否则其中任何状态、功、事件、损伤、曲线或峰值均不得成为 accepted 历史。

### 3.4 单元延拓 capsule

```text
CUnitContinuationCapsule:
  identity / validity_key / versions
  raw_B_response_handle
  accepted_B_snapshot_handle
  accepted_A_opaque_bundle_handle
  DamageStore_dependency
  current_pose / frame / O_A_to_C_transform
  contact_only_wrench / graph
  resultant_axis / CoP / free_couple availability
  balance_branch_rank_nullspace_condition
  active_load_bearing_stick_slip_strength_hardstop_summary
  original_unit_event_group_handles
  tangent_secant_or_admissible_graph
  one_sided_direction / trust_region
  predicted_event_distance_and_bracket
  remaining_spring_and_certified_path_travel
  collision_domain_geometry_model_quality
  normalized_margins / residual_direction_capacity
  uncertainty_and_certification
  full_unit_resolve_callback_requirement
  callback_reason_codes
```

有效性键必须至少哈希：

```text
B contract/model versions
accepted B/A state IDs
DamageStore version
surface/parameter/configuration hashes
current unit pose
O_A -> C transform
control mode and P_i
branch ID
trust region ID
numerical configuration
```

任一组成量变化即失效。

#### 3.4.1 局部整体能力对象

```text
CLocalWrenchCapability:
  parent_CAcceptedState_id
  stage_and_loading_direction
  four_unit_capsule_ids
  four_local_admissible_wrench_graphs
  assembled_local_wrench_graph_at_C
  weakest_normalized_margin_LB
  residual_direction_capacity_LB_UB
  branch_rank_nullspace_condition
  trust_region_and_event_distance
  pose_and_DamageStore_dependency
  conservative_inner_approximation_flag
  omitted_branch_or_nonconvexity_risk
  full_rebuild_conditions
```

在当前固定历史、姿态、活动集和 trust region 内，可定义局部最弱裕度诊断

\[
 c^\star
 =
 \sup\left\{
 c:
 -\lambda_P\mathbf b_P-\mathbf W_{\rm other,authorized}
 \in
 \bigoplus_{i=1}^{4}
 \mathbf J_i^{\mathsf T}\mathcal C_i^{\rm loc}(c)
 \right\}.
\]

该对象只用于事件预测、最弱分支审计和保守局部能力。它不是永久极限面；任一事件、姿态、DamageStore、分支或合同变化后必须失效并重建。若只能构造保守内近似，必须公开有效域和遗漏风险。

### 3.5 事件、事务和能力结果

```text
CEventRecord:
  event_id
  hierarchy: NEEDLE | UNIT | GLOBAL | CERTIFICATION | PEAK_AUDIT
  entity_id
  event_type
  source_B_A_event_ids[]
  path_kind / path_bracket / event_fraction
  pre_event_state_id
  event_point_trial_id
  post_event_state_id_optional
  simultaneous_group_id
  causal_dependencies
  DamageStore_pre_trial_post_versions
  pre_point_post_wrench_pose_graph
  degradation_function_optional
  stability_and_recoverability
  peak_candidate_relation
  localization_error / certification
  committed
  commit_receipt_id_optional
```

```text
CTransactionBundle:
  parent_accepted_state
  target_path_and_pose
  four_B_provisional_intents
  all_internal_A_provisional_states
  one_shared_DamageStore_intent
  event_simultaneous_cascade_ledger
  mechanics_residual_stability_ledger
  work_energy_error_ledger
  curve_peak_milestone_updates
  versions / transforms / hashes / replay_manifest
  prepare_tokens
  global_commit_token
```

```text
CMaximumCapacityResult:
  identity_and_versions
  direction / design / surface / seed / parameter_bundle
  initial_preload_state_id
  F_crit_N | null
  F_crit_confirmed
  current_observed_stable_max_N
  peak_state_or_interval
  peak_delta_P / branch / type / uncertainty
  terminal_status_and_evidence
  critical_q_C_and_rocking
  four_unit_critical_wrench_distribution
  critical_low_level_state_handles
  first_needle_and_first_unit_milestones
  DamageStore_and_remaining_travel
  complete_curve_and_event_handles
  work_energy_quality_certification
  final_accepted_state_id / commit_receipt_id
```

### 3.6 所有权、修改和可见性

| 对象/量 | 物理所有者 | 试探修改者 | 提交者 | 外部可见性 |
|---|---|---|---|---|
| 单刺接触、针梁、针级弹簧、硬限位、材料状态 | A | A/B trial | A/B 随 C 全局提交 | opaque 句柄和摘要 |
| 阵列活动集、逐针共享、单元平衡/graph、单元事件 | B | B trial | B 随 C 全局提交 | 原始响应句柄、wrench、graph、摘要 |
| 共享 DamageStore | A/B 协调器 | 协调器产生 trial 快照 | 随 C 全局提交 | 版本、哈希、事件摘要；内容 opaque |
| 共同 \(s\)、\(s_{\rm stop}\)、\(\delta_P\)、C 位姿 | C | C trial | C | 公开连续量 |
| \(P_i\) 控制输入 | 外部配置/C | 不在 trial 中静默改变 | 新运行或显式控制变更 | 公开 |
| contact-only wrench | B 生成，C 运输 | B trial/C 变换 | 随 C 提交 | 公开完整分量和参考点 |
| 径向驱动、加载器和约束反力 | C/真实机构绑定 | C trial | 随 C 提交 | 分栏公开 |
| 事件分组、里程碑、峰值账本 | C，源事件由 A/B | C trial | C | 公开记录和低层句柄 |
| Newton 缓存、线搜索、分支预测 | 数值求解器 | 数值求解器 | 永不提交为物理状态 | 内部 |
| prepare/rollback token | A/B/C 事务层 | 事务层 | 提交后形成收据 | 仅审计 |
| 原始曲线 | C accepted 历史 | 只在候选提交时追加 | C | 公开 |
| \(F_{\rm crit}\) | C 能力审计 | 只在证据闭合时形成 | C | 公开或 `unavailable` |

### 3.7 可逆状态与不可逆历史

**可逆或当前机械状态**：

- 当前路径坐标、位姿、法向位置；
- 当前 contact-only wrench、graph、切线和作用线；
- 当前弹簧压缩、活动接触和恢复性；
- 当前约束乘子和反力。

**不可逆或路径历史**：

- DamageStore；
- 材料/针体强度失效标记；
- 接触、滑移、脱离、再挂接和硬限位事件序列；
- accepted 路径、分支和级联；
- 功、耗散、数值误差账本；
- 曲线、峰值候选、首次里程碑；
- 版本、哈希、提交收据和重放清单。

不可逆历史只能由全局原子提交推进。新的独立试验或新表面样本才从无损状态开始。

---

# 第二篇：统一方程、装配与去重审计

## 4. C 的阶段化统一方程链

### 4.1 上游唯一物理入口

C 只能调用 B 的无副作用试探入口：

```text
embedded_array_unit_trial(request)
  -> EmbeddedUnitTrialResponse
```

在未来完整姿态扩展中，可以是同一入口的新控制模式或向后兼容的新版本，但 C 的原则不变：

- 从不可变 accepted 快照开始；
- 读取同一共享 DamageStore 版本；
- 返回 contact-only wrench、graph/残量、事件、损伤意图、能力和回滚/提交令牌；
- C 不直接调用 A；
- C 不指定逐针载荷、逐针活动集、经验转移权重或低层参数覆盖；
- C 不按旧结果缩放产生新 trial。

唯一装配策略为：

```text
assembly_policy_id = CONTACT_ONLY_EXTERNAL_ASSEMBLY_V1
```

四个 B contact-only wrench 各运输一次到 C 并求和；\(P_i\)、径向驱动、加载器和真实约束反力保持独立字段。

### 4.2 同步预紧搜索阶段

#### 4.2.1 规定量、未知量和输入

规定：

- 当前 accepted \(s_n\)；
- 共同试探目标 \(s^\star=s_n+\Delta s\)；
- 四个 \(P_i\)；
- 四个 B/A accepted snapshots；
- 同一 DamageStore；
- `rocking=off`；
- 停止、事件、损伤和数值配置。

四个单元共同满足

\[
\boxed{
u_{x_1}=u_{x_2}=u_{x_3}=u_{x_4}=s.
}
\]

每个单元允许有不同的 \(u_{z_i}\)、wrench、活动集、事件、损伤、行程和能力。

#### 4.2.2 法向平衡或 graph

主线控制模式为 `UX_PZ_BALANCED`。第 \(i\) 单元在给定 \(s,P_i\) 下由 B 求 \(u_{z_i}\)：

\[
\boxed{
r_{z_i}(u_{z_i};s,P_i)
=
\mathbf E_Z^{\mathsf T}\mathbf F_i(s,u_{z_i})-P_i=0
}
\]

或退化集合值条件

\[
\boxed{
0\in\mathcal N_{U_i}(s,u_{z_i})-P_i.
}
\]

退化 graph 不得按单元 ID、调用顺序或最小范数静默选成唯一值；若停止策略需要标量，必须使用版本化保守集合映射并保留原 graph。

`PRESCRIBED_XZ_RESIDUAL` 仅用于给定 \(s,u_{z_i}\) 时的残量验证、事件点一致性检查或外层耦合迭代。只有 \(r_{z_i}\) 或 graph 距离通过物理容差时才可称为平衡；求解器退出或代表值存在不能把未闭合残量改写为 `BALANCED`。

法向恒推力求解不得无限向墙推进。若在非承载针体/安装座碰撞、针级弹簧硬限位、最近允许几何位置或 admissible graph 丧失之前仍无法建立目标推力，则必须返回预载不可行或相应未认证/物理状态，并保留最后安全 accepted 状态。

#### 4.2.3 与共同 \(s\) 功共轭的反力

定义正向搜索阻力

\[
R_{x_i}=-\mathbf e_{x_i}^{\mathsf T}\mathbf F_i^G.
\]

contact-only 对共同 \(s\) 的广义力为

\[
\boxed{
Q_s^{\rm contact}
=
\sum_{i=1}^{4}
\mathbf e_{x_i}^{\mathsf T}\mathbf F_i^G
=
-\sum_{i=1}^{4}R_{x_i}.
}
\]

驱动器所需广义反力：

\[
\boxed{
Q_s^{\rm drive}=-Q_s^{\rm contact}
=\sum_{i=1}^{4}R_{x_i}.
}
\]

不能用四个全局力的向量和代替该标量；对称分支的全局面内力可以相消，而 \(Q_s^{\rm drive}\) 仍非零。

#### 4.2.4 对置预紧与完整 wrench

\[
\boxed{
p_X=\frac{R_{x_1}+R_{x_2}}2,
\qquad
p_Y=\frac{R_{x_3}+R_{x_4}}2
}
\]

\[
\boxed{
\Delta_X=R_{x_2}-R_{x_1},
\qquad
\Delta_Y=R_{x_4}-R_{x_3}.
}
\]

完整 contact-only wrench 为

\[
\boxed{
\mathbf W_{\rm contact}^{G,C}
=
\sum_{i=1}^{4}\mathbf W_i^{G,C}.
}
\]

\(p_X,p_Y,\Delta_X,\Delta_Y\) 只是轴向诊断，不能替代完整 wrench。

若规定运动需要额外闭合 wrench，记录

\[
\mathbf W_{\rm support,req}^{\rm preload}
=
-\mathbf W_{\rm contact}^{G,C}
\]

作为诊断；它不是额外墙面承载，也不自动证明真实机构能够承担。

### 4.3 预紧质量、联合停止与搜索上限

每单元能力特征由 B 合法字段构造：

\[
\mathbf A_i(s)=
\Phi_{\chi_A}\!\left(\mathcal R_{U_i}(s)\right).
\]

若某通道为集合值，使用保守下界，例如

\[
A_{ic}^{\rm LB}
=
\inf_{a\in\mathcal A_{ic}}a.
\]

整体预紧质量为版本化聚合：

\[
A_G(s)=
\mathcal A_{\chi_G}
\left(
\mathbf A_1,\mathbf A_2,\mathbf A_3,\mathbf A_4,
\Delta_X,\Delta_Y
\right).
\]

离线标定为每个设计—表面—推力—模型配置生成稳健参考量 \(A_{G,\rm ref}\)。在线只允许使用当前一致 trial、已接受历史和该版本化离线参考；不得读取当前真实运行的未来曲线或未来峰值。令已接受因果窗口的能力下置信界为 \(L_A(s)\)，则平台接近比定义为

\[
\boxed{
\rho_A(s)=\frac{L_A(s)}{A_{G,\rm ref}}.
}
\]

在最近已接受、事件分辨的窗口内构造所有合法一侧割线，并取其乐观上置信界

\[
\boxed{
g_A^U(s_k)
=
\operatorname{UpperConfidence}
\left(
\left\{
\frac{\widetilde A_G(s_b)-\widetilde A_G(s_a)}{s_b-s_a}
\right\}_{s_a<s_b\le s_k}
\right).
}
\]

重大事件后必须重置受影响保持窗口；不能跨未定位事件使用光滑导数。

每个门控通道的归一化有符号裕度为

\[
\widehat m_{ic}=
\begin{cases}
\dfrac{y_{ic}-b_c}{\sigma_c},&\text{下限型},\\[2mm]
\dfrac{b_c-y_{ic}}{\sigma_c},&\text{上限型},
\end{cases}
\]

\[
m_i=\min_c\widehat m_{ic},
\qquad
m_{\min}=\min_i m_i.
\]

安全通道至少覆盖过预紧、材料/针体强度、DamageStore、弹簧剩余行程、硬限位、认证搜索行程、禁止碰撞、表面域/几何质量以及模型/参数可用性。定义

\[
\boxed{
m_{\rm safe}
=
\min_{i,c\in\mathcal C_{\rm safe}}\widehat m_{ic}.
}
\]

不可用、无保守下界或未认证的通道不能按正裕度处理。下文 \(L[\cdot]\) 表示策略配置声明的保守下界或下置信界，而不是任意平滑代表值。

正常停止门槛：

\[
\begin{aligned}
G_{\rm valid}&:\ \text{合同、状态、变换、功、事务和质量认证};\\
G_{\rm plateau}&:\ \rho_A\ge\eta_A;\\
G_{\rm gain}&:\ g_A^U\le\eta_g;\\
G_{\rm weak}&:\ L[m_{\min}]\ge m_{\rm req};\\
G_{\rm safe}&:\ L[m_{\rm safe}]>0;\\
G_{\rm persist}&:\ \text{保持窗口、滞回和置信规则通过};\\
G_{\rm range}&:\ s\le s_{\max}.
\end{aligned}
\]

\[
\boxed{
G_{\rm stop}
=
G_{\rm valid}\land
G_{\rm plateau}\land
G_{\rm gain}\land
G_{\rm weak}\land
G_{\rm safe}\land
G_{\rm persist}\land
G_{\rm range}.
}
\]

其中 \(\eta_A,\eta_g,m_{\rm req}\)、保持窗口、置信度、滞回和 \(s_{\max}\) 均为未决配置，不能硬编码；尤其不能把单元拖拽的 \(100\,{\rm mm}\) 当作整爪搜索上限。

正常停止只有在候选状态通过事件、损伤和事务闭环并原子提交后才成立。

### 4.4 从搜索到锁定的唯一迁移

只有当 `G_stop=true` 且全局提交成功时，状态迁移为

```text
PRELOAD_SEARCH -> PRELOAD_ACCEPTED_LOCKED
```

并冻结

\[
\boxed{
u_{x_i}=s_{\rm stop},
\qquad
ds=0,\quad i=1,\ldots,4.
}
\]

冻结的是 C 层共同径向搜索坐标，不冻结：

- A/B 接触、粘滑、材料、再挂接状态；
- B 内针梁和针级轴向弹簧；
- \(u_{z_i}\) 或未来完整基座姿态；
- contact-only wrench；
- DamageStore 的后续合法演化；
- 剩余行程、事件和能力。

偏心加载不得把 \(s_{\rm stop}\) 归零、重新搜索或给四个单元分配不同径向位移。

### 4.5 偏心渐进加载阶段

#### 4.5.1 路径和完整单元运动

加载阶段规定 \(\delta_P\) 的目标增量，锁定 \(s_{\rm stop}\)，并通过第 2.4 节 Jacobian 计算四个单元的完整 twist。

加载路径约束：

\[
\boxed{
\mathbf b_P^{\mathsf T}\Delta\mathbf q_C
=
\Delta\delta_P.
}
\]

在 B 完整 twist 扩展可用时，未知量可以包括：

- 允许的 \(\mathbf q_C\) 分量；
- \(\lambda_P\)；
- 可选 \(\eta_i\)；
- B 集合值 graph 中的 admissible 分支；
- 真实授权约束的乘子。

#### 4.5.2 六维平衡或集合值残量

令四个单元的历史相关 contact-only response 为

\[
\mathbf W_i
\in
\mathcal W_i
\left(
\boldsymbol\xi_i,\mathcal H_i,\mathcal D,P_i
\right).
\]

统一六维平衡为

\[
\boxed{
\mathbf0
\in
\sum_{i=1}^{4}
\mathbf J_i^{\mathsf T}
\mathcal W_i
+
\lambda_P\mathbf b_P
+
\mathbf W_{\rm other,authorized}
+
\mathbf C_{\mathfrak m}^{\mathsf T}\boldsymbol\mu_{\mathfrak m}
+
\mathbf C_{\rm rig}^{\mathsf T}\boldsymbol\mu_{\rm rig}.
}
\]

其中：

- \(\mathbf W_{\rm other,authorized}\) 只含边界、作用点、对象和功均已明确的真实外部 wrench；
- \(\boldsymbol\mu_{\mathfrak m}\) 是模式约束诊断乘子；
- \(\boldsymbol\mu_{\rm rig}\) 只对真实授权的试验架约束允许非零；
- 未授权乘子必须为零，否则候选依赖隐藏支承，不可接受。

也可直接写成完整残量：

\[
\boxed{
\mathbf r_W
=
\mathbf W_{\rm contact}^{G,C}
+
\mathbf W_{\rm load}^{G,C}
+
\mathbf W_{\rm other,authorized}^{G,C}
=\mathbf0
}
\]

或集合值 graph 包含零。加权最小二乘可作为找根手段，但接受标准必须逐物理分量通过版本化容差；不能因目标函数较小就接受非零未授权 wrench。

#### 4.5.3 固定姿态与 rocking

统一模式约束：

- `rocking=off`：\(\theta_X=\theta_Y=\theta_Z=0\)；
- `rocking=on`：\(\theta_Z=0\)，\(\theta_X,\theta_Y\) 为待求小量；
- 首版不允许大角度或绕 Z 扫描。

固定姿态不授权免费反力矩；必须自然满足

\[
M_X=M_Y=M_Z=0
\]

且对应未授权模式乘子为零。否则返回固定姿态无平衡或未认证状态。

rocking 模式由 X/Y 力矩平衡确定 \(\theta_X,\theta_Y\)。在 \(\rho_{A/i}=0\)、转轴为 C 的解析检查中：

\[
\begin{aligned}
\Delta u_{z_1}^{\rm rock}&=+40\,\Delta\theta_Y\ {\rm mm},\\
\Delta u_{z_2}^{\rm rock}&=-40\,\Delta\theta_Y\ {\rm mm},\\
\Delta u_{z_3}^{\rm rock}&=-40\,\Delta\theta_X\ {\rm mm},\\
\Delta u_{z_4}^{\rm rock}&=+40\,\Delta\theta_X\ {\rm mm}.
\end{aligned}
\]

非零 \(\rho_{A/i}\) 增加

\[
\Delta u_{z_i}^{\rho}
=
\mathbf E_Z^{\mathsf T}
\left(
\Delta\boldsymbol\theta\times
\mathbf R_{Gi}\boldsymbol\rho_{A/i}^{i}
\right).
\]

这些公式只给出运动趋势；压紧、滑移、损伤、脱离和再挂接必须由完整 B response 决定。

### 4.6 稳定性

代数根不等于稳定平衡。令 \(\mathbf N\) 张成固定 \(\delta_P\)、模式约束和真实授权约束下的自由扰动子空间。唯一光滑分支上定义

\[
\mathbf K_{\rm res,red}
=
\mathbf N^{\mathsf T}
\frac{\partial\mathbf r_W}{\partial\mathbf q_C}
\mathbf N,
\qquad
\mathbf K_{\rm rest}
=
-\mathbf K_{\rm res,red}.
\]

保守充分条件为

\[
\boxed{
\delta\mathbf z^{\mathsf T}
\frac{\mathbf K_{\rm rest}+\mathbf K_{\rm rest}^{\mathsf T}}2
\delta\mathbf z>0
}
\]

对所有非零 admissible 一侧扰动成立。

对摩擦、损伤、活动集或集合值分支，应使用：

- 一侧切线或割线；
- 增量功；
- graph 的局部强单调/强正则性；
- 明确的分支和 trust region。

以下事实必须分开：

- Newton 收敛：数值性质；
- 代数平衡存在：静力性质；
- 局部稳定：一侧恢复性质；
- 可恢复性：是否存在后续合法稳定路径；
- 不可恢复脱附：全路径证据。

### 4.7 事件、退化和局部能力

每个单元 capsule 的局部历史关系可写为

\[
\left(
\Delta\mathbf W_i,\Delta\mathcal H_i,\mathcal E_i
\right)
\in
\mathcal G_i^{\rm loc}
\left(
\Delta\boldsymbol\xi_i;
\mathcal H_{i,n},
\mathcal D_n,
P_i,
\chi_i
\right).
\]

只有在合同、姿态、状态、DamageStore、活动集、分支、trust region 和事件距离均不变时，才可使用局部切线/割线/graph 产生候选。任一事件、历史、姿态、DamageStore、控制模式、参考点或合同变化后必须完整回调 B。

单元显著退化采用版本化事件函数族，不硬编码百分比。典型保守最弱裕度：

\[
m_i^{\rm LB}
=
\inf_{\mathbf w\in\mathcal G_i^{\rm admissible}}
\min_{c\in\mathcal C_i}
\widehat m_{ic}(\mathbf w).
\]

可能的事件函数包括

\[
\phi_i^{m}=m_i^{\rm LB}-m_{i,\rm req},
\]

指定方向能力下界、承载 graph 丧失、可恢复到不可恢复转换，或经尺度化的一侧 wrench 跳变。阈值或保守下界缺失时只能返回 `UNIT_SIGNIFICANT_DEGRADATION_UNCERTIFIED`。

### 4.8 当前合同安全拒绝方程

在任何正式偏心加载物理调用前，C 必须先计算四个单元所需完整 twist，并执行合同覆盖审计。

若存在任一非零

\[
\Delta u_{y_i}\ne0
\quad\text{或}\quad
\Delta\boldsymbol\vartheta_i\ne\mathbf0
\]

而当前上游为 `B_TO_C 1.0.0`，则本阶段的规范结果为：

```text
primary_status = C_CONTRACT_EXTENSION_REQUIRED
accepted_state = unchanged
delta_P_increment_accepted = 0
B/A accepted states advanced = false
DamageStore advanced = false
events/work/curve/peak advanced = false
F_crit_confirmed = false
```

不得进入 x/Z 投影、旧 wrench 旋转、固定姿态伪装或经验能力域求解。

### 4.9 两个阶段的实现合同总表

| 项目 | 同步预紧搜索 | 偏心渐进加载 |
|---|---|---|
| 路径坐标 | \(\chi=s\) | \(\chi=\delta_P\) |
| 规定量 | \(s^\star\)、四个 \(P_i\)、rocking=off | \(\delta_P^\star\)、方向、\(s_{\rm stop}\)、模式和系统边界 |
| 主要未知量 | 各 \(u_{z_i}\) 或法向 graph | 允许的 \(\mathbf q_C\)、\(\lambda_P\)、可选 \(\eta_i\)、admissible graph |
| B 控制 | `UX_PZ_BALANCED`；`PRESCRIBED_XZ_RESIDUAL` 仅用于验证/耦合残量 | 需要未来 `PRESCRIBED_SE3_RESIDUAL` 或经机构绑定的扩展模式 |
| 硬约束 | 四个 \(u_{x_i}=s\)；右手坐标；几何/碰撞/行程边界 | \(s=s_{\rm stop}\)、加载点路径、模式约束、yaw=0、真实约束清单 |
| 平衡/graph | 每单元法向平衡；完整 contact-only wrench 作为诊断 | 六维 wrench 平衡、路径约束、模式/机构 graph |
| 允许反力 | 共同径向驱动反力；法向主动输入；规定运动支承仅作诊断 | 加载器反力；仅真实授权试验架反力；未授权模式乘子必须为零 |
| 历史读取 | 四个 B/A accepted states、DamageStore、已接受搜索历史 | 完整锁定预紧态、加载 accepted 历史、四个 B/A states、DamageStore、曲线和峰值账本 |
| 试探写入 | B/A trial、损伤 intents、事件、停止特征、功意图 | B/A trial、姿态、反力、损伤、事件、稳定性、曲线/峰值意图 |
| 接受条件 | 平衡/graph、事件、损伤、功、质量和事务通过 | 合同覆盖、六维平衡、无隐藏支承、稳定性、事件、损伤、功和事务通过 |
| 正常继续 | `C_ACCEPTED_CONTINUE` | `C_ACCEPTED_CONTINUE` |
| 正常阶段终点 | `C_PRELOAD_ACCEPTED_LOCKED` | 经证明的物理终止；必要时 `C_MAXIMUM_CAPACITY_CONFIRMED` |
| 非物理停止 | 参数/模型/数值/事务/安全边界分类 | 合同扩展、参数/模型/域/稳定性/数值/事务分类；\(F_{\rm crit}\) 不确认 |

### 4.10 恒定主动推力与实际接触量

每个 \(P_i\in[0.5,2]\,\mathrm N\) 是执行器的恒定主动广义推力，而不是恒定实际法向接触合力。加载和事件过程中：

- \(\mathbf E_Z^{\mathsf T}\mathbf F_i\) 可以随姿态、活动集、损伤、硬限位和再挂接变化；
- 靠墙侧可以增载，也可能因局部破坏降载；
- 离墙侧可以释放、脱离，也可能在后续路径再挂接；
- C 不得用 \(P_i\) 覆盖 B 返回的 contact-only 法向分量；
- 若法向相对行程未被认证为自由变量，\(\mathbf E_Z^{\mathsf T}\mathbf F_i-P_i\) 应作为传递到安装/控制结构的残量或 graph 信息保留。

---

## 5. 功、能量、执行器和系统边界的唯一账本

### 5.1 总体原则

1. 功和能量只在 accepted 路径上累计；
2. trial、Newton、回溯、事件定位和回滚不累计物理功；
3. 每一项必须声明作用对象、参考点、正方向、系统边界和可用性；
4. 数值残量、约束乘子误差和浮点误差不得记为材料耗散；
5. 同一 \(P_i\) 不能作为 B 控制参数、第二份墙面 wrench 和两份执行器功重复计入。

### 5.2 预紧径向驱动功

\[
\boxed{
dW_s^{\rm drive}=Q_s^{\rm drive}\,ds.
}
\]

当 \(ds>0\) 且接触阻碍搜索时，\(Q_s^{\rm drive}>0\)，驱动输入功为正。

### 5.3 加载器功

\[
\boxed{
dW_{\rm load}=\lambda_P\,d\delta_P.
}
\]

峰后反力下降不改变定义；若 \(\lambda_P>0\) 且 \(d\delta_P>0\)，加载器仍输入正功。

### 5.4 Contact-only 功

每个单元必须通过

\[
dW_{{\rm contact},i}
=
\left(\mathbf W_i^{S_i,O_A}\right)^{\mathsf T}
d\boldsymbol\xi_{A_i}^{S_i}
=
\left(\mathbf W_i^{G,C}\right)^{\mathsf T}
d\boldsymbol\xi_C^G
\]

验证表达和参考点运输一致性。该功是低层净响应的端口功，不得再次拆分出第二份墙面接触功。

### 5.5 法向主动推力的两类功字段

#### 5.5.1 理想单端广义力审计量

在当前理想端口模型下，单元端受力为 \(-P_i\mathbf E_Z\)，可记录

\[
\boxed{
dW_{P_i}^{\rm ideal}
=
-P_i\,du_{z_i}^{\rm port}.
}
\]

该量用于 C1/C2/C3 一致的控制功审计，但不自动等同于真实执行器完整物理功。

#### 5.5.2 经认证的相对执行器功

若真实执行器的源体、目标体、两个端点、作用线和相对行程 \(\eta_i\) 均被版本化绑定，且规定 \(\eta_i>0\) 表示沿 \(-\mathbf E_Z\) 缩短间隙，则

\[
\boxed{
dW_{P_i}^{\rm certified}=P_i\,d\eta_i.
}
\]

只有在源端固定、目标端端口位移与 \(\eta_i\) 的符号关系经认证时，才可证明

\[
dW_{P_i}^{\rm certified}=dW_{P_i}^{\rm ideal}.
\]

否则：

```text
ideal_generalized_force_work = available
certified_relative_actuator_work = unavailable
unavailable_reason = unresolved endpoint/action-line/boundary
```

### 5.6 A/B 内部能量

A/B 负责返回并分栏：

- 球尖接触储能；
- 针梁储能；
- 针级轴向弹簧储能；
- 摩擦耗散；
- 材料/表面损伤耗散；
- 硬限位边界功；
- 接触释放能；
- 数值误差项。

C 只汇总、校验和随事务提交，不重新推导或重分配。

### 5.7 同位置级联

事件点可有

\[
d\chi=0,\qquad
d\mathbf q_C\ne0,\qquad
d\eta_i\ne0.
\]

因此：

- 路径驱动功可能为零；
- 法向执行器相对功可能非零；
- A/B 储能释放和摩擦/损伤耗散可能非零；
- 姿态约束的未授权乘子功必须为零；
- 级联未稳定前所有量保持 trial 状态。

### 5.8 离散账本

```text
CWorkEnergyLedger:
  accepted_path_interval
  radial_drive_work
  eccentric_load_work
  ideal_generalized_force_work[4]
  certified_relative_actuator_work[4] | unavailable
  contact_port_work[4]
  A_B_stored_energy_channels
  A_B_dissipation_channels
  release_energy
  authorized_constraint_work
  unauthorized_multiplier_work_diagnostic
  numerical_residual_work
  floating_point_and_quadrature_error
  balance_check
  commit_receipt_id
```

### 5.9 阶段总外部功与离散平衡检查

预紧阶段的理想控制功审计为

\[
\Delta W_{\rm ext}^{\rm preload,ideal}
=
\int Q_s^{\rm drive}\,ds
+
\sum_{i=1}^{4}\int dW_{P_i}^{\rm ideal}.
\]

若法向执行器端点已认证，则将第二项替换为 `certified_relative_actuator_work`。偏心加载阶段为

\[
\Delta W_{\rm ext}^{\rm load}
=
\int\lambda_P\,d\delta_P
+
\sum_i\int dW_{P_i}^{\rm certified}
+
\Delta W_{\rm authorized\ constraint},
\]

其中不可用的执行器功不得以零填充。每个 accepted 增量应检查

\[
\Delta W_{\rm ext}
=
\Delta U_{A/B}
+
\Delta D_{\rm friction}
+
\Delta D_{\rm damage}
+
\Delta W_{\rm release/hardstop}
+
\varepsilon_{\rm numerical},
\]

并分别报告各通道及数值闭合误差。该检查用于审计，不得用数值误差补足物理耗散。

---

## 6. 柔顺、载荷、失效和损伤去重矩阵

### 6.1 物理位置—所有者—C 处理矩阵

| 物理位置/机理 | 所有者 | 状态量与力/位移 | 能量 | 开关/边界 | C 的处理 | 禁止重复 |
|---|---|---|---|---|---|---|
| 球尖—表面接触 | A | gap、法向/切向接触、摩擦、作用点 | 接触储能、摩擦耗散 | 表面/摩擦参数 | 通过 B 响应读取净 wrench 和事件 | C 不建第二套接触 |
| 露出针体弯曲 | A | 针梁位移、内力、强度 | 梁储能/失效 | `needle_bending` | 只接受 B 净响应和强度事件 | C 不加等效梁 |
| 针级轴向弹簧 | A/B 低层 | \(\delta_s\)、弹簧力、4 mm 硬限位 | 弹簧储能/限位功 | rigid/axial-spring 模式 | 只保留历史、行程和事件 | \(\eta_i\) 不得替代或叠加为第二根弹簧 |
| 针级材料/表面损伤 | A + DamageStore | 损伤变量、强度折减、失效标记 | 损伤耗散 | 具体演化未决 | 组织跨单元冲突；不直接写 | 不相加、不取最大、不按顺序覆盖 |
| 阵列刚性背板兼容 | B | 共同基座运动、逐针兼容 | 由低层汇总 | 背板刚性 | C 提供单元基座运动 | C 不重建逐针兼容 |
| 阵列载荷共享/重分配 | B | 活动集、逐针载荷、graph | 低层端口功 | 历史相关 | 事件后完整回调 B | C 不均分、不用固定权重 |
| 十字参考体 | C | 无质量、无限刚性位姿 | 无弹性储能 | 首版刚体 | 求刚体运动和六维平衡 | 不添加框架柔顺 |
| 共同径向锁定 | C/驱动机构 | \(s_{\rm stop}\)、锁定反力 | 径向驱动功 | C1 接受后冻结 | 作为内部运动约束 | 不当作墙面承载 |
| rocking | C | \(\theta_X,\theta_Y\) 刚体自由度 | 无弹性储能 | off/on，小角度 | 由力矩平衡求解 | 不是弹簧或柔顺 |
| 可选 \(\eta_i\) | 真实机构/C 接口 | 法向执行器相对行程 | 经认证执行器功 | 默认 unavailable | 仅在端点/边界绑定后使用 | 不替代针级弹簧，不静默启用 |
| 加载器 | 外部装置/C | \(\delta_P,\lambda_P\) | \(\lambda_P d\delta_P\) | 位移控制 | 作为唯一加载路径 wrench | 不与 contact-only 重复 |
| 真实试验架约束 | 外部装置 | 明确坐标和乘子 | 真实约束功 | 必须授权 | 独立分栏 | 不以“固定姿态”隐式引入 |
| 单元显著退化 | C 事件审计，原始物理由 A/B | 版本化裕度/能力事件函数 | 不新增耗散 | 阈值未决 | 记录里程碑和触发完整重求 | 不把任意针事件升级为单元失败 |
| 整体失稳/脱附 | C | 六维平衡、稳定、可恢复路径 | 系统层终止证据 | 需模型/数值认证 | 分类并决定终止/继续 | 不用 Newton 失败或峰值代替 |

### 6.2 载荷所有权

| 量 | 是否进入墙面 contact-only 总和 | 是否进入外部平衡 | 是否有独立功通道 |
|---|---:|---:|---:|
| B 返回 contact-only wrench | 是，恰好一次 | 是 | 端口功 |
| \(P_i\) 作为 B 控制输入 | 否 | 取决于系统边界，默认不作为第二份墙面 wrench | 理想/认证执行器功分栏 |
| 共同径向驱动反力 | 否 | 作为内部约束；只有真实外部边界显式建模时另计 | \(Q_s^{\rm drive}ds\) |
| 加载器 \(\lambda_P\mathbf b_P\) | 否 | 是 | \(\lambda_P d\delta_P\) |
| 真实授权试验架反力 | 否 | 是，独立分栏 | 按约束坐标 |
| 未授权模式乘子 | 否 | 不允许加入 | 只能作为隐藏支承诊断 |

### 6.3 失效升级规则

```text
针级滑移
  != 针材料/强度失效
  != 针硬限位
  != 针接触释放

首个针材料/强度失效
  != 单元显著退化

单元显著退化
  != 整体反力峰值

整体反力峰值
  != 物理无平衡
  != 物理失稳
  != 不可恢复脱附

当前无承载
  != 不可恢复脱附
```

升级到更高层事件必须经过相应的完整 B 回调、DamageStore 协调、四单元重平衡、稳定性检查和全局原子提交。

### 6.4 事件后重分配的唯一含义

“载荷重分配”只表示：

1. 低层活动集、损伤或状态改变；
2. B 在当前完整运动和历史上重新求各单元 response；
3. C 重新运输四个 wrench；
4. C 重新求位姿、\(\lambda_P\)、graph 和六维平衡。

它不是：

- 失效载荷平均分给剩余单元；
- 最近邻或距离权重；
- 固定分配矩阵；
- 四个单元峰值缩放；
- \(N_{\rm eff}\times\) 平均单刺力；
- 固定活动集常数 LP 的永久能力域。

文献中的等刚度换载公式只能作为受限解析回归测试，不进入一般正式算子。

---

# 第三篇：状态机、事件、事务与统一算法

## 7. 规范主状态、旧码映射与提交政策

### 7.1 互斥主状态

| 规范主状态 | 含义 | 是否推进物理历史 |
|---|---|---:|
| `C_ACCEPTED_CONTINUE` | 当前预紧或加载稳定候选已原子提交，可继续 | 是 |
| `C_PRELOAD_ACCEPTED_LOCKED` | 联合停止通过，生成唯一锁定预紧态 | 是 |
| `C_BALANCED_DEGENERATE` | 平衡存在但 graph/分支非唯一，且策略完整保留集合 | 条件性 |
| `C_EVENT_REDUCTION_REQUIRED` | 当前目标跨越更早事件 | 否 |
| `C_EVENT_REBALANCE_REQUIRED` | 位于事件点，需损伤/级联后重平衡 | 否 |
| `C_PRELOAD_SEARCH_LIMIT_UNQUALIFIED` | 到 \(s_{\max}\) 但停止门槛未全部通过 | 可提交当前安全终态，但不标合格 |
| `C_PRELOAD_SAFETY_LIMIT` | 下一合法步将越过安全边界 | 只保留最后安全 accepted 状态 |
| `C_CONTRACT_EXTENSION_REQUIRED` | 当前 B 版本不认证所需局部 y/姿态/full twist | 否 |
| `C_STOP_UNCERTIFIED` | 模型、参数、执行器边界、稳定性、域或几何不足 | 否 |
| `C_PHYSICAL_EQUILIBRIUM_INFEASIBLE` | 有效模型下不存在 admissible 代数平衡 | 终止候选 |
| `C_PHYSICAL_INSTABILITY` | 代数根可存在，但所有合法一侧稳定分支消失 | 终止候选 |
| `C_DETACHMENT_RECOVERABLE` | 当前失载但存在合法继续/再挂接路径 | 可在事件后继续 |
| `C_DETACHMENT_IRRECOVERABLE` | 已证明无合法稳定承载/再挂接路径 | 终止候选 |
| `C_PHYSICAL_BOUNDARY_REACHED` | 到达已授权的几何/结构物理边界 | 终止候选 |
| `C_MAXIMUM_CAPACITY_CONFIRMED` | 物理终止/分支覆盖证据闭合并确认 \(F_{\rm crit}\) | 是，终态 |
| `C_STOP_NUMERICAL` | 平衡、事件、损伤、分支或峰值算法未收敛 | 否 |
| `C_TRANSACTION_ERROR` | prepare/commit/持久化失败 | 否 |

### 7.2 旧状态码映射

| 历史码 | 规范码 |
|---|---|
| `CONTINUE_SEARCH` | `C_ACCEPTED_CONTINUE`，阶段 `PRELOAD_SEARCH` |
| `STOP_PRELOAD_ACCEPTED` | `C_PRELOAD_ACCEPTED_LOCKED` |
| `STOP_AT_SEARCH_LIMIT_UNQUALIFIED` | `C_PRELOAD_SEARCH_LIMIT_UNQUALIFIED` |
| `STOP_SAFETY_LIMIT` | `C_PRELOAD_SAFETY_LIMIT` |
| `STOP_IRRECOVERABLE` | `C_DETACHMENT_IRRECOVERABLE`，阶段按发生位置确定 |
| `STOP_UNCERTIFIED`、`C2_STOP_UNCERTIFIED`、`C3_STOP_UNCERTIFIED` | `C_STOP_UNCERTIFIED` |
| `STOP_NUMERICAL`、`C2_STOP_NUMERICAL`、`C3_STOP_NUMERICAL` | `C_STOP_NUMERICAL` |
| `C2_BALANCED_ACCEPTED`、`C3_BALANCED_ACCEPTED` | `C_ACCEPTED_CONTINUE`，阶段 `ECCENTRIC_LOAD_ACCEPTED` |
| `C2_BALANCED_DEGENERATE`、`C3_BALANCED_DEGENERATE` | `C_BALANCED_DEGENERATE` |
| `C2_EVENT_REDUCTION_REQUIRED`、`C3_EVENT_REDUCTION_REQUIRED` | `C_EVENT_REDUCTION_REQUIRED` |
| `C2_EVENT_REBALANCE_REQUIRED`、`C3_EVENT_REBALANCE_REQUIRED` | `C_EVENT_REBALANCE_REQUIRED` |
| `C2_CONTRACT_EXTENSION_REQUIRED`、`C3_CONTRACT_EXTENSION_REQUIRED` | `C_CONTRACT_EXTENSION_REQUIRED` |
| `C2_EQUILIBRIUM_INFEASIBLE`、`C3_GLOBAL_EQUILIBRIUM_INFEASIBLE` | `C_PHYSICAL_EQUILIBRIUM_INFEASIBLE` |
| `C2_PHYSICAL_INSTABILITY`、`C3_GLOBAL_PHYSICAL_INSTABILITY` | `C_PHYSICAL_INSTABILITY` |
| `C3_GLOBAL_DETACHMENT_RECOVERABLE` | `C_DETACHMENT_RECOVERABLE` |
| `C3_GLOBAL_DETACHMENT_IRRECOVERABLE` | `C_DETACHMENT_IRRECOVERABLE` |
| `C3_MAXIMUM_CAPACITY_CONFIRMED` | `C_MAXIMUM_CAPACITY_CONFIRMED` |
| `C2_TRANSACTION_ERROR`、`C3_TRANSACTION_ERROR` | `C_TRANSACTION_ERROR` |

### 7.3 摘要主状态优先级

摘要优先级只决定一个 `primary_status`，不删除 `all_status_codes`，也不改变物理事件顺序：

```text
CONTRACT_VIOLATION / STALE_SNAPSHOT
-> C_CONTRACT_EXTENSION_REQUIRED / KINEMATIC_MODE_UNSUPPORTED
-> OUT_OF_DOMAIN / GEOMETRY_UNCERTAIN / BODY_COLLISION_INVALID
-> MODEL_UNAVAILABLE / PARAMETER_UNAVAILABLE / ACTUATOR_WRENCH_UNCERTIFIED
-> DAMAGE_CONFLICT_UNRESOLVED / TRANSACTION_ERROR
-> NUMERICAL_NONCONVERGENCE
-> C_PHYSICAL_INSTABILITY
-> C_PHYSICAL_EQUILIBRIUM_INFEASIBLE
-> C_DETACHMENT_IRRECOVERABLE
-> STABILITY_UNCERTIFIED / EQUILIBRIUM_DEGENERATE
-> C_EVENT_REDUCTION_REQUIRED / C_EVENT_REBALANCE_REQUIRED
-> C_DETACHMENT_RECOVERABLE / REENGAGED / CASCADE_STABILIZED
-> C_PRELOAD_ACCEPTED_LOCKED / C_ACCEPTED_CONTINUE
```

使用物理终止码的前提是合同、模型、参数、域、几何、事件定位和数值均已认证。否则只能返回更高优先级的未认证或数值状态。

### 7.4 正交事件与里程碑

主状态之外，必须保留：

- 针级事件；
- 单元级事件；
- 全局平衡/稳定/约束/域事件；
- 跨单元同时事件组；
- `FIRST_NEEDLE_FAILURE`；
- `FIRST_UNIT_SIGNIFICANT_DEGRADATION`；
- `GLOBAL_REACTION_PEAK_CANDIDATE`；
- `GLOBAL_CRITICAL_CAPACITY_CONFIRMED`；
- 再挂接、硬限位、可恢复脱附和级联稳定等记录。

里程碑只在对应事件后状态或物理终态原子提交成功后成为 accepted；试探里程碑必须随回滚撤销。

### 7.5 旧事件码到规范事件层级的映射

| 历史事件/状态 | 规范层级与事件 | 升级条件 |
|---|---|---|
| `CONTACT_ESTABLISHED`、`NEEDLE_CONTACT_ESTABLISHED` | `NEEDLE.CONTACT_ESTABLISHED` | 直接保留，不等于承载成功 |
| `STICK_TO_SLIP`、`SLIP_MIGRATION` | `NEEDLE.STICK_TO_SLIP` / `NEEDLE.SLIP_MIGRATION` | 直接保留，不自动记作失效 |
| `MATERIAL_FAILURE` | `NEEDLE.MATERIAL_FAILURE` | 经 A/B 认证且提交后可触发 `FIRST_NEEDLE_FAILURE` |
| `STRENGTH_LIMIT` | `NEEDLE.STRENGTH_LIMIT` | 只有定义为强度失效时可进入首次针失效里程碑 |
| `SPRING_HARDSTOP`、`AT_TRAVEL_LIMIT` | `NEEDLE.SPRING_HARDSTOP` / `UNIT.TRAVEL_LIMIT` | 不自动等于失效；需检查剩余合法路径和整体平衡 |
| `CONTACT_RELEASED` | `NEEDLE.CONTACT_RELEASED` | 可恢复性由事件后 B/C 重平衡判定 |
| `DETACHED_RECOVERABLE`、`UNIT_DETACHED_RECOVERABLE` | `UNIT.DETACHED_RECOVERABLE` | 四单元重平衡后可映射主状态 `C_DETACHMENT_RECOVERABLE` |
| `DETACHED_TERMINAL`、`UNIT_DETACHED_IRRECOVERABLE` | `UNIT.DETACHED_IRRECOVERABLE_CANDIDATE` | 需证明无其他稳定/再挂接路径后才映射整体不可恢复 |
| `REENGAGED` | `NEEDLE/UNIT.REENGAGED` | 形成新 accepted 分支后提交 |
| `EVENT_REDUCTION_REQUIRED` | `GLOBAL.EVENT_REDUCTION_REQUIRED` | 由最小事件分数触发，全部 trial 回滚 |
| `EVENT_REBALANCE_REQUIRED` | `GLOBAL.EVENT_REBALANCE_REQUIRED` | 事件点损伤/级联/整体平衡尚未闭合 |
| `CASCADE_STABILIZED` | `GLOBAL.CASCADE_STABILIZED` | fixed point 与事务通过后提交 |
| `FIRST_UNIT_SIGNIFICANT_DEGRADATION` | `MILESTONE.FIRST_UNIT_SIGNIFICANT_DEGRADATION` | 版本化事件函数跨越且事件后状态已提交 |
| `GLOBAL_REACTION_PEAK_CANDIDATE` | `MILESTONE.GLOBAL_REACTION_PEAK_CANDIDATE` | 仅 accepted 稳定点/合法左右极限 |
| `GLOBAL_CRITICAL_CAPACITY_CONFIRMED` | `MILESTONE.GLOBAL_CRITICAL_CAPACITY_CONFIRMED` | 终止或分支覆盖证据闭合 |

规范事件必须保留源 A/B 事件 ID、原始同时组和事件前/点/后状态。映射只统一层级和名称，不允许删除低层语义。

---

## 8. 阶段无关事件归约、共享损伤、级联与事务

### 8.1 统一路径坐标

```text
path_kind = COMMON_SEARCH_S
  -> chi = s

path_kind = ECCENTRIC_LOAD_DELTA_P
  -> chi = delta_P
```

每个 B 单元、姿态、graph、稳定性、碰撞、域、约束和参数切换事件均返回相对于同一试探增量的事件分数 \(\gamma\in(0,1]\)。

全局最早事件：

\[
\boxed{
\gamma_C
=
\min\left(
\gamma_{U_1},\ldots,\gamma_{U_4},
\gamma_{\rm pose},
\gamma_{\rm graph},
\gamma_{\rm stability},
\gamma_{\rm collision},
\gamma_{\rm domain},
\gamma_{\rm constraint},
\gamma_{\rm parameter}
\right).
}
\]

预紧阶段不适用的整体项标 `not_applicable`，不得伪造为零。

### 8.2 物理事件路径优先级

物理事件顺序只由合法路径上的最小 \(\gamma_C\) 决定。若多个括区间重叠或事件位置在版本化容差内，则全部进入同一同时事件组。

上游依赖偏序只规定重算顺序：

```text
几何支持/接触
  -> 粘滑与针级弹簧分支
  -> 材料/强度
  -> 共享 DamageStore
  -> B 单元平衡和重分配
  -> C 四单元整体平衡
  -> 稳定性/退化/峰值审计
```

它不允许用单元 ID 或调用完成顺序决定物理先后。

### 8.3 跨事件回退

若 \(\gamma_C<1\)：

1. 当前四单元 trial、C 姿态、wrench、DamageStore intents、事件/峰值意图全部回滚；
2. 将共同路径增量缩短到事件括区间或指定事件侧；
3. 从同一个 accepted C 状态重新计算四单元完整输入；
4. 重新调用 B；
5. 重新运输 wrench、协调损伤和求整体平衡；
6. 不得按 \(\gamma_C\) 缩放旧 \(u_z\)、旧姿态、旧 wrench、旧 graph、旧损伤或旧 \(\lambda_P\)。

峰值括区间属于曲线审计事件；它不得覆盖更早的物理、合同、碰撞、域或稳定性事件。

### 8.4 同时事件组

事件满足以下任一条件时组成全局同时组：

- 事件括区间相交；
- 事件路径位置差不超过 `epsilon_chi_sim`；
- DamageStore 读写/损伤核重叠表明耦合；
- 整体 graph/stability 事件与单元事件在同一定位容差内。

规范排序仅用于哈希和重放：

```text
(event_chi, hierarchy, unit_slot_id, B_event_group_id, local_event_id)
```

排序不决定物理先后，也不得拆散 B 返回的单元内部同时组。

### 8.5 共享 DamageStore fixed point

1. 四个 B trial 从同一 accepted DamageStore 读取；
2. 收集 opaque damage intents、read/write sets、核重叠签名和版本；
3. 构造跨单元写—写、写—读和核重叠冲突图；
4. 调用 B/A 共享损伤协调器生成共同 trial DamageStore；
5. 若 DamageStore 内容或依赖改变，从同一 accepted C 状态重新调用所有受影响单元；刚性十字主线默认四单元全调；
6. 重新求 B 单元平衡、C 姿态、\(\lambda_P\)、六维残量、稳定性和事件；
7. 迭代到 DamageStore 哈希、四单元响应、事件组、整体残量和里程碑一致；
8. 若未收敛，返回 `DAMAGE_CONFLICT_UNRESOLVED` 或 `C_STOP_NUMERICAL`，全部回滚。

C 不得直接写 DamageStore，也不得相加、取最大或按调用顺序覆盖损伤。

### 8.6 同位置级联与循环防护

事件点允许 \(d\chi=0\) 且姿态、法向行程、接触、损伤或分支变化。C 必须重复：

```text
完整 B 回调
-> wrench 运输和功检查
-> DamageStore 协调
-> 阶段平衡
-> 新事件归约
-> 稳定性/退化检查
```

直到稳定 fixed point 或明确终止。

必须实现以下循环防护：

- 同一事件点的全状态哈希集合；
- 最大同位置级联轮数；
- 最小有效状态变化阈值；
- Zeno 候选检测；
- 事件括区间不能继续缩小时的 `MINIMUM_STEP_EXHAUSTED`；
- 重复状态哈希且无物理进展时返回数值停止，不得静默跳过事件；
- 所有防护阈值版本化，当前未固定。

### 8.7 prepare、原子提交和回滚

只有以下条件全部通过，才可 prepare：

- 状态、版本、参考点、变换、单位和哈希一致；
- 运动合同覆盖通过；
- 四个 B trial 有效；
- wrench 运输和功不变通过；
- 阶段平衡/graph 通过；
- 最早/同时事件完整；
- DamageStore fixed point 完成；
- 同位置级联稳定；
- 稳定性、退化、恢复性和峰值审计适用；
- 无未授权支承；
- 所有致命诊断均已排除；
- 幂等性键和重放清单完整。

一次全局提交必须同时使以下内容可见：

- C 路径和位姿；
- 四个 B accepted states；
- 全部内部 A accepted states；
- 一个共享 DamageStore；
- 事件、同时组和级联；
- 功、能量和误差；
- 曲线、峰值和里程碑；
- 版本、哈希和提交收据。

任一 prepare、commit 或持久化失败，全部不前进。重复同一幂等性键只能返回原收据或安全拒绝，不能重复累计路径、损伤、功、事件或峰值。

---

## 9. 可执行的统一单步算法

```text
function C_INTEGRATED_STEP(accepted_state, request):

  1. VALIDATE_IDENTITY_AND_FREEZE
     - 校验 C 模型、工程事实、B_TO_C、输入上下文和配置版本。
     - 校验 accepted_state、commit receipt、四个 B/A snapshots、DamageStore。
     - 校验单位、参考点、O_A/O_i 偏置、变换、表面/参数/几何哈希。
     - 校验系统边界、P_i、模式、幂等性键和确定性重放清单。
     - 冻结 parent accepted state；缺失字段不得默认补齐。

  2. SELECT_STAGE_AND_COMMON_PATH
     if stage in {PRELOAD_SEARCH, PRELOAD_EVENT_RESOLUTION}:
       path_kind = COMMON_SEARCH_S
       propose s_target = s_n + requested_delta_s
       enforce u_xi = s_target for all units
       enforce rocking = off
     elif stage in {PRELOAD_ACCEPTED_LOCKED,
                     ECCENTRIC_LOAD_TRIAL,
                     ECCENTRIC_EVENT_RESOLUTION,
                     ECCENTRIC_LOAD_ACCEPTED}:
       path_kind = ECCENTRIC_LOAD_DELTA_P
       enforce s = s_stop and ds = 0
       propose delta_P_target and allowed q_C / eta_i
     else:
       reject illegal stage transition

  3. BUILD_PER_UNIT_KINEMATICS
     - 预紧：构造每单元 target_u_x=s_target 和法向控制模式。
     - 加载：由当前 pose、O_A/C 和 Jacobian 构造完整 local x/y/z/rotation。
     - 保留可选 eta_i 与刚体 twist 的所有权分离。

  4. MOTION_CONTRACT_COVERAGE_AUDIT
     - 在任何加载 B 物理调用前检查当前 B 合同覆盖。
     - 预紧 x/Z 路径在 B 1.0 可按既有合同调用。
     - 正式非零加载若出现局部 y 或旋转：
         return C_CONTRACT_EXTENSION_REQUIRED
         preserve accepted_state unchanged
         advance no history, work, event, curve, peak or damage
     - 禁止 x/Z 投影、旋转旧 wrench、冻结针姿态或经验替代。

  5. CHOOSE_LOCAL_PREDICTION_OR_FULL_B
     - 检查 capsule validity key、branch、trust region、event distance 和质量。
     - 局部对象只用于事件外候选、Newton 线性化或步长控制。
     - 任一事件、姿态、DamageStore、模式、合同、作用点或能力确认需求
       触发完整 B trial。
     - 局部预测不得永久更新低层历史。

  6. FOUR_SIDE_EFFECT_FREE_B_TRIALS
     - 四单元从同一 parent accepted state 和 DamageStore 调用 B。
     - 可并行，但调用完成顺序不得影响物理结果。
     - 收集完整 response/graph、wrench、事件、损伤 intent、
       作用线/CoP/free couple、切线/信任域和 rollback token。

  7. FATAL_STATUS_SCREEN
     - 按摘要优先级识别合同、陈旧、运动、域、几何、碰撞、
       模型、参数、执行器边界和数值问题。
     - 致命候选全部回滚；未认证状态不得改写为零承载。

  8. WRENCH_TRANSPORT_AND_POWER_INVARIANCE
     - 按各自 expressed_frame_id 和 O_A 运输到 C。
     - 同时旋转力和运输力矩。
     - 检查每单元 wrench–twist 功不变。
     - 失败则合同/变换错误，全部回滚。

  9. STAGE_BALANCE_SOLVE
     if PRELOAD:
       - B 在 UX_PZ_BALANCED 下求各 u_zi 或 admissible graph。
       - 计算 R_xi, Q_s_contact, Q_s_drive, p_X, p_Y, Delta_X, Delta_Y。
       - 装配完整 contact-only wrench 和支承诊断。
     if ECCENTRIC_LOAD:
       - 装配 contact-only、loading 和明确授权的其他 wrench。
       - 求 q_C、lambda_P、可选 eta_i 和 graph。
       - 检查加载路径、六维残量、模式乘子、yaw 和真实约束。
       - 未授权乘子非零时拒绝候选。

 10. GLOBAL_EARLIEST_EVENT
     - 归约四单元事件以及 pose/graph/stability/collision/domain/
       constraint/parameter 事件的最小 fraction。
     - 若 gamma<1，回滚当前全部 trial，缩短共同路径增量，
       从同一 parent state 回到步骤 3。
     - 不缩放旧 wrench、姿态、u_z、graph、damage 或 reaction。

 11. SIMULTANEOUS_EVENT_GROUPING
     - 保留每个 B 单元内部事件组。
     - 按共同路径括区间/容差和 DamageStore 冲突构造跨单元组。
     - 规范排序只用于哈希和重放。

 12. SHARED_DAMAGE_FIXED_POINT
     - 收集 opaque intents 和读写依赖。
     - 调用 B/A 协调器得到共同 trial DamageStore。
     - DamageStore 改变后从 parent state 重调受影响单元；
       刚性十字默认四单元全调。
     - 重新执行步骤 8–10，直到 fixed point。
     - 未收敛则全部回滚。

 13. EVENT_POINT_AND_SAME_POSITION_CASCADE
     - 保存事件前、点、后一侧状态。
     - 允许 d(path)=0 而 pose、eta、接触和 DamageStore 变化。
     - 重复完整 B 回调、损伤协调和阶段平衡。
     - 使用状态哈希、级联上限和最小步防护。
     - 直到稳定 fixed point、明确物理终止、未认证或数值停止。

 14. UPDATE_UNIT_EVENT_AND_DEGRADATION_AUDIT
     - 原样记录 contact/slip/material/strength/hardstop/release/
       detachment/reengagement 等针级事件。
     - FIRST_NEEDLE_FAILURE 只由认证材料/强度类事件触发。
     - 按版本化事件函数评估单元显著退化。
     - 缺失阈值/下界时标 uncertified，不伪造里程碑。
     - 更新最弱分支、恢复性和局部能力对象。

 15. STABILITY_AND_QUALITY
     - 预紧阶段检查停止门控所需质量和安全裕度。
     - 加载阶段检查一侧稳定性、graph、域、碰撞、行程、
       材料/强度、作用线和模型质量。
     - Newton 失败不等于物理无解；稳定性未认证不等于失稳。

 16. STOP_OR_CONTINUATION_DECISION
     if PRELOAD:
       - 先处理未认证、数值、不可恢复和安全边界。
       - 再处理 s_max 未达标。
       - 最后评估 G_stop。
       - G_stop 通过则形成 PRELOAD_ACCEPTED_LOCKED 候选。
     if ECCENTRIC_LOAD:
       - 区分稳定继续、可恢复脱附、物理无平衡、
         物理失稳、不可恢复脱附和物理边界。
       - 首个反力下降、首针事件或首个单元退化不自动终止。

 17. CURVE_AND_PEAK_LEDGER_TRIAL_UPDATE
     - 仅对合同、平衡、稳定和质量均通过的候选建立曲线点意图。
     - 评估光滑峰、尖峰、平台、分支端点和多峰候选。
     - 试探点和回滚点不得进入 accepted 峰值账本。
     - current_observed_stable_max 只在提交后更新。

 18. F_CRIT_CONFIRMATION_CHECK
     - 只有物理终止后无合法稳定分支、分支探索穷尽、
       明确物理边界证明无更高路径，或保守上界闭合时，
       才允许 F_crit_confirmed=true。
     - 合同、模型、参数、域、数值或事务停止时保持 null。

 19. PREPARE_GLOBAL_TRANSACTION
     - 组装四个 B/A provisional intents、DamageStore、
       C path/pose、wrench、事件、功、曲线和峰值账本。
     - 任一 prepare 失败则全部 rollback。

 20. ATOMIC_COMMIT_OR_ROLLBACK
     - 一个全局 commit 使全部状态同时可见。
     - 失败则 parent accepted state 完全不变。
     - 同幂等键重试返回原收据或安全拒绝。

 21. BUILD_CANONICAL_RESPONSE
     - 返回新的 CAcceptedState、CEventRecords、诊断和收据；
       或返回 last_valid_state 与明确未认证/数值/事务状态。
     - 若物理终止和能力证据闭合，生成 CMaximumCapacityResult。
```

### 9.1 分支非唯一处理

- 不按单元 ID、调用顺序或最小范数静默选支；
- 返回 admissible graph、分支句柄、连续性条件和保守下界；
- 若策略允许提交退化状态，必须记录选择政策和后续完整回调条件；
- 若无合法选择政策，返回 `C_BALANCED_DEGENERATE` 或 `C_STOP_UNCERTIFIED`；
- 分支枚举缓存属于数值内部状态，不进入物理历史。

### 9.2 确定性重放

相同 accepted 快照、表面、参数、变换、配置、方向和幂等性键必须满足：

- 串行、并行和单元调用顺序置换得到相同 accepted 状态；
- graph 非唯一时返回同一集合或分支句柄；
- 同时事件组和规范哈希一致；
- 重试不重复累计路径、损伤、功、事件、曲线或峰值；
- 提交收据可验证 C、四个 B/A 和 DamageStore 的同一版本组合。

---

# 第四篇：稳定反力曲线、峰值、终止与方向比较

## 10. 稳定可达分支与最大承载

### 10.1 稳定可达状态集合

状态节点定义为

\[
\mathsf s=
\left(
\delta_P,
\mathbf q_C,
\{\mathcal H_i\}_{i=1}^{4},
\mathcal D,
\lambda_P,
b
\right).
\]

\(\mathcal B_{\rm stable,reachable}\) 只包含：

1. 从同一个合法锁定预紧态出发的节点；
2. 合同、坐标、参考点、域、几何、碰撞、模型和参数均认证；
3. 六维平衡/graph 和功检查通过；
4. 一侧稳定性通过；
5. 通过连续 accepted 位移步或已定位、已提交的合法事件跳转可达；
6. 不依赖未授权支承；
7. 已经全局原子提交；
8. graph 非唯一时保留完整分支和选择条件。

以下对象不属于该集合：

- trial、Newton、回溯或回滚点；
- 跨事件插值点；
- 合同扩展缺口点；
- 未认证稳定性点；
- 数值失败点；
- 隐藏支承平衡；
- 只由旧 wrench、固定能力域或经验分配产生的点。

### 10.2 原始反力曲线

每个 accepted 稳定状态输出

\[
\boxed{
F_{\rm reaction}(\delta_P)=\lambda_P.
}
\]

必须同时保存：

- 加载方向和加载点；
- C 位姿和 rocking 角；
- 四单元完整 contact-only wrench；
- 参考点、作用线/CoP 和自由力偶可用性；
- 针/单元事件和 DamageStore；
- branch、rank、nullspace、稳定性和质量；
- 功、能量、误差和收据。

原始曲线不得用单调包络、峰值保持或平滑拟合替换。派生滤波通道必须保留滤波器版本，并不能用于修改 accepted 事件顺序。

### 10.3 峰值候选

允许的峰值类型：

1. 光滑局部峰；
2. 非光滑事件尖峰；
3. 平台区间；
4. 稳定分支端点峰；
5. 集合值峰区间；
6. 再平衡或再挂接后的二次峰；
7. 多个局部峰。

统一一侧检查为

\[
D^-F(\delta_P^\star)\ge0,
\qquad
D^+F(\delta_P^\star)\le0,
\]

但实际应使用事件括区间、左右 accepted 状态、割线和误差界实现，不假定经典可微。

峰值规则：

- 只使用 accepted 稳定点和经定位的合法左右极限；
- 试探、未认证和回滚点不得进入峰值账本；
- 峰值括区间同时控制位移和反力误差；
- 多个峰全部保留；
- 平台报告区间和上下界；
- graph 非唯一时报告集合或能力区间；
- 峰值附近默认强制完整 B 回调。

### 10.4 当前观测最大值与最终能力

只对新提交的稳定状态更新：

\[
F_{\max,n+1}^{\rm obs}
=
\max\left(
F_{\max,n}^{\rm obs},
\lambda_{P,n+1}
\right).
\]

它不是最终能力。

正式定义：

\[
\boxed{
F_{\rm crit}
=
\sup_{\mathsf s\in\mathcal B_{\rm stable,reachable}}
F_{\rm reaction}(\mathsf s).
}
\]

若上确界在 accepted 状态达到，可报告 `max`；否则报告上确界、区间和未达到原因。

`F_crit_confirmed=true` 仅在以下之一成立：

1. 已定位物理终止，且终止后不存在允许的稳定可达分支；
2. 版本化分支探索政策已穷尽所有合法稳定分支；
3. 达到明确物理边界，且剩余行程、再挂接和分支证据证明不能产生更高稳定反力；
4. 集合值问题形成经审查的保守上界，并证明当前峰达到该上界。

若因合同扩展、模型/参数、域/碰撞、作用线、稳定性、数值或事务问题停止：

```text
current_observed_stable_max = retained
peak_candidates = retained
F_crit = null
F_crit_confirmed = false
```

### 10.5 首峰后的继续条件

首个峰值、首次下降、首针失效或首个单元退化均不自动终止。只要：

- 存在经认证稳定可达分支；
- 未越过工程/结构边界；
- B、表面、参数和姿态仍在有效域；
- 事件和损伤可定位并形成 fixed point；
- 未证明不可恢复；

就必须继续位移加载，以捕捉稳定下降、渐进剥离、四单元再平衡、再挂接、二次峰和最终终止。

### 10.6 物理终止证明

| 终止状态 | 必需证明 |
|---|---|
| `C_PHYSICAL_EQUILIBRIUM_INFEASIBLE` | 合同、模型、参数和数值有效；当前路径位置不存在任何 admissible 六维代数平衡 |
| `C_PHYSICAL_INSTABILITY` | 代数根可存在，但所有可达 admissible 分支在允许一侧扰动下失去恢复性 |
| `C_DETACHMENT_IRRECOVERABLE` | 关键分支失载，且剩余合法行程、活动针、DamageStore、再挂接和其他分支均不能形成稳定承载 |
| `C_PHYSICAL_BOUNDARY_REACHED` | 达到已授权的几何/结构边界，并已定位最后稳定状态 |
| `C_MAXIMUM_CAPACITY_CONFIRMED` | 上述终止或分支覆盖证据与峰值账本闭合 |

`C_DETACHMENT_RECOVERABLE` 是中间状态；当前反力可接近零，但存在合法继续或再挂接路径时应继续求解。

---

## 11. `+X` 与 `45°` 工况的符号、分支作用和比较

### 11.1 `+X` 工况

外部 wrench：

\[
\mathbf F_{\rm ext}=F\mathbf E_X,
\qquad
\mathbf M_{\rm ext}=50F\mathbf E_Y.
\]

忽略单元自由力偶、横向力和 \(\rho\) 时，X 对置组的法向力矩为

\[
\boxed{
M_Y^{(1,2)}=40(F_{z1}-F_{z2}).
}
\]

为了抵消 \(+M_Y\)，contact/authorized wrench 倾向于提供 \(-M_Y\)，简化符号上对应 \(F_{z2}>F_{z1}\)。正 \(\theta_Y\) 使单元 2 向墙、单元 1 离墙，符号相容。

但单元 3、4 仍可通过横向力、自由力偶、姿态、作用线、DamageStore 和历史相关 graph 参与平衡，不能冻结为零贡献。

### 11.2 `45°` 工况

\[
\mathbf F_{\rm ext}
=
\frac{F}{\sqrt2}(\mathbf E_X+\mathbf E_Y),
\]

\[
\mathbf M_{\rm ext}
=
\frac{50F}{\sqrt2}
(-\mathbf E_X+\mathbf E_Y).
\]

简化成对法向力矩：

\[
M_X^{(3,4)}=40(F_{z4}-F_{z3}),
\qquad
M_Y^{(1,2)}=40(F_{z1}-F_{z2}).
\]

两组对置分支同时耦合。“分担更均匀”不自动等于能力更高；同时接近横向、剥离、损伤或行程边界也可能更早触发级联。

### 11.3 理想四重对称

若四单元、表面、\(P_i\)、预紧、DamageStore、剩余行程、偏置和参数均按 90° 旋转对应，则：

- `+X` 与 `+Y` 曲线、事件和临界状态应旋转等价；
- 单元身份按旋转置换；
- wrench、姿态和作用线按张量/向量规则变换；
- \(F_{\rm crit}\) 幅值在数值容差内一致。

这不证明 `+X` 与 `45°` 等价。

### 11.4 对称破缺来源

- 表面各向异性；
- `2×5` 与 `5×2` 等阵列方向；
- 不同 C1 事件和 DamageStore；
- 不同作用线、自由力偶和 \(\rho_{A/i}\)；
- 剩余弹簧行程、硬限位和针级损伤；
- graph 非唯一和局部切线差异；
- 制造、参数和 \(P_i\) 差异。

### 11.5 配对比较协议

比较 `+X` 与 `45°` 必须：

1. 使用同一设计、工程事实和参数包；
2. 使用同一 C1 停止策略；
3. 使用同一或可配对的表面实现/种子；
4. 从独立复制的同一锁定预紧态开始；
5. 两个方向使用独立 DamageStore 分支，不能继承另一方向造成的损伤；
6. 保存四单元原始 wrench、姿态、事件、退化、峰后路径和终止；
7. 报告样本级配对差值和不确定性；
8. 不未经求解固定方向优劣。

---

# 第五篇：B 1.0 覆盖审计与上游扩展要求

## 12. 当前 B 合同的精确能力边界

### 12.1 四单元允许平移子空间

B 1.0 对第 \(i\) 单元认证的平移子空间为

\[
\mathcal V_i=
\operatorname{span}\{\mathbf e_{x_i},\mathbf E_Z\}.
\]

四单元交集：

\[
\boxed{
\bigcap_{i=1}^{4}\mathcal V_i
=
\operatorname{span}\{\mathbf E_Z\}.
}
\]

因此除纯全局 Z 平移外，不存在非零整爪平移能同时落在四个单元的 x/Z 认证子空间内。

### 12.2 `+X` 路径局部分量

取 \(\Delta\mathbf u_C=\Delta u\,\mathbf E_X\)，无转动：

| 单元 | \(\Delta u_{x_i}\) | \(\Delta u_{y_i}\) | B 1.0 |
|---|---:|---:|---|
| 1，\(+X\) | \(+\Delta u\) | 0 | x 可表达 |
| 2，\(-X\) | \(-\Delta u\) | 0 | x 可表达 |
| 3，\(+Y\) | 0 | \(-\Delta u\) | y 未认证 |
| 4，\(-Y\) | 0 | \(+\Delta u\) | y 未认证 |

正式 `+X` 路径不能完整推进。

### 12.3 `45°` 路径局部分量

取

\[
\Delta\mathbf u_C
=
\frac{\Delta u}{\sqrt2}
(\mathbf E_X+\mathbf E_Y),
\]

则：

| 单元 | \(\Delta u_{x_i}\) | \(\Delta u_{y_i}\) |
|---|---:|---:|
| 1 | \(+\Delta u/\sqrt2\) | \(+\Delta u/\sqrt2\) |
| 2 | \(-\Delta u/\sqrt2\) | \(-\Delta u/\sqrt2\) |
| 3 | \(+\Delta u/\sqrt2\) | \(-\Delta u/\sqrt2\) |
| 4 | \(-\Delta u/\sqrt2\) | \(+\Delta u/\sqrt2\) |

四单元均需要局部 y 运动。任意 rocking 还需要：

- 动态单元姿态；
- 针轴和针尖姿态更新；
- 表面和碰撞查询；
- 旋转事件和 6D tangent/graph。

### 12.4 B 1.0 当前可做与不可做

可做：

- C1 同步预紧的 x/Z 路径；
- C1 accepted 状态的零增量重放；
- 纯全局 Z 平移的受限构造测试；
- 坐标运输、功和数据结构验证；
- 对未支持运动返回明确安全拒绝。

不可做：

- 正式非零 `+X` 或 `45°` 偏心加载；
- 任意局部 y 平移；
- 真实 \(\theta_X,\theta_Y\)；
- 由旧 x/Z 响应推断完整 6D tangent、作用线变化或稳定性；
- 旋转旧 wrench 代替新姿态 B 重求解。

### 12.5 统一安全拒绝

在扩展接受前，正式非零加载必须：

1. 校验并冻结最后有效锁定预紧态；
2. 计算理论完整 twist；
3. 发现局部 y/转动需求；
4. 返回 `C_CONTRACT_EXTENSION_REQUIRED`；
5. 输出缺失运动分量和扩展字段清单；
6. 保留 last-valid accepted state；
7. 不调用降阶替代；
8. 不推进 \(\delta_P\)、四个 B/A 状态、DamageStore、事件、功、曲线、峰值或 \(F_{\rm crit}\)。

该状态不等于：

- \(F_{\rm crit}=0\)；
- 物理无平衡；
- 物理失稳；
- 不可恢复脱附；
- 数值失败；
- 抓附失败。

## 13. 建议的 B 2.x 最小扩展要求

本节是版本化扩展要求，不是已接受合同。

```text
required_upstream_extension:
  contract_id: B_TO_C
  required_major_version: 2
  backward_compatibility:
    - every valid 1.0.0 x/Z request retains identical semantics
    - existing reference points, units, status and transaction semantics remain
    - new SE3 fields are mandatory only for SE3 modes

  new_control_modes:
    - PRESCRIBED_SE3_RESIDUAL
    - SE3_WITH_FORCE_BALANCED_NORMAL_STROKE  # optional, hardware-bound

  request_kinematics:
    - accepted_T_G_from_A
    - target_T_G_from_A or full_base_twist_increment[6]
    - separate frozen_internal_s_stop
    - local x/y/z and rotation components
    - optional eta_i with endpoint/boundary certification
    - SE3 interpolation and event-fraction basis

  geometry_surface_collision:
    - dynamic unit frame
    - updated needle axes and tip poses
    - full 3D collision/domain queries
    - rocking pose certification domain

  response:
    - contact_only_wrench_at_O_A[6]
    - full motion residuals and control/constraint reactions
    - raw/condensed/one-sided 6D tangent or admissible graph
    - rank/nullspace/branch/trust region
    - translation/rotation/collision/domain event candidates
    - action line / CoP / free-couple availability
    - capability, stability and full-callback requirements
    - wrench-twist power checks

  history_damage_transaction:
    - unchanged opaque A/B histories
    - shared DamageStore intents and fixed point
    - simultaneous event and cascade semantics
    - prepare / atomic commit / rollback / idempotency
```

### 13.1 关闭验证

扩展正式接受前至少验证：

1. B 1.0 x/Z 基准逐位兼容；
2. 任意小 twist 的 wrench–twist 功对偶；
3. 6D tangent/一侧割线与有限差分一致；
4. 动态姿态下针轴、表面、碰撞和事件正确；
5. DamageStore 在平移/旋转事件下确定性；
6. 最早事件缩步后从同一 accepted state 重算；
7. 串行/并行和调用顺序不改变 accepted 结果；
8. 回滚不累计路径、损伤、功或事件；
9. 未支持运动返回 last-valid state，不返回零承载；
10. C 的 `C_CONTRACT_EXTENSION_REQUIRED` 在扩展接受后只对真正未支持模式触发。

---

# 第六篇：公共接口

## 14. 上游 B→C 使用接口

### 14.1 当前正式身份

- 上游合同：`B_TO_C 1.0.0 accepted`；
- C 不重新冻结、修改或补写该合同；
- C 只按 accepted 语义调用 B；
- B 2.x 仍是待接受扩展要求。

### 14.2 C 对 B 的请求约束

每个单元请求至少包含：

```text
identity / trial IDs / idempotency
accepted B snapshot
accepted A opaque bundle
shared DamageStore handle/version/hash
P_i
control mode
target x/Z or future full SE3 motion
surface/parameter/configuration hashes
expressed frame and O_A reference
transform and geometry IDs
event side / interpolation
requested graph/tangent/capability modes
deterministic replay request
```

C 不得包含：

- 逐针力；
- \(P_i/N\)；
- 逐针活动集；
- 经验转移权重；
- C 自算损伤增量；
- A/B 低层参数覆盖；
- 解析修改 opaque 状态的字段。

### 14.3 B 响应的最低保留

C 必须无损保留：

- 原始 B 响应或句柄；
- contact-only wrench、作用方向、表达框架和参考点；
- 平衡/graph、rank、nullspace、branch 和 trust region；
- 针级/单元级事件组；
- DamageStore intents 和读写依赖；
- 行程、碰撞、域、模型、参数和质量；
- 能量、功和数值误差；
- rollback/provisional/prepare 令牌；
- full-unit-resolve callback 条件。

### 14.4 局部 capsule 的使用边界

允许使用局部切线/割线/graph 的条件：

- 合同认证当前完整运动；
- reference frame、O_A、姿态、控制模式和 \(P_i\) 一致；
- B/A accepted states、DamageStore、表面和参数版本未变化；
- 活动集、粘滑、弹簧、材料、强度和恢复分支不变；
- 不跨事件或 trust region；
- graph 质量和保守下界可用；
- 不需要精确损伤、作用线、恢复性、峰值或显著退化确认；
- `full_unit_resolve_callback_requirement=false`。

否则必须完整回调 B。

---

## 15. C 对最终系统集成的公共接口

### 15.1 公共请求

```text
CSystemRequest:
  identity:
    model_versions
    run_id
    request_idempotency_key
  operation:
    INITIALIZE_PRELOAD
    ADVANCE_PRELOAD
    ADVANCE_ECCENTRIC_LOAD
    QUERY_ACCEPTED_STATE
    FINALIZE_CAPACITY_RESULT
  accepted_state_handle_optional
  design_surface_parameter_bindings
  P_i_N[4]
  preload_policy
  loading_direction_and_path
  rocking_and_system_boundary
  event_damage_stability_peak_branch_numerical_configs
  requested_public_outputs
  deterministic_replay_request
```

### 15.2 公共响应

```text
CSystemResponse:
  primary_status / all_status_codes
  stage
  accepted_state_handle | last_valid_state_handle
  preload_state_public_view_optional
  path_and_pose
  reaction_wrench_and_F_reaction
  four_unit_load_distribution
  events_damage_degradation_milestones
  raw_curve_handle / peak_candidates
  maximum_capacity_result | unconfirmed_status
  work_energy_quality_certification
  versions / hashes / commit_receipt / replay_manifest
  contract_extension_requirement_optional
```

### 15.3 公开字段与内部字段

**公开**：

- \(s,s_{\rm stop},\delta_P\)；
- C 位姿和 rocking 角；
- 完整六维 wrench 和 \(F_{\rm reaction}\)；
- 四单元 contact-only force/moment；
- 参考点、作用线/CoP 可用性和成对力矩贡献；
- 单元/针级状态摘要和事件句柄；
- DamageStore 版本/哈希与变化事件；
- 稳定性、质量、功、能量和误差；
- 原始曲线、峰值候选和能力结果；
- 版本、哈希、收据和认证状态。

**内部**：

- Newton 缓存；
- 线搜索和 trust-region 工作区；
- 分支枚举临时对象；
- 未提交 DamageStore 内容；
- A/B 可变 opaque 对象；
- 临时峰值拟合；
- rollback 和 prepare 的内部实现细节。

### 15.4 外部调用者的权限

外部调用者只能：

- 创建请求；
- 持有并原样传回 opaque `CAcceptedState`；
- 读取公开连续量、事件和认证结果；
- 选择显式配置和系统边界。

外部调用者不得：

- 修改 B/A/DamageStore；
- 将未认证 trial 作为 accepted state；
- 绕过 C 的全局原子事务；
- 重置 \(s_{\rm stop}\) 或低层历史；
- 注入逐针载荷或活动集；
- 把 `C_CONTRACT_EXTENSION_REQUIRED` 改写为零能力。

### 15.5 公共认证等级

```text
CCertificationLevel:
  C_THEORY_INTEGRATED
  C_PRELOAD_CONTRACT_SUPPORTED
  C_ECCENTRIC_LOAD_CONTRACT_EXTENSION_REQUIRED
  C_ECCENTRIC_LOAD_CONTRACT_SUPPORTED
  C_NUMERICALLY_VERIFIED
  C_EXPERIMENTALLY_TREND_VALIDATED
```

认证等级是累积证据标签，不替代主状态。当前候选至少满足 `C_THEORY_INTEGRATED`；在 B 1.0 下不满足 `C_ECCENTRIC_LOAD_CONTRACT_SUPPORTED`，也不满足数值或实验验证等级。

### 15.6 状态迁移兼容接口

为了读取既有 accepted 历史，可提供只读迁移器：

```text
migrate_C1PreloadState_to_CAcceptedState(old_state)
migrate_C2AcceptedState_to_CAcceptedState(old_state)
migrate_C3AcceptedState_to_CAcceptedState(old_state)
```

迁移必须：

- 保留全部旧 ID、收据、哈希和原始低层句柄；
- 不重新求解物理；
- 不改变路径、DamageStore、事件或功；
- 记录迁移器版本和可逆映射；
- 若旧字段不足，返回 `MIGRATION_UNCERTIFIED`，不能补默认值。

---

## 16. 面向实验的公共输出与对齐

### 16.1 运行元数据

每个方向和样本必须保存：

- 设计 ID、阵列几何、安装模式、针/弹簧/材料参数包和模型开关；
- 表面类别、实现方法、空间区域、随机种子和初始 DamageStore；
- 工程事实、B 合同、C 模型、求解器、数值和策略版本；
- 锁定预紧态 ID、\(s_{\rm stop}\)、四个 \(P_i\)、预紧事件和初始 wrench；
- 加载方向、加载点、rocking、真实试验架约束和系统边界；
- 请求/响应哈希、提交收据和重放清单。

### 16.2 每个 accepted 点的机械量

- \(\delta_P\)、\(F_{\rm reaction}\)、完整六维外部/反力 wrench；
- C 点位姿、加载点位置、\(\theta_X,\theta_Y\)；
- 四单元 contact-only force/moment、参考点、自由力偶、作用线/CoP；
- 每单元局部 x/y/z 力、法向/切向分量和成对力矩；
- 四单元最弱裕度、graph、branch、局部能力和剩余行程；
- 针/单元活动、承载、粘滑、弹簧、硬限位、损伤、脱离和再挂接摘要；
- 整体残量、稳定性、质量、功、能量、耗散和数值误差。

### 16.3 事件与临界结果

- 所有事件的路径位置、反力、括区间、同时组和定位误差；
- DamageStore 变化和级联轮数；
- 首针材料/强度失效、首单元显著退化；
- 所有峰值候选、类型、分支、误差和后续是否被超过；
- 确认的 \(F_{\rm crit}\) 或未确认状态；
- 最后稳定状态和终止类型；
- 临界时四单元/针级状态句柄。

### 16.4 时间通道

工程事实未固定 C1 的共同搜索速度，也未固定 C2/C3 的偏心加载速度。因而：

- C 的两个阶段均以路径位移为主要独立变量；
- 不得自动沿用 A/B 单刺/阵列直线拖拽的 \(1\,{\rm mm/s}\)；
- 若实验协议提供加载速度或时间戳，可建立版本化 \(t\leftrightarrow\delta_P\) 映射；
- 无协议时，时间为 `unavailable`，事件顺序和位移位置仍完整保存。

### 16.5 仿真—实验对齐

1. 传感器作用点与 \(C+50\mathbf E_Z\) 对齐，或将 wrench 刚体运输到该点；
2. \(\delta_P=0\) 对应同一锁定预紧接受态；
3. 加载器作用于爪和爪作用于传感器的 wrench 同时反号；
4. 明确 C 点、参考体、传感器坐标和姿态变换；
5. 记录 \(s_{\rm stop}\)、四个 \(P_i\)、初始法向位置、DamageStore 和 wrench；
6. 保存原始采样；滤波器、延迟、截止频率和相位版本化；
7. 非因果滤波不得用于在线事件判定；
8. 优先按位移和传感器/图像事件联合对齐；
9. 以独立表面区域、随机种子或试验批次为统计单位；
10. 验证首先比较趋势、设计排序和机理解释，不拟合单次偶然峰值。

### 16.6 禁止自动输出的结论

公共实验接口不得自动产生：

- 二元“抓附成功/失败”；
- 单一综合评分；
- 未经标定的安全系数；
- 由单次峰值反推的材料强度；
- 由不同方向非配对样本直接得出的确定性优劣；
- 在 `F_crit_confirmed=false` 时以当前最大值冒充临界能力。

---

# 第七篇：参数状态、证据边界、验证、风险与关闭条件

## 17. 参数、模型与证据状态

### 17.1 证据分类

| 内容 | 来源等级 | 本文件中的状态 | 使用边界 |
|---|---|---|---|
| 全局/局部坐标、80 mm 几何、50 mm 加载点、正式方向 | 工程事实 | fixed/fixed_set | 不得由论文、代码便利或拟合改写 |
| 每单元 \(P_i=0.5\)–\(2\,\mathrm N\) | 工程事实 | fixed_range | 恒主动推力，不是恒接触合力或逐针载荷 |
| C1 同步搜索、停止、DamageStore 和锁定语义 | accepted C 上下文 | accepted | 阈值和 \(s_{\max}\) 仍未决 |
| C2 刚体、wrench、无隐藏支承和稳定性 | accepted C 上下文 | accepted theory | 正式在线加载受 B 运动合同阻断 |
| C3 事件后四单元重求、峰后路径和 \(F_{\rm crit}\) | accepted C 上下文 | accepted theory | 需要 B 扩展、策略配置、数值和实验验证 |
| B 唯一入口、contact-only、graph、事件、损伤和事务 | `B_TO_C 1.0.0 accepted` | accepted | 只认证局部 x 与全局 Z 平移 |
| 等刚度失去一分支后的等增量换载 | 历史文献特殊基准 | regression-only | 仅在等刚度、固定姿态、同增量、无其他状态变化时使用 |
| 给定活动集的整体平衡/最弱裕度骨架 | 历史文献上层结构 | local diagnostic | 不替代 B 历史 response 或全局能力域 |
| SE(3) 运动、虚功、KKT、事件定位、事务和一侧稳定性 | 通用数学/力学/算法 | integration derivation | 不固定项目数值、材料参数或控制策略 |
| 材料、摩擦、表面、损伤和数值参数 | 工程未决登记 | unresolved | 只能参数化、标 `unavailable` 或通过标定关闭 |
| 代码和目标实验 | 尚未完成 | not verified | 不得声称测试已通过 |

### 17.2 未决问题及安全处理

| 类别 | 未决项 | 影响 | 当前安全处理 | 是否阻断正式加载/能力确认 | 关闭条件 |
|---|---|---|---|---|---|
| 上游合同 | B 全 twist、局部 y、动态姿态、碰撞/表面更新、6D tangent/graph | 正式 `+X/45°` 无法调用 | `C_CONTRACT_EXTENSION_REQUIRED`，零历史推进 | 阻断正式非零加载和 \(F_{\rm crit}\) | B 2.x 实现、兼容、事件、功和事务验证后正式接受 |
| 执行器边界 | 法向执行器端点、作用线、源/目标体 | 完整执行器功和可能外部 wrench 不确定 | ideal work 可用，certified work unavailable | 若平衡依赖其外部 wrench则阻断 | CAD/机构绑定、作用—反作用和功测试 |
| 机构自由度 | \(\eta_i\) 是否自由 | 法向控制方程不同 | 默认 unavailable，不静默启用 | 可能阻断相应模式 | 机构自由度和控制策略确认 |
| rocking | 小角度/姿态 trust region | 稳定性和碰撞有效域 | 无默认值，超域拒绝 | 阻断 rocking 能力确认 | B 几何验证、误差分析和实验标定 |
| C1 停止 | 能力特征、聚合、阈值、最弱分支、窗口、置信、滞回 | 预紧接受位置不确定 | 缺配置则 `STOP_UNCERTIFIED` | 阻断合格预紧态 | B 连续仿真、留出样本、单元/四单元实验 |
| C1 上限 | \(s_{\max}\) | 搜索边界不确定 | 无默认值；禁用 100 mm 回退 | 阻断自动停止 | 离线策略与实验审批 |
| C3 退化 | 通道、阈值、尺度和事件侧 | 单元里程碑不确定 | 保留原始事件，退化标 uncertified | 不必阻断曲线，但阻断该里程碑结论 | 配对仿真、实验和统计审查 |
| 峰值 | 位移/反力容差、平台窗口 | 峰位置和多峰分类 | 输出括区间和不确定性 | 可能阻断能力精确确认 | 步长收敛和噪声分析 |
| 分支 | 探索/选择政策 | 可能漏掉更高稳定分支 | graph 保留，\(F_{\rm crit}\) 不确认 | 阻断最终能力 | 非唯一基准和物理选择验证 |
| 稳定性 | 长度尺度、扰动、容差 | 稳定/失稳分类 | `STABILITY_UNCERTIFIED` | 阻断物理失稳和 \(F_{\rm crit}\) | 解析基准、一侧扰动和收敛测试 |
| 表面/材料 | 摩擦、强度、损伤、统计、分辨率、随机样本 | 绝对数值和排序 | 参数化或 unavailable | 阻断绝对能力，部分趋势研究可继续 | 文献、测量、标定和不确定性方案 |
| 事件数值 | 初始/最小步、同时事件、定位容差 | 事件顺序和峰值 | 配置化，无默认唯一值 | 可能阻断事件/能力确认 | 步长和顺序不变性测试 |
| 损伤协调 | fixed-point 容差和迭代上限 | 跨单元一致性 | 未收敛则回滚 | 阻断相应步 | 协调器实现和故障注入 |
| 残量数值 | 六维缩放和容差 | 平衡接受 | 版本化物理分量门槛 | 阻断 accepted 加载点 | 解析/数值基准和收敛 |
| 加载协议 | C 偏心加载速度 | 时间映射 | 位移主输出，时间 unavailable | 不阻断准静态曲线 | 实验协议或工程事实审批 |
| 验证 | 允许误差和统计方案 | 仿真—实验结论 | 只报告趋势和原始量 | 阻断定量验收 | 重复实验和统计审查 |
| 实现状态 | 代码、故障注入、重放、收敛、实验 | 规范尚未变为可运行系统 | 明确未完成 | 阻断运行结论 | 实际实现并逐项记录测试结果 |

### 17.3 与工程未决登记的映射

| 工程未决 ID | C 集成中的承载位置 |
|---|---|
| `UNRESOLVED.A2.CONTACT_STIFFNESS`、`UNRESOLVED.MATERIAL.NEEDLE` | A/B 参数包；C 仅检查版本和可用性 |
| `UNRESOLVED.SURFACE.STATISTICS`、`FRICTION`、`STRENGTH`、`RESOLUTION` | 表面/参数绑定和不确定性输出 |
| `UNRESOLVED.DAMAGE.EVOLUTION` | A/B DamageStore；C 组织 fixed point，不定义公式 |
| `UNRESOLVED.NUMERICS.EVENT_STEPS` | C/B 事件括区间、最小步、同时事件和 Zeno 防护配置 |
| `UNRESOLVED.STOCHASTIC.SAMPLE_COUNT` | `+X/45°` 配对比较和实验统计 |
| `UNRESOLVED.C1.STOP_THRESHOLD` | `preload_policy_id/version` |
| `UNRESOLVED.C1.MAX_SEARCH_DISTANCE` | `s_max_mm`，无默认值 |
| `UNRESOLVED.VALIDATION.ERROR_TOLERANCE` | 仿真—实验验收和数值收敛 |
| `UNRESOLVED.METRIC.BINARY_SUCCESS` | 明确不由 C 自动输出 |
| `UNRESOLVED.METRIC.COMPOSITE_SCORE` | 明确不由 C 自动输出 |

---

## 18. 集成验证矩阵

> 本节定义必须执行的测试；当前不声称已经通过。

| 编号 | 测试 | 必须结果 |
|---:|---|---|
| C-I01 | 四个 \(\mathbf R_{Gi}\) | 正交且 \(\det=+1\) |
| C-I02 | \(O_i\) 几何 | 形成 80 mm×80 mm 中央空区 |
| C-I03 | 非零 \(\rho_{A/i}\) 运输 | 力矩含 \(\mathbf r\times\mathbf F\)，不默认 \(O_A=O_i\) |
| C-I04 | Wrench–twist 功不变 | 源/目标表达的功在容差内一致 |
| C-I05 | 同步搜索 | 四个 \(u_{x_i}=s\)，其他响应允许不同 |
| C-I06 | 对称内部预紧 | 全局面内合力可为零，而 \(Q_s^{\rm drive}>0\) |
| C-I07 | \(P_i\) 唯一所有权 | 不作为第二份 contact-only wrench；功字段分栏 |
| C-I08 | 理想功与认证功 | 端点未绑定时前者可用、后者 unavailable；绑定后关系可验证 |
| C-I09 | C1 graph 非唯一 | 返回集合/句柄，不按 ID 选伪唯一解 |
| C-I10 | 预紧停止门控 | 平台、边际收益、最弱、安全、保持和范围必须同时通过 |
| C-I11 | \(s_{\max}\) 缺失 | 返回未认证，不回退到 100 mm |
| C-I12 | 锁定迁移 | 仅原子提交后生成锁定态；B/A/DamageStore 不重置 |
| C-I13 | `+X` 偏心 wrench | \(M_Y=+50F\ {\rm N\,mm}\) |
| C-I14 | `45°` 偏心 wrench | \(M_X=-50F/\sqrt2\)、\(M_Y=+50F/\sqrt2\) |
| C-I15 | rocking 四式 | 四单元法向位移符号与第 4.5.3 节一致 |
| C-I16 | 固定姿态无隐藏支承 | 需要非零未授权力矩时拒绝候选 |
| C-I17 | yaw 排除 | 非零 \(M_Z\) 不能由隐式乘子闭合 |
| C-I18 | B 1.0 `+X` 审计 | 单元 3/4 局部 y，返回统一扩展要求 |
| C-I19 | B 1.0 `45°` 审计 | 四单元局部 y 非零，返回统一扩展要求 |
| C-I20 | rocking 防伪 | 旋转旧 wrench、x/Z 投影和冻结针姿态方案被拒绝 |
| C-I21 | 安全拒绝零推进 | \(\delta_P\)、B/A、DamageStore、事件、功、曲线和峰值均不推进 |
| C-I22 | B 2.x 向后兼容 | 旧 x/Z 基准与 1.0 语义一致 |
| C-I23 | 四单元最早事件 | 任一单元先触发时全局缩步，四单元从同一 accepted state 重调 |
| C-I24 | 同时事件和调用顺序 | 顺序置换不改变 accepted 结果或非唯一集合 |
| C-I25 | DamageStore 冲突 | 由协调器 fixed point 处理，不按调用顺序覆盖 |
| C-I26 | 同位置级联 | \(d\chi=0\) 时仍重平衡并正确记能量 |
| C-I27 | Zeno/状态哈希循环 | 返回可诊断数值停止，不静默跳过事件 |
| C-I28 | 原子提交故障注入 | 任一失败使 C、四单元、DamageStore、事件、功和峰值全部不推进 |
| C-I29 | 首针不等于单元失败 | 针材料失效后完整 B/四单元重平衡，单元可继续承载 |
| C-I30 | 显著退化阈值缺失 | 原始事件保留，退化里程碑 uncertified |
| C-I31 | 事件后四单元重分配 | 触发单元和其余单元、姿态、\(\lambda_P\) 全部更新 |
| C-I32 | 拒绝经验载荷转移 | 均分、邻接权重、固定矩阵和峰值缩放不进入正式结果 |
| C-I33 | 局部 capsule trust region | 事件外与完整 B 一致；跨事件立即失效 |
| C-I34 | 稳定根/退化/失稳/数值 | 四种状态严格分离 |
| C-I35 | 可恢复与不可恢复脱附 | 前者继续，后者需全路径证据后终止 |
| C-I36 | 光滑峰、尖峰、平台、多峰 | 正确分类并保存原始曲线 |
| C-I37 | 峰后稳定下降 | 继续加载，不在首峰终止 |
| C-I38 | 再挂接二次峰 | 原下降和二次峰均保留 |
| C-I39 | 未认证停止的能力输出 | \(F_{\rm crit}=null\)，保留当前观测最大值 |
| C-I40 | 理想 D4 对称 | 90° 旋转后曲线、事件和临界状态对应 |
| C-I41 | `+X/45°` 配对比较 | 使用独立 DamageStore 分支并保留四单元原始量 |
| C-I42 | 作用—反作用 | 力和力矩同时反号，峰值幅值一致 |
| C-I43 | 实验位移零点 | \(\delta_P=0\) 绑定同一锁定预紧态 |
| C-I44 | 确定性重放 | 同键返回同一收据/状态，无重复累计 |
| C-I45 | 表示一致性 | 合法坐标/参考点变换不改变功、反力、事件和能力 |
| C-I46 | 单位缩放 | N 与 N·mm 只经版本化尺度组合 |
| C-I47 | 原始曲线不可覆盖 | 滤波和单调包络只能作为派生通道 |
| C-I48 | 终止证据闭合 | 只有物理终止/分支覆盖充分时确认 \(F_{\rm crit}\) |
| C-I49 | 预紧停止后法向自由度 | 锁定 \(s_{\rm stop}\) 不等于冻结 \(u_{z_i}\) 或低层弹簧 |
| C-I50 | 未授权试验架反力 | 必须作为诊断暴露，不能加入承载能力 |
| C-I51 | 单元作用点不可用 | 保留完整 wrench/free couple，不伪造单点力 |
| C-I52 | 峰值与事件竞争 | 更早物理/认证事件优先，峰值括区间不能覆盖它 |
| C-I53 | 迁移器保真 | 旧 C1/C2/C3 状态迁移不改变物理历史或补默认值 |
| C-I54 | 独立方向损伤 | `+X` 与 `45°` 不共享加载后 DamageStore |

### 18.1 解析恒等式

至少自动检查：

\[
\mathbf R_{Gi}^{\mathsf T}\mathbf R_{Gi}=\mathbf I,
\qquad
\det\mathbf R_{Gi}=1,
\]

\[
Q_s^{\rm drive}=\sum_iR_{x_i},
\]

\[
\mathbf J_i^{\mathsf T}\mathbf W_i
=
\begin{bmatrix}
\mathbf R_{Gi}\mathbf F_i\\
\mathbf R_{Gi}\mathbf M_i+
\mathbf r_i\times\mathbf R_{Gi}\mathbf F_i
\end{bmatrix},
\]

\[
\mathbf b_P^{\mathsf T}\Delta\mathbf q_C
=
\hat{\mathbf d}^{\mathsf T}\Delta\mathbf u_P,
\]

以及第 2.5、4.5.3、11.1、11.2 节的全部符号式。

### 18.2 数值收敛扫描

实现阶段至少扫描：

- 预紧和加载步长；
- 最小事件步和括区间；
- 同时事件容差；
- B 平衡/graph 和 C 六维残量容差；
- DamageStore fixed-point 容差和迭代上限；
- 姿态 trust region；
- 一侧稳定性扰动和长度尺度；
- 峰值位移/反力容差、平台窗口；
- 分支探索策略；
- 并行浮点归约顺序。

主要状态、事件位置、\(s_{\rm stop}\)、\(\delta_P\)、\(F_{\max}^{\rm obs}\)、\(F_{\rm crit}\)、终止类型、DamageStore 和四单元临界分配应随设置收敛。未收敛只能报告数值不确定性。

### 18.3 故障注入

必须覆盖：

- 任一 B prepare 失败；
- DamageStore prepare/commit 失败；
- C 路径或峰值账本持久化失败；
- 提交收据丢失后同键重试；
- 版本/哈希在 trial 与 prepare 之间变化；
- 并行调用延迟和返回顺序置换；
- 同位置级联达到上限；
- 最小步耗尽；
- graph 分支数量爆炸；
- 作用点/姿态/单位元数据缺失。

每种故障均必须证明全部物理历史回滚，且 last-valid accepted state 可确定性重放。

## 19. 已知风险

1. B 2.x 未实现，正式偏心加载当前不可运行；
2. 单元显著退化依赖配置，错误阈值会把普通事件升级为失败；
3. graph 非唯一和损伤软化可能形成多个可达分支，探索不充分会低估能力；
4. 局部稳定性可能漏掉远处分支或有限扰动失稳；
5. DamageStore 跨单元 fixed point 可能非唯一或难收敛；
6. 作用线、自由力偶和执行器边界处理错误会制造隐藏支承或重复载荷；
7. 峰值和事件接近时，位移/反力误差会影响候选排序；
8. 表面随机性和方向相关性可能要求较大样本量；
9. 历史文献特殊模型不提供本项目材料、表面或逐针历史参数；
10. 状态迁移和 opaque 句柄若实现不完整，会造成不可见的历史重置；
11. 单元 capsule 若未严格哈希姿态、DamageStore 和分支，会错误复用旧切线；
12. 当前没有求解器代码和目标实验，全部验证仍是待执行规范。

## 20. 候选模型完成判据核对

- [x] C1/C2/C3 已映射为一个状态唯一、阶段化的 C 模型。
- [x] 坐标、参考点、80 mm 力臂、50 mm 加载点、作用方向和单位只有一个规范定义。
- [x] \(s\)、\(s_{\rm stop}\)、\(\delta_P\)、刚体位姿和可选 \(\eta_i\) 已分离。
- [x] contact-only、\(P_i\)、径向驱动、加载器和约束反力已分栏。
- [x] C1 理想 \(-P_i du_{z_i}\) 与完整执行器功可用性已统一。
- [x] C 不重建 A/B 接触、柔顺、载荷共享、失效和损伤。
- [x] rocking 被定义为刚体自由度，不是弹性柔顺。
- [x] 首针失效、单元退化、峰值、无平衡、失稳和脱附已分离。
- [x] 全局最早事件、同时事件、DamageStore fixed point、同位置级联、Zeno 防护和原子事务已统一。
- [x] 单步算法包含运动覆盖审计、四单元 trial、完整重平衡、稳定性、峰值、prepare、commit 和 rollback。
- [x] 首峰后合法稳定分支继续，\(F_{\rm crit}\) 仅在证据闭合后确认。
- [x] B 1.0 正式非零加载安全拒绝，且零历史推进。
- [x] B 2.x 保持为待接受扩展要求，没有被写成正式合同。
- [x] `+X/45°` 比较保留配对初态、四单元原始量和峰后路径，不预设优劣。
- [x] 公共上游、最终系统和实验接口足以独立实现和审计。
- [x] 未决参数、实现、数值和实验缺口均保留关闭条件。
- [x] 未开始全局 A/B/C 集成，未修改低层正式模型或工程事实。

---

## 21. 最终认证声明

本 `C_INTEGRATED_MODEL 1.0.0-candidate` 已完成 C 大模块的理论一致性集成：同步预紧、联合停止、径向锁定、偏心刚体运动、六维 contact-only 平衡、事件后四单元重求、共享损伤、稳定反力曲线、峰后路径、能力确认和原子事务已经由一个规范状态族和一套可执行语义统一。

当前正式运行认证仍受上游合同约束：

```text
preload under B_TO_C 1.0.0:
  theoretically and contractually expressible in the accepted x/Z scope

nonzero formal eccentric loading under B_TO_C 1.0.0:
  C_CONTRACT_EXTENSION_REQUIRED
  no physical history advance
  no zero-capacity inference
  no F_crit confirmation
```

只有在完整 twist/动态姿态 B 扩展被正式接受，并完成本文件第 13、18 节所列兼容、事件、功、损伤、事务、稳定性和收敛验证后，才可把正式 `+X/45°` 偏心加载从“理论集成完成”升级为“在线物理调用已认证”。求解器代码和目标实验也必须在实际完成后单独更新认证状态。

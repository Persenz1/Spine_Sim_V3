# M03 SINGLE_SPINE 冻结需求

**需求标识：** `M03_SINGLE_SPINE_REQUIREMENTS`

**需求版本：** `1.0.0`

**状态：** `frozen`

**冻结日期：** `2026-07-20`

**适用实现：** M03 A-M0 本征单刺核、standalone 单刺驱动器、M00/M02 结果扩展和验证证据

**前置门：** `M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen`、`M01_SURFACE_REQUIREMENTS 1.0.0 frozen`、`M02_NUMERICS_REQUIREMENTS 1.0.0 frozen`

**后续窗口：** [M03 实现窗口提示词](../implementation_prompts/M03_SINGLE_SPINE_IMPLEMENTATION_WINDOW_PROMPT.md)

## 1. 权威输入、产品目标和来源身份

### 1.1 实际读取的权威输入

本需求冻结前完整读取并核对了：

- [项目 README](../../../README.md) 与 [theory 阅读入口](../../../theory/README.md)；
- [仿真器开发入口](../README.md)、[模块规划](../SIMULATOR_MODULE_PLAN.md)与[需求讨论工作流](../REQUIREMENTS_DISCUSSION_WORKFLOW.md)；
- [M00 FOUNDATION 冻结需求](M00_FOUNDATION_REQUIREMENTS.md)、[M01 SURFACE 冻结需求](M01_SURFACE_REQUIREMENTS.md)与[M02 NUMERICS 冻结需求](M02_NUMERICS_REQUIREMENTS.md)；
- [证据复核入口](../../../theory/evidence_reassessment/README.md)与[工程固定上下文](../../../theory/evidence_reassessment/engineering_fixed_context.md)；
- [A_INTEGRATED_MODEL 1.0.0 accepted](../../../theory/modules/A_INTEGRATED_MODEL.md)；
- [A_TO_B_CONTRACT 1.0.0 accepted](../../../theory/interfaces/A_TO_B_CONTRACT.md)；
- [A–C 分层机理独立复核](../../../theory/review/DERIVATION_VERIFICATION_2026-07-17.md)；
- [MECHANISM_DERIVATION_FORMAL 0.2.0-proposed](../../../theory/paper/MECHANISM_DERIVATION_FORMAL.md)；
- [开发期参数与标定政策](../../../theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md)；
- [DEV_BOOTSTRAP_PROFILE 0.1.0](../../../theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml)。

权威顺序冻结为：

1. 正式工程事实；
2. accepted A 与 accepted A→B 1.0.0；
3. 已冻结的 M00、M01、M02 软件合同；
4. 本 M03 软件产品合同；
5. 明示的 `DEV_POLICY` 和 `VALIDATION_ONLY` 内容。

独立复核确认的 P0/P1 修正不得照错实现。Formal 0.2.0-proposed 只允许以 `PROPOSED_SUPPLEMENT` 形成 additive 字段、外层操作协议、能力门或验证 fixture，不修改 accepted A 状态机和 A→B 公共接口。

### 1.2 第一版产品目标

M03 是服务趋势观察和参数选型的 A-M0 单刺产品。第一版必须能够：

- 在解析表面和无材料身份的合成表面上执行 `no_damage`；
- 使用刚性 Signorini/Coulomb 点接触、Euler–Bernoulli 梁和 A 权威安装分支；
- 完成初始搜索、0.5 N standalone 预载及累计 `+local-x` 100 mm 连续拖曳；
- 定位并提交接触建立、载荷建立、粘着/滑动、支持切换、释放、显式回位路径上的扫掠碰撞、再接触和再挂接；
- 返回 accepted A→B 1.0.0 的 side-effect-free embedded response；
- 保存不被筛选或摘要替代的 accepted 原始历史、committed events、rejected diagnostics、残量和功账本；
- 为 M03 验证图和后续 M06 正式绘图提供稳定字段。

全部第一版结果必须标记：

`DEV_PRIOR / synthetic_or_analytic_surface / no_damage / not_certifiable`。

M03 只能说明模型内趋势、分支和参数敏感性。不得声称预测真实砖面破坏、真实材料寿命、针体安全认证或阵列承载能力。

### 1.3 来源身份映射

| 身份 | M03 用途 |
|---|---|
| `FIXED_ENGINEERING` | N–mm–MPa 主单位、坐标、100 mm 路径、1 mm/s、L=4 mm、Pz=0.5 N standalone、4 mm 弹簧行程、参数候选集合 |
| `ACCEPTED_AUTHORITY` | A 本征方程、刚性接触、Coulomb、EB 梁、A 弹簧图、状态/事件、contact-only `A_on_B` wrench、A→B 1.0.0、事务所有权；按独立复核避免累计滑移、旧弹簧摘要和最近特征的错误解释 |
| `PROPOSED_SUPPLEMENT` | 独立复核要求闭合的全局左乘针尖姿态表达、五阶段分栏、外层 release/return/re-search 操作协议和附加 reason/status 字段；只能 additive |
| `DEV_POLICY` | 基线参数、条件 OFAT/交互见证扫描、合成表面 realization、数值激活阈值和最小证据包 |
| `VALIDATION_ONLY` | 解析平面/斜面/球冠/多峰 fixture、Timoshenko/corotational 对照、强制事件/事务故障和负例 |

所有 runtime 值必须保留 `requirement_origin`、`value_provenance`、authority reference、单位、状态、成熟度和 certification metadata。宽先验不得改名为标定值。

## 2. 产品边界、调用模式和依赖方向

### 2.1 两个首版产品面

M03 同时交付两个边界清楚的产品面：

1. `intrinsic_single_spine_kernel`
   - A 本征、低层、确定性单刺核；
   - 唯一对 B 的公共调用为 accepted `embedded_constitutive_trial`；
   - 输入规定背板增量和 immutable history；
   - 不拥有逐针 `Pz`，不搜索 B 的共同法向平衡；
   - trial 无永久副作用，只有外层事务授权后才提交。
2. `standalone_single_spine_driver`
   - 仅用于单刺验证、趋势和参数选型；
   - 拥有初始搜索、预载同伦、100 mm 拖曳和显式释放后操作编排；
   - 通过同一个本征核求局部物理，不复制第二套接触/梁/弹簧本构；
   - 不是 A→B 公共入口，B 不得调用它取得每针恒法向力。

两者在等价 prescribed base path 上必须给出同一 A 本征响应；差异只能来自 standalone 的外层搜索、载荷控制和操作路径。

### 2.2 M03 负责

- 复合针几何、当前针尖姿态和有限球冠合法性；
- M01 最近/并列候选的物理筛选、完整体部净空和查询质量门；
- 刚性 Signorini/Coulomb 活动图和客观粘滑语义；
- Euler–Bernoulli 梁、bending off 控制和 A 权威安装图；
- A-M0 本征残量、分支枚举、低层 signed guards、事件后重求和 trial intents；
- standalone 初始 pose、搜索、预载、拖曳、释放后显式操作协议；
- contact-only wrench、结构量、功、残量、阶段、事件和 capability 输出；
- M00/M02 extension、traceability、验证报告和 plot-ready 数据。

### 2.3 M03 不负责

- B 阵列几何、共享背板平衡、针间载荷分配、阵列筛选或最终4种方案；
- C/System 整机预紧、偏心加载、执行器、电机或阵列回馈；
- 材料损伤、断裂能反演、真实砖面破坏、DamageStore 写入；
- 针体屈服/断裂判断或强度认证；
- 实测形貌导入、材料摩擦识别或实验标定；
- M05 的多 seed 实验设计、scheduler、统计排名、Pareto 选择；
- M06 的正式交互绘图系统、颜色字体和出版版式。

M04 可在后续讨论中生成明显多于4种的阵列候选；本需求既不限定候选数，也不提前给阵列结论。M03 只提供不受 B/C 反向修改的单刺响应端口与原始历史。

### 2.4 依赖方向

```text
M00 identities/config/results/transactions
M01 immutable SurfaceRealization/query
M02 continuation/events/transactions/replay
                 ↓
        M03 intrinsic A-M0 kernel
                 ↓
   standalone driver     accepted A→B trial port
                 ↓                       ↓
 validation/trend data        future M04 caller only
```

M03 runtime 可依赖 M00、M01、M02 的公共 API；不得导入 M04/M05/M06 内部包。M01 不返回接触或承载；M02 不解释物理状态；M04/C 不得反向改变单刺本构。

## 3. 坐标、单位、姿态和规范标量

### 3.1 坐标和单位

- 墙面名义平面为 global `X-Y`，`+global-Z` 指向背板/自由空间；
- 单元局部基为 `{e_x,e_y,E_Z}`，`e_y=E_Z×e_x`；
- `+local-x` 从单元头部指向根部，是搜索统计和拖曳方向；
- 长度 mm、力 N、时间 s、角度 runtime 使用 rad、报告输入可使用 deg、力矩 N·mm、模量 MPa、刚度 N/mm；
- 所有 canonical vector/wrench 默认以 global frame 保存，并同时保存 frame/reference identity；局部量必须显式命名而非覆盖 global 字段。

初始未变形针轴为

\[
\mathbf a_0=
\cos\alpha\cos\beta\,\mathbf e_x+
\cos\alpha\sin\beta\,\mathbf e_y-
\sin\alpha\,\mathbf E_Z.
\]

当前正式分支 `beta=0`。`alpha` 是针轴与安装背板平面的夹角，不是表面坡度或实际接触角。

### 3.2 姿态 P0 闭合

accepted A 的公共字段和接口不改动；实现内部必须采用复核闭合的坐标类型。第一版选择 Formal 的全局左乘表达：

\[
\mathbf R_t=\exp([{}^G\boldsymbol\theta_b]_\times)\mathbf R_0,
\qquad
\mathbf a_t=\exp([{}^G\boldsymbol\theta_b]_\times)\mathbf a_0,
\]

其中 `R0 e1=a0`，梁转角是 global components。该闭合在 schema/provenance 中标为 `PROPOSED_SUPPLEMENT`，只修复内部坐标类型；不得声称修改 accepted A/A→B 状态或接口。禁止把已在 global frame 的 `a0` 再当局部向量二次旋转。

### 3.3 wrench、Rx 和任务方向有效承载

规范 wrench 始终为单刺 A 对背板 B 的 contact-only 作用：

\[
\mathbf F_{A\rightarrow B}=\sum_j\mathbf f_j,
\qquad
\mathbf M_{A\rightarrow B}^{O}=\sum_j(\mathbf p_j-\mathbf r_O)\times\mathbf f_j.
\]

- 方向：`A_on_B`；
- 参考点：请求声明的针基座/背板参考点 `O`；
- canonical frame：global；
- `opposite_wrench_B_on_A=-wrench_A_on_B`；
- 梁根反力、弹簧力和 standalone actuator 力不得再叠加到该 contact-only wrench；
- 首版点接触没有独立接触偶矩。

正抓附阻力为

\[
R_x=-\mathbf e_x\cdot\mathbf F_{A\rightarrow B}.
\]

一般任务方向量定义为 `R_task=-d_task·F_A_on_B`。首版 canonical `d_task=+local-x`；必须保存 direction vector、frame、reference 和数值分辨率。`R_task>0` 只表示当前点抵抗任务运动，不是整个 run 的二元成功。

## 4. 冻结参数、状态和扫描计划

### 4.1 参数表

| 参数 | 首版基线 | 扫描/控制 | 冻结状态与来源 |
|---|---:|---|---|
| `Rt` 针尖球半径 | 0.05 mm | `[0.05,0.10]` mm | design grid，`FIXED_ENGINEERING/DEV_PRIOR` |
| `d` 针径 | 0.80 mm | `[0.60,0.80]` mm | design grid，`FIXED_ENGINEERING` |
| `L` 安装座出口至针尖球心轴向距离 | 4.00 mm | 不扫描 | fixed engineering |
| `alpha` 安装角 | **60 deg** | `[50,60,70,80]` deg | 用户冻结基线；design grid |
| `beta` 偏航角 | 0 deg | 首版固定，不扫描但接口保留 | accepted engineering |
| `E` | 210000 MPa | `[200000,205000,210000]` MPa | handbook-range `DEV_PRIOR`，非材料证书 |
| `nu` | 0.30 | `[0.28,0.29,0.30]` | `DEV_PRIOR`；只随 bending-on 见证 |
| `mu` | 0.40 | `[0.15,0.25,0.40,0.60,0.80]` | wide prior sensitivity，非标定值 |
| standalone `Pz` | 0.50 N | 第一版固定 | standalone 外层工程工况；embedded 禁止出现 |
| drag speed | 1.00 mm/s | 第一版固定 | time mapping |
| drag travel | 100.00 mm | 第一版固定 | total accepted path，不因释放重置 |
| bending | `on` | `on/off` | on 主线，off 控制 |
| mount | `INDEPENDENT_AXIAL_SPRINGS` | 与 `RIGID_MOUNT` 对照 | A 权威分支 |
| `ks` | 0.50 N/mm | `[0.1,0.2,0.5,1.0,2.0]` N/mm | 仅 independent spring；wide prior |
| spring travel | `[0,4]` mm | 固定 | 0=原长，4=硬限位 |
| contact compliance | 0 mm/N | 不扫描 | rigid M0；不得重复柔顺 |
| material model | `no_damage` | 不扫描 | strength/damage unavailable |

`nu` 必须保留并用于适用性/参考对照，即使理想细长 EB 线性柔顺对它不敏感；不得伪造一条不存在的 `nu` 主效应。`E/nu` 在 bending-off 时不运行无意义扫描。`ks` 不得与 rigid mount 同时解释为有效物理参数。

### 4.2 单刺趋势案例

第一版 M03 不是 M05 全笛卡尔实验。冻结为下列可审计设计：

1. **几何主效应：** `2 Rt × 2 d × 4 alpha = 16`，其余取基线；
2. **条件 OFAT：** 在基线几何上扫描 `mu`、`rigid + 5 ks`、bending on/off；只在 bending-on 扫描 E 和 nu；去重后增加 14 个案例；
3. **交互见证：**
   - `2 Rt × {mu=0.15,0.80}`：4 条；
   - `2 d × {ks=0.1,2.0}`：4 条；
   - `{alpha=50,80} × {rigid, spring ks=0.5}`：4 条；
   - 其中2条与几何主效应共享，不重复运行。

上述12条交互记录中，2条 `Rt=0.05` 的摩擦端点已在条件 OFAT，2条 `d=0.80` 的弹簧端点已在条件 OFAT，2条 spring-baseline 角度端点已在几何主效应。因此 primary trend surface 上共 **36 个 distinct cases（约40个）**。不得扩成 `2×2×4×3×3×5×6×2` 的全笛卡尔；完整 DOE、统计效应和稳健排名延期 M05。

### 4.3 表面矩阵

| 组 | 配置 | 用途 |
|---|---|---|
| analytic regression | 平面、斜面、凸/凹球冠、构造多峰/最近特征切换 | 公式、事件、支持和负例；`VALIDATION_ONLY` |
| primary medium synthetic | `H=0.7`、`rms/reference_Rt=1`、`lc/reference_Rt=20`、anisotropy=1、direction=0、seed=30301 | 全部36个 distinct trend cases 的正式 M03 趋势面 |
| gentle smoke | `H=0.9`、`rms/reference_Rt=0.25`、`lc/reference_Rt=80`、seed=30302 | 基线参数 100 mm smoke |
| sharp smoke | `H=0.5`、`rms/reference_Rt=4`、`lc/reference_Rt=5`、seed=30303 | 基线参数 100 mm smoke |

三个 synthetic surfaces 均使用 `surface_scale_reference_Rt=0.05 mm`；扫描 tip `Rt` 不得改变 surface realization identity。配对案例必须复用同一 realization、域、路径起点和 query policy。三个 seed 只是固定工程见证，不是独立统计样本；多 seed ensemble 与置信区间延期 M05。

## 5. 请求、响应和配置合同

### 5.1 embedded 请求/响应

accepted `A_TO_B_CONTRACT 1.0.0` 原样生效。逻辑入口保持：

```text
SingleSpineTrialResponse evaluate_trial(
    EmbeddedSingleSpineTrialRequest request
)
```

request 必须原样支持 accepted 字段：`contract_id`、`contract_version`、`call_mode`、`needle_identity`、`surface_query_handle`、`base_pose_n`、`prescribed_base_increment`、`immutable_single_spine_state_n`、`shared_damage_store_snapshot`、`parameter_bundle`、`trial_identity`、`requested_tangent_mode`、`event_location_config`、`quality_request` 和 `continuation_hint`。

response 必须原样支持 accepted 字段组：wrench、geometry/contact、structure、material/damage capability、states/events、linearization、diagnostics 和 transaction handles。wrench 组至少保留 `direction=A_on_B`、force、moment、frame/reference/units、`opposite_wrench_B_on_A`、`grip_resistance_Rx`、uniqueness 和必要时的 admissible graph handle。

M0 适配规则：

- embedded request 中不得含 `Pz`、`per_spine_normal_force`、`single_spine_Pz` 或等价约束；出现时返回 `CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD`；
- `shared_damage_store_snapshot` 仍保留 accepted schema identity，但 `no_damage` 分支为只读、无 damage intents/write set；
- damage/strength 字段不得删除；按第13节明确返回 unavailable/not applicable；
- open embedded response 返回零 contact wrench 和 `OPEN_RESPONSE`，不得伪造恒力平衡；
- M03 additive 阶段字段位于 `m03` extension；不增删或重命名 accepted A→B 字段。

### 5.2 standalone 请求

`StandaloneSingleSpineRunRequest` 至少包含：

- schema/operation/run/case identities；
- immutable needle parameter bundle 与 provenance；
- immutable M01 `SurfaceRealization`/query handle；
- declared unit frame、task direction、reference point `O`；
- initial pose policy、search mode、preload target/continuation policy；
- 100 mm drag path、speed/time mapping；
- release operation capability/policy；
- M02 numerical config、quality request、diagnostic level；
- output/plot evidence policy；
- explicit no-damage and unavailable capability declarations。

所有默认值必须在 resolved request/config 中展开、哈希并保存；不允许隐藏默认。

### 5.3 standalone 响应

`StandaloneSingleSpineRunResponse` 至少返回：

- run/case/config/surface/parameter identities and hashes；
- terminal operation status 与是否完成100 mm；
- final accepted state/history/transaction receipt；
- canonical dataset references；
- error/failure/capability axes；
- summary references及其定义版本；
- replay manifest、validation/certification labels；
- 若停在 release pose，返回 pose、remaining path、remaining stored energy、unavailable protocol reason。

## 6. 初始位姿、预载、拖曳和释放后操作

### 6.1 初始位姿

standalone 从 undeformed beam、spring original length、zero contact force、`OPEN` 状态开始。`x_total=0`，局部路径起点固定；`a0` 由冻结 alpha/beta 得到。

初始 Z 不使用隐藏常数。驱动器沿 `+global-Z` 回退，直到整个有限球尖、锥段、针杆和安装座都满足 certified positive clearance：

\[
g_{start}\ge
\max(0.20R_t,\;\epsilon_{query}+0.01R_t),
\]

并通过 M01 域/质量门。resolved starting pose、实际最小 clearance、控制特征和 query receipt 必须保存。若找不到，返回 `M03_INITIAL_POSE_INFEASIBLE`，不得直接把针尖投影到表面。

### 6.2 初始搜索和预载

1. 固定 `u_x=0`，使用 accepted `NESTED_Z_SEARCH` 沿 `-global-Z` 定位最早合法球冠零载接触；
2. 每个 probe 都检查完整体部碰撞、所有适用候选和 M01 质量；
3. 事件点进入 `TIP_ZERO_LOAD`，此时可有 geometric candidate，但 `loaded_contact=false`；
4. standalone 以 `eta:0→1` 做法向力同伦，目标 `Pz=0.5 N`，保持 `u_x=0`；
5. 每个 eta 点重新求 `u_z` 和本征状态；不得从零载接触直接跳到0.5 N；
6. 目标达到后进入 accepted attached branch；证明不可行返回 `PRELOAD_INFEASIBLE`，数值未收敛保持独立失败分类。

### 6.3 100 mm 路径和时间映射

- 预载完成后沿 `+local-x` 单调拖曳，`x_total:0→100 mm`；
- nominal speed 为 1 mm/s，所以 canonical `drag_elapsed_time_s=x_total_mm/1`，正常完成时为100 s；
- `x_total` 与 `drag_elapsed_time` 只由 committed accepted movement 推进；trial、retry、event probe、rollback 不推进；
- 释放、再搜索或新 contact cycle 绝不重置 `x_total`、drag clock、work ledger、event序列和历史；
- 初始 Z 搜索/预载以及没有声明速度的 release operation 只有 operation coordinate，不伪造 physical time；若未来显式提供 operation speed，另存 `operation_elapsed_time`，不得改写 drag clock。

### 6.4 释放后外层协议

accepted A 只拥有低层接触、释放、碰撞和再接触语义。以下外层序列冻结为 `PROPOSED_SUPPLEMENT`：

```text
unload
→ drive-off/unlock
→ reverse-search or lift-off
→ swept collision checks
→ recontact guards
→ preload/reengagement
→ continue remaining +local-x travel
```

standalone driver 可作为 owner 执行该协议；未来 embedded 使用时由 C/System 外层编排。首版默认路径冻结为 `LIFT_OFF_RESEARCH_V1`（`PROPOSED_SUPPLEMENT`）：

1. `UNLOAD_AT_FIXED_X`：固定当前累计 x，将仍有效的 standalone normal-load target 由当前值同伦降至0；若接触先释放，最早 release event 优先；
2. `UNLOCK_AT_RELEASE`：关闭 standalone normal-force controller，保持 release pose 连续且不推进路径；
3. `LIFT_OFF_AT_FIXED_X`：从 release pose 沿 `+global-Z` 做准静态 continuation，直到完整tip/body/mount最小gap重新达到第6.1节 `g_start`，且梁/弹簧剩余能量低于 resolved M02 work/energy resolution；不得强制投影为零；
4. `RESEARCH_AT_FIXED_X`：沿同一Z走廊向 `-global-Z` 搜索最早合法 finite-cap zero-load contact；累计x和drag clock保持原值；
5. `RELOAD_AT_FIXED_X`：重新执行0→0.5 N preload homotopy；成功后建立reengagement并恢复剩余 `+local-x` drag。

上述每段均提供 pose interpolation、signed guards、swept envelope、quality gate 和终止条件；没有声明operation speed，所以不伪造物理operation time。M02 对每段使用同样的最早事件、event/post 重求和事务规则。若出现重复同位置release/recontact，按M02 cascade/Zeno门停止，不靠history reset逃逸。

若当前分支没有合法 return path，必须：

- 进入 `HOLD_AT_RELEASE_POSE` operation status；
- 保留梁/弹簧位移、储能、累计滑移、总路径、时间和事件历史；
- 返回 `M03_RELEASE_RETURN_PATH_UNAVAILABLE`、remaining travel 和当前 pose；
- 不得瞬时把梁/弹簧清零，不得跨到新接触，不得伪报100 mm完成。

## 7. 几何候选、有限球冠和查询质量门

### 7.1 候选集合

M01 complete-sphere 最近查询是几何证据，不是接触结论。M03 必须：

- 请求并保留最近、并列最近、previously active、邻域内可能切换的全部候选；
- 检查候选是局部最小/空球支持，而非距离极大或鞍点；
- 使用当前 `a_t` 过滤有限球冠合法性，并保存 legality margin；
- 比较全候选后选择活动图，不以 API 返回顺序或单一最近点硬编码；
- 对非光滑/多支持返回确定性图表或显式非唯一性；
- candidate identity 绑定 realization、feature/chart、query receipt 和位置，不能绑定调用顺序。

### 7.2 完整体部碰撞

每个 trial、event probe、return sweep 和 acceptance witness 都检查：

- spherical tip/cap；
- cone；
- shaft/弯曲中心线 envelope；
- mount/installation envelope。

`CONE_COLLISION`、`SHAFT_COLLISION` 或 `MOUNT_COLLISION` 触发 `BODY_COLLISION_INVALID`；它们不是 tip contact、不是 load-bearing，也不得继续纯球尖结果排名。bending-on 使用当前 EB 中心线/扫掠包络，bending-off 使用刚性轴包络。

### 7.3 查询质量门

物理接受点必须同时满足：

- query in-domain，coverage 包含完整当前/扫掠 footprint；
- capability 支持所需 height/normal/closest/support/distance/derivative；
- `TRUSTED_FOR_DECLARED_SCALE` 或等价 accepted M01 质量；
- raw error bound、normal/feature ambiguity、nonsmooth status 已保存；
- ahead search 至少 `Rt/5`，event/support 至少 `Rt/8`，acceptance witness 使用 `Rt/10`；
- `Rt/8→Rt/10` 事件位置、支持、法向、力/功通过第16节收敛门。

coverage 或质量不足必须 refine/extend；仍不闭合时返回 `GEOMETRY_UNCERTAIN`/M01原 reason，不得继续物理排名。

## 8. M0 物理闭合和柔顺去重

### 8.1 刚性 Signorini/Coulomb

每个支持满足：

\[
g_j\ge0,\quad \lambda_{n,j}\ge0,\quad g_j\lambda_{n,j}=0,
\qquad
\|\lambda_{t,j}\|\le\mu\lambda_{n,j}.
\]

真实滑移使用最大耗散，客观切向增量相对当前局部切平面计算。支持点迁移可为无滑移滚动；摩擦锥达到边界不自动提交滑移。第一版 `contact_compliance=0`，不允许将 penalty regularization 当物理刚度。

### 8.2 Euler–Bernoulli 梁

- bending-on 主线使用 accepted 3D EB 柔顺、位移/转角、根部力矩和梁储能；
- bending-off 令梁位移/转角/储能为零，但仍返回接触 resultant、root resultants 和 `needle_strength_status=UNAVAILABLE`；
- Timoshenko 与 corotational 仅为 `VALIDATION_ONLY` 回归/适用性见证，不成为第一版 production 分支；
- 超出小转角/细长梁适用域返回 `STRUCTURAL_MODEL_OUT_OF_RANGE`，不得继续伪精确趋势。

### 8.3 A 权威安装图

| spring state | 条件 | 力学语义 |
|---|---|---|
| `RIGID_LOCKED` | rigid mount | `delta_s=0`，反力为约束/可能集合值；禁止大 penalty 冒充 |
| `AT_ORIGINAL_LENGTH` | `delta_s=0` | `F_s=Q_s=0`，弹簧不能拉 |
| `COMPRESSING` | `0<delta_s<4 mm` | `Q_s=ks*delta_s` |
| `HARD_STOP` | `delta_s=4 mm` | `Q_s=ks*4+r_H`，`r_H>=0` |

弹簧 compression、remaining travel、force、hard-stop reaction 和 energy 独立输出。不得复制 B 的旧弹簧摘要或错误零位分支。

### 8.4 柔顺/能量唯一归属

第一版可储能元件只有启用的 EB 梁和 independent spring；rigid contact 不储存物理接触压缩能。不得：

- 同时把梁柔顺算进针尖运动学又串联重复一次；
- 把 spring compliance 同时放进 A 和 standalone actuator；
- 用数值 penalty 增加物理接触能；
- 把 contact-only wrench 与内部反力重复相加。

## 9. 五阶段分栏

本节全部为 `PROPOSED_SUPPLEMENT` additive diagnostics，不修改 accepted 主状态或 A→B 1.0.0。五项必须分别输出布尔值、reason、evidence references、criteria version；禁止提供一个可混淆的 `engaged` 布尔值。

| 阶段 | 冻结判据 |
|---|---|
| `geometric_candidate` | 至少一个 M01 质量通过、有限球冠合法、reachable/local-minimum、完整体部净空通过的候选；不要求 gap=0 或力非零 |
| `loaded_contact` | committed active support 中至少一个 `lambda_n` 大于 scale-aware activation tolerance，且 Signorini/quality 通过 |
| `frictionally_stable` | committed 接触图通过 Coulomb/SOC、one-sided branch feasibility/stability 和 graph quality；可对应 stick 或最大耗散 slide，粘滑另列 |
| `load_bearing` | `loaded_contact && frictionally_stable`，分支 accepted/feasible，且声明任务方向 `R_task` 大于 scale-aware force resolution；只是点态能力 |
| `released/reengaged` | 分开记录 release lifecycle：释放已提交；其后新 cycle 经合法再接触并重新预载为正载荷才是 reengaged；不得因 geometric recontact 自动置真 |

额外保存 accepted A 的 `candidate_any/candidate_robust` 方向裕度诊断；它们不替代 geometric candidate，也不自动成为 load-bearing。

必须覆盖以下反例：

- geometric candidate 但 gap/力仍为零；
- loaded contact 但摩擦图不稳定；
- frictionally stable 但 `R_task` 未达到正分辨率；
- recontact zero-load 但尚未 reengaged。

## 10. 主状态、正交状态和事件映射

### 10.1 accepted 主机械状态

M03 原样实现 accepted A 主状态：

`OPEN`、`TIP_ZERO_LOAD`、`PRELOAD_BUILD`、`ATTACHED_STICK`、`ATTACHED_SLIDE`、`REATTACHED_ENTRY`、`RELEASE_TRANSITION`、`REVERSIBLE_RETURN`、`TRAVEL_COMPLETE`。

解释约束：

- `ATTACHED_STICK` 指当前 committed objective slip increment/rate 为零，不要求历史累计滑移归零；
- `REVERSIBLE_RETURN` 只有显式 swept return path 完成时才可走到开放侧；不能解释成瞬时清零；
- `HOLD_AT_RELEASE_POSE` 是 standalone operation terminal status，不冒充 accepted A 主状态；
- `TRAVEL_COMPLETE` 只有累计100 mm accepted drag 完成或明确声明的非正常终止语义；非正常 hold 不得标为完成。

### 10.2 正交子状态

- contact motion per support：`OPEN`、`TOUCH_ZERO_LOAD`、`STICKING_INTERIOR`、`STICKING_AT_CONE_BOUNDARY`、`ROLLING_NO_SLIP`、`SLIDING_COMMITTED`、`SUPPORT_SWITCH_PENDING`、`RELEASE_PENDING`；
- spring：`RIGID_LOCKED`、`AT_ORIGINAL_LENGTH`、`COMPRESSING`、`HARD_STOP`；
- beam/model：`BENDING_OFF`、`EB_ELASTIC`、`STRUCTURAL_MODEL_OUT_OF_RANGE`；
- material：固定 `NO_DAMAGE_MODEL`；
- needle strength：固定 `NEEDLE_STRENGTH_UNAVAILABLE`，除非仅进行 validation adapter fault test；
- quality/solve：沿用 accepted A 与 M02 的独立状态轴；
- standalone operation phase（`PROPOSED_SUPPLEMENT`）：`INITIAL_CLEARANCE`、`INITIAL_SEARCH`、`INITIAL_PRELOAD`、`DRAG`、`UNLOAD`、`DRIVE_OFF_UNLOCK`、`REVERSE_SEARCH`、`LIFT_OFF`、`RESEARCH`、`RELOAD`、`HOLD_RELEASE_POSE`、`COMPLETE`。

### 10.3 事件和 owner

| 事件族 | 语义 owner | 第一版处理 |
|---|---|---|
| tip contact/load onset/release | A/M03 | signed guard、event/post重求、commit |
| friction cone/slip confirmed | A/M03 | 锥边界与真实滑移分开 |
| support/chart/cap legality | A/M03 + M01 evidence | 全候选重评 |
| spring original/hard stop | A/M03 | A权威图切换 |
| cone/shaft/mount collision | A/M03 | fatal pure-tip invalid |
| domain/geometry quality | M01 evidence，A解释 | refine或停止 |
| preload target/infeasible | standalone | 同伦完成或分类失败 |
| release path start/segment/end | standalone/C-System owner | `PROPOSED_SUPPLEMENT` operation event |
| swept collision/recontact | A guard + outer path | 最早事件；新cycle |
| reengagement | A+standalone | 新cycle预载成功后提交 |
| travel complete | standalone | `x_total=100 mm` |

必须使用 M02 raw dimensional signed guards、bracket、earliestness、simultaneous set、cascade、event/post重求和 atomic transaction。event ID 只用于确定性无依赖排序，不是物理优先级。数值未收敛不是物理事件。

## 11. canonical 原始输出

### 11.1 M00 extension datasets

M03 注册 owner `M03`、namespace `m03` 的 versioned `ResultExtensionDescriptor`。冻结数据集为：

| dataset | 每行/对象 | 关键关系 |
|---|---|---|
| `m03.run_requests` | resolved standalone/embedded request与参数/表面/配置哈希 | run/case identity |
| `m03.accepted_state_history` | 每个 committed accepted point 的完整 A 状态 | 引用 M00 accepted point/receipt |
| `m03.support_candidate_history` | 每接受点、每候选的几何/质量/合法性 | accepted point + candidate identity |
| `m03.contact_support_history` | 每接受点、每 active/near support 的力、gap、切基、motion | accepted point + support identity |
| `m03.committed_event_payloads` | A语义 event raw guard、owner payload、pre/event/post引用 | 引用 M02 committed event，不复制identity |
| `m03.release_operation_history` | operation phase/path segment/swept guard/recontact lifecycle | event/cycle/path coordinate |
| `m03.rejected_diagnostics` | rejected trial/event probe/branch diagnostics | 引用 M02 trial/rejection；永不进入物理曲线 |
| `m03.work_ledger` | 每接受增量的功、储能、耗散、误差 | accepted interval/receipt |
| `m03.contact_cycle_records` | cycle开始/结束、支持集合、release/recontact链 | raw lifecycle records |
| `m03.capability_status` | damage/strength/return-path/model availability | run/case/branch |
| `m03.derived_summaries` | versioned optional summaries | 输入accepted IDs及definition hash |
| `m03.plot_recipe_manifest` | recipe字段、分组、filter、事件和数据缺口 | 只读消费合同 |

COMPACT/STANDARD/FULL 可改变存储密度和 diagnostics 细节，但不得丢失 canonical accepted points、committed event identities、failure/capability 或摘要输入引用。任何 filtered/resampled 数据都是 derived，不得替代 raw accepted history。

### 11.2 每个 accepted point 的必需字段

每个 accepted point 至少保存：

- run/case/accepted point/parent/receipt/config/parameter/surface identities；
- `x_total_mm`、`drag_elapsed_time_s`、operation path coordinate、cycle ID、event sequence；
- base/root/tip pose、`a0`、`a_t`、reference point、global/local transforms；
- candidate/support IDs、points、feature/chart、legal/effective gaps、cap margins、normals/tangent bases；
- cone/shaft/mount gaps与最小完整体部 clearance；
- M01 query receipt、LOD、error bound、quality/domain/nonsmooth flags；
- per-support `lambda_n`、tangential multipliers、global contact force、objective slip increment和motion substate；
- contact resultant `Fx,Fy,Fz,Mx,My,Mz`，`A_on_B` direction/frame/reference；
- `Rx`、`R_task`、task direction和force resolution；
- beam translation/rotation global + needle basis、root force/moment、section resultants、beam energy/model validity；
- spring state、compression、remaining travel、force、hard-stop reaction和spring energy；
- accepted primary state、orthogonal states、五阶段分栏及各自reason/evidence；
- residual blocks raw/unit/reference/scale/normalized quality、complementarity/SOC/graph/Jacobian diagnostics；
- work/energy increment、cumulative fields和error；
- capability/certification status；
- 相互独立的 `theory_defined`、`code_implemented`、`numerically_verified`、`experimentally_validated` 四栏成熟度；不得压成一个 completed/validated 布尔值。

### 11.3 committed events

每个 committed event 必须保留：

- raw signed guard/unit/zero/admissible side/direction；
- bracket/probe/earliestness/simultaneous/cascade references；
- pre-side、event-point、transition、post-side accepted response hashes；
- old/new primary和orthogonal states；
- support/branch/path/cycle identities；
- event 前后 wrench、structure、spring、stored/released energy；
- transaction receipt和one-sided consistency。

event/post 必须完整重求，禁止复用 pre-event wrench、pose、Jacobian、graph multiplier或structure values。

### 11.4 rejected diagnostics

rejected trial、line search、retry、event probe、failed branch 和 rollback 必须与 accepted/event datasets 隔离。保存 reason family、raw residual/guard、solver trace、quality、rollback token和parent reference；不得推进 path/time/slip/work/cycle/peak/history，也不得被默认 plot/summary 消费。

### 11.5 字段元数据和采样不变量

每个 extension field 的 machine-readable metadata 必须声明：semantics/class、dtype、shape、unit、frame、reference point、entity/path/event index、accepted/trial/event/summary归属、canonical/derived/diagnostic分类、null/unavailable政策、sampling cadence、schema version、source identity和四栏成熟度。至少遵守：

- 标量连续量使用明确精度的数值dtype，3D vector为shape `[3]`，6D wrench为shape `[6]`或force/moment各`[3]`，不得以未声明长度list代替；
- ID/hash/reason/status/event/state使用稳定string/enum，不使用裸整数猜测语义；
- stage值为独立bool/enum并配套reason/evidence，不允许null暗示false；
- accepted history每个committed point采样，support/candidate按point×entity采样，work按accepted interval采样，event按committed pre/event/post采样，rejected diagnostics按trial/probe采样；
- unavailable数值使用typed null + capability/reason；禁止NaN充当unavailable。

## 12. 功、残量和释放时剩余储能

每个 accepted increment 保存唯一账本：

- base/standalone actuator input work，方向与 A→B 功共轭一致；
- `delta_U_beam`、`delta_U_spring`；
- rigid contact energy = 0；
- friction dissipation，必须非负；
- material dissipation = 0，状态 `NO_DAMAGE_MODEL`；
- released/returned recoverable energy；
- numerical/work closure error raw和normalized；
- cumulative work/energy，释放后不清零。

释放点必须先记录剩余梁/弹簧储能。只有显式 return path 上实际减少的储能才能进入 returned/released energy；`HOLD_AT_RELEASE_POSE` 时剩余储能继续保留，不得凭空消失。

## 13. 可选摘要、多峰与 unavailable 字段

### 13.1 versioned optional summaries

所有摘要必须保存 definition ID/version、input accepted ID range、right-censor status 和 raw dataset links。至少提供：

- first loaded-contact distance；
- first load-bearing distance；100 mm 内未发生时明确 right-censored；
- geometric/loaded/frictionally-stable 但未 load-bearing 的 false-engagement episodes；
- release→recontact、release→reengagement distance/time/cycle records；
- contact cycle count、loaded/load-bearing path fraction；
- per-cycle/multi-peak raw record links，以及可选峰位置/值/drop；
- positive resisting work、friction dissipation、returned energy；
- max/mean/quantile 只作为描述量，不构成 binary success/composite score。

峰值不能替代100 mm曲线，也不能单独成为成功判据。第一版不生成实验统计置信区间、阵列排名或综合评分。

### 13.2 必须显式 unavailable

M0 `no_damage` 下：

- `material_model_id=no_damage`，`material_substate=NO_DAMAGE_MODEL`；
- `damage`, initiation/capacity/failure mode、fracture energy、trial damage intents/write set 均为 typed `NOT_APPLICABLE`/empty，不得伪造零损伤变量代表真实无限材料；
- `material_dissipation=0` 仅表示该模型没有材料损伤通道；
- `failure_prediction_allowed=false`；
- `yield_margin`、`fracture_margin`、stress-concentration-based certification 字段为 null + `NEEDLE_STRENGTH_UNAVAILABLE`；
- root resultants仍必须输出，但不得转成安全系数或认证结论；
- run-level `experimentally_validated=NOT_ASSESSED`、`not_certifiable=true`。

缺失这些 unavailable 状态即 schema/验收失败。

## 14. 首批图和交互筛选需求

### 14.1 所有图的共同规则

- 默认只读 accepted raw 与 committed events；rejected diagnostics 必须显式 opt-in；
- 默认无平滑、无过滤；若展示 derived curve，raw 曲线仍可见且 recipe保存算法/参数；
- x轴默认累计 `x_total_mm`，时间图使用不重置的 `drag_elapsed_time_s`；
- release/recontact 后不分段重置坐标；cycle 仅以颜色/带/marker区分；
- 事件 marker 使用 committed event position，未提交候选不得混入；
- 每图保存 recipe/config/data hash、units、frame/reference、source/maturity/certification；
- 同一趋势比较使用共同 surface realization/path；失败/hold/unavailable 以状态显示，不补线。

### 14.2 冻结 recipe 族

1. **Response overview**
   - `Rx-x`、`Rx-t`、`uz-x`；
   - 完整 `Fx,Fy,Fz` 与 `Mx,My,Mz`，方向标为 `A_on_B`、reference O；
   - release、recontact、reengagement、slip、hard stop、travel complete markers。
2. **State bands**
   - accepted primary mechanical state；
   - standalone operation phase；
   - contact motion stick/slide/rolling/open 与 active support count；
   - spring state。
3. **Five-stage funnel bands (`PROPOSED_SUPPLEMENT`)**
   - geometric candidate、loaded contact、frictionally stable、load-bearing 四条独立 binary lanes；
   - release/recontact/reengagement 事件链和cycle ID；
   - 禁止合成 `engaged` lane。
4. **Local geometry**
   - event/selected point 周围 surface、contact/support points、法向、切基、needle axis、finite cap、cone/shaft/mount outline与task direction；
   - 展示candidate rejected reason与body clearance；不把M01坡度命名为啮合。
5. **Structure and spring**
   - beam tip displacement/rotation components与norm；
   - root resultants；
   - spring compression、remaining travel、force、hard-stop reaction；
   - release时剩余储能。
6. **Event zoom and multi-peak**
   - event前/点/后 raw 放大、signed guard/bracket/probe；
   - release→swept return→recontact→reengagement链；
   - contact cycles和多峰原始记录。
7. **Quality and work**
   - residual blocks raw/normalized、complementarity/SOC/graph error；
   - query/LOD quality；
   - work closure error、beam/spring energy、friction dissipation/returned energy。
8. **Parameter trends**
   - `Rt,d,alpha,mu,ks` 的 paired raw comparisons；
   - 按parameter family facet，不用单一综合分数；
   - E/nu、bending、mount作为技术附图或filter。

### 14.3 交互筛选字段

M03 必须输出足够字段，使 M06 可按以下维度筛选：

- surface family/realization/seed/scale；
- case/design ID、Rt、d、L、alpha、beta、E、nu、mu；
- bending、mount、ks、spring state；
- primary/contact/operation state、五阶段、cycle/event kind；
- frame/reference/task direction；
- accepted/committed/rejected source class（默认前两类）；
- maturity/source/certification/capability status；
- x/t view、global/local component view。

M03 实现窗口生成最小静态 validation evidence pack 和 machine-readable recipes；production interactive UI、颜色、字体、出版版式属于 M06。solver/base runtime 不得依赖 plotting package。

## 15. reason codes 和失败分类

M03 新增 reason codes 至少包括：

- `M03_INVALID_REQUEST`；
- `M03_KINEMATIC_MODE_UNSUPPORTED`；
- `M03_DUPLICATE_NORMAL_LOAD`（映射 accepted contract violation）；
- `M03_INITIAL_POSE_INFEASIBLE`；
- `M03_PRELOAD_INFEASIBLE`；
- `M03_RELEASE_RETURN_PATH_UNAVAILABLE`；
- `M03_HOLD_AT_RELEASE_POSE`；
- `M03_BODY_COLLISION_INVALID`；
- `M03_FINITE_CAP_SUPPORT_UNAVAILABLE`；
- `M03_TASK_DIRECTION_INVALID`；
- `M03_MATERIAL_DAMAGE_UNAVAILABLE`；
- `M03_NEEDLE_STRENGTH_CERTIFICATION_UNAVAILABLE`；
- `M03_STRUCTURAL_MODEL_OUT_OF_RANGE`。

必须保留 M01/M02 原始 reason code 并映射到 M00 failure family，不得改写。`NUMERICAL_FAILURE`、`PHYSICAL_INFEASIBLE`、`CONTRACT_REJECTION`、`DOMAIN_ERROR`、`TRANSACTION_FAILURE` 和 `CAPABILITY_UNAVAILABLE` 为独立轴；数值失败不得参与设计性能比较。

## 16. 测试和验收矩阵

### 16.1 几何和查询

- 平面/斜面/凸凹球冠的gap、最近点、法向、有限cap合法性解析值；
- 多峰、并列最近、previous support、chart switch与全候选比较；
- 局部极大/鞍点不被误选；
- cone/shaft/mount及bent-centerline碰撞；
- domain/coverage/quality/refinement failures原样分类；
- `Rt/5→Rt/8→Rt/10`；`Rt/8→Rt/10` witness要求：event位置≤`0.01Rt`、适用unique support≤`0.02Rt`、normal≤1 deg、force/work summary≤1%、event order完全一致，否则继续refine或失败。

### 16.2 contact/friction

- open、zero-load touch、positive-load Signorini解析解；
- **geometric candidate但零力**负例；
- `mu=0` 无切向承载；
- sticking interior、cone boundary但仍粘着、真实slip maximum-dissipation；
- loaded但frictionally unstable；frictionally stable但非task load-bearing；
- 客观滑移、无滑移滚动和support migration分离；
- action/reaction、reference transport、Rx/task sign与功不变。

### 16.3 beam、spring和去重

- EB cantilever displacement/rotation/root resultant/energy解析回归；
- Timoshenko/corotational `VALIDATION_ONLY` 细长/小转角收敛见证；
- bending-off量归零但root resultant/unavailable strength仍返回；
- spring original length不能拉、interior `ks*delta`、4 mm hard stop、unload；
- rigid mount set-valued/constraint语义，不用大penalty；
- 梁、弹簧、接触柔顺只计一次；能量和tangent/response随branch切换一致。

### 16.4 路径和事件

- 初始certified clearance→最早zero-load contact→preload homotopy→100 mm；
- 1 mm/s下`x/t`映射，释放后累计路径/时间不重置；
- contact load onset、friction boundary、confirmed slip、support switch、cap loss、spring zero/stop、release、recontact、reengagement顺序；
- 大步/减半步、同号端点含内部事件、touch event、simultaneous/cascade；
- event/post完整重求且不复用旧response；
- release时记录储能，显式return sweep检查collision/recontact；
- 无return path时hold release pose并返回剩余路径/能量；
- **释放后不清零历史**负例：path/time/slip/work/event/cycle保持；
- recontact zero-load不能自动reengaged。

### 16.5 standalone/embedded和事务

- 等价 prescribed path 上standalone内部核与embedded response一致；
- embedded open为zero wrench，拒绝per-spine Pz；
- repeated trial/line search/retry/rollback不改变accepted history；
- prepare/commit/idempotency/fault injection无partial state；
- accepted、event、rejected datasets严格隔离；
- deterministic semantic replay；支持时bitwise replay；serial/parallel/cold-warm M01 cache不改变semantic结果。

### 16.6 功、残量和输出

- raw residual block硬门、complementarity/SOC/graph/Jacobian质量；
- 输入功=梁能变化+弹簧能变化+friction dissipation+returned-energy/work terms+数值误差，按冻结符号审计；
- step/event/LOD refinement下残量、功和物理曲线收敛；
- ResultWriter/Reader round trip、relations/hash/manifest/replay；
- summaries可由accepted raw重新生成；删除summary不损失raw；
- rejected数据不改变峰、首次承载、功或趋势；
- damage/strength/certification unavailable字段齐全。

### 16.7 表面和趋势案例

- analytic plane/slope/cap/multi-peak suite全部通过；
- medium synthetic 上36个 distinct cases 完整100 mm或明确、可审计的物理/能力终止；数值失败不得当趋势点；
- gentle/sharp baseline smoke各100 mm或明确终止；
- paired cases共享同一surface realization/path/query policy；
- 验证 `Rt,d,alpha,mu,ks` 变化数据可由plot recipe读取，不要求单调性先验，也不得修改数据迎合预期。

### 16.8 性能与可调度性

- case-by-case streaming，不能一次在内存保留全部36条FULL历史；
- 遵守 M00/M01/M02 已冻结cache和artifact策略，不生成150×150 mm全域`Rt/10` dense grid；
- 报告每case accepted/trial/event/query数、wall time、peak RSS、cache和artifact size；
- baseline、36-case campaign和validation suite均可暂停/恢复/replay；
- 第一版不冻结跨硬件wall-time阈值，但任何无界内存增长、全域密网格或无法完成baseline 100 mm均验收失败。

## 17. schema、API和跨模块闭合

### 17.1 M00闭合

- 使用M00 identity、status、source/maturity/certification、registry、ResultWriter/Reader、transaction receipt和ReplayManifest；
- 只注册`m03` extension，不复制core accepted/event/receipt identity；
- raw/summary/manifest关系和字段metadata完整。

### 17.2 M01闭合

- M01只提供immutable geometry evidence；M03拥有finite cap、姿态、体部碰撞和物理语义；
- `surface_scale_reference_Rt`固定，tip Rt扫描不重生成surface；
- query/LOD/error/domain receipt原样保存；M03不裁剪、wrap、rerandomize或修改surface。

### 17.3 M02闭合

- M03提供residual/guard/branch/post-side/transaction callbacks，M02拥有数值编排；
- characteristic length明确传入Rt；
- accepted/event/rejected隔离、earliestness、cascade、return sweep和rollback遵守M02；
- M03不复制continuation/event/transaction engine。

### 17.4 accepted A→B闭合

- 唯一B入口仍为`embedded_constitutive_trial`；
- request/response字段、A_on_B方向、reference、power、open response、tangent/graph、opaque history、trial side-effect rules原样保持；
- embedded没有Pz；standalone driver永不暴露为B公共入口；
- 五阶段和release outer protocol位于additive `m03` extension并标`PROPOSED_SUPPLEMENT`；
- no-damage适配不删除accepted material/strength capability字段；
- B/C不得修改A history、本构、mu、梁、spring或候选选择。

## 18. 明确延期和禁止项

### 18.1 延期

- 材料损伤、traction–separation、断裂能和真实砖面破坏：未来M1/实验闭合后；
- 针体牌号、yield/ultimate/SCF和强度认证：参数与适用桥闭合后；
- measured surface：M01未来能力；
- beta扫描、Timoshenko/corotational production、大转角/动态：未来版本；
- 阵列候选生成、载荷共享和多于4种阵列筛选：M04需求讨论；
- 多seed DOE、统计排名、Pareto和最终设计缩减：M05；
- 正式交互/出版绘图：M06；
- C/System完整回位、执行器和整机认证：后续合同。

### 18.2 禁止

- 把接触峰值、geometric candidate、loaded contact或frictionally stable当binary success/load-bearing；
- 使用一个`engaged`布尔值覆盖五阶段；
- 释放后重置100 mm path/time或瞬时清零梁/弹簧再跨到新接触；
- 无return path仍自动继续；
- 把filtered/summary/rejected数据替代accepted raw；
- 重复计算梁/弹簧/contact compliance或wrench；
- 用penalty值当物理刚度；
- 把宽先验称标定值或把synthetic surface称真实砖面；
- 输出damage/failure/strength certification数值；
- 让B/C反向调整单刺本构或在M03启动阵列；
- 修改accepted theory、M00–M02 frozen requirements或A→B接口。

## 19. 决策日志和关闭状态

### 19.1 accepted

- standalone + embedded kernel 双边界；embedded只读本征trial，无Pz；
- alpha baseline由用户冻结为60 deg；其余基线/扫描按第4节；
- bending on主线/off控制；spring ks=0.5主线、rigid对照、4 mm hard stop；
- 36-case single-spine conditional scan、medium共同realization、gentle/sharp smoke；
- 初始clearance、nested Z search、preload homotopy、100 mm/100 s drag clock；
- full candidate/finite cap/body collision/query gate；
- accepted主状态+正交状态，不合并engaged；
- contact-only A_on_B wrench、Rx/task-bearing、structure/spring/work raw；
- accepted/event/rejected隔离、versioned summaries和首批plot recipes；
- no-damage、strength unavailable、not certifiable；
- M04阵列广泛候选另窗讨论，M03不启动B。

### 19.2 `PROPOSED_SUPPLEMENT` accepted as additive only

- 全局左乘姿态P0闭合；
- 五阶段分栏与reason/evidence；
- standalone/C-System外层release→return/research协议和operation phases；
- additive M03 reason/status/plot lanes。

这些内容没有修改accepted A状态集合或A→B 1.0.0。

### 19.3 rejected

- alpha baseline 70 deg；
- 全参数全笛卡尔扫描；
- M03多seed统计排名；
- hidden initial Z、zero-load直接跳0.5 N、release瞬时清零；
- 一开始只保留4种阵列；
- peak/binary/composite score；
- damage/strength无限能力默认。

### 19.4 deferred

见第18.1节。

### 19.5 unresolved

无。实现内部非语义选择由实现窗口自行完成；若必须改变本文件语义或accepted接口，返回blocker并开启新的requirements版本，不得静默决定。

## 20. 实现窗口完成判据

M03实现窗口只有同时满足以下条件才可完成：

1. 交付本征核、standalone驱动器、accepted A→B adapter，未实现B阵列；
2. 交付参数/请求/响应/state/event/reason/output typed contracts并严格校验；
3. 交付M00/M01/M02集成和`m03` result extension；
4. 通过第16节完整解析、负例、事件、事务、refinement和output验收；
5. 完成analytic suite、medium 36 cases、gentle/sharp smoke，或对每个非完成case给出非数值伪装的明确终止；
6. 生成可重放canonical result bundle、最小validation figure evidence和machine-readable plot recipes；
7. 生成traceability、validation、performance、acceptance报告，清楚区分fixed/accepted/proposed/dev/validation身份；
8. 报告必须明确`experimentally_validated=NOT_ASSESSED`、`not_certifiable`、damage/strength unavailable和剩余风险；
9. 全量回归、lint、format、type、build、schema、link、import-boundary、replay检查通过；
10. 核对M00–M02和accepted A→B闭合，无竞争schema、无duplicate Pz、无B/C反向影响；
11. 按Git安全交接保留无关改动，只精确暂存M03实现/测试/报告及明确批准的最小兼容修复，检查cached diff，提交推送后停止；
12. 不自动开始M04、M05或M06。

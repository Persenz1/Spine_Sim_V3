# 第 28 组反向审查：LORIS 轻量自由攀爬机器人

**审查身份：** non-normative individual reverse audit；只审第 28 组，不修改 accepted 1.0。
**文献：** Nadan, Backus, Johnson, *LORIS: A Lightweight Free-Climbing Robot for Extreme Terrain Exploration*，ICRA 2024，DOI `10.1109/ICRA57147.2024.10611653`。
**总判定：** 未发现现行完整机理与该文在相同对象、假设和适用域下的真冲突。该文对“定向子爪合成方向承载、内部预载可提高附着裕度、失效后必须重判系统可恢复性”提供趋势支持；方向域设计、最小裕度诊断、控制层零空间接口和机器人支撑集失效是可补充候选。LORIS 的 carriage、被动腕和多足整机不是本项目刚性阵列单元/刚性十字对爪的同一硬件，不能用其公式或数值覆盖现行机理。

**引用约定：** 表中短文件名均指仓库内 `theory/evidence_reassessment/literature/28_loris_lightweight_free_climbing_robot/evidence_card.md`、同目录 `extraction_audit.json`、`theory/paper/MECHANISM_DERIVATION_FORMAL.md`、`theory/modules/A_INTEGRATED_MODEL.md`、`B_INTEGRATED_MODEL.md`、`C_INTEGRATED_MODEL.md`、`theory/system/SYSTEM_INTEGRATED_MODEL.md`；冒号后的数字均为 1-based 行号。

## 1. 提取完整性与适用域

- 提取审计覆盖 PDF 全 7 页，并视觉复核全部页面及保留的 Fig. 2、3、5；三幅裁图本次再次目视核对，符号、方向、角度图和四组裕度均与卡片一致（`theory/evidence_reassessment/literature/28_loris_lightweight_free_climbing_robot/extraction_audit.json:11-24`）。审计状态为 `PASS_WITH_WARNINGS`（同文件 `:169`）。
- 文献对象是“两组外张 carriage + 三自由度被动腕 + 四足多接触 DIG 控制”；逐 carriage 用方向弹簧等效，不解析 13 根刺的载荷共享（`.../28_loris_lightweight_free_climbing_robot/evidence_card.md:19-28`；`.../extraction_audit.json:132-135`）。
- 本项目对象是有限球尖单刺、共同刚性背板阵列及四单元刚性十字参考体（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:29-35`）；工程事实明确禁止单元相对整爪独立转动及框架/导轨柔性（`theory/evidence_reassessment/engineering_fixed_context.md:291-298`）。因此只迁移现象、上层结构或验证义务，不迁移机构边界。

## 2. M1–M6 逐项对照

| # | 卡片原结论与本地来源 | 现行机理对应位置 | 分类 | 判定、优先级与置信度 |
|---:|---|---|---|---|
| 1 | M1/E1：不同方向 carriage 的力经旋转求和，形成扇形面内承载域（`evidence_card.md:22-28,87-101`） | 四个单元方向为 ±X/±Y，wrench 经旋转、移矩后求和（`MECHANISM_DERIVATION_FORMAL.md:1334-1359`）；B 也只装配逐针 contact-only wrench 总和（`B_INTEGRATED_MODEL.md:723-735`） | `supported` | 支持“定向子结构响应必须在同一参考点矢量合成”的建模方向；不支持把 E1 的 lumped `k_i` 取代 A/B 逐刺解。P2，高。 |
| 2 | M1：任一 carriage 投影反向即判抓取失败（`evidence_card.md:22-26,99-100`） | 现行模型要求针事件后全阵列重平衡，首针失效不等于单元失败（`B_INTEGRATED_MODEL.md:856-882,1757-1759`）；单元脱离也不自动等于整爪不可恢复（`SYSTEM_INTEGRATED_MODEL.md:1610-1624`） | `insufficient_evidence` | **表面冲突、非真冲突**：LORIS 明示的是 carriage 级保守失效假设，现行模型解析逐刺/逐单元剩余能力。不得把该假设改写成当前终止规则。P0，高。 |
| 3 | M2/V1：等刚度、等间距且“任一 carriage 反向即失败”时，两 carriage 的方向边界优于 3/5/10/100；增加分支不必扩大边界（`evidence_card.md:30-39,183-189`） | B 扫描的是 2–6×2–6 根针、固定/梯度倾角和刚/弹簧安装（`B_INTEGRATED_MODEL.md:96-110`），当前正式扫描 `beta=0`（同文件 `:588-608`），没有 carriage 数—方向域扫描 | `supplement_candidate` | 漏掉了重要的**非单调设计警示**。建议作为 B/C 布局验证义务，而不是“微刺越少越好”的结论。P2，中高。 |
| 4 | M2：LORIS 最外侧 `alpha_max>约45°` 会因初始攻角过陡而难挂接（`evidence_card.md:33-38`） | 本项目扫描的 50°/60°/70°/80° 是针轴安装倾角（`B_INTEGRATED_MODEL.md:100-107`），不是 LORIS 面内 carriage 外张角 | `insufficient_evidence` | **表面冲突、非真冲突**：两个 `alpha` 的几何定义不同。45° 不能限制或否定当前 50°–80° 扫描；可迁移的只是“方向承载与初始挂接必须联合评价”。P0，高。 |
| 5 | M3/E2：至少三点接触的共点被动腕可自适应 pitch/roll；转轴位置决定拉离分量，yaw 又依赖面内重力（`evidence_card.md:41-50,103-126`） | proposed 主线选择共同刚体 pose 的 C-R，锁定后单元保持刚性关系（`MECHANISM_DERIVATION_FORMAL.md:1399-1448`）；工程事实排除单元独立转动（`engineering_fixed_context.md:291-298`） | `insufficient_evidence` | **硬件范围差异**，不是现行刚性边界与文献冲突。不得静默加入腕自由度、无摩擦基接触或重力自对准。若未来改机构，应新建模型/合同版本。P0，高。 |
| 6 | M3/V2：转轴宜靠近最大承载时微刺合力线；三点/无摩擦基接触失效时模型失效（`evidence_card.md:44-50,191-197`） | 系统已要求输出作用线/CoP，并在无唯一点时返回轴线或不可用（`SYSTEM_INTEGRATED_MODEL.md:2093-2095`）；当前 B 2.x 交接也要求作用线/CoP/free-couple（同文件 `:1168-1176`） | `supplement_candidate` | 可补成“若存在真实转轴/铰链，检查转轴—合力线偏距与接触集有效性”的设计诊断；当前无腕时 `not_applicable`。P3，中。 |
| 7 | M4：刺级法向柔顺 + carriage 独立俯转形成跨尺度贴合（`evidence_card.md:52-61`） | A 已分离局部接触、针梁、逐针轴向弹簧，并分别记能量（`A_INTEGRATED_MODEL.md:1332-1346`）；B 背板共同刚性运动，禁止安装座内转动（`B_INTEGRATED_MODEL.md:918-930`） | `supported` | 文献支持“柔顺应按物理位置分层且不可用总斜率混拟”的方向；现行已覆盖刺/安装级，但没有 carriage 俯转级。P2，中高。 |
| 8 | M4 的 carriage 最大 30°、低刚度复位弹簧和 TPU 蛇形柔顺（`evidence_card.md:55-60,170-173`） | 当前系统不得新增框架/导轨/rocking 弹性（`SYSTEM_INTEGRATED_MODEL.md:225-233`），夹具/根部柔顺仅列为关闭的未来模型（`A_INTEGRATED_MODEL.md:1339-1346`） | `supplement_candidate` | 仅可作为未来“可转 carriage”硬件备选及曲率适应验证项；必须新模型 ID、CAD/止挡/转矩—转角和能量闭合，不能加入当前 accepted 主线。P3，中。 |
| 9 | M5/E3：在整体力/矩平衡和各爪能力约束下最大化最小附着裕度，内转爪自然生成零净 wrench 的 DIG 内力（`evidence_card.md:63-72,128-149`） | C 已有完整六维平衡和历史相关单元 graph（`C_INTEGRATED_MODEL.md:1194-1249,1335-1372`），但系统明确禁止用固定 LP/能力域跨事件外推（`SYSTEM_INTEGRATED_MODEL.md:2393-2406`） | `supplement_candidate` | 建议新增**只读、状态局部** `attachment_margin_LB`/最弱单元裕度诊断或外层设计优化；能力约束必须来自当前 B graph、保留历史并在事件处完整回调。E3 可作线性 fixture，不能成为物理主求解器。P1，中高。 |
| 10 | M5/V3：对置定向内力可提高附着裕度；外张与内转方向组合优于单独改变之一（`evidence_card.md:66-72,199-205`） | C 同步预紧中全局面内力可相消而共同径向驱动反力仍非零（`C_INTEGRATED_MODEL.md:956-1016`）；系统已有对应验证构造（`SYSTEM_INTEGRATED_MODEL.md:2122-2126`） | `supported` | 定性支持“内部预载可在零净面内力下改变各单元安全裕度”。LORIS 的多足姿态不验证本项目十字对爪的数值增益或最佳方向。P2，中高。 |
| 11 | M6/E4：抓取映射零空间投影维持足间内力，不改变机体净 wrench（`evidence_card.md:74-83,151-163`） | 当前 B 明确排除任意控制器（`B_INTEGRATED_MODEL.md:113-125`）；未来 B 2.x 才要求 6D graph 的 rank/nullspace（`SYSTEM_INTEGRATED_MODEL.md:1168-1185`） | `supplement_candidate` | 可作为未来控制层接口：命令必须投影到真实、当前秩的内力子空间，并受执行器饱和、接触切换、状态相关刚度、功和全量 trial 约束；不得写进接触本构。P2，中。 |
| 12 | M6：三足支撑时单爪意外脱离常导致不可恢复跌落（`evidence_card.md:77-83`；`extraction_audit.json:165`） | 当前最高对象是十字对爪而非四足机器人；其规则是单元失载后重平衡并证明是否可恢复（`SYSTEM_INTEGRATED_MODEL.md:1609-1624`） | `supplement_candidate` | 漏掉的是**机器人级支撑集拓扑**：未来整机层应把单爪脱离作为离散事件，按剩余支撑多边形/抓取映射、动态余量和恢复策略重判；不能反向把它变成针/单元级自动终止。P1，中高。 |
| 13 | V4：DIG 砌块对照的步失败率 6.4%→2.3%、全程成功 1/10→6/10（`evidence_card.md:74-81,207-213`） | 现行验证矩阵仅为 `SPEC_DEFINED`，没有求解器、参数或实验通过证据（`SYSTEM_INTEGRATED_MODEL.md:2046-2059`）；趋势验证义务尚未执行（同文件 `:2160-2166`） | `insufficient_evidence` | 可作外部趋势先验，不能声称验证了红砖/混凝土、十字对爪或某个参数。样本小、人工选点且无显著性检验（`evidence_card.md:240-245`）。P1，高。 |

## 3. 真冲突与表面冲突

**真冲突：0 项。** 文献没有在本项目相同的刚性十字硬件、逐刺历史相关接触、同一表面与同一边界条件下给出相反结论。

表面冲突有四类：①“任一 carriage 反向即整抓失败”对“逐刺/逐单元重平衡”，是聚合尺度和保守判据不同；②“两 carriage 优于更多”对“多针阵列扫描”，是 carriage 数与刺数两个设计变量；③被动腕对刚性 C-R，是硬件边界不同；④ LORIS 的固定线性 LP 对现行历史相关非线性 graph，是局部近似与主求解器适用域不同。四者均不得登记为 accepted 机理冲突。

还需保持规范身份边界：严格稿的 C-R 是 `0.1.0-proposed`，accepted C 仍保留各单元独立法向平衡表达；这一本地边界已由独立复核登记为 P0-SYS2（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:409-420`）。LORIS 具有另一套被动腕和腿部执行器边界，既不能裁决 C-R/C-I，也不能关闭 B 1.0 的局部 y、真实转动和 6D graph 缺口；后者仍须按复核要求安全拒绝（同文件 `:387-407`）。

## 4. 漏掉的关键结论与建议补充

1. **P1：状态局部最小附着裕度。** 在 C/System 输出层增加 proposed `attachment_margin_LB`：输入当前四单元 admissible graph、完整六维平衡、边界与不确定性；输出最弱单元/约束、裕度下界和失效原因。活动集、DamageStore、姿态或事件变化即失效并完整回调。验证：线性化 fixture 复现 E3，随后用非线性/事件案例证明不跨域外推。
2. **P1：机器人级支撑集事件接口。** 在未来整机层增加 `GRIPPER_LOSS_SUPPORT_SET_REEVALUATION`，把剩余支撑、抓取映射秩、可恢复路径和跌落风险列为新证据；不修改 A/B/C 的低层“先重平衡再升级”规则。
3. **P2：方向域与布局联合扫描。** 在 B 2.x/C 设计验证加入方向采样、初始挂接距离/概率、持续能力、峰值和事件联合输出；比较分支数、方位和外张角是否非单调。身份是验证义务/设计诊断，不是 LORIS E1 的新本构。
4. **P2：控制层内力子空间接口。** 仅在完整 6D rank/nullspace、执行器端点、估计误差、饱和和接触切换闭合后加入；每个控制步仍必须经物理 trial、事件定位和原子提交。
5. **P3：被动腕/可转 carriage 备选。** 只有工程硬件更改时才新建可选模型，显式加入 pivot、基接触、止挡、复位弹簧、作用线和功；当前主线保持 `not_applicable`。

## 5. 不可直接移植的参数或结论

- 不移植两 carriage、`±45°` 外张、26 根刺、carriage 30°、腕 `±35°/±35°/360°`、3.2 kg、0.20 m/min、1.88/1.89/2.65/5.53 N、失败率、全程成功率和约 9.3% 功耗增量；它们是 LORIS 几何/姿态/表面的样机或单情景结果（`evidence_card.md:170-179`）。
- 不移植 `k_i`、`f_min/f_max`、`theta_max/phi_max`、`phi_slip`、`k_p`、抓取映射或力估计误差；论文没有给完整标定，且力域参数与力估计精度均有缺口（`extraction_audit.json:137-149`）。
- 不移植“carriage 更多必然更差”“45° 是通用挂接阈值”“单爪脱离必然整机跌落”或“DIG 对所有表面均有同等收益”。卡片已明确等刚度、固定接触集、小样本和跨表面不可比边界（`extraction_audit.json:157-165`）。
- 不用砌块、玄武岩、炉渣或凝灰岩结果反推本项目红砖的粗糙度、摩擦、逐刺挂接概率或材料容量（`evidence_card.md:229-245`）。

## 6. 优先级结论

- **P0 / 高置信：** 没有新发现的 P0 真冲突；必须阻止角度同名误映射、LORIS 数值移植、被动腕覆盖刚性工程事实，以及用固定 LP/单 carriage 规则替代历史相关重平衡。
- **P1 / 中高置信：** 增加状态局部裕度下界与未来机器人支撑集失效接口；它们补足上层决策信息，但不改变低层物理。
- **P2 / 中等至中高置信：** 增加方向域—初始挂接联合扫描与未来零空间内力控制验证。
- **P3 / 中等置信：** 被动腕和 carriage 级转动柔顺只作为硬件变更后的独立备选模型。

**最终回答：** 该卡对现行机理没有真冲突；现行机理已覆盖矢量装配、分层柔顺的一部分、对置内部预载以及事件后重平衡。真正遗漏的是方向域非单调设计约束、局部最小附着裕度、控制层内力子空间和机器人级单爪丢失后支撑集重判。它们都可补充为 proposed 输出/验证/上层接口，但该文不足以提供本项目公式闭合或定量参数。

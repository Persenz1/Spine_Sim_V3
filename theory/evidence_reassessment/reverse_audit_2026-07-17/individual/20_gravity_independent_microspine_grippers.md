# 第 20 组反向审查：Gravity-independent Microspine Grippers

**审查身份：** non-normative evidence reverse audit；不修改 accepted 1.0，不把论文样机参数提升为本项目参数。
**文献：** Parness et al., *Gravity-independent Rock-climbing Robot and a Sample Acquisition Tool with Microspine Grippers*, 2013，DOI `10.1002/rob.21476`（身份见 `theory/evidence_reassessment/literature/20_gravity_independent_microspine_grippers/evidence_card.md:L3-L10`）。

**引用简称：** 下文 `CARD` 均指 `theory/evidence_reassessment/literature/20_gravity_independent_microspine_grippers/evidence_card.md`，`AUDIT` 均指同目录 `extraction_audit.json`；其后的 `Lx-Ly` 均为该文件 1-based 行号。图片文件无文本行号，故以 `CARD` 中对应图片入口行定位。

## 1. 提取完整性与适用域

- 提取审计覆盖 PDF 19/19 页，关键页以 260 dpi 复核，Eq. (1)、Eq. (2)–(3) 与 Table I 均逐图核验；Eq. (4) 因仅为钻机滚珠丝杠电机选型而省略（`AUDIT:L17-L24`、`AUDIT:L38-L64`）。最终状态为 `PASS_WITH_WARNINGS`（`AUDIT:L183-L195`），足以审查定性机理和公式边界，但不提供完整统计、表面形貌、摩擦或强度数据。
- 论文对象是 **16 个径向独立车架、每车架 16 刺、中心绞盘收紧、车架级串联柔顺** 的天然岩石整爪及其攀爬/钻削系统；本项目对象是 **四个规则阵列单元、刚性背板、刚性十字参考体、针级梁/单边轴向弹簧**。因此架构、柔顺位置和外载边界不同。
- 本轮主审 proposed 严格稿 `MECHANISM_DERIVATION_FORMAL 0.1.0-proposed`，同时以 accepted A/B/C/System 和验证报告约束结论。验证报告明确 accepted 只表示理论合同被接受，代码、数值、实验均未验证（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:L32-L41`）。
- 分类遵循严格同域判断：只有“同一物理对象、同一自由度/边界、同一加载与材料假设”下结论不相容才记为 `conflict`；仅因论文样机多了车架柔顺、主动抬离、钻削扰动或整机运动学，不把范围外现象误判成冲突。反过来，现行文档出现一个状态名或条件公式，也不自动记为已充分支持：若主线为 `no_damage`、参数仍 `unavailable`、B→C 合同尚未覆盖或验证状态仍是 `BLOCKED_UNAVAILABLE`，本报告只承认现象方向/接口位置被容纳，不承认数值能力已闭合。`supplement_candidate` 只表示值得进入 proposed 限制、可选模型、输出或验证义务；任何候选都不能越过固定工程事实和 accepted 合同。

## 2. 逐项结论

| # | 原始文献结论与本地来源 | 现行机理对应位置 | 分类 | 审查理由 | 优先级 / 置信度 |
|---:|---|---|---|---|---|
| 1 | M1：相反方位径向搜索，把多个单向阵列汇集成跨方向整爪能力（`CARD:L19-L28`；Fig. 5 入口为 `CARD:L176-L178`） | proposed 四单元方向与 wrench 求和：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L1334-L1359`；accepted C 的 ±X/±Y 坐标：`theory/modules/C_INTEGRATED_MODEL.md:L205-L231` | `supported` | “方位分散的单向单元 + 整爪装配”这一骨架一致。16 方位连续近似与四方位十字并非同一几何，论文只支持建模方向，不证明四单元能力数值。 | P2 / 高 |
| 2 | M1/V1/V2：样机在法向、45°、切向均有承载（`CARD:L124-L150`），但试验尽量中心加载、抑制力矩（`CARD:L25-L28`、`CARD:L199-L204`） | B→C 1.0 对 +X、45°、rocking 明确缺 local-y/转动：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L1362-L1395`；验证结论：`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:L387-L407` | `insufficient_evidence` | 论文的三方向中心拉脱不能关闭本项目 50 mm 偏心六维路径，更不能越过当前合同安全拒绝。若据此声称 +X/45°/rocking 已验证，会与证据边界冲突；这不是物理机理冲突。 | P0 / 高 |
| 3 | M2：车架适应 cm 起伏、车架内独立刺适应 mm/更小粗糙度，形成两级柔顺（`CARD:L30-L39`；Fig. 5 `CARD:L176-L178`） | A 已分开建模针梁和针级弹簧：`theory/modules/A_INTEGRATED_MODEL.md:L647-L737`；B 背板保持共同刚性装配：`theory/modules/B_INTEGRATED_MODEL.md:L632-L657`；C 禁止新增框架柔顺：`theory/modules/C_INTEGRATED_MODEL.md:L1618-L1629` | `supplement_candidate` | 针级独立柔顺已覆盖；cm 级车架/框架顺应缺失，但这是固定架构差异，不能直接加进 accepted 主线。可补为“适用域/设计备选”说明：当前模型不代表论文的两级车架构型，若实物出现单元安装顺应，须另立版本化机构模型。 | P2 / 高 |
| 4 | V3：单车架载荷与整爪外载不强相关，不能按总载同比分配（`CARD:L152-L158`；无相关系数/数据集：`AUDIT:L168-L170`） | proposed 由逐针本构和共同平衡得到不均载、事件后重解：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L1257-L1276`；独立复核确认非经验分配：`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:L278-L312` | `supported` | 现行机理比论文定性结论更严格：不设比例分载或固定转移矩阵。论文可作为趋势级外部证据，但不足以给载荷分布概率律。 | P1 / 高 |
| 5 | M3：先压向表面、径向搜索，挂接后串联元件增载；释放先卸中心张力再抬离（`CARD:L41-L50`、`CARD:L188-L193`） | A 的接触—预载—附着—释放—回位—再挂接状态：`theory/modules/A_INTEGRATED_MODEL.md:L1367-L1414`；C 共同搜索/驱动反力：`theory/modules/C_INTEGRATED_MODEL.md:L906-L986` | `supported` | 搜索、接触、建立载荷、释放、再搜索的物理顺序已存在。现行“释放”是接触事件/回位边界，不等同论文的独立主动抬离执行器；后者另列第 6 项。 | P1 / 高 |
| 6 | M3：独立主动脱离降低卡滞；论文给出易卡滞 `<5%`、仍不能脱离 `<1%`，但无试验次数/置信区间（`CARD:L43-L50`、`CARD:L120-L123`） | proposed 只在释放 pose 终止或另开扫掠回位路径：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L1904-L1906`；A 明确排除复杂控制器/安装内部真实结构：`theory/modules/A_INTEGRATED_MODEL.md:L83-L85` | `supplement_candidate` | 可补一个**条件性操作协议/验证义务**：若本项目硬件确有主动抬离机构，记录 `UNLOAD_DRIVE -> LIFT_OFF -> CLEAR`、卡滞与复位结果；没有 CAD 端点、行程和试验时不得加入主物理算子。上述百分数本身属 `insufficient_evidence`，不可移植。 | P2 / 中高 |
| 7 | M4/E1：缆角、力臂和扭簧矩决定切向/法向反力权衡；单一矩式不能闭合两个反力（`CARD:L52-L61`、`CARD:L87-L100`；Fig. 7 `CARD:L180-L182`） | proposed 已把真实执行器端点/作用线缺失标为预紧认证阻断：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L1496-L1529`；当前复核 P0-SYS2：`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:L409-L420` | `supplement_candidate` | 文献强化现有 P0 义务：执行器几何会改变反力组合，必须冻结本项目 CAD 端点、作用线、双端反力和功。Eq. (1) 属另一车架的二维、欠定自由体，不能拿来关闭本项目边界。 | P0 / 高 |
| 8 | E2：对称二维钻削截面中，钻头轴向反力由两侧锚定反力之和限制（`CARD:L102-L114`；Fig. 19 `CARD:L184-L186`） | 本项目采用完整六维平衡且只允许授权外载/约束：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L1640-L1681` | `insufficient_evidence` | 论文式忽略周向钻削扭矩和完整力矩，且本项目没有钻削任务。可作通用“扰动不得超过锚定域”的说明，不能进入十字对爪方程或参数。 | P3 / 高 |
| 9 | M5：粗糙度收益会被表面易碎/松散材料失效截断（`CARD:L63-L72`、`CARD:L137-L143`） | proposed 明分 `M0=no_damage` 与条件材料扩展 M1：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L78-L103`、`:L889-L925`；验证要求 M1 首版仍用 `no_damage`：`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:L255-L263` | `supported` | “几何候选多不等于材料承载高”的方向与现行几何/材料分层一致；但可执行主线 M0 不能再现松散/易碎破坏，M1 也未获目标材料参数，故仅支持现象和模型分支必要性，不支持公式/数值。 | P1 / 高 |
| 10 | V1：跨材料试验同时记录滑脱与材料先破坏，Table I 每格仅 5 次且无离散性（`CARD:L137-L143`、`CARD:L197-L203`） | A 已区分 `CONTACT_RELEASE`、`MATERIAL_INITIATION/FULL_FAILURE` 等事件：`theory/modules/A_INTEGRATED_MODEL.md:L1427-L1441`；系统仍把目标表面统计、摩擦和强度列为未决：`theory/system/SYSTEM_INTEGRATED_MODEL.md:L2198-L2202` | `supplement_candidate` | 可补**目标材料验证义务和输出字段**：同一表面族报告 `failure_mode`、峰值分布、事件顺序及“几何粗糙但材料先坏”的比例；红砖/混凝土/砂纸须自行测量和留出验证，不拟合论文岩石均值。 | P1 / 高 |
| 11 | M6：柔顺改善均载，却造成下垂、定位误差和起孔游走；不能只最大化顺应性（`CARD:L74-L83`、`CARD:L160-L171`） | C 当前只保留针梁/针级弹簧，十字参考体为刚体：`theory/modules/C_INTEGRATED_MODEL.md:L1618-L1629`；系统禁止新增框架柔顺：`theory/system/SYSTEM_INTEGRATED_MODEL.md:L225-L232` | `supplement_candidate` | 可在不改变刚体工程事实的前提下，补**多目标验证**：在相同载荷下同时输出 `N_eff/载荷离散度`、整体/单元位姿误差、有效刚度和剩余行程；若未来引入连接/框架柔顺，必须新建模型版本。 | P2 / 中高 |
| 12 | M6/V5：柔顺能衰减钻削振动，但会放大起孔游走并偶发脱附（`CARD:L167-L172`） | proposed 明确准静态且排除释放冲击：`theory/paper/MECHANISM_DERIVATION_FORMAL.md:L107-L139`；accepted A 排除惯性、冲击和复杂控制：`theory/modules/A_INTEGRATED_MODEL.md:L83-L85` | `insufficient_evidence` | 这是动态钻削—机器人系统结论，超出现行准静态接触域。只能作为未来动态扩展的风险提示，不能以准静态弹簧储能替代振动传递函数。 | P3 / 高 |
| 13 | 样机规模、质量、三方向拉脱、攀爬角、重力卸载、感知误差和约 60 N 钻削力（`CARD:L116-L133`） | accepted C 明确材料/表面/损伤参数 unresolved，代码/实验 not verified：`theory/modules/C_INTEGRATED_MODEL.md:L2821-L2835`；系统同样禁止固定未决数值：`theory/system/SYSTEM_INTEGRATED_MODEL.md:L225-L233` | `insufficient_evidence` | 对象、材料、几何、加载和统计均不相同；这些值只能保留为文献背景/趋势下界，不能成为红砖、混凝土、砂纸或四单元十字爪的先验均值、验收阈值或能力下界。 | P1 / 高 |

## 3. 真冲突与表面冲突

**真正冲突：0 项。** 未发现现行机理与论文在相同对象、边界和适用域下给出不相容结论。

表面冲突均可由范围差异消解：

1. 论文的 16 径向车架不是本项目四单元十字布局；“论文三方向已承载”不能反驳当前 B→C 合同对 +X/45° 的安全拒绝。
2. 论文车架串联元件在挂接后伸长；本项目针级轴向弹簧只压缩、无预压、不可受拉。二者位于不同物理位置，不得共用状态、刚度或符号。
3. 论文中心加载刻意抑制力矩；本项目正式目标是 50 mm 偏心载荷和六维平衡。二维拉脱能力与六维偏心能力不是同一量。
4. 论文的振动衰减、机器人下垂和钻削游走属于动态/整机运动学；现行模型是准静态接触与刚性十字参考体，未声称覆盖这些现象。

## 4. 漏掉的关键结论与可补充项

1. **两级柔顺的架构适用域（P2）：** 现行机理完整描述针级柔顺，但没有论文的车架级 cm 尺度顺应。应补“本模型不代表两级径向车架”的限制；只有实物证实存在该自由度，才另立机构模型。
2. **主动脱离的操作顺序和卡滞结果（P2）：** 可补为条件性外部操作协议及试验输出，不得把论文脱离率当项目概率。
3. **执行器几何决定反力组合（既有 P0 的证据强化）：** Eq. (1) 不可移植，但它强化了冻结端点、作用线、力臂、双端作用—反作用和功的必要性；文献不能替项目 CAD 闭合这一 P0。
4. **粗糙度—材料强度联合验证（P1）：** 增加按目标表面族区分 `滑脱/材料破坏/几何或模型终止` 的实验验证和原始输出；这比只比较峰值更贴合论文关键结论。
5. **柔顺多目标评价（P2）：** 参数优化不得只看峰值或 `N_eff`；应同时报告位姿误差、有效刚度、剩余行程和载荷离散度。动态减振仍保持 `unavailable`，除非建立并验证动态模型。

## 5. 不可直接移植的公式、参数或结论

- Eq. (1) 的 (M_k,T,d_1,d_2,d_3,\theta,R_x,R_y)：属于论文二维车架/缆线机构，且一个矩式不能唯一解两个反力。
- Eq. (2)–(3)：只适用于对称二维钻削截面，不是本项目对爪平衡或六维承载式。
- `16×16=256`、飞行型 `80` 点、1.05 kg、`<5%/<1%` 卡滞率、Fig. 8 的 `>130/>150/>140 N`。
- Table I 八种材料的法向/45°/切向五次试验均值、松散材料 `0.2–3.1 N`；它们不是红砖、混凝土或砂纸参数。
- `<5%` 车架测力误差、10 kg/105° 攀爬、30–60% 重力卸载、约 60 N 钻削进给力；均不得作为本项目传感、整机或载荷验收值。

## 6. 优先级结论

- **P0：** 无新增真正冲突；必须继续执行现有 P0-SYS1/P0-SYS2。该文既不能解除 B 1.0 的 +X/45°/rocking 阻断，也不能替代真实执行器边界。
- **P1：** 增加目标材料的滑脱/材料破坏分支验证；严禁迁移论文力值、概率和材料均值；保留“不按总载比例分配”的实验检查。
- **P2：** 补两级柔顺适用域、主动脱离操作协议和柔顺—位姿精度多目标输出。
- **P3：** 钻削二维平衡、振动衰减和整机攀爬结果仅作未来扩展背景。

**总判定：** `supported=4`，`supplement_candidate=5`，`conflict=0`，`insufficient_evidence=4`。论文与现行完整机理没有真冲突；其最有价值的补充不是新增承载公式，而是三项边界/验证义务：两级柔顺适用域、主动脱离/卡滞记录、以及粗糙度收益受材料易碎性截断并须与位姿代价一起验证。

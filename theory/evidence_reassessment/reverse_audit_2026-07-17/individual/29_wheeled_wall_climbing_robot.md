# 29 — A Wheeled Wall-Climbing Robot with Bio-Inspired Spine Mechanisms 反向审查

**状态：** non-normative reverse-audit working material
**审查对象：** `MECHANISM_DERIVATION_FORMAL 0.1.0-proposed`，并以 accepted A/B/C、SYSTEM 与独立复核为边界
**总体判定：** 未发现同对象、同假设、同适用域下的真正冲突；发现 4 项可补充内容，另有 6 类公式、参数或样机结论不得直接移植。

## 1. 文献身份、完整性与适用域

P29 是 2015 年轮式微刺机器人论文，连接 S 形柔顺单刺、二维多刺分载、尾支撑整机平衡和砖面试验；证据卡将其相关性定为 B（条件启用），并明确二维固定接触限制直接迁移（`theory/evidence_reassessment/literature/29_wheeled_wall_climbing_robot/evidence_card.md:3-13`）。提取审计覆盖全部 12 页，逐页目视检查，关键页以 300 dpi 复核（`theory/evidence_reassessment/literature/29_wheeled_wall_climbing_robot/extraction_audit.json:12-19`），最终为 `PASS_WITH_WARNINGS`（`extraction_audit.json:215-217`）。本次另核对了 Figs. 3–4、5–6、11：前两图确认 S 形悬架/轮转和二维固定铰主动集，Fig. 11 确认四个转角的过零拟合散点，而非通用材料包络；图片身份见 `evidence_card.md:272-284`。

适用域是二维、两轮对称、准静态、小变形、固定铰且脱离前无滑移；硬件为每轮 `16×4=64` 刺，但二维模型将其折成 `n=64` 等角排列且未解释轴向映射（`evidence_card.md:43-52,213-225,295-302`；`extraction_audit.json:190-202`）。因此定性链可信度高，精确分载、砖面系数和整机数值移植可信度低至中。

## 2. 逐项结论

| ID | 原结论与本地来源 | 现行机理对应 | 分类 | 优先级 / 置信度 | 判定 |
|---|---|---|---|---|---|
| 29-01 | 轮转经历预压—挂接—承载—拉脱，M1（`evidence_card.md:21-30`） | accepted A 已有 OPEN、零载接触、预载、承载、释放、回位和再挂接状态（`theory/modules/A_INTEGRATED_MODEL.md:1367-1378`）；proposed 也逐侧定义接触建立/释放 guard（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1773-1797`） | `supported` | P3 / 高 | 抽象事件生命周期一致；文献支持状态顺序，不证明现行事件算法已实现。 |
| 29-02 | 上述循环由轮角和持续基座转动驱动（`evidence_card.md:23-29`） | proposed 的正式路径只有 A/B 直线拖曳、C 同步预紧和偏心加载（`MECHANISM_DERIVATION_FORMAL.md:153-164`）；B 1.0 中针轴不随共同平移转动（`theory/modules/B_INTEGRATED_MODEL.md:632-657`） | `insufficient_evidence` | P2 / 高 | 轮式周期运动学不在当前对象内，是范围差异而非冲突；不得把轮角直接当现行 `u_x`。 |
| 29-03 | 低法向刚度、略负切—法耦合和适中切向刚度改善搜索/承载，M2（`evidence_card.md:32-41`） | 当前 A 只显式拥有针梁和共线单边压簧；根部/夹具柔顺是关闭的未来模型（`A_INTEGRATED_MODEL.md:1334-1346,1818-1828`） | `supplement_candidate` | P2 / 中高 | 可作为未来根部 6D 柔顺的设计假设；S 形 PA2200 悬架不是现行安装结构，耦合符号须先转换到项目坐标并验证正定性。 |
| 29-04 | 两个 3×3 刺端刚度矩阵及 FEA 辨识，E1（`evidence_card.md:89-115`） | 现行主线以可追溯 EB 梁、独立压簧及可选接触柔顺串联（`A_INTEGRATED_MODEL.md:647-737,1211-1245`） | `insufficient_evidence` | **P1 / 高** | 矩阵来自另一几何/材料的 FEA，未做实体刚度验证且含混合单位；不能替换本项目本构或数值。 |
| 29-05 | 主动接触集 + 旋转刚度 + 位移兼容 + 合力/合矩闭合产生多刺分载，M3/E3–E5（`evidence_card.md:43-52,135-189`） | proposed 用共同背板位姿、逐针 trial、wrench 运输求和和共同法向平衡确定非均载，事件后重解（`MECHANISM_DERIVATION_FORMAL.md:1105-1276`）；复核确认此主链代数正确（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:278-312`） | `supported` | P3 / 高 | 现行三维形式是其结构性推广，并未采用经验均载；固定铰/等间距直墙只是论文特例。 |
| 29-06 | Eq. (18) 的 `(3m+2)` 线性系统及 `n=64` 二维等角折叠（`evidence_card.md:207-213,293-300`） | accepted B 保留真实矩形格点、逐针安装轴、共同背板和全阵列 A 调用（`B_INTEGRATED_MODEL.md:560-657,692-735`） | `insufficient_evidence` | **P1 / 高** | 只能作受限解析回归；不能覆盖横向错列、同峰竞争、三维力矩、滑移、损伤或任意事件后分配。 |
| 29-07 | 砖面拉脱 `F_x/F_y` 随机构转角显著增加，M4/V2（`evidence_card.md:54-63,240-247`） | 现行局部坡度、法向力和摩擦共同决定力分量，且标量拖曳不能唯一反演它们（`MECHANISM_DERIVATION_FORMAL.md:2047-2062`）；实验义务尚只概括为挂接/峰值/方向趋势（`MECHANISM_DERIVATION_FORMAL.md:2125-2132`） | `supplement_candidate` | **P1 / 中高** | 无真冲突；应补“按角度与加载历史分层的拉脱散点/包络”验证，而不是另加第二套摩擦律。论文的 `α` 还需与项目安装角做坐标定义对照。 |
| 29-08 | `F_{mx}<cF_{my}`、`c=tan(θ_min-atan(1/μ))` 及砖面 `c=0.44…0.98`，E6（`evidence_card.md:191-205,223-224`） | accepted A 只允许完整三维 SOC/拉离分支，明确禁止把二维标量式当一般判据（`A_INTEGRATED_MODEL.md:1247-1263`） | `insufficient_evidence` | **P0（移植阻断）/ 高** | 原文不等式与“越界拉脱”措辞不能唯一确定可行侧，拟合强制过零且缺重复数、误差、接近角、拖曳距离和预压（`extraction_audit.json:79-82,183-197`）；不得实现为通用失效面或材料常数。 |
| 29-09 | 尾端摩擦/法向支撑与力臂闭合整机平衡，尾长约 120 mm 后收益饱和，M5/E2/V3（`evidence_card.md:65-74,117-133,249-255`） | 当前对象是无质量刚性十字参考体和授权偏心加载器；工程事实明确排除整机质量（`theory/evidence_reassessment/engineering_fixed_context.md:283-298,1021-1037`），外部 wrench 也必须显式授权（`MECHANISM_DERIVATION_FORMAL.md:1640-1681`） | `insufficient_evidence` | P3 / 高 | 属整机边界条件差异，不是现行机理遗漏；未来若扩展移动机器人，可作为独立外部边界低阶校核，不能进入当前 A/B/C。 |
| 29-10 | 过轻导致接触不足、过重导致结构过载；柔顺存在双侧边界，M6（`evidence_card.md:76-85`） | B 已输出承载针数、`N_eff`、不均载、容量利用率和逐针强度状态（`B_INTEGRATED_MODEL.md:1570-1623`），且 accepted 迁移边界已保留过硬/过软竞争趋势（`B_INTEGRATED_MODEL.md:1726-1734`） | `supported` | P2 / 中高 | “低有效接触数—高局部利用率”双侧诊断方向已包含；但整机质量不是当前模型变量，不能把论文质量趋势解释为质量定律。 |
| 29-11 | 60 g、64 刺/轮、S 形/直梁最大倾角 100°/80°及速度等样机结果（`evidence_card.md:209-227`） | 当前目标是设计趋势/排序，不要求拟合单次绝对值（`engineering_fixed_context.md:67-82`），且 review 禁止把开发基线包装成真实红砖预测（`DERIVATION_VERIFICATION_2026-07-17.md:15-16`） | `insufficient_evidence` | **P1 / 高** | 可作外部趋势案例，不能校准本项目质量、刚度、强度、速度或能力阈值。 |
| 29-12 | 砖靠粗糙峰挂接、软质珍珠棉靠穿刺、光滑漆墙因刺尖过大而失败，V5（`evidence_card.md:265-270`） | accepted A 首版排除连续切削/穿刺后续物理（`A_INTEGRATED_MODEL.md:83-85`），统一表面接口只允许球尖承载并要求模型/参数有效（`B_INTEGRATED_MODEL.md:539-556`） | `supplement_candidate` | **P1 / 高** | 应补显式 `attachment_mode/applicability` 门：`hard_rough_interlock` 可评估，`soft_penetration` 返回 out-of-scope；光滑面则让几何/平衡自然判不可行。 |
| 29-13 | 论文整机趋势与仿真一致，但没有同步逐刺力、实际接触数或 Eq. (18) 分载验证（`evidence_card.md:295-302`；`extraction_audit.json:200-202`） | 独立复核说明现有归档不是求解器/参数/实验验证，并要求 B 曲线事件逐点重求共同平衡（`DERIVATION_VERIFICATION_2026-07-17.md:15-16,346-363`） | `insufficient_evidence` | **P1 / 高** | P29 支持建模方向，不足以关闭现行 B 实现、事件完备性或红砖参数验证义务。 |

## 3. 真冲突、表面冲突与遗漏

**真冲突：0 项。** 三个最容易误判的“冲突”都是范围差异：轮角驱动与直线拖曳路径不同；S 形根部悬架与现行共线压簧不同；带尾轮式整机与无质量十字对爪不同。P29 的固定铰、无滑移线性 Eq. (18) 也只是现行三维非光滑共同平衡的受限特例。唯一高风险点是 E6 可行侧未闭合，但现行模型并未采用它，因此是参数/公式移植阻断，不是已经发生的机理冲突。

被漏掉或值得显式化的内容有四项：

1. **A 结构层可选模型假设（P2）：** 将根部/夹具柔顺保留为独立 6D 对称正定本构，可允许经标定的切—法耦合；不得吸收到针梁 E 或轴向弹簧。需项目硬件变更、目标 CAD/FEA、实体多轴刚度试验和能量正定回归。
2. **A/B 验证义务与原始输出（P1）：** 按已明确定义的角度、接近路径、拖曳距离、预压和表面 realization 分层保存释放瞬间 3D wrench、局部法向/切基、支持 ID、状态与不确定度；比较散点/条件包络，不强制过零拟合。需重复数、留出表面和角度坐标映射。
3. **B 双侧设计诊断（P2）：** 联合报告低 `N_eff/N_load` 与高最大容量/强度利用率，作为“接触不足—局部过载”成对诊断；身份为只读输出/验证指标，不是成功阈值。需对刚/柔、预载和表面配对扫描并保留逐针原始量。
4. **系统适用域门（P1）：** 增加 `attachment_mode={hard_rough_interlock, soft_penetration, unsupported}` 元数据/认证状态；软材料穿刺不得由高度场+Coulomb+球尖模型冒充。需显微/力—位移证据确认模式后才能启用新模型。

## 4. 明确不可直接移植

- 两套 PA2200 S 形/直梁 3×3 刚度矩阵、材料模量/强度、S 形几何和负耦合数值；只能复现原论文或作数量级 sanity check（`evidence_card.md:209-220`）。
- Eq. (19) 的不等式方向、公式和四个 `c`；`c` 不是砖材料常数，也不能替代三维摩擦/几何/材料容量。
- Eq. (18)、固定 `ΔH`、固定铰无滑移、`n=64` 二维等角折叠及“两轮对称×2”；不得覆盖本项目矩形阵列和事件后全量重求。
- 尾部 E2、`μ_1`、`L/r/M`、100–200 mm 尾长及 85–105° 饱和值；当前系统没有相同整机边界。
- 60 g/0.6 N、32 mm 轮、64 刺/轮、1 mm 针长、30–60 μm 尖端半径、100°/80° 倾角和 10/20 cm/s 速度；均绑定论文样机、表面和协议。
- 珍珠棉 130° 穿刺能力不得迁移到硬砖挂接模型；砖面散点也不能拆分形貌、摩擦、材料强度和历史效应。

## 5. 优先级结论

**P0：** 阻止 E6/`c` 进入通用拉脱判据。
**P1：** 增加角度—历史条件拉脱验证、表面附着模式门，并保持 B 实现/红砖验证未关闭；阻止刚度矩阵、Eq. (18) 和整机性能值直接定参。
**P2：** 未来根部 6D 柔顺候选与“接触不足—局部过载”联合诊断。
**P3：** 预载—挂接—释放状态链和共同平衡分载主链已获得独立文献支持，无需改写。

最终结论：P29 不推翻现行完整机理；它最有价值的补充是角度/历史条件拉脱验证、软穿刺适用域门及双侧柔顺诊断。其轮式运动学、S 形悬架数值、二维 Eq. (18)、标量 `c` 和尾支撑整机模型均只能作为条件案例，不能静默进入 accepted 或 DEV 参数。

# 08 — Compliant Microspine Arrays 反向审查

**文献：** Asbeck 等，*Scaling Hard Vertical Surfaces with Compliant Microspine Arrays*。
**审查对象：** `MECHANISM_DERIVATION_FORMAL 0.1.0-proposed`，并以 A/B/System accepted 1.0 与独立 verification 为规范基线。
**总判定：** 未发现同一对象、同一假设和同一适用域下的真正冲突。M1、M2、M5 的机理骨架已经覆盖，M3 的准静态事件部分和 M6 的“独立柔顺促进更多挂接、载荷由共同平衡决定”也已覆盖。主要遗漏是方向扫掠后的候选密度诊断、伪挂接统计、测量带宽对排序的显式验证，以及有严格适用域的尺度趋势。动态跳跃、横向沟槽导向、SpinyBotII toe 拓扑和磨损演化属于范围差异，不能据此改写现行首版。

## 1. 证据身份、完整性与适用域

本地来源是 8 页 PDF，而正式 2006 期刊版为 15 页；卡片页码、公式和图号只能对应本地版本（`literature/08_compliant_microspine_arrays/evidence_card.md:3-11`；`literature/08_compliant_microspine_arrays/extraction_audit.json:13-20`）。八页均已检查，公式页及三张关键图以 400 dpi 复核，审计状态为 `PASS_WITH_WARNINGS`（`extraction_audit.json:21-27,203`）。E1–E4 可作为经核对的文献表达；E5 Hertz 链及其后续系数因等效模量量纲、未定义符号而不确定（`extraction_audit.json:69-88,165-173`）。论文覆盖二维准静态轮廓、接触试验、样机机构和系统演示；它不提供本项目三维红砖损伤参数、逐刺载荷统计或对爪内力验证（`evidence_card.md:226-237`）。

## 2. 决定性逐项判断

| ID | 文献卡结论与本地来源 | 现行机理对应位置 | 分类 | 理由、优先级与置信度 |
|---|---|---|---|---|
| 08-01 | M1：有限刺尖沿接近方向扫掠，原轮廓变为 traced/可达表面（`evidence_card.md:19-28`；Fig. 2 为 `figures/fig02_p02_spine_surface_trace.png`） | FORMAL 定义完整球包络、有限球冠和多支持认证（`paper/MECHANISM_DERIVATION_FORMAL.md:341-371,373-398,432-454`）；accepted A 同样以球包络和合法球冠查询为权威（`modules/A_INTEGRATED_MODEL.md:414-466`） | `supported` | 现行三维球冠/距离查询是二维 traced surface 的更一般化版本，没有把质点尖端误当真实针尖。**P1，高置信。** |
| 08-02 | M1 还输出每厘米可用凸体密度和最大可用刺尖半径（`evidence_card.md:22-24`） | FORMAL 当前实验输出集中于峰值、事件距离和有效联合量（`paper/MECHANISM_DERIVATION_FORMAL.md:2008-2022`），未冻结“方向扫掠候选密度/最大可达半径”诊断 | `supplement_candidate` | 可在 A1/验证层增加只读诊断：给定路径、半径、摩擦参数，报告单位搜索长度的合法候选数及其置信区间；它不能替代逐步接触求解，也不能直接作为成功率。**P2，高置信。** |
| 08-03 | M2/E2：稳定候选由加载方向、局部法向与摩擦联合筛选，二维式为 \(\theta_{min}=\theta_{load}+\operatorname{arccot}\mu\)（`evidence_card.md:30-38,94-105`） | FORMAL 使用三维 Signorini 与 SOC Coulomb 最大耗散（`paper/MECHANISM_DERIVATION_FORMAL.md:509-615`）；verification 已确认其可作实现骨架（`review/DERIVATION_VERIFICATION_2026-07-17.md:170-182`） | `supported` | E2 只是固定二维坐标和单支持下的降维检查，不应另加一条角度门槛与摩擦锥重复筛选。建议把 E2 用作解析回归案例。**P1，高置信。** |
| 08-04 | 标量 \(R_a/R_q\) 不能代表啮合潜力；局部法向分布和仪器带宽会改变表面排序（`evidence_card.md:171-183,228-230`） | accepted A 要求可信波数带和测量/生成元数据（`modules/A_INTEGRATED_MODEL.md:414-428`）；System 已要求几何加密平台检验（`system/SYSTEM_INTEGRATED_MODEL.md:2153-2159`） | `supported` | 机理方向一致；文献的 65 μm 光斑造成混凝土失序，补强了“仪器 MTF/可信最短波长必须随 realization 保存”的验证依据，而不是提供新粗糙度阈值。**P1，高置信。** |
| 08-05 | M3：伪挂接后增载滑脱、离面、再接触以及静/动摩擦切换（`evidence_card.md:40-48`） | FORMAL 已有开闭、stick/slide、支持切换和强度事件的一侧 guard（`paper/MECHANISM_DERIVATION_FORMAL.md:1773-1797`）；System 明定释放—继续搜索—再挂接验证（`system/SYSTEM_INTEGRATED_MODEL.md:2093-2095`） | `supported` | “伪凸体”无需成为新接触本构；可由短寿命 `CLOSED→SLIDE/OPEN→REENGAGED` 事件链表达。仍应增加伪挂接次数、持续距离和再捕获距离输出。**P2，高置信。** |
| 08-06 | M3 的 airborne skipping、动态摩擦切换及横向沟槽/凹坑导向（`evidence_card.md:43-46,230`） | FORMAL 明确排除释放后的高速回弹与冲击（`paper/MECHANISM_DERIVATION_FORMAL.md:107-139`），未实现回位时停在释放 pose（`paper/MECHANISM_DERIVATION_FORMAL.md:1904-1906`）；B 1.0 只允许共同 \((u_x,u_z)\)（`paper/MECHANISM_DERIVATION_FORMAL.md:1169-1187`） | `supplement_candidate` | 这是模型范围差异，不是真冲突。未来若高速视频证明这些现象影响排序，应另建过阻尼/动力回位与 local-y 路径扩展；当前 M0 必须继续标为 excluded。**P2，高置信。** |
| 08-07 | M4：近似分形且同比缩放时，候选数约 \(1/r^2\)、单点承载约 \(r^2\)，总面积承载近似不变仅是条件假设（`evidence_card.md:50-58,217-224`；Fig. 5） | 现行模型以实际 SurfaceRealization、球尖尺寸和完整共同平衡求响应；B 明确表面相关性不得生成 IID 成功率或转移权重（`modules/B_INTEGRATED_MODEL.md:660-690`） | `supplement_candidate` | 可作为多尺度参数研究的趋势/反例验证义务，必须同时检验分形尺度区、形貌可信带和同比缩放；不得把幂律写入接触或阵列承载公式。**P2，中置信。** |
| 08-08 | 文献新/钝刺尖约 10–15/25–35 μm，且尺寸变小提高捕获但降低单点承载（`evidence_card.md:161-163,185-189`） | 本项目固定扫描 \(R_t=50,100\) μm（`evidence_reassessment/engineering_fixed_context.md:350-356`），accepted A 首版排除针尖磨损演化（`modules/A_INTEGRATED_MODEL.md:83-85`） | `supplement_candidate` | 只能补充“实测尖端半径/磨钝等级作为静态 geometry ID 与敏感性组”的建议；文献范围与本项目扫描不重合，且无寿命分布，不能建立磨损演化律。**P2，高置信。** |
| 08-09 | M5：滑脱、针根塑性/断裂、凸体脆性剥落三种上限竞争（`evidence_card.md:60-67`） | FORMAL 分别给出 Coulomb 滑移、根截面应力和条件材料容量（`paper/MECHANISM_DERIVATION_FORMAL.md:546-615,773-840,889-1005`）；accepted A 明确三者不得混并（`modules/A_INTEGRATED_MODEL.md:1348-1359`） | `supported` | 模式结构完整，且优于单一极限力。可补“首个控制裕度/并发模式”派生输出；但材料分支尚未标定，不能据此声称定量闭合。**P1，高置信。** |
| 08-10 | E3/E4 给出特定曲刺的根部应力和 Castigliano 端转角尺度（`evidence_card.md:107-133`） | FORMAL 当前采用实际参数化直梁的 3D Euler–Bernoulli 柔顺并设越界返回（`paper/MECHANISM_DERIVATION_FORMAL.md:678-734`），根部参数不足时只输出名义监控（`paper/MECHANISM_DERIVATION_FORMAL.md:773-840`） | `insufficient_evidence` | 论文曲率、边界和受力坐标不同；E3 的 \(d^2\) 趋势可作尺寸回归，E4 不可直接替换现行梁。System 也要求成品针试验/局部 FE 才关闭强度（`system/SYSTEM_INTEGRATED_MODEL.md:2197`）。**P1，高置信。** |
| 08-11 | E5 Hertz 链存在等效模量量纲和符号问题（`evidence_card.md:135-147`；`extraction_audit.json:77-88`） | B 的去重规则明确不得另加 Hertz/罚力（`modules/B_INTEGRATED_MODEL.md:948-959`）；FORMAL 材料扩展要求独立容量与功共轭标定（`paper/MECHANISM_DERIVATION_FORMAL.md:889-1005`） | `insufficient_evidence` | 不存在“现行遗漏了原公式”的冲突；直接移植反而会引入量纲错误和双算。最多保留“接触尺度会改变基材失效”的定性先验。**P0，高置信。** |
| 08-12 | M6/V4：独立柔顺让已挂接成员不阻塞邻成员继续搜索，避免少数刺承担大部分载荷（`evidence_card.md:69-77,191-195`） | B 逐针调用 A、由共同法向平衡得到非等载并在事件后全阵列重解（`paper/MECHANISM_DERIVATION_FORMAL.md:1189-1276`）；accepted B 保存有效针数与不均载指标（`modules/B_INTEGRATED_MODEL.md:1570-1607`） | `supported` | 文献支持“柔顺改善参与率”，不支持强制均载。现行共同平衡恰当地允许非均载、部分接触与级联。**P1，高置信。** |
| 08-13 | SpinyBotII 是 10 个独立平面 toe、每 toe 两刺，并含方向刚度、阻尼和防上转几何（`evidence_card.md:69-77`） | 本项目是共同刚性背板下逐针单边轴向弹簧，无安装座转动，4 mm 硬限位（`evidence_reassessment/engineering_fixed_context.md:579-617`；`modules/B_INTEGRATED_MODEL.md:916-946`） | `insufficient_evidence` | 两者是不同机构拓扑。论文可作为柔顺设计动机，却不能验证本项目 \(k_s\)、4 mm 行程、逐针独立性或阻尼；审计也明确未给 toe 刚度/阻尼/逐刺力（`extraction_audit.json:181-183`）。**P1，高置信。** |
| 08-14 | E1 用指数分布描述二维候选间距/长度（`evidence_card.md:81-92`） | accepted B 保留二维相关/PSD/联合查询，明确不得由邻接或相关性产生 IID 成功率（`modules/B_INTEGRATED_MODEL.md:660-690`） | `insufficient_evidence` | 只有对本项目三维表面、给定方向和球尖半径重新检验后，指数族才可成为候选统计模型；不得默认独立，也不得据此线性放大阵列能力。**P3，高置信。** |

## 3. 真冲突与表面冲突

**真冲突：无。** 文献没有在本项目相同三维几何、相同针尺寸、相同阵列拓扑和相同加载边界下给出与现行方程相反的结果。

表面冲突有四类：其一，E2 的二维角度阈值与三维摩擦锥看似两套判据，实际前者只是后者在特定坐标下的降维；其二，论文说“促进均载”，是设计目标而非逐刺力相等，审计已明确未测得均载等式（`extraction_audit.json:181-183`），现行非等载共同平衡不冲突；其三，论文观察动态跳跃和横向导向，而首版主动排除动力学/local-y，属于适用域差异；其四，论文单刺 1–2 N 与本项目每阵列单元主动推力 0.5–2 N 是不同物理量，后者定义见 `engineering_fixed_context.md:761-770`，不可直接比较。

## 4. 漏项与建议补充

1. **P1 / 高置信：测量带宽证据化。** 在 A1 `SurfaceRealization` 质量记录中强制保存仪器探针/光斑、MTF/SNR、可信最短波长，并用候选密度和设计排序的多分辨率平台关闭验证；这是对现有可信带义务的证据补强。
2. **P2 / 高置信：方向扫掠诊断。** 新增 `accessible_candidate_count_per_length`、`max_accessible_tip_radius`、法向角分布和路径/半径/摩擦版本；身份为只读诊断/验证输出，不能成为第二套接触判据。
3. **P2 / 高置信：伪挂接事件指标。** 从现有事件链派生短寿命挂接次数、挂接持续距离、释放后再捕获距离和重复率，用高速视频验证；不新增“伪凸体材料”。
4. **P2 / 中置信：条件尺度验证。** 对多个真实/合成表面做尖端半径扫描，分别检验候选数、单刺峰值、\(N_{eff}\) 和阵列能力；只有观察到稳定尺度区时才报告局部幂指数。
5. **P2 / 高置信：静态磨钝组。** 将显微测得的新/磨钝尖端作为不同 geometry realization，比对捕获与失效模式；没有时间序列证据前不建磨损演化。
6. **P3 / 中置信：未来动力/横向扩展门槛。** 仅当高速观测证明跳跃或 local-y 导向改变方案排序，才版本化增加过阻尼/动力回位、横向自由度和相应碰撞/再接触验证。

## 5. 明确不可直接移植

- E5 Hertz 系数、未定义 \(\mu_2\) 与最终 \(f_{max}\) 系数；维度和符号审计未通过。
- \(\lambda\) 指数间距模型、\(1/r^2\)、\(r^2\) 及“单位面积总承载不变”作为通用律；它们仅是二维、近似分形/同比缩放条件下的候选趋势。
- \(\mu=0.15\!\sim\!0.25\)、\(\theta_{min}=81\!\sim\!86.5^\circ\)、接近角 45–65°、1–2 N 单刺能力及 20/300 μm 表面尺度阈值；材料、坐标、测量带宽和统计量均不同，且原文无完整不确定度（`evidence_card.md:153-167,226-233`）。
- 15 μm 尖端、1.5 mm 长/200 μm 杆径、10 toe×2 spine、Shore 硬度、机器人载荷/速度；这些是 SpinyBotII 样机配置，不是本项目工程事实或参数先验。
- 由“更多刺”直接推出线性阵列增益、等载或独立捕获概率；现行模型必须保留表面相关性、行程饱和、事件后重平衡与级联。
- SpinyBotII 整机在多种墙面的攀爬演示不能验证本项目十字对爪预紧、偏心载荷、rocking 或 \(F_{crit}\)；提取审计已明确该文不支持 paired-claw 兼容性（`extraction_audit.json:186-191`）。

## 6. 收束判定

该卡对现行完整机理最有价值的作用是**确认骨架并补验证义务**，不是提供可直接抄入的公式或数值。应保留 FORMAL 的三维有限球冠、Coulomb、梁/弹簧、材料容量和 B 共同平衡主链；拟补内容均应以 proposed 诊断、验证义务或未来可选模型进入。verification 已明确当前只能认证 no-damage 受限骨架，不能宣称材料、随机样本或实验承载已经验证（`review/DERIVATION_VERIFICATION_2026-07-17.md:449-465,469-485`）。

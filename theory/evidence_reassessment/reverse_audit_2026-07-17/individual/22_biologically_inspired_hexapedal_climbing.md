# 第 22 组反向审查：Biologically Inspired Climbing with a Hexapedal Robot

## 1. 身份、提取完整性与适用域

- 文献：Spenko 等，2008，六足 RiSE 在砖、灰泥、混凝土砌块和碎石等竖直粗糙硬表面上的微刺足、分层柔顺、足间力反馈与整机实验；证据卡将其判为 A 级相关，但明确不能替代单刺接触模型（`theory/evidence_reassessment/literature/22_biologically_inspired_hexapedal_climbing/evidence_card.md:3-10`）。
- 提取状态：`PASS_WITH_WARNINGS`；20/20 页均检查，关键页 9、12、14 以 260 dpi 复核，Eq. (5)–(6)、Table I 和三张保留图均经目视核验（`theory/evidence_reassessment/literature/22_biologically_inspired_hexapedal_climbing/extraction_audit.json:15-23,50-77,131-173,253-255`）。本审查也查看了三张保留图：趾/踝柔顺、四阶段足轨迹、牵引反馈时序均与卡片表述一致。
- 证据边界：它是“多刺足—六足机器人—经验控制”的足级/整机证据，不是红砖单刺力学、对置四单元六维平衡或材料参数证据；卡片及提取审计已明确足级阈值不得下推、平均牵引控制器不是对爪完整平衡、整机实验不能验证 6D wrench（`evidence_card.md:192-203`；`extraction_audit.json:244-250`）。
- 主审对象 `MECHANISM_DERIVATION_FORMAL.md` 是 `0.1.0-proposed`，不得覆盖 accepted A/B/C/System（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:3-9`）。以下结论据此同时核对 proposed 稿、accepted 基线和 verification。

## 2. M1–M6 逐项结论

| # | 卡片原结论与本地来源 | 现行机理对应位置 | 分类 | 理由、优先级与置信度 |
|---:|---|---|---|---|
| 1 | **M1：硬表面不穿透，轻压后沿面滑动捕获凸体，可同时形成牵引与拉入分量。** `evidence_card.md:19-28` | 球尖非穿透包络与支持认证：`MECHANISM_DERIVATION_FORMAL.md:316-371,432-454`；Signorini–Coulomb：`:509-615`；verification 确认骨架：`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:170-180` | `supported` | 有限球尖、粗糙局部法向、单边正压力和三维摩擦已具备表达方向性合力的必要物理量；“拉入”应按足端有符号法向分量理解，不是材料黏附。模型不会保证任意 realization 必然捕获。P1，高。 |
| 2 | **M1 的操作链是“轻压—滑动搜索—凸体捕获”，而不是一开始即假定 attached。** `evidence_card.md:21-28` | accepted A 已区分零载接触、预载、拖曳，并保留两种搜索策略（`theory/modules/A_INTEGRATED_MODEL.md:1296-1316,1369-1378`），但最终 engagement 判据仍未关闭（`:1871-1878`） | `supplement_candidate` | 可把该链补成 A-standalone/实验协议的显式外层阶段及连续接合裕度；文献只支持流程和现象，不能给本项目二元成功阈值。P1，高。 |
| 3 | **M2：有限刺尖尺度筛选可利用凸体尺度。** `evidence_card.md:30-39` | (R_t) 直接进入球形形态学包络、球冠合法性和全候选比较（`MECHANISM_DERIVATION_FORMAL.md:341-375,432-454`）；项目固定半径扫描为 50/100 μm（`theory/evidence_reassessment/engineering_fixed_context.md:350-363`） | `supported` | 机理已经包含“半径改变可达支持集合”，与文献趋势一致；现行稿缺的是目标表面上半径—支持密度/能力的验证，不是接触公式。P1，高。 |
| 4 | **M2 数值：25/15 μm 分别适合较大/较小凸体，单刺最多数 N，需多刺并联。** `evidence_card.md:32-39,121-124` | 当前固定扫描为 50/100 μm，B 载荷由共同平衡而非“单刺上限×刺数”得到（`MECHANISM_DERIVATION_FORMAL.md:1257-1276`） | `insufficient_evidence` | 审计确认论文没有形貌、摩擦、强度、样本数或概率，也没有单刺试验表（`extraction_audit.json:212-221`）。15/25 μm 与项目 50/100 μm 是不同硬件/表面的范围差异，不是真冲突；前者不得改写固定扫描或作阈值。P1，高。 |
| 5 | **M3：趾—踝—腿的分层、各向异性柔顺在贴合、分载、姿态稳定间存在“过硬/过软”权衡。** `evidence_card.md:41-50`；图片索引 `:169-173` | proposed 只显式拥有针梁与针级轴向弹簧（`MECHANISM_DERIVATION_FORMAL.md:678-770`）；工程固定背板/十字参考体刚性且排除框架、导轨、连接件柔性（`engineering_fixed_context.md:254-297,420-454,579-617`） | `supplement_candidate` | 当前模型含局部针梁/弹簧柔顺，但没有 RiSE 的趾—踝—腿层级。可补为“范围声明、未来可选边界模型和敏感性假设”，不得在无工程修订时把它暗加进 accepted 主线。P2，中高。 |
| 6 | **M3 的 Shore 20A/72DC 与“较硬/尽量柔”可给各层刚度。** `evidence_card.md:47-50,125` | 现行模型要求显式 (E,G,k_s) 和版本化模型；梁/弹簧分属不同部件（`MECHANISM_DERIVATION_FORMAL.md:678-770`） | `insufficient_evidence` | 原文未给几何等效刚度、行程、阻尼，提取审计亦作此警告（`extraction_audit.json:223-226`）；Shore 硬度不能直接转换成项目梁、弹簧、踝或框架刚度。P2，高。 |
| 7 | **M4：接近/压紧、拖曳接合、支撑承载、卸载释放、再接合构成可逆外层状态链。** `evidence_card.md:52-61`；轨迹图索引 `:175-177` | accepted A 有 `OPEN→TIP_ZERO_LOAD→PRELOAD_BUILD→ATTACHED→RELEASE→REATTACHED`（`A_INTEGRATED_MODEL.md:1369-1413`）；System 有释放、继续搜索、再挂接（`theory/system/SYSTEM_INTEGRATED_MODEL.md:1581-1600`） | `supported` | 事件语义和历史不重置已覆盖该通用链；RiSE 的曲柄角和足轨迹只是实例，不是项目唯一运动学。P1，高。 |
| 8 | **M4：反转曲柄、主动抬足并卸载柔顺后循环。** `evidence_card.md:55-60,175-177` | proposed 明确释放后回位必须另开带扫掠碰撞和再接触 guard 的路径，未实现则停在释放 pose（`MECHANISM_DERIVATION_FORMAL.md:1904-1906`）；verification 已标 P1-A7（`DERIVATION_VERIFICATION_2026-07-17.md:265-272`） | `supplement_candidate` | 文献强化“受控卸载/抬离应是外部驱动路径”这一修订方向，可补可选 `CONTROLLED_UNLOAD/LIFT` driver 与验证义务；它没有提供本项目的扫掠几何、速度或碰撞闭合，不能直接关闭 P1-A7。P1，高。 |
| 9 | **M4：初始接合滑移后，在稍不同位置 pawing 重试。** `evidence_card.md:55-61` | proposed 仅规定释放后沿当前历史继续搜索（`MECHANISM_DERIVATION_FORMAL.md:1031-1070`）；System 只定义“可恢复则继续/再挂接”（`SYSTEM_INTEGRATED_MODEL.md:1610-1624`） | `supplement_candidate` | 可增加版本化的“换位重试策略”输入/输出：offset/path ID、重试次数、剩余合法区域、每次结果；不得假设重试必成功或重置损伤。P2，中高。 |
| 10 | **M5：足间牵引反馈以平均力为目标；低载足增载、高载足卸载，过低与过高均有风险。** `evidence_card.md:63-72,87-115` | B 的针间载荷来自共同位姿和再求平衡，明确不是经验转移（`MECHANISM_DERIVATION_FORMAL.md:1239-1276`；`DERIVATION_VERIFICATION_2026-07-17.md:278-312`）；B 已输出 CV/Gini、最大/平均与容量利用率（`B_INTEGRATED_MODEL.md:1570-1591`） | `supplement_candidate` | 可补“欠接合—过利用”双侧裕度及上层监督控制/诊断接口；若执行器自由度允许，目标应容量加权并受整体力矩平衡约束。不得用平均力控制律替代 B 的物理平衡。P2，高。 |
| 11 | **E1/E2、85%–120% 死区、+70%/−41% 腿速可直接作本项目控制器。** `evidence_card.md:87-115,130-131` | 项目四单元只有共同搜索坐标 (s)，不能像六腿那样独立改相位/速度（`engineering_fixed_context.md:887-893`）；System 禁止 C 平均分配 (P_i) 或以固定权重转移载荷（`SYSTEM_INTEGRATED_MODEL.md:264-280`） | `insufficient_evidence` | Eq. (5) 可作诊断均值；Eq. (6) 的增益、单位、采样、饱和和稳定性均缺失（`extraction_audit.json:228-231`），且执行器拓扑不同。P2，高。 |
| 12 | **M6：冗余接触与失效后重分配使单点/单足事件不必等于整机失效。** `evidence_card.md:74-83` | B 事件后全阵列重求（`B_INTEGRATED_MODEL.md:832-882`）；System 明确首针失效只是里程碑、可恢复脱附继续（`SYSTEM_INTEGRATED_MODEL.md:1602-1624`） | `supported` | 六足“五足支撑”不能等同四单元对爪，但“局部事件后仍由剩余接触重新平衡”的冗余原则一致。P1，高。 |
| 13 | **M6：均载、法向搜索、pawing、相位调节组合显著提高失效前距离，适合做控制消融。** `evidence_card.md:74-83,154-167` | 当前验证主要覆盖内核、事件、收敛和趋势，且全部尚为 `SPEC_DEFINED/BLOCKED_UNAVAILABLE`（`SYSTEM_INTEGRATED_MODEL.md:2044-2059,2080-2095,2149-2166`） | `supplement_candidate` | 增加“搜索/重试/重平衡/监督反馈”组合消融及无不可恢复失效的 accepted 路径/循环数、载荷离散度指标；只验证组合方向，不复现 RiSE 距离。P2，中高。 |
| 14 | **960/293/78.7 cm、约 12 m 建筑攀爬和速度结果可作本项目定量验收。** `evidence_card.md:133-134,154-167` | 当前系统是准静态对爪，代码与实验均未验证（`SYSTEM_INTEGRATED_MODEL.md:154-168`） | `insufficient_evidence` | 控制组次数不等、无置信区间/原始运行数据，且机器人质量、表面、步态、自由度不同（`extraction_audit.json:234-250`）。只能作外部趋势证据。P3，高。 |

## 3. 真冲突与表面冲突

**真冲突：未发现。** 在相同对象、假设与适用域下，卡片没有否定有限球尖、单边接触、Coulomb 摩擦、共同平衡或事件后重求。它也不能关闭 verification 已有 P0：当前验证报告仍明确说明损伤、姿态、B 事件和 B→C 合同问题，且已有归档验证不是求解器/参数/实验验证（`DERIVATION_VERIFICATION_2026-07-17.md:9-16`）。

表面冲突有四项：

1. **“平均力反馈”对“禁止经验均载”**：前者是六腿控制器改变相位/速度，后者是 B 层物理平衡；层级不同。只有把 Eq. (5)–(6) 当作逐针本构或固定载荷转移时才会真正违约。
2. **分层柔顺对刚性背板/参考体**：是不同机构。文献可支撑未来备选边界，不能覆盖工程固定刚体事实。
3. **15/25 μm 对 50/100 μm**：是不同针尖与表面域且无通用拟合；不构成公式矛盾，但提示固定扫描必须做目标表面尺度覆盖验证。
4. **五足波步态对四单元同步搜索**：前者有独立腿相位，后者只有共同 (s)；只能迁移冗余与消融思想，不能迁移控制律。

## 4. 被漏掉或仅隐含的关键结论

- 接合不是单一接触事件，而是“轻压—沿面搜索—形成可承载方向组合”的外层过程；现行模型保留连续裕度，却尚未冻结实验 engagement 判据。
- 释放后的主动反转/抬离是一条需要扫掠碰撞与再接触 guard 的受控路径；该文能强化边界选择，不能替代路径方程。
- “稍不同位置”重试是显式策略自由度；现行机制只有继续搜索/再挂接语义，没有 offset、尝试计数和策略身份。
- 足级控制的安全目标是双侧的：过载会触发结构/限位脱开，欠载会导致未充分接合；现行 B 有离散度/利用率输出，但未形成通用的双侧监督裕度。
- 组合反馈的价值应通过消融而非单项峰值证明；当前验证矩阵尚未包含与该文相对应的外层控制组合消融。

## 5. 建议补充项

| 优先级 | 建议进入层级/章节 | 建议身份、条件与验证义务 |
|---|---|---|
| P1 | A standalone/validation：接合协议 | 增加 `PRESS/SEARCH/LOAD_BEARING` 外层阶段与连续 engagement margins；仅用于粗糙硬表面。用项目表面、50/100 μm 针尖和规定预载验证，不由本文设二元阈值。 |
| P1 | A driver 与 FORMAL §11.6 | 增加版本化受控卸载/抬离路径；必须有扫掠碰撞、再接触 guard、事件定位与历史不重置测试。RiSE 曲柄轨迹只作流程证据。 |
| P1 | A1/FORMAL §16 实验验证 | 增加“针尖半径—表面可信带/曲率/支持密度—趋势排序”义务，专门检验 50/100 μm 是否覆盖项目红砖、混凝土、砂纸；不得据本文擅改固定扫描。 |
| P2 | A/B 外层 driver | 增加 `OFFSET_RETRY` 可选策略及原始字段：路径 ID、位移 offset、尝试数、合法剩余区域、首次/再次挂接位置、损伤版本；必须做确定性重放与不重置测试。 |
| P2 | B/C 输出或未来监督控制 | 在已有 CV/Gini/利用率上增加欠接合与过利用两侧裕度。若未来有独立执行器，只能用容量加权、力—力矩约束的控制目标；当前共同 (s) 主线先作诊断。 |
| P2 | System validation | 增加搜索、重试、重平衡、监督反馈的组合消融；输出无不可恢复失效的 accepted 路径/循环数、承载接触数、载荷离散度和事件率，并报告样本数与置信区间。 |
| P2/P3 | 讨论/未来模型 | 记录趾—踝—腿各向异性柔顺的“过硬/过软”权衡为未来硬件边界候选；只有工程上下文版本化修订并有等效刚度/阻尼标定后才能启用。 |

## 6. 不可直接移植的参数或结论

不得直接移植：15/25 μm 刺尖、单刺“数 N”、每足 25–50 趾、Shore 20A/72DC、1 N 接触确认、2 N 承载足判据、85%–120% 死区、+70%/−41% 速度修正、未给出的 (k_p)、5/6 占空比与 1/6 相位、3.8 kg/1.5 kg、960/293/78.7 cm、12 m 建筑演示和 0.25 m/s 目标（参数汇总见 `evidence_card.md:117-134`，局限见 `:192-203`）。这些量分别绑定 RiSE 的针尖、柔顺足、传感器、六腿执行器、表面与试验统计；最多作为数量级或趋势对照。Eq. (5) 的算术平均可作为输出诊断，Eq. (6) 不能成为本项目 B 载荷共享方程。

## 7. 总判定

- **冲突：** 0 项真冲突；4 项为层级、机构或参数域差异。
- **支持：** M1 接触方向性、M2 有限尖端形态学、M4 通用接合/释放/再挂接状态、M6 局部失效后的冗余重平衡均与现行机理一致。
- **最有价值的补充：** P1 的接合协议/验证判据、受控卸载路径、针尖尺度覆盖验证；P2 的换位重试、双侧安全裕度和组合消融。
- **置信度：** 对“无真冲突”和结构性遗漏为高；对分层柔顺及主动反馈能否迁入当前硬件为中；对任何数值参数迁移为低，故统一判作不可直接采用。

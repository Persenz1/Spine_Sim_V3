# 第 13 组反向审查：水泥浆体微划痕—损伤—声发射

## 1. 身份、完整性与适用域

- 文献：Němeček et al., *Fracture toughness of cement paste constituents assessed by micro-scratching correlated with acoustic emission*（2024，DOI 10.1016/j.cemconres.2024.107623）。对象是水泥浆体各水化相在 1–100 μm 尺度下的 R10 球头微划痕、压密、裂纹和撕落，不是烧结红砖有限球尖爪刺的单边摩擦啮合；证据卡因此只给 B 级相关性（`theory/evidence_reassessment/literature/13_cement_paste_micro_scratching/evidence_card.md:3-12`）。
- 提取状态为 `PASS_WITH_WARNINGS`：22/22 页、全部相关章节、Eq. (1)–(15)、四张表和全部图均检查；不确定项集中在 Kc→Gf 排版、解析/数值裂纹路径差异、相互作用尺度、拟合压密态强度和 AE 漏检（`theory/evidence_reassessment/literature/13_cement_paste_micro_scratching/extraction_audit.json:2-38,194-231`）。三张保留图分别确认球头几何、25–500 mN 下由沟槽拉裂向撕落演化、以及“首裂—前缘压损—完全损伤/侧裂”的 FE 时序（`evidence_card.md:216-228`；`figures/fig05_p05_scratch_geometry.png`、`figures/fig14_p13_damage_mode_transition.png`、`figures/fig19_20_p17_damage_evolution.png`）。
- 项目首版对象仍是红砖、混凝土和砂纸（`theory/evidence_reassessment/engineering_fixed_context.md:627-637`），且固定范围不显式追踪裂纹、碎屑、断口重建或地形重网格化（同文件 `:997-1017`）。表面材料容量与损伤的唯一所有者是 A；B/C/System 只能协调、传递和原子提交，不能另造材料律（`theory/system/SYSTEM_INTEGRATED_MODEL.md:264-284`）。因此本卡主要审查 A/FORMAL 的材料扩展和实验验证，不应反推 B/C 阵列规律。

## 2. M1–M6 逐项审查

| ID | 原始结论与本地证据 | 现行机理对应位置 | 分类 | 判断、优先级与置信度 |
|---|---|---|---|---|
| 13-01（M1） | 微划痕 Kc 反演依赖实测压头形状；必须用已知韧度标准样标定形状函数，不能只采用理想球头（`evidence_card.md:20-29,93-119,185-190`）。 | FORMAL 明确使用有限球尖和合法球冠支持（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:316-398`）；accepted A 要求 CAD/显微测量关闭球冠与针体几何，但没有微划痕标准样标定协议（`theory/modules/A_INTEGRATED_MODEL.md:1798-1801`）。 | `supplement_candidate` | 建议进入 A 材料试验/参数标定层，身份为“可选 Kc 测量协议 + 验证义务”：记录实际探针、标准样、作用深度和适用域。它不替代当前接触几何查询，也不证明爪刺球尖必须使用该反演式。P1，高置信度。 |
| 13-02（M1） | Eq. (5) 假设均质材料和水平裂纹，而 FE/SEM 显示首裂可向下倾斜；标准样校准只吸收部分偏差（`evidence_card.md:93-103,239-246`；`extraction_audit.json:200-203`）。 | FORMAL 的 M1 使用经标定的混合模态 Gc 和功共轭分离，不含 Kc 微划痕反演（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:959-1027`）。 | `insufficient_evidence` | 不能把 Eq. (5) 作为现行爪刺接触律、裂纹方向或红砖 Gc 来源；这是测量模型与爪刺本构的对象差异，不是真冲突。P0（若误植则阻断材料认证），高置信度。 |
| 13-03（M2） | 5–100 mN 可经 SEM 选择主导相；约 200 mN 后划痕跨越多相并撕落，只能解释为复合体响应（`evidence_card.md:31-38,171-175,192-202`）。 | accepted A 保存材料标签、可信尺度及不确定性，并定义面片面积/控制深度，但未显式声明“相分辨/有效复合体”层级（`theory/modules/A_INTEGRATED_MODEL.md:414-428,812-875`）。 | `supplement_candidate` | 在 `MaterialParameterSet`/局部试验记录增加 `representation_level`、探针影响体积、组织尺度比、相选择方法和混相质量；同一数值不得跨层级复用。P1，高置信度。论文支持尺度声明义务，不支持项目相尺寸或阈值。 |
| 13-04（M3/E1） | `COF=FT/FV` 是工况相关表观量；随压密先升、撕落后降，不等同常数摩擦系数（`evidence_card.md:40-49,81-91,198-202`）。 | accepted A 的 μ 只属于 Coulomb 锥（`theory/modules/A_INTEGRATED_MODEL.md:543-645`）；FORMAL 明确说明标量拖曳不能唯一反演 μ、局部坡度和法向力（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:2031-2062`）。 | `supported` | 现行机理没有把力比静默当材料常数，方向一致。宜把 `COF_app` 作为派生输出而非参数，并绑定法向力、状态和滤波方法。P1，高置信度。 |
| 13-05（M3） | 压密/堆积阻力、拉裂与高载侧裂撕落竞争，使 COF、拟合强度和有效韧度非单调（`evidence_card.md:40-59,204-208`）。 | accepted A 已有压力敏感 Mohr–Coulomb、拉伸截断和“有目标材料标定才启用”的可选压帽（`theory/modules/A_INTEGRATED_MODEL.md:875-916`）；FORMAL 只保留抽象无损容量集与单一软化坐标（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:889-951`）。 | `supplement_candidate` | 文献支持保留压密/压碎分支和模式竞争，但不足以选定椭圆压帽或状态方程。建议在 M1 增加可选压密内部变量/模式标签及转移验证，未标定继续 `MATERIAL_MODEL_UNAVAILABLE`。P1，中等置信度（跨材料）。 |
| 13-06（M3 数值） | 模式转折约 200 mN、COF 约 0.09→0.45 后下降、拟合压密态强度 39–289 MPa，均受本文材料、R10 和尺度控制（`evidence_card.md:46-48,171-181,230-237`）。 | A/System 将摩擦、局部强度、断裂能和损伤核保持未标定或 `unavailable`（`theory/modules/A_INTEGRATED_MODEL.md:1805-1817`；`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198-2202`）。 | `insufficient_evidence` | 这些量不能成为红砖阈值、先验中心、压帽参数或切换载荷；现行未硬编码策略正确。P0，高置信度。 |
| 13-07（M4） | 数值/SEM 归纳出“向下拉裂→压头前缘压损→接触区完全损伤；高载新增侧向/斜裂纹”的顺序（`evidence_card.md:51-59,204-208,226-228`）。 | accepted A 在材料起始时冻结单一模式并输出 mode/damage，但固定范围不追踪真实裂纹和碎屑（`theory/modules/A_INTEGRATED_MODEL.md:969-991,1688-1693`；`engineering_fixed_context.md:1010-1017`）。 | `supplement_candidate` | 可补 `damage_mode_sequence`、`compaction/tension/lateral_spall_candidate` 事件标签和显微验证目标；不得把标签解释为已解析裂纹路径或修改原始地形。P2，中高置信度。 |
| 13-08（M4/E4–E5） | 论文用拉/压等效应变、线性软化和裂带长度重现早期损伤，并要求网格客观性（`evidence_card.md:121-150,204-208`）。 | accepted A/FORMAL 同样采用断裂能正则化的线性软化方向并要求核/网格/步长客观性（`theory/modules/A_INTEGRATED_MODEL.md:969-991,1739-1750`；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:959-1018`）。 | `supported` | 只支持“能量正则 + 客观性 + 模式验证”的建模方向，不支持直接采用 Eq. (9)–(13)。独立复核仍指出 accepted 损伤缺少功共轭运动学，FORMAL 的关闭条件必须保留（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:255-263`）。P0，高置信度。 |
| 13-09（M4 边界） | 论文 FE 使用均质相、刚性全接触和位移驱动，只到首裂/早期扩展，不含真实摩擦分离、碎屑脱落和再接触（`evidence_card.md:57-59,239-245`）。 | FORMAL 使用 Signorini 单边接触、三维 Coulomb、有限球冠和事件/再挂接；当前 M0 又明确 `no_damage`（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:78-103,509-645,2083-2098`）。 | `supported` | 这是范围差异而非冲突；现行接触边界更接近爪刺问题。本文 FE 只能作局部材料验证候选，不能验证整个 A 接触—滑移—脱附链。P1，高置信度。 |
| 13-10（M5） | 水化致密化、亚微米孔减少与水化相 Kc 上升相关，但熟料颗粒基本不变（`evidence_card.md:61-68,163-181`）。 | 现行模型允许版本化材料参数，却未显式保存孔隙/成熟度条件；目标材料参数仍待局部试验（`theory/modules/A_INTEGRATED_MODEL.md:1813-1826`）。 | `supplement_candidate` | 增加 `material_state_metadata`（批次、孔隙表征、老化/含水环境）和分层标定/留出义务；只作参数条件变量，不能建立水泥水化→烧结红砖韧度的定量映射。P3，中等置信度。 |
| 13-11（M6） | OP/IP/熟料有 SEM 可见裂纹却无 AE hit；只有晶态 CH 的突跳与 AE 峰同步，故“AE 未检出”不是“无裂纹”（`evidence_card.md:70-77,210-214`；`extraction_audit.json:216-218`）。 | FORMAL 实验验证只列力学/轨迹项目，System 原始输出外壳也没有 AE 阈值或多证据裁决语义（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:2125-2132`；`theory/system/SYSTEM_INTEGRATED_MODEL.md:1823-1893`）。 | `supplement_candidate` | 将“AE 阴性不得关闭损伤事件”列为 P1 验证义务；至少联合原始力—位移、显微形貌和 AE，并保存阈值、传播路径、传感器/试样几何与通道质量。高置信度。 |
| 13-12（速度） | 本文相级 Kc 在 1–25 μm/s 内无显著速度趋势（`evidence_card.md:169-170,192-196`）。 | FORMAL 仅在“没有速率本构”时令平衡不显式依赖 1 mm/s 输出映射（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:153-173`）。 | `insufficient_evidence` | 水泥微划痕的小速度窗不能验证红砖爪刺的速率无关性，也不能校准 1 mm/s；最多是设计速率敏感性试验时的对照。P2，高置信度。 |
| 13-13（E6） | 文中 Kc→Gf 的未编号式存在括号/运算次序歧义，审计无法由取整数值消歧（`evidence_card.md:152-161`；`extraction_audit.json:119-123,194-199`）。 | FORMAL 的 M1 需要经标定的混合模态 Gc，但不规定由该式换算（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:959-967`）；System 将断裂能列为未标定（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2200-2202`）。 | `insufficient_evidence` | 未取得作者说明/原始计算前禁止实现该换算；更不能以水泥 Kc 自动生成红砖 Gc。P0，高置信度。 |

## 3. 真冲突与表面冲突

**真冲突：未发现。** 同一对象、假设和适用域下，本卡没有结论与 FORMAL 或 accepted A/B/C/System 不兼容。相反，COF 与 μ 的分离、材料参数未标定即 unavailable、能量正则和多模式竞争方向均与现行机理相容。

表面冲突有四类：水泥水化相与烧结红砖的材料差异；R10 球头划痕反演与有限球尖爪刺单边啮合的试验边界差异；论文均质全接触 FE 与现行 Signorini/Coulomb/释放—再挂接链的模型范围差异；论文显式裂带/撕落解释与项目固定“轻量损伤记忆、不重建碎屑地形”的范围差异。accepted A 的可选压帽与论文压密现象不冲突，但论文不足以认证该压帽公式。独立复核已把材料主线限制为 `no_damage`/未认证 fixture（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:255-263`），本卡不能关闭这一 P0。

## 4. 被漏掉的关键结论与建议补充

1. **A 材料试验接口，P1：** 增加作用尺度/代表层级字段和“实际探针—标准样—目标材料”校准收据；身份为测量协议与验证义务，不是接触方程。
2. **A M1 可选模型，P1：** 增加压密内部变量或至少模式标签，允许 `COMPACTION/CRUSHING`、`TENSILE_CRACK_CANDIDATE`、`LATERAL_SPALL_CANDIDATE` 竞争；启用条件是红砖局部压/剪/混合和峰后证据，未标定即 unavailable。
3. **A/System 派生输出，P1：** 增加 `COF_app=FT/FV`、对应原始分量、法向力、路径位置和材料状态，显式声明 `COF_app != μ`，不得反写 Coulomb 参数。
4. **实验验证合同，P1：** 增加 `damage_evidence_channels`：AE 配置/阈值/原始波形、显微前后图、力—位移事件及一致/不一致裁决；AE 阴性只能是“未检出”，不能是“无损伤”。
5. **材料元数据，P3：** 保存批次、孔隙/组织尺度、老化/含水条件，按条件分层标定并留出验证；禁止建立未经红砖数据验证的水泥水化映射。
6. **局部连续体验证适配器，P2：** 若未来用裂带 FE 检查 M1，只作为离线验证模型；必须重建接触边界、材料参数、裂带长度和网格收敛，并满足 FORMAL 的功共轭关闭条件。

优先级含义还需明确：P0 项不是要求立即启用材料损伤，而是禁止把本卡的公式、阈值或水泥参数作为求解器默认值；在目标材料证据不足时，安全结果仍是 `no_damage`、`unavailable` 或未认证 fixture。P1 项应优先进入下一版材料试验清单与输出 schema，因为它们直接影响参数身份、证据可追溯性及误把 AE 阴性判成无损伤的风险。P2 项属于模式解释和离线验证增强，不阻断 M0 几何—摩擦主线；P3 只用于未来材料状态分层，不能提前形成经验修正系数。

建议的最小验收证据包包括：同一真实探针的几何记录与标准样重复标定；至少两个作用尺度下的目标红砖局部划擦/压剪试验，用显微图确认参数代表层级；原始法向/切向力同步记录并同时给出 COF 与拟合 μ 的不同来源；AE 原始波形、阈值和显微前后图的盲法联合判读；若启用压密或软化分支，再补峰后位移、能量、核/网格/步长收敛和留出样本。缺任一关键通道时只能降低证据等级，不能用模型拟合良好替代独立观测。

上述补充均应以独立版本和适用域声明进入 proposed 层；在正式评审接受前，不修改 accepted A/B/C/System，不改变现有合同，也不提升任何承载结论的认证等级。

## 5. 明确不可直接移植

- R10 的 `α=298.1, δ=0, γ=0` 标定、5–500 mN 载荷、约 200 mN 转折、2.4–12.4 μm 沟槽宽和 1–25 μm/s 速度窗；
- OP/IP/CH/熟料及复合浆体全部 Kc、COF 数值、39–289 MPa 拟合压密态强度、0.62–11.6 μm FE 裂深；
- `k=8`、`ν=0.2`、Eq. (9)–(13) 的本构与参数、存在歧义的 Kc→Gf 式、FE 网格/刚性全接触边界；
- 水化龄期、孔隙率变化及 30%/58% 韧度增幅到红砖的映射；6 μV AE 阈值和峰值范围；
- 由本卡推导任何红砖阵列载荷共享、爪刺脱附、B/C 整体承载或认证参数。

## 6. 总结

本卡与现行完整机理**无真冲突**。最有价值的增量不是把水泥 FE 或数值塞入爪刺模型，而是补强 A 材料层和实验层的可审计边界：先声明探针—组织作用尺度，再区分表观 COF 与 Coulomb μ，以压密/拉裂/侧裂撕落作为可选模式竞争与验证标签，并规定 AE 阴性不得单独否定损伤。所有定量材料分支仍须用目标红砖、真实针尖/探针和正确接触边界重新标定，FORMAL M1 的 P0 关闭条件不因本卡而降低。

本报告全部结论均保持非规范、可撤销，并等待目标材料证据复核。

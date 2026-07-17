# 03 — Compliant directional suspensions for climbing with spines and adhesives 反向审查

**状态：** non-normative reverse-audit working material
**审查对象：** `MECHANISM_DERIVATION_FORMAL 0.1.0-proposed`，并以 accepted A/B/C、SYSTEM 和独立复核为边界
**总体判定：** 未发现同对象、同假设、同适用域下的真正文献—机理冲突；发现 4 项可补充内容、2 项必须阻止直接移植的范围错配。

## 1. 文献身份、提取完整性与适用域

该来源是 Alan T. Asbeck 2010 年 Stanford 博士论文，无 DOI，兼有理论、数值、实验和机构设计，证据卡将其研究对象概括为有限半径微刺搜索、方向承载、悬架均载、再挂接和补丁力矩平衡（`theory/evidence_reassessment/literature/03_compliant_directional_suspensions/evidence_card.md:3-10`）。提取审计覆盖 PDF 全 166 页及相关第 2–6 章和附录（`extraction_audit.json:5-189`），关键方程、表格和图片均逐项审计（`extraction_audit.json:191-324`），最终状态为 `PASS_WITH_WARNINGS`（`extraction_audit.json:360-368`）。因此，对定性机理的提取完整性评为高；对数值、原式和跨硬件移植的可靠性仅为中或低。

本次还目视核对了 Fig. 2.2、4.5、4.27。Fig. 4.5 清楚显示伸长弹簧与基座扭转弹簧构成的 stalk，而不是本项目的共线独立压缩弹簧；Fig. 4.27 只直接证明拖曳阶段总法向/剪切力呈多次跌落—恢复且总附着未归零，不能单凭总力曲线识别每根刺的接触状态。图片身份和保留理由见 `evidence_card.md:265-277`。

适用域边界很强：原形貌模型是二维、单方向、准静态剖面；三维侧滑、反入角和动态弹跳被排除（`evidence_card.md:19-28,288-292`）；多数定量证据来自砂纸、tarpaper、石材或混凝土而非烧结红砖（`evidence_card.md:212-226,290-298`）。本项目则固定为三维准静态求解器（`theory/evidence_reassessment/engineering_fixed_context.md:53-63`），针尖半径扫描为 50/100 μm（`engineering_fixed_context.md:350-363`），且安装机构固定为刚性背板与共线、独立、线性、无预压、不可拉伸/转动的压缩弹簧（`engineering_fixed_context.md:253-281,592-617`）。

## 2. 逐项反向结论

| ID | 文献结论与来源 | 现行机理对应 | 分类 | 优先级 / 置信度 | 判定理由 |
|---|---|---|---|---|---|
| 03-01 | 有限刺尖扫掠生成 traced surface 和可用台阶，M1（`evidence_card.md:19-28`） | proposed 完整球包络、有限球冠和支持认证（`MECHANISM_DERIVATION_FORMAL.md:316-454`）；accepted A 同样保留三维球冠及多支持（`A_INTEGRATED_MODEL.md:414-475`） | `supported` | P3 / 高 | 当前三维有符号距离/球冠模型是二维扫掠思想的严格扩展；二维接近角阈值不是额外必需接触律。 |
| 03-02 | 可用凸体间距服从 Gamma 分布 E2（`evidence_card.md:100-111`） | proposed 已把事件间距分布列为可观测/标定对象，而未预设族（`MECHANISM_DERIVATION_FORMAL.md:2014-2022,2064-2081`） | `insufficient_evidence` | P2 / 高 | Gamma 族只对论文的二维表面、尖端和角度成立；目标三维红砖必须重拟合并检验相关性，不能当搜索距离默认先验。 |
| 03-03 | 单接触安全域由方向/摩擦边界和强度幅值共同截断，M2/E3（`evidence_card.md:30-39,113-124`） | 三维 Coulomb 锥（`MECHANISM_DERIVATION_FORMAL.md:546-615`）、材料容量（`MECHANISM_DERIVATION_FORMAL.md:889-1027`）及针体强度分别建模；accepted A 同样分离摩擦、材料与针体（`A_INTEGRATED_MODEL.md:575-645,812-912,993-1046`） | `supported` | P3 / 高 | 结构性结论完全一致，且当前模型避免用单一经验 (F^*) 合并不同失效机制。论文二维标量式本身不应覆盖三维锥。 |
| 03-04 | 表面加固提高失效幅值但角度边界近似不变，V2（`evidence_card.md:237-242`） | 当前验证清单有二维载荷比/摩擦锥和材料测试，但未把“只改容量、角度边界近似不变”列为交叉消融（`A_INTEGRATED_MODEL.md:1739-1750`） | `supplement_candidate` | P1 / 中高 | 可补为机制解耦验证义务；只能验证建模方向，不能假定涂层绝不改变摩擦或接触几何。 |
| 03-05 | 未挂接—承载—再挂接—脱附的状态化悬架，M3（`evidence_card.md:41-50`） | A 已有 OPEN、attached、release、reattached 状态及正交事件（`A_INTEGRATED_MODEL.md:1367-1449`）；B 有可恢复脱附与再挂接状态（`B_INTEGRATED_MODEL.md:1003-1085,1121-1137`） | `supported` | P3 / 高 | 生命周期结论已完整包含；这不等于论文的特定状态刚度矩阵也已采用。 |
| 03-06 | (k_{xy}<0)、理想径向刚度比和 stalk E5/E6（`evidence_card.md:126-177`） | 项目只允许共线独立线性压簧、无安装座内转动（`engineering_fixed_context.md:592-617`），SYSTEM 禁止高层再加等效刚度（`SYSTEM_INTEGRATED_MODEL.md:264-278`） | `insufficient_evidence` | **P0 / 高** | 这是不同机构，不是真冲突；但证据卡把 E5/E6 标成“可直接进入/采用”（`evidence_card.md:158-176,279-284`）对本项目过强。除非先版本化修改工程事实，stalk、扭簧和交叉刚度不得进入现行本构。 |
| 03-07 | 回壁时间受质量、刚度、速度和凸体间距约束，E4（`evidence_card.md:126-146`） | proposed 明确排除高速回弹（`MECHANISM_DERIVATION_FORMAL.md:107-139`），并要求另建带扫掠碰撞/再接触 guard 的回位路径（`MECHANISM_DERIVATION_FORMAL.md:1904-1906`）；复核已列 P1-A7（`DERIVATION_VERIFICATION_2026-07-17.md:265-274`） | `supplement_candidate` | **P1 / 高** | 文献强化了现有 P1，而不能关闭它。半固有周期式来自另一悬架，不能直接成为本项目时间律；需目标硬件质量/阻尼/预载和回位实验。 |
| 03-08 | 近径向加载线和事件后重新均载可抑制级联，M4（`evidence_card.md:52-61`） | B 由共同平衡自然产生非均载，事件后切换分支并全量重求，不用经验转移矩阵（`MECHANISM_DERIVATION_FORMAL.md:1239-1276`；`B_INTEGRATED_MODEL.md:856-882`） | `supported` | P3 / 高 | “重分配必须重求平衡”的核心一致；文献的特定加载线形状只是受限设计实例。 |
| 03-09 | (L=max/mathrm{mean}) 与方向角折减 Δθ，E7（`evidence_card.md:179-189`） | B 已允许保存最大/平均等不均载量，但未固定方向角损失字段（`B_INTEGRATED_MODEL.md:1570-1591`） | `supplement_candidate` | P2 / 高 | 可作为只读输出补充：对当前承载集合分别报告三维力幅 (L_F)、方向离散和相对局部摩擦锥/容量裕度；不得复用论文单一 θmax。 |
| 03-10 | “先硬后软”非线性伸向律降低最大/平均，V4（`evidence_card.md:251-256`） | 当前工程事实固定线性压簧，B 只扫描该合法范围（`engineering_fixed_context.md:592-621`） | `supplement_candidate` | P2 / 中 | 可进入“未来机构/本构设计假设或回归案例”，不进入当前主模型。必须先有工程变更、独立模型 ID、能量一致性和目标硬件实验。 |
| 03-11 | 交替脱落/再挂接可使长距离拖曳总附着不归零，M5/V5（`evidence_card.md:63-72,258-263`） | SYSTEM 已定义释放—继续搜索—再挂接验证、历史不重置（`SYSTEM_INTEGRATED_MODEL.md:2080-2095`），B 也保存再挂接次数/间隔/恢复能力（`B_INTEGRATED_MODEL.md:1611-1623`） | `supported` | P2 / 中高 | 现象与输出目标一致；但该动态试验不能证明 accepted A 的瞬时回零实现正确，必须服从 03-07 的回位闭合。 |
| 03-12 | 偏载力矩、边缘超限与剥离正反馈，M6（`evidence_card.md:74-83`） | C 以完整 contact-only wrench 做六维平衡、稳定性、重平衡及峰后渐进脱附（`C_INTEGRATED_MODEL.md:1194-1333,1614-1689,2273-2295`） | `supported` | P3 / 中高 | 只支持“力矩—不均载—渐进失效”的建模方向；当前正式非零偏心运行仍被 B 1.0 合同阻断（`SYSTEM_INTEGRATED_MODEL.md:152-203`）。 |
| 03-13 | 连续干式黏附补丁 E8（`evidence_card.md:191-206`） | 当前对象为离散多刺和四单元 wrench 装配；SYSTEM 明确由 A/B/C 各层唯一所有（`SYSTEM_INTEGRATED_MODEL.md:1751-1772`） | `insufficient_evidence` | P1 / 高 | 连续线性单元层、球铰扭簧、平面小角度假设与离散粗糙面十字对爪不同；不得把 E8 当 C 方程或参数。 |
| 03-14 | 论文给出的摩擦、力、刚度、阻尼、行程、预载和试验最低载荷（`evidence_card.md:210-226`） | 当前系统将表面摩擦、强度、柔顺等保持 unresolved/需目标标定（`SYSTEM_INTEGRATED_MODEL.md:2184-2207`） | `insufficient_evidence` | P1 / 高 | 样机、表面、针尖半径和机构均不同；这些值只能用于数量级 sanity check 或复现实验，不能成为 DEV/accepted 参数。 |

## 3. 真冲突与表面冲突

**真冲突：0 项。** 现有审查未找到同对象、同运动学、同材料和同准静态/动态适用域下不兼容的结论。

以下均为表面冲突或范围差异：

1. 二维 θmax/扫掠台阶与三维球冠/Coulomb 锥是降阶模型与推广模型的关系，不是冲突。
2. stalk 的 (k_{xy})、扭转弹簧和非线性伸向律与本项目共线线性压簧属于不同硬件。必须拒绝直接移植，但不能据此说现行机理违背论文。
3. 论文的动态回壁/再挂接与 proposed 的准静态回位阻断处于不同时间尺度。它暴露的是已知 P1-A7，而不是足以替换回位方程的反例。
4. 连续干式黏附补丁与离散微刺十字对爪对象不同；当前 C 的六维力矩平衡保留共同物理方向，但不采用补丁闭式公式。
5. accepted A 曾把 `REVERSIBLE_RETURN` 写成投影回零（`A_INTEGRATED_MODEL.md:1376-1412`），proposed/复核已要求停止或显式扫掠回位；文献支持“回位是有条件的过程”，但没有提供目标硬件闭合，故列补充候选而非真冲突。

## 4. 被漏掉的关键结论与可补充项

| 补充项 | 建议层级/身份 | 适用条件 | 验证义务 |
|---|---|---|---|
| 材料加固只改变幅值、不应自动改摩擦角边界 | A 验证章节；`validation obligation` | 几何、μ、接触律保持相同的受控消融 | 分别保存锥裕度、材料/针体裕度和峰值；若涂层改变 μ/几何则判测试条件失效。 |
| 释放后的有限回位与再接触路径 | A；版本化可选 `quasi-static/overdamped return model`，未实现则 unavailable | 有质量/阻尼/预载、扫掠碰撞和再接触 guard | 事件收敛、无穿透、能量账本、目标机构高速测量；不得用论文半周期式直接定参。 |
| (L_F)、三维载荷方向离散/裕度损失 | B 原始只读输出字段 | 仅统计明确的当前承载集合，并声明力通道 | 对称案例 (L_F=1)、单针/零载边界、坐标旋转不变性和与逐针原始力重算一致。 |
| 径向加载线曲率与先硬后软趋势 | B 参数研究中的 `design hypothesis / regression-only` | 当前线性硬件只做对照；新本构需工程修订 | 同表面/同预载配对扫描，报告 L、首失效对象、级联和持续能力；不得自动推广为定律。 |

Gamma 间距族可在取得目标三维表面和事件数据后作为候选统计模型比较，但当前不是“机理遗漏”，因为 proposed 已保留非参数事件间距分布；只有留出检验优于替代分布后才可成为版本化先验。

## 5. 明确不可直接移植的参数或结论

- 摩擦系数 0.15–0.25、加载角 3.5–8°、接近角 45–65°、有效挂接比例 30–40%、单接触 1–2 N，以及 10–53 μm 论文针尖尺度；目标表面和本项目 50/100 μm 扫描不同（`evidence_card.md:215-220`）。
- RiSE 的 184/16 N/m 刚度、0.42 N·s/m 阻尼、stalk 长度/扭簧/预载角、8/10–11 mm 行程、0.04/0.2 N 预载及 4 mm/4 cm/1 N/2.5 N 动态试验值（`evidence_card.md:221-226`）。
- E4 的半固有周期回壁估计、(k_{xy}<0) 幅值近似，E5 的刚度比，E6 的 stalk 本构和 E8 连续补丁方程。
- Gamma 形状/尺度参数、砂纸/石材的凸体密度和搜索距离先验，均须目标三维表面重拟合。
- 附录 Hertz 精确系数、原文 (R_q) 式、无负号 (k_{xy})、反写角区间及印错的 (k_{ext}) 单位；提取审计逐项标警（`extraction_audit.json:333-364`）。(F_{max}\propto R^2) 最多保留趋势假设，不能给红砖破坏阈值。
- Chapter 5 的剥离正反馈可作现象类比，但补丁宽度、线刚度、球铰刚度和边缘强度不能映射为十字对爪参数。

## 6. 优先级结论

1. **P0 / 高置信度：** 阻止把 E5/E6/stalk 和 (k_{xy}) 作为“可直接采用”写入当前 accepted/DEV 模型；这会静默改写固定机构。
2. **P1 / 高置信度：** 用本卡强化既有 P1-A7：未实现扫掠回位路径时，释放点停止/标 unavailable，不能瞬时投影后跨过潜在再接触。
3. **P1 / 中高置信度：** 增加“材料容量—摩擦角边界解耦”消融验证；保持它是验证义务而非参数结论。
4. **P2 / 高置信度：** 将 (L_F) 和三维方向裕度离散设为 B 的命名输出；先硬后软与径向加载线仅作配对设计假设。
5. **P3：** 有限球尖、三维摩擦锥、共同平衡重分配、再挂接生命周期和偏心六维力矩主链已被文献支持，无需改写。

最终结论是：该论文没有推翻现行完整机理；它最有价值的新增作用是补强回位/再挂接的验证边界、增加材料—摩擦解耦消融和阵列方向/不均载输出。其 stalk、交叉刚度、Gamma 分布、连续补丁方程及全部样机数值均不得静默移植。

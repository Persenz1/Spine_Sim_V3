# 第 26 组反向审查：surface-topography challenge

**性质：** non-normative individual reverse audit
**对象：** P26, Pradhan et al. (2025), *The Surface-Topography Challenge*
**总判定：** `true_conflict = 0`；`supported = 4`；`supplement_candidate = 6`；`insufficient_evidence = 3`。本卡支持的是“可信表面输入如何测量、裁剪和审计”，不支持爪刺啮合、摩擦、承载或损伤定律。

## 1. 文献身份、提取完整性与适用域

该研究汇总两类 CrN/硅硬表面的 2088 次跨仪器形貌测量，证据卡将其定为 B 级条件启用，并明确其用途限于三维形貌采集、预处理和质量审计（`literature/26_surface_topography_challenge/evidence_card.md`:5–13）。提取审计覆盖全部 26 页、正文各节和附录 D–E（`literature/26_surface_topography_challenge/extraction_audit.json`:8–31），RMS、Fourier/PSD、调和插值和窗函数公式均已逐式核验（同文件:33–63）；Fig. 6/7/9 三张关键图也经高分辨率复核（同文件:87–111），最终状态为 `PASS_WITH_WARNINGS`（同文件:144–156）。

适用域只到“由原始高度数据形成可信、多尺度、带不确定度的 `SurfaceRealization`”。样品连续、硬且非多孔；卡片明确排除将其当作红砖材料参数或微刺接触/载荷/损伤证据（`evidence_card.md`:175–195）。因此下文“支持”均指测量现象或建模方向已被现行机理吸收，不表示该文足以认证本项目公式、数值或承载预测。

## 2. M1–M4 逐项对照

| # | 文献卡原结论与本地来源 | 现行机理对应位置 | 分类；优先级；置信度 | 判定理由 |
|---:|---|---|---|---|
| 1 | **M1：表面描述必须携带横向尺度；单个 \(R_a/R_q\) 不唯一。** `evidence_card.md`:21–30, 133–159；Fig. 9 见该文件:171–173。 | proposed 严格稿定义二维 PSD 并限定可信波数带（`paper/MECHANISM_DERIVATION_FORMAL.md`:326–339）；accepted A 同样定义二维 PSD/可信带（`modules/A_INTEGRATED_MODEL.md`:416–428）；B 可消费方向协方差、二维 PSD 和相关长度张量（`modules/B_INTEGRATED_MODEL.md`:684–690）。 | `supported`；P1；高 | “不能用孤立粗糙度标量代替多尺度几何”的核心已进入 A/B 主链，且二维方向表达比论文逐行一维 PSD 更完整。 |
| 2 | **M1 的元数据要求：**扫描范围、像素间距、滤波截止、方向和目标刺尖尺度必须随数据保存（`evidence_card.md`:25–30, 175–181）。 | A 只笼统要求“质量掩膜、可信带、测量/生成元数据”（`modules/A_INTEGRATED_MODEL.md`:414–428）；系统运行外壳仅列 surface ID/domain/quality（`system/SYSTEM_INTEGRATED_MODEL.md`:1825–1852）。 | `supplement_candidate`；P1；高 | 原则已隐含，但没有强制命名这些字段，也没有“目标刺尖尺度是否被可信波段覆盖”的可机读裕度。应补 `SurfaceAcquisitionManifest` 和 `tip_scale_coverage_margin`。 |
| 3 | **M2：名义像素间距不是物理分辨率；不可信高波数必须屏蔽。** `evidence_card.md`:32–41, 140–145。 | A 只在 \(\mathcal B_{trust}\) 内解释尺度并在几何不足时拒绝（`modules/A_INTEGRATED_MODEL.md`:416–428, 508）；分辨率不足返回 `GEOMETRY_UNCERTAIN`（同文件:1796–1799, 1882–1886）；System 要求 MTF/SNR、可信波段与多分辨率收敛（`system/SYSTEM_INTEGRATED_MODEL.md`:2198）。 | `supported`；P1；高 | 现行安全边界与文献一致：伪小尺度不得进入接触求解，数据不足不是“零粗糙度”，而是不可认证。 |
| 4 | **M2 的仪器物理：**光学衍射/陡坡漏检、探针半径卷积和窄谷不可达决定截止（`evidence_card.md`:35–40, 124–127, 179）。 | A 的“测量元数据”字段未展开（`modules/A_INTEGRATED_MODEL.md`:416）；System 关闭条件提到 MTF/SNR，却未规定探针形态、坡度可见性、截止推导及证据（`system/SYSTEM_INTEGRATED_MODEL.md`:2198）。 | `supplement_candidate`；P1；高 | 应新增 `InstrumentTransferManifest`：技术/配置、MTF 或横向分辨率证据、探针半径/形状、陡坡与缺失率、每方向可信 \(q\) 上限及推导版本；不能只存像素间距。 |
| 5 | **M1/M2 到针尖的尺度桥：**可信波段应覆盖刺尖和候选凸体尺度，并扩展到有限刺尖可达形貌（`evidence_card.md`:30, 41, 178–181）。 | proposed 用半径 \(R\) 的完整球包络/欧氏间隙求有限尖端非穿透（`paper/MECHANISM_DERIVATION_FORMAL.md`:341–371）；A 的关闭条件直接检查 50/100 µm 针尖支持法向可靠性（`modules/A_INTEGRATED_MODEL.md`:1796–1799）。 | `supported`；P1；高 | 文献的有限分辨率警告与当前球尖形态学天然相容；但 P26 不验证该球尖接触公式或啮合成功率。 |
| 6 | **M3：位置×方向×尺度复测、异原理技术交叉检查、中位数/IQR 和异常标记。** `evidence_card.md`:43–52, 147–152, 177–180；Fig. 7 见该文件:167–169。 | A 仅要求多位置测量、重复扫描和多分辨率收敛（`modules/A_INTEGRATED_MODEL.md`:1796–1799）；System 只有多位置三维测量/MTF/SNR 与随机样本稳定性（`system/SYSTEM_INTEGRATED_MODEL.md`:2153–2159, 2198）。 | `supplement_candidate`；P1；高 | 现行机理漏掉“异原理复测”及保留技术内/技术间分歧的规则。建议把它作为实测表面验收协议和不确定度输出，而非接触本构。 |
| 7 | **M3 的 IQR/多数规则数值方案。** 卡给出 25%–75%、每尺度箱至少 5 点（`evidence_card.md`:118–127），同时警告多数不等于真值（同文件:180；`extraction_audit.json`:127–136, 152）。 | System 只要求样本顺序增加后置信区间/排序稳定，不固定样本数或稳健阈值（`system/SYSTEM_INTEGRATED_MODEL.md`:2159, 2198）。 | `insufficient_evidence`；P2；高 | 这些阈值是本次多实验室基准的审计选择，不足以成为红砖验收常数。可借用“保留分歧、给不确定带”的方向，不可移植阈值或多数裁决。 |
| 8 | **M4：原始高度、缺失掩膜及完整预处理链必须可复现。** `evidence_card.md`:54–63, 175–177。 | A 的 `SurfaceRealization` 不可变且列有质量掩膜/测量元数据（`modules/A_INTEGRATED_MODEL.md`:289–300, 414–416）；System 的原始数据保真条款目前明确针对力—位移/状态曲线及其滤波（`system/SYSTEM_INTEGRATED_MODEL.md`:2033–2042），未形成表面原始数据专门合同。 | `supplement_candidate`；P1；高 | 应显式保存 raw-height hash/handle、缺失掩膜、每一步输入输出 hash、算法/版本/参数和回放收据，避免仅保存处理后网格。 |
| 9 | **M4：二次去趋势删长波、调和插值不恢复真实形貌、窗函数改变谱，均需敏感性分析。** `evidence_card.md`:67–81, 101–114, 184–190。 | accepted A 只有通用质量掩膜和可信带（`modules/A_INTEGRATED_MODEL.md`:414–428），现有表面/网格加密验证也只看下游 gap/法向/事件/wrench 是否平台（`system/SYSTEM_INTEGRATED_MODEL.md`:2149–2154）。 | `supplement_candidate`；P1；中高 | 这是关键遗漏。建议将去趋势阶次、插补方案、窗函数设为可选预处理模型 ID，并要求原始/不同方案对 PSD、法向、曲率、事件和峰值的敏感性；不得把论文方案固化为唯一默认。 |
| 10 | **E2 是逐行一维 PSD，不等于完整二维各向异性谱。** `evidence_card.md`:83–99, 181, 188。 | proposed/A 使用二维 PSD（`paper/MECHANISM_DERIVATION_FORMAL.md`:326–339；`modules/A_INTEGRATED_MODEL.md`:418–428），B 明确允许方向协方差、二维 PSD 与相关长度张量（`modules/B_INTEGRATED_MODEL.md`:682–690）。 | `supported`；P2；高 | 这是范围扩展而非冲突；现行二维表示不能反过来声称已由 P26 的逐行处理验证。 |
| 11 | **M4/E2：PSD 数值依赖 Fourier 归一化、单位、方向和窗归一化。** `evidence_card.md`:83–99, 101–114；`extraction_audit.json`:144–152。 | proposed/A 已写出一个二维约定（`paper/MECHANISM_DERIVATION_FORMAL.md`:326–336；`modules/A_INTEGRATED_MODEL.md`:418–426），但 surface schema 未强制 `PSDConventionID`、单位检查、方向基和窗能量归一化字段（`modules/A_INTEGRATED_MODEL.md`:414–428）。 | `supplement_candidate`；P1；高 | 公式约定存在不等于导入数据可互操作。应把约定 ID/单位/坐标方向/单双边谱/窗归一化作为导入门槛，不兼容时拒绝或显式转换。 |
| 12 | **CrN/Si 的 RMS、PSD 和分辨率示例不是红砖参数。** `evidence_card.md`:118–129, 175–186。 | 工程事实仍把 PSD、高度分布、相关长度、各向异性和分辨率列为未决（`engineering_fixed_context.md`:705–725）；System 同样保持 `U-SYS-009` 未标定（`system/SYSTEM_INTEGRATED_MODEL.md`:2198）。 | `insufficient_evidence`；P0；高 | 无数值冲突，因为现行机理没有采用这些数值；任何把 900/10.5/3 nm 或本文截止值填入红砖 `SurfaceConfig` 的做法都会越过证据域。 |
| 13 | **论文没有微刺接触、摩擦、捕获、载荷共享或损伤实验。** `evidence_card.md`:9–12, 184–195；`extraction_audit.json`:144–152。 | 独立复核明确区分“理论定义”与代码/数值/实验验证（`review/DERIVATION_VERIFICATION_2026-07-17.md`:32–41），System 当前也只能标记 `SPEC_DEFINED`（`system/SYSTEM_INTEGRATED_MODEL.md`:2046–2059）。 | `insufficient_evidence`；P0；高 | P26 只能把关几何输入，不能用于支持 Coulomb 参数、啮合概率、承载曲线、材料失效或正式 \(F_{crit}\)。 |

## 3. 真冲突与表面冲突

未发现同对象、同假设、同适用域下的真冲突。三个容易误判的差异是：一是 P26 的逐行一维 PSD 与现行二维方向谱属于维度/范围差异；二是 P26 的连续硬 CrN/Si 表面与本项目红砖、混凝土、砂纸属于材料与形貌域差异，工程主线的高度场及完整网格分支仍保持不变（`engineering_fixed_context.md`:667–703）；三是 P26 指出预处理会改谱，而现行机理只是未把这些步骤完全合同化，这是遗漏，不是相反结论。

## 4. 漏掉的关键结论与建议补充

1. **P1，A1 输入证据层：**新增强制 `SurfaceAcquisitionManifest` 和 `InstrumentTransferManifest`。身份为“输入证据/元数据”，不是物理参数；实测表面必须给扫描范围、采样间距、方向、仪器配置、物理分辨率或探针形态、可信波段推导、原始数据与缺失掩膜 hash。合成表面则给生成器/seed/网格/目标谱清单。
2. **P1，A1 可选预处理层：**新增版本化 `SurfacePreprocessingPipeline`，记录去趋势、缺失处理、窗、Fourier/PSD 约定和每步 hash。身份为“可选数值模型”；不同方案必须对可信带、法向/曲率、球尖支持、事件和峰值做敏感性，不能默认采用二次趋势、调和插值或 Hann 窗。
3. **P1，System 验证层：**增加位置×方向×尺度复测，并在设备可用时做异原理技术交叉检查；分别保存技术内 PSD 分布、技术间差值、共识谱和不确定带。中位数/IQR 可作为候选稳健统计，阈值需针对红砖/仪器标定；多数规则不得标成物理真值。
4. **P1，输出层：**为每个 `SurfaceRealization` 输出 `trusted_q_band_by_direction`、尺度相关 \(h_{rms}(L)\) 或滤波尺度描述、二维/方向 PSD、缺失率、插补占比、tip-scale coverage 和所有质量否决码。验证义务是原始数据可重放、单位/归一化闭合、分辨率与预处理敏感性平台、跨技术异常可追踪。

建议把上述补充落实为以下验收门槛，而不是只增加说明文字：

- **采集身份完整性：**每个实测 realization 必须绑定不可变原始文件 hash、仪器与测量原理、镜头/探针配置、坐标方向、扫描足迹、采样间距、缺失掩膜和重复测量组。物理分辨率必须有估计方法和证据来源；只有像素间距而没有传递能力时，最短可信尺度保持未认证。
- **处理链可重放性：**每一步都声明输入、输出、算法版本和参数。去趋势删除的长波范围需写入质量记录；插补区仍保留原掩膜并标成非实测值；窗函数与谱归一化必须通过 Parseval/RMS 一致性和单位测试。不能从最终网格反推一个虚构的原始表面。
- **复测与异常语义：**同位置、同方向和相容扫描尺度下先形成技术内重复分布，再在各自物理可信带裁剪后比较异原理技术。显著分歧应产生 `CROSS_TECHNIQUE_DISAGREEMENT` 及分技术数据，不得为了得到单一共识而静默删除少数技术；外部校准或独立复测才能关闭该标记。
- **下游尺度桥：**针对每种 50/100 µm 针尖，至少比较原始可信数据与重采样/截止扰动后的球包络、支持点、法向、曲率、首次事件和 wrench。只有这些下游量在声明尺度区间进入平台，才可把该 realization 用于材料专属排序；仅 PSD 曲线视觉收敛不足以认证啮合输出。

## 5. 明确不可直接移植

- 数据规模 2088 次、153 人、64 组/企业、20 国不是本项目最低样本量；25%–75% IQR、每尺度箱至少 5 点和多数规则也不是红砖验收阈值（`evidence_card.md`:118–127）。
- 100 µm 尺度的 900/10.5 nm、1 µm 尺度约 3 nm，以及任何 CrN/Si PSD 都不得进入红砖/混凝土/砂纸生成参数（同文件:128–129, 182）。
- 20 nm AFM 探针、2 µm stylus/indenter、2 µm 光学截止和 500 µm 扫描上限均为该数据集的代填/裁剪示例，必须按实际仪器重新确定（同文件:124–127；`extraction_audit.json`:133–136）。
- 二次去趋势、调和插值和归一化 Hann 窗只能作为待敏感性分析的候选处理；论文的一维 PSD 公式不能未经方向、单位和归一化转换直接替换现行二维 PSD（`evidence_card.md`:78–114, 181, 189–190）。
- 该文不提供任何 \(\mu\)、局部强度、接触柔顺、捕获概率、载荷共享、损伤或承载参数；这些量仍按现行未决/`unavailable` 边界处理。

**最终优先级：**无新增 P0 理论冲突；P0 仅用于禁止材料数值与力学结论越域移植。最值得补入现行完整机理的是四项 P1 表面证据合同；在它们关闭前，当前 `GEOMETRY_UNCERTAIN`/材料专属预测不可认证的安全处理应保持不变。

**关闭判据：**只有在目标红砖上完成版本化采集、原始数据回放、物理分辨率裁剪、预处理敏感性、方向/位置复测和下游球尖输出收敛，相关 P1 才可关闭。单一仪器的一张处理后高度图、单个粗糙度值或一条外观平滑的 PSD 均不构成关闭证据；若异技术结果持续分歧，应保留不确定状态并停止材料专属排序，而不是选择更符合预期的一条曲线。

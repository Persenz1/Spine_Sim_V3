# 第 12 组反向审查：红陶砖二维/三维粗糙度测量

## 1. 身份、完整性与适用域

- 文献：Arnold et al., *A Critical Analysis of Red Ceramic Blocks Roughness Estimation by 2D and 3D Methods*（2021，DOI 10.3390/rs13040789）；对象是不同烧成温度红陶砖的二维触针轮廓与三维激光形貌测量，不是爪刺接触、摩擦或破坏试验（`theory/evidence_reassessment/literature/12_red_ceramic_blocks_roughness/evidence_card.md:3-10`）。
- 提取状态为 `PASS_WITH_WARNINGS`；18 页、正文全部章节、公式、表格和图均已核查（`theory/evidence_reassessment/literature/12_red_ceramic_blocks_roughness/extraction_audit.json:2-23,177-180`）。关键图 Fig. 8 已提取，显示 5/2.5/1.25 mm 四叉树节点的空间粗糙度差异及父子节点关系（`theory/evidence_reassessment/literature/12_red_ceramic_blocks_roughness/evidence_card.md:134-140`；`theory/evidence_reassessment/literature/12_red_ceramic_blocks_roughness/figures/fig08_p09_quadtree_roughness_scales.png`）。
- 适用域限于论文的 10 mm × 10 mm、人工选区、特定仪器与处理流程；它能约束 A1 地形输入与质控方向，不能直接标定 150 mm × 150 mm 项目表面、接触力学或材料损伤。项目固定主域仍是 150 mm × 150 mm 单值高度场（`theory/evidence_reassessment/engineering_fixed_context.md:667-683`），而表面统计、摩擦、强度与分辨率仍为未决量（同文件 `:705-724`）。

## 2. M1–M5 逐项审查

| ID | 原始结论与本地证据 | 现行机理对应位置 | 分类 | 判断、优先级与置信度 |
|---|---|---|---|---|
| 12-01（M1） | 红陶砖存在位置/方向异质性，单条二维轮廓的 \(R_a\) 不具代表性（`evidence_card.md:18-27,110-116`）。 | accepted A 要求表面对象保存坐标、域、质量、测量/生成元数据和不确定性，并只在可信波数带解释尺度（`theory/modules/A_INTEGRATED_MODEL.md:414-428`）；表面统计明确包含各向异性并要求多位置三维测量（同文件 `:1794-1799`）。B 还保留方向协方差/PSD/相关长度，并要求转置阵列比较时不旋转或重采样同一表面（`theory/modules/B_INTEGRATED_MODEL.md:680-690`）。 | `supported` | 现象与建模方向已被 accepted 基线吸收；并未把单线 \(R_a\) 当材料常数。P1，高置信度。FORMAL 仅写高度场、PSD 和可信带（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:316-339`），宜补一句明确拒绝单线代表性，但这不是 accepted 机理冲突。 |
| 12-02（M1） | 合并 H/V 有显著差异，但若干单线配对不显著，故不能抽象成固定“某方向更粗糙”的常数（`evidence_card.md:110-116`）。 | B 仅把方向性作为 realization 的相关结构，不把邻接/相关性转成 IID 成功率或载荷权重（`theory/modules/B_INTEGRATED_MODEL.md:660-690`）；系统将各向异性列为未标定项（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198-2199`）。 | `supported` | 当前模型没有强加固定方向符号或强度。论文也不足以给项目各向异性参数。P2，高置信度。 |
| 12-03（M2） | 有限半径触针、横/纵向分辨率、覆盖面积和采样维度共同滤波所见形貌，2D/3D 输出不可互换（`evidence_card.md:29-38`）。 | accepted A 保存测量元数据与可信带（`theory/modules/A_INTEGRATED_MODEL.md:414-428`），分辨率不足返回 `GEOMETRY_UNCERTAIN`，关闭条件包括仪器 MTF/SNR、重复扫描和多分辨率收敛（同文件 `:1796-1799,1882-1887`）；系统也要求 MTF/SNR 与可信波段审查（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198`）。 | `supported` | 测量链是地形输入的不确定性来源这一方向已明确。测量触针滤波与模型中的有限爪刺球尖形态学是两个串联但不同的算子，不能混为同一半径。P1，高置信度。 |
| 12-04（M2/M5） | 本文 3D/2D 平均 \(R_a=2.2701/1.6697\ \mu m\)，二维为三维的 73.6%，且二维分布偏低（`evidence_card.md:62-71,118-124`）。 | 现行模型不设 2D→3D 换算；表面参数无隐藏默认，目标材料专属预测须经三维测量与统计质控（`theory/modules/A_INTEGRATED_MODEL.md:1794-1799,1882-1887`）。 | `insufficient_evidence` | “本仪器/样品下 2D 偏低”可作趋势核验；0.736 不能成为换算系数、缩放因子或参数先验中心。P1，高置信度。 |
| 12-05（M3） | 点云先以一个最小二乘平面去趋势，所有四叉树节点共享该平面，再按 Z 向有符号残差计算平均绝对值（`evidence_card.md:40-49,75-89`）。 | 当前 A1 接受高度场/网格并保存测量元数据，但未规定实测点云如何去趋势（`theory/modules/A_INTEGRATED_MODEL.md:414-428`）；接触计算使用欧氏有符号距离而非测量 Z 残差（同文件 `:430-466`；FORMAL `:341-371`）。 | `supplement_candidate` | 可新增“测量预处理可选基线”，记录拟合域、平面参数、残差方向、算法版本与原始点云哈希；只适用于可由单平面去趋势的小窗口，并须保留原始高度。不得把该 Z 残差公式替换接触间隙。P1，中高置信度。 |
| 12-06（M4） | 5/2.5/1.25 mm 四叉树局部 \(R_a\) 揭示尺度依赖和高/低粗糙区，全域均值会抹平空间异质性（`evidence_card.md:51-60,126-140`）。 | A1/B 接口已有空间与邻域查询（`theory/modules/B_INTEGRATED_MODEL.md:539-552`），但 FORMAL 与 accepted 输出未明确规定“多尺度局部测量质控图”。 | `supplement_candidate` | 建议把四叉树或等价滑窗/多尺度统计作为 `SurfaceRealization` 的 QA 可选输出，用于覆盖度和局部非均匀性检查；节点尺度必须由针尖半径、搜索行程和测量可信带重新选取。P2，高置信度。 |
| 12-07（M4） | \(R_a\) 只表征高度幅值，不能替代坡度、曲率、方向、PSD 或有限刺尖可达性，也不能直接成为啮合能力图（`evidence_card.md:57-60,142-149`）。 | 固定接口要求高度/三维几何、法向、坡度、必要曲率与邻域查询（`engineering_fixed_context.md:645-665`）；系统 A1 句柄同样返回高度/几何、法向、坡度、曲率、域和质量（`theory/system/SYSTEM_INTEGRATED_MODEL.md:457-463`），A 用完整球尖包络/最近支持求接触（`theory/modules/A_INTEGRATED_MODEL.md:430-466`）。 | `supported` | 这是强一致项：现行机理没有用单个 \(R_a\) 替代几何可达性。P1，高置信度。 |
| 12-08（M5） | 测量方法系统改变统计分布，因此数据源必须带方法身份和尺度元数据（`evidence_card.md:62-71`）。 | `SurfaceRealization` 已要求测量/生成元数据、域、质量、可信带和不确定性（`theory/modules/A_INTEGRATED_MODEL.md:414-428`），系统运行外壳保存 realization ID/version/hash/seed/domain/quality（`theory/system/SYSTEM_INTEGRATED_MODEL.md:1825-1852`）。 | `supplement_candidate` | 方向已支持，但字段还不够可审计；宜显式增加 `acquisition_kind/instrument/tip_or_MTF/lateral_pitch/vertical_resolution/window/detrend/metric_definition`。P1，高置信度。 |
| 12-09（跨尺度） | 论文结论来自 10 mm × 10 mm 测区，且样区人工避开宏观缺陷（`evidence_card.md:24-25,98-101,151-158`）。 | 项目固定域为 150 mm × 150 mm（`engineering_fixed_context.md:667-683`），accepted 关闭条件要求“多位置三维测量”但未细化选区偏差（`theory/modules/A_INTEGRATED_MODEL.md:1794-1799`）。 | `supplement_candidate` | 这是范围差异，不是真冲突。建议增加跨位置/跨尺度采样计划、缺陷纳入/排除规则、覆盖率和留出区域；单个小窗口不能证明 150 mm 域平稳或代表性。P1，高置信度。 |
| 12-10（测量质量） | “10 μm 节距、10 mm × 10 mm、约 10,000 点”彼此不相容；触针 5 μm 半径与 4 μm 针尺寸也冲突（`evidence_card.md:99-103,151-157`；`extraction_audit.json:137-147`）。 | 现行模型禁止隐藏默认参数，并以仪器/网格/针尖输出收敛关闭分辨率（`theory/modules/A_INTEGRATED_MODEL.md:351,1882-1887`）。 | `insufficient_evidence` | 不得用该节距、点数或触针尺寸设求解网格/传递函数；需原始数据或仪器记录复核。P1，高置信度。 |
| 12-11（样本选择） | 样区由单一观察者避开宏观缺陷，可能低估服役表面的缺陷与异质性（`evidence_card.md:98-101,151-158`；`extraction_audit.json:169-175`）。 | accepted 仅概括“多位置三维测量、质量掩膜、统计验收”（`theory/modules/A_INTEGRATED_MODEL.md:416,1794-1799`），没有明确规定选择盲法、缺陷分层或选择概率。 | `supplement_candidate` | 将其加入 A1 测量验证义务：随机/分层选区、宏观缺陷单独标注而非静默删除、重复测量和训练/留出区域分离。P1，中高置信度。 |
| 12-12（材料分组） | 700/800/900/1000 °C 只是本文制样组，未建立烧成温度→形貌的独立响应模型（`evidence_card.md:95-97,158`）。 | 表面统计仍未标定，系统只允许版本化 realization（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198`）。 | `insufficient_evidence` | 不得把烧成温度作为项目 PSD、粗糙度或强度的确定性映射，也不得外推到未知红砖批次。P2，高置信度。 |
| 12-13（信息充分性） | 论文未给 PSD、相关长度、坡度、曲率、方向谱或可复算原始点云（`evidence_card.md:151-155`；`extraction_audit.json:169-175`）。 | FORMAL 需要可信带内二维 PSD（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:316-339`），accepted A/B 还需要各向异性、非高斯、相关长度与局部几何查询（`theory/modules/A_INTEGRATED_MODEL.md:1794-1799`；`theory/modules/B_INTEGRATED_MODEL.md:684-690`）。 | `insufficient_evidence` | 本文足以支持测量/质控方向，不足以填充当前 `SurfaceRealization` 的材料专属统计参数或重建接触地形。P1，高置信度。 |
| 12-14（机理边界） | 论文没有爪刺加载、摩擦、局部承载、断裂或损伤试验（`evidence_card.md:148-149,160-162`）。 | A/system 将摩擦、接触柔顺、强度和损伤分别保持 `unavailable` 或待试验关闭（`theory/modules/A_INTEGRATED_MODEL.md:1805-1817`；`theory/system/SYSTEM_INTEGRATED_MODEL.md:2199-2202`）。 | `insufficient_evidence` | 不可用本卡确认或反驳接触/损伤方程，更不能由粗糙度推出抓附力。现行机理的证据隔离正确。P0（若误用则阻断定量认证），高置信度。 |

## 3. 真冲突与表面冲突

**真冲突：未发现。** 在相同对象、假设与适用域下，本卡没有结论与 proposed FORMAL 或 accepted A/B/System 不兼容。当前独立复核也明确指出代码、网格/步长/随机样本及实验验证均未完成（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:32-41,449-465`），所以不能把“规范已有字段”误写成已由本文验证。

表面冲突有四类：一是论文的 Z 向平面残差是**测量预处理量**，现行欧氏有符号距离是**接触间隙**，二者不应相等；二是 10 mm 测窗与 150 mm 仿真域属于采样窗口和工程域差异；三是测量触针半径与爪刺球尖半径对应不同滤波阶段；四是论文观察到部分 H/V 差异，不等于项目红砖具有固定方向常数。它们都应以元数据、尺度适用域和验证义务化解，而不是修改接触主方程。

## 4. 被漏掉的关键结论与建议补充

1. **A1 输入合同，P1：** 新增版本化 `SurfaceAcquisitionMetadata`，至少包含采集维度、仪器/探头、横纵分辨率或 MTF、测区与位置、测线方向、原始数据哈希、去趋势/滤波版本、可信带和度量定义。验证义务是重复扫描、跨仪器/分辨率敏感性及接触输出收敛；身份为“输入质控/验证义务”，不是材料定律。
2. **A1 预处理候选，P1：** 增加可选 `GLOBAL_LS_PLANE_Z_RESIDUAL`，仅对近似平面小窗口启用；保存拟合平面、原始点云和残差场，并与局部/替代去趋势做敏感性检查。身份为“可选测量模型”，不得替换规范接触 gap。
3. **A1 QA 输出，P2：** 增加多尺度局部幅值图、覆盖充分性和空间非均匀性指标；四叉树只是可选实现，尺度须按真实针尖、搜索路径和可信带标定。必须明确 `roughness_QA_map != engagement/capacity_map`。
4. **测量/验证计划，P1：** 明确多位置、方向、批次和缺陷分层，记录人工排除规则，并以留出壁面区域检查统计与设计排序。该项补足 accepted “多位置三维测量”的操作定义。
5. **系统输出 schema，P2：** 区分 `profile_Ra`、来源特定的 3D 平均绝对残差（宜另命名，避免自动等同标准 `Sa`），并绑定窗口、尺度与方法；禁止内建 0.736 换算。

## 5. 明确不可直接移植

- 0.736 比值、2.2701/1.6697 μm 均值、0.5814/0.2543 μm² 方差；
- 5/2.5/1.25 mm 四叉树尺度、10 mm × 10 mm 测窗、10 μm 节距、约 10,000 点；
- 4/5 μm 触针规格、可疑检测力量纲、Table 5 分档阈值；
- 700–1000 °C 烧成温度到项目地形或强度的映射；
- 将单一全局拟合平面扩展到 150 mm 域，或将局部 \(R_a\) 热图当啮合概率/承载图；
- 任何摩擦系数、单刺载荷、材料强度、断裂能或损伤参数。

## 6. 总结

本卡与现行完整机理**无真冲突**，并强力支持其“全场三维地形、可信带、空间相关性、有限球尖可达性、参数未标定则拒绝材料专属预测”的方向。真正的增量不是新增接触方程，而是把 FORMAL/accepted 中较概括的测量元数据要求收紧为可审计的采集—去趋势—多尺度 QA—代表性验证链。当前卡只能提升 A1 输入与验证规范，不能提升红砖接触、摩擦、破坏或承载参数的证据等级。

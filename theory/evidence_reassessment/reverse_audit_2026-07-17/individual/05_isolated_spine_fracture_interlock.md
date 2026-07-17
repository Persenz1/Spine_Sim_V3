# 05｜孤立刺局部断裂与互锁：反向审查

**审查对象：** Iacoponi、Calisti、Laschi（2020），*Simulation and Analysis of Microspines Interlocking Behavior on Rocky Surfaces: An In-Depth Study of the Isolated Spine*。
**本报告状态：** non-normative review working material；不修改 accepted 1.0。
**总判定：** 未发现同一对象、假设和适用域下的真正冲突。M1、M3 和 M5 与现行分层机理高度相容；M2 的“局部损伤后再决定整体释放”方向相容，但二维 Mode-II 断裂面算法不能直接移植；M4、M6 暴露出条件承载分布、有效搜索距离和覆盖层可达性三个实质补充候选。

**引文缩写：** 下文 `.../evidence_card.md` 与 `.../extraction_audit.json` 分别完整指向 `theory/evidence_reassessment/literature/05_isolated_spine_fracture_interlock/evidence_card.md` 和 `theory/evidence_reassessment/literature/05_isolated_spine_fracture_interlock/extraction_audit.json`；冒号后的数字均为 1-based 行号。

## 1. 证据身份、完整性与适用域

证据卡把研究对象限定为近切向加载、有限半径孤立钢刺与岩石/混凝土二维粗糙轮廓，并明确是理论、仿真和单刺实验组合（`theory/evidence_reassessment/literature/05_isolated_spine_fracture_interlock/evidence_card.md:3-10`）。抽取审计覆盖全部 9 页和全部正文节（`.../extraction_audit.json:5-29`），Eq. (1)–(6)、Table 1–7 均逐项核对（`.../extraction_audit.json:31-111`），三张保留图也经目视检查（`.../extraction_audit.json:121-187`）；状态为 `PASS_WITH_WARNINGS`（`.../extraction_audit.json:223-233`）。本次再次查看 Fig. 2、7、12：前者确为二维接触点—断裂线—轮廓再交点构造，后两者只证明样本右偏及 Log-Normal 拟合外观，不提供零值处理或阵列相关性。

适用边界必须保留：二维轮廓、主要切向外载、硬脆基底先破坏、断裂面两向尺度近似相等；三维非共面裂纹、混合模态、塑性压碎和刺体主导失效均在原模型外（`.../evidence_card.md:29-38`）。实验又是近零法向预载、约 30° 刺角、近刚性水平约束的孤立刺（`.../evidence_card.md:215-222`），而本项目单刺预载固定 0.5 N、连续路径固定 100 mm（`theory/evidence_reassessment/engineering_fixed_context.md:750-757,863-873`）。因此其数值不能覆盖工程固定事实，也没有 C 层对爪证据。

## 2. 决定性判断（M1–M6）

| # | 卡片结论与本地证据 | 现行完整机理对应 | 分类与理由 |
|---:|---|---|---|
| 1 | **M1：局部赫兹强度越限不等于整体解锁**；低载局部应力已远超抗压强度，但挂接仍保持（`.../evidence_card.md:19-27,162-166`）。 | accepted A 把材料起始、释放和针体强度分成不同事件，材料更新后必须重求力学才可判释放（`theory/modules/A_INTEGRATED_MODEL.md:99-103,1405-1414`）；FORMAL 也把材料起始与接触释放设为不同 guard（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1787-1797`）。 | **supported（高）**。现行模型没有把赫兹峰值或首次强度越限直接写成整个位形失效，正符合该否定性证据。建议将其升级为显式验证义务，而非新增承载公式。 |
| 2 | **M2：接触诱发裂纹控制局部凸体脱落**，并从接触点搜索二维断裂线/再交点（`.../evidence_card.md:29-38,194-196`）。 | proposed `M1` 已有混合模态断裂能、材料面片软化与功共轭门槛（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:959-1027`），但 accepted A 明确排除显式裂纹扩展和地形重网格（`theory/modules/A_INTEGRATED_MODEL.md:83-85`）。 | **supplement_candidate（中高）**。可补为 A 材料层的可选“脆性凸体/裂面搜索”后端或验证基准；不得把二维裂面直接塞入主线，也不得让损伤静默改写原始表面。 |
| 3 | 原 Eq. (1) 为 \(\tau_{cr}=K_{IIc}\sqrt{\pi c}\)，量纲不是应力；Eq. (2) 又以 \(L_f^2\) 代三维面积（`.../evidence_card.md:80-103`），审计确认乘号无误且无法从本文校正（`.../extraction_audit.json:31-42,196-201`）。 | FORMAL 明确只有功共轭、尺度桥和参数闭合后 `M1` 才可用，否则返回 `MATERIAL_MODEL_UNAVAILABLE`（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1007-1027`）；独立复核要求主线保持 `no_damage`（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:255-263`）。 | **insufficient_evidence（高）**。本文支持“裂纹控制”方向，不足以支持本项目采用其临界式、面积外推或数值；现行阻断必须保持。 |
| 4 | **M3：有限刺尖、粗糙度和允许行程共同决定几何捕获机会**；大 \(R\) 屏蔽小尺度形貌，增大 \(R_a,d\) 在拟合域趋于饱和（`.../evidence_card.md:40-48`）。 | A/FORMAL 用完整球包络、有限球冠合法性和全部支持候选实现三维形态滤波（`theory/modules/A_INTEGRATED_MODEL.md:414-478`; `theory/paper/MECHANISM_DERIVATION_FORMAL.md:341-454`），并保存搜索/附着分段距离（`theory/modules/A_INTEGRATED_MODEL.md:1668-1698`）。 | **supported（高）**。现行三维确定性 realization 模型包含该方向且比原二维坡度筛选更一般；文献可用于 \(R\)、粗糙尺度、观察窗口的趋势测试。 |
| 5 | 原文称 \(p_{lock}\) 与 \(K_{IIc}\) 无关，因为它只由几何点筛选定义（`.../evidence_card.md:40-47`）。 | A 明确规定 `candidate_any/robust` 仅是几何必要标签，不是摩擦稳定、材料安全或抓附成功（`theory/modules/A_INTEGRATED_MODEL.md:466-478`），系统的二元成功阈值也尚未定义（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2217-2218`）。 | **supported（高，定义域差异）**。几何候选对韧度无关与现行分层相容；若把论文 `p_lock` 误译成“最终承载成功率”才会形成表面冲突。应同时输出几何接触率与承载事件率，禁止混名。 |
| 6 | Eq. (4) 的 \(p_{lock}\) 拟合在 \(R_a<t\) 为负、在 \(d=0\) 强制为零，系数仅对应二维合成轮廓和 5/10/50 μm 刺尖（`.../evidence_card.md:118-128,146-154`）。 | 系统要求随机样本数由统计稳定性关闭，趋势优先于偶然峰值，成功阈值未批准即 unavailable（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2159-2166`）。 | **insufficient_evidence（高）**。该式只能作为原论文复现/单元测试夹具或弱经验先验；不能作为红砖捕获律，更不能覆盖 100 mm 工程行程。 |
| 7 | **M4：固定工况承载样本右偏，多数仿真与 Rock A 实验可由 Log-Normal 描述**（`.../evidence_card.md:50-58,168-172,198-204`）。 | FORMAL 已把 \(\mathcal D(F_{peak})\) 作为可观测/标定对象，但未规定分布族（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:2006-2021,2064-2078`）；A 保留完整连续曲线而不设二元成功阈值（`theory/modules/A_INTEGRATED_MODEL.md:1668-1708`）。 | **supplement_candidate（中高）**。在 validation/统计后处理中加入“零/失败质量 + 条件正值承载”的候选模型比较，Log-Normal 只列候选，不写成 A 本构。须预先冻结失败/近零处理。 |
| 8 | 卡片明确禁止把单刺 Bernoulli/Log-Normal 独立复制到阵列（`.../evidence_card.md:206-213`）。 | B 的表面相关性不产生 IID 成功率或载荷转移权重，载荷由逐针 A 响应与共同平衡求得（`theory/modules/B_INTEGRATED_MODEL.md:682-721,723-758`）。 | **supported（高）**。此证据强化现行 B 边界；没有文献依据增设独立同分布针模型或把单刺均值乘针数。 |
| 9 | **M5：表面承载高时会切换为刺体弯曲/断裂主导，表面模型不能无限外推**（`.../evidence_card.md:60-67`）。 | accepted A 分别监控墙面材料和针体强度，禁止无解释的 \(\min(F_{wall},F_{needle})\)；针体有独立根截面应力与屈服/断裂事件（`theory/modules/A_INTEGRATED_MODEL.md:101-103,993-1046`）。 | **supported（高）**。文献支持“双上限竞争/主导模式切换”，现行事件竞争比简单截断更严谨；材料事件后重平衡决定是否真正释放。 |
| 10 | 平均力随 \(\sqrt d,R_a,K_{IIc}\) 增大、随 \(R\) 增大而降，但仿真对 Rock A/C 全部上偏；Eq. (6) 参数单位未报（`.../evidence_card.md:130-140,174-178,217-221`）。 | 系统把局部强度/断裂能列为未标定，允许 `no_damage` 但禁止假装已标定（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2197-2202`），且验证只应先比较趋势/排序（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2165-2166`）。 | **insufficient_evidence（高）**。趋势可作留出验证假设；Eq. (6)、绝对力和线性 \(K_{IIc}\) 关系均不可作本项目参数或定量认证。 |
| 11 | **M6：失接后跳跃会越过候选点，使名义 \(d\) 不等于有效搜索长度**（`.../evidence_card.md:69-76,180-184`）。 | accepted A 的 standalone 会继续同一准静态路径搜索（`theory/modules/A_INTEGRATED_MODEL.md:1296-1316`），但其风险表明确承认不再现跳跃、冲击和弹道再接触（`theory/modules/A_INTEGRATED_MODEL.md:1900-1908`）；FORMAL 更安全地要求未实现扫掠回位时在释放 pose 终止（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1904-1906`）。 | **supplement_candidate（高，范围差异）**。不是文献与严格稿的真冲突；它揭示 accepted 准静态 continuation 的系统性乐观风险。应增加有效搜索/跳过区间输出和明确的 `RECONTACT_DYNAMICS_EXCLUDED`。 |
| 12 | 软黏液层阻断刺尖接触使 \(p_{lock}=0\)，硬化覆盖层成为新的有效基底类别（`.../evidence_card.md:69-76,186-190`）。 | A 的 `SurfaceRealization` 可保存材料标签并支持不同几何后端（`theory/modules/A_INTEGRATED_MODEL.md:414-428`），但现行模型没有软覆盖层—下伏基底的可达性、穿透或层间接触分支。 | **supplement_candidate（中高）**。硬覆盖可作为独立 realization/材料标签；软覆盖阻断需要显式层状表面与 `tip_to_load_bearing_substrate_accessible` 状态，不能靠修改 \(\mu\) 或粗糙度代替。 |

## 3. 真冲突与表面冲突

- **真冲突：0 项。** 文献没有在本项目相同 3D 表面、0.5 N 法向主动预载、100 mm 路径、柔顺阵列或十字对爪条件下给出相反结论。
- **表面冲突 1：** 原文“捕获概率与韧度无关”只指几何筛选；现行“抓附”包含摩擦、平衡、材料和针体安全。统一事件名称后即消失。
- **表面冲突 2：** 原二维 Mode-II 裂面与 proposed 混合模态面片不是两个互斥定律，而是不同维度和闭合程度；前者公式尚不自洽，不能据此否定后者。
- **表面冲突 3：** 原文用刺体上限“截断”表面承载，accepted A 禁止无解释标量 `min`；两者物理意图一致，A 只是用两个事件面及重平衡保留并发/先后。
- **表面冲突 4：** accepted A 的连续再搜索会漏掉真实跳跃，但其适用域已排除惯性/冲击且风险已登记；这是已知模型范围差异。FORMAL 的“无扫掠路径则停在释放点”应保持为实现安全边界。

## 4. 漏掉的关键结论与 proposed 补充项

| 建议进入层级 | 建议身份与最小内容 | 适用条件与验证义务 |
|---|---|---|
| A 事件/验证章节 | `LOCAL_STRESS_EXCEEDANCE_IS_NOT_RELEASE` 负向回归：材料起始只能触发完整重求，不能直接置 `OPEN`。 | 硬脆基底；构造局部应力越限但整体仍有合法平衡的案例，并与逐事件一侧状态核对。 |
| A 材料可选模型 | `brittle_asperity_fracture_candidate`：三维裂面/凸体几何、混合模态容量和地形更新策略分栏；身份只可为 proposed optional model。 | 必须先有量纲闭合、真实裂面尺度桥、功共轭分离、红砖局部试验和网格客观性；否则保持 unavailable。原 Eq. (1) 不得作为默认实现。 |
| validation/统计输出 | 分开 `geometric_candidate_event`、`load_bearing_engagement_event`、失败/零质量和条件正值 \(F_{peak}\)；比较 Log-Normal、Weibull 等而不预设赢家。 | 冻结成功定义、0.2 N 等阈值的身份、删失/近零规则；以整条轨迹/表面留出，报告校准与覆盖，不把单刺分布 IID 复制到 B/C。 |
| A search/output schema | 增加 `nominal_search_distance`、`effective_contact_search_distance`、`skipped_span_after_release`、`recontact_model_status`。 | 准静态连续、过阻尼扫掠和真实跳跃必须不同 model ID；用高速影像/位移同步实验验证跳跃长度和再接触位置。 |
| Surface/A1 | 可选 `surface_layer_stack` 与可达性状态：层厚、刚度/黏性类别、刺尖是否能到达承载层；硬化层可成为新 surface realization。 | 仅在存在覆盖层时启用；需层厚/刚度/穿透试验。不可用单一摩擦系数模拟软层完全阻断。 |

## 5. 明确不可直接移植

1. Eq. (1) 临界剪应力、Eq. (2) 的 \(A\approx L_f^2\) 和二维 Eq. (3) 摩擦角；前两者分别量纲错误/三维尺度未经验证，后者依赖二维纯切向定义（`.../evidence_card.md:80-116`）。
2. Eq. (4) 的 \((v,w,t)\)、Eq. (6) 的 \((m,n,p)\) 及其函数形式；拟合域、单位缺口与负概率问题已记录（`.../evidence_card.md:118-140,153-154`）。
3. \(\mu_s=0.39\)、\(K_{IIc}=4.2/8.0/16.2\ \mathrm{MPa}\sqrt m\)、\(R_a=6.73\)–34.59 μm、\(d=0.1\)–10 mm；它们是钢—砂岩引用值或二维合成轮廓域，不是红砖实测（`.../evidence_card.md:146-152`）。
4. Rock A/C 的 2.45–2.68 N 实测均值、仿真 2.97–7.3 N 和 0.2 N 捕获阈值；模型系统性高估且阈值属于该实验统计定义（`.../evidence_card.md:158-159,174-178`）。
5. “Log-Normal 是最终分布”及“Bernoulli + Log-Normal”联合模型；原文零/失败处理不清楚（`.../extraction_audit.json:218-220`）。
6. 13.2/33.81/32.88 μm 磨损半径与磨损演化；现行首版明确排除针尖磨损（`.../evidence_card.md:155-156`; `theory/modules/A_INTEGRATED_MODEL.md:83-85`）。
7. 任意阵列独立性、载荷共享参数或 C 层能力结论；本文只验证孤立刺，实验边界也不代表柔顺阵列/对爪（`.../evidence_card.md:212-213,221-226`）。

## 6. 优先级与置信度

- **P0｜高置信：** 无新增真冲突；继续执行现有安全门——不得编码 Eq. (1)，材料定量分支在功共轭、尺度桥和参数未闭合时保持 `unavailable/no_damage`。
- **P1｜高置信：** 把“局部材料起始不等于释放”加入事件回归；加入有效搜索距离/跳过区间和 `RECONTACT_DYNAMICS_EXCLUDED`，避免准静态连续搜索给出乐观捕获机会。
- **P1｜中高置信：** 增加覆盖层可达性模型接口与分层统计输出；二者均先作为 proposed schema/验证义务，不进入 accepted 参数。
- **P2｜中高置信：** 以 \(R\)、可信粗糙尺度、观察行程和表面/刺体主导模式切换做趋势验证；Log-Normal 只作为候选分布比较。
- **P2｜中置信：** 研究三维脆性凸体裂面可选后端；本卡足以给方向，不足以冻结本构。
- **P3｜高置信：** 原论文所有拟合系数、材料数值、实验均值和磨损半径仅保留为复现/数量级对照，不进入项目参数表。

**最终结论：** 该卡最强的作用不是提供一个可编码的断裂公式，而是约束事件语义：局部越限、材料损伤、整刺释放和再挂接必须分开。现行完整机理已正确覆盖这一主干；真正的遗漏集中在失接后的有效搜索、覆盖层接触可达性和单刺随机输出解释。三者可补充，但都必须保持 proposed/validation 身份，不能由本卡自动升级为 accepted 物理或工程参数。

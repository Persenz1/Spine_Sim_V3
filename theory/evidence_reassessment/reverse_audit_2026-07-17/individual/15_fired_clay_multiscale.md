# 15 — fired clay multiscale 反向审查

**状态：** non-normative reverse-audit working material
**审查对象：** Buchner (2022) 烧结黏土砖多尺度形貌—刚度—强度证据卡
**结论摘要：** 未发现同对象、同假设、同适用域下的真冲突。文献对“内部多尺度形貌决定方向刚度”“结合基质压力敏感首次失效”提供支持；现行 accepted A 已保留材料方向、压力敏感 Mohr–Coulomb 和参数不可用边界。主要遗漏是显式的内部形貌/RVE 参数层、预存缺陷状态、跨尺度辨识与多轴验证义务。最关键的未闭合项仍是尖端非均匀接触场到 RVE/结合基质平均应力的尺度桥；该文献本身也没有给出这座桥，且不能支持现行峰后软化、断裂能或循环损伤。

## 1. 身份、提取完整性与适用域

- 卡片对应 880 °C 烧结挤出黏土砖，研究链为多技术形貌表征、两级 Mori–Tanaka 均匀化、结合基质 Mohr–Coulomb 首次失效及 FE/多轴验证；身份与相关性见 `theory/evidence_reassessment/literature/15_fired_clay_multiscale/evidence_card.md:3-10`。
- 提取审计覆盖论文全部 144 页，九张 contact sheet 全页目检，并对关键公式、表格和 17 个页面做 260 dpi 复核，状态为 `PASS_WITH_WARNINGS`；见 `theory/evidence_reassessment/literature/15_fired_clay_multiscale/extraction_audit.json:8-27`、`:285-295`。本审查另目检了 Fig. 5.1、5.7、5.12（卡片锚点分别为 `evidence_card.md:198-208`），图中分别确认两级 RVE/ODF、方向压痕卸载包络和归一化三轴子午线。
- 适用域必须收窄：七种砖覆盖的是方向刚度；强度常数只反辨识自一种 880 °C 参考钙质砖；外部多轴砖缺微结构输入且按各自单轴抗压强度归一化。模型只给比例加载下首次失效，不给峰后、裂纹路径、压碎或循环历史；见 `evidence_card.md:221-226` 与 `extraction_audit.json:265-282`。
- B/C/System 不重建低层材料本构：A 是局部柔顺、材料容量和损伤的唯一所有者，B/C 只调度、装配和传播事件；见 `theory/modules/B_INTEGRATED_MODEL.md:77-84`、`theory/modules/C_INTEGRATED_MODEL.md:1620-1625`、`theory/system/SYSTEM_INTEGRATED_MODEL.md:264-274`。因此 M1–M6 的实质比对集中于 FORMAL 与 accepted A，B/C/System 只检查越权和状态传播。

## 2. 逐项结论表

| # | 文献原结论与本地来源 | 现行机理对应位置 | 分类 | 判定、优先级与置信度 |
|---:|---|---|---|---|
| 1 | 外表面粗糙地形与内部孔隙/物相形貌必须分开，内部形貌不能替代表面三维地形；`evidence_card.md:212-217`、`:226-230`。 | `SurfaceRealization` 独立拥有原始几何，材料历史另存于 DamageStore；`theory/modules/A_INTEGRATED_MODEL.md:300`、`:414-428`。 | `supported` | 架构边界一致；文献支持分层方向，不支持任何表面几何参数。P3，高置信度。 |
| 2 | M1：微尺度“结合基质+微孔”和介尺度“泡沫基质+介孔+矿物”两级 RVE，以体积分数、长宽比和 ODF 传递响应；`evidence_card.md:19-28`、`:99-111`，Fig. 5.1 锚点 `:198-200`。 | FORMAL 只把无损容量抽象成 \(\mathcal C_{0,k}\)；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:889-905`。A 面片仅保存面积、深度、核、材料方向与参数；`theory/modules/A_INTEGRATED_MODEL.md:812-815`。 | `supplement_candidate` | 完整机理没有显式内部形貌/RVE 参数包。建议新增可选 `brick_microstructure_model_id` 与相分数、ODF、尺度有效性元数据，不得写入 SurfaceRealization。P1，高置信度。 |
| 3 | M1/V2：两级均匀化可在完美黏结、尺度分离、预失效线弹性下预测方向刚度及相应力集中；`evidence_card.md:22-27`、`:99-111`、`:178-182`。 | A 只允许“独立标定”的局部法向压缩 \(c_n(\lambda_n)\)，主线为刚性接触；`theory/modules/A_INTEGRATED_MODEL.md:543-572`，FORMAL 的 M0 明取 \(c_n=0\)，`theory/paper/MECHANISM_DERIVATION_FORMAL.md:519-544`。 | `supplement_candidate` | 等效方向刚度可作为 `c_n`/局部 FE 的先验或验证目标，但不能把 Mori–Tanaka 宏观刚度直接当微接触刚度；论文介尺度分离仅约 2–3，尖接触更弱，见 `extraction_audit.json:265-267`。P2，中高置信度。 |
| 4 | M2：挤出取向使 \(x/y\) 与 \(z\) 方向刚度和强度不同，近似横观各向同性但可能有轻微正交差异；`evidence_card.md:30-39`。 | A 显式保存材料方向 \(R_{m,k}\)、方向映射 \(\mathbb H_k\)，并在材料坐标中判失效；`theory/modules/A_INTEGRATED_MODEL.md:866-880`。 | `supported` | 支持“必须保留材料方向”这一建模结论；不支持当前任意 \(\mathbb H_k\) 的具体形式或参数。内部材料方向还应与外表面 PSD 各向异性分开。P2，高置信度。 |
| 5 | M3：大石英热失配界面裂纹降低有效承载相比例和刚度；10 µm 零刚度阈值只是该样本的经验硬阈值；`evidence_card.md:41-50`。 | A 的 DamageStore 是接触过程中的容量历史，且损伤不改原始地形/结构参数；`theory/modules/A_INTEGRATED_MODEL.md:969-991`。B 也禁止无证据同步降低其他参数；`theory/modules/B_INTEGRATED_MODEL.md:969-979`。 | `supplement_candidate` | 这是“制造后预存内部缺陷”与“接触诱发演化损伤”的范围差异，不是真冲突。建议用独立 `initial_material_state/defect_state_id` 影响有效刚度、\(\mathcal C_0\) 或 \(c_n\)，不要伪装成 DamageStore 已演化量；10 µm 不移植。P1，高置信度。 |
| 6 | M4/E3：结合基质空间平均主应力按拉正压负的 Mohr–Coulomb 等式定义首次失效；`evidence_card.md:52-61`、`:113-125`。 | accepted A 采用相同符号的压力敏感 Mohr–Coulomb，并允许拉伸截断/经数据启用压帽；`theory/modules/A_INTEGRATED_MODEL.md:853-903`。 | `supported` | 压力敏感、方向相关的首次失效建模方向一致；附加拉截断/压帽是更广模型，不与论文冲突，但需各自证据。P1，高置信度。 |
| 7 | E4–E5：论文先以 RVE 宏观应力 \(\Sigma\) 经两级应力集中张量得到结合基质平均应力；尖端场如何体积平均未定义；`evidence_card.md:127-149`、`:214-215`、`:223-224`。 | A 直接以面片合力/面积构造应力代理，再施加 \(\mathbb H_k\)；`theory/modules/A_INTEGRATED_MODEL.md:853-875`。FORMAL 已声明材料扩展需尺度桥，缺失时 unavailable；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:13-15`、`:1021-1027`、`:2089-2091`。 | `insufficient_evidence` | 不能把 \(\mathbb H_k\) 等同于论文的 \(\mathbb B_{bm}\)，也不能宣称 A 的面片应力就是 RVE/相平均应力。需新增 `contact_to_RVE_bridge` 接口与体积/窗口收敛验证；在此之前维持 unavailable。P0，高置信度。 |
| 8 | M5/V3：宏观弯拉和单轴压缩可经下尺度反辨识 \(c_{bm},\phi_{bm}\)，再用两方向纳米压痕卸载曲线独立校核；`evidence_card.md:63-72`、`:184-188`，Fig. 5.7 锚点 `:202-204`。 | FORMAL 明确单一拖曳曲线不能唯一辨识局部强度/断裂参数；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:2031-2061`。A 当前关闭条件要求局部压入/剪切/混合和方向试验；`theory/modules/A_INTEGRATED_MODEL.md:1805-1815`。 | `supplement_candidate` | 可补充为“宏观反辨识 + 微观方向校核 + 留出验证”的候选标定路线，而非只靠单刺拖曳；必须使用目标砖形貌/弹性输入并报告可辨识性。P1，高置信度。 |
| 9 | M6：下尺度 MC 生成压力敏感、近五棱锥的方向相关多轴首次失效面；`evidence_card.md:74-83`。 | A 以方向 MC/拉截断/可选压帽构造 \(\mathcal C_{0,k}\) 和射线利用率；`theory/modules/A_INTEGRATED_MODEL.md:875-916`。 | `supported` | “法向—剪切组合不能用单一无压敏阈值代替”已被现行容量域覆盖；论文只支持比例加载首次达到，不支持非比例历史和峰后面演化。P2，高置信度。 |
| 10 | V4：归一化三轴两路径与预测子午线相符，双/单轴压强比给出有限验证；`evidence_card.md:190-194`，Fig. 5.12 锚点 `:206-208`；但验证砖缺微结构且只验证归一化形状，`extraction_audit.json:275-277`。 | A 的材料验证目前只列 KKT、断裂能和客观性；`theory/modules/A_INTEGRATED_MODEL.md:1739-1750`。System 只给一般趋势/排序验证；`theory/system/SYSTEM_INTEGRATED_MODEL.md:2165-2178`。 | `supplement_candidate` | 增加“方向单轴点、比例双/三轴路径、归一化形状与绝对强度分栏”的验证义务；不能据此宣称跨砖绝对强度通过。P2，高置信度。 |
| 11 | 文献只预测首次失效，不含峰后软化、断裂能、裂纹路径、压碎、循环损伤和再分配；`evidence_card.md:58-60`、`:80-83`、`:219-225`。 | FORMAL 的 M1 另含残余容量、混合模态断裂能、牵引分解和软化耗散；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:907-1027`。verification 也判定缺功共轭运动学、只能 no_damage/uncertified fixture；`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:242-263`。 | `insufficient_evidence` | 这是机理范围扩展而非反向冲突；本卡不能为 \(G_c,\rho\)、cohesive 分支、DamageStore 核、峰后或循环规律背书。P0，高置信度。 |
| 12 | 卡片列出的相分数、模量、RVE 尺度、10 µm 阈值、\(c_{bm}=37.59\) MPa、\(\phi_{bm}=33.14^\circ\)、宏观/剪切强度均属于特定砖或模型输出；`evidence_card.md:151-168`、`:210-217`。 | System 要求材料/接触/损伤/强度参数均带版本 ID，缺失写 `unavailable`；`theory/system/SYSTEM_INTEGRATED_MODEL.md:1825-1852`，局部强度等仍未标定，`:2197-2202`。 | `insufficient_evidence` | 所有数值禁止直接复制为目标红砖或微接触参数；只能作 DEV_PRIOR 数量级/趋势并单独标识来源。P0，高置信度。 |
| 13 | V1：MIP 测孔喉并低估真实孔径，micro-CT 有体素/连通阈值，需与 SEM 组合才覆盖跨尺度真实孔径；`evidence_card.md:170-176`。 | 现行质量字段主要针对外表面 realization 的可信带/测量元数据；`theory/modules/A_INTEGRATED_MODEL.md:414-428`，System 的 U-SYS-009 也指外表面 PSD，`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198`。 | `supplement_candidate` | 新增独立 `internal_microstructure_quality`：测量模态、分辨率、孔喉/孔体口径、配准和跨模态一致性；不得并入外表面几何质量。P2，高置信度。 |

## 3. 真冲突与表面冲突

**真冲突：0 项。** 没有证据表明现行机理在论文相同对象、线弹性/RVE 假设和首次失效适用域内给出相反结论。

表面上有三处不一致，但均属范围差异：一是 M0 的刚性接触/`no_damage` 与论文的弹性均匀化/首次失效不同，然而 M0 明确是开发基线，材料分支另列 unavailable（`MECHANISM_DERIVATION_FORMAL.md:2085-2098`）；二是论文的结合基质平均应力与 A 的面片应力代理并非同一尺度，尚不能比较；三是论文的大石英预存界面裂纹降低刚度，而 DamageStore 描述接触过程中的容量历史。只有未来把后二者声明为同一物理状态且仍强制“损伤不影响局部刚度”时，才会形成真正冲突风险。

## 4. 被漏掉的关键结论与建议补充

1. **P0 — `contact_to_RVE_bridge`（必需接口/验证义务）：** 明确输入应力场或控制体、平均窗口、尺度分离检查、材料方向、\(\Sigma\rightarrow\sigma_{bm}\) 映射及不确定性；尖端场未收敛到 RVE 平台时返回 unavailable。论文只提供 RVE 内下尺度，不提供接触到 RVE 的前半桥。
2. **P1 — `brick_mc_multiscale`（可选材料模型）：** 在 FORMAL 的 \(\mathcal C_{0,k}\) 下登记两级形貌—方向刚度—结合基质 MC 的显式候选身份；前置条件为目标砖相形貌/相刚度、完美黏结或版本化缺陷分支、预失效线弹性及比例加载。
3. **P1 — `initial_material_state`（参数先验/状态字段）：** 把制造热历史导致的预存孔隙、界面裂纹和非承载相与接触诱发 DamageStore 分开；允许它们影响有效方向刚度、应力集中和无损容量，禁止用 10 µm 通用阈值。
4. **P1 — 分层辨识协议（标定流程）：** 宏观弯拉/压缩反辨识仅作候选，必须由方向纳米压痕和留出多轴路径交叉校核；同时报告绝对强度与归一化失效面形状，避免把跨砖形状验证误写成绝对参数迁移。
5. **P2 — 内部形貌质量与输出字段：** 保存 `internal_morphology_id`、相分数/长宽比/ODF、测量模态与分辨率、`scale_separation_status`、`bridge_validity`、`failure_surface_validation_mode`；与外表面 realization、摩擦和地形质量严格分栏。

## 5. 明确不可直接移植

- 不移植 10 µm 大石英“刚度置零”阈值、参考砖相分数/ODF/RVE 尺度、方向相模量和七砖超声刚度；它们最多形成目标砖表征前的宽先验。
- 不移植 \(c_{bm}=37.59\) MPa、\(\phi_{bm}=33.14^\circ\)、23.10/74.29 MPa 拉压强度或 17.4–17.6 MPa 预测剪切强度；它们不是目标砖局部接触参数，且部分为反辨识/模型输出。
- 不把 Mori–Tanaka 等效刚度直接写成 \(c_n(\lambda_n)\)，不把 \(\mathbb B_{bm}\) 直接替代 A 的 \(\mathbb H_k\)，也不把宏观强度当面片牵引阈值；均需目标砖数据和接触—RVE 桥。
- 不从该文献导出 \(G_c\)、残余容量 \(\rho\)、软化形状、裂纹扩展、压碎、划伤、循环损伤或速率参数；这些内容在原证据适用域之外。

**总优先级：** P0 先保持材料定量分支 unavailable 并关闭尺度桥/参数误迁移；P1 再增加显式砖材候选子模型、预存缺陷状态和分层辨识；P2 补内部形貌质量与多轴验证；P3 仅保留已支持的架构边界，无需改 accepted 1.0。

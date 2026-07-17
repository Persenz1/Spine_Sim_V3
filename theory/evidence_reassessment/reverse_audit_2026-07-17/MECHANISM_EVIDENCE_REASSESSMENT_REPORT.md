# 29 组原始文献卡对现行完整机理的反向审查总报告

**状态：** non-normative evidence reassessment report
**日期：** 2026-07-17
**审查规模：** 29 个独立逐卡审查 + 3 组跨卡去重汇总
**主审对象：** `paper/MECHANISM_DERIVATION_FORMAL.md`，版本 `0.1.0-proposed`
**规范基线：** accepted `SYSTEM_INTEGRATED_MODEL` 与 A/B/C 集成模型
**处置边界：** 本报告不修改 accepted 1.0，不把文献数值提升为项目参数，也不解除任何现有合同阻断。

## 0. 结论先行

| 用户关心的问题 | 总结论 | 当前处置 |
|---|---|---|
| 推导后的完整机理是否与原始文献卡冲突？ | 对 `FORMAL 0.1.0-proposed`，29 卡均未发现新增、未修复的同对象/同假设/同适用域真冲突。 | 保留 proposed 身份，不据此自动升级 accepted。 |
| accepted 1.0 是否有文献暴露的冲突？ | 有 1 项条件性真冲突：accepted 旧语义若把 `MATERIAL_FULL_FAILURE` 解释为 Mode-I 完全分离，却仍保留非零残余容量，则与零牵引物理分离不相容。独立复核已发现，FORMAL 已修复。 | 作为下一版 accepted 修订项，不能继续混用“完全失效”和“残余入口”。 |
| 是否漏掉原始文献的关键结论？ | 有。遗漏主要集中在表面数据契约、搜索/再挂接统计、释放回位物理路径、材料尺度桥与模式分栏、阵列诊断、执行器功边界和验证负例，而不是核心平衡符号。 | 形成 proposed 补充包和验证义务。 |
| 是否有可补充现行完整机理的内容？ | 有，但多数应进入模型身份、输入/输出 schema、验证矩阵或未来可选分支；没有证据支持直接替换 Signorini–Coulomb、共同平衡或六维 wrench 主链。 | 按 P0/P1/P2 分层，先补安全门与验证，再讨论新本构。 |
| 文献参数能否直接采用？ | 不能。29 卡中的摩擦、刚度、角度、载荷、形貌、韧度、概率和样机性能均有材料、尺度、硬件或控制域限制。 | 只允许弱先验、回归 fixture 或趋势验证，并保留来源/适用域。 |

最重要的总体判断是：**现行主链没有被文献推翻，但“完整机理”仍不是“完整证据闭合”。** FORMAL 自己已明确 `M0=no_damage`、条件材料扩展和 C 合同阻断（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:3-15,2083-2098`）；本轮文献卡复核支持继续保持这些边界。

## 1. 审查范围、方法与限制

### 1.1 输入

每个子代理独立读取：

1. 一组 `literature/<NN_...>/evidence_card.md`；
2. 对应 `extraction_audit.json`；
3. 必要的保留图片；
4. FORMAL、相关 accepted A/B/C/System 段落；
5. `DERIVATION_VERIFICATION_2026-07-17.md` 与必要的固定工程事实。

统一分类为 `supported / supplement_candidate / conflict / insufficient_evidence`。判定 `conflict` 时要求对象、硬件、材料、尺度、控制边界和适用域一致；二维降阶式被更一般的三维方程包络，不算冲突。

逐卡协议见 [REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md)，29 份详细报告见 [individual/](individual/)。

### 1.2 权威边界

- accepted System/A/B/C 仍是规范基线；
- FORMAL 是闭合修正版 proposed，不是 accepted 的静默替代；
- evidence card、提取审计和图片是非规范证据输入；
- 本轮没有回到归档 ZIP/PDF 源字节重新做全文提取。因而结论准确地表示“**现行机理与现有 29 组证据卡/审计/关键图的关系**”，不能替代正式 amendment 前的源文献复核。

### 1.3 成熟度边界

本轮只审查“理论/规范与文献证据是否相容”。它不证明：

- 求解器已经实现；
- 数值分支、事件和随机样本已经收敛；
- 参数已经识别；
- 目标红砖、混凝土或砂纸已经实验验证；
- C 偏心承载和正式 `F_crit` 已可执行。

该边界与独立复核的四级成熟度结论一致（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:32-41,449-465`）。

## 2. 冲突审计

### 2.1 FORMAL 0.1.0-proposed：新增未修复真冲突为 0

29 个逐卡报告均未发现 FORMAL 在共同适用域内给出与证据卡相反的物理结论。文献中的二维接触角、载荷比、镜像对置、等刚度换载、候选抓点和随机搜索模型，均属于以下之一：

1. 三维 SOC/Signorini 接触的受限特例；
2. 共同平衡在严格对称条件下的回归特例；
3. 只读统计或后处理模型；
4. 不同硬件、材料、尺度、控制方式或时间域；
5. 证据不足，不能进入本项目。

因此没有理由建立第二套经验接触律、固定载荷转移矩阵或旁路 C 合同的低维公式。

### 2.2 accepted 旧损伤终点：1 项条件性真冲突

卡 14 给出最明确的条件性冲突：在与该文同域的纯 Mode-I 开口分离中，法向黏聚牵引在临界开度处归零；accepted A/System 的旧状态若同时命名 `MATERIAL_FULL_FAILURE` 并允许 `q(δ_f)=ρ>0`，在同一 Mode-I 法向黏聚对象上语义不相容（[14 独立报告](individual/14_fired_clay_tuff_fracture_properties.md)，尤其第 5、20、36 行）。这不否定同位置压剪接触、摩擦或其他明确分栏机制的残余容量。

这不是 FORMAL 的新缺陷。独立复核已把它列为 P0-A3/A4（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:242-263`），FORMAL 已通过以下方式修复：

- `SOFTENING_COMPLETE/RESIDUAL_ENTRY` 与零容量失效分栏；
- 非零残余牵引另列功通道；
- 缺少真实位移跳量、尺度桥或残余功规则时返回 unavailable（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:945-1027`）。

正式处置仍需版本化 amendment；不能因为 proposed 已修复，就把 accepted 旧字段解释成已经迁移。

### 2.3 文献强化的既有闭合问题

这些不是新增文献冲突，但文献显著提高了其优先级：

1. **A 姿态类型。** 方向性/俯仰/偏航文献说明姿态误型会直接污染趋势；应先采用 FORMAL 的全局转角左乘闭合，再做角度研究。
2. **释放后的物理回位。** 状态机虽允许释放/再挂接，但瞬时把梁、弹簧和接触压缩投影回零不能代表真实回位。多卡支持显式卸载、拔出、离壁和再接触路径；FORMAL 已要求未实现扫掠路径时停在释放 pose（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1904-1906`）。
3. **损伤几何。** 脆性凸体脱落或微损伤可能改变有效支持点/法向。当前 `M0=no_damage` 无冲突；若未来声称 FORMAL-M1 完整覆盖硬脆损伤，则必须增加只读原表面上的版本化 `DamageGeometryOverlay` 或返回 unavailable。
4. **B 曲线事件与经验分载。** 文献支持事件后重求平衡；任何固定邻接、平均换载或“失效载荷包”只能作严格受限回归，不能替代 B 的全量重求。
5. **C-R/C-I 与执行器功边界。** 文献强化了执行器几何和力臂的重要性；端点、源/目标体、作用线、传动坐标和功恒等则是 FORMAL/独立复核提出的项目规范闭合要求。两种边界互斥：C-R 是共同刚体 pose + 共同 `s`，各 `u_zi` 由运动学导出，不能逐单元强制 `F_zi=P_i`；C-I 只有在四个独立 Z 执行器端点、行程和功均冻结后才允许独立 `u_zi/P_i`。FORMAL 对 C-R 的选择仍是 proposed，补齐 CAD/端口映射不会自动把 accepted C 的旧混合边界迁移成已认证模型。
6. **B→C 运动子空间。** 文献中的多方向抓持、偏航或被动腕不能解除 local-y/转动缺口。非零 +X、45° 或 rocking 请求必须在物理推进前返回 `C_CONTRACT_EXTENSION_REQUIRED` 并保持历史零推进；正式 `F_crit` 则保持 `null/unavailable`，不是零承载或已发生失效。

### 2.4 主要“表面冲突”其实是范围差异

- 生物足垫、多足主动控制 vs 工程单刺/同步对爪；
- stalk、通道限位、颗粒掌、腱索、四杆、双轨、被动腕、尾撑 vs 固定工程硬件；
- 软木/泡棉穿透 vs 当前硬粗糙面非穿透球冠；
- Persson 名义平面微接触、宏观砖梁 R-curve、RVE 平均应力 vs 针尖局部混合模态接触；
- 动态跳跃、振动、跌落和持载寿命 vs 当前准静态路径事件；
- 单刺、carriage、单元、整爪和整机“失效”聚合层级不同；
- 候选数、挂接概率、真实接触面积、承载针数、有效针数和能力域不是同一量。

## 3. 文献共同支持的现行主链

跨卡反复得到支持的不是某个经验常数，而是以下结构：

1. **有限尖端与真实三维形貌。** 有限球尖会过滤不可达小尺度特征，局部法向和搜索方向共同决定可用支持；单一 `Ra/Sa` 或 grit 不足以表示啮合。
2. **Signorini–Coulomb 主链。** 文献二维摩擦自锁式可作为受限解析回归，不能替代三维多支持 SOC/graph。
3. **分层柔顺与共同兼容。** 独立柔顺可以提高搜索和分载，但载荷仍应由逐针本构、共同位姿与总平衡共同决定，而不是经验均载。
4. **事件后重平衡。** 首针/首瓦片释放不自动等于整体失败；应切换分支、全量重求、再判断稳定和可恢复性。
5. **历史与再挂接。** 搜索、伪挂接、释放、再捕获、过载和表面/针状态具有路径依赖；新的独立试验才允许重置历史。
6. **对置预载与完整 wrench。** 内部预载能改变方向能力和稳定裕度，偏心加载必须同时闭合力与力矩。
7. **参数和证据边界。** 其他样机/材料的公式和数值不足以关闭本项目参数；实验原始量、模型身份和适用域必须保留。

## 4. 漏掉或仅隐含的关键结论

### 4.1 表面 realization 的“证据合同”尚不完整

建议新增带 `surface_source_kind = synthetic/measured` 条件分支的 `SurfaceGenerationAndAcquisitionContract`，至少覆盖：

- **共同字段：** 坐标/单位、区域尺寸、方向、PSD convention、可信波数带、方向谱、roll-off、非高斯高度边际、宏观缺陷标签和原始身份 hash；
- **合成表面分支：** FFT 归一化、Hermitian 配对、零模、seed、周期域及目标/回算 PSD、方差和实值误差；
- **实测表面分支：** 仪器原理、探针半径/形状或 MTF/SNR、原生点距、配准误差、陡坡漏检/窄谷不可达，以及每个方向可信截止及其证据。原生点距或厂商最高分辨率不得等同物理分辨率；
- **预处理可追溯性：** 去趋势阶次、插值、滤波、窗函数、缺失掩膜和可回放处理链。插补值不得视为恢复的真实形貌，原缺失掩膜必须永久保留，并对 PSD、法向、曲率、事件和下游接触输出做方案敏感性分析；
- **显式尺度描述：** 扫描范围、滤波截止/长度；任何 RMS 粗糙度都必须携带尺度，优先保存 `h_rms(L)` 或等价尺度曲线；
- **代表性与异原理复测：** 多位置、方向、批次、缺陷分层与留出区域，以及技术内/技术间 PSD 分布、分歧标记和不确定带；多数技术不得自动充当物理真值；
- **针尖尺度 QA：** 50/100 μm 针尖相对于可信最短波长和有限尖端可达形貌的覆盖裕度。该量只是必要输入质控，不能替代球包络、支持认证或下游输出收敛，更不能单独称为“可抓”判据。

该补充由 01/02/08/11/12/16/22/24/26 多卡共同支持，但它提升的是输入与验证规范，不是红砖接触参数。

### 4.2 搜索、挂接与再挂接需要可观测统计

建议把术语和输出分成：

`geometric_candidate → contact_loaded → frictionally_stable → load_bearing → released/reengaged`。

可增加：

- 首次承载距离的“零距离点质量 + 条件尾部 + 右删失”可选统计；
- 名义搜索距离、有效接触搜索距离、跳过区间和再捕获距离；
- 伪挂接次数、持续距离和分支；
- 条件正峰值分布与未挂接/零质量分栏；
- 单刺统计的相关性检验，明确禁止 IID 直接乘算阵列成功率。

这些都是 ensemble/validation 后处理，不能反馈成逐针经验权重。

### 4.3 释放/拔出是路径，不是状态瞬时投影

多卡支持把卸载、drive-off/解锁、反向搜索或 lift-off、扫掠碰撞、再接触 guard、事件定位、功和历史保留组成显式操作协议。建议由 C/System 编排外部操作路径，A 执行低层接触释放、碰撞与再接触；没有该路径时沿 FORMAL 的安全边界终止当前承载分支。

### 4.4 材料扩展缺少统一尺度桥和模式身份

启用任一 FORMAL-M1 分支时，共同硬门是：真实局部化运动学/位移跳量、与所选模型匹配的 `contact_to_material_bridge`、明确模式和目标材料参数、能量/客观性，以及版本化软化形状与卸载/重载身份。`contact_to_material_bridge` 再按 model ID 分为 `cohesive_interface`、`continuum_RVE`、`resultant_capacity` 等；并非所有材料分支都必须经过 RVE。

分支涉及下列现象时，还必须闭合相应子集：

- `initial_material_state`（制造后孔隙/界面裂纹）与接触诱发 `DamageStore` 分离；
- 压密/压碎、拉裂、侧裂/剥落、凸体断裂、针体屈服/断裂和摩擦滑移分栏；
- `COF_app` 与 `μ_Coulomb` 分栏；
- AE、显微前后图、力—位移等多证据裁决，AE 阴性不得单独推出无裂纹；
- `observed_FPZ_extent`、物理面片尺度、损伤核和数值网格分栏；
- 起裂阻力与扩展 R-curve 的模态/尺度有效域；
- observation operator：实验测量基距、弹性伸长、真实裂纹开度、仿真内部 `δ_d` 与局部跳量不得混名；
- 材料类型/来源批次/试样层级 provenance、不确定度和目标材料后验更新。宏观 `G_F/CoV` 只能作弱先验。

卡 14 只直接识别临界开度，所用双线性软化形状仍来自外部混凝土模型，也没有识别完整卸载/重载律；能量面积闭合不能被解释成整条本构已识别。若共同硬门或所请求分支的必要子集未闭合，`M0=no_damage` 仍可执行，但该 M1 分支必须返回 unavailable。

### 4.5 阵列需要能力—载荷对齐与双侧裕度诊断

建议增加只读诊断：

- `N_nominal / N_candidate / N_contact / N_load / N_eff` 分栏；
- 最大/平均、CV/Gini、方向离散、区域力比—面积比；
- `load_capacity_alignment`，检查自然平衡是否把载荷落到更强/更硬接触；
- 欠接合裕度、过利用裕度、最弱针/单元和剩余行程；
- 回差、刚度窗口、针数×覆盖面积×间距×预载的联合 DOE；
- 位姿/接触位置误差扰动、condition、分支切换率和置信区间。

这些量不能反向成为经验分载权重。

### 4.6 C/System 需要硬件边界与上层诊断，而不是文献样机公式

FORMAL 已定义 `(q_C,s)→` 单元 twist 的 `J_i` 及其 wrench 对偶装配；真正待补的是项目硬件输入端：

- 电机/传动坐标到共同 `s` 的映射；
- 执行器端口/作用线到 active generalized wrench 与功的映射，以及双端、源/目标体和保持反力；
- 四方向单元的力/侧向力/力矩贡献；
- 状态局部最小 `attachment_margin_LB`；
- 未来机器人层的支撑集、抓取映射秩和单爪丢失后可恢复性接口。

C-R/C-I 的互斥边界和 proposed/accepted 身份保持第 2.3 节所述；完成上述硬件映射仍需版本化 amendment、实现和验证，不自动完成规范迁移。

足间反馈、零空间内力控制或保守整机停机规则只能位于上层控制/支撑拓扑，不能替换 B 的物理重平衡。

### 4.7 物理时间和穿透都必须是显式可选模型

- 若研究恒载寿命，应新增 `DWELL/HOLD`、危险量、预测失效时刻、竞争风险与有限时间传播；同位置级联轮数不能冒充传播时间。
- 穿透型抓附必须使用独立 model ID，与 `NONPENETRATING_ROUGHNESS_HOOKING` 互斥；软木/泡棉参数不得进入当前硬表面模型。

两者当前均无目标实验闭合，应保持关闭。

## 5. 合并后的补充优先级

### 5.1 P0：保持或关闭安全门

| P0 安全门 | 来源卡 | 建议处置 |
|---|---|---|
| accepted Mode-I 终点语义修订 | 14 | 与卡 14 同域的纯 Mode-I 开口分离，其法向黏聚牵引归零；压剪/摩擦等非零残余另列状态、机制和功通道。 |
| FORMAL-M1 启用门 | 05/06/11/13/14/15/24/25/27 | 局部化运动学、适当的 material bridge、模式、目标材料参数、能量/客观性及版本化软化/卸载身份缺一即该分支 unavailable。 |
| A 姿态类型与 B 曲线事件等既有 P0 | 01–10 多卡 | 先按 FORMAL 闭合并版本化迁移，不以文献趋势代替修订。 |
| 经验分载防火墙 | 07/09/19/22/23/25/29 | 固定邻接、平均力、等增量只能作严格受限回归，不得替 B 全量重平衡。 |
| C 执行器功边界 | 09/16/18/20 | 保留 C-R/C-I 互斥；电机/传动→`s` 与执行器端口→active wrench/功闭合并完成版本迁移前，真实 C 预紧不可认证。 |
| B→C 运动合同 | 04/16–21/28/29 | local-y/转动及非零 +X/45°/rocking 请求继续安全拒绝并零历史推进；正式 `F_crit` 保持 `null/unavailable`。 |
| 接触模式防串用 | 24/29 | 非穿透、穿透、材料黏附必须以 model ID 互斥。 |
| 公式/参数导入拒绝门 | 全部 | 排版歧义、量纲不闭合、对象/尺度/硬件不匹配时禁止实现或默认化。 |

本轮没有要求立即加入的新 P0 物理；P0 均是修复已知语义、保持阻断或防止误移植。

### 5.2 P1：建议形成下一轮 proposed 补充包

| P1 补充包 | 主要内容 | 建议层级 | 主要来源 |
|---|---|---|---|
| 表面生成/采集/预处理合同 | synthetic/measured 分支、PSD convention、物理分辨率证据、尺度化 RMS、缺失掩膜/预处理敏感性、异原理复测与不确定带 | A1 / SurfaceRealization / System validation | 01/02/08/11/12/16/22/24/26 |
| 搜索与挂接统计基线 | 点质量+条件尾部、删失、伪挂接、有效搜索、相关性 | A standalone / B validation | 01/03/05/08/09/17 |
| 显式卸载与再接触路径 | drive-off、lift-off、扫掠、guard、功和历史 | A driver + C/System operation | 03/05/08/16/17/20/21/22/23/29 |
| 材料尺度桥与模式分栏 | contact→material 子模型、位移跳量、软化/卸载身份、observation operator、初始缺陷、多模式、多证据与批次 provenance | A material / FORMAL-M1 / experiment | 05/06/13/14/15/20/27 |
| 阵列诊断与联合 DOE | 计数分栏、能力—载荷对齐、双侧裕度、回差、误差敏感性 | B output / validation | 03/06/07/10/17/19/21/28/29 |
| 执行器—`s`—wrench/功闭合 | 电机/传动→`s`、执行器端口/作用线→active wrench/功、保持反力 | C/System boundary | 09/16/18/20 |
| 负例和事件级验证库 | 细 grit 失配、7→6→7、首弱刺、镜像对置、主动卸载、点级命中 | A/B/C validation | 01/02/07/09/16/22/23 |
| 针/表面使用史 provenance | 针 ID、试验顺序、过载、前后半径/偏转、表面区域历史 | A parameters / experiment | 17/21/24/29 |

### 5.3 P2：条件性增强

- 方向接触角、切/法力比、凹形指标、候选密度、区域分载等只读派生量；
- Persson 连续接触诊断、空球 oracle、二维自锁和镜像对置等回归 fixture；
- 对置组贡献、closure/torsional margin 与压力中心分栏；
- 柔顺的载荷离散—位姿误差—有效刚度—余程多目标输出；
- 未来针残余几何、磨损、时间危险率、R-curve、穿透和机器人层控制接口；
- 新硬件（stalk、root flexure、carriage、被动腕、框架柔顺）只有在工程事实版本化改变后建模。

## 6. 29 卡逐项索引

| 卡号 | 冲突判定 | 最有价值的补充/边界 |
|---:|---|---|
| [01](individual/01_frictional_engagement.md) | FORMAL 真冲突 0 | 首次承载距离混合统计、负载荷自锁回归、有限半径尺度验证 |
| [02](individual/02_locust_grip_detachment.md) | 真冲突 0 | 尖端—特征尺度、细 grit 负例、生物多足/足垫混杂元数据 |
| [03](individual/03_compliant_directional_suspensions.md) | 真冲突 0；异构机构不可移植 | 回位路径、材料—摩擦消融、方向裕度；禁止 stalk/交叉刚度静默进入 |
| [04](individual/04_orientation_dependent_engagement.md) | 真冲突 0 | 姿态验证、偏航统计、B 2.x 横向一侧刚度 |
| [05](individual/05_isolated_spine_fracture_interlock.md) | 真冲突 0 | 局部损伤后仍互锁、覆盖层/跳跃有效搜索、条件承载分布 |
| [06](individual/06_soft_hard_array_scaling.md) | 真冲突 0；未来损伤几何为能力缺口 | `DamageGeometryOverlay`、阈值活动计数、数量—覆盖—柔顺消融 |
| [07](individual/07_linearly_constrained_spines.md) | 真冲突 0 | 回差、首弱刺/对置镜像回归、差动刺片仅作未来硬件 |
| [08](individual/08_compliant_microspine_arrays.md) | 真冲突 0 | 候选密度、伪挂接、测量带宽与尺度趋势验证 |
| [09](individual/09_stochastic_compliant_spine_arrays.md) | 真冲突 0 | 随机挂接基线、有限搜索、再挂接消融、对置预载切片 |
| [10](individual/10_soft_spiny_paw_load_sharing.md) | 真冲突 0 | 柔度窗口、能力—载荷对齐、区域分载；软掌硬件不移植 |
| [11](individual/11_randomly_rough_contact_mechanics.md) | 真冲突 0 | PSD 归一化、随机相位生成器、二维谱质控、条件多尺度诊断 |
| [12](individual/12_red_ceramic_blocks_roughness.md) | 真冲突 0 | 测量元数据、去趋势溯源、多尺度局部 QA、选区偏差 |
| [13](individual/13_cement_paste_micro_scratching.md) | 真冲突 0 | 作用尺度、损伤模式、COF/μ 分离、AE 多证据裁决 |
| [14](individual/14_fired_clay_tuff_fracture_properties.md) | FORMAL 新冲突 0；accepted 旧终点有 1 项条件冲突 | Mode-I 位移跳量、FPZ/正则化尺度分栏、批次离散 |
| [15](individual/15_fired_clay_multiscale.md) | 真冲突 0 | contact→RVE 尺度桥、内部形貌、初始缺陷、方向多轴验证 |
| [16](individual/16_grappling_claws_3d_wall.md) | 真冲突 0 | 扫描质控、空球 oracle、点级闭环、drive-off 边界事件 |
| [17](individual/17_beetle_claw_mechanical_gripper.md) | 真冲突 0 | 挂接平台统计、主动脱附、抗扭闭合、过载残余几何 |
| [18](individual/18_paired_claws_gecko_robot.md) | 真冲突 0；E1 转矩号/E2 下侧角号未闭合 | 执行器输入端映射、数量×表面验证、阶段脱附输出；0°–180°演示和样机载荷不能解除 B→C 阻断 |
| [19](individual/19_spinyhand_load_sharing.md) | 真冲突 0 | 能力—载荷对齐、病态敏感性、曲率×预载×柔顺 DOE |
| [20](individual/20_gravity_independent_microspine_grippers.md) | 真冲突 0 | 材料破坏/滑脱分型、主动脱离、柔顺—位姿多目标评价 |
| [21](individual/21_underactuated_adaptive_microspines_gripper.md) | 真冲突 0 | 实物交叉柔顺审计、搜索饱和、渐进脱附和高度失配诊断 |
| [22](individual/22_biologically_inspired_hexapedal_climbing.md) | 真冲突 0 | 接合协议、换位重试、双侧裕度、反馈消融 |
| [23](individual/23_dual_rail_spiny_climbing_robot.md) | 真冲突 0 | 主动拔出—离壁路径、7→6→7 对称回归 |
| [24](individual/24_penetration_based_clawed_climbing.md) | 真冲突 0；穿透属互斥模式 | 模式隔离、角度语义、`R_t×P_z` 非单调验证、针尖史 |
| [25](individual/25_time_dependent_fiber_bundles_local_load_sharing.md) | 真冲突 0；最近邻律不可进入 B | 条件持载时钟、危险率、有限时间级联和尺寸诊断 |
| [26](individual/26_surface_topography_challenge.md) | 真冲突 0 | 仪器传递能力、预处理回放、跨技术复测和尺度桥 |
| [27](individual/27_clay_brick_r_curve.md) | 真冲突 0 | 起裂/扩展阻力门、R-curve 有效域、DIC—载荷同步 |
| [28](individual/28_loris_lightweight_free_climbing_robot.md) | 真冲突 0 | 状态局部最小附着裕度、方向域、机器人支撑集接口 |
| [29](individual/29_wheeled_wall_climbing_robot.md) | 真冲突 0；标量拉脱律不可移植 | 角度×历史拉脱包络、模式门、双侧有效针诊断、未来 6D 根柔顺 |

## 7. 不可直接移植清单

### 7.1 数值与参数

不得直接采用文献专属的：

- 摩擦系数、速度、预载、针尖尺寸、安装角、刚度、行程和载荷；
- grit/粒径/粗糙度、PSD、相关长度、仪器分辨率和预处理常数；
- 文献稳健汇总/多数规则和样本规模（如 25%–75% IQR、每尺度箱 5 点、2088 次/64 组），它们不是红砖验收阈值或最低样本量；
- 水泥/砖/岩石的 `E, f_t, c, φ, K_c, G_F, R-curve`、硬度和残余容量；
- 挂接概率、Gamma/指数/Log-Normal 参数、ELS 指数、危险率参数；
- 样机承载、成功率、距离、速度、功耗、振动和整机性能；
- “最优角度/针数/行程/柔顺”经验结论。

### 7.2 公式与硬件模型

不得直接移植：

- 二维单支持式、镜像等载、固定邻接 LLS、经验换载矩阵；
- stalk、通道侧触、软掌/颗粒阻塞、腱—滑轮、四杆、双轨、carriage、被动腕和尾撑公式；
- Persson 名义平面公式作为爪刺承载律；
- 宏观 Mode-I/R-curve 或 RVE 平均应力作为针尖局部混合模态阈值；
- 生物多足主动控制或机器人整机停机规则作为针级本构；
- 排版、量纲、符号或可行侧未闭合的原式。

### 7.3 只能作为弱证据的内容

- 其他材料/硬件的数量级 sanity check；
- 受限解析回归和算法 fixture；
- 趋势或 DOE 假设；
- 未来硬件/控制架构的设计灵感；
- 需要目标表面、目标针尖、目标加载和留出实验重新标定的弱先验。

## 8. 必须统一的术语和字段

| 易混词 | 建议统一 |
|---|---|
| engagement/attachment/success | 分为 geometric candidate、loaded contact、frictionally stable、load-bearing、单元/整爪/整机 success |
| failure | 分为接触释放、滑移、材料起始、软化终点、零牵引分离、残余入口、针体失效、单元脱离、整爪不可恢复、机器人支撑集丢失 |
| load sharing | `equilibrium_redistribution`、`active_force_regulation`、`stochastic_LLS_fixture` 分栏 |
| compliance | 必须带所有者：contact、beam、axial mount、root flexure、frame/wrist、transmission |
| roughness | `profile_Ra`、`Sa`、PSD、局部残差、方向指标和可信带分栏 |
| contact count | candidate、contact、load-bearing、`N_eff` 分栏 |
| capacity | 材料容量域、局部 wrench graph、方向凸包、压力中心、整爪 `F_crit` 分栏 |
| damage | `initial_material_state` 与接触诱发 `DamageStore` 分栏 |
| COF/μ | `COF_app` 是状态相关力比；`μ_Coulomb` 是本构参数 |
| time cascade | 同位置零时间级联与物理危险率传播分栏 |
| α/β/γ/ρ/R | 使用带命名空间字段，避免安装角、力角、点质量、危险率、残余容量和 R-curve 碰撞 |
| P0 | 仅表示阻断性安全门；“文献支持”或“无冲突”不标 P0 |

## 9. 推荐的版本化处置路线

### 9.1 现在可以做

1. 保留 29 份报告和本总报告作为 non-normative evidence input；
2. 把 P1 内容整理成一个单独的 proposed “证据/输入/输出/验证补充包”；
3. 为现有 FORMAL 增加术语表、证据 provenance、负例回归和输出字段提案；
4. 在不启用新物理的前提下，准备表面数据合同与验证 schema；
5. 将 accepted 旧损伤终点的条件性冲突纳入正式 amendment 清单。

### 9.2 只有专项关闭后才能做

- 启用材料损伤、损伤几何或 R-curve；
- 启用持载寿命/危险率；
- 启用穿透型接触；
- 加入 root/frame/wrist 等新柔顺；
- 执行 C 非零 +X、45°、rocking 或正式 `F_crit`；只有版本化 B 2.x 正式 accepted，并完成实现、事件、功、事务和验证门槛后才可能解除相应阻断，文献样机的多方向成功不能升级合同；
- 把任一文献公式或数值提升为默认参数。

### 9.3 不建议做

- 直接把本轮补充拼入 accepted A/B/C/System；
- 用文献样机成功率或二维承载式声称目标机器人已验证；
- 用多数文献“投票”覆盖固定工程事实；
- 因 29 卡没有发现 FORMAL 真冲突，就把 proposed 宣称为 accepted、implemented、validated 或 certified。

## 10. 最终判定

1. **冲突：** FORMAL 0.1.0-proposed 新增未修复真冲突为 0；accepted 旧损伤终点在同域纯 Mode-I 法向黏聚分离解释下有 1 项条件性真冲突，且已由独立复核识别、FORMAL 提议修复；其他压剪/摩擦残余机制不在该判定内。
2. **遗漏：** 有，而且数量不少；但大多数属于证据合同、模型身份、状态/输出、统计后处理和验证义务，不是核心接触/平衡方程缺失。
3. **可补充：** 应优先补表面数据合同、显式卸载/再接触路径、材料尺度桥与模式分栏、阵列诊断、执行器功边界和负例验证库。
4. **不能补：** 不能直接移植任何论文专属数值、硬件公式、低维经验分载、宏观材料参数或整机控制规则。
5. **规范动作：** 本报告本身不改变现行规范；所有进入 accepted 的内容仍需独立 proposed amendment、审查、版本迁移和验证。

# 27 — 黏土砖 R-curve 文献卡反向审查

**审查对象：** *Measurement of R-curve in clay brick blocks using optical measuring technique*（2014，DOI `10.1016/j.engfracmech.2014.04.007`）
**报告身份：** non-normative reverse audit；不修改 accepted 1.0，不把文献经验值提升为项目参数。
**主审机理：** `theory/paper/MECHANISM_DERIVATION_FORMAL.md`（`0.1.0-proposed`）；以 system 与 A/B/C `1.0.0 accepted` 为规范基线。

## 1. 文献身份、提取完整性与适用域

该文研究七个带预裂纹黏土砖梁在三点弯曲下的宏观 Mode-I 裂纹扩展，并以 DIC、CMOD/CTOD 和载荷同步数据构建 R-curve；文献卡已明确它只能条件性约束单刺基材损伤，不能直接代表微尺度压缩—剪切—混合模态接触（`theory/evidence_reassessment/literature/27_clay_brick_r_curve/evidence_card.md:5–16`）。提取审计覆盖 PDF 全 10 页和全部实质章节（`extraction_audit.json:2–18`），Eq. (1)、(3)、(4) 已核，Table 1 已目视复核（`:20–52`）；Fig. 7 与 Fig. 9 已保留并在本次审查中查看，分别显示试样离散/数据缺口与稳定—失稳转折（`:54–63`）。状态为 `PASS_WITH_WARNINGS`（`:71–84`）：Eq. (2) 排印可疑，Eq. (3) 缺实际使用的 (E,\sigma_{ys})，孔隙—裂纹跳跃关联仅为作者推测，快速裂纹造成观测缺口，四阶拟合不是本构。

适用域严格限于厘米级直预裂纹梁、三点弯曲、LEFM、该批 26% 平均孔隙率黏土砖；爪刺问题则是局部非均匀压缩、剪切和混合模态。工程事实虽把红砖列为首版表面，但同时要求各材料走统一接口（`theory/evidence_reassessment/engineering_fixed_context.md:631–663`），并明确排除首版显式裂纹扩展有限元（`:1021–1033`）。

## 2. 总判定

**没有发现真实冲突。** 最接近冲突的是“R-curve 随裂纹增长而升高”与“局部容量随软化坐标下降”。二者不是同一状态量、尺度或模态：accepted A 排除显式裂纹（`theory/modules/A_INTEGRATED_MODEL.md:83–85`），proposed M1 也仅在功共轭和参数闭合后启用（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:13–15,78–103`）。只有把现行软化量称作黏土砖 R-curve，或把宏观 KIC 直接填入微刺阈值，才会制造冲突。

## 3. 逐项结论

| # | 文献原结论与本地来源 | 现行机理对应位置 | 分类 | 优先级 / 置信度与理由 |
|---:|---|---|---|---|
| 1 | M1：可靠段内 (K_I(a/W)) 总体随裂纹增长上升，约 (a/W=0.7) 达峰（`evidence_card.md:20–29,123–128`；`fig07_p07_r_curve_specimens.png`）。 | proposed M1 只有面片容量、单调软化坐标和 (G_c^{mix})（`MECHANISM_DERIVATION_FORMAL.md:889–967`）；accepted A 在起始时冻结失效模式与 (G_c^{mix})（`A_INTEGRATED_MODEL.md:916–991`），无裂纹长度/R-curve 状态。 | `supplement_candidate` | **P1 / 高**。可补“起裂阻力与扩展阻力不是同一量”的模型选择门；不得把梁尺度曲线直接变成本构。 |
| 2 | (a/W>0.8) 多已坍塌而不可靠，四阶拟合不得外推（`evidence_card.md:23–29,119,160,168`；审计 `:77,81`）。 | accepted A/system 排除显式裂纹，缺材料参数即 unavailable（`A_INTEGRATED_MODEL.md:83–85,1805–1816`；`SYSTEM_INTEGRATED_MODEL.md:2197–2202`）。 | `supported` | **P1 / 高**。现行边界没有采用这些拟合；若未来登记 R-curve 先验，必须携带有效域与坍塌后数据禁用标记。 |
| 3 | 峰前 CMOD 缓慢增长，峰后快速张开且载荷下降（`evidence_card.md:130–135`；`fig09_p08_cmod_instability.png`）。 | A 保存完整接触循环、多峰和混合事件（`A_INTEGRATED_MODEL.md:1710–1737`）；system 要求首针失效或首次下降后仍重平衡并保留峰后分支（`SYSTEM_INTEGRATED_MODEL.md:2140–2145`）。 | `supported` | **P2 / 中高**。现行事件/峰值语义与“峰值不等于立即终止”一致，但文献不支持项目采用其峰后幂律。 |
| 4 | M2：试样间幅值、峰值位置和数据密度显著离散（`evidence_card.md:31–40,146–148`）。 | A 允许面片 (k) 各自面积、方向和参数（`A_INTEGRATED_MODEL.md:812–875`），并把表面统计、样本数保留为未标定量（`:1794–1799`）；system 要求随机样本随统计稳定性扩增（`SYSTEM_INTEGRATED_MODEL.md:2153–2159`）。 | `supported` | **P2 / 高（架构层）**。架构可承载空间/样本离散，但尚无红砖材料随机场参数，不能声称已预测该分组。 |
| 5 | 孔隙变化导致裂纹跳跃及高/低两组只是小样本归纳，作者要求进一步验证（`evidence_card.md:33–40,110–113`；审计 `:74`）。 | B 仅登记表面统计、局部强度和损伤演化待材料试验关闭（`B_INTEGRATED_MODEL.md:1804–1813`），验证报告也否认随机样本已收敛（`DERIVATION_VERIFICATION_2026-07-17.md:449–465`）。 | `insufficient_evidence` | **P2 / 中**。只能形成“检验孔隙/位置随机效应与多峰分布”的验证假设，不能建立孔隙率→跳裂概率函数或双峰先验。 |
| 6 | M3：DIC 将逐帧裂尖位置与同时刻载荷配对，生成 (F-a)、CMOD 和 R-curve（`evidence_card.md:42–51,158`）。 | formal 当前实验可观测仅含 (t,x,F_x,P_z) 与元数据，且标量拖曳不能辨识局部强度、断裂能和损伤核（`MECHANISM_DERIVATION_FORMAL.md:2004–2062`）。 | `supplement_candidate` | **P1 / 高**。建议作为未来材料标定协议，而非求解公式；需新增图像帧—载荷—位移共同时间基准及裂尖/裂纹长度原始通道。 |
| 7 | DIC 裂尖为人工阈值跟踪，快速失稳会跨采样间隔并丢点（`evidence_card.md:45–50,165–167`；审计 `:79–80`）。 | system 只规定保留原始/滤波曲线和时间映射（`SYSTEM_INTEGRATED_MODEL.md:2160–2164`），未显式规定图像观测删失。 | `supplement_candidate` | **P2 / 高**。验证数据应记录 threshold、operator/method、frame rate、置信区间、missing-interval/censored 标记；丢点不能伪装为连续裂纹路径。 |
| 8 | M4：两种 (K_{IC}) 算法六个试样差 ≤0.03，但 BRK 2026 差 0.23 MPa√m，可识别异常样本（`evidence_card.md:53–62,137–142`）。 | accepted A 要求局部峰后试验与留出验证，但未规定独立估计器交叉核验（`A_INTEGRATED_MODEL.md:1813–1816`）；全系统目前只有 `SPEC_DEFINED`，无实验通过证据（`SYSTEM_INTEGRATED_MODEL.md:2046–2059`）。 | `supplement_candidate` | **P2 / 高**。加入“独立估计器一致性 + 异常样本不静默剔除”的材料参数 QA 义务；阈值须由目标试验方案预先冻结。 |
| 9 | E1 是特定三点弯曲梁的 LEFM 几何式，不可替代针尖非均匀接触场（`evidence_card.md:66–79`）。 | A 用局部控制体应力代理、Mohr–Coulomb/拉伸截断/可选压帽表示接触材料状态（`A_INTEGRATED_MODEL.md:827–916`），system 禁止上层重写 A 材料模型（`SYSTEM_INTEGRATED_MODEL.md:225–233`）。 | `supported` | **P1 / 高**。Eq. (1) 只能留在宏观材料试验复现工具，不能进入 A 接触残量。 |
| 10 | E2/E3 依赖缺报的 (E,\sigma_{ys}) 及 (k=1,r=0.5)、中心塑性铰等假设（`evidence_card.md:81–104,169–170`；审计 `:34–44,73`）。 | formal 对缺少局部运动学/参数的材料分支强制 `MATERIAL_MODEL_UNAVAILABLE`（`MECHANISM_DERIVATION_FORMAL.md:1007–1027`）；复核要求首版 `no_damage`（`DERIVATION_VERIFICATION_2026-07-17.md:255–263`）。 | `insufficient_evidence` | **P1 / 高**。不能用该卡复现 CTOD 法，更不能据此生成项目 (G_c^{mix})；必须回原文/原始公式并补目标材料参数。 |
| 11 | 宏观 (K_{IC}=0.25–0.54)、(K_{I,max}\approx1.24\pm0.20) MPa√m、CTOD 4.34–13.77 µm，以及 (a/W\approx0.7/0.8)（`evidence_card.md:108–119,154–161`）。 | A 需要局部压入/剪切/混合加载、峰后相对位移、能量正则和留出验证（`A_INTEGRATED_MODEL.md:1805–1826`）；system 同样要求局部压/剪/混合及峰后试验（`SYSTEM_INTEGRATED_MODEL.md:2201`）。 | `insufficient_evidence` | **P1 / 高**。最多作为“目标红砖宏观 Mode-I 数量级”的弱先验/实验 sanity check；不得作局部阈值、混合模态能量或截止常数。 |

## 4. 真冲突、表面冲突与关键遗漏

- **真冲突：无。** 当前主线是 `no_damage`，显式裂纹又被工程范围排除；文献没有在相同对象与假设下反驳现行接触、摩擦、梁、阵列平衡或事务方程。
- **表面冲突 1：** R-curve 上升与 (q(\delta_d)) 下降。前者是宏观裂纹增长阻力，后者是局部接触面片容量折减；只有把二者等同才冲突。
- **表面冲突 2：** 快速裂纹跳跃与准静态模型。准静态事件可表示状态突变，却不能预测裂纹速度或采样间动态；现行排除惯性/显式裂纹，因此属于范围差异。
- **关键遗漏：** 现行材料扩展没有起裂—扩展阻力的显式区分字段、裂纹长度或等效裂纹面积状态、R-curve 有效域；实验合同没有 DIC 图像同步、观测删失与双方法异常审计；材料不确定性尚未区分批次、试样、厚度位置与面片尺度。

## 5. Proposed 补充候选与验证义务

1. **A 材料层 / 可选未来模型（P1）：** 增加 `fracture_resistance_model_id = constant_Gc | evolving_R` 及 `initiation_resistance / propagation_resistance / validity_domain`。只有目标红砖、目标尺度、局部或混合模态试验给出可审计尺度桥后才能启用；在首版显式裂纹排除不变时仅登记为未来扩展，不进入求解器主线。验证须覆盖功共轭、混合模态、网格/核/步长客观性和峰后留出集。
2. **材料不确定性层 / 验证假设（P2）：** 允许强度与 (G_c) 的空间/批次随机效应，但本卡不提供分布；先做多批次、多位置、方向分层实验，检验单峰/多峰与孔隙相关性，未经验证不得设置确定性孔隙耦合。
3. **实验与输出合同（P1/P2）：** 增加 `frame_id/timestamp/load/CMOD/CTOD/crack_tip/crack_length/tracking_method/quality/censored_interval`，保留原图与人工修订记录；以 DIC R-curve 和 CMOD→CTOD 两条独立链交叉校核，并显式保留异常样本。
4. **参数身份（P3）：** 可把该文宏观 (K_{IC}) 登记成带 `macro_Mode_I_beam_prior` 标签的弱先验，必须附批次、几何、尺度、模式和 (a/W\lesssim0.8) 有效域；不得自动换算为 (G_c^{mix}) 或 A 层容量参数。

## 6. 明确不可直接移植

不可直接移植：七个试样的四阶多项式；(a/W\approx0.7) 峰位与 0.8 截止；宏观 (K_{IC})、(K_{I,max})、CTOD；26% 孔隙率到裂纹跳跃/双分组的函数；Eq. (1) 的梁几何因子；Eq. (2) 的可疑排印；Eq. (3)–(4) 在缺 (E,\sigma_{ys}) 且固定 (k,r) 假设下的数值；峰后“幂律”作为爪刺软化律。它们均不能替代目标红砖局部压缩、剪切、混合模态、重复通过与峰后相对位移标定。

**优先级汇总：** P0 无；P1 为防止宏观 R-curve/韧度误灌入 A 层并补齐材料标定门；P2 为 DIC 质量、异常样本和异质性验证；P3 为弱先验登记。总体置信度：对“无真冲突、不可直接参数移植”为高；对“孔隙导致跳裂/双分组”的可补充物理解释为中低。

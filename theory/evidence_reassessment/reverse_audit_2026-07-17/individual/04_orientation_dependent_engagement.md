# 04｜Orientation-dependent bio-inspired spine engagement mechanics 反向审查

**审查对象：** `MECHANISM_DERIVATION_FORMAL 0.1.0-proposed`，并与 A/B/C/System `1.0 accepted` 及独立 verification 对照。
**结论状态：** non-normative；只提出补充候选，不修改 accepted 机理或工程固定扫描集合。

## 1. 文献卡身份、提取完整性与适用域

论文为 2026 年理论＋单刺实验＋蒙特卡洛研究，研究 P60 上的俯仰响应，以及理想各向同性粗糙面上的阵列偏航—命中率—微扰刚度权衡（`theory/evidence_reassessment/literature/04_orientation_dependent_engagement/evidence_card.md:5-12`）。提取审计覆盖全部 13 页和全部主要章节（`.../extraction_audit.json:5-23`），Eq. (1)–(10) 均逐式核过（`.../extraction_audit.json:25-85`）；Fig. 4、6、8 的保留图也已目视复核（`.../extraction_audit.json:121-151`）。总体状态为 `PASS_WITH_WARNINGS`（`.../extraction_audit.json:184-194`）。

证据域必须收窄为：鱼钩尖端、P60、法向载荷 0.1 N、准静态轻载的俯仰实验；以及各向同性高斯凸体、零均值正态偏航、固定接触集合、线性轴向刚度和无穷小扰动的偏航仿真（`.../evidence_card.md:20-28,64-84`）。四种岩/砖材料只做形貌驱动预测，并非力—角实验；补充表 S1/S2 不在工作区（`.../extraction_audit.json:87-99,184-190`）。

## 2. 决定性判断（M1–M6）

| ID | 文献结论与本地来源 | 现行机理对应位置 | 分类 | 判断、优先级与置信度 |
|---|---|---|---|---|
| D01 / M1 | P60 单刺力—俯仰角在约 60° 单峰，钝角侧下降更快（`.../evidence_card.md:20-29,209-215`） | B 已有逐针角度轴式并正式扫描 50/60/70/80°（`theory/modules/B_INTEGRATED_MODEL.md:98-110,588-608`）；A 保存完整反力与峰记录（`theory/modules/A_INTEGRATED_MODEL.md:1668-1737`） | `supported` + `supplement_candidate` | 现行方程和输出可表示该现象，且 60° 已被扫描覆盖；但“单峰、峰位、非对称下降”没有成为验证目标。建议只新增趋势/排序验证，不把 60°写成定律。**P1，高。** |
| D02 / M1 | 结论限定于 0.1 N、25 μm 尖端、P60（`.../evidence_card.md:23-27,192-198`） | 项目单刺为 0.5 N，针尖 0.05/0.10 mm；B 单元为 0.5–2 N（`theory/modules/A_INTEGRATED_MODEL.md:71-80`） | `insufficient_evidence` | 若项目仿真峰位不是 60°，首先是载荷、尖端尺度和表面域差异，不构成同域冲突；论文峰值大小、显著性或钝角下降率不可直接移植。**P1，高。** |
| D03 / M1–M2 | 俯仰/尖端倾角显著改变接触与承载（`.../evidence_card.md:20-40`） | accepted A 的姿态类型存在 P0 二次旋转风险（`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:184-208`）；FORMAL 已改为全局转角左乘并明确 `a_t`（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:481-507`） | `supported` | 文献不产生新冲突，却强化既有 P0：未先版本化采纳 FORMAL 的姿态闭合，就不能信任任何俯仰/偏航比较。应增加刚体角扫描与有限差分姿态回归。**P0，高。** |
| D04 / M2 | 倾斜改变抗滑上限；E2 为 `tan(phi+atan f_s)`（`.../evidence_card.md:88-111`） | A 使用完整三维 SOC Coulomb；二维单支持特例给出 `(tan phi+mu)/(1-mu tan phi)` 并强制有效域检查（`theory/modules/A_INTEGRATED_MODEL.md:575-645,1247-1263`） | `supported` | 角度约定对应后两式代数一致；现行 SOC 比论文二维式更一般，并已处理法向正性、另一侧锥和奇点。无需把 E1/E2 另建成第二套承载律，可将其作为二维解析回归。**P2，高。** |
| D05 / M2 | 鱼钩抛物线尖端随 `theta_i` 增大出现更大 `R_eq`（`.../evidence_card.md:31-40,245-247`） | 项目固定为有限球冠承载、锥/杆/座不承载（`theory/modules/A_INTEGRATED_MODEL.md:71-76,449-478`；`theory/paper/MECHANISM_DERIVATION_FORMAL.md:373-398`） | `supplement_candidate` | 球面本征曲率恒定，而论文 `R_eq(theta_i)` 来自另一种尖端轮廓；这是几何范围差异，不是真冲突。若显微/CAD 表明实际尖端显著偏离球面，可新增“测得轮廓/曲率张量”可选几何分支及 `R_eff` 输出；不得改写当前球冠主线。**P2，中高。** |
| D06 / M2 | `L_f` 随倾角增加，并据抗滑—路径折中取约 10°（`.../evidence_card.md:34-40,217-222`） | FORMAL 的 M0 明确无材料损伤；M1 只在断裂能、相对运动与功共轭闭合后可用（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:78-103,959-1027`） | `insufficient_evidence` | `L_f` 只是高斯凸体几何代理，且 Fig. 4(h)/(i) 单位矛盾、10°实为折中而非抗滑最大点（`.../extraction_audit.json:162-176`）。可保存几何诊断，不能充当红砖破坏载荷、断裂能或项目安装角。**P0（禁止误用），高。** |
| D07 / M3 | `ELS=PDF(phi) EI^p` 将坡度出现概率与互锁质量合成，再映射推荐俯仰角（`.../evidence_card.md:42-51,113-146`） | FORMAL 以二维 PSD、三维支持点/法向和完整接触求解为主（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:316-454`）；A 的候选标签仅是几何必要条件，不是成功判据（`theory/modules/A_INTEGRATED_MODEL.md:414-478`） | `supplement_candidate` | 现行机理缺少这一低成本姿态先验。可在 A1/设计预处理层加入版本化 `orientation_prior/ELS` 派生诊断，但不得替代 SurfaceRealization、SOC、载荷共享或 accepted 判据；`p`、方向剖面和三维化均须重算。**P2，中高。** |
| D08 / M4 | 四材料预测带 52.7°–64.0°，细粒砖 57.9°（`.../evidence_card.md:53-62,224-229`） | 固定扫描集合含 50/60/70/80°，另有 80→50/60 梯度（`theory/evidence_reassessment/engineering_fixed_context.md:506-532`） | `supported` | 预测带与现行扫描的 60°点相容，可解释为何 60°值得保留；它没有遗漏一个必须立刻新增的正式工况，也不支持缩掉 50/70/80°。**P2，高。** |
| D09 / M4 | 57.9°来自细粒砖形貌计算而非承载实验（`.../evidence_card.md:56-62,201-202,260-261`） | 目标表面统计、摩擦、强度仍未标定（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198-2201`） | `insufficient_evidence` | 论文细粒砖不等于项目目标红砖；57.9°只能作离线先验/后续局部加密候选，不能覆盖已固定扫描集合或成为默认值。关闭需目标表面多位置三维测量、方向坡度统计及留出承载实验。**P1，高。** |
| D10 / M5 | 偏航窗口以针方向、表面法向方位和摩擦角判 locked/slip（`.../evidence_card.md:64-73,148-159`） | 工程坐标和逐针数组已保留 `beta`，但首版固定 `beta=0`、不扫描偏航（`theory/evidence_reassessment/engineering_fixed_context.md:210-249,563-577`）；B 亦保留逐针 `beta`（`theory/modules/B_INTEGRATED_MODEL.md:424-454,588-608`） | `supported` + `supplement_candidate` | 数据结构没有遗漏偏航自由参数；缺的是未来扫描政策。静态偏航阵列可在版本化研究分支中加入，不应静默改变首版工程事实。**P1，高。** |
| D11 / M5 | 理想面上 `sigma` 增大使 Eq. (7) 命中率单调下降（`.../evidence_card.md:67-73,231-235`） | A 用真实三维法向与 SOC 决定接触；B 明确相关性诊断不得生成 IID 成功率或载荷权重（`theory/modules/A_INTEGRATED_MODEL.md:456-478,575-645`；`theory/modules/B_INTEGRATED_MODEL.md:660-690`） | `supplement_candidate` | Eq. (7) 可作同假设下的离线筛选诊断和回归 fixture，不能作为生产硬过滤器或把 12.5%/5.5%称作阵列成功率。真实各向异性、搜索、候选竞争和载荷共享允许趋势偏离，属于范围差异。**P1，高。** |
| D12 / M6 | 小偏航离散通过轴向压缩提供双向恢复分量，归一化刚度先升后降（`.../evidence_card.md:75-84,161-186`） | FORMAL/C 已有一侧恢复切线框架（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:1717-1744`；`theory/modules/C_INTEGRATED_MODEL.md:1292-1333`），但 B 1.0 只有 x/Z，局部 y 与完整切线不支持（`theory/system/SYSTEM_INTEGRATED_MODEL.md:1120-1133`） | `supplement_candidate` | 这是关键遗漏：未来 B 2.x 应输出 `K_y+`、`K_y-`、total `K_y`、活动集和通道分解，并以 Eq. (8)–(10) 作“固定接触、线弹性、no_damage”回归；当前不得用该简式绕过合同。**P0（合同边界）/P1（补充），高。** |
| D13 / M6 | 建议 `sigma=10°–20°`，峰约 25°，使用单一 `k_r`（`.../evidence_card.md:79-84,203-205,237-241`） | B 2.x 尚须完整 y/SE(3)、动态几何和 6D tangent/graph（`theory/system/SYSTEM_INTEGRATED_MODEL.md:1135-1185,2190-2192`） | `insufficient_evidence` | `k_r` 不能直接等同于项目的梁、轴向弹簧、接触和夹具组合刚度；10°–20°/25°也仅为理想面仿真结果。只有完成参数去重、真实表面扫描和横向微扰实验后才能形成项目偏航先验。**P1，高。** |
| D14 / M6 | 论文称 `sigma=0` 时无“该横向分量”（`.../evidence_card.md:75-82`） | A 的完整点柔顺含梁、弹簧和接触通道（`theory/modules/A_INTEGRATED_MODEL.md:1211-1245`） | `supported`（范围限定） | 这只表示论文的“偏航轴向投影通道”为零，不表示完整系统总横向刚度必为零；直针仍可能因弯曲、摩擦、表面几何或多支持产生恢复力。建议未来把 `K_y_axial-yaw` 与 `K_y_total` 分栏，避免制造伪冲突。**P1，高。** |

## 3. 真冲突与表面冲突

**同对象、同假设、同适用域的真冲突：未发现。** 论文二维抗滑式与 A 的二维特例相容，现行三维 SOC 更一般；60°也处于正式扫描集合。

表面冲突有四类：约 10°是局部尖端接触倾角折中，不是约 60°安装俯仰角；`R_eq(theta_i)`针对非球形鱼钩轮廓，不反驳项目有限球冠；偏航命中率的单调性限定于理想各向同性抽样，不约束真实方向表面与历史载荷共享；`sigma=0`只消去偏航轴向投影刚度，不消去完整模型的全部横向恢复通道。以上均不得写成机理矛盾。

## 4. 被漏掉且可补充的内容

1. **P0，姿态验证义务：** 在任何角度研究前，把 FORMAL 的姿态类型闭合版本化并入 accepted A；增加 `alpha/beta` 刚体扫描、坐标旋转不变性和姿态有限差分回归。
2. **P1，俯仰趋势验证：** 在 A/B 验证矩阵加入“同表面、同载荷、同尖端下的力—角完整曲线、峰位区间、两侧下降率和多 realization 置信区间”；P60 约 60°只作外部趋势目标。
3. **P2，A1/设计预处理派生量：** 增加方向法向分布、`EI/ELS`、映射得到的 `alpha_prior`，身份为 `diagnostic/prior`；要求三维方向定义、非高斯检验、`p` 敏感性及与完整 A/B 排序的留出验证。
4. **P2，可选真实尖端几何：** 仅当显微/CAD 否定球冠近似时，新增轮廓/曲率张量后端与 `theta_i/R_eff` 输出；不得把论文 25 μm 鱼钩几何移入当前参数包。
5. **P1，未来偏航研究：** 在不改变首版 `beta=0` 的前提下，提出版本化静态偏航分布扫描；同时报告几何候选率、实际承载针率、完整力曲线和不均载，禁止以 Eq. (7) 概率代替成功率。
6. **P0/P1，未来 B 2.x 横向稳定性：** 合同升级后加入正/负一侧横向切线、恢复功、活动集和 `axial-yaw/beam/contact/friction` 通道分解；论文 Eq. (8)–(10)仅作受限解析 fixture，并要求横向微扰实验验证。

## 5. 明确不可直接移植

- P60 的 `mu=0.8±0.04`、0.1 N、10 mm/s、25 μm/20°鱼钩几何及约 60°实验最优；
- `theta_i≈10°`、`L_f` 数值/单位及由它推断的红砖破坏载荷；
- `p=2`、高斯坡度假设、四材料 52.7°–64.0°和细粒砖 57.9°作为项目参数；
- Eq. (7)作为生产硬接触门、12.5%/5.5%作为阵列成功率；
- 蒙特卡洛规模、`sigma=10°–20°/25°`、单一 `k_r`及归一化刚度百分比。

## 6. 最终判定

本卡对现行完整机理的主要价值不是纠错，而是补齐**姿态导向的验证与设计诊断**。现行接触力学没有与原文冲突，但对 M1 的实验趋势、M3 的低成本姿态先验、M5 的偏航统计诊断和 M6 的双向横向刚度输出尚未显式吸收。最高优先级是：先关闭 accepted A 的姿态 P0；随后保持 B 1.0 的 y/转动阻断，不得用论文简式旁路；偏航刚度只能作为 B 2.x 之后的版本化补充与验证任务。

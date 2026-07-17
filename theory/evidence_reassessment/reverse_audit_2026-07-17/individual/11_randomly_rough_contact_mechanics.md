# 11 — Randomly rough contact mechanics 反向审查

**审查对象：** Persson (2006), *Contact mechanics for randomly rough surfaces*，DOI 10.1016/j.surfrep.2006.04.001。论文对象是多尺度随机粗糙的名义平面接触，证据卡只取无黏附的弹性/理想弹塑性主线（`theory/evidence_reassessment/literature/11_randomly_rough_contact_mechanics/evidence_card.md:5-17`）。提取审计覆盖本地 arXiv v1 全部 29 页（`extraction_audit.json:2-7`），E1–E8 的关键公式均经 300–400 dpi 图像核查（`extraction_audit.json:45-116,201-204`），状态为 `PASS_WITH_WARNINGS`（`extraction_audit.json:191-206`）。本轮也目视复核了 Fig. 9、15、30；它们分别支持尺度揭示部分接触、理想弹塑性面积演化和稀疏网格偏差（`extraction_audit.json:147-168`）。因此对论文自身公式和限定域置信度高；对有限球尖钢刺—脆性红砖的公式/参数移植置信度低至中。

## 决定性判断（M1–M6）

| ID | 文献结论与本地证据 | 现行完整机理对应 | 分类 / 优先级 / 置信度 | 判断 |
|---|---|---|---|---|
| 11-01 | M1：跨尺度接触由二维 PSD 及有限波数窗控制，单一 rms 高度不能推出更强接触/摩擦（`evidence_card.md:21-30,89-107`）。 | FORMAL 与 accepted A 都以二维矢量 PSD 和显式可信波段描述高度场（`theory/paper/MECHANISM_DERIVATION_FORMAL.md:316-339`；`theory/modules/A_INTEGRATED_MODEL.md:414-428`）；系统还把 PSD、高度分布、相关长度、各向异性、非高斯列为未标定量（`theory/system/SYSTEM_INTEGRATED_MODEL.md:2198-2201`）。 | `supported` / P1 / 高 | 核心方向已包含，现行机理也未用 `Sa/Ra/rms` 单标量决定承载。材料专属预测仍应保持 `GEOMETRY_UNCERTAIN`，不能把“有 PSD 字段”误写成已标定。 |
| 11-02 | E1 的论文约定把 (1/(2\pi)^2) 放在 PSD 定义内（`evidence_card.md:89-101`）。 | FORMAL/A 把该因子放在反变换/方差积分侧（`MECHANISM_DERIVATION_FORMAL.md:326-339`；`A_INTEGRATED_MODEL.md:418-426`）。 | `supplement_candidate` / P1 / 高 | 不是物理冲突，而是 Fourier 归一化差异；若直接把论文的 (B=(2\pi/L)\sqrt C) 接到现行 (C_h)，会产生常数因子错误。应冻结 `psd_convention_id`、单位和双向换算，并做方差/PSD 回算测试。 |
| 11-03 | M1/E1 给出 (q_L,q_0,q_1,H)、roll-off 和有限自仿射区，同时警告径向平均会丢方向性（`evidence_card.md:24-30,98-106,269-272,348`）。 | A 只要求可信波数带和生成元数据；未决表登记了 PSD、边际、相关长度、各向异性与非高斯（`A_INTEGRATED_MODEL.md:416-428,1794-1799`）。 | `supplement_candidate` / P1 / 高 | 被漏掉的是版本化的谱质控字段/报告，不是新主接触律：建议保存二维 (C(q_x,q_y))、roll-off、物理/仪器截止、拟合区和 (H) 不确定度；只有经检验自仿射时才报告 (H)。 |
| 11-04 | M2/E2：随机相位 Fourier 叠加可生成目标二阶统计表面；实值实现还须共轭对称、去均值和离散归一化核验（`evidence_card.md:32-41,109-127`；`extraction_audit.json:53-56,179-183`）。 | A 已要求 `measurement/generation metadata`、seed；FORMAL/verification 允许合成表面敏感性和 ensemble，却未定义生成算法（`A_INTEGRATED_MODEL.md:414-428`；`MECHANISM_DERIVATION_FORMAL.md:2151-2153`；`theory/review/DERIVATION_VERIFICATION_2026-07-17.md:469-477`）。 | `supplement_candidate` / P1 / 高 | 这是最直接的遗漏。应增加非规范 `SurfaceGenerator/PSD_RANDOM_PHASE_V1`：Hermitian 配对、零模处理、周期域、seed、FFT convention、目标/回算 PSD 误差与方差验收；它生成开发 realization，不替代实测红砖。 |
| 11-05 | M2 的生成式只约束二阶统计，不保证偏度、峰度、孤立孔洞或方向性（`evidence_card.md:38-41,121-126,349`）。 | 系统已把高度分布、各向异性和非高斯列为独立未决量，而非假定 PSD 充分（`SYSTEM_INTEGRATED_MODEL.md:2198`）。 | `supported` / P1 / 高 | 现行边界正确；应把高度直方图、偏/峰度、方向谱和局部缺陷统计加入生成验收，不能通过 PSD 一项就把合成面标为“红砖等价”。 |
| 11-06 | M3：加入高波数后，低倍“完全接触”分裂为微接触/非接触；该结论限于无黏附、线弹性半空间、法向接触（`evidence_card.md:43-52,149-171`；Fig. 9 见 `extraction_audit.json:147`）。 | 现行模型以显式高度场/网格、有限球冠与 Signorini 支持求解；同时要求表面分辨率加密后 gap、法向、事件、wrench、峰值稳定（`A_INTEGRATED_MODEL.md:430-478,1741-1763`；`SYSTEM_INTEGRATED_MODEL.md:2149-2159`）。 | `supported` / P1 / 高 | “短波会改变接触状态、必须做分辨率收敛”已包含；但现行“部分接触”是有限球尖/多针活动支持，不等于 Persson 的名义平面面积分数，二者不得同名替换。 |
| 11-07 | E3 给出尺度分辨应力 PDF、接触面积零阶矩和载荷一阶矩（`evidence_card.md:129-147`）。 | FORMAL/A 的规范输出是离散支持、gap、法/切向乘子和 wrench，未定义名义面积或应力 PDF（`A_INTEGRATED_MODEL.md:364-377,449-478`；`theory/system/SYSTEM_INTEGRATED_MODEL.md:1755-1757`）。 | `supplement_candidate` / P2 / 中 | 可把 (P(\sigma,\zeta))、(A/A_0) 作为**可选离线表面/局部接触诊断**，但必须先冻结名义面积、投影面、压力正号和尺度桥；不得把面积分数直接当作可啮合概率或 A/B 承载乘子。 |
| 11-08 | E4–E5 的 (q^3C(q)) 应力扩散与 erf 面积解来自弹性体—刚性粗糙基底，并把完全接触推导近似延拓到部分接触（`evidence_card.md:149-195,350`）。 | 当前可执行 (mathsf M_0) 是刚性局部接触；可选局部柔顺和材料扩展尚未标定/闭合（`MECHANISM_DERIVATION_FORMAL.md:78-103,2083-2098`；`SYSTEM_INTEGRATED_MODEL.md:2200-2201`）。 | `insufficient_evidence` / P1 / 高 | 范围差异，不是真冲突。缺少有限球尖尺度分离、钢—砖等效模量、砖有限厚度/脆性与局部粗糙带验证，故 E4–E5 不能进入 A 主残量；至多作为未来 `local_normal_compliance_model_id` 的候选，经独立验证后启用。 |
| 11-09 | M4/E6：低接触率、弹性、无黏附时 (A\approx\alpha F_N)，不同理论的 κ 仍不同（`evidence_card.md:54-63,197-216`）；数值比较本身有约 10%–20% 方法差（`evidence_card.md:283-301`）。 | 现行 A/B 直接求支持力和共同平衡，不以真实面积决定切向互锁；局部接触柔顺仍 unresolved（`SYSTEM_INTEGRATED_MODEL.md:1755-1767,2200`）。 | `supplement_candidate` / P2 / 中高 | 仅建议作为无损、低载、连续粗糙接触 fixture 的趋势/数量级验证，输出 (A/F_N) 与离散不确定度；不得用 (A\propto F_N) 替代有限刺几何、Coulomb、损伤或阵列重分配。 |
| 11-10 | M5/E7–E8 用 (P(0)=0)、(P(\sigma_Y)=0) 和面积通量划分弹性/塑性/非接触；其前提是理想塑性硬度边界（`evidence_card.md:65-74,218-263`；Fig. 15 见 `extraction_audit.json:153`）。 | 现行 A 把墙面容量/脆性软化与针体屈服分开，材料模型必须显式选择；FORMAL 当前只执行 `no_damage`，未闭合材料分支返回 unavailable（`A_INTEGRATED_MODEL.md:898-916,969-991,1038-1046`；`MECHANISM_DERIVATION_FORMAL.md:1005-1027`）。 | `insufficient_evidence` / P1 / 高 | 当前处理没有冲突且更安全。塑性面积不能冒充砖压碎、剪裂、断裂或 DamageStore；若未来启用，必须用独立 `ideal_plastic_normal_contact` 模型 ID，并与 brittle-damage 分栏。 |
| 11-11 | M6：稀疏网格会使 (P(0)\ne0) 并高估接触面积；22% 仅是 Fig. 30 算例（`evidence_card.md:76-85,313-321`；`extraction_audit.json:168,191-197`）。 | A/系统已要求高度场—网格加密一致、表面分辨率收敛和不足时几何未认证（`A_INTEGRATED_MODEL.md:1739-1767,1796-1799`；`SYSTEM_INTEGRATED_MODEL.md:2153-2159`），但 verification 明确这些尚未跑通（`DERIVATION_VERIFICATION_2026-07-17.md:449-465`）。 | `supported` / P1 / 高 | 收敛原则已在规范层包含，数值/实验层尚未验证；报告不得把 `SPEC_DEFINED` 写成通过。 |
| 11-12 | 文献建议每最小接触斑至少约 (10\times10)、优选约 (100\times100) 网格，且展示 22% 面积偏差（`evidence_card.md:275-279,313-321`）。 | 现行验收关注 gap、法向、事件、wrench、峰值和损伤的平台，而非固定节点数（`SYSTEM_INTEGRATED_MODEL.md:2151-2159`）。 | `insufficient_evidence` / P2 / 高 | 这些是 2006 年方法/算例经验，不能成为通用网格下限或 22% 修正系数。若未来实现应力 PDF，再补 (P(0))、面积零阶矩、载荷一阶矩和最小接触斑解析度；停止规则仍以目标输出稳定平台为准。 |

## 真冲突与表面冲突

**真冲突：0 项。** 没有发现现行机理在相同对象、材料、尺度和边界条件下否定论文结论。

表面冲突有四类：一是 PSD 的 (2\pi) 因子属于 Fourier convention 差异；二是论文的“部分接触”是名义平面微接触面积，现行 B 的“部分接触”是部分针/支持活动；三是 Persson 主式是线弹性半空间法向接触，现行主链是有限球尖、三维摩擦与切向互锁；四是理想塑性面积通量不同于红砖脆性损伤。它们都不能据此判现行机理错误，也不能用论文公式绕过现有材料 `unavailable` 边界。论文还明确不处理有限爪刺、搜索、互锁和主动脱附（`evidence_card.md:346-357`），因此不能验证 B/C 主链或解除当前合同阻断。

## 被漏掉的关键结论与 proposed 补充

1. **A1 表面生成契约（P1）：** 增加 `PSD_RANDOM_PHASE_V1` 作为开发期生成器/fixture，冻结 PSD convention、Hermitian 对称、零模、周期域、seed 和 FFT 归一化；验收目标 PSD、回算 PSD、方差、均值及实值误差。它只生成合成 ensemble。
2. **A1 谱质控报告（P1）：** 对实测/合成 realization 输出二维 PSD、可信带、(q_L/q_0/q_1)、roll-off、可选 (H) 拟合区与不确定度，并并列高度边际、偏/峰度、方向性和缺陷统计。工程主线仍是 150 mm × 150 mm 高度场，参数仍属 unresolved（`theory/evidence_reassessment/engineering_fixed_context.md:670-717,1068-1075`）。
3. **可选多尺度接触诊断（P2）：** 在独立离线层定义 (P(\sigma,\zeta))、(A_{el}/A_{pl}/A_{non}) 与矩守恒；只有模型 ID、名义面积、尺度桥、等效模量和材料适用域齐全才输出，否则 `unavailable`。不得回写 `SurfaceRealization` 或直接驱动啮合承载。
4. **验证矩阵补充（P1）：** 合成面先做 PSD/方差回算；若启用连续接触子模型，再做低载 (A\propto F_N)、(P(0)=0)、面积/载荷矩与接触斑加密；主求解器继续以 gap、法向、事件、wrench、峰值和损伤的稳定平台验收。
5. **材料模型隔离（P1）：** 增加“ideal-plastic normal contact ≠ brittle damage ≠ needle yield”的 schema/审计断言；理想硬度分支只在目标砖跨尺度压痕/划擦证明塑性主导后作为可选模型启用。

## 不可直接移植

- Persson/Bush 的 κ、(A/A_0<0.1) 示例线性区、Fig. 15 的 (E=10^{11}\) Pa、ν=0.3、σ₀=10 MPa 与 1–5 GPa 硬度（`evidence_card.md:273-278`）；均非目标砖—钢刺参数。
- “压痕硬度约为单轴屈服应力三倍”、尺度相关硬度函数及塑性面积通量；不得替换砖压碎/剪裂/断裂试验（`evidence_card.md:234-262,276`）。
- 各向同性、统计平稳、随机相位/二阶统计充分、线弹性半空间、无黏附、名义平面与法向载荷等适用域（`evidence_card.md:27-28,38-39,49-50,60-61`）。
- Fig. 30 的 22% 与 (10\times10/100\times100) 网格经验；只能保留为收敛风险示例，不能作修正系数或固定停止阈值。
- 论文的黏附、PMMA、Pyrex、轮胎与历史算力尺度限制；提取审计已将其判为目标外内容（`extraction_audit.json:119-134,171-177`）。

## 优先级结论

- **P0：** 无新增文献真冲突；不得以 E4–E8 解锁当前未闭合材料分支或正式 C 承载。
- **P1：** 优先冻结 PSD convention/生成器、二维谱质控、非高斯验收和条件性接触收敛指标。兼容性判断置信度高。
- **P2：** 应力 PDF、面积分区与低载面积斜率只作离线诊断/回归；跨域可用性置信度中。
- **P3：** 论文材料算例、历史网格数量和黏附应用不进入现行参数包。

**总判定：** 第 11 卡与现行完整机理无同域真冲突。现行模型已正确吸收“二维 PSD + 可信波段 + 分辨率收敛 + 材料范围隔离”的原则；真正遗漏的是把这些原则变成可执行、可审计的合成表面与谱质控契约，以及仅在适用域闭合后启用的多尺度法向接触诊断，而不是把 Persson 名义平面公式直接改写成爪刺啮合承载律。

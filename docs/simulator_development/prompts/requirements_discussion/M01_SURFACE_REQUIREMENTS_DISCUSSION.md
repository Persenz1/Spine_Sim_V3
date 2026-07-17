# M01 SURFACE 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M01_SURFACE_REQUIREMENTS
PROMPT_VERSION: 0.1.2

本窗口只讨论并冻结 M01 SURFACE（解析/合成表面提供者）的需求。不得编码，不得开始数值内核、单刺或实现阶段。

第一版不使用白光轮廓仪数据，也不声称重建真实红砖。M01 的任务是为公式回归、事件构造和宽先验趋势筛选提供确定性、可重放的表面查询；它是软件服务模块，不是独立的材料真实性模型。

MECHANISM_DERIVATION_FORMAL 0.2.0-proposed 的 SurfaceGenerationAndAcquisitionContract 只作为 PROPOSED_SUPPLEMENT：本窗口可以把它转成 additive provenance/schema 和验证义务，但不能据此改写 accepted A 的几何、接触或接口。首版只实现 synthetic/analytic provider；measured 分支只冻结可扩展 schema、显式 deferred/unavailable 和迁移边界，不实现仪器采集管线。

开始前完整读取：
1. AGENTS.md、README.md、theory/README.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00_FOUNDATION_REQUIREMENTS.md；若尚未冻结则停止并说明前置缺失；
4. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
5. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
6. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
7. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml；
8. theory/modules/A_INTEGRATED_MODEL.md；
9. theory/paper/MECHANISM_DERIVATION_FORMAL.md 中表面、有限球尖与验证相关内容。

讨论方式：
- 先提出符合现有政策的默认表面库和查询 API，每轮最多询问 3 个决策；
- 不要求用户提供真实 PSD、Ra、摩擦或材料强度；
- 依次讨论“表面族与参数”“查询语义”“缓存/分辨率”“输出字段”“出图与验收”；
- 把参数标为 FIXED_ENGINEERING、DESIGN_VARIABLE、DEV_PRIOR_UNCERTAINTY、NUMERICAL_CONFIGURATION 或 RUN_AND_PLOT_CONFIGURATION。

本窗口必须关闭的问题：
1. `surface_source_kind=analytic/synthetic/measured` 的共同 schema；首版 allowed 与 deferred/unavailable 分支；
2. 平面、斜坡、正弦、单峰/坑、多峰、沟槽和已知最近特征切换的首批集合；
3. self-affine Gaussian 随机场的 H、Sq/Rt、lc/Rt、各向异性、方向和 seed；
4. 共同 provenance：坐标、单位、domain、材料方向、原始身份 hash、生成/处理链和来源身份；
5. synthetic 分支的生成器/版本、随机种子、周期域、归一化、目标/回算 PSD、方差和实值误差；
6. measured 预留字段：仪器/探针或 MTF/SNR、原生点距、可信截止、去趋势/插值/滤波/窗函数、缺失掩膜和不确定带；首版均按未提供显式 unavailable；
7. 150×150 mm 查询域与解析 evaluator/lazy tile 的关系；
8. 高度场公共查询：高度/点/法向/坡度/曲率或质量/邻域/域状态；
9. signed-distance/closest-feature 查询对每个 surface family 是 exact、approximate 还是 unavailable；近似能力的误差、可信尺度和收敛义务；
10. 球尖支持查询与表面后端的责任边界，避免 M01 偷偷拥有接触力学；
11. 三角网格接口是首版 stub、回归能力还是延期项；
12. 边界条件、平铺、查询越界、质量掩膜和可信尺度；
13. Rt/5、Rt/8、Rt/10 分辨率研究，以及针尖相对可信最短波长覆盖裕度如何表达；
14. realization ID/version/hash/seed/domain/quality、target/realized 统计和可视化采样；
15. 首批图：高度图、剖面、坡度/法向、分布、PSD/方向谱、可信带和分辨率收敛；
16. 内存、磁盘、按需采样和确定性要求；
17. 解析值、有限差分、PSD/方差回算、seed 重放、边界、缺失掩膜和针尖尺度测试。

硬边界：
- 合成表面统一标记 synthetic_unidentified，不得命名为真实红砖/混凝土；
- 不用单一 Ra 唯一决定三维表面；
- 可视化网格不成为求解器唯一几何表示；
- M01 不返回接触力、挂接成功、材料失效或方案评分；
- `source_kind=measured` 的 schema 不代表首版已经支持实测导入或证明表面真实性；
- proposed 表面字段不得改变 accepted A 的 SurfaceRealization 语义，必要变化必须标为 amendment/deferred；
- 摩擦/强度可作为表面参数引用，但物理使用权属于 A，不在 M01 复制本构。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md；
2. 明确输入参数表、SurfaceRealization/SurfaceQuery 语义、canonical 输出和出图字段；
3. 生成 docs/simulator_development/implementation_prompts/M01_SURFACE_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验与 M00 schema、A 查询需求和 DEV profile 的一致性；
5. 提交推送并报告后停止。

提交前严格执行 REQUIREMENTS_DISCUSSION_WORKFLOW 的 Git 安全交接：只精确暂存本任务文件，检查 cached diff，禁止使用 git add -A/git add .，不得纳入其他窗口的工作区改动。

不得在本窗口实现表面生成器。
```

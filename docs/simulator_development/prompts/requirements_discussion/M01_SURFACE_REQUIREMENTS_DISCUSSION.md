# M01 SURFACE 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M01_SURFACE_REQUIREMENTS

本窗口只讨论并冻结 M01 SURFACE（解析/合成表面提供者）的需求。不得编码，不得开始数值内核、单刺或实现阶段。

第一版不使用白光轮廓仪数据，也不声称重建真实红砖。M01 的任务是为公式回归、事件构造和宽先验趋势筛选提供确定性、可重放的表面查询；它是软件服务模块，不是独立的材料真实性模型。

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
1. 平面、斜坡、正弦、单峰/坑、多峰、沟槽和已知最近特征切换的首批集合；
2. self-affine Gaussian 随机场的 H、Sq/Rt、lc/Rt、各向异性、方向和 seed；
3. 150×150 mm 查询域与解析 evaluator/lazy tile 的关系；
4. 高度场公共查询：高度/点/法向/坡度/曲率或质量/邻域/域状态；
5. 球尖支持查询与表面后端的责任边界，避免 M01 偷偷拥有接触力学；
6. 三角网格接口是首版 stub、回归能力还是延期项；
7. 边界条件、平铺、查询越界和可信尺度；
8. Rt/5、Rt/8、Rt/10 分辨率研究如何表达；
9. realization ID/version/hash/seed/domain/quality 和可视化采样；
10. 首批图：高度图、剖面、坡度/法向、分布、PSD/方向谱、分辨率收敛；
11. 内存、磁盘、按需采样和确定性要求；
12. 解析值、有限差分、PSD 回算、seed 重放和边界测试。

硬边界：
- 合成表面统一标记 synthetic_unidentified，不得命名为真实红砖/混凝土；
- 不用单一 Ra 唯一决定三维表面；
- 可视化网格不成为求解器唯一几何表示；
- M01 不返回接触力、挂接成功、材料失效或方案评分；
- 摩擦/强度可作为表面参数引用，但物理使用权属于 A，不在 M01 复制本构。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md；
2. 明确输入参数表、SurfaceRealization/SurfaceQuery 语义、canonical 输出和出图字段；
3. 生成 docs/simulator_development/implementation_prompts/M01_SURFACE_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验与 M00 schema、A 查询需求和 DEV profile 的一致性；
5. 提交推送并报告后停止。

不得在本窗口实现表面生成器。
```

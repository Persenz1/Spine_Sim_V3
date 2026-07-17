# M03 SINGLE SPINE 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。

## 提示词正文

```text
TASK_ID: M03_SINGLE_SPINE_REQUIREMENTS
PROMPT_VERSION: 0.1.2

本窗口只讨论并冻结 M03 SINGLE SPINE（A-M0 单刺算子）的产品、参数、输出和出图需求。不得编码，不得开始 B 阵列。

本模块服务趋势和参数选型。第一版必须能够在解析/合成表面上，用 no_damage、刚性 Signorini/Coulomb、Euler–Bernoulli 梁和权威安装分支完成预载及 100 mm 连续拖曳；不能声称预测真实砖面破坏。

开始前完整读取：
1. AGENTS.md、README.md、theory/README.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00、M01、M02 requirements；
4. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
5. theory/modules/A_INTEGRATED_MODEL.md；
6. theory/interfaces/A_TO_B_CONTRACT.md；
7. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
8. theory/paper/MECHANISM_DERIVATION_FORMAL.md；
9. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
10. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml。

权威边界：accepted A/A→B 是现行接口；复核确认的姿态 P0、弹簧零位、事件和释放问题不得照错实现。第一版关闭损伤和针体强度认证，使用 proposed 严格稿已经闭合的 M0 表达、接触阶段分栏或释放路径时必须标为 PROPOSED_SUPPLEMENT，并说明它没有修改 accepted 状态或接口。

讨论方式：
- 先提出最小可运行 A-M0 默认方案；
- 每轮最多问 3 个问题，优先问用户真正关心的参数和图；
- 依次讨论“使用场景/参数”“状态与路径”“raw 输出”“图与摘要”“验收和延期”；
- 不索要实验数据，不把宽先验改称标定值。

本窗口必须关闭的问题：
1. standalone 与 embedded kernel 的首版边界；
2. Rt、d、L、alpha、beta、E、nu、mu、Pz 的默认/扫描/固定状态；
3. bending on/off、rigid mount、independent spring、ks 和 4 mm 行程；
4. 初始位姿、预载模式、+local-x 100 mm 路径和时间映射；
5. 有限球冠支持、最近候选、体部碰撞与查询质量门；
6. geometric candidate、loaded contact、frictionally stable、load-bearing、released/reengaged 五个阶段的判据、来源身份和独立输出，禁止用一个 engaged 布尔值合并；
7. separation/open、stick、slide、release、re-search、recontact/reengagement 的首版主状态、正交状态和事件映射；
8. standalone driver 或 C/System 外层编排的 unload→drive-off/unlock→reverse-search 或 lift-off→swept collision checks→recontact guards 操作协议；A 只拥有低层释放、碰撞和再接触事件，未实现回位时停在 release pose 并返回明确状态；
9. 接触力、A_on_B contact-only wrench、Rx、任务方向有效承载和参考点；
10. 梁位移/转角/根部量、弹簧压缩/余程/硬限位，以及释放时剩余储能；
11. accepted raw、committed event、rejected diagnostics、功与残量；
12. 首次有效承载距离、伪挂接、释放—再接触、多峰/接触循环原始记录与可选摘要；
13. 必须显式 unavailable 的材料损伤、针体强度和认证字段；
14. 首批图的坐标、分组、事件标记和交互筛选；
15. 解析平面/斜面/球冠/多峰、摩擦、梁、弹簧、事件和事务验收，包括“几何候选但零力”和“释放后不清零历史”的负例。

首批图至少讨论：
- Rx-x、Rx-t、uz-x 与完整力分量；
- 主状态/粘滑/弹簧状态带；
- 候选—受压—摩擦稳定—任务承载的阶段带，以及释放—再接触事件链；
- 接触点、法向、针轴和局部表面几何；
- 梁挠度/转角、弹簧压缩/余程；
- 事件前后放大、多峰记录；
- 残量、互补误差和功误差；
- Rt、d、alpha、mu、ks 变化的趋势对照。

硬边界：
- 不实现材料损伤、断裂能反演或针体强度认证；
- 不把接触峰值当二元成功；
- 释放后不重置 100 mm 总路径/时间；
- 不把梁/弹簧储能瞬时清零后跨到新的接触；回位路径未实现时必须停在 release pose；
- 不把 geometric candidate、loaded contact 或 frictionally stable 自动解释为 load-bearing；
- 不把弹簧、梁和接触柔顺重复计入；
- 不把 filtered/summary 数据替代 accepted 原始历史；
- 不允许 B/C 反向影响单刺本构。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md；
2. 冻结参数表、A 请求/响应、状态事件、canonical 输出、图形需求和验收；
3. 生成 docs/simulator_development/implementation_prompts/M03_SINGLE_SPINE_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验 M00–M02 和 A→B 的接口闭合；
5. 提交推送并报告后停止。

提交前严格执行 REQUIREMENTS_DISCUSSION_WORKFLOW 的 Git 安全交接：只精确暂存本任务文件，检查 cached diff，禁止使用 git add -A/git add .，不得纳入其他窗口的工作区改动。

不得在本窗口编码。
```

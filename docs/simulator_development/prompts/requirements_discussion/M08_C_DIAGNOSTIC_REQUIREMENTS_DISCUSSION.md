# M08 C DIAGNOSTIC 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。该模块在首版 A/B 完成后才启动。

## 提示词正文

```text
TASK_ID: M08_C_DIAGNOSTIC_REQUIREMENTS
PROMPT_VERSION: 0.1.2

本窗口只讨论并冻结 M08 C DIAGNOSTIC（受限 C 层合同安全诊断）的需求。它是首版 A/B 完成后的延期模块，不得反向阻塞或扩大 M07。

当前 B_TO_C 1.0.0 不支持 nonzero global +X、45°、local-y 或 rocking。M08 的目标不是算正式临界承载，而是实现请求/响应、合同覆盖、prescribed-s 诊断和安全拒绝，确保以后升级 B 2.x 时有清楚基线。

必须先分开三种身份：accepted C 1.0 当前主线使用 UX_PZ_BALANCED；MECHANISM_DERIVATION_FORMAL 0.2.0-proposed 建议的 C-R 是共同刚体 pose + 共同 s，并以 PRESCRIBED_XZ_RESIDUAL 做条件性诊断；C-I 只有实际存在四个独立 Z 执行器且双端、行程、作用线和功均冻结时才成立。M08 可以实现隔离的 proposed prescribed-s 诊断，但不能把 C-R 或 C-I 静默升级为 accepted/认证预紧。

开始前完整读取：
1. AGENTS.md、README.md、theory/README.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00、M02、M04、M05、M06、M07 requirements；
4. theory/evidence_reassessment/README.md 与 theory/evidence_reassessment/engineering_fixed_context.md；
5. theory/modules/C_INTEGRATED_MODEL.md；
6. theory/interfaces/B_TO_C_CONTRACT.md；
7. theory/system/SYSTEM_INTEGRATED_MODEL.md；
8. theory/review/DERIVATION_VERIFICATION_2026-07-17.md；
9. theory/paper/MECHANISM_DERIVATION_FORMAL.md 的 C-R/C-I 与合同边界；
10. theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md；
11. theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml。

讨论方式：
- 先逐项列出 allowed_now/prohibited_now，不让用户误以为能得到正式 Fcrit；
- 每轮最多问 3 个关于诊断范围、prescribed-s 输入或图形的问题；
- 依次讨论“schema/覆盖”“C-R 扫描”“拒绝记录”“输出/图”“升级与验收”；
- 任何解析 mock 都必须与可比较结果物理隔离。

本窗口必须关闭的问题：
1. accepted C 1.0、PROPOSED_SUPPLEMENT C-R 和 conditional C-I 的状态矩阵、允许输出和 amendment 门；
2. C-R 刚性参考体、共同 s 和 PRESCRIBED_XZ_RESIDUAL 的条件性诊断边界；
3. C-I 独立 Z 执行器为什么保持 conditional/unavailable；
4. zero increment、pure global-Z、conditional x/z preload trial；
5. 电机/传动坐标 q_m→s、速度/力矩到 Qs-drive/功率及损失的接口字段；缺传动证据时哪些量只能 prescribed/ideal；
6. 每个法向执行器的双端、source/target body、作用线、相对行程 eta_i、active wrench、主动功和保持反力；缺失时 certified actuator work/真实预紧认证 unavailable；
7. prescribed-s scan 的输入范围、机械安全上限来源和不自动锁定；
8. 四个 B response、wrench transport、内预紧和最弱分支原始特征；
9. guard/coverage/quality/unavailable 和硬件端口覆盖字段；
10. CertificationRejectionRecord 的请求 twist、不支持分量和零推进不变量；
11. Fcrit=null、curve/peak/events/work/state 不推进；
12. analytic mock 的目录、标签和不得比较规则；
13. 诊断图：四单元响应 vs s、内预紧、最弱分支、guard、contract/hardware coverage、拒绝原因；
14. B 2.0 xyz 与 B 2.x SE(3) 的明确升级门；
15. schema、零推进、幂等、wrench transport、功和拒绝分类验收。

硬边界：
- 不投影 local-y/rotation 到 x/z；
- 不旋转旧 B wrench 代替重求解；
- 不把四个单元峰值相加或经验缩放成 Fcrit；
- 不隐藏框架/导轨反力矩；
- 不用文献样机或未冻结 CAD 的传动公式替代本项目 q_m→s、端点、作用线和功映射；
- 缺执行器端口时不把 ideal/prescribed 功写成 certified actuator work；
- 不自动使用 100 mm 或 1 mm/s 作为 C 搜索；
- 不让 mock 进入 M05/M07 设计排序；
- 不把合同拒绝解释成零承载、失稳或抓附失败。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M08_C_DIAGNOSTIC_REQUIREMENTS.md；
2. 冻结 allowed/prohibited、schema、prescribed-s 输出、拒绝记录、图和验收；
3. 生成 docs/simulator_development/implementation_prompts/M08_C_DIAGNOSTIC_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验与 B_TO_C、M00/M04 和 C-R proposed 边界一致；
5. 提交推送并报告后停止。

提交前严格执行 REQUIREMENTS_DISCUSSION_WORKFLOW 的 Git 安全交接：只精确暂存本任务文件，检查 cached diff，禁止使用 git add -A/git add .，不得纳入其他窗口的工作区改动。

不得在本窗口编码或输出正式 C 承载结果。
```

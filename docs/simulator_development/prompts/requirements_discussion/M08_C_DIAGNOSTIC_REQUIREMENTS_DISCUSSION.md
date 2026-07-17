# M08 C DIAGNOSTIC 需求讨论窗口提示词

将下方正文完整复制到一个新的 Codex 窗口。该模块在首版 A/B 完成后才启动。

## 提示词正文

```text
TASK_ID: M08_C_DIAGNOSTIC_REQUIREMENTS

本窗口只讨论并冻结 M08 C DIAGNOSTIC（受限 C 层合同安全诊断）的需求。它是首版 A/B 完成后的延期模块，不得反向阻塞或扩大 M07。

当前 B_TO_C 1.0 不支持 nonzero global +X、45°、local-y 或 rocking。M08 的目标不是算正式临界承载，而是实现请求/响应、合同覆盖、prescribed-s 诊断和安全拒绝，确保以后升级 B 2.x 时有清楚基线。

开始前完整读取：
1. AGENTS.md；
2. docs/simulator_development/README.md、SIMULATOR_MODULE_PLAN.md、REQUIREMENTS_DISCUSSION_WORKFLOW.md；
3. 已冻结的 M00、M02、M04、M05、M06、M07 requirements；
4. archive/web_pro_derivation_2026-07-17/engineering_fixed_context/engineering_fixed_context.md；
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
1. C-R 刚性参考体、共同 s 和 PRESCRIBED_XZ_RESIDUAL 的条件性边界；
2. C-I 独立 Z 执行器为什么保持 conditional/unavailable；
3. zero increment、pure global-Z、conditional x/z preload trial；
4. prescribed-s scan 的输入范围、机械安全上限来源和不自动锁定；
5. 四个 B response、wrench transport、内预紧和最弱分支原始特征；
6. guard/coverage/quality/unavailable 字段；
7. CertificationRejectionRecord 的请求 twist、不支持分量和零推进不变量；
8. Fcrit=null、curve/peak/events/work/state 不推进；
9. analytic mock 的目录、标签和不得比较规则；
10. 诊断图：四单元响应 vs s、内预紧、最弱分支、guard、coverage、拒绝原因；
11. B 2.0 xyz 与 B 2.x SE(3) 的明确升级门；
12. schema、零推进、幂等、wrench transport 和拒绝分类验收。

硬边界：
- 不投影 local-y/rotation 到 x/z；
- 不旋转旧 B wrench 代替重求解；
- 不把四个单元峰值相加或经验缩放成 Fcrit；
- 不隐藏框架/导轨反力矩；
- 不自动使用 100 mm 或 1 mm/s 作为 C 搜索；
- 不让 mock 进入 M05/M07 设计排序；
- 不把合同拒绝解释成零承载、失稳或抓附失败。

用户确认冻结后：
1. 写 docs/simulator_development/requirements/M08_C_DIAGNOSTIC_REQUIREMENTS.md；
2. 冻结 allowed/prohibited、schema、prescribed-s 输出、拒绝记录、图和验收；
3. 生成 docs/simulator_development/implementation_prompts/M08_C_DIAGNOSTIC_IMPLEMENTATION_WINDOW_PROMPT.md；
4. 校验与 B_TO_C、M00/M04 和 C-R proposed 边界一致；
5. 提交推送并报告后停止。

不得在本窗口编码或输出正式 C 承载结果。
```

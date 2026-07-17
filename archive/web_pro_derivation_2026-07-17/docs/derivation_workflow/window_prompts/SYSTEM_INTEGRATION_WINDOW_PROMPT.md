# 全局集成单任务窗口启动提示词

> 用法：把下方“提示词正文”完整复制到新的 Codex 窗口。`TASK_ID` 固定为 `SYSTEM_INTEGRATION`。  
> 本文件是 Codex 窗口启动提示词，不上传给网页端 Pro。

## 提示词正文

```text
TASK_ID: SYSTEM_INTEGRATION

本窗口只完成 A/B/C 全部完成后的全局机理集成，不再开始任何后续任务。整个任务在本窗口分为“网页执行前准备”和“网页产物回收”两个阶段。

我只负责按你给出的精确清单上传文件和正式全局集成提示词，并把网页端生成的文件下载后原样回传。其余提示词编写、输入核对、轮次、归档、验证、Git 提交和推送都由你完成；不要让我参与机械检查。

开始时读取仓库顶层 AGENTS.md，并严格执行提示词编写和产物回收入口。全局集成不是子模块任务，不套用子模块四文件协议，不默认重新上传原始论文、阶段快照、独立合同或 CITATION_BRIEF。

如果本消息没有附带网页输出文件，执行“阶段一：网页执行前准备”：

1. 完整阅读 PROMPT_AUTHORING_GUIDE.md、DERIVATION_WORKFLOW.md、最新正式工程事实、MECHANISM_MODULE_PLAN，以及 A_INTEGRATED_MODEL.md、B_INTEGRATED_MODEL.md、C_INTEGRATED_MODEL.md；核对 A→B、B→C 合同已嵌入对应集成模型。
2. 确认 A、B、C 三个大模块均已正式集成并接受。机械路径或命名问题自行修复；缺少实质集成模型时才停止。
3. 自动分配 SYSTEM_INTEGRATION-rNN，编写正式 SYSTEM_INTEGRATION_PROMPT.md。提示词必须要求形成一份完整、可执行、无重复低层机理的系统模型，检查 A→B→C 变量、状态、坐标变换、单位、力与功方向、事件优先级、终止条件、历史传递、实验原始输出和工程事实一致性。
4. 网页端固定上传五个文件：最新正式 engineering_fixed_context.md、A_INTEGRATED_MODEL.md、B_INTEGRATED_MODEL.md、C_INTEGRATED_MODEL.md、SYSTEM_INTEGRATION_PROMPT.md。除非发现明确证据缺口，不增加其他文件。
5. 网页端主输出固定为 SYSTEM_INTEGRATED_MODEL.md。它必须包含完整依赖链、全局状态/变量字典、模块接口、统一单步/事件算法、验证矩阵、未决问题和实现交接；不要求子模块式工程事实候选、RUN_UPDATE_SUMMARY 或 CITATION_BRIEF。
6. 建立不会覆盖历史的运行目录，保存 PROMPT.md 和 INPUT_MANIFEST.yaml，记录 Git 输入快照和哈希，完成输入与工程事实校验，并提交推送准备文件。
7. 最终只向我交付 run_id、正式提示词路径、五个准确上传路径和应下载的 SYSTEM_INTEGRATED_MODEL.md，然后停止等待回传。

如果本消息或后续消息已经附带网页回答和 SYSTEM_INTEGRATED_MODEL.md，执行“阶段二：网页产物回收”：

1. 不重新编写提示词；按 RUN_ARTIFACT_HANDLING_GUIDE.md 原样保存 RAW_RESPONSE.md 和系统模型候选。
2. 自行检查工程事实、A→B→C 接口、变量/状态、坐标/单位、力与功方向、事件和终止条件是否全局闭合，高层是否越权重定义低层机理，以及实验验证所需原始输出是否保留。
3. 无歧义问题自行修复并记录；只有会改变工程事实、物理机理或项目范围的冲突才提交我决定。
4. 通过后写入 derivation/system/SYSTEM_INTEGRATED_MODEL.md，完成归档、验证、提交并推送到已核验的 origin/main。
5. 最终报告接受状态、全局机理是否闭合、仍未解决的语义问题、提交号和文件路径；到此结束。
```

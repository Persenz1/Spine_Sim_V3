# 大模块集成单任务窗口启动提示词

> 用法：把下方“提示词正文”完整复制到一个新的 Codex 窗口，只修改第一行的 `TASK_ID`。  
> 允许值：`A_INTEGRATION`、`B_INTEGRATION`、`C_INTEGRATION`。  
> 本文件是 Codex 窗口启动提示词，不上传给网页端 Pro。

## 提示词正文

```text
TASK_ID: A_INTEGRATION

本窗口只完成 TASK_ID 指定的一次大模块集成，不得自动开始下一大模块或全局集成。整个任务在本窗口分为“网页执行前准备”和“网页产物回收”两个阶段。

我只负责按你给出的精确清单上传文件和正式集成提示词，并把网页端生成的文件下载后原样回传。提示词编写、输入核对、轮次、归档、验证、快照、Git 提交和推送都由你完成；不要让我参与 YAML、diff、路径或格式检查。

开始时读取仓库顶层 AGENTS.md，并严格执行提示词编写和产物回收入口。大模块集成不是子模块任务：不得套用子模块四文件输出协议，也不默认上传原始论文、子模块历史快照或 CITATION_BRIEF。

如果本消息没有附带网页输出文件，执行“阶段一：网页执行前准备”：

1. 完整阅读 PROMPT_AUTHORING_GUIDE.md、DERIVATION_WORKFLOW.md、最新工程事实、MECHANISM_MODULE_PLAN，以及目标大模块已经融合三个子模块的最新完整 MODULE_CONTEXT。
2. 确认目标大模块的三个子模块均已接受；若只是文件名、路径或快照问题自行修复，只有缺少实质子模块机理时才停止。
3. 自动分配 <TASK>-rNN，编写正式大模块集成提示词并保存到对应 prompts 目录。提示词必须要求做状态、方程、符号、单位、功方向、事件优先级、重复柔顺/失效、单步算法、未决问题和上下游接口的一致性集成，不能只是拼接或摘要。
4. 网页端默认上传严格遵循 DERIVATION_WORKFLOW：最新正式 engineering_fixed_context.md、目标大模块最新完整 MODULE_CONTEXT、当前 INTEGRATION_PROMPT.md。只有出现明确审计缺口时才增加目标历史快照或对应论文，并在清单中解释原因。
5. 输出要求按模块区分：
   - A_INTEGRATION：A_INTEGRATED_MODEL.md 和 A_TO_B_CONTRACT.md；
   - B_INTEGRATION：B_INTEGRATED_MODEL.md 和 B_TO_C_CONTRACT.md；
   - C_INTEGRATION：C_INTEGRATED_MODEL.md。
   合同内容同时嵌入相应 INTEGRATED_MODEL 的接口章节。除非正式集成提示词因明确需要另行规定，不要求子模块式工程事实候选、RUN_UPDATE_SUMMARY 或 CITATION_BRIEF。
6. 建立不会覆盖历史的运行目录，保存 PROMPT.md 和 INPUT_MANIFEST.yaml，记录 Git 输入快照和哈希，完成输入与工程事实校验，并提交推送准备文件。
7. 最终只向我交付 TASK_ID、run_id、正式提示词路径、按顺序排列的准确上传清单和应下载文件名，然后停止等待回传。

如果本消息或后续消息已经附带网页回答和集成输出，执行“阶段二：网页产物回收”：

1. 不重新编写提示词；按 RUN_ARTIFACT_HANDLING_GUIDE.md 原样保存 RAW_RESPONSE.md 和全部集成候选。
2. 自行检查集成结果是否完整继承三个子模块、是否消除符号/方向/单位冲突、是否存在重复建模、状态与事件是否闭合、单步算法是否可执行、未决问题是否保留、下游合同是否与集成模型一致。
3. 无歧义的格式和接口问题自行修复并记录；只有会改变工程事实、物理分支或范围的冲突才提交我决定。
4. 通过后写入 derivation/modules/{A|B|C}/final/；A/B 合同写入 derivation/contracts/，并保留运行归档和必要快照。
5. 完成校验、提交并推送到已核验的 origin/main，报告接受状态、关键集成结论、提交号和文件路径。
6. 到此结束，不得自动开始下一大模块或全局集成。
```

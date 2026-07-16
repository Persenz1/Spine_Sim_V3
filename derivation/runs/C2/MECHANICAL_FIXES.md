# C2-r01 机械修复记录

> 结论：仅执行归档命名和接受态元数据规范化；没有修改物理方程、工程事实、证据或未决边界。

## 原件与候选工作副本

- 四个网页下载文件按浏览器实际文件名原样保存到 `raw_downloads/`；归档 SHA-256 与下载源逐文件一致。
- 将四个原件复制为规范工作文件名。`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md` 均与各自原件逐字节一致。
- `RUN_UPDATE_SUMMARY.yaml` 与 `RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 逐字节一致；YAML 原件可直接解析，无需缩进、引号、类型或字段修复。
- 接受后 `current/C_MODULE_CONTEXT.md` 已正常滚动到 C2；因此将 `validate_inputs.py` 的旧运行复验改为按 `repository_commit` 读取冻结的 C1 上传版本，避免错误要求当前工作区继续保留旧哈希。

## 接受态元数据规范化

通过语义审查后，仅在 `current` 与 `after_C2` 历史快照中执行下列四项确定性替换：

1. `上下文候选版本` 改为 `上下文版本`；
2. `当前状态: candidate` 改为 `当前状态: accepted`；
3. C1 历史自检中的“本候选”改为“本滚动上下文”；
4. C2 理论状态由“完成候选”改为“已完成并经 C2-r01 审查接受”。

候选原件和 `MODULE_CONTEXT_CANDIDATE.md` 均未回写。上述替换只改变归档/接受状态说明，不改变任何物理含义。

## 无需修复的项目

- 工程事实候选与正式 `engineering_fixed_context 1.0.0` 基线逐字节一致。
- `engineering_context_delta` 已符合 `operation: none` 合同。
- 本地引用编号、GPT 通用知识边界、运行身份、输出路径和 C3 范围边界均合规。

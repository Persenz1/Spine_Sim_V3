# B1-r01 机械与无歧义完整性修复记录

四个网页下载原件按原文件名和原始字节完整保存在 `derivation/runs/B1/raw_downloads/`。`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md` 均与对应下载原件逐字节一致；以下修复只作用于接受版滚动上下文或本地归档路径。

1. 将网页下载文件名中的浏览器重复编号 `(3)` 规范化为本轮固定候选/归档文件名；原始文件名仍保留在 `raw_downloads/` 和 `INPUT_MANIFEST.yaml`。
2. 将接受版 `B_MODULE_CONTEXT.md` 文件头的“上下文候选版本”规范为“上下文版本”，并把状态从 `candidate` 更新为 `accepted`；版本仍为 `0.1.0`，完成阶段仍为 `B1`。
3. 将第 15.4 节与文件头冲突的“当前状态仍为 candidate”同步为接受状态，并明确 `accepted` 只表示 B1 数据与运动学合同通过本轮审查，不表示代码、真实 CAD、表面测量或实验已经完成。

工程事实候选与正式 `engineering_fixed_context 1.0.0` 逐字节一致；运行摘要和引用说明无需修复。本轮没有工程事实变化，也没有需要人工选择的物理分支。


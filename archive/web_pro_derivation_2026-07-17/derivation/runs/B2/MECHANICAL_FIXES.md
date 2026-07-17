# B2-r01 机械与无歧义完整性修复记录

四个网页下载原件按浏览器实际文件名和原始字节完整保存在 `derivation/runs/B2/raw_downloads/`。`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md` 均与对应下载原件逐字节一致；以下修复不改变物理含义。

1. 将浏览器添加的重复编号 `(2)`、`(4)` 规范化为本轮固定候选/归档文件名；原始文件名、字节数和 SHA-256 仍保留在 `raw_downloads/` 和 `INPUT_MANIFEST.yaml`。
2. 将接受版 `B_MODULE_CONTEXT.md` 文件头的“上下文候选版本”规范为“上下文版本”，并把状态从 `candidate` 更新为 `accepted`；版本保持 `0.2.0`，完成阶段保持 `B2`。
3. 将接受版正文中仅表示整份文件归档状态的四处“候选上下文/本候选”措辞同步为“完整上下文/本接受版”；针级候选状态、候选模型、候选相关性、候选平衡和指标候选等物理或数值术语保持不变。
4. 规范化接受版文件末尾的冗余空行。接受版与网页候选的其余内容逐字一致；接受版和 `B_MODULE_CONTEXT_after_B2.md` 历史快照逐字节一致。
5. `validate_inputs.py` 改为在 current 已推进到 B2 后，从本轮冻结 Git 提交恢复 B1 上传输入，并以 B1 历史快照和接受报告复验前置结果；这只修复运行后可复现性，不改变本轮上传清单或冻结哈希。
6. 仓库此前没有 `.gitattributes`，且本机 Git 开启 `core.autocrlf=true`。为保证网页原件和完整文本回答在未来检出时仍保持原始字节，新增仅覆盖 `derivation/runs/**/raw_downloads/**` 与 `derivation/runs/**/RAW_RESPONSE.md` 的 `-text` 规则；验证器同时检查工作副本、Git 索引和清单哈希一致。

`RUN_UPDATE_SUMMARY.yaml` 可直接解析且无需修复；其接受归档与候选及原始下载逐字节一致。工程事实候选与正式 `engineering_fixed_context 1.0.0` 逐字节一致，未发生工程事实变化。引用说明无需修复并仅在本轮运行目录归档。本轮没有需要人工选择的工程事实或物理机理分支。

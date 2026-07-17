# B3-r01 机械与无歧义完整性修复记录

四个网页下载原件按浏览器实际文件名和原始字节完整保存在 `derivation/runs/B3/raw_downloads/`。所有原件的字节数和 SHA-256 已写入 `INPUT_MANIFEST.yaml`；原件不做任何回写。以下处理均不改变物理含义。

1. 将浏览器重名后缀 `(4)`、`(5)` 规范化为本轮固定候选/归档文件名：`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`。
2. 网页原始 `B_MODULE_CONTEXT(4).md` 第 44.4 节的局部关系中，`\text{branch/history}` 的反斜杠被下载文本损坏为一个制表符加 `ext{branch/history}`。依据同一公式、LaTeX 语法和正文语义，工作副本唯一恢复为 `\text{branch/history}`；原件保持不变。修复使候选从 164224 字节变为 164225 字节，SHA-256 从 `4082880404fe0fa681accae2482b809363be3ce31f692b4be26068d260b97941` 变为 `d126f12ace3840347d3d46e8d890b689e1fe8581b698a49f48b907c8deb2674a`。
3. 将通过审查的接受版文件头状态从 `candidate` 更新为 `accepted`，把仅描述整份文档归档状态的“最新完整候选上下文”“本候选版”和 `B_MODULE_CONTEXT 0.3.0 candidate` 同步为接受态；`UnitCapabilityState`、特征、数值分支和模型等仍属候选的技术术语保持不变。
4. 将“候选表示尚未完成人工接受”的归档说明改为“accepted 表示理论与数据合同已通过本地语义审查”，同时保留代码实现、参数标定、真实表面求解和实验验证尚未完成的边界。
5. 接受版规范保存到 `derivation/modules/B/current/B_MODULE_CONTEXT.md`，并建立逐字节一致的 `derivation/modules/B/history/B_MODULE_CONTEXT_after_B3.md`；两者 SHA-256 均为 `35e072fc730e2e74edc1d2c3cdc392382566b0b9ee2a2edd4947585038c4bc21`。
6. `RUN_UPDATE_SUMMARY.yaml` 可直接解析且无需内容修复；其接受归档与候选及原始下载逐字节一致。工程事实候选和引用说明同样与原始下载逐字节一致。
7. `validate_inputs.py` 在 current 推进到 B3 后改为从阶段一冻结 Git 提交恢复网页实际上传的 B2 `0.2.0 accepted` 上下文，并以 B2 历史快照和已归档接受报告复验前置结果；这只修复运行后可复现性，不改变本轮上传输入或冻结哈希。
8. 仓库已有 `.gitattributes` 对 `raw_downloads` 和 `RAW_RESPONSE.md` 禁用文本换行转换；本轮沿用该规则保护四个原件及完整文本回答的原始字节。

本轮没有工程事实变化，没有需要人工选择的物理机理分支，也没有执行 B 大模块集成、生成 `B_TO_C_CONTRACT` 或开始 C1。

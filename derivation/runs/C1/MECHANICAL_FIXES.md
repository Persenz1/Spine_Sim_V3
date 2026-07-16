# C1-r01 机械与无歧义完整性修复记录

四个网页下载原件按浏览器实际文件名和原始字节完整保存在 `derivation/runs/C1/raw_downloads/`。所有原件的字节数和 SHA-256 写入 `INPUT_MANIFEST.yaml`；原件不做任何回写。以下处理均不改变物理含义。

1. 将浏览器重名后缀 `(6)` 规范化为本轮固定候选/归档文件名：`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml`、`RUN_UPDATE_SUMMARY.yaml` 和 `CITATION_BRIEF.md`。
2. 四份规范化候选/归档文件均与各自下载原件逐字节一致；没有公式、YAML、路径、模板占位符或语义内容需要修复。
3. 将通过审查的模块上下文接受版文件头状态从 `candidate` 更新为 `accepted`；正文中的“候选”均描述试探状态、候选停止点、候选策略或待标定方法，属于技术语义，保持不变。
4. 接受版规范保存到 `derivation/modules/C/current/C_MODULE_CONTEXT.md`，并建立逐字节一致的 `derivation/modules/C/history/C_MODULE_CONTEXT_after_C1.md`；两者 SHA-256 均为 `daa5702355fb56cf98cdd8194717fbe8e2b41311c9fd0ef29010484bd5f8654c`。
5. `RUN_UPDATE_SUMMARY.yaml` 可直接解析且无需内容修复；其接受归档、候选和原始下载逐字节一致。工程事实候选和引用说明同样与原始下载逐字节一致。
6. 工程事实候选与正式 `engineering_fixed_context 1.0.0` 逐字节一致；本轮没有工程事实变化、没有需要人工选择的物理机理冲突，也没有执行 C2、C3、C 大模块集成或全局集成。
7. `CITATION_BRIEF.md` 中唯一外部网址指向 Northwestern University 的 Modern Robotics 第 3 章页面；页面明确覆盖 SO(3)/SE(3)、twist、adjoint 和 wrench 表达变换，仅作坐标/功对偶交叉检查，不引入工程数值。该文件只在本轮运行目录归档。
8. 仓库已有 `.gitattributes` 对 `raw_downloads` 和 `RAW_RESPONSE.md` 禁用文本换行转换；本轮沿用该规则保护四个原件及完整文本回答的原始字节。

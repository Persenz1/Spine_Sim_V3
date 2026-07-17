# C3-r01 机械修复记录

> 结论：仅执行原件归档、规范文件命名和接受态元数据转换；没有修改物理方程、工程事实、证据或未决边界。

## 原件与候选工作副本

- 四个网页下载文件按浏览器实际文件名原样保存到 `raw_downloads/`；归档字节数和 SHA-256 与下载源逐文件一致。
- 将四个原件复制为规范工作文件名：`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md`、`RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 和 `CITATION_BRIEF.md`。四个工作副本均与对应原件逐字节一致。
- `RUN_UPDATE_SUMMARY.yaml` 与 `RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 逐字节一致；YAML 原件可直接解析，无需缩进、引号、数据类型或字段修复。
- `RAW_RESPONSE.md` 保存随四个附件收到的网页文本回答；原始回答和 `raw_downloads/` 均受 `.gitattributes -text` 保护。
- `RAW_RESPONSE.md` 原文含行尾空格；为满足“原样保存”要求予以保留，规范工作文件的 whitespace 检查不把该字节保真原件当作待修复文本。

## 接受态元数据规范化

通过完整语义审查后，仅在 `current` 与 `after_C3` 历史快照中执行下列八项确定性转换：

1. 文件头 `上下文候选版本` 改为 `上下文版本`；
2. 文件头 `当前状态: candidate` 改为 `当前状态: accepted`；
3. C3 完成状态改为“已完成并经 `C3-r01` 审查接受”；
4. `C3LoadRequest` 中的上下文状态从 `candidate` 改为 `accepted`；
5. 单元显著退化事件函数族的文档状态从 `candidate` 改为 `accepted`；
6. `F_crit` 稳定可达分支定义的文档状态从 `candidate` 改为 `accepted`；
7. 完成判据中的“已形成 candidate”改为“已经 `C3-r01` 审查接受”；
8. 最终自检中的文件状态从 `candidate` 改为 `accepted`。

候选原件和 `MODULE_CONTEXT_CANDIDATE.md` 均未回写。这些转换只改变归档/接受状态说明，不改变任何物理含义。

## 旧运行复验适配

- C3 接受后，`current/C_MODULE_CONTEXT.md` 已从输入时的 0.2.0 滚动为 0.3.0；因此将 `validate_inputs.py` 的旧运行复验改为按 `repository_commit` 读取冻结的 0.2.0 上传版本。
- 该适配不改变阶段一输入清单、哈希或 Git 提交，只避免错误要求当前工作区继续保持旧上下文哈希。

## 无需修复的项目

- 工程事实候选与正式 `engineering_fixed_context 1.0.0` 基线逐字节一致。
- `engineering_context_delta` 已符合 `operation: none` 合同，无需人工审批。
- C1/C2 已接受主体在候选中保持一致；C3 仅更新文件头/权威说明并追加第 31–48 节。
- 本地引用编号、工程事实 ID、GPT 通用知识边界、运行身份、输出路径以及“不开始 C 集成”的任务边界均合规。

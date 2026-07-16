# C_INTEGRATION-r01 机械与无歧义完整性修复记录

网页下载原件按原文件名和原始字节完整保存在 `derivation/runs/C_INTEGRATION/raw_downloads/C_INTEGRATED_MODEL.md`。`C_INTEGRATED_MODEL_CANDIDATE.md` 与下载原件逐字节一致；以下修复只作用于正式接受版。

1. 将正式 C 模型从网页交付身份 `1.0.0-candidate / candidate` 规范为本地审查后的 `1.0.0 / accepted`，并同步文件头、`CModelIdentity`、公共认证等级说明、完成判据标题和最终认证声明。该修复只表示 C 理论与数据接口集成已经审查接受，不将 B 2.x、求解器、数值验证或实验写成已完成。
2. 将第 1.1 节异常迁移图中连写的 `UNCERTIFIED_STOPPED -> NUMERICAL_OR_TRANSACTION_STOPPED` 改为从任一 trial 阶段分别进入两者之一的并列分支。候选文件后续明确将未认证停止和数值/事务停止定义为互异类别，并都要求保留最后有效接受态；因此这是无歧义的状态图符号修正，不改变优先级、物理分支或提交政策。
3. 作为事件、峰值、试探状态或事务语义的 `candidate`、“候选”和 `*_CANDIDATE` 均保留；它们不是文件接受身份。

本轮未修改 `engineering_fixed_context 1.0.0`、`C_MODULE_CONTEXT 0.3.0 accepted` 或 `B_TO_C 1.0.0 accepted`，未新增或选择工程数值、材料分支、物理范围或全局集成语义，没有需要人工决定的语义冲突。

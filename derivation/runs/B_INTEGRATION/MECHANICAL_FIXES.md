# B_INTEGRATION-r01 机械与无歧义完整性修复记录

两个网页下载原件按原文件名和原始字节完整保存在 `derivation/runs/B_INTEGRATION/raw_downloads/`。`B_INTEGRATED_MODEL_CANDIDATE.md` 和 `B_TO_C_CONTRACT_CANDIDATE.md` 与对应下载原件逐字节一致；以下修复只作用于正式接受版。

1. 将正式 B 模型和 B→C 合同从网页交付身份 `1.0.0-candidate / candidate` 规范为本地审查后的 `1.0.0 / accepted`，并同步独立合同文件头、嵌入合同身份表和 B 模型状态表。
2. 将与交付身份绑定的“候选合同/候选版本/合同接受前”表述同步为“已接受的理论与数据合同/本版本/合同实现验收前”。该修复仅消除接受后的状态时态矛盾，不将理论接受写成代码、CAD、材料参数或实验已验证。
3. 不修改作为事务、事件或能力语义的 `FINAL_COMMIT_CANDIDATE`、`POST_EVENT_CANDIDATE`、候选特征和平台候选等词；这些不是文件接受状态。
4. 候选文件中含标记行的公共合同块 SHA-256 为 `c4bfbdf2fbbf7ba5f9e827939d2e1023b23fb8a2a92be0fb5fe59cd0b289c823`，与网页回答声明一致。接受版因上述身份文字同步变为 `caa451e79c890723ed1c7c7a969dd461c6273751bc2c8a533e8ccf90e6324201`；模型嵌入块与独立合同块仍逐字一致。

本轮没有修改 `engineering_fixed_context 1.0.0`，没有新增或选择工程数值、材料分支、物理范围或 C 层机理，也没有需要人工决定的语义冲突。

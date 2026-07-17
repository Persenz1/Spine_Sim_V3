# SYSTEM_INTEGRATION-r01 机械与无歧义完整性修复记录

网页下载原件按原文件名和原始字节完整保存在 `derivation/runs/SYSTEM_INTEGRATION/raw_downloads/SYSTEM_INTEGRATED_MODEL.md`。`SYSTEM_INTEGRATED_MODEL_CANDIDATE.md` 与下载原件逐字节一致；以下修复只作用于正式接受版 `derivation/system/SYSTEM_INTEGRATED_MODEL.md`。

1. 将文件头的规范状态明确登记为 `accepted`。该状态只表示 A/B/C 全局理论、接口、状态、事件、事务、验证规范和实现交接已经通过本轮审查；没有把代码、数值、参数或实验写成已认证。
2. 将浏览器为本地重名下载生成的 `engineering_fixed_context(13).md` 和三个 `*_INTEGRATED_MODEL(1).md` 显示名恢复为冻结输入清单中的五个规范上传文件名。下载原件给出的 SHA-256 与输入清单逐项一致，因此该修复不改变输入身份或内容。
3. 补充 `StandaloneValidationRequest`，并明确内部 `SYSTEM_EXECUTE` 门面接收互斥并集 `SystemRequest | StandaloneValidationRequest`：公开 `SystemRequest` 仍只调用 C 系统主路径，A/B standalone 使用独立请求、运行 ID、状态和 `DamageStore` 分支。该修复消除了原文“公开请求只允许 C 操作”与统一伪代码可调度 standalone 之间的软件 schema 歧义，不改变任何低层核或物理路径。
4. 将变量字典中 B 的 `contact-only 和` 补为 `contact-only 净和`；同时唯一明确 B→C 运输式中的 `S_i` 是响应声明的源表达坐标，当前 B 1.0 静态局部响应满足 `S_i=F_Ai`、`R_GSi=R_Gi`。这只补齐已有 frame/transform/version 规则，未新增坐标或变换。
5. 明确“终止状态可提交”只允许提交仍满足全部 accepted 不变量的最后有效状态、合法事件点/物理边界状态和独立终止证据；不可行平衡 trial、失稳一侧 trial 或其他非法候选本身不得成为 accepted 物理状态。该修复把原文已有的 last-valid、trial/commit 和全局不变量语义落实到终止表，不改变终止分类或能力定义。

本轮未修改 `engineering_fixed_context 1.0.0`、A/B/C 三个 `1.0.0 accepted` 模型、`A_TO_B 1.0.0 accepted` 或 `B_TO_C 1.0.0 accepted`，未新增或选择工程数值、材料模型、物理分支或项目范围。没有需要用户决定的歧义工程/物理冲突。

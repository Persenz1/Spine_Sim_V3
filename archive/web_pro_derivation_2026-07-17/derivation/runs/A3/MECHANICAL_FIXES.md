# A3-r01 机械与无歧义完整性修复记录

四个网页下载原件按原文件名和原始字节完整保存在 `derivation/runs/A3/raw_downloads/`。`MODULE_CONTEXT_CANDIDATE.md`、`ENGINEERING_FIXED_CONTEXT_CANDIDATE.md` 和 `RUN_UPDATE_SUMMARY_CANDIDATE.yaml` 保留网页候选内容；以下修复只作用于接受版滚动上下文或本轮本地归档引用说明。

1. 将接受版 `A_MODULE_CONTEXT.md` 文件头状态从 `candidate` 改为 `accepted`；版本仍为 `0.3.0`，完成阶段仍为 `A3`。
2. 候选在 `moment_augmented` 可选分支中把 `\Phi_M` 写入首次失效面的最大值，但只定义了力矩广义应力 `\mathbf q_M`。接受版补入通用、标定驱动的无量纲接口

   $$
   r_M=\mathcal G_M(\mathbf q_M;\Theta_M),
   \qquad
   \Phi_M=r_M-1,
   $$

   并明确无力矩容量标定时关闭该分支。这只闭合候选已声明的可选接口，不选择力矩容量函数、不新增参数值，也不改变首版材料主线。参数表中的未定义符号 `\mathbf Q_m,\mathbb H_m` 同步规范为正文已定义的 `\mathbf R_{m,k},\mathbb H_k`。
3. Bažant–Oh crack-band 论文的 Northwestern 作者副本地址在本轮两次读取超时；接受版上下文和本轮 `CITATION_BRIEF.md` 将其替换为同一论文、同一 DOI 的 Springer 官方出版页 `https://link.springer.com/article/10.1007/BF02486267`。论文身份、证据用途和适用边界均未改变。

工程事实候选与正式 `engineering_fixed_context 1.0.0` 逐字一致；运行摘要无需语义修复。本轮没有工程事实变化，也没有需要人工选择的物理分支。

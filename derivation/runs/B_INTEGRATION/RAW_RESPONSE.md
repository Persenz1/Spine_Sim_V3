已依据工程固定上下文、B 集成提示词和 `B_MODULE_CONTEXT 0.3.0 accepted` 完成集成，未引入额外文件、未固定未决参数，也未开始 C1/C2/C3 或全局集成。  

1. [下载 B_INTEGRATED_MODEL.md](sandbox:/mnt/data/B_INTEGRATED_MODEL.md)
   包含完整 B 集成模型：规范对象与所有权、坐标和功方向、统一方程链、柔顺/载荷/失效去重、状态机、事件与级联、standalone/C embedded 分层、可执行单步算法、验证矩阵、风险和未决项，以及完整公共合同正文。

2. [下载 B_TO_C_CONTRACT.md](sandbox:/mnt/data/B_TO_C_CONTRACT.md)
   可由 C 层独立使用，冻结 C→B 输入、B→C 输出、wrench 装配、事件归约、共享损伤、嵌套事务、原子提交、完整回调条件、失败分类和合同验证。

自检结果：

* 只生成上述两个规定文件。
* 两个文件中的 `BEGIN/END B_TO_C_PUBLIC_CONTRACT` 标记块逐字一致。
* 公共合同块 SHA-256：`c4bfbdf2fbbf7ba5f9e827939d2e1023b23fb8a2a92be0fb5fe59cd0b289c823`。
* `P_z` 只在 B 外层施加一次；contact-only wrench、主动推力、控制反力和约束反力已分栏。
* `rocking=on` 的真实单元转动明确返回 `KINEMATIC_MODE_UNSUPPORTED`，没有通过旋转旧 wrench 或投影运动伪装支持。
* 文件状态均为理论与数据合同层面的 `candidate`，未声称源代码、CAD、材料参数或实验已经验证。

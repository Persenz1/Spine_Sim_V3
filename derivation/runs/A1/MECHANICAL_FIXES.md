# A1-r01 机械修复记录

原始网页产物保存在本目录的候选文件中，未被回写修改。通过审查的滚动上下文位于 `derivation/modules/A/`。

1. 将接受版文件头状态由 `candidate` 改为 `accepted`。
2. 修正各向异性 PSD 的旋转变量漏用：原候选先定义 $\mathbf q'=\mathbf R(-\theta_0)\mathbf q$，随后却以 $\mathbf q$ 直接计算椭圆等效波数，使 $\theta_0$ 不生效。接受版改为

   $$
   q_e(\mathbf q)=\sqrt{{\mathbf q'}^\mathsf T\mathbf A\mathbf q'},
   $$

   并明确 $\mathbf A$ 定义于主轴坐标系。该修复保持原文“旋转方向由 $\theta_0$ 控制”的唯一可确定含义。

未修改工程事实候选、运行摘要或引用说明。

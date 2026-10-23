# UPA单极化单流与双流实验

已完成Docomo结构核对及专项验证、400位置单流正式扫描、32位置单极化双流最小验证。CPU与UE分别说明和出图，主参考是完美CSI直接SVD；普通方法使用带噪观测，400 MHz直接换算。

## 报告

| 内容 | Markdown | Word |
|---|---|---|
| 单流正式结果及CPU与UE解释 | [400位置报告](docs/UPA单流400位置正式实验报告.md) | [转发版](docs/UPA单流400位置正式实验报告.docx) |
| 如何从单流扩展双流及最小结果 | [双流扩展报告](docs/UPA单极化双流扩展验证报告.md) | [转发版](docs/UPA单极化双流扩展验证报告.docx) |
| Docomo论文对应与检查 | [专项说明](docs/Docomo结构适配与专项验证.md) | 包含于单流Word报告 |
| 最终信息与反馈口径 | [口径和推进顺序](docs/当前实验口径与推进顺序.md) | 包含于两份Word报告 |

## 数据与复现

- [单流400位置](results/single_stream_V3_full400/README.md)：98,800条记录，19个曲线标签，16个物理配置；原始明细为无损gzip，CPU与UE各11组图。
- [双流32位置](results/dual_stream_minimal32/README.md)：LOS和混合信道，1,408条记录，576个可实施方法配对，CPU与UE各7组图。
- [Docomo检查](results/docomo_validation/README.md)：48项专项检查、701项协议检查及42项UPA/POS回归。
- [双流单元检查](results/dual_stream_unit/README.md)：54项检查。
- [运行和有效载荷格式](README_单流任务二.md)，[CPU说明](docs/CPU说明.md)，[UE说明](docs/UE说明.md)。

单流入口为run_single_stream_task2，双流入口为run_dual_stream_minimal，统一绘图入口为plot_precoding_results。只添加本目录，不要对整个历史副本使用addpath(genpath(...))。解压或重新运行均使用新输出目录，避免覆盖现有结果。

V3正式扫描不额外运行同算法完美CSI配对；之前V2小样本配对仅供诊断。第二流复用每AP空间波束、第一相位仅缩放，UE只增加一组相位，CPU不增加空间反馈。尚未进行完整双流参数扫描。

## 历史材料

6.位置反馈方案为冻结公共输入和基础依赖，本轮未修改。历史双极化多流扩展与旧single_stream_full属于此前实验；UPA_POS_V1和UPA_V2结果是修复阶段记录，不混入本次正式均值。第5、第6目录此前已建立CPU/UE相位口径，本轮恢复第8目录一致性并补齐协议，不将这些原则描述为首次提出。

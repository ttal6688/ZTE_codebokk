# 单流CPU链路实现说明

本文件说明当前代码的CPU链路，不是新增UPA性能报告。已有实现和结果采用单极化单流ULA，UPA尚未适配；原双极化双流报告属于历史材料。

## 计算过程

1. UE针对3个参考AP提取HAQSE频率或DFT索引。HAQSE每参考AP频率14 bit；DFT每参考AP发送一个空间索引。位置方案先从这些量化HAQSE方向定位，再编码二维坐标。
2. CPU由频率或方向索引定位，或者解码位置；随后生成B个AP的空间波束。HAQSE/DFT参考AP保留直接方向对应波束，其他AP按估计位置推断；POS全部AP使用解码位置。
3. geometry_channel使用估计位置、公开AP坐标和朝向，为全部B个AP构造4×BN的平面LOS模型。对该矩阵求主右奇异向量，再投影到每AP空间波束，得到AP间相位。
4. 每AP发送同一个数据符号s，经一个空间波束和一个复相位加权。联合预编码只有一列；每AP幅度统一为1/√B。不存在两种极化的混合，也没有2×2双流系数矩阵。
5. 用真实仿真信道评估接收功率和单流速率。CPU设计几何方案时不读取真实信道，但最终性能评价使用真实信道。

关键实现位于 [run_single_stream_task2.m](../run_single_stream_task2.m) 的partial_designs、paired_design、geometry_channel、co_phases和evaluate_design。

## 信息规模与计算规模

固定R=3使HAQSE/DFT的参考消息来源数不随B增长；POS反馈二维坐标。CPU仍须为所有B个AP推断波束和相位，模型维度4×BN随B、N变化。不能将消息来源数写成固定信道估计矩阵维度。

CPU链路只计入UE上传的空间反馈有效载荷，不额外反馈UE计算的AP间相位。B=8、N=64时，HAQSE为42 bit、DFT为27 bit、POS为24 bit。这些字段不含协议头、码本配置或坐标bit分配的额外说明。

## 仿真结果的归属

CPU图中的HAQSE/DFT/POS为CPU几何链路；Type-I/II使用UE观测CSI，SVD使用真实CSI，均为共享对照。Docomo只在UE链路比较。原400位置输出的CPU部分有45,600条记录，对应19个扫描设置标签、每设置6种方法。

数据位于 [single_stream_full](../results/single_stream_full/README.md)。本次整理不新增性能结论；已有结果不支持UPA或双极化的结论。

## 待核实边界

位置误差会影响几何相位，多径也不能由单一LOS模型完整恢复。旧CSV中的cpu_estimation_dimension=3仅表示参考AP数量，POS的2表示坐标维数；它不是矩阵秩或CPU复杂度测量。位置bit分配与独立整数消息解码仍待核查，详见 [整理说明](整理说明.md)。

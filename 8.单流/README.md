# UPA单极化单流仿真

当前版本为 **UPA_SINGLE_PROTOCOL_V2**。已修正联合主模式基线、Type-II正交分组、统一UE相对相位量化、完整反馈编解码和CPU/UE信息边界；位置反馈仍从连续HAQSE频率定位，只量化一次坐标。

- [本轮修正与验证报告](docs/单流基线与反馈协议修正报告.md)：修改依据、实现、验证结果和结论边界。
- [运行方式与反馈格式](README_单流任务二.md)。
- [CPU独立说明](docs/CPU说明.md)。
- [UE独立说明](docs/UE说明.md)。
- [两位置LOS/MIX验证](results/single_stream_UPA_V2_verify_final/README.md)。
- [四位置MIX流程与图表验证](results/single_stream_UPA_V2_smoke4_final/README.md)。

本轮覆盖6个不同预定位置、64个信道/参数案例、1,216条记录。它们是最小实现验证，不是新的400位置性能排名；同一案例中的CPU参考行不视为额外独立样本。CPU与UE图表分别保存。

## 当前目录和历史材料

`run_single_stream_task2.m`、`+sstr/`和本目录直属的V2结果是当前实现。`6.位置反馈方案`提供冻结的公共配置及基础依赖，本轮未修改。`1`至`5`是阶段性复制材料；`历史双极化多流扩展`保留此前的双极化实验，不代表本轮的单极化或双流结果。

原来的`results/single_stream_full`是旧场景归档。`single_stream_UPA_POS_V1_*`是前一阶段只修复UPA及POS前端的记录，不能用于说明V2已经修正的基线和完整消息协议。历史说明见[前阶段报告](docs/UPA与位置反馈修复说明.md)和[目录整理记录](docs/整理说明.md)。

请只加入本目录，由入口自动加载依赖；不要对整个仓库使用`addpath(genpath(...))`，避免混入历史同名包。新实验仅使用UPA，单极化、单流；本轮没有扩展双流。

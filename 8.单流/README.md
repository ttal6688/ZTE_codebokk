# 单流任务二目录说明

本目录的单流入口为 [run_single_stream_task2.m](run_single_stream_task2.m)，使用说明见 [单流运行与实验口径](README_单流任务二.md)。CPU 与 UE 的计算过程分别见 [CPU说明](docs/CPU说明.md) 和 [UE说明](docs/UE说明.md)。

**当前实现和已保存结果实际采用单极化单流 ULA，带宽换算为400 MHz；尚不是约定的UPA版本。** 本次只整理说明、链接和历史归属，保留计算代码及原始结果。后续正式报告统一采用UPA，CPU和UE分开；UPA适配完成前，这些归档结果不能作为UPA实验结论。

## 当前入口

| 内容 | 文件或目录 | 归属 |
|---|---|---|
| 单流运行与公共配置 | [README_单流任务二.md](README_单流任务二.md) | 当前代码口径 |
| CPU处理链路 | [docs/CPU说明.md](docs/CPU说明.md) | 几何消息及CPU共相位 |
| UE处理链路 | [docs/UE说明.md](docs/UE说明.md) | 观测CSI及UE共相位 |
| 已有数据与图索引 | [results/single_stream_full/README.md](results/single_stream_full/README.md) | 原分支已有结果 |
| 整理范围与待完成事项 | [docs/整理说明.md](docs/整理说明.md) | UPA状态及已知实现边界 |
| 原双极化副本 | [历史双极化多流扩展/归档说明.md](历史双极化多流扩展/归档说明.md) | 历史材料 不属于新增单流实验 |

原来的“7.单流扩展”包含双极化模型、单双流运行程序和旧MD/Word报告，本次恢复其真实归属并移至“历史双极化多流扩展”。不把其中的2×Ns系数、216 bit反馈和双流增益套用到本目录的单极化单流程序。

## 目录边界

`1`至`5`是复制保留的阶段性材料；其中的旧报告有各自的实验日期和范围。`6.位置反馈方案`提供当前程序需要的加载器、公共输入和HAQSE依赖，同时保留旧结果。本次单流输出仅位于本目录直属的`results/single_stream_*`，不是历史副本的`results/dual_*`或`minimal_all_methods_*`。

运行当前单流入口只需加入本目录，不要对整个副本使用`addpath(genpath(...))`，以免同名MATLAB包或历史入口混入路径。程序会自行加入第6目录依赖。

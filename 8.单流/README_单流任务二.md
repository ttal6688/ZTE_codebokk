# UPA单极化单流运行说明

当前入口run_single_stream_task2已修复为UPA，UE有4个单极化接收位置；带宽保持400 MHz窄带速率换算。单流与双流不混合，本阶段没有双流实现。

## 首先执行针对性验证

MATLAB进入第8目录：

```matlab
verify_single_stream_upa;
run_single_stream_task2('Mode','verify','OutputDir',fullfile(pwd,'results','upa_verify_new'),'MakeFigures',false);
```

verify默认使用399、400号位置，覆盖UPA8×8、16×16、32×32及B=5/8/10，共104条记录。默认smoke使用前6个位置；本次另用smoke的前2位置运行12个扫描标签，输出312条记录和CPU/UE各7组PNG/FIG，仅用于流程与绘图检查。

```matlab
run_single_stream_task2('Mode','smoke','Samples',2,'OutputDir',fullfile(pwd,'results','upa_smoke_new'));
```

full支持400位置；本次没有启动全量正式实验。选择新OutputDir；入口拒绝覆盖已有single_stream_trials.csv。不要对整个历史副本使用addpath(genpath(...))。

## 公共设置

默认UPA32×32，每维4倍过采样，共128×128个DFT索引；每AP二维索引14 bit。阵元数扫描改为8×8、16×16、32×32，即64/256/1024。AP数5至10，观测SNR20:5:40 dB，莱斯因子0:5:20 dB；其余参数在扫描时固定为B=8、观测30 dB、UPA32×32、K=10 dB。

UPA位置、朝向、UE高度、共享散射与噪声种子沿用原冻结UPA输入；没有新增极化端口。真实单AP信道4×N，联合信道4×BN，最终只有一个发送向量；总功率1，每个可实施AP功率1/B。理想SVD放松每AP等功率约束。

## 位置反馈的正确链路

UE的三参考AP观测 → 连续二维HAQSE频率 → UE三维定位 → 13/14/9 bit坐标整数消息 → CPU独立解码 → 全部AP空间波束。

POS只量化一次坐标。HAQSE频率反馈分支单独量化每维14 bit；它的量化结果不会送入POS定位。空间消息、量化前位置、连续频率、完整三维解码位置和越界标记均保存到CSV。坐标分配为公开固定配置，总36 bit，不依赖CPU未知的真实或未量化位置。

## CPU与UE分别阅读

- [CPU说明](docs/CPU说明.md)：CPU由空间消息重构相位；R=3不等于矩阵维度固定。
- [UE说明](docs/UE说明.md)：UE利用相同解码波束和有噪观测计算4 bit AP间相位。
- [本次修复与验证](docs/UPA与位置反馈修复说明.md)：测试入口、范围和限制。

默认B=8、UPA32×32时，CPU的HAQSE/DFT/POS反馈为84/42/36 bit；UE再加28 bit，分别为112/70/64 bit。Type-I/II及Docomo的算法规则暂沿用她的实现，只完成必要的二维空间码本适配，不能说已经恢复为原仓库基线或验证为标准实现。Docomo只列在UE图中。

## 结果归属

新验证位于results/single_stream_UPA_POS_V1_verify_final与results/single_stream_UPA_POS_V1_smoke2。CPU和UE图各自单列。旧results/single_stream_full和历史双极化多流扩展属于之前实验，不用于证明这次修复的性能。

400 MHz目前只乘窄带频谱效率，不表示已经实现频率选择性、多载波或带宽相关热噪声。其他审查项继续单独推进，不从这些小样本给出性能排名。

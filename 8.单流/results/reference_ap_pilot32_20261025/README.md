# 固定8个协作AP的定位参考数扫描预实验

2026年10月25日。固定B=8，参考AP数R从3至8。32个位置与前一项低至高SNR预实验一致，SNR固定30 dB，LOS与MIX分别统计，MIX的K固定10 dB。此目录不覆盖既有正式实验。

## 报告

- [MD报告](../../docs/UPA固定8AP定位参考数扫描预实验报告.md)
- [Word报告](../../docs/UPA固定8AP定位参考数扫描预实验报告.docx)

## 控制方式

每个位置和信道只生成一次8 AP观测。每个AP的连续空间频率与DFT方向索引各估计一次，不同R直接使用其中前R个。参考集合按公开活动AP顺序嵌套，既不重抽噪声，也不按结果挑选AP。原始消息和全部32位置均保留。

空间频率：每AP反馈两个14 bit频率，共28R bit。DFT索引：每AP两个7 bit方向索引，共14R bit。位置反馈：UE先用R个AP的连续频率定位，再仅量化一次坐标，固定13/14/9 bit，共36 bit。以上是本次定位空间消息，不含通信相位或传输头；方法、R和AP顺序预先共享。

本次采用LOC_REF_SWEEP_V1定位消息，实际打包整数比特串后仅凭公共配置恢复位置。没有修改原SSTR_V2的R=3完整预编码边界，未对R=4至8运行完整通信吞吐量。位置反馈处理更多AP的导频与计算代价未计入坐标bit数。

CPU与UE共用空间消息解码的定位结果，所以只有1152条物理定位记录。两端分别绘图不代表有两套独立定位样本。Type-I、Type-II、Docomo不输出位置，不加入定位误差图。

## 文件

- localization_trials.csv.gz：1152条位置、方法、信道、R组合的完整坐标及误差，含实际空间比特串。
- ap_estimates.csv.gz：512条AP级连续频率、DFT索引和观测噪声方差。
- localization_summary.csv：均值、中位数、95%分位、条件数、反馈量和越界比例。
- experiment_contract.json：固定条件、位置编号、公开AP顺序和消息格式。
- independent_localization_audit.json：独立恢复消息、位置与数值统计，并与既有R=3基线对齐。
- source_and_input_SHA256.json、compression_manifest.json：实现、公共输入及压缩数据指纹。
- CPU、UE目录：各4组PNG/FIG，分别为LOS/MIX的线性与对数定位误差图。
- diagnostics目录：LOS/MIX各1组连续定位与一次坐标量化后误差图。

逐条独立恢复位置最大差约1.14×10⁻¹³ m，R=3与上一项32位置30 dB的192条结果误差差值为0。Word生成后按用户要求未追加渲染检查。

## 复现

```matlab
addpath('8.单流');
out=fullfile(pwd,'8.单流','results','new_reference_ap_pilot');
run_reference_ap_pilot('OutputDir',out);
plot_reference_ap_pilot(out);
```

进入第8目录后：

```text
python analyze_reference_ap_pilot.py results/new_reference_ap_pilot --stage audit
python analyze_reference_ap_pilot.py results/new_reference_ap_pilot --stage report
```

Python分析直接支持gzip。运行必须指定新的输出目录；原冻结依赖和已有单双流报告不修改。比较R时须使用相同位置、信道、噪声和嵌套集合。与原400位置均值比较时，先对齐样本，不把32位置与400位置的平均数差异误判成实现回归。

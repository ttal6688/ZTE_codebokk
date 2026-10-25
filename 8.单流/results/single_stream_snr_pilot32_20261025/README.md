# 单流低至高观测SNR 32位置预实验

2026年10月25日。该目录是独立诊断预实验，未替换原400位置单流或双流正式结果。

## 报告

- [Markdown报告](../../docs/UPA单流低至高观测SNR预实验报告.md)
- [Word报告](../../docs/UPA单流低至高观测SNR预实验报告.docx)

## 设置与范围

32个位置在原400位置编号中等间隔选取，round(linspace(1,400,32))。每AP为32×32单极化UPA，8个协作AP、3个定位参考AP；UE四接收阵元。LOS与MIX分别运行，MIX的K固定10 dB。

观测SNR扫描−20、−10、0、10、20、30、40 dB；数据链路沿用参考SNR10 dB与冻结rho，400 MHz直接换算。所有算法、码本、整数协议、13/14/9 bit坐标和4 bit UE相位与正式实验相同。

每位置、每物理AP使用一个原冻结噪声矩阵，跨SNR只缩放幅度。本次没有多个独立噪声重复，也未按结果剔除位置。

无观测噪声对照使用同算法和真实信道生成空间消息；CPU仅从空间整数消息及公共几何计算相位。该对照仍受原码本与量化约束，不等同于SVD。CPU图中的Type-I(UE)、Type-II(UE)、Docomo(UE)是UE共享参考。

## 文件

- single_stream_trials.csv.gz：8512条完整主扫描记录，包含观测、UE同算法无噪声诊断和SVD参考。
- paired_CSI.csv.gz：2688条UE观测与无噪声配对，不把这些配对当作新的独立位置。
- noisefree_control_trials.csv.gz：704条无噪声对照，含CPU三种几何方案、UE六种方法和两端SVD参考。
- single_stream_summary.csv、noisefree_control_summary.csv：全部分组均值。
- pilot_diagnostics.csv：均值、中位数、95%分位、最大误差与坐标越界比例。
- pilot_contract.json：范围、位置编号、种子复用和无噪声对照说明。
- independent_protocol_audit.json、independent_pilot_audit.json：消息恢复与独立真实信道速率核验。
- source_and_input_SHA256.json、compression_manifest.json：源代码、输入及压缩文件指纹。
- CPU与UE目录：各4组PNG/FIG，分别为LOS/MIX的定位与吞吐量。
- diagnostics目录：2组连续定位、坐标量化与无观测噪声对照PNG/FIG。

独立重建核验9216条速率；最大误差约5.16×10⁻¹⁰ Mbps。MIX的20、30、40 dB与原400位置重合1248条记录，吞吐量完全一致。上述为数值检查；Word生成后按用户要求未追加渲染检查。

## 复现

在仓库根目录运行，输出必须使用新的目录：

```matlab
addpath('8.单流');
out=fullfile(pwd,'8.单流','results','new_snr_pilot32');
run_single_snr_pilot('OutputDir',out);
plot_single_snr_pilot(out);
```

进入第8目录后执行：

```text
python analyze_single_snr_pilot.py results/new_snr_pilot32 --stage audit
python analyze_single_snr_pilot.py results/new_snr_pilot32 --stage report
```

分析入口可读取gzip；调用底层协议审计前会恢复其需要的paired_CSI.csv。主扫描已完成而无噪声CPU对照尚未生成时，可以用ResumeControls=true继续，并验证原扫描的位置、SNR、阵列与信道设置；不会重跑主扫描。

原run_single_stream_task2新增SampleIds和ObservationSNRs可选输入。未指定时原full、smoke、verify默认设置不变；指定ObservationSNRs时仅运行默认阵列/AP/K下的指定SNR扫描。

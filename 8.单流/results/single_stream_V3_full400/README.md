# UPA单极化单流400位置正式结果

98,800条记录、19个曲线标签、16个物理配置，所有247组各400个不同位置。仅观测CSI方法与真实SVD参考。CPU与UE各11组图。

- [压缩原始明细](single_stream_trials.csv.gz)
- [汇总](single_stream_summary.csv)
- [独立审计](independent_protocol_audit.json)
- [覆盖检查](coverage_audit.json)
- [无损压缩检查](compression_audit.json)
- [配置](experiment_contract.json)
- [运行检查](audit.json)
- [源码输入哈希](source_and_input_SHA256.json)
- [报告](../../docs/UPA单流400位置正式实验报告.md)

CSV本地保留，远端gzip可直接由pandas读取；MATLAB绘图可自动解压。60个越界位置在CPU/UE共120行，不把截断改善解释成量化收益。

| CPU图 | UE图 |
|---|---|
| [吞吐量_SNR](CPU/CPU_吞吐量_SNR.png) | [吞吐量_SNR](UE/UE_吞吐量_SNR.png) |
| [定位误差_SNR](CPU/CPU_定位误差_SNR.png) | [定位误差_SNR](UE/UE_定位误差_SNR.png) |
| [比特数_AP数](CPU/CPU_比特数_AP数.png) | [比特数_AP数](UE/UE_比特数_AP数.png) |
| [POS量化前后](CPU/CPU_POS量化前后.png) | [POS量化前后](UE/UE_POS量化前后.png) |
| [POS越界比例](CPU/CPU_POS越界比例.png) | [POS越界比例](UE/UE_POS越界比例.png) |

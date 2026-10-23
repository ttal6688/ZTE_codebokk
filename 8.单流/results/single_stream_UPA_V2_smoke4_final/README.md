# UPA单极化单流V2最小验证

位置[1, 2, 3, 4]，12组参数标签，模型['MIX']，共912条记录。这是实现与流程验证，不是400位置正式实验。每案例CPU六行、UE十三行；CPU的Type-I/II为UE参考，SVD为上界。

- [完整记录与整数消息](single_stream_trials.csv)
- [分组均值](single_stream_summary.csv)
- [同算法CSI配对](paired_CSI.csv)
- [运行配置](experiment_contract.json)
- [运行检查](audit.json)
- [独立协议审计](independent_protocol_audit.json)
- [源码与输入校验](source_and_input_SHA256.json)
- [修正报告](../../docs/单流基线与反馈协议修正报告.md)

Python独立核验816条有限反馈有效载荷及全部汇总均值；预编码检查量最大误差6.641e-12。共288组CSI配对，36组速率差为负，照实保存。坐标固定13/14/9 bit；CPU不接收参考AP的完整观测信道。400 MHz仅作窄带换算。

CPU和UE分别11组、12组PNG/FIG；主图只使用观测CSI及SVD，配对图单列。

| CPU | UE |
|---|---|
| [吞吐量_SNR](CPU/CPU_吞吐量_SNR.png) | [吞吐量_SNR](UE/UE_吞吐量_SNR.png) |
| [频谱效率_SNR](CPU/CPU_频谱效率_SNR.png) | [频谱效率_SNR](UE/UE_频谱效率_SNR.png) |
| [定位误差_SNR](CPU/CPU_定位误差_SNR.png) | [定位误差_SNR](UE/UE_定位误差_SNR.png) |
| [比特数_AP数](CPU/CPU_比特数_AP数.png) | [比特数_AP数](UE/UE_比特数_AP数.png) |
| [POS量化前后](CPU/CPU_POS量化前后.png) | [POS量化前后](UE/UE_POS量化前后.png) |
| [POS越界比例](CPU/CPU_POS越界比例.png) | [POS越界比例](UE/UE_POS越界比例.png) |
| [固定坐标bit分配](CPU/CPU_固定坐标bit分配.png) | [固定坐标bit分配](UE/UE_固定坐标bit分配.png) |
| CPU不使用UE完美CSI设计权重 | [同算法CSI配对](UE/UE_同算法CSI配对收益.png) |

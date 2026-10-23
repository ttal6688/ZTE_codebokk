# UPA单极化单流V2最小验证

位置[399, 400]，4组参数标签，模型['LOS', 'MIX']，共304条记录。这是实现与流程验证，不是400位置正式实验。每案例CPU六行、UE十三行；CPU的Type-I/II为UE参考，SVD为上界。

- [完整记录与整数消息](single_stream_trials.csv)
- [分组均值](single_stream_summary.csv)
- [同算法CSI配对](paired_CSI.csv)
- [运行配置](experiment_contract.json)
- [运行检查](audit.json)
- [独立协议审计](independent_protocol_audit.json)
- [源码与输入校验](source_and_input_SHA256.json)
- [修正报告](../../docs/单流基线与反馈协议修正报告.md)

Python独立核验272条有限反馈有效载荷及全部汇总均值；预编码检查量最大误差1.116e-11。共96组CSI配对，19组速率差为负，照实保存。坐标固定13/14/9 bit；CPU不接收参考AP的完整观测信道。400 MHz仅作窄带换算。

- [701项协议检查](protocol_unit_audit.json)
- [42项UPA/POS回归](preserved_UPA_POS_audit.json)

LOS/MIX分别统计，本目录未出图。

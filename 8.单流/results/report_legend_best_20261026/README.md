# 最新单流双流报告图例best自动定位

2026年10月26日。按照用户要求，两份最新报告的全部现有图例统一为18 pt和`Location='best'`。共享保存函数先确定最终字号，再强制重新计算best位置，后续不覆盖Position或指定图例宽高。无图例的图不新增图例。

范围为124个独立图文件，对应单流48处、双流82处报告插图引用，包含CPU、UE、LOS、MIX、正文、补充实验和四张百分比图。图片使用各自结果目录下的`legend_best_v3`新路径，历史图片保留。原有曲线数据、坐标轴、刻度、标签、图例文字及百分比定义保持不变；不重跑任何仿真。

- [单流最新报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.md) · [单流Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.docx)
- [双流最新报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.md) · [双流Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.docx)
- [四张百分比图及PPT图片包](../feedback_percentage_20261026/README.md)

figure_manifest.json列出每个旧图和新图路径。figure_audit.json记录保存后FIG的Location、字号及曲线和坐标轴不变检查。Word仅替换现有嵌入图片，保留全部XML、正文及排版，按用户要求不追加Word检查。

本次迁移按顺序执行：

```text
python 8.单流/update_report_best.py prepare
```

```matlab
addpath('8.单流');
update_report_best_figures;
```

```text
python 8.单流/update_report_best.py integrate
```

后续正常绘图由save_report_figure.m统一执行best，报告生成器自动使用legend_best_v3图片路径。best为MATLAB自动定位方式，保留其自动选择结果，不再人工移动图例。

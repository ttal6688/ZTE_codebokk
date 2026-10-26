# 最新单双流报告的图例字号更新

2026年10月26日。本轮字号更新时的单流46处及双流80处插图引用，共126处，对应120个独立图文件；其中固定8个协作AP的6幅定位参考数补充图由两份报告共用。本次将所有现有legend统一调为18 pt，不给原本无图例的图新增图例。

- [单流最新报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.md) · [Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单流400位置正式实验报告.docx)
- [双流最新报告](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.md) · [Word](https://github.com/ttal6688/ZTE_codebokk/blob/feat/upa-single-dual-complete-20261024/8.单流/docs/UPA单极化双流400位置完整实验报告.docx)

直接读取当前报告引用的原可编辑FIG，仅修改legend的FontUnits和FontSize。新PNG及FIG保存在每幅原图目录下的legend_font18_v1版本目录，原PNG和FIG保留。MD切换实际图片路径，避免GitHub继续显示缓存旧图；Word从同一份MD和新图片生成，按用户要求不追加检查。不重新仿真，不改数值、方法名、图例文字或坐标范围。

统一样式见`8.单流/report_figure_style.json`，保存函数`save_report_figure.m`同时供后续正式扫描、定位参考数补充及固定坐标分配图的绘图入口使用，避免后续重新运行时恢复小图例。

figure_manifest.json列出120个源图片和实际新图片路径。legend_audit.json逐图核对保存后FIG的图例字号，确认绘图数值、轴范围、坐标尺度、轴名称及图例文字与原FIG完全一致。report_audit.json核对MD只改变图片地址、原图和数值文件保留，以及所有引用均指向新版本。

```text
python 8.单流/prepare_report_legend_manifest.py
```

```matlab
addpath('8.单流');
update_report_legend_figures;
```

```text
python 8.单流/build_snr_revision_reports.py
python 8.单流/build_word_reports.py UPA单流400位置正式实验报告.md UPA单极化双流400位置完整实验报告.md
```

本目录仅保存本次样式更新清单与核对记录。实验数据仍分别位于upa_snr_revision400_20261025和reference_ap_full400_20261025，原32位置预实验报告不属于本次最新正式报告的修改范围。


后续在四组bit开销实验后各增加一张[相对Type-I的百分比图](../feedback_percentage_20261026/README.md)，不改变本目录原图和数值。两份正式报告现在分别48处、82处插图引用，新增四图也采用18 pt图例。

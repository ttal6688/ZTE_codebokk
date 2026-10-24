"""Expand the existing single-stream report with every published experiment."""
from pathlib import Path
import re
import pandas as pd
from report_experiments import single_experiments
ROOT=Path(__file__).resolve().parent

def build():
    dest=ROOT/'docs/UPA单流400位置正式实验报告.md'
    text=dest.read_text(encoding='utf-8').split('## CPU单流逐实验图表和数值')[0].rstrip()
    text=re.sub(r'^!\[[^\]]*\]\([^)]+\)\n?', '',text,flags=re.M)
    text=text.replace('CPU图中的Type-I/II是UE计算的共享参考，不是CPU几何算法。其默认均值为3298.510/3324.283 Mbps；理想单流SVD为3543.540 Mbps。',
      'CPU图中的全反馈Type-I(UE)、全反馈Type-II(UE)和Docomo(UE)均为UE计算的共享参考。默认均值分别为3298.510、3324.283和3347.721 Mbps；理想单流SVD为3543.540 Mbps。Docomo(UE)反馈129 bit，结果直接复用UE数据，不新增CPU算法或样本。定位误差图只列有位置输出的三种几何方法。')
    text=text.replace('下表为默认配置的400位置均值，仅列CPU三种几何方法。','下表为默认配置的400位置均值，列出CPU三种几何方法和Docomo(UE)共享参考。')
    row='| Docomo(UE) | 3347.721 | 不适用 | 129 |'
    if row not in text:text=text.replace('| 位置反馈 | 3184.002 | 0.009490 | 36 |','| 位置反馈 | 3184.002 | 0.009490 | 36 |\n'+row)
    text=text.replace('双流结果单独报告，不能与本报告的400位置均值直接拼接比较。','双流已按同一400位置和参数逐条配对核对，结果另见双流完整报告，不混入本报告的单流统计。')
    note='2026年10月24日补齐全部22幅实验图、对应逐点数值和结论，实验数据不变。最新单流与双流统一在feat/upa-single-dual-complete-20261024维护，后续修改继续使用该分支。'
    if note not in text:text=text.replace('\n\n## 实验范围与评价口径','\n\n'+note+'\n\n## 实验范围与评价口径')
    s=pd.read_csv(ROOT/'results/single_stream_V3_full400/single_stream_summary.csv')
    parts=[text]+single_experiments('CPU',s)+single_experiments('UE',s)
    content='\n\n'.join(parts)+'\n'
    content=content.replace('Docomo结构适配与验证','Docomo实现与验证').replace('Docomo结构适配','Docomo').replace('Docomo适配','Docomo').replace('HAQSE','空间频率')
    content=content.replace('项目Type-I 含共相位','全反馈Type-I(UE)').replace('项目Type-II','全反馈Type-II(UE)').replace('空间频率频率','空间频率')
    dest.write_text(content,encoding='utf-8');print(dest)

if __name__=='__main__':build()

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
    text=text.replace('双流结果单独报告，不能与本报告的400位置均值直接拼接比较。','双流已按同一400位置和参数逐条配对核对，结果另见双流完整报告，不混入本报告的单流统计。')
    note='2026年10月24日补齐全部22幅实验图、对应逐点数值和结论，实验数据不变。最新单流与双流统一在feat/upa-single-dual-complete-20261024维护，后续修改继续使用该分支。'
    if note not in text:text=text.replace('\n\n## 实验范围与评价口径','\n\n'+note+'\n\n## 实验范围与评价口径')
    s=pd.read_csv(ROOT/'results/single_stream_V3_full400/single_stream_summary.csv')
    parts=[text]+single_experiments('CPU',s)+single_experiments('UE',s)
    dest.write_text('\n\n'.join(parts)+'\n',encoding='utf-8');print(dest)

if __name__=='__main__':build()

"""List only figures referenced by the two current reports; no data reruns."""
from pathlib import Path
import json,re
from report_figure_style import ROOT,STYLE,VERSION
OUT=ROOT/'results/report_legend18_20261026'

def build():
    OUT.mkdir(exist_ok=True)
    reports=['UPA单流400位置正式实验报告.md','UPA单极化双流400位置完整实验报告.md']
    entries={};counts={}
    for name in reports:
        md=ROOT/'docs'/name;links=re.findall(r'!\[[^\]]*\]\(([^)]+\.png)\)',md.read_text(encoding='utf-8'));counts[name]=len(links)
        for link in links:
            path=(md.parent/link).resolve()
            if path.parent.name==VERSION:path=path.parent.parent/path.name
            assert path.is_file() and path.with_suffix('.fig').is_file(),path
            assert path.is_relative_to(ROOT)
            entries[path.as_posix()]=dict(source=path.relative_to(ROOT).as_posix(),target=(path.parent/VERSION/path.name).relative_to(ROOT).as_posix())
    manifest=dict(style=STYLE,reports=counts,unique_figures=len(entries),figures=list(entries.values()))
    (OUT/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Report image references',sum(counts.values()),'; unique figures',len(entries))

if __name__=='__main__':build()

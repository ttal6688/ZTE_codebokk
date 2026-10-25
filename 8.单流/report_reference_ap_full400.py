"""First supplementary experiment shared by the single/two-stream reports."""
from pathlib import Path
import gzip,hashlib,json
import pandas as pd
from report_experiments import table

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/reference_ap_full400_20261025'
METHODS=['HAQSE','DFT_INDEX','POS']
NAMES={'HAQSE':'空间频率','DFT_INDEX':'DFT索引','POS':'位置反馈'}

def reference_ap_supplement(ns):
    audit=json.loads((OUT/'independent_localization_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='passed' and audit['positions']==400
    s=pd.read_csv(OUT/'localization_summary.csv')
    path=OUT/'localization_trials.csv'
    t=pd.read_csv(path if path.exists() else path.with_suffix('.csv.gz'))
    contract=json.loads((OUT/'experiment_contract.json').read_text(encoding='utf-8'))
    stream='单流' if ns==1 else '双流';relative='../results/'+OUT.name
    lines=['### 4.1 固定8个协作AP的定位参考数扫描',
        '本实验固定协作AP总数B=8，横轴改为参与定位的参考／反馈AP数R=3、4、5、6、7、8。采用全部400个冻结位置、每AP32×32单极化UPA、观测SNR 30 dB；LOS与MIX分别运行，MIX的K=10 dB。原正文中固定R=3、改变协作AP总数的实验完整保留，二者是不同自变量。',
        '每个位置与信道只生成一次完整8 AP观测，8个AP的连续空间频率及DFT方向索引各估计一次。按预先公开的活动AP顺序取前R个，形成嵌套集合，各R共用同一份观测及固定噪声方差；不按结果选择AP，也不重新生成噪声。',
        table(['参考／反馈AP数R','物理AP编号'],[[r,','.join(map(str,contract['active_AP_ids'][:r]))] for r in range(3,9)]),
        '空间频率与DFT索引实际打包R个AP的方向整数，CPU解码后定位。位置反馈则由UE用R个AP的连续频率直接定位，再按13/14/9 bit只量化一次坐标；R增加不表示反馈R份位置。所有方法均由整数消息独立恢复用于评价的坐标。',
        f'{stream}的定位来自共用空间前端，与流数和共相位的计算端无关。因此本节CPU、UE及另一份流数报告共用同一份物理定位记录，不把重复展示当作独立试验；增加第二流不增加定位观测。该实验采用LOC_REF_SWEEP_V1定位消息，未将原SSTR_V2的完整预编码协议从R=3改为R=8，不据此给出新增吞吐量结论。']
    findings=[]
    for branch in ['CPU','UE']:
        for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
            rows=[]
            for method in METHODS:
                q=s[s.channel_model.eq(model)&s.method.eq(method)].set_index('R')
                rows.append([NAMES[method]]+[f'{q.loc[r].mean_position_error_m:.6f}' for r in range(3,9)])
            title=f'{branch}{stream}{name}定位误差与定位参考AP数'
            q=s[s.channel_model.eq(model)&s.method.eq('POS')].set_index('R')
            reduction=100*(q.loc[3].mean_position_error_m-q.loc[8].mean_position_error_m)/q.loc[3].mean_position_error_m
            lines += ['**'+title+'**','纵轴为400位置平均定位误差（m），横轴为整数R，协作AP总数始终为8。',
                table(['方法']+[str(r) for r in range(3,9)],rows),
                f'![{title}]({relative}/figures/{branch}/{model}_定位误差_反馈AP数.png)',
                f'结果：位置反馈从R=3的{q.loc[3].mean_position_error_m:.6f} m变为R=8的{q.loc[8].mean_position_error_m:.6f} m，均值变化对应降幅{reduction:.2f}%。CPU与UE位置结果一致，反映共用定位消息，不代表相位设计和吞吐量也相同。']
    lines += ['**从3个到8个参考AP的收益与限制**']
    rows=[]
    for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
        for method in METHODS:
            q=s[s.channel_model.eq(model)&s.method.eq(method)].set_index('R')
            pairs=t[t.channel_model.eq(model)&t.method.eq(method)].pivot(index='sample_id',columns='R',values='position_error_m')
            start=q.loc[3].mean_position_error_m;end=q.loc[8].mean_position_error_m
            fraction=float((pairs[8]<pairs[3]).mean());gain=100*(start-end)/start
            rows.append([name,NAMES[method],f'{1000*start:.3f}',f'{1000*end:.3f}',f'{gain:.2f}',f'{100*fraction:.2f}'])
            findings.append(dict(channel_model=model,method=method,mean_R3_m=start,mean_R8_m=end,mean_reduction_percent=gain,strictly_improved_fraction=fraction))
    lines += [table(['信道','方法','R=3均值 mm','R=8均值 mm','均值降幅 %','逐位置改善 %'],rows),
        '增加参考AP同时增加了方向观测并改变射线的空间几何。当前定位仍使用原无权重射线最小二乘，未调整AP选择、权重或频率估计器；加入一个AP不保证每个位置或每个中间R点都改善。表中同时给出逐位置严格改善比例，全部位置保留，不将平均降幅解释为逐位置保证。此结论仅对应预先固定的嵌套AP顺序。',
        '**位置反馈的连续定位与坐标量化**']
    for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
        q=s[s.channel_model.eq(model)&s.method.eq('POS')].sort_values('R')
        lines += [table(['信道 '+name,'连续误差 mm','解码误差 mm','中位误差 mm','95%分位 mm'],
            [[f'R={r.R}',f'{1000*r.mean_raw_position_error_m:.3f}',f'{1000*r.mean_position_error_m:.3f}',f'{1000*r.median_position_error_m:.3f}',f'{1000*r.p95_position_error_m:.3f}'] for r in q.itertuples()]),
            f'![{name}坐标量化前后定位误差随参考AP数变化]({relative}/figures/diagnostics/{model}_坐标量化前后_反馈AP数.png)',
            '结果：连续定位与量化后位置分开统计，固定坐标量化会影响参考AP增加带来的最终收益；这里始终是连续频率定位后只量化一次坐标。']
    lines += ['**仅空间消息的反馈量**',table(['方法']+[f'R={r}' for r in range(3,9)],
        [['空间频率']+[28*r for r in range(3,9)],['DFT索引']+[14*r for r in range(3,9)],['位置反馈']+[36]*6]),
        '单位为bit，仅统计本定位实验的空间消息；不含相位、公共配置头和FEC。位置反馈只发送一份36 bit坐标，方向消息则随R增加。更多参考AP的观测、计算与导频成本未纳入该bit表，不能据36 bit不变认定其没有其他代价。正文原完整通信开销实验不被此表替换。',
        f'独立恢复全部{audit["physical_localization_records"]:,}条物理定位记录，重算均值、中位数和95%分位。R=3与当前400位置正式结果的{audit["formal400_R3_overlap_records"]:,}条位置误差对齐，最大差{audit["maximum_formal400_R3_error_m"]:.3g} m；原32位置预实验全部R值的{audit["pilot32_all_R_overlap_records"]:,}条消息与误差也对齐。',
        '[本补充实验的数据、配置、整数消息和复现命令](../results/'+OUT.name+'/README.md)。']
    (OUT/'findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
    return lines

def package():
    records=[]
    for name in ['localization_trials.csv','ap_estimates.csv']:
        source=OUT/name;raw=source.read_bytes();target=source.with_suffix('.csv.gz')
        target.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0));assert gzip.decompress(target.read_bytes())==raw
        records.append(dict(file=target.name,raw_sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),round_trip=True))
    (OUT/'compression_manifest.json').write_text(json.dumps(dict(status='passed',files=records),ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':package()

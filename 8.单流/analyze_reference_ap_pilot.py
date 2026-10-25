"""Independent localization-message recovery and report for the fixed-B reference sweep."""
from pathlib import Path
import argparse,gzip,hashlib,json
import numpy as np
import pandas as pd
import audit_single_stream_protocol as base

ROOT=Path(__file__).resolve().parent
METHODS=['HAQSE','DFT_INDEX','POS']
NAMES={'HAQSE':'空间频率','DFT_INDEX':'DFT索引','POS':'位置反馈'}

def read(path,**kw):return pd.read_csv(path if path.exists() else path.with_suffix(path.suffix+'.gz'),**kw)

def localize(freq,refs):
    A=np.zeros((3,3));rhs=np.zeros(3)
    for ref,f in zip(refs,freq.T):
        yz=-2*f;q=np.r_[-np.sqrt(max(0,1-yz@yz)),yz];q/=np.linalg.norm(q)
        ap=base.APS[int(ref)-1];g=-np.array(ap['R_local_to_global'])@q
        P=np.eye(3)-np.outer(g,g);A+=P;rhs+=P@np.ravel(ap['position_m'])
    return np.linalg.solve(A,rhs),float(np.linalg.cond(A))

def integers(wire,widths,shape):
    cursor=0;out=[]
    for w in widths:
        part=wire[cursor:cursor+w];assert len(part)==w;out.append(int(part,2));cursor+=w
    assert cursor==len(wire) and set(wire)<=set('01')
    return np.array(out).reshape(shape,order='F')

def audit(out):
    c=json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'));ids=c['sample_ids'];active=c['active_AP_ids']
    t=read(out/'localization_trials.csv',dtype={'feedback_wire':'string'});e=pd.read_csv(out/'ap_estimates.csv');s=pd.read_csv(out/'localization_summary.csv')
    assert len(t)==len(ids)*2*6*3 and len(e)==len(ids)*2*8
    assert t.B.eq(8).all() and t.observation_SNR_dB.eq(30).all() and t.K_dB.eq(10).all()
    assert set(t.R)==set(range(3,9)) and set(t.sample_id)==set(ids)
    groups=t.groupby(['channel_model','method','R']).sample_id.agg(['count','nunique'])
    assert groups['count'].eq(len(ids)).all() and groups['nunique'].eq(len(ids)).all()
    maximum_position=maximum_error=maximum_condition=0.
    for row in t.itertuples():
        refs=json.loads(row.reference_AP_ids);assert refs==active[:row.R]
        source=e[e.channel_model.eq(row.channel_model)&e.sample_id.eq(row.sample_id)].set_index('physical_AP_id').loc[refs]
        freq=source[['frequency_y','frequency_z']].to_numpy(float).T
        raw,raw_condition=localize(freq,refs);wire=str(row.feedback_wire)
        if row.method=='HAQSE':
            codes=integers(wire,[14]*(2*row.R),(2,row.R))
            expected=np.clip(base.rnd((freq+.5)*(2**14-1)),0,2**14-1).astype(int);assert np.array_equal(codes,expected)
            position,condition=localize(-.5+codes/(2**14-1),refs);raw_for_metric=position
        elif row.method=='DFT_INDEX':
            codes=integers(wire,[7]*(2*row.R),(2,row.R))
            assert np.array_equal(codes,source[['DFT_y','DFT_z']].to_numpy(int).T)
            position,condition=localize(-((codes/128+.5)%1-.5),refs);raw_for_metric=position
        else:
            codes=integers(wire,[13,14,9],(3,))
            encoded=np.floor((raw-base.LO)/base.SPAN*2.**base.BITS);overflow=bool(np.any((encoded<0)|(encoded>=2.**base.BITS)))
            assert np.array_equal(codes,np.clip(encoded,0,2.**base.BITS-1).astype(int));assert overflow==bool(row.quantizer_overflow)
            position=base.LO+(codes+.5)*base.SPAN/2.**base.BITS;condition=raw_condition;raw_for_metric=raw
        expected_bits={'HAQSE':28*row.R,'DFT_INDEX':14*row.R,'POS':36}[row.method]
        assert len(wire)==row.spatial_feedback_bits==expected_bits
        truth=np.array([row.true_x_m,row.true_y_m,row.true_z_m]);saved=np.array([row.estimated_x_m,row.estimated_y_m,row.estimated_z_m])
        stored_raw=np.array([row.raw_x_m,row.raw_y_m,row.raw_z_m])
        maximum_position=max(maximum_position,float(np.max(abs(saved-position))),float(np.max(abs(stored_raw-raw_for_metric))))
        maximum_error=max(maximum_error,abs(np.linalg.norm(position-truth)-row.position_error_m),abs(np.linalg.norm(raw_for_metric-truth)-row.raw_position_error_m))
        maximum_condition=max(maximum_condition,abs(condition-row.localization_condition)/max(1,condition))
        assert np.isclose(row.observation_noise_variance,source.observation_noise_variance.iloc[0],rtol=1e-12)
    assert maximum_position<1e-8 and maximum_error<1e-8 and maximum_condition<1e-9
    assert t.groupby(['channel_model','sample_id']).observation_noise_variance.nunique().eq(1).all()
    assert e.groupby(['channel_model','sample_id']).observation_noise_variance.nunique().eq(1).all()
    keys=['channel_model','method','B','R','observation_SNR_dB','K_dB'];grouped=t.groupby(keys)
    means=grouped.size().reset_index(name='samples')
    for field in ['position_error_m','raw_position_error_m','spatial_feedback_bits','localization_condition','quantizer_overflow']:
        values=grouped[field].mean().reset_index(name='mean_'+field);means=means.merge(values,on=keys,validate='one_to_one')
    means=means.merge(grouped.position_error_m.median().reset_index(name='median_position_error_m'),on=keys)
    # MATLAB prctile uses midpoint plotting positions (NumPy's Hazen method).
    means=means.merge(grouped.position_error_m.agg(lambda v:np.quantile(v,.95,method='hazen')).reset_index(name='p95_position_error_m'),on=keys)
    joined=s.merge(means,on=keys,suffixes=('_m','_p'),validate='one_to_one');assert len(joined)==len(s)==len(means)
    for field in ['samples']+[x for x in s if x.startswith('mean_')]+['median_position_error_m','p95_position_error_m']:
        assert np.allclose(joined[field+'_m'],joined[field+'_p'],rtol=1e-9,atol=1e-10),field
    old=read(ROOT/'results/single_stream_snr_pilot32_20261025/single_stream_trials.csv',
        usecols=['branch','csi','channel_model','x_value','method','sample_id','position_error_m','raw_position_error_m'])
    old=old[old.branch.eq('CPU')&old.csi.eq('OBSERVED')&old.x_value.eq(30)].copy()
    old['method']=old.method.map({'HAQSE_R3':'HAQSE','DFT_INDEX_R3':'DFT_INDEX','POS_R3':'POS'})
    old=old[old.method.isin(METHODS)]
    a=t[t.R.eq(3)].merge(old,on=['channel_model','method','sample_id'],suffixes=('_new','_old'),validate='one_to_one')
    assert len(a)==len(ids)*2*3
    overlap=float(max(abs(a.position_error_m_new-a.position_error_m_old).max(),abs(a.raw_position_error_m_new-a.raw_position_error_m_old).max()));assert overlap<1e-8
    result=dict(status='passed',positions=len(ids),physical_localization_records=len(t),AP_estimate_records=len(e),
        B_fixed=8,R_values=list(range(3,9)),all_groups_have_all_positions=True,all_samples_retained=True,
        maximum_recovered_position_error_m=maximum_position,maximum_reported_distance_error_m=maximum_error,
        maximum_relative_condition_error=maximum_condition,all_summary_statistics_recomputed=True,
        integer_feedback_lengths_checked=True,observations_reused_across_R=True,
        previous_R3_overlap_records=len(a),maximum_previous_R3_error_m=overlap,full_precoder_protocol_extended=False)
    (out/'independent_localization_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[ROOT/'run_reference_ap_pilot.m',ROOT/'plot_reference_ap_pilot.m',Path(__file__),ROOT/'+sstr/space_messages.m',ROOT/'+sstr/messages_from_estimates.m',ROOT/'+sstr/observe_sample.m',ROOT/'+sstr/make_sample.m']
    files+=list((ROOT/'6.位置反馈方案').glob('+*/*.m'))+list((ROOT/'6.位置反馈方案/lib').glob('*.m'))+list(base.PUBLIC.glob('*.json'))+list(base.PUBLIC.glob('*.csv'))
    source=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()) for p in sorted(set(files))]
    (out/'source_and_input_SHA256.json').write_text(json.dumps(dict(text_normalization='CRLF to LF',files=source),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])

def report(out):
    c=json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'));a=json.loads((out/'independent_localization_audit.json').read_text(encoding='utf-8'))
    s=pd.read_csv(out/'localization_summary.csv');t=read(out/'localization_trials.csv',dtype={'feedback_wire':'string'})
    relative='../results/'+out.name;findings=[]
    lines=['# UPA固定8个协作AP的定位参考数扫描预实验报告',
        '2026年10月25日。本次固定协作AP总数B=8，将参与定位的参考AP数R从3扫到8，检查更多定位观测是否改变原来近似水平的曲线。沿用上次32个等间隔冻结位置，观测SNR30 dB，每AP32×32单极化UPA，LOS与MIX分别运行。本次只研究定位，不重新设计单流或双流预编码，也不替换原400位置报告。',
        '## 1 变量与实现边界',
        table(['项目','设置'],[['协作AP总数B','始终固定为8'],['横轴R','定位参考AP数3、4、5、6、7、8，整数刻度'],
        ['参考AP集合','公开活动AP顺序的前R个，逐步嵌套；不是按定位结果挑选AP'],['位置','与低至高SNR预实验相同的32个等间隔位置'],
        ['观测','每个位置与信道只生成一次8 AP观测，跨R直接复用；SNR固定30 dB'],['信道','LOS与MIX分开；MIX的K=10 dB'],
        ['空间频率','每参考AP两个14 bit频率整数，先量化频率再由CPU定位'],['DFT索引','每参考AP两个7 bit方向索引，再由CPU定位'],
        ['位置反馈','UE用R个参考AP的连续频率定位，然后只量化一次坐标；13/14/9 bit固定'],
        ['CPU与UE','共享原定位前端；共相位来源不改变本实验的位置估计，因此共用同一份定位结果']]),
        '对空间频率和DFT索引，R表示发送方向消息的AP数；对位置反馈，R表示UE定位使用的参考AP数，不表示反馈R份位置。位置反馈仍只发送一份36 bit坐标消息。方法、R和AP顺序预先共享，不额外计入配置头；本定位实验没有相位反馈字段。',
        '实现调用原空间频率估计器、射线最小二乘定位、方向消息恢复和坐标编码函数。8个AP各估计一次，再取相同观测的前R个子集。为独立恢复位置，本预实验按R实际打包和解码方向整数或坐标整数；该定位消息格式为LOC_REF_SWEEP_V1，未把原仅支持R=3的SSTR_V2完整预编码协议静默扩展到R=8。',
        '参考AP集合如下：',table(['R','物理AP编号'],[[R,','.join(map(str,c['active_AP_ids'][:R]))] for R in range(3,9)]),
        '## 2 主要发现']
    for model,title in [('LOS','纯LOS'),('MIX','混合信道')]:
        rows=[]
        for method in METHODS:
            q=s[s.channel_model.eq(model)&s.method.eq(method)].set_index('R');start=q.loc[3].mean_position_error_m;end=q.loc[8].mean_position_error_m
            pair=t[t.channel_model.eq(model)&t.method.eq(method)].pivot(index='sample_id',columns='R',values='position_error_m')
            fraction=float((pair[8]<pair[3]).mean());gain=100*(start-end)/start
            rows.append([NAMES[method],f'{1000*start:.3f}',f'{1000*end:.3f}',f'{gain:.2f}%',f'{100*fraction:.2f}%'])
            findings.append(dict(channel_model=model,method=method,mean_R3_m=float(start),mean_R8_m=float(end),mean_reduction_percent=float(gain),R8_better_than_R3_fraction=fraction))
        lines += ['### '+title+'的R=3与R=8对照',table(['方法','R=3均值 mm','R=8均值 mm','均值降幅','逐位置改善比例'],rows)]
    lines += ['DFT索引的方向量化较粗，增加定位参考AP后，本次两种信道下的均值下降较明显。空间频率和位置反馈的误差较小，收益还受观测偏差与坐标量化影响。',
        '纯LOS下位置反馈的量化后误差约为4 mm量级，增加参考观测后的连续定位改善可能被固定坐标量化掩盖。MIX下R=5到6时，部分方法误差回升，之后R=7和8继续下降；当前无权重射线最小二乘并不保证加入一个AP后误差逐点下降。所有AP和位置均保留。',
        '增加R同时改变了AP集合的空间几何与方向观测，本结论只对应这里预先固定的嵌套集合，不代表任意同样数量的AP子集都有相同收益。']
    for chapter,branch in [(3,'CPU'),(4,'UE')]:
        lines += [f'## {chapter} {branch}端定位误差随参考AP数变化',
            '本端位置结果与另一端相同，因为输入空间消息和位置解码规则相同；下表和图复用同一份物理定位记录，不将两端当作两组独立样本。B固定8，横轴是R，不能与此前固定R=3、改变协作AP总数的曲线混为一谈。']
        for model,title in [('LOS','纯LOS'),('MIX','混合信道')]:
            rows=[]
            for method in METHODS:
                q=s[s.channel_model.eq(model)&s.method.eq(method)].set_index('R')
                rows.append([NAMES[method]]+[f'{q.loc[R].mean_position_error_m:.6f}' for R in range(3,9)])
            lines += ['### '+branch+title+'定位误差与定位参考AP数',table(['方法']+list(map(str,range(3,9))),rows),
                f'![{branch}{title}定位误差随参考AP数变化 线性纵轴]({relative}/{branch}/{branch}_{model}_position_reference_APs_linear.png)',
                f'![{branch}{title}定位误差随参考AP数变化 对数纵轴]({relative}/{branch}/{branch}_{model}_position_reference_APs_log.png)',
                '表中单位为m。线性图保留绝对误差差距，对数图补充显示毫米级方法的变化；两图使用相同数值。']
    lines += ['## 5 坐标量化与空间反馈量补充']
    for model,title in [('LOS','纯LOS'),('MIX','混合信道')]:
        q=s[s.channel_model.eq(model)&s.method.eq('POS')].sort_values('R')
        lines += ['### '+title+'位置反馈连续定位与坐标解码',
            table(['R','连续定位均值 mm','坐标解码均值 mm','解码中位 mm','解码95%分位 mm'],
            [[r.R,f'{1000*r.mean_raw_position_error_m:.3f}',f'{1000*r.mean_position_error_m:.3f}',f'{1000*r.median_position_error_m:.3f}',f'{1000*r.p95_position_error_m:.3f}'] for r in q.itertuples()]),
            f'![{title}连续定位与一次坐标量化后误差]({relative}/diagnostics/{model}_POS_continuous_vs_quantized_reference_APs.png)',
            '位置反馈始终由连续频率直接定位后量化一次坐标，没有先量化频率再定位。坐标预算和公共编码区域不随R改变，未使用真实位置调整bit分配。']
    lines += ['### 空间消息反馈量',table(['方法']+[f'R={R}' for R in range(3,9)],
        [['空间频率']+[28*R for R in range(3,9)],['DFT索引']+[14*R for R in range(3,9)],['位置反馈']+[36]*6]),
        '表中单位为bit，仅统计空间消息。空间频率与DFT索引随着R发送更多方向整数；位置反馈只发送一次坐标。UE处理更多参考AP观测的计算及导频资源不计入该bit表，不能据36 bit不变就认定增加参考AP没有其他代价。若恢复原B=8的UE单流通信，相位字段另需28 bit；该通信过程不属于本次定位扫描。',
        '## 6 与原实验的一致性及范围',
        f"独立核验恢复了全部{a['physical_localization_records']}条定位消息，重算位置、欧氏误差、均值、中位数及95%分位，最大位置差{a['maximum_recovered_position_error_m']:.3g} m；每个方法、信道、R均保留全部{a['positions']}个位置。",
        f"R=3时与上次32位置SNR预实验中30 dB的{a['previous_R3_overlap_records']}条记录逐一吻合，最大误差差值{a['maximum_previous_R3_error_m']:.3g} m。因此R变化没有改动既有R=3基线。",
        '这次32位置均值与原400位置报告的均值可能不同，不能直接把两种样本规模的R=3平均数当作回归差异。此次只有一套冻结噪声实现和一种嵌套AP顺序，后续可再扩大至400位置，或另行考察AP子集选择；本次不自动覆盖正式实验。',
        "```matlab\naddpath('8.单流');\nout=fullfile(pwd,'8.单流','results','new_reference_ap_pilot');\nrun_reference_ap_pilot('OutputDir',out);\nplot_reference_ap_pilot(out);\n```",
        '```text\npython analyze_reference_ap_pilot.py results/new_reference_ap_pilot --stage audit\npython analyze_reference_ap_pilot.py results/new_reference_ap_pilot --stage report\n```',
        '原始逐位置记录、8 AP的估计值、参考集合、实际整数比特串、数值汇总及10组PNG/FIG单独保存。Word沿用现有文档流程生成，按用户要求不追加Word检查。']
    dest=ROOT/'docs/UPA固定8AP定位参考数扫描预实验报告.md';dest.write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    (out/'pilot_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(findings,ensure_ascii=False),flush=True);print(dest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('results');p.add_argument('--stage',choices=['audit','report'],default='audit');a=p.parse_args()
    out=Path(a.results);out=out if out.is_absolute() else ROOT/out
    if a.stage=='audit':audit(out)
    else:report(out)

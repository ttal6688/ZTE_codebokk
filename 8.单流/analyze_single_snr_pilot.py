"""Audit and describe the low-to-high observation-SNR pilot without changing algorithms."""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil
import numpy as np
import pandas as pd
import audit_single_stream_protocol as base
from audit_dual_stream import truth

ROOT=Path(__file__).resolve().parent
GEO=['HAQSE_R3','DFT_INDEX_R3','POS_R3']
METHODS=['TYPE_I','TYPE_II','DOCOMO_NFLOS']+GEO
NAMES={'IDEAL_SVD':'SVD参考','TYPE_I':'全反馈Type-I(UE)','TYPE_II':'全反馈Type-II(UE)',
       'DOCOMO_NFLOS':'Docomo','HAQSE_R3':'空间频率','DFT_INDEX_R3':'DFT索引','POS_R3':'位置反馈'}

def read(path,**kw):
    return pd.read_csv(path if path.exists() else path.with_suffix(path.suffix+'.gz'),**kw)

def panel(source,branch):
    q=source[source.branch.eq(branch)].copy()
    if branch=='CPU':
        for m in METHODS[:3]:
            if not q.method.eq(m).any():
                ref=source[source.branch.eq('UE')&source.method.eq(m)].copy();ref['branch']='CPU'
                q=pd.concat([q,ref],ignore_index=True)
    return q

def name(m,branch):return 'Docomo(UE)' if m=='DOCOMO_NFLOS' and branch=='CPU' else NAMES[m]

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])

def audit(out):
    contract=json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'))
    rho=contract['rho_data']
    # Reuse the independent payload decoder, position recovery and mean checks.
    paired=out/'paired_CSI.csv'
    if not paired.exists():
        with gzip.open(paired.with_suffix('.csv.gz'),'rb') as a,paired.open('wb') as b:shutil.copyfileobj(a,b)
    t,_=base.audit(out)
    c=read(out/'noisefree_control_trials.csv',dtype={'feedback_wire':'string'})
    maxrate=0.;maxpower=0.;maxcontrol=0.
    for group in [t,c]:
        for row in group.itertuples():
            H=truth(row.sample_id,row.channel_model,row.UPA_side,row.B,row.Rician_K_dB)
            if row.method=='IDEAL_SVD':
                power=float(np.linalg.eigvalsh(H@H.conj().T)[-1])
            else:
                mode='CPU_MODEL' if row.role=='CPU_METHOD' else ('DOCOMO' if row.method=='DOCOMO_NFLOS' else 'UE_PHASE')
                decoded=base.decode(str(row.feedback_wire),row.method,mode,row.B,row.UPA_side)
                F,p,ny,nz=base.spatial(row.method,decoded,row.B,row.UPA_side)
                saved=np.array(json.loads(row.AP_coefficients));coeff=saved[:,0]+1j*saved[:,1]
                if group is c:
                    if mode=='CPU_MODEL':expected=base.cpu_phase(p,F,row.B,ny,nz)
                    elif mode=='DOCOMO':expected=np.exp(2j*np.pi*np.r_[0,decoded['beta_indices'].ravel()]/4)*np.exp(2j*np.pi*np.arange(row.B)*decoded['ap_dft_index'][0,0]/row.B)
                    else:expected=np.exp(2j*np.pi*np.r_[0,decoded['phase_indices'].ravel()]/16)
                    error=float(np.max(abs(expected-coeff)));maxcontrol=max(maxcontrol,error);assert error<1e-7
                    if p is not None:
                        recorded=np.array([row.estimated_x_m,row.estimated_y_m,row.estimated_z_m]);assert np.max(abs(p-recorded))<1e-8
                        actual=np.array([row.true_x_m,row.true_y_m,row.true_z_m]);assert abs(np.linalg.norm(p-actual)-row.position_error_m)<1e-8
                    assert abs(np.linalg.norm(F*coeff[None,:]/np.sqrt(row.B))**2-1)<1e-10
                w=(F*coeff[None,:]).ravel(order='F')/np.sqrt(row.B);power=float(np.linalg.norm(H@w)**2)
            rate=400*np.log2(1+rho*power)
            maxrate=max(maxrate,abs(rate-row.throughput_Mbps));maxpower=max(maxpower,abs(power-row.received_power))
    assert maxrate<1e-5 and maxpower<1e-8
    controlkeys=['branch','role','csi','channel_model','method']
    expected=c.groupby(controlkeys).agg(samples=('sample_id','count'),mean_position_error_m=('position_error_m','mean'),
        mean_raw_position_error_m=('raw_position_error_m','mean'),mean_throughput_Mbps=('throughput_Mbps','mean'),
        mean_spectral_efficiency=('spectral_efficiency','mean'),mean_feedback_bits=('feedback_bits','mean')).reset_index()
    actual=pd.read_csv(out/'noisefree_control_summary.csv')
    joined=expected.merge(actual,on=controlkeys,suffixes=('_e','_a'),validate='one_to_one');assert len(joined)==len(expected)==len(actual)
    for col in ['samples','mean_position_error_m','mean_raw_position_error_m','mean_throughput_Mbps','mean_spectral_efficiency','mean_feedback_bits']:
        assert np.allclose(joined[col+'_e'],joined[col+'_a'],equal_nan=True,atol=1e-9,rtol=1e-9)
    perfect=t[t.csi.eq('PERFECT')];keys=['branch','channel_model','method','sample_id']
    spread=perfect.groupby(keys).throughput_Mbps.agg(lambda v:v.max()-v.min()).max();assert spread<1e-8
    reference=t[t.method.eq('IDEAL_SVD')].groupby(keys).throughput_Mbps.agg(lambda v:v.max()-v.min()).max();assert reference<1e-8
    old=read(ROOT/'results/single_stream_V3_full400/single_stream_trials.csv',usecols=['branch','channel_model','method','sample_id','curve','x_value','throughput_Mbps'])
    overlap=t[t.channel_model.eq('MIX')&t.x_value.isin([20,30,40])&~t.csi.eq('PERFECT')]
    joined=overlap.merge(old,on=['branch','channel_model','method','sample_id','curve','x_value'],suffixes=('_new','_old'),validate='one_to_one')
    assert len(joined)==len(overlap);error=float(abs(joined.throughput_Mbps_new-joined.throughput_Mbps_old).max());assert error<1e-6
    obs=t[t.csi.eq('OBSERVED')]
    diagnostics=obs.groupby(['branch','channel_model','method','x_value']).agg(samples=('sample_id','count'),
        mean_position_error_m=('position_error_m','mean'),median_position_error_m=('position_error_m','median'),
        p95_position_error_m=('position_error_m',lambda v:v.quantile(.95)),maximum_position_error_m=('position_error_m','max'),
        mean_raw_position_error_m=('raw_position_error_m','mean'),overflow_fraction=('quantizer_overflow','mean'),
        mean_throughput_Mbps=('throughput_Mbps','mean'),mean_feedback_bits=('feedback_bits','mean')).reset_index()
    diagnostics.to_csv(out/'pilot_diagnostics.csv',index=False)
    result=dict(status='passed',main_records=len(t),noisefree_control_records=len(c),positions=32,observation_SNRs=sorted(t.x_value.unique().tolist()),
        independent_true_channel_rate_checks=len(t)+len(c),maximum_rate_error_Mbps=maxrate,maximum_received_power_error=maxpower,
        maximum_noisefree_CPU_or_UE_coefficient_error=maxcontrol,old_full400_overlap_records=len(joined),maximum_old_full400_overlap_error_Mbps=error,
        perfect_control_SNR_spread_Mbps=float(spread),SVD_SNR_spread_Mbps=float(reference),
        independent_noise_repetitions_per_position=1,all_samples_retained=True)
    (out/'independent_pilot_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

def report(out):
    contract=json.loads((out/'pilot_contract.json').read_text(encoding='utf-8'))
    a=json.loads((out/'independent_pilot_audit.json').read_text(encoding='utf-8'))
    s=pd.read_csv(out/'single_stream_summary.csv');s=s[~s.csi.eq('PERFECT')]
    controls=pd.read_csv(out/'noisefree_control_summary.csv');d=pd.read_csv(out/'pilot_diagnostics.csv')
    snrs=sorted(s.x_value.unique());relative='../results/'+out.name
    lines=['# UPA单流低至高观测SNR预实验报告',
        '2026年10月25日。为解释原20至40 dB曲线为何接近水平，本次将CSI观测SNR扩展至−20、−10、0、10、20、30、40 dB，先使用32个冻结位置，分别测试纯LOS与MIX。数据链路参考SNR仍为10 dB，未随横轴增加。本次是诊断预实验，不替代原400位置正式结果。',
        '## 1 实验设置与实现',
        table(['项目','设置'],[['位置选择','从原1至400号位置等间隔取32个，round(linspace(1,400,32))，未按结果挑选'],
        ['阵列与协作','每AP 32×32单极化UPA，8个协作AP，3个定位参考AP，UE四接收阵元'],
        ['横轴','CSI观测SNR：−20、−10、0、10、20、30、40 dB'],['信道','LOS与MIX分开，MIX的K固定10 dB'],
        ['数据链路','沿用冻结参考数据SNR10 dB，rho=39.2994887549；400 MHz直接换算'],
        ['反馈与相位','原整数协议、13/14/9 bit坐标、4 bit UE相位及现有全部方法保持不变'],
        ['无观测噪声对照','同算法直接使用Htrue生成消息；CPU只接收该空间消息和公共几何，真实信道仅作评价'],
        ['噪声重复','每位置、每物理AP使用原冻结噪声矩阵，跨SNR只缩放幅度；每位置一次噪声实现']]),
        '横轴只改变信道估计噪声，不改变真实信道或评价端的数据SNR。SVD参考使用真实信道直接求解，因此应保持水平。同算法无观测噪声对照仍受原码本、量化和相位规则约束，不等同于SVD，也不是有限约束下的全局最优上界。',
        '定位是CPU与UE共用的前端，因此两端定位误差相同；分别列图只为保持报告结构。CPU图中的全反馈Type-I(UE)、全反馈Type-II(UE)和Docomo(UE)仍是UE共享参考。',
        '无观测噪声下的CPU对照由原UE完美观测行中已保存的空间整数消息恢复，清除UE相位字段后，由原CPU解码器重新计算相位；未把完整观测信道传入CPU。',
        '## 2 主要发现']
    findings=[]
    for model,modelname in [('LOS','纯LOS'),('MIX','混合信道')]:
        q=d[d.branch.eq('CPU')&d.channel_model.eq(model)&d.method.eq('POS_R3')].set_index('x_value')
        cpu=panel(s,'CPU');cpu=cpu[cpu.channel_model.eq(model)&cpu.method.eq('POS_R3')].set_index('x_value')
        ue=s[s.branch.eq('UE')&s.channel_model.eq(model)&s.method.eq('POS_R3')].set_index('x_value')
        c=controls[controls.branch.eq('CPU')&controls.channel_model.eq(model)&controls.method.eq('POS_R3')].iloc[0]
        text=f'{modelname}：位置反馈的坐标解码后平均定位误差从−20 dB的{q.loc[-20].mean_position_error_m:.6g} m变为40 dB的{q.loc[40].mean_position_error_m:.6g} m；同算法无观测噪声对照为{c.mean_position_error_m:.6g} m。CPU平均吞吐量从{cpu.loc[-20].mean_throughput_Mbps:.2f}变为{cpu.loc[40].mean_throughput_Mbps:.2f} Mbps，UE从{ue.loc[-20].mean_throughput_Mbps:.2f}变为{ue.loc[40].mean_throughput_Mbps:.2f} Mbps。无观测噪声时，量化前的连续定位误差为{1000*c.mean_raw_position_error_m:.3f} mm，量化解码后为{1000*c.mean_position_error_m:.3f} mm。'
        lines += [text];findings.append(dict(model=model,position_at_minus20_m=float(q.loc[-20].mean_position_error_m),position_at40_m=float(q.loc[40].mean_position_error_m),
            position_noisefree_m=float(c.mean_position_error_m),raw_position_noisefree_m=float(c.mean_raw_position_error_m),CPU_rate_minus20=float(cpu.loc[-20].mean_throughput_Mbps),CPU_rate40=float(cpu.loc[40].mean_throughput_Mbps),
            UE_rate_minus20=float(ue.loc[-20].mean_throughput_Mbps),UE_rate40=float(ue.loc[40].mean_throughput_Mbps)))
    lines += ['本次已看到低SNR退化、过渡与高SNR平台。纯LOS中坐标量化后的平台明显高于连续定位平台；MIX中即使去掉观测噪声，连续定位仍有约毫米级至厘米级残差，提高观测SNR无法消除这些残差。UE吞吐量的饱和早于CPU几何相位方案，不能要求同一条SNR轴上的所有方法持续上升。',
        '低SNR段与高SNR段应分开解读；离散码本、量化和主模式投影不保证逐点或每个样本单调。不能把个别有限SNR结果超过同算法无噪声对照解释为噪声有益。是否存在稳定差异需要增加独立噪声重复。',
        '若继续正式扫描，建议优先在−20至0 dB过渡段按5 dB加密，并保留10、20、30、40 dB观察平台。各方法、CPU与UE使用统一横轴，数据链路SNR仍固定；本次不自动替换原400位置结果。']
    for chapter,branch in [(3,'CPU'),(4,'UE')]:
        q=panel(s,branch);control=panel(controls,branch)
        lines += [f'## {chapter} {branch}端预实验']
        for model,modelname in [('LOS','纯LOS'),('MIX','混合信道')]:
            m=q[q.channel_model.eq(model)];c=control[control.channel_model.eq(model)].set_index('method')
            for metric,field,methods,digits in [('定位误差','mean_position_error_m',GEO,4),('吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+METHODS,2)]:
                rows=[]
                for method in methods:
                    values=m[m.method.eq(method)].set_index('x_value')
                    rows.append([name(method,branch)]+[(f'{values.loc[x,field]:.{digits}g}' if metric=='定位误差' else f'{values.loc[x,field]:.2f}') for x in snrs])
                stem='position' if metric=='定位误差' else 'throughput'
                lines += ['### '+branch+modelname+metric+'随观测SNR变化',
                    '定位误差单位为m，图片采用对数纵轴以兼顾低SNR大误差与高SNR毫米级误差。' if metric=='定位误差' else '吞吐量单位为Mbps，数据链路条件固定；SVD水平线是预期行为。',
                    table(['方法']+[f'{x:g} dB' for x in snrs],rows),
                    f'![{branch}{modelname}{metric}随CSI观测SNR变化]({relative}/{branch}/{branch}_{model}_{stem}_SNR.png)']
            rows=[]
            for method in ['IDEAL_SVD']+METHODS:
                row=c.loc[method];error='不适用' if pd.isna(row.mean_position_error_m) else f'{row.mean_position_error_m:.6g}'
                rows.append([name(method,branch),error,f'{row.mean_throughput_Mbps:.2f}'])
            lines += ['### '+branch+modelname+'同算法无观测噪声对照',table(['方法','定位误差 m','吞吐量 Mbps'],rows)]
    lines += ['## 5 定位平台与低SNR异常的补充诊断']
    for model,modelname in [('LOS','纯LOS'),('MIX','混合信道')]:
        q=d[d.branch.eq('CPU')&d.channel_model.eq(model)&d.method.eq('POS_R3')].sort_values('x_value')
        rows=[[f'{r.x_value:g}',f'{r.mean_raw_position_error_m:.6g}',f'{r.mean_position_error_m:.6g}',f'{r.median_position_error_m:.6g}',f'{r.p95_position_error_m:.6g}',f'{100*r.overflow_fraction:.2f}%'] for r in q.itertuples()]
        lines += ['### '+modelname+'位置反馈连续估计与坐标量化',table(['观测SNR dB','连续均值 m','解码均值 m','解码中位 m','解码95%分位 m','越界比例'],rows),
            f'![{modelname}位置反馈连续估计与量化后定位误差]({relative}/diagnostics/{model}_POS_continuous_vs_quantized.png)',
            '坐标只量化一次。低SNR下若连续估计超出公共编码区域，截断先验可能显著降低解码后的欧氏误差，不能据此认为量化改善了定位估计器。所有32个位置均保留。无观测噪声下仍存在的连续定位误差说明误差并非全部由观测噪声引起；该对照不能进一步单独区分球面波近似、单频点拟合和散射各自的贡献。']
    lines += ['## 6 核验与复现',
        f"独立核验覆盖{a['main_records']:,}条主扫描记录和{a['noisefree_control_records']:,}条对照记录。整数消息、CPU/UE空间消息一致性、反馈长度、位置恢复和汇总均值均已检查；真实信道由独立Python实现重建，速率最大误差{a['maximum_rate_error_Mbps']:.3g} Mbps。",
        f"本次MIX中20、30、40 dB与原400位置实验重合的{a['old_full400_overlap_records']:,}条记录逐一对齐，最大吞吐量差{a['maximum_old_full400_overlap_error_Mbps']:.3g} Mbps。无噪声同算法对照与SVD参考跨观测SNR保持不变。",
        '这是32位置、每位置一次冻结噪声实现的范围诊断，不能替代400位置正式扫描，也不能据此给出独立重复噪声的置信区间。正式范围应结合低SNR退化、过渡段和平台共同确定。',
        "```matlab\naddpath('8.单流');\nout=fullfile(pwd,'8.单流','results','new_snr_pilot32');\nrun_single_snr_pilot('OutputDir',out);\nplot_single_snr_pilot(out);\n```",
        '```text\npython analyze_single_snr_pilot.py results/new_snr_pilot32 --stage audit\npython analyze_single_snr_pilot.py results/new_snr_pilot32 --stage report\n```',
        '输出目录必须是新目录；原400位置单流、双流结果和原报告均不覆盖。参数、位置编号、原始消息、无噪声对照、数值汇总与10组PNG/FIG一起保存。Word沿用现有文档生成流程，按用户要求不追加Word渲染检查。']
    dest=ROOT/'docs/UPA单流低至高观测SNR预实验报告.md';dest.write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    (out/'pilot_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(findings,ensure_ascii=False),flush=True);print(dest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('results');p.add_argument('--stage',choices=['audit','report'],default='audit');a=p.parse_args()
    out=Path(a.results);out=out if out.is_absolute() else ROOT/out
    if a.stage=='audit':audit(out)
    else:report(out)

"""Exhaustive case audit plus scan coverage, pairing and single-run consistency."""
from pathlib import Path
import argparse,json,os
import numpy as np
import pandas as pd
from audit_dual_stream import audit as audit_case
ROOT=Path(__file__).resolve().parent

def read_table(path):
    return pd.read_csv(path if path.exists() else path.with_suffix(path.suffix+'.gz'))

def audit(out,stage,worker,workers):
    if stage=='cases':
        for directory in sorted((out/'cases').glob('case_*')):
            k=int(directory.name.split('_')[-1])
            if (k-worker)%workers==0:
                audit_case(directory)
                print('audited',directory.name,flush=True)
        return
    contract=json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'))
    ids=contract['sample_ids'];summaries=[];pairs=[];audits=[];negative=[]
    for setting in contract['settings']:
        d=out/'cases'/f"case_{setting['case_id']:02d}"
        audit=json.loads((d/'independent_dual_audit.json').read_text(encoding='utf-8'))
        assert audit['status'] in ['passed','passed_metrics_pending_native_replay','passed_with_native_replay']
        if audit['status']!='passed':
            native=json.loads((d/'native_continuous_replay_audit.json').read_text(encoding='utf-8'))
            assert native['status']=='passed' and native['flagged_records']==audit['continuous_optimizer_native_replay_required'] and native['maximum_C_replay_error']<1e-10
        audits.append(audit)
        s=pd.read_csv(d/'dual_stream_summary.csv');p=read_table(d/'single_dual_pairs.csv')
        for table in [s,p]:
            table['curve']=setting['curve'];table['x_value']=setting['xvalue'];table['case_id']=setting['case_id']
            for key in ['Nant','B','SNRdB','KdB']:table[key]=setting[key]
        summaries.append(s);pairs.append(p)
    s=pd.concat(summaries,ignore_index=True);p=pd.concat(pairs,ignore_index=True)
    actual_s=pd.read_csv(out/'dual_stream_summary.csv');actual_p=read_table(out/'single_dual_pairs.csv')
    skeys=['branch','channel_model','method','stream_count','csi','curve','x_value'];pkeys=['branch','channel_model','method','sample_id','curve','x_value']
    for expected,actual,keys in [(s,actual_s,skeys),(p,actual_p,pkeys)]:
        joined=expected.merge(actual,on=keys,suffixes=('_e','_a'),validate='one_to_one');assert len(joined)==len(expected)==len(actual)
        for field in expected.select_dtypes(include='number').columns:
            if field not in keys:assert np.allclose(joined[field+'_e'],joined[field+'_a'],equal_nan=True,rtol=1e-10,atol=1e-7),field
    assert s.samples.eq(len(ids)).all()
    group=p.groupby(['branch','channel_model','method','curve','x_value']).sample_id.agg(['count','nunique'])
    assert group['count'].eq(len(ids)).all() and group['nunique'].eq(len(ids)).all()
    finite=p[~p.method.eq('IDEAL_SVD')].copy()
    assert np.allclose(finite.extra_bits,np.where(finite.branch.eq('CPU'),0,4*(finite.B-1)))
    negatives=finite[finite.delta_Mbps<=0].copy();negatives.to_csv(out/'nonpositive_gain_cases.csv',index=False)
    keys=['branch','channel_model','method','curve','x_value','Nant','B','SNRdB','KdB']
    stats=finite.groupby(keys,dropna=False).agg(samples=('sample_id','count'),mean_single_Mbps=('single_Mbps','mean'),mean_dual_Mbps=('dual_Mbps','mean'),
      mean_delta_Mbps=('delta_Mbps','mean'),minimum_delta_Mbps=('delta_Mbps','min'),positive_fraction=('delta_Mbps',lambda x:np.mean(x>0)),
      mean_second_mode_ratio=('second_mode_ratio','mean'),minimum_second_mode_ratio=('second_mode_ratio','min'),dual_bits=('dual_bits','mean')).reset_index()
    stats.to_csv(out/'method_feasibility_summary.csv',index=False)
    # Historical full single run has the identical MIX samples/settings/noise; do not merely compare means.
    source=ROOT/'results/single_stream_V3_full400/single_stream_trials.csv.gz'
    old=pd.read_csv(source,usecols=['branch','channel_model','curve','x_value','method','sample_id','throughput_Mbps','feedback_bits'])
    compare=p[p.channel_model.eq('MIX')].merge(old,on=pkeys,validate='one_to_one')
    assert len(compare)==len(p[p.channel_model.eq('MIX')])
    error=float(np.max(abs(compare.single_Mbps-compare.throughput_Mbps)))
    assert error<1e-6 and np.allclose(compare.single_bits,compare.feedback_bits,equal_nan=True)
    los=p[p.channel_model.eq('LOS') & p.curve.eq('莱斯因子')]
    spread=los.groupby(['branch','method','sample_id']).dual_Mbps.agg(lambda x:x.max()-x.min()).max()
    assert spread<1e-8
    ref=p[p.method.eq('IDEAL_SVD') & p.curve.eq('SNR')]
    refspread=ref.groupby(['branch','channel_model','sample_id']).dual_Mbps.agg(lambda x:x.max()-x.min()).max()
    assert refspread<1e-8
    unique=finite.drop_duplicates(['case_id','channel_model','branch','method','sample_id'])
    result=dict(status='passed',positions=len(ids),physical_settings=len(contract['physical_settings']),scan_labels=len(contract['settings']),
       physical_records=sum(json.loads((d/'audit.json').read_text())['records'] for d in (out/'cases').glob('case_*')),
       expanded_records=int(s.samples.sum()),expanded_pairs=len(p),implementable_expanded_pairs=len(finite),implementable_physical_pairs=len(unique),
       expanded_nonpositive_pairs=len(negatives),physical_nonpositive_pairs=int(np.sum(unique.delta_Mbps<=0)),
       minimum_gain_Mbps=float(finite.delta_Mbps.min()),maximum_old_single_Mbps_error=error,
       LOS_K_control_maximum_Mbps_spread=float(spread),SVD_observation_SNR_control_maximum_Mbps_spread=float(refspread),
       all_groups_have_400_distinct_samples=(len(ids)==400),all_case_audits_passed=True,
       maximum_metric_SE_error=max(a['maximum_metric_SE_error'] for a in audits),
       maximum_true_effective_channel_error=max(a['maximum_true_effective_channel_error'] for a in audits),
       maximum_CPU_continuous_coefficient_numerical_error=max(a['maximum_CPU_continuous_coefficient_numerical_error'] for a in audits),
       maximum_precoder_signature_error=max(a['maximum_precoder_signature_error'] for a in audits))
    distinct_audits=[json.loads((d/'independent_dual_audit.json').read_text(encoding='utf-8')) for d in (out/'cases').glob('case_*')]
    result['native_replayed_cross_implementation_disagreements']=sum(a.get('continuous_optimizer_native_replay_required',0) for a in distinct_audits)
    result['maximum_CPU_design_SE_cross_implementation_difference']=max((a.get('maximum_CPU_design_SE_cross_implementation_difference',0) for a in distinct_audits if a.get('continuous_optimizer_native_replay_required',0)>0),default=0)
    result['CPU_design_SE_difference_scope']='cases requiring native continuous-optimizer replay'
    (out/'independent_full_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('results');p.add_argument('--stage',choices=['cases','summary'],default='cases');p.add_argument('--worker',type=int,default=1);p.add_argument('--workers',type=int,default=1)
    a=p.parse_args();audit(ROOT/a.results,a.stage,a.worker,a.workers)

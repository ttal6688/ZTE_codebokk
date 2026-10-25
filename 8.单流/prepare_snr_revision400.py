"""Assemble frozen paired cases for the revised 400-position UPA reports.

New cases use the original native runner and decoder. Existing physical cases
are referenced, not simulated again. Localization is decoded from spatial bits.
"""
from pathlib import Path
import argparse, concurrent.futures, gzip, hashlib, json, os, subprocess, sys, time
import numpy as np
import pandas as pd
import audit_single_stream_protocol as base

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'results/upa_snr_revision400_20261025'
OLD = ROOT/'results/dual_stream_full400'
LOCATION_SNRS = list(range(-20,41,10))
RATE_SNRS = list(range(-20,21,5))
SNRS = sorted(set(LOCATION_SNRS+RATE_SNRS))
GEO = ['HAQSE_R3','DFT_INDEX_R3','POS_R3']

def write_json(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def source_csv(directory, name):
    path = directory/name
    return path if path.exists() else path.with_suffix('.csv.gz')

def audit_new():
    def one(snr):
        directory=OUT/'cases'/f'snr_{snr:+03d}'
        for _ in range(1800):
            if (directory/'audit.json').exists():break
            time.sleep(2)
        assert (directory/'audit.json').exists(), directory
        if (directory/'independent_dual_audit.json').exists():return snr
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1')
        log=directory/'independent_audit.log'
        with log.open('w',encoding='utf-8') as f:
            subprocess.run([sys.executable,str(ROOT/'audit_dual_stream.py'),str(directory)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
        return snr
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for snr in pool.map(one,range(-20,20,5)):
            print('independent case audit',snr,flush=True)

def settings():
    result=[]
    for snr in SNRS:result.append(dict(curve='SNR',x_value=snr,N=1024,B=8,SNR=snr,K=10))
    for n in [64,256,1024]:result.append(dict(curve='天线数',x_value=n,N=n,B=8,SNR=30,K=10))
    for b in range(5,11):result.append(dict(curve='AP数',x_value=b,N=1024,B=b,SNR=30,K=10))
    for k in range(0,21,5):result.append(dict(curve='莱斯因子',x_value=k,N=1024,B=8,SNR=30,K=k))
    return result

def assemble():
    previous=json.loads((OLD/'experiment_contract.json').read_text(encoding='utf-8'))
    oldaudit=json.loads((OLD/'independent_full_audit.json').read_text(encoding='utf-8'))
    assert oldaudit['status']=='passed'
    sources={tuple(q):OLD/'cases'/f'case_{i:02d}' for i,q in enumerate(previous['physical_settings'],1)}
    for snr in range(-20,20,5):sources[(1024,8,snr,10)]=OUT/'cases'/f'snr_{snr:+03d}'
    scans=settings();physical={};summaries=[];localizations=[];pair_summaries=[];manifest=[]
    sim=json.loads((base.PUBLIC/'simulation_settings.json').read_text(encoding='utf-8'))
    positions=pd.read_csv(base.PUBLIC/sim['UE_positions_file']).set_index('sample_id')
    cache={};overlap=0;maxdiff=0.
    oldsingle=pd.read_csv(ROOT/'results/single_stream_V3_full400/single_stream_trials.csv.gz',usecols=['branch','channel_model','sample_id','method','curve','x_value','throughput_Mbps','feedback_bits'])
    all_loc=[]
    for setting in scans:
        key=tuple(setting[k] for k in ['N','B','SNR','K'])
        if key in physical:continue
        directory=sources[key];c=json.loads((directory/'experiment_contract.json').read_text(encoding='utf-8'))
        assert c['sample_ids']==list(range(1,401)) and c['channel_models']==['LOS','MIX']
        assert [c['N'],c['B'],c['observation_SNR_dB'],c['K_dB']]==list(key)
        audit=json.loads((directory/'independent_dual_audit.json').read_text(encoding='utf-8'))
        assert audit['status'] in ['passed','passed_with_native_replay'],directory
        path=source_csv(directory,'dual_stream_trials.csv')
        t=pd.read_csv(path,dtype={'feedback_wire':'string'})
        assert len(t)==17600 and t.total_power.between(1-1e-10,1+1e-10).all()
        groups=t.groupby(['branch','channel_model','method','stream_count']).sample_id.agg(['count','nunique'])
        assert groups['count'].eq(400).all() and groups['nunique'].eq(400).all()
        loc=[]
        for r in t[t.stream_count.eq(1)&t.method.isin(GEO)].itertuples():
            width={'HAQSE_R3':84,'DFT_INDEX_R3':6*int(np.log2(4*r.UPA_side)),'POS_R3':36}[r.method]
            wire=str(r.feedback_wire)[:width];ckey=(r.method,r.UPA_side,wire)
            if ckey not in cache:
                decoded=base.decode(wire,r.method,'CPU_MODEL',1,r.UPA_side)
                code=decoded['integer_codes']
                if r.method=='POS_R3':p=base.LO+(code.ravel()+.5)*base.SPAN/2.**base.BITS
                else:
                    freq=-.5+code/(2**14-1) if r.method=='HAQSE_R3' else -((code/(4*r.UPA_side)+.5)%1-.5)
                    p=base.localize(freq)
                cache[ckey]=p
            p=cache[ckey];truth=positions.loc[r.sample_id,['x_m','y_m','UPA_z_m']].to_numpy(float)
            loc.append(dict(branch=r.branch,channel_model=r.channel_model,method=r.method,sample_id=r.sample_id,
                            estimated_x_m=p[0],estimated_y_m=p[1],estimated_z_m=p[2],position_error_m=np.linalg.norm(p-truth)))
        loc=pd.DataFrame(loc)
        # The second column must reuse exactly the same spatial prefix.
        a=t[t.stream_count.eq(1)&t.method.isin(GEO)];b=t[t.stream_count.eq(2)&t.method.isin(GEO)]
        check=a.merge(b,on=['branch','channel_model','method','sample_id'],suffixes=('_a','_b'),validate='one_to_one')
        assert all(str(r.feedback_wire_b).startswith(str(r.feedback_wire_a)) for r in check.itertuples())
        keys=['branch','channel_model','method','stream_count','csi']
        summary=t.groupby(keys).agg(samples=('sample_id','count'),mean_throughput_Mbps=('throughput_Mbps','mean'),
            mean_spectral_efficiency=('spectral_efficiency','mean'),mean_feedback_bits=('feedback_bits','mean'),
            mean_second_mode_ratio=('second_mode_ratio','mean')).reset_index()
        ls=loc.groupby(['branch','channel_model','method']).agg(samples=('sample_id','count'),mean_position_error_m=('position_error_m','mean')).reset_index()
        summary=summary.merge(ls.drop(columns='samples'),on=['branch','channel_model','method'],how='left',validate='many_to_one')
        pair=pd.read_csv(source_csv(directory,'single_dual_pairs.csv'))
        ps=pair[~pair.method.eq('IDEAL_SVD')].groupby(['branch','channel_model','method']).agg(
            mean_delta_Mbps=('delta_Mbps','mean'),minimum_delta_Mbps=('delta_Mbps','min'),positive_fraction=('delta_Mbps',lambda x:float((x>0).mean()))).reset_index()
        # Match the old single-stream formal data for every reused MIX setting.
        match_settings=[s for s in previous['settings'] if tuple(s[k] for k in ['Nant','B','SNRdB','KdB'])==key]
        for oldsetting in match_settings[:1]:
            old=oldsingle[oldsingle.curve.eq(oldsetting['curve'])&oldsingle.x_value.eq(oldsetting['xvalue'])&oldsingle.channel_model.eq('MIX')]
            q=t[t.stream_count.eq(1)&t.channel_model.eq('MIX')]
            m=q.merge(old,on=['branch','channel_model','method','sample_id'],suffixes=('_new','_old'),validate='one_to_one')
            assert len(m)==4400
            err=float(abs(m.throughput_Mbps_new-m.throughput_Mbps_old).max());assert err<1e-7
            assert np.allclose(m.feedback_bits_new,m.feedback_bits_old,equal_nan=True)
            overlap+=len(m);maxdiff=max(maxdiff,err)
        idx=len(physical)+1
        physical[key]=(summary,ps)
        loc['physical_case']=idx
        for name,value in zip(['N','B','SNR','K'],key):loc[name]=value
        all_loc.append(loc)
        published=path if path.suffix=='.gz' else path.with_suffix('.csv.gz')
        assert published.exists(), 'Run package before assemble'
        manifest.append(dict(physical_case=idx,N=key[0],B=key[1],SNR=key[2],K=key[3],
            directory=directory.relative_to(ROOT).as_posix(),source=published.relative_to(ROOT).as_posix(),
            input_sha256=hashlib.sha256(published.read_bytes()).hexdigest(),
            reused=directory.is_relative_to(OLD),audit_status=audit['status']))
        print('assembled',idx,key,flush=True)
    for setting in scans:
        key=tuple(setting[k] for k in ['N','B','SNR','K']);s,p=physical[key]
        s=s.copy();p=p.copy()
        for name,value in setting.items():s[name]=value;p[name]=value
        summaries.append(s);pair_summaries.append(p)
    summary=pd.concat(summaries,ignore_index=True);pairs=pd.concat(pair_summaries,ignore_index=True)
    assert summary.samples.eq(400).all()
    # Ideal references are invariant to observation SNR; LOS ignores K.
    for curve,model in [('SNR',None),('莱斯因子','LOS')]:
        q=summary[summary.curve.eq(curve)]
        if model:q=q[q.channel_model.eq(model)]
        if curve=='SNR':q=q[q.method.eq('IDEAL_SVD')]
        assert q.groupby(['branch','channel_model','method','stream_count']).mean_throughput_Mbps.agg(lambda x:x.max()-x.min()).max()<1e-8
    summary.to_csv(OUT/'experiment_summary.csv',index=False)
    pairs.to_csv(OUT/'paired_gain_summary.csv',index=False)
    locall=pd.concat(all_loc,ignore_index=True)
    locall.to_csv(OUT/'localization_trials.csv.gz',index=False,compression='gzip')
    diag=pd.read_csv(OUT/'position_diagnostics.csv')
    q=locall[locall.method.eq('POS_R3')&locall.N.eq(1024)&locall.B.eq(8)]
    matched=q.merge(diag,on=['channel_model','sample_id','SNR','K'],suffixes=('_wire','_diag'),validate='many_to_one')
    assert len(matched)==24000
    diagerr=float(abs(matched.position_error_m_wire-matched.position_error_m_diag).max())
    assert diagerr<1e-10
    ds=diag.groupby(['channel_model','SNR','K']).agg(samples=('sample_id','count'),
        mean_raw_position_error_m=('raw_position_error_m','mean'),mean_position_error_m=('position_error_m','mean'),
        mean_quantizer_overflow=('quantizer_overflow','mean')).reset_index()
    assert ds.samples.eq(400).all();ds.to_csv(OUT/'position_diagnostics_summary.csv',index=False)
    contract=dict(version='UPA_SINGLE_DUAL_SNR_REVISION_20261025',positions=400,channel_models=['LOS','MIX'],
        localization_observation_SNR_dB=LOCATION_SNRS,throughput_observation_SNR_dB=RATE_SNRS,computed_union_SNR_dB=SNRS,
        default=dict(N=1024,B=8,SNR=30,K=10),data_SNR_fixed=True,bandwidth_Hz=400e6,reference_AP_count=3,
        settings=scans,physical_cases=manifest,physical_case_count=len(physical),
        single_stream_source='stream_count=1 of paired native cases; same original sstr.ue_designs and CPU decoder',
        localization_source='independently decode spatial prefix; second stream reuses exact same spatial bits',
        y_axis='localization label: 定位误差（m）; throughput linear, lower=max(0,min-max(3%*abs(min),1%*range))',
        historical_results_preserved=True)
    write_json(OUT/'experiment_contract.json',contract)
    write_json(OUT/'assembly_audit.json',dict(status='passed',positions=400,physical_cases=len(physical),
        physical_records=17600*len(physical),summary_rows=len(summary),
        old_single_overlap_records=overlap,maximum_old_single_throughput_difference_Mbps=maxdiff,
        CPU_UE_separate=True,LOS_MIX_separate=True,all_groups_400_distinct_positions=True,
        same_spatial_prefix_both_streams=True,ideal_SNR_invariant=True,LOS_K_invariant=True,
        diagnostic_overlap_records=len(matched),maximum_diagnostic_position_error_difference_m=diagerr))

def package():
    records=[]
    for snr in range(-20,20,5):
        directory=OUT/'cases'/f'snr_{snr:+03d}'
        for name in ['dual_stream_trials.csv','single_dual_pairs.csv']:
            source=directory/name;target=source.with_suffix('.csv.gz');raw=source.read_bytes()
            target.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0));assert gzip.decompress(target.read_bytes())==raw
            records.append(dict(file=target.relative_to(OUT).as_posix(),raw_sha256=hashlib.sha256(raw).hexdigest(),
                                gzip_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size))
    write_json(OUT/'compression_manifest.json',dict(status='passed',lossless=True,files=records))

def snapshot():
    paths=list((ROOT/'+sstr').glob('*.m'))
    for name in ['+upa','+posfb','lib']:paths+=list((ROOT/'6.位置反馈方案'/name).rglob('*.m'))
    paths+=list(base.PUBLIC.glob('*.json'))+list(base.PUBLIC.glob('*.csv'))
    for name in ['run_dual_stream_minimal.m','run_snr_revision400.m','run_revision_position_diagnostics.m',
                 'verify_dual_stream_replay.m','prepare_snr_revision400.py','plot_snr_revision400.m',
                 'verify_revision_snr_figures.m','build_snr_revision_reports.py','build_word_reports.py',
                 'build_single_detailed_report.py','build_dual_full_report.py','plot_single_stream_task2.m',
                 'audit_dual_stream.py','audit_single_stream_protocol.py']:
        paths.append(ROOT/name)
    entries=[]
    for path in sorted(set(paths)):
        raw=path.read_bytes().replace(b'\r\n',b'\n')
        entries.append(dict(path=path.relative_to(ROOT).as_posix(),sha256_LF=hashlib.sha256(raw).hexdigest()))
    write_json(OUT/'source_and_input_SHA256.json',dict(normalization='CRLF to LF',files=entries))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit-new','assemble','package','snapshot']);args=p.parse_args()
    {'audit-new':audit_new,'assemble':assemble,'package':package,'snapshot':snapshot}[args.stage]()

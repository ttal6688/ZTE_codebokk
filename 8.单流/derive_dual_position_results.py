"""Recover localization metrics from stored two-stream spatial payloads.

This reads existing messages only; it does not observe channels or optimize phases.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import audit_single_stream_protocol as base

ROOT = Path(__file__).resolve().parent
GEO = ['HAQSE_R3', 'DFT_INDEX_R3', 'POS_R3']


def build(out):
    out = Path(out)
    contract = json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'))
    sim = json.loads((base.PUBLIC/'simulation_settings.json').read_text(encoding='utf-8'))
    positions = pd.read_csv(base.PUBLIC/sim['UE_positions_file']).set_index('sample_id')
    rows = []
    cache = {}
    for case_id in sorted({s['case_id'] for s in contract['settings']}):
        directory = out/'cases'/f'case_{case_id:02d}'
        path = directory/'dual_stream_trials.csv'
        if not path.exists():
            path = path.with_suffix('.csv.gz')
        cols = ['branch','channel_model','sample_id','method','stream_count','UPA_side','feedback_wire']
        t = pd.read_csv(path, usecols=cols, dtype={'feedback_wire':'string'})
        t = t[t.stream_count.eq(2) & t.method.isin(GEO)]
        for r in t.itertuples():
            width = {'POS_R3':36, 'HAQSE_R3':84, 'DFT_INDEX_R3':6*int(np.log2(4*r.UPA_side))}[r.method]
            wire = str(r.feedback_wire)[:width]
            key = (r.method,r.UPA_side,wire)
            if key not in cache:
                s = base.decode(wire,r.method,'CPU_MODEL',1,r.UPA_side)
                codes = s['integer_codes']
                if r.method == 'POS_R3':
                    p = base.LO+(codes.ravel()+.5)*base.SPAN/2.**base.BITS
                else:
                    freq = -.5+codes/(2**14-1) if r.method=='HAQSE_R3' else -((codes/(4*r.UPA_side)+.5)%1-.5)
                    p = base.localize(freq)
                cache[key] = p
            p = cache[key]
            truth = positions.loc[r.sample_id,['x_m','y_m','UPA_z_m']].to_numpy(float)
            rows.append(dict(case_id=case_id,branch=r.branch,channel_model=r.channel_model,
                             sample_id=r.sample_id,method=r.method,stream_count=2,
                             position_error_m=float(np.linalg.norm(p-truth))))
        print(f'localized stored messages case {case_id}',flush=True)
    physical = pd.DataFrame(rows)
    physical.to_csv(out/'dual_position_trials.csv.gz',index=False,compression='gzip')
    scans = []
    for setting in contract['settings']:
        q = physical[physical.case_id.eq(setting['case_id'])].copy()
        q['curve'] = setting['curve'];q['x_value'] = setting['xvalue']
        scans.append(q)
    expanded = pd.concat(scans,ignore_index=True)
    keys = ['branch','channel_model','method','stream_count','curve','x_value','case_id']
    summary = expanded.groupby(keys).agg(samples=('sample_id','count'),mean_position_error_m=('position_error_m','mean')).reset_index()
    summary.to_csv(out/'dual_position_summary.csv',index=False)
    (out/'dual_position_source.json').write_text(json.dumps(dict(
        source='cases/case_XX/dual_stream_trials.csv(.gz), stream_count=2, original feedback_wire spatial prefix',
        truth='frozen public UE positions; evaluation only',
        method='existing integer decoder and localization equations; no channel observation or phase search rerun',
        stream_relation='second stream reuses the first spatial message; localization is unchanged by added stream phases',
        physical_localization_records=len(physical),summary_rows=len(summary)),ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    import sys
    build(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results/dual_stream_full400')

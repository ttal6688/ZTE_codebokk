"""Normalize existing AP-scan payloads to Type-I at the same AP/stream count."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import pandas as pd
from report_experiments import display_panel,UE

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/feedback_percentage_20261026'
SOURCE=ROOT/'results/upa_snr_revision400_20261025/experiment_summary.csv'

def build():
    OUT.mkdir(exist_ok=True)
    source=pd.read_csv(SOURCE);records=[]
    for ns in [1,2]:
        for branch in ['CPU','UE']:
            q=display_panel(source,branch)
            q=q[q.curve.eq('AP数')&q.stream_count.eq(ns)&q.method.isin(UE)]
            mix=q[q.channel_model.eq('MIX')].copy();los=q[q.channel_model.eq('LOS')]
            matched=mix.merge(los,on=['method','x_value'],suffixes=('_mix','_los'),validate='one_to_one')
            assert len(matched)==36 and np.array_equal(matched.mean_feedback_bits_mix,matched.mean_feedback_bits_los)
            reference=mix[mix.method.eq('TYPE_I')].set_index('x_value').mean_feedback_bits
            for r in mix.itertuples():
                B=int(r.x_value);bits=r.mean_feedback_bits;baseline=float(reference.loc[B]);assert r.samples==400
                if r.method=='TYPE_I':expected=18*B-4+(4*(B-1) if ns==2 else 0)
                elif r.method=='TYPE_II':expected=37*B-4+(4*(B-1) if ns==2 else 0)
                elif r.method=='DOCOMO_NFLOS':expected=16*B-2+math.ceil(math.log2(B))+(4*(B-1) if ns==2 else 0)
                else:
                    expected={'HAQSE_R3':84,'DFT_INDEX_R3':42,'POS_R3':36}[r.method]
                    if branch=='UE':expected+=4*ns*(B-1)
                assert bits==expected and baseline==18*B-4+(4*(B-1) if ns==2 else 0)
                records.append(dict(stream_count=ns,branch=branch,method=r.method,x_value=B,B=B,samples=400,
                    feedback_bits=bits,Type_I_bits=baseline,feedback_percentage=100*bits/baseline,
                    saving_percentage=100*(1-bits/baseline)))
    t=pd.DataFrame(records);assert len(t)==144
    assert t[t.method.eq('TYPE_I')].feedback_percentage.eq(100).all()
    t.to_csv(OUT/'feedback_percentage.csv',index=False)
    audit=dict(status='passed',source=SOURCE.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        rows=len(t),experiments=4,methods_per_experiment=6,AP_values=list(range(5,11)),visible_AP_values=list(range(5,10)),
        definition='100 * method payload / Type-I payload at identical AP and stream count',
        LOS_MIX_payloads_equal=True,all_counts_checked_against_integer_payload_formulas=True,simulation_rerun=False,
        below_or_above_100_preserved=True,figure_ylabel='相对全反馈Type-I的反馈开销（%）')
    (OUT/'calculation_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Derived 144 percentage values from existing payloads; four experiments, six methods each.')

if __name__=='__main__':build()

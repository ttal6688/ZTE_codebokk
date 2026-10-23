from pathlib import Path
import json,hashlib,math,subprocess
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
r=ROOT/'8.单流'
models=json.loads((r/'6.位置反馈方案/shared/network_geometry.json').read_text(encoding='utf-8'))
aps=models['models']['UPA32x32']['APs']
lo=np.array([19,19,-1]);span=np.array([12,12,7]);bits=np.array([13,14,9])
def localize(refs,f):
    A=np.zeros((3,3));rhs=np.zeros(3)
    for ref,fr in zip(refs,f.T):
        yz=-2*fr;q=np.r_[-np.sqrt(max(0,1-np.sum(yz**2))),yz];q/=np.linalg.norm(q)
        ap=aps[int(ref)-1];g=-np.array(ap['R_local_to_global'])@q;P=np.eye(3)-np.outer(g,g)
        A+=P;rhs+=P@np.array(ap['position_m']).reshape(3)
    return np.linalg.solve(A,rhs)
files=[r/'run_single_stream_task2.m',r/'plot_single_stream_task2.m',r/'verify_single_stream_upa.m',r/'audit_single_stream_upa.py']+list((r/'+sstr').glob('*.m'))
files+=list((r/'6.位置反馈方案/+upa').glob('*.m'))+list((r/'6.位置反馈方案/+posfb').glob('*.m'))
files+=list((r/'6.位置反馈方案/lib').glob('*.m'))+list((r/'6.位置反馈方案/shared').glob('*.json'))+list((r/'6.位置反馈方案/shared').glob('*.csv'))
manifest=[{'path':str(p.relative_to(r)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()} for p in sorted(files)]
unit=r/'results/single_stream_UPA_POS_V1_verify/fix_unit_audit.json'
if not unit.exists():unit=r/'results/single_stream_UPA_POS_V1_verify_final/fix_unit_audit.json'
for name,expected,ids in [('single_stream_UPA_POS_V1_verify_final',104,{399,400}),('single_stream_UPA_POS_V1_smoke2',312,{1,2})]:
    out=r/'results'/name;t=pd.read_csv(out/'single_stream_trials.csv')
    assert len(t)==expected and set(t.sample_id)==ids
    assert t.array.eq('UPA').all() and set(t.antenna_count)=={64,256,1024}
    assert (t.UPA_side**2==t.antenna_count).all()
    counts=0;maxerr=0.;poscount=0
    for row in t.itertuples():
        d=2*int(math.log2(4*row.UPA_side));B=row.B;phase=4*(B-1)
        expectedbits={'HAQSE_R3':84,'DFT_INDEX_R3':3*d,'POS_R3':36,'TYPE_I':B*d+phase,'TYPE_II':2*B*d+5*B+phase,'DOCOMO_NFLOS':B*d+2*(B-1)+math.ceil(math.log2(B))}
        if row.method=='IDEAL_SVD':assert pd.isna(row.feedback_bits);continue
        eb=expectedbits[row.method]
        if row.method in ['HAQSE_R3','DFT_INDEX_R3','POS_R3'] and row.branch=='UE':eb+=phase
        assert row.feedback_bits==eb
        if row.method not in ['HAQSE_R3','DFT_INDEX_R3','POS_R3']:continue
        msg=json.loads(row.space_message);refs=msg['reference_ap_ids'];k=np.array(msg['integer_codes'])
        actual=np.array([row.estimated_x_m,row.estimated_y_m,row.estimated_z_m])
        if row.method=='POS_R3':
            assert np.array_equal(np.ravel(msg['coordinate_bits']),bits)
            assert (row.coordinate_bits_x,row.coordinate_bits_y,row.coordinate_bits_z)==(13,14,9)
            decoded=lo+(np.ravel(k)+.5)*span/2.**bits
            raw=localize(refs,np.array(json.loads(row.frequency_unquantized)))
            savedraw=np.ravel(json.loads(row.position_before_coordinate_quantization))
            assert np.max(abs(raw-savedraw))<1e-9
            rawk=np.floor((savedraw-lo)/span*2.**bits)
            assert np.array_equal(np.clip(rawk,0,2.**bits-1),np.ravel(k))
            assert bool(row.quantizer_overflow)==bool(np.any((rawk<0)|(rawk>=2.**bits)))
            poscount+=1
        else:
            if row.method=='HAQSE_R3':f=-.5+k/(2**int(msg['q_frequency'])-1)
            else:f=-((k/(4*row.UPA_side)+.5)%1-.5)
            decoded=localize(refs,f)
        err=float(np.max(abs(decoded-actual)));assert err<1e-9;maxerr=max(maxerr,err)
        true=np.array([row.true_x_m,row.true_y_m,row.true_z_m])
        assert abs(np.linalg.norm(decoded-true)-row.position_error_m)<1e-9;counts+=1
    for key,g in t[t.method.eq('POS_R3')].groupby(['curve','x_value','B','antenna_count','observation_SNR_dB','Rician_K_dB','sample_id']):
        assert len(g)==2 and g.space_message.nunique()==1
    audit=dict(status='passed',array='UPA',streams=1,records=len(t),sample_ids=sorted(ids),
        geometry_messages_independently_replayed=counts,POS_coordinate_messages_replayed=poscount,
        maximum_position_replay_error_m=maxerr,feedback_bits_checked=True,CPU_UE_POS_messages_equal=True,
        POS_raw_position_recomputed_from_continuous_frequency=True,POS_coordinate_bits=[13,14,9],
        algorithm_scope='UPA and continuous-POS fixes only; not baseline-equivalence or performance validation')
    (out/'independent_message_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'source_and_input_SHA256.json').write_text(json.dumps({'text_normalization':'CRLF converted to LF before hashing','files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    if name.endswith('verify_final'):(out/'fix_unit_audit.json').write_bytes(unit.read_bytes())
    txt=f'''# UPA单流修复流程验证

本目录为UPA单极化单流小样本验证，只有{len(t)}条记录，样本位置{sorted(ids)}。不是400位置正式实验，不作性能排名。

覆盖8×8、16×16、32×32和多个协作AP数量；带宽按400 MHz换算。POS由连续HAQSE频率定位后仅量化坐标，公开分配13/14/9 bit。

- [原始记录](single_stream_trials.csv)
- [分组均值](single_stream_summary.csv)
- [运行配置](experiment_contract.json)
- [运行检查](audit.json)
- [独立整数消息及反馈审计](independent_message_audit.json)
- [源码与输入校验](source_and_input_SHA256.json)
- [实现与验证说明](../../docs/UPA与位置反馈修复说明.md)

独立重放{counts}条几何空间消息，其中POS有{poscount}条。CPU与UE使用相同POS消息；量化前位置由连续频率重新定位后核对。所有有限反馈记录按对应UPA尺寸重新核算bit。
'''
    if name.endswith('smoke2'):txt+='\nCPU/与UE/各保存7组PNG/FIG，均为绘图流程检查。\n'
    (out/'README.md').write_text(txt,encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))
# Previously archived single-stream data and all frozen dependencies must be untouched.
changed=subprocess.check_output(['git','diff','--name-only','-z'],cwd=ROOT).decode('utf-8').split('\0')
assert not any(p.startswith('8.单流/6.位置反馈方案/') or p.startswith('8.单流/results/single_stream_full/') for p in changed if p)
print('Frozen dependencies and historical results unchanged')

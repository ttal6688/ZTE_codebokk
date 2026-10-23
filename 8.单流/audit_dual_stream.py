"""Independent reconstruction of shared-beam two-stream precoders and metrics."""
from pathlib import Path
import argparse,json,math,functools
import numpy as np
import pandas as pd
import audit_single_stream_protocol as base
ROOT=Path(__file__).resolve().parent
SIM=json.loads((base.PUBLIC/'simulation_settings.json').read_text(encoding='utf-8'))
POS=pd.read_csv(base.PUBLIC/SIM['UE_positions_file']).set_index('sample_id')
ZETA=pd.read_csv(base.PUBLIC/SIM['scatter_coefficients_file'])

def second_stream(E,c1,rho,quantized):
    B=len(c1);scale=np.sqrt(2*B);g1=E@c1/scale;u=g1/max(np.linalg.norm(g1),np.finfo(float).tiny)
    residual=E-np.outer(u,u.conj()@E);R=residual@residual.conj().T;eig,U=np.linalg.eigh((R+R.conj().T)/2)
    ramp=c1*np.exp(2j*np.pi*np.arange(B)/B)
    a=np.exp(1j*np.angle(residual.conj().T@U[:,-1])) if eig[-1]>1e-24*max(1,np.linalg.norm(E)**2) else ramp
    def objective(g2):
        g2=np.asarray(g2);g2=g2[:,None] if g2.ndim==1 else g2
        p1=np.sum(abs(g1)**2);p2=np.sum(abs(g2)**2,axis=0);cross=abs(g1.conj()@g2)**2
        det=1+rho*(p1+p2)+rho**2*np.maximum(0,p1*p2-cross)
        return 2*np.log2(det)-np.log2(1+rho*p1)-np.log2(1+rho*p2)
    best=-np.inf;c2=None
    for seed in [a,ramp]:
        candidate=seed*np.conj(seed[0])
        if quantized:candidate=np.exp(2j*np.pi*(base.rnd(np.angle(candidate)*16/(2*np.pi))%16)/16)
        score=float(objective(E@candidate/scale)[0])
        if score>best:best=score;c2=candidate.copy()
    L=16 if quantized else 64;alphabet=np.exp(2j*np.pi*np.arange(L)/L);gold=(np.sqrt(5)-1)/2
    for _ in range(3):
        total=E@c2/scale
        for b in range(1,B):
            rest=total-E[:,b]*c2[b]/scale;candidates=np.r_[c2[b],alphabet]
            values=objective(rest[:,None]+np.outer(E[:,b],candidates)/scale);k=int(np.argmax(values));value=values[k];chosen=candidates[k]
            if not quantized:
                center=np.angle(chosen);left=center-2*np.pi/L;right=center+2*np.pi/L
                x1=right-gold*(right-left);x2=left+gold*(right-left)
                f1=objective(rest+E[:,b]*np.exp(1j*x1)/scale)[0];f2=objective(rest+E[:,b]*np.exp(1j*x2)/scale)[0]
                for _ in range(24):
                    if f1>f2:
                        right=x2;x2=x1;f2=f1;x1=right-gold*(right-left);f1=objective(rest+E[:,b]*np.exp(1j*x1)/scale)[0]
                    else:
                        left=x1;x1=x2;f1=f2;x2=left+gold*(right-left);f2=objective(rest+E[:,b]*np.exp(1j*x2)/scale)[0]
                if f1>value:value=f1;chosen=np.exp(1j*x1)
                if f2>value:value=f2;chosen=np.exp(1j*x2)
            if value>objective(total)[0]+1e-10:c2[b]=chosen;total=rest+E[:,b]*chosen/scale
    return c2

@functools.lru_cache(maxsize=128)
def truth(sid,channel,side,B,KdB=10):
    p=POS.loc[sid,['x_m','y_m','UPA_z_m']].to_numpy(float);N=side**2
    ny,nz=np.meshgrid(np.arange(side),np.arange(side),indexing='ij');ny=ny.ravel(order='F');nz=nz.ravel(order='F')
    local=np.array([np.zeros(N),(ny-(side-1)/2)*base.D,(nz-(side-1)/2)*base.D])
    offsets=np.array([np.arange(-1.5,2)*base.D,np.zeros(4),np.zeros(4)])
    coeff=ZETA[ZETA.sample_id.eq(sid)].sort_values('scatterer_id');z=coeff.real.to_numpy()+1j*coeff.imag.to_numpy()
    scatter=np.array(SIM['scatterer_positions_m']);blocks=[]
    for apid in base.ACTIVE[:B]:
        ap=base.APS[apid-1];locations=np.array(ap['position_m']).reshape(3,1)+np.array(ap['R_local_to_global'])@local
        los=np.zeros((4,N),complex);nlos=los.copy()
        for u in range(4):
            user=p+offsets[:,u];dist=np.linalg.norm(locations-user[:,None],axis=0);los[u]=np.exp(-1j*base.K*dist)/dist
            if channel=='MIX':
                for ell,point in enumerate(scatter):
                    length=np.linalg.norm(locations-point[:,None],axis=0)+np.linalg.norm(point-user)
                    nlos[u]+=z[ell]*np.exp(-1j*base.K*length)/length
        if channel=='LOS':blocks.append(los)
        else:
            power=10**(KdB/10);nlos*=np.linalg.norm(los)/np.linalg.norm(nlos);blocks.append(np.sqrt(power/(power+1))*los+np.sqrt(1/(power+1))*nlos)
    return np.concatenate(blocks,axis=1)

def audit(out):
    contract=json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'));rho=contract['rho_data']
    source=out/'dual_stream_trials.csv';source=source if source.exists() else source.with_suffix('.csv.gz')
    t=pd.read_csv(source,dtype={'feedback_wire':'string'});ids=np.atleast_1d(contract['sample_ids']).tolist()
    models=contract['channel_models'];models=[models] if isinstance(models,str) else models
    assert len(t)==22*len(models)*len(ids) and set(t.sample_id)==set(ids) and set(t.channel_model)==set(models)
    counts=t.groupby(['branch','channel_model','method','stream_count']).sample_id.agg(['count','nunique'])
    assert counts['count'].eq(len(ids)).all() and counts['nunique'].eq(len(ids)).all()
    maxmetric=0.;maxtrue=0.;maxcpusecond=0.;maxsignature=0.;maxdesign=0.;count=0;replay_rows=[]
    for row in t.itertuples():
        B=row.B;side=row.UPA_side;N=side**2;ns=row.stream_count;H=truth(row.sample_id,row.channel_model,side,B,contract['K_dB'])
        if row.method=='IDEAL_SVD':
            _,s,Vh=np.linalg.svd(H,full_matrices=False);W=Vh.conj().T[:,:ns]/np.sqrt(ns)
        else:
            msg=json.loads(row.feedback_message);mode=msg['mode'];wire=str(row.feedback_wire)
            d=2*int(math.log2(4*side))
            bits={'TYPE_I':B*d+4*(B-1),'TYPE_II':2*B*d+5*B+4*(B-1),'DOCOMO_NFLOS':B*d+2*(B-1)+math.ceil(math.log2(B)),
                  'HAQSE_R3':84,'DFT_INDEX_R3':3*d,'POS_R3':36}[row.method]
            if row.method in ['HAQSE_R3','DFT_INDEX_R3','POS_R3'] and row.branch=='UE':bits+=4*(B-1)
            expected=bits+(4*(B-1) if ns==2 and row.branch=='UE' else 0)
            assert len(wire)==row.feedback_bits==expected
            decoded=base.decode(wire[:bits],row.method,mode,B,side);F,p,ny,nz=base.spatial(row.method,decoded,B,side)
            if mode=='CPU_MODEL':c1=base.cpu_phase(p,F,B,ny,nz)
            elif mode=='DOCOMO':c1=np.exp(2j*np.pi*np.r_[0,decoded['beta_indices'].ravel()]/4)*np.exp(2j*np.pi*np.arange(B)*decoded['ap_dft_index'][0,0]/B)
            else:c1=np.exp(2j*np.pi*np.r_[0,decoded['phase_indices'].ravel()]/16)
            C=np.asarray(json.loads(row.C_real))+1j*np.asarray(json.loads(row.C_imag));C=C.reshape((B,ns))
            assert np.max(abs(C[:,0]-c1/np.sqrt(B*ns)))<1e-8
            if ns==2:
                if row.branch=='UE':
                    extra=np.array([int(wire[bits+4*b:bits+4*(b+1)],2) for b in range(B-1)])
                    c2=np.exp(2j*np.pi*np.r_[0,extra]/16);assert np.max(abs(C[:,1]-c2/np.sqrt(2*B)))<1e-10
                else:
                    model=base.geometry_matrix(p,F,B,ny,nz);E=np.column_stack([model[:,b*N:(b+1)*N]@F[:,b] for b in range(B)])
                    c2=second_stream(E,c1,rho,False);err=float(np.max(abs(C[:,1]-c2/np.sqrt(2*B))));maxcpusecond=max(maxcpusecond,err)
                    def design_se(coeff):
                        G=E@np.column_stack([c1,coeff])/np.sqrt(2*B);A=np.eye(2)+rho*G.conj().T@G
                        return float(np.sum(np.log2(1/np.diag(np.linalg.inv(A)).real)))
                    gap=abs(design_se(c2)-design_se(C[:,1]*np.sqrt(2*B)));maxdesign=max(maxdesign,gap)
                    if err>=1e-3:replay_rows.append(row.Index)
                history=np.array(json.loads(row.design_objective_history));assert np.all(np.diff(history)>=-1e-9)
            W=np.concatenate([F[:,b,None]*C[b,None,:] for b in range(B)],axis=0)
            assert np.max(abs(np.sum(abs(W.reshape((B,N,ns)))**2,axis=(1,2))-1/B))<1e-10
            E=np.column_stack([H[:,b*N:(b+1)*N]@F[:,b] for b in range(B)])
            saved=np.array(json.loads(row.effective_true_channel_real))+1j*np.array(json.loads(row.effective_true_channel_imag))
            err=float(np.max(abs(E-saved)));assert err<1e-8;maxtrue=max(maxtrue,err)
            count+=1
        assert abs(np.linalg.norm(W)**2-1)<1e-10
        if row.method!='IDEAL_SVD':
            n=np.arange(1,len(W)+1);z=np.vstack([(np.sin(.013*j*n)+1j*np.cos(.017*j*n))@W for j in [1,2,3]])
            recorded=np.asarray(json.loads(row.precoder_signature));err=float(np.max(abs(np.c_[z.real,z.imag]-recorded)))
            assert err<1e-7;maxsignature=max(maxsignature,err)
        G=H@W;A=np.eye(ns)+rho*G.conj().T@G;sinr=np.maximum(0,1/np.diag(np.linalg.inv(A)).real-1)
        SE=np.sum(np.log2(1+sinr));joint=np.linalg.slogdet(A)[1]/np.log(2);sv=np.linalg.svd(G,compute_uv=False)
        ratio=sv[1]**2/sv[0]**2 if ns==2 else 0
        err=max(abs(SE-row.spectral_efficiency),abs(joint-row.joint_SE));assert err<1e-7;maxmetric=max(maxmetric,err)
        assert abs(row.throughput_Mbps-400*SE)<1e-4 and abs(row.second_mode_ratio-ratio)<1e-8
        assert SE<=joint+1e-8
    pairsource=out/'single_dual_pairs.csv';pair=pd.read_csv(pairsource if pairsource.exists() else pairsource.with_suffix('.csv.gz'));keys=['branch','channel_model','method','sample_id']
    a=t[t.stream_count.eq(1)];b=t[t.stream_count.eq(2)];m=a.merge(b,on=keys,suffixes=('_single','_dual'),validate='one_to_one').merge(pair,on=keys,validate='one_to_one')
    assert len(m)==11*len(models)*len(ids) and np.allclose(m.delta_Mbps,m.throughput_Mbps_dual-m.throughput_Mbps_single)
    implement=m[~m.method.eq('IDEAL_SVD')]
    assert (implement[implement.branch.eq('CPU')].extra_bits==0).all() and (implement[implement.branch.eq('UE')].extra_bits==4*(contract['B']-1)).all()
    summary=pd.read_csv(out/'dual_stream_summary.csv');keys=['branch','channel_model','method','stream_count','csi']
    for field in [x[5:] for x in summary if x.startswith('mean_')]:
        calc=t.groupby(keys,dropna=False)[field].mean().reset_index(name='independent');check=summary.merge(calc,on=keys,validate='one_to_one')
        assert np.allclose(check['mean_'+field],check.independent,equal_nan=True,rtol=1e-8,atol=1e-8)
    # Near optimizer branch boundaries, independent BLAS/eigensolvers can choose
    # different continuous iterates. Never loosen the coefficient check silently:
    # publish every disagreement and require exact native decoder replay for it.
    t.loc[replay_rows].to_csv(out/'CPU_continuous_replay_required.csv',index=False)
    result=dict(status='passed_metrics_pending_native_replay' if replay_rows else 'passed',positions=len(ids),records=len(t),implementable_records_independently_reconstructed=count,
       maximum_true_effective_channel_error=maxtrue,maximum_metric_SE_error=maxmetric,
       maximum_CPU_continuous_coefficient_numerical_error=maxcpusecond,
       maximum_precoder_signature_error=maxsignature,
       continuous_optimizer_native_replay_required=len(replay_rows),maximum_CPU_design_SE_cross_implementation_difference=maxdesign,
       UE_extra_bits=4*(contract['B']-1),CPU_extra_bits=0,shared_F=True,all_summary_means_recomputed=True,truth_regenerated_from_public_sample_bank=True)
    (out/'independent_dual_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('results');args=parser.parse_args();audit(ROOT/args.results)

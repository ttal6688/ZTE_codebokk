"""Independent Python payload decoder and precoder reconstruction (no MATLAB calls)."""
from pathlib import Path
import argparse, hashlib, json, math, subprocess
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'6.位置反馈方案/shared'
GEOM=json.loads((PUBLIC/'network_geometry.json').read_text(encoding='utf-8'))['models']['UPA32x32']
APS=GEOM['APs'];ACTIVE=np.ravel(GEOM['active_order']).astype(int)
REFS=np.ravel(GEOM['reference_AP_sets']['3']).astype(int)
LO=np.array([19.,19.,-1.]);SPAN=np.array([12.,12.,7.]);BITS=np.array([13,14,9])
LAMBDA=3e8/7e9;K=2*np.pi/LAMBDA;D=LAMBDA/2

def rnd(x):
    return np.sign(x)*np.floor(np.abs(x)+.5)

def localize(f):
    A=np.zeros((3,3));rhs=np.zeros(3)
    for ref,fr in zip(REFS,f.T):
        yz=-2*fr;q=np.r_[-np.sqrt(max(0,1-yz@yz)),yz];q/=np.linalg.norm(q)
        ap=APS[ref-1];g=-np.array(ap['R_local_to_global'])@q
        P=np.eye(3)-np.outer(g,g);A+=P;rhs+=P@np.ravel(ap['position_m'])
    return np.linalg.solve(A,rhs)

def decode(wire,method,mode,B,side):
    assert set(wire)<=set('01')
    cursor=0;M=4*side;d=2*int(math.log2(M));space={}
    def take(name,width,shape):
        nonlocal cursor
        widths=np.repeat(width,math.prod(shape)) if np.isscalar(width) else np.ravel(width)
        value=[]
        for width in widths:
            width=int(width);part=wire[cursor:cursor+width];assert len(part)==width
            value.append(int(part,2));cursor+=width
        space[name]=np.reshape(value,shape,order='F')
    if method in ['TYPE_I','DOCOMO_NFLOS']:take('beam_indices',d,(1,B))
    elif method=='TYPE_II':
        take('beam_indices',d,(2,B));take('amp_indices',3,(1,B));take('internal_phase_indices',2,(1,B))
    elif method=='POS_R3':take('integer_codes',BITS,(3,1))
    elif method=='HAQSE_R3':take('integer_codes',14,(2,3))
    elif method=='DFT_INDEX_R3':take('integer_codes',int(math.log2(M)),(2,3))
    else:raise AssertionError(method)
    if mode=='UE_PHASE':take('phase_indices',4,(B-1,1))
    elif mode=='DOCOMO':take('beta_indices',2,(B-1,1));take('ap_dft_index',math.ceil(math.log2(B)),(1,1))
    else:assert mode=='CPU_MODEL'
    assert cursor==len(wire)
    return space

def spatial(method,s,B,side):
    N=side**2;M=4*side;active=ACTIVE[:B]
    ny,nz=np.meshgrid(np.arange(side),np.arange(side),indexing='ij');ny=ny.ravel(order='F');nz=nz.ravel(order='F')
    def beams(index):
        index=np.ravel(index);return np.exp(2j*np.pi*(ny[:,None]*(index%M)+nz[:,None]*(index//M))/M)/np.sqrt(N)
    p=None
    if method in ['TYPE_I','DOCOMO_NFLOS']:F=beams(s['beam_indices'])
    elif method=='TYPE_II':
        F=np.zeros((N,B),complex)
        for b in range(B):
            idx=s['beam_indices'][:,b];pair=beams(idx)
            assert idx[0]!=idx[1] and (idx[0]%M)%4==(idx[1]%M)%4 and (idx[0]//M)%4==(idx[1]//M)%4
            assert abs(np.vdot(pair[:,0],pair[:,1]))<1e-10
            coeff=s['amp_indices'][0,b]/7*np.exp(2j*np.pi*s['internal_phase_indices'][0,b]/4)
            f=pair@np.array([1,coeff]);F[:,b]=f/np.linalg.norm(f)
    else:
        codes=s['integer_codes']
        if method=='POS_R3':p=LO+(codes.ravel()+.5)*SPAN/2.**BITS
        else:
            freq=-.5+codes/(2**14-1) if method=='HAQSE_R3' else -((codes/M+.5)%1-.5)
            p=localize(freq)
        idx=[]
        for apid in active:
            ap=APS[apid-1];delta=np.ravel(ap['position_m'])-p
            q=np.array(ap['R_local_to_global']).T@delta/np.linalg.norm(delta)
            m=rnd(M*q[1:]/2).astype(int)%M
            if method!='POS_R3' and apid in REFS:
                j=int(np.flatnonzero(REFS==apid)[0])
                m=codes[:,j] if method=='DFT_INDEX_R3' else rnd(-freq[:,j]*M).astype(int)%M
            idx.append(m[0]+M*m[1])
        F=beams(idx)
    return F,p,ny,nz

def geometry_matrix(p,F,B,ny,nz):
    side=int(np.sqrt(F.shape[0]));local=np.array([np.zeros(len(ny)),(ny-(side-1)/2)*D,(nz-(side-1)/2)*D])
    offsets=np.array([np.arange(-1.5,2)*D,np.zeros(4),np.zeros(4)])
    blocks=[]
    for apid in ACTIVE[:B]:
        ap=APS[apid-1];delta=np.ravel(ap['position_m'])-p;r=np.linalg.norm(delta);q=delta/r
        ql=np.array(ap['R_local_to_global']).T@q
        blocks.append(np.exp(-1j*K*r)/r*np.exp(1j*K*offsets.T@q)[:,None]*np.exp(-1j*K*ql@local)[None,:])
    return np.concatenate(blocks,axis=1)

def cpu_phase(p,F,B,ny,nz):
    H=geometry_matrix(p,F,B,ny,nz);eig,U=np.linalg.eigh(H@H.conj().T)
    v=H.conj().T@U[:,-1]/np.sqrt(eig[-1]);a=np.array([np.vdot(F[:,b],v[b*len(ny):(b+1)*len(ny)]) for b in range(B)])
    return np.exp(1j*(np.angle(a)-np.angle(a[0])))

def signature(w):
    n=np.arange(1,len(w)+1);z=np.array([(np.sin(.013*j*n)+1j*np.cos(.017*j*n))@w for j in [1,2,3]])
    return np.c_[z.real,z.imag]

def audit(out):
    c=json.loads((out/'experiment_contract.json').read_text(encoding='utf-8'));c['sample_ids']=np.atleast_1d(c['sample_ids']).tolist()
    source=out/'single_stream_trials.csv';source=source if source.exists() else out/'single_stream_trials.csv.gz'
    t=pd.read_csv(source,dtype={'feedback_wire':'string'})
    assert len(t)==c.get('rows_per_case',19)*len(c['sample_ids'])*len(c['settings'])*len(c['channel_models'])
    assert set(t.sample_id)==set(c['sample_ids']) and set(t.channel_model)==set(c['channel_models'])
    assert t.array.eq('UPA').all() and (t.UPA_side**2==t.antenna_count).all()
    assert 'cpu_estimation_dimension' not in t.columns
    maxsig=0.;maxpos=0.;maxcoeff=0.;count=0
    for row in t.itertuples():
        assert np.isclose(row.throughput_Mbps,400*row.spectral_efficiency,rtol=1e-12)
        assert np.isclose(row.spectral_efficiency,np.log2(1+c['rho_data']*row.received_power),rtol=1e-12)
        assert row.received_power<=row.ideal_received_power*(1+1e-8)
        if row.method=='IDEAL_SVD':assert pd.isna(row.feedback_bits);continue
        mode='CPU_MODEL' if row.role=='CPU_METHOD' else ('DOCOMO' if row.method=='DOCOMO_NFLOS' else 'UE_PHASE')
        wire=str(row.feedback_wire);B=row.B;M=4*row.UPA_side;d=2*int(math.log2(M));s=decode(wire,row.method,mode,B,row.UPA_side)
        bit={'TYPE_I':B*d,'TYPE_II':2*B*d+5*B,'DOCOMO_NFLOS':B*d+2*(B-1)+math.ceil(math.log2(B)),
             'POS_R3':36,'HAQSE_R3':84,'DFT_INDEX_R3':3*d}[row.method]+(4*(B-1) if mode=='UE_PHASE' else 0)
        assert row.feedback_bits==bit==len(wire)
        msg=json.loads(row.feedback_message);assert set(msg)=={'protocol','method','mode','space','phase_indices'}
        assert msg['protocol']=='SSTR_V2' and msg['method']==row.method and msg['mode']==mode
        for key,value in s.items():
            saved=msg['phase_indices'] if key=='phase_indices' else msg['space'][key]
            assert np.array_equal(np.ravel(saved,order='F'),value.ravel(order='F'))
        F,p,ny,nz=spatial(row.method,s,B,row.UPA_side)
        if mode=='CPU_MODEL':coeff=cpu_phase(p,F,B,ny,nz)
        elif mode=='DOCOMO':
            assert s['ap_dft_index'][0,0]<B
            coeff=np.exp(2j*np.pi*np.r_[0,s['beta_indices'].ravel()]/4)*np.exp(2j*np.pi*np.arange(B)*s['ap_dft_index'][0,0]/B)
        else:coeff=np.exp(2j*np.pi*np.r_[0,s['phase_indices'].ravel()]/16)
        recorded=np.array(json.loads(row.AP_coefficients));savedcoeff=recorded[:,0]+1j*recorded[:,1]
        e=float(np.max(abs(coeff-savedcoeff)));assert e<1e-7;maxcoeff=max(maxcoeff,e)
        w=(F*coeff[None,:]).ravel(order='F')/np.sqrt(B)
        assert abs(np.linalg.norm(w)**2-1)<1e-10
        assert np.max(abs(np.sum(abs(w.reshape((-1,B),order='F'))**2,axis=0)-1/B))<1e-10
        e=float(np.max(abs(signature(w)-np.array(json.loads(row.precoder_signature)))));assert e<1e-7;maxsig=max(maxsig,e)
        if p is not None:
            savedp=np.array([row.estimated_x_m,row.estimated_y_m,row.estimated_z_m]);e=float(np.max(abs(p-savedp)))
            assert e<1e-9;maxpos=max(maxpos,e)
            true=np.array([row.true_x_m,row.true_y_m,row.true_z_m]);assert abs(np.linalg.norm(p-true)-row.position_error_m)<1e-9
            if row.method=='POS_R3':
                raw=localize(np.array(json.loads(row.frequency_unquantized)));recordedraw=np.ravel(json.loads(row.position_before_coordinate_quantization))
                assert np.max(abs(raw-recordedraw))<1e-9
                codes=np.floor((raw-LO)/SPAN*2.**BITS);overflow=bool(np.any((codes<0)|(codes>=2.**BITS)))
                assert np.array_equal(np.clip(codes,0,2.**BITS-1),s['integer_codes'].ravel())
                assert overflow==bool(row.quantizer_overflow)
                assert abs(np.linalg.norm(raw-true)-row.raw_position_error_m)<1e-9
                assert (row.coordinate_bits_x,row.coordinate_bits_y,row.coordinate_bits_z)==(13,14,9)
            assert row.reference_AP_count==3 and row.reference_observation_complex_count==4*row.antenna_count*3
            assert row.geometry_parameter_count==(3 if row.method=='POS_R3' else 6)
        if mode=='CPU_MODEL':assert row.full_observation_complex_count==0 and (row.model_rows,row.model_columns)==(4,B*row.antenna_count)
        else:assert row.full_observation_complex_count==4*B*row.antenna_count and row.model_rows==row.model_columns==0
        count+=1
    keys=['channel_model','curve','x_value','B','antenna_count','observation_SNR_dB','Rician_K_dB','sample_id','method']
    ue=t[t.branch.eq('UE') & ~t.csi.eq('IDEAL')];a=ue[ue.csi.eq('OBSERVED')];b=ue[ue.csi.eq('PERFECT')]
    paired=a.merge(b,on=keys,suffixes=('_observed','_perfect'),validate='one_to_one')
    assert (len(b)==0 or len(paired)==len(a)==len(b)) and (paired.feedback_bits_observed==paired.feedback_bits_perfect).all()
    csv=pd.read_csv(out/'paired_CSI.csv');m=paired.merge(csv,on=keys,validate='one_to_one');assert len(m)==len(b)
    assert np.allclose(m.delta_Mbps,m.throughput_Mbps_perfect-m.throughput_Mbps_observed)
    # CPU/UE must use exactly the same decoded spatial payload for observed CSI.
    geo=t[t.method.isin(['HAQSE_R3','DFT_INDEX_R3','POS_R3']) & t.csi.eq('OBSERVED')]
    for _,g in geo.groupby(keys):assert len(g)==2 and g.space_message.nunique()==1
    # Recompute every summary statistic instead of trusting the runner's group means.
    summary=pd.read_csv(out/'single_stream_summary.csv');groupkeys=['branch','role','csi','channel_model','curve','x_value','method','feedback_scope','B','antenna_count','observation_SNR_dB','Rician_K_dB']
    grouped=t.groupby(groupkeys,dropna=False)
    for field in [x[5:] for x in summary.columns if x.startswith('mean_')]:
        calc=grouped[field].mean().reset_index(name='independent');check=summary.merge(calc,on=groupkeys,validate='one_to_one')
        assert len(check)==len(summary) and np.allclose(check['mean_'+field],check.independent,equal_nan=True,rtol=1e-9,atol=1e-10),field
    result=dict(status='passed',records=len(t),sample_ids=sorted(t.sample_id.unique().tolist()),
       channel_models=sorted(t.channel_model.unique().tolist()),independently_decoded_full_payloads=count,
       maximum_precoder_signature_error=maxsig,maximum_CPU_phase_error=maxcoeff,maximum_position_error_m=maxpos,
       all_feedback_bit_lengths_checked=True,CPU_no_measured_CSI=True,all_summary_means_recomputed=True,
       paired_CSI_records=len(paired),paired_feedback_bits_identical=True,
       negative_paired_deltas=int((csv.delta_Mbps<0).sum()),full400=bool(len(c['sample_ids'])==400))
    (out/'independent_protocol_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=[]
    files=list(ROOT.glob('*.m'))+list(ROOT.glob('*.py'))+list((ROOT/'+sstr').glob('*.m'))
    files+=list((ROOT/'6.位置反馈方案').glob('+*/*.m'))+list((ROOT/'6.位置反馈方案/lib').glob('*.m'))
    files+=list(PUBLIC.glob('*.json'))+list(PUBLIC.glob('*.csv'))
    for p in sorted(set(files)):
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()))
    (out/'source_and_input_SHA256.json').write_text(json.dumps(dict(text_normalization='CRLF to LF',files=manifest),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return t,csv

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('results',nargs='+');args=parser.parse_args()
    for name in args.results:audit(ROOT/name)
    changed=subprocess.check_output(['git','diff','4622561','--name-only','-z'],cwd=ROOT).decode().split('\0')
    assert not any(p.startswith('8.单流/6.位置反馈方案/') or p.startswith('8.单流/results/single_stream_UPA_POS_V1_') or p.startswith('8.单流/results/single_stream_full/') for p in changed)
    print('Frozen dependencies and historical results unchanged.')

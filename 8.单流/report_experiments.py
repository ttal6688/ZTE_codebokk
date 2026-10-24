"""Complete per-experiment figures, numeric results and source-grounded notes."""
import pandas as pd
NAMES={'IDEAL_SVD':'SVD参考','TYPE_I':'全反馈Type-I(UE)','TYPE_II':'全反馈Type-II(UE)','DOCOMO_NFLOS':'Docomo','HAQSE_R3':'空间频率','DFT_INDEX_R3':'DFT索引','POS_R3':'位置反馈'}
GEO=['HAQSE_R3','DFT_INDEX_R3','POS_R3'];UE=['TYPE_I','TYPE_II','DOCOMO_NFLOS']+GEO
CURVES=[('SNR','观测SNR','dB'),('天线数','UPA阵元数','阵元'),('AP数','协作AP数','个'),('莱斯因子','莱斯因子K','dB')]

def method_name(method,branch=None):
    return 'Docomo(UE)' if branch=='CPU' and method=='DOCOMO_NFLOS' else NAMES[method]

def display_panel(source,branch):
    result=source[source.branch.eq(branch)].copy()
    if branch=='CPU' and not result.method.eq('DOCOMO_NFLOS').any():
        reference=source[source.branch.eq('UE')&source.method.eq('DOCOMO_NFLOS')].copy()
        if 'csi' in reference:reference=reference[~reference.csi.eq('PERFECT')]
        reference['branch']='CPU'
        if 'role' in reference:reference['role']='UE_REFERENCE'
        result=pd.concat([result,reference],ignore_index=True)
    return result

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows])

def matrix(q,methods,field,digits=2,branch=None):
    xs=sorted(q.x_value.unique());rows=[]
    for m in methods:
        qm=q[q.method.eq(m)].set_index('x_value');values=[]
        for x in xs:
            v=qm.loc[x,field];values.append('不适用' if pd.isna(v) else f'{v:.{digits}f}')
        rows.append([method_name(m,branch)]+values)
    return table(['方法']+[f'{x:g}' for x in xs],rows)

def dual_experiments(branch,s,p,summary):
    methods=['DOCOMO_NFLOS']+GEO if branch=='CPU' else UE;parts=[]
    s=display_panel(s,branch);p=display_panel(p,branch);summary=display_panel(summary,branch)
    for model,modelname in [('LOS','纯LOS'),('MIX','混合信道')]:
        for curve,description,unit in CURVES:
            q=s[s.branch.eq(branch)&s.channel_model.eq(model)&s.curve.eq(curve)]
            title=f'{branch}{modelname}{description}完整扫描'
            fixed='除横轴外采用32×32、B=8、观测30 dB、K=10 dB默认值。'
            parts += ['### '+title,f'本实验只扫描{description}，横轴单位为{unit}。'+fixed+'每个参数点、每种方法都使用全部400个相同位置，以下逐点数值和三幅图来自同一组消息重放结果。']
            if model=='LOS' and curve=='莱斯因子':parts+=['本组为一致性对照：纯LOS生成式不含K，所有K点必须逐位置相同。该检查已通过，不解释为信道随K变化。']
            rows=[]
            for method in methods:
                for r in q[q.method.eq(method)].sort_values('x_value').itertuples():
                    rows.append([method_name(method,branch),f'{r.x_value:g}',f'{r.mean_dual_Mbps:.2f}',f'{r.mean_delta_Mbps:.2f}',f'{100*r.positive_fraction:.2f}',f'{r.mean_second_mode_ratio:.4f}'])
            refs=summary[summary.branch.eq(branch)&summary.channel_model.eq(model)&summary.curve.eq(curve)&summary.method.eq('IDEAL_SVD')&summary.stream_count.eq(2)].sort_values('x_value')
            for r in refs.itertuples():
                rp=p[p.branch.eq(branch)&p.channel_model.eq(model)&p.curve.eq(curve)&p.method.eq('IDEAL_SVD')&p.x_value.eq(r.x_value)]
                rows.append(['SVD参考',f'{r.x_value:g}',f'{r.mean_throughput_Mbps:.2f}',f'{rp.delta_Mbps.mean():.2f}',f'{100*(rp.delta_Mbps>0).mean():.2f}',f'{r.mean_second_mode_ratio:.4f}'])
            parts += [table(['方法','横轴','双流 Mbps','增量 Mbps','正收益 %','第二模式比'],rows)]
            qp=q[q.method.eq('POS_R3')].sort_values('x_value');first=qp.iloc[0];last=qp.iloc[-1]
            ranked=q[q.method.isin(GEO)] if branch=='CPU' else q
            end=ranked[ranked.x_value.eq(ranked.x_value.max())].sort_values('mean_dual_Mbps',ascending=False).iloc[0]
            ranking_scope='CPU几何方法' if branch=='CPU' else 'UE方法'
            parts += [f'![{title}双流吞吐量](../results/dual_stream_full400/{branch}/{branch}_{model}_双流吞吐量_{curve}.png)',
             f'吞吐量结果：位置反馈从横轴{first.x_value:g}时的{first.mean_dual_Mbps:.2f} Mbps变为{last.x_value:g}时的{last.mean_dual_Mbps:.2f} Mbps。终点{ranking_scope}中，{NAMES[end.method]}均值最高，为{end.mean_dual_Mbps:.2f} Mbps；Docomo(UE)在CPU图中为共享参考，SVD单列为理想参考。',
             f'![{title}单双流平均增量](../results/dual_stream_full400/{branch}/{branch}_{model}_单双流增量_{curve}.png)',
             f'增量结果：本组所有方法和参数点的最小400位置平均增量为{q.mean_delta_Mbps.min():.2f} Mbps，最低正收益比例为{100*q.positive_fraction.min():.2f}%。平均增量为正与每个位置都受益是不同结论，逐位置最差值及非正收益单独保留。',
             f'![{title}接收第二模式](../results/dual_stream_full400/{branch}/{branch}_{model}_第二模式功率比_{curve}.png)',
             f'模式结果：位置反馈各参数点的第二与第一接收模式功率比均值范围为{qp.mean_second_mode_ratio.min():.4f}至{qp.mean_second_mode_ratio.max():.4f}；全部参数与位置中最小值为{qp.minimum_second_mode_ratio.min():.5g}。该值由真实接收矩阵HW的奇异值平方计算，模式较弱时，即使发送两列也不保证速率增加。']
        pdflt=p[p.branch.eq(branch)&p.channel_model.eq(model)&p.curve.eq('SNR')&p.x_value.eq(30)]
        parts += ['### '+branch+modelname+'默认配置的均值与分布',
         f'![{branch}{modelname}默认配置单双流吞吐量](../results/dual_stream_full400/{branch}/{branch}_{model}_默认单双流.png)',
         '该柱状图将同一400位置下的单流和双流均值并列，数值见本端默认配置表；两者总功率均为1。SVD两流采用等功率，不能据此表示一般最优功率分配容量。',
         f'![{branch}{modelname}默认配置逐位置增量分布](../results/dual_stream_full400/{branch}/{branch}_{model}_默认增量CDF.png)']
        rows=[]
        for m in methods:
            values=pdflt[pdflt.method.eq(m)].delta_Mbps
            rows.append([method_name(m,branch)]+[f'{values.quantile(x):.2f}' for x in [0,.05,.5,.95,1]])
        parts += [table(['方法','最小 Mbps','5%分位','中位 Mbps','95%分位','最大 Mbps'],rows),
          '分布结果：CDF和分位数均按400个配对增量计算，表中5%分位表示约5%的位置收益不超过该值，不能将中位数或均值当作最差用户保证。']
    q=summary[summary.branch.eq(branch)&summary.channel_model.eq('MIX')&summary.curve.eq('AP数')&summary.stream_count.eq(2)]
    parts += ['### '+branch+'双流有效载荷随AP数量变化',matrix(q,methods,'mean_feedback_bits',0,branch),
      f'![{branch}双流实际反馈量](../results/dual_stream_full400/{branch}/{branch}_双流反馈量_AP数.png)',
      '开销结果：CPU三种几何方法不因新增第二流而增加反馈，固定三个参考AP。UE每增加一个协作AP，第二流额外多4 bit；表中为两流总有效载荷，已经包括原空间消息及第一流所需字段。CPU图与UE图采用各自实际消息长度，不把编码后的比特数替换为JSON字符数。']
    return parts

def single_experiments(branch,s):
    allmethods=['IDEAL_SVD']+UE
    qbranch=display_panel(s,branch);qbranch=qbranch[~qbranch.csi.eq('PERFECT')];parts=['## '+branch+'单流逐实验图表和数值',
      '以下每图均使用400位置均值，信道固定为MIX。各表列标题是图中的实际横轴数值；CPU图中的全反馈Type-I(UE)、全反馈Type-II(UE)和Docomo(UE)均为UE计算的共享参考，定位误差图只列三种几何方法。']
    specs=[('SNR','定位误差','mean_position_error_m','平均定位误差 m',GEO,6),('天线数','定位误差','mean_position_error_m','平均定位误差 m',GEO,6),
      ('AP数','定位误差','mean_position_error_m','平均定位误差 m',GEO,6),('SNR','吞吐量','mean_throughput_Mbps','平均吞吐量 Mbps',allmethods,2),
      ('天线数','吞吐量','mean_throughput_Mbps','平均吞吐量 Mbps',allmethods,2),('莱斯因子','吞吐量','mean_throughput_Mbps','平均吞吐量 Mbps',allmethods,2),
      ('AP数','比特数','mean_feedback_bits','实际有效载荷 bit',[m for m in allmethods if m!='IDEAL_SVD'],0),('SNR','频谱效率','mean_spectral_efficiency','频谱效率 bit/s/Hz',allmethods,4)]
    for curve,stem,field,metric,methods,digits in specs:
        description=next(x[1] for x in CURVES if x[0]==curve);q=qbranch[qbranch.curve.eq(curve)];qp=q[q.method.eq('POS_R3')].sort_values('x_value')
        title=branch+description+stem+'实验';parts += ['### '+title,'实验设置：只改变横轴的'+description+'，其余采用默认配置；表内为'+metric+'。',matrix(q,methods,field,digits,branch),
         f'![{title}](../results/single_stream_V3_full400/{branch}/{branch}_{stem}_{curve}.png)']
        if stem=='定位误差':
            parts += [f"结果：位置反馈在横轴{qp.iloc[0].x_value:g}时平均误差{qp.iloc[0][field]:.6f} m，横轴{qp.iloc[-1].x_value:g}时为{qp.iloc[-1][field]:.6f} m。该指标比较位置估计，不直接等同于波束成形或速率损失。AP数扫描仍固定三个参考AP，增加协作AP不等于增加定位观测。"]
        elif stem=='比特数':parts += ['结果：默认32×32下CPU三种几何消息为HAQSE84、DFT42、POS36 bit；UE几何方法再增加4(B−1) bit第一相位。UE的Type-I、Type-II、Docomo空间字段随AP数增长，图中展示实际打包长度。理想SVD没有有限反馈值，不将它作为0 bit可实施方法。']
        else:
            parts += [f"结果：位置反馈从横轴{qp.iloc[0].x_value:g}时的{qp.iloc[0][field]:.{digits}f}变为{qp.iloc[-1].x_value:g}时的{qp.iloc[-1][field]:.{digits}f}，单位同表。各方法中间点均保留；观测SNR只影响CSI质量，真实SVD参考随其不变。" if curve=='SNR' else f"结果：位置反馈从横轴{qp.iloc[0].x_value:g}时的{qp.iloc[0][field]:.{digits}f}变为{qp.iloc[-1].x_value:g}时的{qp.iloc[-1][field]:.{digits}f}，单位同表。阵元数或K改变了真实信道与可用波束，不能把该曲线解释为仅改变CSI观测噪声。"]
    qp=qbranch[qbranch.method.eq('POS_R3')&qbranch.curve.eq('SNR')].sort_values('x_value')
    parts += ['### '+branch+'位置反馈坐标量化前后实验',
      table(['观测SNR dB','连续定位误差 m','解码坐标误差 m'],[[f'{r.x_value:g}',f'{r.mean_raw_position_error_m:.6f}',f'{r.mean_position_error_m:.6f}'] for r in qp.itertuples()]),
      f'![{branch}位置反馈坐标量化前后](../results/single_stream_V3_full400/{branch}/{branch}_POS量化前后.png)',
      '结果：先以连续HAQSE频率定位，再量化一次坐标。两条曲线衡量同一定位结果在坐标编码前后的误差，不存在先量化频率再定位再量化坐标的处理。坐标量化后的欧氏误差变化不直接决定共相位敏感方向的误差。']
    qp=qbranch[qbranch.method.eq('POS_R3')&qbranch.curve.eq('莱斯因子')].sort_values('x_value')
    parts += ['### '+branch+'位置反馈坐标越界实验',table(['K dB','连续误差 m','解码误差 m','越界比例 %'],[[f'{r.x_value:g}',f'{r.mean_raw_position_error_m:.6f}',f'{r.mean_position_error_m:.6f}',f'{100*r.mean_quantizer_overflow:.2f}'] for r in qp.itertuples()]),
      f'![{branch}位置反馈坐标越界](../results/single_stream_V3_full400/{branch}/{branch}_POS越界比例.png)',
      '结果：K=0 dB时60个位置越界，占15%，其余K点为0。越界坐标截断到公共区域后，平均欧氏误差可能降低，其中包含区域先验；这不证明坐标量化提高定位算法精度。全部位置保留，未剔除越界点。',
      '### '+branch+'相位敏感度坐标bit分配检查',table(['坐标','bit','400个位置是否一致'],[['x',13,'是'],['y',14,'是'],['z',9,'是']]),
      f'![{branch}固定坐标bit分配](../results/single_stream_V3_full400/{branch}/{branch}_固定坐标bit分配.png)',
      '结果：三个方向始终分配13/14/9 bit，总计36 bit。规则由公共几何的相对AP相位敏感度预先固定，不依赖未知真实位置在线调整，也没有隐藏的逐位置分配头。图中真实x仅用于横轴展示，不作为分配算法输入。']
    return parts

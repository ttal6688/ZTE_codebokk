"""Complete per-experiment figures, numeric results and source-grounded notes."""
import pandas as pd
NAMES={'IDEAL_SVD':'SVD参考','TYPE_I':'全反馈Type-I(UE)','TYPE_II':'全反馈Type-II(UE)','DOCOMO_NFLOS':'Docomo','HAQSE_R3':'空间频率','DFT_INDEX_R3':'DFT索引','POS_R3':'位置反馈'}
GEO=['HAQSE_R3','DFT_INDEX_R3','POS_R3'];UE=['TYPE_I','TYPE_II','DOCOMO_NFLOS']+GEO
CURVES=[('SNR','观测SNR','dB'),('天线数','UPA阵元数','阵元'),('AP数','协作AP数','个'),('莱斯因子','莱斯因子K','dB')]

def method_name(method,branch=None):
    return 'Docomo(UE)' if branch=='CPU' and method=='DOCOMO_NFLOS' else NAMES[method]

def display_panel(source,branch):
    result=source[source.branch.eq(branch)].copy()
    if branch=='CPU':
        for method in ['TYPE_I','TYPE_II','DOCOMO_NFLOS']:
            if result.method.eq(method).any():continue
            reference=source[source.branch.eq('UE')&source.method.eq(method)].copy()
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


REFERENCE_NOTE='CPU图中的全反馈Type-I(UE)、全反馈Type-II(UE)、Docomo(UE)复用同一配置下的UE结果，作为共享参考；不新增CPU算法或样本。定位误差只比较空间频率、DFT索引和位置反馈三种有位置输出的方法。'

def single_experiments(branch,s):
    chapter=2 if branch=='CPU' else 3
    qbranch=display_panel(s,branch);qbranch=qbranch[~qbranch.csi.eq('PERFECT')]
    parts=[f'## {chapter} {branch}端正式实验','以下均为MIX信道下400位置均值。除横轴外采用32×32阵元、8 AP、观测SNR 30 dB、K=10 dB。'+REFERENCE_NOTE]
    for group,specs in [(1,[('SNR','定位误差','mean_position_error_m',GEO,6),('天线数','定位误差','mean_position_error_m',GEO,6),('AP数','定位误差','mean_position_error_m',GEO,6)]),
                        (2,[('SNR','吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+UE,2),('天线数','吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+UE,2),('莱斯因子','吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+UE,2)]),
                        (3,[('AP数','比特数','mean_feedback_bits',UE,0)])]:
        parts += [f'### {chapter}.{group} '+{1:'定位误差组',2:'吞吐量组',3:'比特数与AP数目'}[group]]
        for curve,stem,field,methods,digits in specs:
            description=next(x[1] for x in CURVES if x[0]==curve)
            q=qbranch[qbranch.curve.eq(curve)];qp=q[q.method.eq('POS_R3')].sort_values('x_value')
            title=f'{branch}单流{stem}与{description}'
            unit='m' if group==1 else ('Mbps' if group==2 else 'bit')
            parts += ['**'+title+'**',f'纵轴为{stem}（{unit}），横轴为{description}；表内为400位置均值。',matrix(q,methods,field,digits,branch),
                      f'![{title}](../results/single_stream_V3_full400/{branch}/{branch}_{stem}_{curve}.png)']
            if group==1:
                note='AP数改变时仍固定三个定位参考AP，增加协作AP不等于增加定位观测。' if curve=='AP数' else '定位误差不直接等同于共相位误差或吞吐量损失。'
            elif group==2:
                note='横轴SNR仅改变CSI观测噪声，真实CSI直接SVD参考保持不变。' if curve=='SNR' else '阵元数或莱斯因子会改变真实信道和可用波束，结果限定于当前冻结部署。'
            else:
                note='CPU三种几何消息分别为84、42、36 bit，固定三个参考AP；UE方法另含第一流相位字段。Type-I、Type-II和Docomo的全AP码本字段随AP数增加。理想SVD不参加有限反馈bit比较。'
            parts += [f'结果：位置反馈从横轴{qp.iloc[0].x_value:g}时的{qp.iloc[0][field]:.{digits}f} {unit}变为{qp.iloc[-1].x_value:g}时的{qp.iloc[-1][field]:.{digits}f} {unit}。'+note]
    return parts

def dual_experiments(branch,summary,localization):
    chapter=2 if branch=='CPU' else 3
    summary=display_panel(summary,branch)
    parts=[f'## {chapter} {branch}端正式实验','纯LOS与MIX分别列出，不合并均值。所有曲线每点使用同一组400位置；除横轴外采用32×32阵元、8 AP、观测SNR 30 dB、K=10 dB。'+REFERENCE_NOTE,
           f'### {chapter}.1 定位误差组','定位是单双流共用的空间消息前端。以下定位误差从已保存的双流反馈比特串恢复坐标，再与冻结真实位置计算欧氏距离；第二流新增相位不改变定位，未把新增流数描述为定位精度提升。']
    for curve in ['SNR','天线数','AP数']:
        description=next(x[1] for x in CURVES if x[0]==curve)
        for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
            q=localization[localization.branch.eq(branch)&localization.channel_model.eq(model)&localization.curve.eq(curve)]
            title=f'{branch}双流{name}定位误差与{description}'
            qp=q[q.method.eq('POS_R3')].sort_values('x_value')
            note='固定三个定位参考AP，因此协作AP数变化不代表定位参考数增加。' if curve=='AP数' else '三种方法使用带噪观测生成空间消息，位置反馈只量化一次坐标。'
            parts += ['**'+title+'**',f'纵轴为平均定位误差（m），横轴为{description}。',matrix(q,GEO,'mean_position_error_m',6,branch),
                f'![{title}](../results/dual_stream_full400/{branch}/{branch}_{model}_定位误差_{curve}.png)',
                f'结果：位置反馈平均误差从{qp.iloc[0].mean_position_error_m:.6f} m变为{qp.iloc[-1].mean_position_error_m:.6f} m。'+note]
    parts += [f'### {chapter}.2 吞吐量组']
    for curve in ['SNR','天线数','莱斯因子']:
        description=next(x[1] for x in CURVES if x[0]==curve)
        for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
            q=summary[summary.channel_model.eq(model)&summary.curve.eq(curve)&summary.stream_count.eq(2)]
            qp=q[q.method.eq('POS_R3')].sort_values('x_value');title=f'{branch}双流{name}吞吐量与{description}'
            note='观测SNR只控制CSI噪声，评价用数据SNR固定，SVD参考不随观测SNR改变。' if curve=='SNR' else '吞吐量按线性MMSE两流速率和计算，400 MHz直接换算。'
            if model=='LOS' and curve=='莱斯因子':note='纯LOS生成式不使用K，这条平线仅作一致性对照；MIX的K扫描才改变LOS与散射的功率比例。'
            parts += ['**'+title+'**',f'纵轴为双流平均吞吐量（Mbps），横轴为{description}。',matrix(q,['IDEAL_SVD']+UE,'mean_throughput_Mbps',2,branch),
                f'![{title}](../results/dual_stream_full400/{branch}/{branch}_{model}_双流吞吐量_{curve}.png)',
                f'结果：位置反馈平均吞吐量从{qp.iloc[0].mean_throughput_Mbps:.2f} Mbps变为{qp.iloc[-1].mean_throughput_Mbps:.2f} Mbps。'+note]
    q=summary[summary.channel_model.eq('MIX')&summary.curve.eq('AP数')&summary.stream_count.eq(2)]
    parts += [f'### {chapter}.3 比特数与AP数目','纵轴为两流合计的每次更新反馈有效载荷（bit），横轴为协作AP数。各方法的消息长度不依赖信道类型，图表使用MIX对应记录，纯LOS采用相同长度规则。',
              matrix(q,UE,'mean_feedback_bits',0,branch),f'![{branch}双流比特数与AP数目](../results/dual_stream_full400/{branch}/{branch}_双流反馈量_AP数.png)',
              '结果：CPU空间频率、DFT索引、位置反馈分别维持84、42、36 bit；CPU由模型计算第二相位，不新增反馈。UE方法在其单流消息上增加4(B−1) bit第二流相位。CPU图中的三个UE共享参考按各自完整双流消息长度计入。理想SVD没有有限反馈值，不画成0 bit方案。']
    return parts

def dual_supplement(branch,s,p,summary):
    s=display_panel(s,branch);p=display_panel(p,branch);summary=display_panel(summary,branch);parts=[]
    for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
        for curve,description,unit in CURVES:
            q=s[s.channel_model.eq(model)&s.curve.eq(curve)];title=f'{branch}{name}{description}补充分析'
            rows=[]
            for method in UE:
                for r in q[q.method.eq(method)].sort_values('x_value').itertuples():
                    row=[method_name(method,branch),f'{r.x_value:g}']
                    if curve=='AP数':row += [f'{r.mean_dual_Mbps:.2f}']
                    row += [f'{r.mean_delta_Mbps:.2f}',f'{100*r.positive_fraction:.2f}',f'{r.mean_second_mode_ratio:.4f}']
                    rows.append(row)
            headers=['方法','横轴']+(['双流 Mbps'] if curve=='AP数' else [])+['增量 Mbps','正收益 %','第二模式比']
            parts += ['### '+title,table(headers,rows)]
            if curve=='AP数':parts += [f'![{title}吞吐量](../results/dual_stream_full400/{branch}/{branch}_{model}_双流吞吐量_AP数.png)','该AP数与吞吐量关系保留为补充；正文AP扫描的主要开销图是比特数与AP数目。']
            parts += [f'![{title}单双流增量](../results/dual_stream_full400/{branch}/{branch}_{model}_单双流增量_{curve}.png)',
                f'结果：本组最小400位置平均增量为{q.mean_delta_Mbps.min():.2f} Mbps，最低正收益比例为{100*q.positive_fraction.min():.2f}%。平均收益为正不代表每个位置都获益。',
                f'![{title}第二模式](../results/dual_stream_full400/{branch}/{branch}_{model}_第二模式功率比_{curve}.png)',
                '第二模式功率比由真实接收矩阵HW的奇异值平方计算，用于辅助判断双流有效性，不能仅凭发送两列判定第二流有效。']
        default=p[p.channel_model.eq(model)&p.curve.eq('SNR')&p.x_value.eq(30)]
        rows=[]
        for method in UE:
            values=default[default.method.eq(method)].delta_Mbps
            rows.append([method_name(method,branch)]+[f'{values.quantile(x):.2f}' for x in [0,.05,.5,.95,1]])
        parts += ['### '+branch+name+'默认配置补充对照',
            f'![{branch}{name}默认配置单双流](../results/dual_stream_full400/{branch}/{branch}_{model}_默认单双流.png)',
            '同一400位置、总功率1下比较单流与等功率双流；SVD双流是等功率参考。',
            f'![{branch}{name}默认增量CDF](../results/dual_stream_full400/{branch}/{branch}_{model}_默认增量CDF.png)',
            table(['方法','最小 Mbps','5%分位','中位 Mbps','95%分位','最大 Mbps'],rows),
            'CDF与分位数按400个逐位置配对增量计算；不能将平均数或中位数作为最差位置保证。']
    return parts

def single_supplement(branch,s):
    qbranch=display_panel(s,branch);qbranch=qbranch[~qbranch.csi.eq('PERFECT')]
    q=qbranch[qbranch.curve.eq('SNR')]
    parts=['### '+branch+'单流频谱效率补充',matrix(q,['IDEAL_SVD']+UE,'mean_spectral_efficiency',4,branch),
           f'![{branch}单流频谱效率与SNR](../results/single_stream_V3_full400/{branch}/{branch}_频谱效率_SNR.png)',
           '频谱效率与正文吞吐量满足Mbps=400×bit/s/Hz，保留此图作换算补充。']
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

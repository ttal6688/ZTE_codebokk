"""Generate the full-scan Chinese report directly from audited result tables."""
from pathlib import Path
import json
import pandas as pd
from report_experiments import dual_experiments,dual_supplement,display_panel,method_name
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/dual_stream_full400'
NAMES={'TYPE_I':'全反馈Type-I(UE)','TYPE_II':'全反馈Type-II(UE)','DOCOMO_NFLOS':'Docomo','HAQSE_R3':'空间频率','DFT_INDEX_R3':'DFT索引','POS_R3':'位置反馈'}
CPU=['HAQSE_R3','DFT_INDEX_R3','POS_R3'];UE=['TYPE_I','TYPE_II','DOCOMO_NFLOS']+CPU

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows])

def build():
    a=json.loads((OUT/'independent_full_audit.json').read_text(encoding='utf-8'));assert a['status']=='passed' and a['positions']==400
    s=pd.read_csv(OUT/'method_feasibility_summary.csv');summary=pd.read_csv(OUT/'dual_stream_summary.csv')
    localization=pd.read_csv(OUT/'dual_position_summary.csv')
    p=pd.read_csv(OUT/'single_dual_pairs.csv' if (OUT/'single_dual_pairs.csv').exists() else OUT/'single_dual_pairs.csv.gz')
    unique=p[~p.method.eq('IDEAL_SVD')].drop_duplicates(['case_id','channel_model','branch','method','sample_id'])
    neg=unique[unique.delta_Mbps<=0];default=s[s.curve.eq('SNR') & s.x_value.eq(30)]
    lines=['# UPA单极化双流400位置完整实验报告',
      '2026年10月24日。本文面向需要了解实现方法与正式验证结果的项目参与者。双流已扩展至全部400个冻结位置，分别完成纯LOS和混合信道的观测SNR、UPA阵元数、AP数量与莱斯因子扫描。CPU三种几何方法和UE六种方法分别运行和汇总，未筛除低秩或负收益位置。',
      f"完整扫描包含16组不同参数配置、19个曲线标签和{a['physical_records']:,}条实际明细；重复默认配置展开后为{a['expanded_records']:,}条曲线记录。所有已测方法与配置的400位置平均增量均为正，最小为{s.mean_delta_Mbps.min():.2f} Mbps。{a['implementable_physical_pairs']:,}组可实施方法配对中，{len(unique)-len(neg):,}组双流速率高于单流，{len(neg):,}组不高于单流。最差增量为{a['minimum_gain_Mbps']:.3f} Mbps。双流是否值得使用需要结合位置、方法和信道条件，不能将32位置最小验证的全部正收益结论推广到整个范围。",
      '## 1 方法与实验口径',
      table(['项目','设置'],[
      ['阵列和极化','UPA 单极化 UE四接收阵元'],['位置和信道','位置1至400 原冻结部署 纯LOS及MIX分别测试'],
      ['默认配置','每AP32×32阵元 B=8 观测SNR=30 dB K=10 dB'],['观测SNR扫描','20 25 30 35 40 dB 仅改变CSI观测质量'],
      ['UPA规模扫描','8×8 16×16 32×32 即64 256 1024阵元'],['AP数量扫描','5至10个 使用固定公开AP顺序'],['莱斯因子扫描','0 5 10 15 20 dB'],
      ['功率和带宽','总功率1 每AP总功率1/B 两流各1/2 400 MHz直接换算'],['主评价','真实信道上线性MMSE两流速率和 同时保存联合logdet速率'],
      ['理想参考','真实CSI直接SVD 单流最优和等功率双流参考'],['反馈消息','实际整数比特串 由CPU独立解码得到发送矩阵']]),
      '观测SNR扫描不改变评价端的数据SNR；数据SNR及参考功率沿用冻结仿真设置。因此理想SVD参考随观测SNR保持不变。MIX仍包含LOS与散射，K=0 dB表示两者功率相等。纯LOS信道不使用K，保留LOS的K扫描作为一致性对照，不能将这条平线解释为LOS对K变化的物理响应。',
      '19个标签中的默认配置出现四次，直接复用同一份逐位置结果。16组参数配置也共享位置、散射和噪声种子，不将这些条目当作独立随机重复试验。单流与双流始终使用同一个位置、信道、观测和空间消息。',
      '### 从单流扩展到双流的实现',
      '首先完整执行各方法原有单流流程，得到每AP一条单位范数波束f_b和第一流跨AP相位。将空间波束放入BN×B的块对角矩阵F；单极化系数矩阵由B×1变为B×2，发送矩阵为',
      '$$\nW=FC\n$$',
      '单流系数为',
      r'$$'+'\n'+r'C_{b,1}=\frac{e^{j\theta_{b,1}}}{\sqrt{B}}'+'\n'+r'$$',
      '双流复用同一个f_b，两个系数变为',
      r'$$'+'\n'+r'C_{b,s}=\frac{e^{j\theta_{b,s}}}{\sqrt{2B}},\quad s=1,2'+'\n'+r'$$',
      '第一列仅缩放到原单流的1/√2，第一相位和波束均保留。第二流增加每AP不同的相位；若仅给整列乘一个全局相位，两列仍共线，不能形成第二接收模式。每AP两流共同使用原波束，未额外寻找第二条空间波束。',
      '第二相位通过低维有效信道E设计，每列为H_b f_b。先比较残余主模式相位与跨AP相位斜坡两个固定初始化，再进行三轮坐标更新，以两流线性MMSE速率和为目标。UE搜索16个离散相位，CPU采用64点粗搜索和24次固定连续细化。初始化、轮数和容差与最小验证一致，本次未根据完整扫描结果调参；此搜索不保证全局最优。',
      'Type-II保留原来的复合空间波束，两流共用它。Docomo保留已验证的单流结构适配及第一相位，第二流也采用上述统一扩展；它不是论文原始多列AP二维DFT子集的完整复现，报告与图例持续标为结构适配。',
      '位置反馈仍先用连续HAQSE频率定位，再按13/14/9 bit量化一次坐标。普通UE第一相位仍为联合主模式投影后的4 bit相对相位，Docomo保留自身QPSK共相位。第二流不改变定位和第一流的算法。',
      '## CPU端完整实验',
      'CPU分别接收HAQSE频率整数、DFT方向索引或位置坐标整数，只用这些消息和公共几何重建模型、恢复共享波束，计算两流相位。CPU接口不接收观测信道、真实信道或UE连续位置；真实信道仅在仿真评价时使用。第二流相位由CPU在模型上直接计算，空间消息只发送一次，第二流无需新增反馈。']
    def default_table(branch,model):
        q=display_panel(default,branch);q=q[q.channel_model.eq(model)].set_index('method');rows=[]
        for method in UE:
            r=q.loc[method];rows.append([method_name(method,branch),f'{r.mean_single_Mbps:.2f}',f'{r.mean_dual_Mbps:.2f}',f'{r.mean_delta_Mbps:.2f}',f'{100*r.positive_fraction:.2f}%',f'{r.minimum_delta_Mbps:.2f}'])
        return table(['方法','单流 Mbps','双流 Mbps','增量 Mbps','正收益比例','最小增量 Mbps'],rows)
    def branch_section(branch):
        section=[]
        for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
            section += ['### '+branch+name+'默认配置',default_table(branch,model)]
        q=default[default.branch.eq(branch)&default.channel_model.eq('MIX')].set_index('method');pos=q.loc['POS_R3'];haq=q.loc['HAQSE_R3']
        section += [f"默认混合信道下，位置反馈平均速率由{pos.mean_single_Mbps:.2f}提升至{pos.mean_dual_Mbps:.2f} Mbps；相较HAQSE双流均值相差{pos.mean_dual_Mbps-haq.mean_dual_Mbps:+.2f} Mbps。该比较使用全部400个相同位置，表中最小增量和正收益比例保留位置差异。"]
        section += [f"默认混合信道位置反馈的接收第二模式与第一模式功率比均值为{pos.mean_second_mode_ratio:.4f}，最小值为{pos.minimum_second_mode_ratio:.4f}。这组指标与速率一起用于判断第二流是否形成有用接收模式。"]
        section += dual_supplement(branch,s,p,summary)
        k0=s[s.branch.eq(branch)&s.channel_model.eq('MIX')&s.curve.eq('莱斯因子')&s.x_value.eq(0)].set_index('method')
        section += [f"强散射的K=0 dB配置中，位置反馈双流均值为{k0.loc['POS_R3'].mean_dual_Mbps:.2f} Mbps，正收益比例为{100*k0.loc['POS_R3'].positive_fraction:.2f}%；DFT索引双流均值为{k0.loc['DFT_INDEX_R3'].mean_dual_Mbps:.2f} Mbps。位置反馈的低开销优势不代表它在所有信道条件下速率领先。第二相位只能在既定共享波束内调整，不能修复先前定位或空间波束失配。"]
        if branch=='UE':section += ['默认混合信道中Type-II双流均值低于Type-I，Docomo结构适配高于两者。当前空间波束与第一相位按单流设计并冻结，双流未重新联合选择空间波束，因此不能从单流排名或码本大小直接推断双流排名。']
        section += ['本端纯LOS与MIX的逐实验图表、数值和解释已分别列出，不合并两种信道均值。']
        return section
    index=lines.index('## CPU端完整实验')
    cpu_description=lines[index+1]
    lines=lines[:index]
    lines += ['正文按CPU与UE分别列出定位误差三项、吞吐量三项及比特数与AP数一项。AP数与吞吐量、单双流增量、第二模式、CDF及默认配置对照统一放在额外补充。定位误差由保存的双流空间消息恢复，第二流复用原定位前端。']
    lines += dual_experiments('CPU',summary,localization)+dual_experiments('UE',summary,localization)
    lines += ['## 4 额外补充','### CPU端补充分析',cpu_description]
    lines+=branch_section('CPU')
    lines += ['### CPU反馈量和模型限制','默认32×32、8 AP时，HAQSE为84 bit、DFT为42 bit、位置反馈为36 bit，单双流完全相同。阵元数变化时DFT索引位宽随码本规模变化；HAQSE仍为固定6个14 bit频率，位置反馈仍为36 bit。AP数量变化也不增加这三种CPU空间消息的参考AP数量。',
      'CPU在几何模型上优化第二相位，实际信道中的散射、定位误差和波束约束会影响双流性能。不能以模型目标逐轮不下降推断真实信道性能必然提高；目标不下降是相对于双流初值，单流与双流还存在功率平分和接收干扰的差别。',
      '### UE端补充分析',
      'UE使用全部活动AP的带噪观测和消息解码后的波束形成有效信道，设计第二相位，再发送B−1个4 bit相对相位，参考AP固定为0。CPU只依靠原有整数消息与新增相位整数恢复两列预编码，不直接使用UE浮点发送矩阵。']
    lines+=branch_section('UE')
    lines += ['### UE实际反馈开销',table(['方法','默认单流 bit','默认双流 bit','新增 bit'],[[NAMES[m],b,b+28,28] for m,b in zip(UE,[140,292,129,112,70,64])]),
      '新增开销为4(B−1) bit，B从5增至10时依次为16、20、24、28、32、36 bit。默认位置反馈双流为92 bit，HAQSE为140 bit；这只统计各方法一致的有效载荷，不含传输头、纠错等协议开销。Type-I、Type-II与Docomo的空间反馈随阵元数和AP数改变，明细由实际消息长度产生。',
      '### 第二流有效性的判据与不利样本',
      '评价端对真实信道计算G=HW，再由I+ρGᴴG的逆矩阵对角线求各流MMSE SINR，速率为',
      r'$$'+'\n'+r'R=\sum_{s=1}^{2}\log_2(1+\gamma_s)'+'\n'+r'$$',
      'Mbps等于该频谱效率乘400。保存的联合logdet速率用于交叉检查，MMSE速率不高于联合速率。每条明细还保存真实信道、固定空间波束子空间及最终接收矩阵的第二模式功率比，避免仅凭发送矩阵有两列判断双流有效。',
      '真实CSI直接SVD参考不含CSI估计噪声，但真实信道仍按LOS或MIX生成，接收数据SNR照常计入速率。双流SVD取前两个奇异向量并等功率分配，放松每AP等功率限制；它是等功率双流参考，不是任意功率分配下的一般容量上界。']
    if len(neg):
        groups=neg.groupby(['branch','channel_model','method']).agg(count=('sample_id','count'),worst=('delta_Mbps','min')).reset_index()
        lines += ['负收益统计按16组参数配置去除重复默认标签，汇总如下。所有非正收益逐位置记录另存nonpositive_gain_cases.csv，其中保留曲线标签以便定位。',table(['端','信道','方法','非正收益条目','最差增量 Mbps'],[[r.branch,r.channel_model,NAMES[r.method],r.count,f'{r.worst:.2f}'] for r in groups.itertuples()]),
          '负收益表明固定共享波束、保留第一相位并强制等功率双流并不适合所有位置。该实现没有自适应流数或功率分配，也没有用真实信道决定回退单流。后续可在UE观测或CPU模型上设计回退规则，再单独验证其可靠性；本报告不把离线真值择优作为当前算法性能。']
        lines += [f"按配置归类，非正收益中{int((neg.KdB==0).sum())}条出现在K=0 dB，{int((neg.Nant<1024).sum())}条出现在64或256阵元配置。该分布说明默认32×32、K=10 dB下的全部正收益不能推广至小阵列和强散射范围。"]
    else:lines += ['本次全部可实施配对均为正收益，但证据范围仍限于当前冻结部署和参数，不构成任意位置的双流收益保证。']
    lines += ['### 原运行执行过程和独立核验',
      '先在位置1与399上完成全部16组参数配置的小样本流程检查，覆盖阵元数、AP数、观测质量和K值变化。通过后运行正式400位置扫描。不同计算进程写入互不重叠的参数目录，汇总时验证参数、位置编号和消息字段，重复默认配置复用同一明细。',
      f"Python从冻结位置和散射系数独立重建真实信道，逐条解码所有16个配置中的整数消息，计算CPU第二相位参考、系数、功率、发送签名、MMSE速率与第二模式，再重新计算所有均值及单双流配对。共核验{a['physical_records']:,}条实际明细，其中可实施记录{2*a['implementable_physical_pairs']:,}条。全部曲线组均有400个不同位置。",
      f"与上一轮400位置单流正式扫描按方法、位置和参数逐条对齐，最大吞吐量差{a['maximum_old_single_Mbps_error']:.3g} Mbps。独立核验最大频谱效率误差{a['maximum_metric_SE_error']:.3g}，最大真实有效信道误差{a['maximum_true_effective_channel_error']:.3g}；CPU连续相位跨实现最大系数差{a['maximum_CPU_continuous_coefficient_numerical_error']:.3g}。LOS的K对照及SVD的观测SNR对照均通过。",
      f"连续启发式搜索在MATLAB和NumPy的浮点运算下可能进入不同更新分支。本轮有{a['native_replayed_cross_implementation_disagreements']}条记录的归一化系数差达到预设1e−3核对阈值，全部单列于CPU_continuous_replay_required.csv，并在原MATLAB环境仅凭公共几何和比特串严格重放，要求系数与发送签名误差小于1e−10后才通过最终核验。未修改双流算法或原始结果，也未将这些记录排除。发生上述差异的配置中，独立搜索的模型目标最大差为{a['maximum_CPU_design_SE_cross_implementation_difference']:.6g} bit/s/Hz；这与前述对已保存预编码的独立真实速率核验属于不同检查。",
      '### 数据保存和复现',
      '完整明细按16组参数配置保存于results/dual_stream_full400/cases/case_XX。每组含LOS与MIX、CPU与UE、单流与双流全部记录；原始CSV以无损gzip上传，前导零比特串和浮点字段原样保留，并提供SHA256和解压往返校验。汇总及70组PNG与可编辑MATLAB FIG另存，CPU和UE各35组；其中新增12幅定位误差图从原双流消息恢复，其余58幅为已有扫描图。',
      '运行前只添加8.单流目录，不对历史副本递归添加路径。使用新的输出目录，原有报告、结果和冻结输入不覆盖。',
      '```matlab\naddpath(\'8.单流\');\nexperimentDir=fullfile(pwd,\'8.单流\',\'results\',\'new_dual400\');\nrun_dual_stream_task2(\'OutputDir\',experimentDir);\nplot_precoding_results(experimentDir);\n```',
      '```text\npython audit_dual_stream_full.py results/new_dual400 --stage cases\n```',
      '```matlab\nverify_dual_stream_replay(experimentDir);\n```',
      '```text\npython audit_dual_stream_full.py results/new_dual400 --stage summary\npython package_dual_stream_results.py results/new_dual400\n```',
      '需要并行运行时，四个进程分别传入Stage=run、Worker=1至4、Workers=4，完成后单独以Stage=finalize汇总。并行只划分参数配置，不改变样本、算法或消息。包内README给出逐条数据读取与审计方式。',
      '本轮已完成既定四类参数的完整双流实验。同步误差、移动性、宽带逐子载波处理、自适应流数与双极化不属于当前单极化扩展模型，尚无对应验证结论。']
    content='\n\n'.join(lines)+'\n'
    content=content.replace('报告与图例持续标为结构适配','图例统一使用Docomo，实现范围在正文说明').replace('Docomo结构适配','Docomo').replace('HAQSE','空间频率').replace('空间频率频率','空间频率')
    content=content.replace('### CPU端补充分析','### CPU端补充分析\n\n全反馈Type-I(UE)、全反馈Type-II(UE)和Docomo(UE)复用已有UE结果作为共享参考，不计为CPU独立几何算法。')
    dest=ROOT/'docs/UPA单极化双流400位置完整实验报告.md';dest.write_text(content,encoding='utf-8');print(dest)

if __name__=='__main__':build()

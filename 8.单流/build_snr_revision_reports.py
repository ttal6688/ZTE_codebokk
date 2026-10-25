"""Build current single/dual reports with separate CPU, UE and channel results."""
from pathlib import Path
import json, re
import pandas as pd
from report_experiments import GEO, UE, REFERENCE_NOTE, display_panel, matrix, method_name, table
from prepare_snr_revision400 import OUT, LOCATION_SNRS, RATE_SNRS

ROOT=Path(__file__).resolve().parent
TITLES={1:'UPA单流400位置正式实验报告',2:'UPA单极化双流400位置完整实验报告'}
CURVES={'SNR':'观测SNR','天线数':'UPA阵元数','AP数':'协作AP数','莱斯因子':'莱斯因子K'}

def image(ns,branch,name,title):
    stream='single' if ns==1 else 'dual'
    return f'![{title}](../results/{OUT.name}/figures/{stream}/{branch}/{name}.png)'

def method_section(ns):
    lines=['## 1 方法与实验口径',table(['项目','设置'],[
        ['阵列和接收端','单极化UPA，UE四接收阵元'],['位置和信道','冻结位置1至400全部保留；纯LOS和MIX分别给出结果'],
        ['默认配置','每AP32×32阵元、协作AP数8、定位参考AP数3、观测SNR 30 dB、K=10 dB'],
        ['定位误差的观测SNR','−20、−10、0、10、20、30、40 dB'],
        ['吞吐量的观测SNR','−20、−15、−10、−5、0、5、10、15、20 dB'],
        ['UPA阵元数','64、256、1024'],['协作AP数','原始5至10；图的显示范围5至9，横轴仅整数'],
        ['莱斯因子','0、5、10、15、20 dB；纯LOS不使用K，仅作一致性对照'],
        ['功率和带宽','总功率1，各AP总功率1/B；400 MHz直接换算，不增加OFDM或带宽噪声模型'],
        ['评价用数据SNR','固定参考数据SNR 10 dB及原参考功率，不随观测SNR改变'],
        ['主参考','真实信道直接SVD；单流取最优第一右奇异向量，双流取前两向量并等功率'],
        ['反馈','实际MSB优先整数比特串；CPU独立解码；各方法一致不含公共配置、传输头与FEC']]),
        '观测信道由真实信道加CSI估计噪声得到。真实信道仍包含相应的LOS传播或LOS与散射混合传播。普通方法只根据带噪观测或收到的空间消息设计，真实信道只用于评价和SVD参考。观测SNR扫描改变CSI质量，数据链路噪声照常保留，因此SVD参考随观测SNR保持不变。',
        '本轮使用两类SNR点的并集计算或复用物理案例，再按对应实验取点；不是只裁剪旧曲线。所有SNR配置使用同一批位置、散射系数和冻结噪声种子，改变噪声幅度。每点400个不同位置，不把CPU和UE、单双流、重复默认标签作为独立随机样本。定位SNR图纵轴标为“定位误差（m）”；吞吐量采用线性纵轴，下限按该图所有方法的最低值向下留少量余量，上限同样留白。',
        '### 单流空间波束与第一流相位',
        'Type-I将联合观测信道的主右奇异向量按AP分块，匹配本地二维DFT波束。Type-II在同一正交分组选择两条波束，组合幅度3 bit、内部相位2 bit。Type-I、Type-II、空间频率、DFT索引和位置反馈五种普通UE方法统一使用联合主模式投影，共相位以首AP为0，其余AP的相对相位各4 bit。',
        '空间频率反馈三个参考AP的两维估计频率，每维14 bit；DFT索引反馈同三个AP的二维码本索引。位置反馈先以连续空间频率在UE定位，再将坐标按13/14/9 bit量化一次。位置方案不使用已经量化的频率来定位，也不先量化频率再量化坐标。',
        'CPU端三种几何方法仅依靠收到的空间整数消息和公共AP几何恢复位置、空间波束与模型，并在模型上计算相位。CPU不接收参考AP的完整观测信道或UE连续位置。UE端则用全AP观测CSI和消息恢复后的波束计算相位，再反馈相位整数。实现中实际使用从整数消息恢复的发送向量，而非直接使用UE浮点波束。',
        '### Docomo的实现范围',
        'Docomo依据Near-Field Line-of-Sight MIMO Precoding with Distributed Antennas第IV节式25至27与第V节，采用每AP本地DFT波束、QPSK共相位和跨AP模式的结构。当前不规则部署使用公开AP顺序的一维逻辑DFT，保留项目码本和三轮坐标更新；它是结构适配，并非论文全部场景的复现。论文Type-I为NCJT，本项目Type-I含共相位，两者定义不同。默认单流Docomo为129 bit，不套用论文特定场景的26 bit。既有48项Docomo专项、701项协议及42项UPA/POS验证保留，详见[Docomo专项说明](Docomo结构适配与专项验证.md)。']
    if ns==2:
        lines += ['### 从单流扩展到双流',
            '首先完整运行各方法的单流流程，得到每AP一条单位范数空间波束及第一流跨AP相位。把这些波束置于BN×B块对角矩阵F中，系数矩阵C从B×1扩展为B×2，发送矩阵为',
            '$$\nW=FC\n$$',
            '单流每AP系数为',r'$$'+'\n'+r'C_{b,1}=\frac{e^{j\theta_{b,1}}}{\sqrt{B}}'+'\n$$',
            '双流每AP的两个系数为',r'$$'+'\n'+r'C_{b,s}=\frac{e^{j\theta_{b,s}}}{\sqrt{2B}},\quad s=1,2'+'\n$$',
            '两流共用同一条每AP空间波束。第一列只缩放为原单流的1/√2，第一相位保持不变。第二流新增的是每个AP各自的相对相位；仅给整列一个全局相位会令两列共线，不能形成第二模式。每AP两列合计功率1/B，两流各占总功率的一半。',
            '对低维有效信道E=[H_b f_b]设计第二相位。先比较残余主模式和跨AP相位斜坡两个固定初始化，再进行三轮坐标更新，以线性MMSE两流速率和为目标。UE每次搜索16个离散相位，CPU用64点粗搜索及24步固定连续细化。CPU的E来自公共几何模型，UE的E来自带噪观测。该启发式搜索不保证全局最优，本轮仅拓宽观测SNR，没有修改优化规则。',
            'UE额外发送B−1个4 bit第二流相位，新增4(B−1) bit；CPU几何方法自行计算第二相位，空间消息不重复发送，新增0 bit。Type-II两流仍共享其原有复合波束。Docomo第二流采用同样的通用相位扩展，未完整复现论文多列AP二维DFT子集算法。',
            '定位前端和空间消息被两流直接复用，因此同一位置与配置下，单双流的定位误差相同。多一条数据流本身不增加定位观测。双流主指标为真实信道上线性MMSE两流速率和，另保存联合logdet速率核对；等功率两流SVD是参考，不能称为任意功率分配下的一般容量上界。']
    else:
        lines += ['单流使用一个发送向量，速率为log2(1+ρ‖Hw‖²)，Mbps等于频谱效率乘400。真实CSI直接SVD在总功率1下给出最优单流参考，放松可实施方法的每AP等功率约束。',
            '新增单流LOS结果直接取自已验证配对案例中的stream_count=1，使用同一个原生单流设计和解码器；第二流设计不反向修改第一流。现有MIX配置已与此前正式单流逐位置对齐，不能把配对来源理解为使用双流结果代替单流。']
    return lines

def main_experiments(ns,branch,s):
    chapter=2 if branch=='CPU' else 3
    stream='单流' if ns==1 else '双流'
    q=display_panel(s,branch);q=q[q.stream_count.eq(ns)]
    lines=[f'## {chapter} {branch}端正式实验','以下纯LOS、MIX分别列出，每个图表点均为400位置均值。'+REFERENCE_NOTE]
    for group,specs in [(1,[('SNR','定位误差','mean_position_error_m',GEO,6),('天线数','定位误差','mean_position_error_m',GEO,6),('AP数','定位误差','mean_position_error_m',GEO,6)]),
        (2,[('SNR','吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+UE,2),('天线数','吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+UE,2),('莱斯因子','吞吐量','mean_throughput_Mbps',['IDEAL_SVD']+UE,2)])]:
        lines += [f'### {chapter}.{group} '+('定位误差组' if group==1 else '吞吐量组')]
        for curve,stem,field,methods,digits in specs:
            for model,modelname in [('LOS','纯LOS'),('MIX','混合信道')]:
                t=q[q.channel_model.eq(model)&q.curve.eq(curve)]
                if curve=='SNR':t=t[t.x_value.isin(LOCATION_SNRS if group==1 else RATE_SNRS)]
                pos=t[t.method.eq('POS_R3')].sort_values('x_value');a=pos.iloc[0];b=pos.iloc[-1]
                unit='m' if group==1 else 'Mbps';title=f'{branch}{stream}{modelname}{stem}与{CURVES[curve]}'
                lines += ['**'+title+'**',f'横轴为{CURVES[curve]}，纵轴为{stem}（{unit}）。',matrix(t,methods,field,digits,branch),image(ns,branch,f'{model}_{stem}_{curve}',title)]
                if group==1:
                    note='定位参考数仍固定3，增加协作AP不等于增加定位参考观测。' if curve=='AP数' else '空间频率、DFT索引使用各自解码方向定位，位置反馈使用一次量化后的坐标。'
                    if curve=='SNR':note+=' 高SNR后的残余误差受空间估计、信道模型和有限反馈共同影响，不能要求逐点单调。'
                else:
                    note='只改变CSI观测噪声，数据SNR固定，SVD保持不变。更准确的CSI不保证离散码本及固定启发式的每个均值都严格上升。' if curve=='SNR' else '其他参数保持默认值；结论限于当前冻结部署。'
                    if model=='LOS' and curve=='莱斯因子':note='纯LOS不使用K，平线仅作一致性对照；MIX的K扫描才改变LOS和散射比例。'
                    note+=' 纵轴根据本图所有曲线的最小值和最大值留少量余量，未改变数据。'
                lines += [f'结果：位置反馈在横轴{a.x_value:g}时为{a[field]:.{digits}f} {unit}，在{b.x_value:g}时为{b[field]:.{digits}f} {unit}。'+note]
    t=q[q.channel_model.eq('MIX')&q.curve.eq('AP数')]
    lines += [f'### {chapter}.3 比特数与AP数目','横轴为协作AP数，纵轴为每次更新反馈有效载荷（bit）。长度规则不依赖信道类型，LOS与MIX相同；表内保留5至10 AP，图中仅显示整数5至9。',
        matrix(t,UE,'mean_feedback_bits',0,branch),image(ns,branch,'比特数_AP数',f'{branch}{stream}反馈比特数与AP数'),
        '结果：CPU三种几何方法始终为84、42、36 bit。CPU图中的Type-I、Type-II和Docomo为完整UE消息的共享参考；不能将其计为CPU独立算法。UE几何方案还包含4(B−1) bit第一相位。'+('双流UE再增加4(B−1) bit第二相位，CPU不增加反馈。' if ns==2 else '空间消息固定三个参考AP，所以CPU几何开销不随协作AP数增加。')]
    return lines

def supplements(ns,s,p,diag):
    lines=['## 4 额外补充','补充实验也使用当前SNR范围。单流定位前端的量化与越界诊断单独列出；双流补充逐位置增量、第二模式以及默认配置分布。']
    for branch in ['CPU','UE']:
        q=display_panel(s,branch);q=q[q.stream_count.eq(ns)]
        ps=display_panel(p,branch)
        for model,name in [('LOS','纯LOS'),('MIX','混合信道')]:
            t=q[q.channel_model.eq(model)&q.curve.eq('SNR')&q.x_value.isin(RATE_SNRS)]
            title=f'{branch}{name}频谱效率与观测SNR'
            lines += ['### '+title,matrix(t,['IDEAL_SVD']+UE,'mean_spectral_efficiency',4,branch),image(ns,branch,f'{model}_频谱效率_SNR',title),'结果：逐点满足吞吐量Mbps=400×频谱效率，横轴使用−20至20 dB、间隔5 dB。']
            if ns==1:
                d=diag[diag.channel_model.eq(model)&diag.K.eq(10)&diag.SNR.isin(LOCATION_SNRS)].sort_values('SNR')
                title=f'{branch}{name}位置反馈坐标量化前后'
                lines += ['### '+title,table(['观测SNR dB','量化前误差 m','解码后误差 m'],[[r.SNR,f'{r.mean_raw_position_error_m:.6f}',f'{r.mean_position_error_m:.6f}'] for r in d.itertuples()]),image(ns,branch,f'{model}_POS量化前后_SNR',title),
                    '结果：先连续频率定位、再量化坐标一次。低SNR下坐标区域截断可使平均欧氏误差降低，包含公开区域先验，不表示量化提高定位算法精度。CPU与UE使用同一空间消息，因此此处诊断相同。']
                d=diag[diag.channel_model.eq(model)&diag.SNR.eq(30)].sort_values('K');title=f'{branch}{name}坐标量化越界与莱斯因子'
                lines += ['### '+title,table(['K dB','连续误差 m','解码误差 m','越界比例 %'],[[r.K,f'{r.mean_raw_position_error_m:.6f}',f'{r.mean_position_error_m:.6f}',f'{100*r.mean_quantizer_overflow:.2f}'] for r in d.itertuples()]),image(ns,branch,f'{model}_POS越界比例',title),
                    f'结果：本组最大越界比例为{100*d.mean_quantizer_overflow.max():.2f}%，全部位置保留；越界坐标按原公共量化区域截断。']
            else:
                for curve in CURVES:
                    t=q[q.channel_model.eq(model)&q.curve.eq(curve)]
                    gain=ps[ps.channel_model.eq(model)&ps.curve.eq(curve)]
                    if curve=='SNR':t=t[t.x_value.isin(RATE_SNRS)];gain=gain[gain.x_value.isin(RATE_SNRS)]
                    rows=[]
                    for method in UE:
                        for r in gain[gain.method.eq(method)].sort_values('x_value').itertuples():
                            mode=t[t.method.eq(method)&t.x_value.eq(r.x_value)].iloc[0].mean_second_mode_ratio
                            rows.append([method_name(method,branch),f'{r.x_value:g}',f'{r.mean_delta_Mbps:.2f}',f'{100*r.positive_fraction:.2f}',f'{r.minimum_delta_Mbps:.2f}',f'{mode:.4f}'])
                    title=f'{branch}{name}{CURVES[curve]}下的双流增量和第二模式'
                    lines += ['### '+title,table(['方法','横轴','平均增量 Mbps','正收益 %','最差增量 Mbps','第二模式比'],rows),image(ns,branch,f'{model}_单双流增量_{curve}',title+'增量'),image(ns,branch,f'{model}_第二模式_{curve}',title+'第二模式'),
                        f'结果：本组最低平均增量{gain.mean_delta_Mbps.min():.2f} Mbps，最低正收益比例{100*gain.positive_fraction.min():.2f}%。平均正收益不保证每个位置受益，低SNR下强制双流也可能退化。第二模式比按真实接收矩阵HW的奇异值平方计算。']
                    if curve=='AP数':lines += [matrix(t,['IDEAL_SVD']+UE,'mean_throughput_Mbps',2,branch),image(ns,branch,f'{model}_吞吐量_AP数',f'{branch}{name}双流吞吐量与AP数'),'AP数与吞吐量保留在补充；正文对应的主要开销实验是比特数与AP数。']
                title=f'{branch}{name}默认配置单双流与增量分布'
                t=display_panel(s,branch);t=t[t.channel_model.eq(model)&t.curve.eq('SNR')&t.x_value.eq(30)]
                rows=[]
                for method in UE:
                    one=t[t.method.eq(method)&t.stream_count.eq(1)].iloc[0];two=t[t.method.eq(method)&t.stream_count.eq(2)].iloc[0]
                    g=ps[ps.channel_model.eq(model)&ps.curve.eq('SNR')&ps.x_value.eq(30)&ps.method.eq(method)].iloc[0]
                    rows.append([method_name(method,branch),f'{one.mean_throughput_Mbps:.2f}',f'{two.mean_throughput_Mbps:.2f}',f'{g.mean_delta_Mbps:.2f}',f'{100*g.positive_fraction:.2f}'])
                lines += ['### '+title,table(['方法','单流 Mbps','双流 Mbps','增量 Mbps','正收益 %'],rows),image(ns,branch,f'{model}_默认单双流',title),image(ns,branch,f'{model}_默认增量CDF',title+'CDF'),
                    '结果：默认配置仍为观测SNR 30 dB。此处是单独默认点，不向吞吐量SNR扫描中额外插入30 dB；CDF使用全部400个配对位置，数据沿用同一默认案例。']
        if ns==1:
            lines += ['### '+branch+'坐标bit分配',table(['坐标','bit','位置是否改变分配'],[['x',13,'否'],['y',14,'否'],['z',9,'否']]),
                f'![{branch}固定坐标bit分配](../results/single_stream_V3_full400/{branch}/{branch}_固定坐标bit分配.png)',
                '结果：按公共几何的相对AP相位敏感度固定分配13/14/9 bit，总计36 bit。LOS和MIX、单双流均相同，不用未知真实位置在线调整。图中真实x只用于展示，图沿用原冻结分配检查。']
    return lines

def build(stream_counts=(1,2)):
    s=pd.read_csv(OUT/'experiment_summary.csv');p=pd.read_csv(OUT/'paired_gain_summary.csv');d=pd.read_csv(OUT/'position_diagnostics_summary.csv')
    a=json.loads((OUT/'assembly_audit.json').read_text(encoding='utf-8'));assert a['status']=='passed'
    for ns in stream_counts:
        title=TITLES[ns];lines=['# '+title,'2026年10月25日更新。本文解释UPA单极化方案在400个冻结位置上的实现和实验结果，CPU、UE分别报告，纯LOS与MIX逐实验分开展示。定位误差的观测SNR改为−20:10:40，吞吐量改为−20:5:20；单流补齐原先正文缺失的LOS结果。数据链路SNR保持固定。',
            f'本版汇总{a["physical_cases"]}个不同物理配置，共{a["physical_records"]:,}条含单双流配对的原生明细。新增8个低SNR配置，每个含LOS、MIX及400位置；其余14个配置直接复用已审计结果。每张曲线和表格均按400个位置求均值，未筛除不利或越界样本。',
            '正文保持每端定位误差三项、吞吐量三项、比特数与AP数一项的结构。每个实验均附图片、完整数值和结果说明。图例保持全反馈Type-I(UE)、全反馈Type-II(UE)、Docomo、空间频率、DFT索引、位置反馈，CPU共享Docomo标作Docomo(UE)。']
        lines += method_section(ns)
        for branch in ['CPU','UE']:lines += main_experiments(ns,branch,s)
        lines += supplements(ns,s,p,d)
        lines += ['## 5 实现过程与数据复现',
            '先按两类SNR范围的并集确定11个SNR点。已有20、30、40 dB直接复用原物理案例；新增−20、−15、−10、−5、0、5、10、15 dB，保持原信道、噪声种子、码本、第一相位、第二相位优化及整数消息规则。阵元数、AP数、K扫描复用原案例；单流LOS使用同一案例保存的第一流结果。',
            '新增案例先在原MATLAB环境运行，再由独立Python程序解码比特串、重建真实有效信道、核对功率、发送签名、MMSE速率、第二模式及均值。连续第二相位在跨实现浮点边界处有分歧的记录逐条保留，并在原生解码器中仅凭公共几何和整数消息严格重放。定位指标独立从空间前缀恢复；另外重新计算连续位置诊断并与保存的解码位置逐条对齐。',
            f'原单流MIX重叠配置共核对{a["old_single_overlap_records"]:,}条，最大吞吐量差{a["maximum_old_single_throughput_difference_Mbps"]:.3g} Mbps。坐标诊断与消息解码核对{a["diagnostic_overlap_records"]:,}条，最大误差差值{a["maximum_diagnostic_position_error_difference_m"]:.3g} m。SVD随观测SNR不变、纯LOS随K不变及全部曲线组400位置均通过检查。',
            '[数据、配置来源及运行命令](../results/'+OUT.name+'/README.md)。原400位置数据、原小样本SNR预实验和固定8 AP参考数预实验继续保留；本次正式报告替换原报告同名入口，所有新图使用独立版本路径避免缓存。',
            '位置反馈的完整通信协议仍固定三个定位参考AP；之前R=3至8实验是独立定位诊断，本轮未将其混入正式扫描。观测SNR提高不能消除离散反馈和模型误差，双流也不保证每个位置或每个低SNR配置都比单流更好。Word与Markdown由同一内容生成；按用户要求Word不追加检查。']
        content='\n\n'.join(lines)+'\n'
        for link in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',content):assert (ROOT/'docs'/link).resolve().exists(),link
        (ROOT/'docs'/f'{title}.md').write_text(content,encoding='utf-8')
        print(title,content.count('!['),'figures')

if __name__=='__main__':build()

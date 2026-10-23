function audit = run_single_stream_task2(varargin)
%RUN_SINGLE_STREAM_TASK2 UPA单极化单流、400 MHz窄带速率换算入口。
%   默认 smoke 模式只使用少量固定样本检查数据链路与全部出图。
%   完整仿真示例：
%   run_single_stream_task2('Mode','full','OutputDir','results/single_stream_full');
%
%   CPU 侧只由固定 R=3 条方向/位置消息重构波束和共相位；UE 侧
%   使用观测 CSI 计算共相位。Type-I/II 是全反馈（UE-CSI）基线；
%   Docomo 方案仅在 UE 侧吞吐量和反馈开销图中比较。

root = fileparts(mfilename('fullpath'));
dep = fullfile(root,'6.位置反馈方案');
addpath(root,dep,fullfile(dep,'lib'));maxNumCompThreads(1);
parser = inputParser;
addParameter(parser,'Mode','smoke',@(x) ismember(x,{'smoke','full','verify'}));
addParameter(parser,'OutputDir','',@(x) ischar(x) || isstring(x));
addParameter(parser,'Samples',[],@(x) isempty(x) || (isnumeric(x) && isscalar(x) && x>=1));
addParameter(parser,'MakeFigures',true,@islogical);
parse(parser,varargin{:});
opt = parser.Results;

[net0,sim,bank] = upa.load_inputs();
sim.bandwidth_Hz = 400e6;
sim.rho_data = 10^(sim.reference_data_SNR_dB/10)/sim.reference_power;
sim.task_id = 'UPA_SINGLE_POS_CONTINUOUS_V1';
if isempty(opt.OutputDir)
    out = fullfile(root,'results',['single_stream_UPA_POS_V1_' char(opt.Mode)]);
else
    out = char(opt.OutputDir);
end
assert(~exist(fullfile(out,'single_stream_trials.csv'),'file'),'sstr:ExistingResults','Use a new OutputDir to preserve prior results');
if ~exist(out,'dir'), mkdir(out); end

if isempty(opt.Samples)
    if strcmp(opt.Mode,'full'), sampleIds = 1:400; elseif strcmp(opt.Mode,'verify'), sampleIds=[399 400]; else, sampleIds = 1:6; end
else
    sampleIds = 1:min(400,round(opt.Samples));
end
settings = make_settings(opt.Mode);
rows = cell(0,29);
started = tic;

for si = 1:numel(settings)
    q = settings(si);
    net = sstr.configure_upa(net0,q.Nant);
    ids = net.active_order(1:q.B);
    refs = net.reference3;
    for sid = sampleIds
        sample = make_sample(net,sim,bank,sid,q.KdB);
        [Htrue,Hobs] = observe_sample(sample,ids,q.SNRdB);
        [utrue,s2,vtrue] = upa.principal(Htrue);
        truth = struct('u',utrue,'s2',s2,'v',vtrue);
        [type1,type2,docomo,idealDesign] = full_feedback_design(net,Hobs,truth,q.B,sim.UE_phase_bits);
        [haqse,dftindex,position] = partial_designs(net,Hobs,ids,refs,sim);
        % Docomo 的码字选择以 UE 观测 CSI 为依据，按前次讨论不并入
        % CPU 几何反馈链路；Type-I/II 则作为完整 UE-CSI 反馈基线同时列出。
        designs = {idealDesign,type1,type2,haqse.cpu,dftindex.cpu,position.cpu, ...
                   idealDesign,type1,type2,docomo,haqse.ue,dftindex.ue,position.ue};
        branches = [repmat({'CPU'},1,6),repmat({'UE'},1,7)];
        for di = 1:numel(designs)
            design = designs{di};
            metric = evaluate_design(Htrue,truth,design,sim,sample.position);
            rows(end+1,:) = {branches{di},q.curve,q.xvalue,design.method_id,design.feedback_scope, ...
                design.cpu_estimation_dimension,q.B,q.Nant,q.SNRdB,q.KdB,sid, ...
                metric.position_error_m,metric.throughput_Mbps,design.feedback_bits, ...
                design.coordinate_bits_x,design.coordinate_bits_y,sample.position(1),sample.position(2), ...
                design.estimated_position(1),design.coordinate_bits_z,sample.position(3), ...
                design.estimated_position(2),design.estimated_position(3),jsonencode(design.raw_position), ...
                jsonencode(design.continuous_frequency),jsonencode(design.space_message),design.overflow, ...
                'UPA',net.Nside}; %#ok<AGROW>
        end
    end
    fprintf('单流 400 MHz: %s %d/%d，%.1f 秒\n',q.curve,si,numel(settings),toc(started));
end

names = {'branch','curve','x_value','method','feedback_scope','cpu_estimation_dimension', ...
    'B','antenna_count','observation_SNR_dB','Rician_K_dB','sample_id', ...
    'position_error_m','throughput_Mbps','feedback_bits','coordinate_bits_x','coordinate_bits_y', ...
    'true_x_m','true_y_m','estimated_x_m','coordinate_bits_z','true_z_m', ...
    'estimated_y_m','estimated_z_m','position_before_coordinate_quantization','frequency_unquantized', ...
    'space_message','quantizer_overflow','array','UPA_side'};
trials = cell2table(rows,'VariableNames',names);
writetable(trials,fullfile(out,'single_stream_trials.csv'));
summary = summarize_trials(trials);
writetable(summary,fullfile(out,'single_stream_summary.csv'));

contract = struct('task','UPA单极化单流','version',sim.task_id,'array','UPA','default_shape',[32 32], ...
    'POS_input','continuous HAQSE frequency -> UE 3D position -> integer coordinate message', ...
    'POS_frequency_quantization',false,'coordinate_bits',[13 14 9],'AP_phase_bits',sim.UE_phase_bits, ...
    'baseline_status','local-energy TypeI/II and Docomo structure retained; only 2D spatial-codebook adaptation', ...
    'bandwidth_model','narrowband spectral efficiency times 400MHz; not OFDM', ...
    'sample_ids',sampleIds,'settings',settings,'bandwidth_Hz',sim.bandwidth_Hz,'streams',1, ...
    'samples',numel(sampleIds),'reference_AP_count',3,'partial_feedback_methods',{{'HAQSE','DFT-index','位置反馈'}}, ...
    'full_feedback_baselines',{{'Type-I','Type-II','Docomo结构适配（仅 UE）','完美 CSI SVD 上界'}}, ...
    'curves',{{'定位误差-SNR','定位误差-天线数','定位误差-AP数','吞吐量-SNR','吞吐量-天线数','吞吐量-莱斯因子','比特数-AP数'}}, ...
    'CPU_note','R=3固定参考消息来源数；CPU重构矩阵为4×BN，并非固定计算维度。', ...
    'UE_note','UE 使用本地观测 CSI 计算 AP 间共相位；IDEAL_SVD 使用完美 CSI，仅作性能上界。', ...
    'docomo_note','Docomo 采用本地 4 倍过采样 DFT、QPSK beta、AP 逻辑栅格 DFT 和三轮交替更新。对 B=5:10 以 QPSK 坐标更新代替原文仅适用于小 B 的全枚举。', ...
    'status','complete','elapsed_seconds',toc(started));
write_json(fullfile(out,'experiment_contract.json'),contract);
if opt.MakeFigures
    plot_single_stream_task2(out);
end
audit = struct('status','complete','output_directory',out,'records',height(trials),'array','UPA','streams',1,'POS_coordinate_bits',[13 14 9], ...
    'POS_frequency_quantization',false,'coordinate_overflow_records',sum(trials.quantizer_overflow), ...
    'samples',numel(sampleIds),'settings',numel(settings),'bandwidth_Hz',sim.bandwidth_Hz, ...
    'elapsed_seconds',toc(started));
write_json(fullfile(out,'audit.json'),audit);
end

function settings = make_settings(mode)
if strcmp(mode,'full')
    snrs = 20:5:40; antennas = [64 256 1024]; aps = 5:10; ks = 0:5:20;
else
    snrs = [20 30 40]; antennas = [64 256 1024]; aps = [5 8 10]; ks = [0 10 20];
end
settings = struct('curve',{},'xvalue',{},'Nant',{},'B',{},'SNRdB',{},'KdB',{});
if strcmp(mode,'verify')
    settings=[item('SNR',30,64,5,30,10),item('SNR',30,256,8,30,10), ...
              item('SNR',30,1024,8,30,10),item('SNR',30,1024,10,30,10)];return;
end
for x = snrs, settings(end+1) = item('SNR',x,1024,8,x,10); end %#ok<AGROW>
for x = antennas, settings(end+1) = item('天线数',x,x,8,30,10); end %#ok<AGROW>
for x = aps, settings(end+1) = item('AP数',x,1024,x,30,10); end %#ok<AGROW>
for x = ks, settings(end+1) = item('莱斯因子',x,1024,8,30,x); end %#ok<AGROW>
end

function q = item(curve,x,Nant,B,SNRdB,KdB)
q = struct('curve',curve,'xvalue',x,'Nant',Nant,'B',B,'SNRdB',SNRdB,'KdB',KdB);
end

function sample = make_sample(net,sim,bank,sid,KdB)
p = bank.positions(:,sid); scatter = sim.scatterer_positions_m.';
sample.position = p; sample.H = zeros(4,net.Nap,10); sample.Z = sample.H;
K = 10^(KdB/10);
for b = 1:10
    ap = net.ap_elements(:,:,b); los = zeros(4,net.Nap); nlos = los;
    for u = 1:4
        user = p + net.ue_offsets(:,u); r = vecnorm(ap-user);
        los(u,:) = exp(-1j*net.k*r)./r;
        for ell = 1:6
            L = vecnorm(ap-scatter(:,ell)) + norm(scatter(:,ell)-user);
            nlos(u,:) = nlos(u,:) + bank.zeta(sid,ell)*exp(-1j*net.k*L)./L;
        end
    end
    nlos = nlos*norm(los,'fro')/norm(nlos,'fro');
    sample.H(:,:,b) = sqrt(K/(K+1))*los + sqrt(1/(K+1))*nlos;
    rng(bank.noise_seed(sid,b),'twister');
    sample.Z(:,:,b) = (randn(4,net.Nap)+1j*randn(4,net.Nap))/sqrt(2);
end
end

function [Htrue,Hobs] = observe_sample(sample,ids,snr)
Htrue = reshape(sample.H(:,:,ids),4,[]); Z = reshape(sample.Z(:,:,ids),4,[]);
noiseVariance = mean(abs(Htrue(:)).^2)/10^(snr/10);
Hobs = Htrue + sqrt(noiseVariance)*Z;
end

function [type1,type2,docomo,ideal] = full_feedback_design(net,Hobs,truth,B,Q)
% Preserve this runner's local-energy Type-I/II selection; adapt the codebook to 2D.
% 后续使用量化 AP 间相位。全部索引和量化系数都计入 feedback_bits。
F1 = zeros(net.Nap,B);
F2 = zeros(net.Nap,B);

for slot = 1:B
    ix = (slot-1)*net.Nap + (1:net.Nap);
    Hb = Hobs(:,ix);
    G=sstr.codebook_responses(net,Hb,net.M);
    [~,order] = sort(sum(abs(G).^2,1),'descend');
    pair=sstr.local_beams(net,order(1:2)-1,net.M);
    F1(:,slot) = pair(:,1);
    [~,~,v] = upa.principal(Hb);
    a1 = F1(:,slot)'*v; a2 = pair(:,2)'*v;
    amp = round(7*min(1,abs(a2)/max(abs(a1),realmin)))/7;
    phase = 2*pi*mod(round(angle(a2*conj(a1))*4/(2*pi)),4)/4;
    f = F1(:,slot) + amp*exp(1j*phase)*pair(:,2);
    F2(:,slot) = f/norm(f);
end
c1 = greedy_qpsk_phases(Hobs,F1,Q);
c2 = greedy_qpsk_phases(Hobs,F2,Q);
type1 = design('TYPE_I','全反馈（UE-CSI）',B*net.index_bits+(B-1)*Q,F1,c1,nan(3,1),B,NaN,NaN);
type2 = design('TYPE_II','全反馈（UE-CSI）',2*B*net.index_bits+5*B+(B-1)*Q,F2,c2,nan(3,1),B,NaN,NaN);
docomo = docomo_design(net,Hobs,B);
ideal = design('IDEAL_SVD','全反馈',NaN,[],[],nan(3,1),-1,NaN,NaN);
ideal.w = truth.v; ideal.feedback_scope = '全反馈';
end

function [haqse,dftindex,pos] = partial_designs(net,Hobs,ids,refs,sim)
[pred,diag]=sstr.space_messages(net,Hobs,ids,refs,sim.frequency_bits_per_dimension);
haqse=finish(pred.HAQSE,6);dftindex=finish(pred.DFT,6);pos=finish(pred.POS,3);
 function pair=finish(p,dimension)
  bits=nan(3,1);overflow=false;raw=p.position;
  if strcmp(p.direction_message.method,'POS')
   bits=p.direction_message.coordinate_bits;overflow=diag.quantizer_overflow;raw=diag.position_unquantized;
  end
  pair=paired_design(net,Hobs,ids,p.F,p.position,p.localization.condition,p.method_id, ...
      p.direction_bits,dimension,sim.UE_phase_bits,bits(1),bits(2));
  for branch={'cpu','ue'}
   name=branch{1};pair.(name).coordinate_bits_z=bits(3);pair.(name).raw_position=raw;
   pair.(name).continuous_frequency=diag.frequency_unquantized;
   pair.(name).space_message=p.direction_message;pair.(name).overflow=overflow;
  end
 end
end

function pair = paired_design(net,Hobs,ids,F,p,condition,method,bits,dimension,Q,bx,by)
B = numel(ids); Hmodel = geometry_channel(net,p,ids); [~,~,vmodel] = upa.principal(Hmodel);
[~,~,vobs] = upa.principal(Hobs);
ccpu = co_phases(F,vmodel,net.Nap,Inf); cue = co_phases(F,vobs,net.Nap,Q);
pair.cpu = design(method,'部分反馈',bits,F,ccpu,p,dimension,bx,by);
pair.cpu.localization_condition = condition;
pair.ue = design(method,'部分反馈',bits+(B-1)*Q,F,cue,p,dimension,bx,by);
pair.ue.localization_condition = condition;
end

function d = design(method,scope,bits,F,c,p,dimension,bx,by)
d = struct('method_id',method,'feedback_scope',scope,'feedback_bits',bits, ...
    'F',F,'c',c,'w',[],'estimated_position',p,'cpu_estimation_dimension',dimension, ...
    'coordinate_bits_x',bx,'coordinate_bits_y',by,'coordinate_bits_z',NaN, ...
    'raw_position',nan(3,1),'continuous_frequency',[],'space_message',struct,'overflow',false,'localization_condition',NaN);
if ~isempty(F), d.w = reshape(F.*reshape(c,1,[]),[],1)/sqrt(size(F,2)); end
end

function c = greedy_qpsk_phases(H,F,Q)
% 与 Type-I 参考实现一致：固定第一个 AP，按 AP 次序贪婪地选量化相位。
B = size(F,2); Heff = zeros(size(H,1),B);
for slot = 1:B
    ix = (slot-1)*size(F,1)+(1:size(F,1));
    Heff(:,slot) = H(:,ix)*F(:,slot);
end
L = 2^Q; alphabet = exp(1j*2*pi*(0:L-1)/L); c = ones(B,1);
acc = Heff(:,1);
for slot = 2:B
    trials = acc + Heff(:,slot)*alphabet;
    [~,best] = max(sum(abs(trials).^2,1));
    c(slot) = alphabet(best); acc = trials(:,best);
end
end

function d = docomo_design(net,Hobs,B)
% Docomo structure adaptation to a 2D local UPA codebook; AP logical DFT unchanged.
% 本地 4 倍过采样 DFT、QPSK beta、AP 逻辑栅格 DFT，以及 beta/v/f 交替更新。
% 原 simulate_proposed 对 beta 全枚举 4^(B-1)；此处 B=5:10，采用坐标更新。
Mlocal = net.M;
G = cell(B,1); index = ones(B,1);
for slot = 1:B
    ix = (slot-1)*net.Nap+(1:net.Nap); G{slot} = sstr.codebook_responses(net,Hobs(:,ix),Mlocal);
    [~,index(slot)] = max(sum(abs(G{slot}).^2,1));
end
V = ap_grid_dft_basis(B); beta = ones(B,1);
[~,best] = max(arrayfun(@(k) docomo_power(G,index,beta,V(:,k)),1:B));
v = V(:,best);
for outer = 1:3
    beta = docomo_beta_update(G,index,beta,v);
    [~,best] = max(arrayfun(@(k) docomo_power(G,index,beta,V(:,k)),1:B));
    v = V(:,best);
    total = docomo_effective_channel(G,index,beta,v);
    for slot = 1:B
        old = beta(slot)*v(slot)*G{slot}(:,index(slot));
        residual = total-old;
        trials = residual + beta(slot)*v(slot)*G{slot};
        [~,index(slot)] = max(sum(abs(trials).^2,1));
        total = residual + beta(slot)*v(slot)*G{slot}(:,index(slot));
    end
end
F = zeros(net.Nap,B);
for slot = 1:B, F(:,slot) = sstr.local_beams(net,index(slot)-1,Mlocal); end
% design() 以 sqrt(B) 归一化，因此将 AP 栅格 DFT 的 1/sqrt(B) 还原到 c。
c = sqrt(B)*beta.*v;
bits = B*ceil(log2(Mlocal*Mlocal)) + 2*(B-1) + ceil(log2(B));
d = design('DOCOMO_NFLOS','全反馈（UE-CSI）',bits,F,c,nan(3,1),B,NaN,NaN);
end

function V = ap_grid_dft_basis(B)
% 当前活动 AP 的个数可变且不总是矩形网格，按 active_order 建立一维逻辑栅格。
n = (0:B-1).'; V = exp(1j*2*pi*n*(0:B-1)/B)/sqrt(B);
end

function power = docomo_power(G,index,beta,v)
h = docomo_effective_channel(G,index,beta,v); power = sum(abs(h).^2);
end

function h = docomo_effective_channel(G,index,beta,v)
h = zeros(size(G{1},1),1);
for slot = 1:numel(G)
    h = h + beta(slot)*v(slot)*G{slot}(:,index(slot));
end
end

function beta = docomo_beta_update(G,index,beta,v)
% beta(1)=1；其余 AP 依序在 QPSK 上做坐标最大化。
h = docomo_effective_channel(G,index,beta,v);
alphabet = exp(1j*pi/2*(0:3));
for slot = 2:numel(G)
    residual = h-beta(slot)*v(slot)*G{slot}(:,index(slot));
    trials = residual + v(slot)*G{slot}(:,index(slot))*alphabet;
    [~,best] = max(sum(abs(trials).^2,1));
    beta(slot) = alphabet(best); h = trials(:,best);
end
end

function H = geometry_channel(net,p,ids)
H = zeros(4,numel(ids)*net.Nap);
for slot = 1:numel(ids)
    b = ids(slot); delta = net.pb(:,b)-p; r = norm(delta); q = delta/r; ql = net.R(:,:,b)'*q;
    ix = (slot-1)*net.Nap+(1:net.Nap);
    H(:,ix) = exp(-1j*net.k*r)/r*exp(1j*net.k*net.ue_offsets.'*q)*exp(-1j*net.k*ql.'*net.local);
end
end

function c = co_phases(F,v,N,Q)
B = size(F,2); a = zeros(B,1);
for slot = 1:B, ix = (slot-1)*N+(1:N); a(slot) = F(:,slot)'*v(ix); end
theta = angle(exp(1j*(angle(a)-angle(a(1)))));
if isinf(Q), c = exp(1j*theta); else, L = 2^Q; c = exp(1j*2*pi*mod(round(theta*L/(2*pi)),L)/L); end
end

function metric = evaluate_design(H,truth,d,sim,truePosition)
metric.position_error_m = NaN;
if all(isfinite(d.estimated_position)), metric.position_error_m = norm(d.estimated_position-truePosition); end
power = norm(H*d.w)^2; metric.throughput_Mbps = sim.bandwidth_Hz/1e6*log2(1+sim.rho_data*power);
assert(abs(norm(d.w)^2-1)<1e-9);
if ~isempty(d.F)
    B=size(d.F,2);powerByAP=sum(reshape(abs(d.w).^2,size(d.F,1),B),1);
    assert(max(abs(powerByAP-1/B))<1e-10);
end
assert(power <= truth.s2*(1+1e-8));
end

function summary = summarize_trials(t)
keys = {'branch','curve','x_value','method','feedback_scope','cpu_estimation_dimension','B','antenna_count','observation_SNR_dB','Rician_K_dB'};
[g,summary] = findgroups(t(:,keys));
summary.samples = splitapply(@numel,t.sample_id,g);
summary.mean_position_error_m = splitapply(@(x) mean(x,'omitnan'),t.position_error_m,g);
summary.mean_throughput_Mbps = splitapply(@mean,t.throughput_Mbps,g);
summary.mean_feedback_bits = splitapply(@(x) mean(x,'omitnan'),t.feedback_bits,g);
end

function write_json(path,value)
fid = fopen(path,'w'); assert(fid>0);
fwrite(fid,jsonencode(value),'char'); fclose(fid);
end

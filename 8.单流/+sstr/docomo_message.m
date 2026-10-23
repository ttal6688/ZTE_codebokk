function msg = docomo_message(net,Hobs,active)
B=numel(active);
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
msg=struct('protocol','SSTR_V2','method','DOCOMO_NFLOS','mode','DOCOMO', ...
 'space',struct('beam_indices',reshape(index-1,1,[]),'beta_indices', ...
 mod(round(angle(beta(2:end))*2/pi),4),'ap_dft_index',best-1),'phase_indices',[]);
% best is the AP DFT column selected immediately before the local-beam sweep.

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

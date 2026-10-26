function plot_snr_revision400(resultDir)
% Current 400-position figures, kept in new paths to avoid stale GitHub images.
root=fileparts(mfilename('fullpath'));
if nargin<1,resultDir=fullfile(root,'results','upa_snr_revision400_20261025');end
S=readtable(fullfile(resultDir,'experiment_summary.csv'),'TextType','string');
P=readtable(fullfile(resultDir,'paired_gain_summary.csv'),'TextType','string');
D=readtable(fullfile(resultDir,'position_diagnostics_summary.csv'),'TextType','string');
pairFile=fullfile(root,'results','dual_stream_full400','cases','case_03','single_dual_pairs.csv');
if ~exist(pairFile,'file'),gunzip([pairFile '.gz'],fileparts(pairFile));end
Pairs=readtable(pairFile,'TextType','string');
geo=["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
methods=["IDEAL_SVD" "TYPE_I" "TYPE_II" "DOCOMO_NFLOS" geo];
for ns=1:2
 if ns==1,stream='single';else,stream='dual';end
 for branch=["CPU" "UE"]
  tb=panel(S,branch);tb=tb(tb.stream_count==ns,:);pb=panel(P,branch);
  out=fullfile(resultDir,'figures',stream,char(branch));if ~exist(out,'dir'),mkdir(out);end
  for model=["LOS" "MIX"]
   tm=tb(tb.channel_model==model,:);pm=pb(pb.channel_model==model,:);
   for curve=["SNR" "天线数" "AP数"]
    q=tm(tm.curve==curve,:);if curve=="SNR",q=q(ismember(q.x_value,-20:10:40),:);end
    render(q,geo,'mean_position_error_m','定位误差（m）',curve,out,char(model+"_定位误差_"+curve),branch,ns,curve=="SNR",false);
   end
   for curve=["SNR" "天线数" "莱斯因子"]
    q=tm(tm.curve==curve,:);if curve=="SNR",q=q(ismember(q.x_value,-20:5:20),:);end
    render(q,methods,'mean_throughput_Mbps','吞吐量（Mbps）',curve,out,char(model+"_吞吐量_"+curve),branch,ns,false,true);
   end
   q=tm(tm.curve=="SNR"&ismember(tm.x_value,-20:5:20),:);
   render(q,methods,'mean_spectral_efficiency','频谱效率（bit/s/Hz）',"SNR",out,char(model+"_频谱效率_SNR"),branch,ns,false,true);
   if ns==2
    for curve=["SNR" "天线数" "AP数" "莱斯因子"]
     q=pm(pm.curve==curve,:);r=tm(tm.curve==curve,:);
     if curve=="SNR",q=q(ismember(q.x_value,-20:5:20),:);r=r(ismember(r.x_value,-20:5:20),:);end
     render(q,methods(2:end),'mean_delta_Mbps','双流减单流吞吐量（Mbps）',curve,out,char(model+"_单双流增量_"+curve),branch,ns,false,false);
     render(r,methods(2:end),'mean_second_mode_ratio','第二模式与第一模式功率比',curve,out,char(model+"_第二模式_"+curve),branch,ns,false,false);
    end
    q=tm(tm.curve=="AP数",:);
    render(q,methods,'mean_throughput_Mbps','吞吐量（Mbps）',"AP数",out,char(model+"_吞吐量_AP数"),branch,ns,false,true);
    default=tm(tm.curve=="SNR"&tm.x_value==30,:);names=methods(2:end);vals=zeros(7,2);texts=cell(1,7);
    original=panel(S,branch);original=original(original.channel_model==model&original.curve=="SNR"&original.x_value==30,:);
    names=[names "IDEAL_SVD"];
    for j=1:numel(names)
     for count=1:2,vals(j,count)=original.mean_throughput_Mbps(original.method==names(j)&original.stream_count==count);end
     texts{j}=label(names(j),branch,2);
    end
    f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);bar(ax,vals);xticks(ax,1:7);xticklabels(ax,texts);xtickangle(ax,20);ylabel(ax,'吞吐量（Mbps）');set(ax,'FontSize',12);legend(ax,{'单流','双流'},'Location','best');grid(ax,'on');saveplot(f,out,char(model+"_默认单双流"));
    pair=panel(Pairs,branch);pair=pair(pair.channel_model==model,:);
    f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
    for method=methods(2:end)
     values=sort(pair.delta_Mbps(pair.method==method));plot(ax,values,(1:numel(values))/numel(values),'LineWidth',2,'Color',color(method),'DisplayName',label(method,branch,2));
    end
    xlabel(ax,'双流减单流吞吐量（Mbps）');ylabel(ax,'累计概率');ylim(ax,[0 1]);grid(ax,'on');set(ax,'FontSize',16);legend(ax,'Location','best','FontSize',12);saveplot(f,out,char(model+"_默认增量CDF"));
   else
    d=D(D.channel_model==model&D.K==10&ismember(D.SNR,-20:10:40),:);d.x_value=d.SNR;d.method=repmat("POS_R3",height(d),1);
    f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
    plot(ax,d.SNR,d.mean_raw_position_error_m,'-o','LineWidth',2,'DisplayName','坐标量化前');
    plot(ax,d.SNR,d.mean_position_error_m,'-o','LineWidth',2,'DisplayName','坐标解码后');
    set(ax,'YScale','log','FontSize',16);xticks(ax,-20:10:40);xlim(ax,[-20 40]);xlabel(ax,'观测 SNR（dB）');ylabel(ax,'定位误差（m）');grid(ax,'on');legend(ax,'Location','best');saveplot(f,out,char(model+"_POS量化前后_SNR"));
    d=D(D.channel_model==model&D.SNR==30,:);d=sortrows(d,'K');
    f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);plot(ax,d.K,100*d.mean_quantizer_overflow,'-o','LineWidth',2);xlabel(ax,'莱斯因子 K（dB）');ylabel(ax,'坐标量化越界比例（%）');ylim(ax,[0 100]);grid(ax,'on');set(ax,'FontSize',16);saveplot(f,out,char(model+"_POS越界比例"));
   end
  end
  q=tb(tb.channel_model=="MIX"&tb.curve=="AP数",:);
  render(q,methods(2:end),'mean_feedback_bits','每次更新反馈有效载荷（bit）',"AP数",out,'比特数_AP数',branch,ns,false,false);
 end
end
if exist(fullfile(root,'results','feedback_percentage_20261026','feedback_percentage.csv'),'file'),plot_feedback_percentage;end
end
function render(T,methods,field,yt,curve,out,name,branch,ns,logY,adaptive)
f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');values=[];
for method=methods
 q=sortrows(T(T.method==method,:),'x_value');if isempty(q),continue;end
 y=q.(field);values=[values;y(isfinite(y))]; %#ok<AGROW>
 text=label(method,branch,ns);
 plot(ax,q.x_value,y,'-o','Color',color(method),'LineWidth',2,'MarkerSize',7,'DisplayName',text);
end
if logY,set(ax,'YScale','log');end
switch curve
 case "SNR",xt='观测 SNR（dB）';xticks(ax,unique(T.x_value));xlim(ax,[min(T.x_value) max(T.x_value)]);
 case "天线数",xt='每AP UPA阵元数';xticks(ax,unique(T.x_value));
 case "AP数",xt='协作AP数';xticks(ax,5:9);xtickformat(ax,'%d');xlim(ax,[5 9]);
 otherwise,xt='莱斯因子 K（dB）';xticks(ax,unique(T.x_value));
end
xlabel(ax,xt);ylabel(ax,yt);grid(ax,'on');box(ax,'on');set(ax,'FontSize',16,'LineWidth',1.1);
if adaptive&&~isempty(values)
 lo=min(values);hi=max(values);span=max(hi-lo,1);
 pad=max(.03*abs(lo),.01*span);ylim(ax,[max(0,lo-pad) hi+.05*span]);
end
if strcmp(field,'mean_delta_Mbps'),yline(ax,0,':','HandleVisibility','off');end
legend(ax,'Location','best','FontSize',12);
saveplot(f,out,name);
end
function saveplot(f,out,name)
save_report_figure(f,out,name);
end
function T=panel(S,branch)
T=S(S.branch==branch,:);
if branch=="CPU"
 q=S(S.branch=="UE"&ismember(S.method,["TYPE_I" "TYPE_II" "DOCOMO_NFLOS"]),:);
 q.branch(:)="CPU";T=[T;q];
end
end
function text=label(method,branch,ns)
switch method
 case "IDEAL_SVD",text='最优单流SVD参考';if ns==2,text='等功率双流SVD参考';end
 case "TYPE_I",text='全反馈Type-I(UE)';case "TYPE_II",text='全反馈Type-II(UE)';
 case "DOCOMO_NFLOS",text='Docomo';if branch=="CPU",text='Docomo(UE)';end
 case "HAQSE_R3",text='空间频率';case "DFT_INDEX_R3",text='DFT索引';otherwise,text='位置反馈';
end
end
function c=color(m)
switch m
 case "IDEAL_SVD",c=[0 0 0];case "TYPE_I",c=[.8 .24 .14];case "TYPE_II",c=[.91 .55 .1];
 case "DOCOMO_NFLOS",c=[.12 .62 .63];case "HAQSE_R3",c=[.05 .38 .75];
 case "DFT_INDEX_R3",c=[.1 .6 .28];otherwise,c=[.6 .25 .72];
end
end

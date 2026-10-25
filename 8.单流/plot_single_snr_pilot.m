function plot_single_snr_pilot(resultDir)
% Separate CPU/UE and LOS/MIX; the x-axis is observation SNR only.
S=readtable(fullfile(resultDir,'single_stream_summary.csv'),'TextType','string');
C=readtable(fullfile(resultDir,'noisefree_control_summary.csv'),'TextType','string');
snrs=sort(unique(S.x_value));geo=["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
all=["IDEAL_SVD" "TYPE_I" "TYPE_II" "DOCOMO_NFLOS" geo];
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 Q=panel(S,branch);Q=Q(Q.csi~="PERFECT",:);
 for model=["LOS" "MIX"]
  for metric=["position" "throughput"]
   f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
   if metric=="position",methods=geo;field='mean_position_error_m';set(ax,'YScale','log');yl='平均定位误差（m，对数刻度）';
   else,methods=all;field='mean_throughput_Mbps';yl='平均吞吐量（Mbps）';end
   for method=methods
    q=Q(Q.channel_model==model&Q.method==method,:);q=sortrows(q,'x_value');
    plot(ax,q.x_value,q.(field),'-o','Color',color(method),'LineWidth',2,'DisplayName',label(method,branch));
   end
   format(ax,snrs,yl);if metric=="throughput",upper=Q.mean_throughput_Mbps(Q.channel_model==model&Q.method=="IDEAL_SVD");ylim(ax,[0 1.05*max(upper)]);end
   legend(ax,'Location','best','FontSize',12);save(f,out,char(branch+"_"+model+"_"+metric+"_SNR"));
  end
 end
end
out=fullfile(resultDir,'diagnostics');if ~exist(out,'dir'),mkdir(out);end
for model=["LOS" "MIX"]
 f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');set(ax,'YScale','log');
 q=S(S.branch=="CPU"&S.csi=="OBSERVED"&S.channel_model==model&S.method=="POS_R3",:);q=sortrows(q,'x_value');
 c=C(C.branch=="CPU"&C.channel_model==model&C.method=="POS_R3",:);
 plot(ax,q.x_value,q.mean_raw_position_error_m,'-o','LineWidth',2,'DisplayName','连续定位');
 plot(ax,q.x_value,q.mean_position_error_m,'-o','LineWidth',2,'DisplayName','坐标量化解码后');
 yline(ax,c.mean_raw_position_error_m,'--','LineWidth',1.5,'DisplayName','无观测噪声：连续定位');
 yline(ax,c.mean_position_error_m,'--','LineWidth',1.5,'DisplayName','无观测噪声：坐标解码后');
 format(ax,snrs,'位置反馈平均定位误差（m，对数刻度）');legend(ax,'Location','best','FontSize',12);
 save(f,out,char(model+"_POS_continuous_vs_quantized"));
end
end
function Q=panel(S,branch)
Q=S(S.branch==branch,:);
if branch=="CPU"
 for method=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS"]
  if ~any(Q.method==method),ref=S(S.branch=="UE"&S.method==method,:);ref.branch(:)="CPU";Q=[Q;ref];end %#ok<AGROW>
 end
end
end
function format(ax,snrs,y)
xlabel(ax,'CSI观测 SNR（dB）');ylabel(ax,y);xticks(ax,snrs);xlim(ax,[min(snrs) max(snrs)]);
grid(ax,'on');box(ax,'on');set(ax,'FontSize',16,'LineWidth',1.1);
end
function save(f,out,name)
exportgraphics(f,fullfile(out,[name '.png']),'Resolution',180);savefig(f,fullfile(out,[name '.fig']));close(f);
end
function text=label(method,branch)
switch method
 case "IDEAL_SVD",text='真实CSI直接SVD参考';case "TYPE_I",text='全反馈Type-I(UE)';case "TYPE_II",text='全反馈Type-II(UE)';
 case "DOCOMO_NFLOS",text='Docomo';if branch=="CPU",text='Docomo(UE)';end
 case "HAQSE_R3",text='空间频率';case "DFT_INDEX_R3",text='DFT索引';otherwise,text='位置反馈';
end
end
function c=color(method)
switch method
 case "IDEAL_SVD",c=[0 0 0];case "TYPE_I",c=[.8 .24 .14];case "TYPE_II",c=[.91 .55 .1];
 case "DOCOMO_NFLOS",c=[.12 .62 .63];case "HAQSE_R3",c=[.05 .38 .75];case "DFT_INDEX_R3",c=[.1 .6 .28];otherwise,c=[.6 .25 .72];
end
end

function plot_single_stream_task2(resultDir)
% Central V2 plotting: CPU / UE separated, Chinese labels, no figure titles.
T=readtable(fullfile(resultDir,'single_stream_trials.csv'),'TextType','string');
assert(ismember('csi',T.Properties.VariableNames),'V2 results required');
% Both models remain in CSV. Main smoke/full figures use MIX, never pool LOS/MIX.
if any(T.channel_model=="MIX"),T=T(T.channel_model=="MIX",:);end
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 all=T(T.branch==branch,:);tb=all(all.csi~="PERFECT",:);
 for curve=["SNR" "天线数" "AP数"]
  draw(tb,branch,curve,'position_error_m','定位误差（m）',out,'定位误差',true);
 end
 for curve=["SNR" "天线数" "莱斯因子"]
  draw(tb,branch,curve,'throughput_Mbps','吞吐量（Mbps）',out,'吞吐量',false);
 end
 draw(tb,branch,"AP数",'feedback_bits','每次更新反馈有效载荷（bit）',out,'比特数',false);
 draw(tb,branch,"SNR",'spectral_efficiency','频谱效率（bit/s/Hz）',out,'频谱效率',false);
 pos=tb(tb.method=="POS_R3",:);f=newfigure;ax=axes(f);hold(ax,'on');
 for field=["raw_position_error_m" "position_error_m"]
  q=aggregate(pos(pos.curve=="SNR",:),char(field));
  if field=="position_error_m",poslabel='坐标解码后';else,poslabel='坐标量化前';end
  plot(ax,q.x_value,q.value,'-o','LineWidth',2,'DisplayName',poslabel);
 end
 format(ax,'观测 SNR（dB）','位置反馈定位误差（m）');legend(ax,'Location','best');saveplot(f,out,[char(branch) '_POS量化前后']);
 f=newfigure;ax=axes(f);q=aggregate(pos(pos.curve=="莱斯因子",:),'quantizer_overflow');
 plot(ax,q.x_value,100*q.value,'-o','LineWidth',2);format(ax,'莱斯因子 K（dB）','坐标量化越界比例（%）');
 ylim(ax,[0 100]);saveplot(f,out,[char(branch) '_POS越界比例']);
 f=newfigure;ax=axes(f);hold(ax,'on');p=unique(pos(:,{'sample_id','true_x_m','coordinate_bits_x','coordinate_bits_y','coordinate_bits_z'}));
 p=sortrows(p,'true_x_m');
 for j=1:3
  fields={'coordinate_bits_x','coordinate_bits_y','coordinate_bits_z'};labels={'x坐标：固定13 bit','y坐标：固定14 bit','z坐标：固定9 bit'};
  plot(ax,p.true_x_m,p.(fields{j}),'-o','LineWidth',2,'DisplayName',labels{j});
 end
 format(ax,'真实 x 坐标（m）','坐标分配（bit）');ylim(ax,[0 16]);legend(ax,'Location','best');
 saveplot(f,out,[char(branch) '_固定坐标bit分配']);writetable(p,fullfile(out,'固定坐标bit分配.csv'));
 if branch=="UE"
  P=readtable(fullfile(resultDir,'paired_CSI.csv'),'TextType','string');
  if any(P.channel_model=="MIX"),P=P(P.channel_model=="MIX",:);end
  f=newfigure;ax=axes(f);hold(ax,'on');
  for method=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"]
   q=aggregate(P(P.method==method&P.curve=="SNR",:),'delta_Mbps');
   plot(ax,q.x_value,q.value,'-o','LineWidth',2,'Color',color(method),'DisplayName',label(method));
  end
  yline(ax,0,':','HandleVisibility','off');format(ax,'观测 SNR（dB）','完美CSI减观测CSI吞吐量（Mbps）');
  legend(ax,'Location','best','FontSize',12);saveplot(f,out,'UE_同算法CSI配对收益');
 end
end
end
function draw(T,branch,curve,field,ytext,out,stem,geo)
f=newfigure;ax=axes(f);hold(ax,'on');
if geo,methods=["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
elseif branch=="CPU",methods=["IDEAL_SVD" "TYPE_I" "TYPE_II" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
else,methods=["IDEAL_SVD" "TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];end
for method=methods
 z=T(T.curve==curve&T.method==method,:);z=z(isfinite(z.(field)),:);if isempty(z),continue;end
 q=aggregate(z,field);text=label(method);
 if branch=="CPU"&&ismember(method,["TYPE_I" "TYPE_II"]),text=[text '（UE参考）'];end
 plot(ax,q.x_value,q.value,'-o','LineWidth',2,'MarkerSize',7,'Color',color(method),'DisplayName',text);
end
switch curve
 case "SNR",xtext='观测 SNR（dB）';case "天线数",xtext='每AP UPA阵元数';
 case "AP数",xtext='协作AP数';otherwise,xtext='莱斯因子 K（dB）';
end
format(ax,xtext,ytext);legend(ax,'Location','best','FontSize',12);
saveplot(f,out,[char(branch) '_' stem '_' char(curve)]);
end
function q=aggregate(T,field)
[g,q]=findgroups(T(:,{'x_value'}));q.value=splitapply(@mean,double(T.(field)),g);q=sortrows(q,'x_value');
end
function f=newfigure
f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);
end
function format(ax,x,y)
xlabel(ax,x);ylabel(ax,y);grid(ax,'on');box(ax,'on');set(ax,'FontSize',16,'LineWidth',1.1);
end
function saveplot(f,out,name)
exportgraphics(f,fullfile(out,[name '.png']),'Resolution',180);savefig(f,fullfile(out,[name '.fig']));close(f);
end
function c=color(m)
switch m
 case "IDEAL_SVD",c=[0 0 0];case "TYPE_I",c=[.8 .24 .14];case "TYPE_II",c=[.91 .55 .1];
 case "DOCOMO_NFLOS",c=[.12 .62 .63];case "HAQSE_R3",c=[.05 .38 .75];
 case "DFT_INDEX_R3",c=[.1 .6 .28];otherwise,c=[.6 .25 .72];
end
end
function text=label(m)
switch m
 case "IDEAL_SVD",text='理想SVD上界';case "TYPE_I",text='Type-I';case "TYPE_II",text='Type-II';
 case "DOCOMO_NFLOS",text='Docomo结构适配';case "HAQSE_R3",text='HAQSE（R=3）';
 case "DFT_INDEX_R3",text='DFT索引（R=3）';otherwise,text='位置反馈（R=3）';
end
end

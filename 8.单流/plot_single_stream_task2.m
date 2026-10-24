function plot_single_stream_task2(resultDir)
% Central single/dual plotting: CPU / UE separated, Chinese labels, no titles.
if exist(fullfile(resultDir,'cases'),'dir')&&exist(fullfile(resultDir,'dual_stream_summary.csv'),'file'),plot_full_dual(resultDir);return;end
if exist(fullfile(resultDir,'dual_stream_trials.csv'),'file'),plot_dual(resultDir);return;end
if ~exist(fullfile(resultDir,'single_stream_trials.csv'),'file'),gunzip(fullfile(resultDir,'single_stream_trials.csv.gz'),resultDir);end
T=readtable(fullfile(resultDir,'single_stream_trials.csv'),'TextType','string');
assert(ismember('csi',T.Properties.VariableNames),'V2 results required');
% Both models remain in CSV. Main smoke/full figures use MIX, never pool LOS/MIX.
if any(T.channel_model=="MIX"),T=T(T.channel_model=="MIX",:);end
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 all=display_panel(T,branch);tb=all(all.csi~="PERFECT",:);
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
 if branch=="UE" && any(all.csi=="PERFECT")
  P=readtable(fullfile(resultDir,'paired_CSI.csv'),'TextType','string');
  if any(P.channel_model=="MIX"),P=P(P.channel_model=="MIX",:);end
  f=newfigure;ax=axes(f);hold(ax,'on');
  for method=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"]
   q=aggregate(P(P.method==method&P.curve=="SNR",:),'delta_Mbps');
   plot(ax,q.x_value,q.value,'-o','LineWidth',2,'Color',color(method),'DisplayName',label(method,branch));
  end
  yline(ax,0,':','HandleVisibility','off');format(ax,'观测 SNR（dB）','完美CSI减观测CSI吞吐量（Mbps）');
  legend(ax,'Location','best','FontSize',12);saveplot(f,out,'UE_同算法CSI配对收益');
 end
end

end
function plot_full_dual(resultDir)
plot_dual_positions(resultDir);
S=readtable(fullfile(resultDir,'dual_stream_summary.csv'),'TextType','string');
if ~exist(fullfile(resultDir,'single_dual_pairs.csv'),'file'),gunzip(fullfile(resultDir,'single_dual_pairs.csv.gz'),resultDir);end
P=readtable(fullfile(resultDir,'single_dual_pairs.csv'),'TextType','string');
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 methods=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
 for model=["LOS" "MIX"]
  tb=display_panel(S,branch);tb=tb(tb.channel_model==model,:);pb=display_panel(P,branch);pb=pb(pb.channel_model==model,:);
  for curve=["SNR" "天线数" "AP数" "莱斯因子"]
   if curve=="SNR",xtext='观测 SNR（dB）';elseif curve=="天线数",xtext='每AP UPA阵元数';elseif curve=="AP数",xtext='协作AP数';else,xtext='莱斯因子 K（dB）';end
   for metric=["双流吞吐量" "单双流增量" "第二模式功率比"]
    f=newfigure;ax=axes(f);hold(ax,'on');list=methods;if metric=="双流吞吐量",list=["IDEAL_SVD" methods];end
    for method=list
     if metric=="双流吞吐量"
      z=tb(tb.curve==curve&tb.method==method&tb.stream_count==2,:);[x,order]=sort(z.x_value);y=z.mean_throughput_Mbps(order);yt='双流平均吞吐量（Mbps）';
     elseif metric=="单双流增量"
      z=pb(pb.curve==curve&pb.method==method,:);[g,zx]=findgroups(z.x_value);y=splitapply(@mean,z.delta_Mbps,g);[x,order]=sort(zx);y=y(order);yt='双流减单流平均吞吐量（Mbps）';
     else
      z=tb(tb.curve==curve&tb.method==method&tb.stream_count==2,:);[x,order]=sort(z.x_value);y=z.mean_second_mode_ratio(order);yt='接收第二模式与第一模式功率比均值';
     end
     name=label(method,branch);if method=="IDEAL_SVD",name='等功率双流SVD参考';end
     plot(ax,x,y,'-o','LineWidth',2,'Color',color(method),'DisplayName',name);
    end
    if metric=="单双流增量",yline(ax,0,':','HandleVisibility','off');end
    format(ax,xtext,yt);legend(ax,'Location','best','FontSize',12);saveplot(f,out,char(branch+"_"+model+"_"+metric+"_"+curve));
   end
  end
  default=tb(tb.curve=="SNR"&tb.x_value==30,:);pd=pb(pb.curve=="SNR"&pb.x_value==30,:);
  names=[methods "IDEAL_SVD"];values=zeros(numel(names),2);labels=cell(1,numel(names));
  for j=1:numel(names)
   for ns=1:2,values(j,ns)=default.mean_throughput_Mbps(default.method==names(j)&default.stream_count==ns);end
   labels{j}=label(names(j),branch);if names(j)=="IDEAL_SVD",labels{j}='SVD参考';end
  end
  f=newfigure;ax=axes(f);bar(ax,values);xticks(ax,1:numel(names));xticklabels(ax,labels);xtickangle(ax,20);format(ax,'反馈方法','默认配置平均吞吐量（Mbps）');set(ax,'FontSize',13);legend(ax,{'单流','双流等功率'},'Location','best');saveplot(f,out,char(branch+"_"+model+"_默认单双流"));
  f=newfigure;ax=axes(f);hold(ax,'on');
  for method=methods,z=sort(pd.delta_Mbps(pd.method==method));plot(ax,z,(1:numel(z))/numel(z),'LineWidth',2,'Color',color(method),'DisplayName',label(method,branch));end
  format(ax,'默认配置双流减单流吞吐量（Mbps）','累计概率');ylim(ax,[0 1]);legend(ax,'Location','best','FontSize',12);saveplot(f,out,char(branch+"_"+model+"_默认增量CDF"));
 end
 f=newfigure;ax=axes(f);hold(ax,'on');
 displayed=display_panel(S,branch);
 for method=methods,z=displayed(displayed.channel_model=="MIX"&displayed.curve=="AP数"&displayed.method==method& displayed.stream_count==2,:);[x,order]=sort(z.x_value);plot(ax,x,z.mean_feedback_bits(order),'-o','LineWidth',2,'Color',color(method),'DisplayName',label(method,branch));end
 format(ax,'协作AP数','双流每次更新反馈有效载荷（bit）');legend(ax,'Location','best','FontSize',12);saveplot(f,out,char(branch+"_双流反馈量_AP数"));
end
end
function draw(T,branch,curve,field,ytext,out,stem,geo)
f=newfigure;ax=axes(f);hold(ax,'on');
if geo,methods=["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
elseif branch=="CPU",methods=["IDEAL_SVD" "TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
else,methods=["IDEAL_SVD" "TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];end
for method=methods
 z=T(T.curve==curve&T.method==method,:);z=z(isfinite(z.(field)),:);if isempty(z),continue;end
 q=aggregate(z,field);text=label(method,branch);
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
function text=label(m,branch)
if nargin<2,branch="";end
switch m
 case "IDEAL_SVD",text='理想SVD上界';case "TYPE_I",text='全反馈Type-I(UE)';case "TYPE_II",text='全反馈Type-II(UE)';
 case "DOCOMO_NFLOS",text='Docomo';if strcmp(branch,'CPU'),text='Docomo(UE)';end;case "HAQSE_R3",text='空间频率';
 case "DFT_INDEX_R3",text='DFT索引';otherwise,text='位置反馈';
end
end

function plot_dual(resultDir)
T=readtable(fullfile(resultDir,'dual_stream_trials.csv'),'TextType','string');
P=readtable(fullfile(resultDir,'single_dual_pairs.csv'),'TextType','string');
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 methods=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
 for model=["LOS" "MIX"]
  tb=display_panel(T,branch);tb=tb(tb.channel_model==model,:);pb=display_panel(P,branch);pb=pb(pb.channel_model==model,:);
  names=[methods "IDEAL_SVD"];values=zeros(numel(names),2);labels=cell(1,numel(names));
  for j=1:numel(names)
   for ns=1:2,values(j,ns)=mean(tb.throughput_Mbps(tb.method==names(j)&tb.stream_count==ns));end
   labels{j}=label(names(j),branch);if names(j)=="IDEAL_SVD",labels{j}='SVD参考';end
  end
  f=newfigure;ax=axes(f);bar(ax,values);xticks(ax,1:numel(names));xticklabels(ax,labels);xtickangle(ax,20);
  format(ax,'反馈方法','平均吞吐量（Mbps）');legend(ax,{'单流','双流等功率'},'Location','best');
  set(ax,'FontSize',13);saveplot(f,out,[char(branch) '_' char(model) '_单双流吞吐量']);
  for field=["delta_Mbps" "second_mode_ratio"]
   f=newfigure;ax=axes(f);hold(ax,'on');
   for method=methods
    z=sort(pb.(field)(pb.method==method));
    plot(ax,z,(1:numel(z))/numel(z),'-','LineWidth',2,'Color',color(method),'DisplayName',label(method,branch));
   end
   if field=="delta_Mbps",xtext='双流减单流吞吐量（Mbps）';stem='速率增量CDF';else,xtext='接收第二模式与第一模式功率比';stem='第二模式CDF';end
   format(ax,xtext,'累计概率');legend(ax,'Location','best','FontSize',12);ylim(ax,[0 1]);
   saveplot(f,out,[char(branch) '_' char(model) '_' stem]);
  end
 end
 f=newfigure;ax=axes(f);values=zeros(numel(methods),2);labels=cell(1,numel(methods));
 tb=display_panel(T,branch);tb=tb(tb.channel_model=="MIX",:);
 for j=1:numel(methods)
  for ns=1:2,values(j,ns)=mean(tb.feedback_bits(tb.method==methods(j)&tb.stream_count==ns));end
  labels{j}=label(methods(j),branch);
 end
 bar(ax,values);xticks(ax,1:numel(methods));xticklabels(ax,labels);xtickangle(ax,20);
 format(ax,'反馈方法','每次更新反馈有效载荷（bit）');set(ax,'FontSize',13);
 legend(ax,{'单流','双流'},'Location','best');saveplot(f,out,[char(branch) '_单双流反馈量']);
end
end

function result=display_panel(source,branch)
% Existing UE baselines are shared display references, never CPU algorithms.
result=source(source.branch==branch,:);
if strcmp(branch,'CPU')
 for method=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS"]
  if any(result.method==method),continue;end
  reference=source(source.branch=="UE"&source.method==method,:);
  if ismember('csi',reference.Properties.VariableNames),reference=reference(reference.csi~="PERFECT",:);end
  reference.branch(:)="CPU";
  if ismember('role',reference.Properties.VariableNames),reference.role(:)="UE_REFERENCE";end
  result=[result;reference]; %#ok<AGROW>
 end
end
end

function plot_dual_positions(resultDir)
source=fullfile(resultDir,'dual_position_summary.csv');
if ~exist(source,'file'),return;end
S=readtable(source,'TextType','string');
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 for model=["LOS" "MIX"]
  for curve=["SNR" "天线数" "AP数"]
   f=newfigure;ax=axes(f);hold(ax,'on');
   for method=["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"]
    q=S(S.branch==branch&S.channel_model==model&S.curve==curve&S.method==method,:);
    [x,order]=sort(q.x_value);plot(ax,x,q.mean_position_error_m(order),'-o','LineWidth',2,'Color',color(method),'DisplayName',label(method,branch));
   end
   if curve=="SNR",xtext='观测 SNR（dB）';elseif curve=="天线数",xtext='每AP UPA阵元数';else,xtext='协作AP数';end
   format(ax,xtext,'定位误差（m）');legend(ax,'Location','best','FontSize',12);
   saveplot(f,out,char(branch+"_"+model+"_定位误差_"+curve));
  end
 end
end
end

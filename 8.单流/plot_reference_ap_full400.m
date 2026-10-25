function plot_reference_ap_full400(resultDir)
root=fileparts(mfilename('fullpath'));
if nargin<1,resultDir=fullfile(root,'results','reference_ap_full400_20261025');end
S=readtable(fullfile(resultDir,'localization_summary.csv'),'TextType','string');
methods=["HAQSE" "DFT_INDEX" "POS"];labels={'空间频率','DFT索引','位置反馈'};colors=[.05 .38 .75;.1 .6 .28;.6 .25 .72];count=0;
for branch=["CPU" "UE"]
 out=fullfile(resultDir,'figures',char(branch));if ~exist(out,'dir'),mkdir(out);end
 for model=["LOS" "MIX"]
  f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
  for j=1:3
   q=sortrows(S(S.channel_model==model&S.method==methods(j),:),'R');assert(height(q)==6&&all(q.samples==400));
   plot(ax,q.R,q.mean_position_error_m,'-o','Color',colors(j,:),'LineWidth',2,'MarkerSize',7,'DisplayName',labels{j});
  end
  format(ax);legend(ax,'Location','best','FontSize',13);saveplot(f,out,char(model+"_定位误差_反馈AP数"));count=count+1;
 end
end
out=fullfile(resultDir,'figures','diagnostics');if ~exist(out,'dir'),mkdir(out);end
for model=["LOS" "MIX"]
 q=sortrows(S(S.channel_model==model&S.method=="POS",:),'R');
 f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
 plot(ax,q.R,q.mean_raw_position_error_m,'-o','LineWidth',2,'DisplayName','坐标量化前');
 plot(ax,q.R,q.mean_position_error_m,'-o','LineWidth',2,'DisplayName','坐标解码后');
 format(ax);legend(ax,'Location','best','FontSize',13);saveplot(f,out,char(model+"_坐标量化前后_反馈AP数"));
end
% Validate the four comparison figures against the independently audited means.
maximum=0;
for branch=["CPU" "UE"]
 for model=["LOS" "MIX"]
  f=openfig(fullfile(resultDir,'figures',char(branch),char(model+"_定位误差_反馈AP数.fig")),'invisible');ax=findobj(f,'Type','axes');
  assert(numel(ax)==1&&isequal(ax.XTick,3:8)&&isequal(ax.XLim,[3 8])&&~contains(ax.YLabel.String,'对数'));
  lines=findobj(ax,'Type','line');assert(numel(lines)==3);
  for j=1:3
   z=lines(strcmp({lines.DisplayName},labels{j}));q=sortrows(S(S.channel_model==model&S.method==methods(j),:),'R');
   assert(numel(z)==1&&isequal(z.XData,3:8));e=max(abs(z.YData-q.mean_position_error_m.'));assert(e<1e-12);maximum=max(maximum,e);
  end
  close(f);
 end
end
audit=struct('status','passed','comparison_figures',count,'total_figures',6,'R',3:8,'B',8,'maximum_plotted_mean_error',maximum,'Word_inspected',false);
fid=fopen(fullfile(resultDir,'figure_audit.json'),'w');fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end
function format(ax)
set(ax,'YScale','log','FontSize',16,'LineWidth',1.1);xticks(ax,3:8);xtickformat(ax,'%d');xlim(ax,[3 8]);
xlabel(ax,'定位参考／反馈AP数（协作AP数固定为8）');ylabel(ax,'定位误差（m）');grid(ax,'on');box(ax,'on');
end
function saveplot(f,out,name)
exportgraphics(f,fullfile(out,[name '.png']),'Resolution',180);savefig(f,fullfile(out,[name '.fig']));close(f);
end

function plot_reference_ap_pilot(resultDir)
S=readtable(fullfile(resultDir,'localization_summary.csv'),'TextType','string');
methods=["HAQSE" "DFT_INDEX" "POS"];labels={'空间频率','DFT索引','位置反馈'};
colors=[.05 .38 .75;.1 .6 .28;.6 .25 .72];
for branch=["CPU" "UE"]
 out=fullfile(resultDir,char(branch));if ~exist(out,'dir'),mkdir(out);end
 for model=["LOS" "MIX"]
  for scale=["linear" "log"]
   f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
   for j=1:3
    q=S(S.channel_model==model&S.method==methods(j),:);q=sortrows(q,'R');
    plot(ax,q.R,q.mean_position_error_m,'-o','LineWidth',2,'Color',colors(j,:),'DisplayName',labels{j});
   end
   if scale=="log",set(ax,'YScale','log');ylabel(ax,'平均定位误差（m，对数刻度）');
   else,ylabel(ax,'平均定位误差（m）');limits=ylim(ax);ylim(ax,[0 limits(2)]);end
   format(ax);legend(ax,'Location','best','FontSize',12);
   save(f,out,char(branch+"_"+model+"_position_reference_APs_"+scale));
  end
 end
end
out=fullfile(resultDir,'diagnostics');if ~exist(out,'dir'),mkdir(out);end
for model=["LOS" "MIX"]
 f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');set(ax,'YScale','log');
 q=S(S.channel_model==model&S.method=="POS",:);q=sortrows(q,'R');
 plot(ax,q.R,q.mean_raw_position_error_m,'-o','LineWidth',2,'DisplayName','连续定位');
 plot(ax,q.R,q.mean_position_error_m,'-o','LineWidth',2,'DisplayName','一次坐标量化解码后');
 ylabel(ax,'位置反馈平均定位误差（m，对数刻度）');format(ax);legend(ax,'Location','best','FontSize',12);
 save(f,out,char(model+"_POS_continuous_vs_quantized_reference_APs"));
end
end
function format(ax)
xlabel(ax,'定位参考AP数（协作AP数固定为8）');xticks(ax,3:8);xtickformat(ax,'%d');xlim(ax,[3 8]);
grid(ax,'on');box(ax,'on');set(ax,'FontSize',16,'LineWidth',1.1);
end
function save(f,out,name)
exportgraphics(f,fullfile(out,[name '.png']),'Resolution',180);savefig(f,fullfile(out,[name '.fig']));close(f);
end

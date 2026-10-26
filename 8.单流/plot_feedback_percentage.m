function plot_feedback_percentage
root=fileparts(mfilename('fullpath'));out=fullfile(root,'results','feedback_percentage_20261026');
T=readtable(fullfile(out,'feedback_percentage.csv'),'TextType','string');
methods=["TYPE_I" "TYPE_II" "DOCOMO_NFLOS" "HAQSE_R3" "DFT_INDEX_R3" "POS_R3"];
colors=[.8 .24 .14;.91 .55 .1;.12 .62 .63;.05 .38 .75;.1 .6 .28;.6 .25 .72];
names={'全反馈Type-I(UE)','全反馈Type-II(UE)','Docomo','空间频率','DFT索引','位置反馈'};
count=0;
for ns=1:2
 if ns==1,stream='single';else,stream='dual';end
 for branch=["CPU" "UE"]
  directory=fullfile(out,'figures',stream,char(branch),'compact_legend_v2');if ~exist(directory,'dir'),mkdir(directory);end
  f=figure('Visible','off','Color','w','Position',[100 100 1120 760]);ax=axes(f);hold(ax,'on');
  q=T(T.stream_count==ns&T.branch==branch,:);
  for j=1:6
   z=sortrows(q(q.method==methods(j),:),'B');label=names{j};if branch=="CPU"&&j==3,label='Docomo(UE)';end
   plot(ax,z.B,z.feedback_percentage,'-o','LineWidth',2,'MarkerSize',7,'Color',colors(j,:),'DisplayName',label);
  end
  xlabel(ax,'协作AP数');ylabel(ax,'相对全反馈Type-I的反馈开销（%）');
  xlim(ax,[5 9]);xticks(ax,5:9);xtickformat(ax,'%d');ylim(ax,[0 ceil(1.07*max(q.feedback_percentage)/10)*10]);ytickformat(ax,'%.0f%%');
  set(ax,'FontSize',16,'LineWidth',1.1);grid(ax,'on');box(ax,'on');
  % Fit width/height to the labels; move only the anchor into the curve gap.
  lg=legend(ax,'Location','best','FontSize',18);drawnow;lg.Units='normalized';
  position=lg.Position;position(1:2)=[.47 .52];lg.Position=position;
  save_report_figure(f,directory,'反馈开销占比_AP数');count=count+1;
  style=jsondecode(fileread(fullfile(root,'report_figure_style.json')));
  f=openfig(fullfile(directory,style.image_version,'反馈开销占比_AP数.fig'),'invisible');ax=findobj(f,'Type','axes');
  assert(isequal(ax.XLim,[5 9])&&isequal(ax.XTick,5:9));lines=findobj(ax,'Type','line');assert(numel(lines)==6);
  for j=1:6
   label=names{j};if branch=="CPU"&&j==3,label='Docomo(UE)';end
   line=lines(strcmp({lines.DisplayName},label));z=sortrows(q(q.method==methods(j),:),'B');
   assert(numel(line)==1&&isequal(line.XData,5:10)&&max(abs(line.YData-z.feedback_percentage.'))<1e-10);
  end
  lg=findall(f,'Type','legend');assert(lg.FontSize==18&&lg.Position(3)<.30);close(f);
 end
end
audit=struct('status','passed','figures',count,'methods_per_figure',6,'Type_I_reference_percentage',100,'legend_font_size_pt',18, ...
 'plotted_percentages_match_source',true,'integer_AP_ticks',5:9,'values_above_100_retained',true, ...
 'legend_layout','automatic content-sized width/height; only anchor moved into curve gap', ...
 'figure_version','compact_legend_v2','Word_inspected',false);
fid=fopen(fullfile(out,'figure_audit.json'),'w');fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end

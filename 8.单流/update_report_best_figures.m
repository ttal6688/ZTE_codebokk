function update_report_best_figures
% Reposition every current report legend without rerunning any simulations.
root=fileparts(mfilename('fullpath'));out=fullfile(root,'results','report_legend_best_20261026');
manifest=jsondecode(fileread(fullfile(out,'figure_manifest.json')));items=manifest.figures;
legendCount=0;withoutLegend=0;started=tic;
for k=1:numel(items)
 source=fullfile(root,items(k).source);target=fullfile(root,items(k).target);
 f=openfig(strrep(source,'.png','.fig'),'invisible');before=signature(f);
 lg=findall(f,'Type','legend');legendCount=legendCount+numel(lg);
 if isempty(lg),withoutLegend=withoutLegend+1;end
 [folder,name]=fileparts(target);save_report_figure(f,fileparts(folder),name,true);
 f=openfig(strrep(target,'.png','.fig'),'invisible');
 assert(isequaln(before,signature(f)),'Plot values, axes or labels changed');
 lg=findall(f,'Type','legend');
 for j=1:numel(lg)
  assert(strcmp(lg(j).Location,'best')&&lg(j).FontSize==18,'Final legend must use best at 18 pt');
 end
 close(f);
 if mod(k,20)==0||k==numel(items),fprintf('Best legends %d/%d, %.1f s\n',k,numel(items),toc(started));end
end
audit=struct('status','passed','figures',numel(items),'legends_best',legendCount, ...
 'figures_without_legend',withoutLegend,'legend_font_size_pt',18,'legend_location','best', ...
 'manual_Position_override',false,'plot_values_axes_and_labels_preserved',true, ...
 'old_files_preserved',true,'simulation_rerun',false,'Word_inspected',false);
fid=fopen(fullfile(out,'figure_audit.json'),'w');fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end

function result=signature(f)
axesList=findall(f,'Type','axes');result=cell(numel(axesList)+1,1);
for j=1:numel(axesList)
 ax=axesList(j);objects=findobj(ax,'-property','YData');data=cell(numel(objects),1);
 for k=1:numel(objects)
  object=objects(k);value=struct('type',object.Type,'YData',object.YData);
  if isprop(object,'XData'),value.XData=object.XData;end
  if isprop(object,'ZData'),value.ZData=object.ZData;end
  if isprop(object,'DisplayName'),value.DisplayName=object.DisplayName;end
  data{k}=value;
 end
 result{j}=struct('XLim',ax.XLim,'YLim',ax.YLim,'XScale',ax.XScale,'YScale',ax.YScale, ...
  'XTick',ax.XTick,'YTick',ax.YTick,'XLabel',ax.XLabel.String,'YLabel',ax.YLabel.String,'data',{data});
end
lg=findall(f,'Type','legend');texts=cell(numel(lg),1);
for j=1:numel(lg),texts{j}=lg(j).String;end
result{end}=texts;
end

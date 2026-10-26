function update_report_legend_figures
% Font-only edits of the exact current report FIG files, preserving originals.
root=fileparts(mfilename('fullpath'));out=fullfile(root,'results','report_legend18_20261026');
manifest=jsondecode(fileread(fullfile(out,'figure_manifest.json')));items=manifest.figures;
legendCount=0;withoutLegend=0;previous=[];started=tic;
for k=1:numel(items)
 source=fullfile(root,items(k).source);[folder,name]=fileparts(source);
 f=openfig(fullfile(folder,[name '.fig']),'invisible');before=signature(f);lg=findall(f,'Type','legend');
 if isempty(lg),withoutLegend=withoutLegend+1;else
  legendCount=legendCount+numel(lg);
  for j=1:numel(lg),previous(end+1)=lg(j).FontSize;end %#ok<AGROW>
 end
 save_report_figure(f,folder,name,true);
 target=fullfile(root,items(k).target);f=openfig(strrep(target,'.png','.fig'),'invisible');
 assert(isequaln(before,signature(f)),'Plot data, limits, scales, labels or legend text changed');
 lg=findall(f,'Type','legend');for j=1:numel(lg),assert(lg(j).FontSize==manifest.style.legend_font_size_pt&&strcmp(lg(j).FontUnits,'points'));end
 close(f);
 if mod(k,20)==0||k==numel(items),fprintf('Legend refresh %d/%d, %.1f s\n',k,numel(items),toc(started));end
end
assert(all(previous<manifest.style.legend_font_size_pt),'The requested font must enlarge every existing legend');
audit=struct('status','passed','figures',numel(items),'legends_enlarged',legendCount,'figures_without_legend',withoutLegend, ...
 'previous_font_range_pt',[min(previous) max(previous)],'new_font_size_pt',manifest.style.legend_font_size_pt, ...
 'plotted_values_limits_scales_labels_and_legend_text_preserved',true,'original_files_preserved',true,'simulation_rerun',false,'Word_inspected',false);
fid=fopen(fullfile(out,'legend_audit.json'),'w');fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
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
  'XLabel',ax.XLabel.String,'YLabel',ax.YLabel.String,'data',{data});
end
lg=findall(f,'Type','legend');texts=cell(numel(lg),1);for j=1:numel(lg),texts{j}=lg(j).String;end
result{end}=texts;
end

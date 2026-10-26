function save_report_figure(f,out,name,versionOnly)
% Apply one legend style to every plot, including inherited/automatic legends.
if nargin<4,versionOnly=false;end
root=fileparts(mfilename('fullpath'));style=jsondecode(fileread(fullfile(root,'report_figure_style.json')));
legends=findall(f,'Type','legend');
for j=1:numel(legends)
 set(legends(j),'FontUnits','points','FontSize',style.legend_font_size_pt);
 % Recalculate the automatic location using the final font size.
 set(legends(j),'Location','none');
 set(legends(j),'Location',style.legend_location);
end
drawnow;
versionDir=fullfile(out,style.image_version);if ~exist(versionDir,'dir'),mkdir(versionDir);end
exportgraphics(f,fullfile(versionDir,[name '.png']),'Resolution',style.resolution_dpi);
savefig(f,fullfile(versionDir,[name '.fig']));
if ~versionOnly
 copyfile(fullfile(versionDir,[name '.png']),fullfile(out,[name '.png']));
 copyfile(fullfile(versionDir,[name '.fig']),fullfile(out,[name '.fig']));
end
close(f);
end

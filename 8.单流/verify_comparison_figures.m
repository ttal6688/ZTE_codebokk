function audit=verify_comparison_figures()
% Verify presentation-only changes and equality of every shared UE curve.
root=fileparts(mfilename('fullpath'));sets={'single_stream_V3_full400','dual_stream_full400'};figures=0;lines=0;bars=0;maximum=0;
for j=1:numel(sets)
 folder=fullfile(root,'results',sets{j});files=dir(fullfile(folder,'CPU','*.fig'));
 for k=1:numel(files)
  cpuPath=fullfile(files(k).folder,files(k).name);uePath=fullfile(folder,'UE',strrep(files(k).name,'CPU_','UE_'));
  fc=openfig(cpuPath,'invisible');fu=openfig(uePath,'invisible');cleanup=onCleanup(@()close([fc fu])); %#ok<NASGU>
  for f=[fc fu]
   legends=findall(f,'Type','legend');
   for h=legends(:).'
    labels=string(h.String);assert(~any(contains(labels,{'HAQSE','结构适配','UE参考','项目Type-I','R=3'})));
    for name=["全反馈Type-I(UE)" "全反馈Type-II(UE)"]
     if any(contains(labels,extractBefore(name,'(UE)'))),assert(any(labels==name));end
    end
   end
   figures=figures+1;
  end
  c=findall(fc,'Type','line','DisplayName','Docomo(UE)');u=findall(fu,'Type','line','DisplayName','Docomo');
  if ~isempty(c)
   assert(isscalar(c)&&isscalar(u));err=max([abs(c.XData-u.XData),abs(c.YData-u.YData)]);assert(err<1e-10);maximum=max(maximum,err);lines=lines+1;
  end
  cb=findall(fc,'Type','bar');ub=findall(fu,'Type','bar');
  if ~isempty(cb)
   ca=findall(fc,'Type','axes');ua=findall(fu,'Type','axes');ci=find(string(ca.XTickLabel)=="Docomo(UE)");ui=find(string(ua.XTickLabel)=="Docomo");assert(isscalar(ci)&&isscalar(ui));
   assert(numel(cb)==numel(ub));for z=1:numel(cb),err=abs(cb(z).YData(ci)-ub(z).YData(ui));assert(err<1e-10);maximum=max(maximum,err);end
   bars=bars+1;
  end
  if j==2 && ~contains(files(k).name,'定位误差')
   assert(~isempty(c)||~isempty(cb),'Every full CPU dual performance comparison must show Docomo(UE)');
   if isempty(cb)
    for name=["全反馈Type-I(UE)" "全反馈Type-II(UE)"]
     assert(~isempty(findall(fc,'Type','line','DisplayName',name)));
    end
   else
    labels=string(ca.XTickLabel);assert(all(ismember(["全反馈Type-I(UE)" "全反馈Type-II(UE)"],labels)));
   end
  end
  if j==1 && any(contains(files(k).name,{'吞吐量','比特数','频谱效率'})),assert(~isempty(c));end
  clear cleanup
 end
end
assert(figures==92&&lines==32&&bars==2);
audit=struct('status','passed','figures_checked',figures,'CPU_shared_reference_line_plots',lines,'CPU_shared_reference_bar_plots',bars, ...
 'maximum_Docomo_CPU_vs_UE_curve_difference',maximum,'labels',{{'全反馈Type-I(UE)','全反馈Type-II(UE)','空间频率','DFT索引','位置反馈','Docomo','Docomo(UE)'}});
fid=fopen(fullfile(root,'docs','图例及CPU参考图形核验.json'),'w');fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end

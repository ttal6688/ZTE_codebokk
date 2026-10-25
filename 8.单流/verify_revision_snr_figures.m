function verify_revision_snr_figures
% Check scientific axes and actual plotted data, without opening Word files.
root=fileparts(mfilename('fullpath'));out=fullfile(root,'results','upa_snr_revision400_20261025');
S=readtable(fullfile(out,'experiment_summary.csv'),'TextType','string');count=0;maximum=0;
for ns=1:2
 if ns==1,stream='single';else,stream='dual';end
 for branch=["CPU" "UE"]
  tb=S(S.stream_count==ns&S.branch==branch,:);
  if branch=="CPU"
   q=S(S.stream_count==ns&S.branch=="UE"&ismember(S.method,["TYPE_I" "TYPE_II" "DOCOMO_NFLOS"]),:);tb=[tb;q];
  end
  for model=["LOS" "MIX"]
   for stem=["定位误差" "吞吐量"]
    if stem=="定位误差",xs=-20:10:40;field='mean_position_error_m';else,xs=-20:5:20;field='mean_throughput_Mbps';end
    name=fullfile(out,'figures',stream,char(branch),char(model+"_"+stem+"_SNR.fig"));f=openfig(name,'invisible');
    ax=findobj(f,'Type','axes');assert(numel(ax)==1&&~contains(ax.YLabel.String,'对数'));lines=findobj(ax,'Type','line');
    expected=tb(tb.channel_model==model&tb.curve=="SNR"&ismember(tb.x_value,xs),:);
    if stem=="定位误差",expected=expected(ismember(expected.method,["HAQSE_R3" "DFT_INDEX_R3" "POS_R3"]),:);end
    assert(numel(lines)==numel(unique(expected.method))&&isequal(ax.XTick,xs)&&isequal(ax.XLim,[xs(1) xs(end)]));
    remaining=unique(expected.method);
    for j=1:numel(lines)
     assert(isequal(lines(j).XData,xs));best=inf;chosen='';
     for m=remaining.'
      z=sortrows(expected(expected.method==m,:),'x_value');e=max(abs(lines(j).YData-z.(field).'));
      if e<best,best=e;chosen=m;end
     end
     assert(best<1e-9);maximum=max(maximum,best);remaining(remaining==chosen)=[];
    end
    if stem=="吞吐量"
     lo=min(expected.(field));hi=max(expected.(field));span=max(hi-lo,1);lower=max(0,lo-max(.03*abs(lo),.01*span));
     assert(strcmp(ax.YScale,'linear')&&abs(ax.YLim(1)-lower)<1e-9&&ax.YLim(2)>hi);
    end
    close(f);count=count+1;
   end
  end
 end
end
audit=struct('status','passed','SNR_figures',count,'maximum_plotted_value_difference',maximum, ...
 'location_SNR',-20:10:40,'throughput_SNR',-20:5:20,'throughput_minimum_adaptive',true,'Word_inspected',false);
fid=fopen(fullfile(out,'SNR_figure_audit.json'),'w');fwrite(fid,jsonencode(audit),'char');fclose(fid);disp(audit);
end

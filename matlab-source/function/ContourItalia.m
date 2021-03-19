% ContourItalia gives back boudaries for one or all the italian regions.
% Usage:
%       LatLon = ContourItalia(Regions);
% Input:
%       Regions: string vector with the names of the regions
%                Es: Regions = strvcat('Abruzzo','Campania','Lazio');
%                   'All' would load all the regions
% Output:
%       LatLon: a structure with lat and lon of boundaries
% 
% Nico, Jan 2009
%
% History
% 15/01/2009 - First version 

function OUT = ContourItalia(Regions)

load C:\Matools\REGIONI\MFILES\REGIONI.mat

if strcmp(Regions,'All');

 Regions = ...
 ['Abruzzo      ';...
  'Basilicata   ';... 
  'Calabria     ';... 
  'Campania     ';...  
  'EmiliaRomagna';...
  'Friuli       ';...
  'Lazio        ';...  
  'Liguria      ';...
  'Lombardia    ';... 
  'Marche       ';...
  'Molise       ';...
  'Piemonte     ';...
  'Puglia       ';...
  'Sardegna     ';...
  'Sicilia      ';...
  'Toscana      ';...
  'Trentino     ';...
  'Umbria       ';...
  'ValledAosta  ';...
  'Veneto       '];

end

OUT = struct('lat',[],'lon',[]);

for ir = 1:length(Regions(:,1));

    eval(['OUT.lat = [OUT.lat; NaN; ' deblank(Regions(ir,:)) '.lat];']);
    eval(['OUT.lon = [OUT.lon; NaN; ' deblank(Regions(ir,:)) '.lon];']);

end

return
## Split HDM4 export for Zambia using mile markers
# %%
import pandas as pd
import re
from shapely import ops, wkt
from shapely.geometry import *

#%% Read Zambia HDM4 export
hdm4_export = "../data/ZMB/zambia-2017-paved-hdm4.csv"
df = pd.read_csv(hdm4_export)
df

# %% Parse out road name an mile markers from LINK_NAME
link_rx = '(?P<ROAD_NAME>\w+)_(?P<ROAD_TAG>\d+):(?P<SECT_START>\d+)-(?P<SECT_END>\d+)'
parsed_road_df = df['LINK_NAME'].str.extract(link_rx ,expand=True)

#%% Trim road name (ex: T006 -> T6)
def trim_road_name(s):
    (prefix, number) = re.match(r'(\w+?)(\d+)', s).groups()
    return f'{prefix}{int(number)}'

parsed_road_df['ROAD_NAME'] = \
    parsed_road_df['ROAD_NAME'].apply(trim_road_name)
parsed_road_df

# %% Load OSM roads from Geofrabik extract
import geopandas as gpd
osm_roads_shp = "../data/ZMB/zambia-latest-free.shp/gis_osm_roads_free_1.shp"
zmb_roads_gdf = gpd.read_file(osm_roads_shp, layer='gis_osm_roads_free_1')
zmb_roads_gdf

#%% Test Case, Pull out T6
xdf = zmb_roads_gdf[zmb_roads_gdf['ref']=='T6']
segments = list(xdf['geometry'])


t6 =ops.linemerge(segments)
ss = t6.geoms
ops.snap(ss[0], ss[1], 0.1)
t6

#%% substring
def round_geom_precision(g, precision):
    s = wkt.dumps(g, rounding_precision=precision)
    return wkt.loads(s)

def shared_points(line: LineString)-> list:
    xys = line.xy
    head = Point(xys[0][0], xys[1][0])
    tail = Point(xys[0][-1], xys[1][-1])
    return [wkt.dumps(head), wkt.dumps(tail)]

# enter geoms by their shared points
# find first shared point that has two geoms
# take those geometries, remove them from all shared points dict
# merge them with ops.linemerge and re-index new geometry
# until ther is nothing shared
#
# ops.linemerge will always work between 2 touching lines, not with all 3
# if lines reverse winding/direction they will not be merged

dd = {}
for seg in ss:
    for sp in shared_points(seg):
        v = dd.get(sp,[])
        v.append(seg)
        dd[sp] = v

{ k:len(v) for (k,v) in dd.items()}

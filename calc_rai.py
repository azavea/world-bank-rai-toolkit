## Calculate RIA for Guatemala
# %%
import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd
from matplotlib import pyplot

def show_me(imgLr, imgRr):
    import matplotlib.pyplot as plt
    f = plt.figure()
    f.add_subplot(1,2, 1)
    plt.imshow(imgLr)
    f.add_subplot(1,2, 2)
    plt.imshow(imgRr)
    plt.show(block=True)

pfix="py"
code="pry"
cname="paraguay"
#utm_epsg=32615 #for GTM
utm_epsg=32721 #for PRY

#%% Load GADM
gadm = gpd.read_file(
    f"data/inputs/gadm36_{code}.gpkg",
    layer='gadm36_GTM_0')
border = gadm['geometry'][0]

#%% Load GRUMP
grump = gpd.read_file(
    "data/inputs/grump-v1-urban-ext-polygons-rev02-shp/global_urban_extent_polygons_v1.01.shp")

#%% Filter Grump to urbang areas intersecting GTM
grump_df = grump[grump.intersects(border)]
grump  = list(grump_df['geometry'])

#%% Load WorldPop dataset
worldpop = rasterio.open(f"data/inputs/{code}_ppp_2020.tif")

worldpop_img = worldpop.read(1)
pyplot.imshow(worldpop_img)

#%% Mask WorldPop by GRUMP
rural_pop, out_transform = rasterio.mask.mask(worldpop, grump, crop=False, invert=True)
rural_pop = rural_pop[0,:,:]

with rasterio.Env():
    with rasterio.open(f'data/{code}/worldpop_rural.tif', 'w', **worldpop.profile) as dst:
        dst.write(rural_pop, 1)

show_me(worldpop_img, rural_pop)

#%% Load high quality roads from OSM
osm_df = gpd.read_file(
    f'data/inputs/{cname}-latest-free.shp/gis_osm_roads_free_1.shp')

#%% Filter OSM roads to only primary and secondary, assume those are all weather
osm_df = osm_df[osm_df['fclass'].isin(['primary', 'secondary'])]
osm_df.plot()
#%% Read Good matches extracted from GTM HDM4 records
hdm4_df = gpd.read_file(f'data/{code}/{pfix}_good_matches.gpkg').set_crs(epsg=4326)
hdm4_df.plot()

#%% Buffer road dataframe by 2KM
fair_roads = hdm4_df[hdm4_df['roughness'] <= 5.0]
hdm4_buffers = fair_roads.to_crs(epsg=utm_epsg).buffer(2000).to_crs(epsg=4326)
osm_buffers = osm_df.to_crs(epsg=utm_epsg).buffer(2000).to_crs(epsg=4326)

#%% Mask WorldPop by roads
buffers = list(hdm4_buffers) + list(osm_buffers) + grump
rai_pop, out_transform = rasterio.mask.mask(worldpop, buffers, crop=False, invert=True)
rai_pop = rai_pop[0,:,:]

show_me(worldpop_img, rai_pop)
#%%
with rasterio.Env():
    with rasterio.open(f'data/{code}/worldpop_rai.tif', 'w', **worldpop.profile) as dst:
        dst.write(rai_pop, 1)

#%% Calculate RAI
smash_nodata = np.vectorize(lambda v: v if v > 0 else 0)
gtm_rai = 1 - np.sum(smash_nodata(rai_pop)) / np.sum(smash_nodata(rural_pop))
gtm_rai

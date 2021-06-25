# Calculate RAI for Guatemala
# %%
import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union


def show_me(imgLr, imgRr):
    f = plt.figure()
    f.add_subplot(1, 2, 1)
    plt.imshow(imgLr)
    plt.axis('off')
    f.add_subplot(1, 2, 2)
    plt.imshow(imgRr)
    plt.axis('off')
    plt.show(block=True)


# pfix = "py"
# code = "PRY"
# cname = "paraguay"
# utm_epsg = 32721  # for PRY
# iri_col = 'roughness'

pfix = "gt"
code = "GTM"
cname = "guatemala"
utm_epsg = 32615  # for GTM
iri_col = 'iri'

# %% Load GADM
gadm = gpd.read_file(
    f"data/inputs/gadm36_{code}.gpkg", layer=f'gadm36_{code}_0')
border = gadm['geometry'][0]
border

# %% Load GRUMP
grump_df = gpd.read_file(("data/inputs/grump-v1-urban-ext-polygons-rev02-shp/"
                          "global_urban_extent_polygons_v1.01.shp"))

# Filter Grump to urban areas intersecting GTM
grump_df = grump_df[grump_df.intersects(border)]
grump = list(grump_df['geometry'])
grump_df.plot()

# %% Load WorldPop dataset
worldpop = rasterio.open(f"data/inputs/{code.lower()}_ppp_2020.tif")

worldpop_img = worldpop.read(1)
plt.imshow(worldpop_img)

# %% Mask WorldPop by GRUMP
rural_pop_img, out_transform = rasterio.mask.mask(
    worldpop, grump, crop=False, invert=True)
rural_pop_img = rural_pop_img[0, :, :]

# with rasterio.Env():
#     with rasterio.open(f'data/{code}/{code}_worldpop_rural.tif', 'w',
#                        **worldpop.profile) as dst:
#         dst.write(rural_pop_img, 1)

show_me(worldpop_img, rural_pop_img)

# %% Load high quality roads from OSM
osm_df = gpd.read_file(
    f'data/inputs/{cname}-latest-free.shp/gis_osm_roads_free_1.shp')

# Filter OSM roads to only primary and secondary, assume those are all
# weather
# osm_df = osm_df[osm_df['fclass'].isin(['primary', 'secondary'])]
osm_df = osm_df[osm_df['fclass'].isin([
    'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary',
    'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link'
])]
osm_df.plot()

osm_buffers = osm_df.to_crs(epsg=utm_epsg).buffer(2000).to_crs(epsg=4326)
osm_buffers.plot()

# %% Read Good matches extracted from HDM4 records
# hdm4_df = gpd.read_file(f'data/{code}/{pfix}_good_matches.gpkg').set_crs(
#     epsg=4326)
hdm4_df = gpd.read_file(f'data/{code}/{pfix}_good_matches.gpkg')
hdm4_df.plot()

# Buffer road dataframe by 2KM
fair_roads_df = hdm4_df[hdm4_df[iri_col] <= 5.0]
fair_roads_df.plot()

hdm4_buffers = fair_roads_df.to_crs(epsg=utm_epsg).buffer(2000).to_crs(
    epsg=4326)
hdm4_buffers.plot()

# %% Mask WorldPop by roads
# buffers = list(hdm4_buffers) + list(osm_buffers) + grump
buffers = unary_union(hdm4_buffers.geometry.to_list() +
                      osm_buffers.geometry.to_list() + grump)
unserved_pop_img, out_transform = rasterio.mask.mask(
    worldpop, buffers, crop=False, invert=True)
unserved_pop_img = unserved_pop_img[0, :, :]

show_me(rural_pop_img, unserved_pop_img)

# %%
# with rasterio.Env():
#     with rasterio.open(f'data/{code}/{code}_worldpop_rai.tif', 'w',
#                        **worldpop.profile) as dst:
#         dst.write(unserved_pop_img, 1)

# %% Calculate RAI
# smash_nodata = np.vectorize(lambda v: v if v > 0 else 0, otypes=[])
# rural_pop = np.sum(smash_nodata(rural_pop_img))
# unserved_pop = np.sum(smash_nodata(unserved_pop_img))
# rai = (rural_pop - unserved_pop) / rural_pop
# rural_pop, unserved_pop, rai

# %%
rural_pop = rural_pop_img[rural_pop_img >= 0].sum()
unserved_pop = unserved_pop_img[unserved_pop_img >= 0].sum()
rai = (rural_pop - unserved_pop) / rural_pop
{
    'rural_pop': rural_pop,
    'unserved_pop': unserved_pop,
    'served_pop': rural_pop - unserved_pop,
    'rai': rai
}

# %%

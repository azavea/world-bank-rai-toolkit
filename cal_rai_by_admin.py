## Calculte RAI by admin boundary
# Relies on outputs of calc_rai_admin.py
# - Load WorldPop and WorldPop masked by road buffers/urban areas
# - Mask each by region, calculate RAI

# %%
import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd
from matplotlib import pyplot

pfix="py"
code="pry"
cname="paraguay"

#%% Load GADM admin level 1 boundaries
gadm = gpd.read_file(
    f"data/inputs/gadm36_{code}.gpkg",
    layer=f'gadm36_{code}_1')

#%% Load WorldPop
worldpop = rasterio.open(f"data/inputs/{code}_ppp_2020.tif")
worldpop_rural = rasterio.open(f"data/{code}/worldpop_rural.tif")
worldpop_rai = rasterio.open(f"data/{code}/worldpop_rai.tif")

#%% Mask function
def add_rai(row):
    region = row['geometry']
    pop_img, _ = rasterio.mask.mask(worldpop, region, invert=True)
    rural_img, _ = rasterio.mask.mask(worldpop_rural, region, invert=True)
    unserved_img, _ = rasterio.mask.mask(worldpop_rai, region, invert=True)

    smash_nodata = np.vectorize(lambda v: v if v > 0 else 0)
    pop = np.sum(smash_nodata(pop_img[0,:,:]))
    rural = np.sum(smash_nodata(rural_img[0,:,:]))
    unserved = np.sum(smash_nodata(unserved_img[0,:,:]))

    row['rai'] = (rural-unserved)/rural
    row['population'] = pop
    row['population_rural'] = rural
    row['population_unserved'] = unserved
    return row

#%%
rai_df = gadm.apply(add_rai, axis=1)
#%%
rai_df.to_file(f"data/{code}/rai_adm1.json", driver="GeoJSON")
# %%

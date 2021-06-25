# Calculte RAI by admin boundary
# Relies on outputs of calc_rai_admin.py
# - Load WorldPop and WorldPop masked by road buffers/urban areas
# - Mask each by region, calculate RAI

# %%
import rasterio
import rasterio.mask
import geopandas as gpd
from matplotlib import pyplot as plt

# %%
# pfix = "py"
# code = "PRY"
# cname = "paraguay"

pfix = "gt"
code = "GTM"
cname = "guatemala"

# %% Load GADM admin level 1 boundaries
gadm = gpd.read_file(
    f"data/inputs/gadm36_{code}.gpkg", layer=f'gadm36_{code}_1')

# %% Load WorldPop
worldpop = rasterio.open(f"data/inputs/{code.lower()}_ppp_2020.tif", nodata=0)
worldpop_rural = rasterio.open(
    f"data/{code}/{code.lower()}_worldpop_rural.tif", nodata=0)
worldpop_rai = rasterio.open(
    f"data/{code}/{code.lower()}_worldpop_rai.tif", nodata=0)


# %% Mask function
def add_rai(row):
    region = row['geometry']
    pop_img, _ = rasterio.mask.mask(worldpop, region)
    rural_img, _ = rasterio.mask.mask(worldpop_rural, region)
    unserved_img, _ = rasterio.mask.mask(worldpop_rai, region)

    pop = pop_img.clip(min=0, out=pop_img).sum()
    rural = rural_img.clip(min=0, out=rural_img).sum()
    unserved = unserved_img.clip(min=0, out=unserved_img).sum()

    row['rai'] = (rural - unserved) / rural
    row['population'] = int(pop.round())
    row['population_rural'] = int(rural.round())
    row['population_unserved'] = int(unserved.round())
    return row


# %%
rai_df = gadm.apply(add_rai, axis=1)

# %%
rai_df.to_file(f"data/{code}/{code}_rai_adm1.json", driver="GeoJSON")

# %%
out_csv_path = f"data/{code}/{pfix}_population_stats.csv"
out_df = rai_df[[
    'NAME_1', 'rai', 'population', 'population_rural', 'population_unserved'
]]
out_df = out_df.rename(
    mapper={
        'NAME_1': 'name'
    }, axis='columns').to_csv(
        out_csv_path, index=False)

# %%
fig = plt.figure(figsize=(10, 10))
ax = plt.gca()
rai_df.plot(
    column='rai',
    cmap='Blues',
    edgecolor='black',
    linewidth=.5,
    ax=plt.gca(),
    legend=True,
    legend_kwds={
        'orientation': 'horizontal',
        'fraction': .045,
        'pad': 0.02
    })
plt.axis('off')
cax = fig.axes[1]
cax.set_xlabel('RAI', fontsize=18)
plt.show()

out_img_path = f"data/{code}/{pfix}_region_rai.png"
fig.savefig(out_img_path, bbox_inches='tight', pad_inches=0.2)

# %%

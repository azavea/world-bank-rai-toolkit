from typing import Dict, Optional, Union, List, Any
import os
import unicodedata as ud
from collections import defaultdict

from pyproj import CRS
from shapely.geometry import Point, LineString

from tqdm import tqdm
import pandas as pd
import geopandas as gpd

GEOD = CRS.from_epsg(4326).get_geod()


# https://stackoverflow.com/a/15547803/5908685
def rmdiacritics(char):
    '''
    Return the base character of char, by "removing" any
    diacritics like accents or curls and strokes and the like.
    '''
    desc = ud.name(char)
    cutoff = desc.find(' WITH ')
    if cutoff != -1:
        desc = desc[:cutoff]
        try:
            char = ud.lookup(desc)
        except KeyError:
            pass  # removing "WITH ..." produced an invalid name
    return char


def remove_diacritics(s: Any) -> Any:
    if not isinstance(s, str):
        return s
    return ''.join(map(rmdiacritics, s))


def straight_line_distance(p1: Point,
                           p2: Point,
                           epsg: Optional[Union[int, str]] = None) -> float:
    line_string = LineString((p1, p2))
    if epsg is not None:
        dist = CRS.from_epsg(epsg).get_geod().geometry_length(line_string)
    else:
        dist = GEOD.geometry_length(line_string)
    return dist


def read_geonames_csv(path: os.PathLike) -> pd.DataFrame:
    column_names = [
        'geonameid', 'name', 'asciiname', 'alternatenames', 'latitude',
        'longitude', 'feature class', 'feature code', 'country code', 'cc2',
        'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
        'population', 'elevation', 'dem', 'timezone', 'modification '
    ]
    df = pd.read_csv(path, delimiter='\t', header=None)
    df.columns = column_names
    df.loc[:, 'orig_name'] = df.name
    df.name = df.asciiname.str.lower()
    df.alternatenames = df.alternatenames.str.lower().map(remove_diacritics)
    df.longitude = df.longitude.astype(float)
    df.latitude = df.latitude.astype(float)
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    return gdf


def geonames_to_dict(places_df: gpd.GeoDataFrame) -> Dict[str, List[Point]]:
    places = places_df.name.to_numpy()
    places_set = set(places)
    places_to_geoms = defaultdict(list)

    with tqdm(places_set, desc='Mapping names to points') as bar:
        for p in bar:
            poitns = places_df.loc[places == p, 'geometry'].to_list()
            places_to_geoms[p] += poitns
    places_to_alts = defaultdict(set)

    with tqdm(places_set, desc='Mapping names to alternate names') as bar:
        for p in bar:
            alts = places_df.loc[places == p, 'alternatenames']
            alts = [v for v in alts if isinstance(v, str)]
            if len(alts) > 0:
                alts = set.union(*[set(v.split(',')) for v in alts])
                places_to_alts[p] = places_to_alts[p].union(alts)
    with tqdm(
            list(places_to_geoms.items()),
            desc='Mapping alternate names to points') as bar:
        for p, g in bar:
            alts = places_to_alts[p]
            for alt in alts:
                places_to_geoms[alt] += g
    return places_to_geoms

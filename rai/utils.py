from typing import Optional, Union
import unicodedata as ud
from pyproj import CRS
from shapely.geometry import Point, LineString

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


def remove_diacritics(s: str):
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

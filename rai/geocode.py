from abc import abstractmethod
from functools import partial
from typing import Optional, Tuple, List
import sys
import os
from contextlib import AbstractContextManager
import logging

from geopy import geocoders, Location
from geopy.extra.rate_limiter import RateLimiter
from shapely.geometry import Point
import pickle

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from utils import remove_diacritics, read_geonames_csv, geonames_to_dict

CACHE_PATH = 'geocoder.cache'

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger()


class Geocoder(AbstractContextManager):
    def __init__(self,
                 cache_path: os.PathLike = CACHE_PATH,
                 max_results: int = 10) -> None:
        self.cache_path = cache_path
        self.max_results = max_results
        self.cache = {}

    def __enter__(self) -> 'Geocoder':
        self.load_cache_from_file(self.cache_path)
        return self

    def __exit__(self, *args, **kwargs) -> Optional[bool]:
        return self.save_cache_to_file(self.cache_path)

    def load_cache_from_file(self, cache_path: os.PathLike):
        if os.path.exists(cache_path):
            log.info('Loading cache from file ...')
            with open(cache_path, 'rb') as f:
                self.cache = pickle.load(f)

    def save_cache_to_file(self, cache_path: os.PathLike):
        log.info('Saving cache to file ...')
        with open(cache_path, 'wb') as f:
            pickle.dump(self.cache, f)

    @abstractmethod
    def geocode(self, q: str) -> List[Tuple[str, Point]]:
        pass

    def __call__(self, q: str) -> Optional[Tuple[List[str], List[Point]]]:
        return self.geocode(q)


class GeoPyGeocoder(Geocoder):
    def __init__(self,
                 service: str = 'GeoNames',
                 rate_limit: float = 3,
                 service_args: dict = {},
                 query_args: dict = {},
                 cache_path: os.PathLike = CACHE_PATH,
                 max_results: int = 10) -> None:
        self.geolocator = getattr(geocoders, service)(
            user_agent='route-app', **service_args)
        _geocode = partial(self.geolocator.geocode, **query_args)
        self.geocode_fn = RateLimiter(_geocode, min_delay_seconds=rate_limit)
        super().__init__(cache_path=cache_path, max_results=max_results)

    def geocode(self, q: str) -> Optional[Tuple[List[str], List[Point]]]:
        if q in self.cache:
            if len(self.cache[q][0]) > 0:
                return self.cache[q]
        res = self.geocode_fn(q, exactly_one=False)
        if res is not None:
            res = res[:self.max_results]
            names = [r.address for r in res]
            points = [self.loc_to_point(r) for r in res]
            self.cache[q] = names, points
        else:
            names, points = [], []
        return names, points

    def loc_to_point(self, loc: Location) -> Point:
        return Point(loc.longitude, loc.latitude)


class CustomGeocoder(Geocoder):
    def __init__(self,
                 places_to_geoms: dict,
                 fuzz_args: dict = {},
                 cache_path: os.PathLike = CACHE_PATH,
                 max_results: int = 10) -> None:
        self.places_to_geoms = places_to_geoms
        self.places = self.places_to_geoms.keys()
        self.fuzz_args = fuzz_args
        super().__init__(cache_path=cache_path, max_results=max_results)

    def geocode(self, q: str) -> Optional[Tuple[List[str], List[Point]]]:
        scorer = self.fuzz_args.get('scorer', None)
        limit = self.fuzz_args.get('limit', 3)

        if scorer is not None:
            fuzzy_matches = process.extract(
                q, self.places, scorer=scorer, limit=limit)
        else:
            fuzzy_matches_w = process.extract(
                q, self.places, scorer=fuzz.WRatio, limit=limit)
            fuzzy_matches_q = process.extract(
                q, self.places, scorer=fuzz.QRatio, limit=limit)
            fuzzy_matches = fuzzy_matches_w + fuzzy_matches_q

        matches = set(k for k, _ in fuzzy_matches)
        names = []
        points = []
        for name in matches:
            ps = self.places_to_geoms[name]
            points += ps
            names += [name] * len(ps)

        return names, points

    def normalize_string(self, s: str) -> str:
        s = s.stript().lower()
        s = remove_diacritics(s)
        return s

    @classmethod
    def from_geonames_csv(cls, path: os.PathLike,
                          **kwargs) -> 'CustomGeocoder':
        places_df = read_geonames_csv(path)
        places_to_geoms = geonames_to_dict(places_df)
        geocoder = CustomGeocoder(places_to_geoms, **kwargs)
        return geocoder


def test_geopy():
    with GeoPyGeocoder(
            service_args={'username': 'ahassan'}, query_args={'country':
                                                              'GT'}) as g:
        print(g('secoyob'))
        print(g('san luis'))

    with GeoPyGeocoder(
            service_args={'username': 'ahassan'}, query_args={'country':
                                                              'PY'}) as g:
        print(g('ALTO VERA'))
        print(g('VILLETA'))


def test_custom():
    gcm = CustomGeocoder.from_geonames_csv(
        ('/home/adeel/2021 - RAI Toolkit-20210528T125906Z-001/'
         '2021 - RAI Toolkit/'
         'Country Data/Guatemala_4-19-2021/GT/GT.txt'))
    with gcm as g:
        print(g('secoyob'))
        print(g('san luis'))


if __name__ == '__main__':
    test_custom()
    # test_geopy()

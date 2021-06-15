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

CACHE_PATH = 'geocoder.cache'

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger()


class Geocoder(AbstractContextManager):
    def __init__(self,
                 service: str = 'GeoNames',
                 rate_limit: float = 3,
                 cache_path: os.PathLike = CACHE_PATH,
                 max_results: int = 10,
                 service_args: dict = {},
                 query_args: dict = {}) -> None:
        self.geolocator = getattr(geocoders, service)(
            user_agent='route-app', **service_args)
        _geocode = partial(self.geolocator.geocode, **query_args)
        self.geocode_fn = RateLimiter(_geocode, min_delay_seconds=rate_limit)
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

    def geocode(self, q: str) -> Optional[List[Tuple[str, Point]]]:
        if q in self.cache:
            return self.cache[q]
        res = self.geocode_fn(q, exactly_one=False)
        if res is not None:
            res = res[:self.max_results]
            names = [r.address for r in res]
            points = [self.loc_to_point(r) for r in res]
        else:
            names, points = [], []
        self.cache[q] = names, points
        return names, points

    def loc_to_point(self, loc: Location) -> Point:
        return Point(loc.longitude, loc.latitude)

    def __call__(self, q: str) -> Optional[List[Tuple[str, Point]]]:
        return self.geocode(q)


if __name__ == '__main__':

    with Geocoder(
            service_args={'username': 'ahassan'}, query_args={'country':
                                                              'GT'}) as g:
        print(g('secoyob'))
        print(g('san luis'))

    with Geocoder(
            service_args={'username': 'ahassan'}, query_args={'country':
                                                              'PY'}) as g:
        print(g('ALTO VERA'))
        print(g('VILLETA'))

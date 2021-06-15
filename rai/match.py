from typing import Tuple, Iterable, List, Optional
import sys
import os
from itertools import product
import logging

import numpy as np
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

from shapely.geometry import Point

from rai.utils import straight_line_distance
from rai.geocode import Geocoder
from rai.route import Route, Router
from rai.preprocess import get_country_preprocesor
from rai.defaults import (PROCESSED_LENGTH_COL, ENDPOINT_COLS)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger()


class Matcher():
    def __init__(self,
                 geocoder: Geocoder,
                 router: Router,
                 max_candidate_routes: Optional[int] = 10) -> None:
        self.geocoder = geocoder
        self.router = router
        self.max_candidate_routes = max_candidate_routes

    def match(self, p1: str, p2: str, target_length: float) -> Route:
        log.info(f'{p1} -- {p2}')

        _, p1_candidates = self.geocoder(p1)
        _, p2_candidates = self.geocoder(p2)

        candidate_pairs, _ = self.get_candidate_pairs(
            p1_candidates, p2_candidates, target_length, tol=10)

        if self.max_candidate_routes is not None:
            candidate_pairs = candidate_pairs[:self.max_candidate_routes]

        if len(candidate_pairs) == 0:
            return Route.null()

        log.info(f'{len(candidate_pairs)}')
        candidate_routes = self.get_candidate_routes(candidate_pairs)
        matched_route = self.select_best_route(candidate_routes, target_length)
        return matched_route

    def select_best_route(self, candidate_routes: List[Route],
                          target_length: float) -> Route:
        route_lengths = np.array([r.length for r in candidate_routes])
        best_route_idx = np.argmin(np.abs(route_lengths - target_length))
        return candidate_routes[best_route_idx]

    def get_candidate_routes(
            self,
            candidate_pairs: Iterable[Tuple[Point, Point]]) -> List[Route]:
        candidate_routes = [
            self.router.find_route(p1, p2) for p1, p2 in candidate_pairs
        ]
        candidate_routes = [
            r for r in candidate_routes if r.length is not None
        ]
        return candidate_routes

    def get_candidate_pairs(self,
                            p1_candidates: Iterable[Point],
                            p2_candidates: Iterable[Point],
                            target_length: float,
                            tol: float = 10) -> Tuple[List[Point], np.ndarray]:
        pairs = [
            p for p in product(p1_candidates, p2_candidates) if p[0] != p[1]
        ]
        if len(pairs) == 0:
            return [], np.array([])
        straight_dists = [straight_line_distance(p1, p2) for p1, p2 in pairs]
        straight_dists = np.array(straight_dists) / 1e3
        diffs = np.abs(straight_dists - target_length)
        filtered_pairs = [p for p, d in zip(pairs, diffs) if d <= tol]
        filtered_diffs = diffs[diffs <= tol]

        inds = np.argsort(filtered_diffs)
        filtered_pairs = [filtered_pairs[i] for i in inds]
        return filtered_pairs, filtered_diffs


def main():
    country = 'guatemala'
    country_code = 'GT'
    csv_path = '/home/adeel/2021 - RAI Toolkit-20210528T125906Z-001/2021 - RAI Toolkit/' 'Country Data/Guatemala_4-19-2021/Inventario Rutas PDV 2018-2032.csv'  # noqa
    # country = 'paraguay'
    # country_code = 'PY'
    # csv_path = '/home/adeel/2021 - RAI Toolkit-20210528T125906Z-001/2021 - RAI Toolkit/Country Data/Paraguay/PY2018-SECTIONS.csv'  # noqa
    cache_path = f'{country}.geocoder.cache'
    df = pd.read_csv(csv_path)
    preprocessor = get_country_preprocesor(country)(df)
    preprocessor.run()
    df = preprocessor.df
    router = Router(country)
    gcm = Geocoder(
        cache_path=cache_path,
        service_args={'username': 'ahassan'},
        query_args={'country': country_code})
    with gcm as geocoder:
        matcher = Matcher(geocoder, router)
        routes = []
        nmatches = 0
        iter_cols = [*ENDPOINT_COLS, PROCESSED_LENGTH_COL]
        it = df[iter_cols].itertuples(index=False, name=None)
        with tqdm(it, total=len(df)) as bar:
            for p1, p2, tgt_length in bar:
                route = matcher.match(p1, p2, tgt_length)
                routes.append(route)
                if route.length is not None:
                    nmatches += 1
                    bar.set_postfix({
                        'start': p1,
                        'end': p2,
                        'diff': tgt_length - route.length,
                        'matches': nmatches
                    })
    df['geometry'] = [r.geom for r in routes]
    df['route_length'] = [r.length for r in routes]
    gdf = gpd.GeoDataFrame(df)

    out_dir = f'out/{country}'
    os.makedirs(out_dir, exist_ok=True)
    gdf.to_csv(f'{out_dir}/{country}.csv')
    gdf.to_file(f'{out_dir}/{country}.geojson', driver='GeoJSON')


if __name__ == '__main__':
    main()

# def match(p1_name, p2_name, wb_length, debug=False):
#     p1_name, p2_name = p1_name.strip().lower(), p2_name.strip().lower()
#     info = {
#         'p1_name': p1_name,
#         'p2_name': p2_name,
#         'wb_length': wb_length,
#         'route': None
#     }
#     p1_candidates, p1_candidate_names = lookup_place(p1_name)
#     p2_candidates, p2_candidate_names = lookup_place(p2_name)
#     if debug:
#         info['p1_candidates'] = p1_candidates
#         info['p1_candidate_names'] = p1_candidate_names
#         info['p2_candidates'] = p2_candidates
#         info['p2_candidate_names'] = p2_candidate_names

#     candidate_pairs, diffs = candidate_endpoints(
#         p1_candidates, p2_candidates, wb_length, tol=10)
#     if debug:
#         info['candidate_pairs'] = candidate_pairs
#         info['candidate_pair_diffs'] = diffs

#     if len(candidate_pairs) == 0:
#         print(f'Skipping {p1_name} -- {p2_name}, '
#               f'No candidate pairs. '
#               f'wb_len={wb_length}, diffs={diffs.tolist()}')
#         return info

#     candidate_routes = [
#         get_route_info(G, p1, p2) for p1, p2 in candidate_pairs
#     ]
#     route_lengths = np.array([r['length'] for r in candidate_routes])
#     best_route_idx = np.argmin(np.abs(route_lengths - wb_length))
#     print(wb_length, route_lengths)
#     route_info = candidate_routes[best_route_idx]
#     p1, p2 = candidate_pairs[best_route_idx]
#     info.update(route_info)
#     info['p1'] = p1
#     info['p2'] = p2
#     info['straight_line_dist'] = straight_line_distance(p1, p2) / 1e3
#     info['diff'] = wb_length - route_info['length']
#     info['abs_diff'] = abs(info['diff'])
#     info['rel_error'] = info['abs_diff'] / wb_length

#     if debug:
#         info['candidate_routes'] = candidate_routes
#         info['candidate_route_lengths'] = route_lengths
#         info['best_route_idx'] = best_route_idx

#     return info

# matches = []
# with tqdm(df.itertuples(), total=len(df)) as bar:
#     for i, row in enumerate(bar):
#         wb_length = float(row.length)
#         p1_name = row.endpoint_1
#         p2_name = row.endpoint_2

#         info = match(p1_name, p2_name, wb_length)
#         if info.get('route') is None:
#             continue
#         matches.append(info)

#         bar.set_postfix({
#             'start': p1_name,
#             'end': p2_name,
#             'diff': info['diff'],
#             'matches': len(matches)
#         })
#         gc.collect()

from typing import Any, Optional, List
import sys
import os
import logging

from shapely.geometry import Point, LineString

import osmnx as ox
import networkx as nx
from networkx.classes.function import path_weight

from rai.utils import straight_line_distance

ox.config(use_cache=True, log_console=False)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger()


class Route():
    def __init__(self, points: List[Point], length: float) -> None:
        self.points = points
        self.length = length
        self.geom = LineString(points) if len(points) > 0 else None

    @classmethod
    def null(cls):
        return Route([], None)


class Router():
    def __init__(self, region: str) -> None:
        self.region = region
        self.G = self.get_graph(region, save=True)
        self.nodes = self.G.nodes

    def get_graph(self, region: str, save: bool = True) -> nx.Graph:
        if os.path.exists(self.get_save_path(region)):
            log.info('Loading graph from file ...')
            G = ox.load_graphml(self.get_save_path(region))
        else:
            log.info('Downloading graph ...')
            G = download_road_graph(region)
            if save:
                log.info('Saving graph ...')
                self.save_graph(self.get_save_path(region))
        return G

    def get_save_path(self, region: str) -> os.PathLike:
        return f'graphs/{region}.graphml'

    def save_graph(self, save_path: Optional[os.PathLike] = None) -> None:
        if save_path is None:
            save_path = self.get_save_path(self.region)
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        ox.save_graphml(self.G, save_path)

    def heuristic(self, node1: Any, node2: Any) -> float:
        p1, p2 = self.node_to_point(node1), self.node_to_point(node2)
        return straight_line_distance(p1, p2)

    def node_to_point(self, node_key: Any) -> Point:
        node = self.nodes[node_key]
        point = Point(node['x'], node['y'])
        return point

    def nodes_to_points(self, node_keys: Any) -> List[Point]:
        points = [self.node_to_point(k) for k in node_keys]
        return points

    def route_to_geom(self, route: list) -> LineString:
        points = [self.node_to_point(node) for node in route]
        geom = LineString(points)
        return geom

    def find_route(self, p1: Point, p2: Point, km: bool = True) -> Route:
        G = self.G
        start = p1.coords[0]
        end = p2.coords[0]
        start_node = ox.distance.nearest_nodes(G, *start)
        end_node = ox.distance.nearest_nodes(G, *end)

        try:
            path = nx.shortest_paths.astar_path(
                G,
                start_node,
                end_node,
                weight='length',
                heuristic=self.heuristic)
            route_length = path_weight(G, path, weight='length')
            if km:
                route_length /= 1e3
            route = Route(self.nodes_to_points(path), route_length)
        except nx.NetworkXNoPath:
            route = Route.null()

        return route


def download_road_graph(region: str, **kwargs) -> nx.Graph:
    highway_types_to_inlcude = []
    if kwargs.get('trunk', True):
        highway_types_to_inlcude.append('trunk')
        highway_types_to_inlcude.append('trunk_link')
    if kwargs.get('motorway', True):
        highway_types_to_inlcude.append('motorway')
        highway_types_to_inlcude.append('motorway_link')
    if kwargs.get('primary', True):
        highway_types_to_inlcude.append('primary')
        highway_types_to_inlcude.append('primary_link')
    if kwargs.get('secondary', True):
        highway_types_to_inlcude.append('secondary')
        highway_types_to_inlcude.append('secondary_link')
    if kwargs.get('tertiary', True):
        highway_types_to_inlcude.append('tertiary')
        highway_types_to_inlcude.append('tertiary_link')
    if kwargs.get('residential', False):
        highway_types_to_inlcude.append('residential')
        highway_types_to_inlcude.append('residential_link')

    highway_types_to_inlcude = '|'.join(highway_types_to_inlcude)
    custom_filter = f'["highway"~"{highway_types_to_inlcude}"]'

    G = ox.graph_from_place(
        region,
        network_type='drive',
        custom_filter=custom_filter,
        simplify=False)

    return G

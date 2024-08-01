from typing import List
import osmnx as ox
from geopy.geocoders import Nominatim
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import plotly_express as px
import time


class Map:
    def __init__(
        self,
        location: str,
        simplify: bool = False,
        elevation_map: str = "./envigado.tif",
    ):
        self.location = location
        self.G = ox.graph_from_place(location, network_type="drive", simplify=simplify)
        self.show = ox.plot_graph(self.G, figsize=(25, 25))
        self.tif_map = elevation_map
        self.nodes = pd.DataFrame([])
        self.edges = pd.DataFrame([])

    def set_data(self):
        self.add_nodes_edges()
        self.add_speeds()
        self.add_travel_times()

    def add_elevations(self, absolute: bool = True):
        self.G = ox.elevation.add_node_elevations_raster(self.G, self.tif_map, band=1)
        self.G = ox.add_edge_grades(self.G, add_absolute=absolute)

    def add_speeds(self):
        hwy_speeds = {"residential": 35, "secondary": 50, "tertiary": 60}
        self.G = ox.add_edge_speeds(self.G, hwy_speeds)

    def add_travel_times(self):
        """
        Add travel times (seconds) for edges based on edge length and speed.
        """
        self.G = ox.add_edge_travel_times(self.G)

    def add_nodes_edges(self):
        self.nodes, self.edges = ox.graph_to_gdfs(self.G)

    def calculate_heuristic(self, u, v):
        return 1

    def get_operators(self) -> List[int]:
        # Assuming operators are actions to move to neighboring nodes
        return list(range(len(list(self.G.successors(self.G.nodes[0])))))

    def set_route(self, start: str, end: str):
        locator = Nominatim(user_agent="ai-eia-2024-1-isis")
        start_coordinates = geocode_with_retry(start, locator)
        end_coordinates = geocode_with_retry(end, locator)

        start = (start_coordinates.latitude, start_coordinates.longitude)
        end = (end_coordinates.latitude, end_coordinates.longitude)

        start_node = ox.distance.nearest_nodes(self.G, start[1], start[0])
        end_node = ox.distance.nearest_nodes(self.G, end[1], end[0])
        return start_node, end_node

    def display_interactive_route(self, route, start_node, end_node):
        node_start = []
        node_end = []
        X_to = []
        Y_to = []
        X_from = []
        Y_from = []
        length = []
        travel_time = []

        for u, v in zip(route[:-1], route[1:]):
            node_start.append(u)
            node_end.append(v)
            length.append(round(self.G.edges[(u, v, 0)]["length"]))
            travel_time.append(round(self.G.edges[(u, v, 0)]["travel_time"]))
            X_from.append(self.G.nodes[u]["x"])
            Y_from.append(self.G.nodes[u]["y"])
            X_to.append(self.G.nodes[v]["x"])
            Y_to.append(self.G.nodes[v]["y"])
        df = pd.DataFrame(
            list(
                zip(
                    node_start,
                    node_end,
                    X_from,
                    Y_from,
                    X_to,
                    Y_to,
                    length,
                    travel_time,
                )
            ),
            columns=[
                "node_start",
                "node_end",
                "X_from",
                "Y_from",
                "X_to",
                "Y_to",
                "length",
                "travel_time",
            ],
        )
        df.reset_index(inplace=True)
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.X_from, df.Y_from))
        gdf["geometry_to"] = [Point(xy) for xy in zip(gdf.X_to, gdf.Y_to)]
        gdf["line"] = gdf.apply(
            lambda row: LineString([row["geometry_to"], row["geometry"]]), axis=1
        )
        line_gdf = gdf[
            ["node_start", "node_end", "length", "travel_time", "line"]
        ].set_geometry("line")
        start = df[df["node_start"] == start_node]
        end = df[df["node_end"] == end_node]
        fig = px.scatter_mapbox(
            df,
            lon="X_from",
            lat="Y_from",
            zoom=12,
            width=1000,
            height=600,
            animation_frame="index",
            mapbox_style="open-street-map",
        )
        fig.data[0].marker = dict(size=12, color="black")
        fig.add_trace(px.scatter_mapbox(start, lon="X_from", lat="Y_from").data[0])
        fig.data[1].marker = dict(size=15, color="red")
        fig.add_trace(px.scatter_mapbox(end, lon="X_from", lat="Y_from").data[0])
        fig.data[2].marker = dict(size=15, color="green")
        fig.add_trace(px.line_mapbox(df, lon="X_from", lat="Y_from").data[0])
        return fig


def geocode_with_retry(address, geolocator, max_retries=20, timeout=10):
    retries = 0
    while retries < max_retries:
        try:
            location = geolocator.geocode(address, timeout=timeout)
            return location
        except Exception:
            retries += 1
            print(f"Geocoder timed out, retrying... ({retries}/{max_retries})")
            time.sleep(1)
    return None


class FromToMap:
    def __init__(self, start: str, end: str, G):
        self.locator = Nominatim(user_agent="ai-eia-2024-1-isis")
        self.start_coordinates = geocode_with_retry(start, self.locator)
        self.end_coordinates = geocode_with_retry(end, self.locator)

        self.start = (self.start_coordinates.latitude, self.start_coordinates.longitude)
        self.end = (self.end_coordinates.latitude, self.end_coordinates.longitude)

        self.start_node = ox.distance.nearest_nodes(G, self.start[1], self.start[0])
        self.end_node = ox.distance.nearest_nodes(G, self.end[1], self.end[0])

import os
import webbrowser
import random
from classes import BBox, Timer
from load_data import find_xy_fields, data_path

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely import LineString, Point
import momepy
import networkx as nx

"""
Overview: 

Provides a variety of functions for conversion and display of
pandas DataFrames with compatible structures

Functions that plot or map DataFrames or Series will never produce
output; to get the resulting GeoDataFrame and plot it, call the
correct conversion function to obtain the gdf and plot it separately.

GeoDataFrame geometries are expected to have assigned CRS, as most
operations will attempt to convert input GeoDataFrames to Canada
Lambert Conformal Conic (abbreviated to LCC within this file), and most
operations will produce output referenced in Canada LCC.
"""


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##


# ========================================================================= ##
# Script Constants ======================================================== ##
# ========================================================================= ##

timer = Timer()


central_lon = -85
central_lat = 40
stand_parallel_1 = 50
stand_parallel_2 = 70


# standard parallels were taken from stats canada

# WKT string for Canadian lambert conformal conic projection
# refer to the source for projected and WGS84 bounds
# As of 2023-10-02:
#   Center coordinates: 261638.61 2500407.04
#   Projected bounds: -3827665.83  -207619.51
#                      4510310.33  5481591.53
#   WGS84 bounds: -141.01  38.21
#                  -40.73  86.46
# source: https://epsg.io/102002
Can_LCC_wkt = ('PROJCS["Canada_Lambert_Conformal_Conic",'
                    'GEOGCS["NAD83",'
                        'DATUM["North_American_Datum_1983",'
                            'SPHEROID["GRS 1980",6378137,298.257222101,'
                                'AUTHORITY["EPSG","7019"]],'
                            'AUTHORITY["EPSG","6269"]],'
                        'PRIMEM["Greenwich",0,'
                            'AUTHORITY["EPSG","8901"]],'
                        'UNIT["degree",0.0174532925199433,'
                            'AUTHORITY["EPSG","9122"]],'
                        'AUTHORITY["EPSG","4269"]],'
                    'PROJECTION["Lambert_Conformal_Conic_2SP"],'
                    f'PARAMETER["latitude_of_origin",{central_lat}],'
                    f'PARAMETER["central_meridian",{central_lon}]'
                    f'PARAMETER["standard_parallel_1",{stand_parallel_1}],'
                    f'PARAMETER["standard_parallel_2",{stand_parallel_2}],'
                    'PARAMETER["false_easting",0],'
                    'PARAMETER["false_northing",0],'
                    'UNIT["metre",1,'
                        'AUTHORITY["EPSG","9001"]],'
                    'AXIS["Easting",EAST],'
                    'AXIS["Northing",NORTH],'
                    'AUTHORITY["ESRI","102002"]]')


# ========================================================================= ##
# Data Processing ========================================================= ##
# ========================================================================= ##


def connect_points_to_feature(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame) -> dict:
    """
    For each point in points, finds and returns the location on other
    closest to that point.

    Shoutout to Brendan Ward for their Medium article:
    https://medium.com/@brendan_ward/how-to-leverage-geopandas-for-faster-snapping-of-points-to-lines-6113c94e59aa

    :param points: GeoPandas GeoDataFrame
        The points to snap to other.

    :param other: GeoPandas GeoDataFrame
        GeoDataFrame to snap the points to. May be points, lines,
        or polygons.

    :return: dict
        Contains the new points on other and the lines connecting the
        original points to the new points (used for checking quality
        of point snapping. Has 2 keys: 'new_points' & 'lines'. Maintains
        the same order as points.
    """
    # Spatial manipulation is performed in Lambert conformal conic
    # but the geometry of the original datasets are not changed.
    if points.crs != Can_LCC_wkt:
        points = points.to_crs(crs=Can_LCC_wkt)
    if other.crs != Can_LCC_wkt:
        other = other.to_crs(crs=Can_LCC_wkt)

    other = other.assign(unique_ind=other.index)
    other = other.assign(other=other.geometry)
    closest = points.sjoin_nearest(other, how='left', distance_col='distance')

    # project then interpolate appears to be slower for all sizes of data
    # pos = closest['other'].project(closest.geometry)
    # data = closest['other'].interpolate(pos)

    shortest_lines = closest.geometry.shortest_line(closest['other'])

    # Potentially find a more efficient solution that doesn't use apply
    new_points = shortest_lines.apply(lambda line: Point(line.coords[1]))

    return {'new_points': new_points, 'lines': shortest_lines}


def snap_points(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame):
    """
    Wrapper function for connect_points_to_feature() that returns only
    the points and not the connecting lines.
    :return:
    """
    return connect_points_to_feature(points, other)['new_points']


def connectors(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame):
    """
    Wrapper function for connect_points_to_feature() that returns only
    the connecting lines and not the new points.
    :return:
    """
    return connect_points_to_feature(points, other)['lines']


# ========================================================================= ##
# Data Conversion ========================================================= ##
# ========================================================================= ##


def point_gdf_from_df(df: pd.DataFrame, x_field="", y_field="", crs=None) -> gpd.GeoDataFrame:
    """
    Convert a pandas DataFrame to a geopandas GeoDataFrame with point
    geometry, if possible.

    If x and y fields are not provided, the function will search the
    DataFrame for fields to use with find_xy_fields(). If you provide
    x and y fields, you MUST provide a crs as well.

    :param df: pandas DataFrame to convert

    :param x_field: <str> (optional)
        field to use as longitude/x value

    :param y_field: <str> (optional)
        field to use as latitude/y value

    :param crs: value (optional)
        Coordinate reference system of the geometry objects. Can be
        anything accepted by pyproj.CRS.from_user_input().
        i.e.
            WKT String (such as Can_LCC_wkt)
            authority string ("EPSG:4326")

    :return: <Geopandas GeoDataFrame> or <int>
        The resulting GeoDataFrame, or -1 if the conversion failed. If
        a crs is passed, the GDF will be in that crs. If lat/lon fields
        are found by find_xy_fields(), crs will be set to EPSG:4326.

    :raises TypeError:
        If x and y fields are provided, but a CRS is not.

        If df is not a DataFrame.
    """
    timer.start()

    if type(df) != pd.DataFrame:
        raise TypeError("Pandas DataFrame expected but", type(df), "found")
    elif (x_field or y_field) and crs is None:
        raise TypeError("CRS keyword argument missing")

    if not x_field and not y_field:
        x, y = find_xy_fields(df)
        print(f"Searching for fields...\nX field: {x}   Y field: {y}\n")

        if x == "Failed" or y == "Failed" or x == "" or y == "":
            print("Operation Failed. Check your fields")
        else:
            # Lat/lon fields successfully located
            crs = 4326
    else:
        x, y = x_field, y_field

    print(f"Attempting conversion with the following CRS parameter:\n{crs}")
    try:
        gdf = gpd.GeoDataFrame(
            df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs=crs)
        gdf.to_crs(Can_LCC_wkt)
        print("Dataframe successfully converted to geopandas point array")
    except KeyError:
        gdf = -1
        print("Conversion Failed")

    timer.stop()
    return gdf


# ========================================================================= ##
# HydroRIVERS ============================================================= ##
# ========================================================================= ##


def load_hydro_rivers(sample=None, bbox=None) -> gpd.GeoDataFrame:
    """
    Loads HydroRIVERS_v10.shp as a geopandas GeoDataFrame

    Note: As BBox grows larger, spatial distortion increases.
    Attempting to place geometry features outside the projection's
    supported bounds may result in undesirable behaviour. Refer
    to https://epsg.io/102002 (which describes features of projection
    defined by Can_LCC_wkt) for the projected and WGS84 bounds.

    :param sample: int or None (default)
        The number of river segments to load. If None, load all.

    :param bbox: <BBox> or None (default)
        BBox object declaring area of interest or None, indicating
        not to filter by a bounding box

    :return: <Geopandas GeoDataFrame>
    """
    hydro_path = os.path.join(
        data_path, os.path.join("Hydro_RIVERS_v10", "HydroRIVERS_v10_na.shp"))

    data = gpd.read_file(hydro_path, rows=sample, bbox=BBox.to_tuple(bbox))
    return data.to_crs(crs=Can_LCC_wkt)


def assign_stations(edges, stations, stat_id_f, prefix="", max_distance=None):
    """
    Snaps stations to the closest features in edges and assigns
    descriptors to line segments. Uses a solution similar
    to connect_points_to_features().

    For each station, finds the closest line in edge and assigns
    to the selected feature the following values:
        - station id
        - dist(ance) of the closest point to the station from the
          start of the line

    To deal with situations of multiple stations being assigned to
    the same edge feature, station id and distance are stored in a
    field named 'data', which consists of Pandas DataFrames .

    :param edges: Geopandas GeoDataFrame
        The lines/features to assign stations to.

    :param stations: Geopandas GeoDataFrame
        The station points to assign to edges.

    :param stat_id_f: string
        The name of the unique identifier field in stations.

    :param prefix: string
        Prefix to apply to added 'data' column. If left blank, may
        cause overlapping columns in output GeoDataFrame.

    :param max_distance: int or None (default)
        The maximum distance (in CRS units) within which to assign a
        station to edges. If int, must be greater than 0.

    :return: Geopandas GeoDataFrame
        A copy of edges merged that includes selected station related data.
    """
    if stations.crs != Can_LCC_wkt:
        stations = stations.to_crs(crs=Can_LCC_wkt)
    if edges.crs != Can_LCC_wkt:
        edges = edges.to_crs(crs=Can_LCC_wkt)

    edges = edges.assign(unique_ind=edges.index)
    edges = edges.assign(other=edges.geometry)

    stations = stations.sjoin_nearest(edges, how='left', max_distance=max_distance)

    stations = stations.assign(dist=stations['other'].project(stations.geometry))
    stations.rename(columns={stat_id_f: 'ID'}, inplace=True)
    stations = stations[['ID', 'unique_ind', 'dist']]

    grouped = stations.groupby(by='unique_ind', sort=False)

    temp_data = {'unique_ind': [], prefix + 'data': []}

    for ind, data in grouped:
        temp_data['unique_ind'].append(ind)
        temp_data[prefix + 'data'].append(data[['ID', 'dist']])

    temp = pd.DataFrame(data=temp_data)

    edges = edges.merge(temp, on='unique_ind', how='left')

    return edges


def edge_search(network, prefix1='pwqmn_', prefix2='hydat_'):

    def reverse_bfs(source, prefix):
        edges = network.in_edges(nbunch=source, data=True)
        for edge in edges:
            u, v, data = edge

            if (prefix + '_data') in data.keys():
                series = data[prefix + 'data'].sort_values(by='dist', index=1).iloc[0]

                return series['ID'], (u, v)
            else:
                return (*bfs(v, prefix2), (u, v))
        return -1, -1

    def bfs(source, prefix):
        edges = network.out_edges(nbunch=source, data=True)
        for edge in edges:
            u, v, data = edge

            if (prefix + '_data') in data.keys():
                series = data[prefix + 'data'].sort_values(by='dist', index=1).iloc[0]

                return series['ID'], (u, v)
            else:
                return (*bfs(v, prefix2), (u, v))
        return -1, -1

    edges = network.out_edges(data=True)
    pairs = []

    for edge in edges:
        u, v, data = edge

        if type(data[prefix1 + 'data']) in [pd.DataFrame, gpd.GeoDataFrame]:
            if type(data[prefix2 + 'data']) in [pd.DataFrame, gpd.GeoDataFrame]:

                series = data[prefix2 + 'data'].iloc[0]
                point_list = series['ID'], (u, v)
            else:
                point_list = bfs(v, prefix2)

            if point_list[0] != -1:
                pairs.append(point_list)

            point_list = reverse_bfs(u, prefix2)
            if point_list[0] != -1:
                pairs.append(point_list)

    return gpd.GeoSeries([LineString(pair[1]) for pair in pairs], crs=Can_LCC_wkt)


def hyriv_gdf_to_network(hyriv_gdf: gpd.GeoDataFrame, plot=True, show=True) -> nx.DiGraph:
    """
    Creates a directed network from a hydroRIVER line GeoDataFrame.

    A glorified wrapper function that gives the option to plot the
    produced network against the original GeoDataFrame

    :param hyriv_gdf: Geopandas GeoDataFrame
        The GeoDataFrame to turn into a directed network

    :param plot: bool
        If True, plot a network/original line dataset comparison
        to matplotlib.pyplot. If False, do nothing.

    :param show: bool
        If True, display the plot. If False, do nothing.

    :return: networkX DiGraph
        The resultant networkx directed graph.
    """
    p_graph = momepy.gdf_to_nx(hyriv_gdf, approach='primal', directed=True)

    if plot:
        positions = {n: [n[0], n[1]] for n in list(p_graph.nodes)}

        # Plot
        f, ax = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
        hyriv_gdf.plot(color="k", ax=ax[0])
        for i, facet in enumerate(ax):
            facet.set_title(("Rivers", "Graph")[i])
            facet.axis("off")
        nx.draw(p_graph, positions, ax=ax[1], node_size=5)

    if show:
        plt.show()

    return p_graph


def hyriv_network_to_gdf(network, show=True, plot=True):
    return momepy.nx_to_gdf(network)


def check_hyriv_network(digraph: nx.DiGraph) -> float:
    """
    Checks a NetworkX DiGraph (directed graph) created from a
    HydroRIVERS shapefile for correct connectivity and directionality.

    :return: float
        A decimal value representing the percentage of edges with
        correct connectivity. Between 0.0 and 1.0.
    """
    correct_edges, total_edges = 0, 0

    # edges is an iterable of (u, v, key)
    # where u is starting node, v is ending node, and key is the key used to

    # 3: traverse the edges, and ensure that one of the edges leading away from
    #    v node has a hydri_id = next_down

    # edge_dfs is in the form (u, v, key)

    # referencing edge values
    for u, v, data in digraph.edges(data="NEXT_DOWN"):
        total_edges += 1

        out_edges = digraph.out_edges(nbunch=v, data='HYRIV_ID')

        if data == 0 and len(out_edges) != 0:
            # A 'NEXT_DOWN' value of 0 indicates there is no directly
            # connected segment downstream
            break
        elif len(out_edges) == 0:
            # If there are no edges leading away from the node, the
            # node is at the edge of the selected BBox
            correct_edges += 1

        for out_edge in out_edges:
            if out_edge[2] == data:
                correct_edges += 1
                break

    ratio = correct_edges / total_edges

    print(f"{correct_edges}/{total_edges} ({ratio * 100}%) correct.")

    return ratio


def get_hyriv_network(bbox=None, sample=None) -> nx.DiGraph:
    """
    Wrapper function for getting the HydroRIVERS directed graph.

    :return: NetworkX DiGraph
    """
    hyriv = load_hydro_rivers(sample=sample, bbox=bbox)
    return hyriv_gdf_to_network(hyriv)
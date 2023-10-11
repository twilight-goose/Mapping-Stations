import os
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

Provides a variety of functions for conversion and manipulation of
data; primarily that which is related to GeoPandas GeoDataFrames.
This includes data structures provided by Pandas, Shapely, and
NetworkX.

GeoDataFrame and GeoSeries parameters are expected to have assigned
CRSs. Operations affected by coordinate system distortions will attempt 
to convert input geometries to Canada Lambert Conformal Conic, which is
defined by Can_LCC_wkt, and will produce output referenced in this CRS.


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

    # create a unique identifier and a copy of the geometry of other
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

    :return: GeoPandas GeoDataFrame
        Point GeoDataFrame. Consult connect_points_to_feature for more
        information.
    """
    return connect_points_to_feature(points, other)['new_points']


def connectors(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame):
    """
    Wrapper function for connect_points_to_feature() that returns only
    the connecting lines and not the new points.

    :return: GeoPandas GeoDataFrame
        LineString GeoDataFrame. Consult connect_points_to_feature for
        more information.
    """
    return connect_points_to_feature(points, other)['lines']


# ========================================================================= ##
# Data Conversion ========================================================= ##
# ========================================================================= ##


def point_gdf_from_df(df: pd.DataFrame, x_field=None, y_field=None, crs=None) -> gpd.GeoDataFrame:
    """
    Convert a pandas DataFrame to a geopandas GeoDataFrame with point
    geometry, if possible.

    If neither x nor y fields are not provided, the function will
    search the DataFrame for fields to use with find_xy_fields().
    Conversion will fail if only 1 of x_field or y_field is provided.

    If x and y fields are not provided, the crs will be assumed to be
    EPSG:4326. If you provide x and y fields, you MUST provide a crs
    as well.

    :param df: pandas DataFrame
        DataFrame to convert to a GeoDataFrame

    :param x_field: str or None (default)
        Field to use as longitude/x value. If None, searches df
        for X and Y fields to use. Required if y_field is provided.

    :param y_field: str or None (default)
        Field to use as latitude/y value. If None, searches df
        for X and Y fields to use. Required if y_field is provided.

    :param crs: value (optional)
        Coordinate reference system of the geometry objects. Can be
        anything accepted by pyproj.CRS.from_user_input().
        i.e.
        - WKT String (such as Can_LCC_wkt)
        - authority string ("EPSG:4326")

    :return: Geopandas GeoDataFrame or int
        The resulting GeoDataFrame, or -1 if the conversion failed. If
        a crs is passed, the GDF will be in that crs. If lat/lon fields
        are found by find_xy_fields(), crs will be set to EPSG:4326.

    :raises TypeError:
        If x and y fields are provided, but a CRS is not.
        If df is not a DataFrame.
    """
    timer.start()

    # Do checks on passed parameters
    if type(df) != pd.DataFrame:
        raise TypeError("Pandas DataFrame expected but", type(df), "found")
    elif (x_field or y_field) and crs is None:
        raise TypeError("CRS keyword argument missing")

    # Search for X and Y fields, if not provided
    if not x_field and not y_field:
        x, y = find_xy_fields(df)

        if x == "Failed" or y == "Failed" or x is None or y is None:
            print("Couldn't find fields. Check your fields")
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
        print("Dataframe successfully converted to geopandas point geodataframe")
    except KeyError:
        gdf = -1
        print("Conversion Failed")

    timer.stop()
    return gdf


# ========================================================================= ##
# HydroRIVERS ============================================================= ##
# ========================================================================= ##


def assign_stations(edges: gpd.GeoDataFrame, stations: gpd.GeoDataFrame,
                    stat_id_f: str, prefix="", max_distance=None) -> gpd.GeoDataFrame:
    """
    Snaps stations to the closest features in edges and assigns
    descriptors to line segments. Uses a solution similar
    to connect_points_to_features().

    For each station, finds the closest line in edge and assigns
    to the selected feature the following values:
        - station id
        - dist(ance) of the closest point to the station from the
          start of the edge (u). Has been confirmed to correctly
          measure distance along bent lines.

    To deal with situations of multiple stations being assigned to
    the same edge feature, station ids and distances are stored in
    DataFrames.

    :param edges: Geopandas GeoDataFrame
        The lines/features to assign stations to.

    :param stations: Geopandas GeoDataFrame
        The station points to assign to edges.

    :param stat_id_f: string
        The name of the unique identifier field in stations.

    :param prefix: string
        Prefix to apply to added 'data' column. Useful if you need to
        assign more than 1 set of stations to edges. If left blank, may
        cause overlapping columns in output GeoDataFrame.

    :param max_distance: int or None (default)
        The maximum distance (in CRS units) within which to assign a
        station to edges. If int, must be greater than 0.

    :return: Geopandas GeoDataFrame
        A copy of edges merged that includes selected station related
        data. Has the following additional fields:
            - <prefix>_data (DataFrame)
                Contains the following columns:
                    - ID (int) of the station
                    - dist (float) from the start of the line
            - unique_ind    (int)
    """
    if stations.crs != Can_LCC_wkt:
        stations = stations.to_crs(crs=Can_LCC_wkt)
    if edges.crs != Can_LCC_wkt:
        edges = edges.to_crs(crs=Can_LCC_wkt)

    edges = edges.assign(unique_ind=edges.index)
    edges = edges.assign(other=edges.geometry)

    stations = stations.drop_duplicates(stat_id_f)

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


def bfs_search(network: nx.DiGraph, prefix1='pwqmn_', prefix2='hydat_'):
    """

    :param network:
    :param prefix1:
    :param prefix2:
    :return:
    """


def dfs_search(network: nx.DiGraph, prefix1='pwqmn_', prefix2='hydat_'):
    """
    For each station assigned to the network denoted by prefix1,
    locates 1 upstream and 1 downstream station denoted by prefix2
    using depth-first search. Stations located on the same edge are
    marked, but not counted towards the 1 upstream and 1 downstream
    stations. The located stations may not be the closest stations.

    :param network:
    :param prefix1:
    :param prefix2:
    :return: Pandas DataFrame
        DataFrame with the following columns:
            - prefix1_id (string)
            - On_segment (dict)
            - Downstream (dict)
            - Upstream   (dict)
        Where all dict are built of string:LineString key/value pairs,
        string is the ID of the prefix2 closest station, and LineString
        is the sequence of nodes that were traversed to reach that
        station. The output LineStrings represent paths along the Graph
        but it's shape is not accurate to that of the real world path
        representative along the river system.
    """
    def get_out(nbunch, data):
        """
        Wrapper to allow network.out_edges to be passed as a parameter
        because out_edges is both a network function and an attribute.
        """
        return network.out_edges(nbunch=nbunch, data=data)

    def get_in(nbunch, data):
        """
        Wrapper to allow network.in_edges to be passed as a parameter
        because in_edges is both a network function and an attribute.
        """
        return network.in_edges(nbunch=nbunch, data=data)

    def dfs(search_func, source, prefix, direction):
        """
        Traverses edges depth first search moving along the network.

        :param search_func:
        :param source:
        :param prefix:
        :param direction:

        :return:
        """
        edges = search_func(nbunch=source, data=prefix+'data')

        for u, v, data in edges:
            if type(data) in [pd.DataFrame, gpd.GeoDataFrame]:
                series = data.sort_values(by='dist').iloc[0]
                return series['ID'], (u, v)[not direction], (u, v)[direction]
            else:
                result = (*dfs(search_func, (u, v)[not direction], prefix2, direction), \
                        (u, v)[direction])
                if result != -1:
                    return result
        # This is only run if there are no edges and the function has
        # reached the end of the line
        return -1, -1

    def add_to_matches(id1, id2, path, _pos):
        matches[prefix1 + 'id'].append(id1)
        matches[prefix2 + 'id'].append(id2)
        matches['path'].append(path)
        # matches['dist'].append(_dist)
        matches['pos'].append(_pos)

    matches = {prefix1 + 'id': [], prefix2 + 'id' : [], 'path': [], 'pos': []}

    for u, v, data in network.out_edges(data=True):
        pref_1_data = data[prefix1 + 'data']
        pref_2_data = data[prefix2 + 'data']

        if type(pref_1_data) in [pd.DataFrame, gpd.GeoDataFrame]:
            for ind, station in pref_1_data.iterrows():

                if type(pref_2_data) in [pd.DataFrame, gpd.GeoDataFrame]:
                    for ind, row in pref_2_data.iterrows():
                        add_to_matches(station['ID'], row['ID'], LineString([u, v]), 'On')

                down_id, *point_list = dfs(get_out,v, prefix2, 0)
                up_id, *point_list2 = dfs(get_in, u, prefix2, 1)

                if down_id != -1:
                    add_to_matches(station['ID'], down_id, LineString(point_list), 'Down')

                if up_id != -1:
                    add_to_matches(station['ID'], up_id, LineString(point_list2), 'Up')

    return pd.DataFrame(data=matches)


def hyriv_gdf_to_network(hyriv_gdf: gpd.GeoDataFrame, plot=True, show=True) -> nx.DiGraph:
    """
    Creates a directed network from a hydroRIVER line GeoDataFrame.

    A glorified wrapper function that gives the option to plot the
    produced network against the original GeoDataFrame.

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
        # Plot
        f, ax = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
        hyriv_gdf.plot(color="k", ax=ax[0])
        for i, facet in enumerate(ax):
            facet.set_title(("Rivers", "Graph")[i])
            facet.axis("off")
        __draw_network__(p_graph, ax=ax[1])

    if show:
        plt.show()

    return p_graph


def hyriv_network_to_gdf(network, show=True, plot=True):
    nodes, edges, sw = momepy.nx_to_gdf(network)


def straighten(lines):
    pairs = []
    for line in lines.geometry:
        pairs.append(LineString(line.boundary.geoms))
    return gpd.GeoDataFrame(geometry=pairs, crs=lines.crs)


def check_hyriv_network(digraph: nx.DiGraph) -> float:
    """
    Checks a NetworkX DiGraph (directed graph) created from a
    HydroRIVERS shapefile for correct connectivity and directionality.

    Note: Reliability not guaranteed. See assumption below.

    Assumptions: If there are no edges leading away from a node,
        the node is assumed to be at the edge of the loaded bounds
        of the dataset. This means 2 edges that should share a common
        node but are disconnected will be assumed to be correct. This
        assumption is made to support connectivity checks with cropped
        HydroRIVER data.

    :param digraph: NetworkX DiGraph
        The directed graph object whose connectivity will be checked.
        Edges MUST contain the following attributes:
            - 'NEXT_DOWN'
            - 'HYRIV_ID'

    :return: float
        A decimal value representing the percentage of edges with
        correct connectivity. Between 0.0 and 1.0.
    """
    correct_edges, total_edges = 0, 0

    # Obtain from the directed graph every single edge and the ID
    # of the edge that lies directly downstream from it
    for u, v, data in digraph.edges(data="NEXT_DOWN"):
        total_edges += 1

        out_edges = digraph.out_edges(nbunch=v, data='HYRIV_ID')

        if data == 0 and len(out_edges) != 0:
            # A 'NEXT_DOWN' value of 0 indicates there is no directly
            # connected segment downstream. The presence of outgoing
            # edges indicates incorrect connectivity.
            break
        elif len(out_edges) == 0:
            # If there are no edges leading away from the node, the
            # node is assumed to be at the edge of the selected BBox
            # and connectivity assumed to be correct. This however may
            # not always be the case.
            correct_edges += 1

        for out_edge in out_edges:
            # check every edge leading away from v. If any of them
            # match the ID of NEXT_DOWN, connectivity should be correct
            if out_edge[2] == data:
                correct_edges += 1
                break

    ratio = correct_edges / total_edges
    print(f"{correct_edges}/{total_edges} ({ratio * 100}%) correct.")
    return ratio


def __draw_network__(p_graph, ax=None):
    """
    Draws a NetworkX Graph object onto an axes.

    :param p_graph: NetworkX Graph
        The graph object to draw.

    :param ax: plt.Axes object or None (default)
        The Axes to plot g_series onto. If None, creates a new Axes,
        adds it to the current figure, and uses that Axes.
    """
    if ax is None:
        ax = plt.axes()
    positions = {n: [n[0], n[1]] for n in list(p_graph.nodes)}
    nx.draw(p_graph, positions, ax=ax, node_size=3)

from gen_util import find_xy_fields, Can_LCC_wkt, check_geom, BBox

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
# Data Conversion ========================================================= ##
# ========================================================================= ##


def point_gdf_from_df(df: pd.DataFrame, x_field=None, y_field=None, crs=None,
                      query=None) -> gpd.GeoDataFrame:
    """
    Convert a pandas DataFrame to a geopandas GeoDataFrame with point
    geometry, if possible. Output GeoDataFrame is identical to input
    DataFrame with the exception of the added 'geometry' field.

    If neither x nor y fields are not provided, the function will
    search the DataFrame for fields to use with find_xy_fields().
    Conversion will fail if only 1 of x_field or y_field is provided.

    If x and y fields are not provided, the crs will be assumed to be
    EPSG:4326. If x and y fields are provided, a CRS must also be
    provided.

    :param df: pandas DataFrame
        DataFrame to convert to a GeoDataFrame.

    :param x_field: str (optional)
        Field to use as longitude/x value. If None, searches df
        for X and Y fields to use. Required if y_field is provided.

    :param y_field: str (optional)
        Field to use as latitude/y value. If None, searches df
        for X and Y fields to use. Required if y_field is provided.

    :param crs: value (optional)
        Coordinate reference system of the geometry objects. Can be
        anything accepted by pyproj.CRS.from_user_input().
        i.e.
        - WKT String (such as Can_LCC_wkt)
        - authority string ("EPSG:4326")

    :return: Geopandas GeoDataFrame or -1
        The resulting GeoDataFrame, or -1 if the conversion failed. If
        a crs is passed, the GDF will be in that crs. If lat/lon fields
        are found by find_xy_fields(), crs will be set to EPSG:4326.

    :raises TypeError:
        If x and y fields are provided, but a CRS is not.
        If df is not a DataFrame.
    """

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
        gdf.drop_duplicates(subset=[x, y], inplace=True)
        gdf.to_crs(Can_LCC_wkt)
        print("Dataframe successfully converted to geopandas point geodataframe")
    except KeyError:
        gdf = -1
        print("Conversion Failed")

    return gdf


# ========================================================================= ##
# Data Processing ========================================================= ##
# ========================================================================= ##


def connect_points_to_feature(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame) -> dict:
    """
    For each point in points, determines the closest location on other
    and creates a line between them.

    Shoutout to Brendan Ward for their Medium article:
    https://medium.com/@brendan_ward/how-to-leverage-geopandas-for-faster-snapping-of-points-to-lines-6113c94e59aa

    :param points: GeoPandas GeoDataFrame
        The point features to snap to other. Must have a set CRS.
        Must contain only Point geometry.

    :param other: GeoPandas GeoDataFrame
        GeoDataFrame to snap the points to. May be points, lines,
        or polygons, and must have a set CRS.

    :return: dict of string: GeoDataFrame
        Contains the new points on other and the lines connecting the
        original points to the new points (used for checking quality
        of point snapping). Has 2 keys: 'new_points' & 'lines'. Maintains
        the same order as points. All lines have only two vertices.
    """
    # Assert that points contains only Point features
    assert len(points.groupby(by=points.geometry.geom_type).groups) == 1,\
        "GeoDataFrame expected to only contain Points."

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

    shortest_lines = closest.geometry.shortest_line(closest['other'])

    # Potentially find a more efficient solution that doesn't use apply
    new_points = shortest_lines.apply(lambda line: Point(line.coords[1]))

    return {'new_points': new_points, 'lines': shortest_lines}


def snap_points(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame):
    """
    Snaps a set of points to the closest geometry in another set of
    features.

    Wrapper function for connect_points_to_feature() that returns only
    the points and not the connecting lines.

    :param points: gpd.GeoDataFrame
        Original point dataset.

    :param other: gpd.GeoDataFrame
        Features to snap Points to.

    :return: GeoPandas GeoDataFrame
        Point GeoDataFrame. Consult connect_points_to_feature for more
        information.
    """
    return connect_points_to_feature(points, other)['new_points']


def connectors(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame):
    """
    Finds the shortest lines between a set of points to the closest
    geometry in another set of features.

    Wrapper function for connect_points_to_feature() that returns only
    the connecting lines and not the new points.

    :return: GeoPandas GeoDataFrame
        LineString GeoDataFrame. Consult connect_points_to_feature for
        more information.
    """
    return connect_points_to_feature(points, other)['lines']


# ========================================================================= ##
# HydroRIVERS ============================================================= ##
# ========================================================================= ##


def assign_stations(edges: gpd.GeoDataFrame, stations: gpd.GeoDataFrame,
                    prefix="", max_distance=1000) -> gpd.GeoDataFrame:
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

    To address some potential issues caused by course data resolution,
    distortions caused by conversions between coordinate systems, and
    to maintain consistent distances between stations, distances are
    calculated by finding the relative position along the line in the
    set crs as a proportion. That proportion is used to determine the
    distance from the start of the line segment using the HydroRIVERS
    provided LENGTH_KM field.

    :param edges: Geopandas GeoDataFrame
        The lines/features to assign stations to. Must contain a
        LENGTH_KM field.

    :param stations: Geopandas GeoDataFrame
        The station points to assign to edges. Requires that a
        'Station_ID' field exists.

    :param prefix: string (default="")
        Prefix to apply to added 'data' column. Useful if you need to
        assign more than 1 set of stations to edges. If left blank, may
        cause overlapping columns in output GeoDataFrame.

    :param max_distance: int (default=1000)
        The maximum distance (in CRS units) within which to assign a
        station to edges. If int, must be greater than 0. Default
        1000 (meters; Lambert Conformal Conic units ).

    :return: Geopandas GeoDataFrame
        A copy of edges merged that includes selected station related
        data. Has the following additional fields:

        <prefix>_data (DataFrame)
            Contains the following columns:
            - ID (int) of the station
            - geometry (geometry)
                Shapely object representing original
                station location.
            - dist (float)
                Distance in meters) from the start of the river segment
                to the point closest to the station. Calculated by
                finding the relative position along the line as a
                proportion and determining the distance using the
                HydroRIVERS provided length field (LENGTH_KM).

        unique_ind (int)
            Used as a unique identifier for joining and merging data.

    :raises ValueError:
        If stations contains geometries aside from Points
        If edges contains geometries aside from LineStrings

    :raises KeyError:
        If stations doesn't contain a 'Station_ID' field.
    """
    # check inputs
    if not check_geom(stations, 'Point'):
        raise ValueError("Station GeoDataFrame expected to only contain Points.")
    if not check_geom(edges, 'LineString'):
        raise ValueError("Edge GeoDataFrame expected to only contain LineStrings.")
    if not ('Station_ID' in stations.columns):
        raise ValueError('Stations GeoDataFrame does not contain required "Station_ID" field.')
    if not ('LENGTH_KM' in edges.columns):
        raise ValueError('Warning: Edges GeoDataFrame does not contain required "LENGTH_KM" field.')

    if stations.crs != Can_LCC_wkt:
        stations = stations.to_crs(crs=Can_LCC_wkt)
    if edges.crs != Can_LCC_wkt:
        edges = edges.to_crs(crs=Can_LCC_wkt)

    edges = edges.assign(unique_ind=edges.index, other=edges.geometry,
                         LENGTH_M=edges['LENGTH_KM'] * 1000)

    stations = stations.drop_duplicates('Station_ID')
    stations = stations.sjoin_nearest(edges, how='left', max_distance=max_distance)

    rel_pos = stations['other'].project(stations.geometry) / stations['other'].length
    stations = stations.assign(dist=rel_pos * stations['LENGTH_M'])
    stations = stations[['Station_ID', 'unique_ind', 'dist', 'geometry']]

    grouped = stations.groupby(by='unique_ind', sort=False)

    temp_data = {'unique_ind': [], prefix + 'data': []}
    for ind, data in grouped:
        temp_data['unique_ind'].append(ind)
        temp_data[prefix + 'data'].append(data[['Station_ID', 'dist', 'geometry']])

    temp = pd.DataFrame(data=temp_data)
    return edges.merge(temp, on='unique_ind', how='left')


def bfs_search(network: nx.DiGraph, prefix1='pwqmn_', prefix2='hydat_'):
    """

    :param network:
    :param prefix1:
    :param prefix2:
    :return:
    """


def dfs_search(network: nx.DiGraph, prefix1='hydat_', prefix2='pwqmn_',
               max_distance=10000, max_depth=10, direct_match_dist=350):
    """
    For each station assigned to the network denoted by prefix1,
    locates 1 upstream and 1 downstream station denoted by prefix2
    using depth-first search. Stations located on the same edge are
    marked, but not counted towards the 1 upstream and 1 downstream
    stations. The located stations may not be the closest stations.

    All edges in the provided Directed Graph must contain an edge
    attribute for each prefix suffixed by "_data". To encode
    this data to the network, assign stations to the GeoDataFrame
    before converting it to a Network using assign_stations().

    Distance accumulation is calculated using 2 network edge
    attributes; the 'LENGTH_M' attribute (length of the river reach
    segment, in meters) derived from 'LENGTH_KM' provided as part of
    the HydroRIVERS data, and edge attributes suffixed with '_data'
    that hold information about the stations encoded to that edge in
    DataFrames. Said DataFrames MUST contain a 'dist' column.

    For stations located on the same river segment/network edge,
    distance between matched stations is computed geographically.

    :param network: NetworkX Directed Graph
        The graph to search. Must contain station data stored as
        edge attributes.

    :param prefix1: string (default='hydat_')
        Prefix denoting the network edge attribute holding origin
        station data.

    :param prefix2: string (default='pwqmn_')
        Prefix denoting the network edge attribute holding candidate
        station data.

    :param max_distance: int (default=10000)
        Maximum distance to search for a matching station in CRS units.

    :param max_depth: int (default=10)
        The maximum number of river segments to traverse from an origin
        station to search for a match. The greater the resolution of the
        dataset used to build the network, the greater this value should
        be. (HYDAT -> 10; OHN -> 100)

    :param direct_match_dist: int (default=350)
        The maximum distance in CRS units between two stations at which
        it is assumed the most accurate measure of distance along the
        river from origin to candidate is the direct distance between
        the two points. The greater the resolution of the dataset used
        to build the network, the lower this value should be.
            (HYDAT -> 350; OHN -> 100)

    :return: Pandas DataFrame
        DataFrame with the following columns:
            - prefix1_id (string)
                Origin station ID.
            - prefix2_id (string)
                ID of the station matched to the origin station.
            - path (geometry; LineString)
                Path from the origin station to the matched station,
                following network nodes.
            - dist (float)
                Distance along the river network between matched
                stations.
            - pos (string)
                One of "On", "Downstream", "Upstream" indicating
                the relative position of the matched station.
            - seg_apart (int)
                The number of river segments separating the origin and
                matched station. Stations on the same segment will have
                a value of 0.
    """
    def bfs(source):
        pass

    def dfs(source, prefix, direction, cum_dist, depth):
        """
        Traverses edges recursively along the network depth-first.
        Does not accept candidates that are greater than max_distance
        units or max_depth segments away.

        :param source:
            Source node key to search from.

        :param prefix: string
            Prefix of candidate station data.

        :param direction: int (0 or 1)
            Integer flag indicating direction to search.
            0=Downstream, 1=Upstream.

        :param cum_dist: float
            Approximate cumulative distance from origin node.

        :param depth: int
            The number of segments that have been traversed.

        :return:
            If search was successful:

                ID (str), dist (float), depth (int), cord_n (tuple), ... ,cord_0 (tuple)

                Where cord_n is the location of the matched candidate
                station, cord_0 is the location of the origin station,
                and all cords in between are that of network nodes
                between the origin and matched station.

            If search was unsuccessful:
                -1, -1, -1
        """
        if direction == 0:
            edges = network.out_edges(nbunch=source, data=True)
        elif direction == 1:
            edges = network.in_edges(nbunch=source, data=True)
        else:
            raise ValueError('Invalid direction')

        if cum_dist >= max_distance or len(edges) == 0 or depth >= max_depth:
            return -1, -1, -1

        for u, v, data in edges:
            if type(data[prefix + 'data']) in [pd.DataFrame, gpd.GeoDataFrame]:
                series = data[prefix + 'data'].sort_values(
                    by='dist', ascending=not direction
                ).iloc[0]
                dist = cum_dist + abs(direction * data['LENGTH_M'] - series['dist'])

                if dist < max_distance:
                    return series['Station_ID'], dist, depth, series['geometry'], (u, v)[direction]
                return -1, -1, -1
            else:
                result = *dfs((u, v)[not direction], prefix2, direction,
                              cum_dist + data['LENGTH_M'], depth + 1), \
                          (u, v)[direction]

                if result[0] != -1:
                    return result
        # This is only run if there are no edges and the function has
        # reached the end of the line
        return -1, -1, -1

    def add_to_matches(id1, id2, path, _dist, _pos, depth):
        """
        Helper function that adds a set of values to a dictionary with specific keys.
        """
        matches[prefix1 + 'id'].append(id1)
        matches[prefix2 + 'id'].append(id2)
        matches['path'].append(path)
        matches['dist'].append(_dist)
        matches['pos'].append(_pos)
        matches['seg_apart'].append(depth)

    def on_segment():
        on_dist = station['geometry'].distance(row['geometry'])
        if on_dist > direct_match_dist:
            on_dist = abs(station['dist'] - row['dist'])

        if on_dist < max_distance:
            pos = 'On-' + ('Up' if station['dist'] > row['dist'] else 'Down')

            add_to_matches(station['Station_ID'], row['Station_ID'],
                           LineString([station['geometry'], row['geometry']]),
                           on_dist, pos, 0)

    def off_segment():
        # Check for candidate stations upstream and downstream
        down_id, down_dist, down_depth, *point_list = dfs(v, prefix2, 0, data['LENGTH_M'] - station['dist'], 1)
        up_id, up_dist, up_depth, *point_list2 = dfs(u, prefix2, 1, station['dist'], 1)

        if down_id != -1:
            point_list.append(station['geometry'])
            add_to_matches(station['Station_ID'], down_id, LineString(point_list),
                           down_dist, 'Down', down_depth)

        if up_id != -1:
            point_list2.append(station['geometry'])
            add_to_matches(station['Station_ID'], up_id, LineString(point_list2),
                           up_dist, 'Up', up_depth)

    # ===================================================================== #
    # Instantiate dictionary to store matches
    matches = {prefix1 + 'id': [], prefix2 + 'id' : [], 'path': [],
               'dist': [], 'pos': [], 'seg_apart': []}

    # check each edge for origin stations
    for u, v, data in network.out_edges(data=True):
        pref_1_data = data[prefix1 + 'data']
        pref_2_data = data[prefix2 + 'data']

        # check for the presence of origin station data
        if type(pref_1_data) in [pd.DataFrame, gpd.GeoDataFrame]:
            # for each origin station on the edge
            for ind, station in pref_1_data.iterrows():
                # Check if there are candidate stations on the same river segment
                if type(pref_2_data) in [pd.DataFrame, gpd.GeoDataFrame]:
                    # Add each candidate on the same segment to matches
                    for ind, row in pref_2_data.iterrows():
                        on_segment()
                # search for candidate stations on connected river segments
                off_segment()

    return pd.DataFrame(data=matches)


def hyriv_gdf_to_network(hyriv_gdf: gpd.GeoDataFrame, plot=False, show=False) -> nx.DiGraph:
    """
    Creates a directed network from a hydroRIVER line GeoDataFrame.

    A glorified wrapper function that gives the option to plot the
    produced network against the original GeoDataFrame. Refer to the
    momepy documentation for more information about gdf_to_nx().

    Link: https://docs.momepy.org/en/stable/generated/momepy.gdf_to_nx.html#momepy.gdf_to_nx

    :param hyriv_gdf: Geopandas GeoDataFrame
        The GeoDataFrame to turn into a directed network.

    :param plot: bool (default=False)
        If True, plot a network/original line dataset comparison
        to matplotlib.pyplot. If False, do nothing.

    :param show: bool (default=False)
        If True, display the plot. If False, do nothing.

    :return: networkX DiGraph
        The resultant networkx directed graph.
    """
    hyriv_gdf = hyriv_gdf.to_crs(crs=Can_LCC_wkt)
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


def straighten(lines):
    """
    Produces a set of lines from the start and end point of
    each line in liens.

    :param lines: GeoDataFrame
        The line features to straighten. Must contain only lines.

    :return: GeoDataFrame
        The straightened lines.
    """
    pairs = []
    for line in lines.geometry:
        pairs.append(LineString(line.boundary.geoms))
    return gpd.GeoDataFrame(geometry=pairs, crs=lines.crs)


def __draw_network__(p_graph, ax=None, **kwargs):
    """
    Draws a NetworkX Graph object onto an axes.

    :param p_graph: NetworkX Graph
        The graph object to draw.

    :param ax: plt.Axes object (optional)
        The Axes to plot g_series onto. If None, creates a new Axes,
        adds it to the current figure, and uses that Axes.
    """
    if ax is None:
        ax = plt.axes()
    positions = {n: [n[0], n[1]] for n in list(p_graph.nodes)}
    nx.draw(p_graph, pos=positions, ax=ax, node_size=3, **kwargs)


def subset_df(df: pd.DataFrame, **kwargs):
    for key in kwargs.keys():
        value = kwargs[key]

        # Extents subsetting untested
        if key.upper() == 'EXTENT':
            if type(value) in [list, tuple]:
                minx, miny, maxx, maxy = value
            elif type(value) is BBox:
                minx, miny, maxx, maxy = value.to_tuple()
            df = df.query('@minx <= Longitude <= @maxx and'
                          '@miny <= Longitude <= @maxy')
        else:
            if type(value) in [list, tuple]:
                mod = 'in'
            else:
                mod = '=='
            df = df.query(f'{key} {mod} @value')

    return df

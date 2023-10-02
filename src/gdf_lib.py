import os
import webbrowser
import random
from classes import BBox, Timer
from load_data import proj_path, find_xy_fields, data_path

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
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


# default save directories within the project scope
plot_save_dir = os.path.join(proj_path, "plots")
map_save_dir = os.path.join(proj_path, "maps")

timer = Timer()


# Coordinate Reference System Constants
geodetic = ccrs.Geodetic()
albers = ccrs.AlbersEqualArea(central_longitude=-85, central_latitude=50)

# standard parallels were taken from stats canada
lambert = ccrs.LambertConformal(central_longitude=-85, central_latitude=50,
                                standard_parallels=(46, 77),
                                cutoff=30)

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
                    'PARAMETER["latitude_of_origin",40],'
                    'PARAMETER["central_meridian",-96]'
                    'PARAMETER["standard_parallel_1",50],'
                    'PARAMETER["standard_parallel_2",70],'
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
    points = points.to_crs(crs=Can_LCC_wkt)
    other = other.to_crs(crs=Can_LCC_wkt)

    other = other.assign(unique_ind=other.index)
    closest = points.sjoin_nearest(other, how='left', distance_col='distance')

    # Lines is completely normal up to here
    closest = closest.merge(other.rename(columns={'geometry': 'other'}),
                            how='left',
                            on='unique_ind')

    shortest_lines = closest.geometry.shortest_line(closest['other'])
    new_points = shortest_lines.apply(lambda line: Point(line.coords[1]))

    data = {'new_points': gpd.GeoSeries(new_points),
            'lines': gpd.GeoSeries(shortest_lines)}

    return data


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

# HydroRIVERS ============================================================= ##


def load_hydro_rivers(sample=None, bbox=None) -> gpd.GeoDataFrame:
    """
    Loads HydroRIVERS_v10.shp as a geopandas GeoDataFrame

    Note: As BBox grows larger, spatial distortion increases.
    Attempting to place geometry features outside the projection's
    supported bounds may result in undesirable behaviour. Refer
    to https://epsg.io/102002 (which describes features of projection
    defined by Can_LCC_wkt) for the projected and WGS84 bounds.

    :param sample:

    :param bbox: <BBox> or None
        BBox object declaring area of interest or None, indicating
        not to filter by a bounding box

    :return: <Geopandas GeoDataFrame>
    """
    hydro_path = os.path.join(
        data_path, os.path.join("Hydro_RIVERS_v10", "HydroRIVERS_v10_na.shp"))

    data = gpd.read_file(hydro_path, rows=sample, bbox=BBox.to_tuple(bbox))
    return data.to_crs(crs=Can_LCC_wkt)


def snap_to_hyriv(points: gpd.GeoDataFrame, hyriv: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Wrapper function for snapping points to hyriv lines

    :param points:
    :param hyriv:
    :return:
    """
    return connect_points_to_feature(points, hyriv)


def hyriv_gdf_to_network(hyriv_gdf: gpd.GeoDataFrame, plot=False) -> nx.DiGraph:

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

        plt.show()

    return p_graph


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
        print(f"next down: {data}")
        total_edges += 1

        out_edges = digraph.out_edges(nbunch=v, data='HYRIV_ID')
        if len(out_edges) == 0:
            correct_edges += 1
        for out_edge in out_edges:
            if out_edge[2] == data or out_edge[2] == 0:
                correct_edges += 1
                break

    ratio = correct_edges / total_edges

    print(f"{correct_edges}/{total_edges} ({ratio * 100}%) correct.")

    return ratio


def get_hyriv_network(bbox=None, sample=None) -> nx.DiGraph:
    """
    Wrapper function for generating the HydroRIVERS directed graph.
    :return: NetworkX DiGraph
    """
    hyriv = load_hydro_rivers(sample=sample, bbox=bbox)
    return hyriv_gdf_to_network(hyriv)


# ========================================================================= ##
# Other =================================================================== ##
# ========================================================================= ##


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
            crs = "EPSG:4326"
    else:
        x, y = x_field, y_field

    print(f"Attempting conversion with the following CRS parameter:\n{crs}")
    try:
        gdf = gpd.GeoDataFrame(
            df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs=crs)
        print("Dataframe successfully converted to geopandas point array")
    except KeyError:
        gdf = -1
        print("Conversion Failed")

    timer.stop()
    return gdf


# ========================================================================= ##
# Data Mapping ============================================================ ##
# ========================================================================= ##


def map_gdfs(gdfs_to_map):
    """

    :param gdfs_to_map

    :return:
    :return: < gem
    """
    def check_gdfs_iter(gdfs):
        if type(gdfs) == dict:
            gdfs = list(gdfs.values())
        elif not hasattr(gdfs, '__iter__'):
            gdfs = [gdfs, ]
        return gdfs

    color_list = ['red', 'blue', 'yellow', 'purple', 'black']

    def explore_recursive(gdf_list, n):
        m = None
        if n < len(gdf_list) - 1:
            m = explore_recursive(gdf_list, n + 1)
        return gdf_list[n].explore(m=m, style_kwds={'color': color_list[random.randint(0,5)]},
                                   marker_kwds={'radius': 4})

    gdfs_to_map = check_gdfs_iter(gdfs_to_map)
    m = explore_recursive(gdfs_to_map, 0)
    outpath = os.path.join(map_save_dir, "map.html")
    m.save(outpath)
    webbrowser.open(outpath)


# ========================================================================= ##
# Data Plotting =========================================================== ##
# ========================================================================= ##


def plot_g_series(g_series: gpd.GeoSeries, name="", save=False,
                  show=True, add_bg=True, **kwargs):
    """
    Plot a Geopandas GeoSeries.

    :param g_series: Geopandas GeoSeries
        GeoSeries to plot

    :param name: string
        Name to save the plot to

    :param save: bool
        If True, save the plot to disk. If False, do nothing.

    :param show: bool
        If True, display the plot. If False, do nothing

    :param add_bg: bool
        If True, add a background to the plot. If False, do nothing

    :param kwargs:
        keyword arguments to pass when adding g_series data to the plot
    """
    g_series = g_series.to_crs(crs=Can_LCC_wkt)

    if add_bg:
        plt.figure(figsize=(8, 8))
        ax = plt.axes(projection=lambert)

        print(g_series.total_bounds)

        # check if the GeoSeries has a valid bounding information
        if all(g_series.total_bounds):

            min_lon, min_lat, max_lon, max_lat = g_series.total_bounds

            width = max_lon - min_lon
            height = max_lat - min_lat

            lon_buffer = width * 0.2
            lat_buffer = width * 0.2

            center = width / 2 + min_lon, height / 2 + min_lat

            x0 = center[0] - max(width, height) / 2 - lon_buffer
            x1 = center[0] + max(width, height) / 2 + lon_buffer
            y0 = center[1] - max(width, height) / 2 + lat_buffer
            y1 = center[1] + max(width, height) / 2 + lat_buffer

            ax.set_extent([x0, x1, y0, y1], crs=lambert)

            ax.stock_img()
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS)
            ax.add_feature(cfeature.STATES)
        else:
            print("GeoSeries has invalid boundary information. No background will"
                  "be added. Proceeding with plotting.")

    if g_series.geom_type[0] == "Point":
        plt.scatter(g_series.x, g_series.y, **kwargs)

    elif g_series.geom_type[0] == "LineString":
        for line in g_series:
            plt.plot(*line.xy, **kwargs)

    if show:
        plt.show()


def plot_gdf(gdf: gpd.GeoDataFrame, name="", save=False, add_bg=True,
             show=True, **kwargs):
    """
    Plot a geopandas GeoDataFrame on a matplotlib plot

    :param gdf: Geopandas GeoDataFrame

    ::param name: string
        Name to save the plot to

    :param save: bool
        If True, save the plot to disk. If False, do nothing.

    :param show: bool
        If True, display the plot. If False, do nothing

    :param add_bg: bool
        If True, add a background to the plot. If False, do nothing

    :param kwargs:
        keyword arguments to pass when adding g_series data to the plot
    """
    plot_g_series(gdf.geometry, name=name, save=save, add_bg=add_bg,
                  show=show, **kwargs)


def plot_df(df: pd.DataFrame, save=False, name="", **kwargs):
    """
    Plot a pandas DataFrame as point data, if possible. Does not
    return the resulting GeoDataFrame; to get the resulting
    GeoDataFrame, use point_gdf_from_df(), then plot the result with
    plot_gdf().

    :param df: <Pandas DataFrame>
        DataFrame to be plotted

    :param save: bool
        Whether to save the plot to disk

    :param name: string
        File name to save the plot to if save == True

    :raises TypeError:
        Ff df is not a Pandas DataFrame
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    output = point_gdf_from_df(df)

    # Only try to plot the output if the conversion was successful
    if type(output) is gpd.GeoDataFrame:
        plot_gdf(output, save=save, name=name, **kwargs)
    else:
        print(name + " could not be plotted")


def plot_closest(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame):
    """
    For each point in points, finds the closest feature in other, then
    plots both GeoDataFrames and draws lines between them.

    :param points: Geopandas GeoDataFrame
        Origin points.

    :param other: Geopandas GeoDataFrame
        Candidate geometry.
    """
    snapped_dict = connect_points_to_feature(points, other)

    new_points = snapped_dict['new_points']
    lines = snapped_dict['lines']

    plot_g_series(lines, show=False, zorder=1, color='purple', label='connector')
    plot_gdf(other, show=False, add_bg=False, color='red', zorder=9, label='new')
    plot_gdf(points, show=False, add_bg=False, color='blue', zorder=10, label='original')

    plt.show()

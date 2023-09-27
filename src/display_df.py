import os
import webbrowser
import random
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely import LineString, Point
import numpy as np
from timer import Timer
from load_data import proj_path, find_xy_fields, data_path

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
# Data Processing ========================================================= ##
# ========================================================================= ##


def load_hydro_rivers(sample=None) -> gpd.GeoDataFrame:
    """
    Loads HydroRIVERS as a geopandas GeoDataFrame

    :return: <Geopandas GeoDataFrame>
    """
    hydro_path = os.path.join(
        data_path, os.path.join("Hydro_RIVERS_v10", "HydroRIVERS_v10.shp"))
    return gpd.read_file(hydro_path, rows=sample)


def pair_points(origins: gpd.GeoDataFrame, cand: gpd.GeoDataFrame):
    """
    For each point in origin, finds the point in to_pair spatially
    closest to it. Origins and cand must be spatially referenced and
    have assigned coordinate reference systems.

    Produces geometry and coordinates in the Canadian Lambert Conformal
    Conic coordinate reference system. WKT string at top of file.

    :param origins:
        The points for whom to pair to points in to_pair.

    :param cand:
        The candidate points to be matched to points in origin.

    :return: <Geopandas GeoDataFrame>
        The result of spatially joining cand to origins with an inner
        join. The geometry of the returned GeoDataFrame is that of the
        origin point in Canada Lambert Conformal Conic. The produced
        GeoDataFrame is guaranteed to have the following fields:

            orig_x, orig_y, cand_x, cand_y

        These fields refer to Canada Lambert Conformal Conic
        coordinates of the origin and matched candidate points.
    """
    origins.to_crs(crs=Can_LCC_wkt, inplace=True)
    cand.to_crs(crs=Can_LCC_wkt, inplace=True)

    origin_x, origin_y = origins.geometry.x, origins.geometry.y
    cand_x, cand_y = cand.geometry.x, cand.geometry.y

    # Write geometry coordinates to X and Y fields
    # This makes the following operations not dependent on the gdfs
    # containing specific field names
    origins.assign(orig_x=origin_x, orig_y=origin_y)
    cand.assign(cand_x=cand_x, orig_y=cand_y)

    origins.drop_duplicates(subset=['orig_x', 'orig_y'])
    cand.drop_duplicates(subset=['cand_x', 'cand_y'])

    joined = origins.sjoin_nearest(cand, distance_col='Distance')

    return joined


def snap_points_to_line(points: gpd.GeoDataFrame, lines: gpd.GeoDataFrame):
    """
    Code source and explanation can be found here:
    https://medium.com/@brendan_ward/how-to-leverage-geopandas-for-faster-snapping-of-points-to-lines-6113c94e59aa

    :param points:
    :param lines:
    :return:
    """
    points.to_crs(crs=Can_LCC_wkt, inplace=True)
    lines.to_crs(crs=Can_LCC_wkt, inplace=True)

    joined = lines.sjoin_nearest(points, distance_col='distance')
    joined['points'] = points.geometry

    pos = joined.geometry.project(gpd.GeoSeries(joined['points']))
    joined.geometry.interpolate(pos)

    print(joined.dtypes)
    print(joined.head())

    return gpd.GeoDataFrame(joined, geometry='points', crs=Can_LCC_wkt)


# ========================================================================= ##
# Data Mapping ============================================================ ##
# ========================================================================= ##


def map_gdfs(gdfs_to_map):
    """

    :param gdfs_to_map

    :return:
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

    :param g_series:
        A Geopandas GeoSeries
    :param name: name to save the plot to
    :param save: True or False; whether to save the plot to disk
    :param show: True of False; whether to display the plot
    :param add_bg: True or False; whether to add a background to
                    the plot
    :param kwargs: keyword arguments to pass when adding g_series
                    data to the plot
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

    :param gdf: the geopandas GeoDataFrame to be plotted
    :param name: name to save the plot to
    :param save: True or False; whether to save the plot to disk
    :param add_bg: True or False; whether to add a background to
                    the plot
    :param show: True or False; whether to display the plot or not
    :param kwargs: keyword arguments to pass when adding the
                    data to the plot
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


def plot_closest(gdf_1: gpd.GeoDataFrame, gdf_2: gpd.GeoDataFrame, show=True):
    latlon_pairs = pair_points(gdf_1, gdf_2)

    lines = []
    for i, series in latlon_pairs.iterrows():
        lines.append(LineString([
            [series['LONGITUDE'], series['LATITUDE']],
            [series['Longitude'], series['Latitude']]
        ]))

    lines = gpd.GeoSeries(lines)

    plot_g_series(lines, show=False, zorder=1, solid_capstyle='round')
    plot_gdf(gdf_1, show=False, add_bg=False, color='purple', zorder=9)
    plot_gdf(gdf_2, show=False, add_bg=False, color='blue', zorder=10)

    if show:
        plt.show()

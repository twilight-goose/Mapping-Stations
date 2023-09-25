import os
import webbrowser
import random
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import shapely
from timer import Timer
from load_data import proj_path, find_xy_fields

"""
display_df.py

Summary:
Provides a variety of functions for conversion and display of
pandas DataFrames with compatible structures

Functions that plot or map gdfs will never produce output; to get
the resulting gdf, call the correct conversion function to obtain
the gdf and plot it separately.
"""

plot_save_dir = os.path.join(proj_path, "plots")
map_save_dir = os.path.join(proj_path, "maps")
timer = Timer()

# set a default crs to convert all longitude/latitude coordinates to
# Equal area projection chosen to preserve accuracy when searching for
# closest points
geodetic = ccrs.Geodetic()
albers = ccrs.AlbersEqualArea(central_longitude=-85, central_latitude=50)

# standard parallels were taken from stats canada
lambert = ccrs.LambertConformal(central_longitude=-85, central_latitude=50,
                                standard_parallels=(46, 77),
                                cutoff=30)
# lambert = ccrs.epsg(3348)


def point_gdf_from_df(df: pd.DataFrame, x_field="", y_field="") -> gpd.GeoDataFrame:
    """
    Convert a pandas DataFrame to a geopandas GeoDataFrame with point
    geometry, if possible

    If x and y fields are not provided, the function will search the
    DataFrame for fields to use with find_xy_fields()

    :param df: pandas DataFrame to convert
    :param x_field: field to use as longitude (optional)
    :param y_field: field to use as latitude (optional)

    :return gdf: the converted gdf, or -1 if the conversion failed
    """
    timer.start()

    if type(df) != pd.DataFrame:
        raise TypeError("Pandas DataFrame expected but", type(df), "found")

    if not x_field and not y_field:
        x, y = find_xy_fields(df)
    else:
        x, y = x_field, y_field

    gdf = -1        # default output value, indicates if an error occurred

    if x == "Failed" or y == "Failed" or x == "" or y == "":
        print("X/Y field not found. Operation Failed")
    else:
        try:
            gdf = gpd.GeoDataFrame(
                df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs=4326)
            print("X/Y fields found. Dataframe converted to geopandas point array")
        except KeyError:
            print("X/Y field not found. Operation Failed")

    timer.stop()
    return gdf


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


def plot_g_series(g_series: gpd.GeoSeries, name="", save=False):
    """
    Plot a Geopandas GeoSeries.

    :param g_series:
    :param name:
    :param save:
    :return:
    """
    if all(g_series.total_bounds):
        min_lon, min_lat, max_lon, max_lat = g_series.total_bounds

        lon_buffer = (max_lon - min_lon) * 0.2
        lat_buffer = (max_lat - max_lat) * 0.2

        ax = plt.axes(projection=lambert)
        ax.set_extent([min_lon - lon_buffer, max_lon + lon_buffer,
                       min_lat - lat_buffer, max_lat + lat_buffer])
        ax.stock_img()
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(cfeature.STATES)

        if g_series.geom_type[0] == "Point":

            plt.scatter(g_series.x, g_series.y, color='red', transform=geodetic)

        elif g_series.geom_type[0] == "LineString":

            for line in g_series:
                plt.plot(*line.xy, color='red', transform=geodetic)

        plt.show()


def plot_gdf(gdf: gpd.GeoDataFrame, name="", save=False, **kwargs):
    """
    Plot a geopandas GeoDataFrame on a matplotlib plot

    :param gdf: the geopandas GeoDataFrame to be plotted
    :param name: name to save the plot to
    :param save: True or False; whether to save the plot to disk
    :param kwargs:
    """
    g_series = gdf.geometry
    plot_g_series(g_series, name, save)


def plot_df(df: pd.DataFrame, save=False, name="", **kwargs):
    """
    Plot a pandas DataFrame as point data, if possible. Does not
    return the resulting GeoDataFrame; to get the resulting
    GeoDataFrame, use point_gdf_from_df() and plot the result with
    plot_gdf()

    :param df: Pandas DataFrame to be plotted
    :param save: True or False; whether to save the plot to disk
    :param name: name to save the plot to

    :raises TypeError: if df is not a Pandas DataFrame
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    output = point_gdf_from_df(df)

    # Only try to plot the output if the conversion was successful
    if type(output) is gpd.GeoDataFrame:
        plot_gdf(output, save=save, name=name, **kwargs)
    else:
        print(name + " could not be plotted")


def convert_all(datasets: dict) -> dict:
    """

    :param datasets:
    :return:
    """
    ds_names = datasets.keys()
    gdf = None
    gdfs = {}

    for ds_name in ds_names:
        dataset = datasets[ds_name]

        if type(dataset) is pd.DataFrame:
            gdf = point_gdf_from_df(dataset)

        # if the conversion was successful, add it to the output dict
        if type(gdf) is gpd.GeoDataFrame:
            gdfs[ds_name] = gdf

    return gdfs


def plot_closest(gdf_1: gpd.GeoDataFrame, gdf_2: gpd.GeoDataFrame):
    joined = gdf_1.sjoin_nearest(gdf_2, max_distance=1000, distance_col='Distance')


def plot_all(datasets, save=False):
    """
    Plots all georeferenced data in data_dict.

    Produces a geodataframe from every dataset in datasets where it is
    possible and plots them. Does not produce output

    :param datasets: dict of <dataset name>: data where

                data = <pandas DataFrame> or <dict>

                    if data is a dict, data is expected to have a
                    specific structure

    :param save: bool; whether to save the plotted data
    """
    gdfs = convert_all(datasets)

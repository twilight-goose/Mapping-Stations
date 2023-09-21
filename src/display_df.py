import os
import webbrowser
import random
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
from timer import Timer
from load_data import proj_path, find_xy_fields


plot_save_dir = os.path.join(proj_path, "plots")
map_save_dir = os.path.join(proj_path, "maps")
timer = Timer()

# set a default crs to convert all longitude/latitude coordinates to
# Equal area projection chosen to preserve accuracy when searching for
# closest points
default_crs = 'EPSG:3348'


def __map_result(map_result, gdf, popup, color, tooltip):
    """

    :param map_result:
    :param gdf:
    :param popup:
    :param color:
    :param tooltip:
    :return:
    """
    if map_result:
        m = gdf.explore(popup=popup, color=color, tooltip=tooltip)
        save_path = os.path.join(map_save_dir, "map.html")
        m.save(save_path)
        webbrowser.open(save_path)


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
                df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs=default_crs)
            print("X/Y fields found. Dataframe converted to geopandas point array")
        except KeyError:
            print("X/Y field not found. Operation Failed")

    timer.stop()
    return gdf


def check_gdfs_iter(gdfs):
    if type(gdfs) == dict:
        gdfs = list(gdfs.values())
    elif not hasattr(gdfs, '__iter__'):
        gdfs = [gdfs, ]
    return gdfs


def map_gdfs(gdfs_to_map):
    """

    :param gdfs_to_map

    :return:
    """
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


def plot_gdf(gdf: gpd.GeoDataFrame, name="", save=False, **kwargs):
    """
    Plot a geopandas GeoDataFrame on a matplotlib plot

    :param gdf: the geopandas GeoDataFrame to be plotted
    :param name: name to save the plot to
    :param save: True or False; whether to save the plot to disk
    :param kwargs:

    :return:
    """
    if type(gdf) is gpd.GeoDataFrame:

        ax = gdf.plot(figsize=(6, 6), aspect=6)
        cx.add_basemap(ax, crs=gdf.crs)

        if save:
            ax.set_aspect(2)
            plt.savefig(os.path.join(plot_save_dir, name + "_plot.png"))

            print(f"Plot successfully saved to {name}_plot.png\n")
        plt.clf()
    else:
        print(name, "could not be plotted")


def plot_df(df: pd.DataFrame, save=False, name="", **kwargs):
    """
    Plot a pandas DataFrame as point data, if possible

    :param df: Pandas DataFrame to be plotted
    :param save: True or False; whether to save the plot to disk
    :param name: name to save the plot to

    :return:

    :raises TypeError: if df is not a Pandas DataFrame
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    plot_gdf(point_gdf_from_df(df), save=save, name=name, **kwargs)


def gdf_from_pwqmn(pwqmn_dict):
    """
    Generates a gdf from a dict of a specific structure.

    :param pwqmn_dict: input dict with a specific structure.

    Expected structure:

        pwqmn_dict = {<str station number>: table_data>, ...}

            pwqmn_dict is a dict of length n where n is the number of
            unique station numbers in the HYDAT sqlite3 database.

        table_data = {<str table name>: <pandas DataFrame>, ...}

            table_data is a dict of length n where n is the number of
            tables that the station number appears in

    :return:

    :raises DataStructureError:

            Raises a custom error 'DataStructureError' if pwqmn_dict
            does not have the expected structure.
    """


def plot_pwqmn(pwqmn_dict):
    """
    Plots PWQMN data

    :param pwqmn_dict: a dict with a specific structure

    :return:
    """


def plot_all(datasets, save=False):
    """
    Plots all georeferenced data in data_dict

    :param datasets: dict of <dataset name>: data where

                data = <pandas DataFrame> or <dict>

                    if data is a dict, data is expected to have a
                    specific structure

    :param save: bool; whether to save the plotted data

    :return:
    """
    ds_names = datasets.keys()

    for ds_name in ds_names:
        dataset = datasets[ds_name]
        if type(dataset) is pd.DataFrame:
            plot_df(dataset, name=ds_name, save=save)
        elif type(dataset) is dict:
            plot_pwqmn(dataset)

import os
import webbrowser
import random
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
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
default_crs = 'EPSG:3348'


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
            gdf.to_crs(epsg=3348, inplace=True)
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
    """

    ax = gdf.plot(figsize=(8, 8))

    print(gdf.crs.to_string())

    if save:
        plt.savefig(os.path.join(plot_save_dir, name + "_plot.png"))
        print(f"Plot successfully saved to {name}_plot.png\n")

    print("plotting")
    plt.show()


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


def gdf_from_hydat(hydat_dict: dict) -> gpd.GeoDataFrame:
    """

    :param hydat_dict: input dict with a specific structure.

    Expected structure:

        hydat_dict = {<str station number>: table_data>, ...}

            hydat_dict is a dict of length n where n is the number of
            unique station numbers in the HYDAT sqlite3 database.

        table_data = {<str table name>: <pandas DataFrame>, ...}

            table_data is a dict of length n where n is the number of
            tables that the station number appears in

    :return:
    """


def gdf_from_pwqmn(pwqmn_list: dict) -> gpd.GeoDataFrame:
    """
    Generates a gdf from a dict of a specific structure.

    :param pwqmn_list: dict of station_info: station_data pairs where

                station_info is a tuple length 6 of strings in the
                following order:
                    (<Name>, <Location ID>, <Longitude>, <Latitude>, <Variables>)

                station_data is a <pandas DataFrame> of valid data entries

    :return: <Geopandas.GeoDataFrame>

    :raises DataStructureError:

            Raises a custom error 'DataStructureError' if pwqmn_dict
            does not have the expected structure.
    """

    pwqmn_station_info = [key for key in pwqmn_list.keys()]
    print(pwqmn_station_info)
    df = pd.DataFrame(data=pwqmn_station_info, columns=["Name", "Location ID", "Longitude", "Latitude", "Variables"])
    gdf = point_gdf_from_df(df)

    return gdf


def plot_pwqmn(pwqmn_list: list):
    """
    Plots PWQMN data. Does not return the resulting GeoDataFrame.
    To get the resulting GeoDataFrame, use gdf_from_pwqmn() and plot
    it using plot_gdf()

    :param pwqmn_list: a dict with a specific structure

    :return:
    """
    plot_gdf(gdf_from_pwqmn(pwqmn_list))


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

        elif type(dataset) is dict:
            # The hydat and pwqmn data are the only ones that should
            # be in dict format
            if ds_name == "hydat":
                gdf = gdf_from_hydat(dataset)
            elif ds_name == "pwqmn":
                gdf = gdf_from_pwqmn(dataset)

        # if the conversion was successful, add it to the output dict
        if type(gdf) is gpd.GeoDataFrame:
            gdfs[ds_name] = gdf

    return gdfs


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



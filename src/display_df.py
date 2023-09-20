import os
import webbrowser
import random
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from load_data import proj_path
from timer import Timer


plot_save_dir = os.path.join(proj_path, "plots")
map_save_dir = os.path.join(proj_path, "maps")
timer = Timer


def find_xy_fields(df: pd.DataFrame) -> [str, str]:
    """
    Searches a pandas DataFrame for specific field names to use as
    longitudinal and latitudinal values.

    If more than 1 match is found for X or Y, "Failed" will be
    returned. If no match is found for X or Y, an empty string
    will be returned.

    :param df: the pandas DataFrame to search

    :return: [<X field name> or "Failed", <Y field name> or "Failed"]
    """
    def _(i, _field) -> str:  # when I removed this the function stopped working, so it stays
        return _field if i == "" else "Failed"

    x, y = "", ""
    for field in df.columns.values:
        if df[field].dtype == float:
            if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
                x = _(x, field)
            elif field.upper() in ["LAT", "LATITUDE", "Y"]:
                y = _(y, field)

    return x, y


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
        outfp = os.path.join(os.path.dirname(__file__), "map.html")
        m.save(outfp)
        webbrowser.open(outfp)


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


def check_gdfs_iter(gdfs):
    if type(gdfs) == dict:
        gdfs = list(gdfs.values())
    elif not hasattr(gdfs, '__iter__'):
        gdfs = [gdfs, ]
    return gdfs


def map_gdfs(gdfs_to_map):
    """

    :param gdfs_to_map:
    :return:
    """
    color_list = ['red', 'blue', 'yellow', 'purple', 'black']

    def explore_recursive(gdf_list, n):
        m = None
        if n < len(gdf_list) - 1:
            m = explore_recursive(gdf_list, n + 1)
        return gdf_list[n].explore(m=m, color=color_list[random.randint(0, 5)],
                                   marker_kwds={'radius': 4})

    gdfs_to_map = check_gdfs_iter(gdfs_to_map)
    m = explore_recursive(gdfs_to_map, 0)
    outpath = os.path.join(os.path.dirname(__file__), "map.html")
    m.save(outpath)
    webbrowser.open(outpath)


def plot_gdf(gdf: gpd.GeoDataFrame, name="", save=False, **kwargs):
    """
    Plot a geopandas GeoDataFrame on a matplotlib plot

    :param gdf: the geopandas GeoDataFrame to be plotted
    :param name: name to save the plot to
    :param save: True or False; whether to save the plot to disk
    :param kwargs:
    :return: None
    """
    if type(gdf) is gpd.GeoDataFrame:

        ax = gdf.plot(figsize=(10, 6), aspect=2)

        if save:
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
    :return: None
    :raises TypeError: if df is not a Pandas DataFrame
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    plot_gdf(point_gdf_from_df(df), save=save, name=name, **kwargs)

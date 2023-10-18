import os
from util_classes import Timer, BBox
from load_data import proj_path
import gdf_utils

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.gridspec as gspec

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely import Point
from adjustText import adjust_text


timer = Timer()


# ========================================================================= ##
# Script Constants ======================================================== ##
# ========================================================================= ##


# default save directories within the project scope
plot_save_dir = os.path.join(proj_path, "plots")


# Coordinate Reference System Constants
geodetic = ccrs.Geodetic()

lambert = ccrs.LambertConformal(central_longitude=gdf_utils.central_lon,
                                central_latitude=gdf_utils.central_lat,
                                standard_parallels=(gdf_utils.stand_parallel_1,
                                                    gdf_utils.stand_parallel_2))

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
Can_LCC_wkt = gdf_utils.Can_LCC_wkt


# ========================================================================= ##
# Data Plotting =========================================================== ##
# ========================================================================= ##


def add_map_to_plot(total_bounds=None, ax=None, projection=lambert,
                    features=(cfeature.COASTLINE, cfeature.STATES, cfeature.LAKES),
                    **kwargs):
    """
    Adds an axes to the current figure, makes it the current Axes, and
    draws a map onto said axes using cartopy.

    :param total_bounds: tuple or list
        The bounding coordinates to set the extent of the map to.
        i.e
            (min_x, min_y, max_x, max_y)

    :param ax: plt.Axes object or None (default)
        The Axes to plot g_series onto. If None, draws the map on the
        matplotlib.pyplot default axes (without clearing it).

    :param projection: Cartopy CRS object
        Projection to use to display the map. Defaults to Lambert
        Conformal Conic.

    :param features: list or tuple of cartopy.feature attributes
        Cartopy features to add to the map. If None, adds a default
        set of features.

    :param kwargs:
        Additional keyword arguments to instantiate the matplotlib
        Axes with.

    :return: matplotlib Axes
        The created Axes object that the map was draw onto.
    """

    if ax is None:
        plt.figure(figsize=(8, 8))
        ax = plt.axes(projection=projection, **kwargs)

    if type(total_bounds) is BBox:
        total_bounds = total_bounds.to_ccrs(projection)

    # check if the GeoSeries has a valid bounding information
    if total_bounds is not None:
        try:
            min_x, min_y, max_x, max_y = total_bounds

            size = max([max_x - min_x,max_y - min_y]) * 0.6

            x0 = (min_x + max_x) / 2 - size
            x1 = (min_x + max_x) / 2 + size
            y0 = (min_y + max_y) / 2 - size
            y1 = (min_y + max_y) / 2 + size

            ax.set_extent([x0, x1, y0, y1], crs=projection)
        except ValueError:
            print("Invalid boundary information. Extent will not be set.")

    ax.stock_img()

    for feature in features:
        ax.add_feature(feature)

    return ax


def plot_g_series(g_series: gpd.GeoSeries, crs=Can_LCC_wkt, ax=plt,
                  **kwargs):
    """
    Plot a Geopandas GeoSeries. Does not change the original GeoSeries
    geometry.

    :param g_series: Geopandas GeoSeries
        Data to plot. May consist of points or lines, but not polygons.

    :param crs: pyproj.CRS
        The value can be anything accepted by pyproj.CRS.from_user_input(),
        such as an authority string (eg “EPSG:4326”) or a WKT string.

    :param ax: plt.Axes object
        The Axes to plot g_series onto. If plt, plots g_series on
        matplotlib.pyplot (without clearing it).

    :param kwargs:
        Keyword arguments to pass when plotting g_series. Kwargs are
        Line2D properties.

    :return: PathCollection
    """
    assert type(g_series) == gpd.GeoSeries, f"GeoSeries expected, {type(g_series)} found."

    g_series = g_series.to_crs(crs=crs)

    try:
        if g_series.geom_type.iat[0] == "Point":
            path_collection = ax.scatter(g_series.x, g_series.y, **kwargs)

        elif g_series.geom_type.iat[0] == "LineString":
            path_collection = []
            for geom in g_series:
                path_collection.append(ax.plot(*geom.xy, **kwargs))
    except IndexError:
        print("Plotting failed. The GeoSeries has no geometry.")

    return path_collection


def draw_network(p_graph, **kwargs):
    gdf_utils.__draw_network__(p_graph, **kwargs)


def plot_gdf(gdf: gpd.GeoDataFrame, crs=Can_LCC_wkt, ax=plt, **kwargs):
    """
    Plot a Geopandas GeoDataFrame. Does not change the original
    GeoDataFrame geometry.

    :param gdf: Geopandas GeoDataFrame
        Data to plot. May consist of points or lines, but not polygons.

    :param crs: pyproj.CRS
        The value can be anything accepted by pyproj.CRS.from_user_input(),
        such as an authority string (eg “EPSG:4326”) or a WKT string.

    :param ax: plt.Axes object or None (default)
        The Axes to plot g_series onto. If None, clears pyplot, plots
        g_series, and displays the result.

    :param kwargs:
        Keyword arguments to pass when plotting the gdf. Kwargs are
        Line2D properties.

    :return: PathCollection
    """
    return plot_g_series(gdf.geometry, ax=ax, crs=crs, **kwargs)


def plot_df(df: pd.DataFrame, ax=None, crs=Can_LCC_wkt, **kwargs):
    """
    Plot a pandas DataFrame as points, if possible. Does
    not return the resulting GeoDataFrame; to get the resulting
    GeoDataFrame, use point_gdf_from_df().

    :param df: <Pandas DataFrame>
        DataFrame to be plotted.

    :param crs: pyproj.CRS
        The value can be anything accepted by pyproj.CRS.from_user_input(),
        such as an authority string (eg “EPSG:4326”) or a WKT string.

    :param ax: plt.Axes object or None (default)
        The Axes to plot g_series onto. If None, clears pyplot, plots
        g_series, and displays the result.

    :raises TypeError:
        If df is not a Pandas DataFrame

    :return:
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    output = gdf_utils.point_gdf_from_df(df)

    # Only try to plot the output if the conversion was successful
    if type(output) is gpd.GeoDataFrame:
        return plot_gdf(output, ax=ax, crs=crs, **kwargs)
    else:
        print("Could not be plotted")
        return None


def plot_closest(points: gpd.GeoDataFrame, other: gpd.GeoDataFrame, ax=plt):
    """
    For each point in points, finds the closest feature in other, then
    plots both GeoDataFrames and draws lines between them.

    :param points: Geopandas GeoDataFrame
        Origin points.

    :param other: Geopandas GeoDataFrame
        Candidate geometry.
    """
    snapped_dict = gdf_utils.connect_points_to_feature(points, other)

    new_points = snapped_dict['new_points']
    lines = snapped_dict['lines']

    print("plotting connecting lines")
    plot_g_series(lines, ax=ax, zorder=1, color='purple', label='connector')
    print("plotting snapped points")
    plot_g_series(new_points, ax=ax, color='red', zorder=9, label='new')
    print("plotting features that were snapped to")
    plot_gdf(other, ax=ax, color='red', zorder=9, label='new')
    print("plotting original points")
    plot_gdf(points, ax=ax, color='blue', zorder=10, label='original')


def plot_paths(edge_df, ax=None, filter=""):
    """
    Plots geometry data of a DataFrame with a specific structure.
    Accepts the output from gdf_utils.dfs_search(), plots paths
    from origin to matched stations with the following color code:
        On Segment: Orange
        Downstream: Pink
        Upstream: Purple

    :param edge_df: DataFrame
        The structure containing the data to plot. Must contain the
        following columns:
            - 'pos' (string)
            - 'path' (geometry; LineString)

    :param ax:
        The axes to plot the paths onto.

    :param filter: string
        Accepts any value in 'pos'.

    :return:
    """
    grouped = edge_df.groupby(by='pos')
    for ind, group in grouped:
        if ind == 'On':
            color = 'orange'
        elif ind == 'Down':
            color = 'pink'
        elif ind == 'Up':
            color = 'purple'
        else:
            color = 'grey'
        if ind == filter or filter == "":
            plot_g_series(gpd.GeoSeries(group['path'], crs=Can_LCC_wkt), ax=ax,
                          color=color, linewidth=3)


def configure_legend(legend_dict: dict, ax=plt):
    """
    Configures a custom legend on an Axes object based on information
    provided in a dict.

    :param legend_dict: dict
        Dictionary object of 3 key/list pairs, where keys are 'Symbol',
        'Colour', and 'Label', and lists are the same length. Items at
        index i of each list hold properties of the element to add to
        the legend.

        Items in legend_dict['Symbol'] must be either 'point' or 'line'.
        Items in legend_dict['Colour'] must be matplotlib recognized
            colour values.
        Items in legend_dict['Label'] must be strings.

        i.e.
            legend_dict['Symbol'][3], legend_dict['Colour'][3], and
            legend_dict['Label'][3] are used to configure the 4th
            element on the legend.

    :param ax: Axes object
        Axes to plot the configured custom legend onto.

    :return:
    """
    custom_lines = []
    for i in range(len(legend_dict['Symbol'])):
        color = legend_dict['Colour'][i]
        symbol = legend_dict['Symbol'][i]
        label = legend_dict['Label'][i]

        if symbol == 'line':
            custom_lines.append(Line2D([0], [0], color=color, label=label, lw=4))
        elif symbol == 'point':
            custom_lines.append(Line2D([0], [0], color=color, label=label, marker='o',
                                       markersize=5))

    ax.legend(handles=custom_lines, loc='upper right')


def annotate_stations(hydat, pwqmn, ax):
    """

    :param hydat:
    :param pwqmn:
    :return:
    """
    texts = []

    for ind, row in hydat.to_crs(crs=gdf_utils.Can_LCC_wkt).iterrows():
        texts.append(ax.text(row['geometry'].x, row['geometry'].y, row['STATION_NUMBER']))

    for ind, row in pwqmn.to_crs(crs=gdf_utils.Can_LCC_wkt).drop_duplicates('Location_ID').iterrows():
        texts.append(ax.text(row['geometry'].x, row['geometry'].y, row['Location_ID']))

    adjust_text(texts)


def plot_match_array(edge_df, add_to_plot=None, shape=None):
    """

    :param edge_df:
    :param shape:
    :param add_to_plot:

    :return:
    """


    grouped = edge_df.groupby(by='pwqmn_id')

    if shape is None:
        cols = np.ceil(np.sqrt(len(grouped.groups.keys()))) + 1
        rows = np.ceil(len(grouped.groups.keys()) / cols)
        shape = int(rows), int(cols)

    fig, ax = plt.subplots(nrows=shape[0], ncols=shape[1],
                           subplot_kw={'projection': lambert, 'aspect': 'equal'},
                           figsize=(16, 8))

    plt.subplots_adjust(left=0.02, right=0.89, top=0.98, bottom=0.02)
    fig.add_axes([0.91, 0.01, 0.08, 0.96])
    n = 0

    for ind, group in grouped:
        row, col = n // shape[1], n % shape[1]
        ax[row][col].set_box_aspect(1)
        plot_paths(group, ax=ax[row][col])

        for path in group['path']:
            start, end = path.boundary.geoms
            ax[row][col].scatter(
                *lambert.transform_point(start.x, start.y, geodetic), color='blue', zorder=6,
            marker='o', ms=15)
            ax[row][col].scatter(
                *lambert.transform_point(end.x, end.y, geodetic), color='red', zorder=6,
            marker='o', ms=15)

        if add_to_plot is not None:
            for i in add_to_plot:
                if callable(i):
                    i(ax=ax[row][col])

        n += 1

    plt.show()


def show():
    """
    Wrapper function for calling plt.show() from functions that don't
    import matplotlib.

    :return:
    """
    plt.show()


def close():
    """
    Wrapper function for calling plt.show() from functions that don't
    import matplotlib.

    :return:
    """
    plt.close()


def timed_display(seconds=2):
    """
    Displays the current matplotlib.pyplot plot, and automatically
    closes the plot window after a specificied amount of time.r

    :param seconds: int
        Time to display the plot for in seconds. Default 2 seconds.
    :return:
    """
    plt.show(block=False)
    plt.pause(seconds)
    plt.close()

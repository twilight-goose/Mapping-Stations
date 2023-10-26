import os
from load_data import proj_path
import gdf_utils
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import cartopy.feature as cfeature
from adjustText import adjust_text
from matplotlib_scalebar.scalebar import ScaleBar


# ========================================================================= ##
# Script Constants ======================================================== ##
# ========================================================================= ##

# default save directories within the project scope
plot_save_dir = os.path.join(proj_path, "plots")

# ========================================================================= ##
# Data Plotting =========================================================== ##
# ========================================================================= ##


def add_map_to_plot(extent=None, ax=None, projection=lambert, extent_crs=None,
                    features=(cfeature.COASTLINE, cfeature.STATES, cfeature.LAKES),
                    **kwargs):
    """
    Adds an axes to the current figure, makes it the current Axes, and
    draws a map onto said axes using cartopy.

    :param extent: list-like, BBox, or None (Default)
        The bounding coordinates to set the extent of the map to.
        If list-like, must contain exactly 4 elements (min_x, min_y,
        max_x, max_y) and bounds are assumed to be latitude/longitude
        floats. If BBox, must have a set CRS. If None, the extent of
        the Axes is not set or changed.

    :param ax: plt.Axes object or None (default)
        The Axes to plot g_series onto. If None, draws the map on the
        matplotlib.pyplot default axes (without clearing it).

    :param projection: Cartopy CRS object
        Projection to use to display the map. Defaults to Lambert
        Conformal Conic.

    :param extent_crs: value or None (default)
        CRS that total_bounds coordinates are in. If None, assumes
        total_bounds is in latitude longitude format.

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

    if type(extent) is BBox:
        # cast the bounding coordinates to latitude longitude
        extent = extent.to_ccrs(geodetic).bounds

    # check if the GeoSeries has a valid bounding information
    if extent is not None:
        try:
            min_x, min_y, max_x, max_y = extent

            size = max([max_x - min_x, max_y - min_y]) * 0.6

            x0 = (min_x + max_x) / 2 - size
            x1 = (min_x + max_x) / 2 + size
            y0 = (min_y + max_y) / 2 - size
            y1 = (min_y + max_y) / 2 + size

            ax.set_extent([x0, x1, y0, y1], extent_crs)
        except ValueError:
            print("Invalid boundary information. Extent will not be set.")

    ax.stock_img()

    for feature in features:
        ax.add_feature(feature)

    return ax


def add_grid_to_plot(ax=None, projection=lambert, **kwargs):
    """
    Adds a Latitude Longitude grid to an Axes.

    :param ax:
    :param projection:

    :return: cartopy.mpl.gridliner.Gridliner object
        The object used to add gridlines and tick labels to the axes.
    """
    if ax is None:
        ax = plt.axes(projection=projection, **kwargs)

    gridliner = ax.gridlines(draw_labels={"bottom": "x", "left": "y"}, x_inline=False, y_inline=False,
                             dms=False, rotate_labels=False,
                             xlabel_style={'fontsize':8},
                             ylabel_style={'fontsize':8},
                             color='black', alpha=0.3)
    return gridliner


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
    if not (type(g_series) is gpd.GeoSeries):
        raise TypeError(f'GeoSeries expected, {type(g_series)} found.')

    g_series = g_series.to_crs(crs=crs)

    try:
        if g_series.geom_type.iat[0] == "Point":
            lines = ax.plot(np.array(g_series.x),
                            np.array(g_series.y), marker='o',
                            lw=0, **kwargs)
        elif g_series.geom_type.iat[0] == "LineString":
            lines = []
            for geom in g_series:
                lines.append(ax.plot(*geom.xy, **kwargs))
    except IndexError:
        print("Plotting failed. The GeoSeries has no geometry.")

    return lines


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
    if not (type(gdf) is gpd.GeoDataFrame):
        raise TypeError(f'GeoDataFrame expected, {type(gdf)} found.')
    if 'Station_ID' in gdf.columns:
        gdf = gdf.drop_duplicates('Station_ID')
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
    new_points, lines = gdf_utils.connect_points_to_feature(points, other)

    print("plotting connecting lines")
    plot_g_series(lines, ax=ax, zorder=1, color='purple', label='connector')
    print("plotting snapped points")
    plot_g_series(new_points, ax=ax, color='red', zorder=9, label='new')
    print("plotting features that were snapped to")
    plot_gdf(other, ax=ax, color='red', zorder=9, label='new')
    print("plotting original points")
    plot_gdf(points, ax=ax, color='blue', zorder=10, label='original')


def plot_paths(path_df, ax=None, filter=""):
    """
    Plots geometry data of a DataFrame with a specific structure.
    Accepts the output from gdf_utils.dfs_search(), plots paths
    from origin to matched stations with the following color code:
        On Segment: Orange
        Downstream: Pink
        Upstream: Purple

    :param path_df: DataFrame
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
    grouped = path_df.groupby(by='pos')
    for ind, group in grouped:
        if ind.startswith('On'):
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


def configure_legend(legend_elements: list, ax=plt, loc='upper right',
                     **kwargs):
    """
    Configures a custom legend on an Axes object based on information
    provided in a dict.

    :param legend_elements: list of dict
        List of dictionaries where each dictionary defines a legend
        entry and must contain 1 of the following sets of keys:

        'label', 'renderer'
        Where dict['renderer'] contains the output produced by
        plot_gdf()/plot_g_series() when the data was plotted.

        'label', 'symbol', <kwargs>
        Where dict['symbol'] is one of {'point', 'line', 'patch} and
        the other entries are keyword arguments to pass to
        matplotlib.lines.Line2D.set(). For full list of keywords, see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D.set

    :param ax: Axes object
        Axes to place the configured custom legend onto.

    :param loc: string (default='upper right')
        Location in ax to place the legend.
        Options:
        - 'upper left', 'upper right', 'lower left', 'lower right'
        - 'upper center', 'lower center', 'center left', 'center right'
        - 'center', 'best'

    :param kwargs:
        Keyword arguments to pass to ax.legend(). For full list of
        accepted keywords, see:
        https://matplotlib.org/stable/api/legend_api.html#matplotlib.legend.Legend

    :return:
    """
    custom_lines = []
    for i in legend_elements:
        line = Line2D([0], [0])
        renderer = i.get('renderer')
        label = i.get('label')

        if not (renderer is None):
            if type(renderer) is list:
                renderer = renderer[0]

            line.update_from(renderer)
            line.set(label=label)
        else:
            if i.get('symbol') == 'point':
                i['lw'] = 0
                i['marker'] = 'o'
            elif i.get('symbol') == 'line':
                pass
            elif i.get('symbol') == 'polygon':
                pass
            del i['symbol']
            line.set(**i)
        custom_lines.append(line)

    ax.legend(handles=custom_lines, loc=loc, **kwargs)


def annotate_stations(*station_sets, adjust=True, ax=plt):
    """
    Add station id text annotations to a matplotlib plot.

    :param adjust: bool (default=True)
        Whether to adjust the position of the annotations. Turning
        this off improves efficiency.

    :param ax: (default=matplotlib.pyplot)
        Axes to add the annotations to.

    :param station_sets: list of DataFrame or GeoDataFrame
        The DataFrames containing the stations to annotate. Must
        contain a 'Station_ID' field and a 'geometry' field.

    :return:
    """
    texts = []

    for stations in station_sets:
        stations = stations.drop_duplicates(subset=['Station_ID'])

        for ind, row in stations.to_crs(crs=Can_LCC_wkt).iterrows():
            if not row['geometry'].is_empty:
                texts.append(ax.text(row['geometry'].x, row['geometry'].y, row['Station_ID'],
                                  fontsize=8))
            else:
                print(row['Station_ID'], "skipped")

    if len(texts) <= 300 and adjust:
        # dont adjust text if there are over 300 because it takes too long,
        # and at that scale its hard to see the text regardless
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

    legend_elements = [
        {'label': 'HYDAT', 'color': 'blue', 'Symbol': 'point'},
        {'label': 'PWQMN', 'color': 'red', 'Symbol': 'point'},
        {'label': 'On', 'color': 'orange', 'Symbol': 'line'},
        {'label': 'Downstream', 'color': 'pink', 'symbol': 'line'},
        {'label': 'Upstream', 'color': 'purple', 'symbol': 'line'}
    ]

    plt.subplots_adjust(left=0.02, right=0.96, top=0.96, bottom=0.04)
    right_pad = fig.add_axes([0.91, 0.01, 0.08, 0.96])
    right_pad.set_axis_off()
    right_pad.set_title('HYDAT -> PWQMN')
    configure_legend(legend_elements, ax=right_pad)

    n = 0

    for ind, group in grouped:
        row, col = n // shape[1], n % shape[1]
        cur_ax = ax[row][col]
        cur_ax.set_box_aspect(1)
        g_series = gpd.GeoSeries(group['path'], crs=Can_LCC_wkt)
        add_map_to_plot(extent=g_series.total_bounds, ax=cur_ax, extent_crs=lambert)
        add_grid_to_plot(ax=cur_ax)
        plot_paths(group, ax=cur_ax)

        text = []
        for ind, group_row in group.iterrows():
            start, end = group_row['path'].boundary.geoms
            cur_ax.scatter([start.x], [start.y], color='blue', zorder=6, marker='o')
            text.append(cur_ax.text(start.x, start.y, group_row['hydat_id']))

        cur_ax.plot([end.x], [end.y], color='red', zorder=6, marker='o')
        text.append(cur_ax.text(end.x, end.y, group_row['pwqmn_id']))

        if add_to_plot is not None:
            for i in add_to_plot:
                if callable(i):
                    i(ax=cur_ax)

        n += 1
        adjust_text(text)

    plt.show()


def add_scalebar(ax=plt):
    ax.add_artist(ScaleBar(1, location='lower right', box_alpha=0.75))


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


def get_ax():
    return plt.subplot(projection=lambert)

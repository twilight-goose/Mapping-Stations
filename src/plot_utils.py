import os

from load_data import proj_path
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox
import gdf_utils

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import cartopy.feature as cfeature
from adjustText import adjust_text
from matplotlib_scalebar.scalebar import ScaleBar


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##


# Copyright (c) 2023 James Wang - jcw4698(at)gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
    Adds a background map to a plot.

    :param extent: list-like, BBox, or None (Default)
        The bounding coordinates to set the extent of the map to.
        If list-like, must contain exactly 4 elements (min_x, min_y,
        max_x, max_y) and bounds are assumed to be latitude/longitude
        floats. If BBox, must have a set CRS. If None, the extent of
        the Axes is not set or changed.

    :param ax: plt.Axes object or None (default)
        The Axes to draw the map onto. If None, creates a new 8x8 figure
        and a new axes on that figure, and draws the map onto that axes.

    :param projection: Cartopy CRS object (default=lambert; see gen_util)
        Projection to use to display the map. Defaults to Lambert
        Conformal Conic.

    :param extent_crs: value or None (default)
        CRS that extent coordinates are in. If None, assumes
        extent is in latitude longitude format.

    :param features: list or tuple of cartopy.feature attributes
        Cartopy features to add to the map. See the documentation at
        https://scitools.org.uk/cartopy/docs/latest/reference/feature.html
        for accepted arguments. If not provided, adds a default set
        of features.

    :param **kwargs:
        Additional keyword arguments to instantiate the matplotlib
        Axes with, passed directly to matplotlib.pyplot.axes().
        See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.axes.html.

    :return: matplotlib Axes
        The Axes object that the map was draw onto. If ax was provided,
        returns the provided axes. If ax was not provided, returns the
        axes that was created.
    """
    # create a new axes if one wasn't provided
    if ax is None:
        plt.figure(figsize=(8, 8))
        ax = plt.axes(projection=projection, **kwargs)

    if type(extent) is BBox:
        # cast the bounding coordinates to latitude longitude
        extent = extent.to_ccrs(geodetic).bounds

    # check that the GeoSeries has a valid bounding information
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
    
    # add the map background image to the axes
    ax.stock_img()
    
    # add cartopy features
    for feature in features:
        ax.add_feature(feature)
    
    # return the axes the map and features were drawn to
    return ax


def add_grid_to_plot(ax=None, projection=lambert, **kwargs):
    """
    Adds a Latitude/Longitude grid to an Axes.

    :param ax: plt.Axes object or None (default)
        The Axes to draw the grid onto. If None, draws the grid onto
        the matplotlib default axes.
    
    :param projection: Cartopy CRS object (default=lambert; see gen_util)
        Projection to use to display the map. Defaults to Lambert
        Conformal Conic.

    :return: cartopy.mpl.gridliner.Gridliner object
        The object used to add gridlines and tick labels to the axes.
    """
    if ax is None:
        ax = plt

    gridliner = ax.gridlines(draw_labels={"bottom": "x", "left": "y"}, x_inline=False, y_inline=False,
                             dms=False, rotate_labels=False,
                             xlabel_style={'fontsize':8},
                             ylabel_style={'fontsize':8},
                             color='black', alpha=0.3)
    return gridliner


def plot_g_series(g_series: gpd.GeoSeries, crs=Can_LCC_wkt, ax=None,
                  marker="o", **kwargs):
    """
    Plot a Geopandas GeoSeries. Does not change the original GeoSeries
    geometry.

    :param g_series: Geopandas GeoSeries
        Data to plot. May consist of points or lines, but not polygons.

    :param crs: pyproj.CRS (default=Can_LCC_wkt; see gen_util)
        The crs to plot the g_series in. The value may be anything
        accepted by pyproj.CRS.from_user_input(), such as an authority
        string (eg “EPSG:4326”) or a WKT string.

    :param ax: plt.Axes object or None (default)
        The Axes to plot g_series onto. If None, plots the data on the
        matplotlib.pyplot default axes (without clearing it).

    :param kwargs: keyword arguments
        Keyword arguments to pass when plotting g_series. Kwargs are
        Line2D properties.

    :return: PathCollection
        matplotlib.collections.PathCollection object, created by the
        plotting.
    """
    # check the input type
    if not (type(g_series) is gpd.GeoSeries):
        raise TypeError(f'GeoSeries expected, {type(g_series)} found.')
    
    if ax is None:
        ax = plt
    
    # change 
    g_series = g_series.to_crs(crs=crs)
    
    # attempt to plot the geometry
    try:
        if g_series.geom_type.iat[0] == "Point":
            lines = ax.plot(np.array(g_series.x),
                            np.array(g_series.y), marker=marker,
                            lw=0, **kwargs)
        elif g_series.geom_type.iat[0] == "LineString":
            lines = []
            for geom in g_series:
                # plot each line separately to collect the artists
                lines.append(*ax.plot(*geom.xy, **kwargs))
        
        # return the artist(s) used to plot the gometry
        return lines
    except IndexError:
        print("Plotting failed. The GeoSeries has no geometry.")
        return None


def draw_network(p_graph, **kwargs):
    """
    Wrapper function for plotting/drawing a networkx graph.
    
    Draws a NetworkX Graph object onto an axes.

    :param p_graph: NetworkX Graph
        The graph object to draw.

    :param ax: plt.Axes object (optional)
        The Axes to plot g_series onto. If None, creates a new Axes,
        adds it to the current figure, and uses that Axes.
    """
    gdf_utils.__draw_network__(p_graph, **kwargs)


def plot_gdf(gdf: gpd.GeoDataFrame, crs=Can_LCC_wkt, ax=None, **kwargs):
    """
    Plot a Geopandas GeoDataFrame. Does not change the original
    GeoDataFrame geometry.

    :param gdf: Geopandas GeoDataFrame
        Data to plot. May consist of points or lines, but not polygons.

    :param crs: pyproj.CRS
        The value can be anything accepted by pyproj.CRS.from_user_input(),
        such as an authority string (eg “EPSG:4326”) or a WKT string.

    :param ax: plt.Axes object or None (default)
        The Axes to plot the data onto. If None, plots the data on the
        matplotlib.pyplot default axes (without clearing it).

    :param kwargs:
        Keyword arguments to pass when plotting the gdf. Kwargs are
        Line2D properties.

    :return: PathCollection
        matplotlib.collections.PathCollection object, created by the
        plotting.
    """
    if not (type(gdf) is gpd.GeoDataFrame):
        raise TypeError(f'GeoDataFrame expected, {type(gdf)} found.')
    if 'Station_ID' in gdf.columns:
        gdf = gdf.drop_duplicates('Station_ID')
    if ax is None:
        ax = plt
        
    return plot_g_series(gdf.geometry, ax=ax, crs=crs, **kwargs)


def plot_paths(path_df, ax=None, **kwargs):
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

    :param ax: plt.Axes object or None (default)
        The Axes to plot the paths onto. If None, plots the data on the
        matplotlib.pyplot default axes (without clearing it).

    :param filter: string one of {'On', 'Down', 'Up'}(default="")
        Accepts any value in 'pos'.

    :return:
    """
    if ax is None:
        ax = plt
    
    grouped = path_df.groupby(by='pos')
    
    # plot paths, coloring them based on position
    for ind, group in grouped:
        if ind.startswith('On'):
            color = 'orange'
        elif ind == 'Down':
            color = 'pink'
        elif ind == 'Up':
            color = 'purple'
        else:
            color = 'grey'
        
        plot_g_series(group['path'], ax=ax, color=color, linewidth=3, **kwargs)


def configure_legend(legend_elements: list, ax=None, loc='upper right',
                     **kwargs):
    """
    Configures a custom legend on an Axes object based on information
    provided in a dict.

    :param legend_elements: list of dict
        List of dictionaries where each dictionary defines a legend
        entry and must contain 1 of the following sets of keys:

        {'label': str, 'renderer': PathCollection}
        
        Where dict['renderer'] contains the PathCollection object
        returned by plot_gdf/plot_g_series when the data was plotted.

        {'label': str, 'symbol': str, <kwargs>}
        
        Where dict['symbol'] is one of {'point', 'line', 'patch} and
        the other entries are keyword arguments to pass to
        matplotlib.lines.Line2D.set(). For full list of keywords, see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D.set

    :param ax: plt.Axes object or None (default)
        The Axes to place the legend on. If None, places the legend on
        the matplotlib.pyplot default axes (without clearing it).

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
    if ax is None:
        ax = plt
        
    custom_lines = []
    
    # initialize and set up all elements of the legend
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
    
    # create the legend and add it to the desired axes
    ax.legend(handles=custom_lines, loc=loc, **kwargs)


def annotate_stations(*station_sets, adjust=True, ax=None):
    """
    Add station id text annotations to a matplotlib plot.
    
    :param station_sets: list of DataFrame or GeoDataFrame
        The DataFrames containing the stations to annotate. Must
        contain a 'Station_ID' field and a 'geometry' field, and
        'geometry' must be a geoseries.
    
    :param adjust: bool (default=True)
        Whether to adjust the position of the annotations. Turning
        this off improves efficiency. Utilizes the adjustText library
        by Ilya Flyamer at https://github.com/Phlya/adjustText.
        If there are more than a total of 300 stations texts will not
        be adjusted (this parameter is overriden).

    :param ax: plt.Axes object or None (default)
        Axes to add the annotations to. If None, adds the text on
        the matplotlib.pyplot default axes (without clearing it).
        
    :return:
    """
    if ax is None:
        ax = plt
        
    texts = []
    
    for stations in station_sets:
        # remove duplicate stations
        stations = stations.drop_duplicates(subset=['Station_ID'])
        
        # convert geometry to the desired crs
        for ind, row in stations.to_crs(crs=Can_LCC_wkt).iterrows():
            if not row['geometry'].is_empty:
                # add the text to the plot and add the output to a list
                texts.append(ax.text(row['geometry'].x, row['geometry'].y, row['Station_ID'],
                                  fontsize=8))
            else:
                print(row['Station_ID'], "skipped")

    if len(texts) <= 300 and adjust:
        # dont adjust text if there are over 300 because it takes too long,
        # and at that scale its hard to see the text regardless
        adjust_text(texts)
    elif adjust and len(texts) > 300:
        print("adjust keyword overriden. Text positions not adjusted because there are too many.")


def plot_match_array(match_df):
    """
    Creates and displays a series of plots in a matplotlib window;
    one for each pwqmn station in match_df.
    
    :param match_df: DataFrame
        A Dataframe of similar or identical structure to one produced
        by the gdf_utils.dfs_search(). Must contain the following fields:
        - hydat_id
        - pwqmn_id
        - path

    """
    def plot_subplot(n):
        """
        Creates and plots a single subplot within the array of plots.
        """
        cur_ax = ax[n // shape[1]][n % shape[1]]
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

        adjust_text(text)

    grouped = match_df.groupby(by='pwqmn_id')
    
    # set up the shape of the plot array on the figure
    cols = np.ceil(np.sqrt(len(grouped.groups.keys()))) + 1
    rows = np.ceil(len(grouped.groups.keys()) / cols)
    shape = int(rows), int(cols)

    fig, ax = plt.subplots(nrows=shape[0], ncols=shape[1],
                           subplot_kw={'projection': lambert, 'aspect': 'equal'},
                           figsize=(16, 8))
    
    # set up a subplot to place the legend in
    plt.subplots_adjust(left=0.02, right=0.96, top=0.96, bottom=0.04)
    right_pad = fig.add_axes([0.91, 0.01, 0.08, 0.96])
    right_pad.set_axis_off()
    right_pad.set_title('HYDAT -> PWQMN')
    
    # configure the legend and add it to the figure
    legend_elements = [
        {'label': 'HYDAT', 'color': 'blue', 'symbol': 'point'},
        {'label': 'PWQMN', 'color': 'red', 'symbol': 'point'},
        {'label': 'On', 'color': 'orange', 'symbol': 'line'},
        {'label': 'Downstream', 'color': 'pink', 'symbol': 'line'},
        {'label': 'Upstream', 'color': 'purple', 'symbol': 'line'}]
    configure_legend(legend_elements, ax=right_pad)
    
    # create and add each subplot to the figure
    n = 0
    for ind, group in grouped:
        plot_subplot(n)
        n += 1

    plt.show()
    

def add_scalebar(ax=None):
    """
    Adds a scalebar to ax.

    :param ax: plt.Axes object
        The Axes to plot g_series onto. If not provided, plots the data 
        on the matplotlib.pyplot default axes (without clearing it).
        
    :return:
    """ 
    if ax is None:
        ax = plt
        
    ax.add_artist(ScaleBar(1, location='lower right', box_alpha=0.75))


def timed_display(seconds=2):
    """
    Displays the current matplotlib.pyplot plot, and automatically
    closes the plot window after a specificied amount of time.

    :param seconds: int (default=2)
        Time to display the plot for in seconds.
        
    :return:
    """
    plt.show(block=False)
    plt.pause(seconds)
    plt.close()

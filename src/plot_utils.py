import os
from classes import BBox, Timer
from load_data import proj_path, find_xy_fields, data_path
import gdf_utils

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely import Point


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
        Projection to use to display the map.

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
        plt.figure(figsize=(8,8))
        ax = plt.axes(projection=projection, **kwargs)

    print(total_bounds)

    # check if the GeoSeries has a valid bounding information
    try:
        min_x, min_y, max_x, max_y = total_bounds

        x_buffer = (max_x - min_x) * 0.2
        y_buffer = (max_y - min_y) * 0.2

        x0 = min_x - x_buffer
        x1 = max_x + x_buffer
        y0 = min_y - y_buffer
        y1 = max_y + y_buffer

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
    """
    assert type(g_series) == gpd.GeoSeries, f"GeoSeries expected, {type(g_series)} found."

    g_series = g_series.to_crs(crs=crs)

    try:
        if g_series.geom_type.iat[0] == "Point":
            ax.scatter(g_series.x, g_series.y, **kwargs)

        elif g_series.geom_type.iat[0] == "LineString":
            for geom in g_series:
                ax.plot(*geom.xy, **kwargs)
    except IndexError:
        print("Plotting failed. The GeoSeries has no geometry.")


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
    """
    plot_g_series(gdf.geometry, ax=ax, crs=crs, **kwargs)


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
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    output = gdf_utils.point_gdf_from_df(df)

    # Only try to plot the output if the conversion was successful
    if type(output) is gpd.GeoDataFrame:
        plot_gdf(output, ax=ax, crs=crs, **kwargs)
    else:
        print("Could not be plotted")


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


def line_browser(lines, bbox):
    class PointBrowser:
        """
        Click on a point to select and highlight it -- the data that
        generated the point will be shown in the lower axes.  Use the 'n'
        and 'p' keys to browse through the next and previous points
        """

        def __init__(self):
            self.lastind = 0
            self.text = ax.text(0.05, 0.95, 'selected: none',
                                transform=ax.transAxes, va='top')
            self.selected, = ax.plot(0, 0, 'o', ms=12, alpha=0.4,
                                     color='yellow', visible=False)

        def on_press(self, event):
            if self.lastind is None:
                return
            if event.key not in ('n', 'p'):
                return
            if event.key == 'n':
                inc = 1
            else:
                inc = -1

            self.lastind += inc
            self.lastind = np.clip(self.lastind, 0, len(xs) - 1)
            self.update()

        def on_pick(self, event):
            x = event.mouseevent.xdata
            y = event.mouseevent.ydata

            gdf = gpd.GeoDataFrame(
                {'temp': "temp"}, index=[1], geometry=gpd.GeoSeries([Point(x, y)]), crs=geodetic)

            joined = gdf.sjoin_nearest(lines, max_distance=0.0001)

            print(joined.head())

            distances = np.hypot(x - xs[event.ind], y - ys[event.ind])
            indmin = distances.argmin()
            print(indmin)
            print(event.ind)
            dataind = event.ind[indmin]

            self.lastind = dataind
            self.update()

        def update(self):
            if self.lastind is None:
                return

            dataind = self.lastind

            ax2.clear()
            data = X.iloc[dataind].to_dict()
            display_data = []

            for key in list(data.keys())[:-1]:
                display_data.append((key, str(data[key])))

            table = mpl.table.table(ax2, cellText=display_data, loc='upper center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)

            self.selected.set_visible(True)
            self.selected.set_data(
                lambert.transform_point(xs[dataind], ys[dataind], geodetic)
            )

            self.text.set_text('selected: %d' % dataind)
            fig.canvas.draw()

    # Fixing random state for reproducibility
    np.random.seed(19680801)

    X = lines
    coordinates = X.geometry.get_coordinates()
    print(coordinates.head())
    xs = coordinates['x']
    ys = coordinates['y']

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    fig.delaxes(ax)

    ax = fig.add_axes([0.02, 0.04, 0.46, 0.92], projection=lambert)

    add_map_to_plot(ax=ax, total_bounds=bbox.to_ccrs(lambert))

    ax.set_box_aspect(1)
    ax2.set_box_aspect(1)

    ax.set_title('click on point to plot time series')

    plot_gdf(lines, ax=ax, marker='o', picker=True, pickradius=5)

    browser = PointBrowser()

    fig.canvas.mpl_connect('pick_event', browser.on_pick)
    fig.canvas.mpl_connect('key_press_event', browser.on_press)

    plt.show()


def browser(data, bbox):
    class PointBrowser:
        """
        Click on a point to select and highlight it -- the data that
        generated the point will be shown in the lower axes.  Use the 'n'
        and 'p' keys to browse through the next and previous points
        """

        def __init__(self):
            self.lastind = 0
            self.text = ax.text(0.05, 0.95, 'selected: none',
                                transform=ax.transAxes, va='top')
            self.selected, = ax.plot([xs[0]], [ys[0]], 'o', ms=12, alpha=0.4,
                                     color='yellow', visible=False)

        def on_press(self, event):
            if self.lastind is None:
                return
            if event.key not in ('n', 'p'):
                return
            if event.key == 'n':
                inc = 1
            else:
                inc = -1

            self.lastind += inc
            self.lastind = np.clip(self.lastind, 0, len(xs) - 1)
            self.update()

        def on_pick(self, event):
            x = event.mouseevent.xdata
            y = event.mouseevent.ydata

            distances = np.hypot(x - xs[event.ind], y - ys[event.ind])
            indmin = distances.argmin()
            dataind = event.ind[indmin]

            self.lastind = dataind
            self.update()

        def update(self):
            if self.lastind is None:
                return

            dataind = self.lastind

            ax2.clear()
            data = X.iloc[dataind].to_dict()
            display_data = []

            for key in list(data.keys())[:-1]:
                display_data.append((key, str(data[key])))

            table = mpl.table.table(ax2, cellText=display_data, loc='upper center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)

            self.selected.set_visible(True)
            self.selected.set_data(
                lambert.transform_point(xs[dataind], ys[dataind], geodetic)
            )

            self.text.set_text('selected: %d' % dataind)
            fig.canvas.draw()

    # Fixing random state for reproducibility
    np.random.seed(19680801)

    X = data
    xs = X.geometry.x
    ys = X.geometry.y

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    fig.delaxes(ax)

    ax = fig.add_axes([0.02, 0.04, 0.46, 0.92], projection=lambert)

    add_map_to_plot(ax=ax, total_bounds=bbox.to_ccrs(lambert))

    ax.set_box_aspect(1)
    ax2.set_box_aspect(1)

    ax.set_title('click on point to plot time series')

    plot_gdf(data, ax=ax, marker='o', picker=True, pickradius=5)

    browser = PointBrowser()

    fig.canvas.mpl_connect('pick_event', browser.on_pick)
    fig.canvas.mpl_connect('key_press_event', browser.on_press)

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
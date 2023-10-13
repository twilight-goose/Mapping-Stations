import matplotlib.pyplot as plt
from util_classes import BBox

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
import plot_utils
import gdf_utils
import matplotlib as mpl
from matplotlib_scalebar.scalebar import ScaleBar


class LineBuilder(object):
    epsilon = 0.5

    def __init__(self, line):
        canvas = line.figure.canvas
        self.canvas = canvas
        self.line = line
        self.axes = line.axes
        self.xs = list(line.get_xdata())
        self.ys = list(line.get_ydata())

        self.ind = None

        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)

    def get_ind(self, event):
        x = np.array(self.line.get_xdata())
        y = np.array(self.line.get_ydata())
        d = np.sqrt((x - event.xdata) ** 2 + (y - event.ydata) ** 2)
        if min(d) > self.epsilon:
            return None
        if d[0] < d[1]:
            return 0
        else:
            return 1

    def button_press_callback(self, event):
        if event.button != 1:
            return
        self.ind = self.get_ind(event)
        print(self.ind)

        self.line.set_animated(True)
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.line.axes.bbox)

        self.axes.draw_artist(self.line)
        self.canvas.blit(self.axes.bbox)

    def button_release_callback(self, event):
        if event.button != 1:
            return
        self.ind = None
        self.line.set_animated(False)
        self.background = None
        self.line.figure.canvas.draw()

    def motion_notify_callback(self, event):
        if event.inaxes != self.line.axes:
            return
        if event.button != 1:
            return
        if self.ind is None:
            return
        self.xs[self.ind] = event.xdata
        self.ys[self.ind] = event.ydata
        self.line.set_data(self.xs, self.ys)

        self.canvas.restore_region(self.background)
        self.axes.draw_artist(self.line)
        self.canvas.blit(self.axes.bbox)


def legend_pick():
    t = np.linspace(0, 1)
    y1 = 2 * np.sin(2 * np.pi * t)
    y2 = 4 * np.sin(2 * np.pi * 2 * t)

    fig, ax = plt.subplots()
    ax.set_title('Click on legend line to toggle line on/off')
    line1, = ax.plot(t, y1, lw=2, label='1 Hz')
    line2, = ax.plot(t, y2, lw=2, label='2 Hz')
    leg = ax.legend(fancybox=True, shadow=True)

    lines = [line1, line2]
    lined = {}  # Will map legend lines to original lines.
    for legline, origline in zip(leg.get_lines(), lines):
        origline.set_picker(True)  # Enable picking on the legend line.
        lined[origline] = legline

    def on_pick(event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        origline = event.artist
        legline = lined[origline]
        visible = not origline.get_visible()
        origline.set_visible(visible)
        # Change the alpha on the line in the legend, so we can see what lines
        # have been toggled.
        legline.set_alpha(1.0 if visible else 0.2)
        fig.canvas.draw()

    fig.canvas.mpl_connect('pick_event', on_pick)
    plt.show()


# if __name__ == '__main__':
#     fig, ax = plt.subplots()
#     line = Line2D([0, 1], [0, 1], marker='o', markerfacecolor='red')
#     ax.add_line(line)
#
#     linebuilder = LineBuilder(line)
#
#     ax.set_title('click to create lines')
#     ax.set_xlim(-2, 2)
#     ax.set_ylim(-2, 2)
#     plt.show()

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


def browser(hydat, network, pwqmn, edge_df, bbox, **kwargs):
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

            for ind, row in edge_df.iterrows():
                if row['hydat_id'] == data["STATION_NUMBER"]:
                    display_data.append((f'Match: {row["pwqmn_id"]}', f"{row['dist']} m"))

            table = mpl.table.table(ax2, cellText=display_data, loc='upper center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)

            self.selected.set_visible(True)
            self.selected.set_data(
                plot_utils.lambert.transform_point(xs[dataind], ys[dataind], plot_utils.geodetic)
            )

            self.text.set_text('selected: %d' % dataind)
            fig.canvas.draw()

    X = hydat
    xs = X.geometry.x
    ys = X.geometry.y

    fig = plt.figure(figsize=(14, 7))
    ax = plt.subplot(1, 2, 1, projection=plot_utils.lambert, position=[0.02, 0.04, 0.46, 0.92])
    ax2 = plt.subplot(1, 2, 2)
    ax2.set_axis_off()

    plot_utils.add_map_to_plot(ax=ax, total_bounds=bbox.to_ccrs(plot_utils.lambert))

    ax.set_box_aspect(1)
    ax2.set_box_aspect(1)

    plot_utils.plot_gdf(hydat, ax=ax, marker='o', picker=True, pickradius=5, **kwargs)
    plot_utils.draw_network(network, ax=ax)
    plot_utils.plot_paths(edge_df, ax=ax, annotate_dist=True)
    plot_utils.plot_gdf(pwqmn, ax=ax, color='red', zorder=5)

    browser = PointBrowser()

    fig.canvas.mpl_connect('pick_event', browser.on_pick)
    fig.canvas.mpl_connect('key_press_event', browser.on_press)

    for ind, row in hydat.to_crs(crs=gdf_utils.Can_LCC_wkt).iterrows():
        ax.annotate(row['STATION_NUMBER'], xy=(row['geometry'].x, row['geometry'].y))

    for ind, row in pwqmn.to_crs(crs=gdf_utils.Can_LCC_wkt).drop_duplicates('Location ID').iterrows():
        ax.annotate(row['Location ID'], xy=(row['geometry'].x, row['geometry'].y))

    legend_dict = {'Symbol': ['line', 'line', 'line', 'point', 'point'],
                   'Colour': ['orange', 'pink', 'purple', 'blue', 'red'],
                   'Label': ['On', 'Downstream', 'Upstream', 'HYDAT', 'PWQMN']}

    plot_utils.configure_legend(legend_dict, ax=ax)
    ax.set_title('Matching HYDAT (Blue) to PWQMN (Red) Stations')
    ax.add_artist(ScaleBar(1, location='lower right', box_alpha=0.75))

    plt.show()

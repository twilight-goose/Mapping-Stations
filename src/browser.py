import matplotlib.pyplot as plt
from util_classes import BBiox

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

    return ax

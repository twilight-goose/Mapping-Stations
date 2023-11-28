import matplotlib.pyplot as plt
import matplotlib.table as mpl_table
from matplotlib_scalebar.scalebar import ScaleBar

import plot_utils
from gen_util import lambert, geodetic


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
# ========================================================================= ##
# ========================================================================= ##


def match_browser(hydat, network, pwqmn, edge_df, bbox, **kwargs):
    class PointBrowser:
        def __init__(self):
            self.event_ind = 0
            self.event_artist = None
            # self.text = ax.text(0.05, 0.95, 'selected: none',
            #                     transform=ax.transAxes, va='top')
            self.selected, = ax.plot([0], [0], ms=20, alpha=0.4,
                                     color='yellow', visible=False,
                                     marker='*', zorder=6)

        def on_pick(self, event):
            self.event_artist = event.artist
            self.event_ind = event.ind[0]
            self.update()

        def update(self):
            if self.event_ind is None:
                return

            display_data = []

            ax2.clear()

            if self.event_artist == hydat_artist:
                data_key_1 = 'hydat_id'
                data_key_2 = 'pwqmn_id'
                data = hydat.iloc[self.event_ind]
                ax2.set_title('HYDAT Station Info')
            elif self.event_artist == pwqmn_artist:
                data_key_1 = 'pwqmn_id'
                data_key_2 = 'hydat_id'
                data = pwqmn.iloc[self.event_ind]
                ax2.set_title('PWQMN Station Info')

            for key in list(data.keys())[:-1]:
                display_data.append((key, str(data[key])))

            for ind, row in edge_df.iterrows():
                if row[data_key_1] == data['Station_ID']:
                    display_data.append((f'Match: {row[data_key_2]}', f"{row['dist']} m"))

            table = mpl_table.table(ax2, cellText=display_data, loc='upper center',
                                    colWidths=[0.4, 0.6], cellLoc='left')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            ax2.set_axis_off()

            self.selected.set_visible(True)
            self.selected.set_data((data['geometry'].x, data['geometry'].y))
            # self.text.set_text('selected: %d' % dataind)
            fig.canvas.draw()

    fig = plt.figure(figsize=(14, 7))
    ax = plt.subplot(1, 2, 1, projection=lambert, position=[0.04, 0.08, 0.42, 0.84])
    ax.set_box_aspect(1)
    ax.set_facecolor('white')
    plot_utils.add_map_to_plot(ax=ax, extent=bbox)

    ax2 = plt.subplot(1, 2, 2, position=[0.52, 0.04, 0.46, 0.92])
    ax2.set_axis_off()
    ax2.set_box_aspect(1)
    ax2.set_facecolor('white')

    hydat_artist = plot_utils.plot_gdf(hydat, ax=ax, picker=True, pickradius=3, color='blue', zorder=5)[0]
    pwqmn_artist = plot_utils.plot_gdf(pwqmn, ax=ax, picker=True, pickradius=3, color='red', zorder=4)[0]

    plot_utils.draw_network(network, ax=ax)
    plot_utils.plot_paths(edge_df, ax=ax)

    browser = PointBrowser()

    fig.canvas.mpl_connect('pick_event', browser.on_pick)

    plot_utils.annotate_stations(hydat, pwqmn, ax=ax)

    legend_elements = [
        {'label': 'HYDAT', 'renderer': hydat_artist},
        {'label': 'PWQMN', 'renderer': pwqmn_artist},
        {'label': 'On', 'color': 'orange', 'symbol': 'line'},
        {'label': 'Downstream', 'color': 'pink', 'symbol': 'line'},
        {'label': 'Upstream', 'color': 'purple', 'symbol': 'line'}
    ]

    plot_utils.configure_legend(legend_elements, ax=ax)

    ax.set_axis_on()

    ax.set_title('Matching HYDAT (Blue) to PWQMN (Red) Stations')
    ax.add_artist(ScaleBar(1, location='lower right', box_alpha=0.75))

    gridliner = ax.gridlines(draw_labels=True, x_inline=False, y_inline=False, dms=False,
                             rotate_labels=False, color='black', alpha=0.3)
    gridliner.color = 'blue'

    plt.show()

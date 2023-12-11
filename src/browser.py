import matplotlib.pyplot as plt
import matplotlib.table as mpl_table
from matplotlib_scalebar.scalebar import ScaleBar

import plot_utils
import gdf_utils
import load_data
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


def match_browser(origin, cand, network, match_df, bbox, origin_pref="hydat",
                  cand_pref="pwqmn"):
    """
    Creates and opens a basic interactive matplotlib window for exploring
    matches created by gdf_utils.dfs_search()
    
    :param origin: GeoDataFrame
        The origin stations.
    
    :param cand: GeoDataFrame
        The candidate stations.
    
    :param network: networkx DiGraph
        The network passed to dfs_search() that stations were assigned
        to and that was used for the station matching.
    
    :param match_df: DataFrame
        The output from dfs_search that holds the origin/candidate
        station matches and information.
        
    :param bbox: BBox object
        The extent of the interactive map.
        
    :param origin_pref: str
        The name to use for the origin data.
    
    :param cand_pref: str
        The name to use for the candidate data.
    
    """
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

            if self.event_artist == origin_artist:
                data_key_1 = origin_pref + '_id'
                data_key_2 = cand_pref + '_id'
                data = origin.iloc[self.event_ind]
                ax2.set_title(origin_pref.upper() + ' Station Info')
            elif self.event_artist == cand_artist:
                data_key_1 = cand_pref + '_id'
                data_key_2 = origin_pref + '_id'
                data = cand.iloc[self.event_ind]
                ax2.set_title(cand_pref.upper() + ' Station Info')

            for key in list(data.keys())[:-1]:
                display_data.append((key, str(data[key])))

            for ind, row in match_df.iterrows():
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

    origin_artist = plot_utils.plot_gdf(origin, ax=ax, picker=True, pickradius=3, color='blue', zorder=5)[0]
    cand_artist = plot_utils.plot_gdf(cand, ax=ax, picker=True, pickradius=3, color='red', zorder=4)[0]
    
    rivers = load_data.load_rivers(bbox=bbox)
    
    plot_utils.plot_gdf(rivers, ax=ax, color="blue")
    plot_utils.draw_network(network, ax=ax)
    # edge_df['path'] = gdf_utils.get_true_path(edge_df, network)
    plot_utils.plot_paths(match_df, ax=ax, alpha=0.65)

    browser = PointBrowser()

    fig.canvas.mpl_connect('pick_event', browser.on_pick)

    plot_utils.annotate_stations(origin, cand, ax=ax, adjust=False)

    legend_elements = [
        {'label': origin_pref.upper(), 'renderer': origin_artist},
        {'label': cand_pref.upper(), 'renderer': cand_artist},
        {'label': 'On', 'color': 'orange', 'symbol': 'line'},
        {'label': 'Downstream', 'color': 'pink', 'symbol': 'line'},
        {'label': 'Upstream', 'color': 'purple', 'symbol': 'line'}
    ]

    plot_utils.configure_legend(legend_elements, ax=ax)

    ax.set_axis_on()

    ax.set_title(f'Matching {origin_pref.upper()} (Blue) to {cand_pref.upper()} (Red) Stations')
    ax.add_artist(ScaleBar(1, location='lower right', box_alpha=0.75))

    gridliner = ax.gridlines(draw_labels=True, x_inline=False, y_inline=False, dms=False,
                             rotate_labels=False, color='black', alpha=0.3)
    gridliner.color = 'blue'

    plt.show()

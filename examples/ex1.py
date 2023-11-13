import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
from gen_util import BBox

period = ["2002-10-12", "2003-10-12"]
bbox = BBox([-80, 45, -79, 46])

hydat = load_data.get_hydat_stations(period, bbox)
hydat_gdf = gdf_utils.point_gdf_from_df(hydat)

ax = plot_utils.add_map_to_plot(extent=bbox)
ax.set_title('HYDAT Stations')
plot_utils.add_grid_to_plot(ax=ax)
renderer = plot_utils.plot_gdf(hydat_gdf, ax=ax, color='blue')
plot_utils.add_scalebar(ax=ax)
plot_utils.annotate_stations(hydat_gdf, ax=ax)

legend_elements = [
    {'label': 'HYDAT', 'renderer': renderer}
]
plot_utils.configure_legend(legend_elements, ax=ax)

plot_utils.show()

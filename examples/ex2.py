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

hydroRIVERS = load_data.load_rivers()
hydat = load_data.get_hydat_station_data(period, bbox)
hydat_gdf = gdf_utils.point_gdf_from_df(hydat)

hydroRIVERS = gdf_utils.assign_stations(hydroRIVERS, hydat_gdf)
hydroNetwork = gdf_utils.hyriv_gdf_to_network(hydroRIVERS)

# Plotting setup
new_points, connectors = gdf_utils.connect_points_to_feature(hydat_gdf, hydroRIVERS)

ax = plot_utils.add_map_to_plot(extent=bbox)
ax.set_title('Projected Location of HYDAT Stations on HydroRIVERS Segments')
plot_utils.add_grid_to_plot(ax=ax)
og = plot_utils.plot_gdf(hydat_gdf, ax=ax, color='blue')
new = plot_utils.plot_gdf(new_points, ax=ax, color='red')
connect = plot_utils.plot_gdf(connectors, ax=ax, color='grey', linestyle='--')
plot_utils.add_scalebar(ax=ax)
plot_utils.annotate_stations(hydat_gdf, ax=ax)

legend_dict = {'Symbol': ['Point', 'Point', 'Line'],
               'Colour': ['blue', 'red', 'grey'],
               'Label': ['Original Hydat', 'New Hydat', 'Connectors'],
               'Objects': [og, new, connect]}
plot_utils.configure_legend(legend_dict)

plot_utils.show()

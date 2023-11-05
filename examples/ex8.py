import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gen_util
import gdf_utils

hydat = load_data.get_hydat_station_data()
pwqmn = load_data.get_pwqmn_station_data()

hydat = gdf_utils.point_gdf_from_df(hydat)
pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

ax = plot_utils.add_map_to_plot(extent=bbox.to_ccrs(plot_utils.lambert))
plot_utils.plot_closest(points, edges, ax=ax)
plot_utils.timed_display()

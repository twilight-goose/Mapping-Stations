import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox


bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

hydat = load_data.get_hydat_station_data(bbox=bbox)
pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

path = os.path.join(load_data.data_path,
                    os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))

lines = load_data.load_rivers(path=path, bbox=bbox)
hydat = gdf_utils.point_gdf_from_df(hydat)
pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

network = gdf_utils.hyriv_gdf_to_network(lines)

edge_df = gdf_utils.dfs_search(network)
print(edge_df.drop(columns='path').to_string())

browser.match_browser(hydat, network, pwqmn, edge_df, bbox, color='blue')

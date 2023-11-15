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

def plot_matches(lines):
    hydat = load_data.get_hydat_stations(bbox=bbox)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)
    
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network, max_depth=100, max_distance=10000)

    print(edge_df.drop(columns='path').to_string())

    browser.match_browser(hydat, network, pwqmn, edge_df, bbox, color='blue')


ohn_path = os.path.join(load_data.data_path,
					os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))

# to use the OHN dataset for the river network, add path=ohn_path to the
# load_rivers functional call parameters

lines = load_data.load_rivers(path=ohn_path, bbox=bbox)
plot_matches(lines)

import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../../Watershed_Delineation/src/PySheds')

from main import delineate


h_subset = "ex9_hydat_subset.csv"
p_subset = "ex9_pwqmn_subset.csv"

hydat = load_data.get_hydat_stations(subset=h_subset[:50])
hydat.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'}, inplace=True)

pwqmn = load_data.get_pwqmn_stations(subset=p_subset[:50])

hydat = gdf_utils.point_gdf_from_df(hydat)
pwqmn = gdf_utils.point_gdf_from_df(pwqmn)


hminx, hminy, hmaxx, hmaxy = hydat.geometry.total_bounds
pminx, pminy, pmaxx, pmaxy = pwqmn.geometry.total_bounds

# when you have a set of selected stations, you can
# get the maximum extent of the subsets of stations 
# to use as the area of interest to improve efficiency
bbox = BBox(min_x=min(hminx, pminx), max_x=max(hmaxx, pmaxx),
            min_y=min(hminy, pminy), max_y=max(hmaxy, pmaxy))
            
# Load river dataset and assign stations to the segments
lines = load_data.load_rivers(bbox=bbox)
lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

# convert the dataset to a network, then match the stations
network = gdf_utils.hyriv_gdf_to_network(lines)
edge_df = gdf_utils.dfs_search(network)
edge_df = gdf_utils.delineate_matches(edge_df)
# # display the list of matches
print(edge_df.drop(columns='path').to_string())

import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox

bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    
hydat = load_data.get_hydat_stations()
pwqmn = load_data.get_pwqmn_stations()

hydat = gdf_utils.point_gdf_from_df(hydat)
pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

path = os.path.join(load_data.data_path,
					os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))

print('ohn networking')

ohn_lines = load_data.load_rivers(path=path)
ohn_lines = gdf_utils.assign_stations(ohn_lines, hydat, prefix='hydat_')
ohn_lines = gdf_utils.assign_stations(ohn_lines, pwqmn, prefix='pwqmn_')
ohn_network = gdf_utils.hyriv_gdf_to_network(ohn_lines)

print('hydrorivers networking')

hydroRIVERS_lines = load_data.load_rivers()
hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, hydat, prefix='hydat_')
hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, pwqmn, prefix='pwqmn_')
hydroRIVERS_network = gdf_utils.hyriv_gdf_to_network(hydroRIVERS_lines)

ohn_edge_df = gdf_utils.dfs_search(ohn_network, max_depth=100, max_distance=10000)
hydro_edge_df = gdf_utils.dfs_search(hydroRIVERS_network, max_distance=10000)

ohn_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
hydro_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
table = hydro_edge_df.merge(ohn_edge_df, how='outer', on=['hydat_id', 'pwqmn_id'],
							suffixes=('_hyRivers', '_OHN'))
table = table.assign(error=table['dist_hyRivers'] - table['dist_OHN']) /
						   table['dist_OHN'])

print(table)
table.to_csv('table.csv')

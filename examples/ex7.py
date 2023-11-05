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

hydat.to_file(os.path.join(load_data.shp_save_path, 'hydat.shp'))
pwqmn.to_file(os.path.join(load_data.shp_save_path, 'pwqmn.shp'))

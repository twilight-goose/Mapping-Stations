import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox


h_subset = "ex9_hydat_subset.csv"
p_subset = "ex9_pwqmn_subset.csv"

hydat = load_data.get_hydat_stations(subset=h_subset, to_csv='h_subset_station_data')
pwqmn = load_data.get_pwqmn_stations(subset=p_subset, to_csv='p_subset_station_data')

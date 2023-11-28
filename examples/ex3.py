import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
from gen_util import BBox, Period
import geopandas as gpd
from matplotlib import pyplot as plt


def main(timed=False):
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    origins = gpd.read_file("points1.shp")
    candidates = gpd.read_file("points1.shp")

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, prefix='origin_')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='candidate_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network)

    plot_utils.plot_match_array(edge_df, add_to_plot=[plot_utils.add_map_to_plot])


if __name__ == "__main__":
    main()

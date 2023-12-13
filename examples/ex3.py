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


"""
DON'T RUN
"""


def main(timed=False):
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)
    
    # load the origin and candidate stations from shapefiles
    # geopanadas automatically loadas them as GeoDataFrames, so theres
    # no need to convert them.
    origins = gpd.read_file("points1.shp")
    candidates = gpd.read_file("points1.shp")
    
    # load the river dataset
    lines = load_data.load_rivers(bbox=bbox)
    
    # assign the stations/points to the river dataset
    lines = gdf_utils.assign_stations(lines, origins, prefix='origin')
    lines = gdf_utils.assign_stations(lines, candidates, prefix='candidate')
    
    # build a network from the river dataset
    network = gdf_utils.hyriv_gdf_to_network(lines)
    
    # perform the matching
    edge_df = gdf_utils.dfs_search(network, prefix1='origin', prefix2='candidate')
    
    # plot a match array
    plot_utils.plot_match_array(edge_df, add_to_plot=[plot_utils.add_map_to_plot], timed=timed)


if __name__ == "__main__":
    main()

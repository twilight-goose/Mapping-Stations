import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox

import geopandas as gpd


def main(timed=False):
    ### copied from ex4
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_stations(bbox=bbox)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    # "Assign" stations to the river dataset
    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn')

    # build a network from the river dataset with station data
    network = gdf_utils.hyriv_gdf_to_network(lines)
    
    # match hydat to pwqmn stations
    match_df = gdf_utils.dfs_search(network,    # the network
                                    prefix1='hydat', prefix2='pwqmn',   # must match the prefixes
                                                                        # used when assigning stations
                                    max_distance=12000 ) # [m] CHANGE THIS WHEN ACTUALLY MATCHING
    
    # load the date ranges of the hydat and pwqmn data
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    
    # calculate the days of data overlap (number of days where record data
    # is available for both stations)
    # prefixes must match those used when assigning stations
    match_df = gdf_utils.assign_period_overlap(match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
                        
    # display the list of matches
    print(match_df.drop(columns='path').to_string())
    ### copied from ex4
    
    # create a geodataframe from the match dataframe and paths
    paths = gpd.GeoDataFrame(match_df, geometry='path', crs=match_df['path'].crs)
    
    dir_path = os.path.join(load_data.shp_save_path, "ex13_output")
    
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    
    # save the geodataframe to disk
    paths.to_file(os.path.join(dir_path, "paths.shp"))
    print(f"Station match paths saved to {os.path.join(dir_path, 'paths.shp'}")
    

if __name__ == "__main__":
    main()

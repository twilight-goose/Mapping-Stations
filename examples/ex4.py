import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox


def main():
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
    match_df = gdf_utils.dfs_search(network, max_distance=100000)
    
    hydat_dr = get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    match_df = gdf_utils.assign_period_overlap(
                        match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
    # display the list of matches
    print(match_df.drop(columns='path').to_string())

    # plot the matches in an interactive plot
    browser.match_browser(hydat, pwqmn, network, match_df, bbox)
    

if __name__ == "__main__":
    main()

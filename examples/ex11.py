import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox

import pandas as pd


def check_equal(row):
    if row['C station ID'] == row["pwqmn_id"]:
        return "same"
    else:
        return row['C station ID']


def main():
    q_c_pairs = pd.read_csv(os.path.join(load_data.monday_path, "Q_C_pairs.csv"))
    h_subset = q_c_pairs["Q station ID"]
    
    # load station data based on the q_c_pairs subset
    hydat = load_data.get_hydat_stations(subset=h_subset.to_list())
    pwqmn = load_data.get_pwqmn_stations()

    # convert station data
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    hminx, hminy = hydat['Longitude'].min(), hydat['Latitude'].min()
    hmaxx, hmaxy = hydat['Longitude'].max(), hydat['Latitude'].max()
    pminx, pminy = pwqmn['Longitude'].min(), pwqmn['Latitude'].min()
    pmaxx, pmaxy = pwqmn['Longitude'].max(), pwqmn['Latitude'].max()

    # when you have a set of selected stations, you can
    # get the maximum extent of the subsets of stations 
    # to use as the area of interest to improve efficiency
    bbox = BBox(min_x=min(hminx, pminx), max_x=max(hmaxx, pmaxx),
                min_y=min(hminy, pminy), max_y=max(hmaxy, pmaxy))
                
    # Load river dataset and assign stations to the segments
    lines = load_data.load_rivers(bbox=bbox)
    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn')

    # convert the dataset to a network, then match the stations
    network = gdf_utils.hyriv_gdf_to_network(lines)
    match_df = gdf_utils.dfs_search(network, max_distance=15000)

    # load the station data ranges
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    match_df = gdf_utils.assign_period_overlap(
                        match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)

    # format the table for output and saving to compare matches
    match_df.drop(columns=['path', 'seg_apart', "total_hydat_records",
                           "total_pwqmn_records"], inplace=True)
                          
    q_c_pairs = match_df.merge(q_c_pairs, how='outer', right_on=['Q station ID', 'C station ID'], \
                                left_on=['hydat_id', 'pwqmn_id'],
                    suffixes=('_q_c', '_hydat'))
                    
    q_c_pairs['C station ID'] = q_c_pairs.apply(check_equal, axis=1)
    q_c_pairs.drop(columns=["name", "lat", "lon", "pos", "area_km2"], inplace=True)

    print(q_c_pairs)
    
    # save the table to a csv
    q_c_pairs.to_csv("q_c_pair_comparison.csv")


if __name__ == "__main__":
    main()

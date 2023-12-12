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


"""
Expected Terminal Output (file paths preceding "Mapping-Stations" will differ):

>>> python ex1.py

>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Loading rivers from 'D:\Mapping-Stations\examples/..\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>>        pwqmn_id hydat_id  pwqmn_dist_from_net  hydat_dist_from_net          dist  data_overlap  C station ID Q station ID
>>> 0   16018406702  02GA014            40.340714            57.509187     17.345681           415  1.601841e+10         same
>>> 1   16018406702  02GA027            40.340714           125.134537   4713.658838             0           NaN          NaN
>>> 2   16018406702  02GA001            40.340714            92.101287   9489.779028             0           NaN          NaN
>>> 3   16018406702  02GA022            40.340714           141.416757   4493.149667             0           NaN          NaN
>>> 4   16018403702  02GA001            19.487934            92.101287   8217.495285             0           NaN          NaN
>>> ..          ...      ...                  ...                  ...           ...           ...           ...          ...
>>> 64   4002701602  02GG007           138.686411           484.197873  11757.524859             0           NaN          NaN
>>> 65   4002701602  02GG003           138.686411           167.975517    321.413859           143  4.002702e+09         same
>>> 66   4001305802  02GE003            76.197197            25.079773  12109.615763           320  4.001306e+09         same
>>> 67   4001000302  02GH002            17.034923           217.736292   4591.822960           157  4.001000e+09         same
>>> 68  10000200202  02GH003           475.800520           462.912612     13.064987           337  1.000020e+10         same

>>> [69 rows x 8 columns]
>>> saving results to q_c_pair_comparison2.csv

Note: A matplotlib window will open. This window has to be closed manually.
"""


def check_equal(row):
    if row['Q station ID'] == row["hydat_id"]:
        return "same"
    else:
        return row['Q station ID']


def main():
    q_c_pairs = pd.read_csv(os.path.join(load_data.monday_path, "Q_C_pairs.csv"))
    p_subset = q_c_pairs["C station ID"]
    
    # load station data based on the q_c_pairs subset
    hydat = load_data.get_hydat_stations()
    pwqmn = load_data.get_pwqmn_stations(subset=p_subset)
    
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
    match_df = gdf_utils.dfs_search(network, prefix1="pwqmn", prefix2="hydat", max_distance=15000)
    
    # load the station data ranges
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    
    # calculate data overlap of matched stations (prefixes must match those used during assignment)
    match_df = gdf_utils.assign_period_overlap(
                        match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
    
    # format the table for output and saving to compare matches
    match_df.drop(columns=['path', 'seg_apart', "total_hydat_records",
                           "total_pwqmn_records"], inplace=True)
                          
    q_c_pairs = match_df.merge(q_c_pairs, how='outer', right_on=['Q station ID', 'C station ID'], \
                                left_on=['hydat_id', 'pwqmn_id'],
                    suffixes=('_q_c', '_hydat'))
                    
    q_c_pairs['Q station ID'] = q_c_pairs.apply(check_equal, axis=1)
    q_c_pairs.drop(columns=["name", "lat", "lon", "pos", "area_km2"], inplace=True)

    print(q_c_pairs)
    
    # save the table to a csv
    print("saving results to q_c_pair_comparison2.csv")
    q_c_pairs.to_csv("q_c_pair_comparison2.csv")


if __name__ == "__main__":
    main()

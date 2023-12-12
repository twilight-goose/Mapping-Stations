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
You may also see additional warnings.

>>> python ex10.py

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
>>> subsetting stations
>>> create output folder
>>> begining delineations
>>> Compute flow directions
>>> Specify pour point
>>> Compute flow directions
>>> Specify pour point
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Calculate flow accumulation
>>> Snapping pour point
>>> Delineate the catchment
>>> Merging Multi-Part Watersheds
>>> Writing to shapefile
>>> Loading delineated watersheds and performing comparisons
>>>   hydat_id     pwqmn_id  hydat_dist_from_net  pwqmn_dist_from_net         dist      pos  data_overlap  total_hydat_records  total_pwqmn_records  hydat_wshed_area  pwqmn_wshed_area  wshed_overlap
>>> 0  02GA014  16018406702            57.509187            40.340714    17.345681  On-Down           415                22594                  415      6.938293e+08      6.938293e+08   6.938293e+08
>>> 1  02GA014  16018403902            57.509187           128.654562  6272.487606       Up           365                22594                  365      6.938293e+08      8.095144e+05   8.095144e+05
>>> 2  02GA016  16018403702            70.067906            19.487934   736.928477  On-Down           665                25021                  689      8.167572e+08      4.878153e+05   0.000000e+00
>>> 3  02GA016  16018401802            70.067906            48.480687   510.035506    On-Up            78                25021                   78      8.167572e+08      8.154568e+08   8.154568e+08
>>> 4  02GA028  16018407702           100.693319            94.153415     8.550945  On-Down           404                22738                  404      1.628525e+05      1.628525e+05   1.628525e+05

Note: A matplotlib window will open. This window has to be closed manually.
"""


def check_equal(row):
    if row['C station ID'] == row["pwqmn_id"]:
        return "same"
    else:
        return row['C station ID']


def main():
    q_c_pairs = pd.read_csv(os.path.join(load_data.monday_path, "Q_C_pairs.csv"))
    h_subset = q_c_pairs["Q station ID"]

    hydat = load_data.get_hydat_stations(subset=h_subset.to_list())
    pwqmn = load_data.get_pwqmn_stations()

    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    # read min and max x and y from the hydat and pwqmn data
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

    # convert the dataset to a network
    network = gdf_utils.hyriv_gdf_to_network(lines)
    
    # match the stations (prefixes must match those used during assignment)
    match_df = gdf_utils.dfs_search(network, prefix1='hydat', prefix2='pwqmn', max_distance=10000)
    
    # load the station data ranges
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    
    # calculate data overlap of matched stations (prefixes must match those used during assignment)
    match_df = gdf_utils.assign_period_overlap(
                        match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
                        
    # delineate the matches (prefixes must match those used during assignment)
    # to change the delineation method, modify delineate_matches
    # to import a different delineation function
    delineated = gdf_utils.delineate_matches(match_df.iloc[:5], "hydat", hydat, "pwqmn", pwqmn)

    # # display the list of matches
    print(delineated.drop(columns=['path', 'seg_apart']).to_string())


if __name__ == "__main__":
    main()

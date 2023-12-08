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
>>>    hydat_id     pwqmn_id  hydat_dist_from_net  pwqmn_dist_from_net          dist      pos  data_overlap  total_hydat_records  total_pwqmn_records  hydat_wshed_area  pwqmn_wshed_area  wshed_overlap
>>> 31  02GA018  16018415502            35.377813           103.454536   6590.248682  On-Down            17                25117                   17      2.428142e+09      2.428142e+09   2.428142e+09
>>> 49  02GB001  16018400802            84.615396            63.007354   7182.449064  On-Down            48                30399                   48      3.300178e+05      5.399873e+09   3.300178e+05
>>> 76  02GC026  16010900502           103.465066            91.785638   6245.401252     Down           178                16950                  215      6.791036e+11      6.791501e+11   6.791036e+11
>>> 55  02GD003   4001301402            93.700858            66.835388    115.950839    On-Up            95                32742                   95      3.307239e+05      1.488050e+09   2.059958e+01
>>> 38  02GA010  16018403302           749.565669           253.343482  18848.982128    On-Up           432                29922                  435      1.647338e+05      2.103505e+07   0.000000e+00

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

    # convert the dataset to a network, then match the stations
    network = gdf_utils.hyriv_gdf_to_network(lines)
    match_df = gdf_utils.dfs_search(network, max_distance=10000)
    
    # load the station data ranges
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    match_df = gdf_utils.assign_period_overlap(
                        match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
                        
    # delineate the matches
    # to change the delineation method, modify delineate_matches
    # to import a different delineation function
    delineated = gdf_utils.delineate_matches(match_df.sample(5), "hydat", hydat, "pwqmn", pwqmn)

    # # display the list of matches
    # print(match_df.drop(columns='path').to_string())
    print(delineated.drop(columns=['path', 'seg_apart']).to_string())


if __name__ == "__main__":
    main()

import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox


"""
Expected Terminal Output (file paths preceding "Mapping-Stations" will differ):

>>> python ex9.py

>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> HYDAT station data saved to D:\Mapping-Stations\examples/..\data\Hydat\h_subset_station_data.csv
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> PWQMN station data saved to p_subset_station_data.csv

"""


def main():
    h_subset = "ex9_hydat_subset.csv"
    p_subset = "ex9_pwqmn_subset.csv"
    
    # load stations based on subsets in csv form and save the station data
    # to csv files
    hydat = load_data.get_hydat_stations(subset=h_subset, to_csv='h_subset_station_data')
    pwqmn = load_data.get_pwqmn_stations(subset=p_subset, to_csv='p_subset_station_data')
    

if __name__ == "__main__":
    main()
    
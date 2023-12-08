import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gen_util
import gdf_utils


"""
Expected Terminal Output (file paths preceding "Mapping-Stations" will differ):

>>> python ex7.py

>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> D:\Mapping-Stations\examples\ex7.py:23: UserWarning: Column names longer than 10 characters will be truncated when saved to ESRI Shapefile.
>>>   hydat.to_file(os.path.join(load_data.shp_save_path, 'hydat.shp'))
>>> D:\Mapping-Stations\examples\ex7.py:24: UserWarning: Column names longer than 10 characters will be truncated when saved to ESRI Shapefile.
>>>   pwqmn.to_file(os.path.join(load_data.shp_save_path, 'pwqmn.shp'))

"""


def main():
    # load the station data
    hydat = load_data.get_hydat_stations()
    pwqmn = load_data.get_pwqmn_stations()
    
    # geographically reference the data
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)
    
    # save the station data to shapefiles
    # You will see warning messages regaring field name trunaction
    hydat.to_file(os.path.join(load_data.shp_save_path, 'hydat.shp'))
    pwqmn.to_file(os.path.join(load_data.shp_save_path, 'pwqmn.shp'))


if __name__ == "__main__":
    main()

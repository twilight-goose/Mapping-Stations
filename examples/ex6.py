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

>>> python ex6.py

>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> BBox provided but no lat/lon fields found. Skipping BBox query.
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> Loading rivers from 'D:\Mapping-Stations\examples/..\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe

Note: A matplotlib window will open. This window has to be closed manually.
See examples/example_output/ex6.png for expected window appearence.
"""



def main():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)
    
    >>> load stations within a lat/lon bounding box
    hydat = load_data.get_hydat_stations(bbox=bbox)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)

    >>> load the dataset to use for the river network
    lines = load_data.load_rivers(bbox=bbox)
    
    >>> geographically reference station data
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)
    
    >>> "Assign" stations to the river network
    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn')
    
    >>> convert river dataset to a network
    network = gdf_utils.hyriv_gdf_to_network(lines)
    
    >>> match origin to candidate stations
    edge_df = gdf_utils.dfs_search(network)
    
    >>> Plot a match array
    plot_utils.plot_match_array(edge_df)


if __name__ == "__main__":
    main()

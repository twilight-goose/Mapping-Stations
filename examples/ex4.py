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

>>> python ex4.py

>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> BBox provided but no lat/lon fields found. Skipping BBox query.
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> Loading rivers from 'D:\Mapping-Stations\examples/..\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>>    hydat_id    pwqmn_id  hydat_dist_from_net  pwqmn_dist_from_net          dist      pos  seg_apart  data_overlap  total_hydat_records  total_pwqmn_records
>>> 0   02DD002  3013302302           108.004294           121.488122  14416.942052       Up          2             0                11840                  171
>>> 1   02DD009  3013302302           125.404140           121.488122     43.451882  On-Down          0            98                12850                  171
>>> 2   02EA010  3012400102           279.692553            52.964151  16922.784842     Down          4           194                19695                  194
>>> 3   02EA006  3012400202            17.615197            90.834358   1073.440993  On-Down          0            64                30333                   64
>>> 4   02EA006  3012400602            17.615197            29.857827  31239.647096       Up          7            17                30333                   17
>>> 5   02EA001  3009800302            78.331043            50.951323   3785.120896  On-Down          0             0                  792                   61
>>> 6   02EA001  3009800402            78.331043           146.112718   4467.751704  On-Down          0             0                  792                   59
>>> 7   02EB013  3008503402            97.841980           118.680662  10164.261957     Down          1            16                17725                   26
>>> 8   02EB103  3008502802           162.944531           144.020056     18.925278    On-Up          0            52                 2262                  242
>>> 9   02EB103  3008501002           162.944531            42.602862  15575.905785     Down          5            48                 2262                   71
>>> 10  02EB103  3008500202           162.944531            98.368066  15629.548346     Down          5            48                 2262                  211
>>> 11  02EB103  3008501102           162.944531           176.038410  16560.584585     Down          5            48                 2262                  250
>>> 12  02EB004  3008500602           189.006973           173.010407     30.923688    On-Up          0           238                38462                  238
>>> 13  02EB004  3008501502           189.006973           228.054530  23013.028729     Down          5            23                38462                   23
>>> 14  02EB004  3008501302           189.006973            83.416588  23397.210605     Down          5            64                38462                   64
>>> 15  02EB004  3008501202           189.006973            95.388332  24181.756038     Down          5            62                38462                   62
>>> 16  02EB004  3008500702           189.006973           156.563191  12283.974395       Up          3           192                38462                  192
>>> 17  02EB008  3008500902           198.041803            71.314618    296.543161    On-Up          0           193                26265                  193
>>> 18  02EB008  3008500402           198.041803            18.277330  38624.763562     Down          4           275                26265                  278
>>> 19  02EB105  3008502502           266.660024           235.305000     31.614124  On-Down          0            19                 1026                   21
>>> 20  02EB011  3009200102            53.827609           124.272184    336.848454    On-Up          0           297                20230                  297
>>> 21  02EB005  3008500102           248.243244            93.061343  10828.018559  On-Down          0             0                 4985                  308
>>> 22  02EB005  3009200202           248.243244            89.123495   3343.306653    On-Up          0             0                 4985                    2
>>> 23  02EB005  3008501601           248.243244           203.166377   7682.088931       Up          1             0                 4985                   31
>>> 24  02EB005  3008501802           248.243244            48.426933  10678.528108       Up          1             0                 4985                   22
>>> 25  02EB006  3008500102           326.649971            93.061343  10543.867350  On-Down          0           308                30246                  308
>>> 26  02EB006  3009200202           326.649971            89.123495   3676.271811    On-Up          0             2                30246                    2
>>> 27  02EB010  3008500102           109.325585            93.061343   8982.163362  On-Down          0            11                12129                  308
>>> 28  02EB010  3009200202           109.325585            89.123495   5068.978402    On-Up          0             0                12129                    2
>>> 29  02EB012  3008500102            43.811427            93.061343     64.850527  On-Down          0           308                19974                  308
>>> 30  02EB012  3009200202            43.811427            89.123495  14009.739915    On-Up          0             2                19974                    2
>>> Loading rivers from 'D:\Mapping-Stations\examples/..\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'

Note: A matplotlib window will open. This window has to be closed manually.
See examples/example_output/ex4.png for expected window appearence.
"""


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
    match_df = gdf_utils.dfs_search(network,
                                    max_distance=100000 ) # [m] CHANGE THIS WHEN ACTUALLY MATCHING
    
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    match_df = gdf_utils.assign_period_overlap(
                        match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
    # display the list of matches
    print(match_df.drop(columns='path').to_string())

    # plot the matches in an interactive plot
    browser.match_browser(hydat, pwqmn, network, match_df, bbox)
    

if __name__ == "__main__":
    main()

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
>>> 0   02DD009  3013302302           125.404188           121.488169     43.451901  On-Down          0            98                12850                  171
>>> 1   02EA005  3012400102            81.388403            52.964173   6232.600768     Down          0           194                38870                  194
>>> 2   02EA006  3012400202            17.615202            90.834384   1073.440981  On-Down          0            64                30333                   64
>>> 3   02EA006  3012400102            17.615202            52.964173   2792.096322     Down          0           194                30333                  194
>>> 4   02EA001  3009800302            78.331043            50.951323   3785.140234  On-Down          0             0                  792                   61
>>> 5   02EA001  3009800402            78.331043           146.112718   4467.774530  On-Down          0             0                  792                   59
>>> 6   02EB013  3008503402            97.842010           118.680705  10164.260669     Down          0            16                17725                   26
>>> 7   02EB103  3008502802           162.944579           144.020099     18.925284    On-Up          0            52                 2262                  242
>>> 8   02EB004  3008500602           189.007013           173.010444     30.923690    On-Up          0           238                38462                  238
>>> 9   02EB007  3008500602           235.654476           173.010444   3425.444314       Up          1             0                 8507                  238
>>> 10  02EB008  3008500902           198.041818            71.314623    296.543173    On-Up          0           193                26265                  193
>>> 11  02EB105  3008502502           266.660053           235.305025     31.614128  On-Down          0            19                 1026                   21
>>> 12  02EB105  3008501002           266.660053            42.602874  10274.105681     Down          2            20                 1026                   71
>>> 13  02EB105  3008500202           266.660053            98.368093  10327.748237     Down          2            20                 1026                  211
>>> 14  02EB105  3008501102           266.660053           176.038417  11258.784426     Down          2            20                 1026                  250
>>> 15  02EB011  3009200102            53.827612           124.272191    336.848529    On-Up          0           297                20230                  297
>>> 16  02EB005  3008500102           248.243271            93.061348  10828.017126  On-Down          0             0                 4985                  308
>>> 17  02EB005  3009200202           248.243271            89.123497   3343.307209    On-Up          0             0                 4985                    2
>>> 18  02EB005  3008501601           248.243271           203.166407   7682.088405       Up          0             0                 4985                   31
>>> 19  02EB005  3008501802           248.243271            48.426935  10678.527618       Up          0             0                 4985                   22
>>> 20  02EB005  3008500302           248.243271           139.625181   5121.484806       Up          0             0                 4985                  248
>>> 21  02EB006  3008500102           326.650034            93.061348  10543.865971  On-Down          0           308                30246                  308
>>> 22  02EB006  3009200202           326.650034            89.123497   3676.272367    On-Up          0             2                30246                    2
>>> 23  02EB006  3008501601           326.650034           203.166407   7966.239560       Up          0            31                30246                   31
>>> 24  02EB006  3008501802           326.650034            48.426935  10962.678772       Up          0            22                30246                   22
>>> 25  02EB006  3008500302           326.650034           139.625181   5405.635961       Up          0           248                30246                  248
>>> 26  02EB010  3008500102           109.325589            93.061348   8982.162288  On-Down          0            11                12129                  308
>>> 27  02EB010  3009200202           109.325589            89.123497   5068.977725    On-Up          0             0                12129                    2
>>> 28  02EB012  3008500102            43.811429            93.061348     64.850526  On-Down          0           308                19974                  308
>>> 29  02EB012  3009200202            43.811429            89.123497  14009.738178    On-Up          0             2                19974                    2
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

    # plot the matches in an interactive plot
    browser.match_browser(hydat, pwqmn, network, match_df, bbox)
    

if __name__ == "__main__":
    main()

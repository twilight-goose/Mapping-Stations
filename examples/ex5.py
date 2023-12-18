import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
import browser
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox
from matplotlib import pyplot as plt


"""
Expected Terminal Output (file paths preceding "Mapping-Stations" will differ):

>>> python ex5.py

>>> Creating a connection to 'E:\Python projects\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'E:\Python projects\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> BBox provided but no lat/lon fields found. Skipping BBox query.
>>> Creating a connection to 'E:\Python projects\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> Loading rivers from 'E:\Python projects\Mapping-Stations\examples/..\data\OHN\Ontario_Hydro_Network_(OHN)_-_Watercourse.shp'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Creating a connection to 'E:\Python projects\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'E:\Python projects\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
   >>> hydat_id    pwqmn_id  hydat_dist_from_net  pwqmn_dist_from_net          dist      pos  seg_apart  data_overlap  total_hydat_records  total_pwqmn_records
>>> 0   02EA006  3012400202            67.098591             0.295476   1700.666633     Down          3            64                30333                   64
>>> 1   02EA006  3012400102            67.098591             7.408687   4169.973738     Down         12           194                30333                  194
>>> 2   02EA005  3012400102            16.962489             7.408687   7894.037701     Down         20           194                38870                  194
>>> 3   02EB007  3008500602            70.766068             0.093566   3776.371041       Up          9             0                 8507                  238
>>> 4   02EB008  3008500902            49.216984             0.643809    310.248873    On-Up          0           193                26265                  193
>>> 5   02EB004  3008500602            21.935542             0.093566     30.923688    On-Up          0           238                38462                  238
>>> 6   02DD009  3013302302             6.446230             1.446740     43.451882  On-Down          0            98                12850                  171
>>> 7   02EA001  3009800302            29.484851             2.087398   3910.138179     Down          6             0                  792                   61
>>> 8   02EA001  3009800402            29.484851             2.367882   4900.174373     Down          6             0                  792                   59
>>> 9   02EB012  3008500102            37.586724             7.285121     64.850527  On-Down          0           308                19974                  308
>>> 10  02EB105  3008502502            32.101975             1.128910     31.614124    On-Up          0            19                 1026                   21
>>> 11  02EB010  3008500102             0.975112             7.285121   9848.652301     Down         24            11                12129                  308
>>> 12  02EB006  3008500102             2.636719             7.285121  10814.163115     Down         26           308                30246                  308
>>> 13  02EB006  3009200202             2.636719             6.570948   4286.953203       Up          8             2                30246                    2
>>> 14  02EB006  3008501601             2.636719            11.044989  11820.282001       Up         20            31                30246                   31
>>> 15  02EB006  3008500302             2.636719             1.758571   6084.108165       Up         11           248                30246                  248
>>> 16  02EB011  3009200102            31.197777             4.517862    336.848454       Up          0           297                20230                  297
>>> 17  02EB005  3009200102           101.081656             4.517862  11287.235726     Down         17             0                 4985                  297
>>> 18  02EB005  3009200202           101.081656             6.570948   3600.401277       Up          5             0                 4985                    2
>>> 19  02EB005  3008500102           101.081656             7.285121  11500.715041     Down         29             0                 4985                  308
>>> 20  02EB005  3008501601           101.081656            11.044989  11133.730075       Up         17             0                 4985                   31
>>> 21  02EB005  3008500302           101.081656             1.758571   5397.556239       Up          8             0                 4985                  248
>>> 22  02EB103  3008502802             8.297458             9.361552     18.925278  On-Down          0            52                 2262                  242
>>> 23  02EB009  3009200102            54.505443             4.517862   8863.486486     Down         12             5                11765                  297
>>> 24  02EB009  3009200202            54.505443             6.570948   6024.150516       Up         10             0                11765                    2
>>> 25  02EB009  3008500302            54.505443             1.758571   7821.305478       Up         13             4                11765                  248
>>> Loading rivers from 'E:\Python projects\Mapping-Stations\examples/..\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'

Note: A matplotlib window will open. This window has to be closed manually.
See examples/example_output/ex5.png for expected window appearence.
"""


def main(timed=False):
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)
    
    # load stations
    hydat = load_data.get_hydat_stations(bbox=bbox)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)

    # Load the Onario Hydro Network to use as a river network for matching
    path = os.path.join(load_data.data_path,
                        os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))
    lines = load_data.load_rivers(path=path, bbox=bbox)

    # add geographical reference to station data
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
                                    max_distance=12000,     # [m] CHANGE THIS WHEN ACTUALLY MATCHING
                                max_depth=1000)         # increase maximum depth because OHN is a much
                                                        # higher resolution dataset, compared to hydroRIVERS
                                                        # setting it to 1000 to impose almost no restriction
                                                        # on matching
    
    # load the date ranges of the hydat and pwqmn data
    hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=match_df['pwqmn_id'].to_list())
    
    # calculate the days of data overlap (number of days where record data
    # is available for both stations)
    match_df = gdf_utils.assign_period_overlap(match_df, 'hydat', hydat_dr, "pwqmn", pwqmn_dr)
    
    # display the list of matches
    print(match_df.drop(columns='path').to_string())

    # plot the matches in an interactive plot
    browser.match_browser(hydat, pwqmn, network, match_df, bbox, timed=timed)


if __name__ == "__main__":
    main()

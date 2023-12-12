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

>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> BBox provided but no lat/lon fields found. Skipping BBox query.
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>> Loading rivers from 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\OHN\Ontario_Hydro_Network_(OHN)_-_Watercourse.shp'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Warning: Edges GeoDataFrame does not contain LENGTH_KM field.GeoPandas computed length will be used.
>>> Warning: Edges GeoDataFrame does not contain LENGTH_KM field.GeoPandas computed length will be used.
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\PWQMN_cleaned\PWQMN.sqlite3'
>>>    hydat_id    pwqmn_id  hydat_dist_from_net  pwqmn_dist_from_net          dist      pos  seg_apart  data_overlap  total_hydat_records  total_pwqmn_records
>>> 0   02EA006  3012400202            67.098608             0.295476   1725.879401     Down          3            64                30333                   64
>>> 1   02EA006  3012400102            67.098608             7.408690   4231.723541     Down         12           194                30333                  194
>>> 2   02EA005  3012400102            16.962494             7.408690   8010.179431     Down         20           194                38870                  194
>>> 3   02EB007  3008500602            70.766084             0.093566   3838.692706       Up          9             0                 8507                  238
>>> 4   02EB008  3008500902            49.216994             0.643810    315.430130    On-Up          0           193                26265                  193
>>> 5   02EB004  3008500602            21.935546             0.093566     30.923690    On-Up          0           238                38462                  238
>>> 6   02DD009  3013302302             6.446232             1.446741     43.564989  On-Down          0            98                12850                  171
>>> 7   02EA001  3009800302            29.484851             2.087398   3971.484469     Down          6             0                  792                   61
>>> 8   02EA001  3009800402            29.484851             2.367882   4977.059269     Down          6             0                  792                   59
>>> 9   02EB012  3008500102            37.586729             7.285121     64.850526  On-Down          0           308                19974                  308
>>> 10  02EB105  3008502502            32.101981             1.128910     31.614128    On-Up          0            19                 1026                   21
>>> 11  02EB010  3008500102             0.975112             7.285121  10018.495754     Down         24            11                12129                  308
>>> 12  02EB006  3008500102             2.636719             7.285121  11000.633980     Down         26           308                30246                  308
>>> 13  02EB006  3009200202             2.636719             6.570949   4360.732621       Up          8             2                30246                    2
>>> 14  02EB006  3008500302             2.636719             1.758571   6188.870504       Up         11           248                30246                  248
>>> 15  02EB011  3009200102            31.197777             4.517862    339.484760       Up          0           297                20230                  297
>>> 16  02EB005  3009200102           101.081675             4.517862  11480.659101     Down         17             0                 4985                  297
>>> 17  02EB005  3009200202           101.081675             6.570949   3662.363238       Up          5             0                 4985                    2
>>> 18  02EB005  3008500102           101.081675             7.285121  11699.003363     Down         29             0                 4985                  308
>>> 19  02EB005  3008501601           101.081675            11.044990  11325.491588       Up         17             0                 4985                   31
>>> 20  02EB005  3008500302           101.081675             1.758571   5490.501121       Up          8             0                 4985                  248
>>> 21  02EB103  3008502802             8.297460             9.361554     18.925284  On-Down          0            52                 2262                  242
>>> 22  02EB009  3009200102            54.505444             4.517862   9015.211960     Down         12             5                11765                  297
>>> 23  02EB009  3009200202            54.505444             6.570949   6127.810379       Up         10             0                11765                    2
>>> 24  02EB009  3008500302            54.505444             1.758571   7955.948262       Up         13             4                11765                  248
>>> Loading rivers from 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\examples/..\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'

Note: A matplotlib window will open. This window has to be closed manually.
See "examples/example_output/ex5.png" for expected window appearence.
"""


def main():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

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
    # display the list of matches
    print(match_df.drop(columns='path').to_string())

    # plot the matches in an interactive plot
    browser.match_browser(hydat, pwqmn, network, match_df, bbox)


if __name__ == "__main__":
    main()

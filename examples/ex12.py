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
>>>         pwqmn_id hydat_id  pwqmn_dist_from_net  hydat_dist_from_net          dist  data_overlap  C station ID Q station ID
>>> 0   1.601841e+10  02GA014            40.340714            57.509187     17.345681         415.0  1.601841e+10         same
>>> 1   1.601841e+10  02GA027            40.340714           125.134537   4713.658838           0.0           NaN          NaN
>>> 2   1.601841e+10  02GA001            40.340714            92.101287   9489.779028           0.0           NaN          NaN
>>> 3   1.601841e+10  02GA022            40.340714           141.416757   4493.149667           0.0           NaN          NaN
>>> 4   1.601840e+10  02GA001            19.487934            92.101287   8217.495285           0.0           NaN          NaN
>>> 5   1.601840e+10  02GA016            19.487934            70.067906    736.928477         665.0  1.601840e+10         same
>>> 6   1.601840e+10  02GA027            19.487934           125.134537  12993.615476           0.0           NaN          NaN
>>> 7   1.601841e+10  02GA028            94.153415           100.693319      8.550945         404.0  1.601841e+10         same
>>> 8   1.601841e+10  02GA017            94.153415            78.267666  13906.177885           0.0           NaN          NaN
>>> 9   1.601841e+10  02GA040           114.098742           148.236874    150.469919         444.0  1.601841e+10         same
>>> 10  1.601841e+10  02GA007           114.098742           241.034134   3813.962581           0.0           NaN          NaN
>>> 11  1.601841e+10  02GA033           114.098742            80.077149   2872.032116         215.0           NaN          NaN
>>> 12  1.601841e+10  02GA034           167.201707            44.019533   1111.405986         350.0  1.601841e+10         same
>>> 13  1.601841e+10  02GA002           167.201707            56.153488   7897.793360           0.0           NaN          NaN
>>> 14  1.601840e+10  02GA023            75.983914           151.152767   2287.961871         561.0  1.601840e+10         same
>>> 15  1.601840e+10  02GA036            75.983914           111.766642  11992.240146         179.0           NaN          NaN
>>> 16  1.601841e+10  02GA029             0.754923            15.681901     34.521460         403.0  1.601841e+10         same
>>> 17  1.601841e+10  02GA015             0.754923           104.508234   6962.552046         403.0           NaN          NaN
>>> 18  1.601841e+10  02GA031             0.754923           157.734632   8382.847735         403.0           NaN          NaN
>>> 19  1.601840e+10  02GA015            57.698733           104.508234     66.833558         418.0  1.601840e+10         same
>>> 20  1.601840e+10  02GA008            57.698733           185.540550  14609.876857           0.0           NaN          NaN
>>> 21  1.601840e+10  02GA020            57.698733           241.750154   4160.597542           0.0           NaN          NaN
>>> 22  4.001304e+09  02GD014            82.921413            43.884174     43.322512         424.0  4.001304e+09         same
>>> 23  1.601840e+10  02GA018           327.475513            35.377813   3882.546756         470.0  1.601840e+10         same
>>> 24  1.601840e+10  02GA003           176.918084            96.901684  10293.680205         588.0  1.601840e+10         same
>>> 25  1.601840e+10  02GA004           176.918084            74.664883    413.169680           0.0           NaN          NaN
>>> 26  1.601840e+10  02GA009           176.918084            19.345392  11442.676225           0.0           NaN          NaN
>>> 27  4.001308e+09  02GD021           177.800623           157.715986     24.584509         218.0  4.001308e+09         same
>>> 28  1.601840e+10  02GA010           175.621224           749.565669   9462.403721         548.0  1.601840e+10         same
>>> 29  4.001305e+09  02GD015            17.817012            14.604214   6611.327502         299.0  4.001305e+09         same
>>> 30  4.001305e+09  02GD003            17.817012            93.700858   7849.378813         289.0           NaN          NaN
>>> 31  1.601841e+10  02GB004           398.121766           289.630131   6201.690198           0.0           NaN          NaN
>>> 32  1.601841e+10  02GB007           398.121766           355.183880   1424.382777         387.0  1.601841e+10         same
>>> 33  1.601840e+10  02GB001           551.434832            84.615396   3255.977999         491.0  1.601840e+10         same
>>> 34  1.601841e+10  02GB008            98.608700           110.220647     17.753243         469.0  1.601841e+10         same
>>> 35  1.601841e+10  02GB003            98.608700           280.261950   3594.996968           0.0           NaN          NaN
>>> 36  4.001303e+09  02GD003            58.553040            93.700858   1354.329743         312.0  4.001303e+09         same
>>> 37  4.001303e+09  02GD028            58.553040           310.542658   5949.037417          40.0           NaN          NaN
>>> 38  1.601841e+10  02GB010           167.880784           168.367476     21.263013         300.0  1.601841e+10         same
>>> 39  1.601841e+10  02GB005           167.880784           238.081986   3532.287762           0.0           NaN          NaN
>>> 40  1.601090e+10  02GC017           451.329170           446.815987     11.497269         236.0  1.601090e+10         same
>>> 41  1.601640e+10  02GC022            10.417868            28.136444     29.228924         408.0  1.601640e+10         same
>>> 42  1.601590e+10  02GC008            52.878503            37.880957     83.284173         267.0  1.601590e+10         same
>>> 43  1.601590e+10  02GC012            52.878503            37.464646   5166.580770         118.0           NaN          NaN
>>> 44  4.002701e+09  02GG002           210.997633           227.614186     27.357883         369.0  4.002701e+09         same
>>> 45  1.601090e+10  02GC026            48.584550           103.465066     63.421805         147.0  1.601090e+10         same
>>> 46  1.601090e+10  02GC004            48.584550            47.415726   5022.640372           0.0           NaN          NaN
>>> 47  1.601090e+10  02GC015            48.584550            15.920148   7209.302544           0.0           NaN          NaN
>>> 48  1.601240e+10  02GC007           176.036578           193.515440     24.833672         143.0  1.601240e+10         same
>>> 49  4.002702e+09  02GG007           138.686411           484.197873  11756.720999           0.0           NaN          NaN
>>> 50  4.002702e+09  02GG003           138.686411           167.975517    321.413859         143.0  4.002702e+09         same
>>> 51  4.001306e+09  02GE003            76.197197            25.079773  12109.403578         320.0  4.001306e+09         same
>>> 52  4.001000e+09  02GH002            17.034799           217.734533   4591.820577         157.0  4.001000e+09         same
>>> 53  1.000020e+10  02GH003           475.798308           462.910467     13.064921         337.0  1.000020e+10         same
>>> 54           NaN      NaN                  NaN                  NaN           NaN           NaN  1.601840e+10      02GA015
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

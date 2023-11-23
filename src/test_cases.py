import pytest
import browser
import load_data
import gdf_utils
import plot_utils
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox
from gen_util import period_overlap, days_overlapped
import os
import sys
import pandas as pd
import numpy as np
# sys.path.insert(0,
    # os.path.join(
        # os.path.dirname(load_data.proj_path),
        # 'Watershed_Delineation',
        # 'src',
        # 'PySheds')
# )
# import main as pyshed_main

    
# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##
    
    
def test_hydat_load():
    subset = ['02LA019', '02KF009', '02KF004', '04MC001']
    period = ['1999-07-10', '1999-10-11']
    period2 = [None, '1999-07-10']
    period3 = ['1999-07-10', None]
    bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    sample = 10
    
    hydat = load_data.get_hydat_stations(subset=subset)
    hydat.fillna(value=np.nan, inplace=True)
    test1 = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'test_1.csv'),
                        dtype={'REGIONAL_OFFICE_ID':str})
    test1.drop(columns=["Unnamed: 0"], inplace=True)
    pd.testing.assert_frame_equal(hydat, test1, check_dtype=False)

    hydat = load_data.get_hydat_stations(period=period)
    hydat.fillna(value=np.nan, inplace=True)
    test2 = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'test_2.csv'),
                        dtype={'REGIONAL_OFFICE_ID':str})
    test2.drop(columns=["Unnamed: 0"], inplace=True)
    pd.testing.assert_frame_equal(hydat, test2, check_dtype=False)
    
    hydat = load_data.get_hydat_stations(bbox=bbox)
    hydat.fillna(value=np.nan, inplace=True)
    test3 = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'test_3.csv'),
                        dtype={'REGIONAL_OFFICE_ID':str})
    test3.drop(columns=["Unnamed: 0"], inplace=True)
    assert hydat['Station_ID'].to_list() == \
        ["02EA001","02EB005","02EB006","02EB009","02EB010", "02EB011","02EB012","02EB103","02EB105"]
    pd.testing.assert_frame_equal(hydat, test3, check_dtype=False)
    
    hydat = load_data.get_hydat_stations(sample=sample)
    assert hydat.shape == (10, 15)
    
    hydat = load_data.get_hydat_stations(bbox=bbox, period=period)
    hydat.fillna(value=np.nan, inplace=True)
    test5 = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'test_5.csv'),
                        dtype={'REGIONAL_OFFICE_ID':str})
    test5.drop(columns=["Unnamed: 0"], inplace=True)
    assert hydat['Station_ID'].to_list() == ["02EB006","02EB011","02EB012"]
    pd.testing.assert_frame_equal(hydat, test5, check_dtype=False)
    
    hydat = load_data.get_hydat_stations(to_csv="test_6", bbox=bbox, period=period, sample=sample)
    assert hydat['Station_ID'].sort_values().to_list() == ["02EB006","02EB011","02EB012"]
    # don't compare the frames because the sample keyword changes index order
    
    hydat = load_data.get_hydat_stations(period=period2)
    hydat.fillna(value=np.nan, inplace=True)
    test7 = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'test_7.csv'),
                        dtype={'REGIONAL_OFFICE_ID':str})
    test7.drop(columns=["Unnamed: 0"], inplace=True)
    pd.testing.assert_frame_equal(hydat, test7, check_dtype=False)

    hydat = load_data.get_hydat_stations(period=period3)
    hydat.fillna(value=np.nan, inplace=True)
    test8 = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'test_8.csv'),
                        dtype={'REGIONAL_OFFICE_ID':str})
    test8.drop(columns=["Unnamed: 0"], inplace=True)
    pd.testing.assert_frame_equal(hydat, test8, check_dtype=False)
    
    # test hydat data range generation
    dly_flows = pd.read_csv(os.path.join(load_data.data_path, 'Hydat', 'dly_flow_test_example.csv'))
    out_data = load_data.hydat_create_data_range(unittest=dly_flows)
    # refer to
    assert out_data['Station_ID'] == ["02EB004", "02EB004", "02EB004"]
    assert out_data['P_Start'] == ['2010-05-01', '2010-08-26', '2010-09-12']
    assert out_data['P_End'] == ['2010-06-11', '2010-09-07', '2010-09-29']


# ========================================================================= ##
# License ================================================================= ##

def main():
    timer = Timer()
    
    return
    
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_stations(bbox=bbox)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network, max_distance=300000)

    print(edge_df.drop(columns='path').to_string())

    browser.match_browser(hydat, network, pwqmn, edge_df, bbox, color='blue')
    # network_compare()
    
    # output = "output"
    # if not os.path.isdir(output):
        # os.mkdir(output)
    
    # basins = load_data.get_monday_files()['basins.csv']
    # dem = os.path.join(load_data.data_path, "n40w090_dem.tif")
    # pyshed_main.delineate(dem, output, basins)
    
    timer.stop()


if __name__ == "__main__":
    main()

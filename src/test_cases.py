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


"""

Overview:

"""

# ========================================================================= ##
# gen_util tests ========================================================== ##
# ========================================================================= ##


def test_bbox():
    bbox1 = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    bbox2 = BBox(-80, -79.5, 45, 45.5)
    
    assert bbox1.bounds == bbox2.bounds == bbox1.to_tuple() == bbox2.to_tuple()
    
    assert bbox1.contains_point((-79.9, 45.2)) == True
    assert bbox1.contains_point((-89, 45.2)) == False
    assert bbox1.contains_point((-80, 45)) == False
    
    query1 = "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    query2 = "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    
    assert bbox1.sql_query('X', 'Y') == query1
    assert bbox2.sql_query('X', 'Y') == query2
    
    assert BBox.sql_query(bbox1, 'X', 'Y') == query1
    assert BBox.sql_query(bbox2, 'X', 'Y') == query2
    
    
def test_period():
    period1 = ['2020-10-11', None]
    period2 = [None, '2020-10-11']
    period3 = ['2020-09-11', '2020-10-11']
    
    assert Period.check_period(period1) is None
    assert Period.check_period(period2) is None
    assert Period.check_period(period3) is None
    
    # invalid periods
    pytest.raises(ValueError, Period.check_period, ['2010-10-11', '2009-11-11'])
    pytest.raises(ValueError, Period.check_period, "2022-10-11")
    pytest.raises(ValueError, Period.check_period, ["2022-10-11"])
    pytest.raises(ValueError, Period.check_period, ["", "", ""])
        
    assert Period.sql_query(period1, ['DATE']) == \
        "(strftime('%Y-%m-%d', '2020-10-11') <= DATE AND DATE <= strftime('%Y-%m-%d', '9999-12-31'))"
    assert Period.sql_query(period1, ['YEAR_FROM', 'YEAR_TO']) == \
        "(strftime('%Y', '2020-10-11') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '9999-12-31')) OR " + \
        "(strftime('%Y', '2020-10-11') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '9999-12-31')) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO) OR " + \
        "(YEAR_FROM <= strftime('%Y', '9999-12-31') AND strftime('%Y', '9999-12-31') <= YEAR_TO)"
    assert Period.sql_query(period1, ['YEAR', 'MONTH']) == \
        "(strftime('%Y-%m', '2020-10-11') <= strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND" + \
        " strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= strftime('%Y-%m', '9999-12-31'))"
        
    assert Period.sql_query(period2, ['DATE']) == \
        "(strftime('%Y-%m-%d', '0000-01-01') <= DATE AND DATE <= strftime('%Y-%m-%d', '2020-10-11'))"
    assert Period.sql_query(period2, ['YEAR_FROM', 'YEAR_TO']) == \
        "(strftime('%Y', '0000-01-01') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '2020-10-11')) OR " + \
        "(strftime('%Y', '0000-01-01') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '2020-10-11')) OR " + \
        "(YEAR_FROM <= strftime('%Y', '0000-01-01') AND strftime('%Y', '0000-01-01') <= YEAR_TO) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO)"
    assert Period.sql_query(period2, ['YEAR', 'MONTH']) == \
        "(strftime('%Y-%m', '0000-01-01') <= strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= strftime('%Y-%m', '2020-10-11'))"
        
    assert Period.sql_query(period3, ['DATE']) == \
        "(strftime('%Y-%m-%d', '2020-09-11') <= DATE AND DATE <= strftime('%Y-%m-%d', '2020-10-11'))"
    assert Period.sql_query(period3, ['YEAR_FROM', 'YEAR_TO']) == \
        "(strftime('%Y', '2020-09-11') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '2020-10-11')) OR " + \
        "(strftime('%Y', '2020-09-11') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '2020-10-11')) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-09-11') AND strftime('%Y', '2020-09-11') <= YEAR_TO) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO)"
    assert Period.sql_query(period3, ['YEAR', 'MONTH']) == \
        "(strftime('%Y-%m', '2020-09-11') <= strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= strftime('%Y-%m', '2020-10-11'))"

    dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-05', '1991-02-06', '1991-02-07']
    periods = Period.get_periods(dates=dates,silent=True)
    assert periods == [['1991-02-01', '1991-02-03'], ['1991-02-05', '1991-02-07']]


def test_build_sql():
    period = ['2010-10-11', '2011-11-11']
    bbox = BBox(-80, -79.5, 45, 45.5)
    sample = 5
    subset = ["2A", "4N", "9K", "i8"]
    subset2 = [123, 234, 345, 456]
    subset3 = "sample_subset.csv"
    
    id_query = load_data.id_query_from_subset(subset, ['Station_ID'])
    id_query2 = load_data.id_query_from_subset(subset2, ['STATION_NUMBER'])
    id_query3 = load_data.id_query_from_subset("sample_subset.csv", ['Station_ID'])
    
    assert id_query == 'Station_ID in ("2A", "4N", "9K", "i8")'
    assert id_query2 == 'STATION_NUMBER in (123, 234, 345, 456)'
    assert id_query3 == 'Station_ID in (123, 234, "9K", "i8")'
   
    query = load_data.build_sql_query(fields=['name', 'Station_ID', 'X', 'Y', 'Date', 'var'],
                            subset=subset, period=period, bbox=bbox, sample=sample,
                            var=['v','q'], car='merc')
                            
    assert query == ' WHERE Station_ID in ("2A", "4N", "9K", "i8") AND ' + \
        "(strftime('%Y-%m-%d', '2010-10-11') <= Date AND Date <= strftime('%Y-%m-%d', '2011-11-11'))" + \
        ' AND (-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y) AND var in ("v", "q")' + \
        ' ORDER BY RANDOM() LIMIT 5'
    

def test_period_overlap():
    periods1 = [["2002-02-12", "2005-10-12"], ["2006-04-12", "2008-10-12"]]
    
    periods2 = [["2002-02-12", "2002-02-12"], ["2004-02-12", "2004-02-12"],
                ["2005-10-12", "2005-10-13"], ["2006-04-11", "2006-04-12"],
                ["2006-06-12", "2007-06-12"], ["2008-10-12", "2008-10-13"]]
                
    periods3 = [["2005-10-10", "2006-04-20"]]
                
    expected = 1 + 1 + 1 + 1 + 366 + 1
    
    assert days_overlapped(*periods1[0], *periods2[0]) == 1
    assert days_overlapped(*periods1[0], *periods2[2]) == 1
    assert days_overlapped(*periods1[0], *periods2[3]) == 0
    assert days_overlapped(*periods1[1], *periods2[0]) == 0
    assert days_overlapped(*periods1[1], *periods2[3]) == 1
    assert days_overlapped(*periods1[0], "2005-10-10", "2005-10-13") == 3
    assert days_overlapped(*periods1[0], "2005-10-01", "2005-10-10") == 10
    
    assert period_overlap(periods1, periods2) == expected
    assert period_overlap(periods1, periods3) == 12
    
    
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

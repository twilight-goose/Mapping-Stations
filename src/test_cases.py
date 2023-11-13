import pytest
import browser
import load_data
import gdf_utils
import plot_utils
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox
from gen_util import period_overlap, days_overlapped
import os
import sys

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
    
    assert bbox1.sql_query('X', 'Y') == "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    assert bbox2.sql_query('X', 'Y') == "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    
    
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
        "(strftime('%Y-%m', '2020-10-11') <= " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= " + \
        "strftime('%Y-%m', '9999-12-31'))"
        
    assert Period.sql_query(period2, ['DATE']) == \
        "(strftime('%Y-%m-%d', '0000-01-01') <= DATE AND DATE <= strftime('%Y-%m-%d', '2020-10-11'))"
    assert Period.sql_query(period2, ['YEAR_FROM', 'YEAR_TO']) == \
        "(strftime('%Y', '0000-01-01') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '2020-10-11')) OR " + \
        "(strftime('%Y', '0000-01-01') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '2020-10-11')) OR " + \
        "(YEAR_FROM <= strftime('%Y', '0000-01-01') AND strftime('%Y', '0000-01-01') <= YEAR_TO) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO)"
    assert Period.sql_query(period2, ['YEAR', 'MONTH']) == \
        "(strftime('%Y-%m', '0000-01-01') <= " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= " + \
        "strftime('%Y-%m', '2020-10-11'))"
        
    assert Period.sql_query(period3, ['DATE']) == \
        "(strftime('%Y-%m-%d', '2020-09-11') <= DATE AND DATE <= strftime('%Y-%m-%d', '2020-10-11'))"
    assert Period.sql_query(period3, ['YEAR_FROM', 'YEAR_TO']) == \
        "(strftime('%Y', '2020-09-11') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '2020-10-11')) OR " + \
        "(strftime('%Y', '2020-09-11') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '2020-10-11')) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-09-11') AND strftime('%Y', '2020-09-11') <= YEAR_TO) OR " + \
        "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO)"
    assert Period.sql_query(period3, ['YEAR', 'MONTH']) == \
        "(strftime('%Y-%m', '2020-09-11') <= " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
        "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= " + \
        "strftime('%Y-%m', '2020-10-11'))"
        
    dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-04', '1991-02-05', '1991-02-06', '1991-02-07']
    periods = Period.get_periods(dates=dates,silent=True)
    assert periods == [['1991-02-01', '1991-02-07']]

    dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-05', '1991-02-06', '1991-02-07']
    periods = Period.get_periods(dates=dates,silent=True)
    assert periods == [['1991-02-01', '1991-02-03'], ['1991-02-05', '1991-02-07']]


def test_build_sql():
    period = ['2010-10-11', '2011-11-11']
    bbox = BBox(-80, -79.5, 45, 45.5)
    sample = 5
    subset = ["2A", "4N", "9K", "i8"]
    
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
    assert subset.sort() == hydat['Station_ID'].to_list().sort()

    hydat = load_data.get_hydat_stations(period=period)
    assert hydat.shape == (1765, 15)
    
    hydat = load_data.get_hydat_stations(bbox=bbox)
    assert hydat['Station_ID'].to_list() == \
        ["02EA001","02EB005","02EB006","02EB009","02EB010", "02EB011","02EB012","02EB103","02EB105"]
    assert hydat.shape == (9, 15)
    
    hydat = load_data.get_hydat_stations(sample=sample)
    assert hydat.shape == (10, 15)
    
    hydat = load_data.get_hydat_stations(bbox=bbox, period=period)
    assert hydat['Station_ID'].to_list() == ["02EB006","02EB011","02EB012"]
    
    hydat = load_data.get_hydat_stations(bbox=bbox, period=period, sample=sample)
    assert hydat['Station_ID'].sort_values().to_list() == ["02EB006","02EB011","02EB012"]

    hydat = load_data.get_hydat_stations(period=period2)
    assert hydat.shape == (6048, 15)

    hydat = load_data.get_hydat_stations(period=period3)
    assert hydat.shape == (2415, 15)


def point_plot_test():
    bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)

    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    ax = plot_utils.add_map_to_plot(extent=bbox.to_ccrs(plot_utils.lambert))
    plot_utils.plot_gdf(pwqmn, ax=ax)
    plot_utils.timed_display()


def snap_test(points, edges, bbox):
    ax = plot_utils.add_map_to_plot(extent=bbox.to_ccrs(plot_utils.lambert))
    plot_utils.plot_closest(points, edges, ax=ax)
    plot_utils.timed_display()


def network_test(lines):
    network = gdf_utils.hyriv_gdf_to_network(lines, plot=True)
    gdf_utils.check_hyriv_network(network)
    plot_utils.timed_display()


def network_compare():
    import os.path

    # bbox = BBox(min_x=-95.154826, max_x=-74.343496, min_y=41.681435, max_y=56.859036)
    
    bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    
    hydat = load_data.get_hydat_stations(bbox=bbox)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)
    
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    path = os.path.join(load_data.data_path,
                        os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))

    print('ohn networking')

    ohn_lines = load_data.load_rivers(path=path, bbox=bbox)
    ohn_lines = gdf_utils.assign_stations(ohn_lines, hydat, prefix='hydat_')
    ohn_lines = gdf_utils.assign_stations(ohn_lines, pwqmn, prefix='pwqmn_')
    ohn_network = gdf_utils.hyriv_gdf_to_network(ohn_lines)

    print('hydrorivers networking')

    hydroRIVERS_lines = load_data.load_rivers(bbox=bbox)
    hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, hydat, prefix='hydat_')
    hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, pwqmn, prefix='pwqmn_')
    hydroRIVERS_network = gdf_utils.hyriv_gdf_to_network(hydroRIVERS_lines)

    ohn_edge_df = gdf_utils.dfs_search(ohn_network, max_depth=100)
    hydro_edge_df = gdf_utils.dfs_search(hydroRIVERS_network)

    ohn_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
    hydro_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
    table = hydro_edge_df.merge(ohn_edge_df, how='outer', on=['hydat_id', 'pwqmn_id'],
                                suffixes=('_hyRivers', '_OHN'))
    table = table.assign(error=abs(table['dist_hyRivers'] - table['dist_OHN']) /
                               table['dist_OHN'])

    table.to_csv(os.path.join(load_data.data_path, 'table2.csv'))


def assign_all():
    timer = Timer()
    path = os.path.join(
        load_data.data_path,
        os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp")
    )
    bbox = ON_bbox

    print('loading rivers')
    ohn_rivers = load_data.load_rivers(path=path, bbox=bbox)
    timer.stop()
    print('loading stations')
    hydat = load_data.get_hydat_stations(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = load_data.get_pwqmn_stations(bbox=bbox)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)
    timer.stop()
    print('assigning stations')
    ohn_lines = gdf_utils.assign_stations(ohn_rivers, hydat, prefix='hydat_', save_dist=True)
    ohn_lines = gdf_utils.assign_stations(ohn_rivers, pwqmn, prefix='pwqmn_', save_dist=True)
    timer.stop()
    
    
def drainage_compare():
    """
    There is no significant correlation between distance between HYDAT
    stations and difference in drainage area (see plots/drainage delta
    vs distance).
    """
    timer = Timer()
    
    path = os.path.join(
        load_data.data_path,
        os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp")
    )
    
    hydat = load_data.get_hydat_stations(sample=300, bbox=ON_bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    
    ohn_rivers = load_data.load_rivers(path=path, bbox=ON_bbox)
    ohn_lines = gdf_utils.assign_stations(ohn_rivers, hydat, prefix='origin_')
    ohn_lines = gdf_utils.assign_stations(ohn_rivers, hydat, prefix='candidate_')
    
    ohn_lines = gdf_utils.hyriv_gdf_to_network(ohn_lines)
    
    edge_df = gdf_utils.dfs_search(ohn_lines, max_depth=100, prefix1='origin_',
                                   prefix2='candidate_')
                                   
    edge_df = edge_df.merge(hydat[['Station_ID', 'DRAINAGE_AREA_GROSS', 'DRAINAGE_AREA_EFFECT']],
                            on_left='origin_id', right_on='Station_ID')
    edge_df = edge_df.merge(hydat[['Station_ID', 'DRAINAGE_AREA_GROSS', 'DRAINAGE_AREA_EFFECT']],
                            on_left='candidate_id', right_on='Station_ID', suffixes=('_og', '_cand'))
    
    edge_df.to_csv('dist_by_delta_drainage.csv')
    
    
def hydat_data_test():
    hydat = load_data.get_hydat_stations(sample=100)
    hydat_flow = load_data.get_hydat_flow(subset=hydat['Station_ID'],
        period=['1975-10-10', '1975-11-11']
    )
    
    drainage_compare()
    
    print(hydat_flow)


def main():
    timer = Timer()
    
    dly_flow = load_data.get_hydat_flow(subset=["02EB004"])
    
    print(dly_flow)
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

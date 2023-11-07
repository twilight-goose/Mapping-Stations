import browser
import load_data
import gdf_utils
import plot_utils
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox
from gen_util import period_overlap
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
# License ================================================================= ##
# ========================================================================= ##


def period_test():
    # Valid periods
    assert Period.check_period(None) is None
    assert Period.check_period(['2020-10-11', None]) is None
    assert Period.check_period([None, '2020-10-11']) is None
    
    # invalide periods
    assert Period.check_period(['2010-10-11', '2009-11-11']) == ValueError
    assert Period.check_period("2022-10-11") == ValueError
    assert Period.check_period(["2022-10-11"]) == ValueError
    
    
def hydat_load_test():
    subset = ['02LA019', '02KF009', '02KF004', '04MC001']
    period = ['1999-07-10', '1999-10-11']
    bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    sample = 10
    
    hydat = load_data.get_hydat_stations(to_csv='test_1', subset=subset)
    assert subset.sort() == hydat['Station_ID'].to_list().sort()

    hydat = load_data.get_hydat_stations(to_csv='test_2', period=period)
    assert hydat.shape == (1770, 6)
    
    d_range = load_data.get_hydat_data_range(period=period)
    
    from datetime import datetime
    for ind, row in d_range.iterrows():
        start = row['P_Start']
        end = row['P_End']
        
        if (start <= period[0] <= end) or \
           (start <= period[1] <= end) or \
           (period[0] <= start <= period[1]) or \
           (period[0] <= end <= period[1]):
            pass
        else:
            # If functions correctly, nothing is outputted
            print(start, end)
    
    hydat = load_data.get_hydat_stations(to_csv='test_3', bbox=bbox)
    assert hydat['Station_ID'].to_list() == \
        ["02EA001","02EB005","02EB006","02EB009","02EB010",
         "02EB011","02EB012","02EB103","02EB105"]
    assert hydat.shape == (9, 6)
    
    hydat = load_data.get_hydat_stations(to_csv='test_4', sample=sample)
    assert hydat.shape == (10, 6)
    
    hydat = load_data.get_hydat_stations(to_csv='test_5', bbox=bbox, period=period)
    assert hydat.shape == (3, 6)
    assert hydat['Station_ID'].to_list() == ["02EB006","02EB011","02EB012"]
    
    hydat = load_data.get_hydat_stations(to_csv='test_6', bbox=bbox, period=period,
                                         sample=sample)
    assert hydat.shape == (3, 6)
    assert hydat['Station_ID'].sort_values().to_list() == ["02EB006","02EB011","02EB012"]
    

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
    
    # Old Algorithm (uses direct distance instead of distance along r)
    # calcs = {'distance': [],
             # 'drainage_delta': []}
    
    # for ind, origin in hydat.iterrows():
        # for ind, candy in hydat.iterrows():
            # calcs['distance'].append(origin.geometry.distance(candy.geometry))
            # calcs['drainage_delta'].append(abs(float(origin['DRAINAGE_AREA_GROSS']) - \
                                               # float(candy['DRAINAGE_AREA_GROSS'])))
    # from pandas import DataFrame
    # 
    # calcs.to_csv('dist_by_delta_drainage.csv')
    
    
def hydat_data_test():
    hydat = load_data.get_hydat_stations(sample=100)
    hydat_flow = load_data.get_hydat_flow(subset=hydat['Station_ID'],
        period=['1975-10-10', '1975-11-11']
    )
    
    drainage_compare()
    
    print(hydat_flow)


def main():
    timer = Timer()
    
    hydat = load_data.get_hydat_stations(sample=10)
    pwqmn = load_data.get_pwqmn_stations(sample=10)
    
    hydat_dr = load_data.get_hydat_data_range(subset=hydat['Station_ID'].iloc[0])
    pwqmn_dr = load_data.get_pwqmn_data_range(subset=pwqmn['Station_ID'].iloc[0])
    
    print(hydat_dr)
    print(pwqmn_dr)
    
    period_overlap(hydat_dr, pwqmn_dr)

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

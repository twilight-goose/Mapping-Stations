import browser
import load_data
import gdf_utils
import plot_utils
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period, ON_bbox
import os
# import sys

# sys.path.insert(0,
    # os.path.join(
        # os.path.dirname(load_data.proj_path),
        # 'Watershed_Delineation',
        # 'src',
        # 'PySheds')
# )
# import main


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


def point_plot_test():
    bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)

    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
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


def network_assign_test():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network)
    print(edge_df.drop(columns='path').to_string())

    browser.match_browser(hydat, network, pwqmn, edge_df, bbox, color='blue')


def network_assign_test_ohn():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    path = os.path.join(load_data.data_path,
                        os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))

    lines = load_data.load_rivers(path=path, bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network)
    print(edge_df.drop(columns='path').to_string())

    browser.match_browser(hydat, network, pwqmn, edge_df, bbox, color='blue')


def plot_array_test():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network)

    plot_utils.plot_match_array(edge_df, add_to_plot=[plot_utils.add_map_to_plot])


def network_compare():
    import os.path

    bbox = BBox(min_x=-95.154826, max_x=-74.343496, min_y=41.681435, max_y=56.859036)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
    
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

    table.to_csv('table2.csv')


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
    hydat = load_data.get_hydat_station_data(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)
    timer.stop()
    print('assigning stations')
    ohn_lines = gdf_utils.assign_stations(ohn_rivers, hydat, prefix='hydat_', save_dist=True)
    ohn_lines = gdf_utils.assign_stations(ohn_rivers, pwqmn, prefix='pwqmn_', save_dist=True)
    timer.stop()


def main():
    timer = Timer()
    timer.stop()


if __name__ == "__main__":
    main()

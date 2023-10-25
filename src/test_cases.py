import browser
import load_data
import gdf_utils
import plot_utils
from gen_util import lambert, geodetic, Can_LCC_wkt, BBox, Timer, Period
import os
"""

Overview:

"""


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##


def period_test():
    # Test 5 types of period;
    # 1. period = <str> (invalid period)
    # 2. period = None
    # 3. period = [None, date]
    # 4. period = [start, None]
    # 5. period = [start, end]

    assert Period.check_period(None) is None
    assert Period.check_period(['2020-10-11', None]) is None
    assert Period.check_period([None, '2020-10-11']) is None
    assert Period.check_period(['2010-10-11', '2009-11-11']) == ValueError
    assert Period.check_period("2022-10-11") == ValueError
    assert Period.check_period(["2022-10-11"]) == ValueError



def hydat_query_test(points, bbox, period):
    """


    :param points:
    :param bbox:
    :param period:
    :return:
    """
    hydat = load_data.get_hydat_station_data(bbox=bbox, period=period)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    ax = plot_utils.add_map_to_plot(extent=bbox.to_ccrs(lambert))
    plot_utils.plot_gdf(points, ax=ax, zorder=4, color='blue')
    plot_utils.plot_gdf(hydat, ax=ax, zorder=5, color='red')

    plot_utils.timed_display()


def pwqmn_query_test(points, bbox, period):
    """
    Expected behaviour:
        Red and blue points. There should be less red points.

    :param points:
    :param bbox:
    :param period:
    :return:
    """
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox, period=period)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    ax = plot_utils.add_map_to_plot(extent=bbox.to_ccrs(plot_utils.lambert))
    plot_utils.plot_gdf(points, ax=ax, zorder=4, color='blue')
    plot_utils.plot_gdf(pwqmn, ax=ax, zorder=5, color='red')

    plot_utils.timed_display()


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

    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    path = os.path.join(load_data.data_path,
                        os.path.join("OHN", "Ontario_Hydro_Network_(OHN)_-_Watercourse.shp"))

    ohn_lines = load_data.load_rivers(path=path, bbox=bbox)
    ohn_lines = gdf_utils.assign_stations(ohn_lines, hydat, prefix='hydat_')
    ohn_lines = gdf_utils.assign_stations(ohn_lines, pwqmn, prefix='pwqmn_')
    ohn_network = gdf_utils.hyriv_gdf_to_network(ohn_lines)

    hydroRIVERS_lines = load_data.load_rivers(bbox=bbox)
    hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, hydat, prefix='hydat_')
    hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, pwqmn, prefix='pwqmn_')
    hydroRIVERS_network = gdf_utils.hyriv_gdf_to_network(hydroRIVERS_lines)

    ohn_edge_df = gdf_utils.dfs_search(ohn_network, max_depth=100, direct_match_dist=100)
    hydro_edge_df = gdf_utils.dfs_search(hydroRIVERS_network)

    from matplotlib import pyplot as plt
    fig = plt.figure(figsize=(14, 7))

    ax = plt.subplot(1, 2, 2, projection=lambert, position=[0.02, 0.04, 0.46, 0.92])
    ax.set_box_aspect(1)
    ax.set_facecolor('white')
    plot_utils.add_map_to_plot(ax=ax, extent=bbox)
    plot_utils.add_grid_to_plot(ax=ax)
    plot_utils.plot_gdf(hydat, ax=ax, zorder=5, color='blue')
    plot_utils.plot_gdf(pwqmn, ax=ax, zorder=5, color='red')
    plot_utils.draw_network(ohn_network, ax=ax)
    plot_utils.plot_paths(ohn_edge_df, ax=ax)
    plot_utils.annotate_stations(hydat, pwqmn, ax=ax, adjust=False)

    ax2 = plt.subplot(1, 2, 1, projection=lambert, position=[0.52, 0.04, 0.46, 0.92])
    ax2.set_box_aspect(1)
    ax2.set_facecolor('white')
    plot_utils.add_map_to_plot(ax=ax2, extent=bbox)
    plot_utils.add_grid_to_plot(ax=ax2)
    plot_utils.plot_gdf(hydat, ax=ax2, zorder=5, color='blue')
    plot_utils.plot_gdf(pwqmn, ax=ax2, zorder=5, color='red')
    plot_utils.draw_network(hydroRIVERS_network, ax=ax2)
    plot_utils.plot_paths(hydro_edge_df, ax=ax2)
    plot_utils.annotate_stations(hydat, pwqmn, ax=ax2, adjust=False)

    ohn_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
    hydro_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
    table = hydro_edge_df.merge(ohn_edge_df, how='outer', on=['hydat_id', 'pwqmn_id'],
                                suffixes=('_hyRivers', '_OHN'))
    table = table.assign(error=abs(table['dist_hyRivers'] - table['dist_OHN']) / table['dist_OHN'])
    print(table)

    plt.show()


def main():
    timer = Timer()

    # network_assign_test()
    # network_assign_test_ohn()
    network_compare()
    timer.stop()


if __name__ == "__main__":
    main()

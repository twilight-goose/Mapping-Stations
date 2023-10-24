import sys
from util_classes import BBox, Timer, Period
import browser
import load_data
import gdf_utils
import plot_utils
import time


"""

Overview:

"""


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##


def tests():
    # Test 5 types of period;
    # 1. period = <str> (invalid period)
    # 2. period = None
    # 3. period = [None, date]
    # 4. period = [start, None]
    # 5. period = [start, end]

    assert Period.check_period("2022-10-11") == TypeError
    assert Period.check_period(["2022-10-11"]) == TypeError


def hydat_query_test(points, bbox, period):
    """


    :param points:
    :param bbox:
    :param period:
    :return:
    """
    hydat = load_data.get_hydat_station_data(bbox=bbox, period=period)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    ax = plot_utils.add_map_to_plot(
        total_bounds=bbox.to_ccrs(plot_utils.lambert)
    )
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

    ax = plot_utils.add_map_to_plot(
        total_bounds=bbox.to_ccrs(plot_utils.lambert)
    )
    plot_utils.plot_gdf(points, ax=ax, zorder=4, color='blue')
    plot_utils.plot_gdf(pwqmn, ax=ax, zorder=5, color='red')

    plot_utils.timed_display()


def point_plot_test():
    bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)

    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    ax = plot_utils.add_map_to_plot(
        total_bounds=bbox.to_ccrs(plot_utils.lambert)
    )
    plot_utils.plot_gdf(pwqmn, ax=ax)
    plot_utils.timed_display()


def snap_test(points, edges, bbox):
    ax = plot_utils.add_map_to_plot(
        total_bounds=bbox.to_ccrs(plot_utils.lambert)
    )
    plot_utils.plot_closest(points, edges, ax=ax)
    plot_utils.timed_display()


def network_test(lines):
    network = gdf_utils.hyriv_gdf_to_network(lines, plot=True)
    gdf_utils.check_hyriv_network(network)
    plot_utils.timed_display()


def network_assign_test(bbox=BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)):

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, 'STATION_NUMBER', prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, 'Location_ID', prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network)
    print(edge_df.drop(columns='path').to_string())

    browser.match_browser(hydat, network, pwqmn, edge_df, bbox, color='blue')


def browser_test_1():
    bbox = BBox(min_x=-80, max_x=-75, min_y=45, max_y=50)
    hydat = load_data.get_hydat_station_data(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    browser.browser(hydat, bbox)


def browser_test_2():
    bbox = BBox(min_x=-80, max_x=-75, min_y=45, max_y=50)
    lines = load_data.load_rivers(bbox=bbox)
    plot_utils.line_browser(lines, bbox)



def plot_array_test():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    lines = load_data.load_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, 'STATION_NUMBER', prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, 'Location_ID', prefix='pwqmn_')

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
    hydroRIVERS_lines = load_data.load_rivers(bbox=bbox)

    ohn_lines = gdf_utils.assign_stations(ohn_lines, hydat, prefix='hydat_')
    ohn_lines = gdf_utils.assign_stations(ohn_lines, pwqmn, prefix='pwqmn_')
    ohn_network = gdf_utils.hyriv_gdf_to_network(ohn_lines)

    hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, hydat, prefix='hydat_')
    hydroRIVERS_lines = gdf_utils.assign_stations(hydroRIVERS_lines, pwqmn, prefix='pwqmn_')
    hydroRIVERS_network = gdf_utils.hyriv_gdf_to_network(hydroRIVERS_lines)

    ohn_edge_df = gdf_utils.dfs_search(ohn_network, max_depth=100, direct_match_dist=250)
    hydro_edge_df = gdf_utils.dfs_search(hydroRIVERS_network)

    ohn_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)
    hydro_edge_df.drop(columns=['path', 'seg_apart'], inplace=True)

    table = hydro_edge_df.merge(ohn_edge_df, how='outer', on=['hydat_id', 'pwqmn_id'],
                              suffixes=('_hyRivers', '_OHN'))
    table = table.assign(error=abs(table['dist_hyRivers'] - table['dist_OHN']) / table['dist_OHN'])

    print(table)

    from matplotlib import pyplot as plt
    fig = plt.figure(figsize=(14, 7))

    ax = plt.subplot(1, 2, 1, projection=plot_utils.lambert, position=[0.04, 0.08, 0.42, 0.84])
    ax.set_box_aspect(1)
    ax.set_facecolor('white')
    plot_utils.add_map_to_plot(ax=ax, total_bounds=bbox)
    plot_utils.draw_network(ohn_network, ax=ax)
    plot_utils.plot_paths(ohn_edge_df, ax=ax)
    plot_utils.annotate_stations(hydat, pwqmn, ax)

    ax2 = plt.subplot(1, 2, 2, position=[0.52, 0.04, 0.46, 0.92])
    ax2.set_box_aspect(1)
    ax2.set_facecolor('white')
    plot_utils.add_map_to_plot(ax=ax2, total_bounds=bbox)
    plot_utils.draw_network(hydroRIVERS_network, ax=ax2)
    plot_utils.plot_paths(hydro_edge_df, ax=ax2)
    plot_utils.annotate_stations(hydat, pwqmn, ax2)

    plt.show()


def main():
    timer = Timer()

    load_data.generate_pwqmn_sql()
    network_compare()

    # hydat = load_data.get_hydat_station_data(period=['2011-05-12', '2011-07-12'])
    # print(hydat.dtypes)
    # print(hydat[['YEAR', 'MONTH']].sort_values(by='MONTH'))

    timer.stop()


if __name__ == "__main__":
    main()

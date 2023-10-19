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
        total_bounds=bbox.to_ccrs(gdf_utils.lambert)
    )
    plot_utils.plot_gdf(points, ax=ax, zorder=4, color='blue')
    plot_utils.plot_gdf(pwqmn, ax=ax, zorder=5, color='red')

    plot_utils.timed_display()


def point_plot_test(points, bbox):
    ax = plot_utils.add_map_to_plot(
        total_bounds=bbox.to_ccrs(gdf_utils.lambert)
    )
    plot_utils.plot_gdf(points, ax=ax)
    plot_utils.timed_display()


def snap_test(points, edges, bbox):
    ax = plot_utils.add_map_to_plot(
        total_bounds=bbox.to_ccrs(gdf_utils.lambert)
    )
    plot_utils.plot_closest(points, edges, ax=ax)
    ax.xaxis.set_zorder(7)
    ax.yaxis.set_zorder(7)
    ax.grid(visible=True)

    plot_utils.timed_display()


def network_test(lines):
    network = gdf_utils.hyriv_gdf_to_network(lines, plot=True)
    gdf_utils.check_hyriv_network(network)
    plot_utils.timed_display()


def network_assign_test():
    bbox=BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    lines = load_data.load_hydro_rivers(bbox=bbox)
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
    lines = load_data.load_hydro_rivers(bbox=bbox)
    plot_utils.line_browser(lines, bbox)


def run_tests():
    bbox = BBox(min_x=-80, max_x=-75, min_y=45, max_y=50)
    period = Period("2000-01-12", "2004-10-10")

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
    lines = load_data.load_hydro_rivers(bbox=bbox)

    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    point_plot_test(hydat, bbox)
    point_plot_test(pwqmn, bbox)

    hydat_query_test(hydat, bbox, period)
    pwqmn_query_test(pwqmn, bbox, period)

    snap_test(hydat, lines, bbox)
    snap_test(pwqmn, lines, bbox)

    network_test(lines)
    network_assign_test()


def plot_array_test():
    bbox = BBox(min_x=-80, max_x=-79, min_y=45, max_y=46)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)

    lines = load_data.load_hydro_rivers(bbox=bbox)
    hydat = gdf_utils.point_gdf_from_df(hydat)
    pwqmn = gdf_utils.point_gdf_from_df(pwqmn)

    lines = gdf_utils.assign_stations(lines, hydat, 'STATION_NUMBER', prefix='hydat_')
    lines = gdf_utils.assign_stations(lines, pwqmn, 'Location_ID', prefix='pwqmn_')

    network = gdf_utils.hyriv_gdf_to_network(lines)

    edge_df = gdf_utils.dfs_search(network)

    plot_utils.plot_match_array(edge_df, add_to_plot=[plot_utils.add_map_to_plot])


def main():
    timer = Timer()

    network_assign_test()

    timer.stop()


if __name__ == "__main__":
    main()

import sys
from classes import BBox, Timer
import load_data
import gdf_lib


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

    assert load_data.check_period("2022-10-11") == TypeError
    assert load_data.check_period(["2022-10-11"]) == TypeError


def point_plot_test(points, bbox):
    ax = gdf_lib.add_map_to_plot(
        total_bounds=bbox.to_ccrs(gdf_lib.lambert)
    )
    gdf_lib.plot_gdf(points, ax=ax)
    gdf_lib.show()


def snap_test(points, edges, bbox):
    ax = gdf_lib.add_map_to_plot(
        total_bounds=bbox.to_ccrs(gdf_lib.lambert)
    )
    gdf_lib.plot_closest(points, edges, ax=ax)
    gdf_lib.show()


def network_test(lines):
    network = gdf_lib.hyriv_gdf_to_network(lines, plot=True)
    gdf_lib.check_hyriv_network(network)
    gdf_lib.show()


def network_assign_test(lines, stations, field):
    gdf_lib.assign_stations(lines, stations, field)
    gdf_lib.browser(lines)


def run_tests():
    bbox = BBox(min_x=-75, max_x=-70, min_y=45, max_y=50)

    hydat = load_data.get_hydat_station_data(bbox=bbox)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox)
    lines = gdf_lib.load_hydro_rivers(bbox=bbox)

    hydat = gdf_lib.point_gdf_from_df(hydat)
    pwqmn = gdf_lib.point_gdf_from_df(pwqmn)

    point_plot_test(hydat, bbox)
    point_plot_test(pwqmn, bbox)

    snap_test(hydat, lines, bbox)
    snap_test(pwqmn, lines, bbox)

    network_test(lines)
    network_assign_test(lines, pwqmn, 'Location ID')
    network_assign_test(lines, hydat, 'STATION_NUMBER')


def main():
    timer = Timer()

    run_tests()

    timer.stop()


if __name__ == "__main__":
    main()

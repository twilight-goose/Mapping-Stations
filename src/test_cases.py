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


def main():
    timer = Timer()

    # data = load_data.load_all(period=[None, "2010-01-12"], bbox=BBox(-80, -75, 40, 43))
    # gdfs = gdf_lib.plot_all(data)

    # gdf_lib.map_gdfs(gdfs)

    # data = load_data.get_pwqmn_station_info(period=["2008-01-10", "2010-01-12"], bbox=BBox(-80, -75, 40, 43))
    # gdf = gdf_lib.gdf_from_pwqmn(data)
    # gdf_lib.map_gdfs(gdf)

    #data = load_data.load_all(period=["2008-12-01", "2010-12-12"], bbox=BBox(-80, -75, 40, 43))
    #gdfs = {}

    # for name in data.keys():
    #     print(name)
    #     gdf = gdf_lib.point_gdf_from_df(data[name])
    #     if type(gdf) is not int:
    #         gdfs[name] = gdf
    #         gdf_lib.plot_gdf(list(gdfs.values())[0])

    bbox = BBox(min_lon=-80, max_lon=-79, min_lat=44, max_lat=45)

    hydat = load_data.get_hydat_station_data(bbox=bbox, sample=10)
    pwqmn = load_data.get_pwqmn_station_data(bbox=bbox, sample=10)

    hydat = gdf_lib.point_gdf_from_df(hydat)
    pwqmn = gdf_lib.point_gdf_from_df(pwqmn)
    #
    # gdf_lib.plot_gdf(pwqmn)
    #
    # gdf_lib.plot_closest(hydat, pwqmn)

    lines = gdf_lib.load_hydro_rivers(bbox=bbox)
    gdf_lib.plot_closest(hydat, lines)

    network = gdf_lib.hyriv_gdf_to_network(lines)
    gdf_lib.check_hyriv_network(network)

    gdf_lib.plot_closest(pwqmn, hydat)

    # gdf_lib.plot_gdf(connectors, show=False, color='red', marker="*")
    # gdf_lib.plot_gdf(lines, show=False, add_bg=False, color='blue', zorder=6)
    # gdf_lib.plot_gdf(hydat, add_bg=False, color='orange', zorder=9)

    timer.stop()


if __name__ == "__main__":
    main()

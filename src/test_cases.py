import sys
from timer import Timer
from classes import BBox
import load_data
import display_df


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
    # gdfs = display_df.plot_all(data)

    # display_df.map_gdfs(gdfs)

    # data = load_data.get_pwqmn_station_info(period=["2008-01-10", "2010-01-12"], bbox=BBox(-80, -75, 40, 43))
    # gdf = display_df.gdf_from_pwqmn(data)
    # display_df.map_gdfs(gdf)

    #data = load_data.load_all(period=["2008-12-01", "2010-12-12"], bbox=BBox(-80, -75, 40, 43))
    #gdfs = {}

    # for name in data.keys():
    #     print(name)
    #     gdf = display_df.point_gdf_from_df(data[name])
    #     if type(gdf) is not int:
    #         gdfs[name] = gdf
    #         display_df.plot_gdf(list(gdfs.values())[0])

    hydat = load_data.get_hydat_station_data(period=["2000-12-01", "2010-12-12"], bbox=BBox(-80, -75, 40, 43))
    pwqmn = load_data.get_pwqmn_station_data(period=["2000-12-01", "2010-12-12"], bbox=BBox(-80, -75, 40, 43))

    print(hydat)
    print(pwqmn)

    hydat = display_df.point_gdf_from_df(hydat['hydat'])
    pwqmn = display_df.point_gdf_from_df(pwqmn['pwqmn'])

    display_df.plot_gdf(hydat)
    display_df.plot_gdf(pwqmn)

    display_df.plot_closest(hydat, pwqmn)

    timer.stop()


if __name__ == "__main__":
    main()

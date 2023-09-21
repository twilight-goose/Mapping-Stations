import sys
from timer import Timer
from bbox import BBox
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

    data = load_data.load_all(period=[None, "2010-01-12"], bbox=BBox(-80, -75, 40, 43))
    gdfs = []

    for key in data.keys():
        try:
            gdf = display_df.point_gdf_from_df(data[key])
            if not(type(gdf) is int):
                gdfs.append(gdf)
        except TypeError:
            pass

    display_df.map_gdfs(gdfs)

    timer.stop()


if __name__ == "__main__":
    main()

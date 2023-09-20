import sys
from timer import Timer
from bbox import BBox
import load_data
import display_df


def main():
    timer = Timer()

    # data = load_data.load_all(period=[None, "2010-01-12"], bbox=BBox(-80, -75, 40, 43))
    # Loader.get_pwqmn_station_info(bbox=Loader.BBox(-81, -78, 43, 44),
    #                               period=["2001-01-20", "2003-01-20"])

    data = load_data.get_monday_files()
    for key in data.keys():
        display_df.plot_df(data[key], save=True, name=key)
    timer.stop()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()


import sys
import Loader
import matplotlib.pyplot as plt


def map_all(data):
    point_data = {}

    for key in data.keys():
        result = Loader.point_gdf_from_df(data[key])
        if type(result) != int:
            point_data[key] = result

    Loader.map_gdfs(point_data)


def main():
    timer = Loader.Timer()

    data = Loader.load_all(period=[None, "2010-01-12"], bbox=Loader.BBox(-80, -75, 40, 43))
    # Loader.get_pwqmn_station_info(bbox=Loader.BBox(-81, -78, 43, 44),
    #                               period=["2001-01-20", "2003-01-20"])

    timer.stop()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()

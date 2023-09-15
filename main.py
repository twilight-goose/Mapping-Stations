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


def create_bbox(*bbox_param):
    bbox = {}
    if bbox_param:
        min_lat, max_lat, min_lon, max_lon = bbox_param
        bbox = {'min_lat': min_lat, 'max_lat': max_lat,
                'min_lon': min_lon, 'max_lon': max_lon}
    return bbox


def main():
    timer = Loader.Timer()
    data = Loader.get_monday_files()
    for key in data.keys():
        Loader.plot_df(data[key])

    # Loader.get_pwqmn_station_info(bbox=create_bbox(43, 44, -81, -78))

    timer.stop()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()

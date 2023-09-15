import sys
import Loader


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
    Loader.get_monday_files(map_result=True)
    # Loader.get_pwqmn_station_info(create_bbox(), map_result=True)

    timer.stop()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()

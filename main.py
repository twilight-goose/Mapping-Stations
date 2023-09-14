import sys
import Loader


def get_sqlite_table_list(connection):
    pass


def main():
    timer = Loader.Timer()

    monday_files = Loader.get_monday_files()
    basin_gdf = Loader.point_gdf_from_df(monday_files["basins.csv"], map_result=True)

    return

    data = Loader.load_default()
    for key in data.keys():
        Loader.display(data[key])

    timer.stop()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()

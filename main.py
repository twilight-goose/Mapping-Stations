import sys
import Loader


def get_sqlite_table_list(connection):
    pass


def map_all(data):
    point_data = {}

    for key in data.keys():
        result = Loader.point_gdf_from_df(data[key])
        if type(result) != int:
            point_data[key] = result

    Loader.map_all(point_data)


def main():
    timer = Loader.Timer()

    data = Loader.load_all()
    # map_all(data)

    run = True
    while run:
        print("What dataset would you like to act on? (EXIT to exit)")
        print("\n".join(data.keys()))

        dataset = input()

        if dataset not in data.keys():
            print("Invalid dataset name")
        elif dataset.upper() == "PWQMN":
            pwqmn = True
            while pwqmn:
                print(data["pwqmn"].dtypes)
                user_in = input("Type SQL Query (BACK to back):")
                pwqmn = user_in.upper() != "BACK"
                try:
                    print(Loader.query_df(data["pwqmn"], user_in))
                except ValueError or SyntaxError:
                    print("Invalid query")

        elif dataset == "EXIT":
            run = False

    timer.stop()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()

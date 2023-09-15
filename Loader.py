import os
import random
from datetime import datetime
import pandas as pd
import geopandas as gpd
import webbrowser
import sqlite3


class Timer:
    def __init__(self):
        self.s_time = datetime.now()

    def start(self):
        self.s_time = datetime.now()

    def stop(self):
        d = datetime.now() - self.s_time
        print("That took {0} seconds and {1} microseconds\n".format(d.seconds, d.microseconds))


hydat_path = os.path.join(os.path.dirname(__file__), "Hydat.sqlite3\\Hydat.sqlite3")
pwqmn_PATH = os.path.join(os.path.dirname(__file__),
                          "PWQMN_cleaned\\Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
mondayPath = os.path.join(os.path.dirname(__file__), "MondayFileGallery")
hydat_join_f = "STATION_NUMBER"
timer = Timer()


def get_monday_files():
    timer.start()

    print("Loading Monday File Gallery to Memory...")

    data_dict = {}
    for file in filter(lambda x: x.endswith(".csv"), os.listdir(mondayPath)):
        print("> loading '{0}'".format(file))
        data_dict[file] = pd.read_csv(os.path.join(mondayPath, file))

    timer.stop()
    return data_dict


def get_hydat_station_data(query=None):
    timer.start()

    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)
    station_data = pd.read_sql_query("SELECT * FROM 'STATIONS' WHERE PROV_TERR_STATE_LOC == 'ON'", conn)

    station_data[hydat_join_f] = station_data[hydat_join_f].astype('|S')

    n = 0

    print("Joining station number identified data from other tables")
    for tbl_name in table_list['tbl_name'][1:]:
        table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name, conn)
        if hydat_join_f in table_data.columns.values:
            table_data[hydat_join_f] = table_data[hydat_join_f].astype('|S')
            station_data = station_data.join(table_data, on=[hydat_join_f], lsuffix=str(n))
            n += 1

    timer.stop()
    conn.close()
    return {"hydat": station_data}


def get_all_pwqmn_data(query: str) -> pd.DataFrame:
    """
    This function retrieves dated water information of a subset of
    stations based on 'query'
    :return:
    """
    timer.start()
    print("Loading PWQMN station data")

    df = pd.read_csv(pwqmn_PATH,
                     usecols=['MonitoringLocationName', 'ActivityStartDate', 'SampleCollectionEquipmentName',
                              'CharacteristicName', 'ResultSampleFraction', 'ResultValue', 'ResultUnit',
                              'ResultValueType', 'ResultDetectionCondition',
                              'ResultDetectionQuantitationLimitMeasure',
                              'ResultDetectionQuantitationLimitUnit'],
                     dtype={'ResultSampleFraction': str,
                            'ResultValue': float,
                            'ResultUnit': str,
                            'ResultDetectionCondition': str,
                            'ResultDetectionQuantitationLimitMeasure': str,
                            'ResultDetectionQuantitationLimitUnit': str})
    df.query(query, inplace=True)

    timer.stop()
    return df


def in_bbox(bbox: dict, cord: dict) -> bool:
    return (not bbox or
            (bbox['min_lat'] <= cord['lat'] <= bbox['max_lat'] and
             bbox['min_lon'] <= cord['lon'] <= bbox['max_lon']))


def get_pwqmn_station_info(period={}, bbox={}, vars=(), map_result=False):
    """
    This function reads from the cleaned PWQMN data using pd, and
    returns the following information about the set of stations
    that satisfy requirements passed in kwargs (or all if nothing is
    passed):
        - Name
        - ID
        - Longitude
        - Latitude
        - Start Date
        - Available variables
    :return:
    """
    timer.start()
    print("Loading PWQMN station info")

    # make it accept kwargs as parameters
    # loads everything, then sends back a dataframe of just stations that pass the critera

    df = pd.read_csv(pwqmn_PATH, usecols=['MonitoringLocationName',
                                          'MonitoringLocationID',
                                          'MonitoringLocationLatitude',
                                          'MonitoringLocationLongitude',
                                          'ActivityStartDate',
                                          'CharacteristicName'],
                     parse_dates=['ActivityStartDate'])

    grouped = df.groupby(by=['MonitoringLocationName',
                             'MonitoringLocationID',
                             'MonitoringLocationLatitude',
                             'MonitoringLocationLongitude'])

    station_data = []

    # iterate through sequences of (group name, subset object (df)]
    for name, subset_df in grouped:
        observation_dates = pd.to_datetime(subset_df['ActivityStartDate'])
        variables = subset_df['CharacteristicName']

        if in_bbox(bbox, name[2:4]) and (not vars or any([x in variables for x in vars])):
            station_data.append(name + (observation_dates.min(), variables))

    station_data = pd.DataFrame(station_data,
                                columns=['Name', 'ID', 'Latitude',
                                         'Longitude', 'Start Date', 'Variables'])

    timer.stop()

    if map_result:
        point_gdf_from_df(station_data, map_result=True)

    return {"pwqmn": station_data}


def load_all() -> [pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads a set of data at predetermined locations as pandas
    DataFrames

    Calls 3 functions that load the default files
    from predetermined locations
    """
    return {**get_monday_files(),
            **get_hydat_station_data(),
            **get_pwqmn_station_info()}


def find_xy_fields(df: pd.DataFrame, x: str, y: str) -> [str, str]:
    """Given a dataframe, returns the names of the X and y field,
     if found
     """
    fields = df.columns.values

    for field in fields:
        if df[field].dtype == float:
            if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
                if x == "":
                    x = field
                else:
                    x = "Failed"
            elif field.upper() in ["LAT", "LATITUDE", "Y"]:
                if y == "":
                    y = field
                else:
                    y = "Failed"

    return x, y


def point_gdf_from_df(name_df_pair: dict or pd.DataFrame, x_field="", y_field="",
                      map_result=False):
    """Given a pandas Dataframe or a {str: DataFrame} pair, tries
    to generate a GeometryArray
    """
    timer.start()

    if type(name_df_pair) == dict:
        name, df = list(name_df_pair.items())[0]
    else:
        name, df = "DataFrame", name_df_pair

    print("Converting %s to point data" % name)

    x, y = find_xy_fields(df, x_field, y_field)
    gdf = -1

    if x == "Failed" or y == "Failed" or x == "" or y == "":
        print("X/Y field not found. Operation Failed")
    else:
        try:
            gdf = gpd.GeoDataFrame(
                df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs=4326)
            print("X/Y fields found. Dataframe converted to geopandas point array")

            if map_result:
                m = gdf.explore()
                outfp = os.path.join(os.path.dirname(__file__), "map.html")
                m.save(outfp)
                webbrowser.open(outfp)
        except KeyError:
            print("X/Y field not found. Operation Failed")

    timer.stop()
    return gdf


def map_dfs(df_to_map):
    if type(df_to_map) == dict:
        df_to_map = list(df_to_map.values())
    elif not hasattr(df_to_map, '__iter))'):
        df_to_map = [df_to_map, ]

    def explore_recursive(gdfs, n):
        if n == len(gdfs) - 1:
            return gdfs[n].explore()
        else:
            return gdfs[n].explore(m=explore_recursive(gdfs, n + 1),
                                   color=hex(random.randrange(0, 2**24)))

    m = explore_recursive(df_to_map, 0)
    outpath = os.path.join(os.path.dirname(__file__), "map.html")
    m.save(outpath)
    webbrowser.open(outpath)


def query_df(df, query):
    return df.query(query)

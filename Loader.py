import os
import random
from datetime import datetime
import webbrowser
import sqlite3
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
#import geodatasets


# ============================================================================= ##
# Timer Class ================================================================= ##
# ============================================================================= ##


class Timer:
    def __init__(self):
        self.s_time = datetime.now()

    def start(self):
        self.s_time = datetime.now()

    def stop(self):
        d = datetime.now() - self.s_time
        print("That took {0} seconds and {1} microseconds\n".format(d.seconds, d.microseconds))


# ============================================================================= ##
# File Paths & Constant timer ================================================= ##
# ============================================================================= ##


hydat_path = os.path.join(os.path.dirname(__file__), "Hydat.sqlite3\\Hydat.sqlite3")
pwqmn_path = os.path.join(os.path.dirname(__file__),
                          "PWQMN_cleaned\\Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
monday_path = os.path.join(os.path.dirname(__file__), "MondayFileGallery")
hydat_join_f = "STATION_NUMBER"
timer = Timer()


# ============================================================================= ##
# Functions =================================================================== ##
# ============================================================================= ##


def in_bbox(bbox: dict, cord: dict) -> bool:
    """
    Evaluates if a coordinate falls within a bounding box

    :param bbox: the bounding box
    :param cord: the (x, y) coordinate to check
    :return: True if cord is within or on bbox; False otherwise
    """
    return (not bbox or
            (bbox['min_lat'] <= cord['lat'] <= bbox['max_lat'] and
             bbox['min_lon'] <= cord['lon'] <= bbox['max_lon']))


def _map_result(map_result, gdf, popup, color, tooltip):
    if map_result:
        m = gdf.explore(popup=popup, color=color, tooltip=tooltip)
        outfp = os.path.join(os.path.dirname(__file__), "map.html")
        m.save(outfp)
        webbrowser.open(outfp)


def load_csvs(path):
    """
    Loads all .csv files in the provided folder directory as pandas
    DataFrames

    :param path: path to folder directory to iterate over
    :return: {<str filename>: <pandas DataFrame>,...}
    """
    timer.start()

    data_dict = {}
    for file in filter(lambda x: x.endswith(".csv"), os.listdir(path)):
        print("> loading '{0}'".format(file))
        data_dict[file] = pd.read_csv(os.path.join(path, file))

    timer.stop()

    return data_dict


def get_monday_files():
    """
    Wrapper function that calls load_csvs to load .csv files
    downloaded from the Monday.com file gallery

    :return: {<str filename>: <pandas DataFrame>}
    """
    return load_csvs(monday_path)


def get_hydat_station_data(period=None, bbox=None):
    """

    :param period:
    :param bbox:
    :return:
    """
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
    :param query:
    :return:
    """
    timer.start()
    print("Loading PWQMN station data")

    df = pd.read_csv(pwqmn_path,
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


def get_pwqmn_station_info(period=None, bbox=None, var=()):
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
        - Available Data

    :param period:
    :param bbox:
    :param var:

    :return: {"pwqmn": <pandas DataFrame>}
    """
    timer.start()
    print("Loading PWQMN station info")

    # make it accept kwargs as parameters
    # loads everything, then sends back a dataframe of just stations that pass the critera

    df = pd.read_csv(pwqmn_path, usecols=['MonitoringLocationName',
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

        if in_bbox(bbox, {'lat': name[2], 'lon': name[3]}) and \
                (not var or any([x in variables for x in var])):
            station_data.append(name + (observation_dates.min(), variables))

    station_data = pd.DataFrame(station_data,
                                columns=['Name', 'ID', 'Latitude',
                                         'Longitude', 'Start Date', 'Variables'])

    timer.stop()

    return {"pwqmn": station_data}


def load_all() -> {str: pd.DataFrame}:
    """
    Loads all data as pandas DataFrames

    :return: dict of <dataset name> : pandas DataFrame
    """
    return {**get_monday_files(),
            **get_hydat_station_data(),
            **get_pwqmn_station_info()}


def find_xy_fields(df: pd.DataFrame) -> [str, str]:
    """
    Searches a pandas DataFrame for fields to use as longitudinal
    and latitudinal values

    :param df: the pandas DataFrame to search
    :return: [<X field name> or "Failed", <Y field name> or "Failed"]
    """
    def _(i, field) -> str:
        return field if i == "" else "Failed"

    x, y = "", ""
    for field in df.columns.values:
        if df[field].dtype == float:
            if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
                x = _(x, field)
            elif field.upper() in ["LAT", "LATITUDE", "Y"]:
                y = _(y, field)

    return x, y


def point_gdf_from_df(df: pd.DataFrame, x_field="", y_field="") -> gpd.GeoDataFrame:
    """
    Convert a pandas DataFrame to a geopandas GeoDataFrame with point
    geometry, if possible

    :param df: pandas DataFrame
    :param x_field: field to use as longitude
    :param y_field: field to use as latitude
    :return gdf: the converted gdf, or -1 if the conversion failed
    """
    timer.start()

    if not x_field and not y_field:
        x, y = find_xy_fields(df)
    else:
        x, y = x_field, y_field

    gdf = -1

    if x == "Failed" or y == "Failed" or x == "" or y == "":
        print("X/Y field not found. Operation Failed")
    else:
        try:
            gdf = gpd.GeoDataFrame(
                df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs=4326)

            print("X/Y fields found. Dataframe converted to geopandas point array")
        except KeyError:
            print("X/Y field not found. Operation Failed")

    timer.stop()
    return gdf


def check_gdfs_iter(gdfs):
    if type(gdfs) == dict:
        gdfs = list(gdfs.values())
    elif not hasattr(gdfs, '__iter__'):
        gdfs = [gdfs, ]
    return gdfs


def map_gdfs(gdfs_to_map):
    """

    :param gdfs_to_map:
    :return:
    """
    color_list = ['red', 'blue', 'yellow', 'purple', 'black']

    def explore_recursive(gdf_list, n):
        m = None
        if n < len(gdf_list) - 1:
            m = explore_recursive(gdf_list, n + 1)
        return gdf_list[n].explore(m=m, color=color_list[random.randint(0, 5)],
                                   marker_kwds={'radius': 4})

    gdfs_to_map = check_gdfs_iter(gdfs_to_map)
    m = explore_recursive(gdfs_to_map, 0)
    outpath = os.path.join(os.path.dirname(__file__), "map.html")
    m.save(outpath)
    webbrowser.open(outpath)


def plot_gdf(gdf: gpd.GeoDataFrame, **kwargs):
    """
    Plot a geopandas GeoDataFrame on a matplotlib plot

    :param gdf: the geopandas GeoDataFrame to be plotted
    :param kwargs:
    :return:
    """
    gdf.plot()
    plt.show()


def plot_df(df: pd.DataFrame):
    """
    Plot a pandas DataFrame as point data, if possible

    :param df: Pandas DataFrame to be plotted
    :return:
    """
    plot_gdf(point_gdf_from_df(df))


def query_df(df, query):
    return df.query(query)

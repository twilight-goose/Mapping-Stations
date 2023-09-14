import os
from datetime import datetime
import pandas as pd
import geopandas as gpd
import sqlite3


class Timer:
    def __init__(self):
        self.s_time = None

    def start(self):
        self.s_time = datetime.now()

    def stop(self):
        d = datetime.now() - self.s_time
        print("That took {0} seconds and {1} microseconds".format(d.seconds, d.microseconds))


hydat_path = os.path.join(os.path.dirname(__file__), "Hydat.sqlite3\\Hydat.sqlite3")
pwqmn_PATH = os.path.join(os.path.dirname(__file__),
                          "PWQMN_cleaned\\Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
mondayPath = os.path.join(os.path.dirname(__file__), "MondayFileGallery")
hydat_join_f = "STATION_NUMBER"
timer = Timer()


def get_hydat_station_data():
    timer.start()

    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)
    station_data = pd.read_sql_query("SELECT * FROM 'STATIONS' WHERE PROV_TERR_STATE_LOC == 'ON'", conn)

    station_data[hydat_join_f] = station_data[hydat_join_f].astype('|S')

    for tbl_name in table_list['tbl_name'][1:]:
        table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name, conn)
        if hydat_join_f in table_data.columns.values:
            table_data[hydat_join_f] = table_data[hydat_join_f].astype('|S')
            station_data = station_data.join(table_data, on=[hydat_join_f], lsuffix="_L")

    conn.close()
    return {"hydat": station_data}


def get_monday_files():
    timer.start()

    print("Loading Monday File Gallery to Memory...")

    data_dict = {}
    for file in filter(lambda x: x.endswith(".csv"), os.listdir(mondayPath)):
        print("> loading '{0}'".format(file))
        data_dict[file] = pd.read_csv(os.path.join(mondayPath, file))

    timer.stop()
    return data_dict


def get_station_data(query: str) -> pd.DataFrame:
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


def get_pwqmn_stations():
    """
    This function reads from the cleaned PWQMN data into RAM using pd, and returns the following information about
    each station: Name, ID, Longitude, Latitude, and Start Date
    :return:
    """
    timer.start()
    print("Loading PWQMN station info")

    df = pd.read_csv(pwqmn_PATH, usecols=['MonitoringLocationName',
                                                 'MonitoringLocationID',
                                                 'MonitoringLocationLatitude',
                                                 'MonitoringLocationLongitude',
                                                 'ActivityStartDate'])
    grouped = df.groupby(by=['MonitoringLocationName',
                             'MonitoringLocationID',
                             'MonitoringLocationLatitude',
                             'MonitoringLocationLongitude'],)

    station_data = []

    # iterate through sequences of (group name, subsetted object (df)]
    for name, subset_df in grouped:
        time_range = pd.to_datetime(subset_df['ActivityStartDate'])
        station_data.append(name + (time_range.min(),))

    # "One-liner" alternative to the lines above
    # station_data =\
    #     [name + (pd.to_datetime(subset_df['ActivityStartDate']).min())
    #      for name, subset_df in grouped]

    station_data = pd.DataFrame(station_data, columns=['Name', 'ID', 'Longitude',
                                                       'Latitude', 'Start Date',
                                                       'NumRecords', 'Indices'])
    station_data.set_index('Name')
    station_data.style.hide(['Indices'], axis=1)

    timer.stop()
    return {"pwqmn_stations": station_data}


def load_default() -> [pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads a set of data at predetermined locations as pandas
    DataFrames

    Calls 3 functions that load the default files
    from predetermined locations
    """
    return {**get_monday_files(),
            **get_hydat_station_data(),
            **get_pwqmn_stations()}


def find_xy_fields(df: pd.DataFrame, x: str, y: str) -> [str, str]:
    """Given a dataframe, returns the names of the X and y field,
     if found
     """
    fields = df.columns.values
    x, y = "", ""
    for field in fields:
        if any(sub in field.upper() for sub in ["LON", "LONG", "LONGITUDE", "X"]):
            if x == "":
                x = field
            else:
                x = "Failed"
        elif any(sub in field.upper() for sub in ["LAT", "LATITUDE", "Y"]):
            if y == "":
                y = field
            else:
                y = "Failed"

    return x, y


def point_from_df(name_df_pair: dict or pd.DataFrame, x_field="", y_field=""):
    """Given a pandas Dataframe or a {str: DataFrame} pair, tries
    to generate a GeometryArray
    """
    timer.start()

    if type(name_df_pair) == dict:
        name, df = list(name_df_pair.items())[0]
    else:
        name, df = "DataFrame", name_df_pair

    print("Converting %s to point data" % name)

    x, y = find_xy_fields(df, x=x_field, y=y_field)
    point_array = -1

    if x == "Failed" or y == "Failed" or x == "" or y == "":
        print("X/Y field not found. Operation Failed")
    else:
        try:
            point_array = gpd.points_from_xy(df[x], df[y])
            print("X/Y fields found. Dataframe converted to geopandas point array")
        except KeyError:
            print("X/Y field not found. Operation Failed")

    timer.stop()
    return point_array

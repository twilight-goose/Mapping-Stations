import os
import random
from datetime import datetime
import webbrowser
import sqlite3
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
# import geodatasets


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


class BBox:
    def __init__(self, min_lon=None, max_lon=None, min_lat=None, max_lat=None, *bounds):
        if len(bounds) == 4:
            min_lat, max_lat, min_lon, max_lon = bounds
        self.bounds = {'min_lon': min_lon, 'max_lon': max_lon,
                       'min_lat': min_lat, 'max_lat': max_lat}

    def __contains__(self, cord):
        return self.bounds['min_lat'] <= cord['lat'] <= self.bounds['max_lat'] and \
               self.bounds['min_lon'] <= cord['lon'] <= self.bounds['max_lon']


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


def in_bbox(bbox: BBox or None, cord: dict) -> bool:
    """
    Evaluates if a coordinate falls within a bounding box

    :param bbox: the bounding box
    :param cord: the (x, y) coordinate to check
    :return: True if cord is within or on bbox; False otherwise
    """
    return not bbox or cord in bbox


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
    print("Loading monday.com file gallery")
    return load_csvs(monday_path)


def get_hydat_station_data(period=None, bbox=None):
    """

    :param period:
    :param bbox:
    :return: {"hydat": <pandas DataFrame>}
    """
    def in_bbox_hydat(row):
        return in_bbox(bbox, {'lon': row['LONGITUDE'], 'lat': row['LATITUDE']})

    timer.start()

    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)
    station_data = pd.read_sql_query("SELECT * FROM 'STATIONS' WHERE PROV_TERR_STATE_LOC == 'ON'", conn)

    station_data = station_data[station_data.apply(in_bbox_hydat, axis=1)]
    station_data[hydat_join_f] = station_data[hydat_join_f].astype('|S')

    n = 0

    print("Joining station number identified data from other tables")
    for tbl_name in table_list['tbl_name'][1:]:
        table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name, conn)
        if hydat_join_f in table_data.columns.values:
            table_data[hydat_join_f] = table_data[hydat_join_f].astype('|S')

            # join the data from this table to the station table
            # mark duplicate fields using '_' so they can be removed
            station_data = station_data.join(table_data, on=[hydat_join_f], lsuffix=str(n)+"_")
            n += 1

    # change the name of the first station number column to retain it
    station_data.rename(columns={"STATION_NUMBER0_": hydat_join_f}, inplace=True)

    # create a list of fields makred as duplicates and remove them
    to_remove = list(station_data.columns[station_data.columns.str.startswith("STATION_NUMBER")])
    station_data.drop(columns=to_remove, inplace=True)

    timer.stop()
    conn.close()        # close the sqlite3 connection

    # return the data
    return {"hydat": station_data}


def get_pwqmn_station_info(period=None, bbox=None, var=()):
    """
    Reads from the cleaned PWQMN data using pandas
        - Name
        - ID
        - Longitude
        - Latitude
        - Available Data

    :param period: Time period of interest
    :param bbox: <BBox> representing area of interest
    :param var: Variables of interest

    :return: {"pwqmn": list of ((<Name>, <Location ID>, <Longitude>, <Latitude>, <Variables>),
                                <pandas DataFrame>)}
    """
    def filter_pwqmn(row):
        """
        Filters a row of PWQMN data

        :param row:
        :return: True if the record satisfies 3 conditions, False otherwise
        Conditions:
            1. Contains one of the variables of interest
            2. Is within the desired bounding box
            3. Is within the desired period
        """
        return (in_bbox(bbox, {'lat': row['Latitude'], 'lon': row['Longitude']})) and \
               (not period or
                   (not period[0] or period[0] <= row['Date']) and
                   (not period[1] or period[1] >= row['Date'])) and \
               (not var or row['Variable'] in var)

    timer.start()
    print("Loading PWQMN station info")

    # Load PWQMN data as a DataFrame
    df = pd.read_csv(pwqmn_path, usecols=['MonitoringLocationName',
                                          'MonitoringLocationID',
                                          'MonitoringLocationLongitude',
                                          'MonitoringLocationLatitude',
                                          'ActivityStartDate',
                                          'CharacteristicName',
                                          'SampleCollectionEquipmentName',
                                          'ResultSampleFraction',
                                          'ResultValue',
                                          'ResultUnit',
                                          'ResultValueType',
                                          'ResultDetectionCondition',
                                          'ResultDetectionQuantitationLimitMeasure',
                                          'ResultDetectionQuantitationLimitUnit'],
                     dtype={'ResultSampleFraction': str,
                            'ResultValue': float,
                            'ResultUnit': str,
                            'ResultDetectionCondition': str,
                            'ResultDetectionQuantitationLimitMeasure': str,
                            'ResultDetectionQuantitationLimitUnit': str})

    # Rename DataFrame columns for ease of manipulation
    df.rename(columns={'MonitoringLocationName': 'Name',
                       'MonitoringLocationID': "Location ID",
                       'MonitoringLocationLongitude': 'Longitude',
                       'MonitoringLocationLatitude': 'Latitude',
                       'ActivityStartDate': 'Date',
                       'CharacteristicName': 'Variable'}, inplace=True)

    # Filter the DataFrame based on the contents of each row
    df = df.loc[df.apply(filter_pwqmn, axis=1)]

    # Group the data based on common location
    group_list = df.groupby(by=['Name', 'Location ID', 'Longitude', 'Latitude']).__iter__()

    # Usually takes around 80 seconds
    timer.stop()

    return {"pwqmn": group_list}


def load_all() -> {str: pd.DataFrame}:
    """
    Loads all data as pandas DataFrames

    :return: dict of <dataset name> : pandas DataFrame
    """
    return {**get_monday_files(),
            **get_hydat_station_data(),
            **get_pwqmn_station_info()}


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

    gdf = -1        # default output value, indicates if an error occurred

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

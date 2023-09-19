import os
import random
from datetime import datetime
import webbrowser
import sqlite3
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx


# ============================================================================= ##
# Timer Class ================================================================= ##
# ============================================================================= ##


class Timer:
    """
    Just for timing operations during development
    """
    def __init__(self):
        self.s_time = datetime.now()

    def start(self):
        self.s_time = datetime.now()

    def stop(self):
        d = datetime.now() - self.s_time
        print("That took {0} seconds and {1} microseconds\n".format(d.seconds, d.microseconds))


class BBox:
    """
    Class that represents a longitude/latitude bound

    Mainly here to provide a framework for bounding box objects and
    provide a means of adding additional functionality when desired
    such as in sql_query
    """
    def __init__(self, min_lon=None, max_lon=None, min_lat=None, max_lat=None, *bounds):
        """
        Flexible method for instantiating BoundingBox objects. Sets
        of valid argument sets:
        1. None; Creates an empty BBox Object
        2. 4 keyword arguments in any order;
        3. 4 arbitrary positional arguments in the following order:
            min_lon, max_lon, min_lat, max_lat
        """
        if len(bounds) == 4:
            min_lon, max_lon, min_lat, max_lat = bounds
        self.bounds = {'min_lon': min_lon, 'max_lon': max_lon,
                       'min_lat': min_lat, 'max_lat': max_lat}

    def contains_point(self, cord: dict) -> bool:
        """
        :param cord: {'lon': <float>, 'lat': <float>}
                     Longitude/Latitude coordinate of the point.
        :return: True if cord lies within or on the BBox; False otherwise
        """
        return self.bounds['min_lat'] <= cord['lat'] <= self.bounds['max_lat'] and \
               self.bounds['min_lon'] <= cord['lon'] <= self.bounds['max_lon']

    def sql_query(self):
        """
        Translates the bounding box's bounds into an SQL query
        :return:
        """
        # For calls from functions where no boundary is declared
        if self is None:
            return ""
        else:
            min_lon, max_lon = self.bounds['min_lon'], self.bounds['max_lon']
            min_lat, max_lat = self.bounds['min_lat'], self.bounds['max_lat']

            return (f" WHERE {min_lon} <= 'LONGITUDE' AND {max_lon} >= 'LONGITUDE' AND " +
                    f"{min_lat} <= 'LATITUDE' AND {max_lat} >= 'LATITUDE'")


# ============================================================================= ##
# File Paths & Constant timer ================================================= ##
# ============================================================================= ##


file_base_path = os.path.dirname(__file__)
hydat_path = os.path.join(file_base_path, "Hydat.sqlite3\\Hydat.sqlite3")
pwqmn_path = os.path.join(file_base_path,
                          "PWQMN_cleaned\\Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
monday_path = os.path.join(file_base_path, "MondayFileGallery")
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
    return not bbox or bbox.contains_point(cord)


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


def __map_result(map_result, gdf, popup, color, tooltip):
    """

    :param map_result:
    :param gdf:
    :param popup:
    :param color:
    :param tooltip:
    :return:
    """
    if map_result:
        m = gdf.explore(popup=popup, color=color, tooltip=tooltip)
        outfp = os.path.join(os.path.dirname(__file__), "map.html")
        m.save(outfp)
        webbrowser.open(outfp)


def load_csvs(path):
    """
    Loads all .csv files in the provided folder directory as pandas
    DataFrames.

    :param path: path to folder directory to iterate over
    :return: {<str filename>: <pandas DataFrame>,  ...}
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

    :return: {<str filename>: <pandas DataFrame>, ...}
    """
    print("Loading monday.com file gallery")
    return load_csvs(monday_path)


def get_hydat_station_data(period=None, bbox=None):
    """

    :param period:
    :param bbox:
    :return: {"hydat": station_dict} where
        station_dict is a dict of <str station number>: table_data> and
        table_data is a dict of <str table name>: <pandas DataFrame>
    """
    def get_period_sql_query(fields):
        fields = [field[0] for field in fields]
        query = " WHERE "

        if any(period):
            y = ""
            if "DATE" in fields:
                x = "DATE"
            elif "YEAR" in fields:
                x = "YEAR"
            else:
                x, y = "YEAR_FROM", "YEAR_TO"

            if all(period):
                query += f"('{x}' BETWEEN '{period[0]}' AND '{period[1]}')"
                if y:
                    query += f" OR ('{y}' BETWEEN '{period[0]}' AND '{period[1]}')"
            elif not period[0] and period[1]:
                query += f"('{x}' <= '{period[1]}')"
                if y:
                    query += f" OR ('{y}' <= '{period[1]}')"
            else:
                query += f"('{x}' >= '{period[0]}')"
                if y:
                    query += f" OR ('{y}' >= '{period[0]}')"
        else:
            return ""
        return query

    timer.start()

    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)
    station_list = pd.read_sql_query("SELECT * FROM 'STATIONS'" + BBox.sql_query(bbox), conn)
    station_dict = {}

    for i, row in station_list.iterrows():
        st_number = row.pop(hydat_join_f)
        station_dict[st_number] = {'Info': row}

    print("Joining station number identified data from other tables")

    # Iterate through every other table in the sqlite3 database
    for tbl_name in table_list['tbl_name'][1:]:

        curs = conn.execute('select * from %s' % tbl_name)
        date_query = get_period_sql_query(curs.description)

        # Read the contents of the table
        table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name + BBox.sql_query(bbox) + date_query, conn)

        # Check if the table contains data that can be linked to a station
        if hydat_join_f in table_data.columns.values:
            grouped = table_data.groupby(by=hydat_join_f)

            for st_num, group in grouped:
                group.pop(hydat_join_f)
                try:
                    station_dict[st_num][tbl_name] = group
                except KeyError:
                    station_dict[st_num] = {}
                    station_dict[st_num][tbl_name] = group

    timer.stop()
    conn.close()        # close the sqlite3 connection

    print(type(station_dict))
    print(type(station_dict[list(station_dict.keys())[10]]))
    print(type(station_dict[list(station_dict.keys())[10]][list(station_dict[list(station_dict.keys())[10]].keys())[0]]))

    # return the data
    return {"hydat": station_dict}


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
                df.astype(str), geometry=gpd.points_from_xy(df[x], df[y]), crs='epsg:3160')

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


def plot_gdf(gdf: gpd.GeoDataFrame, name="", save=False, **kwargs):
    """
    Plot a geopandas GeoDataFrame on a matplotlib plot

    :param gdf: the geopandas GeoDataFrame to be plotted
    :param name:
    :param save:
    :param kwargs:
    :return: True if the mapping was successful, False otherwise
    """
    if type(gdf) is gpd.GeoDataFrame:
        gdf.plot()
        if save:
            plt.savefig(os.path.join(file_base_path, name + "_plot.png"))
            print(f"Plot successfully saved to {name}_plot.png\n")
        plt.show()
    else:
        print(name, "could not be plotted")


def plot_df(df: pd.DataFrame, save=False, name="", **kwargs):
    """
    Plot a pandas DataFrame as point data, if possible

    :param df: Pandas DataFrame to be plotted
    :param save:
    :param name:
    :return:
    """
    if type(df) != pd.DataFrame:
        raise TypeError("Parameter passed as 'df' is not a DataFrame'")

    plot_gdf(point_gdf_from_df(df), save=save, name=name, **kwargs)


def query_df(df, query):
    return df.query(query)

import os.path
import sqlite3
import pandas as pd
import check_files
from classes import BBox, Period
from timer import Timer


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##


# Copyright (c) 2023 James Wang - jcw4698(at)gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# ========================================================================= ##
# Data File Paths ========================================================= ##
# ========================================================================= ##


# Set up path strings to streamline reading from paths
cwd = os.path.dirname(__file__)
proj_path = os.path.dirname(cwd)
data_path = os.path.join(proj_path, "data")


# Paths to obtain data from
hydat_path = os.path.join(data_path, "Hydat", "Hydat.sqlite3")
pwqmn_path = os.path.join(data_path, "PWQMN_cleaned", "Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
pwqmn_sql_path = os.path.join(data_path, "PWQMN_cleaned", "PWQMN.sqlite3")
monday_path = os.path.join(data_path, "MondayFileGallery")


# Before loading anything, check if the data paths exist
check_files.check_paths(proj_path, data_path, hydat_path, pwqmn_path, monday_path)


# check for need to convert pwqmn data to sqlite3 format
try:
    # have to do this check again to see if the data needs to be converted
    check_files.check_path(pwqmn_sql_path)
except FileNotFoundError:
    # If pwqmn has not yet been converted to sqlite3 format, convert it
    """
    Converts the PWQMN .csv data to sqlite3 format to improve read
    and query speeds. Is only run if the pwqmn.sqlite3 is not detected.
    """
    print("converting PWQMN data to sql format")

    connection = sqlite3.connect(pwqmn_sql_path)
    pwqmn_data = pd.read_csv(pwqmn_path,
                             usecols=['MonitoringLocationName',
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

    pwqmn_data.rename(columns={'MonitoringLocationName': 'Name',
                               'MonitoringLocationID': "Location ID",
                               'MonitoringLocationLongitude': 'Longitude',
                               'MonitoringLocationLatitude': 'Latitude',
                               'CharacteristicName': 'Variables'}, inplace=True)

    pwqmn_data.to_sql("DATA", connection, index=False)

    connection.close()


hydat_join_f = "STATION_NUMBER"
timer = Timer()


# ========================================================================= ##
# Functions =============================================================== ##
# ========================================================================= ##


def find_xy_fields(df: pd.DataFrame) -> [str, str]:
    """
    Searches a pandas DataFrame for specific field names to use as
    longitudinal and latitudinal values.

    If more than 1 match is found for X or Y, "Failed" will be
    returned. If no match is found for X or Y, an empty string
    will be returned. Not case-sensitive.

    :param df: the pandas DataFrame to search

    :return: [<X field name> or "Failed", <Y field name> or "Failed"]
    """
    def _(i, field_name) -> str:
        return field_name if i == "" else "Failed"

    x, y = "", ""

    for field in df.columns.values:

        # Check if the field matches one of the X or Y field names
        if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
            x = _(x, field)
        elif field.upper() in ["LAT", "LATITUDE", "Y"]:
            y = _(y, field)

    return x, y


def load_csvs(path: str, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all .csv files in the provided folder directory as pandas
    DataFrames.

    :param path: path of folder directory to iterate over
    :param bbox: BBox object declaring area of interest or None

    :return: dict of length n where n is the number of .csv files in path
                {<str filename>: <pandas DataFrame>,  ...}
    """
    timer.start()

    # create a dictionary to index .csv data based on filename
    data_dict = {}

    # iterate over each file in path with the ".csv" extension
    for file in filter(lambda x: x.endswith(".csv"), os.listdir(path)):
        print("> loading '{0}'".format(file))

        # read the entirety of the .csv and add it to the dictionary
        # not recommended for use with large .csv files (>500 mb) as
        # loading times can become long
        df = pd.read_csv(os.path.join(path, file))

        # check if a filtering by bbox is necessary
        if bbox is not None:
            # filter the data by location if lat/lon fields can be found
            lon, lat = find_xy_fields(df)

            if lat and lon and lat != "Failed" and lon != "Failed":
                data_dict[file] = df.loc[df.apply(BBox.filter_df, axis=1, args=(bbox, lon, lat))]
        else:
            data_dict[file] = df

    timer.stop()

    return data_dict


def get_monday_files(bbox=None) -> {str: pd.DataFrame}:
    """
    Wrapper function that calls load_csvs to load .csv files
    downloaded from the monday.com file gallery

    :return: dict of length n where n is the number of .csv files in
             the 'monday_path' directory.
                {<str filename>: <pandas DataFrame>, ...}
    """
    print("Loading monday.com file gallery")
    return load_csvs(monday_path, bbox=bbox)


def get_hydat_station_data(period=None, bbox=None, var=None) -> {str: pd.DataFrame}:
    """
    Retrieves HYDAT station data in the period and bbox of interest

    :param period: Tuple/list of length 2 or None

        Tuple/list of (<start date>, <end date>); dates can be either
        <str> in format "YYYY-MM-DD" or None; If None, all dates
        after(before) the start(end) date are retrieved.

            or

        None; No date query. Does not filter data by date.

    :param bbox: BBox object declaring area of interest or None
    :param var:

    :return: {"hydat": <pandas DataFrame>}
    """

    # check period validity
    Period.check_period(period)
    timer.start()

    # create a sqlite3 connection to the hydat data
    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    # generate a sql query from the bbox bounding box
    bbox_query = BBox.sql_query(bbox, "LONGITUDE", "LATITUDE")
    if bbox_query:
        bbox_query = " AND " + bbox_query

    # read station info from the STATIONS table within the database and
    # load that info into the station data dict
    station_df = pd.read_sql_query("SELECT STATION_NUMBER, STATION_NAME, HYD_STATUS, SED_STATUS, LATITUDE, LONGITUDE,"
                                   "DRAINAGE_AREA_GROSS, DRAINAGE_AREA_EFFECT FROM 'STATIONS' WHERE PROV_TERR_STATE_"
                                   "LOC == 'ON'" + bbox_query, conn)

    station_df['LONGITUDE'] = station_df['LONGITUDE'].astype('float')
    station_df['LATITUDE'] = station_df['LATITUDE'].astype('float')

    timer.stop()
    conn.close()        # close the sqlite3 connection

    # return the data
    return {"hydat": station_df}


def get_pwqmn_station_data(period=None, bbox=None, var=()) -> {str: list}:
    """
    Reads from the cleaned PWQMN data using pandas

    :param period: Time period of interest
    :param bbox: <BBox> representing area of interest
    :param var: Variables of interest

    :return: {"pwqmn": <pandas DataFrame>}
    """

    # Check that period is valid
    Period.check_period(period)
    timer.start()

    # create a sqlite3 connection to the pwqmn data
    print("Creating a connection to '{0}'".format(pwqmn_sql_path))
    conn = sqlite3.connect(pwqmn_sql_path)

    # generate a sql query from bbox and period
    curs = conn.execute('PRAGMA table_info(DATA)')
    fields = [field[1] for field in curs.fetchall()]

    period_query = Period.sql_query(period, fields)
    bbox_query = BBox.sql_query(bbox, "Longitude", "Latitude")

    query = ""

    if bbox_query or period_query:
        connector = "OR" if (bbox_query and period_query) else ""
        query = " ".join(["WHERE", bbox_query, connector, period_query])

    # Load PWQMN data as a DataFrame
    station_df = pd.read_sql_query("SELECT * FROM 'DATA'" + query, conn)

    station_df['Longitude'] = station_df['Longitude'].astype('float')
    station_df['Latitude'] = station_df['Latitude'].astype('float')

    # Usually takes around 80 seconds
    timer.stop()

    return {"pwqmn": station_df}


def load_all(period=None, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all data from the paths declared at the top of the file

    :return: dict of <str dataset name> : <pandas DataFrame>
    """
    return {**get_monday_files(),
            **get_hydat_station_data(period=period, bbox=bbox),
            **get_pwqmn_station_data(period=period, bbox=bbox)}

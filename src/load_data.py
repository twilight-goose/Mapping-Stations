import os.path
import sqlite3
import check_files
from util_classes import BBox, Period, Timer

from pandas import read_csv, read_sql_query
from geopandas import read_file


"""
Contains functions, constants, and objects relevant to the loading
and saving of files.
"""

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
# Utilities =============================================================== ##
# ========================================================================= ##


def find_xy_fields(df: pd.DataFrame) -> [str, str]:
    """
    Searches a pandas DataFrame for specific field names to use as
    longitudinal and latitudinal values.

    If more than 1 match is found for X or Y, "Failed" will be
    returned. If no match is found for X or Y, an empty string
    will be returned. Not case-sensitive.

    :param df: <Pandas DataFrame>
        The DataFrame to search

    :return: list(<str>, <str>)
        The result of the search for x and y fields, where each item
        in the list is either the field name or "Failed"
        i.e:
            [<X field name> or "Failed", <Y field name> or "Failed"]
    """

    # simple helper function
    def _(i, field_name) -> str:
        return field_name if i == "" else "Failed"

    # initiate x and y
    x, y = "", ""

    # Iterate through dataframe field names
    for field in df.columns.values:
        # Check if the field matches one of the X or Y field names
        if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
            x = _(x, field)
        elif field.upper() in ["LAT", "LATITUDE", "Y"]:
            y = _(y, field)

    return x, y

# ========================================================================= ##
# Generator =============================================================== ##
# ========================================================================= ##

def generate_pwqmn_sql():
    """
    Creates a sqlite3 database from PWQMN data.

    Creates a connection to the sql database (if it doesn't exist it
    is created), reads a specified set of columns from the PWQMN data,
    then writes it to the sql database as the 'DATA' table. If a 'DATA'
    table exists already, that table is overwritten by the new data.

    :return: None
    """
    print("Generating PWQMN sqlite3 database")
    connection = sqlite3.connect(pwqmn_sql_path)

    # read fields of interest, and set data types for mixed type fields
    pwqmn_data = read_csv(pwqmn_path,
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
                             dtype={'MonitoringLocationLongitude': float,
                                    'MonitoringLocationLatitude': float,
                                    'ResultSampleFraction': str,
                                    'ResultValue': float,
                                    'ResultUnit': str,
                                    'ResultDetectionCondition': str,
                                    'ResultDetectionQuantitationLimitMeasure': str,
                                    'ResultDetectionQuantitationLimitUnit': str})

    # rename some columns to make working with the PWQMN data easier
    pwqmn_data.rename(columns={'MonitoringLocationName': 'Name',
                               'MonitoringLocationID': "Location_ID",
                               'MonitoringLocationLongitude': 'Longitude',
                               'MonitoringLocationLatitude': 'Latitude',
                               'ActivityStartDate': 'Date',
                               'CharacteristicName': 'Variables'}, inplace=True)

    # fill the sql database and close the connection
    pwqmn_data['Date'] = pd.to_datetime(pwqmn_data['Date'])
    pwqmn_data.to_sql("DATA", connection, index=False, if_exists='replace')
    connection.close()


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
hydroRIVERS_path = os.path.join(data_path, os.path.join("Hydro_RIVERS_v10", "HydroRIVERS_v10_na.shp"))


# Before loading anything, check that the data paths exist
check_files.check_paths(proj_path, data_path, hydat_path, pwqmn_path, monday_path,
                        hydroRIVERS_path)

# Check if "PWQMN.sqlite3" already exists. If it doesn't, generate a
# sqlite3 database from the pwqmn data, to accelerate future data
# loading and querying
try:
    check_files.check_path(pwqmn_sql_path)
except FileNotFoundError:
    generate_pwqmn_sql()

hydat_join_f = "STATION_NUMBER"
timer = Timer()


# ========================================================================= ##
# Loaders ================================================================= ##
# ========================================================================= ##


def load_csvs(path: str, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all .csv files in the provided folder directory as pandas
    DataFrames.

    :param path: string
        Path of directory to iterate over.

    :param bbox: BBox or None (default)
        BBox object defining area of interest. If None, doesn't
        filter by a bounding box.

    :return: dict of string: <Pandas DataFrame>
        A dictionary of length n, where n is the number of .csv files
        in the provided folder directory, built of string: DataFrame
        pairs.
        i.e
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
        df = read_csv(os.path.join(path, file))

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

    :return: dict(<str>: <Pandas DataFrame>, ...)
        Dictionary of length n where n is the number of .csv files in
        the 'monday_path' directory.
        i.e
            {<str filename>: <pandas DataFrame>, ...}
    """
    print("Loading monday.com file gallery")
    return load_csvs(monday_path, bbox=bbox)


def get_hydat_station_data(period=None, bbox=None, var=None, sample=False) -> pd.DataFrame:
    """
    Retrieves HYDAT station data in the period and bbox of interest

    :param period: Tuple/list of length 2 or None

        Tuple/list of (<start date>, <end date>); dates can be either
        <str> in format "YYYY-MM-DD" or None; If None, all dates
        after(before) the start(end) date are retrieved.

            or

        None; No date query. Does not filter data by date.

    :param bbox: BBox or None (default)
        BBox object defining area of interest. If None, doesn't
        filter by a bounding box.

    :param var:

    :param sample: <positive nonzero int> or None
        Number of (random) stations to read from HYDAT database. If
        None, do not sample and retrieve entire database.

    :return: <pandas DataFrame>
        Hydat station data.
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

    if sample > 0:
        bbox_query += f" ORDER BY RANDOM() LIMIT {sample}"

    # read station info from the STATIONS table within the database and
    # load that info into the station data dict
    station_df = read_sql_query("SELECT STATION_NUMBER, STATION_NAME, HYD_STATUS, SED_STATUS, LATITUDE, LONGITUDE,"
                                   "DRAINAGE_AREA_GROSS, DRAINAGE_AREA_EFFECT FROM 'STATIONS' WHERE PROV_TERR_STATE_"
                                   "LOC == 'ON'" + bbox_query, conn)

    station_df['LONGITUDE'] = station_df['LONGITUDE'].astype('float')
    station_df['LATITUDE'] = station_df['LATITUDE'].astype('float')

    station_df.rename(columns={'LONGITUDE': 'Longitude', 'LATITUDE': 'Latitude'},
                      inplace=True)

    period_query = Period.sql_query(period, ['YEAR_FROM', 'YEAR_TO'])

    timer.stop()
    conn.close()        # close the sqlite3 connection

    if station_df.empty:
        print("Chosen query resulted in empty GeoDataFrame.")

    # return the data
    return station_df


def get_pwqmn_station_data(period=None, bbox=None, var=(), sample=None) -> pd.DataFrame:
    """
    Loads the PWQMN data based on selected bbox, period, and variables
    of interest.

    :param period: Tuple/list of length 2 or None

        Tuple/list of (<start date>, <end date>); dates can be either
        <str> in format "YYYY-MM-DD" or None; If None, all dates
        after(before) the start(end) date are retrieved.

            or

        None; No date query. Does not filter data by date.

    :param bbox: BBox or None (default)
        BBox object defining area of interest. If None, doesn't
        filter by a bounding box.

    :param var:

    :param sample: <positive nonzero int> or None
        Number of (random) stations to read from PWQMN database. If
        None, do not sample and retrieve entire database.

    :return: <pandas DataFrame>
        PWQMN station data.
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

    # generate a database query from period and bbox
    period_query = Period.sql_query(period, fields)
    bbox_query = BBox.sql_query(bbox, "Longitude", "Latitude")

    query = ""

    if bbox_query or period_query:
        connector = "AND" if (bbox_query and period_query) else ""
        query = " ".join([" WHERE", bbox_query, connector, period_query])

    if sample is not None and sample > 0:
        query += f" ORDER BY RANDOM() LIMIT {sample}"

    # Load PWQMN data as a DataFrame
    station_df = read_sql_query("SELECT * FROM 'DATA'" + query, conn)

    # Usually takes around 80 seconds
    timer.stop()
    conn.close()

    if station_df.empty:
        print("Chosen query resulted in empty GeoDataFrame.")

    return station_df


def load_shp(path, sample=None, bbox=None):
    return read_file(path, rows=sample, bbox=BBox.to_tuple(bbox))


def load_hydro_rivers(sample=None, bbox=None):
    """
    Loads HydroRIVERS_v10.shp as a geopandas GeoDataFrame. The
    HydroRIVERS shapefile are provided in a geographic
    (latitude/longitude) projection referenced to datum WGS84.

    Note: As BBox grows larger, spatial distortion at the edge increases.
    Attempting to place geometry features outside the projection's
    supported bounds may result in undesirable behaviour. Refer
    to https://epsg.io/102002 (which describes features of projection
    defined by Can_LCC_wkt) for the projected and WGS84 bounds.

    :param sample: int or None (default)
        The number of river segments to load. If None, load all.

    :param bbox: BBox or None (default)
        BBox object defining area of interest. If None, doesn't
        filter by a bounding box.

    :return: Geopandas GeoDataFrame
        HydroRIVERS data as a LineString GeoDataFrame.
    """
    return load_shp(hydroRIVERS_path, sample, bbox)


def load_all(period=None, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all data from the paths declared at the top of the file

    :return: dict(<str>: <Pandas DataFrame>, ...)
        Dictionary of length n + 2, where n is the number of files in
        the 'monday_path' directory.
        i.e
            {<str dataset name> : <pandas DataFrame>, ...}
    """
    return {**get_monday_files(),
            'hydat': get_hydat_station_data(period=period, bbox=bbox),
            'pwqmn': get_pwqmn_station_data(period=period, bbox=bbox),
            'hydroRIVERS': load_hydro_rivers(bbox=bbox)}

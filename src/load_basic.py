import os.path
import sqlite3
import pandas as pd
import check_files
from bbox import BBox
from timer import Timer


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
monday_path = os.path.join(data_path, "MondayFileGallery")


# Before loading anything, check if the data paths exist
check_files.check_paths(proj_path, data_path, hydat_path, pwqmn_path, monday_path)


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

        # First check that the field is a valid type
        if df[field].dtype == float:

            # Check if the field matches one of the X or Y field names
            if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
                x = _(x, field)
            elif field.upper() in ["LAT", "LATITUDE", "Y"]:
                y = _(y, field)

    return x, y


def check_period(period):
    """
    Checks that period is in a valid period format. Raises an error
    if it's in an invalid format, with a message describing the issue.

    :param period: the period to be checked

    :raises TypeError:

            if period is not valid. period is valid if it is either:

                Tuple/list of (<start date>, <end date>); dates can be
                either <str> in format "YYYY-MM-DD" or None

                or

                None
    """
    if period is not None:
        if len(period) != 2:
            raise TypeError("Period expected 2 values, found", len(period))
        elif type(period) is not list and type(period) is not tuple:
            raise TypeError("Period of wrong type,", type(period), "found")


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
    def get_period_sql_query(fields) -> str:
        """
        Given a list of fields, generates an SQL query based on period
        and identified date fields. Searches for "DATE", "YEAR_FROM",
        and "YEAR_TO".

        :param fields:

        :return: <str>

            If period (from outer scope) does not have any date bounds
            returns "" (a blank string) to indicate a date query is not
            necessary.

            If period (from outer scope) has date bounds, returns a SQL
            query string.
        """
        query, start_f, end_f = "", "", ""

        # check if a period was passed with at least one date bound
        if period is not None and any(period):

            # Check fields for 1 of 3 potential date fields
            if "DATE" in fields:
                start_f = "DATE"
            elif "YEAR" in fields:
                start_f = "YEAR"
            else:
                start_f, end_f = "YEAR_FROM", "YEAR_TO"

            # Construct the SQL query, based on the period bounds and
            # identified date fields

            # period has start_date and end_date
            if all(period):
                query += f"('{start_f}' BETWEEN '{period[0]}' AND '{period[1]}')"
                if end_f:
                    query += f" OR ('{end_f}' BETWEEN '{period[0]}' AND '{period[1]}')"

            # period has an end_date but no start_date
            elif not period[0] and period[1]:
                query += f"('{start_f}' <= '{period[1]}')"
                if end_f:
                    query += f" OR ('{end_f}' <= '{period[1]}')"

            # period has start_date but no end_date
            else:
                query += f"('{start_f}' >= '{period[0]}')"
                if end_f:
                    query += f" OR ('{end_f}' >= '{period[0]}')"

        return query

    # check period validity
    check_period(period)
    timer.start()

    # create a sqlite3 connection to the hydat data
    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    # generate a sql query from the bbox bounding box
    bbox_query = BBox.sql_query(bbox)
    if bbox_query:
        bbox_query = " AND " + bbox_query

    # read station info from the STATIONS table within the database and
    # load that info into the station data dict
    station_df = pd.read_sql_query("SELECT STATION_NUMBER, STATION_NAME, HYD_STATUS, SED_STATUS, LATITUDE, LONGITUDE,"
                                   "DRAINAGE_AREA_GROSS, DRAINAGE_AREA_EFFECT FROM 'STATIONS' WHERE PROV_TERR_STATE_"
                                   "LOC == 'ON'" + bbox_query, conn)

    timer.stop()
    conn.close()        # close the sqlite3 connection

    # return the data
    return {"hydat": station_df}


def get_pwqmn_station_info(period=None, bbox=None, var=()) -> {str: list}:
    """
    Reads from the cleaned PWQMN data using pandas

    :param period: Time period of interest
    :param bbox: <BBox> representing area of interest
    :param var: Variables of interest

    :return: {"pwqmn": <pandas DataFrame>}
    """
    def filter_pwqmn(row):
        """
        Filters a row of PWQMN data

        :param row: the row of data to be filtered

        :return: True if the record satisfies 3 conditions, False otherwise

            Conditions:
                1. Contains one of the variables of interest
                2. Is within the desired bounding box
                3. Is within the desired period
        """
        return (BBox.contains_point(bbox, {'lat': row['Latitude'], 'lon': row['Longitude']})) and \
               (not var or row['Variable'] in var)

    # Check that period is valid
    check_period(period)
    timer.start()

    print("Loading PWQMN station info")

    # Load PWQMN data as a DataFrame
    df = pd.read_csv(pwqmn_path, usecols=['MonitoringLocationName',
                                          'MonitoringLocationID',
                                          'MonitoringLocationLongitude',
                                          'MonitoringLocationLatitude',
                                          'CharacteristicName'])

    # Rename DataFrame columns for ease of manipulation
    df.rename(columns={'MonitoringLocationName': 'Name',
                       'MonitoringLocationID': "Location ID",
                       'MonitoringLocationLongitude': 'Longitude',
                       'MonitoringLocationLatitude': 'Latitude',
                       'CharacteristicName': 'Variables'}, inplace=True)

    grouped = df.groupby(by=['Name', 'Location ID', 'Longitude', 'Latitude'])

    station_data = []

    for name, subset_df in grouped:  # iterate through sequences of (group name, subsetted object (df)]

        variables = subset_df['Variables']
        cord = {'lon': name[2], 'lat': name[3]}

        if BBox.contains_point(bbox, cord) and (not var or any([x in variables for x in var])):
            station_data.append(name + (variables,))

    station_data = pd.DataFrame(station_data, columns=['Name', 'ID', 'Longitude', 'Latitude', 'Variables'])

    # Usually takes around 80 seconds
    timer.stop()

    return {"pwqmn": station_data}


def load_all(period=None, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all data from the paths declared at the top of the file

    :return: dict of <str dataset name> : <pandas DataFrame>
    """
    return {**get_monday_files(),
            **get_hydat_station_data(),
            **get_pwqmn_station_info()}

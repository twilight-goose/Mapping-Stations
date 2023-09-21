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


cwd = os.path.dirname(__file__)
proj_path = os.path.dirname(cwd)
data_path = os.path.join(proj_path, "data")


hydat_path = os.path.join(data_path, "Hydat", "Hydat.sqlite3")
pwqmn_path = os.path.join(data_path, "PWQMN_cleaned", "Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
monday_path = os.path.join(data_path, "MondayFileGallery")


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
    will be returned.

    :param df: the pandas DataFrame to search

    :return: [<X field name> or "Failed", <Y field name> or "Failed"]
    """
    def _(i, _field) -> str:  # when I removed this the function stopped working, so it stays
        return _field if i == "" else "Failed"

    x, y = "", ""
    for field in df.columns.values:
        if df[field].dtype == float:
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

    :raises TypeError: if period is not valid. period is valid if it
                       is either:

        Tuple/list of (<start date>, <end date>); dates can be either
        <str> in format "YYYY-MM-DD" or None

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
    :param bbox:

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

        # filter the data by location if lat/lon fields can be found
        lon, lat = find_xy_fields(df)

        if lat and lon and lat != "Failed" and lon != "Failed":

            data_dict[file] = df.loc[df.apply(BBox.filter_df, axis=1, args=(bbox, lon, lat))]

    timer.stop()

    return data_dict


def get_monday_files(bbox=None) -> {str: pd.DataFrame}:
    """
    Wrapper function that calls load_csvs to load .csv files
    downloaded from the Monday.com file gallery

    :return: dict of length n where n is the number of .csv files in
             the 'monday_path' directory.
                {<str filename>: <pandas DataFrame>, ...}
    """
    print("Loading monday.com file gallery")
    return load_csvs(monday_path, bbox=bbox)


def get_hydat_station_data(period=None, bbox=None, var=None) -> {str: {str: {str: pd.DataFrame}}}:
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

    :return: {"hydat": station_dict} where

        station_dict = {<str station number>: table_data>, ...}

            station_dict is a dict of length n where n is the number of
            unique station numbers in the HYDAT sqlite3 database.

        table_data = {<str table name>: <pandas DataFrame>, ...}

            table_data is a dict of length n where n is the number of
            tables that the station number appears in
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
        bbox_query = " WHERE " + bbox_query

    # initialize a dictionary to store station data in
    station_dict = {}

    # read table info from sqlite_master
    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)

    # read station info from the STATIONS table within the database and
    # load that info into the station data dict
    station_list = pd.read_sql_query("SELECT * FROM 'STATIONS'" + bbox_query, conn)

    for i, row in station_list.iterrows():
        st_number = row.pop(hydat_join_f)
        station_dict[st_number] = {'Info': row}

    print("Joining station number identified data from other tables")

    # Iterate through every table in the database (other than STATIONS)
    for tbl_name in table_list['tbl_name'][1:]:

        # Read only the field names of the table
        curs = conn.execute('PRAGMA table_info(%s)' % tbl_name)
        fields = [field[1] for field in curs.fetchall()]

        # If the table contains a 'STATION_NUMBER' field, there is
        # data that can be added to station_dict.
        if hydat_join_f in fields:
            # the period sql query
            date_query = get_period_sql_query(fields)

            # combine the bounding box and date queries.
            if bbox_query:
                query = bbox_query + " AND " + date_query
            elif date_query:
                query = " WHERE " + date_query
            else:
                query = ""

            # Read from the table the rows that satisfy the query
            table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name + query, conn)

            # Group the rows by STATION_NUMBER
            grouped = table_data.groupby(by=hydat_join_f)

            # Add the table_data to the dict within station_dict with
            # the corresponding 'STATION_NUMBER' key
            for st_num, group in grouped:

                # remove 'STATION_NUMBER' from the table_data to
                # prevent duplicate fields
                group.pop(hydat_join_f)

                # not all station numbers are in 'STATIONS', so check
                # if station_dict has the st_num key
                try:
                    # if the key exists, just need to add the data
                    station_dict[st_num][tbl_name] = group
                except KeyError:
                    # station_dict does not have the st_num as a key,
                    # add it as a new dict before adding the table data
                    station_dict[st_num] = {}
                    station_dict[st_num][tbl_name] = group

                return

    timer.stop()
    conn.close()        # close the sqlite3 connection

    # return the data
    return {"hydat": station_dict}


def get_pwqmn_station_info(period=None, bbox=None, var=()) -> {str: list}:
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

    :return: {"pwqmn": list of (station_info, station_data) pairs} where

                station_info is a tuple length 6 of strings in the
                following order:
                    (<Name>, <Location ID>, <Longitude>, <Latitude>, <Variables>)

                station_data is a <pandas DataFrame> of valid data entries
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
               (not period or
                   (not period[0] or period[0] <= row['Date']) and
                   (not period[1] or period[1] >= row['Date'])) and \
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

    # Group the data based on common location name, id, and lon/lat
    group_list = df.groupby(by=['Name', 'Location ID', 'Longitude', 'Latitude']).__iter__()

    # Usually takes around 80 seconds
    timer.stop()

    return {"pwqmn": group_list}


def load_all(period=None, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all data from the paths declared at the top of the file

    :return: dict of <str dataset name> : data where

        data = <pandas DataFrame> or <dict>

            where <dict> is of the form described by
            get_pwqmn_station_info().

            for DataFrame/dict structure details, refer to
            individual function outputs.
    """
    return {**get_monday_files(),
            **get_hydat_station_data(period, bbox),
            **get_pwqmn_station_info(period, bbox)}






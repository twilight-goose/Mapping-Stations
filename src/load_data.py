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


def load_csvs(path: str) -> {str: pd.DataFrame}:
    """
    Loads all .csv files in the provided folder directory as pandas
    DataFrames.

    :param path: path to folder directory to iterate over

    :return: dict of length n where n is the number of .csv files in path
                {<str filename>: <pandas DataFrame>,  ...}
    """
    timer.start()

    data_dict = {}
    for file in filter(lambda x: x.endswith(".csv"), os.listdir(path)):
        print("> loading '{0}'".format(file))
        data_dict[file] = pd.read_csv(os.path.join(path, file))

    timer.stop()

    return data_dict


def get_monday_files() -> {str: pd.DataFrame}:
    """
    Wrapper function that calls load_csvs to load .csv files
    downloaded from the Monday.com file gallery

    :return: dict of length n where n is the number of .csv files in
             the 'monday_path' directory
            {<str filename>: <pandas DataFrame>, ...}
    """
    print("Loading monday.com file gallery")
    return load_csvs(monday_path)


def get_hydat_station_data(period=None, bbox=None, var=None) -> {str: {str: {str: pd.DataFrame}}}:
    """
    Retrieves HYDAT station data in the period and bbox of interest

    :param period: Tuple of length 2 containing (<start date>, <end date>)
                   Dates can be either <str> in format "YYYY-MM-DD" or
                   None; If None, all dates after/before the start/end
                   date is retrieved
    :param bbox: BBox object declaring area of interest or None
    :param var:

    :return: {"hydat": station_dict} where

        station_dict = {<str station number>: table_data>, ...}

            station_dict is a dict of length n where n is the number of
            unique station numbers in the HYDAT sqlite3 database.

        table_data = {<str table name>: <pandas DataFrame> pairs, ...}

            table_data is a dict of length n where n is the number of
            tables that the station number appears in
    """
    def get_period_sql_query(fields) -> str:
        """
        I don't want to understand this code, so commenting it is a future problem
        :param fields:
        :return:
        """
        fields = [field[0] for field in fields]
        query = ""
        if period is not None and any(period):
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
        return query

    if period is not None and len(period) == 1:
        raise TypeError("Period expected 2 values, found", len(period))

    timer.start()

    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    bbox_query = BBox.sql_query(bbox)
    if bbox_query:
        bbox_query = " WHERE " + bbox_query

    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)
    station_list = pd.read_sql_query("SELECT * FROM 'STATIONS'" + bbox_query, conn)
    station_dict = {}

    for i, row in station_list.iterrows():
        st_number = row.pop(hydat_join_f)
        station_dict[st_number] = {'Info': row}

    print("Joining station number identified data from other tables")

    # Iterate through every other table in the sqlite3 database
    for tbl_name in table_list['tbl_name'][1:]:

        # Read the field names of the table and generate a sql query using it
        curs = conn.execute('select * from %s' % tbl_name)
        date_query = get_period_sql_query(curs.description)

        if bbox_query:
            query = bbox_query + " AND " + date_query
        elif date_query:
            query = " WHERE " + date_query
        else:
            query = ""

        # Read the contents of the table
        table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name + query, conn)

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

    #print(type(station_dict))
    #print(type(station_dict[list(station_dict.keys())[10]]))
    #print(type(station_dict[list(station_dict.keys())[10]][list(station_dict[list(station_dict.keys())[10]].keys())[0]]))

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

        :param row:
        :return: True if the record satisfies 3 conditions, False otherwise
        Conditions:
            1. Contains one of the variables of interest
            2. Is within the desired bounding box
            3. Is within the desired period
        :raises IndexError:
            Raises an IndexError if period has a length of 1
        """
        return (BBox.contains_point(bbox, {'lat': row['Latitude'], 'lon': row['Longitude']})) and \
               (not period or
                   (not period[0] or period[0] <= row['Date']) and
                   (not period[1] or period[1] >= row['Date'])) and \
               (not var or row['Variable'] in var)

    if period is not None and len(period) == 1:
        raise TypeError("Period needs a start and end date. Expected 2 values, only found 1")

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


def load_all(period=None, bbox=None) -> {str: pd.DataFrame}:
    """
    Loads all data as pandas DataFrames

    :return: dict of <dataset name> : pandas DataFrame
    """
    return {**get_monday_files(),
            **get_hydat_station_data(period, bbox),
            **get_pwqmn_station_info(period, bbox)}






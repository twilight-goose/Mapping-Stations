import os.path
import sqlite3
import check_files
from gen_util import find_xy_fields, BBox, Period, Timer

import pandas as pd
from geopandas import read_file
from datetime import datetime
from datetime import timedelta


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
# Generator =============================================================== ##
# ========================================================================= ##

def generate_pwqmn_sql():
    """
    Creates a sqlite3 database from PWQMN data.

    Creates a connection to the sql database (if it doesn't exist it
    is created), reads a specified set of columns from the PWQMN data,
    then writes it to the sql database as the 'DATA' table. If a 'DATA'
    table exists already, that table is overwritten by the new data.

    Renames certain fields to standardize the column names between PWQMN
    and HYDAT data.

    :return: None
    """
    print("Generating PWQMN sqlite3 database")
    connection = sqlite3.connect(pwqmn_sql_path)

    # read fields of interest, and set data types for mixed type fields
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
                             dtype={'MonitoringLocationLongitude': float,
                                    'MonitoringLocationLatitude': float,
                                    'ResultSampleFraction': str,
                                    'ResultValue': float,
                                    'ResultUnit': str,
                                    'ResultDetectionCondition': str,
                                    'ResultDetectionQuantitationLimitMeasure': str,
                                    'ResultDetectionQuantitationLimitUnit': str})

    # rename some columns to make working with the PWQMN data easier
    pwqmn_data.rename(columns={'MonitoringLocationName': 'Station_Name',
                               'MonitoringLocationID': "Station_ID",
                               'MonitoringLocationLongitude': 'Longitude',
                               'MonitoringLocationLatitude': 'Latitude',
                               'ActivityStartDate': 'Date',
                               'CharacteristicName': 'Variable'}, inplace=True)

    # Create table with all pwqmn data
    pwqmn_data['Date'] = pd.to_datetime(pwqmn_data['Date'])
    pwqmn_data.to_sql("ALL_DATA", connection, index=False, if_exists='replace')
    
    pwqmn_create_stations(pwqmn_df=pwqmn_data, conn=connection)
    pwqmn_create_data_range(pwqmn_df=pwqmn_data, conn=connection)
    
    connection.close()
    
    return pwqmn_data


def pwqmn_create_stations(pwqmn_df=None):
    """
    Adds a 'Stations' table in the PWQMN sqlite3 database containing
    only the name, id, and location of each unique station.
    
    :param pwqmn_df: DataFrame or None (default)
        If provided, data is extracted from the provided DataFrame.
        If None, loads necessary data from the PWQMN database file.
        
    :return: DataFrame
        The created SQL table as a DataFrame.
    
    :raises ValueError:
        If only one of pwqmn_df and conn are provided.
    """
    conn = sqlite3.connect(pwqmn_sql_path)
    
    if pwqmn_data is None:
        pwqmn_data = pd.read_sql_query(
            "SELECT Station_Name, Station_ID, Latitude, Longitude FROM 'ALL_DATA'", conn)
    else:
        pwqmn_data = pwqmn_data[['Station_Name', 'Station_ID', 'Longitude', 'Latitude']]
       
    # Create table with only station id, name, and location
    
    station_data = pwqmn_data.drop_duplicates(ignore_index=True)
    station_data.to_sql('Stations', connection, index=False, if_exists='replace')
    
    conn.close()
    return station_data


def pwqmn_create_data_range(pwqmn_df=None, sample=None):
    """
    Adds a 'Data_Range' table in the PWQMN sqlite3 database. The table
    stores periods where either Nitrogen or Phosphurus data is 
    available for each station using a start and end date.
    
    Fields: Station_ID, Variable, Start, End
    
    Date processing code writter by Juliane Mai, January 2023
    Modified by James Wang, November 2023
    
    :param pwqmn_df: DataFrame or GeoDataFrame or None (default)
        Loaded PWQMN data. Provide it if PWQMN data was previously
        loaded to save time reloading it.
    
    :param sample: positive non-zero int or None (default)
        For testing/debugging purposes only to drastically reduce
        runtime to allow for faster testing. Only provide a sample
        if pwqmn_df and conn were not provided
    
    :return: DataFrame
        The created SQL table as a DataFrame
    """
    def categorize(x):
        if x in ["Nitrite", "Inorganic nitrogen (nitrate and nitrite)",
                 "Total Nitrogen; mixed forms", "Kjeldahl nitrogen", "Nitrate"] or \
           x in ["Total Phosphorus; mixed forms", "Orthophosphate"]:
            return 'N_or_P'
        else:
            return 'Other'
    
    def add_to_output(st_id, var, start, end):
        out_data['Station_ID'].append(st_id)
        out_data['Variable'].append(var)
        out_data['Start'].append(start)
        out_data['End'].append(end)
                        
    conn = sqlite3.connect(pwqmn_sql_path)
    
    if pwqmn_df is None:
        query = "SELECT Station_ID, Variable, Date FROM 'ALL_DATA'"
        if sample is not None and sample > 0:
            query += f" ORDER BY RANDOM() LIMIT {sample}"
        pwqmn_data = pd.read_sql_query(query, conn)
    
    pwqmn_data['Date'] = pd.to_datetime(pwqmn_data['Date'])
    pwqmn_data['Date'] = pwqmn_data['Date'].dt.strftime("%Y-%m-%d")
    
    # print("\n".join(i for i in pwqmn_data['Variable'].unique()))
    
    pwqmn_data['Variable'] = pwqmn_data['Variable'].apply(categorize)
    
    grouped = pwqmn_data.groupby(by=['Station_ID', 'Variable'])
    out_data = {'Station_ID': [], 'Variable': [], 'Start': [], 'End': []}
    
    for key, sub_df in grouped:
        if key[1] != 'Other':
            start = None
            last = None
            
            sub_df = sub_df.sort_values(by='Date')
            
            for ind, row in sub_df.iterrows():
                date = row['Date']
                
                if start is None:
                    start = date
                else:
                    if datetime.strptime(date, "%Y-%m-%d") != \
                            datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1):
                        add_to_output(key[0], key[1], start, last)
                        start = date
                last = date
            
            add_to_output(key[0], key[1], start, last)
      
    out_data = pd.DataFrame(out_data)
    out_data.to_sql('Data_Range', conn, index=False, if_exists='replace')
    
    conn.close()
    return out_data


def get_pwqmn_station_data(period=None, bbox=None, var=(), sample=None) -> pd.DataFrame:
    """
    Loads the PWQMN data based on selected bbox, period, and variables
    of interest from the file at

    The PWQMN sqlite database must contain a 'ALL_DATA' table with the
    following fields:
    - Longitude
    - Latitude
    - Station_ID
    - Station_Name

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
    curs = conn.execute('PRAGMA table_info(ALL_DATA)')
    fields = [field[1] for field in curs.fetchall()]

    # generate a database query from period and bbox
    period_query = Period.sql_query(period, fields)
    bbox_query = BBox.sql_query(bbox, "Longitude", "Latitude")

    query = ''
    if bbox_query or period_query:
        connector = "AND" if (bbox_query and period_query) else ""
        query = " ".join([bbox_query, connector, period_query])
        if query.strip():
            query = ' WHERE ' + query

    if sample is not None and sample > 0:
        query += f" ORDER BY RANDOM() LIMIT {sample}"

    # Load PWQMN data as a DataFrame
    station_df = pd.read_sql_query("SELECT * FROM 'ALL_DATA'" + query, conn)

    timer.stop()
    conn.close()

    if station_df.empty:
        print("Chosen query resulted in empty GeoDataFrame.")

    return station_df


def get_pwqmn_data_range(subset=()):
    conn = sqlite3.connect(pwqmn_sql_path)

    query = "SELECT * FROM 'Data_Range'"
    
    if not hasattr(subset, '__iter__'):
        subset = (subset, )
    # Station ID query
    id_query = ', '.join([f'"{s_id}"' for s_id in subset])
    if id_query:
        query  += f" WHERE Station_ID in ({id_query})"
        
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ========================================================================= ##
# Data File Paths ========================================================= ##
# ========================================================================= ##


# Set up path strings to streamline reading from paths
cwd = os.path.dirname(__file__)
proj_path = os.path.dirname(cwd)
data_path = os.path.join(proj_path, "data")
shp_save_path = os.path.join(data_path, "shapefiles")


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

    :return: dict(<str>: <Pandas DataFrame>, ...)
        Dictionary of length n where n is the number of .csv files in
        the 'monday_path' directory.
        i.e
            {<str filename>: <pandas DataFrame>, ...}
    """
    print("Loading monday.com file gallery")
    return load_csvs(monday_path, bbox=bbox)


def get_hydat_data(tbl_name, *expr, period=None, subset=(), to_csv=False):
    """
    Retrieves HYDAT station data from the chosen table based on
    a period (if applicable) and subset of stations (if applicable).
    
    :param tbl_name: str
        Name of the database table to retrieve. HYDAT.sqlite3 must
        contain the passed table name.
    
    :param period: Tuple/list of length 2 or None (default)

        Tuple/list of (<start date>, <end date>); dates can be either
        <str> in format "YYYY-MM-DD" or None; If None, all dates
        after(before) the start(end) date are retrieved.

            or

        None; No date query. Does not filter data by date.

    :param subset: list-like or pandas Series (default=())
        Iterable containing the ids of the stations whose data
        to retrieve. If empty, retrieves data from all stations.
        This only applies to tables containing a 'STATION_NUMBER'
        field. If a subset value is provided for a table without
        a 'STATION_NUMBER' field, an error will occur.
    
    :param to_csv: bool (default=False)
        If True, saves the table <tbl_name>.csv. If False, does
        nothing.
    
    :param expr: list-like of str (optional)
        SQL query expressions in string form to add to the SQL query.
        No checks are performed on these expressions, so be careful.

    :return: Pandas DataFrame
        Hydat database table.
    
    :save: tbl_name.csv
        Saves the table data to <tbl_name>.csv in the hydat
        directory (if to_csv == True).
    """
    Period.check_period(period)
    timer.start()

    if type(subset) is pd.Series:
        subset = subset.tolist()
    elif type(subset) is str:
        subset = (subset,)

    # create a sqlite3 connection to the hydat data
    print("Creating a connection to '{0}'".format(hydat_path))
    conn = sqlite3.connect(hydat_path)

    curs = conn.execute(f'PRAGMA table_info({tbl_name})')
    fields = [field[1] for field in curs.fetchall()]

    query = []
    
    # Period query
    period_query = Period.sql_query(period, fields)
    if period_query:
        query.append(period_query)

    # Station ID query
    id_query = ', '.join([f'"{s_id}"' for s_id in subset])
    if id_query and 'STATION_NUMBER' in fields:
        query.append(f"STATION_NUMBER in ({id_query})")
    
    for exp in expr:
        query.append(f"({exp})")
    
    query = ' AND '.join(query)
    if query.strip():
        query = " WHERE " + query
    
    data = pd.read_sql_query(f'SELECT * FROM "{tbl_name}"' + query, conn)
    data = data.rename(columns={'STATION_NUMBER': 'Station_ID'})
    
    if to_csv:
        data.to_csv(os.path.join(data_path, 'Hydat', f"{tbl_name}.csv"))
    
    conn.close()
    return data


def get_hydat_flow(*exp, period=None, subset=()):
    return get_hydat_data(period=period, subset=subset, tbl_name='DLY_FLOWS',
                          *exp)
 

def get_hydat_remarks(*exp, period=None, subset=()):
    return get_hydat_data(period=period, subset=subset, tbl_name='STN_REMARKS',
                          *exp)
                          
                          
def get_hydat_data_range(*exp, period=None, subset=()):
    if period:
        start_expr = f"strftime('%Y-%m-%d', Start') >= strftime('%Y-%m-%d', '{period.start})"
        end_expr = f"strftime('%Y-%m-%d', End') <==strftime('%Y-%m-%d', '{period.end})"
        exp.append(start_expr)
        exp.append(end_expr)
    return get_hydat_data(*exp, subset=subset, tbl_name='Data_Range')


def get_hydat_station_data(period=None, bbox=None, sample=None,
                           flow_symbol=None) -> pd.DataFrame:
    """
    Retrieves HYDAT station data based on a bounding box and period.
    Renames certain data fields to standardize between PWQMN and
    HYDAT data.

    The HYDAT sqlite3 database must contain the following tables:
    - STATIONS
    - STN_DATA_RANGE

    STATIONS must contain the following fields:
    - STATION_NUMBER
    - STATION_NAME
    - LONGITUDE
    - LATITUDE
    - DRAINAGE_AREA_GROSS
    - DRAINAGE_AREA_EFFECT

    STN_DATA_RANGE must contain STATION_NUMBER and DATA_TYPE, and one
    of the following sets of fields (or another field name compatible with
    Period.sql_query()):
    - YEAR and MONTH
    - YEAR_FROM and YEAR_TO
    - DATE

    :param period: Tuple/list of length 2 or None

        Tuple/list of (<start date>, <end date>); dates can be either
        <str> in format "YYYY-MM-DD" or None; If None, all dates
        after(before) the start(end) date are retrieved.

            or

        None; No date query. Does not filter data by date.

    :param bbox: BBox or None (default)
        BBox object defining area of interest. If None, doesn't
        filter by a bounding box.

    :param sample: <positive nonzero int> or None
        Number of (random) stations to read from HYDAT database. If
        None, do not sample and retrieve entire database.

    :return: <pandas DataFrame>
        HYDAT stations within the bounds of BBox that have data in var
        during the period of interest, and available monthly streamflow
        data (one record per month of data available Ffrom each station,
        2 columns (flow value, flow symbol) per assumed 31 days of the
        month). Refer to hydat_reference.md DATA_SYMBOLS for
        FLOW_SYMBOL information.
    """
    # check period validity
    Period.check_period(period)
    timer.start()

    # create a sqlite3 connection to the hydat data
    print(f"Creating a connection to '{hydat_path}'")
    conn = sqlite3.connect(hydat_path)
            
    # generate a sql query from the bbox bounding box
    bbox_query = BBox.sql_query(bbox, "LONGITUDE", "LATITUDE")
    if bbox_query:
        bbox_query = ' WHERE ' + bbox_query
    
    # read station info from the STATIONS table within the database and
    # load that info into the station data dict
    station_df = pd.read_sql_query("SELECT STATION_NUMBER, STATION_NAME, LATITUDE, LONGITUDE, "
                                   "DRAINAGE_AREA_GROSS, DRAINAGE_AREA_EFFECT FROM 'STATIONS'" +
                                   bbox_query, conn)

    curs = conn.execute('PRAGMA table_info(STN_DATA_RANGE)')
    fields = [field[1] for field in curs.fetchall()]
    
    period_query = Period.sql_query(period, fields)
    if period_query:
        period_query = ' AND ' + period_query
        
    if not (sample is None):
        period_query += f" ORDER BY RANDOM() LIMIT {sample}"
    
    data_range = pd.read_sql_query("SELECT * FROM 'STN_DATA_RANGE' WHERE DATA_TYPE == 'Q'" +
                                   period_query, conn)
    station_df = station_df.merge(data_range, how='inner', on='STATION_NUMBER')
    if station_df.empty:
        print("Chosen query resulted in empty GeoDataFrame.")

    station_df.rename(columns={'LONGITUDE': 'Longitude', 'LATITUDE': 'Latitude',
                               'STATION_NUMBER': 'Station_ID', 'STATION_NAME': 'Station_Name'},
                      inplace=True)

    # close the sqlite3 connection
    conn.close()
    # return the data
    timer.stop()
    return station_df


def hydat_create_data_range():
    def add_to_output(st_id, start, end):
        out_data['Station_ID'].append(st_id)
        out_data['Start'].append(start)
        out_data['End'].append(end)
        
    dly_flows = get_hydat_flow()
    
    days_by_month = [
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    ]
    
    grouped = dly_flows.groupby('Station_ID')
    out_data = {'Station_ID': [], 'Start': [], 'End': []}
    
    for st_id, sub_df in grouped:
        
        start = None
        last = None
        
        sub_df = sub_df.sort_values(by=['YEAR', 'MONTH'])
        
        for ind, row in sub_df.iterrows():
            year = row['YEAR']
            month = row['MONTH']
            days_in_month = days_by_month[month - 1]
            
            if row['FULL_MONTH']:
                date = f"{year}-{month}-{1}"
                
                if start is None:
                    start = date
                    
                elif datetime.strptime(date, "%Y-%m-%d") != \
                        datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1):

                    add_to_output(st_id, start, last)
                    start = date
                    
                last = f"{year}-{month}-{days_in_month}"
            else:
                for i in range(days_in_month):
                    if row.iloc[11 + i * 2]:
                        date = f"{year}-{month}-{i + 1}"
                    
                        if start is None:
                            start = date
                            
                        elif datetime.strptime(date, "%Y-%m-%d") != \
                                datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1):
                            add_to_output(st_id, start, last)
                            start = date
                            
                        last = date
            
        add_to_output(st_id, start, last)
        
    out_data = pd.DataFrame(data=out_data)
    conn = sqlite3.connect(hydat_path)
    out_data.to_sql('Data_Range', conn, index=False, if_exists='replace')
    conn.close()
    return out_data
    

def load_rivers(path=hydroRIVERS_path, sample=None, bbox=None):
    """
    Loads HydroRIVERS_v10.shp as a geopandas GeoDataFrame. The
    HydroRIVERS shapefile are provided in a geographic
    (latitude/longitude) projection referenced to datum WGS84.

    Note: As BBox grows larger, spatial distortion at the edge increases.
    Attempting to place geometry features outside the projection's
    supported bounds may result in undesirable behaviour. Refer
    to https://epsg.io/102002 (which describes features of projection
    defined by Can_LCC_wkt) for the projected and WGS84 bounds.

    :param path: string
        The file path to load river dataset from.
        Default: hydroRIVERS_path.

    :param sample: int or None (default)
        The number of river segments to load. If None, load all.

    :param bbox: BBox or None (default)
        BBox object defining area of interest. If None, doesn't
        filter by a bounding box.

    :return: Geopandas GeoDataFrame
        HydroRIVERS data as a LineString GeoDataFrame.
    """
    return read_file(path, rows=sample, bbox=BBox.to_tuple(bbox))


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
            'hydroRIVERS': load_rivers(bbox=bbox)}

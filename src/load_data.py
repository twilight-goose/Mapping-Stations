import os.path
import sqlite3
import check_files
from gen_util import find_xy_fields, BBox, Period

import pandas as pd
from geopandas import read_file
from datetime import datetime
from datetime import timedelta
from datetime import date


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
datastream_path = os.path.join(data_path, "datastream")
hydroRIVERS_path = os.path.join(data_path, os.path.join("Hydro_RIVERS_v10", "HydroRIVERS_v10_na.shp"))


# Before loading anything, check that the data paths exist
check_files.check_paths(proj_path, data_path, hydat_path, pwqmn_path, monday_path,
                        hydroRIVERS_path)
                        
# ========================================================================= ##
# Constants =============================================================== ##
# ========================================================================= ##

interest_var = ["Total Nitrogen; mixed forms as N Filtered",
                "Nitrate as N Filtered",
                "Total Nitrogen; mixed forms as N Unfiltered",
                "Total Phosphorus; mixed forms",
                "Orthophosphate as P Filtered",
                "Total Phosphorus; mixed forms as P Unfiltered"]
                
interest_var_query = []
for i in interest_var:
    interest_var_query.append(f'"{i}"')
interest_var_query = ", ".join(interest_var_query)
interest_var_query = f' WHERE Variable ||  " " || MethodSpeciation || " " || ResultSampleFraction in ({interest_var_query})'

# ========================================================================= ##
# ID Query Builder ======================================================== ##
# ========================================================================= ##


def id_query_from_subset(subset, fields):
    """
    Creates a SQL expression that queries ID.
    
    :param subset: string or list-like/Series of string
        The ID to retrieve or a list, tuple, Series of IDs, or file
        path of a .csv file to load IDs from. If file path, IDs will be
        read from the 'Station_ID' field.
    
    :param fields: list-like of string
        List of fields available for the query. This can be a list
        created by reading from the sql table using:
        
        >>> curs = conn.execute('PRAGMA table_info(table_name)')
        >>> fields = [field[1] for field in curs.fetchall()]
        
        Or a user defined list containing all or only the necessary
        fields.
        i.e
        >>> fields = ['Station_ID', 'Station_Name']\
        
    :return: string
        The created sql query string.
    
    tests:
        subset = ["2A", "4N", "9K", "i8"]
        subset2 = [123, 234, 345, 456]
        subset3 = "sample_subset.csv"
        
        id_query = load_data.id_query_from_subset(subset, ['Station_ID'])
        id_query2 = load_data.id_query_from_subset(subset2, ['STATION_NUMBER'])
        id_query3 = load_data.id_query_from_subset("sample_subset.csv", ['Station_ID'])
        
        assert id_query == 'Station_ID in ("2A", "4N", "9K", "i8")'
        assert id_query2 == 'STATION_NUMBER in (123, 234, 345, 456)'
        assert id_query3 == 'Station_ID in (123, 234, "9K", "i8")'
    """
    if 'Station_ID' in fields:
        id_field = 'Station_ID'
    elif 'STATION_NUMBER' in fields:
        id_field = 'STATION_NUMBER'
    else:
        raise ValueError("No ID field found. To add a query for an id field"
                         "include it as a q_kwarg.")
    
    if type(subset) is str:
        if subset.endswith(".csv"):
            subset = pd.read_csv(subset)
            subset = subset['Station_ID'].to_list()
        else:
            subset = (subset, )
    
    id_list = []
    
    for st_id in subset:
        if type(st_id) is not str or st_id.isdigit():
            id_list.append(str(st_id))
        else:
            id_list.append(f'"{st_id}"')
            
    
    id_list_str = ', '.join(id_list)
    if id_list_str:
        return f'{id_field} in ({id_list_str})'
    return ""
    

def build_sql_query(fields, **q_kwargs):
    """
    Builds and returns a SQL query in the form of a string containing
    all valid provided query keyword arguments.
    
    :param fields: str or list-like of str or None (default)
        Fields of the sql table to read from. Used to build the
        period, bbox, and id subset expressions of the query.
        To read all field names of a table use:
        >>> curs = conn.execute('PRAGMA table_info(table_name)')
        >>> fields = [field[1] for field in curs.fetchall()]
        
    
    :param q_kwargs: additional keyword arguments
        Additional keyword arguments to apply to the query.
        Potential q_kwargs key + type:
        
        period: Tuple/list of length 2 or Period object
            Tuple/list of (<start date>, <end date>); dates can be 
            either <str> in format "YYYY-MM-DD" or None; If None, all 
            dates after(before) the start(end) date are retrieved.

        subset: string or list-like/Series of string
            The ID to retrieve or a list, tuple, Series of IDs, or file
            path of a .csv file to load IDs from. If file path, IDs
            will be read from the 'Station_ID' field.
             
        bbox: BBox object
            BBox object defining area of interest.
        
        sample: <positive nonzero int>
            Number of (random) stationsz to read from the table.
            
        other: value or list of values
            Where the keyword is the field name, and the passed
            value is either a single value or list of values
            with which the field will be queryed.
            
            examples:
            brand="Adidas" will add 'brand == "Adidas"' to the
                query expression.
            brand=["Adidas", "Nike", "Puma"] will add
                'brand in ("Adidas", "Nike", "Puma")'
    
    examples/tests:
        period = ['2010-10-11', '2011-11-11']
        bbox = BBox(-80, -79.5, 45, 45.5)
        sample = 5
        subset = ["2A", "4N", "9K", "i8"]
        
        query = load_data.build_sql_query(fields=['name', 'Station_ID', 'X', 'Y', 'Date'],
                                subset=subset, period=period, bbox=bbox, sample=sample,
                                var=['v','q'], car='merc')
                                
        assert query == ' WHERE Station_ID in ("2A", "4N", "9K", "i8") AND ' + \
            "(strftime('%Y-%m-%d', '2010-10-11') <= Date AND Date <= strftime('%Y-%m-%d', '2011-11-11'))" + \
            ' AND (-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y) AND var in ("v", "q")' + \
            ' AND (car == "merc") ORDER BY RANDOM() LIMIT 5'
    """
    query = []
    sample = q_kwargs.get('sample')

    # Add all query arguments passed to the sql query
    for key in q_kwargs:
        q_part = ""
        
        if key == 'bbox':
            x, y = find_xy_fields(fields)
            
            if x != "Failed" and y != "Failed" and x and y:
                q_part = BBox.sql_query(q_kwargs['bbox'], x, y)
            else:
                print("BBox provided but no lat/lon fields found. Skipping BBox query.")
        elif key == 'period':
            q_part = Period.sql_query(q_kwargs['period'], fields)
        elif key == 'subset':
            q_part = id_query_from_subset(q_kwargs['subset'], fields)
        elif key == 'sample':
            pass
        else:
            if key not in fields:
                print(f"{key} field not found in list of fields. Skiping...")
            elif type(q_kwargs[key]) is str:
                q_part = f'({key} == "{q_kwargs[key]}")'
            elif type(q_kwargs[key]) in [int, float]:
                q_part = f'({key} == {q_kwargs[key]})'
            elif hasattr(q_kwargs[key], '__iter__'):
                lst = []
                for i in q_kwargs[key]:
                    if type(i) is str:
                        lst.append(f'"{i}"')
                    else:
                        lst.append(str(i))
                q_part = f'{key} in ({", ".join(lst)})'
        
        if q_part:
            query.append(q_part)

    query = ' AND '.join(query)
    if query:
        query = ' WHERE ' + query
    
    if sample is not None and sample > 0:
        query += f" ORDER BY RANDOM() LIMIT {sample}"

    return query
    
# ========================================================================= ##
# Generator =============================================================== ##
# ========================================================================= ##


def generate_pwqmn_sql():
    """
    Creates a sqlite3 database from PWQMN data.

    Creates a connection to the sql database (if it doesn't exist it
    is created), reads all columns from the PWQMN data, then writes it
    to the sql database as the 'ALL_DATA' table. Also generates a
    'Data_Range' table and a 'Stations' table from the pwqmn data. If
    any of the tables already exist, they are replaced.

    The 'Stations' table stores each unique station that has a record
    of a variable of interest by it's name, ID, latitude, and longitude.
    
    The 'Data_Range' table stores periods where either Nitrogen or
    Phosphurus data is available for each pwqmn station using a start
    and end date.

    Renames certain fields to standardize the column names between PWQMN
    and HYDAT data.

    :return: None
    """
    print("Generating PWQMN sqlite3 database")
    connection = sqlite3.connect(pwqmn_sql_path)

    # read fields of interest, and set data types for mixed type fields
    pwqmn_data = pd.read_csv(pwqmn_path,
                             dtype={'ActivityStartTime': str,
                                    'MethodSpeciation': str,
                                    'MonitoringLocationLongitude': float,
                                    'MonitoringLocationLatitude': float,
                                    'ResultSampleFraction': str,
                                    'ResultValue': float,
                                    'ResultUnit': str,
                                    'ResultDetectionCondition': str,
                                    'ResultDetectionQuantitationLimitType': str,
                                    'ResultDetectionQuantitationLimitMeasure': str,
                                    'ResultDetectionQuantitationLimitUnit': str,
                                    'ResultComment': str,
                                    'ResultAnalyticalMethodID': str,
                                    'ResultAnalyticalMethodContext': str,
                                    'LaboratorySampleID': str})

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
    
    pwqmn_create_stations()
    pwqmn_create_data_range()
    
    connection.close()
    
    return pwqmn_data


def pwqmn_create_stations():
    """
    Adds a 'Stations' table to the PWQMN sqlite3 database. The table
    stores each unique station that has a record of a variable of
    interest by it's name, ID, latitude, and longitude.
    
    :return: DataFrame
        The created SQL table as a DataFrame.
    
    :modifies: database @ pwqmn_sql_path.
    """
    variables = ", ".join(interest_var)
    
    conn = sqlite3.connect(pwqmn_sql_path)
    curs = conn.execute('PRAGMA table_info(ALL_DATA)')
    fields = [field[1] for field in curs.fetchall()]
    
    stations = pd.read_sql_query(
        'SELECT DISTINCT Station_ID, Station_Name, Longitude, Latitude FROM ALL_DATA' + 
        interest_var_query, conn
    )
    stations.to_sql('Stations', conn, index=False, if_exists='replace')
    conn.close()
    
    return stations
    

def pwqmn_create_data_range():
    """
    Adds a 'Data_Range' table to the PWQMN sqlite3 database. The table
    stores periods where either Nitrogen or Phosphurus data is 
    available for each pwqmn station using a start and end date.
    
    Table Name: Data_Range
    Fields: Station_ID, Start, End, Num_Days
    
    Date processing code written by Juliane Mai, January 2023
    Modified by James Wang, November 2023sample
    
    :return: DataFrame
        The created SQL table as a DataFrame.
    
    :modifies: database @ pwqmn_sql_path.
    """
    def add_to_output(st_id, start, end):
        out_data['Station_ID'].append(st_id)
        out_data['P_Start'].append(start)
        out_data['P_End'].append(end)
        delta = date.fromisoformat(end) - date.fromisoformat(start)
        out_data['Num_Days'].append(delta.days + 1)

    conn = sqlite3.connect(pwqmn_sql_path)
    curs = conn.execute('PRAGMA table_info(ALL_DATA)')
    fields = [field[1] for field in curs.fetchall()]
    
    pwqmn_data = pd.read_sql_query('SELECT Station_ID, Date FROM ALL_DATA' + 
                                   interest_var_query, conn)
    
    pwqmn_data['Date'] = pd.to_datetime(pwqmn_data['Date'])
    pwqmn_data['Date'] = pwqmn_data['Date'].dt.strftime("%Y-%m-%d")
    
    grouped = pwqmn_data.groupby(by=['Station_ID'])
    
    out_data = {'Station_ID': [], 'P_Start': [], 'P_End': [], 'Num_Days': []}
    
    for key, sub_df in grouped:
        dates = sub_df['Date'].sort_values().to_list()
        start = None
        last = None
        
        for idate in dates:
            if start is None:
                start = idate
            else:
                str_date = datetime.strptime(idate, "%Y-%m-%d")
                str_last = datetime.strptime(last, "%Y-%m-%d")
                
                if  str_date != str_last + timedelta(days=1) and str_date != str_last:
                    add_to_output(key[0], start, last)
                    start = idate
                    
            last = idate
        add_to_output(key[0], start, last)
      
    out_data = pd.DataFrame(out_data)
    out_data.to_sql('Data_Range', conn, index=False, if_exists='replace')
    
    conn.close()
    return out_data


def get_pwqmn_data(tbl_name, to_csv=False, get_fields="*", **q_kwargs) -> pd.DataFrame:
    """
    Retrieves data from a table in the PWQMN sqlite3 database.
    
    :param tbl_name: str
        Name of the table to read from the pwqmn dataset.
    
    :param to_csv: str or False (default)
        If False, don't save the output DataFrame to a csv file. If
        string, save the output station subset to
        "PWQMN_cleaned/{to_csv}.csv"
    
    :param get_fields: str of list-like of str (default="*")
        The field(s) to read from the sqlite table. Defaults to "*"
        which retrieves all fields from the table.
    
    :param q_kwargs: additional keyword arguments
        Additional keyword arguments to apply to the query.
        Potential q_kwargs key + type:
        
        period: Tuple/list of length 2 or Period object
            Tuple/list of (<start date>, <end date>); dates can be 
            either <str> in format "YYYY-MM-DD" or None; If None, all 
            dates after(before) the start(end) date are retrieved.

        subset: string or list-like/Series of string
            The ID to retrieve or a list, tuple, Series of IDs, or file
            path of a .csv file to load IDs from. If file path, IDs
            will be read from the 'Station_ID' field.
             
        bbox: BBox object
            BBox object defining area of interest. If table does not
            have fields
        
        sample: <positive nonzero int>
            Number of (random) stationsz to read from the table.
            
        other: value or list of values
            Where the keyword is the field name, and the passed
            value is either a single value or list of values
            with which the field will be queryed.
            
            examples:
            brand="Adidas" will add 'brand == "Adidas"' to the
                query expression.
            brand=["Adidas", "Nike", "Puma"] will add
                'brand in ("Adidas", "Nike", "Puma")'
    """
    # create a sqlite3 connection to the pwqmn data
    print("Creating a connection to '{0}'".format(pwqmn_sql_path))
    conn = sqlite3.connect(pwqmn_sql_path)

    # generate a sql query from bbox and period
    curs = conn.execute(f'PRAGMA table_info({tbl_name})')
    fields = [field[1] for field in curs.fetchall()]
    
    query = build_sql_query(fields, **q_kwargs)
    
    if type(get_fields) in (list, tuple):
        get_fields = ', '.join(get_fields)
    
    data = pd.read_sql_query(f'SELECT {get_fields} FROM "{tbl_name}"' + query, conn)
    if to_csv:
        data.to_csv(os.path.join(data_path, 'PWQMN_cleaned', f"{to_csv}.csv"))

    conn.close()
    return data
    

def get_pwqmn_stations(to_csv=False, **q_kwargs) -> pd.DataFrame:
    """
    Loads a list of PWQMN stations with Nitrogen or Phosphorus data 
    from the PWQMN database according to a set of query arguments.

    The PWQMN sqlite database must contain a 'ALL_DATA' table with the
    following fields:
    - Longitude
    - Latitude
    - Station_ID
    - Station_Name
    
    :param to_csv: str or False (default)
        If False, don't save the output DataFrame to a csv file. If
        string, save the output station subset to
        "PWQMN_cleaned/{to_csv}.csv"
    
    :param q_kwargs: additional keyword arguments
        Additional keyword arguments to apply to the query.
        Potential q_kwargs key + type:
        
        period: Tuple/list of length 2 or Period object
            Tuple/list of (<start date>, <end date>); dates can be 
            either <str> in format "YYYY-MM-DD" or None; If None, all 
            dates after(before) the start(end) date are retrieved.

        subset: string or list-like/Series of string
            The ID to retrieve or a list, tuple, Series of IDs, or file
            path of a .csv file to load IDs from. If file path, IDs
            will be read from the 'Station_ID' field.
             
        bbox: BBox object
            BBox object defining area of interest.
        
        sample: <positive nonzero int>
            Number of (random) stationsz to read from the table.
            
        other: value or list of values
            Where the keyword is the field name, and the passed
            value is either a single value or list of values
            with which the field will be queryed.
            
            examples:
            brand="Adidas" will add 'brand == "Adidas"' to the
                query expression.
            brand=["Adidas", "Nike", "Puma"] will add
                'brand in ("Adidas", "Nike", "Puma")'

    :return: <pandas DataFrame>
        PWQMN stations (ID, Name, Lat, Lon) with variables of interest.
    """
    station_df = get_pwqmn_data('Stations', to_csv=False, **q_kwargs)

    if station_df.empty:
        print("Chosen query resulted in empty GeoDataFrame.")
    else:
        if to_csv:
            station_df.to_csv(f"{to_csv}.csv")
            
    return station_df


def get_pwqmn_data_range(to_csv=False, **q_kwargs):
    """
    Retrieves the data ranges of PWQMN stations with variables of
    interest according to query arguments.
    
    :param q_kwargs: additional keyword arguments
        Additional keyword arguments to apply to the query.
        Potential q_kwargs key + type:
        
        period: Tuple/list of length 2 or Period object
            Tuple/list of (<start date>, <end date>); dates can be 
            either <str> in format "YYYY-MM-DD" or None; If None, all 
            dates after(before) the start(end) date are retrieved.

        subset: string or list-like/Series of string
            The ID to retrieve or a list, tuple, Series of IDs, or file
            path of a .csv file to load IDs from. If file path, IDs
            will be read from the 'Station_ID' field.
             
        bbox: BBox object
            BBox object defining area of interest.
        
        sample: <positive nonzero int>
            Number of (random) stationsz to read from the table.
            
        other: value or list of values
            Where the keyword is the field name, and the passed
            value is either a single value or list of values
            with which the field will be queryed.
            
            examples:
            brand="Adidas" will add 'brand == "Adidas"' to the
                query expression.
            brand=["Adidas", "Nike", "Puma"] will add
                'brand in ("Adidas", "Nike", "Puma")'
    
    """
    return get_pwqmn_data('Data_Range', to_csv=to_csv, **q_kwargs)


# ========================================================================= ##
# DataStream ============================================================= ##
# ========================================================================= ##



# ========================================================================= ##
# CSV Loaders ============================================================= ##
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
    
    
# ========================================================================= ##
# HYDAT Loaders =========================================================== ##
# ========================================================================= ##


def get_hydat_data(tbl_name, get_fields='*', to_csv=False, **q_kwargs):
    """
    Retrieves HYDAT station data from the chosen table based on
    a set of fields to retrieve and a set of queries.
    
    :param tbl_name: str
        Name of the database table to retrieve. HYDAT.sqlite3 must
        contain the passed table name.
            
    :param get_fields: string or list of string (default='*')
        The names of the fields to extract from the table. By default
        retrieves all columns from the table.
            
    :param to_csv: bool or string (default=False)
        If string, saves the table to <to_csv>.csv. If False, does
        nothing.
    
    :param q_kwargs: additional keyword arguments
        Additional keyword arguments to apply to the query.
        Potential q_kwargs key + type:
        
        period: Tuple/list of length 2 or Period object
            Tuple/list of (<start date>, <end date>); dates can be 
            either <str> in format "YYYY-MM-DD" or None; If None, all 
            dates after(before) the start(end) date are retrieved.

        subset: string or list-like/Series of string
            The ID to retrieve or a list, tuple, Series of IDs, or file
            path of a .csv file to load IDs from. If file path, IDs
            will be read from the 'Station_ID' field.
             
        b box: BBox object
            BBox object defining area of interest.
        
        sample: <positive nonzero int>
            Number of (random) stationsz to read from the table.
            
        other: value or list of values
            Where the keyword is the field name, and the passed
            value is either a single value or list of values
            with which the field will be queryed.
            
            examples:
            brand="Adidas" will add 'brand == "Adidas"' to the
                query expression.
            brand=["Adidas", "Nike", "Puma"] will add
                'brand in ("Adidas", "Nike", "Puma")'
            
    :return: Pandas DataFrame
        Hydat database table of rows for which all provided query
        arguments are true.
    
    :save: tbl_name.csv
        Saves the table data to <tbl_name>.csv in the hydat
        directory (if to_csv == True).
    
    tests:
        subset = ['02LA019', '02KF009', '02KF004', '04MC001']
        period = ['1999-07-10', '1999-10-11']
        bbox = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
        sample = 10
        
        hydat = load_data.get_hydat_stations(subset=subset)
        assert subset.sort() == hydat['Station_ID'].to_list().sort()
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_1.csv'))

        hydat = load_data.get_hydat_stations(period=period)
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_2.csv'))
        
        hydat = load_data.get_hydat_stations(bbox=bbox)
        assert hydat['Station_ID'].to_list() == \
            ["02EA001","02EB005","02EB006","02EB009","02EB010",
             "02EB011","02EB012","02EB103","02EB105"]
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_3.csv'))
        
        hydat = load_data.get_hydat_stations(sample=sample)
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_4.csv'))
        
        hydat = load_data.get_hydat_stations(bbox=bbox, period=period)
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_5.csv'))
        assert hydat['Station_ID'].to_list() == ["02EB006","02EB011","02EB012"]
        
        hydat = load_data.get_hydat_stations(bbox=bbox, period=period,
                                             sample=sample)
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_6.csv'))
        assert hydat['Station_ID'].sort_values().to_list() == ["02EB006","02EB011","02EB012"]
            
        period2 = [None, '1999-07-10']
        period3 = ['1999-07-10', None]
        
        hydat = load_data.get_hydat_stations(period=period2)
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_7.csv'))

        hydat = load_data.get_hydat_stations(period=period3)
        assert hydat == pd.read_csv(os.path.join(data_path, 'Hydat', 'test_8.csv'))
    
    """
    # create a sqlite3 connection to the hydat data
    print(f"Creating a connection to '{hydat_path}'")
    conn = sqlite3.connect(hydat_path) 

    curs = conn.execute(f'PRAGMA table_info({tbl_name})')
    fields = [field[1] for field in curs.fetchall()]

    query = build_sql_query(fields, **q_kwargs)
   
    if type(get_fields) in (list, tuple):
        get_fields = ', '.join(get_fields)
    
    data = pd.read_sql_query(f'SELECT {get_fields} FROM "{tbl_name}"' + query, conn)
    if to_csv:
        data.to_csv(os.path.join(data_path, 'Hydat', f"{to_csv}.csv"))

    conn.close()
    return data


def get_hydat_flow(to_csv=False, **q_kwargs) -> pd.DataFrame:
    return get_hydat_data('DLY_FLOWS', to_csv=to_csv, **q_kwargs)
 

def get_hydat_remarks(to_csv=False, **q_kwargs) -> pd.DataFrame:
    return get_hydat_data('STN_REMARKS', to_csv=to_csv, **q_kwargs)
                          
                          
def get_hydat_data_range(to_csv=False, **q_kwargs) -> pd.DataFrame:
    try:
        return get_hydat_data('Data_Range', to_csv=to_csv, **q_kwargs)
    except pd.errors.DatabaseError:
        hydat_create_data_range()
    return get_hydat_data('Data_Range', to_csv=to_csv, **q_kwargs)


def get_hydat_stations(to_csv=False, **q_kwargs) -> pd.DataFrame:
    """
    Retrieves HYDAT station data that have streamflow (Q) values.
    Renames certain data fields to standardize between PWQMN and
    HYDAT data.

    The HYDAT sqlite3 database must contain the following tables:
    - STATIONS
    - Data_Range

    STATIONS must contain the following fields:
    - STATION_NUMBER
    - STATION_NAME
    - LONGITUDE
    - LATITUDE

    Data_Range must be created using hydat_create_data_range and
    contain the following fields:
    - Station_ID
    - P_Start
    - P_End
    
    :param to_csv: str or False (default)
        If False, don't save the output DataFrame to a csv file. If
        string, save the output station subset to "Hydat/{to_csv}.csv"
    
    :param q_kwargs: additional keyword arguments
        Additional keyword arguments to apply to the query.
        Potential q_kwargs key + type:
        
        period: Tuple/list of length 2 or Period object
            Tuple/list of (<start date>, <end date>); dates can be 
            either <str> in format "YYYY-MM-DD" or None; If None, all 
            dates after(before) the start(end) date are retrieved.

        subset: string or list-like/Series of string
            The ID to retrieve or a list, tuple, Series of IDs, or file
            path of a .csv file to load IDs from. If file path, IDs
            will be read from the 'Station_ID' field.
             
        bbox: BBox object
            BBox object defining area of interest.
        
        sample: <positive nonzero int>
            Number of (random) stationsz to read from the table.
            
        other: value or list of values
            Where the keyword is the field name, and the passed
            value is either a single value or list of values
            with which the field will be queryed.
            
            examples:
            brand="Adidas" will add 'brand == "Adidas"' to the
                query expression.
            brand=["Adidas", "Nike", "Puma"] will add
                'brand in ("Adidas", "Nike", "Puma")'
    
    :return: <pandas DataFrame>
        HYDAT stations passing all query arguments (see q_kwargs for
        more informatio) with available streamflow data.
    """
    
    sample = q_kwargs.get('sample')
    if sample is not None:
        del q_kwargs['sample']
    
    stations = get_hydat_data('STATIONS', to_csv=False, **q_kwargs)
    data_range = get_hydat_data_range(to_csv=False, **q_kwargs)
    data_range.drop_duplicates(subset=['Station_ID'], inplace=True)
    
    stations = stations.merge(data_range, how='inner', left_on='STATION_NUMBER',
                              right_on='Station_ID')
    stations = stations.drop(columns=['P_Start', 'P_End', 'Station_ID'])
    
    if stations.empty:
        print("Chosen query resulted in empty GeoDataFrame.")

    stations.rename(columns={'LONGITUDE': 'Longitude', 'LATITUDE': 'Latitude',
                               'STATION_NUMBER': 'Station_ID', 'STATION_NAME': 'Station_Name'},
                      inplace=True)
    if sample:
        stations = stations.sample(n=min(sample, stations.shape[0]))
    if to_csv:
        stations.to_csv(os.path.join(data_path, 'Hydat', f"{to_csv}.csv"))
    
    return stations


def hydat_create_data_range(unittest=False):
    """
    Adds a "Data_Range" table to the HYDAT database that contains the
    date ranges for each HYDAT station where streamflow data is
    available. The created table contains 3 fields:
    - Station_ID
    - Start
    - End
    - Num_Days
    
    Requries that the HYDAT database contains the DLY_FLOWS table,
    which has the following fields:
    - STATION_NUMBER
    - YEAR
    - MONTH
    - FLOW1 ... FLOW31 (31 FLOW fields numbered from 1 to 31)
    
    If a Data_Range table already exists, it will be replaced.
    
    :param unittest: bool or DataFrame
        For testing purposes only.
        
    :return: DataFrame
        The table added to the HYDAT database as a DataFrame.
    """
    def add_to_output(st_id, start, end):
        out_data['Station_ID'].append(st_id)
        out_data['P_Start'].append(start)
        out_data['P_End'].append(end)
        delta = date.fromisoformat(end) - date.fromisoformat(start)
        out_data['Num_Days'].append(delta.days + 1)
            
    def is_leap(year):
        return (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0)
    
    def get_periods(st_id, sub_df):
        start = None
        last = None
        
        sub_df = sub_df.sort_values(by=['YEAR', 'MONTH'])
        
        for ind, row in sub_df.iterrows():
            year = row['YEAR']
            month = f"{row['MONTH']:02}"
            days_in_month = row['NO_DAYS']
            
            if row['FULL_MONTH'] == 1:
                idate = f"{year}-{month}-0{1}"
                
                if start is None:
                    start = idate
                elif datetime.strptime(idate, "%Y-%m-%d") != \
                        datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1):
                    add_to_output(st_id, start, last)
                    start = idate
                    
                last = f"{year}-{month}-{days_in_month}"
            else:
                for i in range(1, days_in_month + 1):
                
                    if not pd.isnull(row[f"FLOW{i}"]):
                        idate = f"{year}-{month}-{i:02}"
                        
                        if start is None:
                            start = idate
                        elif datetime.strptime(idate, "%Y-%m-%d") != \
                                datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1):
                            add_to_output(st_id, start, last)
                            start = idate
                        last = idate
            
        add_to_output(st_id, start, last)

    if type(unittest) is pd.DataFrame:
        grouped = unittest.groupby('STATION_NUMBER')
        out_data = {'Station_ID': [], 'P_Start': [], 'P_End': [], 'Num_Days': []} 
        
        for st_id, sub_df in grouped:
            get_periods(st_id, sub_df)
            
    else:
        dly_flows = get_hydat_flow()
        
        grouped = dly_flows.groupby('STATION_NUMBER')
        out_data = {'Station_ID': [], 'P_Start': [], 'P_End': [], 'Num_Days': []}
        
        for st_id, sub_df in grouped:
            get_periods(st_id, sub_df)
            
        out_data = pd.DataFrame(data=out_data)
        conn = sqlite3.connect(hydat_path)
        out_data.to_sql('Data_Range', conn, index=False, if_exists='replace')
        conn.close()
    
    return out_data
    

# ========================================================================= ##
# River Network =========================================================== ##
# ========================================================================= ##


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
    print(f"Loading rivers from '{path}'")
    if not bbox is None:
        bbox = BBox.to_tuple(bbox)
    return read_file(path, rows=sample, bbox=bbox)


# ========================================================================= ##
# Run on Import =========================================================== ##
# ========================================================================= ##


# Check if "PWQMN.sqlite3" already exists. If it doesn't, generate a
# sqlite3 database from the pwqmn data, to accelerate future data
# loading and querying
try:
    check_files.check_path(pwqmn_sql_path)
except FileNotFoundError:
    generate_pwqmn_sql()
